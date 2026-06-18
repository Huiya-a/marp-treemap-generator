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

    # 提取画布高度（从 frontmatter 中，匹配 "height: 720px" 或 "height: 720"）
    # 只匹配 frontmatter 部分（--- 之间），且在 style: 之前
    frontmatter_match = re.search(r'^---\s*\n(.*?)\nstyle:', content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        m = re.search(r'height:\s*(\d+)(?:px)?', frontmatter)
        if m:
            params['SLIDE_HEIGHT_PX'] = float(m.group(1))

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

    # --- 数值按比例缩放 ---
    # 使用 css_baseline（首次生成时的 CSS 值，不可覆盖）作为基准，
    # 直接计算目标值，不从文件读当前值，避免重复 apply 时叠加放大。
    baseline = css_baseline or {}
    numeric_configs = [
        ('MODULE_FONT_SIZE',       'MODULE_FONT_SIZE_PX',       r'(\.module\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px'),
        ('GROUP_HEADER_FONT_SIZE', 'GROUP_HEADER_FONT_SIZE_PX', r'(\.group-header\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px'),
        ('DOMAIN_TITLE_FONT_SIZE', 'DOMAIN_TITLE_FONT_SIZE_PX', r'(\.domain-title\s*\{[^}]*font-size:\s*)(\d+(?:\.\d+)?)px'),
        ('COL_GAP',                'COL_GAP_PX',                r'(\.columns\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px'),
        ('ROW_GAP',                'ROW_GAP_PX',                r'(\.modules\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px'),
        ('COLUMN_GAP',             'COLUMN_GAP_PX',             r'(\.column\s*\{[^}]*gap:\s*)(\d+(?:\.\d+)?)px'),
        ('DOMAIN_BORDER_RADIUS',   'DOMAIN_BORDER_RADIUS_PX',   r'(\.domain-frame-wrapper\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px'),
        ('GROUP_BORDER_RADIUS',    'GROUP_BORDER_RADIUS_PX',    r'(\.group\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px'),
        ('MODULE_BORDER_RADIUS',   'MODULE_BORDER_RADIUS_PX',   r'(\.module\s*\{[^}]*border-radius:\s*)(\d+(?:\.\d+)?)px'),
        ('DOMAIN_TITLE_MARGIN_BOTTOM', 'DOMAIN_TITLE_MARGIN_BOTTOM_PX', r'(\.domain-title\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px'),
        ('GROUP_HEADER_MARGIN_BOTTOM', 'GROUP_HEADER_MARGIN_BOTTOM_PX', r'(\.group-header\s*\{[^}]*margin-bottom:\s*)(\d+(?:\.\d+)?)px'),
        ('DOMAIN_BORDER_WIDTH',    'DOMAIN_BORDER_WIDTH_PX',    r'(\.domain-frame-wrapper\s*\{[^}]*border:\s*)(\d+(?:\.\d+)?)px(\s+solid)'),
    ]
    for param_key, css_key, pattern in numeric_configs:
        if param_key in new_params and param_key in original_params and css_key in baseline:
            config_old = original_params[param_key]
            config_new = new_params[param_key]
            if config_old > 0:
                target = baseline[css_key] * (config_new / config_old)
                if param_key == 'DOMAIN_BORDER_WIDTH':
                    content = _sub_in_css_blocks(content, pattern,
                        lambda m, v=target: m.group(1) + f'{v:.0f}px' + m.group(3))
                elif 'font-size' in pattern:
                    content = _sub_in_css_blocks(content, pattern,
                        lambda m, v=target: m.group(1) + f'{v:.1f}px')
                else:
                    content = _sub_in_css_blocks(content, pattern,
                        lambda m, v=target: m.group(1) + f'{v:.0f}px')

    # --- 模块尺寸（按比例缩放所有 mod-row 的内联变量） ---
    if 'MODULE_W' in new_params and 'MODULE_W' in original_params:
        config_old = original_params['MODULE_W']
        config_new = new_params['MODULE_W']
        if config_old > 0 and 'MOD_W_PX' in baseline:
            target = baseline['MOD_W_PX'] * (config_new / config_old)
            content = re.sub(
                r'(--mod-w:\s*)(\d+(?:\.\d+)?)px',
                lambda m, v=target: m.group(1) + f'{v:.1f}px',
                content)

    if 'MODULE_H' in new_params and 'MODULE_H' in original_params:
        config_old = original_params['MODULE_H']
        config_new = new_params['MODULE_H']
        if config_old > 0 and 'MOD_H_INNER_PX' in baseline:
            target_inner = baseline['MOD_H_INNER_PX'] * (config_new / config_old)
            target_h = baseline['MOD_H_PX'] * (config_new / config_old)
            content = re.sub(
                r'(--mod-h-inner:\s*)(\d+(?:\.\d+)?)px',
                lambda m, v=target_inner: m.group(1) + f'{v:.1f}px',
                content)
            content = re.sub(
                r'(--mod-h:\s*)(\d+(?:\.\d+)?)px',
                lambda m, v=target_h: m.group(1) + f'{v:.1f}px',
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

    # --- 域内边距（特殊处理：两个值） ---
    if 'DOMAIN_PADDING' in new_params and 'DOMAIN_PADDING' in original_params:
        config_old = original_params['DOMAIN_PADDING']
        config_new = new_params['DOMAIN_PADDING']
        if config_old > 0 and 'DOMAIN_PADDING_Y_PX' in baseline:
            target_y = baseline['DOMAIN_PADDING_Y_PX'] * (config_new / config_old)
            target_x = baseline.get('DOMAIN_PADDING_X_PX', 16) * (config_new / config_old)
            content = _sub_in_css_blocks(content,
                r'(\.domain-frame-wrapper\s*\{[^}]*padding:\s*)(\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px',
                lambda m, ty=target_y, tx=target_x: m.group(1) + f'{ty:.0f}px {tx:.0f}px')

    # --- 模块行高（直接替换，非比例缩放） ---
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

    # --- 画布高度（Marp frontmatter 中的 height + CSS section height） ---
    if 'SLIDE_HEIGHT_PX' in new_params:
        new_height = new_params['SLIDE_HEIGHT_PX']
        old_height = original_params.get('SLIDE_HEIGHT_PX', 'N/A')
        print(f"[DEBUG] SLIDE_HEIGHT_PX: old={old_height}, new={new_height}")
        # 只替换 frontmatter 中的 height（在 style: 之前）
        # 格式: height: 720px 或 height: 720
        frontmatter_end = content.find('\nstyle:')
        if frontmatter_end != -1:
            frontmatter = content[:frontmatter_end]
            rest = content[frontmatter_end:]
            print(f"[DEBUG] Frontmatter before: {frontmatter[:200]}...")
            # 替换 frontmatter 中的 height
            frontmatter = re.sub(
                r'(height:\s*)(\d+)(px)?',
                lambda m, h=new_height: m.group(1) + str(int(h)) + 'px',
                frontmatter
            )
            # 如果没有 height 字段，在 backgroundColor 后面添加
            if 'height:' not in frontmatter:
                print("[DEBUG] No height field found, adding one")
                frontmatter = frontmatter.replace(
                    'backgroundColor: "#FAFBFC"',
                    f'backgroundColor: "#FAFBFC"\nheight: {int(new_height)}px'
                )
            print(f"[DEBUG] Frontmatter after: {frontmatter[:200]}...")
            content = frontmatter + rest
        else:
            print("[DEBUG] Could not find \\nstyle: in content")

        # 同时更新 CSS 中的 section height
        content = re.sub(
            r'(section\s*\{[^}]*height:\s*)(\d+)(px\s*!important)',
            lambda m, h=new_height: m.group(1) + str(int(h)) + m.group(3),
            content
        )

    # 写回文件
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True, css_now


def apply_module_color(md_path: str, module_name: str, color: str):
    """为指定名称的模块设置背景颜色。

    通过 CSS class 实现（Marp SVG 渲染不支持 inline style）。
    在 <style> 块中添加 .mc-xxx { background: color !important; } 规则，
    并在模块 div 的 class 中添加 mc-xxx。

    Args:
        md_path: Markdown 文件路径
        module_name: 模块名称（纯文本，不含 <br>）
        color: 颜色值，如 '#FF0000'

    Returns:
        (success: bool, message: str)
    """
    import hashlib

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 用模块名生成稳定的 class 后缀
    name_hash = hashlib.md5(module_name.encode('utf-8')).hexdigest()[:6]
    cls = f'mc-{name_hash}'
    css_rule = f'  .{cls} {{ background: {color} !important; }}'

    # 1. 在 YAML frontmatter 的 style 块末尾（--- 之前）添加 CSS 规则
    #    先移除旧的同名规则（按 class 名匹配，忽略颜色值）
    content = re.sub(r'\s*\.' + re.escape(cls) + r'\s*\{[^}]*\}', '', content)

    # 找到 frontmatter 结束位置（最后一个独立的 ---）
    # Marp frontmatter 结构: --- \n ... \n ---
    last_deli = content.rfind('\n---\n')
    if last_deli == -1:
        return False, '未找到 YAML frontmatter 结束标记'

    # 在 --- 之前插入 CSS 规则
    content = content[:last_deli] + '\n' + css_rule + content[last_deli:]

    # 2. 在匹配的模块 div 上添加/替换 class
    #
    #    不做全局 mc- 清洗 —— 那会把其他模块已有的颜色一起删掉。
    #    而是匹配所有 <div class="module ...">（含或不含 mc-），
    #    逐个检查内容是否为目标模块，是则设置新 mc- 类，否则原样保留。
    #
    #    用 (?!s) 负向前瞻排除 class="modules" —— 否则 "module" 作为
    #    "modules" 的子串会错误匹配到 .modules 容器 div。
    pattern = re.compile(
        r'(<div\s+class="module(?!s)(?:\s+mc-[0-9a-f]+)*">)'
        r'(.*?)'
        r'(</div>)',
        re.DOTALL
    )

    count = 0

    def _replace(m):
        nonlocal count
        tag_open = m.group(1)
        inner = m.group(2)
        close_tag = m.group(3)

        # 检查 inner 的纯文本是否匹配模块名
        plain = re.sub(r'<[^>]+>', '', inner).strip()
        if plain != module_name:
            return m.group(0)

        count += 1

        # 移除 tag 中已有的所有 mc- class，再追加新的
        clean_tag = re.sub(r'\s+mc-[0-9a-f]+', '', tag_open)
        new_tag = clean_tag.replace(
            'class="module"',
            f'class="module {cls}"'
        )

        # 移除可能残留的旧 inline style（background/background-color）
        new_tag = re.sub(r'\s+style="[^"]*(?:background(?:-color)?\s*:\s*[^;]*)[^"]*"', '', new_tag)
        # 如果 style 属性被清空了，整个去掉
        new_tag = re.sub(r'\s+style=""', '', new_tag)

        return new_tag + inner + close_tag

    new_content = pattern.sub(_replace, content)

    if count == 0:
        return False, f'未找到模块: {module_name}'

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True, f'已为 {count} 个 "{module_name}" 模块设置颜色 {color}'
