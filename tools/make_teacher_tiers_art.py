"""CODIS-TEACHER-TIERS (3.29.0): يولّد ثلاث نسخ لونية (برونزية/فضية/ذهبية) من صورة بطاقة الأستاذ الأصلية داخل app/CODIS_FINAL.html (قبل v42)
   py -3 tools/make_teacher_tiers_art.py <نسخة قبل v42> <مجلد الإخراج>   → bronze.webp / silver.webp / gold.webp (800×1000)
   التلوين على مستوى الدرجات اللونية فقط (HSV): الشكل والنص والحواف كما هي بكسلاً ببكسل، ولا أصول خارجية."""
import sys, re, base64, io
import numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
i = s.index('const CODIS_SPECIAL_CARD_ART = {'); j = s.index('\n', i)
m = re.search(r'"teacher": "data:image/webp;base64,([A-Za-z0-9+/=]+)"', s[i:j])
im = Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert('RGBA')
a = np.array(im).astype(np.float32) / 255.0
rgb, alpha = a[..., :3], a[..., 3]
hsv = np.array(Image.fromarray((rgb * 255).astype(np.uint8)).convert('HSV')).astype(np.float32) / 255.0
H, S, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
red = ((H < 22) | (H > 335)) & (S > .35)            # حقل البطاقة القرمزي
navy = (H > 180) & (H < 270) & (S > .25)             # دائرة الشعار الكحلية
def to_img(h, s_, v_):
    hh = (np.clip(h, 0, 360) / 360 * 255).astype(np.uint8)
    o = Image.fromarray(np.stack([hh, (np.clip(s_, 0, 1) * 255).astype(np.uint8), (np.clip(v_, 0, 1) * 255).astype(np.uint8)], -1), 'HSV').convert('RGB')
    return np.array(o).astype(np.float32) / 255.0
def finish(rgb2, name):
    o = np.dstack([np.clip(rgb2, 0, 1), alpha])
    Image.fromarray((o * 255).astype(np.uint8), 'RGBA').save(out + '/' + name + '.webp', 'WEBP', quality=84, method=6)
# برونزية: الحقل نحاسي/بني محمرّ، الباقي دافئ
h, s_, v_ = H.copy(), S.copy(), V.copy()
h[red] = 22; s_[red] = S[red] * .78; v_[red] = V[red] * .98 + .02
h[navy] = 28; s_[navy] = S[navy] * .55; v_[navy] = V[navy] * .85
finish(to_img(h, s_, v_), 'bronze')
# فضية: كل الألوان تُحوَّل لرمادي فولاذي بارد مع تباين أعلى
g = (rgb[..., 0] * .3 + rgb[..., 1] * .59 + rgb[..., 2] * .11)
g = np.clip((g - .5) * 1.18 + .56, 0, 1)
sil = np.dstack([g * .93, g * .97, g * 1.02])
finish(sil, 'silver')
# ذهبية: الحقل ذهبي غني، الدائرة بنية داكنة، ولمعة أعلى
h, s_, v_ = H.copy(), S.copy(), V.copy()
h[red] = 37; s_[red] = np.clip(S[red] * .55 + .38, 0, 1); v_[red] = np.clip(V[red] * 1.1 + .52, 0, 1)
# ألوان الذهب الأصلية (الأصفر) تزداد إشراقاً ليبقى الشعار أبرز من الإطار
gold_ink = (H > 25) & (H < 60) & (S > .3) & ~red
v_[gold_ink] = np.clip(V[gold_ink] * 1.12 + .04, 0, 1); s_[gold_ink] = np.clip(S[gold_ink] * 1.05, 0, 1)
h[navy] = 30; s_[navy] = S[navy] * .6; v_[navy] = V[navy] * .75
finish(to_img(h, s_, v_), 'gold')
im.convert('RGB').resize((400, 500)).save(out + '/_orig.png')
for n in ('bronze', 'silver', 'gold'):
    Image.open(out + '/' + n + '.webp').convert('RGB').resize((400, 500)).save(out + '/_' + n + '.png')
print('ok')
