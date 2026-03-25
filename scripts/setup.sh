#!/bin/bash
# 首次配置：创建 color-mappings 仓库并初始化 CSV
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CSV_DIR="$PROJECT_DIR/csv"
GH="/Users/sxsheng/gh_2.62.0_macOS_arm64/bin/gh"

# 获取当前 GitHub 用户名
GH_USER=$($GH api user --jq '.login' 2>/dev/null)
if [ -z "$GH_USER" ]; then
    echo "错误: 未登录 GitHub CLI"
    echo "请先运行: $GH auth login"
    exit 1
fi
echo "  GitHub 用户: $GH_USER"

REPO_NAME="color-mappings"
REPO_FULL="$GH_USER/$REPO_NAME"

# 检查仓库是否已存在
if $GH repo view "$REPO_FULL" &>/dev/null; then
    echo "  仓库 $REPO_FULL 已存在"
else
    echo "  创建仓库 $REPO_FULL ..."
    $GH repo create "$REPO_FULL" --public --description "Q_Color Mapper 颜色/圆角映射表"
    echo "  仓库已创建"
fi

# 克隆或更新本地 csv 目录
if [ -d "$CSV_DIR/.git" ]; then
    echo "  本地 csv/ 已关联 git 仓库"
    cd "$CSV_DIR" && git pull origin main 2>/dev/null || true
else
    # 清理 csv 目录中非 git 文件（保留已生成的 mappings.csv）
    TEMP_CSV=""
    if [ -f "$CSV_DIR/mappings.csv" ]; then
        TEMP_CSV=$(mktemp)
        cp "$CSV_DIR/mappings.csv" "$TEMP_CSV"
    fi

    rm -rf "$CSV_DIR"
    git clone "https://github.com/$REPO_FULL.git" "$CSV_DIR" 2>/dev/null || {
        # 新仓库可能是空的，手动初始化
        mkdir -p "$CSV_DIR"
        cd "$CSV_DIR"
        git init
        git remote add origin "https://github.com/$REPO_FULL.git"
    }

    # 恢复已生成的 CSV
    if [ -n "$TEMP_CSV" ] && [ -f "$TEMP_CSV" ]; then
        cp "$TEMP_CSV" "$CSV_DIR/mappings.csv"
        rm "$TEMP_CSV"
    fi
fi

# 如果有 CSV 就初始推送
if [ -f "$CSV_DIR/mappings.csv" ]; then
    cd "$CSV_DIR"
    git add mappings.csv
    if ! git diff --cached --quiet 2>/dev/null; then
        git commit -m "feat: 初始化颜色映射表"
        git branch -M main
        git push -u origin main
        echo "  CSV 已推送到 GitHub"
    else
        echo "  CSV 无变更"
    fi
elif [ -f "$CSV_DIR/mappings.example.csv" ]; then
    # 用示例文件初始化
    cd "$CSV_DIR"
    cp mappings.example.csv mappings.csv
    git add mappings.csv
    git commit -m "feat: 初始化颜色映射表（示例）"
    git branch -M main
    git push -u origin main
    echo "  示例 CSV 已推送到 GitHub"
fi

# 输出配置信息
RAW_URL="https://raw.githubusercontent.com/$REPO_FULL/main/mappings.csv"
echo ""
echo "  ══════════════════════════════════════"
echo "  配置完成！"
echo ""
echo "  仓库: https://github.com/$REPO_FULL"
echo "  CSV URL: $RAW_URL"
echo ""
echo "  请在 Figma 插件中配置以上 CSV URL"
echo "  ══════════════════════════════════════"
