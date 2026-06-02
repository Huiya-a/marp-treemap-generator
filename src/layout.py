# -*- coding: utf-8 -*-
"""
布局算法模块

核心职责:
1. 计算每个组（Group）的自然尺寸（宽 × 高）
2. 将组分配到各列（Column），平衡模块数和视觉高度
3. 计算统一的缩放因子，将自然单位映射到画布像素
4. 放置每个模块（Module）的精确坐标

布局层级: 画布(Canvas) → 列(Column) → 组(Group) → 模块(Module)
"""

import numpy as np

from .config import (
    CANVAS_W, CANVAS_H,
    MODULE_W, MODULE_H, MODULE_GAP_X, MODULE_GAP_Y,
    HEADER_H, HEADER_GAP, GROUP_PAD_BOTTOM, GROUP_PAD_X,
    OUTER_PAD_X, OUTER_PAD_TOP, OUTER_PAD_BOTTOM,
    COL_GAP, ROW_GAP, TARGET_RATIO,
    ADJUST_MPR,
)


# ============================================================
# 基础尺寸计算
# ============================================================

def _raw_group_size(n_modules, modules_per_row):
    """
    计算一个组在自然单位下的原始尺寸（不含缩放）。

    组的结构:
    ┌─────────────────────────┐
    │      标题栏 (HEADER_H)   │
    ├─────────────────────────┤
    │  模块行 1                │
    │  模块行 2                │
    │  ...                     │
    │  模块行 N                │
    └─────────────────────────┘
      ← GROUP_PAD_X →  ← GROUP_PAD_X →

    Args:
        n_modules: 模块数量
        modules_per_row: 每行模块数 (mpr)

    Returns:
        (width, height): 自然单位下的组尺寸
    """
    n_rows = int(np.ceil(n_modules / modules_per_row))

    # 宽度 = 每行模块数 × 模块宽 + 模块间水平间距 + 左右内边距
    w = (modules_per_row * MODULE_W
         + (modules_per_row - 1) * MODULE_GAP_X
         + 2 * GROUP_PAD_X)

    # 高度 = 标题栏 + 标题间距 + 模块行高 + 行间垂直间距 + 底部内边距
    h = (HEADER_H + HEADER_GAP
         + n_rows * MODULE_H
         + max(0, n_rows - 1) * MODULE_GAP_Y
         + GROUP_PAD_BOTTOM)

    return w, h


def compute_modules_per_row(n_modules):
    """
    根据模块数量计算最佳每行模块数 (mpr)。

    目标: 使 列数/行数 的比值尽量接近 1.5（偏横向的矩形）。
    遍历 2~6 的候选 mpr，选择最接近目标比值的。

    Args:
        n_modules: 模块数量

    Returns:
        最佳每行模块数 (2~6)
    """
    # 模块数 ≤ 3 时，每行放全部模块即可
    if n_modules <= 3:
        return n_modules

    best_mpr = 3
    best_diff = float('inf')

    for m in range(2, min(n_modules, 6) + 1):
        n_rows = int(np.ceil(n_modules / m))
        ratio = m / n_rows       # 列数 / 行数
        diff = abs(ratio - 1.5)  # 与目标比值的偏差
        if diff < best_diff:
            best_diff = diff
            best_mpr = m

    return best_mpr


def compute_group_size(n_modules, modules_per_row=None):
    """
    根据模块数量计算组的自然尺寸。

    Args:
        n_modules: 模块数量
        modules_per_row: 每行模块数，为 None 时自动计算

    Returns:
        (width, height): 自然单位下的组尺寸
    """
    if modules_per_row is None:
        modules_per_row = compute_modules_per_row(n_modules)
    return _raw_group_size(n_modules, modules_per_row)


# ============================================================
# 列高度计算
# ============================================================

def _visual_rows(n_modules, mpr):
    """
    计算组的视觉行数 = 标题行(1) + 模块行数。

    用于列间高度比较，比精确像素高度更快。
    """
    return int(np.ceil(n_modules / mpr)) + 1


def _col_height(cg):
    """
    计算一列的总自然高度 = 所有组高度之和 + 组间垂直间距。

    Args:
        cg: 列中的组列表 [(name, modules, gw, gh, mpr), ...]

    Returns:
        列的总高度（自然单位）
    """
    h = sum(gh for _, _, _, gh, _ in cg) + ROW_GAP * max(0, len(cg) - 1)
    return h


# ============================================================
# 组打包（行内分组）
# ============================================================

def _pack_groups_into_rows(groups_in_col, col_width):
    """
    将列内的组按宽度贪心打包成水平行。

    每个"行"可以包含多个并排的组（如果宽度允许）。
    打包规则:
    1. 当前行的组数 ≤ 上一行的组数（保证视觉一致性）
    2. 当前行所有组宽度之和 + 间距 ≤ 列宽

    Args:
        groups_in_col: 列中的组列表
        col_width: 列的最大自然宽度

    Returns:
        (rows, row_heights)
        - rows: [[group_tuple, ...], ...] 每行的组列表
        - row_heights: [float, ...] 每行的高度
    """
    if not groups_in_col:
        return [], []

    rows = []
    row_heights = []

    # 从第一个组开始
    current_row = [groups_in_col[0]]
    current_row_h = groups_in_col[0][3]  # gh

    for g in groups_in_col[1:]:
        name, modules, gw, gh, mpr = g
        prev_g = current_row[-1]
        prev_modules = prev_g[1]

        # 检查行数约束：当前组的行数 ≤ 前一组的行数
        cur_n_rows = int(np.ceil(len(modules) / mpr))
        prev_n_rows = int(np.ceil(len(prev_modules) / prev_g[4]))
        row_ok = cur_n_rows <= prev_n_rows

        # 检查宽度约束：所有组宽度 + 间距 ≤ 列宽
        total_w = sum(item[2] for item in current_row) + gw
        gap_w = COL_GAP * len(current_row)
        width_ok = (total_w + gap_w) <= col_width

        if row_ok and width_ok:
            # 可以放入当前行
            current_row.append(g)
            current_row_h = max(current_row_h, gh)
        else:
            # 当前行已满，开始新行
            rows.append(current_row)
            row_heights.append(current_row_h)
            current_row = [g]
            current_row_h = gh

    # 收尾最后一行
    rows.append(current_row)
    row_heights.append(current_row_h)
    return rows, row_heights


# ============================================================
# mpr 平衡调整
# ============================================================

def _adjust_mpr_for_balance(col_groups):
    """
    调整列内各组的 mpr，使列间实际高度尽量相同。

    原理: 较矮的列可以增大组的 mpr（每行放更多模块），
    从而增加行数和高度，向最高列靠拢。

    注意: 只会降低 mpr（增加行数/高度），不会升高 mpr。

    Args:
        col_groups: [[group_tuple, ...], ...] 各列的组

    Returns:
        调整后的列组列表
    """
    ncols = len(col_groups)
    if ncols <= 1:
        return col_groups

    col_h = [_col_height(cg) for cg in col_groups]
    target_h = max(col_h)  # 以最高列为基准

    new_col_groups = []
    for ci, cg in enumerate(col_groups):
        # 已经达到目标高度的列，不做调整
        if col_h[ci] >= target_h:
            new_col_groups.append(list(cg))
            continue

        new_cg = []
        for group_name, modules, gw, gh, mpr in cg:
            n = len(modules)
            cur_h = _col_height(new_cg)

            # 当前列已经够高了，保持原样
            if cur_h >= target_h:
                new_cg.append((group_name, modules, gw, gh, mpr))
                continue

            # 尝试降低 mpr（每行放更少模块 → 更多行 → 更高）
            best_mpr = mpr
            for try_mpr in range(mpr - 1, 1, -1):
                try_gw, try_gh = _raw_group_size(n, try_mpr)
                if try_gh > gh:  # 只在高度确实增加时才考虑
                    test_cg = new_cg + [(group_name, modules, try_gw, try_gh, try_mpr)]
                    if _col_height(test_cg) <= target_h:
                        best_mpr = try_mpr

            gw, gh = _raw_group_size(n, best_mpr)
            new_cg.append((group_name, modules, gw, gh, best_mpr))

        new_col_groups.append(new_cg)

    return new_col_groups


# ============================================================
# 组分配到列
# ============================================================

def _assign_groups_to_columns(group_info, ncols):
    """
    将组分配到各列，综合平衡模块数和视觉行数。

    算法: 贪心分配，按模块数降序处理。
    对每个组，选择当前"得分最低"的列放入。
    评分 = 模块数偏差 + 行数偏差²（行数偏差的平方惩罚优先平衡视觉高度）。

    Args:
        group_info: [(name, modules, gw, gh, mpr), ...] 所有组的信息
        ncols: 目标列数

    Returns:
        (col_groups, col_heights)
        - col_groups: [[group_tuple, ...], ...] 各列的组
        - col_heights: [float, ...] 各列的自然高度
    """
    total_modules = sum(len(modules) for _, modules, _, _, _ in group_info)
    group_vr = [_visual_rows(len(modules), mpr) for _, modules, _, _, mpr in group_info]
    total_vr = sum(group_vr)
    avg_modules = total_modules / ncols  # 平均每列模块数
    avg_vr = total_vr / ncols            # 平均每列视觉行数

    # 按模块数降序排列，大组优先分配
    sorted_groups = sorted(group_info, key=lambda x: len(x[1]), reverse=True)

    # 初始化各列状态
    col_groups = [[] for _ in range(ncols)]
    col_heights = [0.0] * ncols
    col_module_counts = [0] * ncols
    col_vr = [0] * ncols

    for group_name, modules, gw, gh, mpr in sorted_groups:
        # 在原始 group_info 中找到对应的视觉行数
        idx = next(i for i, (gn, gm, _, _, mp) in enumerate(group_info)
                   if gn == group_name and len(gm) == len(modules))
        vr = group_vr[idx]

        # 选择得分最低的列
        best_ci = 0
        best_score = float('inf')
        for ci in range(ncols):
            new_modules = col_module_counts[ci] + len(modules)
            new_vr = col_vr[ci] + vr
            module_dev = (new_modules / avg_modules) if avg_modules > 0 else 0
            vr_dev = (new_vr / avg_vr) if avg_vr > 0 else 0
            # 行数偏差平方惩罚：优先平衡视觉高度，而非仅平衡模块数
            score = module_dev + vr_dev * vr_dev
            if score < best_score:
                best_score = score
                best_ci = ci

        # 将组放入最佳列
        col_groups[best_ci].append((group_name, modules, gw, gh, mpr))
        col_heights[best_ci] += gh + ROW_GAP
        col_module_counts[best_ci] += len(modules)
        col_vr[best_ci] += vr

    # 减去最后一个组多余的 ROW_GAP
    for ci in range(ncols):
        if col_groups[ci]:
            col_heights[ci] -= ROW_GAP

    return col_groups, col_heights


# ============================================================
# 列数决策
# ============================================================

def compute_optimal_column_count(group_info):
    """
    尝试不同列数 (2~4)，选择综合评分最优的。

    评分考虑三个维度:
    1. 模块数平衡: 各列模块数的方差
    2. 视觉行数平衡: 各列视觉行数的方差
    3. 宽高比: 整体布局与 16:9 目标比值的偏差

    Args:
        group_info: [(name, modules, gw, gh, mpr), ...]

    Returns:
        最优列数 (2~4)
    """
    n_groups = len(group_info)
    if n_groups <= 1:
        return 1

    total_modules = sum(len(modules) for _, modules, _, _, _ in group_info)
    all_vr = [_visual_rows(len(modules), mpr) for _, modules, _, _, mpr in group_info]
    total_vr = sum(all_vr)
    best_ncols = 2
    best_score = float('inf')

    for ncols in range(2, min(n_groups, 4) + 1):
        col_groups, col_heights = _assign_groups_to_columns(group_info, ncols)

        # 维度1: 模块数不平衡度
        col_module_counts = [sum(len(m) for _, m, _, _, _ in cg) for cg in col_groups]
        avg_m = total_modules / ncols
        module_imbalance = sum((c - avg_m) ** 2 for c in col_module_counts)

        # 维度2: 视觉行数不平衡度
        col_vr = []
        for cg in col_groups:
            vr = sum(_visual_rows(len(modules), mpr) for _, modules, _, _, mpr in cg)
            col_vr.append(vr)
        avg_vr = total_vr / ncols
        vr_imbalance = sum((v - avg_vr) ** 2 for v in col_vr)

        # 维度3: 宽高比偏差
        max_gw = max(gw for _, _, gw, _, _ in group_info)
        total_w = ncols * max_gw + (ncols - 1) * COL_GAP
        max_vr = max(col_vr) if col_vr else 1
        est_row_h = MODULE_H + MODULE_GAP_Y
        est_height = max_vr * est_row_h
        ratio_diff = abs(total_w / est_height - TARGET_RATIO)

        # 综合评分
        score = module_imbalance + vr_imbalance * avg_m + ratio_diff * avg_m * 2
        if score < best_score:
            best_score = score
            best_ncols = ncols

    return best_ncols


# ============================================================
# 大量分组的专用布局（≥6 组）
# ============================================================

def _row_count(n_modules):
    """计算组的行数 = 标题行(1) + 模块行（固定 mpr=3）"""
    return int(np.ceil(n_modules / 3)) + 1


def _group_height_by_rows(n_rows):
    """根据行数反算组的高度（自然单位）"""
    return (HEADER_H + HEADER_GAP
            + n_rows * MODULE_H
            + max(0, n_rows - 1) * MODULE_GAP_Y
            + GROUP_PAD_BOTTOM)


def _find_combination(groups_with_rows, target, tolerance):
    """
    贪心算法: 从候选组中选出行数总和在 [target, target+tolerance] 范围内的组合。

    用于将组打包到一列中，使每列的总行数接近目标值。

    Args:
        groups_with_rows: [(name, modules, rows), ...] 候选组
        target: 目标行数
        tolerance: 容差

    Returns:
        (chosen, remaining) 或 (None, groups_with_rows)
        - chosen: 被选中的组
        - remaining: 剩余的组
    """
    used = [False] * len(groups_with_rows)
    chosen = []
    chosen_rows = 0

    for i, (name, modules, rows) in enumerate(groups_with_rows):
        if not used[i] and chosen_rows + rows <= target + tolerance:
            chosen.append((name, modules, rows))
            used[i] = True
            chosen_rows += rows

    # 检查是否达到目标
    if abs(chosen_rows - target) <= tolerance:
        remaining = [g for g, u in zip(groups_with_rows, used) if not u]
        return chosen, remaining

    return None, groups_with_rows


def _layout_many_groups(data):
    """
    分组 ≥ 6 时的专用布局策略。

    策略: 固定 mpr=3，按行数贪心填满每列。
    从目标行数 10 开始递减，逐步放宽到 5，直到找到能装下所有组的方案。

    Args:
        data: {group_name: [module_name, ...]}

    Returns:
        [[group_tuple, ...], ...] 各列的组列表
    """
    MPR = 3  # 大量分组时固定 mpr=3

    # 预计算每组的行数
    groups_with_rows = []
    for name, modules in data.items():
        groups_with_rows.append((name, modules, _row_count(len(modules))))

    # 尝试不同的目标行数和容差
    columns = []
    remaining = list(groups_with_rows)

    for target in range(10, 4, -1):          # 目标行数: 10 → 5
        for tolerance in range(0, len(remaining)):  # 容差: 0 → N
            cols = []
            r = list(remaining)
            while r:
                chosen, r = _find_combination(r, target, tolerance)
                if chosen is None:
                    break
                cols.append(chosen)

            if r is None or len(r) == 0:
                columns = cols
                break
        if columns:
            break

    # 兜底: 使用最大容差
    if not columns:
        cols = []
        r = list(groups_with_rows)
        while r:
            chosen, r = _find_combination(r, 10, len(remaining))
            if chosen is None:
                break
            cols.append(chosen)
        if cols:
            columns = cols

    # 将行数信息转为完整的组信息 (name, modules, gw, gh, mpr)
    result = []
    for col in columns:
        col_info = []
        for name, modules, rows in col:
            gw, gh = _raw_group_size(len(modules), MPR)
            col_info.append((name, modules, gw, gh, MPR))
        result.append(col_info)

    return result


# ============================================================
# 主布局函数（用于 matplotlib 渲染）
# ============================================================

def treemap_layout(data, canvas_w=None, canvas_h=None):
    """
    智能布局主函数: 计算组自然尺寸 → 分列 → 等比缩放 → 放置模块。

    流程:
    1. 计算每个组的自然尺寸
    2. 按模块数平衡分配组到各列
    3. 计算统一缩放因子，使内容适应画布
    4. 计算每个组和模块的精确像素坐标

    Args:
        data: {group_name: [module_name, ...]}
        canvas_w: 画布宽度（自然单位），默认 CANVAS_W
        canvas_h: 画布高度（自然单位），默认 CANVAS_H

    Returns:
        (group_rects, module_rects, content_bbox, scale)
        - group_rects: [(name, x, y, w, h, natural_h), ...]
        - module_rects: [(name, x, y, w, h, group_name), ...]
        - content_bbox: (min_x, min_y, max_x, max_y)
        - scale: 缩放因子
    """
    if canvas_w is None:
        canvas_w = CANVAS_W
    if canvas_h is None:
        canvas_h = CANVAS_H

    # 画布可用区域（扣除外边距）
    usable_w = canvas_w - 2 * OUTER_PAD_X
    usable_h = canvas_h - OUTER_PAD_TOP - OUTER_PAD_BOTTOM

    # --- 第一步: 分列 ---
    if len(data) >= 6:
        # 大量分组: 使用专用布局策略
        col_groups = _layout_many_groups(data)
        ncols = len(col_groups)
        col_heights = []
        for cg in col_groups:
            c_max_gw = max(gw for _, _, gw, _, _ in cg) if cg else 1
            rows, rh = _pack_groups_into_rows(cg, c_max_gw)
            h = sum(rh) + ROW_GAP * max(0, len(rows) - 1)
            col_heights.append(h)
    else:
        # 少量分组: 动态计算最优列数
        group_info = []
        for group_name, modules in data.items():
            n = len(modules)
            mpr = compute_modules_per_row(n)
            gw, gh = compute_group_size(n, mpr)
            group_info.append((group_name, modules, gw, gh, mpr))

        ncols = compute_optimal_column_count(group_info)
        col_groups, col_heights = _assign_groups_to_columns(group_info, ncols)

        # 可选: 调整 mpr 使列间高度更均匀
        if ADJUST_MPR:
            col_groups = _adjust_mpr_for_balance(col_groups)
            col_heights = []
            for cg in col_groups:
                c_max_gw = max(gw for _, _, gw, _, _ in cg) if cg else 1
                rows, rh = _pack_groups_into_rows(cg, c_max_gw)
                h = sum(rh) + ROW_GAP * max(0, len(rows) - 1)
                col_heights.append(h)

    # --- 第二步: 计算缩放因子 ---
    # 每列的最大组宽
    col_max_gw = []
    for cg in col_groups:
        if cg:
            col_max_gw.append(max(gw for _, _, gw, _, _ in cg))
        else:
            col_max_gw.append(1)

    max_col_h = max(col_heights) if col_heights and max(col_heights) > 0 else 1
    total_w = sum(col_max_gw) + (ncols - 1) * COL_GAP

    # 缩放因子 = min(宽度方向缩放, 高度方向缩放)，保证内容不超出画布
    scale_x = usable_w / total_w
    scale_y = usable_h / max_col_h
    scale = min(scale_x, scale_y)

    # --- 第三步: 计算列位置 ---
    scaled_gap = COL_GAP * scale
    col_w = [gw * scale for gw in col_max_gw]
    total_scaled_w = sum(col_w) + (ncols - 1) * scaled_gap

    # 水平居中
    start_x = (canvas_w - total_scaled_w) / 2
    col_x = []
    cx = start_x
    for w in col_w:
        col_x.append(cx)
        cx += w + scaled_gap

    # --- 第四步: 放置组和模块 ---
    group_rects = []
    module_rects = []

    for ci in range(ncols):
        # 列垂直居中
        col_total_h = col_heights[ci] * scale
        cy = OUTER_PAD_TOP + (usable_h - col_total_h) / 2

        c_max_gw = col_max_gw[ci]
        packed_rows, packed_row_heights = _pack_groups_into_rows(col_groups[ci], c_max_gw)
        col_w_val = col_w[ci]

        for row_idx, row_groups in enumerate(packed_rows):
            row_h = packed_row_heights[row_idx] * scale
            n_in_row = len(row_groups)

            if n_in_row == 1:
                # --- 单组占满整行 ---
                group_name, modules, gw, gh, mpr = row_groups[0]
                scaled_w = col_w_val
                scaled_h = gh * scale
                gx = col_x[ci]
                gy = canvas_h - cy - scaled_h

                group_rects.append((group_name, gx, gy, scaled_w, scaled_h, gh))

                # 计算组内模块位置
                n = len(modules)
                inner_w = scaled_w - 2 * GROUP_PAD_X * scale
                inner_top = gy + scaled_h - (HEADER_H + HEADER_GAP) * scale

                for i, mod in enumerate(modules):
                    m_row = i // mpr  # 模块所在行
                    m_col = i % mpr   # 模块所在列

                    # 该行实际模块数（最后一行可能不满）
                    row_start = m_row * mpr
                    row_end = min(row_start + mpr, n)
                    n_mods_in_row = row_end - row_start

                    # 缩放后的模块尺寸
                    mw = MODULE_W * scale
                    mh = MODULE_H * scale
                    mgx = MODULE_GAP_X * scale
                    mgy = MODULE_GAP_Y * scale

                    # 模块行总宽，居中放置
                    mod_row_w = n_mods_in_row * mw + (n_mods_in_row - 1) * mgx
                    row_x0 = gx + GROUP_PAD_X * scale + (inner_w - mod_row_w) / 2

                    mx = row_x0 + m_col * (mw + mgx)
                    my = inner_top - (m_row + 1) * mh - m_row * mgy

                    module_rects.append((mod, mx, my, mw, mh, group_name))

                cy += scaled_h + ROW_GAP * scale

            else:
                # --- 多组并排占一行 ---
                max_gw_in_row = max(gw for _, _, gw, _, _ in row_groups)
                small_g = [g for g in row_groups if g[2] < max_gw_in_row]
                large_g = [g for g in row_groups if g[2] >= max_gw_in_row]

                row_scaled_h = row_h
                gy = canvas_h - cy - row_scaled_h

                # 大组: 占据左侧空间
                for g in large_g:
                    group_name, modules, gw, gh, mpr = g
                    if small_g:
                        # 有小组时，大组宽度 = 列宽 - 小组宽 - 间距
                        small_natural_w = small_g[0][2] * scale
                        gw_used = col_w_val - small_natural_w - COL_GAP * scale
                    else:
                        gw_used = col_w_val
                    gx = col_x[ci]

                    group_rects.append((group_name, gx, gy, gw_used, row_scaled_h, gh))

                    # 放置大组内的模块
                    n = len(modules)
                    inner_w = gw_used - 2 * GROUP_PAD_X * scale
                    inner_top = gy + row_scaled_h - (HEADER_H + HEADER_GAP) * scale

                    for i, mod in enumerate(modules):
                        m_row = i // mpr
                        m_col = i % mpr

                        row_start = m_row * mpr
                        row_end = min(row_start + mpr, n)
                        n_mods_in_row = row_end - row_start

                        mw = MODULE_W * scale
                        mh = MODULE_H * scale
                        mgx = MODULE_GAP_X * scale
                        mgy = MODULE_GAP_Y * scale

                        mod_row_w = n_mods_in_row * mw + (n_mods_in_row - 1) * mgx
                        row_x0 = gx + GROUP_PAD_X * scale + (inner_w - mod_row_w) / 2

                        mx = row_x0 + m_col * (mw + mgx)
                        my = inner_top - (m_row + 1) * mh - m_row * mgy

                        module_rects.append((mod, mx, my, mw, mh, group_name))

                # 小组: 靠右放置
                for g in small_g:
                    group_name, modules, gw, gh, mpr = g
                    natural_w = gw * scale
                    natural_h = gh * scale
                    gx = col_x[ci] + col_w_val - natural_w
                    gy_small = gy + row_scaled_h - natural_h

                    group_rects.append((group_name, gx, gy_small, natural_w, natural_h, gh))

                    # 放置小组内的模块
                    n = len(modules)
                    inner_w = natural_w - 2 * GROUP_PAD_X * scale
                    inner_top = gy_small + natural_h - (HEADER_H + HEADER_GAP) * scale

                    for i, mod in enumerate(modules):
                        m_row = i // mpr
                        m_col = i % mpr

                        row_start = m_row * mpr
                        row_end = min(row_start + mpr, n)
                        n_mods_in_row = row_end - row_start

                        mw = MODULE_W * scale
                        mh = MODULE_H * scale
                        mgx = MODULE_GAP_X * scale
                        mgy = MODULE_GAP_Y * scale

                        mod_row_w = n_mods_in_row * mw + (n_mods_in_row - 1) * mgx
                        row_x0 = gx + GROUP_PAD_X * scale + (inner_w - mod_row_w) / 2

                        mx = row_x0 + m_col * (mw + mgx)
                        my = inner_top - (m_row + 1) * mh - m_row * mgy

                        module_rects.append((mod, mx, my, mw, mh, group_name))

                cy += row_scaled_h + ROW_GAP * scale

    # --- 第五步: 水平居中微调 ---
    min_x = min(gx for _, gx, _, _, _, _ in group_rects)
    min_y = min(gy for _, gx, gy, _, _, _ in group_rects)
    max_x = max(gx + gw for _, gx, gy, gw, _, _ in group_rects)
    max_y = max(gy + gh for _, gx, gy, _, gh, _ in group_rects)

    actual_cx = (min_x + max_x) / 2
    canvas_cx = canvas_w / 2
    shift_x = canvas_cx - actual_cx

    # 如果内容整体偏左或偏右，水平平移使其居中
    if abs(shift_x) > 1e-6:
        group_rects = [
            (name, gx + shift_x, gy, gw, gh, nat_h)
            for name, gx, gy, gw, gh, nat_h in group_rects
        ]
        module_rects = [
            (name, mx + shift_x, my, mw, mh, grp)
            for name, mx, my, mw, mh, grp in module_rects
        ]
        min_x += shift_x
        max_x += shift_x

    content_bbox = (min_x, min_y, max_x, max_y)

    return group_rects, module_rects, content_bbox, scale
