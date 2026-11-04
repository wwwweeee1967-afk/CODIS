#!/usr/bin/env python3
"""CODIS-STICKERS-13 — رسمة «جمّار نخيل»: قلب النخلة الأبيض الصالح للأكل (لا التمر).
 صفيحة الستيكرات المرجعية (assets/sticker_sheets/sheet4.webp) تحوي بذلك الموضع وعاء تمر، والمطلوب جمّار؛ فيُرسم هنا بالكود
 بأسلوب الصفيحة نفسها (حبر داكن + ألوان غنية + تظليل ولمعة) ← assets/stickers/source/jummar_palm.svg ثم PNG شفاف (Chrome headless)
 ← tools/make_sticker_sprites.py jummar_palm يضيف حافة القص البيضاء ويكتب sprites/jummar_palm.webp. بدل الرسمة بصورة مولّدة لاحقاً:
 ضع PNG شفافاً بالاسم نفسه في assets/stickers/source/jummar_palm.png وشغّل make_sticker_sprites.py jummar_palm فقط (بلا هذا السكربت).
 الاستعمال: py -3 tools/make_jummar_sprite.py     (يحتاج Chrome مثبّتاً)"""
import os, math, subprocess, shutil, sys
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
SRC = os.path.join(root, 'assets', 'stickers', 'source'); os.makedirs(SRC, exist_ok=True)
INK = '#33241a'
S = 700


def f(v): return ('%.1f' % v).rstrip('0').rstrip('.')


def frond(x, y, ang, length, bend, n=15, wmax=21, seed=0):
    """سعفة نخيل: ضلع منحنٍ + أوراق رفيعة متدرّجة الطول على الجانبين"""
    a = math.radians(ang); b = math.radians(ang + bend)
    p0 = (x, y); p2 = (x + math.cos(a) * length * .55 + math.cos(b) * length * .45, y + math.sin(a) * length * .55 + math.sin(b) * length * .45)
    p1 = (x + math.cos(a) * length * .62, y + math.sin(a) * length * .62)
    def pt(t): return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
    def tg(t):
        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]); dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]); m = math.hypot(dx, dy); return dx / m, dy / m
    out = []
    for i in range(n):
        t = .14 + .84 * i / (n - 1); cx, cy = pt(t); tx, ty = tg(t); L = wmax * (.5 + math.sin(math.pi * (.1 + .9 * (1 - t))) * .75) * 1.7
        for side in (-1, 1):
            ang2 = math.atan2(ty, tx) + side * math.radians(58 - 20 * t)
            ex, ey = cx + math.cos(ang2) * L, cy + math.sin(ang2) * L
            nx, ny = -math.sin(ang2), math.cos(ang2); w = 4.4
            mx, my = (cx + ex) / 2, (cy + ey) / 2
            fill = ('#5fa63e', '#4a9137', '#74b84a')[(i + (side > 0) + seed) % 3]
            out.append('<path d="M%s %sQ%s %s %s %sQ%s %s %s %sZ" fill="%s" stroke="%s" stroke-width="2.6" stroke-linejoin="round"/>' % (
                f(cx), f(cy), f(mx + nx * w), f(my + ny * w), f(ex), f(ey), f(mx - nx * w * .6), f(my - ny * w * .6), f(cx), f(cy), fill, '#22361a'))
    rib = '<path d="M%s %sQ%s %s %s %s" fill="none" stroke="#2f4d22" stroke-width="7" stroke-linecap="round"/><path d="M%s %sQ%s %s %s %s" fill="none" stroke="#8cc65a" stroke-width="2.6" stroke-linecap="round"/>' % (
        f(p0[0]), f(p0[1]), f(p1[0]), f(p1[1]), f(p2[0]), f(p2[1]), f(p0[0]), f(p0[1]), f(p1[0]), f(p1[1]), f(p2[0]), f(p2[1]))
    return rib + ''.join(out)


def heart(uid, length=440, base=82, tip=15):
    """قلب نخلة: مخروط مستطيل أبيض مائل للصفرة، أغماد ملفوفة (أقواس)، ألياف طولية، قاعدة مقطوعة بحلقات، وطرف مخضرّ"""
    def h(x): return base - (base - tip) * (x / length) ** .85
    top = 'M0 %s' % f(-base) + ''.join('L%s %s' % (f(x), f(-h(x))) for x in range(10, length + 1, 10)) + 'Q%s 0 %s %s' % (f(length + 24), f(length), f(tip))
    bot = ''.join('L%s %s' % (f(x), f(h(x))) for x in range(length - 10, -1, -10))
    body = top + bot + 'Z'
    o = '<defs><linearGradient id="b%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fffbea"/><stop offset=".45" stop-color="#f6ecc6"/><stop offset="1" stop-color="#dcc88a"/></linearGradient>' % uid
    o += '<linearGradient id="t%s" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d5e28f" stop-opacity="0"/><stop offset="1" stop-color="#b7cf6a" stop-opacity=".95"/></linearGradient>' % uid
    o += '<radialGradient id="c%s"><stop offset="0" stop-color="#fff6cf"/><stop offset=".7" stop-color="#f0dd9a"/><stop offset="1" stop-color="#d9bd6c"/></radialGradient></defs>' % uid
    o += '<path d="%s" fill="url(#b%s)" stroke="%s" stroke-width="7" stroke-linejoin="round"/>' % (body, uid, INK)
    o += '<path d="M%s %s%sQ%s 0 %s %s%sZ" fill="url(#t%s)"/>' % (f(length * .62), f(-h(length * .62)), ''.join('L%s %s' % (f(x), f(-h(x))) for x in range(int(length * .62) + 10, length + 1, 10)), f(length + 24), f(length), f(tip), ''.join('L%s %s' % (f(x), f(h(x))) for x in range(length - 10, int(length * .62) - 1, -10)), uid)
    for j in range(-3, 4):   # ألياف طولية
        k = j / 3.6
        o += '<path d="M28 %s C%s %s %s %s %s %s" fill="none" stroke="#cdb77a" stroke-width="2.2" opacity=".75"/>' % (f(k * base * .86), f(length * .3), f(k * base * .8), f(length * .62), f(k * h(length * .62) * .8), f(length * .95), f(k * tip * .5))
    for x in (70, 125, 185, 250, 315, 375):   # حواف الأغماد: أقواس تنتفخ باتجاه الطرف
        hx = h(x) * .98
        o += '<path d="M%s %sQ%s 0 %s %s" fill="none" stroke="#bfa768" stroke-width="3.6" stroke-linecap="round"/>' % (f(x), f(-hx), f(x + 38 - x * .03), f(x), f(hx))
        o += '<path d="M%s %sQ%s 0 %s %s" fill="none" stroke="#fffdf0" stroke-width="2.4" stroke-linecap="round" opacity=".85" transform="translate(5 0)"/>' % (f(x), f(-hx), f(x + 38 - x * .03), f(x), f(hx))
    o += '<path d="M40 %s C150 %s 290 %s 410 %s" fill="none" stroke="#fffef6" stroke-width="9" stroke-linecap="round" opacity=".7"/>' % (f(-base * .62), f(-base * .66), f(-base * .45), f(-tip * .6))
    # القاعدة المقطوعة: بيضاوي بحلقات
    o += '<ellipse cx="0" cy="0" rx="30" ry="%s" fill="url(#c%s)" stroke="%s" stroke-width="7"/>' % (f(base), uid, INK)
    for r in (.8, .56, .32):
        o += '<ellipse cx="0" cy="0" rx="%s" ry="%s" fill="none" stroke="#c9a85a" stroke-width="3" opacity=".85"/>' % (f(30 * r), f(base * r))
    o += '<ellipse cx="0" cy="0" rx="4" ry="10" fill="#c9a85a"/>'
    o += '<path d="M-14 %s Q-22 0 -14 %s" fill="none" stroke="#fffdf0" stroke-width="3.5" stroke-linecap="round" opacity=".9"/>' % (f(-base * .5), f(base * .15))
    return o


def svg():
    s = '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (S, S, S, S)
    # سعفات خلف القلبين تنبع من جهة الطرف (الجمّار يُقطع من قمّة النخلة)
    ox, oy = 438, 268   # منبت السعفات: خلف طرفي القلبين
    s += frond(ox, oy, -122, 205, 24, 11, 30, 0) + frond(ox + 6, oy, -80, 232, -8, 12, 32, 1) + frond(ox + 10, oy + 6, -38, 205, -26, 11, 30, 2)
    s += '<g transform="translate(205 468) rotate(-55) scale(.8)">' + heart('b') + '</g>'
    s += '<g transform="translate(120 560) rotate(-36)">' + heart('a') + '</g>'
    # حبل ربط صغير حول القلبين (يُباع غالباً حزمة)
    return s + '</svg>'


def render(svg_path, png_path):
    chrome = next((c for c in (r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe', shutil.which('chrome') or '') if c and os.path.exists(c)), None)
    if not chrome: sys.exit('Chrome غير موجود — ثبّت Chrome أو ضع assets/stickers/source/jummar_palm.png يدوياً')
    html = os.path.join(SRC, '_jummar.html')
    open(html, 'w', encoding='utf-8').write('<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:transparent}svg{display:block}</style>' + open(svg_path, encoding='utf-8').read())
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--default-background-color=00000000', '--force-device-scale-factor=2',
                    '--window-size=%d,%d' % (S, S), '--screenshot=' + png_path, 'file:///' + html.replace('\\', '/')], check=True, capture_output=True, timeout=120)
    os.remove(html)


if __name__ == '__main__':
    p = os.path.join(SRC, 'jummar_palm.svg'); open(p, 'w', encoding='utf-8').write(svg())
    render(p, os.path.join(SRC, 'jummar_palm.png')); print('jummar_palm.png written')
