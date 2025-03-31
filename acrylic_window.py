import sys
import ctypes
import math
from ctypes import wintypes
from PySide6.QtCore import Property, Signal
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                               QLabel, QMenuBar, QToolBar, QPushButton, QSizePolicy, QSizeGrip, QHBoxLayout,
                               QGraphicsDropShadowEffect, QGraphicsBlurEffect, QMenu)
from PySide6.QtCore import Qt, QRect, QPoint, QTimer, QSize, QEvent, QMargins, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QImage, QScreen, QAction, QIcon, QCursor, QPixmap, QFont, QPainterPath, \
    QFontDatabase


class Win32API:
    class ACCENTPOLICY(ctypes.Structure):
        _fields_ = [
            ("AccentState", ctypes.c_uint),
            ("AccentFlags", ctypes.c_uint),
            ("GradientColor", ctypes.c_uint),
            ("AnimationId", ctypes.c_uint),
        ]

    class WINCOMPATTRDATA(ctypes.Structure):
        _fields_ = [
            ("Attribute", ctypes.c_int),
            ("Data", ctypes.POINTER(ctypes.c_ubyte)),
            ("SizeOfData", ctypes.c_size_t),
        ]

    @staticmethod
    def enable_blur(hwnd):
        SetWindowCompositionAttribute = ctypes.windll.user32.SetWindowCompositionAttribute
        SetWindowCompositionAttribute.restype = ctypes.c_bool
        SetWindowCompositionAttribute.argtypes = [wintypes.HWND, ctypes.POINTER(Win32API.WINCOMPATTRDATA)]

        accent = Win32API.ACCENTPOLICY()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        accent.AccentFlags = 0x20 | 0x40
        accent.GradientColor = 0x00FFFFFF  # 完全透明

        data = Win32API.WINCOMPATTRDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_ubyte))

        return SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))


class AcrylicEffect:
    def __init__(self, widget):
        self.widget = widget
        self.blur_radius = 8
        self.tint_color = QColor(30, 30, 30, 150)
        self.update_interval = 50
        self.use_hardware_accel = True

        self.blur_cache = None
        self.dirty_rects = []
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)

    def set_opacity(self, opacity):
        """设置窗口透明度(0-255)"""
        opacity = max(0, min(opacity, 255))  # 确保在0-255范围内
        self.tint_color.setAlpha(opacity)
        self._invalidate_cache()

    def set_blur_radius(self, radius):
        self.blur_radius = max(1, min(radius, 20))
        self._invalidate_cache()

    def set_tint_color(self, color):
        self.tint_color = color
        self._invalidate_cache()

    def set_update_interval(self, interval):
        self.update_interval = max(10, min(interval, 100))
        self.timer.setInterval(self.update_interval)

    def enable_hardware_accel(self, enabled):
        self.use_hardware_accel = enabled
        self._invalidate_cache()

    def _invalidate_cache(self):
        self.blur_cache = None
        self.dirty_rects.append(QRect(0, 0, self.widget.width(), self.widget.height()))
        self.widget.update()

    def _update(self):
        if self.dirty_rects:
            self.widget.update()
            self.dirty_rects.clear()

    def apply_effect(self):
        if self.use_hardware_accel:
            hwnd = int(self.widget.winId())
            if not Win32API.enable_blur(hwnd):
                self.use_hardware_accel = False

        self.timer.start(self.update_interval)

    def paint(self, painter):
        if self.use_hardware_accel:
            painter.fillRect(self.widget.rect(), self.tint_color)
            return

        visible_rect = self.widget.rect()

        if not visible_rect.isEmpty():
            # 获取屏幕截图
            screen = QApplication.primaryScreen()
            global_pos = self.widget.mapToGlobal(QPoint(0, 0))
            screenshot = screen.grabWindow(0,
                                           global_pos.x() + visible_rect.x(),
                                           global_pos.y() + visible_rect.y(),
                                           visible_rect.width(),
                                           visible_rect.height()).toImage()

            # 应用模糊效果
            blurred = self._apply_blur(screenshot)

            # 绘制效果
            painter.drawImage(visible_rect.topLeft(), blurred)
            painter.fillRect(visible_rect, self.tint_color)

    def _apply_blur(self, image):
        # 缩小图像提高性能
        small_img = image.scaled(
            max(1, image.width() // 2),
            max(1, image.height() // 2),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )

        # 应用高斯模糊
        blurred = self._gaussian_blur(small_img, self.blur_radius)

        # 放大回原尺寸
        return blurred.scaled(image.size(), Qt.SmoothTransformation)

    def _gaussian_blur(self, image, radius):
        if radius < 1:
            return image

        passes = 3
        box_radius = int(math.sqrt(radius ** 2 * 12 / passes) + 1) // 2
        if box_radius < 1:
            box_radius = 1

        blurred = image.copy()
        for _ in range(passes):
            blurred = self._box_blur(blurred, box_radius)
        return blurred

    def _box_blur(self, image, radius):
        if radius < 1 or image.isNull():
            return image

        # 水平模糊
        temp = self._box_blur_pass(image, radius, True)
        # 垂直模糊
        return self._box_blur_pass(temp, radius, False)

    def _box_blur_pass(self, src, radius, horizontal):
        w, h = src.width(), src.height()
        dst = QImage(w, h, QImage.Format_ARGB32)
        src_bits = src.bits().asarray(w * h * 4)
        dst_bits = dst.bits().asarray(w * h * 4)

        if horizontal:
            for y in range(h):
                sum_b = sum_g = sum_r = sum_a = 0
                count = 0

                # 初始化窗口
                for x in range(-radius, radius + 1):
                    px = max(0, min(x, w - 1))
                    idx = (y * w + px) * 4
                    sum_b += src_bits[idx]
                    sum_g += src_bits[idx + 1]
                    sum_r += src_bits[idx + 2]
                    sum_a += src_bits[idx + 3]
                    count += 1

                # 滑动处理
                for x in range(w):
                    idx = (y * w + x) * 4
                    dst_bits[idx] = sum_b // count
                    dst_bits[idx + 1] = sum_g // count
                    dst_bits[idx + 2] = sum_r // count
                    dst_bits[idx + 3] = sum_a // count

                    # 更新窗口
                    left = x - radius
                    if left >= 0:
                        left_idx = (y * w + left) * 4
                        sum_b -= src_bits[left_idx]
                        sum_g -= src_bits[left_idx + 1]
                        sum_r -= src_bits[left_idx + 2]
                        sum_a -= src_bits[left_idx + 3]
                        count -= 1

                    right = x + radius + 1
                    if right < w:
                        right_idx = (y * w + right) * 4
                        sum_b += src_bits[right_idx]
                        sum_g += src_bits[right_idx + 1]
                        sum_r += src_bits[right_idx + 2]
                        sum_a += src_bits[right_idx + 3]
                        count += 1
        else:
            # 垂直方向处理
            for x in range(w):
                sum_b = sum_g = sum_r = sum_a = 0
                count = 0

                for y in range(-radius, radius + 1):
                    py = max(0, min(y, h - 1))
                    idx = (py * w + x) * 4
                    sum_b += src_bits[idx]
                    sum_g += src_bits[idx + 1]
                    sum_r += src_bits[idx + 2]
                    sum_a += src_bits[idx + 3]
                    count += 1

                for y in range(h):
                    idx = (y * w + x) * 4
                    dst_bits[idx] = sum_b // count
                    dst_bits[idx + 1] = sum_g // count
                    dst_bits[idx + 2] = sum_r // count
                    dst_bits[idx + 3] = sum_a // count

                    # 更新窗口
                    top = y - radius
                    if top >= 0:
                        top_idx = (top * w + x) * 4
                        sum_b -= src_bits[top_idx]
                        sum_g -= src_bits[top_idx + 1]
                        sum_r -= src_bits[top_idx + 2]
                        sum_a -= src_bits[top_idx + 3]
                        count -= 1

                    bottom = y + radius + 1
                    if bottom < h:
                        bottom_idx = (bottom * w + x) * 4
                        sum_b += src_bits[bottom_idx]
                        sum_g += src_bits[bottom_idx + 1]
                        sum_r += src_bits[bottom_idx + 2]
                        sum_a += src_bits[bottom_idx + 3]
                        count += 1

        return dst


class TitleButton(QPushButton):
    bgColorChanged = Signal(QColor)

    def __init__(self, icon_code, config=None, parent=None):
        super().__init__(parent)
        self._icon_code = icon_code
        self._bg_color = QColor(0, 0, 0, 0)
        self._config = {
            'size': 32,
            'radius': 4,
            'color': 'white',
            'hover_color': 'rgba(255, 255, 255, 0.15)',
            'press_color': 'rgba(255, 255, 255, 0.25)',
            'font_size': 10,
            'font_family': self._best_icon_font()
        }
        if config:
            self._config.update(config)

        self._setup_ui()
        self._setup_animation()

    def _best_icon_font(self):
        preferred = ["Segoe MDL2 Assets", "Material Icons", "FontAwesome"]
        for font in preferred:
            if QFontDatabase.hasFamily(font):
                return font
        return self.font().family()

    def _setup_ui(self):
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
        self.setFixedSize(self._config['size'], self._config['size'])
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._update_style()

    def _setup_animation(self):
        self._anim = QPropertyAnimation(self, b"bgColor")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.OutQuad)

    def get_bg_color(self):
        return self._bg_color

    def set_bg_color(self, color):
        if self._bg_color != color:
            self._bg_color = color
            self.bgColorChanged.emit(color)
            self.update()

    bgColor = Property(QColor, get_bg_color, set_bg_color, notify=bgColorChanged)

    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._bg_color.name(QColor.HexArgb)};
                border: none;
                border-radius: {self._config['radius']}px;
                color: {self._config['color']};
                font-family: {self._config['font_family']};
                font-size: {self._config['font_size']}px;
                min-width: {self._config['size']}px;
                min-height: {self._config['size']}px;
            }}
            QPushButton:hover {{
                background-color: {self._config['hover_color']};
            }}
        """)

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self.bgColor)
        self._anim.setEndValue(QColor(255, 255, 255, 40))
        self._anim.start()

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self.bgColor)
        self._anim.setEndValue(QColor(0, 0, 0, 0))
        self._anim.start()

    def mousePressEvent(self, event):
        self._anim.stop()
        self.bgColor = QColor(255, 255, 255, 60)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        if self.bgColor.alpha() > 0:
            path = QPainterPath()
            path.addRoundedRect(self.rect(),
                                self._config['radius'],
                                self._config['radius'])
            painter.fillPath(path, self.bgColor)

        # 绘制图标
        painter.setFont(QFont(self._config['font_family'],
                              self._config['font_size']))
        painter.setPen(QColor(self._config['color']))
        painter.drawText(self.rect(), Qt.AlignCenter, self._icon_code)


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.drag_pos = None
        self._snap_margin = 20
        self._init_ui()
        self._init_style()

    def _init_ui(self):
        self.setFixedHeight(36)
        self.setMouseTracking(True)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 0, 8, 0)
        self.layout.setSpacing(4)

        # 窗口图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self._update_window_icon()

        # 窗口标题
        self.title_label = QLabel(self.window.windowTitle())
        self.title_label.setFont(QFont("Segoe UI", 9))
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # 窗口控制按钮
        btn_config = {
            'size': 32,
            'radius': 4,
            'color': '#ffffff',
            'hover_color': 'rgba(255,255,255,0.15)',
            'press_color': 'rgba(255,255,255,0.25)'
        }
        self.min_btn = TitleButton("\uE921", config=btn_config)
        self.max_btn = TitleButton("\uE922", config=btn_config)
        self.close_btn = TitleButton("\uE8BB", config={
            **btn_config,
            'color': '#ff5f57',
            'hover_color': '#ff5f57',
            'press_color': '#ff3b30'
        })

        # 按钮功能
        self.min_btn.clicked.connect(self.window.showMinimized)
        self.max_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.window.close)

        # 布局
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.min_btn)
        self.layout.addWidget(self.max_btn)
        self.layout.addWidget(self.close_btn)

        # 事件绑定
        self.window.windowTitleChanged.connect(self.title_label.setText)
        self.installEventFilter(self)

    def _init_style(self):
        self.setStyleSheet("""
            TitleBar {
                background-color: rgba(30, 30, 30, 0.6);
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QLabel {
                color: white;
                padding-left: 6px;
            }
        """)

    def toggle_maximize(self):
        if self.window.isMaximized():
            self.window.showNormal()
            self.max_btn._icon_code = "\uE922"
        else:
            self.window.showMaximized()
            self.max_btn._icon_code = "\uE923"
        self.max_btn.update()

    def _update_window_icon(self):
        icon = self.window.windowIcon()
        if not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(20, 20))

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("最小化", self.window.showMinimized)
        menu.addAction("最大化" if not self.window.isMaximized() else "还原",
                       self.toggle_maximize)
        menu.addAction("关闭", self.window.close)
        menu.exec(event.globalPosition().toPoint())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            self._check_aero_snap(self.drag_pos)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            current_pos = event.globalPosition().toPoint()
            if self._handle_aero_snap(current_pos):
                return
            delta = current_pos - self.drag_pos
            self.window.move(self.window.pos() + delta)
            self.drag_pos = current_pos

    def _check_aero_snap(self, pos):
        screen = QApplication.screenAt(pos)
        if not screen: return
        geo = screen.availableGeometry()
        if pos.y() <= geo.top() + self._snap_margin:
            self.window.showMaximized()
        elif pos.x() <= geo.left() + self._snap_margin:
            self.window.resize(geo.width() // 2, geo.height())
            self.window.move(geo.left(), geo.top())
        elif pos.x() >= geo.right() - self._snap_margin:
            self.window.resize(geo.width() // 2, geo.height())
            self.window.move(geo.left() + geo.width() // 2, geo.top())

    def _handle_aero_snap(self, pos):
        screen = QApplication.screenAt(pos)
        if not screen: return False
        geo = screen.availableGeometry()
        if pos.y() <= geo.top() + 5:
            self.window.showMaximized()
            return True
        return False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonDblClick:
            self.toggle_maximize()
            return True
        return super().eventFilter(obj, event)


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

        # 调整大小相关设置
        self.resize_margin = 10
        self.resize_direction = None
        self.mouse_pressed = False
        self.drag_pos = None

        # 鼠标跟踪设置
        self.setMouseTracking(True)
        self.windowHandle().screenChanged.connect(self.update_scale_factor)

        # 动态DPI适配
        self.dpi_scale = 1.0
        self.last_valid_cursor = None

        # 强制更新定时器
        self.cursor_timer = QTimer(interval=100, timeout=self.force_cursor_update)
        self.cursor_timer.start()

        # 右下角调整手柄
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("QSizeGrip { width: 16px; height: 16px; }")
        self.screen_rect = QApplication.primaryScreen().availableGeometry()



    def update_scale_factor(self):
        """自动适应屏幕缩放比例"""
        screen = self.windowHandle().screen()
        self.dpi_scale = screen.devicePixelRatio()
        self.resize_margin = int(10 * self.dpi_scale)

    def update_resize_cursor(self, pos=None):
        """带坐标补偿的智能检测"""
        if pos is None:
            pos = self.mapFromGlobal(QCursor.pos())

        # 精确坐标转换
        scaled_pos = QPoint(
            int(pos.x() * self.dpi_scale),
            int(pos.y() * self.dpi_scale)
        )

        edge = self._get_resize_edge(scaled_pos)
        if edge == 0:
            if self.last_valid_cursor is not None:
                self.unsetCursor()
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
                self.setCursor(new_cursor)
                self.last_valid_cursor = new_cursor

    def force_cursor_update(self):
        """定时强制更新机制"""
        if not self.underMouse():
            self.unsetCursor()
            self.last_valid_cursor = None
        else:
            self.update_resize_cursor()

    def eventFilter(self, obj, event):
        """子控件事件穿透"""
        if event.type() == QEvent.MouseMove:
            self.update_resize_cursor(event.pos())
        return super().eventFilter(obj, event)

    def _get_resize_edge(self, pos):
        """抗抖动边缘检测算法"""
        x, y = pos.x(), pos.y()
        rect = self.rect()
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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 使用全局坐标作为基准
            self.start_global_pos = event.globalPosition().toPoint()
            self.start_geometry = self.geometry()

            # 检测调整区域
            local_pos = event.position().toPoint()
            self.resize_direction = self._get_resize_edge(local_pos)

            if not self.resize_direction:
                # 窗口拖动模式
                self.drag_offset = self.start_global_pos - self.geometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        current_global_pos = event.globalPosition().toPoint()

        if self.resize_direction and event.buttons() == Qt.LeftButton:
            # 窗口调整模式
            delta = current_global_pos - self.start_global_pos
            new_geo = QRect(self.start_geometry)

            # 根据方向调整几何
            if self.resize_direction & 1:  # 左
                new_geo.setLeft(min(new_geo.left() + delta.x(),
                                    new_geo.right() - self.minimumWidth()))
            if self.resize_direction & 2:  # 右
                new_geo.setRight(max(new_geo.right() + delta.x(),
                                     new_geo.left() + self.minimumWidth()))
            if self.resize_direction & 4:  # 上
                new_geo.setTop(min(new_geo.top() + delta.y(),
                                   new_geo.bottom() - self.minimumHeight()))
            if self.resize_direction & 8:  # 下
                new_geo.setBottom(max(new_geo.bottom() + delta.y(),
                                      new_geo.top() + self.minimumHeight()))

            # 限制在屏幕范围内
            new_geo = new_geo.intersected(self.screen_rect)
            self.setGeometry(new_geo)

        elif event.buttons() == Qt.LeftButton and hasattr(self, 'drag_offset'):
            # 窗口拖动模式
            new_pos = current_global_pos - self.drag_offset
            # 限制窗口在屏幕内
            new_x = max(self.screen_rect.left(),
                        min(new_pos.x(), self.screen_rect.right() - self.width()))
            new_y = max(self.screen_rect.top(),
                        min(new_pos.y(), self.screen_rect.bottom() - self.height()))
            self.move(new_x, new_y)

        # 增加坐标补偿
        scaled_pos = QPoint(
            int(event.position().x() * self.dpi_scale),
            int(event.position().y() * self.dpi_scale))
        self.update_resize_cursor(scaled_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resize_direction = None
        self.update_resize_cursor(event.position().toPoint())  # 释放后立即更新
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口时强制恢复"""
        self.unsetCursor()
        self.last_valid_cursor = None

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
        # 更新屏幕尺寸信息
        self.screen_rect = QApplication.primaryScreen().availableGeometry()
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