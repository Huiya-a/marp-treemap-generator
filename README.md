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

## 版面约束（2026-06-02 确认）

> ⚠️ 版面已调试到接近期望形态，后续调整**不可破坏现有大体轮廓框架**。

### 核心结构（不可改动）

- 模块格子为**固定宽度矩形**，不满一行时**居中显示**，不拉伸填满
- 列分配使用 `score = module_dev + vr_dev²` 平衡视觉高度
- 组数 < 6 用动态列数，≥ 6 用固定 mpr=3 贪心填充
- Marp CSS 约束：section 必须 `display: block`，treemap 必须 `position: absolute`

### 可安全调整

- 颜色值、间距微调（≤20%）、字体大小、换行策略、目标比值（1.2~1.8）

### 禁止改动

- `--mod-w` CSS 变量机制、`justify-content: center` 居中策略
- section/treemap 定位方式、column 的 `flex: 1`
- 两套布局路径的切换逻辑（组数 6 为分界）

### 验证流程

```bash
python generate_treemap_md.py
marp output/*.md --images png --allow-local-files
# 逐张检查：模块等大居中、列高平衡、文字可读、无溢出
```

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

## 生成的 Markdown 文档结构详解

每个生成的 `.md` 文件由两大部分组成：**Frontmatter（元数据 + CSS 样式）** 和 **HTML 正文**。以下逐行说明各部分的作用。

### 一、Frontmatter 区域（`---` 包裹）

#### 1. Marp 元数据（第 1–5 行）

```yaml
---
marp: true
theme: default
paginate: false
backgroundColor: "#FAFBFC"
```

| 字段 | 值 | 说明 |
|------|-----|------|
| `marp: true` | 布尔值 | 声明该文件为 Marp 文档，Marp CLI 才会识别并处理 |
| `theme: default` | 字符串 | 使用 Marp 内置默认主题，不引入外部主题文件 |
| `paginate: false` | 布尔值 | 关闭页码显示，因为 Treemap 图不需要页码 |
| `backgroundColor` | `"#FAFBFC"` | 幻灯片整体背景色，接近白色的浅灰，作为域外框之外的底色 |

#### 2. CSS 样式块（`style: |` 开始）

使用 YAML 的多行字面量语法 `|`，将所有 CSS 规则作为字符串传递给 Marp。每一行 CSS 的作用如下：

##### 2.1 `section` — 覆盖 Marp 默认布局

```css
section {
  display: block !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden !important;
  position: relative !important;
  box-sizing: border-box;
}
```

| 属性 | 值 | 为什么需要 |
|------|-----|-----------|
| `display: block` | block | Marp 默认给 `<section>` 设置 `display: flex; flex-direction: column`，会将所有子元素挤压成纵向单列。改为 `block` 才能让内部的绝对定位 `.treemap` 正常工作 |
| `padding: 0` | 0 | 清除 Marp 主题自带的 section 内边距，防止内容偏移 |
| `margin: 0` | 0 | 清除 section 外边距，确保 slide 边缘对齐 |
| `overflow: hidden` | hidden | 裁切超出 slide 范围的内容，防止出现滚动条或溢出 |
| `position: relative` | relative | 为 `.treemap` 的 `position: absolute` 提供定位参考系 |
| `box-sizing: border-box` | border-box | 让 padding 包含在元素尺寸内，避免尺寸计算偏差 |

##### 2.2 `.treemap` — Treemap 容器

```css
.treemap {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow: hidden;
  padding: 20px;
  box-sizing: border-box;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `position: absolute` | absolute | 绝对定位，脱离文档流，配合 `top/left/right/bottom: 0` 铺满整个 section |
| `top/left/right/bottom: 0` | 0 | 四个方向都为 0，使容器完全填满 section（即整张 slide） |
| `display: flex` | flex | 启用 flexbox，让内部的 `.domain-frame-wrapper` 可以水平居中 |
| `align-items: flex-start` | flex-start | 垂方向顶部对齐，不拉伸域外框 |
| `justify-content: center` | center | 水平居中域外框，当域外框宽度小于 slide 宽度时居中显示 |
| `overflow: hidden` | hidden | 裁切溢出内容 |
| `padding: 20px` | 20px | 容器内边距，让域外框与 slide 边缘保持 20px 间距 |
| `box-sizing: border-box` | border-box | padding 包含在尺寸内 |

##### 2.3 `.domain-frame-wrapper` — 域外框（带边框和背景）

```css
.domain-frame-wrapper {
  width: 1240px;
  height: 100%;
  flex-shrink: 0;
  background: #F0F4F8;
  border: 3px solid #2C3E50;
  border-radius: 12px;
  padding: 12px 16px;
  box-sizing: border-box;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `width: 1240px` | 1240px | 固定宽度，略小于 slide 像素宽度（1280px），两侧各留 20px |
| `height: 100%` | 100% | 高度填满父容器（`.treemap`），即 slide 高度减去 padding |
| `flex-shrink: 0` | 0 | 禁止 flex 收缩，确保域外框不会被挤压变窄 |
| `background: #F0F4F8` | 浅灰蓝 | 域背景色，区分 slide 底色和域内容区域 |
| `border: 3px solid #2C3E50` | 深蓝 | 域边框，3px 实线深蓝色，视觉上框定域的范围 |
| `border-radius: 12px` | 12px | 圆角，使域外框四角圆润 |
| `padding: 12px 16px` | 上下12px 左右16px | 域内容与边框的间距 |
| `box-sizing: border-box` | border-box | padding 和 border 包含在 width/height 内 |

##### 2.4 `.domain-frame` — 域内容容器

```css
.domain-frame {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `width: 100%` / `height: 100%` | 100% | 填满父容器（`.domain-frame-wrapper` 减去 padding 后的空间） |
| `display: flex` | flex | 启用 flexbox |
| `flex-direction: column` | column | 纵向排列子元素：标题在上，列容器在下 |
| `align-items: stretch` | stretch | 子元素横向拉伸填满宽度 |

##### 2.5 `.domain-title` — 域标题

```css
.domain-title {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  color: #2C3E50;
  margin-bottom: 8px;
  flex-shrink: 0;
  font-family: "Microsoft YaHei", sans-serif;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `text-align: center` | center | 标题文字水平居中 |
| `font-size: 20px` | 20px | 字号，比组标题（14px）大，体现层级 |
| `font-weight: bold` | bold | 加粗 |
| `color: #2C3E50` | 深蓝 | 与域边框同色，视觉统一 |
| `margin-bottom: 8px` | 8px | 标题与下方列容器的间距 |
| `flex-shrink: 0` | 0 | 禁止收缩，标题始终完整显示 |
| `font-family` | Microsoft YaHei | 使用微软雅黑，确保 CJK 字符渲染正确 |

##### 2.6 `.columns` — 列容器

```css
.columns {
  display: flex !important;
  flex-direction: row;
  align-items: flex-start;
  gap: 44px;
  width: 100%;
  flex: 0;
  box-sizing: border-box;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `display: flex !important` | flex | 强制 flex 布局，`!important` 防止 Marp 主题覆盖 |
| `flex-direction: row` | row | 列横向排列（从左到右） |
| `align-items: flex-start` | flex-start | 各列顶部对齐，不拉伸到等高（各列高度独立） |
| `gap: 44px` | 44px | 列与列之间的间距 |
| `width: 100%` | 100% | 撑满父容器宽度 |
| `flex: 0` | 0 | 不参与 flex 分配，固定尺寸 |

##### 2.7 `.column` — 单列

```css
.column {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `display: flex` | flex | 启用 flexbox |
| `flex-direction: column` | column | 列内各组纵向排列 |
| `gap: 4px` | 4px | 组与组之间的间距 |
| `flex: 1` | 1 | 等宽分配，所有列平分容器宽度 |
| `min-width: 0` | 0 | 允许列宽度缩小到 0，防止 flex 溢出 |

##### 2.8 `.group` — 应用组容器

```css
.group {
  background: #E0E0E0;
  border: 1.5px solid #BDBDBD;
  border-radius: 6px;
  padding: 4px;
  display: flex !important;
  flex-direction: column;
  box-sizing: border-box;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `background: #E0E0E0` | 浅灰色 | 组的背景色，与域背景（#F0F4F8）区分 |
| `border: 1.5px solid #BDBDBD` | 灰色实线 | 组边框，比域边框细，体现层级 |
| `border-radius: 6px` | 6px | 圆角 |
| `padding: 4px` | 4px | 组内容与边框的间距 |
| `display: flex !important` | flex | 强制 flex 布局 |
| `flex-direction: column` | column | 标题在上，模块网格在下 |

##### 2.9 `.group-header` — 应用组标题栏

```css
.group-header {
  background: #1A73E8;
  color: white;
  text-align: center;
  font-size: 14px;
  font-weight: bold;
  padding: 5px 8px;
  border-radius: 4px;
  margin-bottom: 4px;
  flex-shrink: 0;
  font-family: "Microsoft YaHei", sans-serif;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `background: #1A73E8` | 蓝色 | 组标题栏背景色，鲜明醒目，标识每个组的名称 |
| `color: white` | 白色 | 标题文字颜色，与蓝色背景形成高对比 |
| `text-align: center` | center | 居中对齐 |
| `font-size: 14px` | 14px | 字号，小于域标题（20px） |
| `font-weight: bold` | bold | 加粗 |
| `padding: 5px 8px` | 上下5px 左右8px | 标题栏内边距 |
| `border-radius: 4px` | 4px | 小圆角 |
| `margin-bottom: 4px` | 4px | 与下方模块网格的间距 |
| `flex-shrink: 0` | 0 | 不收缩 |

##### 2.10 `.modules` — 模块网格容器

```css
.modules {
  display: flex !important;
  flex-direction: column !important;
  gap: 4px !important;
  padding: 2px !important;
  flex: 1;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `display: flex !important` | flex | 强制 flex 布局 |
| `flex-direction: column !important` | column | 模块行纵向排列 |
| `gap: 4px !important` | 4px | 行与行之间的间距 |
| `padding: 2px !important` | 2px | 模块网格与组边框的内边距 |
| `flex: 1` | 1 | 占满组容器剩余高度 |

##### 2.11 `.mod-row` — 模块行

```css
.mod-row {
  display: flex !important;
  justify-content: center !important;
  gap: 4px !important;
  height: 39px !important;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `display: flex !important` | flex | 强制 flex 布局 |
| `justify-content: center !important` | center | 模块格子在行内水平居中，不满一行时不拉伸 |
| `gap: 4px !important` | 4px | 模块与模块之间的间距 |
| `height: 39px !important` | 39px | 固定行高，所有行等高，保证视觉整齐 |

##### 2.12 `.module` — 单个模块格子

```css
.module {
  flex: 0 0 auto !important;
  width: var(--mod-w, 120px) !important;
  height: 100% !important;
  overflow: hidden !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: #C4D8FC;
  border: 1px solid white;
  border-radius: 3px;
  text-align: center;
  font-size: 11px;
  font-weight: 500;
  color: #1A1A1A;
  font-family: "Microsoft YaHei", sans-serif;
  line-height: 1.3;
}
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `flex: 0 0 auto !important` | 0 0 auto | 不放大、不缩小、按内容/宽度 sizing，确保固定宽度不被 flex 拉伸 |
| `width: var(--mod-w, 120px) !important` | CSS 变量 | 核心机制：通过行内 style 的 `--mod-w` 变量设置每行的模块宽度，所有同行模块等宽。默认值 120px 作为兜底 |
| `height: 100% !important` | 100% | 填满行高（39px） |
| `overflow: hidden !important` | hidden | 超出格子范围的文字被裁切，不溢出 |
| `display: flex !important` | flex | 启用 flexbox 居中文字 |
| `align-items: center !important` | center | 垂直居中文字 |
| `justify-content: center !important` | center | 水平居中文字 |
| `background: #C4D8FC` | 浅蓝色 | 模块格子背景色 |
| `border: 1px solid white` | 白色 | 白色细边框，分隔相邻模块 |
| `border-radius: 3px` | 3px | 小圆角 |
| `text-align: center` | center | 文字居中（flex 已处理，此为兜底） |
| `font-size: 11px` | 11px | 模块名字号，在小格子内保持可读 |
| `font-weight: 500` | 500 | 中等粗细 |
| `color: #1A1A1A` | 近黑色 | 文字颜色 |
| `font-family` | Microsoft YaHei | CJK 字体 |
| `line-height: 1.3` | 1.3 | 行高，控制多行文字的行间距 |

---

### 二、HTML 正文区域

Frontmatter 之后、第二个 `---` 之后的部分是 HTML 正文，由 Marp 渲染到 slide 中。

#### 2.1 Marp 注释指令

```html
<!-- _paginate: false -->
<!-- _class: treemap-slide -->
```

| 指令 | 说明 |
|------|------|
| `<!-- _paginate: false -->` | Marp 的指令语法，在此 slide 关闭页码（与 frontmatter 中的全局设置一致） |
| `<!-- _class: treemap-slide -->` | 给当前 `<section>` 添加 CSS 类名 `treemap-slide`，可用于针对性样式覆盖 |

#### 2.2 HTML 结构层级

```html
<div class="treemap">                          <!-- 第1层：Treemap 容器，铺满 slide -->
  <div class="domain-frame-wrapper">           <!-- 第2层：域外框，带边框和背景 -->
    <div class="domain-frame">                 <!-- 第3层：域内容容器 -->
      <div class="domain-title">纪检监察域</div>  <!-- 域标题文字 -->
      <div class="columns">                    <!-- 第4层：列容器 -->
        <div class="column">                   <!-- 第5层：单列 -->
          <div class="group">                  <!-- 第6层：应用组 -->
            <div class="group-header">数字办案应用</div>  <!-- 组标题栏 -->
            <div class="modules">              <!-- 第7层：模块网格 -->
              <div class="mod-row" style="--mod-w:188px">  <!-- 模块行，设置格子宽度 -->
                <div class="module">业务审<br>批流配置</div>  <!-- 单个模块格子 -->
                <div class="module">党风政风</div>
                <div class="module">办结案件<br>证据管理</div>
              </div>
              <!-- 更多 mod-row ... -->
            </div>
          </div>
        </div>
        <!-- 更多 column ... -->
      </div>
    </div>
  </div>
</div>
```

#### 2.3 各层级说明

| 层级 | class | 作用 | 生成逻辑 |
|------|-------|------|----------|
| 1 | `.treemap` | 最外层容器，绝对定位铺满 slide | 固定输出，每个 slide 一个 |
| 2 | `.domain-frame-wrapper` | 域外框，提供背景色和边框 | 固定输出，每个 slide 一个 |
| 3 | `.domain-frame` | 域内容 flex 容器，纵向排列标题和列 | 固定输出 |
| — | `.domain-title` | 域名称标题，取自 Excel B 列 | `data_loader` 返回的 `domain_name` |
| 4 | `.columns` | 列容器，横向排列各列 | 固定输出 |
| 5 | `.column` | 单列，纵向排列各组 | 列数由 `compute_optimal_column_count` 或固定 mpr 路径决定 |
| 6 | `.group` | 应用组容器，包含标题和模块 | 组数由 Excel D 列去重决定 |
| — | `.group-header` | 组名称标题栏 | 取自 Excel D 列 |
| 7 | `.modules` | 模块网格，纵向排列各行 | 固定输出 |
| 8 | `.mod-row` | 一行模块，横向排列 | 行数 = ceil(组模块数 / mpr) |
| — | 行内 `style="--mod-w:NNNpx"` | 设置该行所有模块格子的宽度 | 由 `compute_modules_per_row` 计算 mpr，再由 `MODULE_W * scale + gap` 得出像素值 |
| 9 | `.module` | 单个模块格子 | 取自 Excel G 列 |
| — | `.module` 内的 `<br>` | 文字换行 | 由 `_wrap_text` 函数按 CJK 字符规则自动插入 |
| — | `.module-empty` | 空白填充格子 | 当最后一行模块数 < mpr 时生成，防止 flex 拉伸（本例未出现） |

#### 2.4 `--mod-w` CSS 变量机制

这是模块格子固定宽度的核心机制：

```html
<div class="mod-row" style="--mod-w:188px">
  <div class="module">业务审批流配置</div>
  <div class="module">党风政风</div>
  <div class="module">办结案件证据管理</div>
</div>
```

- 同一行的所有 `.module` 共享同一个 `--mod-w` 值，确保等宽
- 不同行可能有不同的 `--mod-w` 值（取决于每组的 mpr 计算结果）
- `.module` 的 CSS 中 `width: var(--mod-w, 120px)` 引用该变量
- `flex: 0 0 auto` 确保格子不被拉伸，配合 `justify-content: center` 实现不满一行时居中

#### 2.5 `<br>` 换行机制

`_wrap_text` 函数对长模块名自动插入 `<br>`：

```python
# 示例输入：业务审批流配置（6个CJK字符）
# _wrap_text 处理后：业务审<br>批流配置

# 示例输入：党风政风（4个CJK字符，<= 阈值）
# _wrap_text 处理后：党风政风（不换行）
```

换行策略基于 CJK 字符计数，当模块名超过一定长度时在合适位置断行，确保文字在格子内可读。
