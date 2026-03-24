# -*- coding: utf-8 -*-
"""校验 Q_Color Mapper 的 CSV 映射表格式"""

import csv
import re
import sys
from pathlib import Path

# 合法的 hex 格式
HEX_RE = re.compile(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$')
# 表头关键词
HEADER_RE = re.compile(r'^(name|match|source|原|源|匹配)', re.IGNORECASE)
# 圆角规则前缀
RADIUS_RE = re.compile(r'^radius:\s*[\d.]+$')


def normalize_hex(h: str) -> str:
    """归一化 hex 色值"""
    h = h.strip().strip('"').strip("'").upper()
    if not h.startswith('#'):
        h = '#' + h
    if len(h) == 4:  # #RGB -> #RRGGBB
        h = '#' + h[1]*2 + h[2]*2 + h[3]*2
    return h


def is_valid_hex(h: str) -> bool:
    """检查是否为合法 hex 色值"""
    return bool(HEX_RE.match(normalize_hex(h)))


def validate_color_str(s: str) -> list[str]:
    """校验色值字符串（支持 - 连接的渐变），返回错误列表"""
    errors = []
    parts = s.split('-')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if not is_valid_hex(part):
            errors.append(f'非法色值: {part}')
    return errors


def validate_csv(filepath: str) -> tuple[list[str], list[str]]:
    """校验 CSV 文件，返回 (errors, warnings)"""
    errors = []
    warnings = []
    path = Path(filepath)

    if not path.exists():
        return [f'文件不存在: {filepath}'], []

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return ['CSV 文件为空'], []

    # 检查列数一致性
    col_counts = set(len(row) for row in rows)
    if len(col_counts) > 1:
        errors.append(f'列数不一致: {col_counts}（所有行列数必须相同，GitHub 才能渲染表格）')

    # 跳过表头
    start = 0
    if rows and HEADER_RE.match(rows[0][0] if rows[0] else ''):
        start = 1

    seen_rules = set()
    color_count = 0
    radius_count = 0

    for i, row in enumerate(rows[start:], start=start + 1):
        if not row or not row[0].strip():
            continue

        name = row[0].strip()
        target = row[1].strip() if len(row) > 1 else ''

        if not target:
            errors.append(f'第 {i} 行: target 列为空')
            continue

        # 圆角规则
        if name.lower().startswith('radius:'):
            radius_count += 1
            source_val = name.split(':', 1)[1].strip()
            try:
                float(source_val)
                float(target)
            except ValueError:
                errors.append(f'第 {i} 行: 圆角值必须是数字，got {name},{target}')
            continue

        # 颜色规则
        color_count += 1

        # 检查重复
        rule_key = f'{name}→{target}'
        if rule_key in seen_rules:
            warnings.append(f'第 {i} 行: 重复规则 {name} → {target}')
        seen_rules.add(rule_key)

        # 按色值匹配
        if name.startswith('#'):
            errs = validate_color_str(name)
            for e in errs:
                errors.append(f'第 {i} 行 name: {e}')

        # 检查 target 色值
        target_errs = validate_color_str(target)
        for e in target_errs:
            errors.append(f'第 {i} 行 target: {e}')

    # 摘要
    print(f'\n  CSV 校验报告: {filepath}')
    print(f'  ─────────────────────────')
    print(f'  颜色规则: {color_count} 条')
    print(f'  圆角规则: {radius_count} 条')
    print(f'  总计: {color_count + radius_count} 条')

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print('用法: python3 scripts/validate.py <csv文件路径>')
        sys.exit(1)

    filepath = sys.argv[1]
    errors, warnings = validate_csv(filepath)

    if warnings:
        print(f'\n  警告 ({len(warnings)}):')
        for w in warnings:
            print(f'    - {w}')

    if errors:
        print(f'\n  错误 ({len(errors)}):')
        for e in errors:
            print(f'    - {e}')
        print('\n  校验失败')
        sys.exit(1)
    else:
        print('\n  校验通过')


if __name__ == '__main__':
    main()
