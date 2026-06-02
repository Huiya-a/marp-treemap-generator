# -*- coding: utf-8 -*-
"""
数据加载模块

负责从 Excel 或 JSON 文件中读取应用架构数据。
返回统一的数据结构: (domain_name, {group_name: [module_name, ...]})
"""


def load_data_from_excel(filepath):
    """
    从 Excel 文件加载应用架构数据。

    Excel 数据格式要求:
    - Sheet 名称需包含 "应用模块清单"（否则回退到第二个 sheet）
    - 数据从第 3 行开始
    - B 列 (index 1): 应用域名称
    - D 列 (index 3): 应用组名称
    - G 列 (index 6): 一级应用模块名称

    Args:
        filepath: Excel 文件路径

    Returns:
        (domain_name, groups_dict)
        - domain_name: 应用域名称（如 "纪检监察域"）
        - groups_dict: {组名: [模块名1, 模块名2, ...]}，模块名已排序去重
    """
    import openpyxl
    wb = openpyxl.load_workbook(filepath)

    # 查找包含 "应用模块清单" 的 sheet
    ws = None
    for sheet in wb.worksheets:
        if '应用模块清单' in sheet.title:
            ws = sheet
            break
    # 回退: 使用第二个 sheet
    if ws is None:
        ws = wb.worksheets[1]

    domain_name = None
    groups = {}  # {group_name: set(module_name)}

    # 从第 3 行开始读取数据
    for row in ws.iter_rows(min_row=3, values_only=True):
        # 第一次遇到非空 B 列时，记录域名称
        if domain_name is None and row[1]:
            domain_name = row[1]  # B 列: 应用域名称

        group_name = row[3]       # D 列: 应用组名称
        module_name = row[6]      # G 列: 一级应用模块名称

        # 只处理组名和模块名都非空的行
        if group_name and module_name:
            if group_name not in groups:
                groups[group_name] = set()
            groups[group_name].add(module_name)  # 自动去重

    # 将 set 转为 sorted list，保证输出顺序一致
    result = {k: sorted(list(v)) for k, v in groups.items()}
    return domain_name or '应用架构', result


def load_data_from_json(filepath):
    """
    从 JSON 文件加载数据（备用方案）。

    JSON 格式: {"domain": "域名", "groups": {"组名": ["模块名", ...]}}

    Args:
        filepath: JSON 文件路径

    Returns:
        (domain_name, data)
    """
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    if isinstance(raw, dict) and 'domain' in raw and 'groups' in raw:
        return raw['domain'], raw['groups']
    return '应用架构', raw
