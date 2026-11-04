#!/usr/bin/env python3
"""CODIS-STICKER-ATMOS — بيانات «جو الستيكر» (تُحسب مرة وقت البناء، لا تحليل صور داخل التطبيق):
 - لوحة ألوان لكل ستيكر من رسمه الحقيقي (tools/sticker_art/sprites/<id>.webp) بتكميم الألوان ثم أدوار:
   [أساسي، ثانوي، لمسة، إضاءة، ظل، توهّج]. الستيكرات المرسومة بالكود تأخذ لوحتها من stickers_meta.PAL.
 - نسخة صغيرة من الرسم (بلا خلفية الستيكر) لعنصر «في يد الشخصية» ← assets/stickers/mini/<id>.webp
 - الوصفة (العناصر/العدد/hold) من stickers_meta.ATMOS.
 يُستدعى من tools/build_stickers.py (block() يعيد كتلة البيانات المحقونة في التطبيق). يحتاج pillow numpy."""
import os, json, hashlib, colorsys
import numpy as np
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
SPR = os.path.join(here, 'sticker_art', 'sprites')
MINI = os.path.join(root, 'assets', 'stickers', 'mini')
MINI_PX = 160

def hx(c): return '#%02x%02x%02x' % tuple(int(round(max(0, min(255, v)))) for v in c)
def mix(a, b, t): return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))
def hsv(c): return colorsys.rgb_to_hsv(*(v / 255 for v in c))
def hue_d(a, b):
    d = abs(hsv(a)[0] - hsv(b)[0]); return min(d, 1 - d) * 360

def palette(path):
    from scipy import ndimage
    im = Image.open(path).convert('RGBA'); im.thumbnail((200, 200))
    A = np.asarray(im); core = ndimage.binary_erosion(A[:, :, 3] > 200, iterations=max(6, round(max(im.size) * .045)))
    a = A[core][:, :3].astype(int)            # داخل الرسم فقط: بلا إطار القص الذهبي/الأبيض الذي يطغى على العدّ
    mx, mn = a.max(1), a.min(1)
    a = a[~(mn > 228) & (mx > 34)]            # بلا حافة القص البيضاء ولا خط الحبر الأسود
    q = Image.fromarray(a.reshape(-1, 1, 3).astype(np.uint8)).quantize(16, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[:48]; cnt = np.bincount(np.asarray(q).ravel(), minlength=16)
    C = [((pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]), cnt[i] / cnt.sum()) for i in range(16) if cnt[i]]
    def score(c, w): h, s, v = hsv(c); return w * (.35 + s) * (.4 + v)
    prim = max(C, key=lambda t: score(*t) if hsv(t[0])[1] > .18 and hsv(t[0])[2] > .22 else score(*t) * .2)[0]
    rest = [t for t in C if hue_d(t[0], prim) > 28 or abs(hsv(t[0])[2] - hsv(prim)[2]) > .35]
    sec = max(rest, key=lambda t: score(*t))[0] if rest else mix(prim, (255, 255, 255), .35)
    # اللمسة: أوضح لون مشبع بعيد بالصبغة عن الأساسي والثانوي معاً (حتى لو قليل: خضرة البقدونس، ضوء السماعة البنفسجي…)
    far = lambda c: min(hue_d(c, prim), hue_d(c, sec) if hsv(sec)[1] > .2 else 360)
    acc_c = [t for t in C if far(t[0]) > 35 and hsv(t[0])[1] > .28 and hsv(t[0])[2] > .3 and t[1] > .004]
    acc = max(acc_c, key=lambda t: hsv(t[0])[1] * hsv(t[0])[2] * t[1] ** .3)[0] if acc_c else mix(prim, (255, 236, 190), .45)
    light = [t for t in C if t[1] > .02]
    hi = mix(max(light, key=lambda t: sum(t[0]))[0], (255, 250, 238), .35)
    sh = mix(prim, (20, 12, 8), .62)
    return [hx(prim), hx(sec), hx(acc), hx(hi), hx(sh)]

def glow(p):
    r, g, b = [int(p[i:i + 2], 16) / 255 for i in (1, 3, 5)]; h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return hx([x * 255 for x in colorsys.hsv_to_rgb(h, min(1, s * 1.1 + .05), min(1, v * .35 + .7))])

def mini(sid):
    p = os.path.join(SPR, sid + '.webp')
    if not os.path.exists(p): return 0
    im = Image.open(p).convert('RGBA'); im = im.crop(im.getchannel('A').getbbox()); im.thumbnail((MINI_PX, MINI_PX), Image.LANCZOS)
    os.makedirs(MINI, exist_ok=True); out = os.path.join(MINI, sid + '.webp')
    im.save(out, 'WEBP', quality=90, alpha_quality=100, method=6)
    return 'mini/%s.webp?v=%s' % (sid, hashlib.sha1(open(out, 'rb').read()).hexdigest()[:6])

def block(M, ids_with_file):
    """CODIS_STICKER_ATMOS = { id: [عناصر, [6 ألوان], ملف_اليد|0, أقصى_عدد|0] } لكل ستيكر له صورة بالمكتبة"""
    out = {}
    for s in M.S:
        sid = s[0]
        if sid not in ids_with_file or sid not in M.ATMOS: continue
        motifs, _, opt = M.ATMOS[sid].partition('|'); opt = opt.split()
        if sid in M.PAL: pal = list(M.PAL[sid])
        else:
            sp = os.path.join(SPR, sid + '.webp')
            pal = palette(sp) if os.path.exists(sp) else ['#c9a46a', '#8a5a3a', '#6f9a5a', '#f6ead2', '#3a2516']
        for i, c in (getattr(M, 'PAL_FIX', {}).get(sid) or {}).items(): pal[i] = c   # تصحيح دور واحد (مثل لمسة خضراء لا تظهر بالعدّ)
        pal.append(glow(pal[0]))
        n = next((int(o[1:]) for o in opt if o[:1] == 'n' and o[1:].isdigit()), 0)
        out[sid] = [motifs.split(), pal, (mini(sid) if 'hold' in opt else 0), n]
    return '/* CODIS-STICKER-ATMOS-DATA */const CODIS_STICKER_ATMOS=%s;/* /CODIS-STICKER-ATMOS-DATA */' % json.dumps(out, separators=(',', ':'))

if __name__ == '__main__':   # مراجعة: لوحة ألوان كل ستيكر بجانب رسمه
    import sys; sys.path.insert(0, here); import stickers_meta as M
    from PIL import ImageDraw
    rows = [s[0] for s in M.S]; C = 64
    sh = Image.new('RGB', (C * 10, len(rows) // 2 * C + C), (40, 42, 48)); d = ImageDraw.Draw(sh)
    for j, sid in enumerate(rows):
        x, y = (j % 2) * C * 5, (j // 2) * C
        sp = os.path.join(SPR, sid + '.webp')
        if os.path.exists(sp):
            im = Image.open(sp).convert('RGBA'); im.thumbnail((C - 4, C - 4)); sh.paste(im, (x + 2, y + 2), im)
        pal = list(M.PAL[sid]) if sid in M.PAL else (palette(sp) if os.path.exists(sp) else [])
        if pal: pal.append(glow(pal[0]))
        for i, c in enumerate(pal): d.rectangle([x + C + i * 30, y + 8, x + C + i * 30 + 26, y + 40], fill=c)
        d.text((x + C, y + 44), sid, fill=(230, 230, 230))
    sh.save(sys.argv[1] if len(sys.argv) > 1 else 'atmos_palettes.png')
