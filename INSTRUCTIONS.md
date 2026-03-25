# Q_Color Mapper — CSV 映射规则编写指南

> 本文档定义了 Figma 插件 Q_Color Mapper 的 CSV 映射表格式规范。
> 任何 AI 工具（Claude、Codex、Kimi 等）都可以参考本文档来生成和编辑映射规则。

## 概述

Q_Color Mapper 是一个 Figma 插件，通过读取远程 CSV 映射表来批量替换设计稿中的颜色和圆角。

**工作流程：**
1. **（可选）从 Figma 画布生成 CSV** — 用户在 Figma 中创建左右对照的颜色映射画布，AI 通过 Figma API 自动解析生成 CSV（`scripts/figma2csv.py`）
2. AI 根据用户需求编辑 `mappings.csv`（或基于第 1 步生成的 CSV 微调）
3. 校验 CSV 格式（`scripts/validate.py`）
4. 推送到 GitHub（`scripts/push.sh`）
5. 用户在 Figma 插件中点「刷新」→「扫描」→「预览」→「替换」

**CSV 仓库：** `<用户名>/color-mappings`（GitHub，首次使用时自动创建）
**CSV URL：** `https://raw.githubusercontent.com/<用户名>/color-mappings/main/mappings.csv`
**本地路径：** `csv/mappings.csv`

---

## 首次配置

运行一次即可，后续使用不需要重复：

```bash
# 前提：已安装 gh CLI 并登录（gh auth login）
bash scripts/setup.sh
```

自动完成：
1. 检测 GitHub 登录状态
2. 创建 `<用户名>/color-mappings` 公开仓库（已存在则跳过）
3. 克隆仓库到本地 `csv/` 目录
4. 如果已有 CSV 则推送初始版本
5. 输出 CSV raw URL（配置到 Figma 插件中）

也可以在首次 `push.sh` 时自动触发，无需手动调用。

---

## CSV 格式规范

### 基本结构

```csv
name,target,C_color,Q_color
```

| 列 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | 匹配源：Variable/Style 名称 或 源色值 |
| `target` | 是 | 目标值：目标色值或目标圆角 |
| `C_color` | 否 | 开发辅助列（GitHub 表格展示用，插件忽略） |
| `Q_color` | 否 | 开发辅助列（GitHub 表格展示用，插件忽略） |

**重要约束：**
- 所有行的列数必须一致（空列也要加 `,`），否则 GitHub 不渲染表格
- CSV 值含逗号时需用双引号包裹（如 `"rgba(0, 212, 227, 0.1)"`）
- 表头行会被自动跳过（匹配 `name|match|source|原|源|匹配`）

---

## 规则类型

### 1. 颜色规则 — 按名称匹配

用 Variable 或 Style 的名称来匹配，这是最精确的方式。

```csv
Core/Color/Blue/Blue-1,#00CAD9,,
Primary/Brand Color,#FA6E0A,,
```

**匹配逻辑：**
- 精确匹配：`Core/Color/Blue/Blue-1`
- 路径尾部匹配：CSV 写 `Blue-1`，可匹配 `Core/Color/Blue/Blue-1`
- 后缀分隔匹配：名称后跟 `·` 或 `#` 等分隔符也可匹配

**名称带源色值后缀（用于文本混合颜色 fallback）：**
```csv
Core/Color/Blue-1·#006FF6,#00CAD9,,
```
`·#006FF6` 会被自动提取为 `sourceHex`，名称部分 `Core/Color/Blue-1` 用于匹配。
这是因为 Figma API 无法直接获取文本字符级别的 Variable 绑定，需要通过源色值 fallback 匹配。

### 2. 颜色规则 — 按色值匹配

当 name 以 `#` 开头时，自动识别为色值匹配（兜底方式）。

```csv
#006FF6,#00CAD9,,
#FF6600,#FA6E0A,,
```

**色值格式：**
- 6 位 hex：`#RRGGBB`（如 `#006FF6`）
- 3 位 hex：`#RGB`（如 `#FFF`，自动展开为 `#FFFFFF`）
- 8 位 hex：`#RRGGBBAA`（如 `#FF000080`，红色 50% 透明度）
- 大小写不敏感

**容差：** 色值匹配支持容差（插件端可调，默认 RGB 每通道 ±2）

### 3. 渐变颜色规则

用 `-` 连接多个色值表示渐变色标。

```csv
#006FF6-#006FF6,#FA6E0A-#FA4A0A,,
纯色变渐变示例,#FF0000-#00FF00,,
```

**渐变规则：**
- 纯色 → 纯色：直接替换
- 纯色 → 渐变（多色）：创建线性渐变 `GRADIENT_LINEAR`
- 渐变 → 渐变：替换色标颜色，保持原渐变方向和位置

### 4. 圆角规则

以 `radius:` 前缀标识。

```csv
radius:8,12,,
radius:4,6,,
radius:0,8,,
```

格式：`radius:<源圆角>,<目标圆角>`
- 源圆角 8px → 目标圆角 12px
- 支持统一圆角和混合圆角（四角不同时逐角匹配）
- 容差固定 0.5px

---

## 辅助列说明（C_color / Q_color）

这两列是开发辅助列，用于在 GitHub 表格中直观显示颜色对应关系。插件不读取这两列。

格式与 `name`/`target` 对应：
```csv
name,target,C_color,Q_color
Core/Color/Blue-1·#006FF6,#00CAD9,#006FF6_1,#00CAD9
#006FF6-#006FF6,#FA6E0A-#FA4A0A,"#006FF6_2 | #006FF6_3","#FA6E0A_2 | #FA4A0A_3"
```

- `_1`、`_2` 等后缀用于区分同色值的不同用途
- `|` 分隔多个色标
- 渐变值含逗号时需双引号包裹

---

## 完整示例

```csv
name,target,C_color,Q_color
Core/Color/Blue/Blue-1·#006FF6,#00CAD9,#006FF6,#00CAD9
Core/Color/Blue/Blue-2,#00B5C4,,
Primary Color,#FA6E0A,,
#FF6600,#00CAD9,#FF6600,#00CAD9
#006FF6-#006FF6,#FA6E0A-#FA4A0A,"#006FF6 | #006FF6","#FA6E0A | #FA4A0A"
radius:8,12,8,12
radius:4,6,4,6
```

---

## 辅助脚本

### 校验 CSV

```bash
python3 scripts/validate.py csv/mappings.csv
```

检查项：
- 列数一致性
- 色值格式合法性（#RGB / #RRGGBB / #RRGGBBAA）
- 圆角规则格式
- 重复规则检测

### 预览规则

```bash
python3 scripts/preview.py csv/mappings.csv
```

以表格形式展示当前所有规则，分颜色和圆角两组。

### 从 Figma 画布生成 CSV

```bash
python3 scripts/figma2csv.py <figma_url> [--token TOKEN] [-o csv/mappings.csv]
```

从 Figma 设计文件中自动提取颜色映射规则。

**Figma 画布约定（左右对照）：**
- 左侧放源色色块 + 标签（文本内容为 Variable/Style 名称，如 `Core/Color/Blue/Blue-1·#006FF6`）
- 右侧放目标色色块 + 标签（文本内容为目标色值，如 `#00CAD9`）
- 左右标签按 Y 坐标对齐，脚本自动配对
- 箭头、色块等视觉元素可选，脚本只解析 TEXT 节点

**Token 传入方式（不会写入文件）：**
1. `--token` 命令行参数
2. `FIGMA_TOKEN` 环境变量
3. 交互式输入

### 推送到 GitHub

```bash
bash scripts/push.sh "更新说明"
```

自动 commit 并 push `csv/mappings.csv` 到 `susansheng/color-mappings` 仓库。

---

## AI 操作指南

### 场景 A：用户给了 Figma 文件链接

1. **解析** 运行 `python3 scripts/figma2csv.py <url> --token $FIGMA_TOKEN`
2. **预览** 运行 `python3 scripts/preview.py csv/mappings.csv` 让用户确认
3. **微调** 如果需要修改，编辑 CSV
4. **校验** 运行 `python3 scripts/validate.py csv/mappings.csv`
5. **推送** 用户确认后运行 `bash scripts/push.sh "描述"`

### 场景 B：用户用自然语言描述需求

1. **读取** `csv/mappings.csv` 了解当前规则
2. **理解** 用户需求（替换什么颜色/圆角，按名称还是色值匹配）
3. **编辑** CSV 文件，遵循上述格式规范
4. **校验** 运行 `python3 scripts/validate.py csv/mappings.csv`
5. **预览** 运行 `python3 scripts/preview.py csv/mappings.csv` 让用户确认
6. **推送** 用户确认后运行 `bash scripts/push.sh "描述"`

### 常见任务映射

| 用户说 | AI 做 |
|-------|------|
| "这个 Figma 文件，帮我生成映射" | 运行 figma2csv.py 解析 |
| "把蓝色换成橙色" | 添加色值匹配规则 `#蓝色hex,#橙色hex` |
| "把 Blue token 换成 Orange" | 添加名称匹配规则 `Blue-1,#橙色hex` |
| "圆角从 8 改成 12" | 添加圆角规则 `radius:8,12` |
| "删除某条规则" | 从 CSV 中移除对应行 |
| "查看当前规则" | 运行 preview 脚本 |
| "整理/排序规则" | 按类型分组排序（名称匹配 → 色值匹配 → 圆角） |
