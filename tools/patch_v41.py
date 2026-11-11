"""CODIS-FINANCE (3.28.0) — الإدارة المالية الشخصية (دينار عراقي) + ربطها بالمكافآت + إعادة ترتيب الشريط العلوي + التقارير بالأرشيف.

  py -3 tools/patch_v41.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (بعد patch_v40؛ ثم set_version.py 3.28.0 + build_sw.py)

  • tools/identity/v41_core.js — المحرك: دفتر حركات data.finance (OPENING_BALANCE · DEPOSIT · SALARY · EXPENSE · REWARD_REDEMPTION)، الرواتب بتعويض الفائت، سعر الصرف (مرة بالشهر)،
    مصفوفة نطاقات 23 بطاقة، التصنيف الذكي المحلي، إنشاء/إعادة تسعير المكافآت التلقائية (مالية/وقتية).
  • tools/identity/v41_ui.js — الواجهة (طبقة eco-fin، الاستبيان، النوافذ، التقارير، معالج الإضافة التلقائية، تأكيد الاستخدام) + متابعة الراتب المستحق.
  • tools/identity/v41.css — الشريط العلوي (المالية + كوينز/فضة فوق بعض بلا مستطيل) + هوية الإدارة المالية (فاتح/داكن).
  • تعديلات: سعر B اليومية 60 → 50 (سلّم الندرة 2.4 → 2؛ الأسبوعية/الشهرية مشتقتان) · التقارير المحفوظة من سجل الكوينز إلى قسم «التقارير» بالأرشيف (المصدر outcomeLedger كما هو) ·
    استخدام المكافأة المالية يخصم من المحفظة المالية بمعاملة واحدة مع حالة النسخة (وتراجع كامل عند الفشل) · نوع المكافأة صريح fin.kind لا يُستنتج من الاسم.
"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-FINANCE' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:120])
    s = s.replace(old, new)
def many(old, new, n):
    global s
    assert s.count(old) == n, ('anchor count', s.count(old), n, old[:120])
    s = s.replace(old, new)

core = rd('v41_core.js').rstrip() + '\n'
ui = rd('v41_ui.js').rstrip() + '\n'
css = rd('v41.css'); assert '</style' not in css and '<!--' not in css

# ---- المحرك + الواجهة ----
once("/* البيانات الافتراضية لأول تشغيل فقط */\nfunction seedData(){", core + "\n/* البيانات الافتراضية لأول تشغيل فقط */\nfunction seedData(){")
once("\nCodisAccount.init();\n\n</script>", "\n/* CODIS-FINANCE: واجهة الإدارة المالية */\n" + ui + "\nCodisAccount.init();\n\n</script>")
once("const SCHEMA_VERSION = 6;   // 6:", "const SCHEMA_VERSION = 7;   // 7: أُضيف data.finance (الإدارة المالية — إضافة فقط) · 6:")
once("  econNormalizeAll(d);   // اقتصاد المكافآت: إعدادات · كائنات · محفظة · حالة · سجل (إضافة فقط)",
     "  codisFinNormalize(d);   /* CODIS-FINANCE: دفتر مالي مستقل (إضافة فقط) */\n  econNormalizeAll(d);   // اقتصاد المكافآت: إعدادات · كائنات · محفظة · حالة · سجل (إضافة فقط)")

# ---- سعر B: 60 → 50 ----
once("ladder:Object.freeze({ C:1, B:2.4, A:6, S:15, SS:40 }),", "ladder:Object.freeze({ C:1, B:2, A:6, S:15, SS:40 }),   /* CODIS-FINANCE: B كانت 2.4 (=60) وصارت 2 (=50): اليومية 50 · الأسبوعية 350 · الشهرية 1,500 */")
once("boxWeight:bo.B,  coinValue:60,   tone:'b'", "boxWeight:bo.B,  coinValue:50,   tone:'b'")
once("شائعة 1 · غير شائعة 2.4 · نادرة 6", "شائعة 1 · غير شائعة 2 · نادرة 6")

# ---- السعر الدقيق للمكافآت التلقائية ----
once("function econEffCoin(item, rar){ if(item && item.fixed && item.fixedCoin > 0) return item.fixedCoin;",
     "function econEffCoin(item, rar){ if(item && item.fin) return codisFinItemCoin(item);   /* CODIS-FINANCE: قيمة دقيقة مشتقة (دينار ÷ سعر الصرف أو دقائق ÷ 2) */\n  if(item && item.fixed && item.fixedCoin > 0) return item.fixedCoin;")
once("coinValue:null, storePrice:null, stickerId:codisStickerIdOk(x.stickerId),\n      enabled:x.enabled !== false, room:room,",
     "coinValue:null, storePrice:null, stickerId:codisStickerIdOk(x.stickerId), fin:x.fin,\n      enabled:x.enabled !== false, room:room,")
once("  codisV34Seed(settings);   /* CODIS-V34: البطاقات الثابتة (آمن وقت التحميل: دوال فقط) */",
     "  codisV34Seed(settings);   /* CODIS-V34: البطاقات الثابتة (آمن وقت التحميل: دوال فقط) */\n  codisFinReconcileItems(settings);   /* CODIS-FINANCE */")
once("    if(status === 'sold'){ it.soldFor = econCN(x.soldFor, 0, 0, 1000000);", "    { const fn = codisFinItemOk(x.fin); if(fn) it.fin = fn; }   /* CODIS-FINANCE: لقطة نوع المكافأة وقيمتها الأصلية */\n    if(status === 'sold'){ it.soldFor = econCN(x.soldFor, 0, 0, 1000000);")
once("    all().push(it);\n    return it;\n  }\n  return { get, owned, closed, sellValue, grant, all };",
     "    { const fn = codisFinItemOk(o.fin); if(fn) it.fin = fn; }   /* CODIS-FINANCE */\n    all().push(it);\n    return it;\n  }\n  return { get, owned, closed, sellValue, grant, all };")
once("owned = CodisInventory.grant({ uid:'own|' + e.id, rewardId:e.rewardId, stickerId:e.stickerId, name:e.item,", "owned = CodisInventory.grant({ uid:'own|' + e.id, rewardId:e.rewardId, stickerId:e.stickerId, fin:e.fin, name:e.item,")
once("CodisInventory.grant({ uid:'own|store|' + tx.id, rewardId:item.id, stickerId:item.stickerId, name:item.name,", "CodisInventory.grant({ uid:'own|store|' + tx.id, rewardId:item.id, stickerId:item.stickerId, fin:item.fin, name:item.name,")
once("CodisInventory.grant({ uid:'own|box|' + uid, rewardId:it.id, stickerId:it.stickerId, name:it.name,", "CodisInventory.grant({ uid:'own|box|' + uid, rewardId:it.id, stickerId:it.stickerId, fin:it.fin, name:it.name,")
once("      if(r.pity) e.pity = true;\n", "      if(r.pity) e.pity = true;\n      if(r.reward && r.reward.fin){ const _fn = codisFinItemOk(r.reward.fin); if(_fn){ _fn.coin = r.coinValue; e.fin = _fn; } }   /* CODIS-FINANCE: نوع المكافأة وقيمتها الأصلية تُثبَّت مع النتيجة */\n")

# ---- كروت التأديب الخاصة: نسخ تلقائية بنفس الخانة ----
once("  const rar = econCfg().rarities[0];\n  const e = Object.assign({ id:id, room:'habits', kind:kind,", "  const rar = econCfg().rarities[0], vr = kind === 'reward' ? codisFinPickVariant(id, def, it) : it;   /* CODIS-FINANCE */\n  const e = Object.assign({ id:id, room:'habits', kind:kind,")
once("if(kind === 'reward') Object.assign(e, { item:it.name, rewardId:def.id, stickerId:codisStickerIdOk(it.stickerId), rarity:rar.id, rarityName:rar.name, rarityTone:rar.tone, rarityOrder:rar.order, odds:null, coinValue:def.coin, storePrice:econEffStore(it, rar), coinsAwarded:0 });",
     "if(kind === 'reward'){ Object.assign(e, { item:vr.name, rewardId:def.id, stickerId:codisStickerIdOk(vr.stickerId), rarity:rar.id, rarityName:rar.name, rarityTone:rar.tone, rarityOrder:rar.order, odds:null, coinValue:vr.fin ? codisFinItemCoin(vr) : def.coin, storePrice:econEffStore(vr, rar), coinsAwarded:0 });\n    if(vr.fin){ const _fn = codisFinItemOk(vr.fin); if(_fn){ _fn.coin = codisFinItemCoin(vr); e.fin = _fn; e.variantId = vr.id; } } }")
once("function codisFixedOutcome(id, kind, def, extra){", """/* مكافأة تلقائية موضوعة ببطاقة خاصة: تُختار بتجزئة معرّف النتيجة (ثابتة عند التحديث/المزامنة) من الكرت الأصلي + نسخه المفعّلة */
function codisFinPickVariant(id, def, base){
  try{
    const vs = (data.settings.rewardItems || []).filter(x=>x && x.enabled !== false && x.variantOf === def.id && x.fin);
    if(!vs.length) return base;
    const all = [base].concat(vs.sort((a, b)=>a.id < b.id ? -1 : 1)); return all[parseInt(econHash(String(id)), 16) % all.length];
  }catch(e){ return base; }
}
function codisFixedOutcome(id, kind, def, extra){""")

# ---- معاملات المحفظة: لقطة الدفتر المالي ضمن المعاملة نفسها ----
once("const w = data.wallet, st = JSON.stringify(data.economyState), inv = JSON.stringify(data.inventory), sv = JSON.stringify(silverW());",
     "const w = data.wallet, st = JSON.stringify(data.economyState), inv = JSON.stringify(data.inventory), sv = JSON.stringify(silverW()), fz = JSON.stringify(data.finance || null);   /* CODIS-FINANCE */")
once("      data.inventory = JSON.parse(inv);   // الممتلكات جزء من نفس المعاملة: لا رصيد بلا مكافأة ولا مكافأة بلا رصيد",
     "      data.inventory = JSON.parse(inv);   // الممتلكات جزء من نفس المعاملة: لا رصيد بلا مكافأة ولا مكافأة بلا رصيد\n      if(fz !== 'null') data.finance = JSON.parse(fz);   /* CODIS-FINANCE: الخصم المالي جزء من نفس المعاملة */")

# ---- استخدام المكافأة: FINANCIAL يخصم ويعلّم معاً · TIME مؤقت · LEGACY كما كان ----
once("""    if(it.status !== 'owned') return { ok:false, reason:it.status === 'sold' ? 'sold' : 'used' };
    return CodisWallet.transact([], ()=>{ it.status = 'used'; it.statusAt = econNowIso(); return { ok:true, item:it }; });""",
"""    if(it.status !== 'owned') return { ok:false, reason:it.status === 'sold' ? 'sold' : 'used' };
    if(it.fin && it.fin.kind === 'financial'){   /* CODIS-FINANCE: الخصم المالي + حالة البطاقة + مرجع الربط = معاملة واحدة */
      const res = CodisWallet.transact([], ()=>{
        const rd = codisFinRedeemIn({ uid:uid, iqd:it.fin.iqd, name:it.name, coins:it.coinValue, rewardId:it.rewardId });
        if(!rd.ok && rd.reason !== 'dup') return rd;   /* dup = خُصمت سابقاً (مزامنة): لا خصم ثانٍ، فقط نعلّم النسخة */
        it.status = 'used'; it.statusAt = econNowIso(); return { ok:true, item:it, fin:rd.entry || null };
      });
      if(res && res.ok){ try{ finRefresh(); }catch(e){} }
      return res;
    }
    return CodisWallet.transact([], ()=>{ it.status = 'used'; it.statusAt = econNowIso(); return { ok:true, item:it }; });""")
once("const _dur = CodisDuration.parse(it.name), _sn = CodisUseCine.snap(it);", "const _dur = codisDurOf(it), _sn = CodisUseCine.snap(it);")
once("""    const ok = await codisConfirm(CodisCopy.useReward(it.name));
    if(!ok) return;
    const r = CodisEconomy.markUsed(uid);""", """    const ok = (it.fin && it.fin.kind === 'financial') ? await codisFinUseConfirm(it) : await codisConfirm(CodisCopy.useReward(it.name));   /* CODIS-FINANCE: مالية ← تأكيد صريح بالمبلغ والرصيد */
    if(!ok) return;
    const r = CodisEconomy.markUsed(uid);""")
once("else { codisSfx('invalid', { ctx:'unavailable' }); showToast(r.reason === 'save' ? 'تعذّر الحفظ — بقيت كما هي' : 'تعذّر التنفيذ', 'var(--warning)'); }\n  } finally { econSellBusy = false; econRenderAll(); }",
     "else { codisSfx('invalid', { ctx:'unavailable' }); showToast(r.reason === 'save' ? 'تعذّر الحفظ — بقيت كما هي' : r.reason === 'funds' ? 'رصيدك المالي غير كافٍ — ما انخصم شيء وبقيت المكافأة بحوزتك' : r.reason === 'nosetup' ? 'أكمل إعداد الإدارة المالية أولاً' : 'تعذّر التنفيذ', 'var(--warning)'); }\n  } finally { econSellBusy = false; econRenderAll(); }")
once("  const d = CodisDuration.parse(it.name); if(!d) return { ok:false, reason:'notimed' };", "  const d = codisDurOf(it); if(!d) return { ok:false, reason:'notimed' };")
once("  const d = CodisDuration.parse(it.name);\n  return '<button type=\"button\" class=\"btn btn-primary own-use own-go'", "  const d = codisDurOf(it);\n  return '<button type=\"button\" class=\"btn btn-primary own-use own-go'")
once("function codisDurBadgeHtml(name){ const d = CodisDuration.parse(name);", "function codisDurBadgeHtml(x){ const d = (x && typeof x === 'object') ? codisDurOf(x) : CodisDuration.parse(x);   /* CODIS-FINANCE: عنصر ← النوع الصريح */")
many("codisDurBadgeHtml(it.name)", "codisDurBadgeHtml(it)", 3)
once("      const dur = CodisDuration.parse(r.owned.name);", "      const dur = codisDurOf(r.owned);")
once("""const uid = s.uid, it = CodisInventory.get(uid); let ok = false, msg = 'هذي المكافأة ما عدت بحوزتك', _sn = null, _d = null;   /* CODIS-USE-CINE */""",
"""const uid = s.uid, it = CodisInventory.get(uid); let ok = false, msg = 'هذي المكافأة ما عدت بحوزتك', _sn = null, _d = null;   /* CODIS-USE-CINE */
    if(it && it.status === 'owned' && it.fin && it.fin.kind === 'financial'){ close(()=>{ try{ econRenderAll(); }catch(e){} setTimeout(()=>{ econUse(uid); }, 140); }); return; }   /* CODIS-FINANCE: المالية لا تُخصم دون نافذة التأكيد — يُغلق المشهد ثم يُفتح مسار الاستخدام العادي */""")
once("const d = CodisDuration.parse(it.name); _sn = CodisUseCine.snap(it); _d = d;", "const d = codisDurOf(it); _sn = CodisUseCine.snap(it); _d = d;")

# ---- إعدادات المكافآت: صف/تحرير/وسم ----
once("""    '<span>استبدال <b>' + econFmt(coin) + '</b></span><span>متجر <b>' + econFmt(price) + '</b></span><span>بيع <b>' + econFmt(econSellValue(coin)) + '</b></span>',""",
     """    codisFinMetaHtml(it) + '<span>استبدال <b>' + econFmt(coin) + '</b></span><span>متجر <b>' + econFmt(price) + '</b></span><span>بيع <b>' + econFmt(econSellValue(coin)) + '</b></span>',""")
once("""  Object.assign(it, v, { updatedAt:econNowIso() });
  econNormalizeItems(data.settings); econEditing = null;
  econSave('انحفظت المكافأة'); econRenderAll();""", """  Object.assign(it, v, { updatedAt:econNowIso() });
  if(it.fin){ const _c = codisFinCardById(it.fin.card); if(_c) codisFinApplyPlacement(it, _c); }   /* CODIS-FINANCE: تصنيف المكافأة التلقائية تحدده قيمتها لا التحرير اليدوي */
  econNormalizeItems(data.settings); econEditing = null;
  econSave('انحفظت المكافأة'); econRenderAll();""")
once("  if(it.room === 'habits') return '<span class=\"rpt-tag cat-chip rpt-none\">بدون تصنيف</span>';",
     "  if(it.variantOf){ const _d = codisFixedById(it.variantOf); return '<span class=\"rpt-tag cat-chip\">' + escapeHtml(_d ? _d.label : 'تلقائية') + '</span>'; }   /* CODIS-FINANCE */\n  if(it.room === 'habits') return '<span class=\"rpt-tag cat-chip rpt-none\">بدون تصنيف</span>';")
once("  function pool(){ return data.settings.rewardItems.filter(x=>x.enabled && !x.fixed && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0); }",
     "  function pool(){ return data.settings.rewardItems.filter(x=>x.enabled && !x.fixed && !x.variantOf && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0); }")
once("return data.settings.rewardItems.filter(x=>x.enabled && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0).map(it=>({ p:CodisEconomy.storePrice(it), n:it.name, it:it }))",
     "return data.settings.rewardItems.filter(x=>x.enabled && !x.variantOf && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0).map(it=>({ p:CodisEconomy.storePrice(it), n:it.name, it:it }))")
once("  const t = document.getElementById('rpu-all-t'); if(t) t.textContent = rpKind === 'punish' ? 'كل العقوبات' : 'كل المكافآت';",
     "  const _au = document.getElementById('rpu-auto-btn'); if(_au) _au.hidden = rpKind === 'punish';   /* CODIS-FINANCE */\n  const t = document.getElementById('rpu-all-t'); if(t) t.textContent = rpKind === 'punish' ? 'كل العقوبات' : 'كل المكافآت';")
once("""      <button type="button" class="rpu-all-btn" id="rpu-all-btn" aria-pressed="false" """, """      <button type="button" class="rpu-all-btn rpu-auto-btn" id="rpu-auto-btn" onclick="finAutoOpen()"><svg class="rpu-all-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5l1.7 4.6 4.6 1.7-4.6 1.7L12 16.1l-1.7-4.6-4.6-1.7 4.6-1.7z"/><path d="M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/></svg><span>إضافة مكافأة تلقائية</span><svg class="rpu-all-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg></button>
      <button type="button" class="rpu-all-btn" id="rpu-all-btn" aria-pressed="false" """)

# ---- الأرشيف: قسم «التقارير» (المصدر outcomeLedger كما هو، بلا نقل ولا تكرار) ----
once("  { id:'habit', label:'العادات', empty:'ماكو عادات مؤرشفة بعد', match:e=>isArchivedHabit(e) }\n];",
     "  { id:'habit', label:'العادات', empty:'ماكو عادات مؤرشفة بعد', match:e=>isArchivedHabit(e) },\n  { id:'reports', label:'التقارير', empty:'ماكو تقارير محفوظة بعد', match:()=>false, count:()=>econReportEntries().length, html:()=>econReportsListHtml() }   /* CODIS-FINANCE: التقارير الأسبوعية/الشهرية — مصدرها data.outcomeLedger */\n];")
once("      const n = all.filter(e=>archSectionOf(e) === s).length;", "      const n = s.count ? s.count() : all.filter(e=>archSectionOf(e) === s).length;")
once("  if(!list.length){\n    wrap.innerHTML = '<div class=\"empty-inline\">' + curSec.empty + '</div>';", "  if(curSec.html){ wrap.innerHTML = curSec.html(); return; }   /* CODIS-FINANCE */\n  if(!list.length){\n    wrap.innerHTML = '<div class=\"empty-inline\">' + curSec.empty + '</div>';")
once("function econReportsListHtml(){\n  const L = data.outcomeLedger, ents = Object.keys(L).map(k=>L[k]).filter(e=>e.report && (e.scope === 'weekly' || e.scope === 'monthly')).sort((a,b)=>a.at < b.at ? 1 : -1);",
     "function econReportEntries(){ const L = data.outcomeLedger; return Object.keys(L).map(k=>L[k]).filter(e=>e && e.report && (e.scope === 'weekly' || e.scope === 'monthly')).sort((a,b)=>a.at < b.at ? 1 : -1); }\nfunction econReportsListHtml(){\n  const ents = econReportEntries();")
once("  return ents.slice(0, 40).map(e=>'<div class=\"rp-list-row\">", "  return '<div class=\"arch-rp-count\" role=\"status\">' + ents.length + ' تقرير محفوظ</div>' + ents.map(e=>'<div class=\"rp-list-row\">")
once("""  html += '<section class="ecl-sec" aria-labelledby="ecl-h-rp"><header class="ecl-sh"><h3 id="ecl-h-rp" class="ecl-h eco-sec-title">التقارير المحفوظة</h3></header><div class="settings-card ecl-card">' + econReportsListHtml() + '</div></section>';\n""", "")

# ---- الشريط العلوي ----
once("""<button type="button" class="coin-chip" id="coin-chip" aria-label="رصيد الكوينز — افتح سجل الكوينز" onclick="econOpenLog()">
  <svg data-icon="coin" data-size="md"></svg>
  <span class="coin-chip-num" id="coin-chip-num">0</span>
  <span class="coin-chip-silver" id="coin-chip-silver" hidden></span>
</button>""", """<button type="button" class="fin-btn" id="fin-btn" aria-label="الإدارة المالية" title="الإدارة المالية" onclick="finOpen()">
  <svg data-icon="wallet" data-size="md"></svg>
</button>

<button type="button" class="coin-chip" id="coin-chip" aria-label="رصيد الكوينز والفضة — افتح سجل الكوينز" onclick="econOpenLog()">
  <span class="cc-row cc-coin"><svg data-icon="coin" data-size="md"></svg><span class="coin-chip-num" id="coin-chip-num">0</span></span>
  <span class="coin-chip-silver cc-row" id="coin-chip-silver"></span>
</button>""")
once("""  if(se){ se.hidden = !(sb > 0); se.innerHTML = ECON_SILVER_SVG + '<b>' + econFmt(sb) + '</b>'; if(sb > 0) chip.setAttribute('aria-label', 'رصيد الكوينز ' + econFmt(b) + ' ورصيد الفضة ' + econFmt(sb) + ' — افتح سجل الكوينز'); }""",
     """  if(se){ se.hidden = false; se.innerHTML = ECON_SILVER_SVG + '<b>' + econFmt(sb) + '</b>'; chip.setAttribute('aria-label', 'رصيد الكوينز ' + econFmt(b) + ' ورصيد الفضة ' + econFmt(sb) + ' — افتح سجل الكوينز'); }   /* CODIS-FINANCE: سطران ثابتان */""")
once("  store: { id:'icon-store', meaning:'المتجر', size:'md',", """  wallet: { id:'icon-wallet', meaning:'الإدارة المالية', size:'md',
    body:'<path d="M5 7.2h12.4a1.6 1.6 0 0 1 1.6 1.6v9a1.6 1.6 0 0 1-1.6 1.6H6.6A1.6 1.6 0 0 1 5 17.8Z"/><path d="M5 7.2v-.8a1.6 1.6 0 0 1 1.6-1.6H15"/><path d="M15.4 12.6H19v3.4h-3.6a1.7 1.7 0 0 1 0-3.4Z"/>' },
  plus: { id:'icon-plus', meaning:'إضافة', size:'md',
    body:'<path d="M12 5v14M5 12h14"/>' },
  store: { id:'icon-store', meaning:'المتجر', size:'md',""")
for _o, _n in [(".notif-bell, .store-btn, .coin-chip{", ".notif-bell, .store-btn, .fin-btn, .coin-chip{"),
               (".notif-bell:active, .store-btn:active, .coin-chip:active", ".notif-bell:active, .store-btn:active, .fin-btn:active, .coin-chip:active"),
               (".notif-bell:hover, .store-btn:hover, .coin-chip:hover", ".notif-bell:hover, .store-btn:hover, .fin-btn:hover, .coin-chip:hover")]:
    assert s.count(_o) >= 1, _o
    s = s.replace(_o, _n)
s = s.replace(".notif-bell, .store-btn, .coin-chip{ color:var(--text-2); }", ".notif-bell, .store-btn, .fin-btn, .coin-chip{ color:var(--text-2); }")
s = s.replace(".notif-bell::after, .store-btn::after, .coin-chip::after{", ".notif-bell::after, .store-btn::after, .fin-btn::after, .coin-chip::after{")
s = s.replace(".notif-bell:active, .store-btn:active, .coin-chip:active, .btn-primary:hover", ".notif-bell:active, .store-btn:active, .fin-btn:active, .coin-chip:active, .btn-primary:hover")

# ---- طبقة الإدارة المالية + أقسام الصفحات + زر الرجوع ----
once("""    <!-- ============ قسم: المظهر (CODIS-THEME) ============ -->""", """    <!-- ============ CODIS-FINANCE: الإدارة المالية (طبقة مثل المتجر وسجل الكوينز) ============ -->
    <div id="settings-page-eco-fin" class="settings-page-section" style="display:none;">
      <button type="button" class="settings-back-btn" onclick="econCloseStore()"><svg class="ios-chevron" data-icon="back"></svg>رجوع</button>
      <div class="settings-section-head">
        <div class="settings-section-title">الإدارة المالية</div>
      </div>
      <div class="settings-grid" id="fin-body"></div>
    </div>

    <!-- ============ قسم: المظهر (CODIS-THEME) ============ -->""")
once("const ECON_PAGES = { 'eco-store':'econRenderStore', 'eco-log':'econRenderLog',", "const ECON_PAGES = { 'eco-store':'econRenderStore', 'eco-log':'econRenderLog', 'eco-fin':'finRender',")
once("  if(open('codis-confirm-modal')) return L('codis-confirm-modal', ()=>resolveCodisConfirm(false));   /* CODIS-CLARITY: التأكيد يعلو الأوراق */",
     "  if(open('codis-confirm-modal')) return L('codis-confirm-modal', ()=>resolveCodisConfirm(false));   /* CODIS-CLARITY: التأكيد يعلو الأوراق */\n  if(CodisFinUI.isOpen()) return { act:CodisFinUI.closeTop, el:CodisFinUI.el() };   /* CODIS-FINANCE */")

once("document.addEventListener('keydown', ev=>{ if(ev.key === 'Escape' && econStoreSaved && !econDetailId",
     "document.addEventListener('keydown', ev=>{ if(ev.key === 'Escape' && econStoreSaved && !CodisFinUI.isOpen() && !econDetailId")   # CODIS-FINANCE: Esc يغلق ورقة الإدارة المالية أولاً لا الطبقة كلها

# ---- CSS ----
i = s.index('<style id="codis-v38-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v41-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v41 ok', len(s))
