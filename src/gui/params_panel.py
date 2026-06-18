# -*- coding: utf-8 -*-
"""
参数调整面板

提供布局参数、颜色、字体等的调整功能。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,
    QColorDialog, QPushButton, QMessageBox, QDialog,
    QComboBox, QSizePolicy, QLineEdit
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


class NoWheelComboBox(QComboBox):
    """禁用滚轮事件的QComboBox"""

    def wheelEvent(self, event: QWheelEvent):
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
    # 信号：单模块调色 (module_name, color)
    module_color_applied = Signal(str, str)
    # 信号：批量模块调色 ([module_names], color)
    batch_module_color_applied = Signal(list, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._template_manager = TemplateManager()
        self._current_modules = {}  # {group_name: [module_name, ...]}
        self._setup_ui()

    def _setup_ui(self):
        """设置UI布局"""
        # 直接布局，由外层 CollapsibleSection 统一管理滚动
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 让面板可以被拉伸
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # ========== 颜色参数组 ==========
        color_group = QGroupBox("颜色设置")
        color_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        color_layout = QVBoxLayout(color_group)

        # 组背景色
        row = QHBoxLayout()
        lbl = QLabel("组背景色:")
        lbl.setFixedWidth(85)
        row.addWidget(lbl)
        self.group_bg_color = ColorButton(config.GROUP_BG)
        self.group_bg_color.setToolTip("应用组的背景颜色")
        self.group_bg_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.group_bg_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 组标题色
        row = QHBoxLayout()
        lbl = QLabel("组标题色:")
        lbl.setFixedWidth(85)
        row.addWidget(lbl)
        self.group_header_color = ColorButton(config.GROUP_HEADER_COLOR)
        self.group_header_color.setToolTip("应用组标题栏的颜色")
        self.group_header_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.group_header_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 模块背景色
        row = QHBoxLayout()
        lbl = QLabel("模块背景色:")
        lbl.setFixedWidth(85)
        row.addWidget(lbl)
        self.module_bg_color = ColorButton(config.MODULE_BG_COLOR)
        self.module_bg_color.setToolTip("应用模块的背景颜色")
        self.module_bg_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.module_bg_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 域背景色
        row = QHBoxLayout()
        lbl = QLabel("域背景色:")
        lbl.setFixedWidth(85)
        row.addWidget(lbl)
        self.domain_bg_color = ColorButton(config.DOMAIN_BG)
        self.domain_bg_color.setToolTip("域外框的背景颜色")
        self.domain_bg_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.domain_bg_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 域边框色
        row = QHBoxLayout()
        lbl = QLabel("域边框色:")
        lbl.setFixedWidth(85)
        row.addWidget(lbl)
        self.domain_border_color = ColorButton(config.DOMAIN_BORDER_COLOR)
        self.domain_border_color.setToolTip("域外框的边框颜色")
        self.domain_border_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.domain_border_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 域标题色
        row = QHBoxLayout()
        lbl = QLabel("域标题色:")
        lbl.setFixedWidth(85)
        row.addWidget(lbl)
        self.domain_title_color = ColorButton(config.DOMAIN_TITLE_COLOR)
        self.domain_title_color.setToolTip("域标题的文字颜色")
        self.domain_title_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.domain_title_color)
        row.addStretch()
        color_layout.addLayout(row)

        # 模块边框色
        row = QHBoxLayout()
        lbl = QLabel("模块边框色:")
        lbl.setFixedWidth(85)
        row.addWidget(lbl)
        self.module_border_color = ColorButton(config.MODULE_BORDER_COLOR)
        self.module_border_color.setToolTip("模块格子的边框颜色")
        self.module_border_color.color_changed.connect(self._on_params_changed)
        row.addWidget(self.module_border_color)
        row.addStretch()
        color_layout.addLayout(row)

        layout.addWidget(color_group)

        # ========== 尺寸参数组 ==========
        size_group = QGroupBox("尺寸设置")
        size_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        size_layout = QVBoxLayout(size_group)

        # 模块宽度 — 暂时隐藏（布局算法尚未适配运行时调整）
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
        _mw_container = QWidget()
        _mw_container.setLayout(row)
        _mw_container.setVisible(False)
        size_layout.addWidget(_mw_container)

        # 模块高度 — 暂时隐藏（布局算法尚未适配运行时调整）
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
        _mh_container = QWidget()
        _mh_container.setLayout(row)
        _mh_container.setVisible(False)
        size_layout.addWidget(_mh_container)

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

        # ========== 间距参数组 ==========
        spacing_group = QGroupBox("间距设置")
        spacing_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        spacing_layout = QVBoxLayout(spacing_group)

        # 域内边距
        row = QHBoxLayout()
        row.addWidget(QLabel("域内边距:"))
        self.domain_padding_spin = NoWheelSpinBox()
        self.domain_padding_spin.setRange(4, 32)
        self.domain_padding_spin.setValue(config.DOMAIN_PADDING_Y)
        self.domain_padding_spin.setToolTip("域外框的内边距 (4-32px)")
        self.domain_padding_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.domain_padding_spin)
        spacing_layout.addLayout(row)

        # 列内组间距
        row = QHBoxLayout()
        row.addWidget(QLabel("列内组间距:"))
        self.column_gap_spin = NoWheelDoubleSpinBox()
        self.column_gap_spin.setRange(2, 16)
        self.column_gap_spin.setSingleStep(1)
        self.column_gap_spin.setValue(config.COLUMN_GAP)
        self.column_gap_spin.setDecimals(0)
        self.column_gap_spin.setToolTip("同一列内组与组之间的间距 (2-16px)")
        self.column_gap_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.column_gap_spin)
        spacing_layout.addLayout(row)

        # 标题下方间距
        row = QHBoxLayout()
        row.addWidget(QLabel("标题下方间距:"))
        self.title_margin_spin = NoWheelDoubleSpinBox()
        self.title_margin_spin.setRange(2, 16)
        self.title_margin_spin.setSingleStep(1)
        self.title_margin_spin.setValue(config.DOMAIN_TITLE_MARGIN_BOTTOM)
        self.title_margin_spin.setDecimals(0)
        self.title_margin_spin.setToolTip("域标题与内容之间的间距 (2-16px)")
        self.title_margin_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.title_margin_spin)
        spacing_layout.addLayout(row)

        layout.addWidget(spacing_group)

        # ========== 圆角参数组 ==========
        radius_group = QGroupBox("圆角设置")
        radius_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        radius_layout = QVBoxLayout(radius_group)

        # 域外框圆角
        row = QHBoxLayout()
        row.addWidget(QLabel("域外框圆角:"))
        self.domain_radius_spin = NoWheelSpinBox()
        self.domain_radius_spin.setRange(0, 24)
        self.domain_radius_spin.setValue(config.DOMAIN_BORDER_RADIUS)
        self.domain_radius_spin.setToolTip("域外框的圆角半径 (0-24px)")
        self.domain_radius_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.domain_radius_spin)
        radius_layout.addLayout(row)

        # 组圆角
        row = QHBoxLayout()
        row.addWidget(QLabel("组圆角:"))
        self.group_radius_spin = NoWheelSpinBox()
        self.group_radius_spin.setRange(0, 16)
        self.group_radius_spin.setValue(config.GROUP_BORDER_RADIUS)
        self.group_radius_spin.setToolTip("应用组的圆角半径 (0-16px)")
        self.group_radius_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.group_radius_spin)
        radius_layout.addLayout(row)

        # 模块圆角
        row = QHBoxLayout()
        row.addWidget(QLabel("模块圆角:"))
        self.module_radius_spin = NoWheelSpinBox()
        self.module_radius_spin.setRange(0, 12)
        self.module_radius_spin.setValue(config.MODULE_BORDER_RADIUS)
        self.module_radius_spin.setToolTip("模块格子的圆角半径 (0-12px)")
        self.module_radius_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.module_radius_spin)
        radius_layout.addLayout(row)

        layout.addWidget(radius_group)

        # ========== 边框参数组 ==========
        border_group = QGroupBox("边框设置")
        border_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        border_layout = QVBoxLayout(border_group)

        # 域边框宽度
        row = QHBoxLayout()
        row.addWidget(QLabel("域边框宽度:"))
        self.domain_border_width_spin = NoWheelSpinBox()
        self.domain_border_width_spin.setRange(0, 6)
        self.domain_border_width_spin.setValue(config.DOMAIN_BORDER_WIDTH)
        self.domain_border_width_spin.setToolTip("域外框的边框宽度 (0-6px)")
        self.domain_border_width_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.domain_border_width_spin)
        border_layout.addLayout(row)

        layout.addWidget(border_group)

        # ========== 字体参数组 ==========
        font_group = QGroupBox("字体设置")
        font_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
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

        # 域标题字号
        row = QHBoxLayout()
        row.addWidget(QLabel("域标题字号:"))
        self.domain_title_font_spin = NoWheelSpinBox()
        self.domain_title_font_spin.setRange(14, 36)
        self.domain_title_font_spin.setValue(config.DOMAIN_TITLE_FONT_SIZE)
        self.domain_title_font_spin.setToolTip("域标题的字体大小 (14-36px)")
        self.domain_title_font_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.domain_title_font_spin)
        font_layout.addLayout(row)

        # 模块字体族 — 暂时隐藏
        row = QHBoxLayout()
        row.addWidget(QLabel("模块字体:"))
        self.font_family_combo = NoWheelComboBox()
        self.font_family_combo.addItems([
            "Microsoft YaHei",
            "SimSun",
            "SimHei",
            "Arial",
            "Segoe UI",
            "Helvetica",
        ])
        self.font_family_combo.setToolTip("模块文字的字体")
        self.font_family_combo.currentTextChanged.connect(self._on_params_changed)
        row.addWidget(self.font_family_combo)
        _ff_container = QWidget()
        _ff_container.setLayout(row)
        _ff_container.setVisible(False)
        font_layout.addWidget(_ff_container)

        # 模块行高 — 暂时隐藏
        row = QHBoxLayout()
        row.addWidget(QLabel("模块行高:"))
        self.module_line_height_spin = NoWheelDoubleSpinBox()
        self.module_line_height_spin.setRange(1.0, 2.0)
        self.module_line_height_spin.setSingleStep(0.1)
        self.module_line_height_spin.setValue(config.MODULE_LINE_HEIGHT)
        self.module_line_height_spin.setDecimals(1)
        self.module_line_height_spin.setToolTip("模块文字的行高倍数 (1.0-2.0)")
        self.module_line_height_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.module_line_height_spin)
        _lh_container = QWidget()
        _lh_container.setLayout(row)
        _lh_container.setVisible(False)
        font_layout.addWidget(_lh_container)

        layout.addWidget(font_group)

        # ========== 布局参数组 ==========
        layout_group = QGroupBox("布局设置")
        layout_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout_layout = QVBoxLayout(layout_group)

        # 启用MPR平衡 — 暂时隐藏
        self.adjust_mpr_check = QCheckBox("启用MPR平衡调整")
        self.adjust_mpr_check.setChecked(config.ADJUST_MPR)
        self.adjust_mpr_check.setToolTip("自动平衡各列的高度，使布局更均匀")
        self.adjust_mpr_check.stateChanged.connect(self._on_params_changed)
        _mpr_container = QWidget()
        _mpr_layout = QHBoxLayout(_mpr_container)
        _mpr_layout.setContentsMargins(0, 0, 0, 0)
        _mpr_layout.addWidget(self.adjust_mpr_check)
        _mpr_container.setVisible(False)
        layout_layout.addWidget(_mpr_container)

        # 目标宽高比 — 暂时隐藏
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
        _ratio_container = QWidget()
        _ratio_container.setLayout(row)
        _ratio_container.setVisible(False)
        layout_layout.addWidget(_ratio_container)

        # 画布高度（Marp frontmatter）
        row = QHBoxLayout()
        row.addWidget(QLabel("画布高度:"))
        self.slide_height_spin = NoWheelSpinBox()
        self.slide_height_spin.setRange(400, 720)
        self.slide_height_spin.setSingleStep(10)
        self.slide_height_spin.setValue(config.SLIDE_HEIGHT_PX)
        self.slide_height_spin.setToolTip("Marp 幻灯片高度 (400-720px)，调整后不影响模块缩放。\n注意：最大720px，超过会导致内容被截断")
        self.slide_height_spin.valueChanged.connect(self._on_params_changed)
        row.addWidget(self.slide_height_spin)
        row.addWidget(QLabel("px"))
        layout_layout.addLayout(row)

        layout.addWidget(layout_group)

        # ========== 单模块调色 ==========
        module_color_group = QGroupBox("单模块调色")
        mc_layout = QHBoxLayout(module_color_group)
        mc_layout.setContentsMargins(4, 4, 4, 4)

        mc_layout.addWidget(QLabel("模块名:"))
        self.module_name_input = QLineEdit()
        self.module_name_input.setPlaceholderText("输入模块名称")
        self.module_name_input.setFixedWidth(120)
        mc_layout.addWidget(self.module_name_input)

        self.module_color_btn = ColorButton('#C4D8FC')
        self.module_color_btn.setToolTip("选择要应用的颜色")
        mc_layout.addWidget(self.module_color_btn)

        self.apply_module_color_btn = QPushButton("应用")
        self.apply_module_color_btn.setToolTip("为指定模块设置颜色")
        self.apply_module_color_btn.clicked.connect(self._on_apply_module_color)
        mc_layout.addWidget(self.apply_module_color_btn)

        layout.addWidget(module_color_group)

        # ========== 批量模块调色 ==========
        self.batch_color_btn = QPushButton("批量调色")
        self.batch_color_btn.setToolTip("打开批量调色窗口，多选模块一起调色")
        self.batch_color_btn.clicked.connect(self._on_batch_color)
        layout.addWidget(self.batch_color_btn)

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

    def _on_params_changed(self):
        """参数改变时触发"""
        self.params_changed.emit(self.get_params())

    def _on_apply_module_color(self):
        """应用单模块颜色"""
        name = self.module_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入模块名称")
            return
        color = self.module_color_btn.get_color()
        self.module_color_applied.emit(name, color)

    def set_current_modules(self, modules: dict):
        """设置当前文件的模块数据，供批量调色使用

        Args:
            modules: {group_name: [module_name, ...]}
        """
        self._current_modules = modules

    def _on_batch_color(self):
        """打开批量调色对话框"""
        if not self._current_modules:
            QMessageBox.warning(self, "提示", "请先选择一个已生成的文件")
            return

        from .module_color_dialog import ModuleColorDialog
        dialog = ModuleColorDialog(self._current_modules, parent=self)
        dialog.colors_applied.connect(self.batch_module_color_applied.emit)
        dialog.exec()

    def get_params(self) -> dict:
        """获取当前所有参数"""
        # 获取字体族（需要加上引号和 sans-serif 后缀）
        font_family_raw = self.font_family_combo.currentText()
        font_family = f'"{font_family_raw}", sans-serif'

        return {
            # 颜色
            'GROUP_BG': self.group_bg_color.get_color(),
            'GROUP_HEADER_COLOR': self.group_header_color.get_color(),
            'MODULE_BG_COLOR': self.module_bg_color.get_color(),
            'DOMAIN_BG': self.domain_bg_color.get_color(),
            'DOMAIN_BORDER_COLOR': self.domain_border_color.get_color(),
            'DOMAIN_TITLE_COLOR': self.domain_title_color.get_color(),
            'MODULE_BORDER_COLOR': self.module_border_color.get_color(),
            # 尺寸
            'MODULE_W': self.module_w_spin.value(),
            'MODULE_H': self.module_h_spin.value(),
            'COL_GAP': self.col_gap_spin.value(),
            'ROW_GAP': self.row_gap_spin.value(),
            # 字体
            'MODULE_FONT_SIZE': self.module_font_spin.value(),
            'GROUP_HEADER_FONT_SIZE': self.header_font_spin.value(),
            'DOMAIN_TITLE_FONT_SIZE': self.domain_title_font_spin.value(),
            'MODULE_FONT_FAMILY': font_family,
            'MODULE_LINE_HEIGHT': self.module_line_height_spin.value(),
            # 间距
            'DOMAIN_PADDING': self.domain_padding_spin.value(),
            'COLUMN_GAP': self.column_gap_spin.value(),
            'GROUP_HEADER_MARGIN_BOTTOM': self.title_margin_spin.value(),
            # 圆角
            'DOMAIN_BORDER_RADIUS': self.domain_radius_spin.value(),
            'GROUP_BORDER_RADIUS': self.group_radius_spin.value(),
            'MODULE_BORDER_RADIUS': self.module_radius_spin.value(),
            # 边框
            'DOMAIN_BORDER_WIDTH': self.domain_border_width_spin.value(),
            # 布局
            'ADJUST_MPR': self.adjust_mpr_check.isChecked(),
            'TARGET_RATIO': self.target_ratio_spin.value(),
            'SLIDE_HEIGHT_PX': self.slide_height_spin.value(),
        }

    def set_params(self, params: dict):
        """设置参数"""
        # 颜色
        if 'GROUP_BG' in params:
            self.group_bg_color.set_color(params['GROUP_BG'])
        if 'GROUP_HEADER_COLOR' in params:
            self.group_header_color.set_color(params['GROUP_HEADER_COLOR'])
        if 'MODULE_BG_COLOR' in params:
            self.module_bg_color.set_color(params['MODULE_BG_COLOR'])
        if 'DOMAIN_BG' in params:
            self.domain_bg_color.set_color(params['DOMAIN_BG'])
        if 'DOMAIN_BORDER_COLOR' in params:
            self.domain_border_color.set_color(params['DOMAIN_BORDER_COLOR'])
        if 'DOMAIN_TITLE_COLOR' in params:
            self.domain_title_color.set_color(params['DOMAIN_TITLE_COLOR'])
        if 'MODULE_BORDER_COLOR' in params:
            self.module_border_color.set_color(params['MODULE_BORDER_COLOR'])
        # 尺寸
        if 'MODULE_W' in params:
            self.module_w_spin.setValue(params['MODULE_W'])
        if 'MODULE_H' in params:
            self.module_h_spin.setValue(params['MODULE_H'])
        if 'COL_GAP' in params:
            self.col_gap_spin.setValue(params['COL_GAP'])
        if 'ROW_GAP' in params:
            self.row_gap_spin.setValue(params['ROW_GAP'])
        # 字体
        if 'MODULE_FONT_SIZE' in params:
            self.module_font_spin.setValue(params['MODULE_FONT_SIZE'])
        if 'GROUP_HEADER_FONT_SIZE' in params:
            self.header_font_spin.setValue(params['GROUP_HEADER_FONT_SIZE'])
        if 'DOMAIN_TITLE_FONT_SIZE' in params:
            self.domain_title_font_spin.setValue(params['DOMAIN_TITLE_FONT_SIZE'])
        if 'MODULE_FONT_FAMILY' in params:
            # 从 "FontName", sans-serif 中提取字体名
            raw = params['MODULE_FONT_FAMILY']
            font_name = raw.split('"')[1] if '"' in raw else raw
            idx = self.font_family_combo.findText(font_name)
            if idx >= 0:
                self.font_family_combo.setCurrentIndex(idx)
        if 'MODULE_LINE_HEIGHT' in params:
            self.module_line_height_spin.setValue(params['MODULE_LINE_HEIGHT'])
        # 间距
        if 'DOMAIN_PADDING' in params:
            self.domain_padding_spin.setValue(params['DOMAIN_PADDING'])
        if 'COLUMN_GAP' in params:
            self.column_gap_spin.setValue(params['COLUMN_GAP'])
        if 'GROUP_HEADER_MARGIN_BOTTOM' in params:
            self.title_margin_spin.setValue(params['GROUP_HEADER_MARGIN_BOTTOM'])
        # 圆角
        if 'DOMAIN_BORDER_RADIUS' in params:
            self.domain_radius_spin.setValue(params['DOMAIN_BORDER_RADIUS'])
        if 'GROUP_BORDER_RADIUS' in params:
            self.group_radius_spin.setValue(params['GROUP_BORDER_RADIUS'])
        if 'MODULE_BORDER_RADIUS' in params:
            self.module_radius_spin.setValue(params['MODULE_BORDER_RADIUS'])
        # 边框
        if 'DOMAIN_BORDER_WIDTH' in params:
            self.domain_border_width_spin.setValue(params['DOMAIN_BORDER_WIDTH'])
        # 布局
        if 'ADJUST_MPR' in params:
            self.adjust_mpr_check.setChecked(params['ADJUST_MPR'])
        if 'TARGET_RATIO' in params:
            self.target_ratio_spin.setValue(params['TARGET_RATIO'])
        if 'SLIDE_HEIGHT_PX' in params:
            self.slide_height_spin.setValue(params['SLIDE_HEIGHT_PX'])

    def _on_reset(self):
        """重置为默认值"""
        self.set_params({
            'GROUP_BG': config.GROUP_BG,
            'GROUP_HEADER_COLOR': config.GROUP_HEADER_COLOR,
            'MODULE_BG_COLOR': config.MODULE_BG_COLOR,
            'DOMAIN_BG': config.DOMAIN_BG,
            'DOMAIN_BORDER_COLOR': config.DOMAIN_BORDER_COLOR,
            'DOMAIN_TITLE_COLOR': config.DOMAIN_TITLE_COLOR,
            'MODULE_BORDER_COLOR': config.MODULE_BORDER_COLOR,
            'MODULE_W': config.MODULE_W,
            'MODULE_H': config.MODULE_H,
            'COL_GAP': config.COL_GAP,
            'ROW_GAP': config.ROW_GAP,
            'MODULE_FONT_SIZE': config.MODULE_FONT_SIZE,
            'GROUP_HEADER_FONT_SIZE': config.GROUP_HEADER_FONT_SIZE,
            'DOMAIN_TITLE_FONT_SIZE': config.DOMAIN_TITLE_FONT_SIZE,
            'MODULE_FONT_FAMILY': config.FONT_FAMILY,
            'MODULE_LINE_HEIGHT': config.MODULE_LINE_HEIGHT,
            'DOMAIN_PADDING': config.DOMAIN_PADDING_Y,
            'COLUMN_GAP': config.COLUMN_GAP,
            'GROUP_HEADER_MARGIN_BOTTOM': config.DOMAIN_TITLE_MARGIN_BOTTOM,
            'DOMAIN_BORDER_RADIUS': config.DOMAIN_BORDER_RADIUS,
            'GROUP_BORDER_RADIUS': config.GROUP_BORDER_RADIUS,
            'MODULE_BORDER_RADIUS': config.MODULE_BORDER_RADIUS,
            'DOMAIN_BORDER_WIDTH': config.DOMAIN_BORDER_WIDTH,
            'ADJUST_MPR': config.ADJUST_MPR,
            'TARGET_RATIO': config.TARGET_RATIO,
            'SLIDE_HEIGHT_PX': config.SLIDE_HEIGHT_PX,
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
