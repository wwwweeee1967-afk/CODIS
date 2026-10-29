/* CODIS-BOXES-V4 — probability model test (evaluate in the page; fresh origin, guest). Statistical + edge cases + single-source checks.
   Returns {passed, failed, results, table}. Sampling uses the REAL CodisBoxes.roll (no reimplementation). */
(async function(){
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i });
  const M = CodisBoxes.model, sellK = econCfg().sellPercent / 100, table = [];
  const tiers = CodisBoxes.tiers();
  /* ---- structure + economics per tier ---- */
  let prevRho = 0, prevEvShare = 0;
  tiers.forEach((t, ti)=>{
    const rows = CodisBoxes.effective(t), pm = rows.map(r=>r.pm), st = CodisBoxes.stats(t);
    T(t.id + ': probabilities sum to exactly 1000‰', pm.reduce((a,b)=>a + b, 0) === 1000);
    T(t.id + ': every class >= floor, integers, no negatives', pm.every(x=>Number.isInteger(x) && x >= M.FLOOR_PM));
    T(t.id + ': lowest class <= 90%', pm[0] <= 900, pm[0]);
    const ratio = st.ev * sellK / t.price;
    T(t.id + ': sell-back EV/price < 1 (no guaranteed profit)', ratio < 1, ratio.toFixed(3));
    T(t.id + ': sell-back ratio matches design rho', Math.abs(ratio - M.RHO[t.id]) < 0.03, ratio.toFixed(3) + ' vs ' + M.RHO[t.id]);
    T(t.id + ': value-per-coin grows with tier', ratio > prevRho, ratio.toFixed(3)); prevRho = ratio;
    const dud = rows.filter(r=>r.mean < M.DUD_RATIO * t.price).reduce((s,r)=>s + r.pm, 0) / 1000;
    T(t.id + ': dud share within cap', dud <= M.DUD_CAP[t.id] + 0.012, dud.toFixed(3) + ' <= ' + M.DUD_CAP[t.id]);
    const hi = rows.reduce((s,r)=>s + r.pm / 1000 * r.vals.filter(v=>v >= 700).length / r.n, 0);
    table.push({ id:t.id, price:t.price, classes:rows.map(r=>r.name + ' ' + (r.pm / 10).toFixed(1) + '%'), ev:+st.ev.toFixed(1), sellRatio:+ratio.toFixed(3), pHi700:+hi.toFixed(4), duds:+dud.toFixed(3) });
  });
  const hiSeq = table.map(r=>r.pHi700); T('chance of a >=700-coin prize never decreases up the ladder', hiSeq.every((x,i)=>i === 0 || x >= hiSeq[i - 1] - 1e-9), hiSeq.join(','));
  T('every prize is obtainable from at least one box (none excluded everywhere)', (()=>{ const seen = new Set(); tiers.forEach(t=>CodisBoxes.effective(t).forEach(r=>r.items.forEach(x=>seen.add(x.id)))); return CodisBoxes.classes(0).reduce((a,c)=>a + c.items.length, 0) === seen.size; })());

  /* ---- displayed == actual: roll() must pick with exactly the displayed pm, then uniform inside the class ---- */
  const origPick = CodisRewardEngine.pick; let spied = null;
  CodisRewardEngine.pick = function(rows, w){ if(rows && rows[0] && rows[0].pm !== undefined && w && w(rows[0]) === rows[0].pm && !spied) spied = rows.map(r=>[r.id, w(r)]); return origPick.apply(this, arguments); };
  const t3 = tiers[2]; CodisBoxes.roll(t3); CodisRewardEngine.pick = origPick;
  T('roll() draws with the displayed per-mille weights (single source)', spied && JSON.stringify(spied) === JSON.stringify(CodisBoxes.effective(t3).map(r=>[r.id, r.pm])));

  /* ---- large-sample comparison against displayed odds (real roll) ---- */
  const N = 40000;
  for(const t of tiers){
    const rows = CodisBoxes.effective(t), cnt = {}, per = {};
    for(let i = 0; i < N; i++){ const r = CodisBoxes.roll(t); const c = r.cls.id; cnt[c] = (cnt[c] || 0) + 1; per[r.item.id] = (per[r.item.id] || 0) + 1; }
    let chi = 0; rows.forEach(r=>{ const e = N * r.pm / 1000; chi += Math.pow((cnt[r.id] || 0) - e, 2) / e; });
    const crit = [0, 0, 13.8, 16.3, 18.5, 20.5, 22.5, 24.3, 26.1, 27.9, 29.6, 31.3][rows.length] || 40;   /* chi-square p=0.001, df=n-1 */
    T(t.id + ': class frequencies match displayed odds (chi2 ' + chi.toFixed(1) + ' < ' + crit + ')', chi < crit);
    let ok = true; rows.forEach(r=>{ r.items.forEach(x=>{ const e = N * r.pm / 1000 / r.n, o = per[x.id] || 0; if(e >= 20 && Math.abs(o - e) > 5 * Math.sqrt(e)) ok = false; }); });
    T(t.id + ': prizes inside a class are equally likely', ok);
    let sample = 0, v = 0; for(let i = 0; i < 20000; i++){ v += CodisBoxes.valueOf(CodisBoxes.roll(t).item); sample++; }
    const emp = v / sample, st = CodisBoxes.stats(t); T(t.id + ': empirical mean prize ~ stats().ev (' + emp.toFixed(1) + ' vs ' + st.ev.toFixed(1) + ')', Math.abs(emp - st.ev) / st.ev < 0.12);
  }

  /* ---- solver edge cases (synthetic pools) ---- */
  const mk = vals=>vals.map((m,i)=>({ mean:m, n:1, vals:[m] }));
  T('single eligible class = 100%', JSON.stringify(M.solve(mk([50]), 100, 80, .5)) === '[1000]');
  const two = M.solve(mk([20, 400]), 100, 150, .5); T('two classes: sums 1000, both >0', two.reduce((a,b)=>a + b, 0) === 1000 && two.every(x=>x >= 1), two.join(','));
  let bad = 0, n = 0; for(let k = 0; k < 4000; k++){ const c = 1 + Math.floor(Math.random() * 7), vs = Array.from({ length:c }, ()=>Math.round(5 + Math.random() * 6000)).sort((a,b)=>a - b), price = 20 + Math.random() * 400, tgt = Math.random() * price * 1.3, cap = Math.random();
    const p = M.solve(mk(vs), price, tgt, cap); n++; if(p.length !== c || p.reduce((a,b)=>a + b, 0) !== 1000 || p.some(x=>!Number.isInteger(x) || x < 1)) bad++; }
  T('random pools (4000): always valid distribution (sum 1000, ints, no negative)', bad === 0, bad + '/' + n);
  T('toPm: tiny/odd inputs stay valid', [[333.3, 333.3, 333.4], [999.99, 0.005, 0.005], [250, 250, 250, 250]].every(a=>{ const p = M.toPm(a); return p.reduce((x,y)=>x + y, 0) === 1000 && p.every(x=>x >= 1); }));

  /* ---- pool-level edge cases using the real data ---- */
  const saved = JSON.stringify(data.settings.rewardItems);
  data.settings.rewardItems.forEach(x=>{ x.enabled = false; });
  T('no eligible rewards: boxes unavailable (empty), buy refused', tiers.every(t=>CodisBoxes.effective(t).length === 0) && CodisBoxes.buy('bx1').reason === 'empty');
  data.settings.rewardItems = JSON.parse(saved); data.settings.rewardItems.forEach((x,i)=>{ x.enabled = i === 0; });
  const one = CodisBoxes.effective(tiers[4]); T('one eligible reward: top box still valid (sum 1000, rolls it)', one.length >= 1 && one.reduce((s,r)=>s + r.pm, 0) === 1000 && !!CodisBoxes.roll(tiers[4]));
  data.settings.rewardItems = JSON.parse(saved);
  T('pool restored', JSON.stringify(data.settings.rewardItems) === saved);

  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed, table:table };
})();
