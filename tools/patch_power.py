"""CODIS-POWER: the developer account has NO limits. Run AFTER tools/patch_admin.py:  python tools/patch_power.py <in> <out>

ADMIN-EXEMPTION RULE (also written in CLAUDE.md — applies to every future change, by any human or AI):
  Any limit, cap, threshold, price check, eligibility rule or anti-abuse guard that restricts the USER must go through
  CodisLimits (CodisLimits.bypass(id) for hard blocks, CodisLimits.num(id, normal) for numeric constants, CodisLimits.afford(have, need)
  for balance checks). Verified developer accounts then pass automatically; everyone else is unaffected. Never add a restriction that skips this.

What the developer exemption is (and is not):
  * Verified developer = CodisAccount.isAdmin(): true only after the SERVER (RLS) allowed this session to read public.admins AND download the private add-on.
  * It only changes how the app behaves on the developer's OWN device/data. It grants nothing on the server (server powers live in sql/codis_admin.sql
    and re-check public.admins on every call). A normal user who forces the flag in devtools changes only their own local copy, which they can already edit.
  * Default behaviour for the developer is the normal economy; only HARD BLOCKS (insufficient funds, weekly purchase lock, expired-use, empty box …)
    are lifted, and numeric constants / box probabilities change only when the developer overrides them (data.adminOverrides) from the panel."""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-POWER' not in t, 'power patch already applied'
assert 'CODIS-ADMIN' in t, 'run tools/patch_admin.py first'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:100]!r}'
    t = t.replace(old, new)

# ================= 1) the registry / gate =================
rep("const CodisWallet = (function(){\n  function balance(){ return data.wallet.balance; }",
r"""/* ================= CODIS-POWER: حساب المطوّر بلا قيود =================
   القاعدة الدائمة: أي حد/سقف/شرط/فحص رصيد يقيّد المستخدم يمر عبر CodisLimits (bypass للمنع الصارم، num للثوابت، afford لفحص الرصيد).
   المطوّر الموثَّق (CodisAccount.isAdmin: الخادم سمح بقراءة public.admins وتنزيل الإضافة الخاصة) يُعفى تلقائياً، وغيره لا يتأثر. */
const CodisLimits = (function(){
  const REG = {}, CONST = {};
  const verified = ()=>{ try{ return CodisAccount.isAdmin() === true; }catch(e){ return false; } };   /* قبل تهيئة الحساب = ليس مطوّراً */
  function on(){ if(!verified()) return false; const p = data && data.adminPower; return !(p && p.off === true); }
  function bypass(id){
    if(!on()) return false;
    const p = data.adminPower; if(p && p.keep && p.keep[id] === true) return false;   /* المطوّر قد يُبقي قيداً بعينه */
    const r = REG[id] || (REG[id] = { id:id, label:id, uses:0 }); r.uses++; return true;
  }
  function afford(have, need, id){ return Number(have) >= Number(need) || bypass(id || 'buy.insufficient'); }
  function num(id, normal){
    if(!on()) return normal;
    const c = data.adminOverrides && data.adminOverrides.constants;
    return (c && typeof c[id] === 'number' && isFinite(c[id])) ? c[id] : normal;
  }
  function reg(id, label, normal){ REG[id] = Object.assign(REG[id] || { id:id, uses:0 }, { label:label }); if(normal !== undefined) CONST[id] = { id:id, label:label, normal:normal }; }
  return { on, verified, bypass, afford, num, reg, registry:()=>Object.keys(REG).map(k=>REG[k]), constants:()=>Object.keys(CONST).map(k=>CONST[k]) };
})();
[['wallet.nonnegative', 'الرصيد لا ينزل تحت الصفر'], ['buy.insufficient', 'فحص كفاية الرصيد عند الشراء'], ['holiday.weekly', 'حدّ شراء بطاقات العطلة الأسبوعي'],
 ['holiday.expireduse', 'منع استخدام بطاقة عطلة منتهية'], ['sell.unsellable', 'منع بيع مكافأة بقيمة تساوي أو تفوق شراءها'], ['box.empty', 'البكج «غير متاح» عندما لا فئات مؤهلة'],
 ['box.rtpGate', 'بوابة العائد المتوقع للبكج'], ['box.prune', 'قصّ سجل البكجات المفتوحة عند 100']].forEach(a=>CodisLimits.reg(a[0], a[1]));

const CodisWallet = (function(){
  function balance(){ return data.wallet.balance; }""")

# ================= 2) data model =================
rep("  d.adminGrantsApplied = Array.isArray(d.adminGrantsApplied)",
r"""  { const ap = d.adminPower, ao = d.adminOverrides, okId = k=>/^[a-z0-9_.]{1,60}$/i.test(k), co = {}, bo = {}, keep = {};
    if(ap && ap.keep && typeof ap.keep === 'object' && !Array.isArray(ap.keep)) Object.keys(ap.keep).forEach(k=>{ if(okId(k) && ap.keep[k] === true) keep[k] = true; });
    d.adminPower = { off:!!(ap && ap.off === true), keep:keep };
    if(ao && ao.constants && typeof ao.constants === 'object' && !Array.isArray(ao.constants)) Object.keys(ao.constants).forEach(k=>{ const v = ao.constants[k]; if(okId(k) && typeof v === 'number' && isFinite(v)) co[k] = v; });
    if(ao && ao.boxes && typeof ao.boxes === 'object' && !Array.isArray(ao.boxes)) Object.keys(ao.boxes).forEach(k=>{ const p = ao.boxes[k] && ao.boxes[k].pm; if(/^bx[1-9]$/.test(k) && Array.isArray(p) && p.length <= 60 && p.every(x=>typeof x === 'number' && isFinite(x) && x >= 0)) bo[k] = { pm:p }; });
    d.adminOverrides = { constants:co, boxes:bo }; }   /* CODIS-POWER: تُقرأ فقط حين يكون المطوّر موثَّقاً */
  d.adminGrantsApplied = Array.isArray(d.adminGrantsApplied)""")

# the flag cannot be flipped through the exported state object: a private closure variable, set only after the server allowed the add-on download
rep("  let inboxAt = 0, inboxBusy = false;", "  let inboxAt = 0, inboxBusy = false, adminOK = false;   /* CODIS-POWER: متغيّر خاص (ليس على S المكشوفة) */")
# adminOK must be true BEFORE the add-on script runs (its panels check CodisLimits.verified() while loading). It is set only after the SERVER allowed the
#    private download (RLS) — i.e. strictly after the admins check and the storage fetch above succeeded.
rep("      const sc = document.createElement('script'); sc.textContent = code + '\\n//# sourceURL=codis-dev-addon.js'; document.head.appendChild(sc);\n      S.admin = true; window.__codisDevLoaded = true; paint();",
    "      adminOK = true;   /* CODIS-POWER: الخادم سمح بالتنزيل ← موثَّق. يُضبط قبل تشغيل الإضافة لأن لوحاتها تتحقق منه أثناء تحميلها */\n      const sc = document.createElement('script'); sc.textContent = code + '\\n//# sourceURL=codis-dev-addon.js'; document.head.appendChild(sc);\n      S.admin = true; window.__codisDevLoaded = true; paint();")
rep("isAdmin:() => S.admin,", "isAdmin:() => adminOK === true,")

# ================= 3) wallet: balance guard =================
rep("    if(w.balance + amount < 0) return null;\n",
r"""    if(w.balance + amount < 0){
      if(!CodisLimits.bypass('wallet.nonnegative')) return null;
      const need = -(w.balance + amount);   /* المطوّر: تُسجَّل تعبئة صريحة بالدفتر ثم تمر العملية — الرصيد لا يصير سالباً والدفتر يبقى متّسقاً */
      w.balance += need; w.lifetimeEarned += need;
      w.transactions.push({ id:econUid('tx'), type:'ADMIN_ADJUSTMENT', amount:need, reason:'تعبئة تلقائية — صلاحية المطوّر', source:'admin', referenceId:'', createdAt:econNowIso() });
    }
""")
rep("    const s = silverW(); if(s.balance + amount < 0) return null;\n",
r"""    const s = silverW();
    if(s.balance + amount < 0){
      if(!CodisLimits.bypass('wallet.nonnegative')) return null;
      const need = -(s.balance + amount);
      s.balance += need; s.lifetimeEarned += need;
      s.transactions.push({ id:econUid('stx'), type:'ADMIN_GRANT', currency:'SILVER', amount:need, reason:'تعبئة تلقائية — صلاحية المطوّر', source:'admin', referenceId:'', createdAt:econNowIso() });
    }
""")

# ================= 4) purchase checks =================
rep("const bal = CodisWallet.silverBalance(); if(bal < d.silver) return", "const bal = CodisWallet.silverBalance(); if(!CodisLimits.afford(bal, d.silver)) return")
rep("      if(CodisWallet.balance() < cost) return { ok:false, reason:'insufficient'", "      if(!CodisLimits.afford(CodisWallet.balance(), cost)) return { ok:false, reason:'insufficient'")
rep("    if(CodisWallet.balance() < price) return { ok:false, reason:'insufficient'", "    if(!CodisLimits.afford(CodisWallet.balance(), price)) return { ok:false, reason:'insufficient'")
rep("    if(CodisWallet.balance() < p) return { ok:false, reason:'insufficient'", "    if(!CodisLimits.afford(CodisWallet.balance(), p)) return { ok:false, reason:'insufficient'")
rep("    if(CodisWallet.balance() < t.price) return { ok:false, reason:'insufficient'", "    if(!CodisLimits.afford(CodisWallet.balance(), t.price)) return { ok:false, reason:'insufficient'")
rep("    if(bal0 < total) return { ok:false, reason:'insufficient'", "    if(!CodisLimits.afford(bal0, total)) return { ok:false, reason:'insufficient'")
# UI enable-states
rep("const price = CodisEconomy.storePrice(it), ok = bal >= price, busy = econBusyId === it.id", "const price = CodisEconomy.storePrice(it), ok = CodisLimits.afford(bal, price), busy = econBusyId === it.id")
rep("ok = avail && bal >= price, busy = econBusyId === it.id || econStoreBusy;", "ok = avail && CodisLimits.afford(bal, price), busy = econBusyId === it.id || econStoreBusy;")
rep("const own = C.owns(d.id), ok = own || sv >= d.silver;", "const own = C.owns(d.id), ok = own || CodisLimits.afford(sv, d.silver);")
rep("ok = !blocked && bal >= p, busy = econStoreBusy;", "ok = !blocked && CodisLimits.afford(bal, p), busy = econStoreBusy;")
rep("ok = bal >= t.price && n > 0, label = !n ? 'غير متاح' : bal >= t.price ?", "ok = CodisLimits.afford(bal, t.price) && n > 0, label = !n ? 'غير متاح' : CodisLimits.afford(bal, t.price) ?")
rep("ok10 = bal >= total && n > 0,", "ok10 = CodisLimits.afford(bal, total) && n > 0,")
rep("    if(data.wallet.balance < t.price){ codisSfx('invalid');", "    if(!CodisLimits.afford(data.wallet.balance, t.price)){ codisSfx('invalid');")

# ================= 5) weekly lock / expired use / sell =================
rep("    if(kind !== undefined) return limited(kind) && !!bw[buyKey(kind, wk)];\n    const ks = kinds().filter(limited); return ks.length > 0 && ks.every(k=>!!bw[buyKey(k, wk)]);",
    "    if(CodisLimits.bypass('holiday.weekly')) return false;\n    if(kind !== undefined) return limited(kind) && !!bw[buyKey(kind, wk)];\n    const ks = kinds().filter(limited); return ks.length > 0 && ks.every(k=>!!bw[buyKey(k, wk)]);")
rep("    if(d.weeklyBuyLimit && buyWeeks()[key]) return { ok:false, reason:'weeklimit' };\n    const p = price(kind);",
    "    if(d.weeklyBuyLimit && buyWeeks()[key] && !CodisLimits.bypass('holiday.weekly')) return { ok:false, reason:'weeklimit' };\n    const p = price(kind);")
rep("      if(d.weeklyBuyLimit && buyWeeks()[key]) return { ok:false, reason:'weeklimit' };",
    "      if(d.weeklyBuyLimit && buyWeeks()[key] && !CodisLimits.bypass('holiday.weekly')) return { ok:false, reason:'weeklimit' };")
rep("    if(c.status === 'expired' || timeExpired(c)){ sweepAndSave(); return { ok:false, reason:'expired' }; }\n    if(c.status !== 'owned') return { ok:false, reason:'used' };",
    "    if((c.status === 'expired' || timeExpired(c)) && !CodisLimits.bypass('holiday.expireduse')){ sweepAndSave(); return { ok:false, reason:'expired' }; }\n    if(c.status !== 'owned' && !(c.status === 'expired' && CodisLimits.bypass('holiday.expireduse'))) return { ok:false, reason:'used' };")
rep("      if(timeExpired(q)) return { ok:false, reason:'expired' };", "      if(timeExpired(q) && !CodisLimits.bypass('holiday.expireduse')) return { ok:false, reason:'expired' };")
rep("    if(!(value > 0) || value >= it.coinValue) return { ok:false, reason:'unsellable' };", "    if((!(value > 0) || value >= it.coinValue) && !(value > 0 && CodisLimits.bypass('sell.unsellable'))) return { ok:false, reason:'unsellable' };")

# ================= 6) boxes: overridable constants, probabilities, gates =================
rep("  const VALUE_SPAN = 50, MAX_PRIZE_X = 12, MAX_RTP = 0.95, MAX_PWIN = 0.6;",
    "  const VALUE_SPAN_N = 50, MAX_PRIZE_X_N = 12, MAX_RTP_N = 0.95, MAX_PWIN_N = 0.6;   /* القيم العادية؛ المطوّر يعدّلها من اللوحة (CODIS-POWER) */\n"
    "  const lim = {}; ['VALUE_SPAN', 'MAX_PRIZE_X', 'MAX_RTP', 'MAX_PWIN'].forEach(k=>{ const id = 'box.' + k, nv = { VALUE_SPAN:VALUE_SPAN_N, MAX_PRIZE_X:MAX_PRIZE_X_N, MAX_RTP:MAX_RTP_N, MAX_PWIN:MAX_PWIN_N }[k]; Object.defineProperty(lim, k, { get(){ return CodisLimits.num(id, nv); } }); });\n"
    "  const VALUE_SPAN_V = ()=>lim.VALUE_SPAN, MAX_PRIZE_X_V = ()=>lim.MAX_PRIZE_X, MAX_RTP_V = ()=>lim.MAX_RTP, MAX_PWIN_V = ()=>lim.MAX_PWIN;")
rep("while(i < items.length && items[i].v - start <= VALUE_SPAN){", "while(i < items.length && items[i].v - start <= VALUE_SPAN_V()){")
rep("  function minValue(id){ const v = Number(MIN_VALUE[id]); return v > 0 ? v : 0; }", "  function minValue(id){ const v = Number(CodisLimits.num('box.minValue.' + id, MIN_VALUE[id])); return v > 0 ? v : 0; }")
rep("  function effective(t){\n    const top = Math.max.apply(null, tiers().map(x=>x.basePrice)), cs = classes(minValue(t.id)).filter(c=>c.max <= MAX_PRIZE_X * t.basePrice || t.basePrice >= top); if(!cs.length) return [];",
    "  /* احتمالات يحدّدها المطوّر (بالألف، قابلة للصفر) تحل محل المحسوبة — فقط للمطوّر الموثَّق وبنفس عدد الفئات */\n"
    "  function adminPermille(ws){ const tot = ws.reduce((s,x)=>s + x, 0); if(!(tot > 0)) return null; const raw = ws.map(x=>x / tot * 1000), out = raw.map(Math.floor); let left = 1000 - out.reduce((s,x)=>s + x, 0); raw.map((x,i)=>({ f:x - Math.floor(x), i:i })).sort((a,b)=>b.f - a.f || a.i - b.i).forEach(o=>{ if(left > 0 && ws[o.i] > 0){ out[o.i]++; left--; } }); return out; }\n"
    "  function overridePm(t, rows){\n    if(!CodisLimits.on()) return rows;\n    const o = data.adminOverrides && data.adminOverrides.boxes && data.adminOverrides.boxes[t.id];\n    if(!o || !Array.isArray(o.pm) || o.pm.length !== rows.length) return rows;\n    const pm = adminPermille(o.pm); if(!pm) return rows;\n    return rows.map((r,i)=>Object.assign({}, r, { pm:pm[i] }));\n  }\n"
    "  function effective(t, raw){\n    const rows = effectiveBase(t); if(raw === true) return rows; return overridePm(t, rows);\n  }\n"
    "  function effectiveBase(t){\n    const top = Math.max.apply(null, tiers().map(x=>x.basePrice));\n    let cs = classes(minValue(t.id)).filter(c=>c.max <= MAX_PRIZE_X_V() * t.basePrice || t.basePrice >= top);\n    if(!cs.length){ if(!CodisLimits.bypass('box.empty')) return []; cs = classes(minValue(t.id)); if(!cs.length) return []; }")
rep("    let lo = -4, hi = 14;\n    for(let k = 0; k < 60; k++)", "    let lo = -4, hi = 14;\n    for(let k = 0; k < 60; k++)")   # sanity: anchor still present
rep("while(win(pm) > MAX_PWIN && hi < 14){ hi += 0.25; pm = mk(hi); }", "while(win(pm) > MAX_PWIN_V() && hi < 14){ hi += 0.25; pm = mk(hi); }")
rep("    if(ev(pm) > MAX_RTP * t.basePrice || win(pm) > MAX_PWIN) return [];", "    if((ev(pm) > MAX_RTP_V() * t.basePrice || win(pm) > MAX_PWIN_V()) && !CodisLimits.bypass('box.rtpGate')) return [];")
rep("  const PRICE_FACTOR = 0.85, KEEP_OPENED = 100;", "  const PRICE_FACTOR = 0.85, KEEP_OPENED_N = 100;")
rep("    if(op.length <= KEEP_OPENED) return;\n    const drop = {}; op.slice(KEEP_OPENED).forEach", "    const keepN = CodisLimits.bypass('box.prune') ? Infinity : CodisLimits.num('box.keepOpened', KEEP_OPENED_N);\n    if(op.length <= keepN) return;\n    const drop = {}; op.slice(keepN).forEach")
rep("  return { tiers, tier, pool, classes, effective, stats,", "  return { tiers, tier, pool, classes, effective, effectiveBase, stats,")
rep("function econBoxPrice(id){\n  const p = Number((econModel().boxPrices || {})[id]);\n  return (isFinite(p) && p >= 1) ? Math.round(p) : 0;",
    "function econBoxPrice(id){\n  const p = Number((econModel().boxPrices || {})[id]);\n  return (isFinite(p) && p >= 1) ? Math.max(1, Math.round(CodisLimits.num('box.price.' + id, Math.round(p)))) : 0;   /* CODIS-POWER: سعر يحدده المطوّر */")
# dismantle constants
rep("  function reward(g){ g = Number(g); return (isFinite(g) && g > 0) ? Math.floor(g * RATE) : 0; }", "  function reward(g){ g = Number(g); return (isFinite(g) && g > 0) ? Math.floor(g * CodisLimits.num('dismantle.rate', RATE)) : 0; }")
rep("fixed:EXPIRED_SILVER, expired:true", "fixed:Math.max(1, Math.trunc(CodisLimits.num('dismantle.expiredSilver', EXPIRED_SILVER))), expired:true")
# register overridable constants (labels for the panel)
rep("/* ================= ACCOUNT & SYNC (CodisAccount) =================",
r"""/* CODIS-POWER: الثوابت القابلة للتعديل من لوحة المطوّر (القيمة العادية تُقرأ الآن) */
(function(){
  const R = CodisLimits.reg;
  CodisBoxes.tiers().forEach(t=>R('box.price.' + t.id, 'سعر ' + t.name + ' (كوين)', t.price));
  [['box.VALUE_SPAN', 'أقصى فرق قيمة داخل الفئة الواحدة', 50], ['box.MAX_PRIZE_X', 'أعلى جائزة مسموحة × سعر البكج', 12], ['box.MAX_RTP', 'أعلى عائد متوقع (نسبة من السعر)', 0.95], ['box.MAX_PWIN', 'أعلى احتمال أن تفوق الجائزة السعر', 0.6],
   ['box.keepOpened', 'عدد البكجات المفتوحة المحفوظة بالسجل', 100], ['dismantle.rate', 'معامل تفكيك البطاقات (× قيمة البطاقة)', 1.5], ['dismantle.expiredSilver', 'فضة تفكيك البطاقة المنتهية', 25]].forEach(a=>R(a[0], a[1], a[2]));
  [['bx2', 50], ['bx3', 90], ['bx4', 165], ['bx5', 245]].forEach(a=>{ const t = CodisBoxes.tier(a[0]); R('box.minValue.' + a[0], 'الحد الأدنى لقيمة جائزة ' + (t ? t.name : a[0]), a[1]); });
})();
/* ================= ACCOUNT & SYNC (CodisAccount) =================""")

# ================= 7) startup: status text + explicit failure recovery (prompt §7) =================
rep(".cs-bar[data-state=\"warn\"] i{ background:var(--gold); }",
    ".cs-bar[data-state=\"warn\"] i{ background:var(--gold); }\n.cs-status{ margin-top:12px; min-height:18px; max-width:min(280px,calc(70 * var(--vw))); text-align:center; font-size:12.5px; color:var(--text-2); opacity:0; animation:csText calc(340ms * var(--k)) var(--ease) calc(560ms * var(--k)) forwards; }\n"
    ".cs-fail{ margin-top:16px; max-width:min(300px,calc(78 * var(--vw))); text-align:center; font-size:13px; color:var(--text); }\n.cs-fail[hidden]{ display:none; }\n.cs-fail p{ margin:0 0 10px; }\n.cs-fail .cs-btns{ display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }\n"
    ".cs-fail button{ min-height:44px; padding:0 16px; border-radius:12px; border:1px solid var(--glass-border); background:var(--glass-strong); color:var(--text); font:inherit; font-weight:600; cursor:pointer; }\n.cs-fail button.is-main{ background:var(--aqua); color:var(--bg); border-color:transparent; }\n"
    "@media (prefers-reduced-motion:reduce){ .cs-status{ opacity:1; animation:none; } }")
rep('<div class="cs-bar" id="cs-bar" role="progressbar" aria-label="تقدّم تجهيز التطبيق" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>\n',
    '<div class="cs-bar" id="cs-bar" role="progressbar" aria-label="تقدّم تجهيز التطبيق" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>\n'
    '  <div class="cs-status" id="cs-status" role="status" aria-live="polite">جارٍ التجهيز…</div>\n'
    '  <div class="cs-fail" id="cs-fail" hidden><p id="cs-fail-msg"></p><div class="cs-btns"><button type="button" class="is-main" id="cs-retry">إعادة المحاولة</button><button type="button" id="cs-go">المتابعة على أي حال</button></div></div>\n')
rep("  window.codisReveal = function(){\n",
    """  window.codisBootStatus = function(txt){ var s = document.getElementById('cs-status'); if(s && txt) s.textContent = txt; };
  /* مرحلة أساسية فشلت: لا كشف صامت. رسالة واضحة + إعادة تحميل، أو متابعة بقرار المستخدم */
  window.codisBootFail = function(names, go){
    var f = document.getElementById('cs-fail'), m = document.getElementById('cs-fail-msg'); if(!f){ go(); return; }
    window.clearTimeout(window.codisStartupTimer); if(window.codisBootStatus) window.codisBootStatus('تعذّر إكمال التجهيز');
    m.textContent = 'تعذّر تجهيز جزء أساسي من التطبيق (' + names.join('، ') + '). بياناتك لم تُمَس.'; f.hidden = false;
    document.getElementById('cs-retry').onclick = function(){ location.reload(); };
    document.getElementById('cs-go').onclick = function(){ f.hidden = true; go(); };
  };
  window.codisReveal = function(){
""")
rep("function codisBoot(){\n  const TOTAL = 12; let done = 0, failed = 0;   /* 11 مرحلة تجهيز + انتظار الخطوط */\n  function step(label, fn){\n    try{ fn(); }\n    catch(err){ failed++; console.error('CODIS init error ('+label+'):', err); }\n    done++;",
    "function codisBoot(){\n  const TOTAL = 14; let done = 0, failed = 0; const reqFailed = [];   /* 13 مرحلة تجهيز + انتظار الخطوط */\n"
    "  const STAGE = { lock:'تأمين التطبيق', motion:'تجهيز الحركة', notifications:'تجهيز الإشعارات', archive:'ترتيب الأرشيف', economy:'تحميل الاقتصاد', coinchip:'تحميل الرصيد', backup:'فحص النسخ', habits:'تجهيز العادات', planning:'تجهيز غرفة التخطيط', tasks:'تجهيز غرفة العمليات', learn:'تجهيز غرفة الأستاذ', route:'اختيار الغرفة', view:'تثبيت الواجهة' };\n"
    "  const REQUIRED = { economy:'الاقتصاد', planning:'غرفة التخطيط', tasks:'غرفة العمليات', learn:'غرفة الأستاذ' };\n"
    "  function step(label, fn){\n    if(window.codisBootStatus && STAGE[label]) window.codisBootStatus(STAGE[label] + '…');\n    try{ fn(); }\n    catch(err){ failed++; if(REQUIRED[label]) reqFailed.push(REQUIRED[label]); console.error('CODIS init error ('+label+'):', err); }\n    done++;")
rep("    if(window.codisBootProgress) window.codisBootProgress(1, failed > 0);\n    window.clearTimeout(codisStartupTimer);\n",
    "    if(window.codisBootProgress) window.codisBootProgress(1, failed > 0);\n    if(window.codisBootStatus && !reqFailed.length) window.codisBootStatus('جاهز');\n    window.codisStartupTimer_ref = codisStartupTimer;\n    const go = function(){\n    window.clearTimeout(codisStartupTimer);\n")
rep("}, remaining + 900);\n    });", "}, remaining + 900);\n    };\n    if(reqFailed.length && window.codisBootFail){ window.clearTimeout(codisStartupTimer); window.codisBootFail(reqFailed, go); } else go();\n    });")

open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
