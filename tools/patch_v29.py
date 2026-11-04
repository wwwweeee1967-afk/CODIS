#!/usr/bin/env python3
"""CODIS-STICKER-ATMOS (بعد patch_v28.py) — 3.16.0 — «جو الستيكر» على بطاقة المكافأة.
 طبقة إضافية مستقلة تظهر فقط حين يكون للبطاقة ستيكر صالح: عناصر صغيرة مرسومة من موضوع الستيكر نفسه بألوانه (مستخرجة وقت البناء)،
 بمواضع آمنة لكل قالب (لا وجه، لا لوحة اسم/سعر، لا شارة ندرة، لا الستيكر) + هالة ضوء ناعمة خلف الستيكر + عنصر «باليد» حيث توجد يد آمنة.
 - الستيكر (.rwc-stk) لا يُمسّ: نفس الوسم/الصورة/المقاس/الموضع/الميل (قواعد .rwc-stk-* كما هي).
 - المصدر الواحد: codisStickerLayerHtml نفسها (اليومي/الأسبوعي/الشهري/الأستاذ/بلا صورة) ⇒ المعاينة والنتيجة والمتجر وبحوزتك والبكج والقلب.
 - الحركة: تستقر الطبقة بعد ظهور البطاقة في نافذة النتيجة فقط (.rv.rwc-wrap.is-on)، مرة واحدة؛ بلا حركة دائمة؛ تقليل الحركة ⇒ ثابتة.
 - لا بيانات ولا تخزين: تُشتق من stickerId المحفوظ مع كل بطاقة. المحرّك: tools/atmos_engine.js · البيانات: tools/sticker_atmos.py عبر build_stickers.py.
 الاستعمال: py -3 tools/patch_v29.py app/CODIS_FINAL.html app/CODIS_FINAL.html ثم py -3 tools/build_stickers.py"""
import sys, os
src, dst = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
s = open(src, encoding='utf-8').read()
if 'CODIS-STICKER-ATMOS' in s: sys.exit('already patched (CODIS-STICKER-ATMOS)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# ---------------------------------------------------------------- CSS (بعد قواعد الستيكر؛ قواعد .rwc-stk نفسها لا تتغير)
rep(""".rwc-stk-p{ left:3%; top:2%; width:36%; }
""", """.rwc-stk-p{ left:3%; top:2%; width:36%; }
/* CODIS-STICKER-ATMOS: جو الستيكر — طبقة مستقلة تحت الستيكر (z3) وتحت نصوص البطاقة؛ لا تغيّر المقاسات ولا تلتقط اللمس */
.rwc-atm{ position:absolute; inset:0; width:100%; height:100%; display:block; pointer-events:none; -webkit-user-drag:none; user-select:none; }
.cfp > .rwc-atm{ z-index:2; }
.rwc-atm-hold{ position:absolute; aspect-ratio:1; object-fit:contain; pointer-events:none; -webkit-user-drag:none; user-select:none; transform:rotate(var(--r, 0deg)); filter:drop-shadow(0 .5cqw .6cqw rgba(0,0,0,.5)); }
.rv.rwc-wrap .rwc-atm, .rv.rwc-wrap .rwc-atm-hold{ opacity:0; }
.rv.rwc-wrap.is-on .rwc-atm{ animation:codisAtmIn 900ms cubic-bezier(.22,.8,.3,1) 420ms both; }
.rv.rwc-wrap.is-on .rwc-atm-hold{ animation:codisAtmHold 640ms cubic-bezier(.34,1.4,.5,1) 860ms both; }
@keyframes codisAtmIn{ from{ opacity:0; transform:translate3d(0,.8%,0) scale(1.02); } to{ opacity:1; transform:none; } }
@keyframes codisAtmHold{ from{ opacity:0; transform:translate3d(0,24%,0) rotate(var(--r, 0deg)) scale(.55); } to{ opacity:1; transform:rotate(var(--r, 0deg)); } }
.outcome-card.fz-calm .rwc-atm, .outcome-card.fz-calm .rwc-atm-hold{ animation:none !important; opacity:1; }
@media (prefers-reduced-motion:reduce){ .rv.rwc-wrap .rwc-atm, .rv.rwc-wrap .rwc-atm-hold{ opacity:1; animation:none !important; } }
""", 'stk css')

# ---------------------------------------------------------------- كتلة البيانات (يملؤها tools/build_stickers.py)
rep("""/* /CODIS-STICKERS-DATA */""", """/* /CODIS-STICKERS-DATA */
/* CODIS-STICKER-ATMOS-DATA */const CODIS_STICKER_ATMOS={};/* /CODIS-STICKER-ATMOS-DATA */""", 'data block')

# ---------------------------------------------------------------- المحرّك + الطبقة الموحّدة
engine = open(os.path.join(here, 'atmos_engine.js'), encoding='utf-8').read().rstrip() + '\n'
rep("""function codisStickerLayerHtml(e, fam){
  const id = codisStickerIdOk(e && e.stickerId), u = id ? CodisStickers.url(id) : '';
  return u ? '<img class="rwc-stk rwc-stk-' + fam + '" src="' + escapeHtml(u) + '" alt="" draggable="false" decoding="async" onerror="this.remove()">' : '';
}""", engine + """/* k: مفتاح القالب (ندرة اليومي/الأسبوعي/الشهري، أو اسم البطاقة الخاصة) لمواضع الجو الآمنة. وسم الستيكر نفسه كما كان حرفياً */
function codisStickerLayerHtml(e, fam, k){
  const id = codisStickerIdOk(e && e.stickerId), u = id ? CodisStickers.url(id) : '';
  return u ? CodisAtmos.html(id, fam, k) + '<img class="rwc-stk rwc-stk-' + fam + '" src="' + escapeHtml(u) + '" alt="" draggable="false" decoding="async" onerror="this.remove()">' : '';
}""", 'layer fn')

# ---------------------------------------------------------------- القالب لكل نوع بطاقة (المعامل الثالث فقط)
rep("""codisStickerLayerHtml(o, 's') +""", """codisStickerLayerHtml(o, 's', k) +""", 'special')
rep("""codisStickerLayerHtml(e, 'w') +""", """codisStickerLayerHtml(e, 'w', k) +""", 'weekly')
rep("""codisStickerLayerHtml(e, 'm') +""", """codisStickerLayerHtml(e, 'm', k) +""", 'monthly')
rep("""codisStickerLayerHtml(e, 'd') +""", """codisStickerLayerHtml(e, 'd', k) +""", 'daily')

open(dst, 'w', encoding='utf-8', newline='').write(s)
print('CODIS-STICKER-ATMOS applied ->', dst)
