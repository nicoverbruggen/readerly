# Readerly

**Readerly** is modified font based on [Newsreader](https://github.com/productiontype/Newsreader), while attempting to be metrically very similar to [Bookerly](https://en.wikipedia.org/wiki/Bookerly), the default font on Kindle devices, to provide a similar reading experience.

When I was doing my usual font tweaking for my [ebook-fonts](https://github.com/nicoverbruggen/ebook-fonts) repository, I stumbled upon variable fonts exporting. Doing this for Newsreader gave me some interesting results at small optical sizes: the font was now reminding me of Bookerly.

I asked myself the question: how close can we get to the metrics of Bookerly while still retaining Newsreader and keeping the font licensed under the OFL, and maybe making some mild manual edits?

The goal was to get a metrically/visually similar font, without actually copying glyphs or anything that would infringe upon the rights of the original creators; after all, Newsreader is a very beautiful font as a starting point.

To get to the final result, I decided to use the variable font and work on it. The original is located in `src` and is available under the same OFL as the end result, which is included in `LICENSE`.

## Project structure

- `src`: Newsreader variable font TTFs
- `scripts`: FontForge Python scripts applied during the build
- `build.py`: The build script to generate Readerly
- `LICENSE`: The OFL license
- `COPYRIGHT`: Copyright information, later embedded in font
- `VERSION`: The version number, later embedded in font

After running `build.py`, you should get:

- `out/sfd`: FontForge source files (generated)
- `out/ttf`: final TTF fonts (generated)

## Prerequisites

- **Python 3**
- **[fontTools](https://github.com/fonttools/fonttools)** — install with `pip install fonttools`
- **[FontForge](https://fontforge.org)** — the build script auto-detects FontForge from PATH, Flatpak, or the macOS app bundle

## Building

```
python3 build.py
```

To customize the font family name or disable old-style kerning:

```
python3 build.py --customize
```

The build script (`build.py`) uses `fontTools` and FontForge to transform the Newsreader variable fonts into Readerly. Each step is described below.

#### Step 1: Instancing

The Newsreader variable font supports two axes: optical size (`opsz`) and weight (`wght`). Using `fontTools.instancer`, the variable fonts are pinned to specific axis values to produce static TTFs. A small optical size (`opsz=9`) is used as the starting point because it produces tighter, more compact letterforms that resemble Bookerly's proportions.

Variant configuration (in `build.py`):
- Regular: wght=450, opsz=9
- Bold: wght=550, opsz=9
- Italic: wght=450, opsz=9
- BoldItalic: wght=550, opsz=9

#### Step 2: Scaling, condensing, and overlap removal

Three transforms are applied in sequence via FontForge:

- **Vertical scaling** (`scale.py`): Lowercase glyphs are scaled up vertically (and slightly horizontally) to increase the x-height, bringing it closer to Bookerly's proportions.
- **Horizontal condensing** (`condense.py`): All glyphs are narrowed slightly to match Bookerly's more compact character widths.
- **Overlap removal** (`overlaps.py`): Overlapping contours are merged into clean, unified outlines and winding direction is corrected. Variable fonts commonly use overlapping paths to aid interpolation between weights. After instancing, these overlaps remain. While desktop renderers handle this fine, e-readers like Kobo apply synthetic font weight scaling that can cause visible artifacts (gaps, blobs, uneven strokes) when contours overlap. Merging the overlaps into single paths prevents these rendering issues.

#### Step 3: Metrics, naming, version, and copyright

Several metadata scripts are applied via FontForge:

- **Vertical metrics** (`metrics.py`): Measures design landmarks (cap height, ascender, x-height, descender) from actual glyph bounding boxes and sets OS/2 Typo metrics to the ink boundaries. Enables `USE_TYPO_METRICS`.
- **Line height** (`lineheight.py`): Overrides Win/hhea metrics to control line spacing and selection box height. Values are expressed as multiples of the font's UPM (units per em) — the coordinate grid that all glyph measurements are defined in (Newsreader uses 2000 UPM). A line height of 1.0x UPM means lines are spaced exactly one em apart, with an 80/20 ascender/descender split. The selection box height (1.32x UPM) controls the highlighted area when selecting text.
- **Renaming** (`rename.py`): Rewrites all SFNT name table entries from Newsreader to Readerly, and sets the correct PS weight string and OS/2 weight class for each variant.
- **Version** (`version.py`): Sets the font version and `head.fontRevision` from `./VERSION`.
- **Copyright** (`license.py`): Sets the copyright notice from `./COPYRIGHT`.

#### Step 4: Export

The final fonts are exported from FontForge as both SFD (FontForge source) and TTF with old-style kern tables for maximum compatibility with e-reader rendering engines.
