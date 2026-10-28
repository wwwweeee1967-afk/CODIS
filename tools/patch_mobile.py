"""CODIS-MOBILE: root fix for the iPhone store overlap + lighter rendering on phones. Run AFTER tools/patch_perf.py:  python tools/patch_mobile.py <in> <out>
1) The store used to be a position:fixed layer INSIDE the .main scroll container (-webkit-overflow-scrolling:touch). iOS Safari does not pin such a
   layer reliably, so it scrolled with the room and the room's header/top bar showed through. Now the store is a normal full page inside .main:
   while data-view="store" every other child of .main is hidden, .main itself is the scroller, and the top bar + dock are hidden.
2) Large inline images (data: URIs) are turned once into blob: URLs, and store images load lazily (off-screen art is not decoded up front).
3) On touch devices a room enters as ONE animation instead of a staggered animation per block (fewer simultaneous animations, no half-drawn room)."""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-MOBILE' not in t, 'mobile patch already applied'
assert 'CODIS-PERF' in t, 'run tools/patch_perf.py first'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

# ---- 1) store = full page in normal flow (no fixed layer inside a scroller) ----
rep("/* ===================== ZOOM LOCK", """/* CODIS-MOBILE: المتجر صفحة كاملة داخل .main (لا طبقة fixed داخل حاوية تمرير — iOS لا يثبّتها). باقي محتوى .main يختفي، و.main هو المُمرِّر */
html[data-view="store"] .main > :not(#page-settings){ display:none !important; }
html[data-view="store"] .main{ padding:0; }
html[data-view="store"] #page-settings.is-store-layer{ position:relative; inset:auto; z-index:auto; overflow:visible; min-height:100vh; min-height:100dvh; overscroll-behavior:auto; }
html[data-view="store"] .topbar-fade, html[data-view="store"] .topbar-mark, html[data-view="store"] .notif-bell,
html[data-view="store"] .store-btn, html[data-view="store"] .coin-chip{ opacity:0; visibility:hidden; pointer-events:none; }
/* أقسام المتجر خارج الشاشة لا تُحسب ولا تُرسم حتى تقترب (قياس: تخطيط المتجر 52–104ms → ~6ms). auto تحفظ الارتفاع الحقيقي بعد أول ظهور */
#eco-store-body > #eco-cosmetics, #eco-store-body > #eco-cards{ content-visibility:auto; contain-intrinsic-size:auto 1200px; }

/* ===================== ZOOM LOCK""")
rep("function econStoreScroller(){ return document.getElementById('page-settings'); }",
    "function econStoreScroller(){ return document.querySelector('.main') || document.getElementById('page-settings'); }   /* CODIS-MOBILE: المتجر يتمرر مع .main */")
rep("sec.style.display = 'block'; codisSyncView(); econDeferRender(secId, render);",
    "sec.style.display = 'block'; codisSyncView(); if(mainEl) mainEl.scrollTop = 0; econDeferRender(secId, render);")

# ---- 2) images: blob URLs once + lazy loading inside the store ----
rep("  function hydrate(root){\n", """  /* CODIS-MOBILE: كل صورة كبيرة تتحول مرة واحدة إلى blob: (عنوان قصير؛ المتصفح يحتفظ بفك ترميزها) بدل إسناد نص base64 ضخم مع كل رسم */
  const blobs = [];
  function blobUrl(i, u){
    if(blobs[i]) return blobs[i];
    if(!window.URL || !URL.createObjectURL || u.slice(0, 11) !== 'data:image/') return u;
    const c = u.indexOf(','), semi = u.indexOf(';'); if(c < 0 || semi < 0 || semi > c || u.slice(semi, c) !== ';base64') return u;
    try{
      const bin = atob(u.slice(c + 1)), arr = new Uint8Array(bin.length);
      for(let k = 0; k < bin.length; k++) arr[k] = bin.charCodeAt(k);
      return (blobs[i] = URL.createObjectURL(new Blob([arr], { type:u.slice(5, semi) })));
    }catch(e){ return u; }
  }
  function hydrate(root){
""")
rep("const im = a[k], u = list[+im.getAttribute('data-art')]; im.removeAttribute('data-art'); if(u){ im.decoding = 'async'; im.src = u; }",
    "const im = a[k], n = +im.getAttribute('data-art'), u = list[n]; im.removeAttribute('data-art'); if(u){ im.decoding = 'async'; if(im.closest('#eco-store-body') && !im.closest('.modal-overlay')) im.loading = 'lazy'; im.src = blobUrl(n, u); }")

# ---- 2b) fitting must not force layout of a skipped (content-visibility) section; it runs when the section comes into view ----
rep("function codisFitLazy(root){\n", "const codisCvOK = !!(window.CSS && CSS.supports && CSS.supports('content-visibility', 'auto') && ('oncontentvisibilityautostatechange' in HTMLElement.prototype));   /* CODIS-MOBILE */\nfunction codisFitLazy(root){\n")
rep("  for(let i = 0; i < cards.length; i++){ const r = cards[i].getBoundingClientRect();",
    "  const skipped = Array.prototype.filter.call(root.querySelectorAll('#eco-cosmetics, #eco-cards'), s=>{ if(!codisCvOK) return false; const r = s.getBoundingClientRect(); return r.top > vh * 1.3 || r.bottom < -vh * .3; });   /* CODIS-MOBILE: قسم بعيد = لا قياس لبطاقاته الآن */\n"
    "  skipped.forEach(s=>{ if(s._cvFit) return; s._cvFit = true; s.addEventListener('contentvisibilityautostatechange', e=>{ if(e.skipped) return; Array.prototype.forEach.call(s.querySelectorAll('.fit-wait'), c=>c.classList.remove('fit-wait')); codisFitLazy(s); }); });\n"
    "  for(let i = 0; i < cards.length; i++){ if(skipped.length && skipped.some(s=>s.contains(cards[i]))){ cards[i].classList.add('fit-wait'); continue; } const r = cards[i].getBoundingClientRect();")

# ---- 3) touch devices: one entrance animation per room ----
rep("    const blocks = collect(el, [], 0);\n    if(!blocks.length){ enter(el, { dir:o.dir, delay:o.delay || 0 }); return; }",
    "    if(window.matchMedia && window.matchMedia('(pointer: coarse)').matches){ enter(el, { dir:o.dir, delay:o.delay || 0 }); return; }   /* CODIS-MOBILE: حركة واحدة للغرفة على الجوال */\n"
    "    const blocks = collect(el, [], 0);\n    if(!blocks.length){ enter(el, { dir:o.dir, delay:o.delay || 0 }); return; }")

open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
