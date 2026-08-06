import json
import math
import socket
import struct
import sys
import time
from collections import deque
from typing import Optional
import pyqtgraph as pg
import pygame
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# UDP Configuration
# ---------------------------------------------------------------------------

UDP_IP = "127.0.0.1"
UDP_PORT = 50000

ANGLE_FORWARD_IP = "127.0.0.1"
ANGLE_FORWARD_PORT = 5006

CONTROL_IP = "134.105.60.99"
CONTROL_PORT = 55001

# Signal names sent by dSPACE
ANGLE_SIGNAL_NAME = "Out1"
TORQUE_SIGNAL_NAME = "Torque"
CURRENT_PHASE_1_NAME = "AO_ch8"
CURRENT_PHASE_2_NAME = "AO_ch16"

R5_TORQUE_SIGNAL_NAME = "Moza R5 Torque"
R5_ANGLE_SIGNAL_NAME = "Moza R5 Angle"


PLOT_WINDOW_SECONDS = 10.0
GUI_UPDATE_PERIOD_MS = 20  # 50 Hz refresh rate


#Stability plot graph(s)
STABILITY_PLOT_PATH = ""
TRANSPARENCY_PLOT_PATH =""


#Max Torque output of Moza R5  wheel
MOZA_R5_MAX_TORQUE = 5.5  # Nm
WIDTH = 800 # FOR LOGGING ACCORDIGN sample sizes for moza torque 

# ---------------------------------------------------------------------------
# Socket Communication Classes
# ---------------------------------------------------------------------------


class UdpReceiver:
    """Non-blocking UDP receiver for dSPACE JSON packets."""

    def __init__(self, ip: str, port: int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.setblocking(False)

    def read_latest_packet(self) -> Optional[dict]:
        """Reads all queued packets and returns only the latest frame."""
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
        try:
            self.socket.close()
        except OSError:
            pass


class UdpSender:
    """UDP sender for forwarding signals (Supports raw bytes & JSON)."""

    def __init__(self, ip: str, port: int, send_as_binary: bool = True):
        self.ip = ip
        self.port = port
        self.send_as_binary = send_as_binary
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_angle(self, angle: float) -> None:
        if self.send_as_binary:
            # Send as 64-bit Little-Endian double (Simulink/C compatible)
            data = struct.pack("<d", float(angle))
        else:
            # Send as JSON string payload
            packet = {"angle": angle}
            data = json.dumps(packet).encode("utf-8")

        try:
            self.socket.sendto(data, (self.ip, self.port))
        except OSError as err:
            print(f"UDP send error: {err}")

    def close(self) -> None:
        try:
            self.socket.close()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# UI Widgets & Visualization Pages
# ---------------------------------------------------------------------------


class SpringWidget(QWidget):
    """Draws a horizontal dynamic spring connected to a movable handle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle_rad = 0.0
        self.measured_torque = 0.0
        self.reference_angle_rad = 0.0
        self.kappa = 1.0
        self.setMinimumHeight(300)

        # Pre-allocate pens to avoid allocations in paintEvent
        self._axis_pen = QPen(QColor(140, 140, 140), 1, Qt.PenStyle.DashLine)
        self._wall_pen = QPen(QColor(70, 70, 70), 5)
        self._handle_pen = QPen(QColor(30, 90, 180), 8)
        self._text_color = QColor(40, 40, 40)

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
        return -self.kappa * (self.angle_rad - self.reference_angle_rad)

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
            -1.0, min(1.0, self.angle_rad / maximum_angle)
        )
        equilibrium_x = width * 0.52
        handle_x = equilibrium_x + (
            normalized_angle * max_visual_displacement
        )

        # Axis Line
        painter.setPen(self._axis_pen)
        painter.drawLine(
            QPointF(equilibrium_x, center_y - 80),
            QPointF(equilibrium_x, center_y + 80),
        )

        # Wall Anchor
        painter.setPen(self._wall_pen)
        painter.drawLine(
            QPointF(fixed_x, center_y - 75), QPointF(fixed_x, center_y + 75)
        )

        # Draw Spring Polyline
        self._draw_spring(
            painter=painter,
            start=QPointF(fixed_x, center_y),
            end=QPointF(handle_x, center_y),
            coils=12,
            amplitude=22,
        )

        # Movable Handle Bar
        painter.setPen(self._handle_pen)
        painter.drawLine(
            QPointF(handle_x, center_y - 60), QPointF(handle_x, center_y + 60)
        )

        # Torque Arrow Indicator
        self._draw_torque_arrow(
            painter, QPointF(handle_x, center_y - 95), self.measured_torque
        )

        # Text Overlay
        painter.setPen(self._text_color)
        angle_deg = math.degrees(self.angle_rad)
        reference_deg = math.degrees(self.reference_angle_rad)

        painter.drawText(20, 30, f"Measured angle: {angle_deg:.2f}°")
        painter.drawText(20, 55, f"Reference: {reference_deg:.2f}°")
        painter.drawText(20, 80, f"Kappa: {self.kappa:.3f} Nm/rad")
        painter.drawText(
            20, 105, f"Measured torque: {self.measured_torque:.3f} Nm"
        )
        painter.drawText(
            20, 130, f"Calculated spring torque: {self.spring_torque():.3f} Nm"
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

            if index in (0, number_of_segments):
                y = start.y()
            else:
                y = (
                    start.y() - amplitude
                    if index % 2
                    else start.y() + amplitude
                )

            points.append(QPointF(x, y))

        points.extend([QPointF(usable_end_x, end.y()), end])
        painter.drawPolyline(QPolygonF(points))

    @staticmethod
    def _draw_torque_arrow(
        painter: QPainter, origin: QPointF, torque: float
    ) -> None:
        if abs(torque) < 1e-6:
            return

        arrow_length = 65
        direction = 1 if torque > 0 else -1
        head_size = 10

        arrow_pen = QPen(QColor(190, 70, 50), 3)
        painter.setPen(arrow_pen)

        end = QPointF(
            origin.x() + direction * arrow_length,
            origin.y(),
        )

        painter.drawLine(origin, end)
        painter.drawLine(
            end,
            QPointF(
                end.x() - direction * head_size, end.y() - head_size
            ),
        )
        painter.drawLine(
            end,
            QPointF(
                end.x() - direction * head_size, end.y() + head_size
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

        self.kappa_input.valueChanged.connect(self.spring_view.set_kappa)
        reset_button.clicked.connect(self._set_current_as_reference)

    def update_measurements(self, angle_rad: float, torque: float) -> None:
        self.spring_view.set_angle(angle_rad)
        self.spring_view.set_measured_torque(torque)
        self.angle_label.setText(
            f"Measured angle: {math.degrees(angle_rad):.3f}°"
        )
        self.torque_label.setText(f"Measured torque: {torque:.3f} Nm")

    def _set_current_as_reference(self) -> None:
        self.spring_view.set_reference_angle(self.spring_view.angle_rad)


class SignalPlotPage(QWidget):
    """Real-time plotting page for current, torque, and steering angle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = time.monotonic()

        maximum_points = (
            int(PLOT_WINDOW_SECONDS * 1000 / GUI_UPDATE_PERIOD_MS) + 100
        )

        self.time_values = deque(maxlen=maximum_points)
        self.torque_values = deque(maxlen=maximum_points)
        self.current_1_values = deque(maxlen=maximum_points)
        self.current_2_values = deque(maxlen=maximum_points)
        self.angle_values = deque(maxlen=maximum_points)

        self.moza_angle_values = deque(maxlen=maximum_points)
        self.moza_torque_values = deque(maxlen=maximum_points)

        self.torque_value_label = QLabel("Torque: --")
        self.current_1_value_label = QLabel(f"{CURRENT_PHASE_1_NAME}: --")
        self.current_2_value_label = QLabel(f"{CURRENT_PHASE_2_NAME}: --")
        self.angle_value_label = QLabel("Angle: --")

        value_layout = QHBoxLayout()
        value_layout.addWidget(self.torque_value_label)
        value_layout.addWidget(self.current_1_value_label)
        value_layout.addWidget(self.current_2_value_label)
        value_layout.addWidget(self.angle_value_label)
        value_layout.addStretch()

        self.current_plot = self._create_plot(
            "Commanded currents", "Current", "A"
        )
        self.torque_plot = self._create_plot("Measured CAPT Motor Torque", "Torque", "Nm")
        self.angle_plot = self._create_plot(
            "Measured CAPT Motor steering angle", "Angle", "degrees"
        )
        # Moza R5 stats 
        self.moza_angle_plot = self._create_plot("Measured Moza R5 Angle", "Moza R5 Angle", "degrees")
        self.moza_torque_plot = self._create_plot("Measured Moza R5 Torque", "Moza R5 Torque", "Nm")

        #Curves configs 

        self.current_1_curve = self.current_plot.plot(
            pen=pg.mkPen(width=2), name=CURRENT_PHASE_1_NAME
        )
        self.current_2_curve = self.current_plot.plot(
            pen=pg.mkPen(color=(0, 0, 255), width=2), name=CURRENT_PHASE_2_NAME
        )
        self.torque_curve = self.torque_plot.plot(
            pen=pg.mkPen(color=(255, 0, 255), width=2), name=TORQUE_SIGNAL_NAME
        )
        self.angle_curve = self.angle_plot.plot(
            pen=pg.mkPen(color=(64, 224, 208), width=2), name=ANGLE_SIGNAL_NAME
        )
        self.moza_angle_curve = self.moza_angle_plot(
            pen = pg.mkPen(color=(64, 224, 208), width=2), name=R5_ANGLE_SIGNAL_NAME
        )
        self.moza_torque_curve = self.moza_torque_plot(
                    pen = pg.mkPen(color=(64, 224, 208), width=2), name=R5_TORQUE_SIGNAL_NAME
        )
        self.current_plot.addLegend()
        self.torque_plot.addLegend()
        self.angle_plot.addLegend()

        self.moza_angle_plot.addLegend()
        self.moza_torque_plot.addLegend()

        clear_button = QPushButton("Clear plots")
        clear_button.clicked.connect(self.clear)

        top_layout = QHBoxLayout()
        top_layout.addLayout(value_layout)
        top_layout.addWidget(clear_button)

        plot_layout = QGridLayout()
        plot_layout.addWidget(self.angle_plot, 0, 0)
        plot_layout.addWidget(self.moza_angle_plot, 0, 1)
        plot_layout.addWidget(self.torque_plot, 1, 0)
        plot_layout.addWidget(self.moza_torque_plot, 1, 1)
        plot_layout.addWidget(self.current_plot, 
                            2,
                            0,
                            1,
                            2
        )

        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addLayout(plot_layout, 1)

    @staticmethod
    def _create_plot(
        title: str, y_label: str, units: str
    ) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)
        plot.setLabel("bottom", "Time", units="s")
        plot.setLabel("left", y_label, units=units)
        plot.showGrid(x=True, y=True, alpha=0.25)
        return plot

    def add_sample(
        self,
        angle_rad: float,
        torque: float,
        current_1: float,
        current_2: float,
        moza_angle: float,
        moza_torque: float
    ) -> None:
        current_time = time.monotonic() - self.start_time

        self.time_values.append(current_time)
        self.torque_values.append(torque)
        self.current_1_values.append(current_1)
        self.current_2_values.append(current_2)
        self.angle_values.append(angle_rad)
        self.moza_angle_values.append(moza_angle)
        self.moza_torque_values.append(moza_torque)

        self.torque_value_label.setText(f"Torque: {torque:.3f} Nm")
        self.current_1_value_label.setText(
            f"{CURRENT_PHASE_1_NAME}: {current_1:.3f} A"
        )
        self.current_2_value_label.setText(
            f"{CURRENT_PHASE_2_NAME}: {current_2:.3f} A"
        )
        self.angle_value_label.setText(f"Angle: {angle_rad:.3f} rad")

        self._update_curves()

    def _update_curves(self) -> None:
        if not self.time_values:
            return

        times = list(self.time_values)
        self.current_1_curve.setData(times, list(self.current_1_values))
        self.current_2_curve.setData(times, list(self.current_2_values))
        self.torque_curve.setData(times, list(self.torque_values))
        self.angle_curve.setData(times, list(self.angle_values))
        self.moza_angle_curve.setData(times, list(self.moza_angle_values))
        self.moza_torque_curve.setData(times, list(self.moza_torque_values))

        latest_time = times[-1]
        if latest_time > PLOT_WINDOW_SECONDS:
            minimum_time = latest_time - PLOT_WINDOW_SECONDS
            maximum_time = latest_time
        else:
            minimum_time = 0.0
            maximum_time = PLOT_WINDOW_SECONDS

        self.current_plot.setXRange(minimum_time, maximum_time, padding=0)
        self.torque_plot.setXRange(minimum_time, maximum_time, padding=0)
        self.angle_plot.setXRange(minimum_time, maximum_time, padding=0)
        self.moza_angle_plot.setXRange(minimum_time, maximum_time, padding=0)
        self.moza_torque_plot.setXRange(minimum_time, maximum_time, padding=0)

    def clear(self) -> None:
        self.start_time = time.monotonic()
        self.time_values.clear()
        self.torque_values.clear()
        self.current_1_values.clear()
        self.current_2_values.clear()
        self.angle_values.clear()

        self.current_1_curve.clear()
        self.current_2_curve.clear()
        self.torque_curve.clear()
        self.angle_curve.clear()


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        title = QLabel("CAPT Motor Dashboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        instructions = QLabel(
            "Waiting for UDP data from dSPACE...\n\n"
            f"UDP Address: {UDP_IP}:{UDP_PORT}\n"
            f"Forward Address: {ANGLE_FORWARD_IP}:{ANGLE_FORWARD_PORT}\n"
            f"CAPT Motor Angle Signal: {ANGLE_SIGNAL_NAME}\n"
            f"CAPT Motor Torque Signal: {TORQUE_SIGNAL_NAME}\n"
            f"Current Signals: {CURRENT_PHASE_1_NAME}, {CURRENT_PHASE_2_NAME}"
            f"Moza R5 Motor Angle Signal: {R5_ANGLE_SIGNAL_NAME}\n"
            f"Moza R5 Motor Torque Signal: {R5_TORQUE_SIGNAL_NAME}\n"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addStretch()



class StabilityPage(QWidget):
    """Real-time plotting page for Stability plots"""

    def __init__(self):
        super().__init__()
    def import_image(stab_img_path):
        pass 



class TransparencyPage(QWidget):
    """Real-time plotting page for transparency metrics"""
    def __init__(self):
        super().__init__()
    def import_image(transparency_img_path):
        pass 
    
   
 
 

# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAPT Motor Dashboard")
        self.resize(1100, 800)

        # Hardware & Sockets Initialization
        self.moza_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.wheel = self._init_joystick()

        self.udp_receiver = UdpReceiver(UDP_IP, UDP_PORT)
        self.angle_sender = UdpSender(
            ANGLE_FORWARD_IP, ANGLE_FORWARD_PORT, send_as_binary=True
        )

        self.latest_angle_rad = 0.0
        self.latest_torque = 0.0
        self.latest_current_1 = 0.0
        self.latest_current_2 = 0.0

        #stats fetched by pygame for Moza R5 wheel
        self.latest_angle_moza = 0.0
        self.latest_torque_moza = 0.0 

        self.packet_count = 0
        self.last_packet_time = None

        self.home_page = HomePage()
        self.signal_plot_page = SignalPlotPage()
        self.spring_page = SpringPage()
        self.stability_page = StabilityPage()
        self.transparency_page = TransparencyPage()
        self.capt_page = HomePage()
        self.moza_page = HomePage()

        tabs = QTabWidget()
        tabs.addTab(self.signal_plot_page, "Live Signals")
        tabs.addTab(self.home_page, "Home")
        tabs.addTab(self.moza_page, "Moza R5 specs")
        tabs.addTab(self.stability_page, "Stability Analysis")
        tabs.addTab(self.transparency_page, "Transparency Analysis")
        tabs.addTab(self.capt_page, "CAPT Motor Characterisation Analysis")
        tabs.addTab(self.spring_page, "Virtual Spring Visualization")

        self.setCentralWidget(tabs)

        self.status_label = QLabel(f"Listening on UDP {UDP_IP}:{UDP_PORT}")
        self.statusBar().addPermanentWidget(self.status_label)

        # Timer for receiving incoming dSPACE data
        self.receive_timer = QTimer(self)
        self.receive_timer.timeout.connect(self._receive_udp_data)
        self.receive_timer.start(GUI_UPDATE_PERIOD_MS)

        # Timer for non-blocking Moza R5 hardware polling
        self.moza_timer = QTimer(self)
        self.moza_timer.timeout.connect(self.poll_moza_wheel)
        self.moza_timer.start(20)  # Poll at 50 Hz

    @staticmethod
    def _init_joystick() -> Optional[pygame.joystick.Joystick]:
        """Safely initializes Pygame joystick for the Moza wheel."""
        try:
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                wheel = pygame.joystick.Joystick(0)
                wheel.init()
                print(f"Connected successfully to: {wheel.get_name()}")
                print(
                    f"Streaming steering angle to: {CONTROL_IP}:{CONTROL_PORT}"
                )
                return wheel
            else:
                print("Moza R5 not detected. Application running without racing wheel input.")
                return None
        except Exception as err:
            print(f"Failed to initialize joystick hardware: {err}")
            return None

    def poll_moza_wheel(self) -> None:
        """Asynchronously poll the Moza steering wheel in non-blocking way """
        if self.wheel is None:
            return

        max_wheel_degs = 900.0
        try:
            pygame.event.pump()
            raw_axis = self.wheel.get_axis(0)
            #FETCH ANGLE 
            self.latest_angle_moza = raw_axis * (max_wheel_degs / 2.0)

            # Send raw Little-Endian double to control target
            payload = struct.pack("<d", float(self.latest_angle_moza))
            torque_history = [0.0] * WIDTH

            self.moza_sock.sendto(payload, (CONTROL_IP, CONTROL_PORT))
            #FETCH TORQUE  
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                simulated_ffb_load = abs(raw_axis) 
                self.latest_torque_moza = simulated_ffb_load * MOZA_R5_MAX_TORQUE
                torque_history.append(self.latest_torque_moza)
                if len(torque_history) > WIDTH:
                    torque_history.pop(0)

    
        except Exception as error:
            print(f"Moza polling error: {error}")


    def _receive_udp_data(self) -> None:
        packet = self.udp_receiver.read_latest_packet()

        if packet is None:
            self._update_connection_status()
            return

        # Single-pass signal extraction
        angle_value = self._read_number(packet, ANGLE_SIGNAL_NAME)
        torque_value = self._read_number(packet, TORQUE_SIGNAL_NAME)
        current_1_value = self._read_number(packet, CURRENT_PHASE_1_NAME)
        current_2_value = self._read_number(packet, CURRENT_PHASE_2_NAME)

        if angle_value is not None:
            self.latest_angle_rad = angle_value
            # Forward decoded angle payload
            self.angle_sender.send_angle(self.latest_angle_rad)

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
            moza_angle = self.latest_angle_moza
            moza_torque = self.latest_torque_moza,
        )

        self.spring_page.update_measurements(
            angle_rad=self.latest_angle_rad,
            torque=self.latest_torque,
        )

        self._update_connection_status()

    @staticmethod
    def _read_number(packet: dict, signal_name: str) -> Optional[float]:
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
                f"Waiting for dSPACE on {UDP_IP}:{UDP_PORT}"
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
            f"{status} | Packets: {self.packet_count} | Fwd: Port {ANGLE_FORWARD_PORT}"
        )

    def closeEvent(self, event) -> None:
        self.receive_timer.stop()
        self.moza_timer.stop()
        self.udp_receiver.close()
        self.angle_sender.close()
        try:
            self.moza_sock.close()
        except OSError:
            pass
        pygame.quit()
        event.accept()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()