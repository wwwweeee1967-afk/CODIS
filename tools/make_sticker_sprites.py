#!/usr/bin/env python3
"""CODIS-STICKERS-PHOTO: يقص رسومات الستيكرات من صفائح المستخدم الشفافة (assets/sticker_sheets/sheet1|2.webp)
 ويكبّرها بعناية (ألفا مضروبة مسبقاً + حدّة خفيفة) ويضيف حافة قص بيضاء بخط حبر خافت مثل بقية المكتبة
 ← tools/sticker_art/sprites/<id>.webp. بعدها: py -3 tools/make_stickers.py <ids> ثم py -3 tools/build_stickers.py
 الاستعمال: py -3 tools/make_sticker_sprites.py [ids...] [--sheet review.png]   (يحتاج pillow numpy scipy)"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
SHEETS = {1: os.path.join(root, 'assets', 'sticker_sheets', 'sheet1.webp'), 2: os.path.join(root, 'assets', 'sticker_sheets', 'sheet2.webp')}
OUT = os.path.join(here, 'sticker_art', 'sprites')
LONG = 300      # الضلع الأطول للرسمة بعد التكبير (px)
RIM = 9         # سمك حافة القص البيضاء (px)

# id: (الصفيحة, x0, y0, x1, y1) بإحداثيات الصفيحة الأصلية 1125×750 — يُؤخذ من الصندوق ما يقع أغلبه داخله فقط
BOX = {
    # بدل رسمة ستيكر موجود
    'shawarma': (1, 709, 135, 817, 232), 'burger': (2, 12, 10, 166, 150), 'pizza': (2, 321, 15, 479, 155),
    'fries': (2, 186, 7, 308, 156), 'donut': (2, 999, 42, 1122, 151), 'ice_cream': (1, 726, 2, 817, 133),
    'orange_juice': (1, 123, 119, 216, 246), 'milkshake': (1, 235, 108, 316, 246), 'cinema': (2, 486, 6, 623, 161),
    'gamepad': (2, 10, 322, 173, 428), 'handheld': (2, 198, 304, 310, 432), 'camera': (2, 735, 432, 873, 539),
    'tv_show': (1, 8, 678, 108, 750), 'trophy': (2, 757, 161, 894, 299), 'treasure': (2, 10, 151, 177, 314),
    'wrapped_gift': (2, 183, 160, 322, 300), 'backpack': (1, 612, 531, 721, 626), 'new_book': (2, 883, 430, 1004, 540),
    # ستيكرات جديدة
    'hot_dog': (1, 334, 123, 468, 235), 'taco': (1, 567, 133, 708, 235), 'sandwich': (1, 819, 142, 940, 232),
    'soda': (2, 641, 7, 738, 159), 'coffee_togo': (2, 771, 16, 878, 158), 'cupcake': (1, 629, 2, 718, 118),
    'cake_slice': (1, 507, 3, 611, 109), 'cookie': (1, 137, 246, 249, 333), 'macaron': (1, 260, 249, 359, 325),
    'chocolate_bar': (1, 7, 241, 130, 348), 'football': (2, 339, 305, 462, 426), 'basketball': (2, 475, 304, 596, 425),
    'billiards': (1, 816, 339, 912, 434), 'darts': (1, 920, 333, 1034, 434), 'theater': (2, 972, 638, 1124, 741),
    'sports_car': (2, 870, 326, 1016, 421), 'diamond': (2, 847, 541, 971, 637), 'rose': (2, 22, 539, 140, 641),
    'medal': (2, 910, 162, 997, 307), 'crown': (2, 624, 161, 757, 296), 'compass': (2, 10, 421, 118, 542),
}

# CODIS-STICKERS-SHEET3: رسومات الصفيحة الجديدة (assets/stickers/source/new_stickers_sheet.png) تُفصل أولاً بـ tools/extract_sheet3.py
# إلى PNG شفاف (assets/stickers/source/extracted/<id>.png). لها حافة قص مرسومة أصلاً ⇒ لا تكبير ولا حافة بيضاء إضافية.
# تتقدّم على BOX أعلاه (handheld كان من الصفيحة 2 وصار من الصفيحة الجديدة).
EXTRACTED = os.path.join(root, 'assets', 'stickers', 'source', 'extracted')
sys.path.insert(0, here)
from extract_sheet3 import BOX as BOX3

def sprite3(sid):
    im = Image.open(os.path.join(EXTRACTED, sid + '.png')).convert('RGBA')
    im = im.crop(im.getchannel('A').getbbox())
    canvas = Image.new('RGBA', (im.width + 4, im.height + 4), (0, 0, 0, 0)); canvas.paste(im, (2, 2))
    canvas.save(os.path.join(OUT, sid + '.webp'), 'WEBP', quality=94, alpha_quality=100, method=6)
    return canvas

_cache = {}
def sheet(n):
    if n not in _cache:
        A = np.asarray(Image.open(SHEETS[n]).convert('RGBA')).copy()
        lab, _ = ndimage.label(ndimage.binary_erosion(A[:, :, 3] > 200, iterations=1))   # النواة الصلبة تفصل العناصر المتلامسة بالحواف الناعمة
        _cache[n] = (A, lab, np.bincount(lab.ravel()))
    return _cache[n]

def crop(sid):
    n, x0, y0, x1, y1 = BOX[sid]; A, lab, cnt = sheet(n)
    sub = lab[y0:y1, x0:x1]; ids, inside = np.unique(sub[sub > 0], return_counts=True)
    keep = [i for i, c in zip(ids, inside) if c / cnt[i] > .55 and c > 20]
    assert keep, 'nothing to crop for ' + sid
    m = ndimage.binary_dilation(np.isin(lab, keep), iterations=4) & (A[:, :, 3] > 0)
    ys, xs = np.where(m)
    out = A[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    out[:, :, 3] = np.where(m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], out[:, :, 3], 0)
    return Image.fromarray(out)

def sprite(sid):
    if sid in BOX3: return sprite3(sid)
    im = crop(sid); k = LONG / max(im.size)
    im = im.convert('RGBa').resize((round(im.width * k), round(im.height * k)), Image.LANCZOS).convert('RGBA')
    a = im.getchannel('A'); im = im.convert('RGB').filter(ImageFilter.UnsharpMask(1.4, 60, 2)).convert('RGBA'); im.putalpha(a)
    pad = RIM + 4; W, H = im.width + 2 * pad, im.height + 2 * pad
    obj = Image.new('RGBA', (W, H), (0, 0, 0, 0)); obj.paste(im, (pad, pad))
    dist = ndimage.distance_transform_edt(np.asarray(obj.getchannel('A')) < 128)
    rim = np.clip(RIM + .5 - dist, 0, 1); ink = np.clip(RIM + 2 - dist, 0, 1) - rim
    canvas = Image.new('RGBA', (W, H), (43, 29, 20, 0))
    canvas.putalpha(Image.fromarray((ink * 70).astype(np.uint8)))
    white = Image.new('RGBA', (W, H), (255, 255, 255, 0)); white.putalpha(Image.fromarray((rim * 255).astype(np.uint8)))
    canvas.alpha_composite(white); canvas.alpha_composite(obj)
    canvas.save(os.path.join(OUT, sid + '.webp'), 'WEBP', quality=92, alpha_quality=100, method=6)
    return canvas

if __name__ == '__main__':
    args = sys.argv[1:]; review = None
    if '--sheet' in args: i = args.index('--sheet'); review = args[i + 1]; del args[i:i + 2]
    ids = args or list(dict.fromkeys(list(BOX) + list(BOX3))); os.makedirs(OUT, exist_ok=True)
    made = [(s, sprite(s)) for s in ids]
    print('sprites:', len(made))
    if review:
        C, cols = 220, 8; rows = (len(made) + cols - 1) // cols
        sh = Image.new('RGB', (cols * C, rows * (C + 16)), (64, 68, 76)); d = ImageDraw.Draw(sh)
        for j, (s, im) in enumerate(made):
            im = im.copy(); im.thumbnail((C - 10, C - 10), Image.LANCZOS); x, y = j % cols * C, j // cols * (C + 16)
            sh.paste(im, (x + (C - im.width) // 2, y + (C - im.height) // 2), im); d.text((x + 6, y + C), s, fill=(240, 240, 240))
        sh.save(review)
