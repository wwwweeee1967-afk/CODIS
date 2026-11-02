// CPU attribution per interaction (sampling profiler; a function's self time includes forced style/layout it triggered).
import { writeFileSync } from 'node:fs';
async function prof(c, label, fn){
  await c.send('Profiler.enable'); await c.send('Profiler.setSamplingInterval', { interval:200 }); await c.send('Profiler.start');
  await fn();
  const { profile } = await c.send('Profiler.stop');
  const self = new Map(), byId = new Map(); profile.nodes.forEach(n=>byId.set(n.id, n));
  const dt = profile.timeDeltas; const cnt = new Map();
  profile.samples.forEach((id, i)=>cnt.set(id, (cnt.get(id) || 0) + (dt[i] || 0)));
  // inclusive time per function (walk parents)
  const parent = new Map(); profile.nodes.forEach(n=>(n.children || []).forEach(ch=>parent.set(ch, n.id)));
  const incl = new Map();
  cnt.forEach((us, id)=>{ const n = byId.get(id); const k = n.callFrame.functionName + ':' + (n.callFrame.lineNumber + 1); self.set(k, (self.get(k) || 0) + us);
    const seen = new Set(); let p = id; while(p){ const q = byId.get(p); const kk = (q.callFrame.functionName || '(anon)') + ':' + (q.callFrame.lineNumber + 1); if(!seen.has(kk)){ seen.add(kk); incl.set(kk, (incl.get(kk) || 0) + us); } p = parent.get(p); } });
  const top = (m, n)=>[...m.entries()].sort((a, b)=>b[1] - a[1]).slice(0, n).map(([k, v])=>k + ' ' + Math.round(v / 1000) + 'ms');
  const out = { label, self:top(self, 22), inclusive:top(incl, 30) };
  console.log(JSON.stringify(out, null, 1));
  return out;
}
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:['ساعة سوشل ميديا','تطلب أكل تحبه','سفرة ثلاثة أيام للمنتجع الكبير','فلم بالسينما','The','1'][i % 6] + ' ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  const all = [];
  all.push(await prof(c, 'store open', async()=>{ await c.evaluate(`econOpenStore()`); await c.sleep(2500); }));
  all.push(await prof(c, 'store scroll', async()=>{ for(let i = 0; i < 4; i++){ await c.swipe(200, 700, 200, 14); await c.sleep(250); } await c.sleep(500); }));
  all.push(await prof(c, 'peek', async()=>{ await c.press('#eco-store-body .shop-card[data-id]', 700); await c.sleep(1200); await c.evaluate(`CodisCardPeek.close()`); await c.sleep(900); }));
  all.push(await prof(c, 'purchase+cinema+close', async()=>{ await c.evaluate(`(()=>{ window.codisConfirm = async()=>true; let best = null; data.settings.rewardItems.forEach(i=>{ if(i.enabled){ const p = CodisEconomy.storePrice(i); if(!best || p > best.p) best = { id:i.id, p }; } }); econBuy(best.id); return 1; })()`); await c.sleep(4500); await c.evaluate(`document.querySelector('.bcx-keep') && document.querySelector('.bcx-keep').click()`); await c.sleep(1800); }));
  writeFileSync('C:/tmp/cx/cpu_312.json', JSON.stringify(all, null, 1));
}
