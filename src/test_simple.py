# -*- coding: utf-8 -*-
"""
简单测试脚本
"""

import sys
import os

# 设置UTF-8编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到Python路径
# 当前文件在 src/test_simple.py，需要向上一级到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("开始测试...")

try:
    # 测试导入配置模块
    from src import config
    print("✅ 配置模块导入成功")
    print(f"   MODULE_W: {config.MODULE_W}")
    print(f"   MODULE_H: {config.MODULE_H}")

    # 测试导入数据加载模块
    from src.data_loader import load_data_from_excel
    print("✅ 数据加载模块导入成功")

    # 测试导入GUI模块
    from src.gui.params_panel import ParamsPanel
    print("✅ ParamsPanel导入成功")

    from src.gui.file_selector import FileSelector
    print("✅ FileSelector导入成功")

    from src.gui.preview_widget import PreviewWidget
    print("✅ PreviewWidget导入成功")

    from src.gui.main_window import MainWindow
    print("✅ MainWindow导入成功")

    print("\n🎉 所有模块导入成功！")
    print("\n现在可以运行 'python app.py' 启动应用。")

except Exception as e:
    print(f"❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
