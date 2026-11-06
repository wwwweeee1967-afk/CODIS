/* ===== CODIS-V34 · نظام التأديب المستقل: عملات كسرية + بطاقات ثابتة + محطات + عقوبات + تذكيرات =====
   كل الدوال هنا تُعرَّف بـ function (hoisted) ولا تقرأ const/let معرَّفاً بعدها وقت التحميل (قاعدة 3.17.2). */

/* ---------- 1) العملات: منزلتان عشريتان. كل عملية تُقرَّب لأقرب 0.01 بعد كل خطوة (لا تراكم أخطاء عائمة) ---------- */
function econC(v){ const n = Number(v); return isFinite(n) ? Math.round(n * 100) / 100 : 0; }
function econCN(v, def, min, max){ let n = (v === null || v === '' || typeof v === 'boolean' || v === undefined) ? NaN : Number(v); if(!isFinite(n)) n = def; return econC(Math.max(min, Math.min(max, n))); }
function econAddC(a, b){ return (Math.round(Number(a) * 100) + Math.round(Number(b) * 100)) / 100; }

/* ---------- 2) البطاقات الثابتة (لا احتمالات ولا ندرات عشوائية) ---------- */
function codisFixedDefs(){
  if(codisFixedDefs.c) return codisFixedDefs.c;
  const R = (id, name, coin, o)=>Object.assign({ id:id, name:name, coin:coin }, o || {});
  const P = (id, name, cost, sev, o)=>Object.assign({ id:id, name:name, cost:cost, sev:sev }, o || {});
  return (codisFixedDefs.c = {
    rewards:[
      R('fx_station7', 'محطة السبعة أيام', 12.5, { art:'milestone', store:12.5, tag:'station7' }),
      R('fx_rs_normal', 'مكافأة حدثية عادية', 18.75, { art:'resistance', tag:'resist', imp:'normal' }),
      R('fx_rs_important', 'مكافأة حدثية مهمة', 37.5, { art:null, tag:'resist', imp:'important' }),
      R('fx_rs_critical', 'مكافأة حدثية حرجة', 125, { art:null, tag:'resist', imp:'critical' }),
      R('fx_ms_normal', 'مكافأة حدثية عادية محسّنة', 75, { art:'milestone', tag:'monthlyEvent', imp:'normal' }),
      R('fx_ms_important', 'مكافأة حدثية مهمة محسّنة', 100, { art:null, tag:'monthlyEvent', imp:'important' }),
      R('fx_ms_critical', 'مكافأة حدثية حرجة محسّنة', 200, { art:null, tag:'monthlyEvent', imp:'critical' })
    ],
    punish:[
      P('fxp_st7_low', 'عقوبة محطة العادات — خفيفة', 31.25, 'LOW', { tag:'st7' }),
      P('fxp_st7_med', 'عقوبة محطة العادات — متوسطة', 62.5, 'MEDIUM', { tag:'st7' }),
      P('fxp_st7_high', 'عقوبة محطة العادات — قوية', 125, 'HIGH', { tag:'st7' }),
      P('fxp_ev_normal', 'عقوبة حدثية عادية', 112.5, 'LOW', { tag:'event', imp:'normal' }),
      P('fxp_ev_important', 'عقوبة حدثية مهمة', 225, 'MEDIUM', { tag:'event', imp:'important' }),
      P('fxp_ev_critical', 'عقوبة حدثية حرجة', 750, 'HIGH', { tag:'event', imp:'critical' })
    ]
  });
}
function codisFixedById(id){ const d = codisFixedDefs(); return d.rewards.find(x=>x.id === id) || d.punish.find(x=>x.id === id) || null; }
function codisFixedFor(list, tag, imp){ return codisFixedDefs()[list].find(x=>x.tag === tag && (!imp || x.imp === imp)) || null; }
/* يُستدعى من econNormalizeItems (وقت التحميل): يضمن وجود البطاقات الثابتة كعناصر حقيقية بالكتالوج (متجر/مخزون/إعدادات) بمعرّفات ثابتة. لا يرمي أبداً */
function codisV34Seed(s){
  try{
    if(!s || !Array.isArray(s.rewardItems) || !Array.isArray(s.punishItems) || !s.economy || !Array.isArray(s.economy.rarities) || !s.economy.rarities.length) return;
    const rid = s.economy.rarities[0].id, now = econNowIso(), D = codisFixedDefs();
    D.rewards.forEach(d=>{
      let it = s.rewardItems.find(x=>x && x.id === d.id);
      if(!it){ it = { id:d.id, name:d.name, rarity:rid, weight:0, coinValue:null, storePrice:null, stickerId:null, enabled:true, room:'habits', createdAt:now, updatedAt:now }; s.rewardItems.push(it); }
      it.name = d.name; it.room = 'habits'; it.rarity = rid; it.weight = 0; it.fixed = true; it.fixedCoin = d.coin; it.fixedStore = (d.store === undefined ? null : d.store);
    });
    D.punish.forEach(d=>{
      let it = s.punishItems.find(x=>x && x.id === d.id);
      if(!it){ it = { id:d.id, name:d.name, severity:d.sev, coinBypassCost:null, enabled:true, room:'habits', createdAt:now, updatedAt:now }; s.punishItems.push(it); }
      it.name = d.name; it.room = 'habits'; it.severity = d.sev; it.fixed = true; it.fixedCost = d.cost; it.fixedGroup = d.tag;
    });
  }catch(e){}
}
/* نتيجة بقيمة ثابتة عبر نفس سجل النتائج (المعرّف فريد ⇒ لا تكرار). مكافأة: أخذ/استبدال بالكوين. عقوبة: تنفيذ أو دفع. لا خصم قبل قرار المستخدم */
function codisFixedOutcome(id, kind, def, extra){
  const L = data.outcomeLedger, ex = L[id];
  if(ex){ if(ex.status === 'void'){ ex.status = 'pending'; ex.decision = null; saveData(); return { entry:ex, isNew:true }; } return { entry:ex, isNew:false }; }
  const items = kind === 'reward' ? data.settings.rewardItems : data.settings.punishItems, it = items.find(x=>x.id === def.id);
  if(it && it.enabled === false) return { entry:null, isNew:false, disabled:true };
  const rar = econCfg().rarities[0];
  const e = Object.assign({ id:id, room:'habits', kind:kind, scope:'habit', type:'habit_' + (kind === 'reward' ? 'reward' : 'punishment'), at:econNowIso(), status:'pending', decision:null, applied:true, celebrated:false, fixedId:def.id, periodic:def.tag }, extra || {});
  if(kind === 'reward') Object.assign(e, { item:def.name, rewardId:def.id, stickerId:null, rarity:rar.id, rarityName:rar.name, rarityTone:rar.tone, rarityOrder:rar.order, odds:null, coinValue:def.coin, storePrice:(def.store !== undefined && def.store !== null) ? def.store : econAutoStore(def.coin), coinsAwarded:0 });
  else Object.assign(e, { item:def.name, punishId:def.id, severity:def.sev, bypassCost:def.cost, coinsSpent:0, noPass:def.tag === 'event' });
  L[id] = e; saveData();
  return { entry:e, isNew:true };
}
function codisHabitFixedCtx(h, label){ return { habitId:h.id, habitText:h.text || '', label:label || '' }; }

/* ---------- 3) محطة السبعة أيام (مكافأة حقيقية) ---------- */
function codisStationId(h, mk){ return ['habit', h.id, 'st7:' + mk, 'reward'].join('|'); }
function codisV34StationReward(h, mk){
  const r = codisFixedOutcome(codisStationId(h, mk), 'reward', codisFixedFor('rewards', 'station7'), codisHabitFixedCtx(h, 'محطة السبعة أيام — «' + h.text + '»'));
  if(r && r.entry && r.isNew){ try{ CodisOutcomeUI.enqueue(r.entry.id, 700); }catch(e){} }
  return r && r.entry ? r : null;
}

/* ---------- 4) تعويض المحطات القديمة (مرة واحدة لكل حساب؛ معاملة حتمية المعرّف فلا تتكرر عبر الأجهزة) ---------- */
function codisV34CompEligible(){
  const out = [];
  const scan = h=>{ if(!h || h.type !== 'E' || !h.milestones || typeof h.milestones !== 'object') return; Object.keys(h.milestones).forEach(k=>{ const m = h.milestones[k]; if(m && typeof m === 'object' && !m.v34 && !m.comp && /^\d{4}-\d{2}-\d{2}:\d+$/.test(k) && Number(k.split(':')[1]) % 7 === 0) out.push(m); }); };
  ((data.habits && data.habits.build) || []).forEach(scan); ((data.habits && data.habits.quit) || []).forEach(h=>{ if(isAbstainDaily(h)) scan(h); });
  (data.archive || []).forEach(a=>{ try{ if(a && a.habit && a.habitType === 'E') scan(a.habit); }catch(e){} });
  return out;
}
function codisV34Compensate(){
  try{
    const st = data.economyState; if(!st || typeof st !== 'object') return false;
    if(st.comp7 && st.comp7.done) return false;
    const list = codisV34CompEligible();
    if(!list.length){ st.comp7 = { done:true, count:0, amount:0, at:econNowIso(), shown:true }; saveData(); return false; }
    const amount = econC(list.length * 12.5);
    const r = CodisWallet.transact([], ()=>{
      const tx = CodisWallet.apply('HABIT_COMPENSATION', amount, 'تعويض محطات السبعة أيام السابقة (' + list.length + ')', 'habit', 'comp7|v34', { count:list.length, txId:'tx_comp7_v34' });
      if(!tx) return { ok:false, reason:'tx' };
      list.forEach(m=>{ m.comp = true; });
      data.economyState.comp7 = { done:true, count:list.length, amount:amount, at:econNowIso(), shown:false };
      return { ok:true };
    });
    return !!(r && r.ok);
  }catch(e){ console.error('CODIS comp7:', e); return false; }
}
function codisV34CompNotice(){
  try{
    const c = data.economyState && data.economyState.comp7; if(!c || !c.done || c.shown || !(c.count > 0)) return;
    c.shown = true; saveData();
    const msg = 'نعتذر منك، في الإصدار السابق كانت محطة السبعة أيام تُسجَّل دون منح مكافأتها المالية بصورة صحيحة. تم تصحيح النظام وإضافة تعويض مالي بقيمة 12.5 كوين عن كل محطة مؤهلة حققتها سابقاً.\nعدد المحطات: ' + c.count + ' — إجمالي التعويض: ' + econFmt(c.amount) + ' كوين.';
    try{ codisConfirm({ title:'تعويض محطات السبعة أيام', message:msg, icon:'info', danger:false, confirmText:'تمام' }); }catch(e){ showToast('أُضيف تعويض ' + econFmt(c.amount) + ' كوين لمحطاتك السابقة', 'var(--success)', 'check'); }
    try{ CodisHabitPush.notifyNow('تعويض محطات السبعة أيام', 'أُضيف ' + econFmt(c.amount) + ' كوين تعويضاً عن ' + c.count + ' محطة سابقة.', 'hc'); }catch(e){}
  }catch(e){}
}

/* ---------- 5) عقوبات محطة السبعة أيام (دورة مستقلة لكل عادة يومية؛ لا أثر رجعي لما قبل التحديث) ---------- */
function codisV34StationPenalties(){
  const today = todayKey(), made = []; let changed = false;
  const habits = ((data.habits && data.habits.build) || []).filter(h=>h && h.type === 'E').concat(((data.habits && data.habits.quit) || []).filter(isAbstainDaily));
  habits.forEach(h=>{
    if(typeof h.c7 !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(h.c7)){ h.c7 = today; changed = true; return; }   // عادة قديمة: الدورة تبدأ اليوم ولا تُعاقَب بأثر رجعي
    let guard = 0;
    while(addDaysKey(h.c7, 6) < today && guard++ < 8){
      const s = h.c7; let ok = 0;
      for(let i = 0; i < 7; i++){ const k = addDaysKey(s, i); if(h.log && h.log[k]) ok++; }
      const fail = 7 - ok, tier = ok === 0 ? 'high' : fail >= 4 ? 'med' : fail >= 2 ? 'low' : '';
      h.c7 = addDaysKey(s, 7); changed = true;
      if(!tier) continue;
      const def = codisFixedDefs().punish.find(x=>x.id === 'fxp_st7_' + tier);
      const r = codisFixedOutcome(['habit', h.id, 'c7:' + s, 'punish'].join('|'), 'punish', def, Object.assign(codisHabitFixedCtx(h, 'دورة ' + s + ' — «' + h.text + '»'), { cycleFrom:s, cycleTo:addDaysKey(s, 6), stats:{ success:ok, fail:fail } }));
      if(r && r.entry && r.isNew) made.push(r.entry.id);
    }
  });
  if(changed) saveData();
  made.forEach((id, i)=>{ try{ CodisOutcomeUI.enqueue(id, 900 + i * 400); }catch(e){} });
  return made;
}

/* ---------- 6) العادة الأسبوعية: أيام فعلية ---------- */
const CODIS_WDAYS = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
function codisTodayIdx(){ return parseKey(todayKey()).getDay(); }
function codisWDaysOk(a){ return Array.isArray(a) ? a.filter((x, i, arr)=>Number.isInteger(x) && x >= 0 && x <= 6 && arr.indexOf(x) === i).sort((p, q)=>p - q) : []; }
function codisWDaysLabel(a){ a = codisWDaysOk(a); return a.length ? a.map(i=>CODIS_WDAYS[i]).join(' · ') : ''; }
let newHabitDays = [];
function toggleNewHabitDay(i){
  i = Number(i); if(!(i >= 0 && i <= 6)) return;
  const at = newHabitDays.indexOf(i); if(at === -1) newHabitDays.push(i); else newHabitDays.splice(at, 1);
  newHabitDays.sort((a, b)=>a - b); renderNewHabitDays(); codisSfx('press', { ctx:'tab' });
}
function renderNewHabitDays(){
  const box = document.getElementById('new-habit-days'); if(!box) return;
  box.innerHTML = CODIS_WDAYS.map((n, i)=>{ const on = newHabitDays.indexOf(i) !== -1; return '<button type="button" class="hb-chip hb-day' + (on ? ' is-on' : '') + '" aria-pressed="' + on + '" onclick="toggleNewHabitDay(' + i + ')">' + n + '</button>'; }).join('');
}
function habitDaysEditorHtml(h){
  const d = codisWDaysOk(h.days);
  return '<div class="hb-days" role="group" aria-label="أيام العادة">' + CODIS_WDAYS.map((n, i)=>{ const on = d.indexOf(i) !== -1; return '<button type="button" class="hb-chip hb-day' + (on ? ' is-on' : '') + '" data-hday="' + i + '" aria-pressed="' + on + '">' + n + '</button>'; }).join('') + '</div>';
}
function setHabitDay(id, i){
  const h = data.habits.build.find(x=>x.id === id && x.type === 'W'); if(!h) return;
  const d = codisWDaysOk(h.days), at = d.indexOf(i);
  if(at === -1) d.push(i); else { if(d.length <= 1){ codisSfx('invalid'); showToast('اترك يوماً واحداً على الأقل', 'var(--warning)'); return; } d.splice(at, 1); }
  h.days = d.sort((a, b)=>a - b);
  if(!(h.requiredPerWeek >= 1) || h.requiredPerWeek !== h.days.length) h.requiredPerWeek = h.days.length;   // السجل السابق (weeklyLogs/weekHistory) يبقى كما هو؛ الهدف الجديد من هذا الأسبوع
  saveData(); codisSfx('press', { ctx:'tab' }); renderHabitsPage();
}
function logWeeklyHabit(id, delta){   // W: «سجّل إنجاز اليوم» — مرة واحدة في يوم من أيام الجدول، ولا تراجع
  if(!(delta > 0)) return;
  const h = data.habits.build.find(x=>x.id === id); if(!h || h.type !== 'W') return;
  const days = codisWDaysOk(h.days);
  if(!days.length){ codisSfx('invalid'); showToast('حدّد أيام هذه العادة أولاً', 'var(--warning)'); return; }
  const tk = todayKey(), wk = currentWeekId(), arr = h.weeklyLogs[wk] = h.weeklyLogs[wk] || [];
  if(days.indexOf(codisTodayIdx()) === -1 && !CodisLimits.bypass('habit.schedule')){ codisSfx('invalid'); showToast('اليوم ليس من أيام هذه العادة', 'var(--warning)'); return; }
  if(arr.indexOf(tk) !== -1 && !CodisLimits.bypass('habit.sameDay')){ codisSfx('invalid'); showToast('سجّلت هذي العادة اليوم', 'var(--warning)'); return; }
  codisJustChangedId = id; codisHaptic(8);
  arr.push(tk);
  saveData(); codisSfx('task.done', { ctx:'habit' }); renderHabitsPage();
}

/* ---------- 7) العادة الحدثية: مكافأة/عقوبة ثابتة بحسب الأهمية ---------- */
function codisV34ImpKey(h){ return habitImportance(h); }
