# -*- coding: utf-8 -*-
"""
文件信息预览组件

显示选中Excel文件的基本信息和数据预览。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QGroupBox, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt

# 导入项目模块
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from src.data_loader import load_data_from_excel


class FileInfoWidget(QWidget):
    """文件信息预览组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 文件信息组
        info_group = QGroupBox("文件信息")
        info_layout = QVBoxLayout(info_group)

        # 文件名
        self.file_name_label = QLabel("文件名: -")
        info_layout.addWidget(self.file_name_label)

        # 文件大小
        self.file_size_label = QLabel("文件大小: -")
        info_layout.addWidget(self.file_size_label)

        # 域名称
        self.domain_label = QLabel("域名称: -")
        info_layout.addWidget(self.domain_label)

        # 应用组数
        self.groups_count_label = QLabel("应用组数: -")
        info_layout.addWidget(self.groups_count_label)

        # 模块总数
        self.modules_count_label = QLabel("模块总数: -")
        info_layout.addWidget(self.modules_count_label)

        layout.addWidget(info_group)

        # 数据预览组
        preview_group = QGroupBox("数据预览")
        preview_layout = QVBoxLayout(preview_group)

        # 数据树形视图
        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["应用组", "模块"])
        self.data_tree.setAlternatingRowColors(True)
        preview_layout.addWidget(self.data_tree)

        layout.addWidget(preview_group)

    def clear(self):
        """清空显示"""
        self.file_name_label.setText("文件名: -")
        self.file_size_label.setText("文件大小: -")
        self.domain_label.setText("域名称: -")
        self.groups_count_label.setText("应用组数: -")
        self.modules_count_label.setText("模块总数: -")
        self.data_tree.clear()

    def load_file(self, file_path: str):
        """加载并显示文件信息

        Args:
            file_path: Excel文件路径
        """
        try:
            # 显示文件基本信息
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_size_str = self._format_file_size(file_size)

            self.file_name_label.setText(f"文件名: {file_name}")
            self.file_size_label.setText(f"文件大小: {file_size_str}")

            # 加载Excel数据
            domain_name, groups = load_data_from_excel(file_path)

            # 显示数据统计
            self.domain_label.setText(f"域名称: {domain_name}")
            self.groups_count_label.setText(f"应用组数: {len(groups)}")

            total_modules = sum(len(modules) for modules in groups.values())
            self.modules_count_label.setText(f"模块总数: {total_modules}")

            # 显示数据树形视图
            self._show_data_tree(domain_name, groups)

        except Exception as e:
            self.file_name_label.setText(f"文件名: {os.path.basename(file_path)}")
            self.file_size_label.setText(f"加载失败: {str(e)}")
            self.domain_label.setText("域名称: -")
            self.groups_count_label.setText("应用组数: -")
            self.modules_count_label.setText("模块总数: -")
            self.data_tree.clear()

    def _show_data_tree(self, domain_name: str, groups: dict):
        """显示数据树形视图

        Args:
            domain_name: 域名称
            groups: 应用组数据
        """
        self.data_tree.clear()
        self.data_tree.setHeaderLabels(["应用组", "模块"])

        for group_name, modules in groups.items():
            # 创建应用组节点
            group_item = QTreeWidgetItem(self.data_tree)
            group_item.setText(0, group_name)
            group_item.setText(1, f"({len(modules)} 个模块)")
            group_item.setExpanded(True)

            # 添加模块节点
            for module_name in modules:
                module_item = QTreeWidgetItem(group_item)
                module_item.setText(0, "")
                module_item.setText(1, module_name)

        # 调整列宽
        self.data_tree.resizeColumnToContents(0)
        self.data_tree.resizeColumnToContents(1)

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小

        Args:
            size_bytes: 文件大小（字节）

        Returns:
            格式化的文件大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
