// Store open: first open vs second open (same session), CPU attribution + wall time until the store is interactive.
async function prof(c, label, fn){
  await c.send('Profiler.enable'); await c.send('Profiler.setSamplingInterval', { interval:200 }); await c.send('Profiler.start');
  const t0 = Date.now(); await fn(); const wall = Date.now() - t0;
  const { profile } = await c.send('Profiler.stop');
  const byId = new Map(); profile.nodes.forEach(n=>byId.set(n.id, n));
  const parent = new Map(); profile.nodes.forEach(n=>(n.children || []).forEach(ch=>parent.set(ch, n.id)));
  const cnt = new Map(); profile.samples.forEach((id, i)=>cnt.set(id, (cnt.get(id) || 0) + (profile.timeDeltas[i] || 0)));
  const self = new Map(), incl = new Map();
  cnt.forEach((us, id)=>{ const n = byId.get(id); const k = (n.callFrame.functionName || '(anon)') + ':' + (n.callFrame.lineNumber + 1); self.set(k, (self.get(k) || 0) + us);
    const seen = new Set(); let p = id; while(p){ const q = byId.get(p); const kk = (q.callFrame.functionName || '(anon)') + ':' + (q.callFrame.lineNumber + 1); if(!seen.has(kk)){ seen.add(kk); incl.set(kk, (incl.get(kk) || 0) + us); } p = parent.get(p); } });
  const top = (m, n)=>[...m.entries()].sort((a, b)=>b[1] - a[1]).slice(0, n).map(([k, v])=>k + ' ' + Math.round(v / 1000));
  console.log(JSON.stringify({ label, wall, self:top(self, 16), incl:top(incl, 26) }));
}
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(3000);
  await prof(c, 'store open #1', async()=>{ await c.evaluate(`econOpenStore()`); await c.sleep(3000); });
  await c.evaluate(`(typeof econCloseLayer === 'function') ? econCloseLayer('eco-store') : (CodisNav && CodisNav.back && CodisNav.back())`); await c.sleep(1500);
  await prof(c, 'store open #2', async()=>{ await c.evaluate(`econOpenStore()`); await c.sleep(3000); });
}
