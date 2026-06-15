# Markdown 复用机制说明

GUI 模式下，非首次运行时对已生成 Markdown 文件的缓存与复用机制。

## 核心数据结构

`MainWindow.__init__()` 中维护 5 个状态：

| 变量 | 类型 | 作用 |
|------|------|------|
| `_session_processed` | `set` | 记录本次会话已处理过的 Excel 路径，防止重复调用 `generate_marp_md` |
| `_generated_md_files` | `{excel_path: md_path}` | Excel 到 Markdown 的映射，供 Apply 操作定位目标文件 |
| `_original_params` | `{md_path: {config_key: value}}` | 首次生成时 `config.py` 的默认值快照，作为缩放比例的分母 |
| `_initial_css` | `{md_path: {css_key: value}}` | 首次生成时文件中实际的 CSS 像素值，作为缩放的基准锚点 |
| `_css_state` | `{md_path: {css_key: value}}` | 当前 CSS 状态的运行时记录（写入但未被读取消费） |

## 会话级去重：`_session_processed`

- 与 `GenerateWorker` 共享同一个 `set` 对象（可变引用传递）
- Worker 中检查：`if file_path not in self._session_processed`
  - 不在集合中 → 调用 `generate_marp_md` 生成新文件，然后 `add` 进集合
  - 已在集合中 → 跳过生成，日志输出"复用已有 Markdown"
- 集合在整个会话生命周期内不清空，重启应用后重置

## 文件映射：`_generated_md_files`

- Worker 每处理一个文件（无论是否复用）都会记录 `excel_path → md_path` 映射
- 被以下场景使用：
  - `_apply_pending_params()` — 遍历所有已知 md 文件执行 CSS 编辑
  - `_on_apply_params()` — 遍历所有已知 md 文件调用 `apply_params_to_md`
  - `_on_params_changed()` — 判断是否有已生成文件，控制"应用参数"按钮的启用状态

## 两套 Apply 路径

### 路径 A：`_apply_pending_params()`（生成时自动触发）

- 触发时机：用户点击"生成"时，若存在未应用的参数修改（`_pending_params` 不为空），在 Worker 启动前自动执行
- 实现方式：在 `main_window.py` 中直接用正则替换 CSS 值
- 处理范围：颜色、字号、间距、圆角、边框宽度、域内边距等

### 路径 B：`_on_apply_params()`（用户手动触发）

- 触发时机：用户点击"应用参数到 Markdown"按钮
- 实现方式：委托给 `md_editor.apply_params_to_md()`，使用 `_sub_in_css_blocks` 确保正则不跨 CSS 规则边界
- 处理范围：路径 A 的全部参数 + 模块尺寸（MODULE_W/MODULE_H）、行高、字体族

### 两者差异

| 维度 | 路径 A | 路径 B |
|------|--------|--------|
| 触发方式 | 生成时自动 | 手动点击按钮 |
| 实现位置 | `main_window.py` 内联逻辑 | `md_editor.apply_params_to_md` |
| 参数覆盖 | 部分参数 | 全部参数 |
| 边界安全 | 使用 `_sub_in_css_blocks` | 使用 `_sub_in_css_blocks` |

## 缩放计算机制

所有数值型参数的修改都基于比例缩放：

```
target_css = initial_css[css_key] × (config_new / config_old)
```

- `initial_css`：首次生成时从文件提取的实际 CSS 像素值（锚点，不变）
- `config_old`：首次生成时 `config.py` 中的原始配置值（分母）
- `config_new`：用户在 UI 中设置的新配置值（分子）

**关键约束**：`_initial_css` 必须保持为首次生成时的值，不可被后续修改覆盖。否则缩放基准会偏移。

## 完整生命周期：生成 → 应用 → 再生成

### 第 1 次点击"生成"

1. `_session_processed` 为空 → 调用 `generate_marp_md` 生成 md 文件
2. 记录 `_session_processed.add(file_path)`
3. Worker 完成后，`_on_finished()` 从文件提取 CSS 快照：
   - `_initial_css[md_path] = css.copy()`（不可变基准）
   - `_css_state[md_path] = css`（运行时状态）

此时状态：
- md 文件在磁盘上，值来自 `config.py` 默认值
- `_initial_css` = 文件中的 CSS 像素值
- `_original_params` = `config.py` 中的配置值

### 用户调整参数后点击"应用参数"

1. `_on_apply_params()` 调用 `apply_params_to_md()`
2. 函数读取磁盘上的 md 文件，按比例缩放 CSS 值，写回文件
3. `_css_state` 更新为新的 CSS 状态
4. `_initial_css` **不变**（仍为首次生成时的值）

此时状态：
- md 文件中的 CSS 已被修改
- `_initial_css` 仍为原始基准

### 再次点击"生成"

1. `_session_processed` 已包含该文件 → **跳过** `generate_marp_md`，复用已有 md 文件
2. Worker 仍然记录 `_original_params`（用当前 `config.py` 默认值覆盖）
3. `_on_finished()` 从 md 文件重新提取 CSS → **覆盖** `_initial_css`

**后果**：`_initial_css` 被重置为用户修改后的 CSS 值。后续 Apply 的缩放基准变为用户修改后的版本，而非最初的 config 默认值。

## 状态流转图

```
┌─────────────────────────────────────────────────────┐
│                    第 1 次生成                         │
│  generate_marp_md → 磁盘 md 文件                      │
│  _initial_css = extract(file)   ← 首次基准            │
│  _original_params = config 默认值                      │
│  _session_processed.add(file)                        │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│                  应用参数（手动）                       │
│  apply_params_to_md(file, new, orig, init_css)       │
│  → 按比例缩放写入磁盘                                  │
│  _css_state = extract(file)    ← 更新运行时状态        │
│  _initial_css 不变             ← 基准锚点保持           │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│                  再次生成                              │
│  _session_processed 命中 → 跳过 generate_marp_md      │
│  但 _on_finished() 仍会:                              │
│    _initial_css = extract(file) ← 基准被重置!          │
│    _original_params = config 默认值 ← 分母被重置!       │
└─────────────────────────────────────────────────────┘
```

## 相关代码位置

- `src/gui/main_window.py` — 5 个状态变量、两条 Apply 路径、Worker、生成决策逻辑
- `src/gui/md_editor.py` — `extract_params_from_md`、`apply_params_to_md`、`_sub_in_css_blocks`
