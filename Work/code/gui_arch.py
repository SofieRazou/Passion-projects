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
import time
import numpy as np
from multiprocessing import shared_memory

import pyqtgraph as pg
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget


NUM_SIGNALS = 4
HISTORY_SIZE = 300
UPDATE_PERIOD = 0.05

MEM_NAME = "shared_mem"
DTYPE = np.float32

STYLES_FILE = "gui_styles.qss"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setStyleSheet(self.read_file(STYLES_FILE))
        except FileNotFoundError:
            print("Style file not found, continuing without QSS.")

        self.sm = shared_memory.SharedMemory(
            name=MEM_NAME,
            create=False
        )

        self.mem_rec_data = np.ndarray(
            (NUM_SIGNALS,),
            dtype=DTYPE,
            buffer=self.sm.buf
        )

        self.setWindowTitle("CAPT Motor Dashboard")

        self.layout = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.layout)

        #setting-up start-gui button 

        self.start_button = QPushButton("Start CAPT Motor recording measurements")
        self.start_button.clicked.connect(self.rec_meas)

        self.layout.addWidget(self.start_button)
        

        self.plot_graph1 = self.layout.addPlot(row=0, col=0, title="Angle (deg)")
        self.plot_graph2 = self.layout.addPlot(row=0, col=1, title="Torque (Nm)")
        self.plot_graph3 = self.layout.addPlot(row=1, col=0, title="Current Phase 1 (A)")
        self.plot_graph4 = self.layout.addPlot(row=1, col=1, title="Current Phase 2 (A)")

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

        self.curve1 = self.plot_graph1.plot(pen=pg.mkPen("#0078D7", width=2))
        self.curve2 = self.plot_graph2.plot(pen=pg.mkPen("#E67E22", width=2))
        self.curve3 = self.plot_graph3.plot(pen=pg.mkPen("#2ECC71", width=2))
        self.curve4 = self.plot_graph4.plot(pen=pg.mkPen("#8E44AD", width=2))

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

        self.angle_history[-1] = angle
        self.torque_history[-1] = torque
        self.phase1_history[-1] = phase1
        self.phase2_history[-1] = phase2

        self.curve1.setData(self.time_history, self.angle_history)
        self.curve2.setData(self.time_history, self.torque_history)
        self.curve3.setData(self.time_history, self.phase1_history)
        self.curve4.setData(self.time_history, self.phase2_history)

        print("GUI read:", data)

    def closeEvent(self, event):
        self.sm.close()
        event.accept()
    
    def rec_meas(self, checked):
        if checked:
            print("Measurement recording starting...")
            self.start_button.setText("Click button to stop recording measurements")
            self.timer.start(int(UPDATE_PERIOD * 1000))
        else:
            print("Recording stopped")
            self.start_button.setText("Click button to start recording measurements")
            self.timer.stop()


    def read_file(self, filename):
        with open(filename, "r") as f:
            print("Reading styles...")
            return f.read()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
