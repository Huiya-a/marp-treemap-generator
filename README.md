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
- ✅ **多种输出**: 支持 Markdown、PPTX、PNG 格式

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
```

## GUI 使用说明

### 1. 选择文件
- 点击"添加文件"按钮选择 Excel 文件
- 点击"添加文件夹"按钮批量添加
- 支持直接拖拽 Excel 文件到文件列表区域

### 2. 调整参数（可选）
在右侧面板中可以调整以下参数：
- **颜色设置**: 组背景色、组标题色、模块背景色
- **尺寸设置**: 模块宽高、列间距、行间距
- **字体设置**: 模块字号、标题字号
- **布局设置**: MPR 平衡调整、目标宽高比

### 3. 生成架构图
- 点击"生成架构图"按钮开始生成
- 底部进度条显示生成进度
- 日志区域显示详细的生成信息

### 4. 查看结果
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
│       ├── main_window.py         # 主窗口
│       ├── file_selector.py       # 文件选择器
│       ├── preview_widget.py      # 预览组件
│       └── params_panel.py        # 参数面板
├── output/                        # 生成的 Markdown / PNG / PPTX
│   └── 调整指南.md                 # 手动调整样式的完整指南
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

生成的 Markdown 文件可以直接编辑。详细的调整方法请查看：

👉 **[调整指南](output/调整指南.md)**

涵盖：字号、内边距、间距、颜色、圆角、模块大小、字体、换行等所有可调整项。

## 技术细节

如需深入了解布局算法、CSS 架构和版本约束，请查看：

👉 **[技术文档](技术文档.md)**

## 项目进度

GUI应用开发进度跟踪，请查看：

👉 **[项目进度](项目进度.md)**

当前进度：4/6阶段完成（67%）
- ✅ 第一阶段：环境搭建与基础框架
- ✅ 第二阶段：文件选择与基础预览
- ✅ 第三阶段：参数调整面板完善
- ✅ 第四阶段：批量处理功能
- 📋 第五阶段：高级功能（待开始）
