# Marp Treemap Generator

将应用架构 Excel 数据转换为 Marp 兼容的 Markdown 文件，可通过 Marp 一键转为 PPT 幻灯片，每页展示一个域的 Treemap 矩形包含关系图。

## 快速开始

```bash
# 1. 安装依赖
pip install openpyxl numpy

# 2. 安装 Marp CLI（用于转 PPT）
npm install -g @marp-team/marp-cli

# 3. 生成 Markdown
python generate_treemap_md.py

# 4. 转换为 PPT
marp output/*.md --pptx
```

## 目录结构

```
marp_workspace/
├── data/                          # Excel 数据源（应用架构表）
├── src/
│   ├── config.py                  # 布局参数与配色
│   ├── data_loader.py             # Excel 数据加载
│   └── layout.py                  # Treemap 布局算法
├── output/                        # 生成的 Markdown / PPTX 文件
├── generate_treemap_md.py         # 主入口脚本（数据加载→布局→HTML→Markdown）
└── README.md
```

## 命令行用法

```bash
# 处理 data/ 下所有 Excel 文件
python generate_treemap_md.py

# 按前缀匹配处理单个文件
python generate_treemap_md.py 03        # 匹配 "03 开头" 的文件
python generate_treemap_md.py 纪检监察   # 包含匹配
```

## 数据流

```
Excel 文件
  → data_loader (读取"应用模块清单" sheet，B=域, D=组, G=模块)
  → layout (计算列数、分列、装箱、缩放)
  → generate_treemap_md (生成 HTML + CSS → Marp Markdown)
  → marp CLI (Markdown → PPTX)
```

## 布局算法详解

### 整体流程

1. **加载数据** — 从 Excel 读取 `{组名: [模块名]}` 字典
2. **计算每组 mpr** — `compute_modules_per_row(n)` 根据模块数 n 计算最优"每行模块数"，目标是列数/行数 ≈ 1.5
3. **确定列数** — `compute_optimal_column_count` 尝试 2~4 列，综合评分（模块分布平衡 + 视觉行数平衡 + 宽高比）选最优
4. **分配组到列** — `_assign_groups_to_columns` 按模块数降序贪心分配，平衡各列的模块数和视觉行数
5. **调整 mpr** — `_adjust_mpr_for_balance` 逐列尝试减小 mpr（3→2 等）来平衡列间高度
6. **行内打包** — `_pack_groups_into_rows` 列内组按宽度贪心打包成行
7. **等比缩放** — `scale = min(scale_x, scale_y)` 统一缩放适配画布，8% 安全边距防溢出
8. **生成 HTML** — 用 CSS flex 布局渲染列和组，输出 Marp Markdown

### 两种代码路径

| 条件 | 路径 | 特点 |
|------|------|------|
| 组数 < 6 | `compute_optimal_column_count` + `_assign_groups_to_columns` | 动态列数，平衡评分 |
| 组数 ≥ 6 | `_layout_many_groups` | 固定 mpr=3，贪心按行数填充列 |

### 关键配置 (`src/config.py`)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CANVAS_W` / `CANVAS_H` | 13.33 / 7.5 | 自然单位画布尺寸 |
| `CANVAS_W_PX` / `CANVAS_H_PX` | 1280 / 720 | Marp 像素尺寸 |
| `MODULE_W` / `MODULE_H` | 1.5 / 0.5 | 模块自然尺寸 |
| `COL_GAP` | 0.2 | 列间间距（自然单位） |
| `ROW_GAP` | 0.1 | 组上下间距（自然单位） |
| `ADJUST_MPR` | True | 是否启用 mpr 平衡调整 |

### Marp CSS 注意事项

- Marp 默认用 `display: flex; flex-direction: column` 包裹 `<section>`，必须用 `section { display: block !important; }` 覆盖
- `.treemap` 必须用 `position: absolute; top/left/right/bottom: 0` 填满 slide
- CSS Grid 在 Marp 中不可靠，用 `<table>` + `table-layout: fixed` 代替
- `.modules` 必须 `display: table !important; width: 100% !important`，否则 Marp 默认样式会破坏布局
- `.column` 必须用 `flex: 1 1 0`，`flex: 0 0 auto` 在 Marp v4.4.0 中不生效
- 空 `<td>` 不要渲染，Marp 默认 td 样式无法用 inline style 覆盖

## 配色方案

| 元素 | 颜色 |
|------|------|
| 域边框 | `#2C3E50` |
| 域背景 | `#F0F4F8` |
| 应用组背景 | `#E0E0E0` |
| 应用组标题 | `#1A73E8` |
| 模块背景 | `#C4D8FC` |

## Excel 数据格式

- Sheet 名称需包含"应用模块清单"，或取第二个 sheet
- 第 3 行起为数据
- B 列：应用域名称（用作 slide 标题）
- D 列：应用组名称
- G 列：一级应用模块名称
