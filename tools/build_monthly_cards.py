#!/usr/bin/env python3
"""CODIS-MONTHLY-CARDS-V2: يفصل الكروت الشهرية الخمسة من الصورة المركبة assets/monthly_source/monthly_cards_new.webp
 (خمسة كروت + خلفية داكنة) إلى أصول شفافة مستقلة، ويوحّد مساحتها، ويحسب لوحتَي الاسم والمعلومات آلياً من الرسم نفسه،
 ثم يحقن الناتج في app/CODIS_FINAL.html مكان CODIS_MONTHLY_ART / CODIS_MONTHLY_SLOTS (الآلية القديمة نفسها: WebP مدفون Base64).
 الاستعمال: py -3 tools/build_monthly_cards.py [ملف_التطبيق] [--preview مجلد]    (يحتاج pillow numpy scipy)
 المفتاح ← موضع التصميم بالصورة المركبة: C أخضر (أعلى يسار) · B أزرق (أعلى وسط) · A بنفسجي (أعلى يمين) · S ذهبي (أسفل يسار) · SS أحمر (أسفل يمين)
 الخطوات: (1) الخلفية = بكسلات داكنة متصلة بالحافة ⇒ كل كرت مكوّن واحد · (2) حافة ناعمة بلا هالة (لون الحافة من أقرب بكسل داخلي)
 · (3) قص على الحد الدقيق ثم وضع الكرت بلا تمديد ولا قص داخل لوحة موحّدة 4:5 · (4) كشف اللوحتين (ورق فاتح محاط بإطار) وحساب المستطيل الآمن للنص."""
import sys, os, re, io, json, base64
import numpy as np
from PIL import Image
from scipy import ndimage
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
SRC = os.path.join(root, 'assets', 'monthly_source', 'monthly_cards_new.webp')
KEYS = ['C', 'B', 'A', 'S', 'SS']       # ترتيب القراءة: الصف العلوي يسار→يمين ثم السفلي
T = 70                                   # أقصى قناة لبكسل يُعدّ خلفية داكنة
CANVAS_H = 564                           # ارتفاع اللوحة الموحّدة؛ العرض = 4:5 (نسبة إطار البطاقة الموحّد بالتطبيق)
CANVAS_W = round(CANVAS_H * .8)


def split_cards(rgb):
    mx = rgb.max(2)
    lab, n = ndimage.label(mx > T)
    cnt = np.bincount(lab.ravel()); cnt[0] = 0
    ids = [i for i in np.argsort(cnt)[::-1][:5]]
    assert len(ids) == 5 and all(cnt[i] > 60000 for i in ids), 'expected 5 cards'
    cards = []
    for i in ids:
        m = ndimage.binary_fill_holes(lab == i)
        ys, xs = np.where(m); cards.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1, m))
    top = sorted([c for c in cards if c[1] < rgb.shape[0] / 3], key=lambda c: c[0])
    bot = sorted([c for c in cards if c[1] >= rgb.shape[0] / 3], key=lambda c: c[0])
    assert len(top) == 3 and len(bot) == 2, 'layout is not 3+2'
    return top + bot


def cut(rgb, c):
    x0, y0, x1, y1, m = c
    # حافة: نواة صلبة (تآكل 2px) ← لون الحافة من أقرب بكسل داخل النواة فلا تظهر هالة الخلفية الداكنة؛ ألفا ناعمة 1px
    core = ndimage.binary_erosion(m, iterations=2)
    _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
    col = rgb[iy, ix]
    a = ndimage.gaussian_filter(ndimage.binary_erosion(m, iterations=1).astype(np.float64), .7)
    a = np.where(ndimage.binary_dilation(m, iterations=1), a, 0)
    out = np.dstack([np.where(core[..., None], rgb, col), a * 255]).clip(0, 255).round().astype(np.uint8)
    return Image.fromarray(out[y0:y1, x0:x1])


def to_canvas(im):
    """بلا تمديد ولا قص: تكبير/تصغير منتظم ليلائم اللوحة الموحّدة ثم وسطها (الفائض شفاف)"""
    k = min(CANVAS_W / im.width, CANVAS_H / im.height)
    w, h = round(im.width * k), round(im.height * k)
    r = im.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')
    can = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ox, oy = (CANVAS_W - w) // 2, (CANVAS_H - h) // 2
    can.alpha_composite(r, (ox, oy))
    return can, (ox, oy, w, h)


def best_rect(M, y_lo, y_hi, hmin):
    """أعرض مستطيل (بارتفاع ≥ hmin) كل بكسلاته ورق حرّ داخل الصفوف [y_lo, y_hi): يتجنب ذروة الميدالية وزخارف اللوحة تلقائياً"""
    best = None
    for y0 in range(y_lo, y_hi - hmin + 1):
        col = np.ones(M.shape[1], bool)
        for y1 in range(y0 + 1, y_hi + 1):
            col &= M[y1 - 1]
            if y1 - y0 < hmin: continue
            d = np.diff(np.r_[0, col.view(np.int8), 0]); st, en = np.where(d == 1)[0], np.where(d == -1)[0]
            if not len(st): break
            k = int(np.argmax(en - st)); w = int(en[k] - st[k]); sc = w * (y1 - y0) ** .35
            if best is None or sc > best[0]: best = (sc, [int(st[k]), y0, int(en[k]), y1])
    return best and best[1]


def find_plates(can):
    """اللوحتان = مقطعان أفقيّان من «ورق فاتح دافئ» يشغلان معظم عرض الكرت داخل ثلثه السفلي (الإطار الورقي الخارجي والخطوط الذهبية رفيعة فلا تبلغ هذه النسبة).
    الارتفاع من مسقط الصفوف؛ ثم داخل كل لوحة أعرض مستطيل ورقي خالٍ تماماً (ذروة الميدالية المركزية تشقّ أعلى اللوحة العليا فلا يدخلها النص).
    تُعاد مستطيلات [x0, y0, x1, y1] بالبكسل: الأعلى = اسم المكافأة · الأسفل = معلومات البطاقة."""
    A = np.asarray(can).astype(float); rgb = A[:, :, :3]; al = A[:, :, 3] > 200
    H, W = al.shape
    mx, mn = rgb.max(2), rgb.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    paper = al & (mx > 90) & (sat > .10) & (sat < .62) & (rgb[:, :, 0] >= rgb[:, :, 2] + 15)
    paper = ndimage.binary_opening(paper, iterations=1)
    xa, xb = int(W * .14), int(W * .86)
    f = paper[:, xa:xb].mean(1)
    rows = [y for y in range(int(H * .62), int(H * .97)) if f[y] > .40]
    groups, cur = [], [rows[0]]
    for y in rows[1:]:
        if y - cur[-1] <= 3: cur.append(y)
        else: groups.append(cur); cur = [y]
    groups.append(cur)
    groups = sorted([g for g in groups if len(g) > 25], key=len, reverse=True)[:2]
    assert len(groups) == 2, 'plates not found (%d)' % len(groups)
    groups.sort(key=lambda g: g[0])
    clean = ndimage.binary_erosion(ndimage.binary_closing(paper, structure=np.ones((3, 3))), iterations=1)   # سدّ شقوق نسيج الورق (≤2px) ثم هامش 1px عن خط الزخرفة
    rects = []
    for idx, g in enumerate(groups):
        y0, y1 = g[0], g[-1] + 1; h = y1 - y0
        ya, yb = int(y0 + h * .10), int(y1 - h * .10)          # الارتفاع من اللوحة نفسها (متقارب بين الكروت الخمسة ⇒ حجم نص متساوٍ)
        ok = clean[ya:yb].mean(0) >= .88                        # عمود «ورق حرّ» إن كان ≥88% من صفوفه كذلك
        d = np.diff(np.r_[0, ok.astype(np.int8), 0]); st, en = np.where(d == 1)[0], np.where(d == -1)[0]
        runs = [(int(a), int(b)) for a, b in zip(st, en) if b - a >= 40]
        assert runs, 'no free columns in plate %d' % idx
        if idx == 0:   # اللوحة العليا مشقوقة بذروة الميدالية: الاسم في الفص الأيمن (جهة بدء القراءة بالعربية)، وإلا الأعرض
            right = [r for r in runs if r[0] > W * .45]; runs = right or runs
        a, b = max(runs, key=lambda r: r[1] - r[0])
        rects.append([a, ya, b, yb])
    return rects


def build(preview=None):
    rgb = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64)
    cards = split_cards(rgb)
    made = []
    for key, c in zip(KEYS, cards):
        im = cut(rgb, c); can, box = to_canvas(im); made.append((key, c, can, box, find_plates(can)))
    # القالب واحد لكل الكروت ⇒ نطاق أفقي مشترك للّوحة (تقاطع الخمسة) فيتساوى عرض النص وحجمه؛ الارتفاع يبقى من كل كرت
    for idx in (0, 1):
        xa = max(m[4][idx][0] for m in made); xb = min(m[4][idx][2] for m in made)
        for m in made: m[4][idx][0], m[4][idx][2] = xa, xb
    art, slots, info = {}, {}, {}
    for key, c, can, box, rects in made:
        # هامش أمان داخل اللوحة ثم نسب مئوية من اللوحة الموحّدة
        def pct(r, mx=.02):
            x0, y0, x1, y1 = r; dx = (x1 - x0) * mx
            return [round((x0 + dx) / CANVAS_W * 100, 2), round(y0 / CANVAS_H * 100, 2), round((x1 - x0 - 2 * dx) / CANVAS_W * 100, 2), round((y1 - y0) / CANVAS_H * 100, 2)]
        slots[key] = {'ar': round(CANVAS_W / CANVAS_H, 4), 'w': CANVAS_W, 'h': CANVAS_H, 'name': pct(rects[0]), 'info': pct(rects[1])}
        buf = io.BytesIO(); can.save(buf, 'WEBP', quality=90, alpha_quality=100, method=6)
        art[key] = 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()
        info[key] = dict(src_bbox=[int(c[0]), int(c[1]), int(c[2]), int(c[3])], src_size=[int(c[2] - c[0]), int(c[3] - c[1])], placed=box, bytes=len(buf.getvalue()), plates=rects)
        if preview:
            from PIL import ImageDraw
            os.makedirs(preview, exist_ok=True); can.save(os.path.join(preview, 'monthly_%s.png' % key))
            bg = Image.new('RGBA', can.size, (70, 150, 220, 255)); bg.alpha_composite(can); d = ImageDraw.Draw(bg)
            for nm, col in (('name', (255, 0, 255, 255)), ('info', (0, 255, 255, 255))):
                l, t, w, h = slots[key][nm]; d.rectangle([l / 100 * CANVAS_W, t / 100 * CANVAS_H, (l + w) / 100 * CANVAS_W, (t + h) / 100 * CANVAS_H], outline=col, width=2)
            bg.convert('RGB').save(os.path.join(preview, 'check_%s.png' % key))
    return art, slots, info


def inject(target, art, slots):
    html = open(target, encoding='utf-8').read()
    pa = re.compile(r'const CODIS_MONTHLY_ART = \{.*?\};'); ps = re.compile(r'const CODIS_MONTHLY_SLOTS = \{.*?\};')
    assert len(pa.findall(html)) == 1 and len(ps.findall(html)) == 1, 'monthly blocks not unique in ' + target
    html = pa.sub(lambda _m: 'const CODIS_MONTHLY_ART = ' + json.dumps(art, separators=(', ', ': ')) + ';', html, count=1)
    html = ps.sub(lambda _m: 'const CODIS_MONTHLY_SLOTS = ' + json.dumps(slots) + ';', html, count=1)
    open(target, 'w', encoding='utf-8', newline='').write(html)


if __name__ == '__main__':
    args = sys.argv[1:]; prev = None
    if '--preview' in args: i = args.index('--preview'); prev = args[i + 1]; del args[i:i + 2]
    art, slots, info = build(prev)
    for k in KEYS: print(k, json.dumps(info[k]))
    if args and args[0] != '--dry':
        inject(args[0], art, slots); print('injected into', args[0])
