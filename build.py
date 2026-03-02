#!/usr/bin/env python3
"""
Readerly Build Script
─────────────────────
Orchestrates the full font build pipeline:

  1. Instances variable fonts into static TTFs (fontTools.instancer)
  2. Applies vertical scale (scale.py) via FontForge
  3. Applies vertical metrics, line height, rename (metrics.py, lineheight.py, rename.py)
  4. Exports to TTF with old-style kern table → ./out/

Uses the Flatpak version of FontForge.
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
MUTATED_DIR = os.path.join(ROOT_DIR, "src_processed")
OUT_DIR     = os.path.join(ROOT_DIR, "out")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

FLATPAK_APP = "org.fontforge.FontForge"

REGULAR_VF = os.path.join(SRC_DIR, "Newsreader-VariableFont_opsz,wght.ttf")
ITALIC_VF  = os.path.join(SRC_DIR, "Newsreader-Italic-VariableFont_opsz,wght.ttf")

VARIANTS = [
    # (output_name, source_vf, wght, opsz)
    ("Readerly-Regular",    REGULAR_VF, 430, 9),
    ("Readerly-Bold",       REGULAR_VF, 550, 9),
    ("Readerly-Italic",     ITALIC_VF,  430, 9),
    ("Readerly-BoldItalic", ITALIC_VF,  550, 9),
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_fontforge_script(script_text):
    """Run a Python script inside FontForge via flatpak."""
    result = subprocess.run(
        [
            "flatpak", "run", "--command=fontforge", FLATPAK_APP,
            "-lang=py", "-script", "-",
        ],
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


def build_export_script(sfd_path, ttf_path):
    """Build a FontForge script that opens an .sfd and exports to TTF with old-style kern."""
    return textwrap.dedent(f"""\
        import fontforge

        f = fontforge.open({sfd_path!r})
        print("Exporting: " + f.fontname)

        # Generate TTF with old-style kern table and Windows-compatible kern pairs
        flags = ("opentype", "old-kern", "no-FFTM-table", "winkern")
        f.generate({ttf_path!r}, flags=flags)

        print("  -> " + {ttf_path!r})
        f.close()
    """)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("=" * 60)
    print("  Readerly Build")
    print("=" * 60)

    # Step 1: Instance variable fonts into static TTFs
    print("\n── Step 1: Instance variable fonts ──\n")
    if os.path.exists(MUTATED_DIR):
        shutil.rmtree(MUTATED_DIR)
    os.makedirs(MUTATED_DIR)

    for name, vf_path, wght, opsz in VARIANTS:
        ttf_out = os.path.join(MUTATED_DIR, f"{name}.ttf")
        print(f"  Instancing {name} (wght={wght}, opsz={opsz})")

        cmd = [
            sys.executable, "-m", "fontTools", "varLib.instancer",
            vf_path,
            "-o", ttf_out,
            f"wght={wght}",
            f"opsz={opsz}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout, end="")
        if result.returncode != 0:
            print(f"\nERROR: instancer failed for {name}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(1)

    variant_names = [name for name, _, _, _ in VARIANTS]
    print(f"  {len(VARIANTS)} font(s) instanced.")

    # Step 2: Apply vertical scale (opens TTF, saves as SFD)
    print("\n── Step 2: Scale lowercase ──\n")

    scale_code    = load_script_as_function(os.path.join(SCRIPTS_DIR, "scale.py"))
    condense_code = load_script_as_function(os.path.join(SCRIPTS_DIR, "condense.py"))

    for name in variant_names:
        ttf_path = os.path.join(MUTATED_DIR, f"{name}.ttf")
        sfd_path = os.path.join(MUTATED_DIR, f"{name}.sfd")
        print(f"Scaling: {name}")

        script = build_per_font_script(ttf_path, sfd_path, [
            ("Scaling Y", scale_code),
            ("Condensing X", condense_code),
        ])
        run_fontforge_script(script)

    # Step 3: Apply metrics and rename (opens SFD, saves as SFD)
    print("\n── Step 3: Apply metrics and rename ──\n")

    metrics_code    = load_script_as_function(os.path.join(SCRIPTS_DIR, "metrics.py"))
    lineheight_code = load_script_as_function(os.path.join(SCRIPTS_DIR, "lineheight.py"))
    rename_code     = load_script_as_function(os.path.join(SCRIPTS_DIR, "rename.py"))

    for name in variant_names:
        sfd_path = os.path.join(MUTATED_DIR, f"{name}.sfd")
        print(f"Processing: {name}")
        print("-" * 40)

        # Set fontname so rename.py can detect the correct style suffix
        set_fontname = f'f.fontname = {name!r}'

        script = build_per_font_script(sfd_path, sfd_path, [
            ("Setting vertical metrics", metrics_code),
            ("Adjusting line height", lineheight_code),
            ("Setting fontname for rename", set_fontname),
            ("Updating font names", rename_code),
        ])
        run_fontforge_script(script)

    # Step 4: Export to TTF
    print("\n── Step 4: Export to TTF ──\n")
    os.makedirs(OUT_DIR, exist_ok=True)

    for name in variant_names:
        sfd_path = os.path.join(MUTATED_DIR, f"{name}.sfd")
        ttf_path = os.path.join(OUT_DIR, f"{name}.ttf")

        script = build_export_script(sfd_path, ttf_path)
        run_fontforge_script(script)

    print("\n" + "=" * 60)
    print("  Build complete!")
    print(f"  TTF fonts are in: {OUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
