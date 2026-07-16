# import sys
# import numpy as np
# from multiprocessing import shared_memory

# from numpy.compat import Path

# import pyqtgraph as pg
# from PyQt6 import QtCore 
# from PyQt6.QtCore import Qt
# from PyQt6.QtGui import QAction, QPixmap
# from PyQt6.QtWidgets import (
#     QApplication, QMainWindow, QPushButton, QWidget,
#     QTabWidget, QVBoxLayout, QToolBar, QLabel
# )

# from matplotlib.figure import Figure 
# import scipy.io as sio
# import control as ct 
# from control.matlab import ss, bode
# import pandas as pd 

# NUM_SIGNALS = 6
# HISTORY_SIZE = 300
# UPDATE_PERIOD = 0.05

# MEM_NAME = "shared_mem"
# DTYPE = np.float32

# MATNAME = "stability_plots.csv"
# BODE_FILE = "bode_plot.png"

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("CAPT Motor Dashboard")

#         self.sm = shared_memory.SharedMemory(name=MEM_NAME, create=False)

#         self.mem_rec_data = np.ndarray(
#             (NUM_SIGNALS,),
#             dtype=DTYPE,
#             buffer=self.sm.buf
#         )

#         self.tabs = QTabWidget()
#         self.setCentralWidget(self.tabs)

#         self.home_page = QWidget()
#         self.stats_page = QWidget()
#         self.stability_page = QWidget()
#         self.debug_page = QWidget()

#         self.tabs.addTab(self.home_page, "Measurements")
#         self.tabs.addTab(self.stats_page, "Impedance / Admittance")
#         self.tabs.addTab(self.stability_page, "Stability Analysis")
#         self.tabs.addTab(self.debug_page, "Debugging")

#         self.home_layout = QVBoxLayout(self.home_page)
#         self.stats_layout = QVBoxLayout(self.stats_page)
#         self.stability_layout = QVBoxLayout(self.stability_page)
#         self.debug_layout = QVBoxLayout(self.debug_page)

#         toolbar = QToolBar("Actions")
#         self.addToolBar(toolbar)

#         home_action = QAction("Measurements", self)
#         home_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
#         toolbar.addAction(home_action)

#         stats_action = QAction("Impedance / Admittance", self)
#         stats_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
#         toolbar.addAction(stats_action)

#         stability_action = QAction("Stability Analysis", self)
#         stability_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
#         toolbar.addAction(stability_action)

#         debug_action = QAction("Debugging", self)
#         debug_action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
#         toolbar.addAction(debug_action)

#         self.start_button = QPushButton("Start CAPT Motor recording measurements")
#         self.start_button.setCheckable(True)
#         self.start_button.clicked.connect(self.rec_meas)
#         self.home_layout.addWidget(self.start_button)

#         # First tab: angle, torque, phase currents
#         self.graph_layout = pg.GraphicsLayoutWidget()
#         self.home_layout.addWidget(self.graph_layout)

#         self.angle_plot = self.graph_layout.addPlot(row=0, col=0, title="Angle (deg)")
#         self.torque_plot = self.graph_layout.addPlot(row=0, col=1, title="Torque (Nm)")
#         self.phase1_plot = self.graph_layout.addPlot(row=1, col=0, title="Current Phase 1 (A)")
#         self.phase2_plot = self.graph_layout.addPlot(row=1, col=1, title="Current Phase 2 (A)")


#         # Second tab: impedance and admittance
#         self.stats_graph_layout = pg.GraphicsLayoutWidget()
#         self.stats_layout.addWidget(self.stats_graph_layout)

#         self.impedance_plot = self.stats_graph_layout.addPlot(row=0, col=0, title="Impedance")
#         self.admittance_plot = self.stats_graph_layout.addPlot(row=1, col=0, title="Admittance")


#         self.stability_title = QLabel("Bode Plot and Stability Analysis")
#         self.stability_title.setAlignment(
#             Qt.AlignmentFlag.AlignCenter
#         )
    
#         self.stability_title.setObjectName("stabilityTitle")

#         self.stability_plot = QLabel()
#         self.stability_plot.setObjectName("stabilityImage")
#         self.stability_plot.setMinimumSize(600, 450)
#         self.stability_plot.setAlignment(
#             Qt.AlignmentFlag.AlignCenter
#         )
       

#         self.stability_layout.addWidget(self.stability_title)
#         self.stability_layout.addWidget(
#             self.stability_plot,
#             stretch=1
#         )
#         bode_path = Path(BODE_FILE).resolve().as_posix()

#         self.setStyleSheet(
#             f"""
#             QLabel#stabilityTitle {{
#                 font-size: 20px;
#                 font-weight: bold;
#                 padding: 10px;
#             }}

#             QLabel#stabilityImage {{
#                 border-image: url("{bode_path}") 0 0 0 0 stretch stretch;
#                 background-color: white;
#                 border: 1px solid #808080;
#                 border-radius: 5px;
#                 margin: 10px;
#             }}
#             """
#         )
#         all_plots = [
#             self.angle_plot,
#             self.torque_plot,
#             self.phase1_plot,
#             self.phase2_plot,
#             self.impedance_plot,
#             self.admittance_plot,
#         ]

#         for plot in all_plots:
#             plot.setLabel("left", "Value")
#             plot.setLabel("bottom", "Time", units="s")
#             plot.showGrid(x=True, y=True, alpha=0.3)

#         # Third tab: plain text
#         self.debug_label = QLabel("Debugging information will appear here.")
#         self.debug_layout.addWidget(self.debug_label)

#         self.time_history = np.linspace(
#             -(HISTORY_SIZE - 1) * UPDATE_PERIOD,
#             0,
#             HISTORY_SIZE,
#             dtype=np.float32
#         )

#         self.angle_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
#         self.torque_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
#         self.phase1_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
#         self.phase2_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
#         self.impedance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
#         self.admittance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)

#         self.angle_curve = self.angle_plot.plot(pen=pg.mkPen("#188BE9", width=2))
#         self.torque_curve = self.torque_plot.plot(pen=pg.mkPen("#2AD1A7", width=2))
#         self.phase1_curve = self.phase1_plot.plot(pen=pg.mkPen("#6113A1", width=2))
#         self.phase2_curve = self.phase2_plot.plot(pen=pg.mkPen("#B80F77", width=2))

#         self.impedance_curve = self.impedance_plot.plot(pen=pg.mkPen("#FF8800", width=2))
#         self.admittance_curve = self.admittance_plot.plot(pen=pg.mkPen("#00AAFF", width=2))


#         #setting up timer 
#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update_plot)

#         # Check whether the image exists
#         if not Path(BODE_FILE).exists():
#             self.stability_plot.setText(
#                 f"Image not found:\n{bode_path}"
#             )

#             self.stability_plot.setStyleSheet(
#                 """
#                 QLabel {
#                     border: 2px dashed red;
#                     font-size: 18px;
#                     color: red;
#                     background-color: white;
#                 }
#                 """
#             )

#     def read_csv(self,filename):
#         file = pd.read_csv(filename)
#         return file 
#     def file_save(self, filename):
#         pass 
#     def import_matlab_graphs(self, matfilename, plotfile):
#         file = self.read_csv(matfilename)
#         A = file['A']
#         B = file['B']
#         C = file['C']
#         D = file['D']
#         plant = ct.ss(A,B,C,D)
#         bodePlot = bode(plant)
#         bodePlot.savefile(plotfile)

#     def update_plot(self):
#         data = self.mem_rec_data.copy()

#         angle = data[0]
#         torque = data[1]
#         phase1 = data[2]
#         phase2 = data[3]
#         impedance = data[4]
#         admittance = data[5]

#         self.angle_history = np.roll(self.angle_history, -1)
#         self.torque_history = np.roll(self.torque_history, -1)
#         self.phase1_history = np.roll(self.phase1_history, -1)
#         self.phase2_history = np.roll(self.phase2_history, -1)
#         self.impedance_history = np.roll(self.impedance_history, -1)
#         self.admittance_history = np.roll(self.admittance_history, -1)

#         self.angle_history[-1] = angle
#         self.torque_history[-1] = torque
#         self.phase1_history[-1] = phase1
#         self.phase2_history[-1] = phase2
#         self.impedance_history[-1] = impedance
#         self.admittance_history[-1] = admittance

#         self.angle_curve.setData(self.time_history, self.angle_history)
#         self.torque_curve.setData(self.time_history, self.torque_history)
#         self.phase1_curve.setData(self.time_history, self.phase1_history)
#         self.phase2_curve.setData(self.time_history, self.phase2_history)

#         self.impedance_curve.setData(self.time_history, self.impedance_history)
#         self.admittance_curve.setData(self.time_history, self.admittance_history)

#         self.debug_label.setText(
#             f"Angle: {angle:.3f} deg\n"
#             f"Torque: {torque:.3f} Nm\n"
#             f"Phase 1 current: {phase1:.3f} A\n"
#             f"Phase 2 current: {phase2:.3f} A\n"
#             f"Impedance: {impedance:.3f}\n"
#             f"Admittance: {admittance:.3f}"
#         )

#     def rec_meas(self, checked):
#         if checked:
#             self.start_button.setText("Stop recording measurements")
#             self.timer.start(int(UPDATE_PERIOD * 1000))
#         else:
#             self.start_button.setText("Start CAPT Motor recording measurements")
#             self.timer.stop()
    

#     def closeEvent(self, event):
#         self.sm.close()
#         event.accept()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.resize(1000, 800)
#     window.show()
#     sys.exit(app.exec())
         
import math
import sys
from multiprocessing import shared_memory
from pathlib import Path

import control as ct
import numpy as np
import pandas as pd
import pyqtgraph as pg

from PyQt6 import QtCore
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import (
    QAction,
    QColor,
    QPainter,
    QPen,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# Global configuration
# ============================================================

NUM_SIGNALS = 6
HISTORY_SIZE = 300
UPDATE_PERIOD = 0.05

MEM_NAME = "shared_mem"
DTYPE = np.float32

MATNAME = "stability_plots.csv"
BODE_FILE = "bode_plot.png"


# ============================================================
# Animated rotational spring visualization
# ============================================================

class RotationalSpringWidget(QWidget):
    """
    Visualize two asymmetric rotational springs around a wheel.

    Positive side:
        tau = -kappa_positive * (error - dead_zone)

    Negative side:
        tau = -kappa_negative * (error + dead_zone)

    Inside the dead zone:
        tau = 0
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Wheel state
        self.angle_deg = 0.0
        self.previous_angle_deg = 0.0
        self.reference_deg = 0.0

        # Spring parameters
        self.kappa_positive = 1.0
        self.kappa_negative = 2.0

        # A value of 5 degrees means a total dead zone of 10 degrees.
        self.dead_zone_half_width_deg = 5.0

        # Visual animation state
        self.animation_phase = 0.0
        self.visual_velocity = 0.0
        self.bounce_amplitude = 0.0

        self.setMinimumHeight(520)

        # Independent animation timer
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(
            self.advance_animation
        )
        self.animation_timer.start(30)

    # --------------------------------------------------------
    # Public setters
    # --------------------------------------------------------

    def set_angle(self, angle_deg: float) -> None:
        new_angle = float(angle_deg)

        delta_angle = new_angle - self.angle_deg

        self.previous_angle_deg = self.angle_deg
        self.angle_deg = new_angle

        # Use wheel movement to excite the visual spring bounce.
        self.visual_velocity = delta_angle

        self.bounce_amplitude = min(
            self.bounce_amplitude + abs(delta_angle) * 0.8,
            14.0,
        )

        self.update()

    def set_reference(self, reference_deg: float) -> None:
        self.reference_deg = float(reference_deg)
        self.update()

    def set_kappa_positive(self, value: float) -> None:
        self.kappa_positive = max(0.0, float(value))
        self.update()

    def set_kappa_negative(self, value: float) -> None:
        self.kappa_negative = max(0.0, float(value))
        self.update()

    def set_dead_zone(self, half_width_deg: float) -> None:
        self.dead_zone_half_width_deg = max(
            0.0,
            float(half_width_deg),
        )
        self.update()

    # --------------------------------------------------------
    # Spring dynamics used by visualization
    # --------------------------------------------------------

    def advance_animation(self) -> None:
        """
        Advance the visual oscillation and gradually let it settle.
        """
        phase_speed = (
            0.16
            + min(abs(self.visual_velocity) * 0.05, 0.4)
        )

        self.animation_phase += phase_speed

        if self.animation_phase > 2.0 * math.pi:
            self.animation_phase -= 2.0 * math.pi

        self.visual_velocity *= 0.88
        self.bounce_amplitude *= 0.93

        if self.bounce_amplitude < 0.01:
            self.bounce_amplitude = 0.0

        self.update()

    def angle_error_deg(self) -> float:
        return self.angle_deg - self.reference_deg

    def active_region(self) -> str:
        error = self.angle_error_deg()
        dead_zone = self.dead_zone_half_width_deg

        if error > dead_zone:
            return "Positive spring"

        if error < -dead_zone:
            return "Negative spring"

        return "Dead zone"

    def positive_activation(self) -> float:
        error = self.angle_error_deg()
        dead_zone = self.dead_zone_half_width_deg

        if error <= dead_zone:
            return 0.0

        return min(
            (error - dead_zone) / 45.0,
            1.0,
        )

    def negative_activation(self) -> float:
        error = self.angle_error_deg()
        dead_zone = self.dead_zone_half_width_deg

        if error >= -dead_zone:
            return 0.0

        return min(
            (-error - dead_zone) / 45.0,
            1.0,
        )

    def spring_torque(self) -> float:
        """
        Calculate continuous asymmetric spring torque.

        Torque begins at zero at each dead-zone boundary.
        """
        error_deg = self.angle_error_deg()
        dead_zone_deg = self.dead_zone_half_width_deg

        if error_deg > dead_zone_deg:
            effective_error_deg = (
                error_deg - dead_zone_deg
            )

            effective_error_rad = math.radians(
                effective_error_deg
            )

            return (
                -self.kappa_positive
                * effective_error_rad
            )

        if error_deg < -dead_zone_deg:
            effective_error_deg = (
                error_deg + dead_zone_deg
            )

            effective_error_rad = math.radians(
                effective_error_deg
            )

            return (
                -self.kappa_negative
                * effective_error_rad
            )

        return 0.0

    # --------------------------------------------------------
    # Main painting method
    # --------------------------------------------------------

    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        center = QPointF(
            width * 0.54,
            height * 0.58,
        )

        wheel_radius = min(width, height) * 0.21
        spring_radius = wheel_radius * 1.38

        wheel_angle_rad = math.radians(
            self.angle_error_deg()
        )

        self.draw_dead_zone(
            painter,
            center,
            spring_radius,
        )

        self.draw_positive_spring(
            painter,
            center,
            spring_radius,
        )

        self.draw_negative_spring(
            painter,
            center,
            spring_radius,
        )

        self.draw_reference_marker(
            painter,
            center,
            wheel_radius,
        )

        self.draw_wheel(
            painter,
            center,
            wheel_radius,
            wheel_angle_rad,
        )

        self.draw_torque_arrow(
            painter,
            center,
            wheel_radius * 0.72,
            self.spring_torque(),
        )

        self.draw_information(painter)

    # --------------------------------------------------------
    # Information panel
    # --------------------------------------------------------

    def draw_information(
        self,
        painter: QPainter,
    ) -> None:
        painter.setPen(
            QColor(35, 35, 35)
        )

        information = [
            f"Measured angle: {self.angle_deg:.2f} deg",
            f"Reference angle: {self.reference_deg:.2f} deg",
            f"Angle error: {self.angle_error_deg():.2f} deg",
            (
                "Dead zone: "
                f"±{self.dead_zone_half_width_deg:.2f} deg"
            ),
            (
                "Positive kappa: "
                f"{self.kappa_positive:.3f} Nm/rad"
            ),
            (
                "Negative kappa: "
                f"{self.kappa_negative:.3f} Nm/rad"
            ),
            f"Active region: {self.active_region()}",
            (
                "Calculated virtual torque: "
                f"{self.spring_torque():.4f} Nm"
            ),
        ]

        y_position = 30

        for line in information:
            painter.drawText(
                20,
                y_position,
                line,
            )

            y_position += 25

    # --------------------------------------------------------
    # Wheel drawing
    # --------------------------------------------------------

    def draw_wheel(
        self,
        painter: QPainter,
        center: QPointF,
        radius: float,
        angle_rad: float,
    ) -> None:
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(45, 55, 65),
                12,
            )
        )

        painter.drawEllipse(
            center,
            radius,
            radius,
        )

        hub_radius = radius * 0.17

        painter.setPen(
            QPen(
                QColor(65, 75, 85),
                5,
            )
        )

        painter.setBrush(
            QColor(180, 185, 190)
        )

        painter.drawEllipse(
            center,
            hub_radius,
            hub_radius,
        )

        painter.setPen(
            QPen(
                QColor(65, 75, 85),
                7,
            )
        )

        spoke_angles = (
            -math.pi / 2,
            math.pi / 6,
            5 * math.pi / 6,
        )

        for base_angle in spoke_angles:
            current_angle = (
                base_angle + angle_rad
            )

            spoke_end = QPointF(
                center.x()
                + radius
                * 0.82
                * math.cos(current_angle),

                center.y()
                + radius
                * 0.82
                * math.sin(current_angle),
            )

            painter.drawLine(
                center,
                spoke_end,
            )

        # Wheel angle indicator
        indicator_angle = (
            -math.pi / 2 + angle_rad
        )

        indicator_start = QPointF(
            center.x()
            + radius
            * 0.78
            * math.cos(indicator_angle),

            center.y()
            + radius
            * 0.78
            * math.sin(indicator_angle),
        )

        indicator_end = QPointF(
            center.x()
            + radius
            * 1.06
            * math.cos(indicator_angle),

            center.y()
            + radius
            * 1.06
            * math.sin(indicator_angle),
        )

        painter.setPen(
            QPen(
                QColor(25, 110, 220),
                8,
            )
        )

        painter.drawLine(
            indicator_start,
            indicator_end,
        )

    # --------------------------------------------------------
    # Reference and dead-zone drawing
    # --------------------------------------------------------

    def draw_reference_marker(
        self,
        painter: QPainter,
        center: QPointF,
        wheel_radius: float,
    ) -> None:
        painter.setPen(
            QPen(
                QColor(30, 30, 30),
                3,
            )
        )

        marker_start = QPointF(
            center.x(),
            center.y()
            - wheel_radius * 1.08,
        )

        marker_end = QPointF(
            center.x(),
            center.y()
            - wheel_radius * 1.30,
        )

        painter.drawLine(
            marker_start,
            marker_end,
        )

        painter.drawText(
            int(center.x() - 32),
            int(
                center.y()
                - wheel_radius * 1.38
            ),
            "Reference",
        )

    def draw_dead_zone(
        self,
        painter: QPainter,
        center: QPointF,
        radius: float,
    ) -> None:
        dead_zone_pen = QPen(
            QColor(145, 145, 145),
            18,
        )

        dead_zone_pen.setCapStyle(
            Qt.PenCapStyle.RoundCap
        )

        painter.setPen(dead_zone_pen)
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        rectangle = QtCore.QRectF(
            center.x() - radius,
            center.y() - radius,
            2 * radius,
            2 * radius,
        )

        start_angle_deg = (
            90.0
            - self.dead_zone_half_width_deg
        )

        span_angle_deg = (
            2.0
            * self.dead_zone_half_width_deg
        )

        painter.drawArc(
            rectangle,
            int(start_angle_deg * 16),
            int(span_angle_deg * 16),
        )

        painter.setPen(
            QColor(90, 90, 90)
        )

        painter.drawText(
            int(center.x() - 42),
            int(center.y() - radius - 25),
            "Dead zone",
        )

    # --------------------------------------------------------
    # Positive and negative springs
    # --------------------------------------------------------

    def draw_positive_spring(
        self,
        painter: QPainter,
        center: QPointF,
        radius: float,
    ) -> None:
        activation = self.positive_activation()
        active = activation > 0.0

        dead_zone_angle_rad = math.radians(
            self.dead_zone_half_width_deg
        )

        positive_displacement_rad = math.radians(
            max(
                0.0,
                self.angle_error_deg()
                - self.dead_zone_half_width_deg,
            )
        )

        moving_angle = (
            -math.pi / 2
            + dead_zone_angle_rad
            + positive_displacement_rad
        )

        fixed_angle = math.radians(25)

        self.draw_animated_rotational_spring(
            painter=painter,
            center=center,
            radius=radius,
            moving_angle_rad=moving_angle,
            fixed_angle_rad=fixed_angle,
            base_coils=14,
            activation=activation,
            active=active,
            animation_phase=self.animation_phase,
            bounce_amplitude=self.bounce_amplitude,
            label=(
                f"kappa + = "
                f"{self.kappa_positive:.2f}"
            ),
        )

    def draw_negative_spring(
        self,
        painter: QPainter,
        center: QPointF,
        radius: float,
    ) -> None:
        activation = self.negative_activation()
        active = activation > 0.0

        dead_zone_angle_rad = math.radians(
            self.dead_zone_half_width_deg
        )

        negative_displacement_rad = math.radians(
            min(
                0.0,
                self.angle_error_deg()
                + self.dead_zone_half_width_deg,
            )
        )

        moving_angle = (
            -math.pi / 2
            - dead_zone_angle_rad
            + negative_displacement_rad
        )

        fixed_angle = math.radians(-205)

        self.draw_animated_rotational_spring(
            painter=painter,
            center=center,
            radius=radius,
            moving_angle_rad=moving_angle,
            fixed_angle_rad=fixed_angle,
            base_coils=14,
            activation=activation,
            active=active,
            animation_phase=-self.animation_phase,
            bounce_amplitude=self.bounce_amplitude,
            label=(
                f"kappa - = "
                f"{self.kappa_negative:.2f}"
            ),
        )

    @staticmethod
    def draw_animated_rotational_spring(
        painter: QPainter,
        center: QPointF,
        radius: float,
        moving_angle_rad: float,
        fixed_angle_rad: float,
        base_coils: int,
        activation: float,
        active: bool,
        animation_phase: float,
        bounce_amplitude: float,
        label: str,
    ) -> None:
        """
        Draw an animated circumferential spring.

        The spring:
        - changes angular length;
        - changes coil density;
        - oscillates radially;
        - bounces when the wheel moves.
        """
        if active:
            spring_color = QColor(
                210,
                70,
                50,
            )

            line_width = 5
        else:
            spring_color = QColor(
                70,
                100,
                140,
            )

            line_width = 3

        painter.setPen(
            QPen(
                spring_color,
                line_width,
            )
        )

        # More activation makes the spring visually denser.
        coil_count = max(
            7,
            int(
                base_coils
                + activation * 7
            ),
        )

        number_of_points = coil_count * 10

        base_coil_amplitude = 8.0

        active_bounce = (
            bounce_amplitude
            * (0.30 + 0.70 * activation)
        )

        points = []

        for index in range(
            number_of_points + 1
        ):
            ratio = (
                index
                / number_of_points
            )

            angle = (
                moving_angle_rad
                + ratio
                * (
                    fixed_angle_rad
                    - moving_angle_rad
                )
            )

            coil_wave = math.sin(
                ratio
                * coil_count
                * 2.0
                * math.pi
                + animation_phase
            )

            whole_spring_bounce = math.sin(
                animation_phase * 1.4
                + ratio * math.pi
            )

            radial_displacement = (
                base_coil_amplitude * coil_wave
                + active_bounce
                * whole_spring_bounce
            )

            current_radius = (
                radius
                + radial_displacement
            )

            point = QPointF(
                center.x()
                + current_radius
                * math.cos(angle),

                center.y()
                + current_radius
                * math.sin(angle),
            )

            points.append(point)

        painter.drawPolyline(
            QPolygonF(points)
        )

        # Label
        label_angle = (
            moving_angle_rad
            + 0.60
            * (
                fixed_angle_rad
                - moving_angle_rad
            )
        )

        label_radius = radius + 44

        label_position = QPointF(
            center.x()
            + label_radius
            * math.cos(label_angle),

            center.y()
            + label_radius
            * math.sin(label_angle),
        )

        painter.setPen(spring_color)

        painter.drawText(
            int(label_position.x() - 48),
            int(label_position.y()),
            label,
        )

    # --------------------------------------------------------
    # Torque direction arrow
    # --------------------------------------------------------

    @staticmethod
    def draw_torque_arrow(
        painter: QPainter,
        center: QPointF,
        radius: float,
        torque: float,
    ) -> None:
        if abs(torque) < 1e-8:
            return

        painter.setPen(
            QPen(
                QColor(210, 65, 45),
                5,
            )
        )

        rectangle = QtCore.QRectF(
            center.x() - radius,
            center.y() - radius,
            2 * radius,
            2 * radius,
        )

        if torque > 0:
            start_angle_deg = 20
            span_angle_deg = 230
        else:
            start_angle_deg = 160
            span_angle_deg = -230

        painter.drawArc(
            rectangle,
            int(start_angle_deg * 16),
            int(span_angle_deg * 16),
        )


# ============================================================
# Main GUI
# ============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "CAPT Motor Dashboard"
        )

        self.sm = shared_memory.SharedMemory(
            name=MEM_NAME,
            create=False,
        )

        self.mem_rec_data = np.ndarray(
            (NUM_SIGNALS,),
            dtype=DTYPE,
            buffer=self.sm.buf,
        )

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.home_page = QWidget()
        self.stats_page = QWidget()
        self.spring_page = QWidget()
        self.stability_page = QWidget()
        self.debug_page = QWidget()

        self.tabs.addTab(
            self.home_page,
            "Measurements",
        )

        self.tabs.addTab(
            self.stats_page,
            "Impedance / Admittance",
        )

        self.tabs.addTab(
            self.spring_page,
            "Rotational Springs",
        )

        self.tabs.addTab(
            self.stability_page,
            "Stability Analysis",
        )

        self.tabs.addTab(
            self.debug_page,
            "Debugging",
        )

        self.home_layout = QVBoxLayout(
            self.home_page
        )

        self.stats_layout = QVBoxLayout(
            self.stats_page
        )

        self.spring_layout = QVBoxLayout(
            self.spring_page
        )

        self.stability_layout = QVBoxLayout(
            self.stability_page
        )

        self.debug_layout = QVBoxLayout(
            self.debug_page
        )

        self.create_toolbar()
        self.create_measurement_page()
        self.create_stats_page()
        self.create_spring_page()
        self.create_stability_page()
        self.create_debug_page()

        self.create_histories()
        self.create_curves()

        self.timer = QtCore.QTimer(self)

        self.timer.timeout.connect(
            self.update_plot
        )

        self.check_bode_image()

    # --------------------------------------------------------
    # Toolbar
    # --------------------------------------------------------

    def create_toolbar(self) -> None:
        toolbar = QToolBar("Actions")
        self.addToolBar(toolbar)

        page_actions = [
            ("Measurements", 0),
            ("Impedance / Admittance", 1),
            ("Rotational Springs", 2),
            ("Stability Analysis", 3),
            ("Debugging", 4),
        ]

        for title, tab_index in page_actions:
            action = QAction(title, self)

            action.triggered.connect(
                lambda checked=False,
                index=tab_index:
                self.tabs.setCurrentIndex(index)
            )

            toolbar.addAction(action)

    # --------------------------------------------------------
    # Measurement tab
    # --------------------------------------------------------

    def create_measurement_page(self) -> None:
        self.start_button = QPushButton(
            "Start CAPT Motor recording measurements"
        )

        self.start_button.setCheckable(True)

        self.start_button.clicked.connect(
            self.rec_meas
        )

        self.home_layout.addWidget(
            self.start_button
        )

        self.graph_layout = (
            pg.GraphicsLayoutWidget()
        )

        self.home_layout.addWidget(
            self.graph_layout
        )

        self.angle_plot = (
            self.graph_layout.addPlot(
                row=0,
                col=0,
                title="Angle (deg)",
            )
        )

        self.torque_plot = (
            self.graph_layout.addPlot(
                row=0,
                col=1,
                title="Torque (Nm)",
            )
        )

        self.phase1_plot = (
            self.graph_layout.addPlot(
                row=1,
                col=0,
                title="Current Phase 1 (A)",
            )
        )

        self.phase2_plot = (
            self.graph_layout.addPlot(
                row=1,
                col=1,
                title="Current Phase 2 (A)",
            )
        )

    # --------------------------------------------------------
    # Impedance/admittance tab
    # --------------------------------------------------------

    def create_stats_page(self) -> None:
        self.stats_graph_layout = (
            pg.GraphicsLayoutWidget()
        )

        self.stats_layout.addWidget(
            self.stats_graph_layout
        )

        self.impedance_plot = (
            self.stats_graph_layout.addPlot(
                row=0,
                col=0,
                title="Impedance",
            )
        )

        self.admittance_plot = (
            self.stats_graph_layout.addPlot(
                row=1,
                col=0,
                title="Admittance",
            )
        )

    # --------------------------------------------------------
    # Rotational spring tab
    # --------------------------------------------------------

    def create_spring_page(self) -> None:
        spring_title = QLabel(
            "Animated Asymmetric Rotational Springs"
        )

        spring_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        spring_title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
            }
            """
        )

        self.spring_widget = (
            RotationalSpringWidget()
        )

        self.kappa_positive_input = (
            QDoubleSpinBox()
        )

        self.kappa_positive_input.setRange(
            0.0,
            20.0,
        )

        self.kappa_positive_input.setDecimals(3)
        self.kappa_positive_input.setSingleStep(0.1)
        self.kappa_positive_input.setValue(1.0)

        self.kappa_positive_input.setSuffix(
            " Nm/rad"
        )

        self.kappa_negative_input = (
            QDoubleSpinBox()
        )

        self.kappa_negative_input.setRange(
            0.0,
            20.0,
        )

        self.kappa_negative_input.setDecimals(3)
        self.kappa_negative_input.setSingleStep(0.1)
        self.kappa_negative_input.setValue(2.0)

        self.kappa_negative_input.setSuffix(
            " Nm/rad"
        )

        self.dead_zone_input = (
            QDoubleSpinBox()
        )

        self.dead_zone_input.setRange(
            0.0,
            90.0,
        )

        self.dead_zone_input.setDecimals(2)
        self.dead_zone_input.setSingleStep(0.5)
        self.dead_zone_input.setValue(5.0)

        self.dead_zone_input.setSuffix(
            " deg"
        )

        self.reference_input = (
            QDoubleSpinBox()
        )

        self.reference_input.setRange(
            -180.0,
            180.0,
        )

        self.reference_input.setDecimals(2)
        self.reference_input.setSingleStep(1.0)
        self.reference_input.setValue(0.0)

        self.reference_input.setSuffix(
            " deg"
        )

        self.reference_button = QPushButton(
            "Set current angle as reference"
        )

        controls_layout = QGridLayout()

        controls_layout.addWidget(
            QLabel("Positive-side kappa:"),
            0,
            0,
        )

        controls_layout.addWidget(
            self.kappa_positive_input,
            0,
            1,
        )

        controls_layout.addWidget(
            QLabel("Negative-side kappa:"),
            0,
            2,
        )

        controls_layout.addWidget(
            self.kappa_negative_input,
            0,
            3,
        )

        controls_layout.addWidget(
            QLabel("Dead-zone half-width:"),
            1,
            0,
        )

        controls_layout.addWidget(
            self.dead_zone_input,
            1,
            1,
        )

        controls_layout.addWidget(
            QLabel("Reference angle:"),
            1,
            2,
        )

        controls_layout.addWidget(
            self.reference_input,
            1,
            3,
        )

        controls_layout.addWidget(
            self.reference_button,
            2,
            0,
            1,
            4,
        )

        self.spring_layout.addWidget(
            spring_title
        )

        self.spring_layout.addWidget(
            self.spring_widget,
            stretch=1,
        )

        self.spring_layout.addLayout(
            controls_layout
        )

        self.kappa_positive_input.valueChanged.connect(
            self.spring_widget.set_kappa_positive
        )

        self.kappa_negative_input.valueChanged.connect(
            self.spring_widget.set_kappa_negative
        )

        self.dead_zone_input.valueChanged.connect(
            self.spring_widget.set_dead_zone
        )

        self.reference_input.valueChanged.connect(
            self.spring_widget.set_reference
        )

        self.reference_button.clicked.connect(
            self.set_current_angle_as_reference
        )

    # --------------------------------------------------------
    # Stability tab
    # --------------------------------------------------------

    def create_stability_page(self) -> None:
        self.stability_title = QLabel(
            "Bode Plot and Stability Analysis"
        )

        self.stability_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.stability_title.setObjectName(
            "stabilityTitle"
        )

        self.stability_plot = QLabel()

        self.stability_plot.setObjectName(
            "stabilityImage"
        )

        self.stability_plot.setMinimumSize(
            600,
            450,
        )

        self.stability_plot.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.stability_layout.addWidget(
            self.stability_title
        )

        self.stability_layout.addWidget(
            self.stability_plot,
            stretch=1,
        )

        bode_path = (
            Path(BODE_FILE)
            .resolve()
            .as_posix()
        )

        self.setStyleSheet(
            f"""
            QLabel#stabilityTitle {{
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
            }}

            QLabel#stabilityImage {{
                border-image:
                    url("{bode_path}")
                    0 0 0 0
                    stretch stretch;

                background-color: white;
                border: 1px solid #808080;
                border-radius: 5px;
                margin: 10px;
            }}
            """
        )

    # --------------------------------------------------------
    # Debugging tab
    # --------------------------------------------------------

    def create_debug_page(self) -> None:
        self.debug_label = QLabel(
            "Debugging information will appear here."
        )

        self.debug_label.setAlignment(
            Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignLeft
        )

        self.debug_layout.addWidget(
            self.debug_label
        )

    # --------------------------------------------------------
    # Signal histories
    # --------------------------------------------------------

    def create_histories(self) -> None:
        self.time_history = np.linspace(
            -(HISTORY_SIZE - 1)
            * UPDATE_PERIOD,
            0,
            HISTORY_SIZE,
            dtype=np.float32,
        )

        self.angle_history = np.zeros(
            HISTORY_SIZE,
            dtype=np.float32,
        )

        self.torque_history = np.zeros(
            HISTORY_SIZE,
            dtype=np.float32,
        )

        self.phase1_history = np.zeros(
            HISTORY_SIZE,
            dtype=np.float32,
        )

        self.phase2_history = np.zeros(
            HISTORY_SIZE,
            dtype=np.float32,
        )

        self.impedance_history = np.zeros(
            HISTORY_SIZE,
            dtype=np.float32,
        )

        self.admittance_history = np.zeros(
            HISTORY_SIZE,
            dtype=np.float32,
        )

    # --------------------------------------------------------
    # Plot curves
    # --------------------------------------------------------

    def create_curves(self) -> None:
        all_plots = [
            self.angle_plot,
            self.torque_plot,
            self.phase1_plot,
            self.phase2_plot,
            self.impedance_plot,
            self.admittance_plot,
        ]

        for plot in all_plots:
            plot.setLabel(
                "left",
                "Value",
            )

            plot.setLabel(
                "bottom",
                "Time",
                units="s",
            )

            plot.showGrid(
                x=True,
                y=True,
                alpha=0.3,
            )

        self.angle_curve = (
            self.angle_plot.plot(
                pen=pg.mkPen(
                    "#188BE9",
                    width=2,
                )
            )
        )

        self.torque_curve = (
            self.torque_plot.plot(
                pen=pg.mkPen(
                    "#2AD1A7",
                    width=2,
                )
            )
        )

        self.phase1_curve = (
            self.phase1_plot.plot(
                pen=pg.mkPen(
                    "#6113A1",
                    width=2,
                )
            )
        )

        self.phase2_curve = (
            self.phase2_plot.plot(
                pen=pg.mkPen(
                    "#B80F77",
                    width=2,
                )
            )
        )

        self.impedance_curve = (
            self.impedance_plot.plot(
                pen=pg.mkPen(
                    "#FF8800",
                    width=2,
                )
            )
        )

        self.admittance_curve = (
            self.admittance_plot.plot(
                pen=pg.mkPen(
                    "#00AAFF",
                    width=2,
                )
            )
        )

    # --------------------------------------------------------
    # Utility methods
    # --------------------------------------------------------

    def check_bode_image(self) -> None:
        if Path(BODE_FILE).exists():
            return

        bode_path = (
            Path(BODE_FILE)
            .resolve()
            .as_posix()
        )

        self.stability_plot.setText(
            f"Image not found:\n{bode_path}"
        )

        self.stability_plot.setStyleSheet(
            """
            QLabel {
                border: 2px dashed red;
                font-size: 18px;
                color: red;
                background-color: white;
            }
            """
        )

    def set_current_angle_as_reference(self) -> None:
        current_angle = float(
            self.mem_rec_data[0]
        )

        self.reference_input.setValue(
            current_angle
        )

    def read_csv(self, filename: str):
        return pd.read_csv(filename)

    def file_save(self, filename: str) -> None:
        pass

    def import_matlab_graphs(
        self,
        matfilename: str,
        plotfile: str,
    ) -> None:
        file = self.read_csv(matfilename)

        A = file["A"].to_numpy()
        B = file["B"].to_numpy()
        C = file["C"].to_numpy()
        D = file["D"].to_numpy()

        plant = ct.ss(A, B, C, D)

        ct.bode_plot(plant)

    # --------------------------------------------------------
    # Real-time update
    # --------------------------------------------------------

    def update_plot(self) -> None:
        data = self.mem_rec_data.copy()

        angle = float(data[0])
        torque = float(data[1])
        phase1 = float(data[2])
        phase2 = float(data[3])
        impedance = float(data[4])
        admittance = float(data[5])

        self.angle_history = np.roll(
            self.angle_history,
            -1,
        )

        self.torque_history = np.roll(
            self.torque_history,
            -1,
        )

        self.phase1_history = np.roll(
            self.phase1_history,
            -1,
        )

        self.phase2_history = np.roll(
            self.phase2_history,
            -1,
        )

        self.impedance_history = np.roll(
            self.impedance_history,
            -1,
        )

        self.admittance_history = np.roll(
            self.admittance_history,
            -1,
        )

        self.angle_history[-1] = angle
        self.torque_history[-1] = torque
        self.phase1_history[-1] = phase1
        self.phase2_history[-1] = phase2
        self.impedance_history[-1] = impedance
        self.admittance_history[-1] = admittance

        self.angle_curve.setData(
            self.time_history,
            self.angle_history,
        )

        self.torque_curve.setData(
            self.time_history,
            self.torque_history,
        )

        self.phase1_curve.setData(
            self.time_history,
            self.phase1_history,
        )

        self.phase2_curve.setData(
            self.time_history,
            self.phase2_history,
        )

        self.impedance_curve.setData(
            self.time_history,
            self.impedance_history,
        )

        self.admittance_curve.setData(
            self.time_history,
            self.admittance_history,
        )

        # Update animated wheel and springs.
        self.spring_widget.set_angle(angle)

        virtual_torque = (
            self.spring_widget.spring_torque()
        )

        active_region = (
            self.spring_widget.active_region()
        )

        self.debug_label.setText(
            f"Angle: {angle:.3f} deg\n"
            f"Measured torque: {torque:.3f} Nm\n"
            f"Phase 1 current: {phase1:.3f} A\n"
            f"Phase 2 current: {phase2:.3f} A\n"
            f"Impedance: {impedance:.3f}\n"
            f"Admittance: {admittance:.3f}\n\n"
            f"Active spring region: {active_region}\n"
            f"Calculated virtual torque: "
            f"{virtual_torque:.4f} Nm"
        )

    # --------------------------------------------------------
    # Start/stop recording
    # --------------------------------------------------------

    def rec_meas(
        self,
        checked: bool,
    ) -> None:
        if checked:
            self.start_button.setText(
                "Stop recording measurements"
            )

            self.timer.start(
                int(
                    UPDATE_PERIOD
                    * 1000
                )
            )
        else:
            self.start_button.setText(
                "Start CAPT Motor recording measurements"
            )

            self.timer.stop()

    # --------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------

    def closeEvent(self, event) -> None:
        self.timer.stop()

        try:
            self.sm.close()
        finally:
            event.accept()


# ============================================================
# Program entry point
# ============================================================

def main() -> None:
    app = QApplication(sys.argv)

    try:
        window = MainWindow()

    except FileNotFoundError:
        print(
            f'Could not connect to shared memory "{MEM_NAME}".'
        )

        print(
            "Start the shared-memory producer before opening the GUI."
        )

        sys.exit(1)

    window.resize(
        1150,
        850,
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
