# -*- coding: utf-8 -*-
"""
文件选择组件

提供Excel文件的选择和管理功能。
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QLabel,
    QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

# 导入QSettings用于历史记录
from PySide6.QtCore import QSettings


class FileSelector(QWidget):
    """文件选择组件，支持选择单个或多个Excel文件"""

    # 信号：当文件选择改变时发出
    files_changed = Signal(list)
    # 信号：当前操作文件改变 (excel_path)
    current_file_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files = []
        self._settings = QSettings("架构图生成器", "应用架构图生成器")
        self._setup_ui()
        self.setAcceptDrops(True)
        self._load_recent_files()

    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.add_file_btn = QPushButton("添加文件")
        self.add_file_btn.clicked.connect(self._on_add_file)
        btn_layout.addWidget(self.add_file_btn)

        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self._on_add_folder)
        btn_layout.addWidget(self.add_folder_btn)

        self.recent_btn = QPushButton("最近文件")
        self.recent_btn.setToolTip("显示最近打开的文件")
        self.recent_btn.clicked.connect(self._on_recent_files)
        btn_layout.addWidget(self.recent_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._on_clear)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setMinimumHeight(60)  # 至少显示约2行
        self.file_list.currentItemChanged.connect(self._on_current_item_changed)
        layout.addWidget(self.file_list)

        # 删除选中按钮
        self.remove_btn = QPushButton("删除选中")
        self.remove_btn.clicked.connect(self._on_remove_selected)
        layout.addWidget(self.remove_btn)

        # 文件计数
        self.count_label = QLabel("共 0 个文件")
        layout.addWidget(self.count_label)

    def _on_add_file(self):
        """添加单个文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        if files:
            self._add_files(files)

    def _on_add_folder(self):
        """添加文件夹中的所有Excel文件"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            excel_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.xlsx', '.xls')):
                        excel_files.append(os.path.join(root, file))
            if excel_files:
                self._add_files(excel_files)
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "提示", "所选文件夹中没有找到Excel文件")

    def _add_files(self, file_paths: list):
        """添加文件到列表"""
        for file_path in file_paths:
            if file_path not in self._files:
                self._files.append(file_path)
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                item.setToolTip(file_path)
                self.file_list.addItem(item)
                # 保存到最近文件
                self._save_to_recent(file_path)
        self._update_count()
        self.files_changed.emit(self._files)

    def _save_to_recent(self, file_path: str):
        """保存文件到最近文件列表"""
        recent_files = self._settings.value("recent_files", [])
        if not isinstance(recent_files, list):
            recent_files = []

        # 如果文件已存在，先移除
        if file_path in recent_files:
            recent_files.remove(file_path)

        # 添加到列表开头
        recent_files.insert(0, file_path)

        # 最多保存10个
        if len(recent_files) > 10:
            recent_files = recent_files[:10]

        self._settings.setValue("recent_files", recent_files)

    def _load_recent_files(self):
        """加载最近文件列表（用于初始化）"""
        # 这个方法可以在启动时调用，预加载最近文件
        pass

    def _on_recent_files(self):
        """显示最近文件菜单"""
        recent_files = self._settings.value("recent_files", [])
        if not isinstance(recent_files, list):
            recent_files = []

        if not recent_files:
            QMessageBox.information(self, "提示", "没有最近打开的文件")
            return

        # 创建菜单
        menu = QMenu(self)

        # 过滤掉不存在的文件
        valid_files = []
        for file_path in recent_files:
            if os.path.exists(file_path):
                valid_files.append(file_path)

        if not valid_files:
            QMessageBox.information(self, "提示", "最近打开的文件都不存在")
            return

        # 添加菜单项
        for file_path in valid_files:
            action = menu.addAction(os.path.basename(file_path))
            action.setToolTip(file_path)
            action.setData(file_path)

        # 显示菜单
        action = menu.exec(self.recent_btn.mapToGlobal(self.recent_btn.rect().bottomLeft()))

        if action:
            file_path = action.data()
            if file_path and os.path.exists(file_path):
                self._add_files([file_path])

    def _on_clear(self):
        """清空文件列表"""
        self._files.clear()
        self.file_list.clear()
        self._update_count()
        self.files_changed.emit([])

    def _on_remove_selected(self):
        """删除选中的文件"""
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path in self._files:
                self._files.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))
        self._update_count()
        self.files_changed.emit(self._files)

    def _update_count(self):
        """更新文件计数"""
        self.count_label.setText(f"共 {len(self._files)} 个文件")

    def get_files(self) -> list:
        """获取当前文件列表"""
        return self._files.copy()

    def get_current_file(self) -> str | None:
        """获取当前操作的 Excel 文件路径"""
        item = self.file_list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None

    def _on_current_item_changed(self, current, previous):
        """列表当前项改变时触发"""
        if current:
            excel_path = current.data(Qt.UserRole)
            if excel_path:
                self.current_file_changed.emit(excel_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.xlsx', '.xls')):
                files.append(file_path)
        if files:
            self._add_files(files)
