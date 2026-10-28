/* CODIS economy/habit rules — in-browser regression test (patch_rules.py).
   Run: serve app/ over http (e.g. python -m http.server 8091), open CODIS_FINAL.html on a FRESH origin/profile, continue as guest,
   then paste this file into the DevTools console (or fetch+eval it). It mutates the local test data only. Returns {passed, failed, results[]}.
   Verified-developer cases are simulated by temporarily replacing CodisAccount.isAdmin (the real flag needs a Google sign-in + server RLS). */
(async function(){
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : info });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  const realIs = CodisAccount.isAdmin, asAdmin = fn=>{ CodisAccount.isAdmin = ()=>true; try{ return fn(); } finally { CodisAccount.isAdmin = realIs; } };
  const today = todayKey(), wk = currentWeekId(), todayIdx = new Date().getDay();
  const ledger = f=>Object.keys(data.outcomeLedger).map(k=>data.outcomeLedger[k]).filter(f);

  /* ---- PHASE 2: boxes ---- */
  const REF = 827; let capped = [];
  CodisBoxes.tiers().forEach(t=>{
    const rows = CodisBoxes.effective(t), pm = rows.map(r=>r.pm);
    T('box ' + t.id + ' available', rows.length > 0);
    T('box ' + t.id + ' sums to 1000‰', pm.reduce((a,b)=>a + b, 0) === 1000, pm.join(','));
    T('box ' + t.id + ' no invalid probability', pm.every(x=>Number.isInteger(x) && x >= 1));
    if(pm[0] === REF) T('box ' + t.id + ' lowest class = 82.7%', true); else { capped.push(t.id + ':' + pm[0]); T('box ' + t.id + ' lowest class >= 82.7% (economy cap)', pm[0] > REF, pm[0]); }
    const st = CodisBoxes.stats(t); T('box ' + t.id + ' RTP within cap (<=0.95)', st.rtp <= 0.95 + 1e-9, st.rtp.toFixed(3));
    const n = 12000, cnt = rows.map(()=>0); for(let i = 0; i < n; i++) cnt[rows.indexOf(CodisRewardEngine.pick(rows, x=>x.pm))]++;
    T('box ' + t.id + ' sampled top-class frequency matches displayed', Math.abs(cnt[0] / n * 1000 - pm[0]) < 25, (cnt[0] / n * 1000).toFixed(0) + ' vs ' + pm[0]);
  });
  T('box 1 is the reference (exactly 82.7%)', CodisBoxes.effective(CodisBoxes.tier('bx1'))[0].pm === REF);
  T('opening a box still works', !!CodisBoxes.roll(CodisBoxes.tier('bx3')));

  /* ---- PHASE 3: reward-card manipulation ---- */
  const origItems = JSON.stringify(data.settings.rewardItems), rar = econCfg().rarities.map(r=>r.id);
  const mk = (rarity, i)=>({ id:'t_' + rarity + i, name:'بطاقة ' + rarity + i, room:'tasks', rarity:rarity, weight:1, enabled:true });
  const ev = (n)=>{ let s = 0; for(let i = 0; i < n; i++) s += CodisRewardEngine.roll('tasks', 'daily').coinValue; return s / n; };
  const setItems = list=>{ data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.room !== 'tasks').concat(list); };
  setItems(rar.map(mk)); const evBase = ev(40000);
  setItems([mk('SS', 0)]); const evDel = ev(40000);
  setItems(rar.map(mk)); econCfg().rarities.forEach(r=>{ r.enabled = r.id === 'SS'; }); const evDis = ev(40000); econCfg().rarities.forEach(r=>{ r.enabled = true; });
  T('deleting every card but the legendary does not raise expected reward', Math.abs(evDel - evBase) / evBase < 0.12, evBase.toFixed(1) + ' → ' + evDel.toFixed(1));
  T('disabling every rarity but the legendary does not raise expected reward', Math.abs(evDis - evBase) / evBase < 0.12, evDis.toFixed(1));
  setItems([]); T('empty pool keeps the old lowest-rarity fallback', ev(2000) === 25);
  setItems([mk('SS', 0)]); const evAdmin = asAdmin(()=>ev(1500)); T('developer is exempt (legacy odds stay available)', evAdmin === econCoinFor('SS', 'daily'), evAdmin);
  data.settings.rewardItems = JSON.parse(origItems);

  /* ---- PHASE 4: tasks ---- */
  codisSfx = codisSfx; const mkPlan = tag=>{ const days = {}; for(let i = 0; i < 7; i++) days[i] = [{ id:tag + '_t' + i, text:'مهمة ' + i, status:null, progress:0, priority:'low' }]; return { days, startedAt:new Date().toISOString() + tag, items:{}, holidayDay:-1, planStartDay:todayIdx, planName:'خطة ' + tag }; };
  const daily = ()=>ledger(e=>e.scope === 'daily' && e.room === 'tasks');
  const pa = mkPlan('A'); data.weeks[wk] = pa; for(let i = 0; i < 7; i++) setTaskStatus('A_t' + i, 'done');
  const futureIdx = [...Array(7).keys()].filter(i=>i > todayIdx);
  T('future days cannot be completed', futureIdx.every(i=>pa.days[i][0].status === null), futureIdx.join(','));
  T('whole week in one day pays at most own-day + one catch-up reward', daily().length <= 2, daily().length);
  const n0 = daily().length; const pb = mkPlan('B'); data.weeks[wk] = pb; for(let i = 0; i <= todayIdx; i++) setTaskStatus('B_t' + i, 'done');
  T('restarting a plan in the same week mints no new daily rewards', daily().length === n0);
  const mkArch = (sid, wid, dates)=>({ weekId:wid, startedAt:sid, status:'completed', cause:'completed', name:'x', pct:100, planPct:100, tasksWeek:{ holidayDay:-1, days:Object.fromEntries([...Array(7).keys()].map(i=>[i, [{ id:'z' + sid + i, text:'t', status:'done', progress:100, doneOn:dates ? dates(i) : undefined }]])) }, learnWeek:null });
  const kind = a=>{ const r = CodisEconomy.weeklyFromArchive(a); return r ? r.entry.kind : null; };
  T('weekly reward refused when the whole week was done on one day', kind(mkArch('X1', wk, ()=>today)) === 'neutral');
  T('weekly reward granted when activity spans several days', kind(mkArch('X2', addDaysKey(wk, -14), i=>addDaysKey(today, -(i % 4)))) === 'reward');
  T('a second plan in an already-paid week pays nothing', kind(mkArch('X3', addDaysKey(wk, -14), i=>addDaysKey(today, -(i % 4)))) === 'neutral');
  T('legacy archives without done-dates are not penalised', kind(mkArch('X4', addDaysKey(wk, -21), null)) === 'reward');
  data.economyState.nextMonth = econThisMonthKey(); CodisEconomy.processMonths(); T('monthly early-settle needs distinct weeks (not plan entries)', !data.outcomeLedger['monthly|' + wk.slice(0, 7)]);
  const pc = mkPlan('C'); data.weeks[wk] = pc; asAdmin(()=>{ for(let i = 0; i < 7; i++) setTaskStatus('C_t' + i, 'done'); });
  T('developer can complete any day', [...Array(7).keys()].every(i=>pc.days[i][0].status === 'done'));
  if(todayIdx < 6){ const pd = mkPlan('D'); data.weeks[wk] = pd; pd.days[6][0].status = 'done'; setTaskStatus('D_t6', 'done'); T('clearing a mistaken future mark is allowed', pd.days[6][0].status === null); }

  /* ---- PHASE 5: weekly habit frequency ---- */
  const mkH = (k, o)=>{ const h = Object.assign({ id:'h' + Math.random().toString(36).slice(2, 8), text:'عادة', createdAt:addDaysKey(today, -10), log:{}, importance:'normal' }, o); normalizeHabit(h, k); (k === 'quit' ? data.habits.quit : data.habits.build).push(h); return h; };
  const w = mkH('build', { type:'W', requiredPerWeek:3, text:'رياضة' });
  logWeeklyHabit(w.id, 1); logWeeklyHabit(w.id, 1); logWeeklyHabit(w.id, 1);
  T('3 clicks on the same day count once', weekCount(w, wk) === 1 && w.weeklyLogs[wk].length === 1);
  w.weeklyLogs[wk] = [today, today, today]; T('legacy same-day duplicates count as one day', weekCount(w, wk) === 1);
  w.weeklyLogs[wk] = [addDaysKey(today, -2), addDaysKey(today, -1)]; logWeeklyHabit(w.id, 1); T('three distinct days count as three', weekCount(w, wk) === 3);
  logWeeklyHabit(w.id, -1); T('undo removes the last log', weekCount(w, wk) === 2);
  w.weeklyLogs[wk] = [today]; asAdmin(()=>logWeeklyHabit(w.id, 1)); T('developer can log twice in a day', w.weeklyLogs[wk].length === 2);

  /* ---- PHASE 7: event habits ---- */
  const hc = econCfg().contexts.habits; T('resist reward enabled by default', hc.resistReward === true); T('lapse penalty configured', hc.lapseCoins === 10, hc.lapseCoins);
  const resists = ()=>ledger(e=>e.periodic === 'resist');
  const e1 = mkH('quit', { type:'H', text:'تدخين' }); resistEventHabit(e1.id);
  T('resist grants one small reward', resists().length === 1 && resists()[0].rarity === econCfg().rarities[0].id, resists()[0] && resists()[0].coinValue);
  resistEventHabit(e1.id); T('duplicate resist click grants nothing', resists().length === 1);
  [1, 2, 3, 4, 5].forEach(i=>resistEventHabit(mkH('quit', { type:'H', text:'ع' + i }).id)); T('daily resist-reward cap holds across many habits', resists().length === hc.resistDailyCap, resists().length);
  data.habits.quit = data.habits.quit.filter(h=>h.id !== e1.id); resistEventHabit(mkH('quit', { type:'H', text:'تدخين' }).id); T('delete + recreate does not farm more', resists().length === hc.resistDailyCap);
  T('every resist reward is the smallest rarity', resists().every(x=>x.rarity === econCfg().rarities[0].id));
  const first = resists()[0], bal0 = CodisWallet.balance(), d1 = CodisEconomy.decideReward(first.id, 'coins'); T('reward converts to coins in the wallet', d1.ok && CodisWallet.balance() - bal0 === first.coinValue);
  T('same reward cannot be claimed twice', CodisEconomy.decideReward(first.id, 'coins').reason === 'already');
  CodisWallet.transact([], ()=>{ data.wallet.balance = 100; return { ok:true }; }); const e2 = mkH('quit', { type:'H', text:'سكر' }), b0 = CodisWallet.balance();
  await recordEventHabit(e2.id); T('lapse deducts exactly the configured amount', CodisWallet.balance() - b0 === -hc.lapseCoins, CodisWallet.balance() - b0);
  T('lapse is written to history and ledger once', e2.occurrences.length === 1 && e2.occurrences[0].coins === hc.lapseCoins && data.wallet.transactions.filter(t=>t.type === 'HABIT_LAPSE' && t.referenceId === 'lapse|' + e2.id + '|' + today).length === 1);
  await recordEventHabit(e2.id); T('second lapse the same day does nothing', CodisWallet.balance() - b0 === -hc.lapseCoins && e2.occurrences.length === 1);
  CodisWallet.transact([], ()=>{ data.wallet.balance = 4; return { ok:true }; }); const e3 = mkH('quit', { type:'H', text:'جوال' }); await recordEventHabit(e3.id); T('penalty never takes the balance below zero', CodisWallet.balance() === 0 && e3.occurrences[0].coins === 4);
  const e5 = mkH('quit', { type:'H', text:'x' }); await recordEventHabit(e5.id); const before = resists().length; resistEventHabit(e5.id); T('no resist reward after a lapse the same day', resists().length === before);
  saveData(); T('lapse transactions are persisted', JSON.parse(localStorage.getItem(STORE_KEY)).wallet.transactions.some(t=>t.type === 'HABIT_LAPSE'));

  /* ---- exemption guard ---- */
  T('a normal user has no developer powers', CodisLimits.on() === false && CodisAccount.isAdmin() === false);
  const passed = out.filter(x=>x.ok).length;
  return { passed, failed:out.length - passed, boxCappedTiers:capped, results:out };
})();
