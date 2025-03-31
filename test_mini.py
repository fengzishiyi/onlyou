import ctypes
import sys
from acrylic_window import AcrylicWindow, AcrylicEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, Qt, QRect, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QLabel, QPushButton


class WindowMiniMode:
    """窗口迷你模式控制器"""

    def __init__(self, window: QWidget):
        self.window = window
        self.normal_geometry = None
        self.visible_strip = 10  # 隐藏后保留的可见像素
        self.animation_duration = 300  # 动画时长(ms)

        # 初始化动画
        self.pos_anim = QPropertyAnimation(window, b"pos")
        self.pos_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.pos_anim.setDuration(self.animation_duration)

    def enable(self):
        """启用迷你模式"""
        if not hasattr(self.window, '_mini_mode'):
            self.window._mini_mode = True
            self.normal_geometry = self.window.geometry()
            self.attach_to_nearest_edge()

    def disable(self):
        """禁用迷你模式"""
        if hasattr(self.window, '_mini_mode'):
            self.window._mini_mode = False
            self.pos_anim.stop()
            self.window.showNormal()
            if self.normal_geometry:
                self.window.setGeometry(self.normal_geometry)

    def toggle(self):
        """切换迷你模式状态"""
        if self.is_enabled():
            self.disable()
        else:
            self.enable()

    def is_enabled(self):
        """检查是否处于迷你模式"""
        return getattr(self.window, '_mini_mode', False)

    def attach_to_nearest_edge(self):
        """精确计算最近边缘并吸附"""
        screen = self.window.screen().availableGeometry()
        window_geo = self.window.geometry()

        # 计算中心点到各边的距离
        center = window_geo.center()
        distances = {
            'left': abs(center.x() - screen.left()),
            'right': abs(screen.right() - center.x()),
            'top': abs(center.y() - screen.top()),
            'bottom': abs(screen.bottom() - center.y())
        }

        closest_edge = min(distances, key=distances.get)
        {
            'left': self.attach_to_left,
            'right': self.attach_to_right,
            'top': self.attach_to_top,
            'bottom': self.attach_to_bottom
        }[closest_edge](screen)

    def attach_to_left(self, screen_geo):
        """吸附到左边缘"""
        target_x = screen_geo.left() - self.window.width() + self.visible_strip
        target_y = max(screen_geo.top(), min(
            self.window.y(),
            screen_geo.bottom() - self.window.height()
        ))
        self.animate_to(QPoint(target_x, target_y))

    def attach_to_right(self, screen_geo):
        """吸附到右边缘"""
        target_x = screen_geo.right() - self.visible_strip
        target_y = max(screen_geo.top(), min(
            self.window.y(),
            screen_geo.bottom() - self.window.height()
        ))
        self.animate_to(QPoint(target_x, target_y))

    def attach_to_top(self, screen_geo):
        """吸附到上边缘"""
        target_x = max(screen_geo.left(), min(
            self.window.x(),
            screen_geo.right() - self.window.width()
        ))
        target_y = screen_geo.top() - self.window.height() + self.visible_strip
        self.animate_to(QPoint(target_x, target_y))

    def attach_to_bottom(self, screen_geo):
        """吸附到底部"""
        target_x = max(screen_geo.left(), min(
            self.window.x(),
            screen_geo.right() - self.window.width()
        ))
        target_y = screen_geo.bottom() - self.visible_strip
        self.animate_to(QPoint(target_x, target_y))

    def animate_to(self, target_pos):
        """执行位移动画"""
        self.pos_anim.stop()
        self.pos_anim.setStartValue(self.window.pos())
        self.pos_anim.setEndValue(target_pos)
        self.pos_anim.start()

    def handle_enter_event(self):
        """鼠标进入时展开窗口"""
        if self.is_enabled():
            self.expand_window()

    def handle_leave_event(self):
        """鼠标离开时收回窗口"""
        if self.is_enabled() and not self.window.geometry().contains(QCursor.pos()):
            self.attach_to_nearest_edge()

    def expand_window(self):
        """从迷你模式展开"""
        self.pos_anim.stop()
        if self.normal_geometry:
            self.window.setGeometry(self.normal_geometry)
        else:
            # 默认展开到右侧
            screen = self.window.screen().availableGeometry()
            self.window.setGeometry(
                screen.right() - self.window.width(),
                screen.top(),
                self.window.width(),
                screen.height()
            )


class MiniModeDemo(AcrylicWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini模式测试")
        self.resize(600, 400)

        # 初始化迷你模式控制器
        self.mini_controller = WindowMiniMode(self)

        # 添加测试内容
        content = QWidget()
        layout = QVBoxLayout(content)

        label = QLabel("拖动窗口到屏幕边缘测试迷你模式\n或点击下方按钮切换状态")
        label.setAlignment(Qt.AlignCenter)

        toggle_btn = QPushButton("切换迷你模式")
        toggle_btn.clicked.connect(self.mini_controller.toggle)

        layout.addWidget(label)
        layout.addWidget(toggle_btn)
        # self.content.setLayout(layout)

        # 设置样式
        # self.content.setStyleSheet("""
        #     QLabel {
        #         color: rgba(0,0,0,0.8);
        #         font-size: 16px;
        #         margin-bottom: 20px;
        #     }
        #     QPushButton {
        #         background: rgba(255,255,255,0.3);
        #         border: 1px solid rgba(0,0,0,0.1);
        #         border-radius: 4px;
        #         padding: 8px;
        #         min-width: 120px;
        #     }
        #     QPushButton:hover {
        #         background: rgba(255,255,255,0.5);
        #     }
        # """)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.mini_controller.is_enabled():
                # 在迷你模式下拖动时临时展开
                self.mini_controller.expand_window()
                self.title_bar.toggle_mini_mode()  # 更新按钮状态
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.mini_controller.is_enabled():
            # 拖动结束后重新吸附
            self.mini_controller.attach_to_nearest_edge()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        if self.mini_controller.is_enabled():
            # 鼠标进入时延迟展开防止误触
            QTimer.singleShot(300, self.mini_controller.expand_window)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.mini_controller.is_enabled():
            # 鼠标离开时延迟收回
            QTimer.singleShot(500, self.mini_controller.attach_to_nearest_edge)
        super().leaveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Windows系统启用DPI感知
    if sys.platform == "win32":
        ctypes.windll.shcore.SetProcessDpiAwareness(2)

    window = MiniModeDemo()
    window.show()

    sys.exit(app.exec())