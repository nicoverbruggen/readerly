# Readerly

When I was doing my usual font tweaking for my ebook-fonts repository, I stumbled upon variable fonts exporting. Doing this for Newsreader gave me some interesting results at small optical sizes: the font was now reminding me of Bookerly.

I asked myself the question: how close can we get to the visual appearance of Bookerly while still retaining Newsreader and keeping the font licensed under the OFL?

The goal is to get a metrically/visually similar font, without actually copying glyphs or anything that would infringe upon the rights of the original creators.

To accomplish this, I wanted to start from the 9pt font, which I exported. Then, it was a matter of playing around with scripts and manual edits to see if I could get something that was optically close enough.

## Project structure

- `./src`: Newsreader variable font TTFs (source of truth)
- `./scripts`: FontForge Python scripts applied during the build
  - `scale.py`: scales lowercase glyphs vertically to increase x-height
  - `metrics.py`: sets vertical metrics (OS/2 Typo, Win, hhea)
  - `lineheight.py`: adjusts OS/2 Typo metrics to control line spacing
  - `rename.py`: updates font name metadata from Newsreader to Readerly
  - `version.py`: sets the font version from `./VERSION`
- `./src_processed`: intermediate files after instancing/processing (generated)
- `./out`: final TTF fonts (generated)

## Building

```
python3 build.py
```

This uses `fontTools.instancer` and the Flatpak version of FontForge to:

1. Instance the variable fonts into static TTFs at configured axis values (opsz, wght)
2. Scale lowercase glyphs (configurable in `scripts/scale.py`)
3. Set vertical metrics, adjust line height, and update font names
4. Export to TTF with old-style kerning in `./out`

Variant configuration (in `build.py`):
- Regular: wght=400, opsz=9
- Bold: wght=550, opsz=9
- Italic: wght=400, opsz=9
- BoldItalic: wght=550, opsz=9
