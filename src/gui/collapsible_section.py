# -*- coding: utf-8 -*-
"""
可折叠面板组件

提供带展开/收起功能的面板容器。
三个面板共用外层 QScrollArea，组件本身不创建滚动条。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal


class CollapsibleSection(QWidget):
    """可折叠面板：点击标题栏展开/收起内容"""

    toggled = Signal(bool)  # 展开/收起时发出

    def __init__(self, title: str, content_widget: QWidget, parent=None, expanded: bool = True):
        super().__init__(parent)

        self._title = title
        self._content_widget = content_widget

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

        # 内容区域
        layout.addWidget(self._content_widget)

        self._update_arrow()

    def _toggle(self):
        """切换展开/收起"""
        visible = self._header.isChecked()
        self._content_widget.setVisible(visible)
        self._update_arrow()
        self._update_stretch(visible)
        # 通知父布局重新计算
        parent = self.parentWidget()
        if parent and parent.layout():
            parent.layout().activate()
        self.toggled.emit(visible)

    def _update_stretch(self, expanded: bool):
        """展开时在父布局中设置 stretch=1 撑满空间，收起时恢复 stretch=0"""
        parent = self.parentWidget()
        if parent and parent.layout():
            layout = parent.layout()
            idx = layout.indexOf(self)
            if idx >= 0:
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

    def set_expanded(self, expanded: bool):
        self._header.setChecked(expanded)
        self._content_widget.setVisible(expanded)
        self._update_arrow()

    def is_expanded(self) -> bool:
        return self._header.isChecked()
