import sys
import ctypes
import math
from ctypes import wintypes
from PySide6.QtCore import QTimer, QRect, QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QImage
from PySide6.QtWidgets import QApplication


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