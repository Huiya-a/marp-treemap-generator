# -*- coding: utf-8 -*-
"""
主窗口模块

提供应用的主窗口界面。
"""

import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSplitter, QTextEdit, QLabel,
    QProgressBar, QMessageBox, QStatusBar, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QShortcut, QKeySequence

# 导入自定义组件
from .file_selector import FileSelector
from .preview_widget import PreviewWidget
from .params_panel import ParamsPanel
from .file_info_widget import FileInfoWidget
from .collapsible_section import CollapsibleSection

# 导入项目模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from src import config
from src.data_loader import load_data_from_excel
from src.gui.md_editor import extract_params_from_md, apply_params_to_md, _sub_in_css_blocks, apply_module_color

# ========== 调试开关 ==========
DEBUG_MODULE_COLOR = True  # 改为 True 开启模块调色调试日志
# =============================


class GenerateWorker(QThread):
    """生成工作线程"""

    # 信号
    progress = Signal(int, str)  # 进度百分比, 消息
    finished = Signal(bool, str)  # 是否成功, 消息或文件路径
    log = Signal(str)  # 日志消息
    file_generated = Signal(str, str)  # 单个文件生成完成，传递(md路径, png路径)
    file_status = Signal(int, str, str)  # 文件状态更新 (索引, 状态, 消息)

    def __init__(self, files: list, output_dir: str, params: dict, export_format: str = 'png',
                 session_processed: set = None):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.params = params
        self.export_format = export_format
        self._is_cancelled = False
        self._generated_md_files = []
        self._original_params = {}
        self._session_processed = session_processed if session_processed is not None else set()
        self._excel_to_md = {}

    def run(self):
        """执行生成任务"""
        try:
            total = len(self.files)
            success_count = 0
            generated_files = []

            for i, file_path in enumerate(self.files):
                if self._is_cancelled:
                    self.log.emit("用户取消了操作")
                    self.finished.emit(False, "操作已取消")
                    return

                self.progress.emit(int(i / total * 100), f"处理中 ({i+1}/{total}): {os.path.basename(file_path)}")
                self.file_status.emit(i, "processing", "处理中...")
                self.log.emit(f"[{i+1}/{total}] 处理文件: {file_path}")

                try:
                    # 加载数据
                    domain_name, data = load_data_from_excel(file_path)
                    self.log.emit(f"  域名称: {domain_name}")
                    self.log.emit(f"  应用组数: {len(data)}")
                    self.log.emit(f"  模块总数: {sum(len(m) for m in data.values())}")

                    # 生成输出文件名
                    safe_domain = domain_name.replace(' ', '_').replace('/', '_')
                    output_path = os.path.join(self.output_dir, f"{safe_domain}.md")

                    # 会话级复用：本次打开后首次处理该文件则生成，否则复用
                    if file_path not in self._session_processed:
                        self.log.emit("  首次生成 Markdown...")
                        from generate_treemap_md import generate_marp_md
                        generate_marp_md(domain_name, data, output_path, proportional_width=None)
                        self._session_processed.add(file_path)
                    else:
                        self.log.emit(f"  复用已有 Markdown: {output_path}")

                    # 保存原始参数（config 默认值）
                    self._original_params[output_path] = {
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
                        }

                    self.log.emit(f"  Markdown生成成功: {output_path}")
                    self._generated_md_files.append(output_path)
                    self._excel_to_md[file_path] = output_path

                    # 根据导出格式生成文件
                    png_path = ""
                    pptx_path = ""
                    html_path = ""

                    if self.export_format in ['png', 'both', 'png_html', 'all']:
                        png_path = self._generate_png(output_path)
                        if png_path:
                            self.log.emit(f"  PNG生成成功: {png_path}")
                            generated_files.append(png_path)
                        else:
                            self.log.emit(f"  PNG生成失败（可能未安装MarP CLI）")

                    if self.export_format in ['pptx', 'both', 'all']:
                        pptx_path = self._generate_pptx(output_path)
                        if pptx_path:
                            self.log.emit(f"  PPTX生成成功: {pptx_path}")
                            generated_files.append(pptx_path)
                        else:
                            self.log.emit(f"  PPTX生成失败（可能未安装MarP CLI）")

                    if self.export_format in ['html', 'png_html', 'all']:
                        html_path = self._generate_html(output_path)
                        if html_path:
                            self.log.emit(f"  HTML生成成功: {html_path}")
                            generated_files.append(html_path)
                        else:
                            self.log.emit(f"  HTML生成失败（可能未安装MarP CLI）")

                    success_count += 1
                    self.file_generated.emit(output_path, png_path)
                    self.file_status.emit(i, "completed", "完成")

                except Exception as e:
                    self.log.emit(f"  生成失败: {str(e)}")
                    import traceback
                    self.log.emit(f"  错误详情: {traceback.format_exc()}")
                    self.file_status.emit(i, "failed", f"失败: {str(e)}")

            self.progress.emit(100, "完成")
            self.finished.emit(True, f"成功生成 {success_count}/{total} 个文件")

        except Exception as e:
            self.log.emit(f"发生错误: {str(e)}")
            self.finished.emit(False, f"发生错误: {str(e)}")

    def get_generated_md_files(self) -> list:
        """获取生成的MD文件路径列表"""
        return self._generated_md_files.copy()

    def get_original_params(self) -> dict:
        """获取每个文件的原始参数"""
        return self._original_params.copy()

    def get_excel_to_md(self) -> dict:
        """获取 excel_path -> md_path 映射"""
        return self._excel_to_md.copy()

    def _generate_png(self, md_path: str) -> str:
        """调用MarP CLI生成PNG图片"""
        try:
            png_path = md_path.replace('.md', '.png')
            cmd = ['marp', md_path, '--images', 'png', '--allow-local-files', '-o', png_path]
            self.log.emit(f"  执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
                shell=True, encoding='utf-8', errors='ignore'
            )

            if result.returncode == 0:
                if os.path.exists(png_path):
                    return png_path
                md_dir = os.path.dirname(md_path)
                base_name = os.path.splitext(os.path.basename(md_path))[0]
                for f in os.listdir(md_dir):
                    if f.startswith(base_name) and f.endswith('.png'):
                        return os.path.join(md_dir, f)
                dir_path = os.path.splitext(md_path)[0]
                if os.path.isdir(dir_path):
                    for f in os.listdir(dir_path):
                        if f.endswith('.png'):
                            return os.path.join(dir_path, f)
                return png_path
            else:
                self.log.emit(f"  MarP CLI错误: {result.stderr}")
                return ""
        except FileNotFoundError:
            self.log.emit("  未找到MarP CLI，请先安装: npm install -g @marp-team/marp-cli")
            return ""
        except subprocess.TimeoutExpired:
            self.log.emit("  MarP CLI执行超时")
            return ""
        except Exception as e:
            self.log.emit(f"  调用MarP CLI失败: {str(e)}")
            return ""

    def _generate_pptx(self, md_path: str) -> str:
        """调用MarP CLI生成PPTX文件"""
        try:
            pptx_path = md_path.replace('.md', '.pptx')
            cmd = ['marp', md_path, '--pptx', '--allow-local-files', '-o', pptx_path]
            self.log.emit(f"  执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
                shell=True, encoding='utf-8', errors='ignore'
            )

            if result.returncode == 0:
                if os.path.exists(pptx_path):
                    return pptx_path
                md_dir = os.path.dirname(md_path)
                base_name = os.path.splitext(os.path.basename(md_path))[0]
                for f in os.listdir(md_dir):
                    if f.startswith(base_name) and f.endswith('.pptx'):
                        return os.path.join(md_dir, f)
                return pptx_path
            else:
                self.log.emit(f"  MarP CLI错误: {result.stderr}")
                return ""
        except FileNotFoundError:
            self.log.emit("  未找到MarP CLI，请先安装: npm install -g @marp-team/marp-cli")
            return ""
        except subprocess.TimeoutExpired:
            self.log.emit("  MarP CLI执行超时")
            return ""
        except Exception as e:
            self.log.emit(f"  调用MarP CLI失败: {str(e)}")
            return ""

    def _generate_html(self, md_path: str) -> str:
        """调用MarP CLI生成HTML文件"""
        try:
            html_path = md_path.replace('.md', '.html')
            cmd = ['marp', md_path, '--html', '--allow-local-files', '-o', html_path]
            self.log.emit(f"  执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
                shell=True, encoding='utf-8', errors='ignore'
            )

            if result.returncode == 0:
                if os.path.exists(html_path):
                    return html_path
                md_dir = os.path.dirname(md_path)
                base_name = os.path.splitext(os.path.basename(md_path))[0]
                for f in os.listdir(md_dir):
                    if f.startswith(base_name) and f.endswith('.html'):
                        return os.path.join(md_dir, f)
                return html_path
            else:
                self.log.emit(f"  MarP CLI错误: {result.stderr}")
                return ""
        except FileNotFoundError:
            self.log.emit("  未找到MarP CLI，请先安装: npm install -g @marp-team/marp-cli")
            return ""
        except subprocess.TimeoutExpired:
            self.log.emit("  MarP CLI执行超时")
            return ""
        except Exception as e:
            self.log.emit(f"  调用MarP CLI失败: {str(e)}")
            return ""

    def cancel(self):
        """取消操作"""
        self._is_cancelled = True


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._worker = None
        self._generated_md_files = {}  # {excel_path: md_path}
        self._original_params = {}  # {md_path: {param: value}}
        self._css_state = {}  # {md_path: {css_key: css_value}}
        self._initial_css = {}  # {md_path: {css_key: css_value}} — 首次生成时的 CSS 值
        self._pending_params = None
        self._session_processed = set()  # 本次会话已生成过的 Excel 文件
        self._current_excel_path = None  # 当前操作的 Excel 文件路径
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """设置UI布局"""
        # 设置窗口属性
        self.setWindowTitle("应用架构图生成器")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # ========== 左侧面板 ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # --- 三个可折叠面板，共享一个 ScrollArea ---
        self.file_selector = FileSelector()
        self.file_section = CollapsibleSection("文件选择", self.file_selector)

        self.file_info = FileInfoWidget()
        self.file_info_section = CollapsibleSection("文件信息", self.file_info)

        self.params_panel = ParamsPanel()
        self.params_section = CollapsibleSection("参数调整", self.params_panel)

        # 内容容器
        scroll_container = QWidget()

        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        scroll_layout.addWidget(self.file_section)
        scroll_layout.addWidget(self.file_info_section)
        scroll_layout.addWidget(self.params_section)
        # stretch: 文件选择=1, 文件信息=1, 参数调整=2
        scroll_layout.setStretchFactor(self.file_section, 1)
        scroll_layout.setStretchFactor(self.file_info_section, 1)
        scroll_layout.setStretchFactor(self.params_section, 2)

        # 共享 ScrollArea
        self._shared_scroll = QScrollArea()
        self._shared_scroll.setWidgetResizable(True)
        self._shared_scroll.setFrameShape(QScrollArea.NoFrame)
        self._shared_scroll.setWidget(scroll_container)
        self._shared_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_layout.addWidget(self._shared_scroll, stretch=1)

        # 面板折叠/展开时，动态调整容器约束
        self._scroll_container = scroll_container
        self.file_section.toggled.connect(self._on_section_toggled)
        self.file_info_section.toggled.connect(self._on_section_toggled)
        self.params_section.toggled.connect(self._on_section_toggled)
        self._update_scroll_resizable()

        # 应用参数按钮
        self.apply_params_btn = QPushButton("应用参数到 Markdown")
        self.apply_params_btn.setEnabled(False)
        self.apply_params_btn.setToolTip("将调整后的参数写入已生成的 Markdown 文件")
        self.apply_params_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.apply_params_btn.clicked.connect(self._on_apply_params)
        left_layout.addWidget(self.apply_params_btn)

        # 生成按钮
        self.generate_btn = QPushButton("生成架构图")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A73E8;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1557B0;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        left_layout.addWidget(self.generate_btn)

        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        left_layout.addWidget(self.cancel_btn)

        # 导出格式选择
        from PySide6.QtWidgets import QComboBox
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("导出格式:"))
        from .params_panel import NoWheelComboBox
        self.export_format_combo = NoWheelComboBox()
        self.export_format_combo.addItem("PNG图片", "png")
        self.export_format_combo.addItem("PPTX演示文稿", "pptx")
        self.export_format_combo.addItem("HTML网页", "html")
        self.export_format_combo.addItem("PNG + PPTX", "both")
        self.export_format_combo.addItem("PNG + HTML", "png_html")
        self.export_format_combo.addItem("全部格式", "all")
        self.export_format_combo.setToolTip("选择生成的文件格式")
        format_layout.addWidget(self.export_format_combo)
        left_layout.addLayout(format_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        left_panel.setMaximumWidth(420)
        left_panel.setMinimumWidth(300)
        splitter.addWidget(left_panel)

        # ========== 右侧区域 ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 预览组件
        self.preview_widget = PreviewWidget()
        right_layout.addWidget(self.preview_widget, stretch=3)

        # 日志区域
        log_label = QLabel("生成日志")
        log_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("background-color: #f5f5f5; font-family: Consolas, monospace;")
        right_layout.addWidget(self.log_text, stretch=1)

        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # ========== 快捷键设置 ==========
        self._setup_shortcuts()

    def _on_section_toggled(self, _visible):
        """面板折叠/展开时更新容器约束"""
        self._update_scroll_resizable()

    def _update_scroll_resizable(self):
        """全折叠时：widgetResizable=False + 限制 container 高度为 header 总高
        有展开时：widgetResizable=True + 清除高度限制"""
        any_expanded = (
            self.file_section.is_expanded()
            or self.file_info_section.is_expanded()
            or self.params_section.is_expanded()
        )
        self._shared_scroll.setWidgetResizable(any_expanded)

        container = self._scroll_container
        if any_expanded:
            # 展开：清除所有约束，让 scroll area 自由管理
            container.setMinimumHeight(0)
            container.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
            container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        else:
            # 全折叠：锁定 container 高度为三个 header 的总高
            header_h = sum(
                s._header.sizeHint().height()
                for s in [self.file_section, self.file_info_section, self.params_section]
            )
            container.setMaximumHeight(header_h)
            container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            container.setFixedHeight(header_h)

    def _setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+O: 打开文件
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self._on_open_file)

        # Ctrl+S: 保存模板
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._on_save_template)

        # Ctrl+Enter: 生成架构图
        generate_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        generate_shortcut.activated.connect(self._on_generate)

        # Ctrl+Q: 退出应用
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

    def _on_open_file(self):
        """打开文件（快捷键触发）"""
        self.file_selector._on_add_file()

    def _on_save_template(self):
        """保存模板（快捷键触发）"""
        self.params_panel._on_save_template()

    def _setup_connections(self):
        """设置信号连接"""
        # 生成按钮
        self.generate_btn.clicked.connect(self._on_generate)

        # 参数改变
        self.params_panel.params_changed.connect(self._on_params_changed)

        # 单模块调色
        self.params_panel.module_color_applied.connect(self._on_module_color_applied)

        # 批量模块调色
        self.params_panel.batch_module_color_applied.connect(self._on_batch_module_color_applied)

        # 文件选择改变
        self.file_selector.files_changed.connect(self._on_files_changed)

        # 当前操作文件改变
        self.file_selector.current_file_changed.connect(self._on_current_file_changed)

    def _on_generate(self):
        """点击生成按钮 — 只处理选中的文件"""
        # 优先使用列表中选中的文件；无选中项时处理全部
        selected_items = self.file_selector.file_list.selectedItems()
        if selected_items:
            files = [item.data(Qt.UserRole) for item in selected_items]
        else:
            files = self.file_selector.get_files()
        if not files:
            QMessageBox.warning(self, "警告", "请先选择Excel文件")
            return

        # 如果有 pending 参数，先应用到已有 markdown
        if self._pending_params and self._generated_md_files:
            self._apply_pending_params()
            self._pending_params = None
            self.apply_params_btn.setEnabled(False)

        # 清空图片历史记录
        self.preview_widget.clear()

        # 创建输出目录
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'output')
        os.makedirs(output_dir, exist_ok=True)

        # 获取参数
        params = self.params_panel.get_params()

        # 获取导出格式
        export_format = self._get_export_format()

        # 创建工作线程
        self._worker = GenerateWorker(files, output_dir, params, export_format,
                                       session_processed=self._session_processed)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.log.connect(self._on_log)
        self._worker.file_generated.connect(self._on_file_generated)
        self._worker.file_status.connect(self._on_file_status)

        # 更新UI状态
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 启动工作线程
        self._worker.start()

    def _apply_pending_params(self):
        """将 pending 参数应用到已有 markdown 文件（仅修改 CSS，不重新生成）

        所有 CSS 替换通过 _sub_in_css_blocks 执行，确保正则不跨越 } 边界。
        """
        import re
        params = self._pending_params
        applied_count = 0

        for excel_path, md_path in self._generated_md_files.items():
            if not os.path.exists(md_path):
                continue
            orig = self._original_params.get(md_path, {})
            init_css = self._initial_css.get(md_path, {})
            if not orig or not init_css:
                continue

            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # --- 颜色直接替换 ---
            color_map = {
                'GROUP_BG': (r'(\.group\s*\{[^}]*background:\s*)', 'GROUP_BG'),
                'GROUP_HEADER_COLOR': (r'(\.group-header\s*\{[^}]*background:\s*)', 'GROUP_HEADER_COLOR'),
                'MODULE_BG_COLOR': (r'(\.module\s*\{[^}]*background:\s*)', 'MODULE_BG_COLOR'),
                'DOMAIN_BG': (r'(\.domain-frame-wrapper\s*\{[^}]*background:\s*)', 'DOMAIN_BG'),
                'DOMAIN_BORDER_COLOR': (r'(\.domain-frame-wrapper\s*\{[^}]*border:\s*(?:\d+(?:\.\d+)?px\s+solid\s+))', 'DOMAIN_BORDER_COLOR'),
                'DOMAIN_TITLE_COLOR': (r'(\.domain-title\s*\{[^}]*color:\s*)', 'DOMAIN_TITLE_COLOR'),
                'MODULE_BORDER_COLOR': (r'(\.module\s*\{[^}]*border:\s*\d+(?:\.\d+)?px\s+solid\s+)', 'MODULE_BORDER_COLOR'),
            }
            for param_key, (pattern, orig_key) in color_map.items():
                if param_key in params and orig_key in orig:
                    old_val = orig[orig_key]
                    new_val = params[param_key]
                    if old_val != new_val:
                        content = _sub_in_css_blocks(content,
                            pattern + re.escape(old_val),
                            lambda m, v=new_val: m.group(1) + v)

            # --- 数值按比例缩放 ---
            # 使用 _initial_css（首次生成时的 CSS 值，不可覆盖）作为基准，
            # 确保重复 apply 时不会叠加放大。
            css_configs = {
                'MODULE_FONT_SIZE':      ('MODULE_FONT_SIZE_PX',      r'(\.module\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px'),
                'GROUP_HEADER_FONT_SIZE':('GROUP_HEADER_FONT_SIZE_PX',r'(\.group-header\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px'),
                'DOMAIN_TITLE_FONT_SIZE':('DOMAIN_TITLE_FONT_SIZE_PX',r'(\.domain-title\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px'),
                'COL_GAP':               ('COL_GAP_PX',               r'(\.columns\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px'),
                'ROW_GAP':               ('ROW_GAP_PX',               r'(\.modules\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px'),
                'COLUMN_GAP':            ('COLUMN_GAP_PX',            r'(\.column\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px'),
                'DOMAIN_BORDER_RADIUS':  ('DOMAIN_BORDER_RADIUS_PX',  r'(\.domain-frame-wrapper\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px'),
                'GROUP_BORDER_RADIUS':   ('GROUP_BORDER_RADIUS_PX',   r'(\.group\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px'),
                'MODULE_BORDER_RADIUS':  ('MODULE_BORDER_RADIUS_PX',  r'(\.module\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px'),
                'DOMAIN_TITLE_MARGIN_BOTTOM': ('DOMAIN_TITLE_MARGIN_BOTTOM_PX', r'(\.domain-title\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px'),
                'GROUP_HEADER_MARGIN_BOTTOM': ('GROUP_HEADER_MARGIN_BOTTOM_PX', r'(\.group-header\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px'),
                'DOMAIN_BORDER_WIDTH':   ('DOMAIN_BORDER_WIDTH_PX',   r'(\.domain-frame-wrapper\s*\{[^}]*border:\s*)(\d+(?:\.\d+)?)px(\s+solid)'),
            }
            for param_key, (css_key, pattern) in css_configs.items():
                if param_key in params and css_key in init_css:
                    config_old = orig.get(param_key, 0)
                    config_new = params[param_key]
                    if config_old > 0:
                        target_css = init_css[css_key] * (config_new / config_old)
                        if param_key == 'DOMAIN_BORDER_WIDTH':
                            content = _sub_in_css_blocks(content, pattern,
                                lambda m, v=target_css: m.group(1) + f'{v:.0f}px' + m.group(3))
                        elif 'font-size' in pattern:
                            content = _sub_in_css_blocks(content, pattern,
                                lambda m, v=target_css: m.group(1) + f'{v:.1f}px')
                        else:
                            content = _sub_in_css_blocks(content, pattern,
                                lambda m, v=target_css: m.group(1) + f'{v:.0f}px')

            # --- 域内边距（特殊处理：两个值） ---
            if 'DOMAIN_PADDING' in params and 'DOMAIN_PADDING_Y_PX' in init_css:
                config_old = orig.get('DOMAIN_PADDING', 0)
                config_new = params['DOMAIN_PADDING']
                if config_old > 0:
                    target_y = init_css['DOMAIN_PADDING_Y_PX'] * (config_new / config_old)
                    target_x = init_css.get('DOMAIN_PADDING_X_PX', 16) * (config_new / config_old)
                    content = _sub_in_css_blocks(content,
                        r'(\.domain-frame-wrapper\s*\{[^}]*padding:\s*)(\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px',
                        lambda m, ty=target_y, tx=target_x: m.group(1) + f'{ty:.0f}px {tx:.0f}px')

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self._css_state[md_path] = extract_params_from_md(md_path)
            applied_count += 1

        self.log_text.append(f"参数已应用到 {applied_count} 个 Markdown 文件")
        self.statusBar().showMessage(f"参数已应用到 {applied_count} 个文件")

    def _get_export_format(self) -> str:
        """获取导出格式"""
        if hasattr(self, 'export_format_combo'):
            return self.export_format_combo.currentData()
        return 'png'  # 默认导出PNG

    def _on_cancel(self):
        """取消生成操作"""
        if self._worker and self._worker.isRunning():
            self.log_text.append("\n--- 用户取消操作 ---")
            self._worker.cancel()
            self.cancel_btn.setEnabled(False)

    def _on_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(message)

    def _on_finished(self, success: bool, message: str):
        """生成完成"""
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        if success:
            # 合并 worker 的追踪数据到 MainWindow
            if self._worker:
                self._generated_md_files.update(self._worker.get_excel_to_md())
                self._original_params.update(self._worker.get_original_params())

                # 为新生成的文件提取 CSS 状态（作为后续参数调整的基准）
                for md_path in self._worker.get_generated_md_files():
                    if os.path.exists(md_path):
                        css = extract_params_from_md(md_path)
                        self._css_state[md_path] = css
                        # _initial_css 只在首次生成时设置，不可覆盖
                        # 否则后续 apply 的缩放基准会偏移
                        if md_path not in self._initial_css:
                            self._initial_css[md_path] = css.copy()

            self.statusBar().showMessage("生成完成")

            # 显示最后一个生成的文件预览
            log_content = self.log_text.toPlainText()
            last_md_path = ""
            for line in reversed(log_content.split('\n')):
                if 'Markdown生成成功:' in line:
                    last_md_path = line.split('Markdown生成成功:')[1].strip()
                    break

            if last_md_path:
                self._show_preview(last_md_path)

            QMessageBox.information(self, "完成", message)
        else:
            self.statusBar().showMessage("生成失败")
            QMessageBox.warning(self, "失败", message)

        self._worker = None

    def _on_log(self, message: str):
        """添加日志"""
        self.log_text.append(message)

    def _on_file_generated(self, md_path: str, png_path: str):
        """单个文件生成完成"""
        # 添加图片到历史记录
        if png_path:
            self.preview_widget.add_image(png_path)
        else:
            self.preview_widget.add_image(md_path)

    def _on_file_status(self, index: int, status: str, message: str):
        """文件状态更新"""
        # 可以在这里更新文件列表中的状态显示
        pass

    def _on_params_changed(self, params: dict):
        """参数改变时，暂存变更，等待用户点击[应用参数]按钮"""
        self._pending_params = params
        self.apply_params_btn.setEnabled(bool(self._generated_md_files))
        self.statusBar().showMessage("参数已调整，点击[应用参数到 Markdown]生效")

    def _on_module_color_applied(self, module_name: str, color: str):
        """为当前文件中的指定模块设置颜色，并重新生成 PNG"""
        if not self._generated_md_files:
            QMessageBox.warning(self, "提示", "请先生成架构图")
            return

        # 确定要处理的 MD 文件：优先当前文件，否则全部
        if self._current_excel_path and self._current_excel_path in self._generated_md_files:
            targets = {self._current_excel_path: self._generated_md_files[self._current_excel_path]}
        else:
            targets = self._generated_md_files

        import subprocess

        if DEBUG_MODULE_COLOR:
            print(f"\n[ModuleColor] === 开始调色 ===")
            print(f"[ModuleColor] 模块名: '{module_name}', 颜色: {color}")
            print(f"[ModuleColor] 目标文件: {list(targets.values())}")

        success_count = 0
        last_md = None
        for excel_path, md_path in targets.items():
            if not os.path.exists(md_path):
                continue

            ok, msg = apply_module_color(md_path, module_name, color)
            if ok:
                success_count += 1
                last_md = md_path
                self.log_text.append(f"[模块调色] {os.path.basename(md_path)}: {msg}")
                # 重新生成 PNG
                try:
                    png_path = md_path.replace('.md', '.png')
                    cmd = ['marp', md_path, '--images', 'png', '--allow-local-files', '-o', png_path]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                   shell=True, encoding='utf-8', errors='ignore')
                except Exception as e:
                    self.log_text.append(f"[模块调色] PNG生成失败: {e}")
            else:
                self.log_text.append(f"[模块调色] {os.path.basename(md_path)}: {msg}")

        if success_count > 0:
            self.statusBar().showMessage(f'已为 {success_count} 个文件中的模块 "{module_name}" 设置颜色')
            # 刷新预览
            if last_md and os.path.exists(last_md):
                png_path = last_md.replace('.md', '.png')
                if os.path.exists(png_path):
                    self.preview_widget.set_image(png_path, force_refresh=True)
        else:
            QMessageBox.warning(self, "提示", f'未在任何文件中找到模块: {module_name}')

    def _on_batch_module_color_applied(self, module_names: list, color: str):
        """批量为当前文件中的多个模块设置颜色"""
        if not self._generated_md_files:
            QMessageBox.warning(self, "提示", "请先生成架构图")
            return

        # 确定目标文件
        if self._current_excel_path and self._current_excel_path in self._generated_md_files:
            md_path = self._generated_md_files[self._current_excel_path]
        else:
            QMessageBox.warning(self, "提示", "请先选择一个文件")
            return

        if not os.path.exists(md_path):
            return

        import subprocess
        total = len(module_names)
        success = 0
        for i, name in enumerate(module_names):
            ok, msg = apply_module_color(md_path, name, color)
            if ok:
                success += 1
                self.log_text.append(f"[批量调色] ({i+1}/{total}) {name}: {msg}")

        # 重新生成 PNG
        if success > 0:
            try:
                png_path = md_path.replace('.md', '.png')
                cmd = ['marp', md_path, '--images', 'png', '--allow-local-files', '-o', png_path]
                subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                               shell=True, encoding='utf-8', errors='ignore')
            except Exception as e:
                self.log_text.append(f"[批量调色] PNG生成失败: {e}")

            # 刷新预览
            png_path = md_path.replace('.md', '.png')
            if os.path.exists(png_path):
                self.preview_widget.set_image(png_path, force_refresh=True)

            self.statusBar().showMessage(f"已为 {success}/{total} 个模块设置颜色")
        else:
            QMessageBox.warning(self, "提示", "未找到任何匹配的模块")

    def _on_apply_params(self):
        """将暂存的参数应用到当前 Markdown 文件"""
        if not self._pending_params or not self._generated_md_files:
            return

        # 确定要处理的 MD 文件：优先当前文件，否则全部
        if self._current_excel_path and self._current_excel_path in self._generated_md_files:
            targets = {self._current_excel_path: self._generated_md_files[self._current_excel_path]}
        else:
            targets = self._generated_md_files

        params = self._pending_params
        applied_count = 0

        for excel_path, md_path in targets.items():
            if not os.path.exists(md_path):
                continue

            orig = self._original_params.get(md_path, {})
            init_css = self._initial_css.get(md_path, {})
            if not orig or not init_css:
                continue

            ok, updated_css = apply_params_to_md(md_path, params, orig, css_baseline=init_css)
            if ok:
                self._css_state[md_path] = updated_css or extract_params_from_md(md_path)
                applied_count += 1

        self._pending_params = None
        self.apply_params_btn.setEnabled(False)
        self.log_text.append(f"参数已应用到 {applied_count} 个 Markdown 文件")
        self.statusBar().showMessage(f"参数已应用到 {applied_count} 个文件")

        # 刷新预览
        if self._current_excel_path and self._current_excel_path in targets:
            md_path = targets[self._current_excel_path]
            if os.path.exists(md_path):
                self._show_preview(md_path)

    def _on_files_changed(self, files: list):
        """文件选择改变时"""
        if files:
            # 显示第一个文件的信息
            self.file_info.load_file(files[0])
            self.statusBar().showMessage(f"已选择 {len(files)} 个文件")
        else:
            self.file_info.clear()
            self.statusBar().showMessage("就绪")

    def _on_current_file_changed(self, excel_path: str):
        """当前操作文件改变时，更新文件信息和预览"""
        self._current_excel_path = excel_path
        # 更新文件信息面板
        self.file_info.load_file(excel_path)
        # 将模块数据传递给参数面板（供批量调色使用）
        if excel_path in self.file_info._cache:
            _, groups = self.file_info._cache[excel_path]
            self.params_panel.set_current_modules(groups)
        # 查找对应的 MD 文件并刷新预览
        md_path = self._generated_md_files.get(excel_path)
        if md_path and os.path.exists(md_path):
            self._show_preview(md_path)
            self.statusBar().showMessage(f"当前文件: {os.path.basename(excel_path)}")

    def _show_preview(self, md_path: str):
        """显示预览

        Args:
            md_path: 生成的Markdown文件路径
        """
        import glob

        # 尝试显示对应的PNG图片
        png_path = md_path.replace('.md', '.png')

        # 检查图片是否存在
        if os.path.exists(png_path):
            self.preview_widget.set_image(png_path)
            self.log_text.append(f"预览图片: {png_path}")
            return

        # 尝试查找MarP生成的文件 (xxx.001.png 格式)
        md_dir = os.path.dirname(md_path)
        base_name = os.path.splitext(os.path.basename(md_path))[0]

        # 查找所有匹配的PNG文件
        pattern = os.path.join(md_dir, f'{base_name}*.png')
        matches = glob.glob(pattern)

        if matches:
            # 使用第一个匹配的文件
            self.preview_widget.set_image(matches[0])
            self.log_text.append(f"预览图片: {matches[0]}")
            return

        # 尝试查找MarP生成的图片目录
        img_dir = os.path.splitext(md_path)[0]

        if os.path.isdir(img_dir):
            # 查找目录中的png文件
            for f in os.listdir(img_dir):
                if f.endswith('.png'):
                    actual_png = os.path.join(img_dir, f)
                    self.preview_widget.set_image(actual_png)
                    self.log_text.append(f"预览图片: {actual_png}")
                    return

        # 如果没有找到图片，显示提示信息
        self.preview_widget.image_label.setText(
            f"Markdown文件已生成:\n{md_path}\n\n"
            f"PNG文件未找到，请检查MarP CLI是否正确安装"
        )
