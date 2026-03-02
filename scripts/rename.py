"""
FontForge: Update font name metadata
─────────────────────────────────────
Replaces Newsreader references with Readerly in all name table entries
and font-level properties.

Run inside FontForge (or via build.py which sets `f` before running this).
"""

import fontforge

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FAMILY = "Readerly"

# Map style suffixes to weight strings
STYLE_MAP = {
    "Regular": "Regular",
    "Bold": "Bold",
    "Italic": "Italic",
    "BoldItalic": "Bold Italic",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DETECT STYLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Determine style from the current fontname (e.g. "Readerly-BoldItalic")
style_suffix = f.fontname.split("-")[-1] if "-" in f.fontname else "Regular"
style_display = STYLE_MAP.get(style_suffix, style_suffix)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPDATE FONT PROPERTIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

f.fontname = f"{FAMILY}-{style_suffix}"
f.familyname = FAMILY
f.fullname = f"{FAMILY} {style_display}"

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
print("Done.")
