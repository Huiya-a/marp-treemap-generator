# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Marp Treemap Generator — reads application architecture Excel data and generates Marp-compatible Markdown files that render as treemap rectangle diagrams (one slide per domain). Output can be converted to PPTX/PNG via Marp CLI. Has both a CLI and a PySide6 GUI (`src/app.py`).

## Commands

```bash
# Install dependencies
pip install openpyxl numpy            # CLI mode
pip install "PySide6>=6.5.0"          # GUI mode (additional)

# Install Marp CLI (for PPT/PNG conversion)
npm install -g @marp-team/marp-cli

# CLI: Generate Markdown from all Excel files in data/
python generate_treemap_md.py

# CLI: Process a single file (prefix or contains match)
python generate_treemap_md.py 03
python generate_treemap_md.py 纪检监察

# CLI: Multi-file proportional width mode
python generate_treemap_md.py --proportional-width

# Convert output
marp output/*.md --pptx
marp output/*.md --images png --allow-local-files

# GUI: Launch graphical interface
python src/app.py
# Or use the Windows batch launcher (auto-installs PySide6 + openpyxl + numpy if missing)
启动应用.bat

# Smoke tests (no formal test suite — import-only checks)
python src/test_simple.py
python src/test_gui.py
```

## Architecture

**Data flow:** Excel → `data_loader` → `layout` → HTML generation → Marp Markdown → PPTX/PNG

### Core modules

- **`generate_treemap_md.py`** — CLI entry point + HTML rendering. `_compute_structure` runs a two-pass layout: pass 1 measures content bounding box, adjusts canvas to 16:9, pass 2 reruns with adjusted canvas. `generate_marp_md` produces the full Marp Markdown file with embedded CSS+HTML. `_wrap_text` handles CJK-aware line breaking.
- **`src/config.py`** — All layout constants in "natural units" (canvas 13.33×7.5). Uniform `scale` factor maps to 1280×720 Marp pixel canvas.
- **`src/data_loader.py`** — Reads Excel. Sheet containing "应用模块清单" (or 2nd sheet). Row 3+: B=domain, D=group, G=module. Returns `(domain_name, {group: [modules]})`.
- **`src/layout.py`** — Core layout engine (two code paths):
  - **<6 groups:** `compute_modules_per_row` → `compute_optimal_column_count` (tries 2–4 cols, scores on module imbalance + visual row imbalance + aspect ratio) → `_assign_groups_to_columns` (greedy, largest first, score = `module_dev + vr_dev²`) → `_adjust_mpr_for_balance`
  - **≥6 groups:** `_layout_many_groups` — fixed MPR=3, greedy bin-packing with target row counts (10→5)

### GUI architecture

Entry: `src/app.py` → `MainWindow` (PySide6 QMainWindow with QSplitter layout).

```
MainWindow
├── LEFT PANEL
│   ├── FileSelector (QListWidget + drag-drop + recent files via QSettings)
│   ├── FileInfoWidget (Excel metadata + data tree preview)
│   ├── ParamsPanel (7 ColorButtons, 15 spin boxes, 1 checkbox, template management)
│   ├── Generate / Cancel buttons
│   ├── Export format combo (PNG/PPTX/HTML/PNG+PPTX/PNG+HTML/All)
│   └── Progress bar
├── RIGHT PANEL
│   ├── PreviewWidget (image display + left/right navigation arrows)
│   └── Log area (QTextEdit)
└── StatusBar
```

Key GUI modules in `src/gui/`:
- `md_editor.py` — regex-based CSS editor (`_sub_in_css_blocks`, `extract_params_from_md`, `apply_params_to_md`, `apply_module_color`)
- `module_color_dialog.py` — per-module color picker dialog (uses MD5 hash of module name for CSS class `mc-{hash}`)
- `template_manager.py` — save/load parameter presets to `~/.架构图生成器/templates/`

**Signal flow:** `FileSelector.files_changed` → update `FileInfoWidget`; `ParamsPanel.params_changed` → `md_editor.apply_params_to_md()` (regex-based CSS editing, no re-layout); Generate button → `GenerateWorker(QThread)` → signals back to UI.

**Parameter adjustment mechanism:** The GUI does NOT re-run the layout algorithm for parameter tweaks. Instead, `md_editor.py` directly edits CSS values in existing `.md` files via regex replacement, scaling pixel values proportionally. This works because `config.py` values are imported via `from config import X` (bound at import time), making runtime monkey-patching ineffective for layout recalculation.

**Session-level reuse:** Generated Markdown files are cached per session (`_session_processed` set in `GenerateWorker`). If the same Excel file is re-processed within the same GUI session, the existing `.md` is reused and only parameter edits (CSS regex) are applied — no re-layout occurs. A fresh `python src/app.py` clears this cache.

**Template storage:** JSON files in `~/.架构图生成器/templates/`.

### Layout hierarchy (CSS nesting)

```
section → .treemap → .domain-frame-wrapper → .domain-frame
  → .domain-title + .columns → .column → .group
    → .group-header + .modules → .mod-row → .module
```

Modules use flexbox (`<div>`, not `<table>`). Each `.mod-row` gets inline CSS variables `--mod-w`/`--mod-h` for consistent sizing. Incomplete rows center modules via `justify-content: center` (never stretch).

## Excel Data Format

- Sheet name must contain "应用模块清单" (or falls back to second sheet)
- Data starts at row 3
- B column: application domain name (slide title)
- D column: application group name
- G column: first-level module name

## Key Configuration Parameters (`src/config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CANVAS_W` / `CANVAS_H` | 13.33 / 7.5 | Natural unit canvas size |
| `CANVAS_W_PX` / `CANVAS_H_PX` | 1280 / 720 | Marp pixel dimensions |
| `MODULE_W` / `MODULE_H` | 1.2 / 0.4 | Module natural dimensions (3:1 ratio) |
| `COL_GAP` / `ROW_GAP` | 0.2 / 0.12 | Column/row gaps (natural units) |
| `ADJUST_MPR` | True | Enable mpr balance adjustment |
| `TARGET_RATIO` | 16/9 | Target aspect ratio |

## Layout Constraints

### Stable core (do not change)

1. **Module grid:** Fixed-width rectangles via `--mod-w` CSS variable + `flex: 0 0 auto`. Incomplete rows use `justify-content: center` — never stretch to fill.
2. **Column assignment:** `_assign_groups_to_columns` uses `score = module_dev + vr_dev²` (row-count deviation squared penalty) to balance visual height.
3. **Two layout paths:** <6 groups → dynamic column count + balance scoring; ≥6 groups → fixed MPR=3 greedy bin-packing. The 6-group threshold must not change.
4. **Marp CSS constraints:** `section { display: block; position: relative }`, `.treemap { position: absolute }`, flexbox not grid/table.

### Safe to adjust

- Colors in `src/config.py` (GROUP_BG, MODULE_BG_COLOR, etc.)
- Spacing in `src/config.py` (COL_GAP, ROW_GAP, OUTER_PAD — ≤20% change)
- Line-break strategy in `_wrap_text`
- Font sizes, line heights, border radii, border widths
- MPR target ratio in `compute_modules_per_row` (current 1.5, safe range 1.2–1.8)
- Scoring weights in `_assign_groups_to_columns` (current `module_dev + vr_dev²`, minor tuning OK)

### Forbidden changes

- Module fixed-width mechanism (`--mod-w` + `flex: 0 0 auto`)
- `justify-content: center` centering strategy
- section / `.treemap` positioning (`position: absolute` + `display: block`)
- `.column` `flex: 1` equal-width distribution
- Two-path layout switching logic (6-group threshold)
- Marp frontmatter structure (`marp: true` + `style: |` block)

### Verification after changes

```bash
python generate_treemap_md.py          # regenerate
marp output/*.md --images png --allow-local-files  # generate images
# check all 4 images for:
# 1. Module boxes same size, correctly centered
# 2. Column heights roughly balanced
# 3. Text readable, line breaks reasonable
# 4. No overflow or clipping
```

## Marp CSS Pitfalls

Marp wraps all content in a `<section>` element with its own flex layout (`display: flex; flex-direction: column`). Key rules:

- **Override `section`**: Must set `section { display: block; position: relative; }`, otherwise flex-column forces single vertical column.
- **`.treemap` fill the slide**: Use `position: absolute; top/left/right/bottom: 0`. Section must be `position: relative`.
- **CSS Grid doesn't work**: Marp's default theme overrides `display: grid`. Use `<div>` with flexbox.
- **Module grid uses flexbox, not `<table>`**: Marp's SVG wrapper forces `border-collapse: collapse` on tables. Use `.modules > .mod-row > .module` flexbox. Empty `.module-empty` cells prevent row stretching.
- **`.column` flex**: Must use `flex: 1 1 0` — `flex: 0 0 auto` fails in Marp v4.4.0.
- **`!important` partially stripped**: Marp strips `!important` from some properties but not others. Don't rely on it consistently.
- **Output filenames**: Spaces break Marp CLI. Generator replaces spaces with underscores (`safe_stem`).
- **Marp frontmatter `style` block**: Uses double braces `{{` / `}}` for Python f-string escaping.

## Technical Documentation (Chinese)

- `技术文档.md` — Full technical documentation
- `技术文档-布局算法详解.md` — Layout algorithm deep-dive
- `marp-rules.md` — Marp Markdown quick reference card
