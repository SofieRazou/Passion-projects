import json
import math
import socket
import struct
import sys
import time
from collections import deque
from threading import Lock
from typing import Optional
import numpy as np
import pyqtgraph as pg
import pygame
from PyQt6.QtCore import QPointF, Qt, QTimer, QThread
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
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

ANGLE_SIGNAL_NAME = "Out1"
TORQUE_SIGNAL_NAME = "Torque"
CURRENT_PHASE_1_NAME = "AO_ch8"
CURRENT_PHASE_2_NAME = "AO_ch16"

R5_TORQUE_SIGNAL_NAME = "Moza R5 Torque"
R5_ANGLE_SIGNAL_NAME = "Moza R5 Angle"

PLOT_WINDOW_SECONDS = 10.0
GUI_UPDATE_PERIOD_MS = 20  # 50 Hz UI Refresh Rate
MOZA_R5_MAX_TORQUE = 5.5  # Nm

# ---------------------------------------------------------------------------
# Socket Communication Classes & Background Worker
# ---------------------------------------------------------------------------

class UdpReceiver:
    """Non-blocking UDP receiver for dSPACE JSON packets."""

    def __init__(self, ip: str, port: int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.setblocking(False)

    def read_latest_packet(self) -> Optional[dict]:
        latest_packet = None
        while True:
            try:
                raw_data, _sender = self.socket.recvfrom(65535)
            except (BlockingIOError, OSError):
                break

            try:
                packet = json.loads(raw_data.decode("utf-8"))
                if isinstance(packet, dict):
                    latest_packet = packet
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
        return latest_packet

    def close(self) -> None:
        try:
            self.socket.close()
        except OSError:
            pass


class UdpSender:
    """UDP sender for forwarding signals."""

    def __init__(self, ip: str, port: int, send_as_binary: bool = True):
        self.ip = ip
        self.port = port
        self.send_as_binary = send_as_binary
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_angle(self, angle: float) -> None:
        data = struct.pack("<d", float(angle)) if self.send_as_binary else json.dumps({"angle": angle}).encode("utf-8")
        try:
            self.socket.sendto(data, (self.ip, self.port))
        except OSError:
            pass

    def close(self) -> None:
        try:
            self.socket.close()
        except OSError:
            pass


class UdpWorkerThread(QThread):
    """Background thread handling high-frequency socket polling safely."""
    
    def __init__(self, receiver: UdpReceiver, sender: UdpSender):
        super().__init__()
        self.receiver = receiver
        self.sender = sender
        self._is_running = True
        self.buffer_lock = Lock()
        self.latest_packet: Optional[dict] = None

    def run(self) -> None:
        while self._is_running:
            packet = self.receiver.read_latest_packet()
            if packet is not None:
                angle_val = packet.get(ANGLE_SIGNAL_NAME)
                if angle_val is not None:
                    try:
                        numeric_angle = float(angle_val)
                        if math.isfinite(numeric_angle):
                            self.sender.send_angle(numeric_angle)
                    except (TypeError, ValueError):
                        pass

                with self.buffer_lock:
                    self.latest_packet = packet
            else:
                QThread.msleep(1)

    def get_latest_packet(self) -> Optional[dict]:
        with self.buffer_lock:
            pkt = self.latest_packet
            self.latest_packet = None  
            return pkt

    def stop(self) -> None:
        self._is_running = False
        self.wait()


# ---------------------------------------------------------------------------
# UI Widgets & Visualization Pages
# ---------------------------------------------------------------------------

class SpringWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle_rad = 0.0
        self.measured_torque = 0.0
        self.reference_angle_rad = 0.0
        self.kappa = 1.0
        self.setMinimumHeight(300)

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

        width, height = self.width(), self.height()
        center_y, fixed_x = height * 0.52, width * 0.12
        max_visual_displacement, maximum_angle = width * 0.28, math.radians(30)

        normalized_angle = max(-1.0, min(1.0, self.angle_rad / maximum_angle))
        equilibrium_x = width * 0.52
        handle_x = equilibrium_x + (normalized_angle * max_visual_displacement)

        painter.setPen(self._axis_pen)
        painter.drawLine(QPointF(equilibrium_x, center_y - 80), QPointF(equilibrium_x, center_y + 80))

        painter.setPen(self._wall_pen)
        painter.drawLine(QPointF(fixed_x, center_y - 75), QPointF(fixed_x, center_y + 75))

        self._draw_spring(painter, QPointF(fixed_x, center_y), QPointF(handle_x, center_y), 12, 22)

        painter.setPen(self._handle_pen)
        painter.drawLine(QPointF(handle_x, center_y - 60), QPointF(handle_x, center_y + 60))

        self._draw_torque_arrow(painter, QPointF(handle_x, center_y - 95), self.measured_torque)

        painter.setPen(self._text_color)
        painter.drawText(20, 30, f"Measured angle: {math.degrees(self.angle_rad):.2f}°")
        painter.drawText(20, 55, f"Reference: {math.degrees(self.reference_angle_rad):.2f}°")
        painter.drawText(20, 80, f"Kappa: {self.kappa:.3f} Nm/rad")
        painter.drawText(20, 105, f"Measured torque: {self.measured_torque:.3f} Nm")
        painter.drawText(20, 130, f"Calculated spring torque: {self.spring_torque():.3f} Nm")

    @staticmethod
    def _draw_spring(painter: QPainter, start: QPointF, end: QPointF, coils: int, amplitude: float) -> None:
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        lead_length = 20.0
        usable_start_x, usable_end_x = start.x() + lead_length, end.x() - lead_length

        if usable_end_x <= usable_start_x:
            painter.drawLine(start, end)
            return

        points = [start, QPointF(usable_start_x, start.y())]
        num_segs = coils * 2
        spring_length = usable_end_x - usable_start_x

        for index in range(num_segs + 1):
            ratio = index / num_segs
            x = usable_start_x + ratio * spring_length
            y = start.y() if index in (0, num_segs) else (start.y() - amplitude if index % 2 else start.y() + amplitude)
            points.append(QPointF(x, y))

        points.extend([QPointF(usable_end_x, end.y()), end])
        painter.drawPolyline(QPolygonF(points))

    @staticmethod
    def _draw_torque_arrow(painter: QPainter, origin: QPointF, torque: float) -> None:
        if abs(torque) < 1e-6:
            return
        direction = 1 if torque > 0 else -1
        painter.setPen(QPen(QColor(190, 70, 50), 3))
        end = QPointF(origin.x() + direction * 65, origin.y())
        painter.drawLine(origin, end)
        painter.drawLine(end, QPointF(end.x() - direction * 10, end.y() - 10))
        painter.drawLine(end, QPointF(end.x() - direction * 10, end.y() + 10))


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
        reset_button.clicked.connect(lambda: self.spring_view.set_reference_angle(self.spring_view.angle_rad))

    def update_measurements(self, angle_rad: float, torque: float) -> None:
        self.spring_view.set_angle(angle_rad)
        self.spring_view.set_measured_torque(torque)
        self.angle_label.setText(f"Measured angle: {math.degrees(angle_rad):.3f}°")
        self.torque_label.setText(f"Measured torque: {torque:.3f} Nm")


class StabilityPage(QWidget):
    """Stability Analysis tab with feature to import and display a photo from the PC."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.image_label = QLabel("No stability photo loaded. Click below to add one.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #aaa; color: #666; background: #f9f9f9;")
        self.image_label.setMinimumHeight(400)

        load_button = QPushButton("Load Stability Photo from PC")
        load_button.clicked.connect(self.load_photo)

        layout.addWidget(self.image_label, 1)
        layout.addWidget(load_button)

    def load_photo(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Stability Image", "", "Image Files (*.png *.jpg *.bmp *.jpeg)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                ))
                self.image_label.setStyleSheet("border: none; background: transparent;")


class SignalPlotPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = time.monotonic()
        max_pts = int(PLOT_WINDOW_SECONDS * 1000 / GUI_UPDATE_PERIOD_MS) + 100

        self.time_values = deque(maxlen=max_pts)
        self.torque_values = deque(maxlen=max_pts)
        self.current_1_values = deque(maxlen=max_pts)
        self.current_2_values = deque(maxlen=max_pts)
        self.angle_values = deque(maxlen=max_pts)
        self.moza_angle_values = deque(maxlen=max_pts)
        self.moza_torque_values = deque(maxlen=max_pts)

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

        self.current_plot = self._create_plot("Commanded currents", "Current", "A")
        self.torque_plot = self._create_plot("Measured CAPT Motor Torque", "Torque", "Nm")
        self.angle_plot = self._create_plot("Measured CAPT Motor steering angle", "Angle", "degrees")
        self.moza_angle_plot = self._create_plot("Measured Moza R5 Angle", "Moza R5 Angle", "degrees")
        self.moza_torque_plot = self._create_plot("Measured Moza R5 Torque", "Moza R5 Torque", "Nm")

        self.current_1_curve = self.current_plot.plot(pen=pg.mkPen(width=2), name=CURRENT_PHASE_1_NAME)
        self.current_2_curve = self.current_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name=CURRENT_PHASE_2_NAME)
        self.torque_curve = self.torque_plot.plot(pen=pg.mkPen(color=(255, 0, 255), width=2), name=TORQUE_SIGNAL_NAME)
        self.angle_curve = self.angle_plot.plot(pen=pg.mkPen(color=(64, 224, 208), width=2), name=ANGLE_SIGNAL_NAME)
        self.moza_angle_curve = self.moza_angle_plot.plot(pen=pg.mkPen(color=(64, 224, 208), width=2), name=R5_ANGLE_SIGNAL_NAME)
        self.moza_torque_curve = self.moza_torque_plot.plot(pen=pg.mkPen(color=(64, 224, 208), width=2), name=R5_TORQUE_SIGNAL_NAME)

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
        plot_layout.addWidget(self.current_plot, 2, 0, 1, 2)

        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addLayout(plot_layout, 1)

    @staticmethod
    def _create_plot(title: str, y_label: str, units: str) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)
        plot.setLabel("bottom", "Time", units="s")
        plot.setLabel("left", y_label, units=units)
        plot.showGrid(x=True, y=True, alpha=0.25)
        return plot

    def add_sample(self, angle_rad: float, torque: float, current_1: float, current_2: float, moza_angle: float, moza_torque: float) -> None:
        t = time.monotonic() - self.start_time
        self.time_values.append(t)
        self.torque_values.append(torque)
        self.current_1_values.append(current_1)
        self.current_2_values.append(current_2)
        self.angle_values.append(angle_rad)
        self.moza_angle_values.append(moza_angle)
        self.moza_torque_values.append(moza_torque)

        self.torque_value_label.setText(f"Torque: {torque:.3f} Nm")
        self.current_1_value_label.setText(f"{CURRENT_PHASE_1_NAME}: {current_1:.3f} A")
        self.current_2_value_label.setText(f"{CURRENT_PHASE_2_NAME}: {current_2:.3f} A")
        self.angle_value_label.setText(f"Angle: {angle_rad:.3f} rad")

        self._update_curves()

    def _update_curves(self) -> None:
        if not self.time_values:
            return

        # Optimized direct NumPy array translation to bypass overhead
        times = np.fromiter(self.time_values, dtype=float)
        
        self.current_1_curve.setData(times, np.fromiter(self.current_1_values, dtype=float))
        self.current_2_curve.setData(times, np.fromiter(self.current_2_values, dtype=float))
        self.torque_curve.setData(times, np.fromiter(self.torque_values, dtype=float))
        self.angle_curve.setData(times, np.fromiter(self.angle_values, dtype=float))
        self.moza_angle_curve.setData(times, np.fromiter(self.moza_angle_values, dtype=float))
        self.moza_torque_curve.setData(times, np.fromiter(self.moza_torque_values, dtype=float))

        latest_time = times[-1]
        min_time = max(0.0, latest_time - PLOT_WINDOW_SECONDS)
        max_time = max(PLOT_WINDOW_SECONDS, latest_time)

        for pw in [self.current_plot, self.torque_plot, self.angle_plot, self.moza_angle_plot, self.moza_torque_plot]:
            pw.setXRange(min_time, max_time, padding=0)

    def clear(self) -> None:
        self.start_time = time.monotonic()
        for q in [self.time_values, self.torque_values, self.current_1_values, self.current_2_values, self.angle_values, self.moza_angle_values, self.moza_torque_values]:
            q.clear()
        for c in [self.current_1_curve, self.current_2_curve, self.torque_curve, self.angle_curve, self.moza_angle_curve, self.moza_torque_curve]:
            c.clear()


class HomePage(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        title = QLabel(text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions = QLabel(
            "Waiting for UDP data from dSPACE...\n\n"
            f"UDP Address: {UDP_IP}:{UDP_PORT}\n"
            f"Forward Address: {ANGLE_FORWARD_IP}:{ANGLE_FORWARD_PORT}\n"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addStretch()


# ---------------------------------------------------------------------------
# Main Window & Update Loops
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAPT Motor Dashboard")
        self.resize(1100, 800)

        self.moza_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.wheel = self._init_joystick()

        self.udp_receiver = UdpReceiver(UDP_IP, UDP_PORT)
        self.angle_sender = UdpSender(ANGLE_FORWARD_IP, ANGLE_FORWARD_PORT, send_as_binary=True)

        self.udp_worker = UdpWorkerThread(self.udp_receiver, self.angle_sender)
        self.udp_worker.start()

        self.latest_angle_rad = 0.0
        self.latest_torque = 0.0
        self.latest_current_1 = 0.0
        self.latest_current_2 = 0.0
        self.latest_angle_moza = 0.0
        self.latest_torque_moza = 0.0

        self.packet_count = 0
        self.last_packet_time = None

        self.signal_plot_page = SignalPlotPage()
        self.spring_page = SpringPage()
        self.stability_page = StabilityPage()

        tabs = QTabWidget()
        tabs.addTab(self.signal_plot_page, "Live Signals")
        tabs.addTab(HomePage("CAPT Motor Dashboard"), "Home")
        tabs.addTab(HomePage("Moza R5 specs"), "Moza R5 specs")
        tabs.addTab(self.stability_page, "Stability Analysis")
        tabs.addTab(QWidget(), "Transparency Analysis")
        tabs.addTab(HomePage("CAPT Motor Characterisation Analysis"), "CAPT Motor Characterisation Analysis")
        tabs.addTab(self.spring_page, "Virtual Spring Visualization")
        self.setCentralWidget(tabs)

        self.status_label = QLabel(f"Listening on UDP {UDP_IP}:{UDP_PORT}")
        self.statusBar().addPermanentWidget(self.status_label)

        self.gui_timer = QTimer(self)
        self.gui_timer.timeout.connect(self._process_gui_tick)
        self.gui_timer.start(GUI_UPDATE_PERIOD_MS)

    @staticmethod
    def _init_joystick() -> Optional[pygame.joystick.Joystick]:
        try:
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                wheel = pygame.joystick.Joystick(0)
                wheel.init()
                return wheel
        except Exception:
            pass
        return None

    def _process_gui_tick(self) -> None:
        packet = self.udp_worker.get_latest_packet()
        if packet is not None:
            self.packet_count += 1
            self.last_packet_time = time.monotonic()

            if (val := self._read_number(packet, ANGLE_SIGNAL_NAME)) is not None:
                self.latest_angle_rad = val
            if (val := self._read_number(packet, TORQUE_SIGNAL_NAME)) is not None:
                self.latest_torque = val
            if (val := self._read_number(packet, CURRENT_PHASE_1_NAME)) is not None:
                self.latest_current_1 = val
            if (val := self._read_number(packet, CURRENT_PHASE_2_NAME)) is not None:
                self.latest_current_2 = val

        if self.wheel is not None:
            try:
                pygame.event.pump()
                raw_axis = self.wheel.get_axis(0)
                self.latest_angle_moza = raw_axis * 450.0
                self.latest_torque_moza = abs(raw_axis) * MOZA_R5_MAX_TORQUE
                self.moza_sock.sendto(struct.pack("<d", self.latest_angle_moza), (CONTROL_IP, CONTROL_PORT))
            except Exception:
                pass

        self.signal_plot_page.add_sample(
            self.latest_angle_rad, self.latest_torque,
            self.latest_current_1, self.latest_current_2,
            self.latest_angle_moza, self.latest_torque_moza
        )
        self.spring_page.update_measurements(self.latest_angle_rad, self.latest_torque)
        self._update_connection_status()

    @staticmethod
    def _read_number(packet: dict, signal_name: str) -> Optional[float]:
        try:
            val = float(packet.get(signal_name))
            return val if math.isfinite(val) else None
        except (TypeError, ValueError):
            return None

    def _update_connection_status(self) -> None:
        if self.last_packet_time is None:
            self.status_label.setText(f"Waiting for dSPACE on {UDP_IP}:{UDP_PORT}")
            return
        elapsed = time.monotonic() - self.last_packet_time
        status = "Receiving" if elapsed < 1.0 else ("No recent packets" if elapsed < 3.0 else "Connection inactive")
        self.status_label.setText(f"{status} | Packets: {self.packet_count}")

    def closeEvent(self, event) -> None:
        self.udp_worker.stop()
        self.udp_receiver.close()
        self.angle_sender.close()
        try:
            self.moza_sock.close()
        except OSError:
            pass
        pygame.quit()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
