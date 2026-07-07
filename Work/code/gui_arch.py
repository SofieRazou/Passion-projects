import sys
from multiprocessing import shared_memory
from  SManager import create_mem

import time
import pandas as pd
import numpy as np
import random 
import matplotlib.pyplot as plt 

import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QVBoxLayout, QWidget


BUFFER_SIZE = 4
sm, mem_rec_data = create_mem(mem_name="udp_share", size=BUFFER_SIZE)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground('w')
        pen = pg.mkPen(color=(255,0,255), width=2)


        self.setCentralWidget(self.plot_graph)
    
        self.plot_graph.setTitle("Motor Torque over Time" , color= "b", size = "18pt")
        self.plot_graph.setLabel('left', 'Torque (Nm)', color='b', size=30)
        self.plot_graph.setLabel('bottom', 'Time (s)', color='b', size=30)
        self.plot_graph.showGrid(x=True, y=True)
        self.plot_graph.setXRange(0, 10)
        self.plot_graph.setYRange(20,30)

        self.time = list(range(10))
        self.torque = mem_rec_data.tolist()  # Fetch received-over-UDP data from shared memory
        self.plot_graph.plot(self.time, self.torque, name="Torque", pen=pen, symbol='o', symbolSize=10, symbolBrush=('b'))

    

    #dynamic data update
    def upd_plot(self, sampling_rate, torque_data):
        fetched_data = self.fetch_data_from_mem(mem_name="udp_share", size=BUFFER_SIZE)
        print(f"Fetched data from shared memory: {fetched_data}")
app  = QApplication([])
window = MainWindow()
window.show()
app.exec()



