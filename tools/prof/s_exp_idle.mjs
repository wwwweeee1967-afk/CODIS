// Experiment: cost of the store while idle — baseline vs offscreen animations paused vs all paused vs no backdrop.
async function trace(c, label, fn){
  const events = []; c.onMsg(m=>{ if(m.method === 'Tracing.dataCollected') events.push(...m.params.value); });
  await c.send('Tracing.start', { transferMode:'ReportEvents', traceConfig:{ includedCategories:['devtools.timeline', 'disabled-by-default-devtools.timeline', 'cc'] } });
  await fn();
  const done = new Promise(r=>c.onMsg(m=>{ if(m.method === 'Tracing.tracingComplete') r(); })); await c.send('Tracing.end'); await done;
  const sum = {}, cnt = {}; for(const e of events){ if(e.ph !== 'X' || !e.dur) continue; sum[e.name] = (sum[e.name] || 0) + e.dur; cnt[e.name] = (cnt[e.name] || 0) + 1; }
  const k = ['UpdateLayoutTree', 'Layout', 'PrePaint', 'Paint', 'Layerize', 'UpdateLayer', 'FunctionCall'];
  console.log(JSON.stringify({ label, ms:Object.fromEntries(k.filter(x=>sum[x]).map(x=>[x, Math.round(sum[x] / 1000) + '/' + cnt[x]])) }));
}
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  await c.evaluate(`econOpenStore()`); await c.sleep(3500);
  await trace(c, 'A store idle baseline', ()=>c.sleep(3000));
  await c.evaluate(`(()=>{ const vh = innerHeight; let n = 0; document.getAnimations().forEach(a=>{ const t = a.effect && a.effect.target; if(!t) return; const r = t.getBoundingClientRect(); if(!(r.bottom > 0 && r.top < vh)){ a.pause(); n++; } }); return n; })()`);
  await trace(c, 'B offscreen animations paused', ()=>c.sleep(3000));
  await c.evaluate(`document.getAnimations().forEach(a=>a.pause())`);
  await trace(c, 'C all animations paused', ()=>c.sleep(3000));
  await c.evaluate(`(()=>{ const s = document.createElement('style'); s.textContent = '*{ -webkit-backdrop-filter:none; backdrop-filter:none; }'; document.head.appendChild(s); return 1; })()`);
  await trace(c, 'D + no backdrop', ()=>c.sleep(3000));
  await c.evaluate(`document.getAnimations().forEach(a=>a.play())`);
  await trace(c, 'E animations on, no backdrop', ()=>c.sleep(3000));
}
