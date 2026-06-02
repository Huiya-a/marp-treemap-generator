# -*- coding: utf-8 -*-
"""
Marp Treemap Generator — 主入口

读取 Excel 数据，生成 Marp 兼容的 Markdown 文件。
输出的 MD 文件可通过 marp CLI 转换为 PPTX/PNG。

数据流: Excel → data_loader → layout → HTML 渲染 → Marp Markdown

用法:
    python generate_treemap_md.py          # 处理 data/ 下所有 Excel
    python generate_treemap_md.py 03       # 处理文件名匹配 "03" 的 Excel
    python generate_treemap_md.py 纪检监察  # 处理文件名包含 "纪检监察" 的 Excel
"""

import os
import sys

from src.data_loader import load_data_from_excel
from src.layout import (
    treemap_layout, compute_modules_per_row, compute_group_size,
    _layout_many_groups, _assign_groups_to_columns, _adjust_mpr_for_balance,
    _pack_groups_into_rows, compute_optimal_column_count,
    _raw_group_size, _col_height,
)
from src.config import (
    MODULE_W, MODULE_H, MODULE_GAP_X, MODULE_GAP_Y,
    HEADER_H, HEADER_GAP, GROUP_PAD_BOTTOM, GROUP_PAD_X,
    COL_GAP, ROW_GAP, TARGET_RATIO, ADJUST_MPR,
    GROUP_BG, GROUP_BORDER, GROUP_HEADER_COLOR, MODULE_BG_COLOR,
    MODULE_FONT_SIZE, GROUP_HEADER_FONT_SIZE,
)


# ============================================================
# 文本处理
# ============================================================

def _wrap_text(mod_name):
    """
    CJK 智能换行：在模块名称中插入 <br> 标签。

    策略:
    - 长度 ≤ 6: 不换行
    - 中文为主: 在中文分隔符（括号、顿号、破折号等）处断行
    - 英文为主: 在单词边界处断行（不拆开单词）

    Args:
        mod_name: 模块名称字符串

    Returns:
        插入 <br> 后的字符串
    """
    if len(mod_name) <= 6:
        return mod_name

    mid = len(mod_name) // 2

    # 英文单词: 在中点附近寻找单词边界
    if mod_name[mid].isalpha() and mod_name[mid].isascii():
        # 向左找到单词开头
        word_start = mid
        while word_start > 0 and mod_name[word_start - 1].isalpha() and mod_name[word_start - 1].isascii():
            word_start -= 1
        # 向右找到单词结尾
        word_end = mid
        while word_end < len(mod_name) - 1 and mod_name[word_end + 1].isalpha() and mod_name[word_end + 1].isascii():
            word_end += 1
        # 选择断开后两半长度更均衡的位置
        break_before = abs(word_start - (len(mod_name) - word_start))
        break_after = abs((word_end + 1) - (len(mod_name) - word_end - 1))
        mid = word_start if break_before <= break_after else word_end + 1
    else:
        # 中文: 在中点附近寻找分隔符
        # 向右找分隔符
        for i in range(mid, min(mid + 3, len(mod_name))):
            if mod_name[i] in '（、-—/':
                mid = i
                break
        # 向左找分隔符
        for i in range(mid, max(mid - 3, 0), -1):
            if mod_name[i] in '）、-—/':
                mid = i + 1
                break

    return mod_name[:mid] + '<br>' + mod_name[mid:]


# ============================================================
# 布局计算（CSS 像素）
# ============================================================

def _compute_structure(data):
    """
    计算语义布局结构，将自然单位转换为 CSS 像素尺寸。

    采用两遍布局:
    1. 第一遍: 用默认画布计算内容边界
    2. 第二遍: 根据内容自适应调整画布尺寸，重新布局

    Args:
        data: {group_name: [module_name, ...]}

    Returns:
        dict 包含:
        - domain_columns: 各列的组信息（用于生成 HTML）
        - scale: 自然单位到像素的缩放因子
        - module_font / header_font: 字体大小（px）
        - row_h: 模块行高（px）
        - domain_frame_w / domain_frame_h: 外框尺寸（px）
        - col_inner_w: 每列内容区宽度（px）
        - gap_px: 列间距（px）
        - row_gap_px: 行间距（px）
    """
    from src.config import (
        CANVAS_W, CANVAS_H, CANVAS_W_PX, CANVAS_H_PX,
        OUTER_PAD_X, OUTER_PAD_TOP, OUTER_PAD_BOTTOM,
        DOMAIN_PAD, TITLE_H, TARGET_RATIO,
    )

    def _run_layout(canvas_w, canvas_h):
        """
        内部函数: 执行一次完整布局，返回列分组和缩放信息。
        """
        usable_w = canvas_w - 2 * OUTER_PAD_X
        usable_h = canvas_h - OUTER_PAD_TOP - OUTER_PAD_BOTTOM

        # 根据分组数量选择布局策略
        if len(data) >= 6:
            col_groups = _layout_many_groups(data)
        else:
            group_info = []
            for group_name, modules in data.items():
                n = len(modules)
                mpr = compute_modules_per_row(n)
                gw, gh = compute_group_size(n, mpr)
                group_info.append((group_name, modules, gw, gh, mpr))

            ncols = compute_optimal_column_count(group_info)
            col_groups, _ = _assign_groups_to_columns(group_info, ncols)

            if ADJUST_MPR:
                col_groups = _adjust_mpr_for_balance(col_groups)

        # 计算每列高度
        ncols = len(col_groups)
        col_heights = []
        for cg in col_groups:
            c_max_gw = max(gw for _, _, gw, _, _ in cg) if cg else 1
            rows, rh = _pack_groups_into_rows(cg, c_max_gw)
            h = sum(rh) + ROW_GAP * max(0, len(rows) - 1)
            col_heights.append(h)

        # 计算缩放因子
        col_max_gw = []
        for cg in col_groups:
            if cg:
                col_max_gw.append(max(gw for _, _, gw, _, _ in cg))
            else:
                col_max_gw.append(1)
        max_col_h = max(col_heights) if col_heights and max(col_heights) > 0 else 1
        total_w = sum(col_max_gw) + (ncols - 1) * COL_GAP
        scale_x = usable_w / total_w
        scale_y = usable_h / max_col_h
        scale = min(scale_x, scale_y)

        # 计算每列的水平位置
        scaled_gap = COL_GAP * scale
        col_w = [gw * scale for gw in col_max_gw]
        total_scaled_w = sum(col_w) + (ncols - 1) * scaled_gap
        start_x = (canvas_w - total_scaled_w) / 2
        col_x = []
        cx = start_x
        for w in col_w:
            col_x.append(cx)
            cx += w + scaled_gap

        # 内容边界
        min_x = col_x[0] if col_x else 0
        max_x = (col_x[-1] + col_w[-1]) if col_x else canvas_w
        min_y = OUTER_PAD_TOP
        max_y = OUTER_PAD_TOP + max_col_h * scale

        return col_groups, col_heights, col_max_gw, scale, ncols, (min_x, min_y, max_x, max_y)

    # ---- 第一遍: 用默认画布计算内容边界 ----
    _, _, _, _, _, content_bbox = _run_layout(CANVAS_W, CANVAS_H)
    cx_min, cy_min, cx_max, cy_max = content_bbox

    # ---- 自适应画布尺寸 ----
    # 根据内容实际大小调整画布，避免浪费空间
    domain_w = cx_max - cx_min + 2 * DOMAIN_PAD
    domain_h = cy_max - cy_min + 2 * DOMAIN_PAD + TITLE_H
    canvas_w = domain_w + 2 * OUTER_PAD_X
    canvas_h = domain_h + OUTER_PAD_TOP + OUTER_PAD_BOTTOM
    # 确保不小于 16:9 目标比
    if canvas_w / canvas_h < TARGET_RATIO:
        canvas_w = canvas_h * TARGET_RATIO

    # ---- 第二遍: 用正确画布尺寸重新布局 ----
    col_groups, col_heights, col_max_gw, scale, ncols, content_bbox2 = _run_layout(canvas_w, canvas_h)

    # ============================================================
    # 以下转为 CSS 像素单位计算
    # ============================================================
    px_per_unit = CANVAS_W_PX / canvas_w  # 自然单位 → 像素的转换因子

    # 字体大小（固定值，与 matplotlib 渲染效果一致）
    module_font_px = MODULE_FONT_SIZE       # 11px
    header_font_px = GROUP_HEADER_FONT_SIZE # 14px

    # 模块行高: 确保能容纳 2 行文本
    line_h = module_font_px * 1.4
    row_h = max(module_font_px + 12, 2 * line_h + 8)

    # ---- CSS 尺寸常量 ----
    css_group_header_h = max(header_font_px + 10, 30)  # 组标题栏高度
    css_row_gap = 4     # 模块行间距
    css_group_pad = 8   # 组内边距 (4px top + 4px bottom)
    css_group_gap = ROW_GAP * scale * px_per_unit  # 组间垂直间距

    # ---- 计算每列实际像素高度 ----
    col_heights_px = []
    for cg in col_groups:
        effective_h = 0
        for gi, (group_name, modules, gw, gh, mpr) in enumerate(cg):
            n = len(modules)
            n_rows = (n + mpr - 1) // mpr
            group_css_h = (css_group_header_h
                           + n_rows * row_h
                           + max(0, n_rows - 1) * css_row_gap
                           + css_group_pad)
            effective_h += group_css_h
            if gi < len(cg) - 1:
                effective_h += css_group_gap
        col_heights_px.append(effective_h)

    max_col_h_px = max(col_heights_px) if col_heights_px else 1

    # ---- 可用像素空间 ----
    available_w = CANVAS_W_PX - 2 * 20  # section padding (20px × 2)
    available_h = CANVAS_H_PX - 2 * 20

    # ---- domain-frame 内容区高度 ----
    title_area_h = header_font_px + 14  # 标题字体 + margin
    domain_pad_px = DOMAIN_PAD * px_per_unit
    domain_frame_inner_h = title_area_h + max_col_h_px + 2 * domain_pad_px

    # ---- wrapper 尺寸 ----
    # wrapper = 最外层的圆角矩形框（含 padding 和 border）
    total_natural_w = sum(col_max_gw) + (ncols - 1) * COL_GAP  # 自然单位总列宽
    total_content_px = total_natural_w * scale * px_per_unit     # 像素总列宽

    wrapper_content_h = domain_frame_inner_h
    wrapper_outer_h = wrapper_content_h + 2 * 12 + 2 * 3  # + padding(12) + border(3)
    if wrapper_outer_h > available_h:
        wrapper_outer_h = available_h  # 不超过可用高度

    # wrapper 宽度 = 内容宽度 + padding + border，不超过可用宽度
    wrapper_outer_w = min(total_content_px + 2 * 16 + 2 * 3, available_w)

    # 内容区宽度 = wrapper 宽度 - padding - border
    frame_inner_w = wrapper_outer_w - 2 * 16 - 2 * 3

    # ---- 列间距（像素）----
    # 用自然单位 gap 与总宽度的比例，映射到 frame 像素宽度
    gap_px = COL_GAP * frame_inner_w / total_natural_w if total_natural_w > 0 else 0
    total_cols_w = frame_inner_w - (ncols - 1) * gap_px
    col_inner_w = total_cols_w / ncols  # 每列内容区宽度

    # ---- 构建返回数据 ----
    result_columns = []
    for cg in col_groups:
        col_data = []
        for group_name, modules, gw, gh, mpr in cg:
            col_data.append({
                'name': group_name,
                'modules': modules,
                'mpr': mpr,
                'gh': gh,
                'col_w': col_inner_w,  # 列内容区宽度，用于计算模块固定宽度
            })
        result_columns.append(col_data)

    return {
        'domain_columns': result_columns,
        'scale': scale,
        'module_font': module_font_px,
        'header_font': header_font_px,
        'row_h': row_h,
        'domain_frame_w': wrapper_outer_w,
        'domain_frame_h': wrapper_outer_h,
        'col_inner_w': col_inner_w,
        'gap_px': gap_px,
        'row_gap_px': css_row_gap,
    }


# ============================================================
# HTML 渲染
# ============================================================

def _render_group_html(group_data, col_inner_w=None):
    """
    渲染单个组的 HTML。

    模块格子为固定宽度矩形，不满一行时居中显示，不拉伸填充。

    结构:
    <div class="group">
      <div class="group-header">组名</div>
      <div class="modules">
        <div class="mod-row">
          <div class="module" style="width: 136px">模块1</div>
          <div class="module" style="width: 136px">模块2</div>
          ...
        </div>
        ...
      </div>
    </div>

    Args:
        group_data: dict with keys 'name', 'modules', 'mpr', 'col_w'
        col_inner_w: 列内容区宽度（备用，优先使用 group_data['col_w']）

    Returns:
        HTML 字符串
    """
    name = group_data['name']
    modules = group_data['modules']
    mpr = group_data['mpr']

    # 获取列宽度，计算模块固定宽度
    col_w = group_data.get('col_w', col_inner_w)
    if col_w and mpr > 0:
        # 模块宽度 = (列宽 - 左右 padding - 模块间间距) / 每行模块数
        mod_w = (col_w - 2 * 4 - (mpr - 1) * 4) / mpr
        mod_w_px = f'{mod_w:.0f}px'
    else:
        mod_w_px = None

    n_modules = len(modules)
    n_rows = (n_modules + mpr - 1) // mpr

    rows_html = ''
    for r in range(n_rows):
        cells = ''
        for c in range(mpr):
            idx = r * mpr + c
            if idx < n_modules:
                display = _wrap_text(modules[idx])
                cells += f'<div class="module">{display}</div>'
        # 在 mod-row 上设置 CSS 变量 --mod-w，控制模块固定宽度
        style = f' style="--mod-w:{mod_w_px}"' if mod_w_px else ''
        rows_html += f'<div class="mod-row"{style}>{cells}</div>\n'

    return f'''<div class="group">
  <div class="group-header">{name}</div>
  <div class="modules">
{rows_html}  </div>
</div>'''


# ============================================================
# Marp Markdown 生成
# ============================================================

def generate_marp_md(domain_name, data, output_path):
    """
    生成完整的 Marp Markdown 文件。

    文件结构:
    1. YAML frontmatter (marp 配置 + CSS 样式)
    2. HTML 内容 (treemap 结构)

    Args:
        domain_name: 应用域名称（如 "纪检监察域"）
        data: {group_name: [module_name, ...]}
        output_path: 输出 .md 文件路径
    """
    # 计算布局结构
    structure = _compute_structure(data)
    columns = structure['domain_columns']
    scale = structure['scale']
    module_font = structure['module_font']
    header_font = structure['header_font']
    domain_frame_w = structure['domain_frame_w']
    domain_frame_h = structure['domain_frame_h']
    row_h = structure['row_h']
    gap_px = structure['gap_px']
    row_gap_px = structure['row_gap_px']

    # 生成每列的 HTML
    columns_html = ''
    for ci, col in enumerate(columns):
        groups_html = ''
        for g in col:
            groups_html += _render_group_html(g) + '\n'
        columns_html += f'<div class="column">\n{groups_html}</div>\n'

    # 组装完整的 Marp Markdown
    # 注意: CSS 中使用双大括号 {{ }} 是因为 Python f-string 转义
    md = f'''---
marp: true
theme: default
paginate: false
backgroundColor: "#FAFBFC"
style: |
  section {{
    display: block !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    position: relative !important;
    box-sizing: border-box;
  }}
  .treemap {{
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
  }}
  .domain-frame-wrapper {{
    width: {domain_frame_w:.0f}px;
    height: 100%;
    flex-shrink: 0;
    background: #F0F4F8;
    border: 3px solid #2C3E50;
    border-radius: 12px;
    padding: 12px 16px;
    box-sizing: border-box;
  }}
  .domain-frame {{
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }}
  .domain-title {{
    text-align: center;
    font-size: {header_font + 6:.0f}px;
    font-weight: bold;
    color: #2C3E50;
    margin-bottom: 8px;
    flex-shrink: 0;
    font-family: "Microsoft YaHei", sans-serif;
  }}
  .columns {{
    display: flex !important;
    flex-direction: row;
    align-items: flex-start;
    gap: {gap_px:.0f}px;
    width: 100%;
    flex: 0;
    box-sizing: border-box;
  }}
  .column {{
    display: flex;
    flex-direction: column;
    gap: {row_gap_px:.0f}px;
    flex: 1;
    min-width: 0;
  }}
  .group {{
    background: {GROUP_BG};
    border: 1.5px solid {GROUP_BORDER};
    border-radius: 6px;
    padding: 4px;
    display: flex !important;
    flex-direction: column;
    box-sizing: border-box;
  }}
  .group-header {{
    background: {GROUP_HEADER_COLOR};
    color: white;
    text-align: center;
    font-size: {header_font:.0f}px;
    font-weight: bold;
    padding: 5px 8px;
    border-radius: 4px;
    margin-bottom: 4px;
    flex-shrink: 0;
    font-family: "Microsoft YaHei", sans-serif;
  }}
  .modules {{
    display: flex !important;
    flex-direction: column !important;
    gap: {row_gap_px:.0f}px !important;
    padding: 2px !important;
    flex: 1;
  }}
  .mod-row {{
    display: flex !important;
    justify-content: center !important;
    gap: 4px !important;
    height: {row_h:.0f}px !important;
  }}
  .module {{
    flex: 0 0 auto !important;
    width: var(--mod-w, 120px) !important;
    height: 100% !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: {MODULE_BG_COLOR};
    border: 1px solid white;
    border-radius: 3px;
    text-align: center;
    font-size: {module_font:.0f}px;
    font-weight: 500;
    color: #1A1A1A;
    font-family: "Microsoft YaHei", sans-serif;
    line-height: 1.3;
  }}
---

<!-- _paginate: false -->
<!-- _class: treemap-slide -->

<div class="treemap">
<div class="domain-frame-wrapper">
<div class="domain-frame">
<div class="domain-title">{domain_name}</div>
<div class="columns">
{columns_html}</div>
</div>
</div>
</div>
'''

    # 写入文件
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'Marp Markdown saved to: {output_path}')


# ============================================================
# 文件查找
# ============================================================

def _find_excel(data_dir, input_name):
    """
    在 data_dir 中按前缀/包含匹配查找 Excel 文件。

    查找优先级:
    1. 前缀匹配: 文件名以 input_name 开头
    2. 包含匹配: 文件名包含 input_name

    Args:
        data_dir: 数据目录路径
        input_name: 用户输入的搜索关键词

    Returns:
        (file_path, display_name) 或 (None, match_list)
    """
    excel_files = [f for f in os.listdir(data_dir)
                   if f.endswith('.xlsx') and not f.startswith('~')]

    # 优先: 前缀匹配
    prefix_matches = [f for f in excel_files if f.startswith(input_name)]
    if len(prefix_matches) == 1:
        return os.path.join(data_dir, prefix_matches[0]), prefix_matches[0]
    if len(prefix_matches) > 1:
        return None, prefix_matches

    # 次选: 包含匹配
    contain_matches = [f for f in excel_files if input_name in f]
    if len(contain_matches) == 1:
        return os.path.join(data_dir, contain_matches[0]), contain_matches[0]
    if len(contain_matches) > 1:
        return None, contain_matches

    return None, []


# ============================================================
# 主函数
# ============================================================

def main():
    """
    主入口: 解析命令行参数，遍历 Excel 文件，生成 Marp Markdown。

    支持两种模式:
    1. 指定文件名: python generate_treemap_md.py 03
    2. 处理全部: python generate_treemap_md.py
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    excel_files_to_process = []

    if len(sys.argv) > 1:
        # 指定文件名模式: 按前缀/包含匹配查找
        input_name = sys.argv[1]

        # 尝试直接路径
        excel_path = os.path.join(data_dir, input_name)
        if not os.path.exists(excel_path):
            excel_path = input_name
        if not os.path.exists(excel_path):
            # 模糊匹配
            if os.path.exists(data_dir):
                result, info = _find_excel(data_dir, input_name)
                if result is None and isinstance(info, list) and len(info) > 0:
                    print(f'Multiple matches found for "{input_name}":')
                    for i, f in enumerate(info, 1):
                        print(f'  {i}. {f}')
                    return
                excel_path = result
                if result:
                    print(f'Matched file: {info}')
            if not excel_path or not os.path.exists(excel_path):
                print(f'Error: file not found: {input_name}')
                return
        excel_files_to_process.append(excel_path)
    else:
        # 处理全部模式: 扫描 data/ 目录下所有 .xlsx 文件
        if os.path.exists(data_dir):
            excel_files = sorted([f for f in os.listdir(data_dir)
                                  if f.endswith('.xlsx') and not f.startswith('~')])
        else:
            excel_files = []
        excel_files_to_process = [os.path.join(data_dir, f) for f in excel_files]

    if not excel_files_to_process:
        print('No Excel files found in data/')
        return

    # 逐个处理 Excel 文件
    for excel_path in excel_files_to_process:
        print(f'Processing: {os.path.basename(excel_path)}')

        # 加载数据
        domain_name, data = load_data_from_excel(excel_path)

        # 生成输出文件名（空格替换为下划线，避免 Marp CLI 报错）
        input_stem = os.path.splitext(os.path.basename(excel_path))[0]
        safe_stem = input_stem.replace(' ', '_')
        output_path = os.path.join(output_dir, f'{safe_stem}.md')

        # 打印数据摘要
        print(f'  Domain: {domain_name}')
        print(f'  Groups: {len(data)}')
        for k, v in data.items():
            print(f'    {k}: {len(v)} modules')

        # 生成 Marp Markdown
        generate_marp_md(domain_name, data, output_path)

    print(f'\nDone! Convert to PPTX with:')
    print(f'  marp {output_dir}/*.md --pptx')


if __name__ == '__main__':
    main()
