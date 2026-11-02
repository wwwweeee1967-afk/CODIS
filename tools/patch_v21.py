#!/usr/bin/env python3
"""CODIS-SMOOTH (بعد patch_v20.py) — 3.12.1 — أداء فقط: لا تغيير بأي حركة/شكل/نص.
أسباب التعليك المقاسة (محاكاة آيفون 393x852 DPR3 + معالج مبطّأ ×6 عبر CDP: tools/prof/):
 1) ملاءمة خط الأسماء: 11 حلقة تصغّر الخط بخطوات 0.2–0.3 وكل خطوة تجبر إعادة تخطيط (حتى 50 مرة لكل اسم، لكل بطاقة، بعد كل رسم للمتجر)
    ⇒ codisFitShrink: نفس تسلسل الأحجام بالضبط (نفس الطرح العشري المتكرر) لكن بحث ثنائي (~6 قياسات بدل حتى 50) — النتيجة نفسها.
 2) codisFitEach كان يخلط قراءة المقاس مع الكتابة بطاقةً بطاقة ⇒ إعادة تخطيط لكل بطاقة. الآن: قراءة الكل أولاً ثم الكتابة (نفس النتائج المحفوظة).
 3) الشراء: كان المتجر يُعاد بناؤه 3 مرات (قبل الشراء — لا يُرسم أصلاً لأنه بنفس المهمة — ثم قبل أول إطار من مشهد الشراء، ثم بعد الإغلاق).
    الآن مرة واحدة بعد الإغلاق كما كان (keep/useNow يرسمان أصلاً). حالة «جارٍ الشراء…» تُكتب على زر البطاقة نفسه بنفس الصنف والنص.
 4) tok() في مشهد الشراء والمعاينة: getComputedStyle(documentElement) مع كل حركة ⇒ إعادة حساب ستايل الصفحة كلها. المتغيرات (--ease*) ثابتة في :root ⇒ تُقرأ مرة.
 5) مزامنة شريط أقسام المتجر أثناء التمرير: لا تكتب class/aria-current إلا عند التغيّر.
"""
import sys, re
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-SMOOTH' in s: sys.exit('already patched (CODIS-SMOOTH)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# 1) حلقات الملاءمة ← codisFitShrink (نفس النتيجة)
pat = re.compile(r"for\(let i = 0; i < (\d+) && size > ([\d.]+) && (.+?); i\+\+\)\{ size -= ([\d.]+); t\.style\.fontSize = size \+ 'cqw'; \}")
s, n = pat.subn(lambda m: "size = codisFitShrink(t, size, %s, %s, %s, ()=>(%s));" % (m.group(4), m.group(2), m.group(1), m.group(3)), s)
if n != 11: sys.exit('fit loops replaced: %d (expected 11)' % n)

HELP = """/* CODIS-SMOOTH: نفس حلقة التصغير القديمة (size, size-step, … حتى min أو n خطوات، يتوقف عند أول حجم لا يفيض) لكن ببحث ثنائي.
   التسلسل يُبنى بالطرح المتكرر نفسه فالأحجام مطابقة رقمياً؛ والقياس ~log2(n) بدل n (كل قياس = إعادة تخطيط) */
function codisFitShrink(t, size, step, min, n, over){
  const seq = [size]; for(let i = 0; i < n && seq[i] > min; i++) seq.push(seq[i] - step);
  const last = seq.length - 1; if(!last || !over()) return size;
  let lo = 0, hi = last;
  while(hi - lo > 1){ const mid = (lo + hi) >> 1; t.style.fontSize = seq[mid] + 'cqw'; if(over()) lo = mid; else hi = mid; }
  t.style.fontSize = seq[hi] + 'cqw'; return seq[hi];
}
const codisFitMemo = new Map();"""
rep("const codisFitMemo = new Map();", HELP, 'fit helper')

# 2) codisFitEach: قراءة كل المقاسات أولاً ثم الكتابة
rep("""  for(let i = 0; i < list.length; i++){
    const box = list[i], t = box.firstElementChild; if(!t || box.closest('.fit-wait')) continue;   /* بطاقة بعيدة عن الشاشة تنتظر دورها في codisFitLazy */
    const w = box.clientWidth, h = box.clientHeight; if(!w || !h) continue;
    const key = box.className + '|' + w + 'x' + h + '|' + fs + '|' + box.textContent;
    if(box._codisFit === key) continue;
    const ar = t.querySelector('.wkc-tier i'), m = codisFitMemo.get(key);""",
"""  const jobs = [];   /* CODIS-SMOOTH: مرحلة قراءة (إعادة تخطيط واحدة) ثم مرحلة كتابة — بدل قراءة/كتابة متناوبة لكل بطاقة */
  for(let i = 0; i < list.length; i++){
    const box = list[i], t = box.firstElementChild; if(!t || box.closest('.fit-wait')) continue;   /* بطاقة بعيدة عن الشاشة تنتظر دورها في codisFitLazy */
    const w = box.clientWidth, h = box.clientHeight; if(!w || !h) continue;
    const key = box.className + '|' + w + 'x' + h + '|' + fs + '|' + box.textContent;
    if(box._codisFit === key) continue;
    jobs.push([box, t, key]);
  }
  for(let j = 0; j < jobs.length; j++){
    const box = jobs[j][0], t = jobs[j][1], key = jobs[j][2];
    const ar = t.querySelector('.wkc-tier i'), m = codisFitMemo.get(key);""", 'fitEach two-phase')

# 3) الشراء: لا إعادة بناء قبل الشراء ولا تحت مشهد الشراء
rep("econBusyId = id; econRenderStore();", "econBusyId = id; econMarkBusy(id);", 'econBuy busy')
rep("""    econStoreBusy = false; econBusyId = null; econRenderAll();
    if(boughtId){""", """    econStoreBusy = false; econBusyId = null;
    /* CODIS-SMOOTH: مشهد الشراء مفتوح ⇒ «تخزين/استخدام» يعيدان رسم المتجر عند الإغلاق أصلاً (ووسم is-bought يضيع بذلك الرسم)؛ الرسم هنا كان يجمّد أول إطار من المشهد */
    const cineOpen = CodisBuyCine.isOpen();
    if(!cineOpen) econRenderAll();
    if(boughtId && !cineOpen){""", 'econBuy finally')
rep("async function econBuy(id){", """/* CODIS-SMOOTH: نفس ما يرسمه econStoreCardHtml لزر البطاقة المشغولة (صنف is-busy + معطّل + «جارٍ الشراء…») بلا إعادة بناء المتجر */
function econMarkBusy(id){
  try{ Array.prototype.forEach.call(document.querySelectorAll('#eco-store-body .shop-card'), c=>{ if(c.dataset.id !== id) return; const b = c.querySelector('.shop-buy'); if(!b) return;
    b.classList.add('is-busy'); b.disabled = true; b.setAttribute('aria-disabled', 'true'); b.textContent = 'جارٍ الشراء…'; }); }catch(e){}
}
async function econBuy(id){""", 'econMarkBusy')

# 4) tok() مرة واحدة لكل متغير
rep("  const tok = n=>{ try{ return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }catch(e){ return ''; } };",
    "  const tokC = {}, tok = n=>{ if(n in tokC) return tokC[n]; try{ return (tokC[n] = getComputedStyle(document.documentElement).getPropertyValue(n).trim()); }catch(e){ return ''; } };   /* CODIS-SMOOTH: --ease* ثابتة في :root */", 'tok cache', 2)

# 5) شريط الأقسام: كتابة عند التغيّر فقط
rep("""  Array.prototype.forEach.call(box.querySelectorAll('.st-nav button'), b=>{ const on = b.getAttribute('data-to') === cur; b.classList.toggle('is-on', on); if(on) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current'); });""",
    """  Array.prototype.forEach.call(box.querySelectorAll('.st-nav button'), b=>{ const on = b.getAttribute('data-to') === cur; if(b.classList.contains('is-on') === on) return; b.classList.toggle('is-on', on); if(on) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current'); });   /* CODIS-SMOOTH */""", 'nav sync')

# 6) بطاقات القلب: 3D فقط وقت الحاجة. كانت كل بطاقة (62 بالمتجر) preserve-3d + وجهان backface-hidden + rotateY ⇒ كل وجه طبقة GPU دائمة
#    (حتى الظهر المخفي) — على Safari/iOS ذاكرة طبقات ضخمة (DPR3) وتركيب ثقيل بكل إطار تمرير. الشكل الساكن مطابق: rotateY(0) = لا تحويل،
#    والظهر كان مخفياً بـ backface فصار مخفياً بـ visibility. القلب نفسه بنفس الـtransition حرفياً (is-3d يُضاف قبل الإطار الأول).
rep("""function codisFlipToggle(el){
  const on = !el.classList.contains('is-flipped');
  el.classList.toggle('is-flipped', on);""", """function codisFlipToggle(el){
  const on = !el.classList.contains('is-flipped');
  /* CODIS-SMOOTH: تفعيل 3D قبل بدء الدوران (قراءة offsetWidth تثبّت الحالة) ثم إسقاطه بعد عودة البطاقة لوجهها */
  if(!el.classList.contains('is-3d')){ el.classList.add('is-3d'); void el.offsetWidth; }
  clearTimeout(el._flat3d);
  if(!on){ const inn = el.querySelector('.cflip-in'), flat = ()=>{ clearTimeout(el._flat3d); if(inn) inn.removeEventListener('transitionend', onEnd); if(!el.classList.contains('is-flipped')) el.classList.remove('is-3d'); };
    const onEnd = e=>{ if(e.target === inn && e.propertyName === 'transform') flat(); };
    if(inn) inn.addEventListener('transitionend', onEnd); el._flat3d = setTimeout(flat, 900); }
  el.classList.toggle('is-flipped', on);""", 'flip lazy 3d')

# 7) معاينة البطاقة على iPhone (لقطتا المالك): Safari/WebKit يطبّق zoom مرتين على وحدات الحاوية (cqw) ⇒ إطار البطاقة الشهرية ونصوص
#    الأسماء/لوحة العطلة تتضاعف فتخرج البطاقة عن الشاشة ويُقص النص. zoom يبقى فقط حيث يطبَّق صحيحاً (فحص فعلي + ليس WebKit)؛
#    غيره: البطاقة تُرسم بعرضها النهائي فعلاً داخل غلاف fly (حادة، وكل ما بوحدات cqw/% يتناسب) بنفس حركة FLIP.
rep("  function open(card){\n    if(s || !card.isConnected) return;", """  /* CODIS-SMOOTH: هل zoom يطبَّق صحيحاً على وحدات الحاوية؟ (Chrome الحديث نعم؛ WebKit/iOS يضاعفها) — يُفحص مرة واحدة */
  let zoomSound;
  function codisZoomSound(){
    if(zoomSound !== undefined) return zoomSound;
    zoomSound = false;
    try{
      const ua = navigator.userAgent || '', webkit = /iP(hone|ad|od)/.test(ua) || (navigator.platform === 'MacIntel' && (navigator.maxTouchPoints || 0) > 1) || (/AppleWebKit/.test(ua) && !/(Chrome|Chromium|Edg)\\//.test(ua));
      if(!window.__codisNoZoom && !webkit && window.CSS && CSS.supports && CSS.supports('zoom', '2')){
        const o = document.createElement('div'), i = document.createElement('div');
        o.style.cssText = 'position:fixed;left:0;top:0;width:100px;height:4px;zoom:2;container-type:inline-size;visibility:hidden;pointer-events:none';
        i.style.cssText = 'width:50cqw;height:2px'; o.appendChild(i); document.body.appendChild(o);
        const wo = o.getBoundingClientRect().width, wi = i.getBoundingClientRect().width; o.remove();
        zoomSound = wo > 150 && Math.abs(wi / wo - .5) < .03;
      }
    }catch(e){ zoomSound = false; }
    return zoomSound;
  }
  function open(card){
    if(s || !card.isConnected) return;""", 'zoom probe')
rep("    const zoomOk = k > 1.02 && !!(window.CSS && CSS.supports && CSS.supports('zoom', '2'));",
    "    const zoomOk = k > 1.02 && codisZoomSound(), widthMode = k > 1.02 && !zoomOk;", 'zoomOk')
rep("    const fw = r.width * k, fh = r.height * k, fl = (vw - fw) / 2, ft = (vh - fh) / 2 - 12;",
    "    const fw = r.width * k, fl = (vw - fw) / 2; let fh = r.height * k, ft = (vh - fh) / 2 - 12;", 'peek fw')
rep("    const dx = ((r.left - o.left) + r.width / 2) - (fl + fw / 2), dy = ((r.top - o.top) + r.height / 2) - (ft + fh / 2);",
    "    const dx = ((r.left - o.left) + r.width / 2) - (fl + fw / 2); let dy = ((r.top - o.top) + r.height / 2) - (ft + fh / 2);", 'peek dxdy')
rep("    if(zoomOk){\n      fly = document.createElement('div'); fly.className = 'peek-fly';", "    if(zoomOk || widthMode){\n      fly = document.createElement('div'); fly.className = 'peek-fly';", 'peek branch')
rep("      Object.assign(card.style, { zoom:String(k), width:r.width + 'px', margin:'0' });",
    """      if(zoomOk) Object.assign(card.style, { zoom:String(k), width:r.width + 'px', margin:'0' });
      else {   /* CODIS-SMOOTH (WebKit): رسم بالعرض النهائي بلا zoom؛ الارتفاع الفعلي يُقاس ويُوسَّط */
        Object.assign(card.style, { width:fw + 'px', margin:'0' }); fly.style.transform = 'none';
        const h2 = card.getBoundingClientRect().height;
        if(h2 > 0 && h2 < r.height * (1 + (k - 1) / 2)){   /* عنصر بمقاسات ثابتة (صندوق البكج): لا يتجاوب مع العرض ⇒ تكبير بالمقياس نفسه */
          Object.assign(card.style, { width:r.width + 'px', transformOrigin:(getComputedStyle(card).direction === 'rtl' ? '100% 0' : '0 0'), transform:'scale(' + k + ')' });
        } else if(h2 > 0){ fh = h2; ft = Math.max(8, (vh - fh) / 2 - 12); fly.style.top = ft + 'px'; fly.style.height = fh + 'px'; dy = ((r.top - o.top) + r.height / 2) - (ft + fh / 2); }
      }""", 'peek width mode')
rep("['position', 'left', 'top', 'width', 'margin', 'zIndex', 'transform', 'opacity', 'zoom'].forEach(k=>{ st.card.style[k] = ''; });",
    "['position', 'left', 'top', 'width', 'margin', 'zIndex', 'transform', 'transformOrigin', 'opacity', 'zoom'].forEach(k=>{ st.card.style[k] = ''; });", 'peek cleanup')

CSS = """
/* CODIS-SMOOTH: بطاقة قلب ساكنة غير مقلوبة = مسطّحة (لا طبقات GPU)؛ is-3d أو is-flipped = نفس قواعد القلب الأصلية حرفياً */
.cflip:not(.is-3d):not(.is-flipped) .cflip-in{ transform-style:flat; }
.cflip:not(.is-3d):not(.is-flipped) .cflip-f{ transform:none; -webkit-backface-visibility:visible; backface-visibility:visible; }
.cflip:not(.is-3d):not(.is-flipped) .cflip-b{ transform:none; visibility:hidden; -webkit-backface-visibility:visible; backface-visibility:visible; }
"""
i = s.index("</style>"); s = s[:i] + CSS + s[i:]

open(dst, 'w', encoding='utf-8', newline='').write(s)
print('ok')
