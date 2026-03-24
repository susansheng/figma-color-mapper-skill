# -*- coding: utf-8 -*-
"""预览 Q_Color Mapper 的 CSV 映射规则"""

import csv
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r'^(name|match|source|原|源|匹配)', re.IGNORECASE)


def preview_csv(filepath: str):
    """解析并分组展示 CSV 规则"""
    path = Path(filepath)
    if not path.exists():
        print(f'文件不存在: {filepath}')
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    start = 0
    if rows and HEADER_RE.match(rows[0][0] if rows[0] else ''):
        start = 1

    name_rules = []    # 按名称匹配的颜色规则
    color_rules = []   # 按色值匹配的颜色规则
    radius_rules = []  # 圆角规则

    for row in rows[start:]:
        if not row or not row[0].strip():
            continue

        name = row[0].strip()
        target = row[1].strip() if len(row) > 1 else ''

        if name.lower().startswith('radius:'):
            source_val = name.split(':', 1)[1].strip()
            radius_rules.append((source_val, target))
        elif name.startswith('#'):
            color_rules.append((name, target))
        else:
            # 去掉 ·#hex 后缀用于显示
            display_name = re.sub(r'[·]\s*#[0-9A-Fa-f]+$', '', name).strip()
            source_hex = ''
            hex_match = re.search(r'[·]\s*(#[0-9A-Fa-f]+)$', name)
            if hex_match:
                source_hex = hex_match.group(1)
            name_rules.append((display_name, target, source_hex))

    # 输出
    print(f'\n  Q_Color Mapper 规则预览')
    print(f'  ═══════════════════════\n')

    if name_rules:
        print(f'  颜色规则 — 按名称匹配 ({len(name_rules)} 条)')
        print(f'  {"名称":<40} {"目标色值":<20} {"源色值(fallback)"}')
        print(f'  {"─"*40} {"─"*20} {"─"*15}')
        for name, target, src in name_rules:
            print(f'  {name:<40} {target:<20} {src}')
        print()

    if color_rules:
        print(f'  颜色规则 — 按色值匹配 ({len(color_rules)} 条)')
        print(f'  {"源色值":<25} {"目标色值"}')
        print(f'  {"─"*25} {"─"*20}')
        for src, tgt in color_rules:
            print(f'  {src:<25} {tgt}')
        print()

    if radius_rules:
        print(f'  圆角规则 ({len(radius_rules)} 条)')
        print(f'  {"源圆角":<15} {"目标圆角"}')
        print(f'  {"─"*15} {"─"*15}')
        for src, tgt in radius_rules:
            print(f'  {src:<15}px → {tgt}px')
        print()

    total = len(name_rules) + len(color_rules) + len(radius_rules)
    print(f'  总计: {total} 条规则')


def main():
    if len(sys.argv) < 2:
        print('用法: python3 scripts/preview.py <csv文件路径>')
        sys.exit(1)
    preview_csv(sys.argv[1])


if __name__ == '__main__':
    main()
