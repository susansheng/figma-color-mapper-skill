# -*- coding: utf-8 -*-
"""从 Figma 画布的左右对照布局中提取颜色映射，生成 CSV 文件。

用法:
  python3 scripts/figma2csv.py <figma_file_url> [--token TOKEN] [--output csv/mappings.csv]

Figma Token 可通过以下方式提供（按优先级）:
  1. --token 命令行参数
  2. FIGMA_TOKEN 环境变量
  3. 交互式输入（不会保存）
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.request
import urllib.error


def get_token(cli_token: str | None) -> str:
    """获取 Figma API Token"""
    if cli_token:
        return cli_token
    token = os.environ.get('FIGMA_TOKEN', '')
    if token:
        return token
    # 交互式输入
    token = input('请输入 Figma Personal Access Token: ').strip()
    if not token:
        print('错误: 未提供 Token')
        sys.exit(1)
    return token


def extract_file_key(url: str) -> str:
    """从 Figma URL 中提取文件 key"""
    # https://www.figma.com/design/XXXXXX/Name?node-id=...
    # https://www.figma.com/file/XXXXXX/Name
    match = re.search(r'figma\.com/(?:design|file)/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    # 直接传入 file key
    if re.match(r'^[a-zA-Z0-9]+$', url):
        return url
    print(f'错误: 无法从 URL 中提取文件 key: {url}')
    sys.exit(1)


def fetch_figma_file(file_key: str, token: str) -> dict:
    """通过 Figma REST API 获取文件数据"""
    url = f'https://api.figma.com/v1/files/{file_key}'
    req = urllib.request.Request(url, headers={'X-Figma-Token': token})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print('错误: Token 无效或无权访问该文件')
        elif e.code == 404:
            print('错误: 文件不存在')
        else:
            print(f'错误: Figma API 返回 {e.code}')
        sys.exit(1)


def rgb_to_hex(color: dict) -> str:
    """Figma RGBA (0-1) 转 hex"""
    r = int(color['r'] * 255)
    g = int(color['g'] * 255)
    b = int(color['b'] * 255)
    a = color.get('a', 1.0)
    if a < 0.99:
        return f'#{r:02X}{g:02X}{b:02X}{int(a * 255):02X}'
    return f'#{r:02X}{g:02X}{b:02X}'


def get_fill_hex(node: dict) -> str | None:
    """提取节点的填充色值，支持纯色和渐变"""
    fills = node.get('fills', [])
    if not fills:
        return None
    fill = fills[0]
    if fill.get('type') == 'SOLID':
        return rgb_to_hex(fill['color'])
    if 'GRADIENT' in fill.get('type', ''):
        stops = fill.get('gradientStops', [])
        if stops:
            colors = [rgb_to_hex(s['color']) for s in stops]
            return '-'.join(colors)
    return None


def flatten_nodes(node: dict) -> list[dict]:
    """递归展开所有子节点"""
    nodes = [node]
    for child in node.get('children', []):
        nodes.extend(flatten_nodes(child))
    return nodes


def find_mapping_frame(data: dict) -> dict | None:
    """查找包含映射规则的 Frame（名称含「映射」或「mapping」）"""
    for page in data['document'].get('children', []):
        for node in page.get('children', []):
            name = node.get('name', '').lower()
            if '映射' in name or 'mapping' in name or '规则' in name:
                return node
    # 兜底：取第一个 Frame
    for page in data['document'].get('children', []):
        children = page.get('children', [])
        if children:
            return children[0]
    return None


def parse_mapping_frame(frame: dict) -> list[dict]:
    """从 Frame 中解析左右对照的颜色映射。

    布局约定：
    - 左侧：源色标签（TEXT 节点，内容为 Variable/Style 名称或色值）
    - 右侧：目标色标签（TEXT 节点，内容为目标色值如 #00CAD9）
    - 左右标签按 Y 坐标精确对齐配对
    - 箭头（VECTOR）和色块（RECTANGLE）仅作视觉辅助
    """
    all_nodes = flatten_nodes(frame)

    # 收集所有文本标签
    texts = []
    # 忽略的标题/注释文本
    ignore_texts = {'原始颜色', '映射颜色', 'Source', 'Target'}

    for node in all_nodes:
        bbox = node.get('absoluteBoundingBox')
        if not bbox:
            continue

        if node.get('type') != 'TEXT':
            continue

        chars = node.get('characters', '').strip()
        if not chars or chars in ignore_texts:
            continue

        texts.append({
            'x': bbox['x'],
            'y': bbox['y'],
            'text': chars,
        })

    if len(texts) < 2:
        print('警告: 文本标签不足，无法配对')
        return []

    # 计算 X 轴中位数，区分左右
    all_x = [t['x'] for t in texts]
    mid_x = (min(all_x) + max(all_x)) / 2

    left_texts = [t for t in texts if t['x'] < mid_x]
    right_texts = [t for t in texts if t['x'] >= mid_x]

    # 左侧过滤：映射标签通常含 / 或 # 或 · 或较长
    # 短注释（如「优惠色」）排除
    mapping_texts = []
    for t in left_texts:
        text = t['text']
        if '/' in text or '#' in text or '·' in text or len(text) > 5:
            mapping_texts.append(t)

    if not mapping_texts:
        mapping_texts = left_texts

    # 右侧过滤：目标标签通常以 # 开头（色值）或含 - 连接的渐变
    target_texts = []
    for t in right_texts:
        text = t['text']
        if text.startswith('#') or '-#' in text:
            target_texts.append(t)

    if not target_texts:
        target_texts = right_texts

    # 按 Y 坐标排序
    mapping_texts.sort(key=lambda t: t['y'])
    target_texts.sort(key=lambda t: t['y'])

    # 按 Y 坐标精确配对（容差 50px）
    Y_TOLERANCE = 50
    mappings = []
    used_targets = set()

    for src in mapping_texts:
        best = None
        best_dist = float('inf')
        for i, tgt in enumerate(target_texts):
            if i in used_targets:
                continue
            dist = abs(src['y'] - tgt['y'])
            if dist < best_dist:
                best_dist = dist
                best = i
        if best is not None and best_dist < Y_TOLERANCE:
            used_targets.add(best)
            mappings.append({
                'name': src['text'],
                'target': target_texts[best]['text'],
            })
        else:
            print(f'  警告: 标签「{src["text"]}」未找到配对的目标标签 (y={src["y"]:.0f})')

    return mappings


def write_csv(mappings: list[dict], output_path: str):
    """将映射规则写入 CSV 文件"""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'target', 'C_color', 'Q_color'])
        for m in mappings:
            name = m['name']
            target = m['target']
            # C_color 和 Q_color 辅助列
            # 从 name 中提取源色值
            c_color = ''
            if name.startswith('#'):
                c_color = name
            else:
                hex_match = re.search(r'[·]\s*(#[0-9A-Fa-f]+)', name)
                if hex_match:
                    c_color = hex_match.group(1)
            q_color = target
            writer.writerow([name, target, c_color, q_color])

    print(f'\n  CSV 已生成: {output_path}')
    print(f'  共 {len(mappings)} 条规则')


def main():
    parser = argparse.ArgumentParser(description='从 Figma 画布生成 Q_Color Mapper CSV 映射表')
    parser.add_argument('url', help='Figma 文件 URL 或 file key')
    parser.add_argument('--token', help='Figma Personal Access Token（也可用 FIGMA_TOKEN 环境变量）')
    parser.add_argument('--output', '-o', default='csv/mappings.csv', help='输出 CSV 路径（默认: csv/mappings.csv）')
    args = parser.parse_args()

    token = get_token(args.token)
    file_key = extract_file_key(args.url)

    print(f'  正在获取 Figma 文件 {file_key}...')
    data = fetch_figma_file(file_key, token)
    print(f'  文件名: {data.get("name", "?")}')

    frame = find_mapping_frame(data)
    if not frame:
        print('错误: 未找到映射 Frame')
        sys.exit(1)
    print(f'  映射 Frame: {frame["name"]}')

    mappings = parse_mapping_frame(frame)
    if not mappings:
        print('错误: 未解析到任何映射规则')
        sys.exit(1)

    print(f'\n  解析到 {len(mappings)} 条映射:')
    for m in mappings:
        print(f'    {m["name"]}  →  {m["target"]}')

    write_csv(mappings, args.output)


if __name__ == '__main__':
    main()
