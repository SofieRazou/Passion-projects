from pathlib import Path

source = Path("/mnt/data/Pasted text(20).txt")
text = source.read_text(encoding="utf-8")

# Rename the existing signal page to indicate that it is now the first/home page.
text = text.replace(
    'class SignalPlotPage(QWidget):\n    """Real-time plots for signals received over UDP."""',
    'class SignalPlotPage(QWidget):\n    """First-page plots for commanded currents and measured torque."""'
)

# Replace the SignalPlotPage block with a simplified first-page layout:
start = text.index("class SignalPlotPage(QWidget):")
end = text.index("\n\nclass HomePage(QWidget):", start)

new_block = '''class SignalPlotPage(QWidget):
    """First-page plots for commanded currents and measured torque."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.start_time = time.monotonic()

        maximum_points = int(
            PLOT_WINDOW_SECONDS
            * 1000
            / GUI_UPDATE_PERIOD_MS
        ) + 100

        self.time_values = deque(maxlen=maximum_points)
        self.torque_values = deque(maxlen=maximum_points)
        self.current_1_values = deque(maxlen=maximum_points)
        self.current_2_values = deque(maxlen=maximum_points)

        self.torque_value_label = QLabel("Torque: --")
        self.current_1_value_label = QLabel(
            f"{CURRENT_PHASE_1_NAME}: --"
        )
        self.current_2_value_label = QLabel(
            f"{CURRENT_PHASE_2_NAME}: --"
        )

        value_layout = QHBoxLayout()
        value_layout.addWidget(self.torque_value_label)
        value_layout.addWidget(self.current_1_value_label)
        value_layout.addWidget(self.current_2_value_label)
        value_layout.addStretch()

        self.current_plot = self._create_plot(
            title="Commanded currents",
            y_label="Current",
            units="A",
        )

        self.torque_plot = self._create_plot(
            title="Measured torque",
            y_label="Torque",
            units="Nm",
        )

        self.current_1_curve = self.current_plot.plot(
            pen=pg.mkPen(width=2),
            name=CURRENT_PHASE_1_NAME,
        )

        self.current_2_curve = self.current_plot.plot(
            pen=pg.mkPen(
                width=2,
                style=Qt.PenStyle.DashLine,
            ),
            name=CURRENT_PHASE_2_NAME,
        )

        self.torque_curve = self.torque_plot.plot(
            pen=pg.mkPen(width=2),
            name=TORQUE_SIGNAL_NAME,
        )

        self.current_plot.addLegend()
        self.torque_plot.addLegend()

        clear_button = QPushButton("Clear plots")
        clear_button.clicked.connect(self.clear)

        top_layout = QHBoxLayout()
        top_layout.addLayout(value_layout)
        top_layout.addWidget(clear_button)

        plot_layout = QGridLayout()
        plot_layout.addWidget(self.current_plot, 0, 0)
        plot_layout.addWidget(self.torque_plot, 1, 0)

        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addLayout(plot_layout, 1)

    @staticmethod
    def _create_plot(
        title: str,
        y_label: str,
        units: str,
    ) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)

        plot.setLabel(
            "bottom",
            "Time",
            units="s",
        )

        plot.setLabel(
            "left",
            y_label,
            units=units,
        )

        plot.showGrid(
            x=True,
            y=True,
            alpha=0.25,
        )

        return plot

    def add_sample(
        self,
        angle_rad: float,
        torque: float,
        current_1: float,
        current_2: float,
    ) -> None:
        del angle_rad

        current_time = time.monotonic() - self.start_time

        self.time_values.append(current_time)
        self.torque_values.append(torque)
        self.current_1_values.append(current_1)
        self.current_2_values.append(current_2)

        self.torque_value_label.setText(
            f"Torque: {torque:.3f} Nm"
        )

        self.current_1_value_label.setText(
            f"{CURRENT_PHASE_1_NAME}: {current_1:.3f} A"
        )

        self.current_2_value_label.setText(
            f"{CURRENT_PHASE_2_NAME}: {current_2:.3f} A"
        )

        self._update_curves()

    def _update_curves(self) -> None:
        if not self.time_values:
            return

        times = list(self.time_values)

        self.current_1_curve.setData(
            times,
            list(self.current_1_values),
        )

        self.current_2_curve.setData(
            times,
            list(self.current_2_values),
        )

        self.torque_curve.setData(
            times,
            list(self.torque_values),
        )

        latest_time = times[-1]

        if latest_time > PLOT_WINDOW_SECONDS:
            minimum_time = latest_time - PLOT_WINDOW_SECONDS
            maximum_time = latest_time
        else:
            minimum_time = 0.0
            maximum_time = PLOT_WINDOW_SECONDS

        self.current_plot.setXRange(
            minimum_time,
            maximum_time,
            padding=0,
        )

        self.torque_plot.setXRange(
            minimum_time,
            maximum_time,
            padding=0,
        )

    def clear(self) -> None:
        self.start_time = time.monotonic()

        self.time_values.clear()
        self.torque_values.clear()
        self.current_1_values.clear()
        self.current_2_values.clear()

        self.current_1_curve.clear()
        self.current_2_curve.clear()
        self.torque_curve.clear()
'''

text = text[:start] + new_block + text[end:]

# Make this plotting page the first tab, while preserving the remaining pages.
old_tabs = '''        self.home_page = HomePage()
        self.signal_plot_page = SignalPlotPage()
        self.spring_page = SpringPage()

        tabs = QTabWidget()
        tabs.addTab(self.home_page, "Home")
        tabs.addTab(self.signal_plot_page, "Live Signals")
        tabs.addTab(self.spring_page, "Virtual Spring")
'''
new_tabs = '''        self.home_page = HomePage()
        self.signal_plot_page = SignalPlotPage()
        self.spring_page = SpringPage()

        tabs = QTabWidget()
        tabs.addTab(self.signal_plot_page, "Live Signals")
        tabs.addTab(self.home_page, "Home")
        tabs.addTab(self.spring_page, "Virtual Spring")
'''
text = text.replace(old_tabs, new_tabs)

output = Path("/mnt/data/capt_motor_gui_updated.py")
output.write_text(text, encoding="utf-8")

print(f"Created: {output}")
