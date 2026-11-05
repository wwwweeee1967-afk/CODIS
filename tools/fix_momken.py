"""Momken ships with NO OpenType shaping (its GSUB is empty): the joined letter forms live only at the legacy Arabic Presentation-Forms
code points (FE70-FEFF). Chrome's HarfBuzz falls back to those code points, but WebKit/CoreText (iPhone) does not, so headings render as
disconnected letters there. This adds the standard Arabic shaping features (isol/fina/init/medi + lam-alef rlig) that simply map each base
letter to the presentation glyphs ALREADY in the font. Outlines, metrics, GPOS and the name table (designer credit) are untouched.
  py -3 tools/fix_momken.py      (needs fonttools)  ->  assets/fonts/source/Momken_Typeface_Regular_shaped.otf"""
import os, unicodedata, io
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts', 'source')
f = TTFont(os.path.join(A, 'Momken_Typeface_Regular.otf')); cm = f.getBestCmap()
nm = lambda cp: cm.get(cp)
feat = {'isolated': {}, 'final': {}, 'initial': {}, 'medial': {}}
for cp in range(0xFE70, 0xFF00):
    d = unicodedata.decomposition(chr(cp))
    if not d.startswith('<') or nm(cp) is None: continue
    tag, base = d.split()[0].strip('<>'), [int(x, 16) for x in d.split()[1:]]
    if len(base) == 1 and tag in feat and nm(base[0]) and nm(base[0]) != nm(cp): feat[tag][nm(base[0])] = nm(cp)
fea = ['languagesystem DFLT dflt;', 'languagesystem arab dflt;']
for tag, ft in (('isolated', 'isol'), ('final', 'fina'), ('initial', 'init'), ('medial', 'medi')):
    if feat[tag]:
        fea.append('feature %s {' % ft); fea += ['  sub %s by %s;' % (a, b) for a, b in sorted(feat[tag].items())]; fea.append('} %s;' % ft)
# lam-alef: positional features run first, so the ligature is written on the positional glyphs
lam_i, lam_m = nm(0xFEDF), nm(0xFEE0)
pairs = [(0xFE8E, 0xFEFB, 0xFEFC), (0xFE82, 0xFEF5, 0xFEF6), (0xFE84, 0xFEF7, 0xFEF8), (0xFE88, 0xFEF9, 0xFEFA)]
lig = []
for alef_fin, iso, fin in pairs:
    if nm(alef_fin) and nm(iso) and nm(fin) and lam_i and lam_m:
        lig.append('  sub %s %s by %s;' % (lam_i, nm(alef_fin), nm(iso))); lig.append('  sub %s %s by %s;' % (lam_m, nm(alef_fin), nm(fin)))
if lig: fea += ['feature rlig {'] + lig + ['} rlig;']
addOpenTypeFeaturesFromString(f, '\n'.join(fea))
out = os.path.join(A, 'Momken_Typeface_Regular_shaped.otf'); f.save(out)
print('isol %d fina %d init %d medi %d lam-alef %d -> %s' % (len(feat['isolated']), len(feat['final']), len(feat['initial']), len(feat['medial']), len(lig) // 2, os.path.basename(out)))
