#!/usr/bin/env python3
"""Render filled SVG outline comparisons for two TTF files."""

import argparse
import math
import os
import re
import xml.sax.saxutils as xml_escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

DEFAULT_TEXT = "\n".join([
    "Readerly",
    "Hamburgefontsiv",
    "minimum adhesion",
    "The quick brown fox jumps over a lazy dog.",
    "0123456789 &?!",
])


def safe_name(path):
    name = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "font"


def svg_glyph_paths(font_path, lines, px_size, pad, label_height):
    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    ascent = font["hhea"].ascent
    descent = font["hhea"].descent
    scale = px_size / upm
    line_height = (ascent - descent) * scale
    paths = []
    max_width = 0

    for line_index, line in enumerate(lines):
        x = pad
        baseline = label_height + pad + ascent * scale + line_index * line_height
        for ch in line:
            glyph_name = cmap.get(ord(ch))
            if glyph_name is None:
                continue
            advance = hmtx[glyph_name][0] * scale
            if glyph_name != ".notdef":
                pen = SVGPathPen(glyph_set)
                glyph_set[glyph_name].draw(pen)
                commands = pen.getCommands()
                if commands:
                    paths.append((commands, x, baseline, scale))
            x += advance
        max_width = max(max_width, x)

    font.close()
    height = label_height + pad * 2 + line_height * len(lines)
    return paths, max_width + pad, height


def write_svg_comparison(left_path, right_path, lines, out, label_a, label_b,
                         px_size, mode):
    pad = 48
    label_height = 34
    title_height = 36
    legend_height = 52
    left_paths, left_width, left_height = svg_glyph_paths(
        left_path, lines, px_size, pad, label_height)
    right_paths, right_width, right_height = svg_glyph_paths(
        right_path, lines, px_size, pad, label_height)
    width = math.ceil(max(left_width, right_width))
    panel_height = math.ceil(max(left_height, right_height))
    height = title_height + panel_height + legend_height

    def path_elements(paths, color, opacity):
        chunks = []
        for commands, x, y, scale in paths:
            d = xml_escape.escape(commands)
            chunks.append(
                f'<path d="{d}" transform="translate({x:.2f} '
                f'{y + title_height:.2f}) scale({scale:.6f} {-scale:.6f})" '
                f'fill="{color}" fill-opacity="{opacity:.2f}" '
                f'fill-rule="nonzero" stroke="none"/>')
        return "\n".join(chunks)

    title = xml_escape.escape(f"{label_a} vs {label_b}")
    legend_y = title_height + panel_height + 18

    if mode == "overlap":
        body = "\n".join([
            path_elements(left_paths, "#ec0078", 0.42),
            path_elements(right_paths, "#0087e6", 0.42),
        ])
        legend = f'''  <rect x="12" y="{legend_y}" width="16" height="16" fill="#ec0078" opacity="0.42"/>
  <text x="36" y="{legend_y + 13}">{xml_escape.escape(label_a)}</text>
  <rect x="170" y="{legend_y}" width="16" height="16" fill="#0087e6" opacity="0.42"/>
  <text x="194" y="{legend_y + 13}">{xml_escape.escape(label_b)}</text>'''
    else:
        removed_id = "removed-mask"
        added_id = "added-mask"
        left_white = path_elements(left_paths, "white", 1)
        left_black = path_elements(left_paths, "black", 1)
        right_white = path_elements(right_paths, "white", 1)
        right_black = path_elements(right_paths, "black", 1)
        body = f'''<defs>
  <mask id="{removed_id}" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{height}">
    <rect width="100%" height="100%" fill="black"/>
{left_white}
{right_black}
  </mask>
  <mask id="{added_id}" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{height}">
    <rect width="100%" height="100%" fill="black"/>
{right_white}
{left_black}
  </mask>
</defs>
{path_elements(right_paths, "#d8d8d8", 0.55)}
<g mask="url(#{removed_id})">
{path_elements(left_paths, "#d62728", 0.90)}
</g>
<g mask="url(#{added_id})">
{path_elements(right_paths, "#148f2b", 0.90)}
</g>'''
        legend = f'''  <rect x="12" y="{legend_y}" width="16" height="16" fill="#d62728" opacity="0.90"/>
  <text x="36" y="{legend_y + 13}">removed from {xml_escape.escape(label_a)}</text>
  <rect x="260" y="{legend_y}" width="16" height="16" fill="#148f2b" opacity="0.90"/>
  <text x="284" y="{legend_y + 13}">added in {xml_escape.escape(label_b)}</text>
  <rect x="480" y="{legend_y}" width="16" height="16" fill="#d8d8d8" opacity="0.55"/>
  <text x="504" y="{legend_y + 13}">{xml_escape.escape(label_b)} fill</text>'''

    with open(out, "w", encoding="utf-8") as f:
        f.write(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/>
<text x="12" y="22" font-family="sans-serif" font-size="13">{title}</text>
{body}
<g font-family="sans-serif" font-size="13">
{legend}
</g>
</svg>
''')


def compare(args):
    lines = args.text.split("\\n") if args.text is not None else DEFAULT_TEXT.split("\n")
    label_a = args.left_label or safe_name(args.left)
    label_b = args.right_label or safe_name(args.right)
    out = args.out
    if not out:
        os.makedirs("out/scripts/compare", exist_ok=True)
        out = os.path.join(
            "out/scripts/compare",
            f"{safe_name(args.left)}-vs-{safe_name(args.right)}.svg")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    write_svg_comparison(args.left, args.right, lines, out, label_a, label_b,
                         args.size, args.mode)
    print("wrote", out)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", help="left/previous TTF file")
    parser.add_argument("right", help="right/current TTF file")
    parser.add_argument("--out", default="", help="output SVG path")
    parser.add_argument("--size", type=int, default=72, help="outline size in px")
    parser.add_argument("--mode", choices=["diff", "overlap"], default="overlap",
                        help="comparison mode; diff uses green additions/red removals")
    parser.add_argument("--left-label", default="", help="label for left font")
    parser.add_argument("--right-label", default="", help="label for right font")
    parser.add_argument("--text", default=None,
                        help="sample text; use literal \\n for line breaks")
    return parser


if __name__ == "__main__":
    compare(build_parser().parse_args())
