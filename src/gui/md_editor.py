# -*- coding: utf-8 -*-
"""
Markdown 文件编辑器

直接修改已生成的 Markdown 文件中的 CSS 属性值和 HTML 内联变量，
无需修改 Python 源码或 config 模块。
"""

import re


def extract_params_from_md(md_path: str) -> dict:
    """从已生成的 Markdown 文件中提取当前的 CSS 参数值

    Returns:
        dict: 包含所有可调参数的当前值
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    params = {}

    # 提取颜色
    # .group { background: #E0E0E0; ... }
    m = re.search(r'\.group\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['GROUP_BG'] = m.group(1)

    # .group { border: 1.5px solid #BDBDBD; ... }
    m = re.search(r'\.group\s*\{[^}]*border:\s*[\d.]+px\s+solid\s+(#[0-9A-Fa-f]{6})', content)
    if m:
        params['GROUP_BORDER'] = m.group(1)

    # .group-header { background: #1A73E8; ... }
    m = re.search(r'\.group-header\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['GROUP_HEADER_COLOR'] = m.group(1)

    # .module { background: #C4D8FC; ... }
    m = re.search(r'\.module\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['MODULE_BG_COLOR'] = m.group(1)

    # 提取字体大小
    # .module { font-size: 19px; ... }
    m = re.search(r'\.module\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['MODULE_FONT_SIZE_PX'] = float(m.group(1))

    # .group-header { font-size: 25px; ... }
    m = re.search(r'\.group-header\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['GROUP_HEADER_FONT_SIZE_PX'] = float(m.group(1))

    # 提取间距
    # .columns { gap: 28px; ... }
    m = re.search(r'\.columns\s*\{[^}]*gap:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['COL_GAP_PX'] = float(m.group(1))

    # .modules { gap: 5px !important; ... }
    m = re.search(r'\.modules\s*\{[^}]*gap:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['ROW_GAP_PX'] = float(m.group(1))

    # 提取模块尺寸（从第一个 mod-row 的内联变量）
    m = re.search(
        r'--mod-w:\s*(\d+(?:\.\d+)?)px.*?--mod-h:\s*(\d+(?:\.\d+)?)px.*?--mod-h-inner:\s*(\d+(?:\.\d+)?)px',
        content, re.DOTALL
    )
    if m:
        params['MOD_W_PX'] = float(m.group(1))
        params['MOD_H_PX'] = float(m.group(2))
        params['MOD_H_INNER_PX'] = float(m.group(3))

    # --- 域样式 ---
    # .domain-frame-wrapper { background: #F0F4F8; ... }
    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['DOMAIN_BG'] = m.group(1)

    # .domain-frame-wrapper { border: 3px solid #2C3E50; ... }
    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*border:\s*(\d+(?:\.\d+)?)px\s+solid\s+(#[0-9A-Fa-f]{6})', content)
    if m:
        params['DOMAIN_BORDER_WIDTH_PX'] = float(m.group(1))
        params['DOMAIN_BORDER_COLOR'] = m.group(2)

    # .domain-frame-wrapper { border-radius: 12px; ... }
    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*border-radius:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_BORDER_RADIUS_PX'] = float(m.group(1))

    # .domain-frame-wrapper { padding: 12px 16px; ... }
    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*padding:\s*(\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_PADDING_Y_PX'] = float(m.group(1))
        params['DOMAIN_PADDING_X_PX'] = float(m.group(2))

    # .domain-title { font-size: 22px; ... }
    m = re.search(r'\.domain-title\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_TITLE_FONT_SIZE_PX'] = float(m.group(1))

    # .domain-title { color: #2C3E50; ... }
    m = re.search(r'\.domain-title\s*\{[^}]*color:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['DOMAIN_TITLE_COLOR'] = m.group(1)

    # .domain-title { margin-bottom: 8px; ... }
    m = re.search(r'\.domain-title\s*\{[^}]*margin-bottom:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_TITLE_MARGIN_BOTTOM_PX'] = float(m.group(1))

    # .column { gap: 8px; ... }
    m = re.search(r'\.column\s*\{[^}]*gap:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['COLUMN_GAP_PX'] = float(m.group(1))

    # .group-header { margin-bottom: 4px; ... }
    m = re.search(r'\.group-header\s*\{[^}]*margin-bottom:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['GROUP_HEADER_MARGIN_BOTTOM_PX'] = float(m.group(1))

    # .group { border-radius: 6px; ... }
    m = re.search(r'\.group\s*\{[^}]*border-radius:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['GROUP_BORDER_RADIUS_PX'] = float(m.group(1))

    # .module { border-radius: 3px; ... }
    m = re.search(r'\.module\s*\{[^}]*border-radius:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['MODULE_BORDER_RADIUS_PX'] = float(m.group(1))

    # .module { border: 1px solid white; ... }
    m = re.search(r'\.module\s*\{[^}]*border:\s*\d+(?:\.\d+)?px\s+solid\s+(#[0-9A-Fa-f]{6}|white)', content)
    if m:
        params['MODULE_BORDER_COLOR'] = m.group(1)

    # .module { line-height: 1.3; ... }
    m = re.search(r'\.module\s*\{[^}]*line-height:\s*(\d+(?:\.\d+)?)', content)
    if m:
        params['MODULE_LINE_HEIGHT'] = float(m.group(1))

    # .module { font-family: "Microsoft YaHei", sans-serif; ... }
    m = re.search(r'\.module\s*\{[^}]*font-family:\s*([^;]+);', content)
    if m:
        params['MODULE_FONT_FAMILY'] = m.group(1).strip()

    return params


def apply_params_to_md(md_path: str, new_params: dict, original_params: dict,
                       css_baseline: dict = None) -> tuple:
    """将新的参数值写入 Markdown 文件

    通过比较 new_params 和当前 CSS 实际值计算比例，
    然后用正则替换 Markdown 中对应的 CSS/HTML 值。

    Args:
        md_path: Markdown 文件路径
        new_params: 用户在 UI 中设置的新参数值（config 参数名 -> 值）
        original_params: 首次生成时的 config 参数名 -> 值（仅用于颜色直接替换）
        css_baseline: 当前文件中 CSS 的实际值（dict），用于计算比例。
                      传入 None 时回退到用 original_params。

    Returns:
        tuple: (bool, dict) — 是否成功修改, 更新后的 css_baseline
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 从文件中提取当前 CSS 实际值作为比例计算的基准
    css_now = extract_params_from_md(md_path)
    # 合并：css_now 中有的值优先，没有的回退到 original_params
    baseline = {}
    for key in set(list(css_now.keys()) + list(original_params.keys())):
        if key in css_now:
            baseline[key] = css_now[key]
        elif key in original_params:
            baseline[key] = original_params[key]

    # --- 颜色（直接替换，不需要比例） ---
    if 'GROUP_BG' in new_params and 'GROUP_BG' in original_params:
        old_color = original_params['GROUP_BG']
        new_color = new_params['GROUP_BG']
        if old_color != new_color:
            content = re.sub(
                r'(\.group\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color,
                content
            )

    if 'GROUP_HEADER_COLOR' in new_params and 'GROUP_HEADER_COLOR' in original_params:
        old_color = original_params['GROUP_HEADER_COLOR']
        new_color = new_params['GROUP_HEADER_COLOR']
        if old_color != new_color:
            content = re.sub(
                r'(\.group-header\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color,
                content
            )

    if 'MODULE_BG_COLOR' in new_params and 'MODULE_BG_COLOR' in original_params:
        old_color = original_params['MODULE_BG_COLOR']
        new_color = new_params['MODULE_BG_COLOR']
        if old_color != new_color:
            content = re.sub(
                r'(\.module\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color,
                content
            )

    # --- 字体大小（按比例缩放） ---
    # ratio = config_new / config_old，乘以当前 CSS px 值
    # 注意：始终执行（不跳过），因为 config 值相同但 CSS 值可能因 fill_scale 不同
    if 'MODULE_FONT_SIZE' in new_params and 'MODULE_FONT_SIZE' in original_params:
        config_old = original_params['MODULE_FONT_SIZE']
        config_new = new_params['MODULE_FONT_SIZE']
        if config_old > 0:
            m = re.search(r'(\.module\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    if 'GROUP_HEADER_FONT_SIZE' in new_params and 'GROUP_HEADER_FONT_SIZE' in original_params:
        config_old = original_params['GROUP_HEADER_FONT_SIZE']
        config_new = new_params['GROUP_HEADER_FONT_SIZE']
        if config_old > 0:
            m = re.search(r'(\.group-header\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    # --- 间距（按比例缩放） ---
    if 'COL_GAP' in new_params and 'COL_GAP' in original_params:
        config_old = original_params['COL_GAP']
        config_new = new_params['COL_GAP']
        if config_old > 0:
            m = re.search(r'(\.columns\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    if 'ROW_GAP' in new_params and 'ROW_GAP' in original_params:
        config_old = original_params['ROW_GAP']
        config_new = new_params['ROW_GAP']
        if config_old > 0:
            m = re.search(r'(\.modules\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    # --- 模块尺寸（按比例缩放所有 mod-row 的内联变量） ---
    if 'MODULE_W' in new_params and 'MODULE_W' in original_params:
        config_old = original_params['MODULE_W']
        config_new = new_params['MODULE_W']
        if config_old > 0:
            ratio = config_new / config_old
            content = re.sub(
                r'(--mod-w:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content
            )

    if 'MODULE_H' in new_params and 'MODULE_H' in original_params:
        config_old = original_params['MODULE_H']
        config_new = new_params['MODULE_H']
        if config_old > 0:
            ratio = config_new / config_old
            content = re.sub(
                r'(--mod-h-inner:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content
            )
            content = re.sub(
                r'(--mod-h:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content
            )

    # --- 域样式 ---
    # 域背景色（直接替换）
    if 'DOMAIN_BG' in new_params and 'DOMAIN_BG' in original_params:
        old_color = original_params['DOMAIN_BG']
        new_color = new_params['DOMAIN_BG']
        if old_color != new_color:
            content = re.sub(
                r'(\.domain-frame-wrapper\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color,
                content
            )

    # 域边框色（直接替换）
    if 'DOMAIN_BORDER_COLOR' in new_params and 'DOMAIN_BORDER_COLOR' in original_params:
        old_color = original_params['DOMAIN_BORDER_COLOR']
        new_color = new_params['DOMAIN_BORDER_COLOR']
        if old_color != new_color:
            content = re.sub(
                r'(\.domain-frame-wrapper\s*\{[^}]*border:\s*(?:\d+(?:\.\d+)?px\s+solid\s+))' + re.escape(old_color),
                r'\g<1>' + new_color,
                content
            )

    # 域标题色（直接替换）
    if 'DOMAIN_TITLE_COLOR' in new_params and 'DOMAIN_TITLE_COLOR' in original_params:
        old_color = original_params['DOMAIN_TITLE_COLOR']
        new_color = new_params['DOMAIN_TITLE_COLOR']
        if old_color != new_color:
            content = re.sub(
                r'(\.domain-title\s*\{[^}]*color:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color,
                content
            )

    # 模块边框色（直接替换）
    if 'MODULE_BORDER_COLOR' in new_params and 'MODULE_BORDER_COLOR' in original_params:
        old_color = original_params['MODULE_BORDER_COLOR']
        new_color = new_params['MODULE_BORDER_COLOR']
        if old_color != new_color:
            content = re.sub(
                r'(\.module\s*\{[^}]*border:\s*\d+(?:\.\d+)?px\s+solid\s+)' + re.escape(old_color),
                r'\g<1>' + new_color,
                content
            )

    # --- 域标题字号（按比例缩放）---
    if 'DOMAIN_TITLE_FONT_SIZE' in new_params and 'DOMAIN_TITLE_FONT_SIZE' in original_params:
        config_old = original_params['DOMAIN_TITLE_FONT_SIZE']
        config_new = new_params['DOMAIN_TITLE_FONT_SIZE']
        if config_old > 0:
            m = re.search(r'(\.domain-title\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    # --- 域内边距（按比例缩放）---
    if 'DOMAIN_PADDING' in new_params and 'DOMAIN_PADDING' in original_params:
        config_old = original_params['DOMAIN_PADDING']
        config_new = new_params['DOMAIN_PADDING']
        if config_old > 0:
            m = re.search(r'(\.domain-frame-wrapper\s*\{[^}]*padding:\s*)(\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px', content)
            if m:
                current_y = float(m.group(2))
                current_x = float(m.group(3))
                ratio = config_new / config_old
                new_y = current_y * ratio
                new_x = current_x * ratio
                content = content[:m.start(2)] + f'{new_y:.0f}px {new_x:.0f}px' + content[m.end(3):]

    # --- 列内组间距（按比例缩放）---
    if 'COLUMN_GAP' in new_params and 'COLUMN_GAP' in original_params:
        config_old = original_params['COLUMN_GAP']
        config_new = new_params['COLUMN_GAP']
        if config_old > 0:
            m = re.search(r'(\.column\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.0f}' + content[m.end(2):]

    # --- 标题下方间距（按比例缩放）---
    if 'GROUP_HEADER_MARGIN_BOTTOM' in new_params and 'GROUP_HEADER_MARGIN_BOTTOM' in original_params:
        config_old = original_params['GROUP_HEADER_MARGIN_BOTTOM']
        config_new = new_params['GROUP_HEADER_MARGIN_BOTTOM']
        if config_old > 0:
            m = re.search(r'(\.group-header\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.0f}' + content[m.end(2):]

    # --- 域标题下方间距（按比例缩放）---
    if 'DOMAIN_TITLE_MARGIN_BOTTOM' in new_params and 'DOMAIN_TITLE_MARGIN_BOTTOM' in original_params:
        config_old = original_params['DOMAIN_TITLE_MARGIN_BOTTOM']
        config_new = new_params['DOMAIN_TITLE_MARGIN_BOTTOM']
        if config_old > 0:
            m = re.search(r'(\.domain-title\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.0f}' + content[m.end(2):]

    # --- 域外框圆角（按比例缩放）---
    if 'DOMAIN_BORDER_RADIUS' in new_params and 'DOMAIN_BORDER_RADIUS' in original_params:
        config_old = original_params['DOMAIN_BORDER_RADIUS']
        config_new = new_params['DOMAIN_BORDER_RADIUS']
        if config_old > 0:
            m = re.search(r'(\.domain-frame-wrapper\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.0f}' + content[m.end(2):]

    # --- 组圆角（按比例缩放）---
    if 'GROUP_BORDER_RADIUS' in new_params and 'GROUP_BORDER_RADIUS' in original_params:
        config_old = original_params['GROUP_BORDER_RADIUS']
        config_new = new_params['GROUP_BORDER_RADIUS']
        if config_old > 0:
            m = re.search(r'(\.group\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.0f}' + content[m.end(2):]

    # --- 模块圆角（按比例缩放）---
    if 'MODULE_BORDER_RADIUS' in new_params and 'MODULE_BORDER_RADIUS' in original_params:
        config_old = original_params['MODULE_BORDER_RADIUS']
        config_new = new_params['MODULE_BORDER_RADIUS']
        if config_old > 0:
            m = re.search(r'(\.module\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.0f}' + content[m.end(2):]

    # --- 域边框宽度（按比例缩放）---
    if 'DOMAIN_BORDER_WIDTH' in new_params and 'DOMAIN_BORDER_WIDTH' in original_params:
        config_old = original_params['DOMAIN_BORDER_WIDTH']
        config_new = new_params['DOMAIN_BORDER_WIDTH']
        if config_old > 0:
            m = re.search(r'(\.domain-frame-wrapper\s*\{[^}]*border:\s*)(\d+(?:\.\d+)?)px(\s+solid)', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (config_new / config_old)
                content = content[:m.start(2)] + f'{new_px:.0f}' + content[m.end(2):]

    # --- 模块行高（直接替换）---
    if 'MODULE_LINE_HEIGHT' in new_params and 'MODULE_LINE_HEIGHT' in original_params:
        old_val = original_params['MODULE_LINE_HEIGHT']
        new_val = new_params['MODULE_LINE_HEIGHT']
        if old_val != new_val:
            content = re.sub(
                r'(\.module\s*\{[^}]*line-height:\s*)' + re.escape(str(old_val)),
                r'\g<1>' + str(new_val),
                content
            )

    # --- 模块字体族（直接替换）---
    if 'MODULE_FONT_FAMILY' in new_params and 'MODULE_FONT_FAMILY' in original_params:
        old_val = original_params['MODULE_FONT_FAMILY']
        new_val = new_params['MODULE_FONT_FAMILY']
        if old_val != new_val:
            content = re.sub(
                r'(\.module\s*\{[^}]*font-family:\s*)' + re.escape(old_val),
                r'\g<1>' + new_val,
                content
            )

    # 写回文件
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True, css_now
