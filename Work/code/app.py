import sys
import csv
from pathlib import Path

import pandas as pd

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


CSV_FILE = Path("capt_logs.csv")
UPDATE_INTERVAL_MS = 500


def load_dspace_csv(file_path: str | Path) -> pd.DataFrame:
    """
    Load a dSPACE CSV export.

    The function searches for:
    - the row containing 'path'
    - the row containing 'trace_values'

    It supports metadata rows with different column counts.
    """

    file_path = Path(file_path).expanduser()

    if not file_path.exists() and file_path.suffix == "":
        possible_csv_path = file_path.with_suffix(".csv")

        if possible_csv_path.exists():
            file_path = possible_csv_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path.resolve()}"
        )

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as csv_file:

        sample = csv_file.read(4096)
        csv_file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(
                sample,
                delimiters=",;\t",
            )
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        reader = csv.reader(csv_file, delimiter=delimiter)
        rows = list(reader)

    if not rows:
        raise ValueError("The CSV file is empty.")

    rows = [
        [cell.strip() for cell in row]
        for row in rows
    ]

    maximum_columns = max(len(row) for row in rows)

    padded_rows = [
        row + [""] * (maximum_columns - len(row))
        for row in rows
    ]

    raw_df = pd.DataFrame(padded_rows)

    def find_row_containing(value: str) -> int:
        target = value.strip().lower()

        for row_index, row in raw_df.iterrows():
            cells = row.astype(str).str.strip().str.lower()

            if cells.eq(target).any():
                return row_index

        raise ValueError(
            f"Could not find a row containing '{value}'."
        )

    path_row_index = find_row_containing("path")
    trace_row_index = find_row_containing("trace_values")

    path_row = raw_df.iloc[path_row_index].tolist()
    trace_row = raw_df.iloc[trace_row_index].tolist()

    path_column_index = next(
        index
        for index, value in enumerate(path_row)
        if str(value).strip().lower() == "path"
    )

    trace_column_index = next(
        index
        for index, value in enumerate(trace_row)
        if str(value).strip().lower() == "trace_values"
    )

    signal_names = path_row[path_column_index + 1:]

    while signal_names and not signal_names[-1]:
        signal_names.pop()

    if not signal_names:
        raise ValueError(
            "The 'path' row was found, but no signal names were detected."
        )

    signal_names = make_unique_names(signal_names)

    data_start_column = trace_column_index + 1
    number_of_signals = len(signal_names)

    data_df = raw_df.iloc[
        trace_row_index:,
        data_start_column:data_start_column + number_of_signals,
    ].copy()

    data_df.columns = signal_names

    for column_name in data_df.columns:
        data_df[column_name] = pd.to_numeric(
            data_df[column_name]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False),
            errors="coerce",
        )

    data_df = data_df.dropna(how="all").reset_index(drop=True)

    if data_df.empty:
        raise ValueError(
            "No numerical values were found after 'trace_values'."
        )

    return data_df


def make_unique_names(names: list[str]) -> list[str]:
    """Ensure that all DataFrame column names are unique."""

    counts: dict[str, int] = {}
    unique_names: list[str] = []

    for index, raw_name in enumerate(names):
        name = str(raw_name).strip()

        if not name:
            name = f"Signal_{index + 1}"

        count = counts.get(name, 0)

        if count == 0:
            unique_name = name
        else:
            unique_name = f"{name}_{count + 1}"

        counts[name] = count + 1
        unique_names.append(unique_name)

    return unique_names


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Live Data")
        self.resize(1200, 700)

        self.last_modified_time: float | None = None
        self.is_monitoring = False

        self.create_interface()
        self.create_toolbar()
        self.create_timer()

        # Load the file once when the GUI opens.
        self.start_monitoring()

    def create_interface(self) -> None:
        self.info_label = QLabel("Waiting for CSV data...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.table)

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)
        self.setStatusBar(QStatusBar(self))

    def create_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.start_action = QAction(
            QIcon("start_icon.png"),
            "Start monitoring",
            self,
        )
        self.start_action.setStatusTip(
            "Start reading updated values from the CSV file"
        )
        self.start_action.triggered.connect(self.start_monitoring)
        toolbar.addAction(self.start_action)

        self.stop_action = QAction(
            "Stop monitoring",
            self,
        )
        self.stop_action.setStatusTip(
            "Stop reading values from the CSV file"
        )
        self.stop_action.triggered.connect(self.stop_monitoring)
        toolbar.addAction(self.stop_action)

        self.reload_action = QAction(
            "Reload now",
            self,
        )
        self.reload_action.setStatusTip(
            "Reload the complete CSV file immediately"
        )
        self.reload_action.triggered.connect(
            lambda: self.update_from_file(force=True)
        )
        toolbar.addAction(self.reload_action)

    def create_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.setInterval(UPDATE_INTERVAL_MS)
        self.timer.timeout.connect(self.update_from_file)

    def start_monitoring(self) -> None:
        self.is_monitoring = True
        self.timer.start()

        self.update_from_file(force=True)

        self.statusBar().showMessage(
            f"Monitoring {CSV_FILE} every "
            f"{UPDATE_INTERVAL_MS} ms"
        )

    def stop_monitoring(self) -> None:
        self.is_monitoring = False
        self.timer.stop()

        self.statusBar().showMessage("CSV monitoring stopped")

    def update_from_file(self, force: bool = False) -> None:
        """
        Reload the CSV only if it has changed.

        force=True reloads it regardless of its modification time.
        """

        if not force and not self.is_monitoring:
            return

        try:
            if not CSV_FILE.exists():
                self.info_label.setText(
                    f"File not found: {CSV_FILE.resolve()}"
                )
                return

            current_modified_time = CSV_FILE.stat().st_mtime

            if (
                not force
                and self.last_modified_time == current_modified_time
            ):
                return

            data_df = load_dspace_csv(CSV_FILE)

            self.display_dataframe(data_df)

            self.last_modified_time = current_modified_time

            self.info_label.setText(
                f"File: {CSV_FILE.name} | "
                f"Rows: {len(data_df)} | "
                f"Signals: {len(data_df.columns)}"
            )

            self.statusBar().showMessage(
                "CSV data updated successfully"
            )

        except PermissionError:
            # The exporting program may briefly lock the file while writing.
            self.statusBar().showMessage(
                "The CSV file is currently being written. Retrying..."
            )

        except (FileNotFoundError, ValueError, csv.Error) as error:
            self.statusBar().showMessage(str(error))

        except Exception as error:
            self.statusBar().showMessage(
                f"Unexpected CSV error: {error}"
            )

    def display_dataframe(self, data_df: pd.DataFrame) -> None:
        """Display every DataFrame row and column in the table."""

        previous_vertical_scroll = (
            self.table.verticalScrollBar().value()
        )
        previous_horizontal_scroll = (
            self.table.horizontalScrollBar().value()
        )

        self.table.setUpdatesEnabled(False)

        try:
            self.table.clear()

            self.table.setRowCount(len(data_df))
            self.table.setColumnCount(len(data_df.columns))

            self.table.setHorizontalHeaderLabels(
                [str(column) for column in data_df.columns]
            )

            for row_index, row in enumerate(
                data_df.itertuples(index=False, name=None)
            ):
                for column_index, value in enumerate(row):

                    if pd.isna(value):
                        displayed_value = ""
                    else:
                        displayed_value = f"{value:.6g}"

                    item = QTableWidgetItem(displayed_value)
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                    self.table.setItem(
                        row_index,
                        column_index,
                        item,
                    )

            self.table.resizeColumnsToContents()

            self.table.verticalScrollBar().setValue(
                previous_vertical_scroll
            )
            self.table.horizontalScrollBar().setValue(
                previous_horizontal_scroll
            )

        finally:
            self.table.setUpdatesEnabled(True)


def main() -> None:
    app = QApplication(sys.argv)

    window = MainWindow()
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

