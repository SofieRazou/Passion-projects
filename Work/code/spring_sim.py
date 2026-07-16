import math
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import QPointF


class SpringWidget(QWidget):
    """Draws a horizontal spring connected to a movable handle."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.angle_rad = 0.0
        self.reference_angle_rad = 0.0
        self.kappa = 1.0

        self.setMinimumHeight(300)

    def set_angle(self, angle_rad: float) -> None:
        self.angle_rad = angle_rad
        self.update()

    def set_reference_angle(self, reference_rad: float) -> None:
        self.reference_angle_rad = reference_rad
        self.update()

    def set_kappa(self, kappa: float) -> None:
        self.kappa = kappa
        self.update()

    def spring_torque(self) -> float:
        """Restoring spring torque."""
        return -self.kappa * (
            self.angle_rad - self.reference_angle_rad
        )

    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        center_y = height * 0.52
        fixed_x = width * 0.12

        # Convert angular displacement to a visible linear displacement.
        max_visual_displacement = width * 0.28
        maximum_angle = math.radians(30)

        normalized_angle = max(
            -1.0,
            min(1.0, self.angle_rad / maximum_angle),
        )

        equilibrium_x = width * 0.52
        handle_x = equilibrium_x + (
            normalized_angle * max_visual_displacement
        )

        # Background axis.
        axis_pen = QPen(QColor(140, 140, 140), 1)
        axis_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(axis_pen)
        painter.drawLine(
            QPointF(equilibrium_x, center_y - 80),
            QPointF(equilibrium_x, center_y + 80),
        )

        # Fixed wall.
        wall_pen = QPen(QColor(70, 70, 70), 5)
        painter.setPen(wall_pen)
        painter.drawLine(
            QPointF(fixed_x, center_y - 75),
            QPointF(fixed_x, center_y + 75),
        )

        # Spring.
        self._draw_spring(
            painter=painter,
            start=QPointF(fixed_x, center_y),
            end=QPointF(handle_x, center_y),
            coils=12,
            amplitude=22,
        )

        # Handle.
        handle_pen = QPen(QColor(30, 90, 180), 8)
        painter.setPen(handle_pen)
        painter.drawLine(
            QPointF(handle_x, center_y - 60),
            QPointF(handle_x, center_y + 60),
        )

        # Torque arrow.
        torque = self.spring_torque()
        self._draw_torque_arrow(
            painter,
            QPointF(handle_x, center_y - 95),
            torque,
        )

        # Text.
        painter.setPen(QColor(40, 40, 40))

        angle_deg = math.degrees(self.angle_rad)
        reference_deg = math.degrees(self.reference_angle_rad)

        painter.drawText(
            20,
            30,
            f"Angle: {angle_deg:.2f}°",
        )
        painter.drawText(
            20,
            55,
            f"Reference: {reference_deg:.2f}°",
        )
        painter.drawText(
            20,
            80,
            f"Kappa: {self.kappa:.3f} Nm/rad",
        )
        painter.drawText(
            20,
            105,
            f"Spring torque: {torque:.3f} Nm",
        )

    @staticmethod
    def _draw_spring(
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        coils: int,
        amplitude: float,
    ) -> None:
        spring_pen = QPen(QColor(50, 50, 50), 3)
        painter.setPen(spring_pen)

        lead_length = 20.0
        usable_start_x = start.x() + lead_length
        usable_end_x = end.x() - lead_length

        if usable_end_x <= usable_start_x:
            painter.drawLine(start, end)
            return

        points = [start, QPointF(usable_start_x, start.y())]

        number_of_segments = coils * 2
        spring_length = usable_end_x - usable_start_x

        for index in range(number_of_segments + 1):
            ratio = index / number_of_segments
            x = usable_start_x + ratio * spring_length

            if index == 0 or index == number_of_segments:
                y = start.y()
            else:
                y = (
                    start.y() - amplitude
                    if index % 2
                    else start.y() + amplitude
                )

            points.append(QPointF(x, y))

        points.extend(
            [
                QPointF(usable_end_x, end.y()),
                end,
            ]
        )

        painter.drawPolyline(QPolygonF(points))

    @staticmethod
    def _draw_torque_arrow(
        painter: QPainter,
        origin: QPointF,
        torque: float,
    ) -> None:
        if abs(torque) < 1e-6:
            return

        arrow_length = 65
        direction = 1 if torque > 0 else -1

        arrow_pen = QPen(QColor(190, 70, 50), 3)
        painter.setPen(arrow_pen)

        end = QPointF(
            origin.x() + direction * arrow_length,
            origin.y(),
        )

        painter.drawLine(origin, end)

        head_size = 10
        painter.drawLine(
            end,
            QPointF(
                end.x() - direction * head_size,
                end.y() - head_size,
            ),
        )
        painter.drawLine(
            end,
            QPointF(
                end.x() - direction * head_size,
                end.y() + head_size,
            ),
        )


class SpringPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.spring_view = SpringWidget()

        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(-300, 300)
        self.angle_slider.setValue(0)

        self.kappa_input = QDoubleSpinBox()
        self.kappa_input.setRange(0.0, 20.0)
        self.kappa_input.setDecimals(3)
        self.kappa_input.setSingleStep(0.1)
        self.kappa_input.setValue(1.0)
        self.kappa_input.setSuffix(" Nm/rad")

        reset_button = QPushButton("Reset")

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Angle"))
        control_layout.addWidget(self.angle_slider, 1)
        control_layout.addWidget(QLabel("Kappa"))
        control_layout.addWidget(self.kappa_input)
        control_layout.addWidget(reset_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.spring_view, 1)
        layout.addLayout(control_layout)

        self.angle_slider.valueChanged.connect(
            self._update_angle_from_slider
        )
        self.kappa_input.valueChanged.connect(
            self.spring_view.set_kappa
        )
        reset_button.clicked.connect(self._reset)

    def _update_angle_from_slider(self, value: int) -> None:
        angle_degrees = value / 10.0
        self.spring_view.set_angle(math.radians(angle_degrees))

    def _reset(self) -> None:
        self.angle_slider.setValue(0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAPT Motor Dashboard")
        self.resize(950, 650)

        tabs = QTabWidget()

        home_page = QWidget()
        spring_page = SpringPage()

        tabs.addTab(home_page, "Home")
        tabs.addTab(spring_page, "Virtual Spring")

        self.setCentralWidget(tabs)


def main() -> None:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
