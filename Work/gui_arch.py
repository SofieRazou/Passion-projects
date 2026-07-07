import sys
import time
import pandas as pd
import random 

import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QTimer

from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QVBoxLayout, QWidget



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground('w')
        pen = pg.mkPen(color=(255,0,255), width=2)


        self.setCentralWidget(self.plot_graph)
        styles = {"color":"b", "font-size":"18px"}
        self.plot_graph.setTitle("Motor Torque over Time" , color= "b", size = "18pt")
        self.plot_graph.setLabel('left', 'Torque (Nm)', color='b', size=30)
        self.plot_graph.setLabel('bottom', 'Time (s)', color='b', size=30)
        self.plot_graph.showGrid(x=True, y=True)
        self.plot_graph.setXRange(0, 10)
        self.plot_graph.setYRange(20,30)

        self.time = list(range(10))
        self.torque = [random.uniform(20,30) for _ in range(10)] 
        self.plot_graph.plot(self.time, self.torque, name="Torque", pen=pen, symbol='o', symbolSize=10, symbolBrush=('b'))


        #dynamic data update
        self.timer = QTimer()
        self.timer.setInterval(1000) #in ms 
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()
        self.line = self.plot_graph.plot(pen=pen, symbol='o', symbolSize=10, symbolBrush=('b'))

    def update_plot(self):
        self.time = self.time[1:]
        self.time.append(self.time[-1] + 1)
        self.torque = self.torque[1:]
        self.torque.append(random.uniform(20,30))
        self.plot_graph.line.setData(self.time, self.torque)        

app  = QApplication([])
window = MainWindow()
window.show()
app.exec()





