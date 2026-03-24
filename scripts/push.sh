#!/bin/bash
# 推送 mappings.csv 到 GitHub 仓库 susansheng/color-mappings
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CSV_FILE="$PROJECT_DIR/csv/mappings.csv"
REPO_DIR="$PROJECT_DIR/csv"
GH="/Users/sxsheng/gh_2.62.0_macOS_arm64/bin/gh"
MESSAGE="${1:-更新映射规则}"

# 检查文件存在
if [ ! -f "$CSV_FILE" ]; then
    echo "错误: $CSV_FILE 不存在"
    echo "请先将 susansheng/color-mappings 仓库克隆到 csv/ 目录："
    echo "  cd $PROJECT_DIR && git clone git@github.com:susansheng/color-mappings.git csv"
    exit 1
fi

# 先校验
echo "校验 CSV 格式..."
python3 "$SCRIPT_DIR/validate.py" "$CSV_FILE"
if [ $? -ne 0 ]; then
    echo "校验失败，终止推送"
    exit 1
fi

# 推送
cd "$REPO_DIR"
git add mappings.csv
if git diff --cached --quiet; then
    echo "没有变更，无需推送"
    exit 0
fi

git commit -m "$MESSAGE"
git push origin main
echo "推送成功"
