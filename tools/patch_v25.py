#!/usr/bin/env python3
"""CODIS-BUTTER (بعد patch_v24.py المطبَّق على ناتج patch_v22 — الصور مدفونة، ملف واحد) — 3.14.0
أسباب التعليك على التطبيق المثبّت (standalone) والحل الجذري، بلا أي تغيير بالشكل أو الحركات:
 1) التمرير كان ينتظر الجافاسكربت بكل لمسة: مستمعا touchmove غير passive على document (سحب الرجوع — فعّال فقط بالتطبيق المثبّت لأن
    nativeSwipe=false — وسحب ترتيب المهام). الآن كلاهما passive، ومنع التمرير أثناء السحب الفعلي يتم بقفل overflow للإطار المتمرّر
    مؤقتاً (codisScrollLock) ثم إرجاعه ⇒ التمرير بكل الشاشات لا يمر على الجافاسكربت أبداً.
 2) المتجر كان يُهدم ويُبنى (≈5700 عنصر) بكل فتح حتى لو لم يتغير شيء. الآن: إن لم يُحفظ أي تغيير منذ آخر بناء ولا تغيّر اليوم/حالة الواجهة،
    يُعرض المتجر الجاهز وتُعاد حركة الدخول نفسها (is-enter). أي تغيير ⇒ يُبنى كما كان.
 3) ملاءمة خط الأسماء: نتائجها (codisFitMemo) تُحفظ بالجهاز ⇒ الجلسات القادمة بلا أي قياس.
 4) صور المتجر: نسخة مصغّرة مدفونة (≤420px، حجم العرض الفعلي ×3) بدل فك صورة 800×1000 لخانة 115px ⇒ ذاكرة الصور المفكوكة ~51MB → ~11MB.
    المعاينة بالضغط المطوّل تبدّل للأصلية (بعد فك ترميزها) وتعيد المصغّرة عند الإغلاق. مشهد الشراء/التفاصيل/×10 على الأصلية كما هي.
Usage: py -3 tools/patch_v25.py <in.html> <out.html>
"""
import sys, re, io, base64
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-BUTTER' in s: sys.exit('already patched (CODIS-BUTTER)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# ---------------------------------------------------------------- 1) التمرير لا ينتظر الجافاسكربت
HELP = """/* CODIS-BUTTER: قفل تمرير مؤقت لإطار واحد أثناء سحب فعلي (بديل preventDefault على touchmove غير passive الذي كان يجعل كل تمرير ينتظر الجافاسكربت) */
function codisScrollLock(el, on){
  if(!el || !el.style) return;
  if(on){ if(el._codisLock) return; el._codisLock = [el.style.overflowY]; el.style.overflowY = 'hidden'; }
  else if(el._codisLock){ el.style.overflowY = el._codisLock[0]; el._codisLock = null; }
}
function codisScrollerOf(n){
  n = n && n.nodeType === 1 ? n : n && n.parentElement;
  while(n && n !== document.body && n !== document.documentElement){ const cs = getComputedStyle(n); if(/(auto|scroll)/.test(cs.overflowY) && n.scrollHeight > n.clientHeight + 1) return n; n = n.parentElement; }
  return document.scrollingElement || document.documentElement;
}
const CodisTaskDrag = (function(){"""
rep("const CodisTaskDrag = (function(){", HELP, 'helpers')
rep("  document.addEventListener('touchmove', e=>{ if(d && e.cancelable) e.preventDefault(); }, { passive:false });\n", "", 'drag touchmove')
rep("sc:sc, st0:sc.scrollTop, slot:rects[from].height + gap, raf:0 };",
    "sc:sc, st0:sc.scrollTop, slot:rects[from].height + gap, raf:0 }; codisScrollLock(sc, true);", 'drag lock')
rep("const st = d; d = null; if(st.raf) cancelAnimationFrame(st.raf);",
    "const st = d; d = null; if(st.raf) cancelAnimationFrame(st.raf); codisScrollLock(st.sc, false);", 'drag unlock', 2)

rep("""    const s0 = g; g = null; if(!s0) return;
    const el = s0.el; busyDrag = false;""", """    const s0 = g; g = null; if(!s0) return;
    if(s0.sc) codisScrollLock(s0.sc, false);
    const el = s0.el; busyDrag = false;""", 'swipe settle unlock')
rep("if(g.dx > 12 && g.dx > g.dy * 1.2){ g.active = true; busyDrag = true;",
    "if(g.dx > 12 && g.dx > g.dy * 1.2){ g.active = true; busyDrag = true; g.sc = codisScrollerOf(e.target); codisScrollLock(g.sc, true);", 'swipe lock')
rep("""      if(g.active){
        if(e.cancelable) e.preventDefault();
""", """      if(g.active){
""", 'swipe no preventDefault')
rep("""    }, { passive:false });
    document.addEventListener('touchend', ()=>{ if(!g) return; if(!g.active){ g = null; return; } const done = true; if(!g.el){ const ok = g.dx >= MIN; g = null;""",
    """    }, { passive:true });   /* CODIS-BUTTER: passive — التمرير لا ينتظر الجافاسكربت */
    document.addEventListener('touchend', ()=>{ if(!g) return; if(!g.active){ g = null; return; } const done = true; if(!g.el){ const ok = g.dx >= MIN; if(g.sc) codisScrollLock(g.sc, false); g = null;""", 'swipe passive')

# ---------------------------------------------------------------- 2) المتجر الجاهز
rep("function saveData(){\n  if(codisSaveSuspended) return codisSaveSuspended !== 'fail';",
    "function saveData(){\n  if(codisSaveSuspended) return codisSaveSuspended !== 'fail';\n  window.__codisSaveN = (window.__codisSaveN || 0) + 1;   /* CODIS-BUTTER: عدّاد تغييرات البيانات (يُبطل المتجر الجاهز) */", 'save counter')
rep("function econOpenStore(){ econStoreEnterAt = Date.now(); econOpenLayer('eco-store', econRenderStore); }",
    """/* CODIS-BUTTER: بصمة كل ما يقرأه رسم المتجر: أي حفظ بيانات، اليوم (وكل 10 دقائق)، حالة الواجهة، الرصيد، صلاحية المطوّر */
function econStoreSig(){
  let adm = false; try{ adm = CodisAccount.isAdmin(); }catch(e){}
  return [window.__codisSaveN || 0, new Date().toDateString(), Math.floor(Date.now() / 600000), econClosedOpen, econClosedView, econSelMode, Object.keys(econSelSet || {}).length,
    econOwnOpen, econBusyId, econStoreBusy, econSellBusy, econSilverBusy, data.wallet.balance, adm, innerWidth].join('|');
}
function econStoreReopen(){
  const box = document.getElementById('eco-store-body');
  if(box && box.firstElementChild && box._codisSig && box._codisSig === econStoreSig()){
    box.classList.remove('is-enter'); void box.offsetWidth; box.classList.toggle('is-enter', !econCalm());   /* نفس حركة الدخول */
    try{ econVaultSync(); econStoreNavSync(); }catch(e){}
    return;
  }
  econRenderStore();
}
function econOpenStore(){ econStoreEnterAt = Date.now(); econOpenLayer('eco-store', econStoreReopen); }""", 'store reopen')
rep("  codisFitLazy(box); codisWatchRewardCards(box);\n  econVaultSync(); econStoreNavBind(); econStoreNavSync();",
    "  codisFitLazy(box); codisWatchRewardCards(box);\n  econVaultSync(); econStoreNavBind(); econStoreNavSync();\n  box._codisSig = econStoreSig();", 'store sig')

# ---------------------------------------------------------------- 3) ملاءمة الأسماء محفوظة بالجهاز
rep("const codisFitMemo = new Map();", """const codisFitMemo = new Map();
/* CODIS-BUTTER: نتائج الملاءمة نفسها تُحفظ بالجهاز (المفتاح: الصنف + المقاس بالبكسل + حالة الخطوط + النص) ⇒ لا قياس بالجلسات القادمة */
const CODIS_FIT_KEY = 'codis_fit_v1';
try{ const a = JSON.parse(localStorage.getItem(CODIS_FIT_KEY) || '[]'); if(Array.isArray(a)) a.forEach(e=>{ if(Array.isArray(e) && e.length === 2) codisFitMemo.set(e[0], e[1]); }); }catch(e){}
let codisFitSaveT = 0;
function codisFitPersist(){ if(codisFitSaveT) return; codisFitSaveT = setTimeout(()=>{ codisFitSaveT = 0; try{ localStorage.setItem(CODIS_FIT_KEY, JSON.stringify(Array.from(codisFitMemo.entries()).slice(-700))); }catch(e){} }, 2500); }""", 'fit persist')
rep("codisFitMemo.set(key, [t.style.cssText, ar ? ar.style.display : '']); }",
    "codisFitMemo.set(key, [t.style.cssText, ar ? ar.style.display : '']); codisFitPersist(); }", 'fit persist call')
rep("if(codisFitMemo.size > 600) codisFitMemo.clear();", "if(codisFitMemo.size > 900) codisFitMemo.clear();", 'fit cap')

# ---------------------------------------------------------------- 4) صور المتجر المصغّرة (مدفونة بالملف)
TW = 400
thumbs = {}
def key_of(u): return str(len(u)) + ':' + u[-64:]
for m in re.finditer(r'data:image/(webp|png|jpeg);base64,([A-Za-z0-9+/]{2048,}={0,2})', s):
    u = m.group(0); k = key_of(u)
    if k in thumbs: continue
    im = Image.open(io.BytesIO(base64.b64decode(m.group(2))))
    if im.width <= TW + 40: continue
    h = round(im.height * TW / im.width)
    t = im.convert('RGBA').resize((TW, h), Image.LANCZOS)
    b = io.BytesIO(); t.save(b, "WEBP", quality=80, method=6)
    thumbs[k] = 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
if len(thumbs) < 10: sys.exit('thumbs: %d' % len(thumbs))
import json
TH = '/* CODIS-BUTTER: نسخ مصغّرة لصور المتجر (≤%dpx ≈ أعرض خانة ×3)، مفتاحها طول الصورة الأصلية + آخر 64 حرفاً */\nconst CODIS_ART_THUMBS = %s;\n' % (TW, json.dumps(thumbs, separators=(',', ':')))
rep("const CodisArt = (function(){", TH + "const CodisArt = (function(){", 'thumbs table')
rep("  let depth = 0;\n  function src(u){", "  let depth = 0, thumbsOn = false;\n  const thumbKey = u=>u.length + ':' + u.slice(-64);\n  function src(u){", 'art state')
rep("""  const blobs = [];
  function blobUrl(i, u){
    if(blobs[i]) return blobs[i];""", """  const blobs = [], tblobs = [];
  function blobUrl(i, u, th){
    const cache = th ? tblobs : blobs;
    if(cache[i]) return cache[i];""", 'blob cache split')
rep("      return (blobs[i] = URL.createObjectURL(new Blob([arr], { type:u.slice(5, semi) })));",
    "      return (cache[i] = URL.createObjectURL(new Blob([arr], { type:u.slice(5, semi) })));", 'blob cache store')
rep("im.loading = 'lazy'; im._codisAk = u.length + ':' + u.slice(-64); im.src = blobUrl(n, u); }",
    "im.loading = 'lazy'; im._codisAk = u.length + ':' + u.slice(-64); const th = thumbsOn ? CODIS_ART_THUMBS[thumbKey(u)] : null; if(th){ im._codisFull = n; im.src = blobUrl(n, th, true); } else im.src = blobUrl(n, u); }", 'hydrate thumb')
rep("  function set(el, fn){ depth++; let h; try{ h = fn(); } finally { depth--; } el.innerHTML = h; hydrate(el); }",
    """  function set(el, fn, o){ depth++; let h; try{ h = fn(); } finally { depth--; } el.innerHTML = h; thumbsOn = !!(o && o.thumbs); try{ hydrate(el); } finally { thumbsOn = false; } }
  /* المعاينة: الأصلية بعد فك ترميزها (لا وميض)، ثم المصغّرة عند الإغلاق (تحرير الذاكرة) */
  function full(root){
    if(!root || !root.querySelectorAll) return;
    Array.prototype.forEach.call(root.querySelectorAll('img'), im=>{ const n = im._codisFull; if(n === undefined || !list[n]) return; const u = blobUrl(n, list[n]);
      if(im.src === u) return; const pre = new Image(); pre.src = u; const go = ()=>{ if(im.isConnected && im._codisFull === n) im.src = u; }; (pre.decode ? pre.decode() : Promise.resolve()).then(go, go); });
  }
  function thumb(root){
    if(!root || !root.querySelectorAll) return;
    Array.prototype.forEach.call(root.querySelectorAll('img'), im=>{ const n = im._codisFull; if(n === undefined || !list[n]) return; const th = CODIS_ART_THUMBS[thumbKey(list[n])]; if(th) im.src = blobUrl(n, th, true); });
  }""", 'art set/full/thumb')
rep("  return { src:src, hydrate:hydrate, set:set, html:html };", "  return { src:src, hydrate:hydrate, set:set, html:html, full:full, thumb:thumb };", 'art api')
rep("    econStoreNavHtml() + (econClosedOpen ? econClosedPanelHtml() : '') + econBoxesHtml() + econCosmeticsShopHtml() + econShopHtml() + econOwnSheetHtml());",
    "    econStoreNavHtml() + (econClosedOpen ? econClosedPanelHtml() : '') + econBoxesHtml() + econCosmeticsShopHtml() + econShopHtml() + econOwnSheetHtml(), { thumbs:true });", 'store thumbs on')
# المعاينة: الأصلية عند الفتح والمصغّرة بعد الإغلاق
rep("    card.classList.add('is-peek');\n", "    card.classList.add('is-peek'); CodisArt.full(card);   /* CODIS-BUTTER */\n", 'peek full')
rep("      if(back) st.ph.parentNode.insertBefore(st.card, st.ph); else st.card.remove();",
    "      if(back) st.ph.parentNode.insertBefore(st.card, st.ph); else st.card.remove();\n      CodisArt.thumb(st.card);   /* CODIS-BUTTER */", 'peek thumb')

# ---------------------------------------------------------------- 5) الوجه الخلفي يُبنى عند القلب فقط
#    55% من عناصر المتجر كانت وجوهاً خلفية (زخرفة SVG + صفوف) لا تُرى إلا بالقلب. الآن داخل <template>: يُقرأ لكن بلا ستايل/تخطيط/رسم،
#    ويُنقل للبطاقة قبل أول إطار من حركة القلب ⇒ القلب نفسه حرفياً. بطاقة ×10 المكبّرة تبقى جاهزة (eager).
rep("""    '<div class="cflip-in"><div class="cflip-f">' + front + '</div><div class="cflip-b" aria-hidden="true">' + back + '</div></div></div>';""",
    """    '<div class="cflip-in"><div class="cflip-f">' + front + '</div><div class="cflip-b" aria-hidden="true">' + (o.eager ? back : '<template class="cflip-lazy">' + back + '</template>') + '</div></div></div>';   /* CODIS-BUTTER */""", 'flip lazy back')
rep("""function codisFlipToggle(el){
  const on = !el.classList.contains('is-flipped');""", """function codisFlipToggle(el){
  const on = !el.classList.contains('is-flipped');
  const lz = el.querySelector('.cflip-b > template.cflip-lazy');   /* CODIS-BUTTER: الظهر يُبنى الآن، قبل بدء الدوران */
  if(lz){ const bk = lz.parentNode; bk.replaceChild(lz.content, lz); try{ codisHydrateIcons(bk); }catch(e){} }""", 'flip materialize')
rep("codisFlipHtml(art, back, { label:inf.name })", "codisFlipHtml(art, back, { label:inf.name, eager:true })", 'bulk zoom eager')

# ---------------------------------------------------------------- 6) خانات المتجر البعيدة لا تُحسب حتى تقترب (content-visibility لكل خانة)
#    فقط حيث يدعم المتصفح الحدث contentvisibilityautostatechange (codisCvOK) — غيره: السلوك القديم حرفياً.
rep("function codisFitLazy(root){\n  if(!root) return;", """if(codisCvOK) document.documentElement.classList.add('codis-cv');   /* CODIS-BUTTER */
/* خانة تقترب من الشاشة ⇒ تُرسم ⇒ ملاءمة بطاقاتها (من الذاكرة المحفوظة غالباً، بلا قياس) */
function codisCvTiles(root){
  if(root._cvTiles) return; root._cvTiles = true;
  root.addEventListener('contentvisibilityautostatechange', e=>{
    if(e.skipped) return; const t = e.target; if(!t || !t.parentElement || t.parentElement.getAttribute('role') !== 'list') return;
    const w = t.querySelectorAll('.fit-wait'); if(!w.length) return;
    Array.prototype.forEach.call(w, c=>c.classList.remove('fit-wait')); codisFitRewardCard(t);
  }, true);
}
function codisFitLazy(root){
  if(!root) return;""", 'cv tiles fn')
rep("  codisFitRewardCard(root);\n  if(!far.length) return;\n", "  codisFitRewardCard(root);\n  if(!far.length) return;\n  if(codisCvOK && root.id === 'eco-store-body'){ codisCvTiles(root); return; }   /* CODIS-BUTTER: البعيدة تُلاءم عند ظهورها لا بطابور يجبر تخطيطها */\n", 'cv tiles hook')
CSS = """
/* CODIS-BUTTER: خانات المتجر البعيدة عن الشاشة لا تُحسب ولا تُرسم حتى تقترب (المقاس يُتذكّر بعد أول رسم) */
.codis-cv #eco-store-body [role="list"] > *{ content-visibility:auto; contain-intrinsic-size:auto 240px; }
"""
i = s.index("</style>"); s = s[:i] + CSS + s[i:]

s = s.replace('<meta name="codis-version"', '<!-- CODIS-BUTTER --><meta name="codis-version"', 1)
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('ok thumbs=%d thumbsKB=%d out=%dKB' % (len(thumbs), sum(len(v) for v in thumbs.values()) // 1024, len(s.encode('utf-8')) // 1024))
