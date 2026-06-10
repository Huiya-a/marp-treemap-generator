# -*- coding: utf-8 -*-
"""
可折叠面板组件

提供带展开/收起功能的面板容器。
内容短时自然显示，超出可用空间时才出现滚动条。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt


class CollapsibleSection(QWidget):
    """可折叠面板：点击标题栏展开/收起内容"""

    def __init__(self, title: str, content_widget: QWidget, parent=None, expanded: bool = True):
        super().__init__(parent)

        self._content_widget = content_widget
        self._scroll_area = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题按钮
        self._header = QPushButton(title)
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.setStyleSheet("""
            QPushButton {
                text-align: left;
                font-weight: bold;
                font-size: 13px;
                padding: 6px 8px;
                border: none;
                background-color: #E8E8E8;
                color: #333;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # 内容插入位置（header 之后 = index 1）
        self._content_index = 1
        layout.insertWidget(self._content_index, self._content_widget)

        self._update_arrow()

    def _toggle(self):
        """切换展开/收起"""
        visible = self._header.isChecked()
        if self._scroll_area is not None:
            self._scroll_area.setVisible(visible)
        else:
            self._content_widget.setVisible(visible)
        self._update_arrow()
        self._update_stretch(visible)
        if visible:
            self._check_scroll()

    def _update_stretch(self, expanded: bool):
        """展开时在父布局中设置 stretch=1 撑满空间，收起时恢复 stretch=0"""
        parent = self.parentWidget()
        if parent and parent.layout():
            layout = parent.layout()
            idx = layout.indexOf(self)
            if idx >= 0:
                item = layout.itemAt(idx)
                if item:
                    layout.setStretchFactor(self, 1 if expanded else 0)

    def _update_arrow(self):
        """更新标题栏箭头方向"""
        arrow = "▼ " if self._header.isChecked() else "▶ "
        text = self._header.text()
        for prefix in ("▼ ", "▶ "):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        self._header.setText(arrow + text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._header.isChecked():
            self._check_scroll()

    def _check_scroll(self):
        """根据内容高度决定是否需要滚动条。"""
        available = self.height() - self._header.height()
        content_h = self._content_widget.sizeHint().height()
        layout = self.layout()

        if content_h > available and self._scroll_area is None:
            # 内容超出 → 包裹 QScrollArea
            self._scroll_area = QScrollArea()
            self._scroll_area.setWidgetResizable(True)
            self._scroll_area.setFrameShape(QScrollArea.NoFrame)
            self._scroll_area.setWidget(self._content_widget)

            layout.removeWidget(self._content_widget)
            layout.insertWidget(self._content_index, self._scroll_area)

        elif content_h <= available and self._scroll_area is not None:
            # 内容未超出 → 移除 QScrollArea，恢复直接显示
            self._scroll_area.setWidget(None)
            layout.removeWidget(self._scroll_area)
            self._scroll_area.deleteLater()
            self._scroll_area = None
            layout.insertWidget(self._content_index, self._content_widget)

    def set_expanded(self, expanded: bool):
        self._header.setChecked(expanded)
        if self._scroll_area is not None:
            self._scroll_area.setVisible(expanded)
        else:
            self._content_widget.setVisible(expanded)
        self._update_arrow()

    def is_expanded(self) -> bool:
        return self._header.isChecked()
