from PySide6.QtCore import (Qt, QPoint, QPropertyAnimation, Property,
                            Signal, QEvent, QRect, QEasingCurve)
from PySide6.QtGui import (QColor, QPainter, QPainterPath, QFont,
                          QFontDatabase, QIcon)
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel, QHBoxLayout,
                              QSizePolicy, QMenu, QApplication)

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