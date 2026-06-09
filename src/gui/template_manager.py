# -*- coding: utf-8 -*-
"""
模板管理器

提供参数配置模板的保存、加载和删除功能。
"""

import os
import json
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt

# 获取用户目录
USER_DIR = os.path.expanduser("~")
TEMPLATES_DIR = os.path.join(USER_DIR, ".架构图生成器", "templates")


class TemplateManager:
    """模板管理器，提供模板的保存、加载和删除功能"""

    def __init__(self):
        """初始化模板管理器"""
        self._ensure_templates_dir()

    def _ensure_templates_dir(self):
        """确保模板目录存在"""
        if not os.path.exists(TEMPLATES_DIR):
            os.makedirs(TEMPLATES_DIR, exist_ok=True)

    def save_template(self, name: str, params: dict, description: str = "") -> bool:
        """保存参数配置为模板

        Args:
            name: 模板名称
            params: 参数配置字典
            description: 模板描述（可选）

        Returns:
            保存是否成功
        """
        try:
            # 创建模板数据
            template_data = {
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "params": params
            }

            # 生成文件名（将模板名称转换为安全的文件名）
            safe_name = self._safe_filename(name)
            file_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")

            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"保存模板失败: {e}")
            return False

    def load_template(self, name: str) -> dict:
        """加载模板

        Args:
            name: 模板名称

        Returns:
            模板数据字典，失败返回None
        """
        try:
            safe_name = self._safe_filename(name)
            file_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")

            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)

            return template_data

        except Exception as e:
            print(f"加载模板失败: {e}")
            return None

    def delete_template(self, name: str) -> bool:
        """删除模板

        Args:
            name: 模板名称

        Returns:
            删除是否成功
        """
        try:
            safe_name = self._safe_filename(name)
            file_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")

            if os.path.exists(file_path):
                os.remove(file_path)
                return True

            return False

        except Exception as e:
            print(f"删除模板失败: {e}")
            return False

    def list_templates(self) -> list:
        """列出所有可用的模板

        Returns:
            模板信息列表，每个元素包含name、description、created_at
        """
        templates = []

        try:
            if not os.path.exists(TEMPLATES_DIR):
                return templates

            for file_name in os.listdir(TEMPLATES_DIR):
                if file_name.endswith('.json'):
                    file_path = os.path.join(TEMPLATES_DIR, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            templates.append({
                                "name": template_data.get("name", ""),
                                "description": template_data.get("description", ""),
                                "created_at": template_data.get("created_at", "")
                            })
                    except:
                        # 跳过无效的模板文件
                        continue

        except Exception as e:
            print(f"列出模板失败: {e}")

        return templates

    def _safe_filename(self, name: str) -> str:
        """将模板名称转换为安全的文件名

        Args:
            name: 原始名称

        Returns:
            安全的文件名
        """
        # 替换Windows文件名中的非法字符
        illegal_chars = '<>:"/\\|?*'
        safe_name = name
        for char in illegal_chars:
            safe_name = safe_name.replace(char, '_')

        # 限制文件名长度
        if len(safe_name) > 50:
            safe_name = safe_name[:50]

        return safe_name


class TemplateDialog(QDialog):
    """模板选择对话框"""

    def __init__(self, parent=None, mode="load"):
        """初始化对话框

        Args:
            parent: 父窗口
            mode: 对话框模式，"load"或"save"
        """
        super().__init__(parent)
        self.mode = mode
        self.selected_template = None
        self.template_manager = TemplateManager()
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        """设置UI布局"""
        self.setWindowTitle("模板管理" if self.mode == "load" else "保存模板")
        self.setMinimumSize(400, 400)

        layout = QVBoxLayout(self)

        if self.mode == "load":
            # 加载模板模式
            label = QLabel("选择要加载的模板:")
            layout.addWidget(label)

            # 模板列表
            self.template_list = QListWidget()
            self.template_list.itemDoubleClicked.connect(self._on_load)
            layout.addWidget(self.template_list)

            # 按钮区域
            btn_layout = QHBoxLayout()

            self.load_btn = QPushButton("加载")
            self.load_btn.clicked.connect(self._on_load)
            self.load_btn.setEnabled(False)
            btn_layout.addWidget(self.load_btn)

            self.delete_btn = QPushButton("删除")
            self.delete_btn.clicked.connect(self._on_delete)
            self.delete_btn.setEnabled(False)
            btn_layout.addWidget(self.delete_btn)

            self.cancel_btn = QPushButton("取消")
            self.cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(self.cancel_btn)

            layout.addLayout(btn_layout)

            # 连接选择事件
            self.template_list.currentItemChanged.connect(self._on_selection_changed)

        else:
            # 保存模板模式
            label = QLabel("输入模板名称:")
            layout.addWidget(label)

            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText("例如：默认配置")
            layout.addWidget(self.name_edit)

            desc_label = QLabel("模板描述（可选）:")
            layout.addWidget(desc_label)

            self.desc_edit = QTextEdit()
            self.desc_edit.setMaximumHeight(100)
            self.desc_edit.setPlaceholderText("输入模板描述...")
            layout.addWidget(self.desc_edit)

            # 按钮区域
            btn_layout = QHBoxLayout()

            self.save_btn = QPushButton("保存")
            self.save_btn.clicked.connect(self._on_save)
            btn_layout.addWidget(self.save_btn)

            self.cancel_btn = QPushButton("取消")
            self.cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(self.cancel_btn)

            layout.addLayout(btn_layout)

    def _load_templates(self):
        """加载模板列表"""
        if self.mode != "load":
            return
        self.template_list.clear()
        templates = self.template_manager.list_templates()

        for template in templates:
            item = QListWidgetItem(template["name"])
            item.setData(Qt.UserRole, template)
            tooltip = f"名称: {template['name']}"
            if template.get('description'):
                tooltip += f"\n描述: {template['description']}"
            if template.get('created_at'):
                tooltip += f"\n创建时间: {template['created_at']}"
            item.setToolTip(tooltip)
            self.template_list.addItem(item)

    def _on_selection_changed(self, current, previous):
        """选择改变时"""
        has_selection = current is not None
        self.load_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _on_load(self):
        """加载模板"""
        current_item = self.template_list.currentItem()
        if current_item:
            template_data = current_item.data(Qt.UserRole)
            self.selected_template = template_data
            self.accept()

    def _on_delete(self):
        """删除模板"""
        current_item = self.template_list.currentItem()
        if current_item:
            template_data = current_item.data(Qt.UserRole)
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除模板 '{template_data['name']}' 吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if self.template_manager.delete_template(template_data['name']):
                    self._load_templates()  # 刷新列表
                else:
                    QMessageBox.warning(self, "错误", "删除模板失败")

    def _on_save(self):
        """保存模板"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入模板名称")
            return

        description = self.desc_edit.toPlainText().strip()
        self.selected_template = {
            "name": name,
            "description": description
        }
        self.accept()

    def get_selected_template(self) -> dict:
        """获取选中的模板"""
        return self.selected_template


def get_template_manager() -> TemplateManager:
    """获取模板管理器实例"""
    return TemplateManager()
