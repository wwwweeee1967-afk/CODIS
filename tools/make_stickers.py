#!/usr/bin/env python3
"""يولّد ملفات الستيكرات SVG من tools/sticker_art/art_*.py إلى assets/stickers/ ويكتب ورقة مراجعة اختيارية.
 py -3 tools/make_stickers.py [--sheet out.html] [ids...]   (بعدها py -3 tools/build_stickers.py لتحديث بيانات المكتبة)"""
import sys, os, re, importlib
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here); sys.path.insert(0, root)
mods = sorted(fn[:-3] for fn in os.listdir(os.path.join(here, 'sticker_art')) if fn.startswith('art_') and fn.endswith('.py'))
ART = {}
for m in mods:
    try: ART.update(importlib.import_module('tools.sticker_art.' + m).ART)
    except ModuleNotFoundError as e:
        if m not in str(e): raise
args = sys.argv[1:]; sheet = None
if '--sheet' in args:
    i = args.index('--sheet'); sheet = args[i + 1]; del args[i:i + 2]
ids = args or list(ART)
out = os.path.join(root, 'assets', 'stickers'); os.makedirs(out, exist_ok=True)
for i in ids:
    svg = ART[i]()
    assert '<text' not in svg and 'font-' not in svg, i + ' has text'
    open(os.path.join(out, i + '.svg'), 'w', encoding='utf-8').write(svg)
print('wrote', len(ids), 'stickers;', len(ART), 'defined')
if sheet:
    cells = ''.join('<figure><img src="assets/stickers/%s.svg"><figcaption>%s</figcaption></figure>' % (i, i) for i in ids)
    open(sheet, 'w', encoding='utf-8').write('<!doctype html><meta charset=utf-8><body style="margin:0;background:#2a2d33;display:grid;grid-template-columns:repeat(var(--c,5),1fr);gap:6px;padding:6px"><style>figure{margin:0;text-align:center;color:#ccc;font:11px sans-serif}img{width:100%}</style>' + cells +
        '<script>const q=new URLSearchParams(location.search),a=+q.get("a")||0,b=+q.get("b")||999,ids=(q.get("ids")||"").split(",").filter(Boolean);document.body.style.setProperty("--c",q.get("c")||5);[...document.querySelectorAll("figure")].forEach((f,i)=>{const id=f.textContent.trim();f.style.display=(ids.length?ids.includes(id):(i>=a&&i<b))?"":"none"});</script>')
