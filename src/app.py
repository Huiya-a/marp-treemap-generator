# -*- coding: utf-8 -*-
"""
应用架构图生成器 - 主入口

启动GUI应用程序。
"""

import sys
import os

# 确保项目根目录在Python路径中
# 当前文件在 src/app.py，需要向上一级到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from src.gui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("应用架构图生成器")
    app.setOrganizationName("架构图生成器")

    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
