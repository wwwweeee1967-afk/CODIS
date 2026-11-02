#!/usr/bin/env python3
"""CODIS-OFFLINE (بعد patch_v19.py) — 3.12.0
 1) العمل دون إنترنت + مزامنة تلقائية: طبقة IndexedDB مرآة لنسخة العمل + لقطة الأساس لكل حساب، ودمج ثلاثي (أساس/جهاز/حساب) بلا أي نافذة اختيار،
    رفع تفاؤلي بإصدار الخادم مع إعادة المحاولة، مشغّلات online/visibility/focus/pageshow/Background Sync، وحالة مزامنة صريحة.
 2) المخزون والمؤقتات: «استخدام» الزر الرئيسي و«بيع» ثانوي · قفل البيع يشمل المؤقت الشغّال والمنتهي غير المثبَّت · إكمال الانتهاء قابل لإعادة المحاولة (idempotent).
 3) معاينة البطاقة بالضغط المطوّل: تُرسم بحجمها النهائي (zoom) ثم تُصغَّر بالـFLIP بدل تكبير صورة صغيرة — حادة دائماً.
 4) الإشعارات: رسائل حالة دقيقة (VAPID/iOS/تسجيل الدخول)، إعادة جدولة المؤقتات المعلقة عند عودة المزامنة، وSW يستقبل pushsubscriptionchange وBackground Sync."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-OFFLINE' in s: sys.exit('already patched (CODIS-OFFLINE)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

def between(a, b, new, label):
    """يستبدل الجزء من أول ظهور لـ a حتى (دون) أول ظهور لاحق لـ b"""
    global s
    if s.count(a) != 1: sys.exit('start anchor "%s" matched %d times' % (label, s.count(a)))
    i = s.index(a); j = s.index(b, i)
    s = s[:i] + new + s[j:]

# =====================================================================
# 1) المخزون والمؤقتات
# =====================================================================
rep("doneAt:n(x.doneAt) || null, notified:!!x.notified, server:!!x.server };",
    "doneAt:n(x.doneAt) || null, notified:!!x.notified, server:!!x.server, fin:x.state === 'done' ? x.fin !== false : false };", 'timer clean')

rep("""    all().forEach(t=>{
      if(t.state !== 'running') return;
      const h = H[t.kind];
      if(!h || (h.alive && !h.alive(t))){ t.state = 'cancelled'; t.doneAt = now; changed = true; kinds[t.kind] = 1; CodisPush.unschedule(t); return; }
      if(now < t.endsAt) return;
      t.state = 'done'; t.doneAt = t.endsAt; changed = true; kinds[t.kind] = 1;
      let ok = true; try{ ok = h.done(t) !== false; }catch(e){ console.error('CodisTimers.done:', e); }
      if(ok) announce(t, now);
    });""", """    all().forEach(t=>{
      if(t.state === 'done' && t.fin === false){   /* CODIS-OFFLINE: انتهى لكن تثبيت الحالة (markUsed) لم ينجح بعد — يُعاد بأمان (idempotent) حتى ينجح، والبيع محجوب طوال ذلك */
        const h2 = H[t.kind]; let ok2 = false; try{ ok2 = !h2 || h2.done(t) !== false; }catch(e){ console.error('CodisTimers.retry:', e); }
        if(ok2){ t.fin = true; changed = true; kinds[t.kind] = 1; announce(t, now); }
        return;
      }
      if(t.state !== 'running') return;
      const h = H[t.kind];
      if(!h || (h.alive && !h.alive(t))){ t.state = 'cancelled'; t.doneAt = now; changed = true; kinds[t.kind] = 1; CodisPush.unschedule(t); return; }
      if(now < t.endsAt) return;
      t.state = 'done'; t.doneAt = t.endsAt; t.fin = false; changed = true; kinds[t.kind] = 1;
      let ok = false; try{ ok = h.done(t) !== false; }catch(e){ console.error('CodisTimers.done:', e); }
      if(ok){ t.fin = true; announce(t, now); }
    });""", 'timer tick')

rep("""    const want = run.length > 0 && document.visibilityState === 'visible';
    if(want && !ivl) ivl = setInterval(paint, 1000);""", """    if(!tmo && all().some(t=>t.state === 'done' && t.fin === false)) tmo = setTimeout(tick, 4000);   /* إعادة محاولة تثبيت الانتهاء */
    const want = run.length > 0 && document.visibilityState === 'visible';
    if(want && !ivl) ivl = setInterval(paint, 1000);""", 'timer arm')

rep("""function codisTimerBlocksSell(uid){ return !!CodisTimers.active('reward', uid) && !CodisLimits.bypass('timer.sellActive'); }""",
"""function codisTimerBlocksSell(uid){
  /* القفل في منطق الاقتصاد (sellCheck → كل مسارات البيع الفردي/الجماعي/المكررات) لا في الواجهة: مؤقت شغّال، أو منتهٍ لكن تثبيته كـ«مستخدمة» لم يكتمل بعد */
  const l = CodisTimers.latest('reward', uid), live = !!l && (l.state === 'running' || (l.state === 'done' && l.fin === false));
  return live && !CodisLimits.bypass('timer.sellActive');
}""", 'sell block')

rep("""  done:t=>{ const r = CodisEconomy.markUsed(t.ref); return !!(r && r.ok); },
  message:t=>({ title:'انتهى الوقت', body:'انتهى وقت مكافأة ' + t.label }),""", """  done:t=>{   /* idempotent: النسخة المستخدَمة/المباعة/المحذوفة سلفاً = تم الإكمال ولا يُكرَّر شيء */
    const it = CodisInventory.get(t.ref); if(!it || it.status !== 'owned') return true;
    const r = CodisEconomy.markUsed(t.ref); return !!(r && r.ok);
  },
  message:t=>({ title:'انتهى الوقت', body:'انتهى وقت مكافأة ' + t.label }),""", 'reward done')

# زر «استخدام» رئيسي + «بيع» ثانوي
rep("""  return '<button type="button" class="chip-act' + (d ? ' tmr-go' : '') + '" ' + (busy ? 'disabled' : '') + ' onclick="econUse(\\'' + uid + '\\')">' + (d ? CODIS_PLAY_SVG + 'ابدأ · ' + CodisDuration.label(d.min) : 'استخدمتها') + '</button>';""",
    """  return '<button type="button" class="btn btn-primary own-use own-go' + (d ? ' tmr-go' : '') + '" ' + (busy ? 'disabled aria-disabled="true"' : '') + ' onclick="econUse(\\'' + uid + '\\')">' + (d ? CODIS_PLAY_SVG + '<span>ابدأ · ' + CodisDuration.label(d.min) + '</span>' : codisIcon('check') + '<span>استخدام</span>') + '</button>';""", 'use btn')
rep("""'<div class="shop-acts"><button type="button" class="btn btn-secondary" ' + (can && !busy ? '' : 'disabled aria-disabled="true"') + ' aria-label="' + escapeHtml((can ? 'بيع ' + it.name""",
    """'<div class="shop-acts">' + codisOwnUseBtnHtml(it, uid, busy) + '<button type="button" class="btn btn-secondary own-sell" ' + (can && !busy ? '' : 'disabled aria-disabled="true"') + ' aria-label="' + escapeHtml((can ? 'بيع ' + it.name""", 'acts open')
rep("""'<span>لا تُباع</span>') + '</button>' +
          codisOwnUseBtnHtml(it, uid, busy) + '</div></div>';""", """'<span>لا تُباع</span>') + '</button></div></div>';""", 'acts close')

# =====================================================================
# 2) معاينة البطاقة الحادة
# =====================================================================
between("    host.appendChild(card);\n    card.classList.add('is-peek');", "    requestAnimationFrame(()=>ov.classList.add('is-in'));", """    card.classList.add('is-peek');
    /* CODIS-OFFLINE (جودة): كانت البطاقة تُرسَم بحجمها الصغير ثم تُكبَّر بـtransform+will-change فتُمدَّد صورة الطبقة (بكسلة/بهتان).
       الآن تُرسَم فعلاً بالحجم النهائي (zoom) داخل غلاف fly، والحركة FLIP تبدأ مصغَّرة 1/k وتصل 1 — التركيب يعتمد أكبر مقياس بالحركة فتبقى الحدة كاملة. */
    const o = ov.getBoundingClientRect();
    const vw = o.width, vh = o.height, k = Math.max(1, Math.min(2.3, vw * .8 / r.width, vh * .64 / r.height));
    const zoomOk = k > 1.02 && !!(window.CSS && CSS.supports && CSS.supports('zoom', '2'));
    const fw = r.width * k, fh = r.height * k, fl = (vw - fw) / 2, ft = (vh - fh) / 2 - 12;
    const dx = ((r.left - o.left) + r.width / 2) - (fl + fw / 2), dy = ((r.top - o.top) + r.height / 2) - (ft + fh / 2);
    let fly = null;
    if(zoomOk){
      fly = document.createElement('div'); fly.className = 'peek-fly';
      Object.assign(fly.style, { position:'fixed', left:fl + 'px', top:ft + 'px', width:fw + 'px', height:fh + 'px', zIndex:'2' });
      host.appendChild(fly); fly.appendChild(card);
      Object.assign(card.style, { zoom:String(k), width:r.width + 'px', margin:'0' });
      s = { card:card, ph:ph, ov:ov, r:r, prev:document.activeElement, fly:fly, k:k, fl:fl, ft:ft, fw:fw, fh:fh };
      const from = 'translate(' + dx + 'px,' + dy + 'px) scale(' + (1 / k) + ')';
      fly.style.transform = 'none';   /* الحالة النهائية مكتوبة أولاً؛ الحركة تنطلق منها فقط (تقليل الحركة/تعذّر الحركة ← النهائية فوراً) */
      codisAnim(fly, [{ transform:from }, { transform:'translate(' + dx * .08 + 'px,' + (dy * .08 - 8) + 'px) scale(1.035)', offset:.72 }, { transform:'translate(0px,0px) scale(1)' }], { dur:560, ease:tok('--ease-glide') || 'cubic-bezier(.25,1.08,.4,1)' });
    } else {   /* متصفح بلا zoom: المسار القديم لكن بلا will-change/3D ليُعاد تصيير الطبقة بالمقياس النهائي */
      host.appendChild(card); card.classList.add('peek-nofly');
      Object.assign(card.style, { position:'fixed', left:(r.left - o.left) + 'px', top:(r.top - o.top) + 'px', width:r.width + 'px', margin:'0', zIndex:'2' });
      const ddx = (o.left + vw / 2) - (r.left + r.width / 2), ddy = (o.top + vh / 2) - (r.top + r.height / 2) - 12, to = 'translate(' + ddx + 'px,' + ddy + 'px) scale(' + k + ')';
      s = { card:card, ph:ph, ov:ov, r:r, prev:document.activeElement };
      card.style.transform = to;
      codisAnim(card, [{ transform:'translate(0,0) scale(1)' }, { transform:'translate(' + ddx * .9 + 'px,' + (ddy * .9 - 10) + 'px) scale(' + k * 1.04 + ')', offset:.7 }, { transform:to }], { dur:560, ease:tok('--ease-glide') || 'cubic-bezier(.25,1.08,.4,1)' });
    }
""", 'peek open')

between("  function close(){\n    if(!s || s.closing) return; const st = s; st.closing = true;", "  return { close:close, isOpen:()=>!!s, el:()=>s && s.ov, _open:open };", """  function close(){
    if(!s || s.closing) return; const st = s; st.closing = true;
    const back = st.ph.isConnected, o = st.ov.getBoundingClientRect(), tgt = st.fly || st.card;
    let to = 'translate(0px,0px) scale(1)';
    if(back){
      const pr = st.ph.getBoundingClientRect();
      if(st.fly) to = 'translate(' + ((pr.left - o.left) + pr.width / 2 - (st.fl + st.fw / 2)) + 'px,' + ((pr.top - o.top) + pr.height / 2 - (st.ft + st.fh / 2)) + 'px) scale(' + (1 / st.k) + ')';
      else to = 'translate(' + (pr.left - st.r.left) + 'px,' + (pr.top - st.r.top) + 'px) scale(1)';
    }
    st.ov.classList.remove('is-in'); st.ov.classList.add('is-out');
    let fin = false;
    const done = ()=>{
      if(fin) return; fin = true;
      try{ tgt.getAnimations().forEach(a=>a.cancel()); }catch(e){}
      st.card.classList.remove('is-peek', 'peek-nofly'); ['position', 'left', 'top', 'width', 'margin', 'zIndex', 'transform', 'opacity', 'zoom'].forEach(k=>{ st.card.style[k] = ''; });
      if(back) st.ph.parentNode.insertBefore(st.card, st.ph); else st.card.remove();
      if(st.fly) st.fly.remove();
      st.ph.remove(); st.ov.remove(); if(s === st) s = null;
      try{ if(st.prev && st.prev.isConnected && st.prev.focus) st.prev.focus({ preventScroll:true }); }catch(e){}
    };
    const cur = (st.fly ? 'translate(0px,0px) scale(1)' : st.card.style.transform);
    const kf = back ? [{ transform:cur }, { transform:to }] : [{ transform:cur, opacity:1 }, { transform:cur + ' scale(.9)', opacity:0 }];
    const a = codisAnim(tgt, kf, { dur:360, ease:tok('--ease-ios') || 'cubic-bezier(.32,.72,0,1)', fill:'forwards', done:done });
    if(!a) done(); else setTimeout(done, 460);
  }
""", 'peek close')

rep(".peek .is-peek{ transform-origin:50% 50%; will-change:transform; filter:drop-shadow(0 26px 40px rgba(0,0,0,.55)); }",
    ".peek .peek-fly{ transform-origin:50% 50%; filter:drop-shadow(0 26px 40px rgba(0,0,0,.55)); }\n.peek .is-peek.peek-nofly{ transform-origin:50% 50%; filter:drop-shadow(0 26px 40px rgba(0,0,0,.55)); }\n.peek .peek-fly > .is-peek{ position:relative; }", 'peek css')

# =====================================================================
# 3) الطبقات الجديدة: IndexedDB + الدمج الثلاثي
# =====================================================================
LAYER = r"""/* ===== CODIS-OFFLINE: التخزين المحلي الدائم (IndexedDB) =====
   localStorage يبقى مسار الحفظ المتزامن السريع (saveData)، وIndexedDB مرآة دائمة لنسخة العمل + لقطة «الأساس» (آخر ما أكّده الخادم) لكل حساب.
   الاستعادة غير المتزامنة تحدث فقط إن اختفت نسخة localStorage (إخلاء المتصفح/امتلاء). المرآة مرتبطة بمعرّف المالك فلا تنتقل بين حسابات. */
const CodisLocalDB = (function(){
  'use strict';
  let dbp = null, pend = null, flushing = false;
  function open(){
    if(dbp) return dbp;
    dbp = new Promise(res=>{
      try{
        if(!('indexedDB' in window) || !indexedDB){ res(null); return; }
        const rq = indexedDB.open('codis-local', 1);
        rq.onupgradeneeded = ()=>{ const d = rq.result; if(!d.objectStoreNames.contains('kv')) d.createObjectStore('kv'); };
        rq.onsuccess = ()=>res(rq.result); rq.onerror = ()=>res(null); rq.onblocked = ()=>res(null);
      }catch(e){ res(null); }
    });
    return dbp;
  }
  const run = (mode, fn)=>open().then(db=>db ? new Promise(res=>{
    try{ const t = db.transaction('kv', mode), st = t.objectStore('kv'); let out = true; const rq = fn(st); if(rq && 'onsuccess' in rq) rq.onsuccess = ()=>{ out = rq.result === undefined ? null : rq.result; };
      t.oncomplete = ()=>res(out); t.onerror = t.onabort = ()=>res(null); }catch(e){ res(null); }
  }) : null);
  const put = (k, v)=>run('readwrite', st=>st.put(v, k));
  const get = k=>run('readonly', st=>st.get(k));
  const del = k=>run('readwrite', st=>st.delete(k));
  const clearAll = ()=>run('readwrite', st=>st.clear());
  /* مرآة نسخة العمل: تُدمَج الكتابات المتتالية (الأحدث فقط) وتُكتب بعد الحفظ المحلي الناجح */
  function mirror(raw){
    pend = raw; if(flushing) return; flushing = true;
    Promise.resolve().then(async ()=>{
      try{ while(pend !== null){ const r = pend; pend = null; let owner = 'guest'; try{ const m = JSON.parse(localStorage.getItem('codis_sync_meta') || 'null'); if(m && m.owner) owner = m.owner; }catch(e){} await put('work', { json:r, owner:owner, at:Date.now() }); } }
      finally{ flushing = false; }
    });
  }
  return { open:open, put:put, get:get, del:del, clearAll:clearAll, mirror:mirror, flush:()=>new Promise(r=>{ const w = ()=>flushing || pend !== null ? setTimeout(w, 10) : r(true); w(); }) };
})();

/* ===== CODIS-OFFLINE: الدمج الثلاثي (أساس / نسخة الجهاز / نسخة الحساب) =====
   لا يسأل المستخدم ولا يختار «أحدث تاريخ ثم يحذف الأخرى»:
   · كائنات: دمج مفتاحاً مفتاحاً · مصفوفات ذات معرّفات (id/uid/ev): اتحاد بالمعرّف مع دمج كل عنصر على حدة · غير ذلك: اتحاد بالقيمة
   · الحذف يُحتسب فقط إن حذفه طرف ولم يعدّله الآخر (التعديل يتفوّق على الحذف فلا يضيع شيء)
   · حالات أحادية الاتجاه (owned < used < sold، running < cancelled < done، pending < resolved…): الأعلى يفوز
   · المحفظة: الرصيد = رصيد الحساب + مجموع معاملات هذا الجهاز الجديدة فقط، ومعاملة (type+referenceId) المكرَّرة لا تُحسب مرتين
   · بعد الدمج: اتساق المخزون مع دفتر المحفظة، وعدم تكرار مكافأة قُرِّر عليها على جهازين بقرارين مختلفين */
const CodisMerge = (function(){
  'use strict';
  const IDK = ['id', 'uid', 'ev'];
  const RANK = { pending:0, owned:0, running:0, open:0, active:0, cancelled:1, void:1, expired:1, used:2, opened:2, resolved:2, done:3, sold:3 };
  const isO = v=>!!v && typeof v === 'object' && !Array.isArray(v);
  const js = v=>JSON.stringify(v);
  const same = (a, b)=>js(a) === js(b);
  const cl = v=>v === undefined ? undefined : JSON.parse(js(v));
  const prim = v=>v === null || typeof v !== 'object';
  function canon(v){ if(Array.isArray(v)) return '[' + v.map(canon).join(',') + ']'; if(isO(v)) return '{' + Object.keys(v).sort().map(k=>JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}'; return JSON.stringify(v); }
  function ident(x){ if(!isO(x)) return null; for(let i = 0; i < IDK.length; i++){ const v = x[IDK[i]]; if(typeof v === 'string' && v) return IDK[i] + ':' + v; } return null; }
  function pickScalar(b, l, r, c){
    if(typeof l === 'string' && typeof r === 'string' && l in RANK && r in RANK && RANK[l] !== RANK[r]) return RANK[l] > RANK[r] ? l : r;
    return c.localNewer ? l : r;
  }
  function mergeValue(b, l, r, c, path){
    if(same(l, r)) return cl(l);
    if(b !== undefined && same(l, b)) return cl(r);
    if(b !== undefined && same(r, b)) return cl(l);
    if(path === 'wallet' && isO(l) && isO(r)) return mergeWallet(isO(b) ? b : null, l, r, c);
    if(isO(l) && isO(r)) return mergeObj(isO(b) ? b : undefined, l, r, c, path);
    if(Array.isArray(l) && Array.isArray(r)) return mergeArr(Array.isArray(b) ? b : undefined, l, r, c, path);
    return cl(pickScalar(b, l, r, c));
  }
  function mergeObj(b, l, r, c, path){
    const out = {}, keys = {}; Object.keys(r).forEach(k=>{ keys[k] = 1; }); Object.keys(l).forEach(k=>{ keys[k] = 1; });
    Object.keys(keys).forEach(k=>{
      const hasL = Object.prototype.hasOwnProperty.call(l, k), hasR = Object.prototype.hasOwnProperty.call(r, k), hasB = !!b && Object.prototype.hasOwnProperty.call(b, k), bv = hasB ? b[k] : undefined;
      if(hasL && hasR){ out[k] = mergeValue(bv, l[k], r[k], c, path ? path + '.' + k : k); return; }
      if(hasL){ if(hasB && same(l[k], bv)) return; out[k] = cl(l[k]); return; }   // حذفه الحساب ولم نعدّله ← يُحذف
      if(hasB && same(r[k], bv)) return; out[k] = cl(r[k]);                         // حذفناه محلياً ولم يعدّله الحساب ← يُحذف
    });
    return out;
  }
  function mergeArr(b, l, r, c, path){
    const hasIds = a=>a.length > 0 && a.every(x=>ident(x) !== null);
    if((hasIds(l) || !l.length) && (hasIds(r) || !r.length) && (!b || hasIds(b) || !b.length)){
      const bm = new Map((b || []).map(x=>[ident(x), x])), lm = new Map(l.map(x=>[ident(x), x])), rm = new Map(r.map(x=>[ident(x), x])), order = [], seen = new Set();
      r.forEach(x=>{ const i = ident(x); if(!seen.has(i)){ seen.add(i); order.push(i); } }); l.forEach(x=>{ const i = ident(x); if(!seen.has(i)){ seen.add(i); order.push(i); } });
      const out = [];
      order.forEach(i=>{
        const bi = bm.get(i), li = lm.get(i), ri = rm.get(i);
        if(li !== undefined && ri !== undefined) out.push(mergeValue(bi, li, ri, c, path));
        else if(li !== undefined){ if(bi !== undefined && same(li, bi)) return; out.push(cl(li)); }
        else { if(bi !== undefined && same(ri, bi)) return; out.push(cl(ri)); }
      });
      return out;
    }
    const bs = new Set((b || []).map(js)), ls = new Set(l.map(js)), rs = new Set(r.map(js)), out = [];
    r.forEach(x=>{ const k = js(x); if(bs.has(k) && !ls.has(k)) return; out.push(cl(x)); });
    l.forEach(x=>{ const k = js(x); if(!rs.has(k) && !bs.has(k)) out.push(cl(x)); });
    return out;
  }
  /* محفظة (كوين/فضة): الرصيد لا يُجمع من نسختين — تُضاف فقط معاملات الجهاز الجديدة غير الموجودة بالحساب */
  function mergeWalletSide(b, l, r){
    const out = cl(r), bt = new Set(((b && b.transactions) || []).map(t=>t && t.id)), txs = (r.transactions || []).slice();
    const haveId = new Set(txs.map(t=>t && t.id)), key = t=>t.type + '|' + t.referenceId, haveKey = new Set(txs.filter(t=>t && t.referenceId).map(key));
    let add = 0, earned = 0, spent = 0;
    (l.transactions || []).forEach(t=>{
      if(!t || typeof t.amount !== 'number' || bt.has(t.id) || haveId.has(t.id)) return;
      if(t.referenceId && haveKey.has(key(t))) return;
      txs.push(cl(t)); haveId.add(t.id); if(t.referenceId) haveKey.add(key(t));
      add += t.amount; if(t.amount > 0) earned += t.amount; else spent += -t.amount;
    });
    out.transactions = txs.length > 1500 ? txs.slice(txs.length - 1500) : txs;
    out.balance = (Number(r.balance) || 0) + add; out.lifetimeEarned = (Number(r.lifetimeEarned) || 0) + earned; out.lifetimeSpent = (Number(r.lifetimeSpent) || 0) + spent;
    return out;
  }
  function mergeWallet(b, l, r, c){
    const out = mergeWalletSide(b, l, r);
    if(isO(l.silver) || isO(r.silver)) out.silver = mergeWalletSide(b && b.silver, l.silver || { transactions:[], balance:0 }, r.silver || { transactions:[], balance:0 });
    Object.keys(l).forEach(k=>{ if(!(k in out) && k !== 'silver') out[k] = cl(l[k]); });
    return out;
  }
  /* اتساق ما بعد الدمج */
  function finalize(m){
    try{
      const w = m.wallet, inv = m.inventory, led = m.outcomeLedger;
      const txs = (w && Array.isArray(w.transactions)) ? w.transactions : [];
      const byRef = {}; txs.forEach(t=>{ if(t && t.referenceId) byRef[t.type + '|' + t.referenceId] = t; });
      if(inv && Array.isArray(inv.items)){
        inv.items.forEach(it=>{ const t = byRef['SELL_REWARD|sell|' + it.uid]; if(t && it.status !== 'sold'){ it.status = 'sold'; it.soldFor = t.amount; it.sellTx = t.id; } });
        if(led && isO(led)) Object.keys(led).forEach(id=>{
          const e = led[id]; if(!e || e.kind !== 'reward' || e.status !== 'resolved') return;
          const coin = byRef['EARN_REWARD_EXCHANGE|' + id], idx = inv.items.findIndex(x=>x.uid === 'own|' + id);
          if(!coin || idx < 0) return;   // قرار واحد فقط ← سليم
          /* قرار «كوين» على جهاز و«أخذ المكافأة» على آخر: لا مكافأتان. نبقى على الكوين إن كانت النسخة ما زالت مملوكة، وإلا نبقى على النسخة ونسحب الكوين */
          if(inv.items[idx].status === 'owned'){ inv.items.splice(idx, 1); e.decision = 'coins'; }
          else { const ti = txs.indexOf(coin); if(ti >= 0){ txs.splice(ti, 1); w.balance -= coin.amount; if(coin.amount > 0) w.lifetimeEarned -= coin.amount; } e.decision = 'item'; }
        });
      }
    }catch(e){ console.warn('[CODIS merge] finalize:', e && e.message); }
    return m;
  }
  function merge(base, local, remote, opts){
    const c = Object.assign({ localNewer:false }, opts || {});
    const b = isO(base) ? base : undefined, l = isO(local) ? local : {}, r = isO(remote) ? remote : {};
    return finalize(mergeValue(b, l, r, c, ''));
  }
  return { merge:merge, same:(a, b)=>canon(a) === canon(b), canon:canon };
})();

const CodisAccount = (function(){"""
rep("const CodisAccount = (function(){", LAYER, 'layer insert')

# مرآة بعد كل حفظ ناجح
rep("  if(ok && typeof CodisAccount !== 'undefined'){ try{ CodisAccount.noteChange(); }catch(e){} }   // مزامنة الحساب (إن وُجد)\n  return ok;",
    "  if(ok){ try{ CodisLocalDB.mirror(raw); }catch(e){} }   /* CODIS-OFFLINE: مرآة دائمة IndexedDB */\n  if(ok && typeof CodisAccount !== 'undefined'){ try{ CodisAccount.noteChange(); }catch(e){} }   // مزامنة الحساب (إن وُجد)\n  return ok;", 'mirror hook')

# استعادة من IndexedDB إن اختفت نسخة localStorage
rep("let data = loadData();\n", """let data = loadData();
/* CODIS-OFFLINE: إن اختفت نسخة localStorage (إخلاء المتصفح/تنظيف) تُستعاد نسخة العمل من IndexedDB لنفس المالك — مرة واحدة ثم إعادة تحميل */
(function(){
  try{
    if(localStorage.getItem(STORE_KEY) || typeof indexedDB === 'undefined') return;
    if(sessionStorage.getItem('codis_idb_restore')) return;
    CodisLocalDB.get('work').then(w=>{
      try{
        if(!w || typeof w.json !== 'string' || w.json.length < 20) return;
        const mo = JSON.parse(localStorage.getItem('codis_sync_meta') || 'null'), owner = (mo && mo.owner) || 'guest';
        if((w.owner || 'guest') !== owner) return;
        JSON.parse(w.json);
        localStorage.setItem(STORE_KEY, w.json); sessionStorage.setItem('codis_idb_restore', '1'); location.reload();
      }catch(e){}
    });
  }catch(e){}
})();
""", 'idb restore')

# =====================================================================
# 4) CodisAccount: حالة + دمج + دفع + مطابقة بلا اختيارات
# =====================================================================
rep("""  const LABELS = { idle:'', synced:'تمّت المزامنة', syncing:'جارٍ المزامنة…', pending:'بانتظار المزامنة', offline:'لا يوجد اتصال — ستُزامَن تلقائياً عند عودته', error:'تعذّرت المزامنة — ستُعاد المحاولة', expired:'انتهت الجلسة — سجّل الدخول مجدداً' };""",
"""  /* CODIS-OFFLINE: «محفوظ على الجهاز» ≠ «محفوظ بالحساب» — كل حالة بنص مستقل */
  const LABELS = { idle:'', synced:'متزامن مع الحساب — كل تغييراتك محفوظة بالحساب', syncing:'جارٍ رفع التغييرات إلى الحساب…', pending:'محفوظة على هذا الجهاز — بانتظار الرفع إلى الحساب',
    offline:'دون اتصال — تغييراتك محفوظة على الجهاز وتُرفع تلقائياً عند عودة الإنترنت', error:'تعذّر الوصول للخادم — محفوظة على الجهاز وستُعاد المحاولة تلقائياً',
    expired:'انتهت جلسة الدخول — تغييراتك محفوظة على الجهاز، سجّل الدخول لإكمال المزامنة' };
  const SHORT = { synced:'متزامن', syncing:'جارٍ الرفع', pending:'بانتظار الرفع', offline:'دون اتصال', error:'ستُعاد المحاولة', expired:'تحتاج دخولاً', idle:'مسجّل' };""", 'labels')
rep("S.status === 'synced' ? 'متزامن' : S.status === 'syncing' ? 'جارٍ المزامنة' : S.status === 'idle' ? 'مسجّل' : 'بانتظار المزامنة'", "(SHORT[S.status] || 'بانتظار الرفع')", 'home label')

between("  function applyRemote(row){", "  /* ---------- الدفع ---------- */", """  /* لقطة الأساس = آخر نسخة أكّد الخادم أنها عنده (لكل حساب) — أساس الدمج الثلاثي */
  const baseKey = uid => 'base|' + uid;
  async function loadBase(uid){ try{ return await CodisLocalDB.get(baseKey(uid)); }catch(e){ return null; } }
  async function saveBase(uid, snap){ try{ await CodisLocalDB.put(baseKey(uid), { v:1, at:Date.now(), data:snap }); }catch(e){} }
  async function applyRemote(row){
    const d = row.data && typeof row.data === 'object' ? row.data : {};
    try{ const cur = jparse(rd(STORE_KEY), null); if(!d.settings || typeof d.settings !== 'object') d.settings = {}; d.settings.appLockFace = cur && cur.settings ? (cur.settings.appLockFace || null) : null; }catch(e){}
    codisSaveSuspended = true;
    if(!wr(STORE_KEY, JSON.stringify(d))){ codisSaveSuspended = false; setStatus('error', 'تعذّر حفظ بيانات الحساب على هذا الجهاز (التخزين ممتلئ أو معطّل).'); return false; }
    await saveBase(S.user.id, d);
    saveMeta({ owner:S.user.id, base:row.version, dirty:false, lastSync:Date.now(), changedAt:0 });
    try{ await CodisLocalDB.flush(); }catch(e){}
    reloadGuarded(); return true;
  }

""", 'applyRemote')

between("  async function push(){", "  /* ---------- تسجيل الدخول (Google / PKCE) ---------- */", r"""  async function push(){
    if(window.CODIS_SYNC_HOLD || pushing || !ready()) return;   /* CODIS-SYNC-HOLD */
    const m = meta(); if(m.owner !== S.user.id || !m.dirty) return;
    pushing = true; const sent = changeCtr; setStatus('syncing');
    try{
      const snap = snapshot();
      const r = await rpc('save_progress', { p_data:snap, p_base_version:m.base });
      if(r && r.ok){
        await saveBase(S.user.id, snap);
        const m2 = meta(); m2.base = r.version; m2.dirty = changeCtr !== sent; m2.lastSync = Date.now(); saveMeta(m2); retryMs = 0;
        setStatus(m2.dirty ? 'pending' : 'synced'); if(m2.dirty) schedule(600);
        try{ CodisPush.resync(); }catch(e){}   /* جدولة إشعارات المؤقتات التي لم تصل للخادم أثناء الانقطاع */
      } else if(r && r.conflict && (r.data === null || r.data === undefined)){ const m3 = meta(); m3.base = r.version || 0; m3.dirty = true; saveMeta(m3); schedule(100); }
      else if(r && r.conflict){ pushing = false; await resolveConflict(r); }
      else throw new Error('bad response');
    }catch(e){ netFail(e); }
    finally{ pushing = false; }
  }
  /* دمج + رفع بلا أسئلة: يعيد المحاولة عند سباق جديد، ويعتمد النتيجة محلياً (ثم إعادة تحميل فقط إن اختلفت عمّا بالجهاز) */
  async function mergeAndAdopt(row, localData, tag){
    S.reconciling = true; setStatus('syncing');
    try{
      const uid = S.user.id; const baseRec = await loadBase(uid); let baseData = baseRec ? baseRec.data : null, local = localData || snapshot(), remote = row, pushed = false, merged = null, ver = row.version;
      for(let tries = 0; tries < 6; tries++){
        const m = meta(), ctr = changeCtr;
        merged = CodisMerge.merge(baseData, local, remote.data || {}, { localNewer:(m.changedAt || 0) > (remote.updated_at ? Date.parse(remote.updated_at) : 0) });
        if(!merged.settings || typeof merged.settings !== 'object') merged.settings = {};
        merged.settings.appLockFace = (local.settings && local.settings.appLockFace) || null;
        let res = null; try{ res = await rpc('save_progress', { p_data:merged, p_base_version:remote.version }); }catch(e){ if(e && (e.net || e.http >= 500)){ pushed = false; ver = remote.version; break; } throw e; }
        if(res && res.ok){
          pushed = true; ver = res.version;
          if(!localData && changeCtr !== ctr){ baseData = local; local = snapshot(); remote = { data:merged, version:res.version }; continue; }   // المستخدم عدّل أثناء الدمج: نعيد الدمج فوق النتيجة المرفوعة
          break;
        }
        if(res && res.conflict){ remote = { data:res.data || {}, version:res.version || 0, updated_at:res.updated_at }; continue; }
        throw new Error('bad response');
      }
      const same = CodisMerge.same(merged, local);
      try{ backupLocal(tag || 'before_merge', rd(STORE_KEY) || ''); }catch(e){}
      await saveBase(uid, pushed ? merged : remote.data);
      if(same){
        saveMeta({ owner:uid, base:ver, dirty:!pushed, lastSync:pushed ? Date.now() : (meta().lastSync || 0), changedAt:Date.now() });
        S.reconciling = false; setStatus(pushed ? 'synced' : 'pending'); if(!pushed) schedule(5000); return true;
      }
      codisSaveSuspended = true;
      if(!wr(STORE_KEY, JSON.stringify(merged))){ codisSaveSuspended = false; setStatus('error', 'تعذّر حفظ البيانات المدموجة على هذا الجهاز (التخزين ممتلئ أو معطّل).'); return false; }
      saveMeta({ owner:uid, base:ver, dirty:!pushed, lastSync:pushed ? Date.now() : 0, changedAt:Date.now() });
      try{ await CodisLocalDB.put('work', { json:JSON.stringify(merged), owner:uid, at:Date.now() }); }catch(e){}
      S.reconciling = false; reloadGuarded(); return true;
    } finally { S.reconciling = false; }
  }
  async function resolveConflict(row){ await mergeAndAdopt(row, null, 'before_merge'); }

  /* ---------- مطابقة عند الدخول/الإقلاع/العودة (بلا أي نافذة اختيار) ---------- */
  async function reconcile(){
    if(window.CODIS_SYNC_HOLD) return;   /* CODIS-SYNC-HOLD */
    S.reconciling = true; setStatus('syncing');
    try{
      const uid = S.user.id; let m = meta(), row;
      try{ row = await getRow(); }catch(e){ if(e.net || e.http >= 500){ setStatus('offline'); retryMs = 5000; schedule(5000); return; } throw e; }
      if(m.owner !== uid){
        if(m.owner && m.owner !== 'guest'){
          /* بيانات حساب آخر على الجهاز: تغييراته المعلقة تُركن باسم صاحبها فقط (لا يعتمدها حساب آخر) ثم يبدأ هذا الحساب نظيفاً */
          if(m.dirty){ wr(K_STASH + m.owner, JSON.stringify({ data:rd(STORE_KEY), meta:m })); }
          rm(STORE_KEY); try{ await CodisLocalDB.del('work'); }catch(e){} data = loadData(); m = { owner:'guest', base:0, dirty:false, lastSync:0, changedAt:0 }; saveMeta(m);
          reloadGuarded(); return;
        }
        /* بيانات ضيف (أو فارغة) → هذا الحساب: دمج آمن تلقائي بلا سؤال. نسخة احتياطية تبقى حتى يتأكد نجاح الترحيل */
        const own = stashRead(uid), guestHas = hasProgress(data);
        let remoteSide = row;
        if(own && own.data){ const od = typeof own.data === 'string' ? jparse(own.data, null) : own.data; if(od){ remoteSide = row ? { version:row.version, updated_at:row.updated_at, data:CodisMerge.merge(null, od, row.data || {}, { localNewer:true }) } : { version:0, data:od }; } }
        if(guestHas){
          backupLocal('guest_before_account', rd(STORE_KEY) || '');
          if(remoteSide && (remoteSide.version > 0 || row || own)){ rm(K_STASH + uid); S.reconciling = false; await mergeAndAdopt(remoteSide, snapshot(), 'guest_before_merge'); return; }
          saveMeta({ owner:uid, base:0, dirty:true, lastSync:0, changedAt:Date.now() });   // حساب جديد: يُرفع تقدّمك الحالي كما هو
        } else if(remoteSide && (row || own)){
          rm(K_STASH + uid);
          if(row && !own){ S.reconciling = false; await applyRemote(row); return; }
          S.reconciling = false; await mergeAndAdopt(remoteSide, snapshot(), 'stash_before_merge'); return;
        } else { saveMeta({ owner:uid, base:0, dirty:true, lastSync:0, changedAt:Date.now() }); }
      } else {
        if(!row){ m.base = 0; m.dirty = true; saveMeta(m); }
        else if(row.version > m.base){
          if(!m.dirty){ S.reconciling = false; await applyRemote(row); return; }
          S.reconciling = false; await mergeAndAdopt({ version:row.version, data:row.data, updated_at:row.updated_at }, null, 'before_merge'); return;
        } else if(row.version < m.base){ m.base = row.version; m.dirty = true; saveMeta(m); }
      }
      sessionStorage.removeItem('codis_reload_n');
    } catch(e){ netFail(e); return; }
    finally{ S.reconciling = false; }
    const m3 = meta(); if(m3.dirty) await push(); else { m3.lastSync = Date.now(); saveMeta(m3); setStatus('synced'); try{ CodisPush.resync(); }catch(e){} }
  }

""", 'sync core')

# إزالة askChoice
rep("  const askChoice = o => codisConfirm(Object.assign({ danger:false, icon:'info' }, o));\n", "", 'askChoice removed') if "const askChoice = o => codisConfirm" in s else None

# Background Sync + إشعار التغيير
rep("""    if(configured && S.user && m.owner === S.user.id && !S.reconciling){ setStatus(navigator.onLine === false ? 'offline' : 'pending'); schedule(2500); }
  }""", """    if(configured && S.user && m.owner === S.user.id && !S.reconciling){ setStatus(navigator.onLine === false ? 'offline' : 'pending'); schedule(2500); bgSync(); }
  }
  /* Background Sync حيث يُدعم: يوقظ الصفحة (إن بقيت حيّة) لتُكمل الرفع فور عودة الاتصال؛ غير ذلك يعتمد على online/visibility/focus */
  let bgAt = 0;
  function bgSync(){
    if(Date.now() - bgAt < 30000) return; bgAt = Date.now();
    try{ if('serviceWorker' in navigator && navigator.serviceWorker.ready) navigator.serviceWorker.ready.then(r=>{ if(r && r.sync && r.sync.register) return r.sync.register('codis-sync'); }).catch(()=>{}); }catch(e){}
  }""", 'noteChange bg')

# تسجيل الخروج: بلا نافذة، التغييرات المعلقة تُركن باسم المالك
between("      if(m.owner === S.user.id && m.dirty){\n        const go = await codisConfirm({ title:'تغييرات غير مزامَنة'", "      try{ const lo = await raw('/auth/v1/logout?scope=local'", """      if(m.owner === S.user.id && m.dirty){
        /* CODIS-OFFLINE: لا فقد ولا نسخة بديلة — التغييرات غير المرفوعة تُركن باسم صاحبها فقط وتُدمج تلقائياً عند دخوله مجدداً */
        wr(K_STASH + S.user.id, JSON.stringify({ data:rd(STORE_KEY), meta:m }));
        try{ showToast('تغييراتك غير المرفوعة محفوظة وتُدمج تلقائياً عند دخولك مجدداً', 'var(--text-2)'); }catch(e){}
      }
""", 'signout')
rep("      rm(STORE_KEY); rm(K_SESSION); rm(K_GUEST); rm(K_PKCE); saveMeta({ owner:'guest', base:0, dirty:false, lastSync:0, changedAt:0 });\n      codisSaveSuspended = true; location.reload();",
    "      rm(STORE_KEY); rm(K_SESSION); rm(K_GUEST); rm(K_PKCE); saveMeta({ owner:'guest', base:0, dirty:false, lastSync:0, changedAt:0 });\n      try{ await CodisLocalDB.del('work'); }catch(e){}   /* المرآة المحلية تخص الحساب الخارج فقط */\n      codisSaveSuspended = true; location.reload();", 'signout wipe')
rep("      const uid = S.user.id; rm(K_STASH + uid);\n      if(opt && opt.wipeLocal){ wipeAppKeys(); }",
    "      const uid = S.user.id; rm(K_STASH + uid); try{ await CodisLocalDB.del(baseKey(uid)); await CodisLocalDB.del('work'); }catch(e){}\n      if(opt && opt.wipeLocal){ wipeAppKeys(); }", 'delete acct')

# مشغّلات المزامنة التلقائية
rep("""    window.addEventListener('online', () => { if(S.user){ if(meta().owner === S.user.id && meta().dirty) schedule(300); else if(!S.reconciling) reconcile(); } });
    document.addEventListener('visibilitychange', () => { if(!document.hidden && S.user && !S.reconciling && !pushing){ const m = meta(); if(m.owner === S.user.id && m.dirty) schedule(300); } });""",
"""    /* CODIS-OFFLINE: مشغّلات المزامنة التلقائية. navigator.onLine لا يُعتمد عليه وحده — نجاح الاتصال الفعلي (طلب save_progress/getRow) هو الدليل، والفشل يُعاد بتدرّج */
    let lastPull = 0;
    const resume = () => {
      if(!S.user || S.reconciling || pushing || window.CODIS_SYNC_HOLD) return;
      const m = meta();
      if(m.owner === S.user.id && m.dirty){ schedule(200); return; }
      if(Date.now() - lastPull > 15000){ lastPull = Date.now(); reconcile(); }
    };
    window.addEventListener('online', () => { retryMs = 0; lastPull = 0; resume(); });
    window.addEventListener('focus', resume);
    window.addEventListener('pageshow', resume);
    document.addEventListener('visibilitychange', () => { if(!document.hidden) resume(); });
    try{ if('serviceWorker' in navigator) navigator.serviceWorker.addEventListener('message', ev => { if(ev && ev.data && ev.data.type === 'codis-sync'){ retryMs = 0; lastPull = 0; resume(); } }); }catch(e){}""", 'init triggers')

rep("meta, isAdmin:() => adminOK === true, _test:{", "meta, isAdmin:() => adminOK === true, _test:{ merge:CodisMerge.merge, loadBase, saveBase, mergeAndAdopt,", 'return exports')

# =====================================================================
# 5) الإشعارات: حالة دقيقة + إعادة جدولة
# =====================================================================
rep("  function all_pending(){ try{ CodisTimers.all().filter(t=>t.state === 'running' && !t.server).forEach(schedule); }catch(e){} }",
    """  function all_pending(){ try{ CodisTimers.all().filter(t=>t.state === 'running' && !t.server).forEach(schedule); }catch(e){} }
  /* حالة دقيقة بدل وعد مضلِّل: ما الذي ينقص لتصل الإشعارات والتطبيق مسكّر؟ */
  function status(){
    if(!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) return { ok:false, code:'unsupported', msg:unsupportedText() };
    if(ios() && !standalone()) return { ok:false, code:'ios-install', msg:unsupportedText() };
    if(!signedIn()) return { ok:false, code:'signin', msg:'سجّل الدخول بحسابك أول حتى يربط الخادم إشعارات هذا الجهاز بحسابك.' };
    if(!vapid()) return { ok:false, code:'no-vapid', msg:'إشعارات الخلفية غير مهيّأة على الخادم بعد (مفتاح VAPID العام فارغ) — تصلك التنبيهات والتطبيق مفتوح فقط إلى أن يُضبط الخادم (راجع docs/CODIS_PUSH_SETUP.md).' };
    if(Notification.permission === 'denied') return { ok:false, code:'denied', msg:'الإذن مرفوض من إعدادات المتصفح — فعّله من إعدادات الموقع.' };
    return { ok:true, code:'ready', msg:'' };
  }""", 'push status')
rep("return { show:show, enable:enable, schedule:schedule,", "return { show:show, enable:enable, status:status, resync:all_pending, schedule:schedule,", 'push exports')
rep("""      CodisPush.enable().then(r=>{ showToast(r.ok ? 'انفعلت الإشعارات على هذا الجهاز' + (r.push ? ' — وتوصل حتى لو التطبيق مسكّر' : '') : 'انفعلت إشعارات الجهاز', 'var(--success)', 'check'); });""",
    """      CodisPush.enable().then(r=>{
        if(r.push) showToast('انفعلت الإشعارات على هذا الجهاز — وتوصل حتى لو التطبيق مسكّر', 'var(--success)', 'check');
        else { const st = CodisPush.status(); showToast('انفعلت إشعارات الجهاز' + (st.ok ? '' : ' (والتطبيق مفتوح فقط): ' + st.msg), st.ok ? 'var(--success)' : 'var(--warning)', st.ok ? 'check' : undefined); }
      });""", 'push toast')

rep("  window.addEventListener('load', ()=>{ setTimeout(()=>{ registration(); try{ CodisTimers.tick(); }catch(e){} }, 300); });",
    """  window.addEventListener('load', ()=>{ setTimeout(()=>{ registration(); try{ CodisTimers.tick(); }catch(e){} }, 300); });
  /* CODIS-OFFLINE: المتصفح بدّل/أنهى اشتراك Push ← نعيد الاشتراك من الصفحة (تملك المفتاح العام وجلسة الحساب) إن كانت الإشعارات مفعّلة */
  try{ if('serviceWorker' in navigator) navigator.serviceWorker.addEventListener('message', ev=>{ if(ev && ev.data && ev.data.type === 'codis-push-resub'){ try{ if(localStorage.getItem(LS) === '1') enable(); }catch(e){} } }); }catch(e){}""", 'push resub')

# =====================================================================
# 6) CSS
# =====================================================================
css = r"""
/* CODIS-OFFLINE */
.st-tile .shop-acts .own-use.own-go{ order:-1; font-weight:800; }
.st-tile .shop-acts .own-use.own-go svg{ width:15px; height:15px; }
.st-tile .shop-acts .own-sell{ font-weight:600; opacity:.92; }
.st-tile .shop-acts .tmr-chip.is-run{ order:-1; }
.acct-sync.is-pending .acct-dot, .acct-sync.is-offline .acct-dot{ background:var(--warning); }
.acct-sync.is-expired .acct-dot, .acct-sync.is-error .acct-dot{ background:var(--danger); }
"""
rep("</style>", css + "</style>", 'css')
rep("<!-- CODIS-STICKERS -->", "<!-- CODIS-STICKERS -->\n<!-- CODIS-OFFLINE -->", 'marker')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v20 OK')
