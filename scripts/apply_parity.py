"""Apply Readerly accent corrections, Polish forms, and small caps before hinting.

The five donor outlines per style come from Libron develop at 4a444ac.
All other letters and the small caps use Readerly's own outlines.
"""
from pathlib import Path
import sys

import fontforge
import psMat

from smallcaps import apply as add_smallcaps


def replace_outline(font, donor, name, target=None):
    glyph = font[target or name]
    width, anchors = glyph.width, glyph.anchorPoints
    glyph.references = ()
    glyph.layers[1] = donor[name].layers[1]
    glyph.width = width
    glyph.anchorPoints = anchors


def fix_accents(font, donor, style):
    # Match the normal i-caron to dotless i plus the same mark as i-breve.
    target = font[fontforge.nameFromUnicode(0x01D0)]
    exemplar = font['ibreve']
    mark_refs = [(n, m) for n, m, _ in exemplar.references
                 if n != 'dotlessi']
    if len(mark_refs) != 1:
        raise ValueError('Expected one mark reference in ibreve')
    caron = font[fontforge.nameFromUnicode(0x030C)].glyphname
    width = target.width
    target.clear()
    target.references = (('dotlessi', (1, 0, 0, 1, 0, 0)),
                         (caron, mark_refs[0][1]))
    target.width = width

    # Shift these default acutes towards the letter, as in Libron's Polish pass.
    acute = font[fontforge.nameFromUnicode(0x0301)].glyphname
    shift = -60 if 'Bold' in style else -50
    for name in ('cacute', 'nacute', 'oacute', 'zacute'):
        glyph = font[name]
        glyph.references = tuple(
            (ref, matrix[:4] + (matrix[4] + shift, matrix[5]), selected)
            if ref == acute else (ref, matrix, selected)
            for ref, matrix, selected in glyph.references)

    replace_outline(font, donor, 'uni1E9E', fontforge.nameFromUnicode(0x1E9E))
    font[fontforge.nameFromUnicode(0x1E9E)].width = donor['uni1E9E'].width
    replace_outline(font, donor, 'Aogonek')
    ogonek = font[fontforge.nameFromUnicode(0x0328)].glyphname
    replace_outline(font, donor, 'ogonek', ogonek)
    mark_anchors = {a[0]: (a[2], a[3]) for a in font[ogonek].anchorPoints
                    if a[1] == 'mark'}
    for name, base_name in (('aogonek', 'a'), ('eogonek', 'e')):
        glyph = font[name]
        anchor = next(a for a in font[base_name].anchorPoints
                      if a[1] == 'base' and a[0] in mark_anchors)
        mx, my = mark_anchors[anchor[0]]
        dx = -70 if name == 'eogonek' and 'Italic' in style else 0
        dy = 40 if name == 'eogonek' else 0
        width = glyph.width
        glyph.clear()
        glyph.references = ((base_name, (1, 0, 0, 1, 0, 0)),
                            (ogonek, (1.03, 0, 0, 1.08,
                                      anchor[2] - 1.03 * mx + dx,
                                      anchor[3] - 1.08 * my + dy)))
        glyph.width = width

    # Synthetic t marks start 50 units above the ascender. Keep 110 units
    # of clearance, with the italic correction measured in Libron.
    dxs = {'Regular': (-30, 0), 'Bold': (-15, 0),
           'Italic': (-85, -65), 'BoldItalic': (-90, -70)}
    for cp, dx in zip((0x1E6B, 0x1E97), dxs[style]):
        glyph = font[fontforge.nameFromUnicode(cp)]
        base_top = font['t'].boundingBox()[3]
        layer = glyph.layers[1]
        adjusted = fontforge.layer()
        adjusted.is_quadratic = layer.is_quadratic
        for contour in layer:
            if contour.boundingBox()[1] > base_top:
                contour.transform(psMat.translate(dx, 60))
            adjusted += contour
        glyph.layers[1] = adjusted


def clone_kerning(font, mapping):
    # Localized letters must retain both sides of class and explicit kerning.
    for lookup in font.gpos_lookups:
        if font.getLookupInfo(lookup)[0] != 'gpos_pair':
            continue
        for sub in font.getLookupSubtables(lookup):
            if font.isKerningClass(sub):
                first, second, values = font.getKerningClass(sub)
                def extend(classes):
                    return tuple(None if members is None else tuple(members) +
                                 tuple(mapping[n] for n in members if n in mapping)
                                 for members in classes)
                font.alterKerningClass(sub, extend(first), extend(second), values)
            else:
                entries = [(g.glyphname, e) for g in font.glyphs()
                           for e in g.getPosSub(sub) if e[1] == 'Pair']
                for left, entry in entries:
                    right = entry[2]
                    for a in (left, mapping[left]) if left in mapping else (left,):
                        for b in (right, mapping[right]) if right in mapping else (right,):
                            if (a, b) != (left, right):
                                font[a].addPosSub(sub, b, *entry[3:])


def add_polish(font, donor, style):
    mapping = {}
    for name in (font[fontforge.nameFromUnicode(0x0301)].glyphname, 'acutecomb.case'):
        alternate = name + '.loclPLK'
        glyph = font.createChar(-1, alternate)
        glyph.layers[1] = donor[name + '.loclPLK'].layers[1]
        glyph.width = font[name].width
        glyph.anchorPoints = font[name].anchorPoints
        glyph.glyphclass = font[name].glyphclass
        mapping[name] = alternate
    for ch in 'ćńóśźĆŃÓŚŹ':
        name = font[fontforge.nameFromUnicode(ord(ch))].glyphname
        for source in (name, name + '.sc') if ch.isupper() else (name,):
            base = font[source]
            glyph = font.createChar(-1, source + '.loclPLK')
            glyph.layers[1] = base.layers[1]
            glyph.references = tuple((mapping.get(n, n), m, selected)
                                     for n, m, selected in base.references)
            # The steeper acute needs a little more room on upright lowercase.
            # Libron's follow-up correction leaves capitals and small caps alone.
            if ch.islower() and style in ('Regular', 'Bold'):
                glyph.references = tuple(
                    (ref, matrix[:4] + (matrix[4] + 50, matrix[5]), selected)
                    if ref.endswith('.loclPLK') else (ref, matrix, selected)
                    for ref, matrix, selected in glyph.references)
            if glyph.references == base.references:
                raise ValueError(f'{source} has no acute reference')
            glyph.width = base.width
            glyph.anchorPoints = base.anchorPoints
            glyph.glyphclass = base.glyphclass
            mapping[source] = glyph.glyphname
    clone_kerning(font, mapping)
    # A new language system must inherit all default Latin features.
    # Otherwise Polish text loses the source font's ligatures and figures.
    for existing in font.gsub_lookups + font.gpos_lookups:
        features = font.getLookupInfo(existing)[2]
        extended = tuple((feature, tuple(
            (script, languages + ('PLK ',) if script == 'latn' and
             'dflt' in languages and 'PLK ' not in languages else languages)
            for script, languages in systems)) for feature, systems in features)
        font.lookupSetFeatureList(existing, extended)
    lookup = 'Readerly Polish forms'
    # Small caps run first so their Polish alternates are selected too.
    after = "'c2sc' Capitals to Small Capitals in Latin"
    font.addLookup(lookup, 'gsub_single', (),
                   (('locl', (('latn', ('PLK ',)),)),), after)
    font.addLookupSubtable(lookup, lookup + ' subtable')
    for source, target in mapping.items():
        font[source].addPosSub(lookup + ' subtable', target)
    print(f'  Added {len(mapping)} Polish alternates')


def main(path, style):
    font = fontforge.open(path)
    donor = fontforge.open(str(Path(__file__).resolve().parents[1] /
                               'src' / 'parity' / (style + '.sfd')))
    fix_accents(font, donor, style)
    add_smallcaps(font, style)
    add_polish(font, donor, style)
    font.selection.all()
    font.removeOverlap()
    font.correctDirection()
    font.generate(path, flags=('opentype', 'no-FFTM-table'))
    donor.close()
    font.close()


if __name__ == '__main__':
    main(*sys.argv[1:])
