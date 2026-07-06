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

