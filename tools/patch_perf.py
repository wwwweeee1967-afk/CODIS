"""CODIS-PERF: navigation/store-layer coherence, deferred store render, real startup readiness bar, independent Sold/Used unread badges,
multi-pouch use (atomic) and expired holiday-card dismantle (flat 25 silver). Run AFTER tools/patch_dev.py:  python tools/patch_perf.py <in> <out>"""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-PERF' not in t, 'perf patch already applied'
assert 'CODIS-SYNC-HOLD' in t, 'run tools/patch_dev.py first'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

# ================= 1) one coherent active view (room | settings | store) =================
rep("function navigateToPage(page){\n  const target = document.querySelector(`.navbtn[data-page=\"${page}\"]`);\n  if(!target) return;\n",
    "function navigateToPage(page){\n  const target = document.querySelector(`.navbtn[data-page=\"${page}\"]`);\n  if(!target) return;\n"
    "  if(econStoreSaved) econCloseStore({ silent:true });   /* CODIS-PERF: طبقة المتجر/السجل لا تبقى فوق غرفة أخرى */\n")
rep("  } finally {\n    CodisMotion.navEnd(mo);", "  } finally {\n    codisSyncView();\n    CodisMotion.navEnd(mo);")
rep("let econStoreSaved = null;\n", """let econStoreSaved = null;
/* CODIS-PERF: حالة العرض الوحيدة على <html data-view="room|settings|store"> — تتحكم بإخفاء الشريط العلوي (الإعدادات) والشريط السفلي (المتجر) */
function codisSyncView(){
  const act = document.querySelector('.navbtn.active'), page = act ? act.dataset.page : '';
  document.documentElement.setAttribute('data-view', econStoreSaved ? 'store' : (page === 'settings' ? 'settings' : 'room'));
}
/* رسم المتجر بعد أول لوحة: الطبقة تظهر فوراً والمحتوى يلحق بها؛ الرمز يُبطل أي رسم متأخر إذا أُغلقت الطبقة أو فُتحت أخرى */
let econRenderTok = 0;
function econDeferRender(secId, render){
  const tok = ++econRenderTok; let done = false;
  const run = ()=>{
    if(done) return; done = true;
    if(tok !== econRenderTok || !econStoreSaved || econStoreSaved.secId !== secId) return;
    try{ render(); }catch(e){ console.error('CODIS store render:', e); }
  };
  if(window.requestAnimationFrame) requestAnimationFrame(()=>setTimeout(run, 0));
  setTimeout(run, 90);
}
""")
rep("sec.style.display = 'block'; render();", "sec.style.display = 'block'; codisSyncView(); econDeferRender(secId, render);")
rep("function econCloseStore(){\n  const st = econStoreSaved; if(!st) return;\n", "function econCloseStore(opts){\n  const st = econStoreSaved; if(!st) return;\n  const quiet = !!(opts && opts.silent);\n  econRenderTok++;\n")
rep("  codisSfx('close');\n  if(sec) sec.style.display = 'none';", "  if(!quiet) codisSfx('close');\n  if(sec) sec.style.display = 'none';")
rep("if(mainEl) mainEl.scrollTop = st.scroll;", "if(mainEl) mainEl.scrollTop = st.scroll;\n  codisSyncView();")
rep("  if(st.opener && st.opener.focus && document.contains(st.opener)){", "  if(!quiet && st.opener && st.opener.focus && document.contains(st.opener)){")
rep("    step('route', function(){ if(currentPlanActive()) navigateToPage('tasks'); });",
    "    step('route', function(){ if(currentPlanActive()) navigateToPage('tasks'); });\n    step('view', codisSyncView);")

rep("/* ===================== ZOOM LOCK", """/* CODIS-PERF: الإعدادات بلا شريط علوي (الجرس/المتجر/الرصيد/الشعار) والمتجر بلا شريط سفلي؛ الفراغ العلوي يتقلّص تلقائياً عبر --pad-top */
html[data-view="settings"] .topbar-fade, html[data-view="settings"] .topbar-mark, html[data-view="settings"] .notif-bell,
html[data-view="settings"] .store-btn, html[data-view="settings"] .coin-chip{ opacity:0; visibility:hidden; pointer-events:none; }
html[data-view="settings"] .main{ --pad-top:calc(var(--safe-t) + 18px); }
html[data-view="store"] .sidebar{ opacity:0; visibility:hidden; pointer-events:none; transform:translateY(18px); }
.eco-ctabs{ display:flex; gap:8px; margin-bottom:12px; }
.eco-ctab{ flex:1; min-height:44px; display:inline-flex; align-items:center; justify-content:center; gap:8px; border-radius:12px; border:1px solid var(--glass-border); background:var(--glass); color:var(--text-2); font:inherit; font-weight:600; cursor:pointer; }
.eco-ctab.is-on{ background:var(--glass-strong); color:var(--text); border-color:var(--aqua); }
.eco-ctab-n{ position:static; }
.cs-bar{ width:min(180px,calc(46 * var(--vw))); height:3px; margin-top:16px; border-radius:2px; background:rgb(var(--aqua-rgb) / .16); overflow:hidden; direction:rtl; opacity:0; animation:csText calc(340ms * var(--k)) var(--ease) calc(500ms * var(--k)) forwards; }
.cs-bar i{ display:block; width:100%; height:100%; background:var(--aqua); transform:scaleX(var(--p,0)); transform-origin:right center; transition:transform 180ms var(--ease); }
.cs-bar[data-state="warn"] i{ background:var(--gold); }
@media (prefers-reduced-motion:reduce){ .cs-bar{ opacity:1; animation:none; } .cs-bar i{ transition:none; } }

/* ===================== ZOOM LOCK""")

# ================= 2) real startup readiness bar =================
rep('  <div class="cs-line" aria-hidden="true"></div>\n',
    '  <div class="cs-line" aria-hidden="true"></div>\n  <div class="cs-bar" id="cs-bar" role="progressbar" aria-label="تقدّم تجهيز التطبيق" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>\n')
rep("  window.codisReveal = function(){\n",
    """  /* CODIS-PERF: التقدّم يُحسب من مراحل التجهيز الفعلية (codisBoot) لا من مؤقّت؛ warn = فشلت مرحلة وسُجّل الخطأ والتطبيق يكمل */
  window.codisBootProgress = function(p, warn){
    var b = document.getElementById('cs-bar'); if(!b || !b.firstElementChild) return;
    p = Math.max(0, Math.min(1, +p || 0));
    b.firstElementChild.style.setProperty('--p', p);
    b.setAttribute('aria-valuenow', String(Math.round(p * 100)));
    if(warn) b.setAttribute('data-state', 'warn');
  };
  window.codisReveal = function(){
""")
rep("    Math.max(0, window.CODIS_BOOT_DURATION - window.getCodisExitDuration() - performance.now())\n  );",
    "    Math.max(0, 5000 - performance.now())   /* CODIS-PERF: شبكة أمان فقط (الإقلاع الطبيعي يكشف عند الجاهزية) */\n  );")
rep("function codisBoot(){\n  function step(label, fn){\n    try{ fn(); }\n    catch(err){ console.error('CODIS init error ('+label+'):', err); }\n  }",
    "function codisBoot(){\n  const TOTAL = 12; let done = 0, failed = 0;   /* 11 مرحلة تجهيز + انتظار الخطوط */\n"
    "  function step(label, fn){\n    try{ fn(); }\n    catch(err){ failed++; console.error('CODIS init error ('+label+'):', err); }\n"
    "    done++; if(window.codisBootProgress) window.codisBootProgress(done / TOTAL, failed > 0);\n  }")
rep("    window.clearTimeout(codisStartupTimer);\n    const revealAt = window.CODIS_BOOT_DURATION - window.getCodisExitDuration();\n    const remaining = Math.max(0, revealAt - performance.now());\n    codisStartupTimer = window.setTimeout(window.codisReveal, remaining);\n    window.setTimeout(function(){ econUiReady = true;",
    "    const fontsReady = (document.fonts && document.fonts.ready) ? Promise.race([document.fonts.ready, new Promise(function(r){ setTimeout(r, 2500); })]) : Promise.resolve();\n"
    "    fontsReady.catch(function(){}).then(function(){\n    if(window.codisBootProgress) window.codisBootProgress(1, failed > 0);\n"
    "    window.clearTimeout(codisStartupTimer);\n    const revealAt = window.CODIS_BOOT_DURATION - window.getCodisExitDuration();\n    const remaining = Math.max(0, revealAt - performance.now());\n    codisStartupTimer = window.setTimeout(window.codisReveal, remaining);\n    window.setTimeout(function(){ econUiReady = true;")
rep("}, remaining + 900);", "}, remaining + 900);\n    });")

# ================= 3) Sold / Used: independent unread badges =================
rep("  d.holidayCardLog = holidayNormalizeLog(d.holidayCardLog);",
    "  { const cs = d.closedSeen, nowI = new Date().toISOString(), okT = x=>typeof x === 'string' && !isNaN(Date.parse(x)); d.closedSeen = { sold:(cs && okT(cs.sold)) ? cs.sold : nowI, used:(cs && okT(cs.used)) ? cs.used : nowI }; }   /* CODIS-PERF: آخر مشاهدة لكل عرض (المباعة/المستخدمة) */\n"
    "  d.holidayCardLog = holidayNormalizeLog(d.holidayCardLog);")
a = t.index("function econClosedCount(){")
b0 = t.index("function econToggleClosed(){")
b = t.index("\n", b0) + 1
NEW_CLOSED = r"""/* CODIS-PERF: المباعة والمستخدمة عرضان مستقلان؛ لكل منهما عدّاد «غير مقروء» (سجلات أحدث من آخر مشاهدة data.closedSeen[العرض]) يُصفَّر بفتح عرضه فقط. السجل نفسه لا يُحذف */
let econClosedView = 'used';
function econClosedRows(){
  const rows = [];
  CodisInventory.closed().forEach(it=>{
    const sold = it.status === 'sold';
    rows.push({ k:sold ? 'sold' : 'used', t:it.statusAt, html:'<div class="eco-log-row"><b class="' + (sold ? 'eco-up' : '') + '">' + (sold ? '+' + econFmt(it.soldFor) : ICONS.check) + '</b><div class="eco-log-main"><span class="eco-log-reason">' + escapeHtml(it.name) + '</span>' +
      '<span class="eco-log-sub">' + (sold ? 'بيعت' : 'استُخدمت') + ' · ' + escapeHtml(it.rarityName) + ' · ' + escapeHtml(formatArDate(it.statusAt)) + '</span></div></div>' });
  });
  CodisPasses.used().forEach(p=>rows.push({ k:'used', t:p.usedAt, html:'<div class="eco-log-row"><b class="eco-log-ico">' + ICONS.check + '</b><div class="eco-log-main"><span class="eco-log-reason">' + escapeHtml(CodisPasses.label(p)) + '</span>' +
    '<span class="eco-log-sub">استُخدمت' + (p.usedForName ? ' لتجاوز «' + escapeHtml(p.usedForName) + '»' : '') + ' · بطاقة تجاوز · ' + escapeHtml(formatArDate(p.usedAt)) + '</span></div></div>' }));
  hcdClosedRows().forEach(r=>{ r.k = 'used'; rows.push(r); }); econSilverRows().forEach(r=>{ r.k = 'used'; rows.push(r); });
  return rows;
}
function econClosedSeenObj(){
  const cs = data.closedSeen;
  if(!cs || typeof cs !== 'object' || Array.isArray(cs)) data.closedSeen = { sold:econNowIso(), used:econNowIso() };
  if(typeof data.closedSeen.sold !== 'string') data.closedSeen.sold = econNowIso();
  if(typeof data.closedSeen.used !== 'string') data.closedSeen.used = econNowIso();
  return data.closedSeen;
}
function econClosedUnread(rows){
  const sn = econClosedSeenObj(), u = { sold:0, used:0 };
  (rows || econClosedRows()).forEach(r=>{ if(r.t && r.t > sn[r.k]) u[r.k]++; });
  return u;
}
function econClosedMarkSeen(view){
  const rows = econClosedRows();
  if(!(econClosedUnread(rows)[view] > 0)) return;
  let mx = econNowIso(); rows.forEach(r=>{ if(r.k === view && r.t && r.t > mx) mx = r.t; });
  econClosedSeenObj()[view] = mx; saveData();
}
function econClosedCount(){ const u = econClosedUnread(); return u.sold + u.used; }
function econClosedPanelHtml(){
  const rows = econClosedRows(), u = econClosedUnread(rows), v = econClosedView;
  const list = rows.filter(r=>r.k === v).sort((a, b)=>a.t < b.t ? 1 : a.t > b.t ? -1 : 0);
  const tab = (id, label)=>'<button type="button" role="tab" class="eco-ctab' + (v === id ? ' is-on' : '') + '" aria-selected="' + (v === id ? 'true' : 'false') + '" onclick="econClosedSetView(\'' + id + '\')">' + label +
    (u[id] ? '<span class="eco-hist-n eco-ctab-n" aria-label="' + escapeHtml(econFmt(u[id]) + ' غير مقروء') + '">' + econFmt(u[id]) + '</span>' : '') + '</button>';
  return '<div class="settings-card eco-closed" id="eco-closed-panel"><div class="eco-ctabs" role="tablist" aria-label="المباعة والمستخدمة">' + tab('sold', 'المباعة') + tab('used', 'المستخدمة') + '</div>' +
    '<div class="eco-sec-title">' + (v === 'sold' ? 'المباعة' : 'المستخدمة') + ' (' + econFmt(list.length) + ')</div>' +
    (list.length ? '<div class="ios-list eco-log" role="tabpanel">' + list.slice(0, 60).map(r=>r.html).join('') + '</div>' : '<div class="eco-empty">' + (v === 'sold' ? 'ما في مكافآت مباعة بعد' : 'ما في مكافآت مستخدمة بعد') + '</div>') +
    (v === 'used' ? hcdTaskLogHtml() : '') + '</div>';
}
function econToggleClosed(){
  econClosedOpen = !econClosedOpen;
  if(econClosedOpen){ const u = econClosedUnread(); econClosedView = (u.sold > 0 && u.used === 0) ? 'sold' : (u.used > 0 ? 'used' : econClosedView); }
  codisSfx(econClosedOpen ? 'open' : 'close'); econRenderStore();
}
function econClosedSetView(v){ if(v !== 'sold' && v !== 'used') return; econClosedView = v; codisSfx('press'); econRenderStore(); }
"""
t = t[:a] + NEW_CLOSED + t[b:]
rep("  const nClosed = econClosedCount(), bal = data.wallet.balance,", "  if(econClosedOpen) econClosedMarkSeen(econClosedView);   /* CODIS-PERF: العرض المفتوح يُعدّ مقروءاً */\n  const nClosed = econClosedCount(), bal = data.wallet.balance,")

# ================= 4) multi-pouch use =================
rep("  return { defs:()=>DEFS.slice(), def, get, owned, used, all, value, prizes, grant, use };",
"""  /* استخدام n كيساً بمعاملة واحدة ذرّية: كل كيس يسحب مبلغه العشوائي ويُسجَّل بمرجع pouch|uid (لا تكرار)، وأي فشل يُرجع كل شيء كما كان. CODIS-PERF */
  function useMany(type, n){
    const d = def(type); n = Math.trunc(Number(n));
    if(!d || !(n >= 1) || n > 100) return { ok:false, reason:'invalid' };
    if(owned(d.type).length < n) return { ok:false, reason:'notowned' };
    const amounts = [];
    for(let i = 0; i < n; i++){ const a = CodisRewardEngine.pick(d.rewards, ()=>1); if(d.rewards.indexOf(a) === -1) return { ok:false, reason:'failed' }; amounts.push(a); }
    return CodisWallet.transact([], ()=>{
      const ps = owned(d.type).slice(0, n); if(ps.length < n) return { ok:false, reason:'notowned' };
      let total = 0; const items = [];
      for(let i = 0; i < n; i++){
        const p = ps[i]; if(p.status !== 'owned') return { ok:false, reason:'notowned' };
        p.status = 'used'; p.usedAt = econNowIso(); p.silver = amounts[i];
        const tx = CodisWallet.applySilver('OPEN_POUCH', amounts[i], 'فتح ' + d.name, 'inventory', 'pouch|' + p.uid, { name:d.name, pouch:d.type, uid:p.uid });
        if(!tx) return { ok:false, reason:'tx' };
        total += amounts[i]; items.push({ uid:p.uid, amount:amounts[i], tx:tx });
      }
      return { ok:true, def:d, count:n, amount:total, items:items };
    });
  }
  return { defs:()=>DEFS.slice(), def, get, owned, used, all, value, prizes, grant, use, useMany };""")

rep("function econPouchUse(type){\n  if(econSilverBusy || dqState) return;\n",
"""function econPouchUse(type){
  if(econSilverBusy || dqState) return;
  { const have = CodisPouches.owned(type).length; if(have > 1 && econPouchSheet(type, have)) return; }   /* CODIS-PERF: أكثر من كيس ← اختيار العدد ثم تأكيد */
""")
rep("/* ---- 3) فتح الكيس: العملية الفعلية أولاً",
r"""/* CODIS-PERF: اختيار عدد الأكياس. المبلغ عشوائي لكل كيس فيُعرض المجال المحتمل للمجموع قبل التأكيد، والمبلغ الفعلي بعد الفتح */
function econPouchSheet(type, have){
  const d = CodisPouches.def(type), ov = dqOv(), b = dqBody(); if(!d || !ov || !b) return false;
  const lo = Math.min.apply(null, d.rewards), hi = Math.max.apply(null, d.rewards);
  const s = dqState = { mode:'qty', kind:'pouch', type:d.type, ref:'', name:d.name, uids:[], max:Math.min(have, 100), n:1, lo:lo, hi:hi, busy:false, lock:false, done:false, closing:false, fxLive:false, timers:[], anims:[], at:Date.now() };
  dqPrevFocus = document.activeElement;
  b.innerHTML =
    '<h3 class="dq-title" id="dq-title">' + escapeHtml(d.name) + '</h3>' +
    '<p class="dq-sub">لديك <b>' + escapeHtml(econFmt(have)) + '</b> من هذا النوع</p>' +
    '<div class="dq-stage is-qty" id="dq-stage"><div class="pch-art is-big">' + econPouchSvg(d.type) + '</div><span class="dq-badge" id="dq-badge" dir="ltr" hidden></span></div>' +
    '<div class="dq-count" aria-live="polite"><span class="dq-count-lab">عدد الأكياس</span><b class="dq-count-n" id="dq-n" dir="ltr">1</b><span class="dq-count-of" id="dq-of"></span></div>' +
    '<div class="dq-steps" role="group" aria-label="تغيير عدد الأكياس">' +
      '<button type="button" class="btn btn-secondary dq-step" id="dq-b-m1" onclick="dqSub()" aria-label="إنقاص كيس واحد"><span dir="ltr">−1</span></button>' +
      '<button type="button" class="btn btn-secondary dq-step" id="dq-b-p1" onclick="dqAdd(1)" aria-label="زيادة كيس واحد"><span dir="ltr">+1</span></button>' +
      '<button type="button" class="btn btn-secondary dq-step" id="dq-b-p10" onclick="dqAdd(10)" aria-label="زيادة عشرة أكياس"><span dir="ltr">+10</span></button>' +
      '<button type="button" class="btn btn-secondary dq-step" id="dq-b-max" onclick="dqMax()" aria-label="تحديد كل الأكياس">الكل</button>' +
    '</div>' +
    '<dl class="dq-rows"><div><dt>مكافأة الكيس الواحد (عشوائية)</dt><dd id="dq-unit"></dd></div><div class="is-key"><dt>مجموع الفضة المحتمل</dt><dd id="dq-sum"></dd></div></dl>' +
    '<p class="dq-warn">المبلغ الفعلي يُسحب عشوائياً لكل كيس ويظهر بعد الفتح. لا يمكن التراجع.</p>' +
    '<div class="modal-actions"><button type="button" class="btn btn-primary" id="dq-ok" onclick="dqConfirm()">افتح</button><button type="button" class="btn btn-secondary" id="dq-cancel" onclick="dqCancel()">إلغاء</button></div>';
  ov.setAttribute('aria-hidden', 'false');
  pqSync(s);
  codisSfx('open'); CodisMotion.modalIn(ov);
  setTimeout(()=>{ const ok = document.getElementById('dq-ok'); if(ok && dqState === s && s.mode === 'qty'){ try{ ok.focus({ preventScroll:true }); }catch(e){} } }, 60);
  return true;
}
function pqSync(s){
  const set = (id, h)=>{ const e = document.getElementById(id); if(e) e.innerHTML = h; };
  const dis = (id, v)=>{ const e = document.getElementById(id); if(e){ e.disabled = !!v; if(v) e.setAttribute('aria-disabled', 'true'); else e.removeAttribute('aria-disabled'); } };
  const rng = (n)=>s.lo === s.hi ? econFmt(s.lo * n) : econFmt(s.lo * n) + ' – ' + econFmt(s.hi * n);
  set('dq-n', econFmt(s.n)); set('dq-of', 'من أصل ' + econFmt(s.max));
  set('dq-unit', rng(1) + ' فضة'); set('dq-sum', rng(s.n) + ' فضة');
  const ok = document.getElementById('dq-ok');
  if(ok){ ok.textContent = 'افتح ' + econFmt(s.n); ok.disabled = !!s.busy; ok.setAttribute('aria-label', 'فتح ' + econFmt(s.n) + ' من ' + s.name + ' — مجموع محتمل ' + rng(s.n) + ' فضة'); }
  const atMax = s.n >= s.max; dis('dq-b-m1', s.n <= 1); dis('dq-b-p1', atMax); dis('dq-b-p10', atMax); dis('dq-b-max', atMax);
  const bd = document.getElementById('dq-badge'); if(bd){ bd.hidden = s.n < 2; bd.textContent = '×' + econFmt(s.n); }
  const ae = document.activeElement; if(ae && ae.disabled && ok && !ok.disabled){ try{ ok.focus({ preventScroll:true }); }catch(e){} }
}
function pqConfirm(s){
  if(s.busy || s.closing || econSilverBusy) return;
  s.busy = true; s.lock = true; econSilverBusy = true;
  const okb = document.getElementById('dq-ok'); if(okb) okb.disabled = true;
  const before = CodisWallet.silverBalance();
  const r = CodisPouches.useMany(s.type, s.n);
  if(!r.ok){ codisSfx('invalid'); showToast(r.reason === 'save' ? 'تعذّر الحفظ — بقيت الأكياس كما هي' : (r.reason === 'notowned' ? 'تغيّر مخزونك — ما تكفي الأكياس للعدد المحدد' : 'تعذّر فتح الأكياس'), 'var(--warning)'); dqEnd(); return; }
  const after = CodisWallet.silverBalance(), added = after - before;
  if(added !== r.amount) console.error('CODIS DQ: مجموع الأكياس المسحوب يختلف عن المضاف فعلاً', r.amount, added);
  s.res = { type:r.def.type, name:r.def.name, count:r.count, silver:added, before:before, after:after };
  s.mode = 'fx'; s.fxLive = true; s.at = Date.now(); s.timers = []; s.anims = [];
  codisSfx('confirm'); dqPlay();
}
/* ---- 3) فتح الكيس: العملية الفعلية أولاً""")
rep("function dqSync(){\n  const s = dqState; if(!s || s.mode !== 'qty') return;\n", "function dqSync(){\n  const s = dqState; if(!s || s.mode !== 'qty') return;\n  if(s.kind === 'pouch') return pqSync(s);\n")
rep("function dqConfirm(){\n  const s = dqState; if(!s || s.mode !== 'qty' || s.busy || s.closing || econSilverBusy) return;\n",
    "function dqConfirm(){\n  const s = dqState; if(!s || s.mode !== 'qty' || s.busy || s.closing || econSilverBusy) return;\n  if(s.kind === 'pouch') return pqConfirm(s);\n")
rep("(pouch ? 'حصلت من الكيس على' :", "(pouch ? (s.res.count > 1 ? 'حصلت من ' + econFmt(s.res.count) + ' أكياس على' : 'حصلت من الكيس على') :")
rep("econPouchSvg(s.res.type) + '</div>'", "econPouchSvg(s.res.type) + '</div>' + (s.res.count > 1 ? '<span class=\"dq-badge\" dir=\"ltr\">×' + econFmt(s.res.count) + '</span>' : '')")

# ================= 5) expired holiday cards: dismantle for exactly 25 silver =================
rep("  const RATE = 1.5;\n", "  const RATE = 1.5, EXPIRED_SILVER = 25;   /* CODIS-PERF: البطاقة المنتهية تُفكَّك بـ25 فضة ثابتة */\n")
rep("""    if(kind === 'holiday'){ const c = CodisHolidayCards.get(uid), d = c ? CodisHolidayCards.def(c.kind) : null; return (c && d && CodisHolidayCards.isUsable(c)) ? { rec:c, name:d.name, gold:CodisHolidayCards.price(c.kind), list:()=>data.inventory.holidayCards } : null; }""",
"""    if(kind === 'holiday'){
      const H = CodisHolidayCards, c = H.get(uid), d = c ? H.def(c.kind) : null; if(!c || !d) return null;
      if(H.isUsable(c)) return { rec:c, name:d.name, gold:H.price(c.kind), list:()=>data.inventory.holidayCards };
      if(c.status === 'expired' || (c.status === 'owned' && H.timeExpired(c))) return { rec:c, name:d.name, gold:0, fixed:EXPIRED_SILVER, expired:true, list:()=>data.inventory.holidayCards };
      return null;
    }""")
rep("const s = reward(t.gold); return s > 0 ? { ok:true, name:t.name, gold:t.gold, silver:s } : { ok:false, reason:'ineligible' }; }",
    "const s = t.fixed || reward(t.gold); return s > 0 ? { ok:true, name:t.name, gold:t.gold, silver:s, expired:!!t.expired } : { ok:false, reason:'ineligible' }; }")
rep("const s = reward(t.gold), arr = t.list(), i = arr.indexOf(t.rec);", "const s = t.fixed || reward(t.gold), arr = t.list(), i = arr.indexOf(t.rec);")
rep("const s = reward(t.gold), arr = t.list(), at = arr.indexOf(t.rec);", "const s = t.fixed || reward(t.gold), arr = t.list(), at = arr.indexOf(t.rec);")
rep("    else { const H = CodisHolidayCards, d = H.def(t.rec.kind); list = (d && d.ui && d.ui.stack)",
    "    else if(t.expired){ list = CodisHolidayCards.expired().filter(x=>x.kind === t.rec.kind); }\n    else { const H = CodisHolidayCards, d = H.def(t.rec.kind); list = (d && d.ui && d.ui.stack)")
rep("return { ok:true, kind:kind, uids:list.map(x=>x.uid), name:pv.name, gold:pv.gold, silver:pv.silver };", "return { ok:true, kind:kind, uids:list.map(x=>x.uid), name:pv.name, gold:pv.gold, silver:pv.silver, expired:!!t.expired };")
rep("return { RATE, reward, preview, dismantle, group, previewMany, dismantleMany };", "return { RATE, EXPIRED_SILVER, reward, preview, dismantle, group, previewMany, dismantleMany };")
rep("function econDismBtn(kind, uid, gold){ const s = CodisDismantle.reward(gold);", "function econDismBtn(kind, uid, gold, fixed){ const s = fixed || CodisDismantle.reward(gold);")
rep("""        : '<button type="button" class="btn btn-secondary own-use hcd-use" disabled aria-disabled="true">منتهية</button>') + '</div></div>';""",
    """        : econDismBtn('holiday', c.uid, 0, CodisDismantle.EXPIRED_SILVER)) + '</div></div>';""")
rep("mode:'qty', kind:kind, ref:g.uids[0], name:g.name, gold:g.gold,", "mode:'qty', kind:kind, ref:g.uids[0], name:g.name, gold:g.gold, expired:!!g.expired, unit:g.silver,")
rep("<dl class=\"dq-rows\"><div><dt>قيمة البطاقة الواحدة</dt><dd>' + econFmt(s.gold) + ' كوين</dd></div>",
    "<dl class=\"dq-rows\"><div><dt>' + (s.expired ? 'الحالة' : 'قيمة البطاقة الواحدة') + '</dt><dd>' + (s.expired ? 'منتهية الصلاحية' : econFmt(s.gold) + ' كوين') + '</dd></div>")
rep("set('dq-unit', econSilver(CodisDismantle.reward(s.gold)));", "set('dq-unit', econSilver(s.unit));")
rep("'<p class=\"dq-warn\">لا يمكن التراجع بعد التفكيك.</p>'", "'<p class=\"dq-warn\">' + (s.expired ? 'بطاقة منتهية الصلاحية: مكافأتها ثابتة ' + econFmt(s.unit) + ' فضة. ' : '') + 'لا يمكن التراجع بعد التفكيك.</p>'")
rep("  const before = CodisWallet.silverBalance();\n  const r = CodisDismantle.dismantleMany(",
    "  { const pvx = CodisDismantle.previewMany(s.kind, g.uids.slice(0, s.n)); if(!pvx.ok || (s.pv && pvx.silver !== s.pv.silver)){ codisSfx('invalid'); showToast('تغيّرت حالة البطاقات — أعد المحاولة', 'var(--warning)'); dqEnd(); return; } }   /* إعادة تحقق قبل التنفيذ */\n"
    "  const before = CodisWallet.silverBalance();\n  const r = CodisDismantle.dismantleMany(")

open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
