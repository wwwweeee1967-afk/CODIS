// Experiment: per-tile content-visibility in the cards section — layout cost of a store open with/without (env CVTILE=1).
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(3000);
  if(process.env.CVTILE) await c.evaluate(`(()=>{ const s = document.createElement('style'); s.textContent = '#eco-store-body [role="list"] > *{ content-visibility:auto; contain-intrinsic-size:auto 300px; }'; document.head.appendChild(s); return 1; })()`);
  await c.evaluate(`econOpenStore()`); await c.sleep(3000); await c.evaluate(`CodisNav.back()`); await c.sleep(1500);
  for(let run = 0; run < 2; run++){
    const events = []; const h = m=>{ if(m.method === 'Tracing.dataCollected') events.push(...m.params.value); }; c.onMsg(h);
    await c.send('Tracing.start', { transferMode:'ReportEvents', traceConfig:{ includedCategories:['devtools.timeline', 'disabled-by-default-devtools.timeline'] } });
    const t0 = Date.now(); await c.evaluate(`econOpenStore()`); const block = Date.now() - t0; await c.sleep(2500);
    const done = new Promise(r=>c.onMsg(m=>{ if(m.method === 'Tracing.tracingComplete') r(); })); await c.send('Tracing.end'); await done;
    const s = {}; for(const e of events){ if(e.ph === 'X' && e.dur && ['Layout', 'UpdateLayoutTree', 'Paint', 'FunctionCall', 'RunTask'].includes(e.name)) s[e.name] = (s[e.name] || 0) + e.dur; }
    console.log(JSON.stringify({ cv:!!process.env.CVTILE, run, blockMs:block, ms:Object.fromEntries(Object.entries(s).map(([k, v])=>[k, Math.round(v / 1000)])) }));
    await c.evaluate(`CodisNav.back()`); await c.sleep(1500);
  }
}
