# -*- coding: utf-8 -*-
"""CODIS-STICKERS-PHOTO: رسومات حقيقية (sprites/<id>.webp من tools/make_sticker_sprites.py) داخل هوية المكتبة نفسها.
 REPLACE: يُبقي خلفية الستيكر القديم كما هي (شكل القص · لون الورق · الحافة · الحبيبات · الظل · الميل) ويبدّل الرسم وحده.
 NEW: ستيكرات جديدة بنفس المجمّع (build) وأشكال/ألوان مختارة لتباين الرسمة. يُحمَّل آخراً (z) فيتقدّم على art_v2."""
import os, base64, importlib
from . import core
from .core import *

SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sprites')
BOX = 158   # أكبر ضلع للرسمة (مع حافتها) داخل لوح 256

def _sprite(sid, dx=0, dy=0, box=BOX):
    from PIL import Image
    p = os.path.join(SPR, sid + '.webp'); raw = open(p, 'rb').read(); w, h = Image.open(p).size
    k = box / max(w, h); W, H = w * k, h * k; x, y = 128 - W / 2 + dx, 128 - H / 2 + dy
    shade = ground(128 + dx, y + H - 4, W * .42, 10, .30)
    img = '<image href="data:image/webp;base64,%s" x="%s" y="%s" width="%s" height="%s"/>' % (base64.b64encode(raw).decode(), f(x), f(y), f(W), f(H))
    return shade, img

def _old_backing(sid):
    """يشغّل رسم الستيكر القديم مع build معترَض ليلتقط الخلفية فقط (بلا الرسم)"""
    here = os.path.dirname(os.path.abspath(__file__)); owner = None
    for m in sorted(fn[:-3] for fn in os.listdir(here) if fn.startswith('art_') and fn.endswith('.py') and fn != 'art_z_photo.py'):
        mod = importlib.import_module('tools.sticker_art.' + m)
        if sid in mod.ART: owner = mod
    cap = {}
    def grab(shape, bg, art='', top='', rot=0, **kw): cap.update(shape=shape, bg=bg, rot=rot, kw=kw); return ''
    real = owner.build; owner.build = grab
    try: owner.ART[sid]()
    finally: owner.build = real; core._defs.clear(); core._gc.clear()
    return cap

SPARK = (star(206, 50, 9) + star(46, 204, 8), star(50, 56, 9) + star(208, 206, 8))

# id: (dx, dy, box) — ضبط بصري لكل رسمة داخل خلفيتها القديمة
REPLACE = {
    'shawarma': (0, 2, 186), 'burger': (0, 0, 179), 'pizza': (0, 2, 184), 'fries': (0, 2, 184), 'donut': (0, 2, 181),
    'ice_cream': (0, 0, 190), 'orange_juice': (0, 0, 186), 'milkshake': (0, 0, 189), 'cinema': (0, 0, 184),
    'gamepad': (0, 2, 186), 'handheld': (0, 0, 184), 'camera': (0, 2, 186), 'tv_show': (0, 2, 186), 'trophy': (0, 0, 177),
    'treasure': (0, 2, 184), 'wrapped_gift': (0, 0, 175), 'backpack': (0, 2, 181), 'new_book': (0, 2, 179),
}

# CODIS-STICKERS-SHEET3: رسومات الصفيحة الجديدة (sprites من tools/extract_sheet3.py) — نفس المعرّف والخلفية القديمة، الرسم فقط يتبدّل.
# handheld كان مستبدلاً من الصفيحة 2 ← الآن من الصفيحة الجديدة (نفس خلفيته الأصلية).
REPLACE.update({
    'falafel': (0, 2, 186), 'fried_chicken': (0, 2, 186), 'noodles': (0, 2, 186), 'dolma': (0, 2, 186), 'sambusa': (0, 2, 186),
    'kebab': (0, 2, 186), 'masgouf': (0, 2, 186), 'biryani': (0, 2, 186), 'tashreeb': (0, 2, 186), 'kubba': (0, 2, 186),
    'kunafa': (0, 2, 186), 'baklava': (0, 2, 186), 'cheesecake': (0, 2, 186), 'waffle': (0, 2, 186), 'croissant': (0, 2, 186),
    'choco_cake': (0, 2, 186), 'tea_glass': (0, 2, 186), 'espresso': (0, 2, 186), 'park_picnic': (0, 2, 186), 'mall_bag': (0, 2, 186),
    'dinner_out': (0, 2, 186), 'armchair': (0, 2, 186), 'nap': (0, 2, 186), 'bath': (0, 2, 186), 'sleep_in': (0, 2, 186),
    'candle_spa': (0, 2, 186), 'board_game': (0, 2, 186), 'handheld': (0, 2, 186), 'puzzle': (0, 2, 186), 'headset': (0, 2, 186),
    'movie_night': (0, 2, 186), 'anime': (0, 2, 186), 'paint': (0, 2, 186), 'oud': (0, 2, 186), 'pottery': (0, 2, 186),
    'wrapped_gift': (0, 2, 186), 'shoes': (0, 2, 186), 'wristwatch': (0, 2, 186), 'perfume': (0, 2, 186), 'hair_care': (0, 2, 186),
    'skincare': (0, 2, 186), 'friends_cups': (0, 2, 186), 'phone_call': (0, 2, 186), 'camping': (0, 2, 186), 'landmark': (0, 2, 186),
})

# id: (shape, (فاتح, غامق), ميل, box, شرارات)
NEW = {
    'hot_dog':       (scallop_d(128, 128, 104, 14, 6), ('#c4ece6', '#4fb0a4'), -4, 188, 0),
    'taco':          (blob_d(128, 128, 104, 100, 4, .05), ('#d2efb2', '#72b84e'), 5, 188, 1),
    'sandwich':      (rrect_d(26, 26, 204, 204, 62), ('#ffd8c4', '#ea8a66'), -5, 186, 0),
    'soda':          (circle_d(128, 128, 104), ('#cfe8ff', '#5f9fe0'), 5, 184, 1),
    'coffee_togo':   (arch_d(128, 18, 196, 240), ('#dcefd6', '#86b882'), -4, 184, 0),
    'cupcake':       (star_d(128, 128, 112, 98, 12), ('#fff0bc', '#f2b24c'), 5, 168, 1),
    'cake_slice':    (scallop_d(128, 128, 104, 12, 7), ('#d4ecff', '#7fb4e4'), -5, 175, 0),
    'cookie':        (circle_d(128, 128, 104), ('#d2e6ff', '#719fe0'), 4, 177, 1),
    'macaron':       (blob_d(128, 128, 104, 100, 8, .05), ('#d6f3e0', '#78c696'), -6, 175, 0),
    'chocolate_bar': (rrect_d(26, 26, 204, 204, 66), ('#ffe0ea', '#ec92b2'), 5, 179, 1),
    'football':      (circle_d(128, 128, 104), ('#c4ecc4', '#46a65a'), -4, 170, 0),
    'basketball':    (arch_d(128, 18, 196, 240), ('#d2e0ff', '#678ddc'), 5, 170, 1),
    'billiards':     (rrect_d(26, 26, 204, 204, 62), ('#86d6a8', '#26845a'), -5, 166, 0),
    'darts':         (star_d(128, 128, 112, 98, 12), ('#ffe9a6', '#f0aa44'), 4, 168, 1),
    'theater':       (shield_d(128, 20, 204, 218), ('#e8d6ff', '#9472d4'), -4, 181, 0),
    'sports_car':    (rrect_d(22, 40, 212, 176, 64), ('#d8ecff', '#6fa6e8'), 5, 190, 1),
    'diamond':       (star_d(128, 128, 112, 98, 10), ('#eadcff', '#a17fe2'), -5, 168, 0),
    'rose':          (blob_d(128, 128, 104, 100, 2, .05), ('#fff0d6', '#f2c27a'), 5, 175, 1),
    'medal':         (shield_d(128, 20, 204, 218), ('#d2e4ff', '#5888d6'), 4, 189, 0),
    'crown':         (scallop_d(128, 128, 104, 12, 6), ('#eadaff', '#8866cc'), -4, 175, 1),
    'compass':       (circle_d(128, 128, 104), ('#d6efe8', '#72b8a6'), 5, 170, 0),
    # CODIS-STICKERS-SHEET3: ستيكرات جديدة من الصفيحة الجديدة
    'tikka':         (rrect_d(26, 26, 204, 204, 62), ('#ffe0c2', '#e88a4a'), 4, 188, 1),
    'pancakes':      (scallop_d(128, 128, 104, 12, 7), ('#fff0c8', '#ecb45a'), -5, 184, 0),
    'cat_nap':       (blob_d(128, 128, 104, 100, 6, .05), ('#dce0ff', '#7f86d8'), 4, 188, 1),
    'domino':        (circle_d(128, 128, 104), ('#d4efd8', '#5fae74'), -4, 176, 0),
    'backgammon':    (rrect_d(22, 40, 212, 176, 64), ('#ffe4cc', '#d98d52'), 5, 190, 1),
    'music':         (star_d(128, 128, 112, 98, 12), ('#e6dcff', '#9a7ee0'), -5, 172, 0),
    'lunch':         (circle_d(128, 128, 104), ('#fff2cc', '#e8b048'), 4, 184, 1),
    # CODIS-STICKERS-13: 13 ستيكراً جديداً (الصفيحة 4 + جمّار مرسوم)
    'social_media':       (circle_d(128, 128, 104), ('#ffd9ec', '#e66aa8'), -4, 186, 1),
    'cigarettes':         (rrect_d(26, 26, 204, 204, 62), ('#ffd7d0', '#e07a6a'), 5, 184, 0),
    'jummar_palm':        (blob_d(128, 128, 104, 100, 4, .05), ('#e9f3c8', '#9cc454'), -4, 200, 1),
    'lettuce_head':       (scallop_d(128, 128, 104, 12, 6), ('#d4f2c4', '#62b84a'), 4, 186, 0),
    'iraqi_samoon':       (arch_d(128, 18, 196, 240), ('#ffe8c2', '#e0a24e'), -5, 186, 1),
    'pickles':            (shield_d(128, 20, 204, 218), ('#e2f2c0', '#86b23c'), 5, 188, 0),
    'mushrooms':          (circle_d(128, 128, 104), ('#f1e4d6', '#c29a78'), -4, 186, 1),
    'shish_shawarma':     (star_d(128, 128, 112, 98, 12), ('#ffd9b0', '#e8803c'), 4, 178, 0),
    'chicken_tikka_rice': (rrect_d(22, 40, 212, 176, 64), ('#fff0c0', '#e8b040'), -4, 190, 1),
    'italian_saj':        (scallop_d(128, 128, 104, 12, 7), ('#ffd6c8', '#e66a4a'), 5, 188, 0),
    'fishing_trip':       (blob_d(128, 128, 104, 100, 6, .05), ('#c8e8ff', '#4f9ed8'), -5, 188, 1),
    'cafe_front':         (arch_d(128, 18, 196, 240), ('#e6d6c4', '#a67c52'), 4, 188, 0),
    'lamb_mandi':         (rrect_d(22, 40, 212, 176, 64), ('#ffe4b8', '#d9903a'), -4, 192, 1),
}

def _replace(sid):
    dx, dy, box = REPLACE[sid]; b = _old_backing(sid); shade, img = _sprite(sid, dx, dy, box)
    return build(b['shape'], b['bg'], shade, img + SPARK[len(sid) % 2], b['rot'], **b['kw'])

def _new(sid):
    shape, bg, rot, box, sp = NEW[sid]; shade, img = _sprite(sid, 0, 2, box)
    return build(shape, bg, shade, img + SPARK[sp], rot)

ART = {}
for _s in REPLACE: ART[_s] = (lambda s: lambda: _replace(s))(_s)
for _s in NEW: ART[_s] = (lambda s: lambda: _new(s))(_s)
