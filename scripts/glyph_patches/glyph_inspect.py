#!/usr/bin/env python3
"""Outline inspection helper for authoring per-glyph patches.

Renders a glyph's filled outline (via FreeType) with numbered control points
(on-curve = red square, off-curve = blue circle) and the baseline, optionally
with coordinate overrides applied first — so you can spot and tune outline
issues without editing the font. Two modes:

  # one annotated outline per character
  glyph_inspect.py outline FONT.ttf CHARS [--points SPEC] [--set IDX=X,Y ...]
                                          [--region R] [--ppem N] [--out DIR]

  # side-by-side comparison of candidate edits to one glyph
  glyph_inspect.py variants FONT.ttf CHAR --variant "LABEL:IDX=X,Y;IDX=X,Y" ...
                                          [--points SPEC] [--region R] [--out FILE]

SPEC for --points: "all" (default), "none", or a comma list like "34,35,36".
R for --region: full (default), bottom, top, br, bl, tr, tl  (zoom a region).

Examples:
  glyph_inspect.py outline Readerly-Regular.ttf nud
  glyph_inspect.py outline Readerly-Regular.ttf u --region br --points 20,21,22,23
  glyph_inspect.py variants Readerly-Regular.ttf d --region br \\
      --variant "current:" --variant "fix 37->76:37=772,76"

Run inside the fntbld-oci container (needs freetype-py + pillow); the
glyph_inspect.sh wrapper does that for you. Importable too:
  from glyph_inspect import render      # -> PIL.Image
"""

import argparse
import os
import sys
import tempfile

from fontTools.ttLib import TTFont
import freetype
from PIL import Image, ImageDraw

# Fraction (left, top, right, bottom) of the rendered image kept per region.
REGIONS = {
    "full":   (0.00, 0.00, 1.00, 1.00),
    "bottom": (0.00, 0.45, 1.00, 1.00),
    "top":    (0.00, 0.00, 1.00, 0.55),
    "br":     (0.38, 0.55, 1.00, 1.00),
    "bl":     (0.00, 0.55, 0.62, 1.00),
    "tr":     (0.38, 0.00, 1.00, 0.45),
    "tl":     (0.00, 0.00, 0.62, 0.45),
}


def parse_edits(spec):
    """'23=831,92;24=789,84' -> {23: (831, 92), 24: (789, 84)}."""
    edits = {}
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        idx, xy = part.split("=")
        x, y = xy.split(",")
        edits[int(idx)] = (int(x), int(y))
    return edits


def _parse_points(spec, npoints):
    if spec == "all":
        return set(range(npoints))
    if spec == "none":
        return set()
    return {int(i) for i in spec.split(",") if i.strip() != ""}


def render(font_path, char, edits=None, points="all", region="full",
           ppem=900, label=None, fill=0.22, markers=True, baseline=True):
    """Render one glyph's annotated outline to a PIL RGB image."""
    f = TTFont(font_path)
    cmap = f.getBestCmap()
    upm = f["head"].unitsPerEm
    name = cmap[ord(char)]
    glyph = f["glyf"][name]

    if edits:
        for i, xy in edits.items():
            glyph.coordinates[i] = xy
        glyph.recalcBounds(f["glyf"])
        tmp = tempfile.NamedTemporaryFile(
            prefix=os.path.basename(font_path) + ".",
            suffix=".inspect.tmp.ttf",
            dir=os.path.dirname(font_path) or ".",
            delete=False)
        tmp.close()
        render_path = tmp.name
        f.save(render_path)
    else:
        render_path = font_path

    coords, flags = glyph.coordinates, glyph.flags
    scale = ppem / upm

    face = freetype.Face(render_path)
    face.set_pixel_sizes(0, ppem)
    face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    bm = face.glyph.bitmap
    left, top = face.glyph.bitmap_left, face.glyph.bitmap_top

    MX, MY = 130, 150
    W, H = bm.width + 2 * MX, bm.rows + 2 * MY
    img = Image.new("RGB", (W, H), (255, 255, 255))
    if bm.rows and bm.width:
        gl = Image.frombytes("L", (bm.width, bm.rows), bytes(bm.buffer))
        gl = Image.eval(gl, lambda v: 255 - int(v * fill))
        img.paste(gl.convert("RGB"), (MX, MY))

    d = ImageDraw.Draw(img)
    baseline_y = MY + top
    originx = MX - left
    if baseline:
        d.line([(0, baseline_y), (W, baseline_y)], fill=(220, 30, 30))
    if label:
        d.text((6, 6), label, fill=(0, 0, 0))

    if markers:
        show = _parse_points(points, len(coords))
        for i, (x, y) in enumerate(coords):
            px, py = originx + x * scale, baseline_y - y * scale
            on = flags[i] & 1
            r = 6
            col = (200, 0, 0) if on else (0, 80, 220)
            (d.rectangle if on else d.ellipse)(
                [px - r, py - r, px + r, py + r], outline=col, width=2)
            if i in show:
                d.text((px + 8, py - 7), str(i), fill=(0, 0, 0))

    f.close()
    if render_path != font_path:
        os.remove(render_path)

    fl, ft, fr, fb = REGIONS.get(region, REGIONS["full"])
    if (fl, ft, fr, fb) != (0.0, 0.0, 1.0, 1.0):
        img = img.crop((int(W * fl), int(H * ft), int(W * fr), int(H * fb)))
    return img


def hstack(images, gap=12, bg=(245, 245, 245)):
    """Compose images left-to-right onto one canvas."""
    W = sum(im.width for im in images) + gap * (len(images) - 1)
    H = max(im.height for im in images)
    out = Image.new("RGB", (W, H), bg)
    x = 0
    for im in images:
        out.paste(im, (x, 0))
        x += im.width + gap
    return out


def cmd_outline(args):
    os.makedirs(args.out, exist_ok=True)
    edits = parse_edits(args.set_) if args.set_ else None
    for ch in args.chars:
        img = render(args.font, ch, edits=edits, points=args.points,
                     region=args.region, ppem=args.ppem, markers=args.markers,
                     baseline=args.baseline,
                     label=f"{args.label or os.path.basename(args.font)} {ch}".strip())
        p = os.path.join(args.out, f"outline-{ch}.png")
        img.save(p)
        print("wrote", p)


def cmd_variants(args):
    panels = []
    for spec in args.variant:
        label, _, edit_spec = spec.partition(":")
        edits = parse_edits(edit_spec) if edit_spec.strip() else None
        panels.append(render(args.font, args.char, edits=edits,
                             points=args.points, region=args.region,
                             ppem=args.ppem, markers=args.markers,
                             baseline=args.baseline,
                             label=label or "base"))
    out = args.out or f"glyph-variants-{args.char}.png"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    hstack(panels).save(out)
    print("wrote", out)


def build_parser():
    p = argparse.ArgumentParser(description="Glyph outline inspection helper.")
    sub = p.add_subparsers(dest="mode", required=True)

    o = sub.add_parser("outline", help="annotated outline per character")
    o.add_argument("font")
    o.add_argument("chars")
    o.add_argument("--points", default="all")
    o.add_argument("--set", dest="set_", default="",
                   help="coordinate overrides, e.g. '23=831,92;24=789,84'")
    o.add_argument("--region", default="full", choices=list(REGIONS))
    o.add_argument("--ppem", type=int, default=900)
    o.add_argument("--label", default="")
    o.add_argument("--no-points", dest="markers", action="store_false",
                   help="render the clean filled glyph without point markers")
    o.add_argument("--no-baseline", dest="baseline", action="store_false",
                   help="render without the baseline guide")
    o.add_argument("--out", default="glyph-outlines")
    o.set_defaults(func=cmd_outline)

    v = sub.add_parser("variants", help="compare candidate edits side by side")
    v.add_argument("font")
    v.add_argument("char")
    v.add_argument("--variant", action="append", required=True,
                   help="'LABEL:IDX=X,Y;IDX=X,Y' (repeatable; empty edits = base)")
    v.add_argument("--points", default="all")
    v.add_argument("--region", default="full", choices=list(REGIONS))
    v.add_argument("--ppem", type=int, default=900)
    v.add_argument("--no-points", dest="markers", action="store_false",
                   help="render clean filled glyphs without point markers")
    v.add_argument("--no-baseline", dest="baseline", action="store_false",
                   help="render without the baseline guide")
    v.add_argument("--out", default="")
    v.set_defaults(func=cmd_variants)
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
