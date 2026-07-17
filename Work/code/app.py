from pathlib import Path
import csv

import pandas as pd


def load_dspace_csv(file_path: str | Path) -> pd.DataFrame:
    file_path = Path(file_path).expanduser()

    # Automatically try adding .csv if no extension was supplied.
    if not file_path.exists() and file_path.suffix == "":
        csv_path = file_path.with_suffix(".csv")

        if csv_path.exists():
            file_path = csv_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path.resolve()}"
        )

    # Detect the delimiter from the beginning of the file.
    with file_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline=""
    ) as file:
        sample = file.read(4096)
        file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(
                sample,
                delimiters=",;\t"
            )
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        reader = csv.reader(file, delimiter=delimiter)
        rows = [row for row in reader]

    if not rows:
        raise ValueError("The CSV file is empty.")

    # Strip whitespace from all cells.
    rows = [
        [cell.strip() for cell in row]
        for row in rows
    ]

    # Different metadata rows may have different column counts.
    # Pad every row to the maximum width.
    maximum_columns = max(len(row) for row in rows)

    padded_rows = [
        row + [""] * (maximum_columns - len(row))
        for row in rows
    ]

    raw_df = pd.DataFrame(padded_rows)

    def find_row_containing(value: str) -> int:
        value = value.lower()

        for row_index, row in raw_df.iterrows():
            cells = row.astype(str).str.strip().str.lower()

            if cells.eq(value).any():
                return row_index

        raise ValueError(f"Could not find a row containing '{value}'.")

    path_row_index = find_row_containing("path")
    trace_row_index = find_row_containing("trace_values")

    path_row = raw_df.iloc[path_row_index].tolist()

    # Locate the actual cell containing "path".
    path_column_index = next(
        index
        for index, value in enumerate(path_row)
        if str(value).strip().lower() == "path"
    )

    # Locate the actual cell containing "trace_values".
    trace_row = raw_df.iloc[trace_row_index].tolist()

    trace_column_index = next(
        index
        for index, value in enumerate(trace_row)
        if str(value).strip().lower() == "trace_values"
    )

    # In many dSPACE exports, the signal names begin after the "path" cell.
    signal_names = path_row[path_column_index + 1:]

    # Remove empty trailing signal names.
    while signal_names and signal_names[-1] == "":
        signal_names.pop()

    if not signal_names:
        raise ValueError(
            "The 'path' row was found, but no signal names were detected."
        )

    # Data can begin on the trace_values row or directly below it.
    # Start from the column after the trace_values label.
    data_start_column = trace_column_index + 1
    number_of_signals = len(signal_names)

    data_df = raw_df.iloc[
        trace_row_index:,
        data_start_column:data_start_column + number_of_signals
    ].copy()

    data_df.columns = signal_names

    # Convert all cells to numeric.
    data_df = data_df.apply(
        lambda column: pd.to_numeric(
            column.str.replace(",", ".", regex=False),
            errors="coerce"
        )
    )

    # Remove metadata and completely empty rows.
    data_df = data_df.dropna(how="all").reset_index(drop=True)

    if data_df.empty:
        raise ValueError(
            "No numerical data was found after the 'trace_values' row."
        )

    return data_df


if __name__ == "__main__":
    file_path = "exp1_001.csv"

    try:
        data_df = load_dspace_csv(file_path)

        print("CSV loaded successfully.")
        print(f"Shape: {data_df.shape}")
        print("\nColumns:")
        print(data_df.columns.tolist())
        print("\nFirst rows:")
        print(data_df.head())

    except Exception as error:
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

