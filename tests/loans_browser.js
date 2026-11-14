/* CODIS-V45 (3.32.0) — «سلفني»: اختبار تكامل داخل المتصفح (محرك المحفظة + دفتر القروض + الدمج). Returns { passed, failed, results[] }.
   Run: TEST=tests/loans_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   أو يدوياً: (0,eval)(await (await fetch('/tests/loans_browser.js')).text()) داخل الصفحة. يعدّل بيانات ملف الاختبار المحلي فقط. */
window.__loanRes = null;
(async function(){
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : String(info) });
  const eq = (name, a, b)=>T(name, JSON.stringify(a) === JSON.stringify(b), JSON.stringify(a) + ' vs ' + JSON.stringify(b));
  const snapData = JSON.stringify(data);
  const W = ()=>data.wallet, bal = ()=>CodisWallet.balance(), debt = ()=>CodisLoans.debt();
  /* حالة نظيفة */
  data.wallet.balance = 0; data.wallet.lifetimeEarned = 0; data.wallet.lifetimeSpent = 0; data.wallet.transactions = []; data.loans = { v:1, events:[] };
  const silverBefore = JSON.stringify(data.wallet.silver), finBefore = JSON.stringify(data.finance || null);
  let n = 0; const earn = (amt, type)=>CodisWallet.transact([], ()=>{ const tx = CodisWallet.apply(type || 'EARN_REWARD_EXCHANGE', amt, 'اختبار', 'test', 'ref_' + (++n) + '_' + Math.random()); return tx ? { ok:true, tx } : { ok:false, reason:'tx' }; });
  const borrow = (a, rid)=>CodisLoans.borrow(a, rid);

  /* --- الاقتراض --- */
  let r = borrow(200, 'a1'); T('borrow 200 ok', r.ok); eq('balance 200', bal(), 200); eq('debt 200', debt(), 200);
  eq('lifetimeEarned not raised by loan', W().lifetimeEarned, 0);
  eq('tx type LOAN_BORROW', W().transactions[W().transactions.length - 1].type, 'LOAN_BORROW');
  r = borrow(300, 'a2'); T('borrow 300 more rejected (cap)', !r.ok && r.reason === 'cap', JSON.stringify(r)); eq('debt still 200', debt(), 200); eq('balance still 200', bal(), 200);
  r = borrow(200, 'a3'); T('borrow 200 more ok → debt 400', r.ok); eq('debt 400', debt(), 400); eq('room 0', CodisLoans.room(), 0);
  r = borrow(1, 'a4'); T('borrow at cap rejected', !r.ok && r.reason === 'maxed', JSON.stringify(r)); eq('debt 400 unchanged', debt(), 400);
  r = borrow(1.5, 'a5'); T('fractional amount rejected', !r.ok && r.reason === 'amount'); r = borrow(0, 'a6'); T('zero rejected', !r.ok); r = borrow(-5, 'a7'); T('negative rejected', !r.ok);
  eq('state maxed', CodisLoans.state(), 'maxed'); eq('balance 400 total borrowed', bal(), 400);

  /* --- الاستقطاع التلقائي --- */
  const before = bal(); r = earn(100); T('earn 100 ok', r.ok);
  eq('debt 300 after earning 100', debt(), 300); eq('balance unchanged (100 went to debt)', bal(), before);
  eq('lifetimeEarned = 100 (earned counted, loan not)', W().lifetimeEarned, 100);
  const incoming = W().transactions.filter(t=>t.type === 'EARN_REWARD_EXCHANGE').pop(), rep = W().transactions.filter(t=>t.type === 'LOAN_REPAY').pop();
  eq('incoming tx marked debtPaid 100', incoming.meta && incoming.meta.debtPaid, 100); eq('repay tx −100', rep.amount, -100); eq('repay ref points to incoming', rep.meta.from, incoming.id);
  r = earn(500); eq('earn 500 with debt 300 → debt 0', debt(), 0); eq('balance +200 only', bal(), before + 200); eq('state clear', CodisLoans.state(), 'clear');
  const b2 = bal(); earn(50); eq('earn with no debt: full 50 added', bal(), b2 + 50); T('no repay tx created when no debt', W().transactions[W().transactions.length - 1].type === 'EARN_REWARD_EXCHANGE');
  eq('room back to 400', CodisLoans.room(), 400);
  /* سلفة 300 ثم سداد 100 → المتاح 200 (المثال) */
  borrow(300, 'b1'); eq('debt 300', debt(), 300); eq('room 100', CodisLoans.room(), 100); earn(100); eq('debt 200 after repaying 100', debt(), 200); eq('room 200', CodisLoans.room(), 200);
  /* السداد لا يسحب من الرصيد القديم */
  const b3 = bal(); earn(30); eq('old balance untouched: balance unchanged, debt 170', [bal(), debt()], [b3, 170]);
  /* المصادر الأخرى */
  const b4 = bal(); earn(20, 'SELL_REWARD'); eq('SELL_REWARD repays too', [debt(), bal()], [150, b4]);
  earn(10, 'HABIT_COMPENSATION'); eq('HABIT_COMPENSATION repays', debt(), 140);
  earn(5, 'ADMIN_ADJUSTMENT'); eq('ADMIN_ADJUSTMENT (grant) repays', debt(), 135);
  const b5 = bal(); CodisWallet.adjust(40, 'dev tweak'); eq('manual dev adjust (noRepay) goes fully to balance', [debt(), bal()], [135, b5 + 40]);
  /* خصم/مصروف لا يسدّد */
  const b6 = bal(); CodisWallet.transact([], ()=>{ const t = CodisWallet.apply('PURCHASE_BOX', -10, 'شراء', 'store', 'pb_' + Math.random()); return { ok:!!t }; }); eq('spending does not touch debt', [debt(), bal()], [135, b6 - 10]);
  /* تكرار المعاملة نفسها لا يكرر الكسب ولا السداد */
  const ref = 'dupref_1', dd = debt();
  CodisWallet.transact([], ()=>({ ok:!!CodisWallet.apply('EARN_REWARD_EXCHANGE', 7, 'x', 's', ref) })); const dAfter = debt(), bAfter = bal();
  CodisWallet.transact([], ()=>({ ok:!!CodisWallet.apply('EARN_REWARD_EXCHANGE', 7, 'x', 's', ref) }));
  eq('re-sending same reward ref: no double repay / earn', [debt(), bal()], [dAfter, bAfter]); eq('first send repaid 7', dAfter, dd - 7);
  /* مكافأة عنصر (لا كوينز) → لا استقطاع */
  const dItem = debt(); const inv0 = data.inventory.items.length; CodisWallet.transact([], ()=>{ CodisInventory.grant({ uid:'own|loanTest', name:'عنصر', rarity:'C', coinValue:50 }); return { ok:true }; });
  eq('taking the item instead of coins: debt unchanged', debt(), dItem); T('item granted', data.inventory.items.length === inv0 + 1);
  /* تكرار الضغط (نفس requestId) */
  const dBorrow = debt(), bBorrow = bal(); const room0 = CodisLoans.room();
  const x1 = borrow(50, 'dup1'), x2 = borrow(50, 'dup1'); T('same requestId twice → only one loan', x1.ok && !x2.ok && x2.reason === 'dup', JSON.stringify(x2)); eq('only +50 debt', debt(), dBorrow + 50); eq('only +50 balance', bal(), bBorrow + 50);

  /* --- ذرّية: فشل الحفظ يُرجع كل شيء --- */
  const dBefore = debt(), balBefore = bal(), evBefore = CodisLoans.events().length, txBefore = W().transactions.length;
  let rolled = null;
  try{
    const __sd = window.saveData; window.saveData = function(){ return false; };
    rolled = borrow(10, 'failsave');
    window.saveData = __sd;
  }catch(e){ try{ window.saveData = __sd; }catch(_){} T('save-fail test harness', false, e.message); }
  if(rolled){ T('failed save → borrow reports failure', !rolled.ok && rolled.reason === 'save', JSON.stringify(rolled)); eq('rollback: debt/balance/events/tx unchanged', [debt(), bal(), CodisLoans.events().length, W().transactions.length], [dBefore, balBefore, evBefore, txBefore]); }
  /* فشل أثناء الاستقطاع (استثناء) يُرجع الإضافة والسداد معاً */
  const origRepay = CodisLoans.repayFrom; const d9 = debt(), b9 = bal(), e9 = CodisLoans.events().length;
  const __sd2 = window.saveData; window.saveData = function(){ return false; };
  const rf = earn(25); window.saveData = __sd2;
  T('earn with failed save → rolled back (no earn, no repay)', !rf.ok && debt() === d9 && bal() === b9 && CodisLoans.events().length === e9, JSON.stringify([rf, debt(), bal()]));

  /* --- سلامة الدفتر وإعادة البناء --- */
  const v = CodisLoans.verify(); T('verify ok', v.ok, v.problems.join(' | ')); eq('debt = borrowed − repaid', debt(), Math.max(0, v.borrowed - v.repaid));
  T('debt never exceeds cap', debt() <= 400);
  /* بقاء الدين بعد إعادة التحميل: تطبيع + إعادة قراءة */
  const keep = debt(), evs = JSON.stringify(CodisLoans.events()); const copy = JSON.parse(JSON.stringify(data)); econNormalizeAll(copy); eq('normalize keeps loan events', JSON.stringify(copy.loans.events), evs);
  /* تقليم سجل المحفظة لا يمس الدين */
  const pruned = JSON.parse(JSON.stringify(data)); pruned.wallet.transactions = pruned.wallet.transactions.slice(-3); econNormalizeAll(pruned);
  eq('wallet tx pruning does not change debt events', JSON.stringify(pruned.loans.events), evs);
  /* بيانات مشوّهة لا ترمي */
  [null, 5, 'x', [], {}, { events:'x' }, { events:[null, 3, { id:'a' }, { id:'b', kind:'borrow', amount:'zz' }, { id:'c', kind:'borrow', amount:5 }, { id:'c', kind:'borrow', amount:6 }] }].forEach((bad, i)=>{
    let o, thr = false; try{ o = codisLoansNorm(bad); }catch(e){ thr = true; } T('codisLoansNorm odd #' + i + ' safe', !thr && o && Array.isArray(o.events)); if(i === 6) eq('odd data keeps only valid unique event', o.events.map(e=>e.id), ['c']);
  });
  /* --- الدمج بين جهازين --- */
  const base = JSON.parse(JSON.stringify(data)); const A = JSON.parse(JSON.stringify(base)), B = JSON.parse(JSON.stringify(base));
  const mkEv = (id, kind, amount)=>({ id, kind, amount, at:new Date().toISOString(), ref:id });
  A.loans.events.push(mkEv('ln_devA', 'borrow', 100)); A.wallet.transactions.push({ id:'txA', type:'LOAN_BORROW', amount:100, reason:'s', source:'loan', referenceId:'borrow|devA', createdAt:new Date().toISOString() }); A.wallet.balance += 100;
  B.loans.events.push(mkEv('rp|devB', 'repay', 5)); B.wallet.transactions.push({ id:'txB', type:'LOAN_REPAY', amount:-5, reason:'s', source:'loan', referenceId:'repay|devB', createdAt:new Date().toISOString() }); B.wallet.balance -= 5; B.wallet.lifetimeSpent += 5;
  const M = CodisMerge.merge(base, A, B, { localNewer:true }); const ids = M.loans.events.map(e=>e.id);
  T('merge unions both devices’ loan events', ids.includes('ln_devA') && ids.includes('rp|devB'));
  eq('merge: no duplicate events', ids.length, new Set(ids).size);
  eq('merge: balance = base +100 −5', M.wallet.balance, base.wallet.balance + 95);
  eq('merge: lifetimeEarned not raised by borrow', M.wallet.lifetimeEarned, base.wallet.lifetimeEarned);
  const M2 = CodisMerge.merge(M, M, M, {}); eq('merge idempotent (same sides)', M2.loans.events.length, M.loans.events.length);
  /* دين سُدِّد بالكامل على جهاز لا يُحيا من جهاز قديم */
  const full = JSON.parse(JSON.stringify(base)); full.loans.events = [mkEv('ln_x', 'borrow', 50), mkEv('rp|x', 'repay', 50)];
  const old = JSON.parse(JSON.stringify(base)); old.loans.events = [mkEv('ln_x', 'borrow', 50)];
  const M3 = CodisMerge.merge(old, old, full, {}); const debtOf = d=>Math.max(0, d.loans.events.reduce((a, e)=>a + (e.kind === 'borrow' ? e.amount : -e.amount), 0)); eq('merge: paid debt not resurrected by stale device', debtOf(M3), 0);
  const M4 = CodisMerge.merge(old, full, old, {}); eq('merge (reverse sides): still 0', debtOf(M4), 0);

  /* --- الفضة والمالية بالدينار لا تتأثران --- */
  eq('silver wallet untouched', JSON.stringify(data.wallet.silver), silverBefore); eq('IQD finance untouched', JSON.stringify(data.finance || null), finBefore);
  T('limits: admin cap registered', CodisLimits.constants().some(c=>c.id === 'loan.cap'));
  T('LOAN types accepted by wallet', econTxTypes().includes('LOAN_BORROW') && econTxTypes().includes('LOAN_REPAY'));

  /* --- الواجهة --- */
  try{
    const wasLog = document.getElementById('eco-log-body'); econRenderLog(); const html = document.getElementById('eco-log-body').innerHTML;
    T('log shows سلفني card', html.includes('ln-card') && html.includes('سلفني')); T('log marks loan rows', html.includes('is-loan') && html.includes('سداد تلقائي'));
    codisLoanOpen(); await new Promise(r=>setTimeout(r, 400)); const sh = document.querySelector('.ln-ov');
    T('سلفني sheet opens with limit/debt/room', !!sh && sh.textContent.includes('الحد الأعلى') && sh.textContent.includes('المتبقي للاقتراض') && sh.textContent.includes('سجل السلف'));
    const inp = sh && sh.querySelector('#ln-amt'), go = sh && sh.querySelector('#ln-go');
    if(inp && go){ const room = CodisLoans.room(), d0 = debt(); inp.value = String(room + 1); inp.dispatchEvent(new Event('input')); go.click(); T('UI: over-limit refused with message', debt() === d0 && !sh.querySelector('.fin-err').hidden); inp.value = '1'; inp.dispatchEvent(new Event('input')); go.click(); T('UI: valid borrow works', debt() === d0 + 1); }
    CodisFinUI.closeTop();
  }catch(e){ T('ui exercise', false, e.message); }

  /* استعادة */
  try{ data.wallet = JSON.parse(JSON.stringify(JSON.parse(snapData).wallet)); data.loans = JSON.parse(snapData).loans; data.inventory = JSON.parse(snapData).inventory; saveData(); }catch(e){}
  const failed = out.filter(x=>!x.ok);
  return (window.__loanRes = { passed:out.length - failed.length, failed:failed.length, failedList:failed, results:out.length });
})();
