/* CODIS-V34 discipline test — evaluate in the page (guest). Mutates local test data only.
   TEST=tests/discipline_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1 */
(async function(){
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : String(i) });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const L = ()=>data.outcomeLedger, key = (...a)=>a.join('|');
  const mkE = (id, abst)=>Object.assign({ id:id, text:'عادة ' + id, type:'E', importance:'normal', createdAt:dateKeyOffset(-30), log:{}, milestones:{}, misses:[], doneEvents:{}, checkedThrough:yesterdayKey(), c7:todayKey() }, abst ? { abstain:true, failLog:{} } : {});
  const mkH = (id, imp, ago)=>({ id:id, text:'حدثية ' + id, type:'H', importance:imp, createdAt:dateKeyOffset(-ago), log:{}, occurrences:[], lastOccurrence:null, bestDays:0, monthlyMilestones:{}, resists:{} });
  const bal = ()=>CodisWallet.balance();
  codisConfirm = ()=>Promise.resolve(true);

  /* ---- catalog: fixed cards exist with exact values ---- */
  const ri = id=>data.settings.rewardItems.find(x=>x.id === id), pi = id=>data.settings.punishItems.find(x=>x.id === id);
  T('7 fixed reward cards seeded', codisFixedDefs().rewards.every(d=>ri(d.id) && ri(d.id).fixed && ri(d.id).fixedCoin === d.coin));
  T('6 fixed penalty cards seeded', codisFixedDefs().punish.every(d=>pi(d.id) && pi(d.id).fixed && pi(d.id).fixedCost === d.cost));
  T('station card: value 12.5 and store price 12.5 (no markup)', econEffCoin(ri('fx_station7')) === 12.5 && CodisEconomy.storePrice(ri('fx_station7')) === 12.5);
  T('fixed rewards never enter random draws / boxes', !CodisBoxes.pool().some(x=>x.fixed));
  T('habit pass prices 31.25 / 62.5 / 125', CodisPasses.price({ scope:'habit', severity:'LOW' }) === 31.25 && CodisPasses.price({ scope:'habit', severity:'MEDIUM' }) === 62.5 && CodisPasses.price({ scope:'habit', severity:'HIGH' }) === 125);
  T('other pass prices unchanged', CodisPasses.price({ scope:'daily', severity:'MEDIUM' }) === econBypassFor('MEDIUM', 'daily'));

  /* ---- coins: fractions through the whole cycle ---- */
  const b0 = bal();
  const vals = [12.5, 18.75, 31.25, 37.5, 62.5, 112.5]; let exp = b0;
  for(const v of vals){ const r = CodisWallet.transact([], ()=>{ const tx = CodisWallet.apply('ADMIN_ADJUSTMENT', v, 't', 'test', econUid('t')); return tx ? { ok:true } : { ok:false }; }); exp = econAddC(exp, v); T('credit ' + v, r.ok && bal() === exp, bal()); }
  T('sum exact (no float drift)', bal() === econAddC(b0, 275), bal());
  const sp = CodisWallet.transact([], ()=>{ const tx = CodisWallet.apply('ADMIN_ADJUSTMENT', -18.75, 't', 'test', econUid('t')); return tx ? { ok:true } : { ok:false }; });
  T('debit 18.75', sp.ok && bal() === econAddC(b0, 256.25), bal());
  const huge = CodisWallet.transact([], ()=>{ const tx = CodisWallet.apply('PENALTY_BYPASS', -(bal() + 0.01), 't', 'test', econUid('t')); return tx ? { ok:true } : { ok:false, reason:'tx' }; });
  T('no negative balance (non-admin)', !huge.ok && bal() === econAddC(b0, 256.25));
  { const ref = 'dup|' + Date.now(); const a = CodisWallet.transact([], ()=>({ ok:!!CodisWallet.apply('ADMIN_ADJUSTMENT', 1.25, 't', 'test', ref) })), c = CodisWallet.transact([], ()=>({ ok:!!CodisWallet.apply('ADMIN_ADJUSTMENT', 1.25, 't', 'test', ref) })); T('same reference never applies twice', a.ok && !c.ok); }
  T('econFmt keeps fractions', econFmt(12.5) === '12.5' && econFmt(18.75) === '18.75' && econFmt(31.25) === '31.25' && econFmt(112.5) === '112.5' && econFmt(1234) === '1,234');
  { const raw = JSON.parse(localStorage.getItem('life_organizer_data_v1') || '{}'); T('persisted wallet keeps fractions', raw.wallet && raw.wallet.balance === bal(), raw.wallet && raw.wallet.balance); }
  { const copy = JSON.parse(JSON.stringify(data)); copy.wallet.balance = 100; copy.wallet.transactions = []; T('legacy integer balance stays 100 (never ×100)', econCN(copy.wallet.balance, 0, 0, 1e12) === 100); }

  /* ---- 7-day station: real financial reward, no duplicates, build/quit separate ---- */
  const hb = mkE('tb1'), hq = mkE('tq1', true);
  data.habits.build.push(hb); data.habits.quit.push(hq);
  for(let i = 1; i <= 6; i++){ hb.log[dateKeyOffset(-i)] = true; hq.log[dateKeyOffset(-i)] = true; }
  toggleDailyHabit('tb1'); await sleep(50);
  const mkb = Object.keys(hb.milestones)[0], idb = codisStationId(hb, mkb);
  T('7th day creates a real reward outcome', !!L()[idb] && L()[idb].coinValue === 12.5 && L()[idb].status === 'pending' && L()[idb].fixedId === 'fx_station7', idb);
  T('6 days alone give nothing', (()=>{ const h = mkE('tb6'); data.habits.build.push(h); for(let i = 1; i <= 5; i++) h.log[dateKeyOffset(-i)] = true; toggleDailyHabit('tb6'); return !Object.keys(L()).some(k=>k.indexOf('habit|tb6|') === 0); })());
  toggleDailyHabit('tb1'); toggleDailyHabit('tb1');   // undo then redo
  T('undo before pickup voids, redo revives the same entry (no duplicate)', Object.keys(L()).filter(k=>k.indexOf('habit|tb1|st7:') === 0).length === 1 && L()[idb].status === 'pending');
  toggleDailyHabit('tq1');
  T('quit-daily is a separate habit with its own entry', Object.keys(L()).some(k=>k.indexOf('habit|tq1|st7:') === 0) && !Object.keys(L()).some(k=>k.indexOf('habit|tq1|') === 0 && k.indexOf('habit|tb1|') === 0));
  { const b1 = bal(), r = CodisEconomy.decideReward(idb, 'coins'); T('exchange pays exactly 12.5', r.ok && bal() === econAddC(b1, 12.5), bal() - b1); T('cannot take twice', !CodisEconomy.decideReward(idb, 'coins').ok); }
  { const e2 = codisFixedOutcome(key('habit', 'tq1', 'st7:x', 'reward'), 'reward', codisFixedFor('rewards', 'station7'), {}); const r = CodisEconomy.decideReward(e2.entry.id, 'item'); const it = r.ok && r.owned; T('item path grants inventory copy with fractional value', it && it.coinValue === 12.5 && it.rewardId === 'fx_station7' && CodisInventory.sellValue(it) > 0 && CodisInventory.sellValue(it) < 12.5, it && CodisInventory.sellValue(it)); }
  { const b1 = bal(), r = CodisEconomy.purchase('fx_station7'); T('store purchase of station card costs exactly 12.5', r.ok && bal() === econAddC(b1, -12.5) && r.owned.paid === 12.5); }

  /* ---- retro compensation: once, deterministic ---- */
  { const h = mkE('tc1'); h.milestones = { [dateKeyOffset(-20) + ':7']:{ date:dateKeyOffset(-20), reward:'' }, [dateKeyOffset(-13) + ':14']:{ date:dateKeyOffset(-13), reward:'' } }; data.habits.build.push(h);
    const q = mkE('tc2', true); q.milestones = { [dateKeyOffset(-9) + ':7']:{ date:dateKeyOffset(-9), reward:'' } }; data.habits.quit.push(q);
    const fresh = Object.keys(hb.milestones).length;
    delete data.economyState.comp7; const b1 = bal();
    const n = codisV34CompEligible().length; const ok = codisV34Compensate();
    T('compensation counts every legacy milestone (both rooms)', n === 3 && ok && bal() === econAddC(b1, 37.5) && data.economyState.comp7.count === 3, n + ' / ' + (bal() - b1));
    T('compensation tx has a unique reference + fixed id', data.wallet.transactions.some(t=>t.type === 'HABIT_COMPENSATION' && t.referenceId === 'comp7|v34' && t.id === 'tx_comp7_v34'));
    const b2 = bal(); codisV34Compensate(); T('second run pays nothing', bal() === b2);
    T('new v34 milestones are never compensated', Object.values(hb.milestones).every(m=>m.v34) && codisV34CompEligible().length === 0 && fresh >= 1); }

  /* ---- 7-day penalties ---- */
  const cyc = (id, okDays, abst)=>{ const h = mkE(id, abst); h.c7 = dateKeyOffset(-7); for(let i = 0; i < okDays; i++) h.log[addDaysKey(h.c7, i)] = true; (abst ? data.habits.quit : data.habits.build).push(h); return h; };
  const hz = cyc('p0', 0), h1 = cyc('p1', 1), h3 = cyc('p3', 3), h5 = cyc('p5', 5), h6 = cyc('p6', 6), h7 = cyc('p7', 7), hq0 = cyc('pq0', 0, true);
  codisV34StationPenalties();
  const pen = h=>L()[key('habit', h.id, 'c7:' + dateKeyOffset(-7), 'punish')];
  T('0 successes → strong 125', pen(hz) && pen(hz).bypassCost === 125 && pen(hz).severity === 'HIGH');
  T('1 success (6 fails) → medium 62.5', pen(h1) && pen(h1).bypassCost === 62.5 && pen(h1).severity === 'MEDIUM');
  T('3 successes (4 fails) → medium 62.5', pen(h3) && pen(h3).bypassCost === 62.5);
  T('5 successes (2 fails) → light 31.25', pen(h5) && pen(h5).bypassCost === 31.25 && pen(h5).severity === 'LOW');
  T('6 successes (1 fail) → none', !pen(h6));
  T('7 successes → none', !pen(h7));
  T('quit-daily evaluated independently', pen(hq0) && pen(hq0).bypassCost === 125);
  T('cycle advanced (no repeat)', hz.c7 === todayKey() && (()=>{ const n = Object.keys(L()).length; codisV34StationPenalties(); return Object.keys(L()).length === n; })());
  T('old habit gets no retroactive penalty', (()=>{ const h = mkE('pold'); delete h.c7; data.habits.build.push(h); codisV34StationPenalties(); return h.c7 === todayKey() && !Object.keys(L()).some(k=>k.indexOf('habit|pold|') === 0); })());
  T('penalty passes: only matching habit+severity pass fits', (()=>{ const e = pen(hz); const ok = CodisPasses.fits({ scope:'habit', severity:'HIGH' }, e), no = CodisPasses.fits({ scope:'habit', severity:'LOW' }, e), no2 = CodisPasses.fits({ scope:'daily', severity:'HIGH' }, e); return ok && !no && !no2; })());
  { const e = pen(h5), b1 = bal(), r = CodisEconomy.decidePenalty(e.id, 'bypass'); T('bypass costs exactly 31.25', r.ok && bal() === econAddC(b1, -31.25)); T('no second payment', !CodisEconomy.decidePenalty(e.id, 'bypass').ok && !CodisEconomy.decidePenalty(e.id, 'execute').ok); }
  { const e = pen(h1), b1 = bal(), r = CodisEconomy.decidePenalty(e.id, 'execute'); T('executing costs nothing', r.ok && bal() === b1); }

  /* ---- event habit: fixed rewards / penalties by importance, no auto deduction ---- */
  const imps = [['normal', 18.75, 112.5, 75], ['important', 37.5, 225, 100], ['critical', 125, 750, 200]];
  for(const [imp, rc, pc, mc] of imps){
    const h = mkH('e_' + imp, imp, 5); data.habits.quit.push(h);
    resistEventHabit(h.id); const re = L()[key('habit', h.id, 'rs:' + todayKey(), 'reward')];
    T('resist ' + imp + ' = ' + rc, re && re.coinValue === rc && re.kind === 'reward' && !re.odds && re.status === 'pending');
    resistEventHabit(h.id); T('resist twice same day creates nothing new', Object.keys(L()).filter(k=>k.indexOf('habit|' + h.id + '|rs:') === 0).length === 1);
    const b1 = bal(); h.resists = {}; delete L()[key('habit', h.id, 'rs:' + todayKey(), 'reward')];
    await recordEventHabit(h.id); const pe = L()[key('habit', h.id, 'ev:' + todayKey(), 'punish')];
    T('occurrence ' + imp + ' = penalty ' + pc + ', nothing deducted yet', pe && pe.bypassCost === pc && pe.status === 'pending' && bal() === b1 && pe.noPass === true);
    T('event penalty has no compatible pass', CodisPasses.compatible(pe).length === 0);
    T('event: days counter reset + no HABIT_LAPSE tx', h.lastOccurrence === todayKey() && !data.wallet.transactions.some(t=>t.type === 'HABIT_LAPSE' && t.referenceId.indexOf(h.id) !== -1));
    const g = mkH('m_' + imp, imp, 65); data.habits.quit.push(g); runHabitChecks();
    const ms = Object.keys(L()).filter(k=>k.indexOf('habit|' + g.id + '|hm:') === 0).map(k=>L()[k]);
    T('30-day ' + imp + ' = ' + mc + ' (two stations at 65 days → 2 entries)', ms.length >= 2 && ms.every(x=>x.coinValue === mc && !x.odds), ms.length);
    const n1 = Object.keys(L()).length; runHabitChecks(); T('30-day: no duplicate on rerun', Object.keys(L()).length === n1);
  }
  { const h = mkH('e_pay', 'critical', 3); data.habits.quit.push(h); await recordEventHabit(h.id); const e = L()[key('habit', h.id, 'ev:' + todayKey(), 'punish')]; const b1 = bal();
    const need = e.bypassCost - bal(); if(need > 0) CodisWallet.transact([], ()=>({ ok:!!CodisWallet.apply('ADMIN_ADJUSTMENT', need + 5, 't', 'test', econUid('t')) }));
    const b2 = bal(), r = CodisEconomy.decidePenalty(e.id, 'bypass'); T('event bypass pays exactly 750', r.ok && bal() === econAddC(b2, -750)); }

  /* ---- weekly habit with real days ---- */
  { const today = codisTodayIdx(), other = (today + 3) % 7;
    const h = { id:'tw1', text:'رياضة', type:'W', importance:'normal', createdAt:dateKeyOffset(-20), log:{}, requiredPerWeek:2, days:[today, other], weeklyLogs:{}, weekHistory:[], firstFullWeek:firstFullWeekFor(todayKey()) }; data.habits.build.push(h);
    logWeeklyHabit('tw1', 1); const n1 = (h.weeklyLogs[currentWeekId()] || []).length; T('log on a scheduled day works once', n1 === 1);
    logWeeklyHabit('tw1', 1); logWeeklyHabit('tw1', 1); T('same day twice does not add', (h.weeklyLogs[currentWeekId()] || []).length === 1);
    logWeeklyHabit('tw1', -1); T('undo (-1) does nothing', (h.weeklyLogs[currentWeekId()] || []).length === 1);
    const h2 = { id:'tw2', text:'قراءة', type:'W', importance:'normal', createdAt:dateKeyOffset(-20), log:{}, requiredPerWeek:1, days:[(today + 2) % 7], weeklyLogs:{}, weekHistory:[], firstFullWeek:firstFullWeekFor(todayKey()) }; data.habits.build.push(h2);
    logWeeklyHabit('tw2', 1); T('log on a non-scheduled day is refused', (h2.weeklyLogs[currentWeekId()] || []).length === 0);
    const legacy = { id:'tw3', text:'قديمة', type:'W', importance:'normal', createdAt:dateKeyOffset(-40), log:{}, requiredPerWeek:3, weeklyLogs:{ '2026-01-04':['2026-01-05'] }, weekHistory:[{ weekId:'2026-01-04', done:1, required:3, ok:false, partial:false }], firstFullWeek:'2026-01-11' }; data.habits.build.push(legacy);
    logWeeklyHabit('tw3', 1); T('legacy weekly (no days): blocked until a schedule is chosen, records kept', !(legacy.weeklyLogs[currentWeekId()] || []).length && legacy.weekHistory.length === 1 && legacy.weeklyLogs['2026-01-04'].length === 1);
    setHabitDay('tw3', today); T('choosing days keeps old logs/history', legacy.days.length === 1 && legacy.weekHistory.length === 1 && legacy.requiredPerWeek === 1);
    renderHabitsPage(); T('no «تراجع عن آخر تسجيل» anywhere', document.body.innerText.indexOf('تراجع عن آخر تسجيل') === -1 && !document.querySelector('[data-undo]'));
    const btn = [...document.querySelectorAll('#build-habit-list .habit-card')].find(c=>c.textContent.indexOf('قراءة') !== -1);
    T('button disabled off-schedule', btn && btn.querySelector('.stat-btn').disabled); }

  /* ---- decoupling from planning ---- */
  { const arch = { id:'a1', weekId:dateKeyOffset(-14), startedAt:'t', name:'خطة', status:'completed', cause:'completed',
      tasksWeek:{ holidayDay:6, days:{ 0:[{ id:'x1', text:'a', status:'done' }, { id:'x2', text:'b', status:'done' }], 1:[], 2:[], 3:[], 4:[], 5:[], 6:[] } }, learnWeek:null };
    const hs0 = CodisDiscipline.weekStats(arch.weekId); const r = CodisEconomy.weeklyFromArchive(arch);
    T('weekly outcome ignores habits (overall == plan %)', r && r.entry.pct === r.entry.stats.planPct && r.entry.stats.habitPct === null, r && r.entry.pct + '/' + r.entry.stats.habitPct);
    T('weekly report carries no habit rows', r && r.entry.report && r.entry.report.habits.length === 0 && r.entry.report.weights.habit === 0);
    const m = Object.keys(L()).length; const sm = CodisEconomy.monthStats(econThisMonthKey());
    T('monthly stats have no habits component', !sm || !sm.parts.some(p=>p.k === 'habits')); const nPun = Object.values(L()).filter(e=>e.scope === 'habit' && e.kind === 'punish').length; T('habit penalties exist yet do not count as monthly punishments', nPun > 5 && (!sm || sm.punishments === 0 || sm.punishments < nPun), nPun + '/' + (sm && sm.punishments)); }

  /* ---- push plan (client side; the server send needs a real project) ---- */
  { const old = CodisAccount.state; let patched = false; try{ CodisAccount.state = { user:{ id:'1a2b3c4d-0000-0000-0000-000000000000' } }; patched = CodisAccount.state.user.id.length > 0; }catch(e){}
    if(patched){ const p = CodisHabitPush.plan(); const ids = Object.keys(p);
      T('plan: 23:00 reminder per day lists open daily habits', ids.some(i=>i.indexOf('ev_hn231a2b3c4d') === 0) && Object.values(p).some(x=>x.title === 'تذكير بالعادات اليومية' && new Date(x.at).getHours() === 23));
      { const w = Object.values(p).filter(x=>x.title === 'موعد عادة اليوم'); const sch = [codisTodayIdx(), (codisTodayIdx() + 3) % 7]; T('plan: weekly reminders at 09:00 on the chosen days only, for the right habit', w.every(x=>new Date(x.at).getHours() === 9 && x.body.indexOf('اليوم موعد عادة ') === 0) && w.filter(x=>x.body.endsWith('رياضة')).length >= 1 && w.filter(x=>x.body.endsWith('رياضة')).every(x=>sch.indexOf(new Date(x.at).getDay()) !== -1), w.length); }
      T('plan: event ids are valid and unique', ids.every(i=>/^ev_[a-z0-9]{6,40}$/.test(i)) && new Set(ids).size === ids.length);
      T('plan: event habits never get reminders', !Object.values(p).some(x=>x.body.indexOf('حدثية') !== -1));
      try{ CodisAccount.state = old; }catch(e){} }
    else T('plan could not run: CodisAccount.state not writable', false); }

  return JSON.stringify({ passed:out.filter(x=>x.ok).length, failed:out.filter(x=>!x.ok).length, failures:out.filter(x=>!x.ok) });
})();
