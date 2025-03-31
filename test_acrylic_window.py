import sys
from PySide6.QtCore import (Qt, QPoint, QTimer, QSize, QEvent, QMargins,
                            QPropertyAnimation, QEasingCurve, QRect)
from PySide6.QtGui import QColor, QCursor, QPainter
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSizeGrip, QApplication)
from acrylic_effect import AcrylicEffect
from title_bar import TitleBar
from windowresizer import WindowResizer

class AcrylicWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(400, 300)

        # 亚克力效果
        self.acrylic = AcrylicEffect(self)
        self.acrylic.apply_effect()

        self.main_content = QWidget()
        self.main_content.setAttribute(Qt.WA_TranslucentBackground)
        self.main_content.setStyleSheet("background: transparent;")

        # 使用垂直布局包裹内容
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.setAlignment(self.title_bar, Qt.AlignTop)
        self.main_layout.addWidget(self.main_content)

        # 窗口调整功能
        self.window_resizer = WindowResizer(self)

        # 右下角调整手柄
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("QSizeGrip { width: 16px; height: 16px; }")

    def mousePressEvent(self, event):
        self.window_resizer.handle_mouse_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.window_resizer.handle_mouse_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.window_resizer.handle_mouse_release(event)
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self.window_resizer.handle_leave_event(event)
        super().leaveEvent(event)

    def showEvent(self, event):
        # 为所有子控件安装事件过滤器
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)
            child.setMouseTracking(True)

    def resizeEvent(self, event):
        """优化手柄位置更新"""
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height()
        )
        self.acrylic._invalidate_cache()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.acrylic.paint(painter)
        super().paintEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = AcrylicWindow()
    window.resize(800, 600)
    window.setStyleSheet("""
        QWidget {
            background: transparent;
        }
    """)

    # 效果参数设置
    window.acrylic.set_blur_radius(10)
    window.acrylic.set_tint_color(QColor(40, 40, 40, 180))
    window.acrylic.set_update_interval(30)
    window.acrylic.set_opacity(10)

    window.show()
    sys.exit(app.exec())