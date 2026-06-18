# -*- coding: utf-8 -*-
"""
批量模块调色对话框

展示当前文件所有模块，支持多选 + 选色 + 批量应用。
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal

from .params_panel import ColorButton


class ModuleColorDialog(QDialog):
    """批量模块调色对话框"""

    # 信号：(module_names: list[str], color: str)
    colors_applied = Signal(list, str)

    def __init__(self, modules: dict, parent=None):
        """
        Args:
            modules: {group_name: [module_name, ...]}
        """
        super().__init__(parent)
        self.setWindowTitle("批量模块调色")
        self.setMinimumSize(500, 400)
        self._modules = modules
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)

        # 提示
        hint = QLabel("选择要调色的模块（按住 Ctrl 多选），选择颜色后点击应用")
        hint.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(hint)

        # 主体：左右分栏
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：模块树
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["分组 / 模块", "数量"])
        self.tree.setSelectionMode(QTreeWidget.MultiSelection)
        self.tree.setAlternatingRowColors(True)
        self.tree.setColumnWidth(0, 300)  # 分组/模块列宽
        self.tree.setColumnWidth(1, 50)   # 数量列窄
        self._populate_tree()
        splitter.addWidget(self.tree)

        # 右侧：操作区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 4, 0)
        right_layout.setSpacing(6)

        # 全选 / 取消全选
        select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all)
        select_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("取消全选")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        select_layout.addWidget(self.deselect_all_btn)
        right_layout.addLayout(select_layout)

        # 颜色选择
        right_layout.addWidget(QLabel("选择颜色:"))
        self.color_btn = ColorButton('#C4D8FC')
        right_layout.addWidget(self.color_btn)

        # 已选计数
        self.count_label = QLabel("已选: 0 个模块")
        right_layout.addWidget(self.count_label)

        # 应用按钮
        self.apply_btn = QPushButton("应用")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.apply_btn.clicked.connect(self._on_apply)
        right_layout.addWidget(self.apply_btn)

        splitter.addWidget(right_widget)
        splitter.setSizes([340, 170])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # 连接选择变化
        self.tree.itemSelectionChanged.connect(self._update_count)

    def _populate_tree(self):
        """填充模块树"""
        for group_name, modules in self._modules.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, group_name)
            group_item.setText(1, f"{len(modules)} 个")
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)
            group_item.setExpanded(True)

            for module_name in modules:
                item = QTreeWidgetItem(group_item)
                item.setText(0, module_name)
                item.setData(0, Qt.UserRole, module_name)

    def _select_all(self):
        """全选所有模块"""
        self.tree.selectAll()

    def _deselect_all(self):
        """取消全选"""
        self.tree.clearSelection()

    def _update_count(self):
        """更新已选计数"""
        count = len(self.tree.selectedItems())
        self.count_label.setText(f"已选: {count} 个模块")

    def _get_selected_modules(self) -> list:
        """获取选中的模块名列表"""
        modules = []
        for item in self.tree.selectedItems():
            name = item.data(0, Qt.UserRole)
            if name:
                modules.append(name)
        return modules

    def _on_apply(self):
        """应用颜色"""
        modules = self._get_selected_modules()
        if not modules:
            return
        color = self.color_btn.get_color()
        self.colors_applied.emit(modules, color)
        self.accept()  # 关闭对话框
