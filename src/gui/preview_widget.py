# -*- coding: utf-8 -*-
"""
预览组件

提供架构图的预览显示功能，支持多图片切换。
"""

from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap


class PreviewWidget(QWidget):
    """预览组件，用于显示生成的架构图，支持多图片切换"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pixmap = None  # 保存原始图片
        self._image_history = []  # 图片历史记录
        self._current_index = -1  # 当前显示的图片索引
        self._setup_ui()

    def _setup_ui(self):
        """设置UI布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建导航栏（左右箭头 + 图片计数）
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(5, 5, 5, 5)

        # 左箭头按钮
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A73E8;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1557B0;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.prev_btn.clicked.connect(self._on_prev)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)

        # 图片计数标签
        self.count_label = QLabel("0 / 0")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("font-weight: bold; color: #666;")
        nav_layout.addWidget(self.count_label)

        # 右箭头按钮
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A73E8;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1557B0;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.next_btn.clicked.connect(self._on_next)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        main_layout.addLayout(nav_layout)

        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")

        # 设置默认提示文字
        self._show_welcome_message()
        self.image_label.setMinimumSize(400, 300)

        self.scroll_area.setWidget(self.image_label)
        main_layout.addWidget(self.scroll_area)

    def _show_welcome_message(self):
        """显示欢迎信息"""
        self.image_label.setText(
            "欢迎使用应用架构图生成器\n\n"
            "使用步骤:\n"
            "1. 在左侧选择Excel文件\n"
            "2. 调整参数（可选）\n"
            "3. 点击\"生成架构图\"按钮\n\n"
            "生成的架构图将在此处显示\n"
            "支持左右箭头切换多张图片"
        )

    def add_image(self, image_path: str):
        """添加图片到历史记录

        Args:
            image_path: 图片文件路径
        """
        if image_path and image_path not in self._image_history:
            self._image_history.append(image_path)
            self._current_index = len(self._image_history) - 1
            self._update_navigation()
            self._show_current_image()

    def set_image(self, image_path: str, force_refresh: bool = False):
        """设置预览图片（兼容旧接口）

        Args:
            image_path: 图片文件路径
            force_refresh: 如果为 True，即使路径相同也强制刷新图片
        """
        if force_refresh and image_path and image_path in self._image_history:
            # 强制刷新当前显示的图片（文件内容已更新）
            self._current_index = self._image_history.index(image_path)
            self._show_current_image()
        else:
            self.add_image(image_path)

    def _update_navigation(self):
        """更新导航按钮状态"""
        total = len(self._image_history)
        current = self._current_index + 1

        # 更新计数标签
        self.count_label.setText(f"{current} / {total}")

        # 更新按钮状态
        self.prev_btn.setEnabled(self._current_index > 0)
        self.next_btn.setEnabled(self._current_index < total - 1)

    def _show_current_image(self):
        """显示当前索引的图片"""
        if not self._image_history or self._current_index < 0:
            return

        image_path = self._image_history[self._current_index]
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self._original_pixmap = pixmap
            self._update_image_size()
        else:
            self.image_label.setText(f"无法加载图片:\n{image_path}")

    def _on_prev(self):
        """点击左箭头"""
        if self._current_index > 0:
            self._current_index -= 1
            self._update_navigation()
            self._show_current_image()

    def _on_next(self):
        """点击右箭头"""
        if self._current_index < len(self._image_history) - 1:
            self._current_index += 1
            self._update_navigation()
            self._show_current_image()

    def _update_image_size(self):
        """更新图片大小以适应预览区域"""
        if self._original_pixmap is None:
            return

        # 获取滚动区域的大小
        scroll_size = self.scroll_area.size()

        # 缩放图片以适应预览区域
        scaled_pixmap = self._original_pixmap.scaled(
            scroll_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self._update_image_size()

    def clear(self):
        """清空预览"""
        self._original_pixmap = None
        self._image_history = []
        self._current_index = -1
        self.image_label.clear()
        self._show_welcome_message()
        self._update_navigation()

    def clear_history(self):
        """清空历史记录但保留当前显示"""
        if self._image_history:
            current_image = self._image_history[self._current_index]
            self._image_history = [current_image]
            self._current_index = 0
            self._update_navigation()

    def get_history(self):
        """获取图片历史记录"""
        return self._image_history.copy()

    def get_current_index(self):
        """获取当前图片索引"""
        return self._current_index

    def set_html(self, html_content: str):
        """设置HTML内容预览（备用方案）

        Args:
            html_content: HTML内容字符串
        """
        # 如果需要支持HTML预览，可以使用QWebEngineView
        # 目前先保留图片预览方式
        pass
