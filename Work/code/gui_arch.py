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


self.animation_timer = QtCore.QTimer(self)
self.animation_timer.timeout.connect(self.advance_animation)
self.animation_timer.start(30)

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
        self.create_impedance_page()
        self.create_spring_page()
        self.create_stability_page()
        self.create_debug_page()

        self.create_signal_histories()
        self.create_plot_curves()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(
            self.update_plot
        )

        self.check_bode_image()

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
                self.tabs.setCurrentIndex(
                    index
                )
            )

            toolbar.addAction(action)

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

    def create_impedance_page(self) -> None:
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

    def create_spring_page(self) -> None:
        title = QLabel(
            "Asymmetric Rotational Spring Environment"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(
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
            QLabel("Positive-side κ:"),
            0,
            0,
        )

        controls_layout.addWidget(
            self.kappa_positive_input,
            0,
            1,
        )

        controls_layout.addWidget(
            QLabel("Negative-side κ:"),
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

        self.spring_layout.addWidget(title)

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

    def create_signal_histories(self) -> None:
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

    def create_plot_curves(self) -> None:
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

        # Update wheel and springs using the live angle.
        self.spring_widget.set_angle(angle)

        virtual_torque = (
            self.spring_widget.spring_torque()
        )

        active_region = (
            self.spring_widget.active_region()
        )

        self.debug_label.setText(
            f"Angle: {angle:.3f} deg\n"
            f"Torque: {torque:.3f} Nm\n"
            f"Phase 1 current: {phase1:.3f} A\n"
            f"Phase 2 current: {phase2:.3f} A\n"
            f"Impedance: {impedance:.3f}\n"
            f"Admittance: {admittance:.3f}\n\n"
            f"Spring region: {active_region}\n"
            f"Virtual spring torque: "
            f"{virtual_torque:.4f} Nm"
        )

    def rec_meas(self, checked: bool) -> None:
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

    def closeEvent(self, event) -> None:
        self.timer.stop()

        try:
            self.sm.close()
        finally:
            event.accept()


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

    window.resize(1150, 850)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
