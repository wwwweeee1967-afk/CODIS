/* CODIS-GRACE test — evaluate in the page (fresh guest origin). Reproduces the reported scenario:
   tasks done in real life but not yet recorded, a new week begins, the app is opened → must NOT archive/punish immediately. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  /* CODIS-CYCLE: the grace window now counts from the END of the plan's own 7-day cycle (not the calendar week) */
  const cur = currentWeekId(), today = todayKey(), L = ()=>data.outcomeLedger;
  const Sp = addDaysKey(today, -8), So = addDaysKey(today, -14), prev = getWeekId(parseKey(Sp)), old = getWeekId(parseKey(So));
  const openIdx = (S, k)=>(parseKey(S).getDay() + 4 + k) % 7;   /* the three open days = offsets 4..6 of the cycle */
  const mkWeek = (S, ids)=>{ const sd = parseKey(S).getDay(), days = {}; for(let i = 0; i < 7; i++) days[i] = [];
    [0, 1, 2, 3].forEach(o=>{ days[(sd + o) % 7] = [{ id:ids + 'd' + o, text:'مهمة ' + o, status:'done', progress:100, qty:1, priority:'low', doneOn:S }]; });
    [0, 1, 2].forEach(k=>{ days[openIdx(S, k)] = [{ id:ids + 'o' + k, text:'مفتوحة ' + k, status:null, progress:0, qty:1, priority:'low' }]; });
    return { days:days, startedAt:S + 'T09:00:00.000Z', items:{}, holidayDay:-1, planStartDay:sd, cyc:2, planName:'خطتي' }; };
  const weeklyIds = ()=>Object.keys(L()).filter(k=>k.indexOf('weekly|') === 0 && !/reopened/.test(k));

  /* ---- 1) the reported situation ---- */
  data.weeks[prev] = mkWeek(Sp, 'p');
  const nBefore = (data.archive || []).length, archived = archiveStaleWeeksIfAny();
  T('stale week WITH unanswered tasks is NOT archived on opening', archived === 0 && !!data.weeks[prev] && (data.archive || []).length === nBefore);
  T('no weekly punishment/outcome was created', weeklyIds().length === 0, weeklyIds().join(','));
  T('week is listed for settlement with the right count', graceWeeks().length === 1 && graceWeeks()[0].open === 3);
  document.querySelector('.navbtn[data-page="tasks"]').click(); await sleep(500);
  T('banner shown in the operations room', !!document.querySelector('#page-tasks .grace-banner') && /3 مهمة/.test(document.querySelector('#page-tasks .grace-banner').innerText));
  T('the month of that week is held back', codisGraceMonthKeys().has(planEndKey(prev, data.weeks[prev]).slice(0, 7)));
  const mk = planEndKey(prev, data.weeks[prev]).slice(0, 7), keepM = data.economyState.nextMonth; data.economyState.nextMonth = mk;
  const realKeys = codisGraceMonthKeys; const monthsUnheld = (cur.slice(0, 7) > mk);
  if(monthsUnheld){ CodisEconomy.processMonths(); T('processMonths does not settle a month while its week is pending', data.economyState.nextMonth === mk && !L()['monthly|' + mk]); }
  else { /* v38: hold the month processing starts from (the previous month); before, it held mk but started one month earlier, so that earlier month settled correctly and the assertion was wrong whenever today is in mk */ data.economyState.nextMonth = addDaysKey(mk + '-01', -2).slice(0, 7); const nm = data.economyState.nextMonth; codisGraceMonthKeys = ()=>new Set([nm]); CodisEconomy.processMonths(); T('processMonths hold gate stops at a held month (simulated: same month as today)', data.economyState.nextMonth === nm && !L()['monthly|' + nm]); codisGraceMonthKeys = realKeys; }
  data.economyState.nextMonth = keepM;

  /* ---- 2) record from the settlement sheet ---- */
  openGraceSheet(); await sleep(500);
  T('settlement sheet opens with the three open tasks', !!document.querySelector('.gs-ov') && document.querySelectorAll('.gs-row').length === 3);
  const click = (sel)=>{ const b = document.querySelector(sel); if(b) b.click(); return !!b; };
  click('.gs-row[data-id="po0"] .gs-btns button[data-s="done"]'); await sleep(150);
  T('recording one task keeps the week open and updates the count', !!data.weeks[prev] && data.weeks[prev].days[openIdx(Sp, 0)][0].status === 'done' && graceWeeks()[0].open === 2);
  click('.gs-row[data-id="po1"] .gs-btns button[data-s="half"]'); await sleep(100);
  T('«نصها» asks for a percentage first (no status yet)', data.weeks[prev].days[openIdx(Sp, 1)][0].status === null && !!document.querySelector('.gs-half'));
  click('.gs-half button[data-p="50"]'); await sleep(150);
  T('half recorded with the chosen percentage', data.weeks[prev].days[openIdx(Sp, 1)][0].status === 'half' && data.weeks[prev].days[openIdx(Sp, 1)][0].progress === 50);
  const bal0 = data.wallet.balance, tx0 = data.wallet.transactions.length;
  click('.gs-row[data-id="po2"] .gs-btns button[data-s="none"]'); await sleep(500);
  const arc = (data.archive || []).find(a=>a.weekId === prev);
  T('when all are recorded the week settles as a normal completed plan', !!arc && arc.status === 'completed' && arc.cause === 'completed' && !data.weeks[prev]);
  T('final percentage uses the recorded answers (not zeros)', arc && arc.pct > 50, arc && arc.pct);
  const wid = weeklyIds()[0], we = wid && L()[wid];
  T('exactly one weekly outcome, created only now, from the real result', weeklyIds().length === 1 && we && we.stats && we.stats.open === 0, we && JSON.stringify(we.stats));
  T('no coins moved by recording', data.wallet.balance === bal0 && data.wallet.transactions.length === tx0);
  T('banner removed after settlement', !document.querySelector('.grace-banner') && !document.querySelector('.gs-ov'));

  /* ---- 3) «end the week now» ---- */
  delete L()[wid]; data.archive = data.archive.filter(a=>a.weekId !== prev);
  data.weeks[prev] = mkWeek(Sp, 'q'); saveData();
  openGraceSheet(); await sleep(400); click('#gs-end'); await sleep(500);
  const arc2 = (data.archive || []).find(a=>a.weekId === prev);
  T('«end the week now» archives with the old stale behaviour', !!arc2 && arc2.cause === 'stale' && !data.weeks[prev] && weeklyIds().length === 1);

  /* ---- 4) after the grace window the old automatic behaviour applies ---- */
  data.archive = data.archive.filter(a=>a.weekId !== prev); Object.keys(L()).filter(k=>k.indexOf('weekly|') === 0).forEach(k=>delete L()[k]);
  data.weeks[old] = mkWeek(So, 'x'); saveData();
  T('a week older than the grace window is not held', graceWeeks().every(g=>g.id !== old));
  const n2 = archiveStaleWeeksIfAny();
  T('...and is archived automatically as before', n2 >= 1 && !data.weeks[old] && (data.archive || []).some(a=>a.weekId === old && a.cause === 'stale'));

  /* ---- 5) reopen an auto-archived plan (rescue) ---- */
  const oldArc = data.archive.find(a=>a.weekId === old), oldW = ['weekly', old, oldArc.startedAt || ''].join('|');
  T('auto-archived week produced a pending weekly outcome', !!L()[oldW] && L()[oldW].status === 'pending', L()[oldW] && L()[oldW].status);
  openArchiveDetail(oldArc.id); await sleep(500);
  const rb = document.getElementById('archive-detail-reopen');
  T('archive detail shows an enabled «reopen» button', rb && rb.style.display !== 'none' && !rb.disabled, rb && rb.textContent);
  const ok = reopenArchivedPlan(oldArc.id); await sleep(500);
  T('reopen succeeds: plan back, archive entry removed', ok && !!data.weeks[old] && !data.archive.some(a=>a.id === oldArc.id));
  T('pending weekly outcome voided with a trace, no live entry', !L()[oldW] && Object.keys(L()).some(k=>k.indexOf(oldW + '|reopened') === 0 && L()[k].status === 'void'));
  T('reopened week is held for the new grace window', graceWeeks().some(g=>g.id === old));
  closeGraceSheet(); await sleep(300);
  /* reopen refuses a decided outcome */
  data.weeks[old].days[openIdx(So, 0)][0].status = 'done'; archivePlanForWeek(old, 'stopped', 'stale');
  const a3 = data.archive.find(a=>a.weekId === old), w3 = ['weekly', old, a3.startedAt || ''].join('|'); if(L()[w3]) L()[w3].status = 'resolved';
  T('reopen refuses when the weekly result was already decided', reopenArchiveReason(a3) !== '' && reopenArchivedPlan(a3.id) === false && data.archive.some(a=>a.id === a3.id));
  T('persisted', !!JSON.parse(localStorage.getItem(STORE_KEY)));
  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
