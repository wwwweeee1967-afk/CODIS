#!/usr/bin/env python3
"""CODIS-STICKERS-SHEET3: يفصل صفيحة الستيكرات الجديدة (assets/stickers/source/new_stickers_sheet.png — خلفية سوداء معتمة)
 إلى ملفات PNG مستقلة بشفافية حقيقية ← assets/stickers/source/extracted/<id>.png
 - الخلفية = البكسلات الداكنة المتصلة بحواف الصفيحة فقط (Flood Fill من الحواف) — الأسود داخل الرسومات يبقى كما هو.
 - حافة ناعمة: شريط ±2px حول الحد يُفكّ مزجه مع الأسود (alpha = سطوع البكسل / سطوع أقرب بكسل داخلي، واللون = اللون/alpha)
   فلا تظهر هالة سوداء ولا حافة خشنة.
 - كل ستيكر = مكوّناته المتصلة (بعضها مجموعة: نوتات الموسيقى، حروف zzz، المشط...) بحجمه الأصلي بلا تكبير + هامش شفاف.
 الاستعمال: py -3 tools/extract_sheet3.py [--review out.png]   (يحتاج pillow numpy scipy)
 بعدها: py -3 tools/make_sticker_sprites.py <ids> ثم py -3 tools/make_stickers.py <ids> ثم py -3 tools/build_stickers.py"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
SRC = os.path.join(root, 'assets', 'stickers', 'source', 'new_stickers_sheet.png')
OUT = os.path.join(root, 'assets', 'stickers', 'source', 'extracted')
T = 35       # أقصى قناة لبكسل يُعدّ خلفية سوداء (إذا اتصل بالحافة)
PAD = 12     # هامش شفاف حول كل ستيكر

# معرّف الستيكر بالمكتبة : صندوق تقريبي (x0, y0, x1, y1) بإحداثيات الصفيحة 1536×1024 بترتيب القراءة.
# يُؤخذ كل مكوّن يقع ≥55% منه داخل الصندوق (فالأسياخ المتداخلة لا تختلط).
BOX = {
    # الصف 1
    'falafel': (8, 8, 198, 196), 'fried_chicken': (200, 8, 378, 194), 'noodles': (384, 8, 572, 194),
    'dolma': (548, 26, 754, 182), 'sambusa': (752, 16, 966, 190), 'tikka': (942, 6, 1160, 178),
    'kebab': (1117, 8, 1357, 196), 'masgouf': (1311, 28, 1536, 180),
    # الصف 2
    'biryani': (5, 188, 233, 340), 'tashreeb': (231, 196, 410, 342), 'kubba': (407, 194, 621, 339),
    'kunafa': (618, 189, 813, 343), 'baklava': (809, 190, 996, 343), 'cheesecake': (993, 169, 1156, 345),
    'waffle': (1154, 190, 1353, 343), 'pancakes': (1350, 188, 1532, 341),
    # الصف 3
    'croissant': (12, 352, 207, 509), 'choco_cake': (211, 338, 381, 504), 'tea_glass': (381, 342, 529, 511),
    'espresso': (527, 354, 712, 510), 'park_picnic': (714, 338, 935, 511), 'mall_bag': (935, 337, 1156, 510),
    'dinner_out': (1154, 344, 1338, 519), 'armchair': (1352, 349, 1531, 519),
    # الصف 4
    'nap': (5, 518, 202, 676), 'cat_nap': (200, 500, 410, 670), 'bath': (408, 509, 617, 676),
    'sleep_in': (630, 508, 760, 674), 'candle_spa': (779, 519, 940, 671), 'domino': (953, 520, 1102, 663),
    'board_game': (1099, 516, 1334, 681), 'backgammon': (1331, 520, 1534, 674),
    # الصف 5
    'handheld': (12, 677, 196, 837), 'puzzle': (214, 680, 362, 833), 'headset': (362, 674, 513, 830),
    'movie_night': (520, 671, 688, 834), 'music': (688, 680, 820, 828), 'anime': (818, 671, 970, 845),
    'paint': (972, 657, 1130, 835), 'oud': (1124, 671, 1310, 855), 'pottery': (1275, 697, 1380, 844),
    'wrapped_gift': (1385, 680, 1524, 836),
    # الصف 6
    'shoes': (6, 834, 213, 1002), 'wristwatch': (216, 836, 325, 1008), 'perfume': (342, 837, 447, 1008),
    'hair_care': (474, 834, 632, 1016), 'skincare': (636, 838, 707, 1008), 'friends_cups': (705, 848, 926, 1016),
    'phone_call': (925, 849, 1047, 1012), 'lunch': (1044, 861, 1214, 1001), 'camping': (1208, 839, 1376, 1009),
    'landmark': (1371, 844, 1533, 1014),
}


def alpha_sheet():
    """الصفيحة كاملة RGBA: خلفية الحواف شفافة، وحافة ناعمة مفكوكة المزج. تُعيد (RGBA, fg mask)"""
    A = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64)
    mx = A.max(2)
    lab, _ = ndimage.label(mx < T)
    edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]); edge = edge[edge > 0]
    fg = ~np.isin(lab, edge)
    d_in = ndimage.distance_transform_edt(fg); d_out = ndimage.distance_transform_edt(~fg)
    band = (fg & (d_in <= 2)) | (~fg & (d_out <= 2))
    interior = fg & ~band
    _, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)
    ref = np.maximum(mx[iy, ix], 1.0)
    a = np.where(interior, 1.0, 0.0)
    a = np.where(band, np.clip(mx / ref, 0, 1), a)
    a[a < .05] = 0
    rgb = np.where(band[..., None] & (a[..., None] > 0), np.clip(A / np.maximum(a, 1e-3)[..., None], 0, 255), A)
    out = np.dstack([rgb, a * 255]).round().astype(np.uint8)
    return out, fg


def extract(sid, rgba, lab, cnt):
    x0, y0, x1, y1 = BOX[sid]
    sub = lab[y0:y1, x0:x1]; ids, inside = np.unique(sub[sub > 0], return_counts=True)
    keep = [i for i, c in zip(ids, inside) if c / cnt[i] >= .55 and cnt[i] >= 40]
    assert keep, 'nothing to extract for ' + sid
    m = ndimage.binary_dilation(np.isin(lab, keep), iterations=3) & (rgba[:, :, 3] > 0)
    # لا نأخذ بكسلات ستيكر مجاور حتى داخل التوسعة
    other = (lab > 0) & ~np.isin(lab, keep)
    m &= ~ndimage.binary_dilation(other, iterations=1) | np.isin(lab, keep)
    ys, xs = np.where(m)
    crop = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    crop[:, :, 3] = np.where(m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], crop[:, :, 3], 0)
    h, w = crop.shape[:2]
    canvas = np.zeros((h + 2 * PAD, w + 2 * PAD, 4), np.uint8); canvas[PAD:PAD + h, PAD:PAD + w] = crop
    return Image.fromarray(canvas), len(keep)


def main():
    args = sys.argv[1:]; review = None
    if '--review' in args: i = args.index('--review'); review = args[i + 1]; del args[i:i + 2]
    rgba, fg = alpha_sheet()
    lab, _ = ndimage.label(fg, structure=np.ones((3, 3)))
    cnt = np.bincount(lab.ravel())
    os.makedirs(OUT, exist_ok=True)
    made = []; used = {}
    for sid in (args or list(BOX)):
        im, n = extract(sid, rgba, lab, cnt)
        im.save(os.path.join(OUT, sid + '.png'), optimize=True)
        made.append((sid, im)); print('%-14s %3dx%-3d parts=%d' % (sid, im.width, im.height, n))
    # كل مكوّن كبير يجب أن ينتمي لستيكر واحد بالضبط
    if not args:
        for sid in BOX:
            x0, y0, x1, y1 = BOX[sid]; sub = lab[y0:y1, x0:x1]; ids, c = np.unique(sub[sub > 0], return_counts=True)
            for i, k in zip(ids, c):
                if k / cnt[i] >= .55 and cnt[i] >= 40: used.setdefault(i, []).append(sid)
        dup = {i: v for i, v in used.items() if len(v) > 1}
        miss = [i for i in range(1, len(cnt)) if cnt[i] >= 40 and i not in used]
        print('components dup:', dup, ' unassigned:', [(i, cnt[i]) for i in miss])
    if review:
        C, cols = 200, 10; rows = (len(made) + cols - 1) // cols
        sh = Image.new('RGB', (cols * C, rows * (C + 14)), (70, 118, 160)); d = ImageDraw.Draw(sh)
        for j, (s, im) in enumerate(made):
            im = im.copy(); im.thumbnail((C - 8, C - 8), Image.LANCZOS); x, y = j % cols * C, j // cols * (C + 14)
            if j % 2: d.rectangle([x, y, x + C - 1, y + C - 1], fill=(236, 236, 236))
            sh.paste(im, (x + (C - im.width) // 2, y + (C - im.height) // 2), im); d.text((x + 4, y + C), s, fill=(255, 255, 255))
        sh.save(review)


if __name__ == '__main__':
    main()
