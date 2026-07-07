import sys
import numpy as np
from multiprocessing import shared_memory

import pyqtgraph as pg
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QApplication


BUFFER_SIZE = 8
MEM_NAME = "shared_mem"
DTYPE = np.float32


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground("w")
        self.setCentralWidget(self.plot_graph)

        self.plot_graph.setTitle("Shared Memory Data", color="b", size="18pt")
        self.plot_graph.setLabel("left", "Value", color="b")
        self.plot_graph.setLabel("bottom", "Sample", color="b")
        self.plot_graph.showGrid(x=True, y=True)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())





