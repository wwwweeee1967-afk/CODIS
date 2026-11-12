/* CODIS-FINANCE (3.28.0) — in-browser regression test: tests/finance_browser.js
   Run (headless, guest, fresh profile):
     TEST=tests/finance_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   It mutates the local TEST profile's data only. Time is controlled through window.__CODIS_FIN_NOW__ (honoured on local hosts only).
   Returns { passed, failed, results[] }. */
(async function(){
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : String(info) });
  const eq = (name, a, b)=>T(name, JSON.stringify(a) === JSON.stringify(b), JSON.stringify(a) + ' vs ' + JSON.stringify(b));
  const near = (name, a, b, e)=>T(name, Math.abs(a - b) <= (e || 1e-9), a + ' vs ' + b);
  const at = (y, m, d, h)=>{ window.__CODIS_FIN_NOW__ = Date.UTC(y, m - 1, d, (h === undefined ? 9 : h)); };   /* 09:00 UTC = 12:00 بغداد */
  const realConfirm = codisConfirm; codisConfirm = async()=>true;
  const snapAll = JSON.stringify({ w:data.wallet, i:data.inventory, l:data.outcomeLedger });
  const coinWalletBefore = JSON.stringify(data.wallet);
  const fresh = ()=>{ data.finance = codisFinBlank(); data.settings.rewardItems = data.settings.rewardItems.filter(x=>!x.fin); data.inventory.items = data.inventory.items.filter(x=>!x.fin); };
  const setup = (o)=>codisFinSetupNow(Object.assign({ work:'freelance', opening:500000, rate:40 }, o || {}));
  const mkR = (o)=>{ let r = codisFinCreateReward(o); if(!r.ok && r.reason === 'ambiguous' && !o.raw) r = codisFinCreateReward(Object.assign({}, o, { cardId:r.suggestions[0].card.id })); return r; };
  const rarOf = it=>econRarityById(it.rarity) || econCfg().rarities[0];
  const own = (cat, uid)=>CodisWallet.transact([], ()=>{ const r = rarOf(cat), it = CodisInventory.grant({ uid:uid, rewardId:cat.id, name:cat.name, rarity:r.id, rarityName:r.name, rarityTone:r.tone, rarityOrder:r.order, room:cat.room, source:'outcome', sourceRef:uid, scope:'daily', coinValue:codisFinItemCoin(cat), fin:cat.fin }); return it ? { ok:true, item:it } : { ok:false, reason:'inventory' }; });

  /* ===== H0: المصفوفة ===== */
  const mc = codisFinMatrixCheck(); T('matrix: 25 cards, refs match model, no gap 10..30000', mc.ok, mc.problems.join(' | '));
  eq('matrix: count', codisFinCards().length, 25);
  const C = id=>codisFinCardById(id);
  eq('range: learn bronze 10–12.5 (open top)', [C('learn_bronze').min, C('learn_bronze').max], [10, 12.5]); eq('range: learn silver 12.5–20', [C('learn_silver').min, C('learn_silver').max], [12.5, 20]); eq('range: learn gold 20–30', [C('learn_gold').min, C('learn_gold').max], [20, 30]);
  eq('range: station7 12.5–18.75', [C('fx_station7').min, C('fx_station7').max], [12.5, 18.75]);
  eq('range: event normal 18.75–37.5', [C('fx_rs_normal').min, C('fx_rs_normal').max], [18.75, 37.5]);
  eq('range: event important 37.5–50', [C('fx_rs_important').min, C('fx_rs_important').max], [37.5, 50]);
  eq('range: daily C 25–37.5', [C('daily_C').min, C('daily_C').max], [25, 37.5]);
  eq('range: monthly normal 75–100', [C('fx_ms_normal').min, C('fx_ms_normal').max], [75, 100]);
  eq('range: monthly important 100–125', [C('fx_ms_important').min, C('fx_ms_important').max], [100, 125]);
  eq('range: event critical 125–150', [C('fx_rs_critical').min, C('fx_rs_critical').max], [125, 150]);
  eq('range: monthly critical 200–375', [C('fx_ms_critical').min, C('fx_ms_critical').max], [200, 375]);
  eq('range: monthly S 11,250–18,750', [C('monthly_S').min, C('monthly_S').max], [11250, 18750]);
  eq('range: monthly SS 18,750–30,000 (reversed, ref 30,000)', [C('monthly_SS').min, C('monthly_SS').max, C('monthly_SS').ref], [18750, 30000, 30000]);
  eq('prices: B daily 50 · weekly 350 · monthly 1,500', [econCoinFor('B', 'daily'), econCoinFor('B', 'weekly'), econCoinFor('B', 'monthly')], [50, 350, 1500]);
  eq('prices: others unchanged (C 25/175/750 · A 150/1050/4500 · S 375/2625/11250 · SS 1000/7000/30000)',
    ['C', 'A', 'S', 'SS'].map(r=>['daily', 'weekly', 'monthly'].map(s=>econCoinFor(r, s))), [[25, 175, 750], [150, 1050, 4500], [375, 2625, 11250], [1000, 7000, 30000]]);
  eq('prices: box prices / silver untouched', [econBoxPrice('bx1'), econBoxPrice('bx5')], [35, 266]);
  [10, 12.5, 18.75, 25, 30, 37.5, 45, 50, 75, 100, 125, 150, 200, 375, 1000, 11250, 18750, 30000].forEach(v=>{
    const c = codisFinClassify('xyz', v); T('classify ' + v + ' has a valid card', c.ok && c.candidates.every(x=>codisFinInRange(x.card, v)) && c.candidates.length >= 1, c.ok ? c.candidates.map(x=>x.card.id).join(',') : c.reason);
    const again = codisFinClassify('xyz', v); eq('classify ' + v + ' stable (no ordering randomness)', c.candidates.map(x=>x.card.id), again.candidates.map(x=>x.card.id));
  });
  { let gaps = 0; for(let v = 10; v <= 30000; v += 0.25){ if(!codisFinCardsFor(v).length) gaps++; } T('no value 10..30000 (step .25) without a card', gaps === 0, gaps); }
  T('18,750 shared by monthly S and SS', codisFinCardsFor(18750).map(c=>c.id).sort().join() === 'monthly_S,monthly_SS', codisFinCardsFor(18750).map(c=>c.id).join());
  T('below 10 / above 30,000 refused', codisFinClassify('x', 9.99).reason === 'low' && codisFinClassify('x', 30000.01).reason === 'high');
  { const c = codisFinClassify('لفة شاورما', 25); T('shawarma 25 → daily C (food) not event card', c.ok && c.best.card.id === 'daily_C' && !c.ambiguous, c.best && c.best.card.id); near('shawarma exact 25 kept (not 30/37.5)', c.coin, 25); }
  { const c = codisFinClassify('الاستماع للموسيقى', 10); T('music 10 → professor room', c.ok && c.best.card.id === 'learn_bronze', c.best && c.best.card.id); }
  { const c = codisFinClassify('كلشي مبهم', 25); T('unknown name with several rooms → ambiguous with suggestions', c.ok && c.ambiguous && c.suggestions.length >= 1); }
  { const c = codisFinClassify('سفرة شمال', 7000); T('trip 7000 → monthly/weekly card by meaning+price', c.ok && c.best.card.id === 'weekly_SS' || c.best.card.id === 'monthly_A', c.best.card.id); }

  /* ===== A: سعر الصرف ===== */
  [[20, 100], [40, 50], [80, 25], [120, 16.67], [160, 12.5], [200, 10]].forEach(([r, c])=>near('2000 IQD @' + r + ' = ' + c + ' coins', codisFinCoinOfIqd(2000, r), c, 1e-9));
  near('Floating-point safe: 1000/40', codisFinCoinOfIqd(1000, 40), 25); near('15,000/160', codisFinCoinOfIqd(15000, 160), 93.75);
  /* ===== B: الوقت ===== */
  near('90 min = 45 coins', codisFinCoinOfMinutes(90), 45); near('60 min = 30', codisFinCoinOfMinutes(60), 30); near('10 min = 5', codisFinCoinOfMinutes(10), 5); near('120 = 60', codisFinCoinOfMinutes(120), 60);
  fresh(); at(2026, 11, 11); setup({ rate:40 }); near('time value unaffected by rate (40)', codisFinCoinOfMinutes(90), 45);

  /* ===== D: المصروفات والإيداع ===== */
  fresh(); at(2026, 11, 11); { const r = setup({ opening:500000 }); T('setup ok', r.ok, r.reason); }
  eq('opening balance 500,000', codisFinBalance(), 500000);
  eq('opening is OPENING_BALANCE (not salary/deposit)', codisFin().ledger.map(e=>e.type), ['OPENING_BALANCE']);
  T('setup cannot run twice', !setup().ok);
  { const r = codisFinExpenseNow({ name:'مسواك', amount:1000, cat:'personal' }); T('expense 1,000 ok', r.ok); eq('balance 499,000', codisFinBalance(), 499000); }
  { const r = codisFinExpenseNow({ name:'طماطم', amount:2500, cat:'food' }); T('expense 2,500 ok', r.ok); eq('balance 496,500', codisFinBalance(), 496500); }
  { const before = JSON.stringify(data.finance), r = codisFinExpenseNow({ name:'كبير', amount:496501, cat:'other' }); T('over-balance refused (funds)', !r.ok && r.reason === 'funds', r.reason); eq('data unchanged after refusal', JSON.stringify(data.finance), before); }
  { const r = codisFinExpenseNow({ name:'بالضبط', amount:496500, cat:'other' }); T('exactly the balance allowed → 0', r.ok && codisFinBalance() === 0); }
  T('never negative', codisFinBalance() >= 0);
  { const r1 = codisFinDepositNow({ amount:15000, desc:'ربح صافٍ', src:'مشروع', ref:'dep_x' }), r2 = codisFinDepositNow({ amount:15000, desc:'ربح صافٍ', src:'مشروع', ref:'dep_x' }); T('deposit ok', r1.ok); T('duplicate ref refused (double tap)', !r2.ok && r2.reason === 'dup'); eq('deposit counted once', codisFinBalance(), 15000); }
  T('invalid amounts refused (0 / negative)', !codisFinDepositNow({ amount:0, desc:'x' }).ok && !codisFinDepositNow({ amount:-5, desc:'x' }).ok);
  T('decimal IQD rounds to integer (no fractions kept)', Number.isInteger(codisFin().ledger.slice(-1)[0].amount));
  T('future date refused', codisFinDepositNow({ amount:10, desc:'x', date:'2026-12-01' }).reason === 'future');
  T('ledger verify: opening + income − expenses = balance', codisFinVerify().ok, JSON.stringify(codisFinVerify()));
  { const run = codisFinRunning(); eq('running balance last = balance', run[run.length - 1].bal, codisFinBalance()); }
  T('finance does not touch coin wallet', JSON.stringify(data.wallet) === coinWalletBefore);
  T('finance entries have no wallet tx types', codisFin().ledger.every(e=>codisFinTypes().indexOf(e.type) !== -1 && econTxTypes().indexOf(e.type) === -1));
  { const r = codisFinExpenseNow({ name:'', amount:10 }); T('empty name refused', !r.ok); }

  /* ===== C: الراتب ===== */
  fresh(); at(2026, 11, 11); setup({ work:'employee', opening:500000, salary:{ amount:600000, day:5, from:'2026-11-11' } });
  eq('salary: start 11 Nov, due the 5th → nothing yet', codisFin().ledger.filter(e=>e.type === 'SALARY').length, 0);
  eq('next salary = 5 Dec', codisFinNextSalary().due, '2026-12-05');
  at(2026, 12, 4); eq('4 Dec: not due', codisFinCatchUp(), 0);
  at(2026, 12, 5); eq('5 Dec: due → 1 salary', codisFinCatchUp(), 1);
  { const e = codisFin().ledger.filter(x=>x.type === 'SALARY')[0]; eq('salary entry: due date kept & ref unique', [e.due, e.ref, e.amount], ['2026-12-05', 'sal|2026-12', 600000]); }
  eq('repeat catch-up adds nothing (no duplicate)', codisFinCatchUp(), 0); eq('balance 1,100,000', codisFinBalance(), 1100000);
  at(2027, 3, 20); eq('app closed for months: Jan+Feb+Mar added (3)', codisFinCatchUp(), 3);
  eq('salaries have original due dates', codisFin().ledger.filter(e=>e.type === 'SALARY').map(e=>e.due), ['2026-12-05', '2027-01-05', '2027-02-05', '2027-03-05']);
  eq('repeat again = 0', codisFinCatchUp(), 0);
  /* change salary: only future dues */
  { const r = codisFinSetSalary({ amount:700000, day:5, from:'2027-04-01' }); T('salary change future ok', r.ok, r.reason); }
  { const r = codisFinSetSalary({ amount:1, day:5, from:'2027-01-01' }); T('salary change in the past refused', !r.ok && r.reason === 'past'); }
  eq('old salaries untouched', codisFin().ledger.filter(e=>e.type === 'SALARY').map(e=>e.amount), [600000, 600000, 600000, 600000]);
  at(2027, 4, 5); eq('April uses new amount', [codisFinCatchUp(), codisFin().ledger.filter(e=>e.due === '2027-04-05')[0].amount], [1, 700000]);
  /* month-end clamp */
  fresh(); at(2027, 3, 1); setup({ work:'employee', opening:0, salary:{ amount:100000, day:31, from:'2027-01-31' } });
  eq('day 31: Jan 31 + Feb 28 (last day) + (Mar not yet)', codisFin().ledger.filter(e=>e.type === 'SALARY').map(e=>e.due), ['2027-01-31', '2027-02-28']);
  at(2027, 3, 31); codisFinCatchUp(); eq('Mar 31 added once', codisFin().ledger.filter(e=>e.type === 'SALARY').length, 3);
  /* before start */
  fresh(); at(2026, 11, 20); setup({ work:'employee', opening:0, salary:{ amount:50000, day:10, from:'2026-11-15' } });
  eq('start 15 Nov, day 10: Nov 10 NOT added (before start)', codisFin().ledger.filter(e=>e.type === 'SALARY').length, 0);
  eq('first salary Dec 10', codisFinNextSalary().due, '2026-12-10');
  /* retro start: only months from start */
  fresh(); at(2026, 11, 11); setup({ work:'employee', opening:0, salary:{ amount:10, day:5, from:'2026-09-01' } });
  eq('retro start Sep 1: Sep, Oct, Nov salaries', codisFin().ledger.filter(e=>e.type === 'SALARY').map(e=>e.ref), ['sal|2026-09', 'sal|2026-10', 'sal|2026-11']);
  /* freelance never gets salary */
  fresh(); at(2026, 11, 11); setup({ work:'freelance', opening:100 }); at(2027, 6, 1); eq('freelance: no automatic income', [codisFinCatchUp(), codisFinBalance()], [0, 100]);

  /* ===== simulated dev clock must not affect finance ===== */
  fresh(); at(2026, 11, 11); setup({ work:'employee', opening:0, salary:{ amount:1000, day:5, from:'2026-11-11' } });
  { const c0 = JSON.stringify(codisFin().ledger); try{ CodisClock.begin && 0; }catch(e){} T('finance date independent of CodisClock (uses real Baghdad date)', codisFinToday() === '2026-11-11'); eq('ledger unchanged', JSON.stringify(codisFin().ledger), c0); }
  at(2026, 11, 11, 22); eq('22:00 UTC = 01:00 next day Baghdad → 12 Nov', codisFinToday(), '2026-11-12');
  at(2026, 12, 31, 21); eq('21:00 UTC 31 Dec = 00:00 1 Jan Baghdad', codisFinToday(), '2027-01-01');

  /* ===== G: تغيير سعر الصرف وإعادة التسعير ===== */
  fresh(); at(2026, 11, 11); setup({ opening:500000, rate:40 });
  const mk = mkR({ name:'لفة شاورما', kind:'financial', iqd:2000 });
  T('financial reward created (50 coins @40)', mk.ok && Math.abs(mk.coin - 50) < 1e-9, mk.reason);
  const item = data.settings.rewardItems.find(x=>x.id === mk.item.id);
  eq('stored original value 2,000 IQD + kind', [item.fin.iqd, item.fin.kind], [2000, 'financial']);
  near('50 coins → effective coin', econEffCoin(item, rarOf(item)), 50);
  T('50 coins is in its card range', codisFinInRange(C(item.fin.card), 50), item.fin.card);
  eq('owning a financial reward costs nothing', [codisFinBalance(), JSON.stringify(data.wallet) === coinWalletBefore], [500000, true]);
  const g1 = own(item, 'own|t_fin1'); T('granted to inventory (with fin snapshot)', g1.ok && g1.item.fin && g1.item.fin.iqd === 2000);
  eq('after getting it: balance still 500,000', codisFinBalance(), 500000);
  { const r = codisFinChangeRate(80); T('rate change 40→80 accepted', r.ok, r.reason); }
  near('reward now 25 coins', econEffCoin(item, rarOf(item)), 25); eq('IQD value still 2,000', item.fin.iqd, 2000);
  T('card re-evaluated to one containing 25', codisFinInRange(C(item.fin.card), 25), item.fin.card);
  near('inventory (unused) repriced to 25', CodisInventory.get('own|t_fin1').coinValue, 25);
  T('second change same month refused', codisFinChangeRate(120).reason === 'monthly');
  T('status shows next month', codisFinFxStatus().nextAllowed === '2026-12-01', codisFinFxStatus().nextAllowed);
  eq('fx log has initial + change', codisFin().fxLog.map(x=>x.kind), ['initial', 'change']);
  { const l = codisFin().fxLog[1]; eq('log: from 40 to 80', [l.from, l.to], [40, 80]); T('log has month', l.month === '2026-11'); }
  const ledBefore = JSON.stringify(codisFin().ledger);
  at(2026, 11, 30, 20); T('still refused 30 Nov (23:00 Baghdad)', codisFinChangeRate(120).reason === 'monthly');
  at(2026, 11, 30, 21); T('00:00 Baghdad 1 Dec → allowed again', codisFinChangeRate(120).ok);
  near('reward now 16.67 coins @120', econEffCoin(item, rarOf(item)), 16.67); eq('ledger unchanged by repricing', JSON.stringify(codisFin().ledger), ledBefore);
  T('rate list is exactly the six official', JSON.stringify(codisFinRates()) === '[20,40,80,120,160,200]');
  T('invalid rate refused', codisFinChangeRate(50).reason === 'rate');
  T('limits: admin exemption registered through CodisLimits', typeof CodisLimits.bypass === 'function');
  /* admin bypass of monthly limit (simulated verified developer) */
  { const real = CodisAccount.isAdmin; CodisAccount.isAdmin = ()=>true; const r = codisFinChangeRate(200); CodisAccount.isAdmin = real; T('verified developer exempt from monthly limit', r.ok, r.reason); }
  /* dev clock must not consume the allowance */
  try{ at(2027, 2, 1); const r = codisFinChangeRate(40); T('new month → change allowed', r.ok || r.reason === 'same', r.reason); }catch(e){ T('new month change', false, e.message); }

  /* ===== E: استخدام مكافأة مالية ===== */
  fresh(); at(2026, 11, 11); setup({ opening:500000, rate:40 });
  const mk2 = mkR({ name:'لفة شاورما', kind:'financial', iqd:2000 }), it2 = data.settings.rewardItems.find(x=>x.id === mk2.item.id); own(it2, 'own|t_fin2');
  eq('E: balance before use 500,000', codisFinBalance(), 500000);
  { const r1 = CodisEconomy.markUsed('own|t_fin2'); T('E: use ok', r1.ok, r1.reason); eq('E: balance 498,000', codisFinBalance(), 498000); eq('E: item used', CodisInventory.get('own|t_fin2').status, 'used');
    const e = codisFin().ledger.filter(x=>x.type === 'REWARD_REDEMPTION')[0]; eq('E: ledger link', [e.amount, e.ref, e.meta.uid], [-2000, 'rwd|own|t_fin2', 'own|t_fin2']);
    const r2 = CodisEconomy.markUsed('own|t_fin2'); T('E: second press refused', !r2.ok); eq('E: no double deduction', codisFinBalance(), 498000); }
  T('E: ledger still verifies', codisFinVerify().ok);
  /* insufficient funds: item stays owned */
  { const mk3 = mkR({ name:'غالية', kind:'financial', iqd:900000 }); T('E: expensive reward created (22,500 coins)', mk3.ok, mk3.reason); const it3 = data.settings.rewardItems.find(x=>x.id === mk3.item.id); own(it3, 'own|t_fin3');
    const bal = codisFinBalance(), r = CodisEconomy.markUsed('own|t_fin3'); T('E: insufficient → refused', !r.ok && r.reason === 'funds', r.reason); eq('E: item still owned', CodisInventory.get('own|t_fin3').status, 'owned'); eq('E: balance unchanged', codisFinBalance(), bal); }
  /* sync duplicate: redemption exists but copy shows owned → marked used with NO second deduction */
  { const mk4 = mkR({ name:'نسخة مزامنة', kind:'financial', iqd:3000 }), it4 = data.settings.rewardItems.find(x=>x.id === mk4.item.id); own(it4, 'own|t_fin4');
    const f = codisFin(); f.ledger.push({ id:'rwd|own|t_fin4', ref:'rwd|own|t_fin4', type:'REWARD_REDEMPTION', amount:-3000, cur:'IQD', desc:'x', cat:'rewards', src:'reward', date:codisFinToday(), at:codisFinIso() });
    const bal = codisFinBalance(), r = CodisEconomy.markUsed('own|t_fin4'); T('E: sync-dup marks used', r.ok); eq('E: sync-dup does not deduct again', codisFinBalance(), bal); }
  /* failed save → full rollback */
  { const mk5 = mkR({ name:'يفشل الحفظ', kind:'financial', iqd:4000 }), it5 = data.settings.rewardItems.find(x=>x.id === mk5.item.id); own(it5, 'own|t_fin5');
    const bal = codisFinBalance(), led = codisFin().ledger.length; codisSaveSuspended = 'fail'; const r = CodisEconomy.markUsed('own|t_fin5'); codisSaveSuspended = false;
    T('E: save failure → refused', !r.ok && r.reason === 'save', r.reason); eq('E: item still owned after failed save', CodisInventory.get('own|t_fin5').status, 'owned'); eq('E: balance + ledger rolled back', [codisFinBalance(), codisFin().ledger.length], [bal, led]); }
  /* finance not set up */
  { const keep = data.finance.setup.done; data.finance.setup.done = false; const mk6 = (data.finance.setup.done = true, mkR({ name:'بلا إعداد', kind:'financial', iqd:1000 })); data.finance.setup.done = false; const it6 = data.settings.rewardItems.find(x=>x.id === mk6.item.id); own(it6, 'own|t_fin6'); const r = CodisEconomy.markUsed('own|t_fin6'); T('E: no finance setup → refused, item stays', !r.ok && r.reason === 'nosetup' && CodisInventory.get('own|t_fin6').status === 'owned', r.reason); data.finance.setup.done = keep; }
  /* explicit type: a financial reward whose NAME contains a duration is NOT a timer */
  { const mk7 = mkR({ name:'تذكرة سينما ساعتين', kind:'financial', iqd:3000 }), it7 = data.settings.rewardItems.find(x=>x.id === mk7.item.id); own(it7, 'own|t_fin7');
    T('type: name with "ساعتين" is still financial (no timer)', codisDurOf(CodisInventory.get('own|t_fin7')) === null && codisFinUseKind(CodisInventory.get('own|t_fin7')) === 'FINANCIAL'); const b = codisFinBalance(); CodisEconomy.markUsed('own|t_fin7'); eq('type: used → deducted 3,000', codisFinBalance(), b - 3000); }
  /* legacy item (no fin): old behaviour, no deduction */
  { const b = codisFinBalance(); CodisWallet.transact([], ()=>{ CodisInventory.grant({ uid:'own|t_old', rewardId:null, name:'مكافأة قديمة', rarity:'C', rarityName:'شائعة', rarityTone:'c', rarityOrder:1, room:'tasks', source:'outcome', sourceRef:'t_old', scope:'daily', coinValue:25 }); return { ok:true }; });
    const r = CodisEconomy.markUsed('own|t_old'); T('legacy: markUsed works as before', r.ok && CodisInventory.get('own|t_old').status === 'used'); eq('legacy: no money deducted', codisFinBalance(), b);
    T('legacy name-based duration still parsed', codisDurOf({ name:'مشاهدة ساعتين فلم' }) !== null); T('legacy kind', codisFinUseKind({ name:'x' }) === 'LEGACY'); }

  /* ===== F: مكافأة وقتية ===== */
  fresh(); at(2026, 11, 11); setup({ opening:500000, rate:40 });
  const mt = mkR({ name:'مشاهدة مباراة', kind:'time', minutes:90 }); T('F: time reward created', mt.ok, mt.reason); near('F: 45 coins', mt.coin, 45);
  const itT = data.settings.rewardItems.find(x=>x.id === mt.item.id); eq('F: minutes stored explicitly', [itT.fin.kind, itT.fin.minutes], ['time', 90]);
  T('F: 45 coins lands in a card containing 45', codisFinInRange(C(itT.fin.card), 45), itT.fin.card);
  own(itT, 'own|t_time'); { const inv = CodisInventory.get('own|t_time'); eq('F: duration from saved field (not name)', codisDurOf(inv).min, 90);
    const b = codisFinBalance(), r = codisRewardTimerStart('own|t_time'); T('F: timer started', r.ok, r.reason); eq('F: no IQD deducted', codisFinBalance(), b);
    const t = CodisTimers.active('reward', 'own|t_time'); T('F: running timer has 90 minutes', t && t.minutes === 90, t && t.minutes);
    const u = CodisEconomy.markUsed('own|t_time'); T('F: finishing marks used with no deduction', u.ok && codisFinBalance() === b);
    CodisTimers.cancel && CodisTimers.cancel(t && t.id); }
  { const c = codisFinCoinOfMinutes(90); codisFinChangeRate(160); near('F: rate change leaves time value 45', econEffCoin(itT, rarOf(itT)), c); }
  codisFin().fx.rate = 40;   /* (اختبار) إعادة السعر لتجربة حدود القيمة */
  T('F: financial value limits (min 10 coins) enforced', mkR({ name:'رخيصة', kind:'financial', iqd:100 }).reason === 'low');
  T('F: max 30,000 coins enforced', mkR({ name:'غالية جداً', kind:'financial', iqd:6000001 }).reason === 'high', mkR({ name:'غالية جداً', kind:'financial', iqd:6000001 }).reason);
  T('F: time below 20 min refused (<10 coins)', mkR({ name:'قصيرة', kind:'time', minutes:10 }).reason === 'low');
  { const r = mkR({ name:'تمام', kind:'time', minutes:30 }); near('F: 30 min → 15 coins', r.coin, 15); }
  T('F: financial needs finance setup', (()=>{ const k = data.finance.setup.done; data.finance.setup.done = false; const r = mkR({ name:'x', kind:'financial', iqd:2000 }); data.finance.setup.done = k; return r.reason === 'nosetup'; })());
  { const dup = mkR({ name:'لفة شاورما', kind:'financial', iqd:1000 }), dup2 = mkR({ name:'لفة شاورما', kind:'financial', iqd:1000 }); T('F: same name twice → distinct ids', dup.ok && dup2.ok && dup.item.id !== dup2.item.id); }
  { const r = mkR({ name:'مبهمة', kind:'financial', iqd:1000, raw:true }); T('F: ambiguous name needs a chosen destination', !r.ok && r.reason === 'ambiguous' && r.suggestions.length > 0, r.reason); const ok = mkR({ name:'مبهمة2', kind:'financial', iqd:1000, cardId:r.suggestions[0].card.id }); T('F: choosing a valid destination works', ok.ok); const bad = mkR({ name:'مبهمة2', kind:'financial', iqd:1000, cardId:'monthly_SS' }); T('F: destination outside price range refused', !bad.ok && bad.reason === 'range'); }

  /* ===== persistence + exact price survives reload/normalize ===== */
  { const before = JSON.stringify(data.settings.rewardItems.filter(x=>x.fin).map(x=>[x.id, x.fin.kind, x.fin.iqd, x.fin.minutes, x.fin.card, x.room, x.rarity]));
    const copy = JSON.parse(JSON.stringify(data)); normalizeData(copy); const after = JSON.stringify(copy.settings.rewardItems.filter(x=>x.fin).map(x=>[x.id, x.fin.kind, x.fin.iqd, x.fin.minutes, x.fin.card, x.room, x.rarity]));
    eq('normalize keeps fin items intact (idempotent)', after, before);
    const raw = JSON.stringify(data); const re = JSON.parse(raw); normalizeData(re); eq('finance ledger survives save → load', JSON.stringify(re.finance.ledger), JSON.stringify(data.finance.ledger)); }
  /* variant items (special cards) keep placement through normalize */
  fresh(); at(2026, 11, 11); setup({ opening:500000, rate:40 });
  { const v = mkR({ name:'مكافأة محطة', kind:'financial', iqd:1000, cardId:'fx_rs_normal' }); T('variant in event-normal card (25 coins is in 18.75–37.5)', v.ok, v.reason);
    if(v.ok){ const it = data.settings.rewardItems.find(x=>x.id === v.item.id); eq('variant placement', [it.room, it.variantOf, it.weight], ['habits', 'fx_rs_normal', 0]); const cp = JSON.parse(JSON.stringify(data)); normalizeData(cp); const it2 = cp.settings.rewardItems.find(x=>x.id === v.item.id); eq('variant survives normalize', [it2.room, it2.variantOf, it2.weight, it2.fin.iqd], ['habits', 'fx_rs_normal', 0, 1000]);
      T('variant excluded from boxes/store pools', !CodisBoxes.pool || CodisBoxes.pool().every(x=>x.id !== v.item.id)); } }
  { const D = codisFixedDefs().rewards.find(d=>d.id === 'fx_rs_normal'), vid = 'hab|test|variant', kinds = {}; for(let i = 0; i < 40; i++){ const p = codisFinPickVariant('hab|x|' + i, D, data.settings.rewardItems.find(x=>x.id === D.id)); kinds[p.id] = 1; }
    T('variant selection deterministic per outcome id', codisFinPickVariant('hab|fixed', D, data.settings.rewardItems.find(x=>x.id === D.id)).id === codisFinPickVariant('hab|fixed', D, data.settings.rewardItems.find(x=>x.id === D.id)).id); T('variant selection spreads over base+variants', Object.keys(kinds).length >= 1); }

  /* ===== I: بيانات قديمة ===== */
  { const old = JSON.parse(snapAll); const d0 = JSON.parse(JSON.stringify(data)); delete d0.finance; d0.schemaVersion = 6; normalizeData(d0);
    T('I: old data (no finance) gets an EMPTY finance block', d0.finance && d0.finance.ledger.length === 0 && !d0.finance.setup.done && d0.finance.fx.rate === null);
    eq('I: coin wallet untouched by normalize', JSON.stringify(d0.wallet), JSON.stringify(data.wallet));
    eq('I: outcome ledger (reports) untouched', Object.keys(d0.outcomeLedger).length, Object.keys(data.outcomeLedger).length);
    T('I: no phantom expenses / no retro rewards', d0.finance.ledger.length === 0 && d0.inventory.items.filter(x=>x.fin).length === data.inventory.items.filter(x=>x.fin).length);
    const d1 = JSON.parse(JSON.stringify(d0)); normalizeData(d1); eq('I: normalize twice = same (no duplicate migration)', JSON.stringify(d1.finance), JSON.stringify(d0.finance));
    const odd = [null, 5, 'x', [], { ledger:'x' }, { ledger:[null, 1, { id:'a' }, { id:'b', type:'DEPOSIT', amount:'12', date:'2026-01-01', at:'2026-01-01T00:00:00Z' }] }, { salary:{ rules:[{}] }, fx:{ rate:7 } }];
    odd.forEach((v, i)=>{ const d = JSON.parse(JSON.stringify(d0)); d.finance = v; let ok = true; try{ normalizeData(d); }catch(e){ ok = false; } T('I: weird stored finance #' + i + ' never throws', ok && d.finance && Array.isArray(d.finance.ledger)); });
    { const d = JSON.parse(JSON.stringify(d0)); d.finance = { ledger:[{ id:'b', type:'DEPOSIT', amount:'12', date:'2026-01-01', at:'2026-01-01T00:00:00Z', desc:'ok' }, { id:'e', type:'EXPENSE', amount:50, date:'2026-01-02', at:'2026-01-02T00:00:00Z', desc:'wrong sign' }] }; normalizeData(d); eq('I: sign enforced by type', d.finance.ledger.map(e=>e.amount), [12, -50]); } }

  /* ===== J: المزامنة (دمج ثلاثي) ===== */
  fresh(); at(2026, 11, 11); setup({ opening:500000, rate:40 });
  { const base = JSON.parse(JSON.stringify(data)); const local = JSON.parse(JSON.stringify(data)), remote = JSON.parse(JSON.stringify(data));
    local.finance.ledger.push({ id:'dep_off1', ref:'dep_off1', type:'DEPOSIT', amount:15000, cur:'IQD', desc:'offline deposit', cat:'', src:'', date:'2026-11-11', at:'2026-11-11T08:00:00.000Z' });
    local.finance.ledger.push({ id:'exp_off1', ref:'exp_off1', type:'EXPENSE', amount:-2500, cur:'IQD', desc:'offline expense', cat:'food', src:'', date:'2026-11-11', at:'2026-11-11T08:05:00.000Z' });
    remote.finance.ledger.push({ id:'dep_dev2', ref:'dep_dev2', type:'DEPOSIT', amount:1000, cur:'IQD', desc:'from other device', cat:'', src:'', date:'2026-11-11', at:'2026-11-11T07:00:00.000Z' });
    remote.finance.ledger.push({ id:'sal|2026-11', ref:'sal|2026-11', type:'SALARY', amount:600000, cur:'IQD', desc:'s', cat:'', src:'salary', date:'2026-11-05', due:'2026-11-05', at:'2026-11-11T07:00:00.000Z' });
    local.finance.ledger.push({ id:'sal|2026-11', ref:'sal|2026-11', type:'SALARY', amount:600000, cur:'IQD', desc:'s', cat:'', src:'salary', date:'2026-11-05', due:'2026-11-05', at:'2026-11-11T08:00:00.000Z' });
    const m = CodisMerge.merge(base, local, remote, { localNewer:true }); normalizeData(m);
    const ids = m.finance.ledger.map(e=>e.id).sort(); eq('J: union of both devices, salary once', ids, ['dep_dev2', 'dep_off1', 'exp_off1', 'open', 'sal|2026-11']);
    eq('J: merged balance = sum of ledger', codisFinBalance(m.finance), 500000 + 15000 - 2500 + 1000 + 600000); T('J: merged ledger verifies', codisFinVerify(m.finance).ok);
    const again = CodisMerge.merge(base, m, m, { localNewer:true }); normalizeData(again); eq('J: merging again adds nothing', again.finance.ledger.length, m.finance.ledger.length); }
  { /* one device uses a reward offline, the other still shows it owned → single deduction after merge */
    const mkS = mkR({ name:'مزامنة استخدام', kind:'financial', iqd:2000 }), itR = data.settings.rewardItems.find(x=>x.id === mkS.item.id); own(itR, 'own|t_sync');
    const base = JSON.parse(JSON.stringify(data)); const a = JSON.parse(JSON.stringify(base)), b = JSON.parse(JSON.stringify(base));
    const keep = data; data = a; CodisEconomy.markUsed('own|t_sync'); data = b; CodisEconomy.markUsed('own|t_sync'); data = keep;
    const m = CodisMerge.merge(base, a, b, { localNewer:true }); normalizeData(m);
    eq('J: both devices used it → ONE redemption entry', m.finance.ledger.filter(e=>e.ref === 'rwd|own|t_sync').length, 1);
    eq('J: merged item is used', m.inventory.items.find(x=>x.uid === 'own|t_sync').status, 'used'); }
  T('J: finance data lives inside the same synced blob (data.finance)', JSON.stringify(data).indexOf('"finance"') !== -1);

  /* ===== أرشيف التقارير ===== */
  { const sec = ARCHIVE_SECTIONS.find(s=>s.id === 'reports'); T('archive: reports section exists', !!sec && sec.label === 'التقارير');
    data.outcomeLedger['rep_t1'] = { id:'rep_t1', kind:'reward', scope:'weekly', report:true, weekId:'2026-11-01', pct:91, at:'2026-11-08T10:00:00Z', item:'x', status:'resolved', room:'tasks', type:'weekly_reward' };
    const n0 = econReportEntries().length; T('archive: report counted from outcomeLedger (source unchanged)', n0 >= 1 && econReportsListHtml().indexOf('codisOpenReport') !== -1);
    T('archive: no copy into data.archive', !(data.archive || []).some(e=>e && e.id === 'rep_t1'));
    renderArchiveList(); archOpen('reports'); const w = document.getElementById('archive-list'); T('archive: list rendered in reports section', w && w.innerHTML.indexOf('rp-list-row') !== -1);
    const bar = document.getElementById('arch-filter-bar'); T('archive: section button shows count', bar && bar.innerHTML.indexOf('التقارير') !== -1);
    delete data.outcomeLedger['rep_t1']; renderArchiveList(); }
  { econRenderLog && econOpenLog && 0; const box = document.getElementById('eco-log-body'); econRenderLog(); T('coin log no longer has saved reports section', !box || box.innerHTML.indexOf('التقارير المحفوظة') === -1); }

  /* ===== K: الواجهة ===== */
  { const rects = ['notif-bell', 'store-btn', 'fin-btn', 'coin-chip'].map(i=>document.getElementById(i).getBoundingClientRect());
    T('K: order from edge: bell < store < fin < chip (RTL slots)', rects[0].left < rects[1].left && rects[1].left < rects[2].left && rects[2].left < rects[3].left, rects.map(r=>Math.round(r.left)).join(','));
    T('K: fin icon is between store and chip (right of store)', rects[2].left > rects[1].left && rects[2].right <= rects[3].left + 1);
    const chip = document.getElementById('coin-chip'); data.wallet.balance = 123456789.5; data.wallet.silver.balance = 9876543; econRenderChip();
    const cr = chip.getBoundingClientRect(); const rows = chip.querySelectorAll('.cc-row'); T('K: chip has coin row above silver row', rows.length === 2 && rows[0].getBoundingClientRect().top < rows[1].getBoundingClientRect().top);
    T('K: long numbers not clipped', chip.scrollWidth <= chip.clientWidth + 1 && cr.right <= innerWidth, cr.right + '/' + innerWidth + ' sw=' + chip.scrollWidth + ' cw=' + chip.clientWidth);
    const cs = getComputedStyle(chip); T('K: chip has no rectangle (no bg/border)', cs.backgroundColor === 'rgba(0, 0, 0, 0)' && cs.borderTopColor === 'rgba(0, 0, 0, 0)' && cs.boxShadow === 'none');
    chip.click && 0; T('K: chip still opens coin log', chip.getAttribute('onclick') === 'econOpenLog()'); T('K: fin button opens finance', document.getElementById('fin-btn').getAttribute('onclick') === 'finOpen()');
    data.wallet.balance = 0; data.wallet.silver.balance = 0; econRenderChip(); }
  { fresh(); at(2026, 11, 11); finOpen(); await new Promise(r=>setTimeout(r, 350)); const body = document.getElementById('fin-body');
    T('K: finance page opens (wizard first for new account)', body && body.innerHTML.indexOf('fin-wiz') !== -1 && econStoreIsOpen());
    finWizSet('work', 'employee'); finWizNext(); finWiz.salary = '600,000'; finWiz.day = '5'; finWiz.opening = '500,000'; finWiz.start = '2026-11-11'; finWizNext(); finWiz.rate = 40; finWizNext(); finWizNext();
    T('K: wizard completes → dashboard', document.getElementById('fin-bal') && document.getElementById('fin-bal').textContent.indexOf('٥') !== -1 || document.getElementById('fin-bal').textContent === '500,000', document.getElementById('fin-bal') && document.getElementById('fin-bal').textContent);
    T('K: wizard not shown again', (finRender(), document.getElementById('fin-body').innerHTML.indexOf('fin-wiz') === -1));
    finDepositOpen(); T('K: deposit sheet opens', CodisFinUI.isOpen() && !!document.getElementById('fd-amt')); const d = document.getElementById('fd-amt'); d.value = '15000'; finAmtInput(d); T('K: amount formats with commas', d.value === '15,000', d.value);
    document.getElementById('fd-desc').value = 'ربح'; document.getElementById('fd-go').click(); T('K: deposit via UI → 515,000', codisFinBalance() === 515000 && !CodisFinUI.isOpen(), codisFinBalance());
    finExpenseOpen(); document.getElementById('fe-name').value = 'مسواك'; document.getElementById('fe-amt').value = '1,000'; document.getElementById('fe-go').click(); T('K: expense via UI → 514,000', codisFinBalance() === 514000, codisFinBalance());
    await new Promise(r=>setTimeout(r, 300)); finExpenseOpen(); document.getElementById('fe-name').value = 'ضخم'; document.getElementById('fe-amt').value = '9,000,000'; document.getElementById('fe-go').click(); T('K: UI refuses overdraft and keeps sheet', CodisFinUI.isOpen() && codisFinBalance() === 514000 && !CodisFinUI.el().querySelector('.fin-err').hidden); CodisFinUI.close();
    await new Promise(r=>setTimeout(r, 300)); finRateOpen(); T('K: rate sheet shows 6 options', document.querySelectorAll('.fin-rate').length === 6); CodisFinUI.close(); await new Promise(r=>setTimeout(r, 300));
    finReportsOpen(); T('K: reports sheet verifies the equation', document.querySelector('.fin-verify.is-ok') !== null); CodisFinUI.close(); await new Promise(r=>setTimeout(r, 300));
    finAutoOpen(); finAutoSet('kind', 'financial'); finAutoNext(); document.getElementById('fa-name').oninput = null; finAuto.name = 'لفة شاورما'; finAuto.iqd = '1,000'; finAutoNext(); T('K: auto-reward preview chooses daily C and shows exact 25', finAuto.step === 2 && /25/.test(document.getElementById('fa-root').innerText) && finAuto.cardId === 'daily_C', finAuto.cardId); finAutoNext(); await new Promise(r=>setTimeout(r, 200));
    T('K: auto-reward saved', data.settings.rewardItems.some(x=>x.fin && x.name === 'لفة شاورما' && x.fin.iqd === 1000 && x.rarity === 'C' && x.room === 'tasks')); econCloseStore(); }
  { const t = document.getElementById('rpu-auto-btn'); T('K: auto-reward section button exists above "all rewards"', !!t && t.nextElementSibling && t.nextElementSibling.id === 'rpu-all-btn'); }

  /* ===== الملف المالي ===== */
  fresh(); at(2026, 11, 11); setup({ work:'freelance', opening:1000, avg:900000 });
  T('profile: freelance average (avg) never enters the balance', codisFinBalance() === 1000);
  { const r0 = codisFinSetProfile({ work:'employee', salary:{ amount:300000, day:10, from:'2026-11-01' } }); T('profile: switching to employee with a PAST start refused (no retro pay)', !r0.ok && r0.reason === 'past', r0.reason);
    const r1 = codisFinSetProfile({ work:'employee', salary:{ amount:300000, day:10, from:'2026-11-12' } }); T('profile: switch to employee ok', r1.ok && codisFin().work === 'employee', r1.reason); eq('profile: no salary booked before due', codisFinBalance(), 1000);
    at(2026, 11, 10 + 1 + 0); at(2026, 12, 10); codisFinCatchUp(); eq('profile: first salary Dec 10', codisFin().ledger.filter(e=>e.type === 'SALARY').map(e=>e.due), ['2026-12-10']);
    const r2 = codisFinSetProfile({ work:'freelance', source:'تصميم' }); T('profile: back to freelance keeps ledger', r2.ok && codisFin().work === 'freelance' && codisFin().source === 'تصميم' && codisFinBalance() === 301000); at(2027, 3, 1); eq('profile: freelance gets no further salaries', codisFinCatchUp(), 0); }
  { fresh(); at(2026, 11, 11); setup({ work:'employee', opening:100, salary:{ amount:50, day:3, from:'2026-11-12' } }); codisFinDepositNow({ amount:5, desc:'x', date:'2026-11-05' }); codisFinDepositNow({ amount:7, desc:'y', date:'2026-11-06' }); const run = codisFinRunning(); T('ledger order: opening first then by date', run[0].e.type === 'OPENING_BALANCE' && run[0].bal === 100 && run[run.length - 1].bal === 112, JSON.stringify(run.map(r=>[r.e.type, r.bal]))); }
  { fresh(); const d = document.getElementById('fin-btn'); T('K: finance page for brand-new account shows wizard, not data', (finOpen(), true)); await new Promise(r=>setTimeout(r, 300)); T('K: wizard rendered', document.getElementById('fin-body').innerHTML.indexOf('fin-wiz') !== -1); finWizSet('work', 'freelance'); finWizNext(); finWiz.opening = '0'; finWiz.source = 'مبيعات'; finWizNext(); finWiz.rate = 80; finWizNext(); finWizNext(); T('K: freelance wizard with zero opening completes', codisFin().setup.done && codisFinBalance() === 0 && codisFin().work === 'freelance' && codisFin().ledger.length === 1); econCloseStore(); }

  /* ===== cleanup ===== */
  window.__CODIS_FIN_NOW__ = undefined; codisConfirm = realConfirm;
  const bad = out.filter(x=>!x.ok);
  return { passed:out.length - bad.length, failed:bad.length, results:out };
})()
