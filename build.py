#!/usr/bin/env python3
"""
Readerly Build Script
─────────────────────
Orchestrates the full font build pipeline:

  1. Copies ./src/*.sfd → ./mutated/
  2. Applies vertical scale (scale.py)
  3. Applies vertical metrics (metrics.py)
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
MUTATED_DIR = os.path.join(ROOT_DIR, "mutated")
OUT_DIR     = os.path.join(ROOT_DIR, "out")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

FLATPAK_APP = "org.fontforge.FontForge"

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


def build_per_font_script(sfd_path, steps):
    """
    Build a FontForge Python script that opens an .sfd file, runs the given
    step scripts (which expect `f` to be the active font), saves, and closes.

    Each step is a (label, script_body) tuple. The script_body should use `f`
    as the font variable.
    """
    parts = [
        f'import fontforge',
        f'f = fontforge.open({sfd_path!r})',
        f'print("\\nOpened: " + f.fontname + "\\n")',
    ]
    for label, body in steps:
        parts.append(f'print("── {label} ──\\n")')
        parts.append(body)
    parts.append(f'f.save({sfd_path!r})')
    parts.append(f'print("\\nSaved: {sfd_path}\\n")')
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

    # Step 1: Copy src → mutated
    print("\n── Step 1: Copy sources to ./mutated ──\n")
    if os.path.exists(MUTATED_DIR):
        shutil.rmtree(MUTATED_DIR)
    shutil.copytree(SRC_DIR, MUTATED_DIR)
    sfd_files = sorted(f for f in os.listdir(MUTATED_DIR) if f.endswith(".sfd"))
    for f in sfd_files:
        print(f"  Copied: {f}")
    print(f"  {len(sfd_files)} font(s) ready.")

    # Step 2: Apply vertical scale to lowercase glyphs
    print("\n── Step 2: Scale lowercase ──\n")

    scale_code = load_script_as_function(os.path.join(SCRIPTS_DIR, "scale.py"))

    for sfd_name in sfd_files:
        sfd_path = os.path.join(MUTATED_DIR, sfd_name)
        print(f"Scaling: {sfd_name}")

        script = build_per_font_script(sfd_path, [
            ("Scaling Y", scale_code),
        ])
        run_fontforge_script(script)

    # Step 3: Apply metrics.py to each font
    print("\n── Step 3: Apply vertical metrics ──\n")

    metrics_code = load_script_as_function(os.path.join(SCRIPTS_DIR, "metrics.py"))

    for sfd_name in sfd_files:
        sfd_path = os.path.join(MUTATED_DIR, sfd_name)
        print(f"Processing: {sfd_name}")
        print("-" * 40)

        script = build_per_font_script(sfd_path, [
            ("Setting vertical metrics", metrics_code),
        ])
        run_fontforge_script(script)

    # Step 4: Export to TTF
    print("\n── Step 4: Export to TTF ──\n")
    os.makedirs(OUT_DIR, exist_ok=True)

    for sfd_name in sfd_files:
        sfd_path = os.path.join(MUTATED_DIR, sfd_name)
        ttf_name = sfd_name.replace(".sfd", ".ttf")
        ttf_path = os.path.join(OUT_DIR, ttf_name)

        script = build_export_script(sfd_path, ttf_path)
        run_fontforge_script(script)

    print("\n" + "=" * 60)
    print("  Build complete!")
    print(f"  TTF fonts are in: {OUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
