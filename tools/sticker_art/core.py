# -*- coding: utf-8 -*-
"""CODIS-STICKERS art engine — يرسم ستيكرات SVG (حبر + ألوان مسطحة + أضواء + حافة قص بيضاء + ظل ورقي + حبيبات) بلا أي نص.
 كل ستيكر يوفّر: shape (مسار حافة القص) · bg (خلفية المشهد) · art (الرسم داخل الشكل) · top (عناصر تخرج عن الشكل) · rot (ميل)."""
import math, random

INK = '#2b1d14'
CREAM = '#f6ecd6'

def f(v): return ('%.1f' % v).rstrip('0').rstrip('.')

# ---------- تظليل الحجم: كل لون صريح بشكل مُحبَّر يتحول تدرّجاً (ضوء أعلى-يسار → ظل أسفل-يمين) ----------
_defs, _gc = [], {}

def _rgb(c):
    c = c.lstrip('#')
    if len(c) == 3: c = ''.join(ch * 2 for ch in c)
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]

def _hex(v): return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(x)))) for x in v)

def lighten(c, k): return _hex([x + (255 - x) * k for x in _rgb(c)])

def darken(c, k): return _hex([x * (1 - k) for x in _rgb(c)])

def vol(c):
    if not (isinstance(c, str) and c.startswith('#') and len(c) in (4, 7)): return c
    if c in _gc: return _gc[c]
    gid = 'v%d' % len(_gc)
    _defs.append('<linearGradient id="%s" x1="0" y1="0" x2=".75" y2="1"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (gid, lighten(c, .28), c, darken(c, .22)))
    _gc[c] = 'url(#%s)' % gid
    return _gc[c]

def ground(cx, cy, rx, ry, o=.32):
    """ظل أرضي ناعم بلا فلتر (تدرّج شعاعي)"""
    gid = 'gr%d' % len(_defs)
    _defs.append('<radialGradient id="%s"><stop offset="0" stop-color="#140a04" stop-opacity="%s"/><stop offset="1" stop-color="#140a04" stop-opacity="0"/></radialGradient>' % (gid, o))
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="url(#%s)"/>' % (f(cx), f(cy), f(rx), f(ry), gid)

def gloss(cx, cy, rx, ry, rot=0, o=.55):
    """لمعة بيضاء ناعمة"""
    gid = 'gl%d' % len(_defs)
    _defs.append('<radialGradient id="%s"><stop offset="0" stop-color="#fff" stop-opacity="%s"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>' % (gid, o))
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="url(#%s)"%s/>' % (f(cx), f(cy), f(rx), f(ry), gid, _tf(rot, cx, cy))

def _tf(rot, cx, cy): return ' transform="rotate(%s %s %s)"' % (f(rot), f(cx), f(cy)) if rot else ''

def P(d, fill, sw=3.4, s=INK, o=None, extra=''):
    fill = vol(fill)
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s%s/>' % (d, fill, s, f(sw), (' opacity="%s"' % o) if o else '', extra)

def N(d, fill, o=None):   # بلا حبر
    return '<path d="%s" fill="%s"%s/>' % (d, fill, (' opacity="%s"' % o) if o else '')

def S(d, c, sw=3.4, o=None):   # خط فقط
    return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"%s/>' % (d, c, f(sw), (' opacity="%s"' % o) if o else '')

def C(cx, cy, r, fill, sw=3.4, s=INK, o=None):
    fill = vol(fill)
    return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s"%s/>' % (f(cx), f(cy), f(r), fill, s, f(sw), (' opacity="%s"' % o) if o else '')

def E(cx, cy, rx, ry, fill, sw=3.4, rot=0, s=INK, o=None):
    fill = vol(fill)
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="%s"%s%s/>' % (f(cx), f(cy), f(rx), f(ry), fill, s, f(sw), _tf(rot, cx, cy), (' opacity="%s"' % o) if o else '')

def R(x, y, w, h, a=0, b=0, sw=3.4, rot=0, s=INK, o=None):
    fill, r = (a, b) if isinstance(a, str) else (b, a)   # يقبل (fill, r) أو (r, fill)
    fill = vol(fill)
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s%s/>' % (f(x), f(y), f(w), f(h), f(r), fill, s, f(sw), _tf(rot, x + w / 2, y + h / 2), (' opacity="%s"' % o) if o else '')

def HL(d, o=.45, sw=4):   # لمعة
    return S(d, '#fff', sw, o)

def NE(cx, cy, rx, ry, fill, rot=0, o=None):  # قطع ناقص بلا حبر
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"%s%s/>' % (f(cx), f(cy), f(rx), f(ry), fill, _tf(rot, cx, cy), (' opacity="%s"' % o) if o else '')

def NC(cx, cy, r, fill, o=None):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"%s/>' % (f(cx), f(cy), f(r), fill, (' opacity="%s"' % o) if o else '')

def NR(x, y, w, h, a=0, b=0, rot=0, o=None):
    fill, r = (a, b) if isinstance(a, str) else (b, a)
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s%s/>' % (f(x), f(y), f(w), f(h), f(r), fill, _tf(rot, x + w / 2, y + h / 2), (' opacity="%s"' % o) if o else '')

def star(x, y, r, fill='#fff', o=None, sw=0):
    d = 'M%s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Z' % (f(x), f(y - r), f(x), f(y), f(x + r), f(y), f(x), f(y), f(x), f(y + r), f(x), f(y), f(x - r), f(y), f(x), f(y), f(x), f(y - r))
    return '<path d="%s" fill="%s"%s/>' % (d, fill, (' opacity="%s"' % o) if o else '')

def steam(x, y, h=40, c='#fff', o=.85, sw=4):
    return (S('M%s %s q-8 -%s 0 -%s t0 -%s' % (f(x), f(y), f(h / 4), f(h / 4), f(h / 4)), c, sw, o) +
            S('M%s %s q-8 -%s 0 -%s t0 -%s' % (f(x + 14), f(y + 4), f(h / 4), f(h / 4), f(h / 4)), c, sw, o))

def dots(pts, r, fill, o=None):
    return ''.join(NC(x, y, r, fill, o) for x, y in pts)

# ---------- أشكال حافة القص ----------
def circle_d(cx, cy, r):
    return 'M%s %s a%s %s 0 1 0 %s 0 a%s %s 0 1 0 -%s 0Z' % (f(cx - r), f(cy), f(r), f(r), f(2 * r), f(r), f(r), f(2 * r))

def rrect_d(x, y, w, h, r):
    return ('M%s %s h%s a%s %s 0 0 1 %s %s v%s a%s %s 0 0 1 -%s %s h-%s a%s %s 0 0 1 -%s -%s v-%s a%s %s 0 0 1 %s -%s Z' %
            (f(x + r), f(y), f(w - 2 * r), f(r), f(r), f(r), f(r), f(h - 2 * r), f(r), f(r), f(r), f(r), f(w - 2 * r), f(r), f(r), f(r), f(r), f(h - 2 * r), f(r), f(r), f(r), f(r)))

def smooth_d(pts, t=.5):
    n = len(pts); d = 'M%s %s' % (f(pts[0][0]), f(pts[0][1]))
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 3 * 2, p1[1] + (p2[1] - p0[1]) * t / 3 * 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 3 * 2, p2[1] - (p3[1] - p1[1]) * t / 3 * 2)
        d += ' C%s %s %s %s %s %s' % (f(c1[0]), f(c1[1]), f(c2[0]), f(c2[1]), f(p2[0]), f(p2[1]))
    return d + 'Z'

def poly_d(pts, r=10):
    """مضلع بزوايا مدوّرة"""
    n = len(pts); d = ''
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        def toward(a, b, dist):
            l = math.hypot(b[0] - a[0], b[1] - a[1]) or 1; k = min(dist, l / 2) / l
            return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        a = toward(p1, p0, r); b = toward(p1, p2, r)
        d += ('M' if i == 0 else 'L') + '%s %s Q%s %s %s %s ' % (f(a[0]), f(a[1]), f(p1[0]), f(p1[1]), f(b[0]), f(b[1]))
    return d + 'Z'

def scallop_d(cx, cy, r, n=12, amp=7):
    pts = []
    for i in range(n * 2):
        a = i * math.pi / n - math.pi / 2; rr = r + (amp if i % 2 == 0 else -amp * .2)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return smooth_d(pts, .45)

def blob_d(cx, cy, rx, ry, seed=1, wob=.08, n=9):
    rnd = random.Random(seed); pts = []
    for i in range(n):
        a = i * 2 * math.pi / n; k = 1 + rnd.uniform(-wob, wob)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return smooth_d(pts)

def star_d(cx, cy, r1, r2, n=8):
    pts = []
    for i in range(n * 2):
        a = i * math.pi / n - math.pi / 2; rr = r1 if i % 2 == 0 else r2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return poly_d(pts, 4)

def shield_d(cx=128, top=24, w=190, h=210):
    x0, x1 = cx - w / 2, cx + w / 2
    return 'M%s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Z' % (
        f(x0), f(top + 30), f(x0), f(top), f(x0 + 36), f(top), f(cx), f(top + 14), f(x1 - 36), f(top), f(x1), f(top), f(x1), f(top + 30),
        f(x1), f(top + h * .65), f(cx), f(top + h), f(x0), f(top + h * .65), f(x0), f(top + 30))

def arch_d(cx=128, top=22, w=170, bottom=236, r=None):
    r = r or w / 2; x0, x1 = cx - w / 2, cx + w / 2
    return 'M%s %s L%s %s A%s %s 0 0 1 %s %s L%s %s Q%s %s %s %s L%s %s Q%s %s %s %s Z' % (
        f(x0), f(top + r), f(x0), f(top + r), f(r), f(r), f(x1), f(top + r), f(x1), f(bottom - 20), f(x1), f(bottom), f(x1 - 20), f(bottom), f(x0 + 20), f(bottom), f(x0), f(bottom), f(x0), f(bottom - 20))

# ---------- مجمّع الستيكر ----------
GRAIN = ''.join('<circle cx="%d" cy="%d" r="%s" fill="#000" opacity=".05"/>' % (x, y, r) for x, y, r in
                [(5, 9, .9), (17, 40, .7), (30, 12, 1), (44, 52, .8), (11, 58, .6), (52, 20, .9), (38, 33, .6), (58, 44, 1), (24, 26, .7), (48, 6, .6), (3, 30, .8), (35, 58, .7)])

def build(shape, bg, art, top='', rot=0, rim='#d9c8a0', halftone=True, shadow=True, scale=.93):
    """shape: مسار d · bg: (لون1, لون2) أو لون · art/top: نصوص SVG"""
    if isinstance(bg, str): bg = (bg, bg)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><defs>',
           '<clipPath id="k"><path d="%s"/></clipPath>' % shape,
           '<radialGradient id="g" cx=".38" cy=".3" r=".85"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>' % (lighten(bg[0], .18), bg[0], bg[1]),
           '<pattern id="h" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(25)"><circle cx="3.5" cy="3.5" r="1.15" fill="#fff" opacity=".16"/></pattern>',
           '<pattern id="p" width="64" height="64" patternUnits="userSpaceOnUse">%s</pattern>' % GRAIN,
           ''.join(_defs),
           '</defs><g transform="translate(128 128) scale(%s) rotate(%s) translate(-128 -128)">' % (f(scale), f(rot))]
    _defs.clear(); _gc.clear()
    if shadow: out.append('<path d="%s" transform="translate(3 7)" fill="#1a1008" opacity=".28"/>' % shape)
    out.append('<path d="%s" fill="#fff" stroke="#fff" stroke-width="17" stroke-linejoin="round"/>' % shape)
    out.append('<path d="%s" fill="%s"/>' % (shape, rim))
    out.append('<g clip-path="url(#k)"><rect width="256" height="256" fill="url(#g)"/>')
    if halftone: out.append('<rect width="256" height="256" fill="url(#h)"/>')
    out.append(art)
    out.append('<rect width="256" height="256" fill="url(#p)"/>')
    out.append('<path d="%s" fill="none" stroke="#000" stroke-opacity=".14" stroke-width="7"/></g>' % shape)
    out.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" stroke-opacity=".8"/>' % (shape, rim))
    out.append(top)
    out.append('</g></svg>')
    return ''.join(out)

def G(c, rot=0, x=0, y=0, s=1):
    """مجموعة: ترجمة (x,y) ثم تدوير rot ثم تكبير s حول نقطة الأصل"""
    return '<g transform="translate(%s %s) rotate(%s) scale(%s)">%s</g>' % (f(x), f(y), f(rot), f(s), c)

def GC(c, rot=0, cx=128, cy=128, dx=0, dy=0, s=1):
    """مجموعة تدور وتتكبر حول مركزها (cx,cy) ثم تُزاح (dx,dy)"""
    return '<g transform="translate(%s %s) rotate(%s) scale(%s) translate(%s %s)">%s</g>' % (f(cx + dx), f(cy + dy), f(rot), f(s), f(-cx), f(-cy), c)


_hid = [0]

def hatch(x, y, w, h, step=10, c='#000', o=.18, sw=2):
    """خطوط قطرية مقصوصة داخل مستطيل"""
    _hid[0] += 1; cid = 'ht%d' % _hid[0]
    ls = ''.join('M%s %s l%s %s' % (f(x + i), f(y), f(h), f(h)) for i in range(-int(h), int(w), int(step)))
    return '<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s"/></clipPath><g clip-path="url(#%s)">%s</g>' % (cid, f(x), f(y), f(w), f(h), cid, S(ls, c, sw, o))
