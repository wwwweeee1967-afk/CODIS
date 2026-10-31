/* CODIS-CYCLE test — evaluate in the page (fresh guest origin). Reproduces the reported bug relative to TODAY:
   a plan distributed 2 days ago must live its own 7-day cycle (wrap days = real future dates), never be archived/punished at the calendar-week rollover. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  const L = ()=>data.outcomeLedger, today = todayKey(), weeklyIds = ()=>Object.keys(L()).filter(k=>k.indexOf('weekly|') === 0 && !/reopened/.test(k));
  const mk = (S, tag)=>{ const sd = parseKey(S).getDay(), key = getWeekId(parseKey(S)), days = {};
    for(let i = 0; i < 7; i++){ const off = (i - sd + 7) % 7, date = addDaysKey(S, off);
      days[i] = [{ id:tag + i, text:'مهمة ' + i, status:date <= today ? 'done' : null, progress:date <= today ? 100 : 0, qty:1, priority:'low' }]; }
    return { key:key, sd:sd, w:{ days:days, startedAt:S + 'T09:00:00.000Z', items:{}, holidayDay:-1, planStartDay:sd, planName:'خطتي', cyc:2 } }; };

  /* ---- 1) the reported situation: distributed 2 days ago ---- */
  const S = addDaysKey(today, -2), a = mk(S, 'a');
  a.w.days[(a.sd + 5) % 7][0].status = null; a.w.days[(a.sd + 5) % 7][0].progress = 0;   /* a future day stays open */
  data.weeks[a.key] = a.w; saveData();
  T('plan key follows the plan cycle', currentPlanKey() === a.key, currentPlanKey() + ' vs ' + a.key);
  T('plan is active', currentPlanActive());
  T('cycle end = start + 6', planEndKey(a.key, a.w) === addDaysKey(S, 6));
  const n = archiveStaleWeeksIfAny();
  T('NOT archived while its cycle is running', n === 0 && !!data.weeks[a.key] && !(data.archive || []).some(x=>x.weekId === a.key));
  T('no weekly punishment/outcome', weeklyIds().length === 0);
  CodisEconomy.processMonths();
  T('no monthly outcome created', !Object.keys(L()).some(k=>k.indexOf('monthly|') === 0 && L()[k].status !== 'void'));
  T('plan day dates are consecutive from the start date', [0, 1, 2, 3, 4, 5, 6].every(i=>dateForWeekDay(a.key, i) === addDaysKey(S, (i - a.sd + 7) % 7)));
  T('every date inside the cycle', [0, 1, 2, 3, 4, 5, 6].every(i=>{ const d = dateForWeekDay(a.key, i); return d >= S && d <= addDaysKey(S, 6); }));
  const futIdx = (a.sd + 3) % 7, pastIdx = a.sd, todayIdx = new Date().getDay();
  T('a future wrap/cycle day is locked', codisTaskDayLocked(a.key, futIdx, a.w.days[futIdx][0], 'done') === true);
  T('start day is not locked', codisTaskDayLocked(a.key, pastIdx, a.w.days[pastIdx][0], 'done') !== true);
  T('today is not locked', codisTaskDayLocked(a.key, todayIdx, a.w.days[todayIdx][0], 'done') !== true);
  document.querySelector('.navbtn[data-page="tasks"]').click(); await sleep(500);
  T('operations room shows today tasks, no grace banner', !document.querySelector('#page-tasks .grace-banner'));
  T('no grace week listed', graceWeeks().length === 0);

  /* ---- 2) after the cycle ends: grace first, then automatic archive ---- */
  delete data.weeks[a.key];
  const b = mk(addDaysKey(today, -8), 'b'); b.w.days[b.sd][0].status = null; b.w.days[b.sd][0].progress = 0;   /* ended 2 days ago with one open task */
  data.weeks[b.key] = b.w; saveData();
  T('ended plan with open tasks is held for grace', archiveStaleWeeksIfAny() === 0 && graceWeeks().length === 1 && graceWeeks()[0].id === b.key);
  T('grace end is cycle end + 4', graceWeeks()[0].until === addDaysKey(planEndKey(b.key, b.w), 4));
  T('the end month of the plan is held', codisGraceMonthKeys().has(planEndKey(b.key, b.w).slice(0, 7)));
  delete data.weeks[b.key];
  const c = mk(addDaysKey(today, -12), 'c'); c.w.days[c.sd][0].status = null; c.w.days[c.sd][0].progress = 0;
  data.weeks[c.key] = c.w; saveData();
  const n2 = archiveStaleWeeksIfAny();
  T('plan past its grace window is archived automatically', n2 >= 1 && !data.weeks[c.key] && (data.archive || []).some(x=>x.weekId === c.key && x.cause === 'stale'));

  /* ---- 3) month attribution = month of the cycle END ---- */
  const A = { weekId:'2026-10-25', tasksWeek:{ cyc:2, planStartDay:5 } }, B = { weekId:'2026-10-25', tasksWeek:{ planStartDay:5 } };
  T('plan started Fri 30 Oct is a NOVEMBER plan', codisPlanMonth(A) === '2026-11', codisPlanMonth(A));
  T('legacy archive keeps its old month', codisPlanMonth(B) === '2026-10', codisPlanMonth(B));
  T('start Sunday: cycle inside the same calendar week', planEndKey('2026-10-25', { cyc:2, planStartDay:0 }) === '2026-10-31');
  T('start Saturday: ends next Friday', planEndKey('2026-10-25', { cyc:2, planStartDay:6 }) === '2026-11-06');
  T('daily entry month follows planEnd', CodisEconomy && (function(){ const e = { scope:'daily', weekId:'2026-10-25', day:5, planEnd:'2026-11-05', at:'2026-10-30T10:00:00Z' }; return codisEntryPlanMonth(e) === '2026-11'; })());

  /* ---- 4) rescue: an auto-archived legacy plan reopens with the new model ---- */
  Object.keys(L()).forEach(k=>delete L()[k]); data.archive = [];
  const S4 = addDaysKey(today, -2), d4 = mk(S4, 'r'), legacy = JSON.parse(JSON.stringify(d4.w)); delete legacy.cyc;
  const arc = { id:'arcRescue', name:'خطتي', weekId:d4.key, status:'stopped', cause:'stale', startedAt:legacy.startedAt, pct:57, planPct:57, taskCount:7, learnCount:0, tasksWeek:legacy, learnWeek:null, archivedAt:new Date().toISOString(), stoppedAt:new Date().toISOString() };
  data.archive.unshift(arc);
  const wId = ['weekly', d4.key, legacy.startedAt].join('|'), mId = 'monthly|' + d4.key.slice(0, 7);
  L()[wId] = { id:wId, scope:'weekly', kind:'punish', status:'pending', weekId:d4.key, at:new Date().toISOString() };
  L()[mId] = { id:mId, scope:'monthly', kind:'punish', status:'pending', at:new Date().toISOString() };
  T('the reported punishments are rescue-able', reopenArchiveReason(arc) === '', reopenArchiveReason(arc));
  const ok = reopenArchivedPlan('arcRescue'); await sleep(500);
  T('reopen restores the plan with the cycle model', ok && !!data.weeks[d4.key] && data.weeks[d4.key].cyc === 2);
  T('pending weekly + monthly punishments voided', !L()[wId] && !L()[mId] && Object.keys(L()).some(k=>k.indexOf(wId + '|reopened') === 0) && Object.keys(L()).some(k=>k.indexOf(mId + '|reopened') === 0));
  closeGraceSheet && closeGraceSheet(); await sleep(200);
  T('restored plan survives the boot archive step', archiveStaleWeeksIfAny() === 0 && !!data.weeks[d4.key]);
  T('restored plan is the current plan', currentPlanKey() === d4.key && currentPlanActive());

  /* ---- 5) new plan distributed today uses the cycle model ---- */
  delete data.weeks[d4.key]; saveData();
  saveDraftFromInputs = ()=>{}; data.planningDraft = { tasksRaw:'مهمة أ\nمهمة ب\nمهمة ج\nمهمة د\nمهمة هـ\nمهمة و\nمهمة ز\nمهمة ح', learnRaw:'' };
  const hasFn = typeof distributePlan === 'function' ? 'distributePlan' : null;
  T('distribute function exists', !!hasFn);
  if(hasFn){ try{ await window[hasFn](); }catch(e){ T('distribute ran', false, String(e)); }
    const w = data.weeks[currentWeekId()];
    T('new plan is stamped cyc:2 with today as the start day', !!w && w.cyc === 2 && w.planStartDay === new Date().getDay());
    T('new plan: all 7 days fall inside today..today+6', !!w && [0, 1, 2, 3, 4, 5, 6].every(i=>{ const d = dateForWeekDay(currentWeekId(), i); return d >= today && d <= addDaysKey(today, 6); })); }
  T('persisted', !!JSON.parse(localStorage.getItem(STORE_KEY)));
  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
