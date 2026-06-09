# -*- coding: utf-8 -*-
"""
GUI模块测试脚本
"""

import sys
import os

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到Python路径
# 当前文件在 src/test_gui.py，需要向上一级到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    # 测试导入GUI模块
    from src.gui.main_window import MainWindow
    from src.gui.params_panel import ParamsPanel
    from src.gui.file_selector import FileSelector
    from src.gui.preview_widget import PreviewWidget

    print("✅ 所有GUI模块导入成功")

    # 测试ParamsPanel
    panel = ParamsPanel()
    params = panel.get_params()
    print(f"✅ ParamsPanel创建成功")
    print(f"   MODULE_W: {params['MODULE_W']}")
    print(f"   MODULE_H: {params['MODULE_H']}")
    print(f"   GROUP_BG: {params['GROUP_BG']}")

    # 测试FileSelector
    selector = FileSelector()
    print("✅ FileSelector创建成功")

    # 测试PreviewWidget
    preview = PreviewWidget()
    print("✅ PreviewWidget创建成功")

    print("\n🎉 所有测试通过！应用可以正常启动。")
    print("\n现在可以运行 'python app.py' 启动应用。")

except Exception as e:
    print(f"❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
