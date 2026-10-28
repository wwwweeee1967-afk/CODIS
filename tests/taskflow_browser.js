/* CODIS-V4 task flow — in-browser regression test (patch_v4.py).
   Run: serve app/ over http, open CODIS_FINAL.html on a FRESH origin, continue as guest, then evaluate this file in the page (it mutates local test data only).
   Returns {passed, failed, results[]}. Animation timing is real (≈2.6 s per answered task). */
(async function(){
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : info });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  const wk = currentWeekId(), di = new Date().getDay(), tid = i=>'tf' + i;
  const seed = (n, keepOpen)=>{
    const days = {}; for(let i = 0; i < 7; i++) days[i] = [];
    days[di] = Array.from({ length:n }, (_, i)=>({ id:tid(i), text:'مهمة ' + i, status:null, itemId:null, qty:1, unit:null, priority:'low' }));
    if(keepOpen) days[(di + 1) % 7] = [{ id:'tfx', text:'غداً', status:null, itemId:null, qty:1, unit:null, priority:'low' }];   /* خطة غير مكتملة: لا أرشفة تلقائية */
    data.weeks[wk] = { days:days, startedAt:todayKey(), items:[], holidayDay:null, planStartDay:di, planName:'x' }; delete data.learnWeeks[wk];
    data.outcomeLedger = {}; data.archive = []; saveData(); renderTasksPage();
  };
  const T0 = i=>currentWeek().days[di][i];
  const item = i=>document.querySelector('#day-task-list .task-item[data-tid="' + tid(i) + '"]');
  const balance = ()=>data.wallet.balance, txn = ()=>data.wallet.transactions.length, ledgerN = ()=>Object.keys(data.outcomeLedger).length;

  /* ---- partial: no premature value ---- */
  seed(6); let b0 = balance(), x0 = txn();
  item(0).querySelector('[data-status="half"]').click(); await sleep(150);
  let panel = item(0).querySelector('.pp-panel');
  T('partial opens a percentage panel', !!panel);
  T('partial: status NOT changed before confirming', T0(0).status === null);
  T('partial: confirm disabled until a percentage is chosen', panel.querySelector('.pp-ok').disabled === true);
  T('partial: result/preview hidden before choosing', panel.querySelector('.pp-preview').hidden === true);
  T('partial: shows "choose" not a number', /اختر/.test(panel.querySelector('.pp-val').textContent));
  panel.querySelector('.pp-ok').click(); await sleep(100);
  T('partial: clicking disabled confirm does nothing', T0(0).status === null);
  panel.querySelector('.pp-chip[data-v="50"]').click(); await sleep(50);
  T('partial: preview revealed after choosing', panel.querySelector('.pp-preview').hidden === false && /50%/.test(panel.querySelector('.pp-val').textContent));
  const p50 = panel.querySelector('.pp-preview').textContent;
  const rg = panel.querySelector('.pp-range'); rg.value = 30; rg.dispatchEvent(new Event('input', { bubbles:true }));
  T('partial: changing percentage updates value + preview (no stale)', panel.querySelector('.pp-val').textContent === '30%' && panel.querySelector('.pp-preview').textContent !== p50);
  T('partial: status still unchanged while adjusting', T0(0).status === null);
  /* rapid repeated confirm */
  let calls = 0; const origSet = setTaskStatus; setTaskStatus = function(){ calls++; return origSet.apply(this, arguments); };
  const ok = panel.querySelector('.pp-ok'); ok.click(); ok.click(); CodisTaskFlow.answer('tasks', tid(0), 'done', item(0)); CodisTaskFlow.answer('tasks', tid(0), 'half', item(0));
  await sleep(120); setTaskStatus = origSet;
  T('partial: rapid repeated confirm applies exactly once', calls === 1, 'calls=' + calls);
  T('partial: recorded status/percentage equals the selection', T0(0).status === 'half' && T0(0).progress === 30, T0(0).status + '/' + T0(0).progress);
  T('answer time recorded', typeof T0(0).answeredAt === 'string');
  T('task still visible during animation', !!item(0) && !!item(0).querySelector('.pen-ov'));
  T('exactly one overlay (no duplicate animation)', item(0).querySelectorAll('.pen-ov').length === 1);
  await sleep(2600);
  T('partial: task left the active list after animation', !item(0));
  T('no wallet change from partial answer', balance() === b0 && txn() === x0);
  T('answered task persisted after save', JSON.parse(localStorage.getItem(STORE_KEY)).weeks[wk].days[di][0].status === 'half');

  /* ---- done / none ---- */
  item(1).querySelector('[data-status="done"]').click(); item(2).querySelector('[data-status="none"]').click(); await sleep(300);
  T('done + none animate concurrently (overlay each)', !!item(1) && !!item(2) && !!item(1).querySelector('.pen-check') && !!item(2).querySelector('.pen-x'));
  T('done/none states saved immediately', T0(1).status === 'done' && T0(2).status === 'none');
  await sleep(2500);
  T('done/none removed from active list', !item(1) && !item(2));
  T('no leftover overlays/timers', document.querySelectorAll('.pen-ov').length === 0 && CodisTaskFlow._anim.size === 0 && CodisTaskFlow._busy.size === 0);
  const bar = document.querySelector('#day-task-list .cd-trigger');
  T('completed control shows count 3', !!bar && bar.querySelector('.cd-n').textContent === '3');

  /* ---- sheet + restore ---- */
  bar.click(); await sleep(400);
  const rows = [...document.querySelectorAll('.cd-row')];
  T('sheet lists the 3 answered tasks grouped', rows.length === 3 && document.querySelectorAll('.cd-group').length === 3);
  T('sheet shows percentage for partial', /30%/.test(document.querySelector('.cd-row.is-half .cd-pct').textContent));
  const b1 = balance(), x1 = txn(), l1 = ledgerN();
  const rb = document.querySelector('.cd-row.is-done .cd-restore'); rb.click(); rb.click(); await sleep(400);
  T('restore: task returns to active list exactly once', document.querySelectorAll('#day-task-list .task-item[data-tid="' + tid(1) + '"]').length === 1 && T0(1).status === null);
  T('restore: progress/doneOn/answeredAt cleared, trace kept', T0(1).progress === 0 && !T0(1).doneOn && !T0(1).answeredAt && T0(1).restores === 1);
  await CodisTaskFlow.restore('tasks', tid(1)); await CodisTaskFlow.restore('tasks', tid(1));
  T('repeated restore is a no-op', T0(1).restores === 1);
  T('restore causes no financial change', balance() === b1 && txn() === x1 && ledgerN() === l1);
  document.querySelector('.cd-close').click(); await sleep(400);
  T('sheet closes and is removed', !document.querySelector('.cd-ov'));

  /* ---- day outcome: pending void on restore, no double grant ---- */
  seed(2, true); item(0).querySelector('[data-status="none"]').click(); await sleep(150); item(1).querySelector('[data-status="none"]').click(); await sleep(2800);
  const ents = ()=>Object.keys(data.outcomeLedger).map(k=>data.outcomeLedger[k]).filter(e=>e.scope === 'daily');
  T('answering the whole day creates exactly one day outcome', ents().filter(e=>e.status !== 'void').length === 1, JSON.stringify(ents().map(e=>[e.kind, e.status])));
  const e0 = ents()[0], id0 = e0 && e0.id, item0 = e0 && e0.item, wal = balance();
  await CodisTaskFlow.restore('tasks', tid(1)); await sleep(100);
  T('restore voids a still-pending outcome', data.outcomeLedger[id0].status === 'void');
  item(1).querySelector('[data-status="none"]').click(); await sleep(2800);
  const again = ents().filter(e=>e.id === id0);
  T('re-answering reuses the same entry (no new roll, no duplicate)', again.length === 1 && again[0].status === 'pending' && again[0].item === item0 && ents().length === 1);
  T('wallet untouched by the whole cycle', balance() === wal);
  /* resolved outcome stays */
  data.outcomeLedger[id0].status = 'resolved'; data.outcomeLedger[id0].decision = 'accept'; saveData();
  await CodisTaskFlow.restore('tasks', tid(0)); await sleep(100);
  T('restore never touches a resolved outcome', data.outcomeLedger[id0].status === 'resolved' && balance() === wal);

  /* ---- fail-safe: animation rendering fails ---- */
  seed(3); const realMount = CodisPen.mount; CodisPen.mount = function(){ throw new Error('boom'); };
  item(0).querySelector('[data-status="done"]').click(); await sleep(400);
  CodisPen.mount = realMount;
  T('animation failure: state saved + task leaves the list anyway', T0(0).status === 'done' && !item(0) && CodisTaskFlow._anim.size === 0);

  /* ---- interrupted by refresh: state is already saved before the animation ---- */
  seed(3); item(1).querySelector('[data-status="none"]').click(); await sleep(200);
  const mid = JSON.parse(localStorage.getItem(STORE_KEY)).weeks[wk].days[di][1];
  T('refresh mid-animation: saved state already final', mid.status === 'none');
  await sleep(2600);

  /* ---- learn room parity ---- */
  const lw = { days:{}, startedAt:todayKey(), items:[], holidayDay:null, planStartDay:di, planName:'l' }; for(let i = 0; i < 7; i++) lw.days[i] = [];
  lw.days[di] = [0, 1].map(i=>({ id:'lf' + i, text:'درس ' + i, status:null, itemId:null, qty:1, unit:null, priority:'low' })); data.learnWeeks[wk] = lw; saveData(); renderLearnPage();
  const li = i=>document.querySelector('#learn-day-task-list .task-item[data-tid="lf' + i + '"]');
  li(0).querySelector('[data-status="half"]').click(); await sleep(150);
  T('learn: partial panel gated too', !!li(0).querySelector('.pp-panel') && data.learnWeeks[wk].days[di][0].status === null);
  li(0).querySelector('.pp-chip[data-v="75"]').click(); li(0).querySelector('.pp-ok').click(); await sleep(2800);
  T('learn: answered task leaves list, recorded 75', !li(0) && data.learnWeeks[wk].days[di][0].progress === 75);
  await CodisTaskFlow.restore('learn', 'lf0'); await sleep(100);
  T('learn: restore works', !!li(0) && data.learnWeeks[wk].days[di][0].status === null);

  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, results:out, failures:failed };
})();
