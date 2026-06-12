# -*- coding: utf-8 -*-
"""
可折叠面板组件

提供带展开/收起功能的面板容器。
内容短时自然显示，超出可用空间时才出现滚动条。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QScrollArea, QSizePolicy
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
        # 强制父布局重新计算，让 stretch 立即生效
        parent = self.parentWidget()
        if parent and parent.layout():
            parent.layout().activate()

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
        """根据内容高度决定是否需要滚动条。

        始终用 QScrollArea 包裹内容，让 stretch 撑满剩余空间，
        内容超出时出现滚动条，未超出时自然显示。
        """
        layout = self.layout()
        if self._scroll_area is not None:
            # 已经有滚动区域，确保它可见并刷新
            self._scroll_area.setVisible(True)
            return

        # 始终用 QScrollArea 包裹，让 stretch 生效
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QScrollArea.NoFrame)
        self._scroll_area.setWidget(self._content_widget)

        # 关键：让 QScrollArea 和内容 widget 都能被拉伸
        self._scroll_area.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding
        )
        self._content_widget.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding
        )

        layout.removeWidget(self._content_widget)
        layout.insertWidget(self._content_index, self._scroll_area)

    def set_expanded(self, expanded: bool):
        self._header.setChecked(expanded)
        if self._scroll_area is not None:
            self._scroll_area.setVisible(expanded)
        else:
            self._content_widget.setVisible(expanded)
        self._update_arrow()

    def is_expanded(self) -> bool:
        return self._header.isChecked()
