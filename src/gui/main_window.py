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
    QProgressBar, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QShortcut, QKeySequence

# 导入自定义组件
from .file_selector import FileSelector
from .preview_widget import PreviewWidget
from .params_panel import ParamsPanel
from .file_info_widget import FileInfoWidget

# 导入项目模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from src import config
from src.data_loader import load_data_from_excel


class GenerateWorker(QThread):
    """生成工作线程"""

    # 信号
    progress = Signal(int, str)  # 进度百分比, 消息
    finished = Signal(bool, str)  # 是否成功, 消息或文件路径
    log = Signal(str)  # 日志消息
    file_generated = Signal(str, str)  # 单个文件生成完成，传递(md路径, png路径)
    file_status = Signal(int, str, str)  # 文件状态更新 (索引, 状态, 消息)

    def __init__(self, files: list, output_dir: str, params: dict, export_format: str = 'png'):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.params = params
        self.export_format = export_format  # 导出格式: 'png', 'pptx', 'both'
        self._is_cancelled = False
        self._generated_md_files = []  # 保存生成的MD文件路径

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

                    # 更新配置参数
                    self._apply_params()

                    # 生成Markdown
                    from generate_treemap_md import generate_marp_md
                    generate_marp_md(domain_name, data, output_path, proportional_width=None)

                    self.log.emit(f"  Markdown生成成功: {output_path}")
                    self._generated_md_files.append(output_path)

                    # 根据导出格式生成文件
                    png_path = ""
                    pptx_path = ""
                    html_path = ""

                    if self.export_format in ['png', 'both', 'png_html', 'all']:
                        # 调用MarP CLI生成PNG图片
                        png_path = self._generate_png(output_path)
                        if png_path:
                            self.log.emit(f"  PNG生成成功: {png_path}")
                            generated_files.append(png_path)
                        else:
                            self.log.emit(f"  PNG生成失败（可能未安装MarP CLI）")

                    if self.export_format in ['pptx', 'both', 'all']:
                        # 调用MarP CLI生成PPTX
                        pptx_path = self._generate_pptx(output_path)
                        if pptx_path:
                            self.log.emit(f"  PPTX生成成功: {pptx_path}")
                            generated_files.append(pptx_path)
                        else:
                            self.log.emit(f"  PPTX生成失败（可能未安装MarP CLI）")

                    if self.export_format in ['html', 'png_html', 'all']:
                        # 调用MarP CLI生成HTML
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
        finally:
            # 恢复配置模块的原始值
            self._restore_config()

    def get_generated_md_files(self) -> list:
        """获取生成的MD文件路径列表"""
        return self._generated_md_files.copy()

    def _generate_png(self, md_path: str) -> str:
        """调用MarP CLI生成PNG图片

        Args:
            md_path: Markdown文件路径

        Returns:
            生成的PNG文件路径，失败返回空字符串
        """
        try:
            # 构建PNG输出路径
            png_path = md_path.replace('.md', '.png')

            # 调用MarP CLI
            cmd = [
                'marp',
                md_path,
                '--images', 'png',
                '--allow-local-files',
                '-o', png_path
            ]

            self.log.emit(f"  执行命令: {' '.join(cmd)}")

            # 执行命令，使用shell=True以便在Windows上找到命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60秒超时
                shell=True,  # 在Windows上需要使用shell
                encoding='utf-8',  # 指定编码
                errors='ignore'  # 忽略编码错误
            )

            if result.returncode == 0:
                # MarP CLI会生成文件，文件名可能是:
                # 1. 直接是 png_path
                # 2. png_path 目录下的文件
                # 3. md文件同目录下的 xxx.001.png 格式

                # 检查直接路径
                if os.path.exists(png_path):
                    return png_path

                # 检查目录
                md_dir = os.path.dirname(md_path)
                base_name = os.path.splitext(os.path.basename(md_path))[0]

                # 查找 xxx.001.png 格式的文件
                for f in os.listdir(md_dir):
                    if f.startswith(base_name) and f.endswith('.png'):
                        return os.path.join(md_dir, f)

                # 检查同名目录
                dir_path = os.path.splitext(md_path)[0]
                if os.path.isdir(dir_path):
                    for f in os.listdir(dir_path):
                        if f.endswith('.png'):
                            return os.path.join(dir_path, f)

                # 如果都没找到，返回预期的路径
                return png_path
            else:
                self.log.emit(f"  MarP CLI错误: {result.stderr}")
                return ""

        except FileNotFoundError:
            self.log.emit("  未找到MarP CLI，请先安装: npm install -g @marp-team/marp-cli")
            self.log.emit("  或者尝试使用完整路径调用")
            return ""
        except subprocess.TimeoutExpired:
            self.log.emit("  MarP CLI执行超时")
            return ""
        except Exception as e:
            self.log.emit(f"  调用MarP CLI失败: {str(e)}")
            import traceback
            self.log.emit(f"  错误详情: {traceback.format_exc()}")
            return ""

    def _generate_pptx(self, md_path: str) -> str:
        """调用MarP CLI生成PPTX文件

        Args:
            md_path: Markdown文件路径

        Returns:
            生成的PPTX文件路径，失败返回空字符串
        """
        try:
            # 构建PPTX输出路径
            pptx_path = md_path.replace('.md', '.pptx')

            # 调用MarP CLI
            cmd = [
                'marp',
                md_path,
                '--pptx',
                '--allow-local-files',
                '-o', pptx_path
            ]

            self.log.emit(f"  执行命令: {' '.join(cmd)}")

            # 执行命令，使用shell=True以便在Windows上找到命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 120秒超时（PPTX生成较慢）
                shell=True,  # 在Windows上需要使用shell
                encoding='utf-8',  # 指定编码
                errors='ignore'  # 忽略编码错误
            )

            if result.returncode == 0:
                if os.path.exists(pptx_path):
                    return pptx_path
                else:
                    # 检查是否生成了其他格式的文件
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
            import traceback
            self.log.emit(f"  错误详情: {traceback.format_exc()}")
            return ""

    def _generate_html(self, md_path: str) -> str:
        """调用MarP CLI生成HTML文件

        Args:
            md_path: Markdown文件路径

        Returns:
            生成的HTML文件路径，失败返回空字符串
        """
        try:
            # 构建HTML输出路径
            html_path = md_path.replace('.md', '.html')

            # 调用MarP CLI
            cmd = [
                'marp',
                md_path,
                '--html',
                '--allow-local-files',
                '-o', html_path
            ]

            self.log.emit(f"  执行命令: {' '.join(cmd)}")

            # 执行命令，使用shell=True以便在Windows上找到命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60秒超时
                shell=True,  # 在Windows上需要使用shell
                encoding='utf-8',  # 指定编码
                errors='ignore'  # 忽略编码错误
            )

            if result.returncode == 0:
                if os.path.exists(html_path):
                    return html_path
                else:
                    # 检查是否生成了其他格式的文件
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
            import traceback
            self.log.emit(f"  错误详情: {traceback.format_exc()}")
            return ""

    def _apply_params(self):
        """应用参数到配置模块"""
        # 保存原始值，以便生成后恢复
        self._original_config = {}
        for key, value in self.params.items():
            if hasattr(config, key):
                self._original_config[key] = getattr(config, key)
                setattr(config, key, value)

    def _restore_config(self):
        """恢复配置模块的原始值"""
        if hasattr(self, '_original_config'):
            for key, value in self._original_config.items():
                setattr(config, key, value)
            self._original_config = {}

    def cancel(self):
        """取消操作"""
        self._is_cancelled = True


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._worker = None
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

        # 文件选择器
        self.file_selector = FileSelector()
        left_layout.addWidget(self.file_selector)

        # 文件信息预览
        self.file_info = FileInfoWidget()
        left_layout.addWidget(self.file_info)

        # 参数面板
        self.params_panel = ParamsPanel()
        left_layout.addWidget(self.params_panel)

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
        self.export_format_combo = QComboBox()
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

        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(280)
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
        splitter.setSizes([350, 850])

        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # ========== 快捷键设置 ==========
        self._setup_shortcuts()

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

        # 文件选择改变
        self.file_selector.files_changed.connect(self._on_files_changed)

    def _on_generate(self):
        """点击生成按钮"""
        files = self.file_selector.get_files()
        if not files:
            QMessageBox.warning(self, "警告", "请先选择Excel文件")
            return

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
        self._worker = GenerateWorker(files, output_dir, params, export_format)
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
            self.statusBar().showMessage("生成完成")

            # 显示最后一个生成的文件预览
            # 从日志中获取最后生成的文件路径
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
        """参数改变时"""
        # 参数改变时不做任何操作，等待用户点击"生成架构图"按钮
        pass

    def _on_files_changed(self, files: list):
        """文件选择改变时"""
        if files:
            # 显示第一个文件的信息
            self.file_info.load_file(files[0])
            self.statusBar().showMessage(f"已选择 {len(files)} 个文件")
        else:
            self.file_info.clear()
            self.statusBar().showMessage("就绪")

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
