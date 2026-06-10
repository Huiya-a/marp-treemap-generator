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

    return params


def apply_params_to_md(md_path: str, new_params: dict, original_params: dict) -> bool:
    """将新的参数值写入 Markdown 文件

    通过比较 new_params 和 original_params 计算比例，
    然后用正则替换 Markdown 中对应的 CSS/HTML 值。

    Args:
        md_path: Markdown 文件路径
        new_params: 用户在 UI 中设置的新参数值（config 参数名 -> 值）
        original_params: 首次生成时的 config 参数名 -> 值

    Returns:
        bool: 是否成功修改
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 从 original_params 和 new_params 中提取基准值和目标值
    # original_params 使用 config 参数名，new_params 也是

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
    if 'MODULE_FONT_SIZE' in new_params and 'MODULE_FONT_SIZE' in original_params:
        old_val = original_params['MODULE_FONT_SIZE']
        new_val = new_params['MODULE_FONT_SIZE']
        if old_val != new_val and old_val > 0:
            # 从 Markdown 中提取当前的 px 值
            m = re.search(r'(\.module\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                # 计算当前实际值对应的基础值（去除 fill_scale）
                # current_px = base * fill_scale，我们不知道 fill_scale
                # 但我们可以用比例：new_px = current_px * (new_val / old_val)
                new_px = current_px * (new_val / old_val)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    if 'GROUP_HEADER_FONT_SIZE' in new_params and 'GROUP_HEADER_FONT_SIZE' in original_params:
        old_val = original_params['GROUP_HEADER_FONT_SIZE']
        new_val = new_params['GROUP_HEADER_FONT_SIZE']
        if old_val != new_val and old_val > 0:
            m = re.search(r'(\.group-header\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (new_val / old_val)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    # --- 间距（按比例缩放） ---
    if 'COL_GAP' in new_params and 'COL_GAP' in original_params:
        old_val = original_params['COL_GAP']
        new_val = new_params['COL_GAP']
        if old_val != new_val and old_val > 0:
            m = re.search(r'(\.columns\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (new_val / old_val)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    if 'ROW_GAP' in new_params and 'ROW_GAP' in original_params:
        old_val = original_params['ROW_GAP']
        new_val = new_params['ROW_GAP']
        if old_val != new_val and old_val > 0:
            m = re.search(r'(\.modules\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px', content)
            if m:
                current_px = float(m.group(2))
                new_px = current_px * (new_val / old_val)
                content = content[:m.start(2)] + f'{new_px:.1f}' + content[m.end(2):]

    # --- 模块尺寸（按比例缩放所有 mod-row 的内联变量） ---
    if 'MODULE_W' in new_params and 'MODULE_W' in original_params:
        old_val = original_params['MODULE_W']
        new_val = new_params['MODULE_W']
        if old_val != new_val and old_val > 0:
            ratio = new_val / old_val
            # 缩放所有 --mod-w 值
            content = re.sub(
                r'(--mod-w:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content
            )

    if 'MODULE_H' in new_params and 'MODULE_H' in original_params:
        old_val = original_params['MODULE_H']
        new_val = new_params['MODULE_H']
        if old_val != new_val and old_val > 0:
            ratio = new_val / old_val
            # 缩放 --mod-h-inner（内部高度）
            content = re.sub(
                r'(--mod-h-inner:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content
            )
            # 缩放 --mod-h（含边框的总高度）
            content = re.sub(
                r'(--mod-h:\s*)(\d+(?:\.\d+)?)px',
                lambda m: m.group(1) + f'{float(m.group(2)) * ratio:.1f}' + 'px',
                content
            )

    # 写回文件
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True
