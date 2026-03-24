# Codex 指令 — Q_Color Mapper CSV 编辑

> 本文件供 Codex CLI 使用。调用方式：
> `codex exec -s workspace-write -C /Users/sxsheng/Documents/代码/figma-color-mapper-skill "任务描述"`

## 你的角色

编辑 `csv/mappings.csv` 文件，生成 Figma 插件 Q_Color Mapper 的颜色/圆角映射规则。
也可以从 Figma 文件自动生成 CSV：`FIGMA_TOKEN=<token> python3 scripts/figma2csv.py <figma_url>`

## 格式规范

详见 `INSTRUCTIONS.md`。核心要点：

- 4 列：`name,target,C_color,Q_color`（所有行列数一致）
- 颜色 — 按名称匹配：`Variable/Style名称,#目标hex,,`
- 颜色 — 按色值匹配：`#源hex,#目标hex,,`
- 渐变：用 `-` 连接多色（如 `#FF0000-#00FF00`）
- 圆角：`radius:源值,目标值,,`
- 色值大写 6 位 hex
- 含逗号的值用双引号包裹

## 编辑后

运行校验：`python3 scripts/validate.py csv/mappings.csv`
