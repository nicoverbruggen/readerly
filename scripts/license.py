"""
FontForge: Set copyright information
─────────────────────────────────────
Sets the copyright notice from COPYRIGHT_TEXT injected by build.py.

Run inside FontForge (or via build.py which sets `f` and `COPYRIGHT_TEXT` before running this).
"""

import fontforge

f = fontforge.activeFont()

# COPYRIGHT_TEXT is injected by build.py before this script runs

lang = "English (US)"

f.copyright = COPYRIGHT_TEXT
f.appendSFNTName(lang, "Copyright", COPYRIGHT_TEXT)

print(f"  Copyright: {COPYRIGHT_TEXT.splitlines()[0]}")
print("Done.")
