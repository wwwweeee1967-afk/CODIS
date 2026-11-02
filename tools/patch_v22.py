#!/usr/bin/env python3
"""CODIS-SMOOTH2 (بعد patch_v21.py) — 3.12.2 — أداء/ذاكرة فقط، بلا أي تغيير مرئي (تحقق بكسلي).
 1) طبقة أشعة مشهد الشراء: نفس الأشعة بنفس المسافات المطلقة على طبقة أصغر (140vmax بدل 190vmax) ⇒ ذاكرة GPU أقل بالنصف تقريباً.
 2) CodisCardAmb: الخلفية المحيطة (صورة 48x60 مشتقة من صورة البطاقة) كانت تُحسب بكل جلسة بـ drawImage = فك ترميز متزامن لكل صورة كبيرة
    عند أول فتح للمتجر. الناتج ثابت لكل صورة ⇒ يُحفظ دائمياً (localStorage، مفتاح من نص الصورة نفسها) ويُعاد استعماله كما هو حرفياً.
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-SMOOTH2' in s: sys.exit('already patched (CODIS-SMOOTH2)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

rep("im.loading = 'lazy'; im.src = blobUrl(n, u); }", "im.loading = 'lazy'; im._codisAk = u.length + ':' + u.slice(-64); im.src = blobUrl(n, u); }", 'hydrate key')
rep("""  function paint(frame, img){
    const src = img.getAttribute('src') || ''; if(!src) return;
    let v = cache.get(src);
    if(v === undefined){ try{ v = make(img); }catch(e){ v = ''; } if(v) cache.set(src, v); }""", """  /* CODIS-SMOOTH2: نتيجة make ثابتة لكل صورة ⇒ تُحفظ دائمياً بمفتاح من نص الصورة (طول + آخر 64 حرفاً) فلا يتكرر فك ترميز الصور الكبيرة بكل جلسة */
  const PK = 'codis_amb_v1'; let disk = null;
  const diskGet = k=>{ if(!disk){ try{ disk = JSON.parse(localStorage.getItem(PK) || '{}') || {}; }catch(e){ disk = {}; } } return disk[k]; };
  const diskSet = (k, v)=>{ diskGet(k); disk[k] = v; const ks = Object.keys(disk); if(ks.length > 120) delete disk[ks[0]]; try{ localStorage.setItem(PK, JSON.stringify(disk)); }catch(e){} };
  function paint(frame, img){
    const src = img.getAttribute('src') || ''; if(!src) return;
    const key = img._codisAk || '';
    let v = cache.get(src);
    if(v === undefined && key){ const d = diskGet(key); if(d){ v = d; cache.set(src, v); } }
    if(v === undefined){ try{ v = make(img); }catch(e){ v = ''; } if(v){ cache.set(src, v); if(key) diskSet(key, v); } }""", 'amb disk cache')
CSS = """
/* CODIS-SMOOTH2: طبقة أشعة مشهد الشراء 190vmax (≈1619px، ~94MB على iPhone DPR3) كانت شفافة تماماً بعد نصف قطر 69.86vmax (52% من نصف قطر الزاوية).
   نفس الأشعة بنفس المسافات المطلقة على طبقة 140vmax: قناع closest-side (70vmax) بنقاط 42.224% / 99.803% = 29.557vmax / 69.862vmax كما كانت ⇒ الشكل نفسه بنصف الذاكرة تقريباً */
.bcx-rays{ width:140vmax; height:140vmax; margin:-70vmax 0 0 -70vmax;
  -webkit-mask:radial-gradient(circle closest-side, #000 0, rgba(0,0,0,.6) 42.224%, transparent 99.803%); mask:radial-gradient(circle closest-side, #000 0, rgba(0,0,0,.6) 42.224%, transparent 99.803%); }
"""
i = s.index("</style>"); s = s[:i] + CSS + s[i:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('ok')
