# Marp Treemap Generator

将应用架构 Excel 数据转换为 Treemap 矩形图，输出 Marp 兼容的 Markdown，可一键转为 PPT 幻灯片。

## 效果预览

每页展示一个应用域的 Treemap 包含关系图，包含域标题、应用组（蓝色标题栏）和模块格子。

## 功能特性

- ✅ **命令行模式**: 批量生成 Markdown 文件
- ✅ **GUI 模式**: 图形界面，支持实时预览和参数调整
- ✅ **文件选择**: 支持选择单个或多个 Excel 文件，支持拖拽导入
- ✅ **参数调整**: 可以调整颜色、间距、字体等参数
- ✅ **批量处理**: 支持多文件批量生成
- ✅ **多种输出**: 支持 Markdown、PPTX、PNG、HTML 格式及组合导出
- ✅ **模板管理**: 保存和加载参数配置模板
- ✅ **历史记录**: 使用QSettings存储最近打开的文件
- ✅ **快捷键**: Ctrl+O 打开、Ctrl+S 保存、Ctrl+Enter 生成、Ctrl+Q 退出
- ✅ **可折叠面板**: 左侧各区域支持展开/收起
- ✅ **模块调色**: 单模块调色 + 批量多模块调色，支持重复修改
- ✅ **会话级复用**: 已生成的 Markdown 在同一会话内不重复生成

## 快速开始

### 安装依赖

```bash
# 命令行模式
pip install openpyxl numpy

# GUI 模式（额外需要 PySide6）
pip install "PySide6>=6.5.0" "openpyxl>=3.1.0" "numpy>=1.24.0"

# 安装 Marp CLI（转 PPT 用）
npm install -g @marp-team/marp-cli
```

### 命令行模式

```bash
# 生成 Markdown
python generate_treemap_md.py

# 转 PPTX
marp output/*.md --pptx

# 转 PNG 图片
marp output/*.md --images png --allow-local-files
```

### GUI 模式

```bash
# 启动 GUI 应用
python src/app.py

# 或者双击启动脚本 (Windows)
启动应用.bat
```

## 命令行用法

```bash
# 处理 data/ 下所有 Excel 文件
python generate_treemap_md.py

# 按前缀/包含匹配处理单个文件
python generate_treemap_md.py 03        # 匹配 "03 开头" 的文件
python generate_treemap_md.py 纪检监察   # 包含匹配

# 多文件按列数比例分配宽度（使不同幻灯片列宽可比）
python generate_treemap_md.py --proportional-width
```

## GUI 使用说明

### 1. 选择文件
- 点击"添加文件"按钮选择 Excel 文件
- 点击"添加文件夹"按钮批量添加
- 支持直接拖拽 Excel 文件到文件列表区域

### 2. 调整参数（可选）
在右侧面板中可以调整以下参数：
- **颜色设置**: 组背景色、组标题色、模块背景色、域背景色、域边框色、域标题色
- **间距设置**: 列间距、组间距
- **字体设置**: 模块字号、组标题字号
- **布局设置**: MPR 平衡调整、目标宽高比

### 3. 模块调色（可选）
- **单模块调色**: 在参数面板中输入模块名、选颜色，点击"应用"即可为指定模块设置独立背景色
- **批量调色**: 点击"批量调色"按钮，在弹窗中 Ctrl 多选模块，统一设置颜色
- 支持重复修改，多次调色会覆盖前一次的颜色

### 4. 生成架构图
- 点击"生成架构图"按钮开始生成
- 底部进度条显示生成进度
- 日志区域显示详细的生成信息

### 5. 查看结果
生成完成后，架构图会保存在 `output/` 目录中。

## 目录结构

```
marp_workspace/
├── generate_treemap_md.py         # 命令行主入口
├── 启动应用.bat                   # GUI 启动脚本 (Windows)
├── data/                          # Excel 数据源
├── src/
│   ├── app.py                     # GUI 应用入口
│   ├── config.py                  # 布局参数与配色
│   ├── data_loader.py             # Excel 数据加载
│   ├── layout.py                  # Treemap 布局算法
│   └── gui/                       # GUI 模块
│       ├── main_window.py         # 主窗口 + GenerateWorker线程
│       ├── file_selector.py       # 文件选择器（拖拽、历史记录）
│       ├── file_info_widget.py    # 文件信息预览
│       ├── preview_widget.py      # 预览组件（多图切换）
│       ├── params_panel.py        # 参数面板（颜色、尺寸、字体等）
│       ├── template_manager.py    # 模板管理器（保存/加载配置）
│       ├── md_editor.py           # Markdown CSS 正则编辑
│       ├── module_color_dialog.py # 批量模块调色对话框
│       └── collapsible_section.py # 可折叠面板组件
├── output/                        # 生成的 Markdown / PNG / PPTX
└── README.md
```

## Excel 数据格式

| 要求 | 说明 |
|------|------|
| Sheet 名称 | 需包含"应用模块清单"，或取第二个 sheet |
| 数据起始行 | 第 3 行 |
| B 列 | 应用域名称（作为 slide 标题） |
| D 列 | 应用组名称 |
| G 列 | 一级应用模块名称 |

## 数据流

```
Excel → data_loader → layout → HTML 生成 → Marp Markdown → PPTX/PNG
```

## 手动调整样式

生成的 Markdown 文件可以直接编辑，修改 CSS 属性即可调整样式。涵盖：字号、内边距、间距、颜色、圆角、模块大小、字体、换行等。

## 技术文档

如需深入了解布局算法、CSS 架构和版本约束，请查看：

- 👉 **[技术文档](doc/技术文档.md)**
- 👉 **[布局算法详解](doc/技术文档-布局算法详解.md)**
- 👉 **[Marp 规则参考](doc/marp-rules.md)**

## 附录

- 👉 **[代码结构说明](doc/代码结构说明.md)** — 各代码文件的职责、关键函数和调用关系
