#!/usr/bin/env python3
"""CODIS-CYCLE (بعد patch_v15.py): الخطة تعيش دورتها الكاملة (7 أيام من يوم توزيعها) لا الأسبوع التقويمي.
 قبل: خطة وُزّعت الجمعة 30/10 كانت تُقصّ عند السبت 31/10 (أيام الالتفاف = تواريخ ماضية)، وتُؤرشف أول الأحد، وتعطي عقوبة أسبوعية وشهرية فوراً.
 بعد: · أيام الالتفاف تقع على تواريخها الحقيقية القادمة (الأحد→الخميس التالي) وتُقفل حتى يأتي يومها
      · الأرشفة التلقائية ومهلة التسجيل تُحسب من نهاية دورة الخطة (آخر يومها السابع)
      · الخطة والنتائج الأسبوعية واليومية تُنسب لشهر نهاية الدورة، والشهر الذي فيه خطة شغّالة لا يُحسم
      · نافذة العادات تتبع أيام الخطة الفعلية
      · الخطط الجارية القديمة تُرحَّل تلقائياً (cyc:2) وإعادة فتح أرشيف الخطة تُرجعها بالنموذج الجديد"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-CYCLE' in s: sys.exit('already patched (CODIS-CYCLE)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# ---------- 1) المساعدات الأساسية ----------
rep("""function currentWeekId(){ return getWeekId(new Date()); }
function currentWeek(){ return data.weeks[currentWeekId()]; }
""", """function currentWeekId(){ return getWeekId(new Date()); }
/* ===== CODIS-CYCLE =====
   مفتاح الخطة = الأحد التقويمي ليوم توزيعها (للتوافق). دورتها = 7 أيام تبدأ من يوم التوزيع (مفتاح + planStartDay) وتنتهي بعد 6 أيام.
   الخطط الموسومة cyc:2 تستعمل هذا النموذج؛ أرشيف قديم بلا العلامة يبقى بتواريخه القديمة (أسبوع تقويمي). */
function planHostFor(id){
  const h = (data.weeks && data.weeks[id]) || (data.learnWeeks && data.learnWeeks[id]); if(h) return h;
  const a = (data.archive || []).find(x=>x && x.weekId === id && x.kind !== 'habit' && (x.tasksWeek || x.learnWeek));
  return a ? (a.tasksWeek || a.learnWeek) : null;
}
function planStartIdx(host){
  if(!host) return 0;
  if(Number.isInteger(host.planStartDay) && host.planStartDay >= 0 && host.planStartDay <= 6) return host.planStartDay;
  return inferPlanStartDay(host);
}
function planStartKey(id, host){ host = host || planHostFor(id); return addDaysKey(id, host && host.cyc === 2 ? planStartIdx(host) : 0); }
function planEndKey(id, host){ return addDaysKey(planStartKey(id, host), 6); }
function codisPlanMonth(a){ return planEndKey(a.weekId, a.tasksWeek || a.learnWeek).slice(0, 7); }
/* مفتاح الخطة الجارية: الخطة التي تقع دورتها على اليوم (الأحدث أولاً)، وإلا أسبوع اليوم التقويمي (للتوزيع الجديد) */
function currentPlanKey(){
  const t = todayKey(); let best = null;
  new Set([].concat(Object.keys(data.weeks || {}), Object.keys(data.learnWeeks || {}))).forEach(id=>{
    const h = (data.weeks && data.weeks[id]) || (data.learnWeeks && data.learnWeeks[id]); if(!h) return;
    if(planStartKey(id, h) <= t && t <= planEndKey(id, h) && (best === null || id > best)) best = id;
  });
  return best === null ? currentWeekId() : best;
}
function currentWeek(){ return data.weeks[currentPlanKey()]; }
/* ترحيل الخطط الجارية القديمة إلى نموذج الدورة (مرة واحدة لكل خطة) وإعادة حساب تواريخ عاداتها */
function codisMigrateCycle(){
  [data.weeks, data.learnWeeks].forEach(st=>Object.keys(st || {}).forEach(id=>{
    const w = st[id]; if(!w || typeof w !== 'object' || w.cyc === 2) return;
    if(!Number.isInteger(w.planStartDay) || w.planStartDay < 0 || w.planStartDay > 6) w.planStartDay = inferPlanStartDay(w);
    w.cyc = 2;
    if(w.habitPlan && Array.isArray(w.habitPlan.days)){
      const days = []; for(let n = 0; n < 7; n++){ const i = (w.planStartDay + n) % 7; if(isHolidayIdx(w, i)) continue; const k = dateForWeekDay(id, i, w); if(k) days.push(k); }
      w.habitPlan.days = days;
    }
  }));
}
""", 'helpers')

# تاريخ اليوم: أيام الالتفاف (قبل يوم البدء) = الأسبوع التالي
rep("""function dateForWeekDay(weekId, dayIdx){
  if(!weekId) return null;
  const parts = weekId.split('-').map(Number);
  if(parts.length!==3 || parts.some(isNaN)) return null;
  const d = new Date(parts[0], parts[1]-1, parts[2] + dayIdx);""", """function dateForWeekDay(weekId, dayIdx, host){
  if(!weekId) return null;
  const parts = weekId.split('-').map(Number);
  if(parts.length!==3 || parts.some(isNaN)) return null;
  let off = dayIdx;
  if(Number.isInteger(dayIdx) && dayIdx >= 0 && dayIdx < 7){ const h = host || planHostFor(weekId); if(h && h.cyc === 2 && dayIdx < planStartIdx(h)) off = dayIdx + 7; }
  const d = new Date(parts[0], parts[1]-1, parts[2] + off);""", 'dateForWeekDay')
rep("const dayDate = dateForWeekDay(weekId, i);", "const dayDate = dateForWeekDay(weekId, i, week);", 'archive day date')

# ---------- 2) الوسم عند التوزيع والتوسيع ----------
rep("planStartDay: todayIdx, planName: planNameAtDistribution, sourceRaw: draft.tasksRaw || '' };", "planStartDay: todayIdx, cyc: 2, planName: planNameAtDistribution, sourceRaw: draft.tasksRaw || '' };", 'create tasks')
rep("planStartDay: todayIdx, planName: planNameAtDistribution, sourceRaw: draft.learnRaw || '' };", "planStartDay: todayIdx, cyc: 2, planName: planNameAtDistribution, sourceRaw: draft.learnRaw || '' };", 'create learn')
rep("planStartDay:getPlanStartDay(host), planName:host.planName || currentPlanName() }", "planStartDay:getPlanStartDay(host), cyc:2, planName:host.planName || currentPlanName() }", 'extend learn week')

# ---------- 3) أيام العادات = أيام الدورة السبعة ----------
rep("const days = []; for(let i=startIdx; i<7; i++){ if(i === holidayDay) continue; const k = dateForWeekDay(wk, i); if(k) days.push(k); }",
    "const days = [], ph = { cyc:2, planStartDay:startIdx }; for(let n=0; n<7; n++){ const i = (startIdx + n) % 7; if(i === holidayDay) continue; const k = dateForWeekDay(wk, i, ph); if(k) days.push(k); }", 'habit snapshot')
rep("const days = []; for(let i = getPlanStartDay(w); i < 7; i++){ if(isHolidayIdx(w, i)) continue; const k = dateForWeekDay(ctx.wk, i); if(k) days.push(k); }",
    "const days = [], ph = { cyc:2, planStartDay:getPlanStartDay(w) }; for(let n = 0; n < 7; n++){ const i = (ph.planStartDay + n) % 7; if(isHolidayIdx(w, i)) continue; const k = dateForWeekDay(ctx.wk, i, ph); if(k) days.push(k); }", 'sync habit days')

# ---------- 4) سياق الخطة = مفتاح الخطة الجارية ----------
rep("const weekId = currentWeekId(), week = room === 'learn'", "const weekId = currentPlanKey(), week = room === 'learn'", 'econ daily')
rep("const wk = currentWeekId(), weeks = [];", "const wk = currentPlanKey(), weeks = [];", 'planContext')
rep("weekId:currentWeekId(), total:list.length", "weekId:currentPlanKey(), total:list.length", 'day ctx')
rep("function currentPlanActive(){\n  const wk = currentWeekId();", "function currentPlanActive(){\n  const wk = currentPlanKey();", 'planActive')
rep("function currentPlanName(){\n  const wk = currentWeekId();", "function currentPlanName(){\n  const wk = currentPlanKey();", 'planName')
rep("function computePlanProgress(){ return computePlanProgressForWeek(currentWeekId()); }", "function computePlanProgress(){ return computePlanProgressForWeek(currentPlanKey()); }", 'progress')
rep("const _name = currentPlanName(), _wk = currentWeekId();", "const _name = currentPlanName(), _wk = currentPlanKey();", 'stop/complete', 2)
rep("function isPlanFullyComplete(){\n  const wk = currentWeekId();", "function isPlanFullyComplete(){\n  const wk = currentPlanKey();", 'fullyComplete')
rep("if(wk === currentWeekId()) data.loadedPlanId = null;", "if(wk === currentPlanKey()) data.loadedPlanId = null;", 'loadedPlanId')
rep("function archiveCurrentPlan(reason){ return archivePlanForWeek(currentWeekId(), reason); }", "function archiveCurrentPlan(reason){ return archivePlanForWeek(currentPlanKey(), reason); }", 'archiveCurrent')
rep("today = new Date().getDay(), wk = currentWeekId();", "today = new Date().getDay(), wk = currentPlanKey();", 'remaining days')
rep("const wk = currentWeekId(), host = data.weeks[wk] || data.learnWeeks[wk];", "const wk = currentPlanKey(), host = data.weeks[wk] || data.learnWeeks[wk];", 'extend submit')
rep("const wk = currentWeekId(), tw = data.weeks[wk], lw = data.learnWeeks[wk];\n  const tasksRaw", "const wk = currentPlanKey(), tw = data.weeks[wk], lw = data.learnWeeks[wk];\n  const tasksRaw", 'save active')
rep("codisTaskDayLocked(currentWeekId(), f.day, f.t, 'half')", "codisTaskDayLocked(currentPlanKey(), f.day, f.t, 'half')", 'half lock')
rep("const w = weekOf(k), weekId = currentWeekId(), list = answered(k, day);", "const w = weekOf(k), weekId = currentPlanKey(), list = answered(k, day);", 'weekOf')
rep("const weekId = currentWeekId(), ents = dayEntries(k, weekId, f.day)", "const weekId = currentPlanKey(), ents = dayEntries(k, weekId, f.day)", 'dayEntries')
rep("codisTaskDayLocked(currentWeekId(), changedDay, t, status)", "codisTaskDayLocked(currentPlanKey(), changedDay, t, status)", 'lock ops')
rep("function learnCurrentWeek(){ return data.learnWeeks[currentWeekId()]; }", "function learnCurrentWeek(){ return data.learnWeeks[currentPlanKey()]; }", 'learnCurrent')
rep("codisTaskDayLocked(currentWeekId(), Number(dIdx), t, status)", "codisTaskDayLocked(currentPlanKey(), Number(dIdx), t, status)", 'lock learn')

# ---------- 5) أرشفة تلقائية ومهلة من نهاية الدورة ----------
rep("const base = dateForWeekDay(id, 7 + GRACE_DAYS), ex =", "const base = addDaysKey(planEndKey(id, tw || lw), 1 + GRACE_DAYS), ex =", 'graceEnd')
rep("const cur = currentWeekId(), ids = new Set([].concat(Object.keys(data.weeks || {}), Object.keys(data.learnWeeks || {}))), out = [];",
    "const cur = todayKey(), ids = new Set([].concat(Object.keys(data.weeks || {}), Object.keys(data.learnWeeks || {}))), out = [];", 'graceWeeks cur')
rep("""    if(!(id < cur)) return;
    const tw = data.weeks[id], lw = data.learnWeeks[id], open = graceOpenTasks(tw).length + graceOpenTasks(lw).length, until = graceEndKey(id, tw, lw);""",
"""    const tw = data.weeks[id], lw = data.learnWeeks[id];
    if(!(planEndKey(id, tw || lw) < cur)) return;   /* ما زالت دورتها جارية: ليست بانتظار التسوية */
    const open = graceOpenTasks(tw).length + graceOpenTasks(lw).length, until = graceEndKey(id, tw, lw);""", 'graceWeeks body')
rep("function codisGraceMonthKeys(){ return new Set(graceWeeks().map(g=>g.id.slice(0, 7))); }",
    """function codisGraceMonthKeys(){   /* شهر نهاية أي خطة شغّالة أو بانتظار التسوية لا يُحسم */
  const set = new Set(graceWeeks().map(g=>codisPlanMonth({ weekId:g.id, tasksWeek:g.tw, learnWeek:g.lw })));
  [data.weeks, data.learnWeeks].forEach(st=>Object.keys(st || {}).forEach(id=>{ if(st[id]) set.add(planEndKey(id, st[id]).slice(0, 7)); }));
  return set;
}""", 'graceMonthKeys')
rep("function archiveStaleWeeksIfAny(){\n  const wk = currentWeekId();", "function archiveStaleWeeksIfAny(){\n  codisMigrateCycle();", 'stale head')
rep("].filter(id=>id!==wk));", "].filter(id=>planEndKey(id, data.weeks[id] || data.learnWeeks[id]) < todayKey()));   /* بعد نهاية دورتها فقط */", 'stale filter')

# ---------- 6) نسب الشهر = شهر نهاية الدورة ----------
old_em = """  function entryMonth(e){
    try{ if(e.scope === 'daily' && e.weekId && Number.isInteger(e.day)){ const ds = dateForWeekDay(e.weekId, e.day); if(ds) return ds.slice(0,7); }
      if(e.scope === 'weekly' && typeof e.weekId === 'string' && /^\\d{4}-\\d{2}-\\d{2}$/.test(e.weekId)) return e.weekId.slice(0,7);"""
new_em = """  function entryMonth(e){
    try{ const pm = codisEntryPlanMonth(e); if(pm) return pm;
      if(e.scope === 'daily' && e.weekId && Number.isInteger(e.day)){ const ds = dateForWeekDay(e.weekId, e.day); if(ds) return ds.slice(0,7); }
      if(e.scope === 'weekly' && typeof e.weekId === 'string' && /^\\d{4}-\\d{2}-\\d{2}$/.test(e.weekId)) return e.weekId.slice(0,7);"""
rep(old_em, new_em, 'entryMonth', 2)
rep("""function currentPlanKey(){""", """/* شهر إدخال سجل اليومي/الأسبوعي = شهر نهاية دورة خطته (المحفوظ planEnd، أو من الخطة الجارية/المؤرشفة الموسومة) */
function codisEntryPlanMonth(e){
  if(!e) return '';
  if(typeof e.planEnd === 'string' && /^\\d{4}-\\d{2}-\\d{2}$/.test(e.planEnd)) return e.planEnd.slice(0, 7);
  if((e.scope === 'daily' || e.scope === 'weekly') && typeof e.weekId === 'string'){ const h = planHostFor(e.weekId); if(h && h.cyc === 2) return planEndKey(e.weekId, h).slice(0, 7); }
  return '';
}
function currentPlanKey(){""", 'entryPlanMonth')
rep("a.weekId.slice(0,7) === m && a.cause !== 'manual'", "codisPlanMonth(a) === m && a.cause !== 'manual'", 'plans month', 2)
rep("{ late:late, weekId:weekId, planId:planId || null,", "{ late:late, weekId:weekId, planEnd:planEndKey(weekId, week), planId:planId || null,", 'daily planEnd')
rep("{ weekId:arch.weekId, planId:arch.startedAt || null,", "{ weekId:arch.weekId, planEnd:planEndKey(arch.weekId, arch.tasksWeek || arch.learnWeek), planId:arch.startedAt || null,", 'weekly planEnd')

# ---------- 7) نافذة العادات تتبع أيام الخطة ----------
rep("  const wEnd = wk=>addDaysKey(wk, 6);\n", "  const wFrom = wk=>planStartKey(wk);   /* CODIS-CYCLE: بداية نافذة الخطة */\n  const wEnd = wk=>addDaysKey(wFrom(wk), 6);\n", 'wEnd')
rep("const k = addDaysKey(wk, i); if(k < h.createdAt", "const k = addDaysKey(wFrom(wk), i); if(k < h.createdAt", 'days()')
rep("(h.occurrences || []).filter(x=>x.date >= wk && x.date <= wEnd(wk))", "(h.occurrences || []).filter(x=>x.date >= wFrom(wk) && x.date <= wEnd(wk))", 'occ')
rep("Object.keys(h.resists || {}).filter(k=>k >= wk && k <= wEnd(wk))", "Object.keys(h.resists || {}).filter(k=>k >= wFrom(wk) && k <= wEnd(wk))", 'resists')
rep("return { weekId:wk, from:wk, to:wEnd(wk),", "return { weekId:wk, from:wFrom(wk), to:wEnd(wk),", 'weekStats from')

# ---------- 8) إعادة الفتح بالنموذج الجديد ----------
rep("  if(!(p.weekId < currentWeekId())) return 'خطة الأسبوع الحالي';\n", "", 'reason current week')
rep("mid = 'monthly|' + p.weekId.slice(0, 7);\n  if(L[wid] && L[wid].status === 'resolved')", "mid = 'monthly|' + p.weekId.slice(0, 7), mid2 = 'monthly|' + codisPlanMonth(p);\n  if(L[wid] && L[wid].status === 'resolved')", 'reason mids')
rep("  if(L[mid] && L[mid].status === 'resolved') return 'نتيجة الشهر انحسمت بقرارك';", "  if((L[mid] && L[mid].status === 'resolved') || (L[mid2] && L[mid2].status === 'resolved')) return 'نتيجة الشهر انحسمت بقرارك';", 'reason month')
rep("mid = 'monthly|' + p.weekId.slice(0, 7), stamp = Date.now();", "mid = 'monthly|' + p.weekId.slice(0, 7), mid2 = 'monthly|' + codisPlanMonth(p), stamp = Date.now();", 'reopen mids')
rep("[wid, mid].forEach(k=>{ const e = L[k];", "[wid, mid, mid2].filter((k, i, a)=>a.indexOf(k) === i).forEach(k=>{ const e = L[k];", 'reopen void')
rep("  data.archive = data.archive.filter(x=>x.id !== id);\n  /* الشهر الذي ينتظر", "  data.archive = data.archive.filter(x=>x.id !== id);\n  codisMigrateCycle();   /* تعود بنموذج الدورة: أيام الالتفاف قادمة لا ماضية */\n  /* الشهر الذي ينتظر", 'reopen migrate')
rep("const m = p.weekId.slice(0, 7); if(data.economyState && data.economyState.nextMonth > m)", "const m = [p.weekId.slice(0, 7), codisPlanMonth(p)].sort()[0]; if(data.economyState && data.economyState.nextMonth > m)", 'reopen nextMonth')
rep("p.cause === 'stale' && p.weekId < currentWeekId()) ?", "p.cause === 'stale') ?", 'reopen button')

# ---------- 9) علامة ----------
rep("<!-- CODIS-GRACE -->", "<!-- CODIS-GRACE -->\n<!-- CODIS-CYCLE -->", 'marker')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v16 OK')
