"""CODIS-V34 (3.21.0) — إعادة هندسة غرفة التأديب.

  py -3 tools/patch_v34.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (بعد patch_v33؛ ثم set_version.py)

  1  عملات كسرية (منزلتان عشريتان؛ تقريب لأقرب 0.01 بعد كل عملية) عبر المحفظة/المخزون/القرارات/العرض — الأرصدة القديمة تبقى كما هي
  2  بطاقات ثابتة القيمة كعناصر حقيقية بالكتالوج (متجر/مخزون/إعدادات): محطة 7 أيام 12.5 · مقاومة 18.75/37.5/125 · محطة 30 يوم 75/100/200 ·
     عقوبات محطة العادات 31.25/62.5/125 · عقوبات حدثية 112.5/225/750 (بلا احتمالات)
  3  محطة السبعة أيام = مكافأة مالية حقيقية + تعويض مرة واحدة للمحطات القديمة + عقوبات دورة السبعة أيام + بطاقات تجاوز العادة بالقيم الجديدة
  4  عادة أسبوعية بأيام فعلية، بلا تراجع
  5  عادة حدثية: مكافأة/عقوبة ثابتة بالأهمية؛ لا خصم تلقائي (lapseCoins ملغى)
  6  فصل غرفة التأديب عن التقييم الأسبوعي/الشهري للتخطيط
  7  تذكيرات Web Push (23:00 يومي، يوم العادة الأسبوعية 09:00) عبر push_timers
"""
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-V34' not in s, 'already applied'

def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:100])
    s = s.replace(old, new)
def many(old, new, minimum=1):
    global s
    n = s.count(old); assert n >= minimum, ('anchor missing', old[:100]); s = s.replace(old, new); print('  x%d' % n, old[:60])
def fn_slice(start, end):
    i = s.index(start); j = s.index(end, i + 1); return i, j
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()

# ---------------------------------------------------------------- module
mod = rd('v34.js') + '\n' + rd('v34b.js')
once('/* ================= CODIS DISCIPLINE — أداء العادات الأسبوعي والتقارير', '/* ===== CODIS-V34 ===== */\n' + mod + '\n/* ================= CODIS DISCIPLINE — أداء العادات الأسبوعي والتقارير')

once("['habit.sameDay', 'العادة الأسبوعية تُحتسب مرة واحدة باليوم'],", "['habit.sameDay', 'العادة الأسبوعية تُحتسب مرة واحدة باليوم'], ['habit.schedule', 'العادة الأسبوعية تُسجَّل فقط بأيام جدولها'],")
once("build:{ E:'عادة أمارسها كل يوم — سلسلة مستمرة، ومكافأة كل 7 أيام متتالية.', W:'عدد مرات محدد بالأسبوع بدون أيام ثابتة — مكافأة إذا تحقق، وعقوبة إذا لا.' },",
     "build:{ E:'عادة أمارسها كل يوم — سلسلة مستمرة، ومحطة مكافأة كل 7 أيام متتالية، وعقوبة بنهاية دورة السبعة أيام إذا كثرت الإخفاقات.', W:'أيام ثابتة تختارها — تسجّل إنجازك مرة واحدة في كل يوم منها، ويصلك تذكير بداية اليوم.' },")
once("quit:{  E:'عادة سيئة أمتنع عنها كل يوم — أسجّل نجاح اليوم، ومكافأة كل 7 أيام نظيفة، وعقوبة عند الإخفاق.', H:'عادة سيئة تحدث عند موقف معيّن — عداد أيام بدون وقوع، ومكافأة كل 30 يوماً.' }",
     "quit:{  E:'عادة سيئة أمتنع عنها كل يوم — أسجّل نجاح اليوم، ومحطة مكافأة كل 7 أيام نظيفة، وعقوبة بنهاية دورة السبعة أيام إذا كثرت الإخفاقات.', H:'عادة سيئة تحدث عند موقف معيّن — عداد أيام بدون وقوع، ومكافأة ثابتة عند «قاومت» وكل 30 يوماً، وعقوبة ثابتة عند الوقوع بحسب الأهمية.' }")
once("لا عادات محتسبة هذا الأسبوع — النتيجة من الخطة وحدها.", "غرفة التأديب مستقلة — النتيجة من الخطة وحدها.")
once("(it.coinBypassCost === null ? ' (حسب الشدة)' : '')", "(it.coinBypassCost === null && !it.fixed ? ' (حسب الشدة)' : '')")
# ---------------------------------------------------------------- 1) coins
once("function econFmt(n){ return String(Math.trunc(Number(n) || 0)).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ','); }",
     "function econFmt(n){ n = econC(n); const neg = n < 0, p = Math.abs(n).toFixed(2).split('.'); const f = p[1].replace(/0+$/, ''); return (neg ? '-' : '') + p[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',') + (f ? '.' + f : ''); }   /* CODIS-V34: 12.50 ← 12.5 · 18.75 كما هي */")
once("'PURCHASE_HOLIDAY_CARD','HABIT_LAPSE']", "'PURCHASE_HOLIDAY_CARD','HABIT_LAPSE','HABIT_COMPENSATION']")
once("type:t.type, amount:Math.trunc(t.amount), reason:", "type:t.type, amount:econC(t.amount), reason:")
once("d.wallet = { balance:econNum(w.balance, 0, 0, 1e12, true), lifetimeEarned:econNum(w.lifetimeEarned, 0, 0, 1e12, true), lifetimeSpent:econNum(w.lifetimeSpent, 0, 0, 1e12, true), transactions:txs,",
     "d.wallet = { balance:econCN(w.balance, 0, 0, 1e12), lifetimeEarned:econCN(w.lifetimeEarned, 0, 0, 1e12), lifetimeSpent:econCN(w.lifetimeSpent, 0, 0, 1e12), transactions:txs,")
once("coinValue:econNum(x.coinValue, 0, 0, 1000000, true), paid:(x.paid === null || x.paid === undefined) ? null : econNum(x.paid, 0, 0, 1000000, true) };\n    if(status === 'sold'){ it.soldFor = econNum(x.soldFor, 0, 0, 1000000, true);",
     "coinValue:econCN(x.coinValue, 0, 0, 1000000), paid:(x.paid === null || x.paid === undefined) ? null : econCN(x.paid, 0, 0, 1000000) };\n    if(status === 'sold'){ it.soldFor = econCN(x.soldFor, 0, 0, 1000000);")
once("coinValue:econNum(o.coinValue, 0, 0, 1000000, true), paid:(o.paid === null || o.paid === undefined) ? null : econNum(o.paid, 0, 0, 1000000, true) };",
     "coinValue:econCN(o.coinValue, 0, 0, 1000000), paid:(o.paid === null || o.paid === undefined) ? null : econCN(o.paid, 0, 0, 1000000) };")
once("Math.max(0, Math.min(v, it.paid - 1))", "Math.max(0, Math.min(v, econC(it.paid - 1)))")
once("    amount = Math.trunc(Number(amount));\n    if(!isFinite(amount) || amount === 0) return null;\n    const w = data.wallet;\n    if(w.balance + amount < 0){",
     "    amount = econC(amount);\n    if(amount === 0) return null;\n    const w = data.wallet;\n    if(econAddC(w.balance, amount) < 0){")
once("const need = -(w.balance + amount);", "const need = econC(-econAddC(w.balance, amount));")
once("w.balance += need; w.lifetimeEarned += need;", "w.balance = econAddC(w.balance, need); w.lifetimeEarned = econAddC(w.lifetimeEarned, need);")
once("const tx = { id:econUid('tx'), type:type, amount:amount,", "const tx = { id:(meta && meta.txId) ? String(meta.txId).slice(0, 60) : econUid('tx'), type:type, amount:amount,")
once("    w.balance += amount;\n    if(amount > 0) w.lifetimeEarned += amount; else w.lifetimeSpent += -amount;",
     "    w.balance = econAddC(w.balance, amount);\n    if(amount > 0) w.lifetimeEarned = econAddC(w.lifetimeEarned, amount); else w.lifetimeSpent = econAddC(w.lifetimeSpent, -amount);")
many("Math.max(0, Math.trunc(Number(e.bypassCost) || 0))", "econC(Math.max(0, Number(e.bypassCost) || 0))")
many("Math.max(0, Math.trunc(Number(e.coinValue) || 0))", "econC(Math.max(0, Number(e.coinValue) || 0))")
many("Math.max(0, Math.trunc(Number(o.price !== undefined ? o.price : e.coinValue) || 0))", "econC(Math.max(0, Number(o.price !== undefined ? o.price : e.coinValue) || 0))")
many("Math.max(0, Math.trunc(Number(o.coin) || 0))", "econC(Math.max(0, Number(o.coin) || 0))")
many("Math.trunc(Number(e && e.coinValue) || 0)", "econC(Number(e && e.coinValue) || 0)")
many("need:cost - CodisWallet.balance()", "need:econC(cost - CodisWallet.balance())")
many("need:price - CodisWallet.balance()", "need:econC(price - CodisWallet.balance())", 0)
once("function econSellValue(coin){\n  coin = Math.trunc(Number(coin) || 0);\n  if(coin <= 1) return 0;\n  return Math.max(1, Math.min(coin - 1, Math.floor(coin * econCfg().sellPercent / 100)));\n}",
     "function econSellValue(coin){\n  coin = econC(coin);\n  if(coin <= 1) return 0;\n  if(Number.isInteger(coin)) return Math.max(1, Math.min(coin - 1, Math.floor(coin * econCfg().sellPercent / 100)));   /* القيم الصحيحة القديمة: السلوك نفسه حرفياً */\n  return Math.max(0.01, Math.min(econC(coin - 1), Math.floor(coin * econCfg().sellPercent) / 100));\n}")

# ---------------------------------------------------------------- 2) fixed cards in the catalog
once("function econEffCoin(item, rar){ if(item && item.room === 'learn') return ECON_LEARN_COIN;", "function econEffCoin(item, rar){ if(item && item.fixed && item.fixedCoin > 0) return item.fixedCoin; if(item && item.room === 'learn') return ECON_LEARN_COIN;")
once("function econEffStore(item, rar){\n  return econAutoStore(econEffCoin(item, rar));",
     "function econEffStore(item, rar){\n  if(item && item.fixed && item.fixedStore > 0) return item.fixedStore;   /* محطة السبعة أيام: سعرها = قيمتها بلا زيادة المتجر */\n  return econAutoStore(econEffCoin(item, rar));")
once("function econPenaltyCost(item){ return econBypassFor(", "function econPenaltyCost(item){ if(item && item.fixed && item.fixedCost > 0) return item.fixedCost; return econBypassFor(")
once("coinBypassCost:null,\n      enabled:x.enabled !== false, room:room, createdAt:typeof x.createdAt === 'string' ? x.createdAt : now, updatedAt:typeof x.updatedAt === 'string' ? x.updatedAt : now };\n  });\n}",
     "coinBypassCost:null,\n      enabled:x.enabled !== false, room:room, createdAt:typeof x.createdAt === 'string' ? x.createdAt : now, updatedAt:typeof x.updatedAt === 'string' ? x.updatedAt : now };\n  });\n  codisV34Seed(settings);   /* CODIS-V34: البطاقات الثابتة (آمن وقت التحميل: دوال فقط) */\n}")
once("function poolOf(room){ return data.settings.rewardItems.filter(x=>x.enabled && x.room === room); }", "function poolOf(room){ return data.settings.rewardItems.filter(x=>x.enabled && x.room === room && !x.fixed); }")
once("const enabled = data.settings.punishItems.filter(x=>x.enabled && x.room === room);", "const enabled = data.settings.punishItems.filter(x=>x.enabled && x.room === room && !x.fixed);")
once("function pool(){ return data.settings.rewardItems.filter(x=>x.enabled && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0); }",
     "function pool(){ return data.settings.rewardItems.filter(x=>x.enabled && !x.fixed && econRarityById(x.rarity) && CodisEconomy.storePrice(x) > 0); }   /* الثابتة خارج البكجات: لا تمسّ نموذج الاحتمالات */")
# passes: habit-scope prices follow the new 7-day penalties; event penalties never take a pass
once("function fits(p, e){ return !!(p && e && e.kind === 'punish' && p.scope === e.scope &&", "function fits(p, e){ return !!(p && e && e.kind === 'punish' && !e.noPass && p.scope === e.scope &&")
once("function price(p){ return p ? econBypassFor(", "function price(p){ if(p && p.scope === 'habit') return ({ LOW:31.25, MEDIUM:62.5, HIGH:125 })[econNormSeverity(p.severity, 'MEDIUM')] || 62.5; return p ? econBypassFor(")

# special card rendering (art or neutral placeholder)
once("  holidayExtra: { ar:0.8, w:800, h:1000, plate:[21, 78.4, 58, 10] }\n};", "  holidayExtra: { ar:0.8, w:800, h:1000, plate:[21, 78.4, 58, 10] },\n  plain:        { ar:0.8, w:800, h:1000, plate:[10, 41, 80, 18] }   /* CODIS-V34: بطاقة بلا صورة بعد — تصميم موحّد حتى تُضاف */\n};")
once("'<img class=\"rwc-art scx-art\" src=\"' + CodisArt.src(CODIS_SPECIAL_CARD_ART[k]) + '\" alt=\"\" draggable=\"false\">' + codisStickerLayerHtml(o, 's', k) +",
     "(CODIS_SPECIAL_CARD_ART[k] ? '<img class=\"rwc-art scx-art\" src=\"' + CodisArt.src(CODIS_SPECIAL_CARD_ART[k]) + '\" alt=\"\" draggable=\"false\">' : '<div class=\"rwc-art scx-ph scx-ph-' + escapeHtml(String(o.tone || 'normal')) + '\" aria-hidden=\"true\"></div>') + codisStickerLayerHtml(o, 's', k) +")
once("function codisHabitSpecialKey(e){ return e && e.kind === 'reward' && e.scope === 'habit' ? (e.periodic === 'resist' ? 'resistance' : 'milestone') : null; }",
     "function codisHabitSpecialKey(e){ if(!(e && e.kind === 'reward' && e.scope === 'habit')) return null; if(e.fixedId){ const d = codisFixedById(e.fixedId); return d && d.art ? d.art : 'plain'; } return e.periodic === 'resist' ? 'resistance' : 'milestone'; }")
once("return codisSpecialCardHtml(k, { name:name, coin:coin, plain:o.plain, label:o.label ||", "return codisSpecialCardHtml(k, { name:name, coin:coin, plain:o.plain, tone:(e.fixedId && (codisFixedById(e.fixedId) || {}).imp) || 'normal', label:o.label ||")
once("function econStoreFaceHtml(it, rar, o){\n  o = o || {};", "function econStoreFaceHtml(it, rar, o){\n  o = o || {};\n  if(it && it.fixed) return codisHabitSpecialCardHtml({ kind:'reward', scope:'habit', fixedId:it.id, item:it.name, coinValue:it.fixedCoin }, { plain:true, price:o.price, label:o.label });")

# ---------------------------------------------------------------- 6) decoupling
once("const hs = CodisDiscipline.weekStats(arch.weekId), pw = cx.planWeight, hw = hs.pct === null ? 0 : cx.habitWeight;\n    const overall = hs.pct === null ? st.pct : Math.round((st.pct * pw + hs.pct * hw) / ((pw + hw) || 1));",
     "const hs = Object.assign({}, CodisDiscipline.weekStats(arch.weekId), { items:[], counted:0, pct:null });   /* CODIS-V34: غرفة التأديب مستقلة — لا تدخل العادات بنتيجة الخطة ولا بتقريرها */\n    const overall = st.pct;")
once("r.notes.push('لا توجد عادات قابلة للحساب لهذا الأسبوع، فبنيت النتيجة على الخطة وحدها.');", "r.notes.push('نتيجة الأسبوع تعكس الخطة فقط — غرفة التأديب لها تقييمها ومكافآتها وعقوباتها المستقلة.');")
once("const ents = Object.keys(L()).map(k=>L()[k]).filter(e=>e.scope !== 'monthly' && e.status !== 'void' && entryMonth(e) === m);", "const ents = Object.keys(L()).map(k=>L()[k]).filter(e=>e.scope !== 'monthly' && e.scope !== 'habit' && e.status !== 'void' && entryMonth(e) === m);   /* V34: نتائج التأديب خارج التقييم الشهري */")
i = s.index("    const hp = wk.filter(e=>e.stats && typeof e.stats.habitPct === 'number');"); j = s.index("    parts.push({ k:'punish'", i)
s = s[:i] + "    /* V34: أداء العادات لا يدخل التقييم الشهري للتخطيط */\n" + s[j:]

# ---------------------------------------------------------------- 3,5) habit flows
once("function runHabitChecks(){\n", "function runHabitChecks(){\n  try{ codisV34Daily(); }catch(e){ console.error('v34 daily', e); }\n")
# 30-day station: fixed by importance, no rolls
i = s.index("  data.habits.quit.filter(h=>h.type === 'H').forEach(h=>{   /* المعالم الشهرية للحدثية فقط"); j = s.index("  if(!changed) return;\n  saveData();\n  out.forEach(", i)
s = s[:i] + r"""  data.habits.quit.filter(h=>h.type === 'H').forEach(h=>{   /* المعالم الشهرية للحدثية فقط — V34: مكافأة ثابتة بحسب الأهمية كل 30 يوماً بلا وقوع */
    const n = Math.floor(hDays(h)/30), rk = hRunKey(h);
    for(let k=1;k<=n;k++){
      const key = rk+':'+k; if(h.monthlyMilestones[key]) continue;
      const def = codisV34Ms30Def(h), re = def ? codisFixedOutcome(['habit', h.id, 'hm:' + key, 'reward'].join('|'), 'reward', def, codisHabitFixedCtx(h, (k*30) + ' يوماً بدون وقوع — «' + h.text + '»')) : null, r = (re && re.entry) ? re.entry.item : '';
      h.monthlyMilestones[key] = { date:today, days:k*30, reward:r }; changed = true;
      out.push({ kind:'reward', ev:'HABIT_H_MILESTONE', p:{ id:h.id, text:h.text, importance:habitImportance(h), key:key, detail:(k*30)+' يوماً'+(r ? ' — '+r : '') }, detail:(k*30)+' يوماً بدون وقوع'+(r ? ' — '+r : ''), entryId:(re && re.entry && re.isNew) ? re.entry.id : null });
    }
  });
""" + s[j:]
# daily habit toggle: real station reward + void on undo
once("  codisJustChangedId = id; codisHaptic(8);\n  if(was) delete h.log[key]; else h.log[key] = true;",
     "  codisJustChangedId = id; codisHaptic(8);\n  if(was){ const s0 = buildStreak(h); if(s0 > 0 && s0 % 7 === 0){ const mk0 = streakStart(h, s0) + ':' + s0; if(h.milestones[mk0] && h.milestones[mk0].v34 && CodisEconomy.voidIfPending(codisStationId(h, mk0))) delete h.milestones[mk0]; } }   /* V34: تراجع قبل الاستلام يلغي المحطة فلا تُمنح قبل اكتمال سبعة أيام فعلاً */\n  if(was) delete h.log[key]; else h.log[key] = true;")
once("        h.milestones[mk] = { date:key, reward:'' };\n        CodisMotion.milestone(h.id);",
     "        h.milestones[mk] = { date:key, reward:'', v34:true };\n        { const sr = codisV34StationReward(h, mk); if(sr && sr.entry) h.milestones[mk].reward = sr.entry.item; }   /* V34: استحقاق مالي حقيقي بمعرّف فريد لكل محطة */\n        CodisMotion.milestone(h.id);")
# event habit + weekly: replace whole functions (new versions live in the module)
i = s.index("function logWeeklyHabit(id, delta){   // W: +1 / -1 (undo) inside the current week"); j = s.index("/* ---- rendering: each card shows only what belongs to its type ---- */", i)
s = s[:i] + s[j:]
once("occurred:(coins)=>({ title:'تسجيل وقوع بالعادة؟', message:'العداد يبدأ من جديد ويدخل التقييم الأسبوعي.' + (coins > 0 ? ' وتُخصم ' + coins + ' كوين من رصيدك (لا ينزل تحت الصفر).' : '') + ' السجل السابق يبقى محفوظ.',",
     "occurred:(coins)=>({ title:'تسجيل وقوع بالعادة؟', message:'العداد يبدأ من جديد.' + (coins > 0 ? ' ستظهر لك عقوبة تنفّذها أو تتجاوزها بدفع ' + econFmt(coins) + ' كوين — ولا يُخصم شيء قبل قرارك.' : '') + ' السجل السابق يبقى محفوظ.',")
once("    Object.assign(h, { milestones:{}, misses:[], doneEvents:{}, checkedThrough:yesterdayKey() });", "    Object.assign(h, { milestones:{}, misses:[], doneEvents:{}, checkedThrough:yesterdayKey(), c7:todayKey() });")
once("    const n = Math.max(1, Math.min(7, parseInt((document.getElementById('new-habit-weekly')||{}).value,10) || 1));\n    Object.assign(h, { requiredPerWeek:n, weeklyLogs:{}, weekHistory:[], firstFullWeek:firstFullWeekFor(todayKey()) });",
     "    const dys = codisWDaysOk(newHabitDays); if(!dys.length){ codisSfx('invalid'); showToast('اختر يوماً واحداً على الأقل لهذه العادة', 'var(--warning)'); return; }\n    Object.assign(h, { requiredPerWeek:dys.length, days:dys, weeklyLogs:{}, weekHistory:[], firstFullWeek:firstFullWeekFor(todayKey()) });")
once("if(wf) wf.style.display = (habitMode==='build' && newHabitType==='W') ? 'block' : 'none';", "if(wf) wf.style.display = (habitMode==='build' && newHabitType==='W') ? 'block' : 'none';\n  renderNewHabitDays();")
once("const wk = document.getElementById('new-habit-weekly'); if(wk) wk.value = 3;", "newHabitDays = [];")
once('''          <div id="hb-weekly-field" style="display:none;">
            <label class="field-label" for="new-habit-weekly">كم مرة بالأسبوع؟</label>
            <input type="number" id="new-habit-weekly" min="1" max="7" value="3" inputmode="numeric">
          </div>''', '''          <div id="hb-weekly-field" style="display:none;">
            <div class="field-label" id="new-habit-days-l">أيام العادة</div>
            <div class="hb-days" id="new-habit-days" role="group" aria-labelledby="new-habit-days-l"></div>
            <div class="hb-hint">اختر الأيام التي تمارس فيها العادة — يتفعّل زر التسجيل فيها فقط، ويصلك تذكير بداية كل يوم منها.</div>
          </div>''')
# weekly card
i = s.index("    const todayDone = ((h.weeklyLogs[wk]||[]).indexOf(today) !== -1);"); j = s.index("  } else {\n    const days = hDays(h), best", i)
s = s[:i] + r"""    const dset = codisWDaysOk(h.days), isDay = dset.indexOf(codisTodayIdx()) !== -1, todayDone = ((h.weeklyLogs[wk]||[]).indexOf(today) !== -1), can = isDay && !todayDone;
    extra = '<div class="hb-state '+(todayDone?'is-ok':isDay?'is-open':'')+'">'+(!dset.length ? 'حدّد أيام هذه العادة لتبدأ التسجيل' : todayDone ? 'اليوم: سُجّل ✓' : isDay ? 'اليوم موعد العادة — سجّل إنجازك ('+c+' من '+req+')' : 'ليس يوم هذه العادة — أيامها: '+codisWDaysLabel(dset))+'</div>' + (dset.length ? '' : habitDaysEditorHtml(h));
    meta += (dset.length ? '<span class="hb-days-wrap">أيام العادة '+habitDaysEditorHtml(h)+'</span>' : '');
    action = '<button type="button" class="stat-btn stat-done '+(todayDone?'active':'')+'" aria-pressed="'+todayDone+'"'+(can?'':' disabled aria-disabled="true"')+' aria-label="سجّل إنجاز اليوم" title="سجّل إنجاز اليوم"><span class="stat-ico">'+ICONS.check+'</span><span class="hbx-lab">'+(todayDone ? 'سُجّلت اليوم' : 'سجّل إنجاز اليوم')+'</span></button>';
""" + s[j:]
once("main.onclick = ()=>logWeeklyHabit(h.id, 1); const u = row.querySelector('[data-undo]'); if(u) u.onclick = ()=>logWeeklyHabit(h.id, -1);", "main.onclick = ()=>logWeeklyHabit(h.id, 1);")
once("  row.querySelector('.task-del').onclick = ()=>removeHabit(kind, h.id);\n  return { row:row", "  row.querySelectorAll('[data-hday]').forEach(b=>{ b.onclick = ()=>setHabitDay(h.id, Number(b.dataset.hday)); });\n  row.querySelector('.task-del').onclick = ()=>removeHabit(kind, h.id);\n  return { row:row")
once("  updatePlanBar();   /* العادات اليومية جزء من شريط الأسبوع */\n}", "  updatePlanBar();   /* العادات اليومية جزء من شريط الأسبوع */\n  try{ CodisHabitPush.kick(); }catch(e){}   /* V34: أي تغيير بالعادات يحدّث التذكيرات الخلفية */\n}")

# ---------------------------------------------------------------- settings UI
def edit_fn(start, end, fn):
    global s
    i = s.index(start); j = s.index(end, i); s = s[:i] + fn(s[i:j]) + s[j:]
def rowfix(t):
    t = t.replace("ed = econEditing === it.id;", "ed = econEditing === it.id && !it.fixed;")
    a = t.index("'<button type=\"button\" class=\"chip-act\" onclick=\"econEdit("); b = t.index("</button>' +", a) + len("</button>' +")
    t = t[:a] + "(it.fixed ? '<span class=\"eco-fixed-tag\">ثابتة</span>' : " + t[a:b-2].rstrip() + ") +" + t[b:]
    a = t.index("'<button type=\"button\" class=\"chip-del\""); b = t.index("ICONS.trash + '</button></div>' +", a)
    t = t[:a] + "(it.fixed ? '' : " + t[a:b] + "ICONS.trash + '</button>') + '</div>' +" + t[b + len("ICONS.trash + '</button></div>' +"):]
    return t
edit_fn("function econRewardRowHtml(it){", "/* CODIS-CLARITY: كل قائمة تُرسم بقسمها", rowfix)
edit_fn("function econPunishRowHtml(it){", "function econRenderPunish(){", rowfix)
once("const items = all.filter(x=>x.room === room).sort(sortFn);", "const items = all.filter(x=>x.room === room && x.fixedGroup !== 'event').sort(sortFn);   /* V34: عقوبات الحدثية ثابتة بقسمها المستقل */")
once("room=>room === 'weekly' ? 'ماكو عقوبات أسبوعية' : room === 'monthly' ? 'ماكو عقوبات شهرية' : 'ماكو عقوبات بـ«' + econRoomLabel(room) + '»');\n}",
     "room=>room === 'weekly' ? 'ماكو عقوبات أسبوعية' : room === 'monthly' ? 'ماكو عقوبات شهرية' : 'ماكو عقوبات بـ«' + econRoomLabel(room) + '»');\n  codisFillEventPenalties();\n}\nfunction codisFillEventPenalties(){\n  const list = document.getElementById('punish-list-event'); if(!list) return;\n  const rows = data.settings.punishItems.filter(x=>x.fixedGroup === 'event').sort((a, b)=>(a.fixedCost || 0) - (b.fixedCost || 0));\n  list.innerHTML = rows.map(econPunishRowHtml).join('');\n  const sec = list.closest('.rpu-sec'), c = sec && sec.querySelector('[data-count]'); if(c) c.textContent = 'العدد ' + rows.length + ' · ثابتة القيمة';\n}")
once('''      <div hidden id="rpu-stash"><div id="reward-add-box"></div><div id="punish-add-box"></div></div>''',
     '''      <div hidden id="rpu-stash"><div id="reward-add-box"></div><div id="punish-add-box"></div></div>''')
once('''          <div class="eco-list rpu-list" id="punish-list-monthly"></div>
        </section>''', '''          <div class="eco-list rpu-list" id="punish-list-monthly"></div>
        </section>
        <section class="rpu-sec" id="rpu-p-event" data-period="event" aria-labelledby="rpu-p-event-h">
          <header class="rpu-head">
            <span class="rpu-ico" aria-hidden="true"><svg data-icon="warning" data-size="md"></svg></span>
            <div class="rpu-ht"><h3 class="rpu-h" id="rpu-p-event-h">عقوبات العادات الحدثية</h3><span class="rpu-sub" data-count></span></div>
          </header>
          <p class="rpu-note">ثلاث عقوبات ثابتة بحسب أهمية العادة (عادية · مهمة · حرجة). تظهر عند «وقعت بها» ولا يُخصم شيء قبل أن تقرر: تنفيذها أو دفع قيمتها.</p>
          <div class="eco-list rpu-list" id="punish-list-event"></div>
        </section>''')
once("async function econDeleteReward(id){\n  const it = data.settings.rewardItems.find(x=>x.id === id); if(!it) return;", "async function econDeleteReward(id){\n  const it = data.settings.rewardItems.find(x=>x.id === id); if(!it || it.fixed) return;")

# ---------------------------------------------------------------- stylesheet
css = rd('v34.css')
assert '</style' not in css
once('<script>\n/* CODIS-V33: long-press on content', '<style id="codis-v34-css">\n' + css + '</style>\n<script>\n/* CODIS-V33: long-press on content')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v34 ok', len(s))
