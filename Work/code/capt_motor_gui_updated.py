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
    """
    Visualisation of an asymmetric rotational spring around the motor.

    Positive rotation:
        +K spring after positive deadzone

    Negative rotation:
        -K spring after negative deadzone
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.angle_rad = 0.0
        self.measured_torque = 0.0

        self.reference_angle_rad = 0.0

        # asymmetric spring parameters
        self.kappa_positive = 2.0   # Nm/rad
        self.kappa_negative = 0.8   # Nm/rad

        # rotational deadzone
        self.deadzone_rad = math.radians(5)

        self.setMinimumHeight(400)


    def set_angle(self, angle_rad):

        self.angle_rad = angle_rad
        self.update()


    def set_measured_torque(self, torque):

        self.measured_torque = torque
        self.update()


    def set_reference_angle(self, reference_rad):

        self.reference_angle_rad = reference_rad
        self.update()


    def spring_torque(self):

        error = (
            self.angle_rad -
            self.reference_angle_rad
        )

        if error > self.deadzone_rad:

            return (
                -self.kappa_positive *
                (error-self.deadzone_rad)
            )


        elif error < -self.deadzone_rad:

            return (
                -self.kappa_negative *
                (error+self.deadzone_rad)
            )


        return 0.0



    def paintEvent(self,event):

        del event


        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )


        w = self.width()
        h = self.height()


        cx = w/2
        cy = h/2


        # ------------------------------------------------
        # Motor body
        # ------------------------------------------------

        motor_radius = 65


        painter.setPen(
            QPen(
                QColor(60,60,60),
                4
            )
        )


        painter.drawEllipse(
            QPointF(cx,cy),
            motor_radius,
            motor_radius
        )


        # motor shaft angle

        shaft_length = 110


        angle = self.angle_rad


        shaft_end = QPointF(
            cx +
            shaft_length*math.cos(angle),

            cy -
            shaft_length*math.sin(angle)
        )


        painter.setPen(
            QPen(
                QColor(30,90,200),
                6
            )
        )


        painter.drawLine(
            QPointF(cx,cy),
            shaft_end
        )



        # ------------------------------------------------
        # zero reference line
        # ------------------------------------------------

        painter.setPen(
            QPen(
                QColor(160,160,160),
                2,
                Qt.PenStyle.DashLine
            )
        )


        painter.drawLine(
            QPointF(cx-150,cy),
            QPointF(cx+150,cy)
        )



        # ------------------------------------------------
        # rotational springs
        # ------------------------------------------------


        positive_active = (
            angle >
            self.deadzone_rad
        )


        negative_active = (
            angle <
            -self.deadzone_rad
        )


        self._draw_rotational_spring(
            painter,
            cx,
            cy,
            side=1,
            active=positive_active
        )


        self._draw_rotational_spring(
            painter,
            cx,
            cy,
            side=-1,
            active=negative_active
        )



        # ------------------------------------------------
        # torque arrow
        # ------------------------------------------------

        self._draw_torque_arrow(
            painter,
            QPointF(
                cx,
                cy-160
            ),
            self.measured_torque
        )



        # ------------------------------------------------
        # information
        # ------------------------------------------------


        painter.setPen(
            QColor(40,40,40)
        )


        painter.drawText(
            20,
            30,
            f"Angle: {math.degrees(self.angle_rad):.2f} deg"
        )


        painter.drawText(
            20,
            55,
            f"Deadzone: ±{math.degrees(self.deadzone_rad):.1f} deg"
        )


        painter.drawText(
            20,
            80,
            f"K+: {self.kappa_positive:.2f} Nm/rad"
        )


        painter.drawText(
            20,
            105,
            f"K-: {self.kappa_negative:.2f} Nm/rad"
        )


        painter.drawText(
            20,
            130,
            f"Spring torque: {self.spring_torque():.3f} Nm"
        )


        painter.drawText(
            20,
            155,
            f"Measured torque: {self.measured_torque:.3f} Nm"
        )



    def _draw_rotational_spring(
        self,
        painter,
        cx,
        cy,
        side,
        active
    ):


        radius = 125


        if side > 0:

            color = QColor(
                40,
                160,
                70
            )

            start = 0


        else:

            color = QColor(
                180,
                70,
                50
            )

            start = math.pi



        if not active:

            color = QColor(
                180,
                180,
                180
            )


        painter.setPen(
            QPen(
                color,
                3
            )
        )


        points=[]


        turns = 4


        for i in range(100):

            theta = (
                start +
                side *
                2 *
                math.pi *
                turns *
                i /
                99
            )


            r = (
                radius +
                12 *
                math.sin(
                    turns*theta
                )
            )


            x = (
                cx +
                r *
                math.cos(theta)
            )


            y = (
                cy -
                r *
                math.sin(theta)
            )


            points.append(
                QPointF(x,y)
            )


        painter.drawPolyline(
            QPolygonF(points)
        )



    def _draw_torque_arrow(
        self,
        painter,
        origin,
        torque
    ):

        if abs(torque)<1e-6:
            return


        length = 70


        direction = (
            1
            if torque > 0
            else -1
        )


        painter.setPen(
            QPen(
                QColor(200,50,50),
                3
            )
        )


        end = QPointF(
            origin.x()+direction*length,
            origin.y()
        )


        painter.drawLine(
            origin,
            end
        )


        painter.drawLine(
            end,
            QPointF(
                end.x()-direction*10,
                end.y()-10
            )
        )


        painter.drawLine(
            end,
            QPointF(
                end.x()-direction*10,
                end.y()+10
            )
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
