# 第五阶段：高级功能实现计划

## 概述

本阶段将为应用架构图生成器添加三个核心高级功能：历史记录保存、模板功能和快捷键支持。

## 目标

1. **历史记录保存**：使用QSettings存储最近打开的文件，方便用户快速访问
2. **模板功能**：支持保存和加载参数配置模板
3. **快捷键支持**：添加常用操作的快捷键

## 实现方案

### 1. 历史记录保存

**实现位置**：`src/gui/main_window.py` + `src/gui/file_selector.py`

**功能设计**：
- 使用QSettings存储最近打开的文件路径（最多保存10个）
- 在文件选择器中添加"最近文件"下拉菜单
- 启动时自动加载上次的文件列表
- 文件不存在时自动从历史记录中移除

**QSettings配置**：
```python
# 组织名称和应用名称已在app.py中设置
# OrganizationName: "架构图生成器"
# ApplicationName: "应用架构图生成器"

# 存储键值
settings.setValue("recent_files", file_list)  # QStringList
settings.setValue("last_dir", last_directory)  # 最后打开的目录
```

**UI修改**：
- 在`FileSelector`中添加"最近文件"按钮
- 点击显示下拉菜单，列出最近打开的文件
- 选择文件后直接添加到文件列表

### 2. 模板功能

**实现位置**：新建`src/gui/template_manager.py` + 修改`src/gui/params_panel.py`

**功能设计**：
- 支持将当前参数配置保存为模板
- 支持加载已保存的模板
- 模板存储在用户目录下（如`~/.架构图生成器/templates/`）
- 模板格式为JSON文件

**模板文件格式**：
```json
{
  "name": "默认模板",
  "description": "默认参数配置",
  "created_at": "2026-06-09T10:00:00",
  "params": {
    "GROUP_BG": "#E0E0E0",
    "GROUP_HEADER_COLOR": "#1A73E8",
    "MODULE_BG_COLOR": "#C4D8FC",
    "MODULE_W": 1.5,
    "MODULE_H": 0.5,
    "COL_GAP": 0.4,
    "ROW_GAP": 0.25,
    "MODULE_FONT_SIZE": 10,
    "GROUP_HEADER_FONT_SIZE": 12,
    "ADJUST_MPR": true,
    "TARGET_RATIO": 1.33
  }
}
```

**UI修改**：
- 在`ParamsPanel`中添加模板管理区域
- 包含"保存模板"和"加载模板"按钮
- 加载模板时显示模板选择对话框

### 3. 快捷键支持

**实现位置**：`src/gui/main_window.py`

**快捷键设计**：
| 快捷键 | 功能 | 说明 |
|--------|------|------|
| Ctrl+O | 打开文件 | 触发文件选择器的添加文件功能 |
| Ctrl+S | 保存模板 | 触发参数面板的保存模板功能 |
| Ctrl+Enter | 生成架构图 | 触发生成按钮 |
| Ctrl+Q | 退出应用 | 关闭主窗口 |

**实现方式**：
- 使用PySide6的`QShortcut`类
- 在`MainWindow`的`_setup_ui`方法中创建快捷键
- 绑定到对应的槽函数

### 4. 导出选项增强

**现状**：已支持PNG和PPTX导出

**增强内容**：
- 添加HTML导出选项（使用MarP的`--html`参数）
- 在导出格式下拉菜单中添加"HTML"选项
- 更新`GenerateWorker`以支持HTML生成

## 实现步骤

### 步骤1：创建模板管理器
1. 新建`src/gui/template_manager.py`
2. 实现`TemplateManager`类
3. 提供保存、加载、删除模板的方法
4. 实现模板选择对话框

### 步骤2：修改参数面板
1. 在`ParamsPanel`中添加模板管理按钮
2. 集成`TemplateManager`
3. 实现保存和加载模板的槽函数

### 步骤3：修改文件选择器
1. 添加"最近文件"按钮
2. 实现最近文件菜单
3. 集成QSettings存储历史记录

### 步骤4：修改主窗口
1. 添加快捷键支持
2. 在启动时加载历史记录
3. 在关闭时保存历史记录

### 步骤5：增强导出功能
1. 在导出格式下拉菜单中添加HTML选项
2. 修改`GenerateWorker`支持HTML生成
3. 更新日志显示

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `src/gui/template_manager.py` | 新建：模板管理器 |
| `src/gui/params_panel.py` | 添加模板管理UI |
| `src/gui/file_selector.py` | 添加最近文件功能 |
| `src/gui/main_window.py` | 添加快捷键、历史记录管理 |

## 验证方法

1. **历史记录验证**：
   - 打开应用，选择文件并生成
   - 关闭应用，重新打开
   - 检查"最近文件"菜单是否显示之前的文件

2. **模板功能验证**：
   - 调整参数，点击"保存模板"
   - 重置参数，点击"加载模板"
   - 检查参数是否恢复

3. **快捷键验证**：
   - 测试Ctrl+O、Ctrl+S、Ctrl+Enter、Ctrl+Q
   - 检查是否正确触发对应功能

4. **HTML导出验证**：
   - 选择HTML导出格式
   - 生成文件并检查HTML是否正确

## 注意事项

1. **跨平台兼容性**：
   - QSettings在Windows上使用注册表，在macOS上使用plist，在Linux上使用ini文件
   - 模板文件存储在用户目录下，确保跨平台兼容

2. **错误处理**：
   - 文件不存在时从历史记录中移除
   - 模板加载失败时显示错误信息
   - 快捷键冲突时显示警告

3. **用户体验**：
   - 历史记录菜单显示文件名和完整路径
   - 模板管理界面清晰易用
   - 快捷键提示显示在菜单项旁边
