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
