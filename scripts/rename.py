"""
FontForge: Update font name metadata
─────────────────────────────────────
Replaces Newsreader references with the target family name in all name table
entries and font-level properties.

FAMILY is injected by build.py before this script runs (defaults to "Readerly").
Run inside FontForge (or via build.py which sets `f` and `FAMILY` before running this).
"""

import fontforge

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# FAMILY is injected by build.py; default if run standalone
if "FAMILY" not in dir():
    FAMILY = "Readerly"

# Map style suffixes to display names, PS weight strings, and OS/2 weight classes
STYLE_MAP = {
    "Regular":    ("Regular",     "Book", 400),
    "Bold":       ("Bold",        "Bold", 700),
    "Italic":     ("Italic",      "Book", 400),
    "BoldItalic": ("Bold Italic", "Bold", 700),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DETECT STYLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Determine style from the current fontname (e.g. "Readerly-BoldItalic")
style_suffix = f.fontname.split("-")[-1] if "-" in f.fontname else "Regular"
style_display, ps_weight, os2_weight = STYLE_MAP.get(style_suffix, (style_suffix, "Book", 400))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPDATE FONT PROPERTIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

f.fontname = f"{FAMILY}-{style_suffix}"
f.familyname = FAMILY
f.fullname = f"{FAMILY} {style_display}"
f.weight = ps_weight
f.os2_weight = os2_weight

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPDATE SFNT NAME TABLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

lang = "English (US)"

f.appendSFNTName(lang, "Family", FAMILY)
f.appendSFNTName(lang, "SubFamily", style_display)
f.appendSFNTName(lang, "Fullname", f"{FAMILY} {style_display}")
f.appendSFNTName(lang, "PostScriptName", f"{FAMILY}-{style_suffix}")
f.appendSFNTName(lang, "Preferred Family", FAMILY)
f.appendSFNTName(lang, "Preferred Styles", style_display)
f.appendSFNTName(lang, "Compatible Full", f"{FAMILY} {style_display}")
f.appendSFNTName(lang, "UniqueID", f"{FAMILY} {style_display}")

# Clear Newsreader-specific entries
f.appendSFNTName(lang, "Trademark", "")
f.appendSFNTName(lang, "Manufacturer", "")
f.appendSFNTName(lang, "Designer", "")
f.appendSFNTName(lang, "Vendor URL", "")
f.appendSFNTName(lang, "Designer URL", "")

count = 0
for name in f.sfnt_names:
    count += 1
print(f"  Updated {count} name entries for {FAMILY} {style_display}")
print(f"  PS weight: {ps_weight}, OS/2 usWeightClass: {os2_weight}")
print("Done.")
