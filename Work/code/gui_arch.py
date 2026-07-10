import sys
import numpy as np
from multiprocessing import shared_memory

from numpy.compat import Path

import pyqtgraph as pg
from PyQt6 import QtCore 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget,
    QTabWidget, QVBoxLayout, QToolBar, QLabel
)

from matplotlib.figure import Figure 
import scipy.io as sio
import control as ct 
from control.matlab import ss, bode
import pandas as pd 

NUM_SIGNALS = 6
HISTORY_SIZE = 300
UPDATE_PERIOD = 0.05

MEM_NAME = "shared_mem"
DTYPE = np.float32

MATNAME = "stability_plots.csv"
BODE_FILE = "bode_plot.png"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")

        self.sm = shared_memory.SharedMemory(name=MEM_NAME, create=False)

        self.mem_rec_data = np.ndarray(
            (NUM_SIGNALS,),
            dtype=DTYPE,
            buffer=self.sm.buf
        )

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.home_page = QWidget()
        self.stats_page = QWidget()
        self.stability_page = QWidget()
        self.debug_page = QWidget()

        self.tabs.addTab(self.home_page, "Measurements")
        self.tabs.addTab(self.stats_page, "Impedance / Admittance")
        self.tabs.addTab(self.stability_page, "Stability Analysis")
        self.tabs.addTab(self.debug_page, "Debugging")

        self.home_layout = QVBoxLayout(self.home_page)
        self.stats_layout = QVBoxLayout(self.stats_page)
        self.stability_layout = QVBoxLayout(self.stability_page)
        self.debug_layout = QVBoxLayout(self.debug_page)

        toolbar = QToolBar("Actions")
        self.addToolBar(toolbar)

        home_action = QAction("Measurements", self)
        home_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        toolbar.addAction(home_action)

        stats_action = QAction("Impedance / Admittance", self)
        stats_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        toolbar.addAction(stats_action)

        stability_action = QAction("Stability Analysis", self)
        stability_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        toolbar.addAction(stability_action)

        debug_action = QAction("Debugging", self)
        debug_action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        toolbar.addAction(debug_action)

        self.start_button = QPushButton("Start CAPT Motor recording measurements")
        self.start_button.setCheckable(True)
        self.start_button.clicked.connect(self.rec_meas)
        self.home_layout.addWidget(self.start_button)

        # First tab: angle, torque, phase currents
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.home_layout.addWidget(self.graph_layout)

        self.angle_plot = self.graph_layout.addPlot(row=0, col=0, title="Angle (deg)")
        self.torque_plot = self.graph_layout.addPlot(row=0, col=1, title="Torque (Nm)")
        self.phase1_plot = self.graph_layout.addPlot(row=1, col=0, title="Current Phase 1 (A)")
        self.phase2_plot = self.graph_layout.addPlot(row=1, col=1, title="Current Phase 2 (A)")


        # Second tab: impedance and admittance
        self.stats_graph_layout = pg.GraphicsLayoutWidget()
        self.stats_layout.addWidget(self.stats_graph_layout)

        self.impedance_plot = self.stats_graph_layout.addPlot(row=0, col=0, title="Impedance")
        self.admittance_plot = self.stats_graph_layout.addPlot(row=1, col=0, title="Admittance")


        self.stability_title = QLabel("Bode Plot and Stability Analysis")
        self.stability_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.stability_title.setObjectName("stabilityTitle")

        self.stability_plot = QLabel()
        self.stability_plot.setObjectName("stabilityImage")
        self.stability_plot.setMinimumSize(600, 450)
        self.stability_plot.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.stability_layout.addWidget(self.stability_title)
        self.stability_layout.addWidget(
            self.stability_plot,
            stretch=1
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
                border-image: url("{bode_path}") 0 0 0 0 stretch stretch;
                background-color: white;
                border: 1px solid #808080;
                border-radius: 5px;
                margin: 10px;
            }}
            """
        )
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

        # Third tab: plain text
        self.debug_label = QLabel("Debugging information will appear here.")
        self.debug_layout.addWidget(self.debug_label)

        self.time_history = np.linspace(
            -(HISTORY_SIZE - 1) * UPDATE_PERIOD,
            0,
            HISTORY_SIZE,
            dtype=np.float32
        )

        self.angle_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.torque_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.phase1_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.phase2_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.impedance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.admittance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)

        self.angle_curve = self.angle_plot.plot(pen=pg.mkPen("#188BE9", width=2))
        self.torque_curve = self.torque_plot.plot(pen=pg.mkPen("#2AD1A7", width=2))
        self.phase1_curve = self.phase1_plot.plot(pen=pg.mkPen("#6113A1", width=2))
        self.phase2_curve = self.phase2_plot.plot(pen=pg.mkPen("#B80F77", width=2))

        self.impedance_curve = self.impedance_plot.plot(pen=pg.mkPen("#FF8800", width=2))
        self.admittance_curve = self.admittance_plot.plot(pen=pg.mkPen("#00AAFF", width=2))


        #setting up timer 
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

        # Check whether the image exists
        if not Path(BODE_FILE).exists():
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

    def read_csv(self,filename):
        file = pd.read_csv(filename)
        return file 
    def import_matlab_graphs(self, matfilename, plotfile):
        file = self.read_csv(matfilename)
        A = file['A']
        B = file['B']
        C = file['C']
        D = file['D']
        plant = ct.ss(A,B,C,D)
        bodePlot = bode(plant)
        bodePlot.savefile(plotfile)

    def update_plot(self):
        data = self.mem_rec_data.copy()

        angle = data[0]
        torque = data[1]
        phase1 = data[2]
        phase2 = data[3]
        impedance = data[4]
        admittance = data[5]

        self.angle_history = np.roll(self.angle_history, -1)
        self.torque_history = np.roll(self.torque_history, -1)
        self.phase1_history = np.roll(self.phase1_history, -1)
        self.phase2_history = np.roll(self.phase2_history, -1)
        self.impedance_history = np.roll(self.impedance_history, -1)
        self.admittance_history = np.roll(self.admittance_history, -1)

        self.angle_history[-1] = angle
        self.torque_history[-1] = torque
        self.phase1_history[-1] = phase1
        self.phase2_history[-1] = phase2
        self.impedance_history[-1] = impedance
        self.admittance_history[-1] = admittance

        self.angle_curve.setData(self.time_history, self.angle_history)
        self.torque_curve.setData(self.time_history, self.torque_history)
        self.phase1_curve.setData(self.time_history, self.phase1_history)
        self.phase2_curve.setData(self.time_history, self.phase2_history)

        self.impedance_curve.setData(self.time_history, self.impedance_history)
        self.admittance_curve.setData(self.time_history, self.admittance_history)

        self.debug_label.setText(
            f"Angle: {angle:.3f} deg\n"
            f"Torque: {torque:.3f} Nm\n"
            f"Phase 1 current: {phase1:.3f} A\n"
            f"Phase 2 current: {phase2:.3f} A\n"
            f"Impedance: {impedance:.3f}\n"
            f"Admittance: {admittance:.3f}"
        )

    def rec_meas(self, checked):
        if checked:
            self.start_button.setText("Stop recording measurements")
            self.timer.start(int(UPDATE_PERIOD * 1000))
        else:
            self.start_button.setText("Start CAPT Motor recording measurements")
            self.timer.stop()

    def closeEvent(self, event):
        self.sm.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())



(capt) C:\Users\javot\Desktop\sofia_code>python gui_arch.py
Reading styles...
Traceback (most recent call last):
  File "C:\Users\javot\Desktop\sofia_code\gui_arch.py", line 102, in update_plot
    self.curve1.setData(self.time, self.angle_history)
  File "C:\Users\javot\Desktop\capt\lib\site-packages\pyqtgraph\graphicsItems\PlotDataItem.py", line 741, in setData
    raise TypeError('When passing two unnamed argument



import sys
import numpy as np
from multiprocessing import shared_memory

import pyqtgraph as pg
from PyQt6 import QtCore
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget,
    QTabWidget, QVBoxLayout, QToolBar, QLabel
)

from matplotlib.figure import Figure 
import scipy.io as sio
import pandas as pd 

NUM_SIGNALS = 6
HISTORY_SIZE = 300
UPDATE_PERIOD = 0.05

MEM_NAME = "shared_mem"
DTYPE = np.float32

MATNAME = "stability_plots.csv"
BODE_FILE = "bode_plot.png"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")

        self.sm = shared_memory.SharedMemory(name=MEM_NAME, create=False)

        self.mem_rec_data = np.ndarray(
            (NUM_SIGNALS,),
            dtype=DTYPE,
            buffer=self.sm.buf
        )

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.home_page = QWidget()
        self.stats_page = QWidget()
        self.stability_page = QWidget()
        self.debug_page = QWidget()

        self.tabs.addTab(self.home_page, "Measurements")
        self.tabs.addTab(self.stats_page, "Impedance / Admittance")
        self.tabs.addTab(self.stability_page, "Stability Analysis")
        self.tabs.addTab(self.debug_page, "Debugging")

        self.home_layout = QVBoxLayout(self.home_page)
        self.stats_layout = QVBoxLayout(self.stats_page)
        self.stability_layout = QVBoxLayout(self.stability_page)
        self.debug_layout = QVBoxLayout(self.debug_page)

        toolbar = QToolBar("Actions")
        self.addToolBar(toolbar)

        home_action = QAction("Measurements", self)
        home_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        toolbar.addAction(home_action)

        stats_action = QAction("Impedance / Admittance", self)
        stats_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        toolbar.addAction(stats_action)

        stability_action = QAction("Stability Analysis", self)
        stability_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        toolbar.addAction(stability_action)

        debug_action = QAction("Debugging", self)
        debug_action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        toolbar.addAction(debug_action)

        self.start_button = QPushButton("Start CAPT Motor recording measurements")
        self.start_button.setCheckable(True)
        self.start_button.clicked.connect(self.rec_meas)
        self.home_layout.addWidget(self.start_button)

        # First tab: angle, torque, phase currents
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.home_layout.addWidget(self.graph_layout)

        self.angle_plot = self.graph_layout.addPlot(row=0, col=0, title="Angle (deg)")
        self.torque_plot = self.graph_layout.addPlot(row=0, col=1, title="Torque (Nm)")
        self.phase1_plot = self.graph_layout.addPlot(row=1, col=0, title="Current Phase 1 (A)")
        self.phase2_plot = self.graph_layout.addPlot(row=1, col=1, title="Current Phase 2 (A)")


        # Second tab: impedance and admittance
        self.stats_graph_layout = pg.GraphicsLayoutWidget()
        self.stats_layout.addWidget(self.stats_graph_layout)

        self.impedance_plot = self.stats_graph_layout.addPlot(row=0, col=0, title="Impedance")
        self.admittance_plot = self.stats_graph_layout.addPlot(row=1, col=0, title="Admittance")

        self.stability_plot = QLabel()
        pixmap = QPixmap(BODE_FILE)
        self.stability_plot.setPixmap(pixmap)
        self.stability_layout.addWidget(self.stability_plot)

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

        # Third tab: plain text
        self.debug_label = QLabel("Debugging information will appear here.")
        self.debug_layout.addWidget(self.debug_label)

        self.time_history = np.linspace(
            -(HISTORY_SIZE - 1) * UPDATE_PERIOD,
            0,
            HISTORY_SIZE,
            dtype=np.float32
        )

        self.angle_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.torque_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.phase1_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.phase2_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.impedance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.admittance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)

        self.angle_curve = self.angle_plot.plot(pen=pg.mkPen("#188BE9", width=2))
        self.torque_curve = self.torque_plot.plot(pen=pg.mkPen("#2AD1A7", width=2))
        self.phase1_curve = self.phase1_plot.plot(pen=pg.mkPen("#6113A1", width=2))
        self.phase2_curve = self.phase2_plot.plot(pen=pg.mkPen("#B80F77", width=2))

        self.impedance_curve = self.impedance_plot.plot(pen=pg.mkPen("#FF8800", width=2))
        self.admittance_curve = self.admittance_plot.plot(pen=pg.mkPen("#00AAFF", width=2))


        #setting up timer 
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

    def read_csv(self,filename):
        file = pd.read_csv(filename)

    def import_matlab_graphs(self, matfilename, plotfile):
        plant = self.read_csv(matfilename)
        bodePlot = Figure(figsize=(20,20), dpi=100)
        ct.bode_plot(plant, dB=True, deg=True, margins= True)
        bodePlot.savefile(plotfile)

    def update_plot(self):
        data = self.mem_rec_data.copy()

        angle = data[0]
        torque = data[1]
        phase1 = data[2]
        phase2 = data[3]
        impedance = data[4]
        admittance = data[5]

        self.angle_history = np.roll(self.angle_history, -1)
        self.torque_history = np.roll(self.torque_history, -1)
        self.phase1_history = np.roll(self.phase1_history, -1)
        self.phase2_history = np.roll(self.phase2_history, -1)
        self.impedance_history = np.roll(self.impedance_history, -1)
        self.admittance_history = np.roll(self.admittance_history, -1)

        self.angle_history[-1] = angle
        self.torque_history[-1] = torque
        self.phase1_history[-1] = phase1
        self.phase2_history[-1] = phase2
        self.impedance_history[-1] = impedance
        self.admittance_history[-1] = admittance

        self.angle_curve.setData(self.time_history, self.angle_history)
        self.torque_curve.setData(self.time_history, self.torque_history)
        self.phase1_curve.setData(self.time_history, self.phase1_history)
        self.phase2_curve.setData(self.time_history, self.phase2_history)

        self.impedance_curve.setData(self.time_history, self.impedance_history)
        self.admittance_curve.setData(self.time_history, self.admittance_history)

        self.debug_label.setText(
            f"Angle: {angle:.3f} deg\n"
            f"Torque: {torque:.3f} Nm\n"
            f"Phase 1 current: {phase1:.3f} A\n"
            f"Phase 2 current: {phase2:.3f} A\n"
            f"Impedance: {impedance:.3f}\n"
            f"Admittance: {admittance:.3f}"
        )

    def rec_meas(self, checked):
        if checked:
            self.start_button.setText("Stop recording measurements")
            self.timer.start(int(UPDATE_PERIOD * 1000))
        else:
            self.start_button.setText("Start CAPT Motor recording measurements")
            self.timer.stop()

    def closeEvent(self, event):
        self.sm.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
# import sys
# import numpy as np
# from multiprocessing import shared_memory

# import pyqtgraph as pg
# from PyQt6 import QtCore
# from PyQt6.QtWidgets import QMainWindow, QApplication


# BUFFER_SIZE = 8
# MEM_NAME = "shared_mem"
# DTYPE = np.float32

# STYLES_FILE = "gui_styles.qss"


# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         #setting up modern styles :)
#         self.setStyleSheet(read_file, STYLES_FILE)

#         #shared memory for data acquisition 
#         self.sm = shared_memory.SharedMemory(
#             name=MEM_NAME,
#             create=False
#         )

#         self.mem_rec_data = np.ndarray(
#             (BUFFER_SIZE,),
#             dtype=DTYPE,
#             buffer=self.sm.buf
#         )

#         self.setWindowTitle("CAPT Motor Dashboard")

#         self.plot_graph = pg.PlotWidget()
#         self.plot_graph.setBackground("w")
#         self.setCentralWidget(self.plot_graph)

#         self.plot_graph.setTitle("Shared Memory Data", color="b", size="18pt")
#         self.plot_graph.setLabel("left", "Value", color="b")
#         self.plot_graph.setLabel("bottom", "Sample", color="b")
#         self.plot_graph.showGrid(x=True, y=True)

#         self.x = np.arange(BUFFER_SIZE)
#         self.y = self.mem_rec_data.copy()

#         pen = pg.mkPen(color=(255, 0, 255), width=2)

#         self.curve = self.plot_graph.plot(
#             self.x,
#             self.y,
#             pen=pen,
#             symbol="o",
#             symbolSize=8,
#             symbolBrush="b"
#         )


#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update_plot)
#         self.timer.start(50)

#     def update_plot(self):
#         self.y = self.mem_rec_data.copy()
#         self.curve.setData(self.x, self.y)
#         print("GUI read:", self.y)

#     def closeEvent(self, event):
#         self.sm.close()
#         event.accept()
#     def read_file(self, filename="styles"):
#          with open(filename, "r") as f:
#              print("Reading styles...")
#              return f.read()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec())import sys
import sys
import numpy as np
from multiprocessing import shared_memory

import pyqtgraph as pg
from PyQt6 import QtCore
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget,
    QTabWidget, QVBoxLayout, QToolBar, QLabel
)

from matplotlib.figure import Figure 
import scipy.io as sio
import pandas as pd 

NUM_SIGNALS = 6
HISTORY_SIZE = 300
UPDATE_PERIOD = 0.05

MEM_NAME = "shared_mem"
DTYPE = np.float32

MATNAME = "stability_plots.csv"
BODE_FILE = "bode_plot.png"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")

        self.sm = shared_memory.SharedMemory(name=MEM_NAME, create=False)

        self.mem_rec_data = np.ndarray(
            (NUM_SIGNALS,),
            dtype=DTYPE,
            buffer=self.sm.buf
        )

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.home_page = QWidget()
        self.stats_page = QWidget()
        self.stability_page = QWidget()
        self.debug_page = QWidget()

        self.tabs.addTab(self.home_page, "Measurements")
        self.tabs.addTab(self.stats_page, "Impedance / Admittance")
        self.tabs.addTab(self.stability_page, "Stability Analysis")
        self.tabs.addTab(self.debug_page, "Debugging")

        self.home_layout = QVBoxLayout(self.home_page)
        self.stats_layout = QVBoxLayout(self.stats_page)
        self.stability_layout = QVBoxLayout(self.stability_page)
        self.debug_layout = QVBoxLayout(self.debug_page)

        toolbar = QToolBar("Actions")
        self.addToolBar(toolbar)

        home_action = QAction("Measurements", self)
        home_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        toolbar.addAction(home_action)

        stats_action = QAction("Impedance / Admittance", self)
        stats_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        toolbar.addAction(stats_action)

        stability_action = QAction("Stability Analysis", self)
        stability_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        toolbar.addAction(stability_action)

        debug_action = QAction("Debugging", self)
        debug_action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        toolbar.addAction(debug_action)

        self.start_button = QPushButton("Start CAPT Motor recording measurements")
        self.start_button.setCheckable(True)
        self.start_button.clicked.connect(self.rec_meas)
        self.home_layout.addWidget(self.start_button)

        # First tab: angle, torque, phase currents
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.home_layout.addWidget(self.graph_layout)

        self.angle_plot = self.graph_layout.addPlot(row=0, col=0, title="Angle (deg)")
        self.torque_plot = self.graph_layout.addPlot(row=0, col=1, title="Torque (Nm)")
        self.phase1_plot = self.graph_layout.addPlot(row=1, col=0, title="Current Phase 1 (A)")
        self.phase2_plot = self.graph_layout.addPlot(row=1, col=1, title="Current Phase 2 (A)")


        # Second tab: impedance and admittance
        self.stats_graph_layout = pg.GraphicsLayoutWidget()
        self.stats_layout.addWidget(self.stats_graph_layout)

        self.impedance_plot = self.stats_graph_layout.addPlot(row=0, col=0, title="Impedance")
        self.admittance_plot = self.stats_graph_layout.addPlot(row=1, col=0, title="Admittance")

        self.stability_plot = QLabel()
        pixmap = QPixmap(BODE_FILE)
        self.stability_plot.setPixmap(pixmap)
        self.stability_layout.addWidget(self.stability_plot)

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

        # Third tab: plain text
        self.debug_label = QLabel("Debugging information will appear here.")
        self.debug_layout.addWidget(self.debug_label)

        self.time_history = np.linspace(
            -(HISTORY_SIZE - 1) * UPDATE_PERIOD,
            0,
            HISTORY_SIZE,
            dtype=np.float32
        )

        self.angle_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.torque_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.phase1_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.phase2_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.impedance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)
        self.admittance_history = np.zeros(HISTORY_SIZE, dtype=np.float32)

        self.angle_curve = self.angle_plot.plot(pen=pg.mkPen("#188BE9", width=2))
        self.torque_curve = self.torque_plot.plot(pen=pg.mkPen("#2AD1A7", width=2))
        self.phase1_curve = self.phase1_plot.plot(pen=pg.mkPen("#6113A1", width=2))
        self.phase2_curve = self.phase2_plot.plot(pen=pg.mkPen("#B80F77", width=2))

        self.impedance_curve = self.impedance_plot.plot(pen=pg.mkPen("#FF8800", width=2))
        self.admittance_curve = self.admittance_plot.plot(pen=pg.mkPen("#00AAFF", width=2))


        #setting up timer 
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

    def read_csv(self,filename):
        file = pd.read_csv(filename)

    def import_matlab_graphs(self, matfilename, plotfile):
        plant = self.read_csv(matfilename)
        bodePlot = Figure(figsize=(20,20), dpi=100)
        ct.bode_plot(plant, dB=True, deg=True, margins= True)
        bodePlot.savefile(plotfile)

    def update_plot(self):
        data = self.mem_rec_data.copy()

        angle = data[0]
        torque = data[1]
        phase1 = data[2]
        phase2 = data[3]
        impedance = data[4]
        admittance = data[5]

        self.angle_history = np.roll(self.angle_history, -1)
        self.torque_history = np.roll(self.torque_history, -1)
        self.phase1_history = np.roll(self.phase1_history, -1)
        self.phase2_history = np.roll(self.phase2_history, -1)
        self.impedance_history = np.roll(self.impedance_history, -1)
        self.admittance_history = np.roll(self.admittance_history, -1)

        self.angle_history[-1] = angle
        self.torque_history[-1] = torque
        self.phase1_history[-1] = phase1
        self.phase2_history[-1] = phase2
        self.impedance_history[-1] = impedance
        self.admittance_history[-1] = admittance

        self.angle_curve.setData(self.time_history, self.angle_history)
        self.torque_curve.setData(self.time_history, self.torque_history)
        self.phase1_curve.setData(self.time_history, self.phase1_history)
        self.phase2_curve.setData(self.time_history, self.phase2_history)

        self.impedance_curve.setData(self.time_history, self.impedance_history)
        self.admittance_curve.setData(self.time_history, self.admittance_history)

        self.debug_label.setText(
            f"Angle: {angle:.3f} deg\n"
            f"Torque: {torque:.3f} Nm\n"
            f"Phase 1 current: {phase1:.3f} A\n"
            f"Phase 2 current: {phase2:.3f} A\n"
            f"Impedance: {impedance:.3f}\n"
            f"Admittance: {admittance:.3f}"
        )

    def rec_meas(self, checked):
        if checked:
            self.start_button.setText("Stop recording measurements")
            self.timer.start(int(UPDATE_PERIOD * 1000))
        else:
            self.start_button.setText("Start CAPT Motor recording measurements")
            self.timer.stop()

    def closeEvent(self, event):
        self.sm.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
