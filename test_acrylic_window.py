import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QApplication
from acrylic_window import AcrylicWindow


class MyWindow(AcrylicWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口内容

        label = QLabel("这是一个亚克力效果窗口")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: white; font-size: 24px;")

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

        # 自定义效果参数
        self.acrylic.set_blur_radius(10)
        self.acrylic.set_tint_color(QColor(40, 40, 40, 180))
        self.acrylic.set_update_interval(30)
        self.acrylic.set_opacity(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())