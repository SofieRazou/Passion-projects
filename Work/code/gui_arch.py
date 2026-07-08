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
import numpy as np
from multiprocessing import shared_memory

import pyqtgraph as pg
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QApplication


BUFFER_SIZE = 16
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
            (BUFFER_SIZE,),
            dtype=DTYPE,
            buffer=self.sm.buf
        )

        self.setWindowTitle("CAPT Motor Dashboard")

        # Main layout for multiple plots
        self.layout = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.layout)

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
            plot.setLabel("bottom", "Sample")
            plot.showGrid(x=True, y=True)
            plot.setMouseEnabled(x=True, y=True)

        self.x = np.arange(BUFFER_SIZE)

        pen = pg.mkPen(color=(255, 0, 255), width=2)

        self.curve1 = self.plot_graph1.plot(pen=pen, symbol="o", symbolSize=8, symbolBrush="b")
        self.curve2 = self.plot_graph2.plot(pen=pen, symbol="o", symbolSize=8, symbolBrush="b")
        self.curve3 = self.plot_graph3.plot(pen=pen, symbol="o", symbolSize=8, symbolBrush="b")
        self.curve4 = self.plot_graph4.plot(pen=pen, symbol="o", symbolSize=8, symbolBrush="b")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

    def update_plot(self):
        data = self.mem_rec_data.copy()

        # Example split:
        # data[0:2] angle-related
        # data[2:4] torque-related
        # data[4:6] current phase 1
        # data[6:8] current phase 2

        self.curve1.setData(np.arange(2), data[0:2])
        self.curve2.setData(np.arange(2), data[2:4])
        self.curve3.setData(np.arange(2), data[4:6])
        self.curve4.setData(np.arange(2), data[6:8])

        print("GUI read:", data)

    def closeEvent(self, event):
        self.sm.close()
        event.accept()

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



