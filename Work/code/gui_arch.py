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
from pathlib import Path
from multiprocessing import shared_memory

import numpy as np
import pandas as pd
import pyqtgraph as pg
import control as ct

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QPointF
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
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


NUM_SIGNALS = 6
HISTORY_SIZE = 300
UPDATE_PERIOD = 0.05

MEM_NAME = "shared_mem"
DTYPE = np.float32

MATNAME = "stability_plots.csv"
BODE_FILE = "bode_plot.png"


class SpringWidget(QWidget):
    """Visualizes a virtual rotational spring."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.angle_deg = 0.0
        self.reference_deg = 0.0
        self.kappa = 1.0

        self.setMinimumHeight(400)

    def set_angle(self, angle_deg: float) -> None:
        self.angle_deg = float(angle_deg)
        self.update()

    def set_kappa(self, kappa: float) -> None:
        self.kappa = float(kappa)
        self.update()

    def set_reference(self, reference_deg: float) -> None:
        self.reference_deg = float(reference_deg)
        self.update()

    def spring_torque(self) -> float:
        angle_error_rad = math.radians(
            self.angle_deg - self.reference_deg
        )

        return -self.kappa * angle_error_rad

    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        center_y = height * 0.55
        wall_x = width * 0.10
        equilibrium_x = width * 0.52

        max_angle_deg = 45.0
        max_displacement = width * 0.30

        normalized_angle = max(
            -1.0,
            min(1.0, self.angle_deg / max_angle_deg),
        )

        handle_x = (
            equilibrium_x
            + normalized_angle * max_displacement
        )

        # Equilibrium line
        equilibrium_pen = QPen(QColor(130, 130, 130), 2)
        equilibrium_pen.setStyle(Qt.PenStyle.DashLine)

        painter.setPen(equilibrium_pen)
        painter.drawLine(
            QPointF(equilibrium_x, center_y - 100),
            QPointF(equilibrium_x, center_y + 100),
        )

        painter.drawText(
            int(equilibrium_x - 35),
            int(center_y + 125),
            "Reference",
        )

        # Fixed wall
        wall_pen = QPen(QColor(60, 60, 60), 6)
        painter.setPen(wall_pen)

        painter.drawLine(
            QPointF(wall_x, center_y - 90),
            QPointF(wall_x, center_y + 90),
        )

        # Draw spring
        self.draw_spring(
            painter,
            QPointF(wall_x, center_y),
            QPointF(handle_x, center_y),
        )

        # Draw handle
        handle_pen = QPen(QColor(30, 100, 210), 10)
        painter.setPen(handle_pen)

        painter.drawLine(
            QPointF(handle_x, center_y - 75),
            QPointF(handle_x, center_y + 75),
        )

        # Torque arrow
        self.draw_torque_arrow(
            painter,
            QPointF(handle_x, center_y - 115),
            self.spring_torque(),
        )

        # Information
        painter.setPen(QColor(30, 30, 30))

        painter.drawText(
            20,
            35,
            f"Angle: {self.angle_deg:.2f} deg",
        )

        painter.drawText(
            20,
            65,
            f"Reference: {self.reference_deg:.2f} deg",
        )

        painter.drawText(
            20,
            95,
            f"Kappa: {self.kappa:.3f} Nm/rad",
        )

        painter.drawText(
            20,
            125,
            f"Spring torque: {self.spring_torque():.3f} Nm",
        )

    @staticmethod
    def draw_spring(
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        coils: int = 12,
        amplitude: float = 25.0,
    ) -> None:
        spring_pen = QPen(QColor(40, 40, 40), 3)
        painter.setPen(spring_pen)

        lead_length = 20.0

        spring_start_x = start.x() + lead_length
        spring_end_x = end.x() - lead_length

        if spring_end_x <= spring_start_x:
            painter.drawLine(start, end)
            return

        points = [
            start,
            QPointF(spring_start_x, start.y()),
        ]

        segments = coils * 2
        spring_length = spring_end_x - spring_start_x

        for index in range(segments + 1):
            ratio = index / segments
            x = spring_start_x + ratio * spring_length

            if index == 0 or index == segments:
                y = start.y()
            elif index % 2 == 0:
                y = start.y() + amplitude
            else:
                y = start.y() - amplitude

            points.append(QPointF(x, y))

        points.append(QPointF(spring_end_x, end.y()))
        points.append(end)

        painter.drawPolyline(QPolygonF(points))

    @staticmethod
    def draw_torque_arrow(
        painter: QPainter,
        origin: QPointF,
        torque: float,
    ) -> None:
        if abs(torque) < 1e-6:
            return

        direction = 1 if torque > 0 else -1
        arrow_length = 70

        arrow_pen = QPen(QColor(200, 60, 50), 4)
        painter.setPen(arrow_pen)

        end = QPointF(
            origin.x() + direction * arrow_length,
            origin.y(),
        )

        painter.drawLine(origin, end)

        head_size = 12

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")

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
            "Virtual Spring",
        )

        self.tabs.addTab(
            self.stability_page,
            "Stability Analysis",
        )

        self.tabs.addTab(
            self.debug_page,
            "Debugging",
        )

        self.home_layout = QVBoxLayout(self.home_page)
        self.stats_layout = QVBoxLayout(self.stats_page)
        self.spring_layout = QVBoxLayout(self.spring_page)
        self.stability_layout = QVBoxLayout(
            self.stability_page
        )
        self.debug_layout = QVBoxLayout(self.debug_page)

        self.create_toolbar()
        self.create_measurement_page()
        self.create_stats_page()
        self.create_spring_page()
        self.create_stability_page()
        self.create_debug_page()
        self.create_history()
        self.create_curves()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.check_bode_image()

    def create_toolbar(self) -> None:
        toolbar = QToolBar("Actions")
        self.addToolBar(toolbar)

        actions = [
            ("Measurements", 0),
            ("Impedance / Admittance", 1),
            ("Virtual Spring", 2),
            ("Stability Analysis", 3),
            ("Debugging", 4),
        ]

        for title, index in actions:
            action = QAction(title, self)
            action.triggered.connect(
                lambda checked=False, i=index:
                self.tabs.setCurrentIndex(i)
            )
            toolbar.addAction(action)

    def create_measurement_page(self) -> None:
        self.start_button = QPushButton(
            "Start CAPT Motor recording measurements"
        )

        self.start_button.setCheckable(True)
        self.start_button.clicked.connect(self.rec_meas)

        self.home_layout.addWidget(self.start_button)

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.home_layout.addWidget(self.graph_layout)

        self.angle_plot = self.graph_layout.addPlot(
            row=0,
            col=0,
            title="Angle (deg)",
        )

        self.torque_plot = self.graph_layout.addPlot(
            row=0,
            col=1,
            title="Torque (Nm)",
        )

        self.phase1_plot = self.graph_layout.addPlot(
            row=1,
            col=0,
            title="Current Phase 1 (A)",
        )

        self.phase2_plot = self.graph_layout.addPlot(
            row=1,
            col=1,
            title="Current Phase 2 (A)",
        )

    def create_stats_page(self) -> None:
        self.stats_graph_layout = pg.GraphicsLayoutWidget()
        self.stats_layout.addWidget(self.stats_graph_layout)

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

    def create_spring_page(self) -> None:
        self.spring_title = QLabel(
            "Virtual Spring Visualization"
        )

        self.spring_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.spring_title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
            }
            """
        )

        self.spring_widget = SpringWidget()

        self.kappa_input = QDoubleSpinBox()
        self.kappa_input.setRange(-20.0, 20.0)
        self.kappa_input.setDecimals(3)
        self.kappa_input.setSingleStep(0.1)
        self.kappa_input.setValue(1.0)
        self.kappa_input.setSuffix(" Nm/rad")

        self.reference_input = QDoubleSpinBox()
        self.reference_input.setRange(-180.0, 180.0)
        self.reference_input.setDecimals(2)
        self.reference_input.setSingleStep(1.0)
        self.reference_input.setValue(0.0)
        self.reference_input.setSuffix(" deg")

        self.reset_spring_button = QPushButton(
            "Reset reference"
        )

        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Kappa:"))
        controls_layout.addWidget(self.kappa_input)

        controls_layout.addWidget(
            QLabel("Reference angle:")
        )
        controls_layout.addWidget(self.reference_input)

        controls_layout.addWidget(
            self.reset_spring_button
        )

        self.spring_layout.addWidget(self.spring_title)
        self.spring_layout.addWidget(
            self.spring_widget,
            stretch=1,
        )
        self.spring_layout.addLayout(controls_layout)

        self.kappa_input.valueChanged.connect(
            self.spring_widget.set_kappa
        )

        self.reference_input.valueChanged.connect(
            self.spring_widget.set_reference
        )

        self.reset_spring_button.clicked.connect(
            self.reset_spring_reference
        )

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

        self.stability_plot.setMinimumSize(600, 450)
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

        bode_path = Path(BODE_FILE).resolve().as_posix()

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
                    0 0 0 0 stretch stretch;
                background-color: white;
                border: 1px solid #808080;
                border-radius: 5px;
                margin: 10px;
            }}
            """
        )

    def create_debug_page(self) -> None:
        self.debug_label = QLabel(
            "Debugging information will appear here."
        )

        self.debug_layout.addWidget(self.debug_label)

    def create_history(self) -> None:
        self.time_history = np.linspace(
            -(HISTORY_SIZE - 1) * UPDATE_PERIOD,
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
            plot.setLabel("left", "Value")
            plot.setLabel("bottom", "Time", units="s")
            plot.showGrid(x=True, y=True, alpha=0.3)

        self.angle_curve = self.angle_plot.plot(
            pen=pg.mkPen("#188BE9", width=2)
        )

        self.torque_curve = self.torque_plot.plot(
            pen=pg.mkPen("#2AD1A7", width=2)
        )

        self.phase1_curve = self.phase1_plot.plot(
            pen=pg.mkPen("#6113A1", width=2)
        )

        self.phase2_curve = self.phase2_plot.plot(
            pen=pg.mkPen("#B80F77", width=2)
        )

        self.impedance_curve = self.impedance_plot.plot(
            pen=pg.mkPen("#FF8800", width=2)
        )

        self.admittance_curve = self.admittance_plot.plot(
            pen=pg.mkPen("#00AAFF", width=2)
        )

    def check_bode_image(self) -> None:
        if Path(BODE_FILE).exists():
            return

        bode_path = Path(BODE_FILE).resolve().as_posix()

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

    def reset_spring_reference(self) -> None:
        current_angle = float(self.mem_rec_data[0])

        self.reference_input.setValue(current_angle)
        self.spring_widget.set_reference(current_angle)

    def read_csv(self, filename):
        return pd.read_csv(filename)

    def file_save(self, filename):
        pass

    def import_matlab_graphs(
        self,
        matfilename,
        plotfile,
    ):
        file = self.read_csv(matfilename)

        A = file["A"]
        B = file["B"]
        C = file["C"]
        D = file["D"]

        plant = ct.ss(A, B, C, D)

        ct.bode_plot(plant)
        pg.exporters.ImageExporter.export(plotfile)

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

        # Update the virtual spring tab
        self.spring_widget.set_angle(angle)

        self.debug_label.setText(
            f"Angle: {angle:.3f} deg\n"
            f"Torque: {torque:.3f} Nm\n"
            f"Phase 1 current: {phase1:.3f} A\n"
            f"Phase 2 current: {phase2:.3f} A\n"
            f"Impedance: {impedance:.3f}\n"
            f"Admittance: {admittance:.3f}\n"
            f"Virtual spring torque: "
            f"{self.spring_widget.spring_torque():.3f} Nm"
        )

    def rec_meas(self, checked: bool) -> None:
        if checked:
            self.start_button.setText(
                "Stop recording measurements"
            )

            self.timer.start(
                int(UPDATE_PERIOD * 1000)
            )
        else:
            self.start_button.setText(
                "Start CAPT Motor recording measurements"
            )

            self.timer.stop()

    def closeEvent(self, event) -> None:
        self.timer.stop()
        self.sm.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1100, 850)
    window.show()

    sys.exit(app.exec())
