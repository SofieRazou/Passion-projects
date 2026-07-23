import json
import math
import socket
import sys
import time
from collections import deque

import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------------
# UDP and signal configuration
# ---------------------------------------------------------------------------

UDP_IP = "127.0.0.1"
UDP_PORT = 50000

CURRENT_PHASE_1_NAME = "AO_ch8"
CURRENT_PHASE_2_NAME = "AO_ch16"
TORQUE_SIGNAL_NAME = "Torque"
ELAPSED_TIME_NAME = "elapsed_time"
PACKET_NUMBER_NAME = "packet"

PLOT_WINDOW_SECONDS = 10.0
GUI_UPDATE_PERIOD_MS = 20


class UdpReceiver:
    """Receive JSON packets from dSPACE without blocking the GUI."""

    def __init__(self, ip: str, port: int) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.setblocking(False)

    def read_latest_packet(self) -> dict | None:
        """Return the newest waiting packet and discard older queued packets."""
        latest_packet = None

        while True:
            try:
                raw_data, _sender = self.socket.recvfrom(65535)
            except BlockingIOError:
                break
            except OSError as error:
                print(f"UDP receive error: {error}")
                break

            try:
                packet = json.loads(raw_data.decode("utf-8"))

                if isinstance(packet, dict):
                    latest_packet = packet

            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                print(f"Invalid UDP packet: {error}")

        return latest_packet

    def close(self) -> None:
        self.socket.close()


class HomePage(QWidget):
    """Basic connection and signal information."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        title = QLabel("CAPT Motor Dashboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        instructions = QLabel(
            "Waiting for UDP data from dSPACE...\n\n"
            f"UDP address: {UDP_IP}:{UDP_PORT}\n"
            f"Current phase 1: {CURRENT_PHASE_1_NAME}\n"
            f"Current phase 2: {CURRENT_PHASE_2_NAME}\n"
            f"Torque: {TORQUE_SIGNAL_NAME}\n"
            f"Time axis: {ELAPSED_TIME_NAME}"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addStretch()


class SignalPlotPage(QWidget):
    """
    Real-time plots for:

    1. AO_ch8 and AO_ch16 together on the same current plot.
    2. Torque on a separate plot.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.local_start_time = time.monotonic()
        self.first_received_elapsed_time: float | None = None

        maximum_points = int(
            PLOT_WINDOW_SECONDS * 1000 / GUI_UPDATE_PERIOD_MS
        ) + 200

        self.time_values = deque(maxlen=maximum_points)
        self.current_1_values = deque(maxlen=maximum_points)
        self.current_2_values = deque(maxlen=maximum_points)
        self.torque_values = deque(maxlen=maximum_points)

        self.current_1_value_label = QLabel(
            f"{CURRENT_PHASE_1_NAME}: --"
        )
        self.current_2_value_label = QLabel(
            f"{CURRENT_PHASE_2_NAME}: --"
        )
        self.torque_value_label = QLabel(
            f"{TORQUE_SIGNAL_NAME}: --"
        )
        self.packet_value_label = QLabel("Packet: --")

        value_layout = QHBoxLayout()
        value_layout.addWidget(self.current_1_value_label)
        value_layout.addWidget(self.current_2_value_label)
        value_layout.addWidget(self.torque_value_label)
        value_layout.addWidget(self.packet_value_label)
        value_layout.addStretch()

        # Plot 1: both current phases on the same axes.
        self.current_plot = self._create_plot(
            title="Motor phase signals",
            y_label="Signal value",
            units="",
        )

        self.current_1_curve = self.current_plot.plot(
            pen=pg.mkPen(width=2),
            name=CURRENT_PHASE_1_NAME,
        )

        self.current_2_curve = self.current_plot.plot(
            pen=pg.mkPen(
                width=2,
                style=Qt.PenStyle.DashLine,
            ),
            name=CURRENT_PHASE_2_NAME,
        )

        self.current_plot.addLegend()

        # Plot 2: torque.
        self.torque_plot = self._create_plot(
            title="Motor torque",
            y_label="Torque",
            units="Nm",
        )

        self.torque_curve = self.torque_plot.plot(
            pen=pg.mkPen(width=2),
            name=TORQUE_SIGNAL_NAME,
        )

        self.torque_plot.addLegend()

        clear_button = QPushButton("Clear plots")
        clear_button.clicked.connect(self.clear)

        top_layout = QHBoxLayout()
        top_layout.addLayout(value_layout)
        top_layout.addWidget(clear_button)

        plot_layout = QGridLayout()
        plot_layout.addWidget(self.current_plot, 0, 0)
        plot_layout.addWidget(self.torque_plot, 1, 0)
        plot_layout.setRowStretch(0, 1)
        plot_layout.setRowStretch(1, 1)

        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addLayout(plot_layout, 1)

    @staticmethod
    def _create_plot(
        title: str,
        y_label: str,
        units: str,
    ) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)

        plot.setLabel(
            "bottom",
            "Elapsed time",
            units="s",
        )

        plot.setLabel(
            "left",
            y_label,
            units=units,
        )

        plot.showGrid(
            x=True,
            y=True,
            alpha=0.25,
        )

        plot.setClipToView(True)
        plot.setDownsampling(auto=True, mode="peak")

        return plot

    def add_sample(
        self,
        current_1: float,
        current_2: float,
        torque: float,
        elapsed_time: float | None,
        packet_number: int | None,
    ) -> None:
        """Add one UDP sample to the plots."""

        if elapsed_time is None:
            plot_time = time.monotonic() - self.local_start_time
        else:
            # Start the displayed time axis from zero, even when dSPACE sends
            # an elapsed time such as 25.69 seconds in the first received packet.
            if self.first_received_elapsed_time is None:
                self.first_received_elapsed_time = elapsed_time

            plot_time = elapsed_time - self.first_received_elapsed_time

        self.time_values.append(plot_time)
        self.current_1_values.append(current_1)
        self.current_2_values.append(current_2)
        self.torque_values.append(torque)

        self.current_1_value_label.setText(
            f"{CURRENT_PHASE_1_NAME}: {current_1:.3f}"
        )
        self.current_2_value_label.setText(
            f"{CURRENT_PHASE_2_NAME}: {current_2:.3f}"
        )
        self.torque_value_label.setText(
            f"{TORQUE_SIGNAL_NAME}: {torque:.3f} Nm"
        )

        if packet_number is not None:
            self.packet_value_label.setText(
                f"Packet: {packet_number}"
            )

        self._update_curves()

    def _update_curves(self) -> None:
        if not self.time_values:
            return

        times = list(self.time_values)

        self.current_1_curve.setData(
            times,
            list(self.current_1_values),
        )
        self.current_2_curve.setData(
            times,
            list(self.current_2_values),
        )
        self.torque_curve.setData(
            times,
            list(self.torque_values),
        )

        latest_time = times[-1]
        minimum_time = max(0.0, latest_time - PLOT_WINDOW_SECONDS)
        maximum_time = max(PLOT_WINDOW_SECONDS, latest_time)

        self.current_plot.setXRange(
            minimum_time,
            maximum_time,
            padding=0,
        )
        self.torque_plot.setXRange(
            minimum_time,
            maximum_time,
            padding=0,
        )

    def clear(self) -> None:
        self.local_start_time = time.monotonic()
        self.first_received_elapsed_time = None

        self.time_values.clear()
        self.current_1_values.clear()
        self.current_2_values.clear()
        self.torque_values.clear()

        self.current_1_curve.clear()
        self.current_2_curve.clear()
        self.torque_curve.clear()

        self.current_1_value_label.setText(
            f"{CURRENT_PHASE_1_NAME}: --"
        )
        self.current_2_value_label.setText(
            f"{CURRENT_PHASE_2_NAME}: --"
        )
        self.torque_value_label.setText(
            f"{TORQUE_SIGNAL_NAME}: --"
        )
        self.packet_value_label.setText("Packet: --")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")
        self.resize(1100, 800)

        try:
            self.udp_receiver = UdpReceiver(UDP_IP, UDP_PORT)
        except OSError as error:
            raise RuntimeError(
                f"Could not bind UDP socket to {UDP_IP}:{UDP_PORT}: {error}"
            ) from error

        self.latest_current_1 = 0.0
        self.latest_current_2 = 0.0
        self.latest_torque = 0.0

        self.packet_count = 0
        self.last_packet_time: float | None = None

        self.home_page = HomePage()
        self.signal_plot_page = SignalPlotPage()

        tabs = QTabWidget()
        tabs.addTab(self.home_page, "Home")
        tabs.addTab(self.signal_plot_page, "Live Signals")
        self.setCentralWidget(tabs)

        self.status_label = QLabel(
            f"Listening on UDP {UDP_IP}:{UDP_PORT}"
        )
        self.statusBar().addPermanentWidget(self.status_label)

        self.receive_timer = QTimer(self)
        self.receive_timer.timeout.connect(self._receive_udp_data)
        self.receive_timer.start(GUI_UPDATE_PERIOD_MS)

    def _receive_udp_data(self) -> None:
        packet = self.udp_receiver.read_latest_packet()

        if packet is None:
            self._update_connection_status()
            return

        current_1_value = self._read_number(
            packet,
            CURRENT_PHASE_1_NAME,
        )
        current_2_value = self._read_number(
            packet,
            CURRENT_PHASE_2_NAME,
        )
        torque_value = self._read_number(
            packet,
            TORQUE_SIGNAL_NAME,
        )
        elapsed_time_value = self._read_number(
            packet,
            ELAPSED_TIME_NAME,
        )
        packet_number_value = self._read_integer(
            packet,
            PACKET_NUMBER_NAME,
        )

        # Skip packets that do not contain all three plotted signals.
        if (
            current_1_value is None
            or current_2_value is None
            or torque_value is None
        ):
            print(f"Incomplete UDP packet ignored: {packet}")
            self._update_connection_status()
            return

        self.latest_current_1 = current_1_value
        self.latest_current_2 = current_2_value
        self.latest_torque = torque_value

        self.packet_count += 1
        self.last_packet_time = time.monotonic()

        self.signal_plot_page.add_sample(
            current_1=self.latest_current_1,
            current_2=self.latest_current_2,
            torque=self.latest_torque,
            elapsed_time=elapsed_time_value,
            packet_number=packet_number_value,
        )

        self._update_connection_status()

    @staticmethod
    def _read_number(
        packet: dict,
        signal_name: str,
    ) -> float | None:
        value = packet.get(signal_name)

        if value is None:
            return None

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(numeric_value):
            return None

        return numeric_value

    @staticmethod
    def _read_integer(
        packet: dict,
        signal_name: str,
    ) -> int | None:
        value = packet.get(signal_name)

        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _update_connection_status(self) -> None:
        if self.last_packet_time is None:
            self.status_label.setText(
                f"Waiting for dSPACE on {UDP_IP}:{UDP_PORT}"
            )
            return

        seconds_since_packet = time.monotonic() - self.last_packet_time

        if seconds_since_packet < 1.0:
            status = "Receiving"
        elif seconds_since_packet < 3.0:
            status = "No recent packets"
        else:
            status = "Connection inactive"

        self.status_label.setText(
            f"{status} | Received samples: {self.packet_count}"
        )

    def closeEvent(self, event) -> None:
        self.receive_timer.stop()
        self.udp_receiver.close()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)

    try:
        window = MainWindow()
    except RuntimeError as error:
        print(error)
        sys.exit(1)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
