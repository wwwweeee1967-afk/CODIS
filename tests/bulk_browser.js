/* CODIS-BULK-V3 — ten-box opening test (evaluate in the page, fresh guest origin). Real economy engine.
   The stage timeline is driven with CodisBulkCinema._seek (deterministic, test-only); a real-time run is also checked at the end. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  const boxes = ()=>(data.inventory.boxes || []);
  const t = CodisBoxes.tier('bx3'), N = CodisBoxes.BULK, total = t.price * N;
  data.wallet.balance = 10000; saveData();
  const bal0 = data.wallet.balance, boxes0 = boxes().length;
  await econBuyBox10('bx3'); await sleep(150);
  const s = econBulkState, res = s && s.res;
  T('purchase succeeded and the stage is running', !!s && s.phase === 'opening' && CodisBulkCinema.active() && !!document.querySelector('.bkc-stage'));
  T('exactly price x10 deducted, once', data.wallet.balance === bal0 - total, bal0 - data.wallet.balance + ' vs ' + total);
  const nb = boxes().slice(boxes0);
  T('10 boxes recorded and opened before the animation (animation grants nothing)', nb.length === N && nb.every(b=>b.status === 'opened'));
  T('10 results = 10 recorded boxes (same uids)', res.items.length === N && res.items.every(r=>nb.some(b=>b.uid === r.box.uid)));
  T('no results grid while opening (one box at a time, not all cards at once)', !document.querySelector('#econ-bulk-modal .bk-grid') && document.querySelectorAll('.bkc-slot').length === N);
  T('tray starts with no revealed cards', document.querySelectorAll('.bkc-slot.is-filled').length === 0);

  /* schedule: ascending value order, own moment per box, duration grows with group */
  const sch = econBulkSch, ord = econBulkOrder(res), lv = ord.map(o=>o.lv);
  T('reveal order ascending by reward value level (strongest last)', lv.every((v, i)=>i === 0 || v >= lv[i - 1]), lv.join(','));
  const st = sch.items.map(p=>p.start); T('each box starts strictly after the previous one', st.every((v, i)=>i === 0 || v > st[i - 1]));
  const pool = CodisBoxes.classes(0).reduce((a, c)=>a.concat(c.items), []).sort((a, b)=>CodisBoxes.valueOf(a) - CodisBoxes.valueOf(b));
  const mixed = { items:[0, 3, 8, 15, 22, 28, 31, 33, 34, 35].filter(k=>k < pool.length).map(k=>({ item:pool[k] })) }, ms = econBulkSchedule(mixed);
  const byG = {}; ms.items.forEach(p=>{ (byG[p.g] = byG[p.g] || []).push(p.end - p.start); });
  const gs = Object.keys(byG).map(Number).sort((a, b)=>a - b), mx = gs.map(g=>Math.max.apply(null, byG[g])), mn = gs.map(g=>Math.min.apply(null, byG[g]));
  T('mixed pool spans several power groups', gs.length >= 3, gs.join(','));
  T('stronger group = longer box (every box of a higher group lasts longer than any lower one)', gs.every((g, i)=>i === 0 || mn[i] > mx[i - 1]), gs.map((g, i)=>g + ':' + Math.round(mn[i]) + '-' + Math.round(mx[i])).join(' '));
  const ant = gs.map(g=>ms.items.find(p=>p.g === g).ant); T('suspense (charge) grows with group', ant.every((v, i)=>i === 0 || v > ant[i - 1]), ant.map(Math.round).join(','));

  /* step through the real stage deterministically */
  let okSeq = true, okName = true;
  for(const p of sch.items){
    CodisBulkCinema._seek(p.reveal + 5);
    const card = document.querySelector('.bkc-layer .bkc-card'), name = econBulkInfo(res.items[p.i]).name, ban = document.querySelector('.bkc-banner b');
    if(!card) okSeq = false;
    if(!ban || ban.textContent !== name) okName = false;
    if(document.querySelector('.bkc-count b').textContent !== String(p.k + 1)) okSeq = false;
    if(document.querySelectorAll('.bkc-slot.is-filled').length !== p.k) okSeq = false;   /* earlier ones only */
    CodisBulkCinema._seek(p.end + 5);
    if(document.querySelectorAll('.bkc-slot.is-filled').length !== p.k + 1) okSeq = false;
  }
  T('cards are revealed one by one; tray fills exactly one slot per box', okSeq);
  T('banner shows the right reward name for each box', okName);
  const slot0 = document.querySelector('.bkc-slot[data-k="0"]');
  T('slot keeps the source box number', slot0 && slot0.querySelector('.bkc-no').textContent === String(sch.items[0].i + 1));
  T('no stage card left floating after its box', !document.querySelector('.bkc-layer .bkc-card'));
  CodisBulkCinema._seek(sch.total + 10); await sleep(80);
  T('end of the timeline shows the results (phase done, grid of 10)', econBulkState.phase === 'done' && document.querySelectorAll('#econ-bulk-modal .bk-cell').length === N && !CodisBulkCinema.active());
  T('animation changed nothing in data', data.wallet.balance === bal0 - total && boxes().length === boxes0 + N);
  const inv = JSON.stringify(data.inventory), bal1 = data.wallet.balance;

  /* tap = fast-forward current box only */
  econBulkShow(res); await sleep(60);
  const p0 = econBulkSch.items[0]; CodisBulkCinema._seek(p0.start + p0.enter + 10);
  document.querySelector('.bkc-stage').click(); CodisBulkCinema._seek(econBulkSch.items[1].start + 5);
  T('tap completes the current box and moves to the next', document.querySelectorAll('.bkc-slot.is-filled').length === 1 && document.querySelector('.bkc-count b').textContent === '2');
  /* skip */
  econBulkSkip(); econBulkSkip(); await sleep(80);
  T('skip goes straight to results; repeated skip harmless; stage stopped', econBulkState.phase === 'done' && !CodisBulkCinema.active() && !document.querySelector('.bkc'));
  T('skip changed no balance or inventory', data.wallet.balance === bal1 && JSON.stringify(data.inventory) === inv);
  /* close mid-run + restart safety */
  econBulkShow(res); await sleep(40); const tok1 = econBulkState.token; econBulkShow(res); const tok2 = econBulkState.token;
  T('restart invalidates the old session (new token, one stage only)', tok2 > tok1 && document.querySelectorAll('.bkc').length === 1);
  econBulkClose(true); await sleep(60);
  T('close mid-run stops everything, no data change', !CodisBulkCinema.active() && !econBulkState && data.wallet.balance === bal1 && JSON.stringify(data.inventory) === inv);
  /* reduced motion */
  const calm0 = econCalm; econCalm = ()=>true; econBulkShow(res); await sleep(80);
  T('reduced motion: results immediately, no stage', econBulkState.phase === 'done' && !document.querySelector('.bkc') && !CodisBulkCinema.active());
  econCalm = calm0; econBulkClose(true);
  /* zoom still works on results */
  econBulkShow(res); econBulkSkip(); await sleep(80);
  document.querySelectorAll('#econ-bulk-modal .bk-cell')[0].click(); await sleep(300);
  T('results: tap a card opens the enlarged flippable card', !!document.querySelector('.bk-zoom .cflip .cbk'));
  econBulkZoomClose(); econBulkClose(true);
  /* real-time run (no seek): the stage advances on its own */
  econBulkShow(res); await sleep(2600);
  const filled = document.querySelectorAll('.bkc-slot.is-filled').length;
  T('real-time: boxes open by themselves one after another', filled >= 1 && filled < N, filled + ' filled after 2.6 s');
  econBulkClose(true);
  const saved = JSON.parse(localStorage.getItem(STORE_KEY));
  T('persisted once: balance and ten opened boxes in storage', saved.wallet.balance === data.wallet.balance && saved.inventory.boxes.filter(b=>b.status === 'opened').length >= N);
  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
