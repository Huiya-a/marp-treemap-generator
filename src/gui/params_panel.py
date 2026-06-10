# -*- coding: utf-8 -*-
"""
参数调整面板

提供布局参数、颜色、字体等的调整功能。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,
    QColorDialog, QPushButton, QScrollArea, QMessageBox, QDialog
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QWheelEvent

# 导入配置模块
import sys
import os
# 从src/gui向上两级到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from src import config

# 导入模板管理器
from .template_manager import TemplateManager, TemplateDialog


class NoWheelSpinBox(QSpinBox):
    """禁用滚轮事件的QSpinBox"""

    def wheelEvent(self, event: QWheelEvent):
        # 忽略滚轮事件
        event.ignore()


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """禁用滚轮事件的QDoubleSpinBox"""

    def wheelEvent(self, event: QWheelEvent):
        # 忽略滚轮事件
        event.ignore()


class ColorButton(QPushButton):
    """颜色选择按钮"""

    color_changed = Signal(str)

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._on_click)
        self.setFixedSize(60, 25)

    def _update_style(self):
        """更新按钮样式"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 1px solid #999;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 1px solid #666;
            }}
        """)

    def _on_click(self):
        """点击打开颜色选择器"""
        color = QColorDialog.getColor(QColor(self._color), self, "选择颜色")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self) -> str:
        """获取当前颜色"""
        return self._color

    def set_color(self, color: str):
        """设置颜色"""
        self._color = color
        self._update_style()


class ParamsPanel(QWidget):
    """参数调整面板"""

    # 信号：参数改变时发出
    params_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._template_manager = TemplateManager()
        self._setup_ui()

    def _setup_ui(self):
        """设置UI布局"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # ========== 颜色参数组 ==========
        color_group = QGroupBox("颜色设置")
        color_layout = QVBoxLayout(color_group)

        # 组背景色
        row = QHBoxLayout()
        row.addWidget(QLabel("组背景色:"))
        self.group_bg_color = ColorButton(config.GROUP_BG)
        self.group_bg_color.setToolTip("应用组的背景颜色")
        self.group_bg_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.group_bg_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 组标题色
        row = QHBoxLayout()
        row.addWidget(QLabel("组标题色:"))
        self.group_header_color = ColorButton(config.GROUP_HEADER_COLOR)
        self.group_header_color.setToolTip("应用组标题栏的颜色")
        self.group_header_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.group_header_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 模块背景色
        row = QHBoxLayout()
        row.addWidget(QLabel("模块背景色:"))
        self.module_bg_color = ColorButton(config.MODULE_BG_COLOR)
        self.module_bg_color.setToolTip("应用模块的背景颜色")
        self.module_bg_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.module_bg_color)
        row.addStretch()
        color_layout.addLayout(row)

        layout.addWidget(color_group)

        # ========== 尺寸参数组 ==========
        size_group = QGroupBox("尺寸设置")
        size_layout = QVBoxLayout(size_group)

        # 模块宽度
        row = QHBoxLayout()
        row.addWidget(QLabel("模块宽度:"))
        self.module_w_spin = NoWheelDoubleSpinBox()
        self.module_w_spin.setRange(0.5, 3.0)
        self.module_w_spin.setSingleStep(0.1)
        self.module_w_spin.setValue(config.MODULE_W)
        self.module_w_spin.setDecimals(2)
        self.module_w_spin.setToolTip("模块矩形的宽度 (0.5-3.0)")
        self.module_w_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.module_w_spin)
        size_layout.addLayout(row)

        # 模块高度
        row = QHBoxLayout()
        row.addWidget(QLabel("模块高度:"))
        self.module_h_spin = NoWheelDoubleSpinBox()
        self.module_h_spin.setRange(0.2, 1.0)
        self.module_h_spin.setSingleStep(0.05)
        self.module_h_spin.setValue(config.MODULE_H)
        self.module_h_spin.setDecimals(2)
        self.module_h_spin.setToolTip("模块矩形的高度 (0.2-1.0)")
        self.module_h_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.module_h_spin)
        size_layout.addLayout(row)

        # 列间距
        row = QHBoxLayout()
        row.addWidget(QLabel("列间距:"))
        self.col_gap_spin = NoWheelDoubleSpinBox()
        self.col_gap_spin.setRange(0.05, 1.0)
        self.col_gap_spin.setSingleStep(0.05)
        self.col_gap_spin.setValue(config.COL_GAP)
        self.col_gap_spin.setDecimals(2)
        self.col_gap_spin.setToolTip("列与列之间的间距 (0.05-1.0)")
        self.col_gap_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.col_gap_spin)
        size_layout.addLayout(row)

        # 行间距
        row = QHBoxLayout()
        row.addWidget(QLabel("行间距:"))
        self.row_gap_spin = NoWheelDoubleSpinBox()
        self.row_gap_spin.setRange(0.05, 1.0)
        self.row_gap_spin.setSingleStep(0.05)
        self.row_gap_spin.setValue(config.ROW_GAP)
        self.row_gap_spin.setDecimals(2)
        self.row_gap_spin.setToolTip("行与行之间的间距 (0.05-1.0)")
        self.row_gap_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.row_gap_spin)
        size_layout.addLayout(row)

        layout.addWidget(size_group)

        # ========== 字体参数组 ==========
        font_group = QGroupBox("字体设置")
        font_layout = QVBoxLayout(font_group)

        # 模块字号
        row = QHBoxLayout()
        row.addWidget(QLabel("模块字号:"))
        self.module_font_spin = NoWheelSpinBox()
        self.module_font_spin.setRange(8, 24)
        self.module_font_spin.setValue(config.MODULE_FONT_SIZE)
        self.module_font_spin.setToolTip("模块名称的字体大小 (8-24px)")
        self.module_font_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.module_font_spin)
        font_layout.addLayout(row)

        # 标题字号
        row = QHBoxLayout()
        row.addWidget(QLabel("标题字号:"))
        self.header_font_spin = NoWheelSpinBox()
        self.header_font_spin.setRange(10, 32)
        self.header_font_spin.setValue(config.GROUP_HEADER_FONT_SIZE)
        self.header_font_spin.setToolTip("应用组标题的字体大小 (10-32px)")
        self.header_font_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.header_font_spin)
        font_layout.addLayout(row)

        layout.addWidget(font_group)

        # ========== 布局参数组 ==========
        layout_group = QGroupBox("布局设置")
        layout_layout = QVBoxLayout(layout_group)

        # 启用MPR平衡
        self.adjust_mpr_check = QCheckBox("启用MPR平衡调整")
        self.adjust_mpr_check.setChecked(config.ADJUST_MPR)
        self.adjust_mpr_check.setToolTip("自动平衡各列的高度，使布局更均匀")
        self.adjust_mpr_check.stateChanged.connect(self._on_params_changed)
        layout_layout.addWidget(self.adjust_mpr_check)

        # 目标宽高比
        row = QHBoxLayout()
        row.addWidget(QLabel("目标宽高比:"))
        self.target_ratio_spin = NoWheelDoubleSpinBox()
        self.target_ratio_spin.setRange(1.0, 2.5)
        self.target_ratio_spin.setSingleStep(0.1)
        self.target_ratio_spin.setDecimals(2)
        self.target_ratio_spin.setValue(config.TARGET_RATIO)
        self.target_ratio_spin.setToolTip("整体布局的目标宽高比 (1.0-2.5)")
        self.target_ratio_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.target_ratio_spin)
        layout_layout.addLayout(row)

        layout.addWidget(layout_group)

        # ========== 分隔线 ==========
        from PySide6.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # ========== 重置按钮 ==========
        reset_btn = QPushButton("重置为默认值")
        reset_btn.setToolTip("将所有参数恢复为默认值")
        reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(reset_btn)

        # ========== 模板管理按钮 ==========
        template_layout = QHBoxLayout()

        self.load_template_btn = QPushButton("加载模板")
        self.load_template_btn.setToolTip("从模板加载参数配置")
        self.load_template_btn.clicked.connect(self._on_load_template)
        template_layout.addWidget(self.load_template_btn)

        self.save_template_btn = QPushButton("保存模板")
        self.save_template_btn.setToolTip("将当前参数保存为模板")
        self.save_template_btn.clicked.connect(self._on_save_template)
        template_layout.addWidget(self.save_template_btn)

        layout.addLayout(template_layout)

        layout.addStretch()

        scroll_area.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _on_params_changed(self):
        """参数改变时触发"""
        self.params_changed.emit(self.get_params())

    def get_params(self) -> dict:
        """获取当前所有参数"""
        return {
            'GROUP_BG': self.group_bg_color.get_color(),
            'GROUP_HEADER_COLOR': self.group_header_color.get_color(),
            'MODULE_BG_COLOR': self.module_bg_color.get_color(),
            'MODULE_W': self.module_w_spin.value(),
            'MODULE_H': self.module_h_spin.value(),
            'COL_GAP': self.col_gap_spin.value(),
            'ROW_GAP': self.row_gap_spin.value(),
            'MODULE_FONT_SIZE': self.module_font_spin.value(),
            'GROUP_HEADER_FONT_SIZE': self.header_font_spin.value(),
            'ADJUST_MPR': self.adjust_mpr_check.isChecked(),
            'TARGET_RATIO': self.target_ratio_spin.value(),
        }

    def set_params(self, params: dict):
        """设置参数"""
        if 'GROUP_BG' in params:
            self.group_bg_color.set_color(params['GROUP_BG'])
        if 'GROUP_HEADER_COLOR' in params:
            self.group_header_color.set_color(params['GROUP_HEADER_COLOR'])
        if 'MODULE_BG_COLOR' in params:
            self.module_bg_color.set_color(params['MODULE_BG_COLOR'])
        if 'MODULE_W' in params:
            self.module_w_spin.setValue(params['MODULE_W'])
        if 'MODULE_H' in params:
            self.module_h_spin.setValue(params['MODULE_H'])
        if 'COL_GAP' in params:
            self.col_gap_spin.setValue(params['COL_GAP'])
        if 'ROW_GAP' in params:
            self.row_gap_spin.setValue(params['ROW_GAP'])
        if 'MODULE_FONT_SIZE' in params:
            self.module_font_spin.setValue(params['MODULE_FONT_SIZE'])
        if 'GROUP_HEADER_FONT_SIZE' in params:
            self.header_font_spin.setValue(params['GROUP_HEADER_FONT_SIZE'])
        if 'ADJUST_MPR' in params:
            self.adjust_mpr_check.setChecked(params['ADJUST_MPR'])
        if 'TARGET_RATIO' in params:
            self.target_ratio_spin.setValue(params['TARGET_RATIO'])

    def _on_reset(self):
        """重置为默认值"""
        self.set_params({
            'GROUP_BG': config.GROUP_BG,
            'GROUP_HEADER_COLOR': config.GROUP_HEADER_COLOR,
            'MODULE_BG_COLOR': config.MODULE_BG_COLOR,
            'MODULE_W': config.MODULE_W,
            'MODULE_H': config.MODULE_H,
            'COL_GAP': config.COL_GAP,
            'ROW_GAP': config.ROW_GAP,
            'MODULE_FONT_SIZE': config.MODULE_FONT_SIZE,
            'GROUP_HEADER_FONT_SIZE': config.GROUP_HEADER_FONT_SIZE,
            'ADJUST_MPR': config.ADJUST_MPR,
            'TARGET_RATIO': config.TARGET_RATIO,
        })

    def _on_load_template(self):
        """加载模板"""
        dialog = TemplateDialog(self, mode="load")
        if dialog.exec() == QDialog.Accepted:
            template = dialog.get_selected_template()
            if template and "params" in template:
                self.set_params(template["params"])
                self._on_params_changed()

    def _on_save_template(self):
        """保存模板"""
        dialog = TemplateDialog(self, mode="save")
        if dialog.exec() == QDialog.Accepted:
            template_info = dialog.get_selected_template()
            if template_info:
                params = self.get_params()
                if self._template_manager.save_template(
                    template_info["name"],
                    params,
                    template_info.get("description", "")
                ):
                    QMessageBox.information(self, "成功", "模板保存成功")
                else:
                    QMessageBox.warning(self, "错误", "模板保存失败")
