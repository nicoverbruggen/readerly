"""
FontForge: Set font version
────────────────────────────
Sets the font version from a VERSION variable injected by build.py.

Run inside FontForge (or via build.py which sets `f` and `VERSION` before running this).
"""

import fontforge

f = fontforge.activeFont()

# VERSION is injected by build.py before this script runs
# e.g. VERSION = "1.0"

version_str = "Version " + VERSION

f.version = VERSION
f.sfntRevision = float(VERSION)
f.appendSFNTName("English (US)", "Version", version_str)

print(f"  Version set to: {version_str}")
print(f"  head.fontRevision set to: {float(VERSION)}")
print("Done.")
