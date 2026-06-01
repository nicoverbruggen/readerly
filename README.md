# Readerly

**Readerly** is modified font based on [Newsreader](https://github.com/productiontype/Newsreader), while attempting to be metrically very similar to [Bookerly](https://en.wikipedia.org/wiki/Bookerly), the default font on Kindle devices, to provide a similar reading experience.

<kbd><img src="./screenshot.png" width='400px'/></kbd>

When I was doing my usual font tweaking for my [ebook-fonts](https://github.com/nicoverbruggen/ebook-fonts) repository, I stumbled upon variable fonts exporting. Doing this for Newsreader gave me some interesting results at small optical sizes: the font was now reminding me of Bookerly.

I asked myself the question: how close can we get to the metrics of Bookerly while still retaining Newsreader and keeping the font licensed under the OFL, and maybe making some mild manual edits?

The goal was to get a metrically/visually similar font, without actually copying glyphs or anything that would infringe upon the rights of the original creators; after all, Newsreader is a very beautiful font as a starting point.

To get to the final result, I decided to use the variable font and work on it. The original is located in `src` and is available under the same OFL as the end result, which is included in `LICENSE`.

## Downloads

Three versions are generated via the pipeline of the [latest release](../../releases/latest).

### 1. KF Readerly

**Use this if you have a Kobo e-reader**, this version contains optimizations and fixes made with [Kobo Font Fix](https://github.com/nicoverbruggen/kobo-font-fix). These are Kobo-optimized TrueType fonts with a legacy kern table and `KF` prefix.

### 2. Readerly

The standard, non-Kobo fonts, as TrueType files. Useful for other e-readers and use on your desktop computer or smartphone.

### 3. Readerly Web

WOFF2 webfonts for use with `@font-face` in browsers. You can use this CSS as the basis:

```css
@font-face {
  font-family: 'Readerly';
  src: url('/fonts/Readerly-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Readerly';
  src: url('/fonts/Readerly-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Readerly';
  src: url('/fonts/Readerly-Italic.woff2') format('woff2');
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: 'Readerly';
  src: url('/fonts/Readerly-BoldItalic.woff2') format('woff2');
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}
```

## System requirements

- **Python 3**
- **[fontTools](https://github.com/fonttools/fonttools)** — install with `pip install fonttools`
- **[brotli](https://pypi.org/project/Brotli/)** — required for WOFF2 generation; install with `pip install brotli`
- **[skia-pathops](https://pypi.org/project/skia-pathops/)** — required by Kobo Font Fix for outline simplification; install with `pip install skia-pathops`
- **[FontForge](https://fontforge.org)** — the build script auto-detects FontForge from PATH, Flatpak, or the macOS app bundle
- **[ttfautohint](https://freetype.org/ttfautohint/)** — required for proper rendering on Kobo e-readers

## Project structure

- `src`: Newsreader variable font TTFs
- `build.py`: The build script to generate Readerly
- `LICENSE`: The OFL license
- `COPYRIGHT`: Copyright information, later embedded in font
- `VERSION`: The version number, later embedded in font

After running `build.py`, you should get:

- `out/ttf`: final TTF fonts (generated)
- `out/kf`: Kobo-optimized TTF fonts (generated)
- `out/web`: WOFF2 webfonts (generated)

The build script (`build.py`) uses `fontTools` and FontForge to transform the Newsreader variable fonts into Readerly. After export, it post-processes the TTFs: clamping x-height overshoots that cause uneven rendering on e-ink, normalizing style flags, and autohinting with `ttfautohint` for Kobo's FreeType renderer. Configuration and step-by-step details live in the header comments of `build.py`.

## Building

If you want to build the font yourself, you can use the `fntbld-oci` container or build it natively. You can find instructions on how to do so in [BUILD.md](./BUILD.md).
