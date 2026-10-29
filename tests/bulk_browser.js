/* CODIS-BULK-V2 — ten-box opening test (evaluate in the page, fresh guest origin). Real economy engine; animation timing is real (~6-9 s per run). */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  const t = CodisBoxes.tier('bx3'), N = CodisBoxes.BULK, total = t.price * N;
  data.wallet.balance = 10000; saveData();
  const bal0 = data.wallet.balance, boxes0 = (data.inventory.boxes || []).length, tx0 = data.wallet.transactions.length;
  await econBuyBox10('bx3'); await sleep(200);
  const s = econBulkState;
  T('purchase succeeded and the results modal is open (opening phase)', !!s && s.phase === 'opening');
  T('exactly price x10 deducted, once', data.wallet.balance === bal0 - total, bal0 - data.wallet.balance + ' vs ' + total);
  const newBoxes = (data.inventory.boxes || []).slice(boxes0);
  T('10 boxes recorded and all opened (granted before the animation)', newBoxes.length === N && newBoxes.every(b=>b.status === 'opened'));
  T('10 results shown = 10 recorded boxes (same uids)', s.res.items.length === N && s.res.items.every(r=>newBoxes.some(b=>b.uid === r.box.uid)));
  /* schedule: ascending level order, strictly increasing times, holds grow with level */
  const sch = econBulkSchedule(s.res), ord = econBulkOrder(s.res), lvs = ord.map(o=>o.lv);
  T('reveal order is ascending by reward level (best last)', lvs.every((v, i)=>i === 0 || v >= lvs[i - 1]), lvs.join(','));
  const ats = ord.map(o=>sch.at[o.i]); T('each box opens at its own strictly later moment', ats.every((v, i)=>i === 0 || v > ats[i - 1]), ats.join(','));
  T('total duration = schedule total', econBulkTotalMs(s.res) === sch.total);
  const hi = ord.filter(o=>o.lv >= 6).map(o=>sch.dur[o.i]), lo = ord.filter(o=>o.lv <= 2).map(o=>sch.dur[o.i]);
  T('higher levels get longer holds than ordinary ones', !hi.length || !lo.length || Math.min.apply(null, hi) > Math.max.apply(null, lo), hi.join(',') + ' vs ' + lo.join(','));
  const cells = [...document.querySelectorAll('#econ-bulk-modal .bk-cell')];
  T('ten cells rendered, each with its own --d and level, data-box uid kept', cells.length === N && cells.every(c=>c.style.getPropertyValue('--d') && c.dataset.lv && c.dataset.box));
  T('delays differ between cells (not a fixed step)', new Set(cells.map(c=>c.style.getPropertyValue('--d'))).size === N);
  /* synthetic mixed-value results: the schedule must stretch with value (pure function of the real levels) */
  const pool = CodisBoxes.classes(0).reduce((a, c)=>a.concat(c.items), []).sort((a, b)=>CodisBoxes.valueOf(a) - CodisBoxes.valueOf(b));
  const pickIdx = [0, 3, 8, 15, 22, 28, 31, 33, 34, 35].filter(k=>k < pool.length), mixed = { items:pickIdx.map(k=>({ item:pool[k] })) };
  const ms = econBulkSchedule(mixed), mo = econBulkOrder(mixed), mlv = mo.map(o=>o.lv), mat = mo.map(o=>ms.at[o.i]), msteps = mat.map((v, i)=>i ? v - mat[i - 1] : 0).slice(1);
  T('mixed levels span several tiers', new Set(mlv).size >= 4, mlv.join(','));
  T('mixed: gaps between boxes grow with level (not a fixed step)', new Set(msteps).size >= 3 && msteps[msteps.length - 1] > msteps[0], msteps.join(','));
  T('mixed: strictly increasing opening times, total > last opening', mat.every((v, i)=>i === 0 || v > mat[i - 1]) && ms.total > mat[mat.length - 1]);
  const intensities = cells.map(c=>getComputedStyle(c).getPropertyValue('--sh').trim()); T('shake intensity set per level', intensities.every(Boolean), intensities.join(','));
  /* clicking a cell while opening neither flips nor zooms */
  cells[0].querySelector('.cflip') && cells[0].click(); await sleep(100);
  T('no zoom/flip while opening', !document.querySelector('.bk-zoom') && !document.querySelector('#econ-bulk-modal .cflip.is-flipped'));
  /* skip: once, clean */
  const bal1 = data.wallet.balance, tx1 = data.wallet.transactions.length, inv1 = JSON.stringify(data.inventory);
  econBulkSkip(); econBulkSkip(); econBulkSkip(); await sleep(150);
  T('skip goes to the final state immediately (phase done), repeated skip harmless', econBulkState.phase === 'done' && !document.querySelector('#econ-bulk-modal .bk-chest'));
  T('skip changes no balance, transactions or inventory', data.wallet.balance === bal1 && data.wallet.transactions.length === tx1 && JSON.stringify(data.inventory) === inv1);
  T('no pending timers after skip', econBulkState.timer === 0 && econBulkState.cues.length === 0);
  /* zoom + back layer */
  document.querySelectorAll('#econ-bulk-modal .bk-cell')[0].click(); await sleep(400);
  const z = document.querySelector('.bk-zoom');
  T('after finishing, tapping a card opens an enlarged card', !!z && !!z.querySelector('.cflip') && !!z.querySelector('.cbk'));
  const zb = z.querySelector('.cbk'); T('enlarged back shows the right card: title = result name', zb.querySelector('.cbk-t').textContent === econBulkInfo(econBulkState.res.items[0]).name);
  const wz = z.querySelector('.cflip').getBoundingClientRect().width; T('enlarged card is wide enough to read (>=250px)', wz >= 250 || innerWidth < 330, Math.round(wz));
  T('back target while zoomed = the zoom (one layer)', codisBackLayer().act === econBulkZoomClose);
  CodisNav.back(); await sleep(350);
  T('back closes only the zoom, results stay open', !document.querySelector('.bk-zoom') && !!econBulkState && econBulkState.phase === 'done');
  document.querySelectorAll('#econ-bulk-modal .bk-cell')[1].click(); await sleep(300);
  document.dispatchEvent(new KeyboardEvent('keydown', { key:'Escape', bubbles:true })); await sleep(350);
  T('Esc closes only the zoom', !document.querySelector('.bk-zoom') && !!econBulkState);
  /* close: no data change; re-show uses fresh token; stale timers cannot touch the new session */
  econBulkClose(true); await sleep(100);
  T('closing keeps everything granted exactly once', data.wallet.balance === bal1 && (data.inventory.boxes || []).length === boxes0 + N && JSON.stringify(data.inventory) === inv1);
  const res = s.res; econBulkShow(res); const tok1 = econBulkState.token; econBulkShow(res); const tok2 = econBulkState.token;
  T('restart bumps the token (stale session invalidated)', tok2 > tok1);
  await sleep(sch.total + 600);
  T('only the newest session finishes; no duplicate finish', econBulkState && econBulkState.token === tok2 && econBulkState.phase === 'done' && document.querySelectorAll('#econ-bulk-modal .bk-cell').length === N);
  T('re-showing the animation never changes balance/inventory', data.wallet.balance === bal1 && JSON.stringify(data.inventory) === inv1);
  econBulkClose(true);
  /* reduced motion: straight to results, no chest layer */
  const calm0 = econCalm; econCalm = ()=>true; econBulkShow(res); await sleep(200);
  T('reduced motion: results immediately, no chests, no skip button', econBulkState.phase === 'done' && !document.querySelector('#econ-bulk-modal .bk-chest') && !document.querySelector('.bk-skip'));
  econCalm = calm0; econBulkClose(true);
  /* persistence */
  const saved = JSON.parse(localStorage.getItem(STORE_KEY));
  T('persisted: ten opened boxes + balance in storage', saved.wallet.balance === data.wallet.balance && saved.inventory.boxes.filter(b=>b.status === 'opened').length >= N);
  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:"EXCEPTION", info:String(e && e.stack || e) }] }; } })();
