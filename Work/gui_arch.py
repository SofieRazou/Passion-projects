#capt inside capt
# import sys
# from PyQt6.QtCore import QSize
# from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton


# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.button_checked = True
#         self.setWindowTitle("CAPT motor GUI")

#         self.button = QPushButton("Start running")
#         self.setMinimumSize(100,100)
#         self.setMaximumSize(500,500)
        

#         self.button.setCheckable(True)
#         self.button.released.connect(self.b_released)
#         self.button.setChecked(self.button_checked)
#         self.button.clicked.connect(self.b_clicked)
#         self.button.clicked.connect(self.b_toggled)
#         self.setCentralWidget(self.button)
    
#     def b_clicked(self):
#         print("CLICKED!")
    
#     def b_toggled(self, checked):
#         self.button_checked = checked
#         print("Checked?", checked)
    
#     def b_released(self):
#         self.button_checked = self.button.isChecked()

#         print(self.button_checked)


# app = QApplication(sys.argv)

# window = MainWindow()
# window.show()

# app.exec()
import sys
import time
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton

motor_actions =[
    "spring",
    "damping in rotational spring",
    "lane assist experiment",
    "motor overload"
]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.start_time = time.time()

        self.setWindowTitle("CAPT motor Demo")

        self.button = QPushButton("Start tracking")
        self.button.clicked.connect(self.b_clicked)
        self.windowTitleChanged.connect(self.title_change)


        self.setMinimumSize(100, 100)
        self.setMaximumSize(600,600)


        self.setCentralWidget(self.button)

    def b_clicked(self):
        print("CLICKED!")
        time_elapsed = time.time() - self.start_time
        print(f"Elapsed time: {time_elapsed:.2f} s")

        
        if time_elapsed<1.0 :
            new_window_title = motor_actions[0]
   

        elif time_elapsed>1.0 and time_elapsed<4.0:
            new_window_title = motor_actions[1]
        
        elif time_elapsed>4.0 and time_elapsed<7.0:
            new_window_title = motor_actions[2]

        
        else:
            new_window_title = motor_actions[3]
        
        print("Motor state changed")
        print(f"Setting window title to: {new_window_title}")
        self.setWindowTitle(new_window_title)

    def title_change(self, window_title):
        print("Title change commences")
        if window_title == "motor overload":
            self.button.setDisabled(True)


    
#running the app with the respective windows 
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()


