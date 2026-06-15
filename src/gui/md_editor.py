# -*- coding: utf-8 -*-
"""
Markdown 文件编辑器

直接修改已生成的 Markdown 文件中的 CSS 属性值和 HTML 内联变量，
无需修改 Python 源码或 config 模块。
"""

import re


def _extract_css_blocks(content):
    """将 CSS 文本拆分为独立的规则块列表。

    Returns:
        list of (selector, block_content, full_match)
        - selector: 选择器文本（如 '.module'）
        - block_content: 花括号内的属性内容
        - full_match: 完整的规则文本（含选择器和花括号）
    """
    blocks = []
    for m in re.finditer(r'([^\s{][^{}]*?)\s*\{([^}]*)\}', content):
        blocks.append((m.group(1).strip(), m.group(2), m.group(0)))
    return blocks


def _sub_in_css_blocks(content, pattern, replacement):
    """在 CSS 规则块内执行正则替换，不跨越 } 边界。

    对内容中的每个 CSS 规则块（selector { props }）独立执行 re.sub，
    避免 [^}]* 等正则跨越规则边界匹配。
    """
    result = content
    for _, _, full_block in _extract_css_blocks(content):
        new_block = re.sub(pattern, replacement, full_block)
        if new_block != full_block:
            result = result.replace(full_block, new_block, 1)
    return result


def extract_params_from_md(md_path: str) -> dict:
    """从已生成的 Markdown 文件中提取当前的 CSS 参数值

    Returns:
        dict: 包含所有可调参数的当前值
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    params = {}

    # 提取颜色
    m = re.search(r'\.group\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['GROUP_BG'] = m.group(1)

    m = re.search(r'\.group\s*\{[^}]*border:\s*[\d.]+px\s+solid\s+(#[0-9A-Fa-f]{6})', content)
    if m:
        params['GROUP_BORDER'] = m.group(1)

    m = re.search(r'\.group-header\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['GROUP_HEADER_COLOR'] = m.group(1)

    m = re.search(r'\.module\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['MODULE_BG_COLOR'] = m.group(1)

    # 提取字体大小
    m = re.search(r'\.module\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['MODULE_FONT_SIZE_PX'] = float(m.group(1))

    m = re.search(r'\.group-header\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['GROUP_HEADER_FONT_SIZE_PX'] = float(m.group(1))

    # 提取间距
    m = re.search(r'\.columns\s*\{[^}]*gap:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['COL_GAP_PX'] = float(m.group(1))

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
    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['DOMAIN_BG'] = m.group(1)

    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*border:\s*(\d+(?:\.\d+)?)px\s+solid\s+(#[0-9A-Fa-f]{6})', content)
    if m:
        params['DOMAIN_BORDER_WIDTH_PX'] = float(m.group(1))
        params['DOMAIN_BORDER_COLOR'] = m.group(2)

    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*border-radius:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_BORDER_RADIUS_PX'] = float(m.group(1))

    m = re.search(r'\.domain-frame-wrapper\s*\{[^}]*padding:\s*(\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_PADDING_Y_PX'] = float(m.group(1))
        params['DOMAIN_PADDING_X_PX'] = float(m.group(2))

    m = re.search(r'\.domain-title\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_TITLE_FONT_SIZE_PX'] = float(m.group(1))

    m = re.search(r'\.domain-title\s*\{[^}]*color:\s*(#[0-9A-Fa-f]{6})', content)
    if m:
        params['DOMAIN_TITLE_COLOR'] = m.group(1)

    m = re.search(r'\.domain-title\s*\{[^}]*margin-bottom:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['DOMAIN_TITLE_MARGIN_BOTTOM_PX'] = float(m.group(1))

    m = re.search(r'\.column\s*\{[^}]*gap:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['COLUMN_GAP_PX'] = float(m.group(1))

    m = re.search(r'\.group-header\s*\{[^}]*margin-bottom:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['GROUP_HEADER_MARGIN_BOTTOM_PX'] = float(m.group(1))

    m = re.search(r'\.group\s*\{[^}]*border-radius:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['GROUP_BORDER_RADIUS_PX'] = float(m.group(1))

    m = re.search(r'\.module\s*\{[^}]*border-radius:\s*(\d+(?:\.\d+)?)px', content)
    if m:
        params['MODULE_BORDER_RADIUS_PX'] = float(m.group(1))

    m = re.search(r'\.module\s*\{[^}]*border:\s*\d+(?:\.\d+)?px\s+solid\s+(#[0-9A-Fa-f]{6}|white)', content)
    if m:
        params['MODULE_BORDER_COLOR'] = m.group(1)

    m = re.search(r'\.module\s*\{[^}]*line-height:\s*(\d+(?:\.\d+)?)', content)
    if m:
        params['MODULE_LINE_HEIGHT'] = float(m.group(1))

    m = re.search(r'\.module\s*\{[^}]*font-family:\s*([^;]+);', content)
    if m:
        params['MODULE_FONT_FAMILY'] = m.group(1).strip()

    return params


def apply_params_to_md(md_path: str, new_params: dict, original_params: dict,
                       css_baseline: dict = None) -> tuple:
    """将新的参数值写入 Markdown 文件

    通过比较 new_params 和当前 CSS 实际值计算比例，
    然后用正则替换 Markdown 中对应的 CSS/HTML 值。

    所有 CSS 替换都通过 _sub_in_css_blocks 执行，确保正则不跨越 } 边界。

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

    css_now = extract_params_from_md(md_path)

    # --- 颜色（直接替换） ---
    if 'GROUP_BG' in new_params and 'GROUP_BG' in original_params:
        old_color = original_params['GROUP_BG']
        new_color = new_params['GROUP_BG']
        if old_color != new_color:
            content = _sub_in_css_blocks(content,
                r'(\.group\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color)

    if 'GROUP_HEADER_COLOR' in new_params and 'GROUP_HEADER_COLOR' in original_params:
        old_color = original_params['GROUP_HEADER_COLOR']
        new_color = new_params['GROUP_HEADER_COLOR']
        if old_color != new_color:
            content = _sub_in_css_blocks(content,
                r'(\.group-header\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color)

    if 'MODULE_BG_COLOR' in new_params and 'MODULE_BG_COLOR' in original_params:
        old_color = original_params['MODULE_BG_COLOR']
        new_color = new_params['MODULE_BG_COLOR']
        if old_color != new_color:
            content = _sub_in_css_blocks(content,
                r'(\.module\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color)

    # --- 字体大小（按比例缩放） ---
    if 'MODULE_FONT_SIZE' in new_params and 'MODULE_FONT_SIZE' in original_params:
        config_old = original_params['MODULE_FONT_SIZE']
        config_new = new_params['MODULE_FONT_SIZE']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.module\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}px')

    if 'GROUP_HEADER_FONT_SIZE' in new_params and 'GROUP_HEADER_FONT_SIZE' in original_params:
        config_old = original_params['GROUP_HEADER_FONT_SIZE']
        config_new = new_params['GROUP_HEADER_FONT_SIZE']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.group-header\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}px')

    # --- 间距（按比例缩放） ---
    if 'COL_GAP' in new_params and 'COL_GAP' in original_params:
        config_old = original_params['COL_GAP']
        config_new = new_params['COL_GAP']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.columns\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}px')

    if 'ROW_GAP' in new_params and 'ROW_GAP' in original_params:
        config_old = original_params['ROW_GAP']
        config_new = new_params['ROW_GAP']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.modules\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}px')

    # --- 模块尺寸（按比例缩放所有 mod-row 的内联变量） ---
    if 'MODULE_W' in new_params and 'MODULE_W' in original_params:
        config_old = original_params['MODULE_W']
        config_new = new_params['MODULE_W']
        if config_old > 0:
            ratio = config_new / config_old
            content = re.sub(
                r'(--mod-w:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content)

    if 'MODULE_H' in new_params and 'MODULE_H' in original_params:
        config_old = original_params['MODULE_H']
        config_new = new_params['MODULE_H']
        if config_old > 0:
            ratio = config_new / config_old
            content = re.sub(
                r'(--mod-h-inner:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content)
            content = re.sub(
                r'(--mod-h:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content)

    # --- 域背景色 ---
    if 'DOMAIN_BG' in new_params and 'DOMAIN_BG' in original_params:
        old_color = original_params['DOMAIN_BG']
        new_color = new_params['DOMAIN_BG']
        if old_color != new_color:
            content = _sub_in_css_blocks(content,
                r'(\.domain-frame-wrapper\s*\{[^}]*background:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color)

    # 域边框色
    if 'DOMAIN_BORDER_COLOR' in new_params and 'DOMAIN_BORDER_COLOR' in original_params:
        old_color = original_params['DOMAIN_BORDER_COLOR']
        new_color = new_params['DOMAIN_BORDER_COLOR']
        if old_color != new_color:
            content = _sub_in_css_blocks(content,
                r'(\.domain-frame-wrapper\s*\{[^}]*border:\s*(?:\d+(?:\.\d+)?px\s+solid\s+))' + re.escape(old_color),
                r'\g<1>' + new_color)

    # 域标题色
    if 'DOMAIN_TITLE_COLOR' in new_params and 'DOMAIN_TITLE_COLOR' in original_params:
        old_color = original_params['DOMAIN_TITLE_COLOR']
        new_color = new_params['DOMAIN_TITLE_COLOR']
        if old_color != new_color:
            content = _sub_in_css_blocks(content,
                r'(\.domain-title\s*\{[^}]*color:\s*)' + re.escape(old_color),
                r'\g<1>' + new_color)

    # 模块边框色
    if 'MODULE_BORDER_COLOR' in new_params and 'MODULE_BORDER_COLOR' in original_params:
        old_color = original_params['MODULE_BORDER_COLOR']
        new_color = new_params['MODULE_BORDER_COLOR']
        if old_color != new_color:
            content = _sub_in_css_blocks(content,
                r'(\.module\s*\{[^}]*border:\s*\d+(?:\.\d+)?px\s+solid\s+)' + re.escape(old_color),
                r'\g<1>' + new_color)

    # --- 域标题字号 ---
    if 'DOMAIN_TITLE_FONT_SIZE' in new_params and 'DOMAIN_TITLE_FONT_SIZE' in original_params:
        config_old = original_params['DOMAIN_TITLE_FONT_SIZE']
        config_new = new_params['DOMAIN_TITLE_FONT_SIZE']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.domain-title\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}px')

    # --- 域内边距 ---
    if 'DOMAIN_PADDING' in new_params and 'DOMAIN_PADDING' in original_params:
        config_old = original_params['DOMAIN_PADDING']
        config_new = new_params['DOMAIN_PADDING']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.domain-frame-wrapper\s*\{[^}]*padding:\s*)(\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px {float(m.group(3)) * ratio:.0f}px')

    # --- 列内组间距 ---
    if 'COLUMN_GAP' in new_params and 'COLUMN_GAP' in original_params:
        config_old = original_params['COLUMN_GAP']
        config_new = new_params['COLUMN_GAP']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.column\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px')

    # --- 标题下方间距 ---
    if 'GROUP_HEADER_MARGIN_BOTTOM' in new_params and 'GROUP_HEADER_MARGIN_BOTTOM' in original_params:
        config_old = original_params['GROUP_HEADER_MARGIN_BOTTOM']
        config_new = new_params['GROUP_HEADER_MARGIN_BOTTOM']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.group-header\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px')

    # --- 域标题下方间距 ---
    if 'DOMAIN_TITLE_MARGIN_BOTTOM' in new_params and 'DOMAIN_TITLE_MARGIN_BOTTOM' in original_params:
        config_old = original_params['DOMAIN_TITLE_MARGIN_BOTTOM']
        config_new = new_params['DOMAIN_TITLE_MARGIN_BOTTOM']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.domain-title\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px')

    # --- 域外框圆角 ---
    if 'DOMAIN_BORDER_RADIUS' in new_params and 'DOMAIN_BORDER_RADIUS' in original_params:
        config_old = original_params['DOMAIN_BORDER_RADIUS']
        config_new = new_params['DOMAIN_BORDER_RADIUS']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.domain-frame-wrapper\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px')

    # --- 组圆角 ---
    if 'GROUP_BORDER_RADIUS' in new_params and 'GROUP_BORDER_RADIUS' in original_params:
        config_old = original_params['GROUP_BORDER_RADIUS']
        config_new = new_params['GROUP_BORDER_RADIUS']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.group\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px')

    # --- 模块圆角 ---
    if 'MODULE_BORDER_RADIUS' in new_params and 'MODULE_BORDER_RADIUS' in original_params:
        config_old = original_params['MODULE_BORDER_RADIUS']
        config_new = new_params['MODULE_BORDER_RADIUS']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.module\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px')

    # --- 域边框宽度 ---
    if 'DOMAIN_BORDER_WIDTH' in new_params and 'DOMAIN_BORDER_WIDTH' in original_params:
        config_old = original_params['DOMAIN_BORDER_WIDTH']
        config_new = new_params['DOMAIN_BORDER_WIDTH']
        if config_old > 0:
            ratio = config_new / config_old
            content = _sub_in_css_blocks(content,
                r'(\.domain-frame-wrapper\s*\{[^}]*border:\s*)(\d+(?:\.\d+)?)px(\s+solid)',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.0f}px' + m.group(3))

    # --- 模块行高 ---
    if 'MODULE_LINE_HEIGHT' in new_params and 'MODULE_LINE_HEIGHT' in original_params:
        old_val = original_params['MODULE_LINE_HEIGHT']
        new_val = new_params['MODULE_LINE_HEIGHT']
        if old_val != new_val:
            content = _sub_in_css_blocks(content,
                r'(\.module\s*\{[^}]*line-height:\s*)' + re.escape(str(old_val)),
                r'\g<1>' + str(new_val))

    # --- 模块字体族 ---
    if 'MODULE_FONT_FAMILY' in new_params and 'MODULE_FONT_FAMILY' in original_params:
        old_val = original_params['MODULE_FONT_FAMILY']
        new_val = new_params['MODULE_FONT_FAMILY']
        if old_val != new_val:
            content = _sub_in_css_blocks(content,
                r'(\.module\s*\{[^}]*font-family:\s*)' + re.escape(old_val),
                r'\g<1>' + new_val)

    # 写回文件
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True, css_now
