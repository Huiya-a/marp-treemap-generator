# Marp Markdown 规则速查

## 1. Frontmatter 声明

文件顶部必须用 `---` 包裹，否则 Marp 不会识别为演示文稿：

```yaml
---
marp: true
theme: default
paginate: true
---
```

常用 frontmatter 选项：

| 选项 | 说明 | 示例值 |
|------|------|--------|
| `marp` | 启用 Marp | `true`（必须） |
| `theme` | 主题 | `default`, `gaia`, `uncover` |
| `paginate` | 页码 | `true`, `false`, `skipFirst` |
| `header` | 页眉 | 自定义文本 |
| `footer` | 页脚 | 自定义文本 |
| `backgroundColor` | 背景色 | `#ffffff`, `white` |
| `color` | 文字颜色 | `#333` |
| `backgroundImage` | 全局背景图 | `url('https://...')` |
| `image` | 背景图（简写） | `url('img.png')` |
| `class` | CSS class | `invert` |
| `style` | 内联样式 | 可选，少用 |

## 2. `---` 分页符

普通 Markdown 中 `---` 是水平线，Marp 中它是**幻灯片分隔符**，新起一页：

```markdown
# 第一页

内容

---

# 第二页

内容
```

## 3. 注释指令（逐页控制）

用 HTML 注释语法注入控制指令，作用于**当前页**：

```markdown
<!-- _paginate: false -->        <!-- 本页关闭页码 -->
<!-- _class: lead -->            <!-- 给本页加 CSS class -->
<!-- _backgroundColor: #000 -->   <!-- 本页背景色 -->
<!-- _color: white -->            <!-- 本页文字颜色 -->
<!-- _header: "" -->              <!-- 本页隐藏页眉 -->
<!-- _footer: "" -->              <!-- 本页隐藏页脚 -->
<!-- _backgroundImage: url('...') --> <!-- 本页背景图 -->
```

## 4. `bg` 图片指令

在图片链接中加 `bg` 实现背景图或分栏布局：

```markdown
![bg](image.png)                  <!-- 整页背景图，铺满 -->
![bg left:40%](image.png)         <!-- 左侧40%放图，右侧放内容 -->
![bg right:50%](image.png)        <!-- 右侧50%放图，左侧放内容 -->
![bg contain](image.png)          <!-- 图片不裁切，居中显示 -->
![bg fit](image.png)              <!-- 图片缩放适应，不裁切 -->
![bg blur](image.png)             <!-- 背景图模糊处理 -->
```

## 5. 内置主题

Marp 自带三个主题，控制整体排版风格：

- `default` — 默认简洁风格
- `gaia` — 现代感更强，带侧边栏样式
- `uncover` — 深色背景，适合科技感展示

## 6. CSS 自定义

用 `<style>` 标签直接写 CSS，作用于所有页或特定 class：

```markdown
<style>
  section {
    font-size: 28px;
  }
  section.lead {
    justify-content: center;
    text-align: center;
  }
  h1 {
    color: #e74c3c;
  }
</style>
```

## 7. 支持的 Markdown 语法

标准 Markdown 语法均支持：

- 标题（h1-h6）
- 加粗、斜体、删除线
- 有序/无序列表
- 链接、图片
- 表格
- 代码块（支持语法高亮）
- 引用块
- LaTeX 数学公式：`$...$`（行内），`$$...$$`（块级）
- HTML（部分 CSS 可直接内联）

## 8. 常用命令

```bash
# 转 HTML（默认）
marp slides.md -o slides.html

# 转 PDF
marp slides.md --pdf -o slides.pdf

# 转 PowerPoint
marp slides.md --pptx -o slides.pptx

# 启动本地预览服务器（实时热更新）
marp slides.md --preview

# 允许 HTML（需显式开启）
marp slides.md --html -o slides.html

# 指定主题
marp slides.md --theme gaia -o slides.html
```
