class TransparencyPage(QWidget):
    """Transparency Analysis tab that automatically loads and displays two images side-by-side."""
    def __init__(self, image_path_1: str, image_path_2: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Transparency Analysis - Automatic Image Comparison")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Horizontal layout to hold the two images side-by-side
        images_layout = QHBoxLayout()

        # Image Label 1
        self.image_label_1 = QLabel()
        self.image_label_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label_1.setMinimumHeight(350)
        self._load_image(image_path_1, self.image_label_1)

        # Image Label 2
        self.image_label_2 = QLabel()
        self.image_label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label_2.setMinimumHeight(350)
        self._load_image(image_path_2, self.image_label_2)

        images_layout.addWidget(self.image_label_1, 1)
        images_layout.addWidget(self.image_label_2, 1)

        layout.addLayout(images_layout, 1)

    @staticmethod
    def _load_image(file_path: str, target_label: QLabel) -> None:
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            target_label.setPixmap(pixmap.scaled(
                target_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
            target_label.setStyleSheet("border: none; background: transparent;")
        else:
            target_label.setText(f"Could not load image from:\n{file_path}")
            target_label.setStyleSheet("border: 2px dashed #374151; color: #ef4444; background: #181b22; border-radius: 8px;")






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
    QScrollArea,
    QFrame,
    QMessageBox,
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

TRANSPARENCY_SIGNAL = "Transparency"
HAPTIC_FIDELITY_SIGNAL = "Haptic Fidelity"

PLOT_WINDOW_SECONDS = 10.0
GUI_UPDATE_PERIOD_MS = 20  # 50 Hz UI Refresh Rate
MOZA_R5_MAX_TORQUE = 5.5  # Nm

# ---------------------------------------------------------------------------
# Modern Professional Styling Sheet (Sleek Dark/Slate Theme)
# ---------------------------------------------------------------------------

MODERN_STYLE_SHEET = """
QMainWindow {
    background-color: #121418;
}
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    color: #e1e4e8;
    background-color: #121418;
}
QTabWidget::pane {
    border: 1px solid #2b313b;
    background: #181b22;
    border-radius: 8px;
}
QTabBar::tab {
    background: #1f242d;
    color: #8b949e;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background: #2563eb;
    color: #ffffff;
    font-weight: 600;
}
QTabBar::tab:hover:not(:selected) {
    background: #2d3442;
    color: #c9d1d9;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton#ClearButton, QPushButton#SaveButton {
    background-color: #374151;
    color: #f3f4f6;
    border: 1px solid #4b5563;
}
QPushButton#ClearButton:hover, QPushButton#SaveButton:hover {
    background-color: #4b5563;
}
QLabel {
    color: #e1e4e8;
}
QDoubleSpinBox {
    background-color: #1f242d;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 4px 8px;
    color: #ffffff;
}
QStatusBar {
    background: #0d1117;
    color: #8b949e;
    border-top: 1px solid #21262d;
}
"""

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
    
    def __init__(self, receiver: Optional[UdpReceiver], sender: Optional[UdpSender]):
        super().__init__()
        self.receiver = receiver
        self.sender = sender
        self._is_running = True
        self.buffer_lock = Lock()
        self.latest_packet: Optional[dict] = None

    def run(self) -> None:
        while self._is_running:
            if self.receiver is not None:
                packet = self.receiver.read_latest_packet()
                if packet is not None:
                    angle_val = packet.get(ANGLE_SIGNAL_NAME)
                    if angle_val is not None and self.sender is not None:
                        try:
                            numeric_angle = float(angle_val)
                            if math.isfinite(numeric_angle):
                                self.sender.send_angle(numeric_angle)
                        except (TypeError, ValueError):
                            pass

                    with self.buffer_lock:
                        self.latest_packet = packet
                else:
                    QThread.msleep(5)
            else:
                QThread.msleep(100)

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
        self.kappa = 43.91
        self.setMinimumHeight(300)

        self._axis_pen = QPen(QColor(140, 140, 140), 1, Qt.PenStyle.DashLine)
        self._wall_pen = QPen(QColor(100, 110, 120), 5)
        self._handle_pen = QPen(QColor(37, 99, 235), 8)
        self._text_color = QColor(225, 228, 232)

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
        painter.setPen(QPen(QColor(180, 180, 180), 3))
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
        painter.setPen(QPen(QColor(239, 68, 68), 3))
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
        self.kappa_input.setRange(0.0, 200.0)
        self.kappa_input.setDecimals(2)
        self.kappa_input.setSingleStep(1.0)
        self.kappa_input.setValue(43.91)
        self.kappa_input.setSuffix(" Nm/rad")

        reset_button = QPushButton("Reset reference")
        reset_button.setObjectName("ClearButton")
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
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.image_label = QLabel("No stability photo loaded. Click below to import evaluation plots or schematics.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #374151; color: #9ca3af; background: #181b22; border-radius: 8px;")
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


class TransferFunctionPage(QWidget):
    """Dedicated Transfer Function & Frequency Response page for system characterization."""
    def __init__(self, title_text: str, description_text: str, default_tf_eq: str, J: float, b: float, kappa: float, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        
        desc = QLabel(description_text)
        desc.setStyleSheet("color: #9ca3af; font-size: 13px;")

        eq_frame = QFrame()
        eq_frame.setStyleSheet("background-color: #181b22; border: 1px solid #2b313b; border-radius: 6px; padding: 10px;")
        eq_layout = QVBoxLayout(eq_frame)
        eq_title = QLabel("System Transfer Function Model: G(s)")
        eq_title.setStyleSheet("font-weight: bold; color: #60a5fa;")
        eq_content = QLabel(default_tf_eq)
        eq_content.setStyleSheet("font-family: Consolas, monospace; font-size: 14px; color: #e1e4e8;")
        eq_layout.addWidget(eq_title)
        eq_layout.addWidget(eq_content)

        plot_layout = QHBoxLayout()
        self.mag_plot = self._create_plot("Bode Magnitude Response", "Gain", "dB")
        self.phase_plot = self._create_plot("Bode Phase Response", "Phase", "°")
        
        plot_layout.addWidget(self.mag_plot)
        plot_layout.addWidget(self.phase_plot)

        frequencies = np.logspace(-1, 3, 200)
        omega = 2 * np.pi * frequencies
        
        real_part = kappa - J * (omega**2)
        imag_part = b * omega
        
        mag_val = 1.0 / np.sqrt(real_part**2 + imag_part**2)
        mag = 20 * np.log10(mag_val / mag_val[0])
        phase = -np.arctan2(imag_part, real_part) * (180 / np.pi)

        self.mag_plot.plot(frequencies, mag, pen=pg.mkPen(color=(37, 99, 235), width=2))
        self.phase_plot.plot(frequencies, phase, pen=pg.mkPen(color=(168, 85, 247), width=2))
        
        for p in [self.mag_plot, self.phase_plot]:
            p.setLogMode(x=True, y=False)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(eq_frame)
        layout.addLayout(plot_layout, 1)

    @staticmethod
    def _create_plot(title: str, y_label: str, units: str) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)
        plot.setBackground('#181b22')
        plot.setLabel("bottom", "Frequency", units="Hz")
        plot.setLabel("left", y_label, units=units)
        plot.showGrid(x=True, y=True, alpha=0.15)
        return plot


class TransparencyPage(QWidget):
    """Transparency Analysis tab with live interactive plots."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = time.monotonic()
        max_pts = int(PLOT_WINDOW_SECONDS * 1000 / GUI_UPDATE_PERIOD_MS) + 100

        self.time_values = deque(maxlen=max_pts)
        self.transparency_values = deque(maxlen=max_pts)
        self.haptic_fidelity_values = deque(maxlen=max_pts)

        self.transparency_plot = self._create_plot("Transparency Analysis", "Transparency Index", "")
        self.fidelity_plot = self._create_plot("Haptic Fidelity Analysis", "Fidelity Score", "%")

        self.transparency_curve = self.transparency_plot.plot(pen=pg.mkPen(color=(0, 200, 100), width=2), name=TRANSPARENCY_SIGNAL)
        self.fidelity_curve = self.fidelity_plot.plot(pen=pg.mkPen(color=(150, 50, 255), width=2), name=HAPTIC_FIDELITY_SIGNAL)

        save_button = QPushButton("Save Transparency Plots")
        save_button.setObjectName("SaveButton")
        save_button.clicked.connect(self.save_plots_to_csv)

        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(save_button)

        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.transparency_plot)
        plot_layout.addWidget(self.fidelity_plot)

        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addLayout(plot_layout, 1)

    @staticmethod
    def _create_plot(title: str, y_label: str, units: str) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)
        plot.setBackground('#181b22')
        plot.setLabel("bottom", "Time", units="s")
        plot.setLabel("left", y_label, units=units)
        plot.showGrid(x=True, y=True, alpha=0.15)
        return plot

    def add_sample(self, torque_val: float, angle_val: float) -> None:
        t = time.monotonic() - self.start_time
        self.time_values.append(t)

        syn_transparency = max(0.0, 1.0 - abs(angle_val) * 0.05)
        syn_fidelity = min(100.0, max(0.0, 50.0 + torque_val * 10.0))

        self.transparency_values.append(syn_transparency)
        self.haptic_fidelity_values.append(syn_fidelity)

        self._update_curves()

    def _update_curves(self) -> None:
        if not self.time_values:
            return

        times = np.fromiter(self.time_values, dtype=float)
        self.transparency_curve.setData(times, np.fromiter(self.transparency_values, dtype=float))
        self.fidelity_curve.setData(times, np.fromiter(self.haptic_fidelity_values, dtype=float))

        latest_time = times[-1]
        min_time = max(0.0, latest_time - PLOT_WINDOW_SECONDS)
        max_time = max(PLOT_WINDOW_SECONDS, latest_time)

        for pw in [self.transparency_plot, self.fidelity_plot]:
            pw.setXRange(min_time, max_time, padding=0)

    def save_plots_to_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Transparency Data", "transparency_data.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Time(s),Transparency,HapticFidelity\n")
                    for t, tr, hf in zip(self.time_values, self.transparency_values, self.haptic_fidelity_values):
                        f.write(f"{t:.4f},{tr:.4f},{hf:.4f}\n")
            except Exception as e:
                print(f"Error saving file: {e}")


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
        clear_button.setObjectName("ClearButton")
        clear_button.clicked.connect(self.clear)

        save_button = QPushButton("Save Live Data (.csv)")
        save_button.setObjectName("SaveButton")
        save_button.clicked.connect(self.save_plots_to_csv)

        top_layout = QHBoxLayout()
        top_layout.addLayout(value_layout)
        top_layout.addWidget(save_button)
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
        plot.setBackground('#181b22')
        plot.setLabel("bottom", "Time", units="s")
        plot.setLabel("left", y_label, units=units)
        plot.showGrid(x=True, y=True, alpha=0.15)
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

    def save_plots_to_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Live Signals Data", "live_signals.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Time(s),Torque,Current1,Current2,AngleRad,MozaAngle,MozaTorque\n")
                    for t, tr, c1, c2, ang, mang, mtor in zip(
                        self.time_values, self.torque_values, self.current_1_values, 
                        self.current_2_values, self.angle_values, self.moza_angle_values, self.moza_torque_values
                    ):
                        f.write(f"{t:.4f},{tr:.4f},{c1:.4f},{c2:.4f},{ang:.4f},{mang:.4f},{mtor:.4f}\n")
            except Exception as e:
                print(f"Error saving data: {e}")

    def clear(self) -> None:
        self.start_time = time.monotonic()
        for q in [self.time_values, self.torque_values, self.current_1_values, self.current_2_values, self.angle_values, self.moza_angle_values, self.moza_torque_values]:
            q.clear()
        for c in [self.current_1_curve, self.current_2_curve, self.torque_curve, self.angle_curve, self.moza_angle_curve, self.moza_torque_curve]:
            c.clear()


class HomePage(QWidget):
    """Informative, professional dashboard overview home page."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("CAPT Motor Real-Time Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        
        subtitle = QLabel("High-performance telemetry, haptic steering characterization, and controller analysis suite.")
        subtitle.setStyleSheet("font-size: 14px; color: #8b949e;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        card1 = self._create_info_card("System Status", f"Listening for dSPACE packets on UDP:\n{UDP_IP}:{UDP_PORT}\n\nForwarding Target:\n{ANGLE_FORWARD_IP}:{ANGLE_FORWARD_PORT}")
        card2 = self._create_info_card("Hardware Integration", f"Control Target Address:\n{CONTROL_IP}:{CONTROL_PORT}\n\nMax Wheel Torque Output:\n{MOZA_R5_MAX_TORQUE} Nm (Moza R5)")
        card3 = self._create_info_card("Active Telemetry Signals", f"• Steering Angle: {ANGLE_SIGNAL_NAME}\n• Motor Torque: {TORQUE_SIGNAL_NAME}\n• Phase Currents: {CURRENT_PHASE_1_NAME}, {CURRENT_PHASE_2_NAME}")
        card4 = self._create_info_card("Analysis Modules", "• Live Signals & Plot Export (.csv)\n• Stability Photo Import & Review\n• Real-Time Transparency Metrics\n• Virtual Spring Dynamic Simulator\n• Transfer Function Frequency Analyses")

        grid_layout.addWidget(card1, 0, 0)
        grid_layout.addWidget(card2, 0, 1)
        grid_layout.addWidget(card3, 1, 0)
        grid_layout.addWidget(card4, 1, 1)

        layout.addLayout(grid_layout)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    @staticmethod
    def _create_info_card(title_text: str, body_text: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #181b22;
                border: 1px solid #2b313b;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        v_layout = QVBoxLayout(card)
        
        t_label = QLabel(title_text)
        t_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #60a5fa; margin-bottom: 8px;")
        
        b_label = QLabel(body_text)
        b_label.setStyleSheet("font-size: 13px; color: #c9d1d9; line-height: 140%;")
        b_label.setWordWrap(True)

        v_layout.addWidget(t_label)
        v_layout.addWidget(b_label)
        return card


class MainWindow(QMainWindow):
    """Main application window tying together all modules and the background UDP loop."""
    def __init__(self, udp_worker: UdpWorkerThread):
        super().__init__()
        self.udp_worker = udp_worker
        self.setWindowTitle("CAPT Motor & Haptic Interface Telemetry Suite")
        self.resize(1300, 850)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.home_page = HomePage()
        self.signals_page = SignalPlotPage()
        self.spring_page = SpringPage()
        self.stability_page = StabilityPage()
        self.transparency_page = TransparencyPage()
        
        self.tf_page = TransferFunctionPage(
            title_text="CAPT Motor Characterisation",
            description_text="Frequency response analysis based on identified second-order mechanical properties.",
            default_tf_eq="G(s) = 1 / (0.0103 s^2 + 9.31 s + 43.91)",
            J=0.0103, b=9.31, kappa=43.91
        )

        self.tabs.addTab(self.home_page, "Dashboard")
        self.tabs.addTab(self.signals_page, "Live Signals")
        self.tabs.addTab(self.spring_page, "Virtual Spring")
        self.tabs.addTab(self.tf_page, "CAPT Characterisation")
        self.tabs.addTab(self.transparency_page, "Transparency Analysis")
        self.tabs.addTab(self.stability_page, "Stability Evaluation")

        self.timer = QTimer(self)
        self.timer.setInterval(GUI_UPDATE_PERIOD_MS)
        self.timer.timeout.connect(self.process_incoming_packet)
        self.timer.start()

    def process_incoming_packet(self) -> None:
        packet = self.udp_worker.get_latest_packet()
        
        # If no UDP stream is live, fallback to default/zeroed data so the UI runs smoothly
        if packet is None:
            angle_val = 0.0
            torque_val = 0.0
            curr_1 = 0.0
            curr_2 = 0.0
            moza_angle = 0.0
            moza_torque = 0.0
        else:
            angle_val = float(packet.get(ANGLE_SIGNAL_NAME, 0.0))
            torque_val = float(packet.get(TORQUE_SIGNAL_NAME, 0.0))
            curr_1 = float(packet.get(CURRENT_PHASE_1_NAME, 0.0))
            curr_2 = float(packet.get(CURRENT_PHASE_2_NAME, 0.0))
            moza_angle = float(packet.get(R5_ANGLE_SIGNAL_NAME, 0.0))
            moza_torque = float(packet.get(R5_TORQUE_SIGNAL_NAME, 0.0))

        self.signals_page.add_sample(angle_val, torque_val, curr_1, curr_2, moza_angle, moza_torque)
        self.spring_page.update_measurements(angle_val, torque_val)
        self.transparency_page.add_sample(torque_val, angle_val)

    def closeEvent(self, event) -> None:
        self.udp_worker.stop()
        event.accept()


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE_SHEET)

    receiver = None
    sender = None

    try:
        receiver = UdpReceiver(UDP_IP, UDP_PORT)
        sender = UdpSender(ANGLE_FORWARD_IP, ANGLE_FORWARD_PORT)
    except OSError as e:
        print(f"Warning: Could not bind to UDP port {UDP_PORT}: {e}")
        # Continue executing without crashing so the GUI can still open for review/testing

    udp_worker = UdpWorkerThread(receiver, sender)
    udp_worker.start()

    window = MainWindow(udp_worker)
    window.show()

    exit_code = app.exec()

    udp_worker.stop()
    if receiver:
        receiver.close()
    if sender:
        sender.close()
    sys.exit(exit_code)
