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
import csv
import socket
import struct
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# CONFIGURATION
# ============================================================

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

# The order must match the dSPACE UDP transmission vector.
SIGNAL_NAMES = [
    "Angle",
    "Torque",
    "Angular velocity",
    "Phase current 1",
    "Phase current 2",
    "Controller output",
]

SIGNAL_UNITS = [
    "rad",
    "Nm",
    "rad/s",
    "A",
    "A",
    "Nm",
]

NUM_SIGNALS = len(SIGNAL_NAMES)

# dSPACE sends six little-endian float32 values.
PACKET_FORMAT = f"<{NUM_SIGNALS}f"
EXPECTED_PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

# Number of seconds shown in the plots.
HISTORY_SECONDS = 10

# Expected UDP transmission frequency.
RECEIVE_FREQUENCY = 100

# Maximum number of stored samples.
HISTORY_SIZE = HISTORY_SECONDS * RECEIVE_FREQUENCY

# GUI redraw interval. 20 ms corresponds to approximately 50 FPS.
GUI_UPDATE_MS = 20

CSV_FILE = Path("dspace_live_recording.csv")


# ============================================================
# UDP RECEIVER THREAD
# ============================================================

class UDPReceiver(QThread):
    """
    Receives UDP packets without blocking the graphical interface.
    """

    packet_received = pyqtSignal(float, object)
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.running = False
        self.sock = None

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Allows the port to be reused after restarting the program.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.sock.bind((UDP_IP, UDP_PORT))

            # A timeout allows the thread to check whether it should stop.
            self.sock.settimeout(0.5)

            self.running = True

            self.status_changed.emit(
                f"Listening on {UDP_IP}:{UDP_PORT}"
            )

            while self.running:
                try:
                    packet, sender = self.sock.recvfrom(4096)

                except socket.timeout:
                    continue

                except OSError:
                    break

                if len(packet) != EXPECTED_PACKET_SIZE:
                    self.status_changed.emit(
                        f"Rejected packet from {sender[0]}: "
                        f"received {len(packet)} bytes, "
                        f"expected {EXPECTED_PACKET_SIZE} bytes"
                    )
                    continue

                try:
                    values = struct.unpack(PACKET_FORMAT, packet)

                except struct.error as error:
                    self.status_changed.emit(
                        f"Packet decoding error: {error}"
                    )
                    continue

                timestamp = time.perf_counter()

                # Send timestamp and values to the GUI thread.
                self.packet_received.emit(timestamp, values)

        except OSError as error:
            self.status_changed.emit(f"UDP error: {error}")

        finally:
            if self.sock is not None:
                self.sock.close()

            self.sock = None
            self.running = False

    def stop(self):
        self.running = False

        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass

        self.wait(2000)


# ============================================================
# MAIN GUI
# ============================================================

class LivePlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("dSPACE Live Signal Monitor")
        self.resize(1200, 900)

        # Relative time reference.
        self.start_time = None

        # Buffers for timestamps and all six signals.
        self.time_buffer = deque(maxlen=HISTORY_SIZE)

        self.signal_buffers = [
            deque(maxlen=HISTORY_SIZE)
            for _ in range(NUM_SIGNALS)
        ]

        # Latest values received from the UDP thread.
        self.latest_timestamp = None
        self.latest_values = None

        # CSV state.
        self.csv_handle = None
        self.csv_writer = None

        self.received_packet_count = 0
        self.last_packet_display_count = 0

        self.setup_interface()
        self.setup_receiver()
        self.setup_timers()

    def setup_interface(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        self.status_label = QLabel(
            f"Waiting for dSPACE data on UDP port {UDP_PORT}..."
        )
        main_layout.addWidget(self.status_label)

        self.value_label = QLabel("No signal values received")
        main_layout.addWidget(self.value_label)

        self.record_checkbox = QCheckBox("Record received samples to CSV")
        self.record_checkbox.stateChanged.connect(
            self.set_csv_recording
        )
        main_layout.addWidget(self.record_checkbox)

        self.clear_button = QPushButton("Clear plots")
        self.clear_button.clicked.connect(self.clear_plots)
        main_layout.addWidget(self.clear_button)

        self.plot_widget = pg.GraphicsLayoutWidget()
        main_layout.addWidget(self.plot_widget)

        self.plots = []
        self.curves = []

        for index, (name, unit) in enumerate(
            zip(SIGNAL_NAMES, SIGNAL_UNITS)
        ):
            plot = self.plot_widget.addPlot(
                row=index,
                col=0,
                title=name,
            )

            plot.setLabel("left", name, units=unit)
            plot.setLabel("bottom", "Time", units="s")
            plot.showGrid(x=True, y=True, alpha=0.3)

            curve = plot.plot()

            self.plots.append(plot)
            self.curves.append(curve)

        # Keep all time axes synchronized.
        for plot in self.plots[1:]:
            plot.setXLink(self.plots[0])

        self.setCentralWidget(central_widget)

    def setup_receiver(self):
        self.receiver = UDPReceiver()

        self.receiver.packet_received.connect(
            self.handle_packet
        )

        self.receiver.status_changed.connect(
            self.status_label.setText
        )

        self.receiver.start()

    def setup_timers(self):
        # Redraw plots at a lower frequency than packet reception.
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(GUI_UPDATE_MS)

        # Update packet-rate information once per second.
        self.statistics_timer = QTimer(self)
        self.statistics_timer.timeout.connect(
            self.update_statistics
        )
        self.statistics_timer.start(1000)

    def handle_packet(self, timestamp, values):
        """
        Called whenever the UDP thread receives a complete packet.
        """

        if self.start_time is None:
            self.start_time = timestamp

        relative_time = timestamp - self.start_time

        self.time_buffer.append(relative_time)

        for index, value in enumerate(values):
            self.signal_buffers[index].append(value)

        self.latest_timestamp = relative_time
        self.latest_values = values
        self.received_packet_count += 1

        if self.csv_writer is not None:
            self.csv_writer.writerow(
                [relative_time, *values]
            )

            # Flush so that the CSV is updated while acquisition runs.
            self.csv_handle.flush()

    def update_plots(self):
        """
        Updates all six plots using the most recent buffer contents.
        """

        if not self.time_buffer:
            return

        times = np.asarray(self.time_buffer, dtype=np.float64)

        for curve, buffer in zip(
            self.curves,
            self.signal_buffers,
        ):
            values = np.asarray(buffer, dtype=np.float32)
            curve.setData(times, values)

        # Show a moving time window.
        latest_time = times[-1]

        if latest_time > HISTORY_SECONDS:
            minimum_time = latest_time - HISTORY_SECONDS
            maximum_time = latest_time

            self.plots[0].setXRange(
                minimum_time,
                maximum_time,
                padding=0,
            )

        if self.latest_values is not None:
            value_text = " | ".join(
                f"{name}: {value:.4f} {unit}"
                for name, value, unit in zip(
                    SIGNAL_NAMES,
                    self.latest_values,
                    SIGNAL_UNITS,
                )
            )

            self.value_label.setText(value_text)

    def update_statistics(self):
        packets_per_second = (
            self.received_packet_count
            - self.last_packet_display_count
        )

        self.last_packet_display_count = (
            self.received_packet_count
        )

        recording_text = (
            f"Recording to {CSV_FILE}"
            if self.csv_writer is not None
            else "CSV recording disabled"
        )

        self.status_label.setText(
            f"Receiving on port {UDP_PORT} | "
            f"{packets_per_second} packets/s | "
            f"{recording_text}"
        )

    def set_csv_recording(self, state):
        """
        Starts or stops live CSV recording.
        """

        recording_enabled = self.record_checkbox.isChecked()

        if recording_enabled:
            try:
                new_file = not CSV_FILE.exists()

                self.csv_handle = CSV_FILE.open(
                    mode="a",
                    newline="",
                    encoding="utf-8",
                )

                self.csv_writer = csv.writer(self.csv_handle)

                if new_file or CSV_FILE.stat().st_size == 0:
                    self.csv_writer.writerow(
                        ["Time_s", *SIGNAL_NAMES]
                    )
                    self.csv_handle.flush()

                self.status_label.setText(
                    f"Recording data to {CSV_FILE.resolve()}"
                )

            except OSError as error:
                self.status_label.setText(
                    f"Could not open CSV file: {error}"
                )

                self.record_checkbox.blockSignals(True)
                self.record_checkbox.setChecked(False)
                self.record_checkbox.blockSignals(False)

                self.csv_handle = None
                self.csv_writer = None

        else:
            self.close_csv_file()

    def close_csv_file(self):
        if self.csv_handle is not None:
            try:
                self.csv_handle.flush()
                self.csv_handle.close()
            except OSError:
                pass

        self.csv_handle = None
        self.csv_writer = None

    def clear_plots(self):
        self.time_buffer.clear()

        for buffer in self.signal_buffers:
            buffer.clear()

        for curve in self.curves:
            curve.clear()

        self.start_time = None
        self.latest_timestamp = None
        self.latest_values = None

        self.value_label.setText("No signal values received")

    def closeEvent(self, event):
        """
        Cleanly closes the socket, thread, timers and CSV file.
        """

        self.plot_timer.stop()
        self.statistics_timer.stop()

        self.receiver.stop()
        self.close_csv_file()

        event.accept()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

def main():
    pg.setConfigOptions(
        antialias=True,
    )

    app = QApplication(sys.argv)

    window = LivePlotWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# import sys
# from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit,QVBoxLayout, QWidget

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("CAPT motor demo 2")
#         self.label = QLabel()

#         self.input = QLineEdit()
#         self.input.textChanged.connect(self.label.setText)

#         layout = QVBoxLayout()
#         layout.addWidget(self.input)
#         layout.addWidget(self.label)

#         container = QWidget()
#         container.setLayout(layout)

#         self.setCentralWidget(container)



# app = QApplication(sys.argv)
# window = MainWindow()
# window.show()
# app.exec()

# import sys
# from PyQt6.QtCore import Qt
# from PyQt6.QtWidgets import (QApplication,
#                              QPushButton, 
#                              QLabel, 
#                              QMainWindow, 
#                              QSpinBox,
#                              QVBoxLayout,
#                              QLineEdit, 
#                              QSlider, 
#                              QDial, 
#                              QTextEdit, 
#                              QWidget)
# from PyQt6.QtGui import QPixmap

# class MainWindow(QMainWindow):

#      def value_changed(self, i):
#             print(i)
        
#      def slider_position(self, p):
#             print("Position: ", p)

        
#      def slider_pressed(self):
#             print("Pressed!")

#      def slider_released(self):
#             print("Released")

#      def text_changed(self, str):
#            print("Text has been altered to: %s" % str)
    
#      def update_image(self):
#         scaled = self.pixmap.scaled(
#               self.widget4.size(),
#               Qt.AspectRatioMode.KeepAspectRatio,
#               Qt.TransformationMode.SmoothTransformation,
#         )
#         self.widget4.setPixmap(scaled)

#         def resizeEvent(self,event):
#               self.update_image()
#               super().resizeEvent(event)
        
#      def __init__(self):
#         super().__init__()

#         layout = QVBoxLayout()

#         self.setWindowTitle("CAPT Motor options")
#         widget1 = QSlider(Qt.Orientation.Horizontal)

#         widget1.setMinimum(-20)
#         widget1.setMaximum(5)

#         widget1.setSingleStep(5)

#         widget1.valueChanged.connect(self.value_changed)
#         widget1.sliderMoved.connect(self.slider_position)
#         widget1.sliderPressed.connect(self.slider_pressed)
#         widget1.sliderReleased.connect(self.slider_released)


#         widget2 = QSpinBox()
#         widget2.setMinimum(30)
#         widget2.setMaximum(50)
#         widget2.setSingleStep(3)
#         widget2.setPrefix(" ")
#         widget2.setSuffix(" ")

#         widget2.valueChanged.connect(self.value_changed)
#         widget2.textChanged.connect(self.text_changed)

#         widget3 = QLabel()
#         widget3.setText("Sof sof is the bestt THE BEST")
#         font = widget3.font()
#         widget3.setFont(font)
#         widget3.setAlignment(
#               Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
#         )
#         self.setCentralWidget(widget3)
        
#         self.widget4 = QLabel()
#         self.widget4.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.widget4.setMinimumSize(200,200)
#         self.pixmap = QPixmap("stars.jpg")
#         self.update_image()

#         widget5 = QLineEdit()
#         widget5.setInputMask('000.000.000.000;_')

#         widgets = [widget1, widget2, widget3, self.widget4, widget5]

#         for w in widgets:
#               layout.addWidget(w)
            
#         widget = QWidget()
#         widget.setLayout(layout)
#         self.setCentralWidget(widget)

       

# app = QApplication(sys.argv)
# window = MainWindow()
# window.show()
# app.exec()


import sys
import pandas
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (QApplication, 
                             QMainWindow, 
                             QWidget,
                             QTabWidget, 
                             QVBoxLayout,
                             QToolBar, 
                             QStatusBar)
from layout_colorwidget import Color

filename = "capt_logs.csv"

def read_and_unpack_data():
    pass 


complementary = {
    "pink" : "blue",
    "blue":  "green",
    "green": "red",
    "yellow": "purple"
}

class MainWindow(QMainWindow):

    def toolbar_button_clicked(self,checked):
        current_index = self.tabs.currentIndex()
        current_color = self.tabs.tabText(current_index)

        new_color = complementary[current_color]

        self.tabs.removeTab(current_index)
        self.tabs.insertTab(current_index, Color(new_color), new_color)
        self.tabs.setCurrentIndex(current_index)

        print(f"{current_color} changed to {new_color}")

        print("clicked", checked)


    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAPT Motor Layouts")

        layout = QVBoxLayout()


        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.East)
        self.tabs.setMovable(True)

        for color in ["pink", "blue", "green", "yellow"]:
            self.tabs.addTab(Color(color), color)

    
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(26,26))
        self.addToolBar(toolbar)

        button_action = QAction(QIcon("start_icon.png"),"Start", self)
        button_action.setStatusTip("Use to start the motor")
        button_action.triggered.connect(self.toolbar_button_clicked)
        button_action.setCheckable(True)
        self.setStatusBar(QStatusBar(self))
        toolbar.addAction(button_action)

        widget1 = Color("light blue")

        
        widgets = [toolbar, self.tabs, widget1]

        for w in widgets:
            layout.addWidget(w)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


    
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
