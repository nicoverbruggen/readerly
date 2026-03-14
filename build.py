#!/usr/bin/env python3
"""
Readerly Build Script
─────────────────────
Orchestrates the full font build pipeline:

  1. Instances variable fonts into static TTFs (fontTools.instancer)
  2. Applies vertical scale (scale.py) via FontForge
  3. Applies vertical metrics, line height, rename (metrics.py, lineheight.py, rename.py)
  4. Exports to SFD and TTF → ./out/sfd/ and ./out/ttf/

Uses FontForge (detected automatically).
Run with: python3 build.py
"""

import os
import shutil
import subprocess
import sys
import textwrap

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Most of these values are safe to tweak. The --customize flag only toggles
# a small subset at runtime (family name, old-style kerning, outline fixes).
#
# Quick reference (what each knob does):
# - REGULAR_VF / ITALIC_VF: input variable fonts from ./src
# - DEFAULT_FAMILY: default output family name
# - VARIANT_STYLES: (style, source VF, wght, opsz) pins for instancing
# - SCALE_LOWER_X/Y: lowercase-only scale (x-height tuning)
# - CONDENSE_X: horizontal condense for all glyphs
# - LINE_HEIGHT: Typo line height (default line spacing)
# - SELECTION_HEIGHT: Win/hhea selection box height and clipping
# - ASCENDER_RATIO: ascender share of total height
# - STYLE_MAP: naming/weight metadata per style

ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
SRC_DIR     = os.path.join(ROOT_DIR, "src")
OUT_DIR     = os.path.join(ROOT_DIR, "out")
OUT_SFD_DIR = os.path.join(OUT_DIR, "sfd")  # generated FontForge sources
OUT_TTF_DIR = os.path.join(OUT_DIR, "ttf")  # generated TTFs

REGULAR_VF = os.path.join(SRC_DIR, "Newsreader-VariableFont_opsz,wght.ttf")
ITALIC_VF  = os.path.join(SRC_DIR, "Newsreader-Italic-VariableFont_opsz,wght.ttf")

with open(os.path.join(ROOT_DIR, "VERSION")) as _vf:
    FONT_VERSION = _vf.read().strip()

with open(os.path.join(ROOT_DIR, "COPYRIGHT")) as _cf:
    COPYRIGHT_TEXT = _cf.read().strip()

DEFAULT_FAMILY = "Readerly"  # default if --customize not used

VARIANT_STYLES = [
    # (style_suffix, source_vf, wght, opsz)
    # opsz=9 is intentionally small to tighten letterforms for e-readers.
    ("Regular",    REGULAR_VF, 450, 9),
    ("Bold",       REGULAR_VF, 650, 9),
    ("Italic",     ITALIC_VF,  450, 9),
    ("BoldItalic", ITALIC_VF,  650, 9),
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INLINE FONTFORGE SCRIPT CONFIG
# (Migrated from ./scripts for readability and single-file builds.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Step 2: Scaling + overlap cleanup
# - SCALE_LOWER_* affects lowercase only (x-height tuning).
# - CONDENSE_X narrows all glyphs to match Bookerly-like widths.

# Scale lowercase glyphs vertically (and slightly widen).
SCALE_LOWER_X = 1.03
SCALE_LOWER_Y = 1.08

# Condense all glyphs horizontally.
CONDENSE_X = 0.95

# Step 3: Vertical metrics + line spacing (relative to UPM)
# - LINE_HEIGHT drives OS/2 Typo metrics (default line spacing)
# - SELECTION_HEIGHT drives Win/hhea metrics (selection box + clipping)
# - ASCENDER_RATIO splits the total height between ascender/descender
LINE_HEIGHT = 1.0
SELECTION_HEIGHT = 1.3
ASCENDER_RATIO = 0.8

# Step 3: Naming and style metadata (used by the rename step)
STYLE_MAP = {
    "Regular":    ("Regular",     "Book", 400),
    "Bold":       ("Bold",        "Bold", 700),
    "Italic":     ("Italic",      "Book", 400),
    "BoldItalic": ("Bold Italic", "Bold", 700),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FONTFORGE_CMD = None

def find_fontforge():
    """Detect FontForge on the system. Returns a command list."""
    global FONTFORGE_CMD
    if FONTFORGE_CMD is not None:
        return FONTFORGE_CMD

    # 1. fontforge on PATH (native install, Homebrew, Windows, etc.)
    if shutil.which("fontforge"):
        FONTFORGE_CMD = ["fontforge"]
        return FONTFORGE_CMD

    # 2. Flatpak (Linux)
    if shutil.which("flatpak"):
        result = subprocess.run(
            ["flatpak", "info", "org.fontforge.FontForge"],
            capture_output=True,
        )
        if result.returncode == 0:
            FONTFORGE_CMD = [
                "flatpak", "run",
                "--command=fontforge", "org.fontforge.FontForge",
            ]
            return FONTFORGE_CMD

    # 3. macOS app bundle
    mac_paths = [
        "/Applications/FontForge.app/Contents/MacOS/FontForge",
        "/Applications/FontForge.app/Contents/Resources/opt/local/bin/fontforge",
    ]
    for mac_path in mac_paths:
        if os.path.isfile(mac_path):
            FONTFORGE_CMD = [mac_path]
            return FONTFORGE_CMD

    print(
        "ERROR: FontForge not found.\n"
        "Install it via your package manager, Flatpak, or from https://fontforge.org",
        file=sys.stderr,
    )
    sys.exit(1)


def run_fontforge_script(script_text):
    """Run a Python script inside FontForge."""
    cmd = find_fontforge() + ["-lang=py", "-script", "-"]
    result = subprocess.run(
        cmd,
        input=script_text,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        # FontForge prints various info/warnings to stderr; filter noise
        for line in result.stderr.splitlines():
            if line.startswith("Copyright") or line.startswith(" License") or \
               line.startswith(" Version") or line.startswith(" Based on") or \
               line.startswith(" with many parts") or \
               "pkg_resources is deprecated" in line or \
               "Invalid 2nd order spline" in line:
                continue
            print(f"  [stderr] {line}", file=sys.stderr)
    if result.returncode != 0:
        print(f"\nERROR: FontForge script exited with code {result.returncode}", file=sys.stderr)
        sys.exit(1)


def build_per_font_script(open_path, save_path, steps):
    """
    Build a FontForge Python script that opens a font file, runs the given
    step scripts (which expect `f` to be the active font), saves as .sfd,
    and closes.

    Each step is a (label, script_body) tuple. The script_body should use `f`
    as the font variable.
    """
    parts = [
        f'import fontforge',
        f'f = fontforge.open({open_path!r})',
        f'print("\\nOpened: " + f.fontname + "\\n")',
    ]
    for label, body in steps:
        parts.append(f'print("── {label} ──\\n")')
        parts.append(body)
    parts.append(f'f.save({save_path!r})')
    parts.append(f'print("\\nSaved: {save_path}\\n")')
    parts.append('f.close()')
    return "\n".join(parts)


def ff_scale_lowercase_script():
    """FontForge script: scale lowercase glyphs vertically."""
    return textwrap.dedent(f"""\
        import psMat
        import unicodedata

        # Scale lowercase glyphs only, from glyph origin.
        SCALE_X = {SCALE_LOWER_X}
        SCALE_Y = {SCALE_LOWER_Y}

        mat = psMat.scale(SCALE_X, SCALE_Y)

        f.selection.none()
        count = 0
        for g in f.glyphs():
            if g.unicode < 0:
                continue
            try:
                cat = unicodedata.category(chr(g.unicode))
            except (ValueError, OverflowError):
                continue
            if cat == "Ll" or g.unicode in (0x00AA, 0x00BA):
                f.selection.select(("more",), g.glyphname)
                count += 1

        f.transform(mat, ("round",))
        print(f"  Scaled {{count}} lowercase glyphs by X={{SCALE_X:.0%}}, Y={{SCALE_Y:.0%}}")
    """)


def ff_condense_script():
    """FontForge script: condense all glyphs horizontally."""
    return textwrap.dedent(f"""\
        import psMat

        SCALE_X = {CONDENSE_X}
        mat = psMat.scale(SCALE_X, 1.0)

        f.selection.all()
        f.transform(mat, ("round",))

        count = sum(1 for g in f.glyphs() if g.isWorthOutputting())
        print(f"  Condensed {{count}} glyphs by X={{SCALE_X:.0%}}")
    """)


def ff_remove_overlaps_script():
    """FontForge script: merge overlapping contours and fix direction."""
    return textwrap.dedent("""\
        f.selection.all()
        f.removeOverlap()
        f.correctDirection()

        count = sum(1 for g in f.glyphs() if g.isWorthOutputting())
        print(f"  Removed overlaps and corrected direction for {count} glyphs")
    """)


def ff_metrics_script():
    """FontForge script: measure landmarks and set OS/2 Typo metrics."""
    return textwrap.dedent("""\
def _bbox(name):
    # Return bounding box (xmin, ymin, xmax, ymax) or None.
    if name in f and f[name].isWorthOutputting():
        bb = f[name].boundingBox()
        if bb != (0, 0, 0, 0):
            return bb
    return None

def measure_chars(chars, *, axis="top"):
    # Measure a set of reference characters.
    #   axis="top"    -> return the highest yMax
    #   axis="bottom" -> return the lowest  yMin
    # Returns (value, display_char) or (None, None).
    idx  = 3 if axis == "top" else 1
    pick = max if axis == "top" else min
    hits = []
    for ch in chars:
        name = fontforge.nameFromUnicode(ord(ch))
        bb = _bbox(name)
        if bb is not None:
            hits.append((bb[idx], ch))
    if not hits:
        return None, None
    return pick(hits, key=lambda t: t[0])

def scan_font_extremes():
    # Walk every output glyph; return (yMax, yMin, max_name, min_name).
    y_max, y_min = 0, 0
    max_nm, min_nm = None, None
    for g in f.glyphs():
        if not g.isWorthOutputting():
            continue
        bb = g.boundingBox()
        if bb == (0, 0, 0, 0):
            continue
        if bb[3] > y_max:
            y_max, max_nm = bb[3], g.glyphname
        if bb[1] < y_min:
            y_min, min_nm = bb[1], g.glyphname
    return y_max, y_min, max_nm, min_nm

print("─── Design landmarks ───\\n")

cap_h, cap_c = measure_chars("HIOX", axis="top")
asc_h, asc_c = measure_chars("bdfhkl", axis="top")
xht_h, xht_c = measure_chars("xuvw", axis="top")
dsc_h, dsc_c = measure_chars("gpqyj", axis="bottom")

for label, val, ch in [
    ("Cap height", cap_h, cap_c),
    ("Ascender",   asc_h, asc_c),
    ("x-height",   xht_h, xht_c),
    ("Descender",  dsc_h, dsc_c),
]:
    if val is not None:
        print(f"  {label:12s}  {int(val):>6}  ('{ch}')")
    else:
        print(f"  {label:12s}  {'N/A':>6}")

print("\\n─── Full font scan ───\\n")

font_ymax, font_ymin, ymax_name, ymin_name = scan_font_extremes()
print(f"  Highest glyph:  {int(font_ymax):>6}  ({ymax_name})")
print(f"  Lowest  glyph:  {int(font_ymin):>6}  ({ymin_name})")

upm = f.em

design_top = asc_h if asc_h is not None else cap_h
design_bot = dsc_h   # negative value

if design_top is None or design_bot is None:
    raise SystemExit(
        "ERROR: Could not measure ascender/cap-height or descender.\\n"
        "       Make sure your font contains basic Latin glyphs (H, b, p, etc.)."
    )

typo_ascender  = int(round(design_top))
typo_descender = int(round(design_bot))

f.os2_typoascent  = typo_ascender
f.os2_typodescent = typo_descender
f.os2_typolinegap = 0

if hasattr(f, "os2_xheight") and xht_h is not None:
    f.os2_xheight = int(round(xht_h))
if hasattr(f, "os2_capheight") and cap_h is not None:
    f.os2_capheight = int(round(cap_h))

# Win/hhea set to same initial values; lineheight step overrides these.
f.os2_winascent  = typo_ascender
f.os2_windescent = abs(typo_descender)
f.hhea_ascent    = typo_ascender
f.hhea_descent   = typo_descender
f.hhea_linegap   = 0

typo_metrics_set = False

if hasattr(f, "os2_use_typo_metrics"):
    f.os2_use_typo_metrics = True
    typo_metrics_set = True

if not typo_metrics_set and hasattr(f, "os2_fsselection"):
    f.os2_fsselection |= (1 << 7)
    typo_metrics_set = True

if not typo_metrics_set:
    if hasattr(f, "os2_version") and f.os2_version < 4:
        f.os2_version = 4

if not typo_metrics_set:
    print("  WARNING: Could not set USE_TYPO_METRICS programmatically.")
    print("  -> In Font Info -> OS/2 -> Misc, tick 'USE_TYPO_METRICS'.\\n")

typo_line = typo_ascender - typo_descender

print(f"\\n─── Applied metrics ───\\n")
print(f"  UPM:  {upm}")
print(f"  Typo: {typo_ascender} / {typo_descender} (ink span: {typo_line}, {typo_line/upm:.2f}x UPM)")

if cap_h is not None:
    print(f"  Cap height:   {int(cap_h)}")
if xht_h is not None:
    print(f"  x-height:     {int(xht_h)}")
""")


def ff_lineheight_script():
    """FontForge script: set line height and selection box metrics."""
    return textwrap.dedent(f"""\
        # Line height (Typo) as a multiple of UPM.
        LINE_HEIGHT = {LINE_HEIGHT}

        # Selection box height (Win/hhea) as a multiple of UPM.
        SELECTION_HEIGHT = {SELECTION_HEIGHT}

        # Ascender share of the line/selection height.
        ASCENDER_RATIO = {ASCENDER_RATIO}

        upm = f.em

        # OS/2 Typo — controls line spacing
        typo_total = int(round(upm * LINE_HEIGHT))
        typo_asc   = int(round(typo_total * ASCENDER_RATIO))
        typo_dsc   = typo_asc - typo_total   # negative

        f.os2_typoascent  = typo_asc
        f.os2_typodescent = typo_dsc
        f.os2_typolinegap = 0

        # Win/hhea — controls selection box height and clipping
        sel_total = int(round(upm * SELECTION_HEIGHT))
        sel_asc   = int(round(sel_total * ASCENDER_RATIO))
        sel_dsc   = sel_total - sel_asc

        f.hhea_ascent    = sel_asc
        f.hhea_descent   = -sel_dsc
        f.hhea_linegap   = 0
        f.os2_winascent  = sel_asc
        f.os2_windescent = sel_dsc

        print(f"  Typo: {{typo_asc}} / {{typo_dsc}} / gap 0  (line height: {{typo_total}}, {LINE_HEIGHT:.2f}x UPM)")
        print(f"  hhea: {{sel_asc}} / {{-sel_dsc}} / gap 0  (selection: {{sel_total}}, {SELECTION_HEIGHT:.2f}x UPM)")
        print(f"  Win:  {{sel_asc}} / {{sel_dsc}}")
    """)


def ff_rename_script():
    """FontForge script: update font name metadata."""
    style_map = repr(STYLE_MAP)
    return textwrap.dedent(f"""\
        # FAMILY is injected by build.py; default if run standalone.
        if "FAMILY" not in dir():
            FAMILY = "Readerly"

        STYLE_MAP = {style_map}

        # Determine style from the current fontname (e.g. "Readerly-BoldItalic")
        style_suffix = f.fontname.split("-")[-1] if "-" in f.fontname else "Regular"
        style_display, ps_weight, os2_weight = STYLE_MAP.get(
            style_suffix, (style_suffix, "Book", 400)
        )

        f.fontname = f"{{FAMILY}}-{{style_suffix}}"
        f.familyname = FAMILY
        f.fullname = f"{{FAMILY}} {{style_display}}"
        f.weight = ps_weight
        f.os2_weight = os2_weight

        # Set head.macStyle for style linking if supported by FontForge
        if hasattr(f, "macstyle"):
            macstyle = f.macstyle
            macstyle &= ~((1 << 0) | (1 << 1))
            if "Bold" in style_suffix:
                macstyle |= (1 << 0)
            if "Italic" in style_suffix:
                macstyle |= (1 << 1)
            f.macstyle = macstyle

        lang = "English (US)"

        f.appendSFNTName(lang, "Family", FAMILY)
        f.appendSFNTName(lang, "SubFamily", style_display)
        f.appendSFNTName(lang, "Fullname", f"{{FAMILY}} {{style_display}}")
        f.appendSFNTName(lang, "PostScriptName", f"{{FAMILY}}-{{style_suffix}}")
        f.appendSFNTName(lang, "Preferred Family", FAMILY)
        f.appendSFNTName(lang, "Preferred Styles", style_display)
        f.appendSFNTName(lang, "Compatible Full", f"{{FAMILY}} {{style_display}}")
        f.appendSFNTName(lang, "UniqueID", f"{{FAMILY}} {{style_display}}")

        # Clear Newsreader-specific entries
        f.appendSFNTName(lang, "Trademark", "")
        f.appendSFNTName(lang, "Manufacturer", "")
        f.appendSFNTName(lang, "Designer", "")
        f.appendSFNTName(lang, "Vendor URL", "")
        f.appendSFNTName(lang, "Designer URL", "")

        count = 0
        for _name in f.sfnt_names:
            count += 1
        print(f"  Updated {{count}} name entries for {{FAMILY}} {{style_display}}")
        print(f"  PS weight: {{ps_weight}}, OS/2 usWeightClass: {{os2_weight}}")
    """)


def ff_version_script():
    """FontForge script: set font version."""
    return textwrap.dedent("""\
        # VERSION is injected by build.py before this script runs.
        version_str = "Version " + VERSION

        f.version = VERSION
        f.sfntRevision = float(VERSION)
        f.appendSFNTName("English (US)", "Version", version_str)

        print(f"  Version set to: {version_str}")
        print(f"  head.fontRevision set to: {float(VERSION)}")
    """)


def ff_license_script():
    """FontForge script: set copyright."""
    return textwrap.dedent("""\
        # COPYRIGHT_TEXT is injected by build.py before this script runs.
        lang = "English (US)"

        f.copyright = COPYRIGHT_TEXT
        f.appendSFNTName(lang, "Copyright", COPYRIGHT_TEXT)

        print(f"  Copyright: {COPYRIGHT_TEXT.splitlines()[0]}")
    """)


def build_export_script(sfd_path, ttf_path, old_kern=True):
    """Build a FontForge script that opens an .sfd and exports to TTF."""
    if old_kern:
        flags_line = 'flags = ("opentype", "old-kern", "no-FFTM-table", "winkern")'
    else:
        flags_line = 'flags = ("opentype", "no-FFTM-table")'
    return textwrap.dedent(f"""\
        import fontforge

        f = fontforge.open({sfd_path!r})
        print("Exporting: " + f.fontname)

        {flags_line}
        f.generate({ttf_path!r}, flags=flags)

        print("  -> " + {ttf_path!r})
        f.close()
    """)


def clean_ttf_degenerate_contours(ttf_path):
    """Remove zero-area contours (<=2 points) from a TTF in-place."""
    try:
        from fontTools.ttLib import TTFont
        from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
    except Exception:
        print("  [warn] Skipping cleanup: fontTools not available", file=sys.stderr)
        return

    font = TTFont(ttf_path)
    glyf = font["glyf"]  # type: ignore[index]

    removed_total = 0
    modified = set()
    for name in font.getGlyphOrder():
        glyph = glyf[name]  # type: ignore[index]
        if glyph.isComposite():
            continue
        end_pts = getattr(glyph, "endPtsOfContours", None)
        if not end_pts:
            continue

        coords = glyph.coordinates
        flags = glyph.flags

        new_coords = []
        new_flags = []
        new_end_pts = []

        start = 0
        removed = 0
        for end in end_pts:
            count = end - start + 1
            if count <= 2:
                removed += 1
            else:
                new_coords.extend(coords[start:end + 1])
                new_flags.extend(flags[start:end + 1])
                new_end_pts.append(len(new_coords) - 1)
            start = end + 1

        if removed:
            removed_total += removed
            modified.add(name)
            glyph.coordinates = GlyphCoordinates(new_coords)
            glyph.flags = new_flags
            glyph.endPtsOfContours = new_end_pts
            glyph.numberOfContours = len(new_end_pts)

    if removed_total:
        glyph_set = font.getGlyphSet()
        for name in modified:
            glyph = glyf[name]  # type: ignore[index]
            if hasattr(glyph, "recalcBounds"):
                glyph.recalcBounds(glyph_set)
        if hasattr(glyf, "recalcBounds"):
            glyf.recalcBounds(glyph_set)  # type: ignore[attr-defined]
        font.save(ttf_path)
        print(f"  Cleaned {removed_total} zero-area contour(s)")
    font.close()


def fix_ttf_style_flags(ttf_path, style_suffix):
    """Normalize OS/2 fsSelection and head.macStyle for style linking."""
    try:
        from fontTools.ttLib import TTFont
    except Exception:
        print("  [warn] Skipping style flag fix: fontTools not available", file=sys.stderr)
        return

    font = TTFont(ttf_path)
    os2 = font["OS/2"]
    head = font["head"]

    fs_sel = os2.fsSelection
    fs_sel &= ~((1 << 0) | (1 << 5) | (1 << 6))
    if style_suffix == "Regular":
        fs_sel |= (1 << 6)
    if "Italic" in style_suffix:
        fs_sel |= (1 << 0)
    if "Bold" in style_suffix:
        fs_sel |= (1 << 5)
    os2.fsSelection = fs_sel

    macstyle = 0
    if "Bold" in style_suffix:
        macstyle |= (1 << 0)
    if "Italic" in style_suffix:
        macstyle |= (1 << 1)
    head.macStyle = macstyle

    font.save(ttf_path)
    font.close()
    print(f"  Normalized style flags for {style_suffix}")


def autohint_ttf(ttf_path):
    """Run ttfautohint to add proper TrueType hinting.

    Kobo uses FreeType for font rasterization. Without embedded hints,
    FreeType's auto-hinter computes "blue zones" from the outlines.
    When a glyph (e.g. italic 't') has a curved tail that dips just
    below the baseline, the auto-hinter snaps that edge up to y=0 —
    shifting the entire glyph upward relative to its neighbors. This
    is most visible at small sizes.

    ttfautohint replaces FreeType's built-in auto-hinter with its own
    hinting, which may handle sub-baseline overshoots more gracefully.
    The resulting bytecode is baked into the font, so FreeType uses
    the TrueType interpreter instead of falling back to auto-hinting.
    """
    if not shutil.which("ttfautohint"):
        print("  [warn] ttfautohint not found, skipping", file=sys.stderr)
        return

    tmp_path = ttf_path + ".autohint.tmp"
    result = subprocess.run(
        ["ttfautohint", "--no-info", ttf_path, tmp_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  [warn] ttfautohint failed: {result.stderr.strip()}", file=sys.stderr)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return

    os.replace(tmp_path, ttf_path)
    print(f"  Autohinted with ttfautohint")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def check_ttfautohint():
    """Verify ttfautohint is installed before starting the build."""
    if shutil.which("ttfautohint"):
        return
    print(
        "ERROR: ttfautohint not found.\n"
        "\n"
        "ttfautohint is required for proper rendering on Kobo e-readers.\n"
        "Install it with:\n"
        "  macOS/Bazzite:      brew install ttfautohint\n"
        "  Debian/Ubuntu:      sudo apt install ttfautohint\n"
        "  Fedora:             sudo dnf install ttfautohint\n"
        "  Arch:               sudo pacman -S ttfautohint\n",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    print("=" * 60)
    print("  Readerly Build")
    print("=" * 60)

    ff_cmd = find_fontforge()
    print(f"  FontForge: {' '.join(ff_cmd)}")
    check_ttfautohint()
    print(f"  ttfautohint: {shutil.which('ttfautohint')}")

    family   = DEFAULT_FAMILY
    old_kern = False
    outline_fix  = True

    if "--customize" in sys.argv:
        print()
        family = input(f"  Font family name [{DEFAULT_FAMILY}]: ").strip() or DEFAULT_FAMILY
        old_kern_input = input("  Export with old-style kerning? [y/N]: ").strip().lower()
        old_kern = old_kern_input in ("y", "yes")
        outline_input = input("  Apply outline fixes (remove overlaps + zero-area cleanup)? [Y/n]: ").strip().lower()
        outline_fix = outline_input not in ("n", "no")

    print()
    print(f"  Family:    {family}")
    print(f"  Old kern:  {'yes' if old_kern else 'no'}")
    print(f"  Outline fix: {'yes' if outline_fix else 'no'}")
    print()

    tmp_dir = os.path.join(ROOT_DIR, "tmp")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    try:
        _build(tmp_dir, family=family, old_kern=old_kern, outline_fix=outline_fix)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _build(tmp_dir, family=DEFAULT_FAMILY, old_kern=True, outline_fix=True):
    variants = [(f"{family}-{style}", vf, wght, opsz)
                for style, vf, wght, opsz in VARIANT_STYLES]
    variant_names = [name for name, _, _, _ in variants]

    # Step 1: Instance variable fonts into static TTFs
    print("\n── Step 1: Instance variable fonts ──\n")

    for name, vf_path, wght, opsz in variants:
        ttf_out = os.path.join(tmp_dir, f"{name}.ttf")
        print(f"  Instancing {name} (wght={wght}, opsz={opsz})")

        cmd = [
            sys.executable, "-m", "fontTools.varLib.instancer",
            vf_path,
            f"wght={wght}",
            f"opsz={opsz}",
            "-o", ttf_out,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout, end="")
        if result.returncode != 0:
            print(f"\nERROR: instancer failed for {name}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(1)


    print(f"  {len(variants)} font(s) instanced.")

    # Step 2: Apply vertical scale (opens TTF, saves as SFD)
    print("\n── Step 2: Scale lowercase ──\n")

    scale_code = ff_scale_lowercase_script()
    condense_code = ff_condense_script()
    overlap_code = ff_remove_overlaps_script()

    for name in variant_names:
        ttf_path = os.path.join(tmp_dir, f"{name}.ttf")
        sfd_path = os.path.join(tmp_dir, f"{name}.sfd")
        print(f"Scaling: {name}")

        steps = [
            ("Scaling Y", scale_code),
            ("Condensing X", condense_code),
        ]
        if outline_fix:
            steps.append(("Removing overlaps", overlap_code))
        script = build_per_font_script(ttf_path, sfd_path, steps)
        run_fontforge_script(script)

    # Step 3: Apply metrics and rename (opens SFD, saves as SFD)
    print("\n── Step 3: Apply metrics and rename ──\n")

    metrics_code = ff_metrics_script()
    lineheight_code = ff_lineheight_script()
    rename_code = ff_rename_script()
    version_code = ff_version_script()
    license_code = ff_license_script()

    for name in variant_names:
        sfd_path = os.path.join(tmp_dir, f"{name}.sfd")
        print(f"Processing: {name}")
        print("-" * 40)

        # Set fontname so rename.py can detect the correct style suffix
        set_fontname = f'f.fontname = {name!r}'
        set_family   = f'FAMILY = {family!r}'
        set_version  = f'VERSION = {FONT_VERSION!r}'
        set_license  = f'COPYRIGHT_TEXT = {COPYRIGHT_TEXT!r}'

        script = build_per_font_script(sfd_path, sfd_path, [
            ("Setting vertical metrics", metrics_code),
            ("Adjusting line height", lineheight_code),
            ("Setting fontname for rename", set_fontname),
            ("Updating font names", set_family + "\n" + rename_code),
            ("Setting version", set_version + "\n" + version_code),
            ("Setting license", set_license + "\n" + license_code),
        ])
        run_fontforge_script(script)

    # Step 4: Export to out/sfd and out/ttf
    print("\n── Step 4: Export ──\n")
    os.makedirs(OUT_SFD_DIR, exist_ok=True)
    os.makedirs(OUT_TTF_DIR, exist_ok=True)

    for name in variant_names:
        sfd_path = os.path.join(tmp_dir, f"{name}.sfd")
        ttf_path = os.path.join(OUT_TTF_DIR, f"{name}.ttf")
        style_suffix = name.split("-")[-1] if "-" in name else "Regular"

        # Copy final SFD to out/sfd/
        shutil.copy2(sfd_path, os.path.join(OUT_SFD_DIR, f"{name}.sfd"))
        print(f"  -> {OUT_SFD_DIR}/{name}.sfd")

        # Export TTF
        script = build_export_script(sfd_path, ttf_path, old_kern=old_kern)
        run_fontforge_script(script)
        if outline_fix:
            clean_ttf_degenerate_contours(ttf_path)
        fix_ttf_style_flags(ttf_path, style_suffix)
        autohint_ttf(ttf_path)


    print("\n" + "=" * 60)
    print("  Build complete!")
    print(f"  SFD fonts are in: {OUT_SFD_DIR}/")
    print(f"  TTF fonts are in: {OUT_TTF_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
