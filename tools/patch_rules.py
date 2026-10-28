"""CODIS-RULES: economy integrity + habit rules. Run AFTER tools/patch_power.py:  python tools/patch_rules.py <in> <out>

Root causes found by tracing the real code (not assumed):
 1. BOXES — effective() fitted each tier's distribution only to its own RTP target, so the lowest class got 84% / 99% / 98% / 65% / 92% across the 5 tiers.
 2. REWARD CARDS — CodisRewardEngine.rarityTable() re-normalised the rarity odds over only the rarities that still had cards (and were enabled): delete or disable the
    weak cards and the 0.6% legendary became 100%. Rarity coin values are fixed, so the only lever was this renormalisation.
 3. TASKS — outcome ids contain the plan's startedAt: starting another plan in the SAME week minted brand-new daily/weekly ids (infinite rewards); future days could be
    completed on day 1; the monthly early-settle counted weekly ENTRIES (4 quick plans = a monthly reward).
 4. HABITS — logWeeklyHabit pushed todayKey() every click (3 clicks = 3 "days"); resistReward was hard-forced to false; a lapse had no consequence of its own.
All new restrictions go through CodisLimits (CLAUDE.md → ADMIN EXEMPTION RULE), so the verified developer is never limited."""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-RULES' not in t, 'rules patch already applied'
assert 'CODIS-POWER' in t, 'run tools/patch_power.py first'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:100]!r}'
    t = t.replace(old, new)

# ---------- register the new limits (labels shown in the developer panel) ----------
rep("['box.prune', 'قصّ سجل البكجات المفتوحة عند 100']].forEach(a=>CodisLimits.reg(a[0], a[1]));",
    "['box.prune', 'قصّ سجل البكجات المفتوحة عند 100'],\n"
    " ['reward.protectedOdds', 'حماية احتمالات الندرة (حذف/تعطيل الكروت لا يغيّر الاحتمالات)'], ['claim.crossPlan', 'منع تكرار مكافأة نفس اليوم/الأسبوع عند بدء خطة جديدة'],\n"
    " ['task.futureDay', 'منع إنجاز مهام يوم لم يأتِ بعد'], ['habit.sameDay', 'العادة الأسبوعية تُحتسب مرة واحدة باليوم'], ['habit.resistCap', 'حدّ مكافآت «قاومت» اليومي'],\n"
    " ['claim.lateCap', 'حدّ مكافآت أيام التعويض (يوم فائت واحد باليوم لكل غرفة)'], ['claim.burst', 'مكافأة الأسبوع تتطلب نشاطاً على أيام مختلفة']].forEach(a=>CodisLimits.reg(a[0], a[1]));")
rep("  [['bx2', 50], ['bx3', 90], ['bx4', 165], ['bx5', 245]].forEach(",
    "  R('box.refTop', 'نسبة الفئة الأدنى بكل بكج (‰ — 827 = 82.7%)', 827);\n  R('task.weeklyMinDays', 'أقل عدد أيام مختلفة لنيل مكافأة الأسبوع', 3);\n  [['bx2', 50], ['bx3', 90], ['bx4', 165], ['bx5', 245]].forEach(")

# ================= PHASE 2: one distribution for every box =================
rep("  const PRICE_FACTOR = 0.85, KEEP_OPENED_N = 100;", "  const PRICE_FACTOR = 0.85, KEEP_OPENED_N = 100, REF_TOP = 827;   /* CODIS-RULES: نسبة الفئة الأدنى المرجعية = 82.7% لكل البكجات */")
a = t.index("    const target = t.basePrice / (PRICE_FACTOR * BOX_MARKUP);\n    const mk = b=>toPermille(")
endm = "    return cs.map((c,i)=>Object.assign({}, c, { pm:pm[i] }));\n  }"
b = t.index(endm, a) + len(endm)
assert t.count("    const target = t.basePrice / (PRICE_FACTOR * BOX_MARKUP);\n    const mk = b=>toPermille(") == 1
NEW = r"""    const target = t.basePrice / (PRICE_FACTOR * BOX_MARKUP), n = cs.length;
    const ev = p=>p.reduce((s,x,i)=>s + x / 1000 * cs[i].mean, 0);
    const win = p=>p.reduce((s,x,i)=>s + x / 1000 * cs[i].vals.filter(v=>v > t.basePrice).length / cs[i].vals.length, 0);
    /* CODIS-RULES — توزيع موحَّد لكل المستويات: الفئة الأدنى بنسبة مرجعية ثابتة (REF_TOP‰ = 82.7%)، والباقي (17.3%) على بقية الفئات بنفس عائلة التناقص الأسي
       المستعملة أصلاً (∝ المتوسط^−β) مع β يُحَلّ ليبقى العائد المتوقع عند هدف التسعير نفسه (لا يتغيّر اقتصاد البكج). إن كانت المرجعية تجعل العائد يتجاوز سقف
       RTP لمستوى معيّن (فئته الأدنى غالية نسبةً لسعره) تُرفع نسبتها بأقل مقدار لازم بدل جعل البكج «غير متاح». كل رقم مُصدَّر من هنا هو ما يسحب به roll() وما تعرضه الواجهة. */
    let pm;
    if(n === 1) pm = [1000];
    else {
      const k = n - 1, fMax = 1000 - k;
      const build = (f, b)=>{
        const raw = cs.slice(1).map(c=>Math.pow(c.mean, -b)), s = raw.reduce((x,y)=>x + y, 0) || 1, tot = 1000 - f;
        const base = raw.map(x=>x / s * (tot - k)), out = base.map(x=>1 + Math.floor(x)); let left = tot - out.reduce((x,y)=>x + y, 0);
        base.map((x,i)=>({ f:x - Math.floor(x), i:i })).sort((p,q)=>q.f - p.f || p.i - q.i).forEach(o=>{ if(left > 0){ out[o.i]++; left--; } });
        return [f].concat(out);
      };
      const ok = p=>ev(p) <= MAX_RTP_V() * t.basePrice && win(p) <= MAX_PWIN_V();
      let f = Math.min(Math.max(1, Math.round(CodisLimits.num('box.refTop', REF_TOP))), fMax);
      while(f < fMax && !ok(build(f, 14))) f += 5;
      f = Math.min(f, fMax);
      let lo = -4, hi = 14;
      for(let i = 0; i < 60; i++){ const m = (lo + hi) / 2; if(ev(build(f, m)) > target) lo = m; else hi = m; }
      pm = build(f, hi);
    }
    if((ev(pm) > MAX_RTP_V() * t.basePrice || win(pm) > MAX_PWIN_V()) && !CodisLimits.bypass('box.rtpGate')) return [];
    return cs.map((c,i)=>Object.assign({}, c, { pm:pm[i] }));
  }"""
t = t[:a] + NEW + t[b:]

# ================= PHASE 3: reward-card manipulation =================
rep("      const n = pool.filter(x=>x.rarity === r.id && wnum(x.weight) > 0).length;\n",
    "      const n = (prot && !r.enabled) ? 0 : pool.filter(x=>x.rarity === r.id && wnum(x.weight) > 0).length;   /* CODIS-RULES: ندرة معطّلة = بلا بطاقات لكن احتمالها ثابت */\n")
rep("    const rows = usableRarities().map(r=>{\n", "    const prot = !CodisLimits.bypass('reward.protectedOdds');   /* احتمالات الندرة تُحسب على كل الندرات دائماً (حذف/تعطيل الكروت لا يُركّز الاحتمال على العليا) */\n    const rows = (prot ? econCfg().rarities : usableRarities()).map(r=>{\n")
rep("    }).filter(x=>x.n > 0);\n    if(!rows.length) return [];", "    }).filter(x=>prot || x.n > 0);\n    if(!rows.length || (prot && !pool.length)) return [];   /* بلا أي بطاقة بالقائمة: السلوك القديم (مكافأة عامة بأدنى ندرة) */")
rep("    const rows = rewardTable(room, row.r.id);\n    const pick = weightedPick(rows, x=>x.w) || rows[0];",
    "    const rows = row.n > 0 ? rewardTable(room, row.r.id) : [];\n    const pick = rows.length ? (weightedPick(rows, x=>x.w) || rows[0]) : null;\n"
    "    const gcoin = pick ? 0 : (room === 'learn' ? ECON_LEARN_COIN : econCoinFor(row.r.id, econScopeOfRoom(room)));   /* ندرة بلا بطاقات: مكافأة عامة بنفس قيمة ندرتها */")
rep("reward:pick.item, rarity:row.r,", "reward:pick ? pick.item : null, genericName:pick ? '' : 'مكافأة ' + row.r.name, rarity:row.r,")
rep("coinValue:econEffCoin(pick.item, row.r), storePrice:econEffStore(pick.item, row.r) };", "coinValue:pick ? econEffCoin(pick.item, row.r) : gcoin, storePrice:pick ? econEffStore(pick.item, row.r) : econAutoStore(gcoin) };")
rep("item:r.reward ? r.reward.name : 'مكافأة', rewardId:r.reward ? r.reward.id : null,", "item:r.reward ? r.reward.name : (r.genericName || 'مكافأة'), rewardId:r.reward ? r.reward.id : null,")

# ================= PHASE 4: task farming =================
rep("  function daily(room, dayIdx, kind, pct){\n    const weekId = currentWeekId(), week = room === 'learn' ? learnCurrentWeek() : currentWeek(), planId = (week && week.startedAt) || '';\n    const id = [room, weekId, planId, dayIdx, kind].join('|');\n    if(L()[id]) return create(id, kind, 'daily', room, 'daily');\n",
    "  /* CODIS-RULES: نتيجة واحدة لكل (غرفة + أسبوع + يوم + نوع) مهما بدأ المستخدم من خطط داخل الأسبوع — معرّف الخطة كان يخلق معرّفاً جديداً فيتكرر الدفع */\n"
    "  function claimedDay(room, weekId, dayIdx, kind){ return Object.keys(L()).map(k=>L()[k]).find(e=>e && e.scope === 'daily' && e.room === room && e.weekId === weekId && e.day === dayIdx && e.kind === kind && e.status !== 'void') || null; }\n"
    "  function weekAlreadyPaid(weekId, room, exceptId){ if(CodisLimits.bypass('claim.crossPlan')) return false; return Object.keys(L()).some(k=>{ const e = L()[k]; return k !== exceptId && e && e.scope === 'weekly' && e.weekId === weekId && e.room === room && e.kind === 'reward' && e.status !== 'void'; }); }\n"
    "  function daily(room, dayIdx, kind, pct){\n    const weekId = currentWeekId(), week = room === 'learn' ? learnCurrentWeek() : currentWeek(), planId = (week && week.startedAt) || '';\n    const id = [room, weekId, planId, dayIdx, kind].join('|');\n    if(L()[id]) return create(id, kind, 'daily', room, 'daily');\n"
    "    { const dup = claimedDay(room, weekId, dayIdx, kind); if(dup && !CodisLimits.bypass('claim.crossPlan')) return { entry:dup, isNew:false }; }\n"
    "    /* أيام التعويض: دورة الخطة تلتف داخل الأسبوع فتصير أيام قبل اليوم قابلة للإنجاز دفعة واحدة. مكافأة يوم فائت واحد فقط لكل غرفة باليوم؛ مهام يومها نفسه دائماً تُكافأ */\n"
    "    const dk = dateForWeekDay(weekId, dayIdx), tk = todayKey(), late = !!(dk && dk < tk && kind === 'reward');\n"
    "    if(late){ const used = Object.keys(L()).map(k=>L()[k]).filter(e=>e && e.scope === 'daily' && e.room === room && e.late === true && e.status !== 'void' && localDateStr(new Date(e.at)) === tk).length;\n"
    "      if(used >= 1 && !CodisLimits.bypass('claim.lateCap')) return { entry:null, isNew:false }; }\n")
rep("return create(id, kind, 'daily', room, 'daily', { weekId:weekId, planId:planId || null,", "return create(id, kind, 'daily', room, 'daily', { late:late, weekId:weekId, planId:planId || null,")
# weekly reward needs activity on different calendar days (not the whole week in one day) — legacy tasks without a done-date are never penalised
rep("  function weekAlreadyPaid(weekId, room, exceptId){",
    "  function weekBurst(arch){\n    if(CodisLimits.bypass('claim.burst')) return false;\n    const seen = {}; let unknown = false, taskDays = 0;\n"
    "    [arch && arch.tasksWeek, arch && arch.learnWeek].forEach(w=>{ if(!w || !w.days) return; for(let d=0; d<7; d++){ if(d === w.holidayDay || holidayExtras(w).indexOf(d) !== -1) continue; const l = w.days[d] || []; if(l.length) taskDays++; l.forEach(x=>{ if(x && x.status === 'done'){ if(x.doneOn) seen[x.doneOn] = 1; else unknown = true; } }); } });\n"
    "    if(unknown) return false;\n    return Object.keys(seen).length < Math.min(Math.max(1, Math.trunc(CodisLimits.num('task.weeklyMinDays', 3))), taskDays);\n  }\n  function weekAlreadyPaid(weekId, room, exceptId){")
rep("cls = econClassifyPct(overall, th), success = cls === 'reward';", "cls0 = econClassifyPct(overall, th), cls = (cls0 === 'reward' && (weekAlreadyPaid(arch.weekId, cx.room, id) || weekBurst(arch))) ? 'neutral' : cls0, success = cls === 'reward';   /* دُفعت مكافأة هذا الأسبوع، أو أُنجز كله بيوم واحد: لا مكافأة */")
rep("  t.status = (t.status === status) ? null : status;\n  if(t.status === 'done') t.progress = 100;\n  else if(t.status === 'half')", "  t.status = (t.status === status) ? null : status;\n  if(t.status === 'done'){ t.progress = 100; t.doneOn = todayKey(); }   /* CODIS-RULES: تاريخ الإنجاز لقاعدة «ليس الأسبوع كله بيوم» */\n  else if(t.status === 'half')")
rep("  else t.progress = 0;\n  return t.status;", "  else t.progress = 0;\n  if(t.status !== 'done') delete t.doneOn;\n  return t.status;")
rep("t.progress = Math.max(0, Math.min(100, Math.round(opts.progress))); return t.status; }", "t.progress = Math.max(0, Math.min(100, Math.round(opts.progress))); delete t.doneOn; return t.status; }")
rep("      Object.keys(L()).forEach(k=>{ const e = L()[k]; if(e && e.scope === 'weekly' && e.status !== 'void'){ const mk = entryMonth(e); if(mk) cnt[mk] = (cnt[mk] || 0) + 1; } });",
    "      const seenW = {};   /* CODIS-RULES: أسابيع مختلفة فقط — عدّ الإدخالات كان يسمح بحسم الشهر بأربع خطط في يوم واحد */\n"
    "      Object.keys(L()).forEach(k=>{ const e = L()[k]; if(e && e.scope === 'weekly' && e.status !== 'void'){ const mk = entryMonth(e); if(mk && !seenW[mk + '|' + e.weekId]){ seenW[mk + '|' + e.weekId] = 1; cnt[mk] = (cnt[mk] || 0) + 1; } } });")
rep("function setTaskStatus(id, status, opts){\n",
    "/* CODIS-RULES: لا يُنجَز يوم لم يأتِ بعد (يُسمح بالمسح/التراجع). المطوّر معفى */\n"
    "function codisTaskDayLocked(weekId, dayIdx, t, status){\n  if(t && t.status === status) return false;\n  const dk = dateForWeekDay(weekId, dayIdx); if(!dk || dk <= todayKey()) return false;\n  if(CodisLimits.bypass('task.futureDay')) return false;\n"
    "  codisSfx('invalid'); showToast('هذا اليوم لم يأتِ بعد — تُنجَز مهامه في موعده', 'var(--warning)'); return true;\n}\n"
    "function setTaskStatus(id, status, opts){\n")
rep("      newStatus = codisApplyTaskStatus(t, status, opts);\n      break;", "      if(codisTaskDayLocked(currentWeekId(), changedDay, t, status)) return;\n      newStatus = codisApplyTaskStatus(t, status, opts);\n      break;")
rep("    if(t){ newStatus = codisApplyTaskStatus(t, status, opts); changed = true; changedDay = Number(dIdx); break; }", "    if(t){ if(codisTaskDayLocked(currentWeekId(), Number(dIdx), t, status)) return; newStatus = codisApplyTaskStatus(t, status, opts); changed = true; changedDay = Number(dIdx); break; }")

# ================= PHASE 5: weekly habit frequency =================
rep("function weekCount(h, wk){ return ((h.weeklyLogs||{})[wk]||[]).length; }",
    "/* CODIS-RULES: أيام مختلفة فقط (سجلات قديمة مكرّرة لنفس اليوم تبقى محفوظة لكن لا تُحتسب أكثر من يوم) */\nfunction weekCount(h, wk){ const a = ((h.weeklyLogs||{})[wk]||[]); return CodisLimits.bypass('habit.sameDay') ? a.length : new Set(a).size; }")
rep("  if(delta > 0) arr.push(todayKey()); else arr.pop();",
    "  if(delta > 0){\n    const tk = todayKey();\n    if(arr.indexOf(tk) !== -1 && !CodisLimits.bypass('habit.sameDay')){ codisSfx('invalid'); showToast('سجّلت هذي العادة اليوم — تُحتسب مرة واحدة باليوم، كمّل غداً', 'var(--warning)'); return; }\n    arr.push(tk);\n  } else arr.pop();")
rep("    if(c > 0) extra = '<button type=\"button\" class=\"hb-link\" data-undo=\"1\">تراجع عن آخر تسجيل</button>';\n    action = '<button type=\"button\" class=\"stat-btn stat-done '+(nameDone?'active':'')+'\" aria-label=\"سجّلت إنجازاً\" title=\"سجّلت إنجازاً\">",
    "    const todayDone = ((h.weeklyLogs[wk]||[]).indexOf(today) !== -1);\n"
    "    extra = '<div class=\"hb-state '+(todayDone?'is-ok':'is-open')+'\">'+(todayDone ? 'اليوم: سُجّل — التسجيل الجاي غداً' : (c >= req ? 'اكتمل هدف الأسبوع — تقدر تسجّل يوماً إضافياً' : 'اليوم: متاح — المتبقي '+(req-c)+' من '+req+' (يوم مختلف لكل تسجيل)'))+'</div>'\n"
    "          + (c > 0 ? '<button type=\"button\" class=\"hb-link\" data-undo=\"1\">تراجع عن آخر تسجيل</button>' : '');\n"
    "    action = '<button type=\"button\" class=\"stat-btn stat-done '+(todayDone?'active':'')+'\" aria-pressed=\"'+todayDone+'\"'+(todayDone?' aria-disabled=\"true\"':'')+' aria-label=\"'+(todayDone?'سُجّلت اليوم':'سجّلت إنجازاً')+'\" title=\"'+(todayDone?'سُجّلت اليوم':'سجّلت إنجازاً')+'\">")

# ================= PHASE 7: event habits =================
rep("habits:  { resistReward:false, monthlyReward:true, eventPenalty:50 },", "habits:  { resistReward:true, resistRewardV2:true, monthlyReward:true, eventPenalty:50, lapseCoins:10, resistDailyCap:3 },")
rep("    habits: { resistReward:false,", "    habits: { resistReward:((cx.habits || {}).resistRewardV2 === true ? (cx.habits || {}).resistReward !== false : true), resistRewardV2:true, lapseCoins:econNum((cx.habits || {}).lapseCoins, 10, 0, 100, true), resistDailyCap:econNum((cx.habits || {}).resistDailyCap, 3, 1, 20, true),")
rep("function econTxTypes(){ return ['EARN_REWARD_EXCHANGE','PURCHASE_REWARD','SELL_REWARD','PENALTY_BYPASS','ADMIN_ADJUSTMENT','PURCHASE_BOX','PURCHASE_HOLIDAY_CARD']; }",
    "function econTxTypes(){ return ['EARN_REWARD_EXCHANGE','PURCHASE_REWARD','SELL_REWARD','PENALTY_BYPASS','ADMIN_ADJUSTMENT','PURCHASE_BOX','PURCHASE_HOLIDAY_CARD','HABIT_LAPSE']; }")
rep("  return CodisEconomy.create(['habit', h.id, suffix, kind].join('|'), kind, 'habit', wk ? 'weekly' : 'habits', wk ? 'weekly' : 'daily', { habitId:h.id, habitText:h.text || '', label:label || '', periodic:wk ? 'monthlyEvent' : 'resist' });",
    "  /* CODIS-RULES: مكافأة «قاومت» صغيرة دائماً = أدنى ندرة فقط (لا تصل الندرات العليا) */\n"
    "  const small = (opts && opts.resist) ? { mult:econCfg().rarities.reduce((o, r, i)=>{ o[r.id] = i === 0 ? 1 : 0; return o; }, {}) } : null;\n"
    "  return CodisEconomy.create(['habit', h.id, suffix, kind].join('|'), kind, 'habit', wk ? 'weekly' : 'habits', wk ? 'weekly' : 'daily', { habitId:h.id, habitText:h.text || '', label:label || '', periodic:wk ? 'monthlyEvent' : 'resist' }, small);")
rep("  const rr = econCfg().contexts.habits.resistReward ? habitOutcome(h, 'rs:' + today, 'reward', 'قاومت «' + h.text + '»') : null;\n  h.resists[today] = { outcomeId:rr ? rr.entry.id : null };\n  saveData();\n  if(rr && rr.isNew) CodisOutcomeUI.enqueue(rr.entry.id, 250); else codisSfx('task.done');",
    "  let rr = null, capped = false; const hc = econCfg().contexts.habits;\n"
    "  if(hc.resistReward){\n"
    "    /* حدّ يومي على كل العادات: لا تُحصد مكافآت بإنشاء عادات كثيرة أو حذفها وإعادتها (العدّ من سجل النتائج الذي يبقى بعد الحذف) */\n"
    "    const todayN = Object.keys(data.outcomeLedger).filter(k=>{ const e = data.outcomeLedger[k]; return e && e.periodic === 'resist' && e.status !== 'void' && localDateStr(new Date(e.at)) === today; }).length;\n"
    "    if(todayN >= hc.resistDailyCap && !CodisLimits.bypass('habit.resistCap')) capped = true;\n"
    "    else rr = habitOutcome(h, 'rs:' + today, 'reward', 'قاومت «' + h.text + '»', { resist:true });\n"
    "  }\n"
    "  h.resists[today] = { outcomeId:rr ? rr.entry.id : null };\n  saveData();\n"
    "  if(rr && rr.isNew){ CodisOutcomeUI.enqueue(rr.entry.id, 250); showToast('ممتاز! مقاومة اليوم — مكافأة صغيرة بانتظارك', 'var(--success)', 'check'); }\n"
    "  else { codisSfx('task.done'); if(capped) showToast('سُجّلت المقاومة ✓ — بلغت حدّ مكافآت المقاومة اليوم (' + hc.resistDailyCap + ')', 'var(--aqua)', 'info'); }")
rep("  const ok = await codisConfirm(CodisCopy.occurred());", "  const lapseCoins = Math.max(0, Math.trunc(Number(econCfg().contexts.habits.lapseCoins) || 0));\n  const ok = await codisConfirm(CodisCopy.occurred(lapseCoins));")
rep("  codisJustChangedId = id; codisHaptic(8);\n  const days = hDays(h), pun = '';   // لا عقوبة مستقلة: الوقوع يدخل التقييم الأسبوعي",
    "  codisJustChangedId = id; codisHaptic(8);\n"
    "  /* عقوبة الوقوع: صغيرة، مرة واحدة لكل (عادة+يوم) بمعرّف مرجعي فريد، ولا تُنزل الرصيد تحت الصفر. تُنفَّذ بمعاملة ذرّية قبل تسجيل الوقوع */\n"
    "  let pen = 0;\n"
    "  if(lapseCoins > 0){\n"
    "    const lr = CodisWallet.transact([], ()=>{ const amt = Math.min(lapseCoins, Math.max(0, CodisWallet.balance())); if(amt <= 0) return { ok:true, amt:0 }; const tx = CodisWallet.apply('HABIT_LAPSE', -amt, 'وقوع بعادة «' + h.text + '»', 'habit', 'lapse|' + h.id + '|' + today, { name:h.text }); return tx ? { ok:true, amt:amt } : { ok:false, reason:'tx' }; });\n"
    "    if(!lr || !lr.ok){ codisSfx('invalid'); showToast('تعذّر تسجيل الوقوع — لم يتغيّر شي', 'var(--danger)'); return; }\n"
    "    pen = lr.amt;\n"
    "  }\n"
    "  const days = hDays(h), pun = '';   // لا عقوبة بطاقة مستقلة: الوقوع يدخل التقييم الأسبوعي + خصم الكوينز أعلاه")
rep("  h.occurrences.push({ date:today, daysBefore:days, punishment:pun }); h.lastOccurrence = today; h.log[today] = true;\n  saveData(); codisSfx('discipline.penalty');",
    "  h.occurrences.push({ date:today, daysBefore:days, punishment:pun, coins:pen }); h.lastOccurrence = today; h.log[today] = true;\n  saveData(); codisSfx('discipline.penalty');\n  showToast(pen > 0 ? 'سُجّل الوقوع — خُصم ' + econFmt(pen) + ' كوين. تكمل من جديد 💪' : 'سُجّل الوقوع — تكمل من جديد', 'var(--warning)');")
rep("'وقوع' + (o.daysBefore!=null ? ' بعد ' + o.daysBefore + ' يوم' : ''), o.date, o.punishment))", "'وقوع' + (o.daysBefore!=null ? ' بعد ' + o.daysBefore + ' يوم' : ''), o.date, o.punishment || (o.coins ? 'خُصم ' + o.coins + ' كوين' : '')))")
rep("  occurred:()=>({ title:'تسجيل وقوع بالعادة؟', message:'العداد يبدأ من جديد ويدخل التقييم الأسبوعي. السجل السابق يبقى محفوظ.', icon:'warning', confirmText:'سجّل الوقوع' }),",
    "  occurred:(coins)=>({ title:'تسجيل وقوع بالعادة؟', message:'العداد يبدأ من جديد ويدخل التقييم الأسبوعي.' + (coins > 0 ? ' وتُخصم ' + coins + ' كوين من رصيدك (لا ينزل تحت الصفر).' : '') + ' السجل السابق يبقى محفوظ.', icon:'warning', confirmText:'سجّل الوقوع' }),")
rep("    econSwitch('contexts.habits.monthlyReward', c.contexts.habits.monthlyReward, 'مكافأة شهر كامل بلا وقوع (بحجم الأسبوعية)') +",
    "    econSwitch('contexts.habits.monthlyReward', c.contexts.habits.monthlyReward, 'مكافأة شهر كامل بلا وقوع (بحجم الأسبوعية)') +\n"
    "    econSwitch('contexts.habits.resistReward', c.contexts.habits.resistReward, 'مكافأة صغيرة عند «قاومت» (مرة باليوم لكل عادة)') +\n"
    "    econField('عقوبة الوقوع (كوينز تُخصم، لا ينزل الرصيد تحت الصفر)', econNumInput('contexts.habits.lapseCoins', c.contexts.habits.lapseCoins, { min:0, max:100, label:'عقوبة الوقوع بالكوينز' })) +\n"
    "    econField('حدّ مكافآت المقاومة اليومي (لكل العادات)', econNumInput('contexts.habits.resistDailyCap', c.contexts.habits.resistDailyCap, { min:1, max:20, label:'حدّ مكافآت المقاومة اليومي' })) +")

# ================= PHASE 6: visual identity for habit importance =================
rep("const HB_EV_ICON = { ok:'check', fail:'close', partial:'half', reward:'gift' };", "const HB_EV_ICON = { ok:'check', fail:'close', partial:'half', reward:'gift' };\nconst HB_IMP_ICON = { normal:'calendar', important:'sparkle', critical:'warning' };   /* CODIS-RULES: الأهمية تظهر بالشكل والأيقونة والنص، لا باللون وحده */")
rep("  row.className = 'habit-card '+cls+(h.id===codisJustChangedId ? ' just-changed' : '');", "  row.className = 'habit-card imp-'+imp+' '+cls+(h.id===codisJustChangedId ? ' just-changed' : '');\n  row.setAttribute('data-imp', imp);")
rep("<span class=\"pill hb-pill is-'+imp+'\">'+habitImpLabel(imp)+'</span>';", "<span class=\"pill hb-pill is-'+imp+'\">'+(ICONS[HB_IMP_ICON[imp]] || '')+habitImpLabel(imp)+'</span>';")
rep("/* ===================== ZOOM LOCK", """/* CODIS-RULES · هوية الأهمية للعادات: عادية = هادئة ومستقرة · مهمة = دافئة · حرجة = تركيز وإلحاح. التمييز بالشكل (سماكة الشريط/الإطار) والأيقونة والنص قبل اللون */
#page-habits .hb-pill .ico{ --ctx-ico-n:var(--ico-xs); margin-inline-end:4px; vertical-align:-2px; }
#page-habits .habit-card.imp-normal::before{ width:3px; }
#page-habits .habit-card.imp-normal .streak-ring .ring-fill{ stroke:var(--aqua); }
#page-habits .hb-pill.is-normal{ color:var(--text-2); }
#page-habits .habit-card.imp-important{ background:linear-gradient(135deg, rgb(var(--warning-rgb) / .07) 0%, transparent 50%), var(--disc-card); border-color:rgb(var(--warning-rgb) / .22); }
#page-habits .habit-card.imp-important::before{ width:4px; background:var(--warning); }
#page-habits .habit-card.imp-important .streak-ring .ring-fill{ stroke:var(--warning-ink); }
#page-habits .habit-card.imp-critical{ background:linear-gradient(135deg, var(--danger-a12) 0%, transparent 58%), var(--disc-card); border-color:var(--danger-a40); border-width:1.5px;
  box-shadow:inset 0 1px 0 rgb(var(--danger-rgb) / .20), 0 1px 2px rgb(var(--lo-rgb) / .28); }
#page-habits .habit-card.imp-critical::before{ width:5px; background:var(--danger); }
#page-habits .habit-card.imp-critical.is-restrain::before{ background:repeating-linear-gradient(180deg, var(--danger) 0 6px, transparent 6px 9px); }
#page-habits .habit-card.imp-critical .habit-name{ font-weight:700; }
#page-habits .habit-card.imp-critical .streak-ring .ring-fill{ stroke:var(--danger-ink); }
#page-habits .habit-card.imp-critical:not(:has(.active)):not(.is-abstain)::before{ animation:hbCritBeat 3.6s ease-in-out infinite; }   /* انتباه خفيف فقط ما دامت لم تُنجَز اليوم */
@keyframes hbCritBeat{ 0%, 100%{ opacity:1; } 50%{ opacity:.5; } }
@media (prefers-reduced-motion:reduce){ #page-habits .habit-card.imp-critical:not(:has(.active))::before{ animation:none; } }

/* ===================== ZOOM LOCK""")

open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
