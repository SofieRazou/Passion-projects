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
#     sys.exit(app.exec())


import sys
import numpy as np
from multiprocessing import shared_memory

import pyqtgraph as pg
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QApplication


BUFFER_SIZE = 8
MEM_NAME = "shared_mem"
DTYPE = np.float32

STYLES_FILE = "gui_styles.qss"
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        #setting up modern styles :)
        self.setStyleSheet(self.read_file(STYLES_FILE), STYLES_FILE)


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

        #Layout configuration
        layout = pg.GraphicsLayoutWidget()
        self.setCentralWidget(layout)

        self.plot_graph1 = pg.PlotWidget()
        self.plot_graph2 = pg.PlotWidget()
        self.plot_graph1.setBackground("w")
        self.plot_graph2.setBackground("w")
        self.plot_graph3.setBackground("w")
        self.plot_graph4.setBackground("w")
        self.setCentralWidget(self.plot_graph1)
        self.setCentralWidget(self.plot_graph2)
        self.setCentralWidget(self.plot_graph3)
        self.setCentralWidget(self.plot_graph4)

        #positioning plots 
        self.addWidget(self.plot_graph1, 0,0)
        self.addWidget(self.plot_graph2, 0,1)
        self.addWidget(self.plot_graph3,1, 0)
        self.addWidget(self.plot_graph4,1,1)


        self.plot_graph1.setTitle("Angle(deg)", color="b", size="18pt")
        self.plot_graph1.setLabel("left", "Value", color="b")
        self.plot_graph1.setLabel("bottom", "Sample", color="b")
        self.plot_graph1.showGrid(x=True, y=True)

        self.plot_graph2.setTitle("Torque(Nm)", color="b", size="18pt")
        self.plot_graph2.setLabel("left", "Value", color="b")
        self.plot_graph2.setLabel("bottom", "Sample", color="b")
        self.plot_graph2.showGrid(x=True, y=True)


        self.plot_graph3.setTitle("Current Phase 1 (A)", color="b", size="18pt")
        self.plot_graph3.setLabel("left", "Value", color="b")
        self.plot_graph3.setLabel("bottom", "Sample", color="b")
        self.plot_graph3.showGrid(x=True, y=True)

        self.plot_graph4.setTitle("Current Phase 2 (A)", color="b", size="18pt")
        self.plot_graph4.setLabel("left", "Value", color="b")
        self.plot_graph4.setLabel("bottom", "Sample", color="b")
        self.plot_graph4.showGrid(x=True, y=True)

        self.x = np.arange(BUFFER_SIZE)
        self.y = self.mem_rec_data.copy()

        pen = pg.mkPen(color=(255, 0, 255), width=2)

        self.curve = self.plot_graph.plot(
            self.x,
            self.y,
            pen=pen,
            symbol="o",
            symbolSize=8,
            symbolBrush="b"
        )

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

    def update_plot(self):
        self.y = self.mem_rec_data.copy()
        self.curve.setData(self.x, self.y)
        print("GUI read:", self.y)

    def closeEvent(self, event):
        self.sm.close()
        event.accept()
    
    #read styles file function
    def read_file(self, filename="styles"):
         with open(filename, "r") as f:
             print("Reading styles...")
             return f.read()
         
    def show_plots(self, plots):
        for p in plots:
            window.p

plts = [plot_graph1, plot_graph2, plot_graph3, plot_graph4]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.show_plots(plts)

    sys.exit(app.exec())




