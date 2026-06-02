# Glyph patches

Surgical, reproducible per-glyph outline edits that are awkward to express as
global build rules (e.g. softening a bowl→foot bracket spur). The build applies
them after the Y-floor/ceiling passes and before autohinting; KF and WOFF2
variants inherit them from the patched TTF.

## Layout

```
glyph_patches/
  apply.py          runner — infers style from the font filename and applies
                    that style's patches (e.g. Readerly-Regular.ttf -> regular/)
  _lib.py           shared apply logic (idempotent + self-guarding)
  glyph_inspect.py  outline inspection tool (annotated plots, candidate grids)
  glyph_inspect.sh  container wrapper for glyph_inspect.py
  regular/          patches for the Regular style — one file per glyph
    u.py b.py d.py s.py
  bold/             patches for the Bold style
    u.py b.py d.py s.py
```

Patches are **per style** (`regular/`, `bold/`, …); to patch another style, add
a sibling folder with the same one-file-per-glyph shape. A style with no folder
is left untouched. The same glyph in different styles has different outlines, so
each style's patch carries its own point indices and coordinates.

## A patch file

Each glyph file declares the points it touches as two coordinate maps:

- `ORIGINAL` — the coordinates expected in the un-patched build.
- `TARGET`   — the coordinates to set.

Patches set **absolute** coordinates (so rebuilds never compound them) and are
**self-guarding**: if the outline doesn't match `ORIGINAL` (the source font
changed), the patch refuses rather than corrupt the glyph.

## Usage

```bash
# apply (the build does this automatically; here it's manual/standalone)
python3 scripts/glyph_patches/apply.py out/ttf/Readerly-Regular.ttf
python3 scripts/glyph_patches/regular/s.py out/ttf/Readerly-Regular.ttf   # one glyph

# inspect / tune outlines (needs the fntbld-oci container)
scripts/glyph_patches/glyph_inspect.sh outline out/ttf/Readerly-Regular.ttf s --region bottom
scripts/glyph_patches/glyph_inspect.sh variants out/ttf/Readerly-Regular.ttf d \
    --region br --variant "current:" --variant "fix:37=772,76"
```
