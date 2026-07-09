(capt) C:\Users\javot\Desktop\sofia_code>python gui_arch.py
Reading styles...
Traceback (most recent call last):
  File "C:\Users\javot\Desktop\sofia_code\gui_arch.py", line 102, in update_plot
    self.curve1.setData(self.time, self.angle_history)
  File "C:\Users\javot\Desktop\capt\lib\site-packages\pyqtgraph\graphicsItems\PlotDataItem.py", line 741, in setData
    raise TypeError('When passing two unnamed argument
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
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget,
    QTabWidget, QVBoxLayout, QToolBar, QLabel
)

NUM_SIGNALS = 4
HISTORY_SIZE = 300
UPDATE_PERIOD = 0.05

MEM_NAME = "shared_mem"
DTYPE = np.float32

PAGE_NAMES = ["Home", "Stats", "Debugging"]


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

        # Main tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create pages
        self.home_page = QWidget()
        self.stats_page = QWidget()
        self.debug_page = QWidget()

        self.tabs.addTab(self.home_page, "Home")
        self.tabs.addTab(self.stats_page, "Stats")
        self.tabs.addTab(self.debug_page, "Debugging")

        # Layouts for each page
        self.home_layout = QVBoxLayout(self.home_page)
        self.stats_layout = QVBoxLayout(self.stats_page)
        self.debug_layout = QVBoxLayout(self.debug_page)

        # Toolbar
        toolbar = QToolBar("Actions")
        self.addToolBar(toolbar)

        home_action = QAction("Home", self)
        home_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        toolbar.addAction(home_action)

        stats_action = QAction("Stats", self)
        stats_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        toolbar.addAction(stats_action)

        debug_action = QAction("Debugging", self)
        debug_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        toolbar.addAction(debug_action)

        # First tab: 4 regular graphs
        self.start_button = QPushButton("Start CAPT Motor recording measurements")
        self.start_button.setCheckable(True)
        self.start_button.clicked.connect(self.rec_meas)
        self.home_layout.addWidget(self.start_button)

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.home_layout.addWidget(self.graph_layout)

        self.plot_graph1 = self.graph_layout.addPlot(row=0, col=0, title="Angle (deg)")
        self.plot_graph2 = self.graph_layout.addPlot(row=0, col=1, title="Torque (Nm)")
        self.plot_graph3 = self.graph_layout.addPlot(row=1, col=0, title="Current Phase 1 (A)")
        self.plot_graph4 = self.graph_layout.addPlot(row=1, col=1, title="Current Phase 2 (A)")

        self.plots = [
            self.plot_graph1,
            self.plot_graph2,
            self.plot_graph3,
            self.plot_graph4,
        ]

        for plot in self.plots:
            plot.setLabel("left", "Value")
            plot.setLabel("bottom", "Time", units="s")
            plot.showGrid(x=True, y=True, alpha=0.3)

        # Second tab: 2 graphs
        self.stats_graph_layout = pg.GraphicsLayoutWidget()
        self.stats_layout.addWidget(self.stats_graph_layout)

        self.stats_plot1 = self.stats_graph_layout.addPlot(row=0, col=0, title="Angle vs Torque")
        self.stats_plot2 = self.stats_graph_layout.addPlot(row=1, col=0, title="Current Difference")

        self.stats_plot1.showGrid(x=True, y=True, alpha=0.3)
        self.stats_plot2.showGrid(x=True, y=True, alpha=0.3)

        # Third tab: text
        self.debug_label = QLabel("Debugging information will appear here.")
        self.debug_layout.addWidget(self.debug_label)

        # Data history
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
        self.current_diff_history = np.zeros(HISTORY_SIZE, dtype=np.float32)

        # Curves for first tab
        self.curve1 = self.plot_graph1.plot(pen=pg.mkPen("#0078D7", width=2))
        self.curve2 = self.plot_graph2.plot(pen=pg.mkPen("#2AD1A7", width=2))
        self.curve3 = self.plot_graph3.plot(pen=pg.mkPen("#6113A1", width=2))
        self.curve4 = self.plot_graph4.plot(pen=pg.mkPen("#B80F77", width=2))

        # Curves for second tab
        self.stats_curve1 = self.stats_plot1.plot(pen=pg.mkPen("#FF8800", width=2))
        self.stats_curve2 = self.stats_plot2.plot(pen=pg.mkPen("#00AAFF", width=2))

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

    def update_plot(self):
        data = self.mem_rec_data.copy()

        angle = data[0]
        torque = data[1]
        phase1 = data[2]
        phase2 = data[3]

        self.angle_history = np.roll(self.angle_history, -1)
        self.torque_history = np.roll(self.torque_history, -1)
        self.phase1_history = np.roll(self.phase1_history, -1)
        self.phase2_history = np.roll(self.phase2_history, -1)
        self.current_diff_history = np.roll(self.current_diff_history, -1)

        self.angle_history[-1] = angle
        self.torque_history[-1] = torque
        self.phase1_history[-1] = phase1
        self.phase2_history[-1] = phase2
        self.current_diff_history[-1] = phase1 - phase2

        # First tab plots
        self.curve1.setData(self.time_history, self.angle_history)
        self.curve2.setData(self.time_history, self.torque_history)
        self.curve3.setData(self.time_history, self.phase1_history)
        self.curve4.setData(self.time_history, self.phase2_history)

        # Second tab plots
        self.stats_curve1.setData(self.angle_history, self.torque_history)
        self.stats_curve2.setData(self.time_history, self.current_diff_history)

        # Third tab text
        self.debug_label.setText(
            f"Angle: {angle:.3f} deg\n"
            f"Torque: {torque:.3f} Nm\n"
            f"Phase 1 current: {phase1:.3f} A\n"
            f"Phase 2 current: {phase2:.3f} A"
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
