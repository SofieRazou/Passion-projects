from pathlib import Path

import pandas as pd


def load_dspace_csv(file_path: str | Path) -> pd.DataFrame:
    """
    Load a dSPACE CSV export containing:
    - a 'path' row with signal names
    - a 'trace_values' row followed by numerical samples
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    # Read the file without assuming where the header and data rows are.
    raw_df = pd.read_csv(
        file_path,
        header=None,
        dtype=str,
        keep_default_na=False
    )

    # Remove leading/trailing whitespace from every string cell.
    raw_df = raw_df.apply(lambda column: column.str.strip())

    # Find the row containing "path".
    path_rows = raw_df.index[
        raw_df.apply(
            lambda row: row.str.lower().eq("path").any(),
            axis=1
        )
    ]

    if path_rows.empty:
        raise ValueError("Could not find a row containing 'path'.")

    path_row_index = path_rows[0]

    # Find the row containing "trace_values".
    trace_rows = raw_df.index[
        raw_df.apply(
            lambda row: row.str.lower().eq("trace_values").any(),
            axis=1
        )
    ]

    if trace_rows.empty:
        raise ValueError("Could not find a row containing 'trace_values'.")

    trace_row_index = trace_rows[0]

    # Extract signal names from the path row.
    column_names = raw_df.iloc[path_row_index].tolist()

    # The first column normally contains the row identifier "path".
    column_names[0] = "Time"

    # Replace missing signal names with generated names.
    column_names = [
        name if name else f"Signal_{index}"
        for index, name in enumerate(column_names)
    ]

    # Ensure duplicate signal names do not cause ambiguity.
    seen_names: dict[str, int] = {}
    unique_column_names: list[str] = []

    for name in column_names:
        count = seen_names.get(name, 0)

        if count == 0:
            unique_name = name
        else:
            unique_name = f"{name}_{count}"

        unique_column_names.append(unique_name)
        seen_names[name] = count + 1

    # Numerical values may begin either on the trace_values row or the next row.
    data_df = raw_df.iloc[trace_row_index:].copy()
    data_df.columns = unique_column_names

    # Remove the trace_values label without replacing it with a fake time value.
    data_df.iloc[0, 0] = ""

    # Convert every value to numeric.
    # Invalid metadata cells become NaN.
    data_df = data_df.apply(
        lambda column: pd.to_numeric(column, errors="coerce")
    )

    # Remove rows that contain no numerical data.
    data_df = data_df.dropna(how="all")

    # A valid sample should normally have a time value.
    data_df = data_df.dropna(subset=["Time"])

    # Reset row numbering after removing metadata rows.
    data_df = data_df.reset_index(drop=True)

    return data_df


if __name__ == "__main__":
    file_path = "your_file.csv"

    try:
        data_df = load_dspace_csv(file_path)

        print(data_df.head())
        print("\nColumn types:")
        print(data_df.dtypes)

    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        print(f"Failed to load the dSPACE CSV: {error}")



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

