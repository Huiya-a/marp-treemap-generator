# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Marp Treemap Generator — reads application architecture Excel data and generates Marp-compatible Markdown files that render as treemap rectangle diagrams (one slide per domain). Output can be converted to PPTX via Marp CLI.

## Commands

```bash
# Install dependencies
pip install openpyxl numpy

# Install Marp CLI (for PPT conversion)
npm install -g @marp-team/marp-cli

# Generate Markdown from all Excel files in data/
python generate_treemap_md.py

# Process a single file (prefix or contains match)
python generate_treemap_md.py 03
python generate_treemap_md.py 纪检监察

# Convert output to PPTX
marp output/*.md --pptx
```

## Architecture

**Data flow:** Excel → `data_loader` → `layout` → HTML generation → Marp Markdown → PPTX

- **`generate_treemap_md.py`** — Main entry point. Orchestrates loading, layout, HTML rendering, and file output. Contains `_wrap_text` (CJK-aware line breaking) and `_compute_structure` (delegates to layout, returns semantic columns + scale).
- **`src/config.py`** — All layout constants: canvas size (`13.33×7.5` natural units), module/group dimensions, gaps, colors, and the `ADJUST_MPR` toggle. `TARGET_RATIO` = 16/9.
- **`src/data_loader.py`** — Reads Excel files. Looks for a sheet containing "应用模块清单", falls back to second sheet. Row 3+: B=domain, D=group, G=module. Returns `(domain_name, {group: [modules]})`.
- **`src/layout.py`** — Core layout engine. Two code paths by group count:
  - **≥6 groups:** `_layout_many_groups` — fixed MPR=3, greedy row-filling with target row counts (10→5)
  - **<6 groups:** `compute_optimal_column_count` + `_assign_groups_to_columns` — dynamic column count (2–4), balances module count + visual rows across columns, optional `_adjust_mpr_for_balance`

## Excel Data Format

- Sheet name must contain "应用模块清单" (or falls back to second sheet)
- Data starts at row 3
- B column: application domain name (used as slide title)
- D column: application group name
- G column: first-level module name

## Key Layout Concepts

- All dimensions in `config.py` are in "natural" units; the layout engine computes a uniform `scale` factor to fit the Marp slide canvas.
- `modules_per_row` (mpr) is computed per group via `compute_modules_per_row`, targeting a column/row ratio ≈ 1.5.
- `_pack_groups_into_rows` packs groups within a column into horizontal rows, constrained by width and row-count consistency.
- Colors are defined in `config.py` and injected into the Marp frontmatter CSS in `generate_marp_md.py`.

### Key Configuration Parameters (`src/config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CANVAS_W` / `CANVAS_H` | 13.33 / 7.5 | Natural unit canvas size |
| `CANVAS_W_PX` / `CANVAS_H_PX` | 1280 / 720 | Marp pixel dimensions |
| `MODULE_W` / `MODULE_H` | 1.5 / 0.5 | Module natural dimensions |
| `COL_GAP` / `ROW_GAP` | 0.4 / 0.25 | Column/row gaps (natural units) |
| `ADJUST_MPR` | True | Enable mpr balance adjustment |

### Color Scheme

| Element | Color |
|---------|-------|
| Domain border | `#2C3E50` |
| Domain background | `#F0F4F8` |
| Group background | `#E0E0E0` |
| Group header | `#1A73E8` |
| Module background | `#C4D8FC` |

## 当前稳定版面状态（2026-06-02 确认）

版面已调试到接近期望形态，后续调整必须遵守以下约束，**不可破坏现有大体轮廓框架**。

### 已稳定的核心结构（不可改动）

1. **整体布局层级**：`section → .treemap → .domain-frame-wrapper → .domain-frame → .domain-title + .columns → .column → .group → .group-header + .modules → .mod-row → .module`
2. **模块格子为固定宽度矩形**：通过 CSS 变量 `--mod-w` 控制，不满一行时 `justify-content: center` 居中显示，**不拉伸填满整行**
3. **列分配算法**：`_assign_groups_to_columns` 使用 `score = module_dev + vr_dev²`（行数偏差平方惩罚）平衡视觉高度
4. **两套布局路径**：组数 < 6 用动态列数 + 平衡评分；≥ 6 用固定 mpr=3 贪心填充
5. **Marp CSS 约束**：section 必须 `display: block`；treemap 必须 `position: absolute`；模块用 flexbox 不用 table

### 可安全调整的范围（不影响整体轮廓）

- `src/config.py` 中的**颜色值**（GROUP_BG、MODULE_BG_COLOR 等）
- `src/config.py` 中的**间距微调**（COL_GAP、ROW_GAP、OUTER_PAD 等，幅度 ≤ 20%）
- `_wrap_text` 中的**换行策略**（分隔符列表、断行位置偏好）
- CSS 中的**字体大小、行高、圆角、边框宽度**
- `compute_modules_per_row` 中的**目标比值**（当前 1.5，可在 1.2~1.8 范围调整）
- `_assign_groups_to_columns` 中的**评分权重**（当前 module_dev + vr_dev²，权重可微调）

### 禁止改动的部分（会破坏整体框架）

- 模块格子的固定宽度机制（`--mod-w` CSS 变量 + `flex: 0 0 auto`）
- `justify-content: center` 的居中策略（改为其他对齐方式会导致版面错乱）
- section / .treemap 的定位方式（`position: absolute` + `display: block`）
- `.column` 的 `flex: 1` 等宽分配
- 两套布局路径的切换逻辑（组数 6 为分界）
- Marp frontmatter 的基本结构（`marp: true` + `style: |` 块）

### 调整后的验证流程

每次改动后必须执行：
```bash
python generate_treemap_md.py          # 重新生成
marp output/*.md --images png --allow-local-files  # 生成图片
# 逐张检查 4 张图，确认：
# 1. 模块格子大小一致、居中正确
# 2. 列高基本平衡
# 3. 文字可读、换行合理
# 4. 无溢出或裁切
```

## Marp CSS Pitfalls

Marp wraps all content in a `<section>` element with its own flex layout (`display: flex; flex-direction: column`). Key rules to avoid layout breakage:

- **Override `section`**: Must set `section { display: block; position: relative; }` in the style block, otherwise the default flex-column behavior forces content into a single vertical column.
- **`.treemap` fill the slide**: Use `position: absolute; top/left/right/bottom: 0` on `.treemap` to force it to fill the entire section. The section must be `position: relative`.
- **CSS Grid doesn't work**: Marp's default theme overrides `display: grid` on child elements. Use `<div>` with flexbox instead.
- **Module grid uses flexbox, not `<table>`**: Marp's SVG wrapper forces `border-collapse: collapse` on tables, making `height`/`max-height` on `<td>` unreliable. The module grid uses `<div>` flexbox instead (`.modules > .mod-row > .module`). Each `.mod-row` has a fixed `height`, and `.module` uses inline `width` (calculated per group from mpr). Empty `.module-empty` cells fill incomplete last rows to prevent stretching.
- **`.column` flex**: Must use `flex: 1 1 0` — `flex: 0 0 auto` doesn't work in Marp v4.4.0.
- **`!important` partially stripped**: Marp's CSS processing strips `!important` from some properties (e.g., `border-collapse`, `border-spacing`) but not others (e.g., `width`, `display`). Don't rely on `!important` for all properties.
- **Output filenames**: Spaces in filenames break Marp CLI. The generator replaces spaces with underscores (`safe_stem`).
- **Marp frontmatter `style` block**: Uses double braces `{{` / `}}` for Python f-string escaping.
