"""CODIS fonts: source TTF/OTF -> WOFF2 (all glyphs kept, name table kept = designer credit stays inside the file, as the
ALAMERAH licence requires). Output: assets/fonts/*.woff2 (embedded as base64 by tools/patch_v32.py).
  py -3 tools/build_fonts.py      (needs: pip install fonttools brotli)"""
import os
from fontTools.ttLib import TTFont
H = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(H, '..', 'assets', 'fonts')
for src, dst in (('source/ALAMERAH-Regular.ttf', 'ALAMERAH-Regular.woff2'), ('source/Momken_Typeface_Regular_shaped.otf', 'Momken-Regular.woff2')):
    f = TTFont(os.path.join(A, src)); f.flavor = 'woff2'
    out = os.path.join(A, dst); f.save(out); print(dst, os.path.getsize(out), 'bytes')
