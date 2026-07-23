(capt) C:\Users\javot\Desktop\sofia_code>python gui_trigger.py
Traceback (most recent call last):
  File "C:\Users\javot\Desktop\sofia_code\capt_motor_udp_gui.py", line 45, in <module>
    class UdpReceiver:
  File "C:\Users\javot\Desktop\sofia_code\capt_motor_udp_gui.py", line 63, in UdpReceiver
    def read_latest_packet(self) -> dict | None:
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
GUI execution terminated...


import json
import math
import socket
import sys
import time
from collections import deque

import pyqtgraph as pg

from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------------
# UDP configuration
# ---------------------------------------------------------------------------

UDP_IP = "127.0.0.1"
UDP_PORT = 50000

# Change this to the exact angle variable name sent by dSPACE.
ANGLE_SIGNAL_NAME = "Angle"

TORQUE_SIGNAL_NAME = "Torque"
CURRENT_PHASE_1_NAME = "AO_ch8"
CURRENT_PHASE_2_NAME = "AO_ch16"

PLOT_WINDOW_SECONDS = 10.0
GUI_UPDATE_PERIOD_MS = 20


class UdpReceiver:
    """Non-blocking UDP receiver for dSPACE JSON packets."""

    def __init__(self, ip: str, port: int):
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        self.socket.bind((ip, port))
        self.socket.setblocking(False)

    def read_latest_packet(self) -> dict | None:
        """
        Read every currently waiting packet and return only the latest one.

        Discarding older queued packets prevents the GUI from slowly falling
        behind when packets arrive faster than the plots are refreshed.
        """
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
                decoded_data = raw_data.decode("utf-8")
                packet = json.loads(decoded_data)

                if isinstance(packet, dict):
                    latest_packet = packet

            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                print(f"Invalid UDP packet: {error}")

        return latest_packet

    def close(self) -> None:
        self.socket.close()


class SpringWidget(QWidget):
    """Draws a horizontal spring connected to a movable handle."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.angle_rad = 0.0
        self.measured_torque = 0.0
        self.reference_angle_rad = 0.0
        self.kappa = 1.0

        self.setMinimumHeight(300)

    def set_angle(self, angle_rad: float) -> None:
        self.angle_rad = angle_rad
        self.update()

    def set_measured_torque(self, torque: float) -> None:
        self.measured_torque = torque
        self.update()

    def set_reference_angle(self, reference_rad: float) -> None:
        self.reference_angle_rad = reference_rad
        self.update()

    def set_kappa(self, kappa: float) -> None:
        self.kappa = kappa
        self.update()

    def spring_torque(self) -> float:
        """Torque calculated from the virtual spring model."""
        return -self.kappa * (
            self.angle_rad - self.reference_angle_rad
        )

    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        center_y = height * 0.52
        fixed_x = width * 0.12

        max_visual_displacement = width * 0.28
        maximum_angle = math.radians(30)

        normalized_angle = max(
            -1.0,
            min(1.0, self.angle_rad / maximum_angle),
        )

        equilibrium_x = width * 0.52
        handle_x = equilibrium_x + (
            normalized_angle * max_visual_displacement
        )

        axis_pen = QPen(QColor(140, 140, 140), 1)
        axis_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(axis_pen)
        painter.drawLine(
            QPointF(equilibrium_x, center_y - 80),
            QPointF(equilibrium_x, center_y + 80),
        )

        wall_pen = QPen(QColor(70, 70, 70), 5)
        painter.setPen(wall_pen)
        painter.drawLine(
            QPointF(fixed_x, center_y - 75),
            QPointF(fixed_x, center_y + 75),
        )

        self._draw_spring(
            painter=painter,
            start=QPointF(fixed_x, center_y),
            end=QPointF(handle_x, center_y),
            coils=12,
            amplitude=22,
        )

        handle_pen = QPen(QColor(30, 90, 180), 8)
        painter.setPen(handle_pen)
        painter.drawLine(
            QPointF(handle_x, center_y - 60),
            QPointF(handle_x, center_y + 60),
        )

        self._draw_torque_arrow(
            painter,
            QPointF(handle_x, center_y - 95),
            self.measured_torque,
        )

        painter.setPen(QColor(40, 40, 40))

        angle_deg = math.degrees(self.angle_rad)
        reference_deg = math.degrees(self.reference_angle_rad)

        painter.drawText(
            20,
            30,
            f"Measured angle: {angle_deg:.2f}°",
        )
        painter.drawText(
            20,
            55,
            f"Reference: {reference_deg:.2f}°",
        )
        painter.drawText(
            20,
            80,
            f"Kappa: {self.kappa:.3f} Nm/rad",
        )
        painter.drawText(
            20,
            105,
            f"Measured torque: {self.measured_torque:.3f} Nm",
        )
        painter.drawText(
            20,
            130,
            f"Calculated spring torque: {self.spring_torque():.3f} Nm",
        )

    @staticmethod
    def _draw_spring(
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        coils: int,
        amplitude: float,
    ) -> None:
        spring_pen = QPen(QColor(50, 50, 50), 3)
        painter.setPen(spring_pen)

        lead_length = 20.0
        usable_start_x = start.x() + lead_length
        usable_end_x = end.x() - lead_length

        if usable_end_x <= usable_start_x:
            painter.drawLine(start, end)
            return

        points = [start, QPointF(usable_start_x, start.y())]

        number_of_segments = coils * 2
        spring_length = usable_end_x - usable_start_x

        for index in range(number_of_segments + 1):
            ratio = index / number_of_segments
            x = usable_start_x + ratio * spring_length

            if index == 0 or index == number_of_segments:
                y = start.y()
            else:
                y = (
                    start.y() - amplitude
                    if index % 2
                    else start.y() + amplitude
                )

            points.append(QPointF(x, y))

        points.extend(
            [
                QPointF(usable_end_x, end.y()),
                end,
            ]
        )

        painter.drawPolyline(QPolygonF(points))

    @staticmethod
    def _draw_torque_arrow(
        painter: QPainter,
        origin: QPointF,
        torque: float,
    ) -> None:
        if abs(torque) < 1e-6:
            return

        arrow_length = 65
        direction = 1 if torque > 0 else -1

        arrow_pen = QPen(QColor(190, 70, 50), 3)
        painter.setPen(arrow_pen)

        end = QPointF(
            origin.x() + direction * arrow_length,
            origin.y(),
        )

        painter.drawLine(origin, end)

        head_size = 10

        painter.drawLine(
            end,
            QPointF(
                end.x() - direction * head_size,
                end.y() - head_size,
            ),
        )

        painter.drawLine(
            end,
            QPointF(
                end.x() - direction * head_size,
                end.y() + head_size,
            ),
        )


class SpringPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.spring_view = SpringWidget()

        self.angle_label = QLabel("Measured angle: 0.000°")
        self.torque_label = QLabel("Measured torque: 0.000 Nm")

        self.kappa_input = QDoubleSpinBox()
        self.kappa_input.setRange(0.0, 20.0)
        self.kappa_input.setDecimals(3)
        self.kappa_input.setSingleStep(0.1)
        self.kappa_input.setValue(1.0)
        self.kappa_input.setSuffix(" Nm/rad")

        reset_button = QPushButton("Reset reference")

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.angle_label)
        control_layout.addWidget(self.torque_label)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("Kappa"))
        control_layout.addWidget(self.kappa_input)
        control_layout.addWidget(reset_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.spring_view, 1)
        layout.addLayout(control_layout)

        self.kappa_input.valueChanged.connect(
            self.spring_view.set_kappa
        )

        reset_button.clicked.connect(self._set_current_as_reference)

    def update_measurements(
        self,
        angle_rad: float,
        torque: float,
    ) -> None:
        self.spring_view.set_angle(angle_rad)
        self.spring_view.set_measured_torque(torque)

        self.angle_label.setText(
            f"Measured angle: {math.degrees(angle_rad):.3f}°"
        )

        self.torque_label.setText(
            f"Measured torque: {torque:.3f} Nm"
        )

    def _set_current_as_reference(self) -> None:
        self.spring_view.set_reference_angle(
            self.spring_view.angle_rad
        )


class SignalPlotPage(QWidget):
    """First-page plots for commanded currents and measured torque."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.start_time = time.monotonic()

        maximum_points = int(
            PLOT_WINDOW_SECONDS
            * 1000
            / GUI_UPDATE_PERIOD_MS
        ) + 100

        self.time_values = deque(maxlen=maximum_points)
        self.torque_values = deque(maxlen=maximum_points)
        self.current_1_values = deque(maxlen=maximum_points)
        self.current_2_values = deque(maxlen=maximum_points)

        self.torque_value_label = QLabel("Torque: --")
        self.current_1_value_label = QLabel(
            f"{CURRENT_PHASE_1_NAME}: --"
        )
        self.current_2_value_label = QLabel(
            f"{CURRENT_PHASE_2_NAME}: --"
        )

        value_layout = QHBoxLayout()
        value_layout.addWidget(self.torque_value_label)
        value_layout.addWidget(self.current_1_value_label)
        value_layout.addWidget(self.current_2_value_label)
        value_layout.addStretch()

        self.current_plot = self._create_plot(
            title="Commanded currents",
            y_label="Current",
            units="A",
        )

        self.torque_plot = self._create_plot(
            title="Measured torque",
            y_label="Torque",
            units="Nm",
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

        self.torque_curve = self.torque_plot.plot(
            pen=pg.mkPen(width=2),
            name=TORQUE_SIGNAL_NAME,
        )

        self.current_plot.addLegend()
        self.torque_plot.addLegend()

        clear_button = QPushButton("Clear plots")
        clear_button.clicked.connect(self.clear)

        top_layout = QHBoxLayout()
        top_layout.addLayout(value_layout)
        top_layout.addWidget(clear_button)

        plot_layout = QGridLayout()
        plot_layout.addWidget(self.current_plot, 0, 0)
        plot_layout.addWidget(self.torque_plot, 1, 0)

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
            "Time",
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

        return plot

    def add_sample(
        self,
        angle_rad: float,
        torque: float,
        current_1: float,
        current_2: float,
    ) -> None:
        del angle_rad

        current_time = time.monotonic() - self.start_time

        self.time_values.append(current_time)
        self.torque_values.append(torque)
        self.current_1_values.append(current_1)
        self.current_2_values.append(current_2)

        self.torque_value_label.setText(
            f"Torque: {torque:.3f} Nm"
        )

        self.current_1_value_label.setText(
            f"{CURRENT_PHASE_1_NAME}: {current_1:.3f} A"
        )

        self.current_2_value_label.setText(
            f"{CURRENT_PHASE_2_NAME}: {current_2:.3f} A"
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

        if latest_time > PLOT_WINDOW_SECONDS:
            minimum_time = latest_time - PLOT_WINDOW_SECONDS
            maximum_time = latest_time
        else:
            minimum_time = 0.0
            maximum_time = PLOT_WINDOW_SECONDS

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
        self.start_time = time.monotonic()

        self.time_values.clear()
        self.torque_values.clear()
        self.current_1_values.clear()
        self.current_2_values.clear()

        self.current_1_curve.clear()
        self.current_2_curve.clear()
        self.torque_curve.clear()


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        title = QLabel("CAPT Motor Dashboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        instructions = QLabel(
            "Waiting for UDP data from dSPACE...\n\n"
            f"UDP address: {UDP_IP}:{UDP_PORT}\n"
            f"Angle signal: {ANGLE_SIGNAL_NAME}\n"
            f"Torque signal: {TORQUE_SIGNAL_NAME}\n"
            f"Current signals: {CURRENT_PHASE_1_NAME}, "
            f"{CURRENT_PHASE_2_NAME}"
        )

        instructions.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")
        self.resize(1100, 800)

        self.udp_receiver = UdpReceiver(
            UDP_IP,
            UDP_PORT,
        )

        self.latest_angle_rad = 0.0
        self.latest_torque = 0.0
        self.latest_current_1 = 0.0
        self.latest_current_2 = 0.0

        self.packet_count = 0
        self.last_packet_time = None

        self.home_page = HomePage()
        self.signal_plot_page = SignalPlotPage()
        self.spring_page = SpringPage()

        tabs = QTabWidget()
        tabs.addTab(self.signal_plot_page, "Live Signals")
        tabs.addTab(self.home_page, "Home")
        tabs.addTab(self.spring_page, "Virtual Spring")

        self.setCentralWidget(tabs)

        self.status_label = QLabel(
            f"Listening on UDP {UDP_IP}:{UDP_PORT}"
        )

        self.statusBar().addPermanentWidget(
            self.status_label
        )

        self.receive_timer = QTimer(self)
        self.receive_timer.timeout.connect(
            self._receive_udp_data
        )

        self.receive_timer.start(
            GUI_UPDATE_PERIOD_MS
        )

    def _receive_udp_data(self) -> None:
        packet = self.udp_receiver.read_latest_packet()

        if packet is None:
            self._update_connection_status()
            return

        angle_value = self._read_number(
            packet,
            ANGLE_SIGNAL_NAME,
        )

        torque_value = self._read_number(
            packet,
            TORQUE_SIGNAL_NAME,
        )

        current_1_value = self._read_number(
            packet,
            CURRENT_PHASE_1_NAME,
        )

        current_2_value = self._read_number(
            packet,
            CURRENT_PHASE_2_NAME,
        )

        if angle_value is not None:
            # Assumes dSPACE sends angle in radians.
            self.latest_angle_rad = angle_value

        if torque_value is not None:
            self.latest_torque = torque_value

        if current_1_value is not None:
            self.latest_current_1 = current_1_value

        if current_2_value is not None:
            self.latest_current_2 = current_2_value

        self.packet_count += 1
        self.last_packet_time = time.monotonic()

        self.signal_plot_page.add_sample(
            angle_rad=self.latest_angle_rad,
            torque=self.latest_torque,
            current_1=self.latest_current_1,
            current_2=self.latest_current_2,
        )

        self.spring_page.update_measurements(
            angle_rad=self.latest_angle_rad,
            torque=self.latest_torque,
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

    def _update_connection_status(self) -> None:
        if self.last_packet_time is None:
            self.status_label.setText(
                f"Waiting for dSPACE on "
                f"{UDP_IP}:{UDP_PORT}"
            )
            return

        elapsed = time.monotonic() - self.last_packet_time

        if elapsed < 1.0:
            status = "Receiving"
        elif elapsed < 3.0:
            status = "No recent packets"
        else:
            status = "Connection inactive"

        self.status_label.setText(
            f"{status} | Packets: {self.packet_count}"
        )

    def closeEvent(self, event) -> None:
        self.receive_timer.stop()
        self.udp_receiver.close()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```
