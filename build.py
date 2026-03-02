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

ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
SRC_DIR     = os.path.join(ROOT_DIR, "src")
OUT_DIR     = os.path.join(ROOT_DIR, "out")
OUT_SFD_DIR = os.path.join(OUT_DIR, "sfd")
OUT_TTF_DIR = os.path.join(OUT_DIR, "ttf")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

REGULAR_VF = os.path.join(SRC_DIR, "Newsreader-VariableFont_opsz,wght.ttf")
ITALIC_VF  = os.path.join(SRC_DIR, "Newsreader-Italic-VariableFont_opsz,wght.ttf")

with open(os.path.join(ROOT_DIR, "VERSION")) as _vf:
    FONT_VERSION = _vf.read().strip()

with open(os.path.join(ROOT_DIR, "COPYRIGHT")) as _cf:
    COPYRIGHT_TEXT = _cf.read().strip()

DEFAULT_FAMILY = "Readerly"

VARIANT_STYLES = [
    # (style_suffix, source_vf, wght, opsz)
    ("Regular",    REGULAR_VF, 450, 9),
    ("Bold",       REGULAR_VF, 550, 9),
    ("Italic",     ITALIC_VF,  450, 9),
    ("BoldItalic", ITALIC_VF,  550, 9),
]

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


def load_script_as_function(script_path):
    """
    Read a script file and adapt it from using fontforge.activeFont() to
    using a pre-opened font variable `f`.
    """
    with open(script_path) as fh:
        code = fh.read()
    # Replace activeFont() call — the font is already open as `f`
    code = code.replace("fontforge.activeFont()", "f")
    return code


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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("=" * 60)
    print("  Readerly Build")
    print("=" * 60)

    ff_cmd = find_fontforge()
    print(f"  FontForge: {' '.join(ff_cmd)}")

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

    scale_code    = load_script_as_function(os.path.join(SCRIPTS_DIR, "scale.py"))
    condense_code = load_script_as_function(os.path.join(SCRIPTS_DIR, "condense.py"))
    overlap_code  = load_script_as_function(os.path.join(SCRIPTS_DIR, "overlaps.py"))

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

    metrics_code    = load_script_as_function(os.path.join(SCRIPTS_DIR, "metrics.py"))
    lineheight_code = load_script_as_function(os.path.join(SCRIPTS_DIR, "lineheight.py"))
    rename_code     = load_script_as_function(os.path.join(SCRIPTS_DIR, "rename.py"))
    version_code    = load_script_as_function(os.path.join(SCRIPTS_DIR, "version.py"))
    license_code    = load_script_as_function(os.path.join(SCRIPTS_DIR, "license.py"))

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

        # Copy final SFD to out/sfd/
        shutil.copy2(sfd_path, os.path.join(OUT_SFD_DIR, f"{name}.sfd"))
        print(f"  -> {OUT_SFD_DIR}/{name}.sfd")

        # Export TTF
        script = build_export_script(sfd_path, ttf_path, old_kern=old_kern)
        run_fontforge_script(script)
        if outline_fix:
            clean_ttf_degenerate_contours(ttf_path)


    print("\n" + "=" * 60)
    print("  Build complete!")
    print(f"  SFD fonts are in: {OUT_SFD_DIR}/")
    print(f"  TTF fonts are in: {OUT_TTF_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
