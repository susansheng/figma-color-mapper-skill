#!/bin/bash
# 推送 mappings.csv 到 GitHub color-mappings 仓库
# 如果仓库或本地 git 未初始化，自动调用 setup.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CSV_FILE="$PROJECT_DIR/csv/mappings.csv"
CSV_DIR="$PROJECT_DIR/csv"
MESSAGE="${1:-更新映射规则}"

# 检查 CSV 文件
if [ ! -f "$CSV_FILE" ]; then
    echo "错误: $CSV_FILE 不存在"
    echo "请先运行 figma2csv.py 生成 CSV"
    exit 1
fi

# 如果本地 csv/ 不是 git 仓库，自动运行 setup
if [ ! -d "$CSV_DIR/.git" ]; then
    echo "  首次推送，自动初始化仓库..."
    bash "$SCRIPT_DIR/setup.sh"
    exit 0
fi

# 校验
echo "  校验 CSV 格式..."
python3 "$SCRIPT_DIR/validate.py" "$CSV_FILE"

# 推送
cd "$CSV_DIR"
git add mappings.csv
if git diff --cached --quiet; then
    echo "  没有变更，无需推送"
    exit 0
fi

git commit -m "$MESSAGE"
git push origin main
echo "  推送成功"
