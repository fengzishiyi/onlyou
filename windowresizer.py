# window_resizer.py
from PySide6.QtCore import (Qt, QPoint, QTimer, QEvent, QRect, QObject)
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QWidget


class WindowResizer:
    """专门处理窗口边框调整功能的类"""

    def __init__(self, window):
        self.window = window
        self.resize_margin = 10
        self.resize_direction = None
        self.start_global_pos = None
        self.start_geometry = None
        self.drag_offset = None
        self.last_valid_cursor = None
        self.dpi_scale = 1.0

        # 初始化设置
        self.window.setMouseTracking(True)
        self.window.windowHandle().screenChanged.connect(self.update_scale_factor)
        self.screen_rect = QApplication.primaryScreen().availableGeometry()

        # 强制更新定时器
        self.cursor_timer = QTimer(interval=100, timeout=self.force_cursor_update)
        self.cursor_timer.start()

    def update_scale_factor(self):
        """自动适应屏幕缩放比例"""
        screen = self.window.windowHandle().screen()
        self.dpi_scale = screen.devicePixelRatio()
        self.resize_margin = int(10 * self.dpi_scale)

    def update_resize_cursor(self, pos=None):
        """更新鼠标光标形状以指示可调整方向"""
        if pos is None:
            pos = self.window.mapFromGlobal(QCursor.pos())

        # 精确坐标转换
        scaled_pos = QPoint(
            int(pos.x() * self.dpi_scale),
            int(pos.y() * self.dpi_scale)
        )

        edge = self._get_resize_edge(scaled_pos)
        if edge == 0:
            if self.last_valid_cursor is not None:
                self.window.unsetCursor()
                self.last_valid_cursor = None
        else:
            cursor_map = {
                1: Qt.SizeHorCursor, 2: Qt.SizeHorCursor,
                4: Qt.SizeVerCursor, 8: Qt.SizeVerCursor,
                5: Qt.SizeFDiagCursor, 6: Qt.SizeBDiagCursor,
                9: Qt.SizeBDiagCursor, 10: Qt.SizeFDiagCursor
            }
            new_cursor = cursor_map.get(edge, Qt.ArrowCursor)
            if new_cursor != self.last_valid_cursor:
                self.window.setCursor(new_cursor)
                self.last_valid_cursor = new_cursor

    def force_cursor_update(self):
        """定时强制更新鼠标光标"""
        if not self.window.underMouse():
            self.window.unsetCursor()
            self.last_valid_cursor = None
        else:
            self.update_resize_cursor()

    def _get_resize_edge(self, pos):
        """确定鼠标位于哪个可调整边缘"""
        x, y = pos.x(), pos.y()
        rect = self.window.rect()
        edge = 0

        # 动态边界计算
        margin = self.resize_margin + int(2 * (1 - abs(x / rect.width() - 0.5) * 4))
        margin = min(margin, 20)  # 防止过度扩大

        if x <= margin: edge |= 1
        if x >= rect.width() - margin: edge |= 2
        if y <= margin: edge |= 4
        if y >= rect.height() - margin: edge |= 8

        # 抑制微小抖动
        if edge in (5, 6, 9, 10) and (x < margin * 2 or y < margin * 2):
            edge = max(1 if x < margin else 2, 4 if y < margin else 8)

        return edge

    def handle_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.start_global_pos = event.globalPosition().toPoint()
            self.start_geometry = self.window.geometry()

            local_pos = event.position().toPoint()
            self.resize_direction = self._get_resize_edge(local_pos)

            if not self.resize_direction:
                # 窗口拖动模式
                self.drag_offset = self.start_global_pos - self.window.geometry().topLeft()

    def handle_mouse_move(self, event):
        """处理鼠标移动事件"""
        current_global_pos = event.globalPosition().toPoint()

        if self.resize_direction and event.buttons() == Qt.LeftButton:
            # 窗口调整模式
            delta = current_global_pos - self.start_global_pos
            new_geo = QRect(self.start_geometry)

            # 根据方向调整几何
            if self.resize_direction & 1:  # 左
                new_geo.setLeft(min(new_geo.left() + delta.x(),
                                    new_geo.right() - self.window.minimumWidth()))
            if self.resize_direction & 2:  # 右
                new_geo.setRight(max(new_geo.right() + delta.x(),
                                     new_geo.left() + self.window.minimumWidth()))
            if self.resize_direction & 4:  # 上
                new_geo.setTop(min(new_geo.top() + delta.y(),
                                   new_geo.bottom() - self.window.minimumHeight()))
            if self.resize_direction & 8:  # 下
                new_geo.setBottom(max(new_geo.bottom() + delta.y(),
                                      new_geo.top() + self.window.minimumHeight()))

            # 限制在屏幕范围内
            new_geo = new_geo.intersected(self.screen_rect)
            self.window.setGeometry(new_geo)

        elif event.buttons() == Qt.LeftButton and hasattr(self, 'drag_offset'):
            # 窗口拖动模式
            new_pos = current_global_pos - self.drag_offset
            # 限制窗口在屏幕内
            new_x = max(self.screen_rect.left(),
                        min(new_pos.x(), self.screen_rect.right() - self.window.width()))
            new_y = max(self.screen_rect.top(),
                        min(new_pos.y(), self.screen_rect.bottom() - self.window.height()))
            self.window.move(new_x, new_y)

        # 更新鼠标光标
        scaled_pos = QPoint(
            int(event.position().x() * self.dpi_scale),
            int(event.position().y() * self.dpi_scale))
        self.update_resize_cursor(scaled_pos)

    def handle_mouse_release(self, event):
        """处理鼠标释放事件"""
        self.resize_direction = None
        self.update_resize_cursor(event.position().toPoint())

    def handle_leave_event(self, event):
        """处理鼠标离开窗口事件"""
        self.window.unsetCursor()
        self.last_valid_cursor = None