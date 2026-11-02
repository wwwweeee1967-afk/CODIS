// Rendering breakdown (style / layout / paint / raster / decode / composite) per interaction via Tracing.
import { writeFileSync } from 'node:fs';
async function trace(c, label, fn){
  const events = [];
  const h = m=>{ if(m.method === 'Tracing.dataCollected') events.push(...m.params.value); };
  c.__on ? 0 : 0;
  c.onMsg(h);
  await c.send('Tracing.start', { transferMode:'ReportEvents', traceConfig:{ includedCategories:['devtools.timeline', 'disabled-by-default-devtools.timeline', 'blink', 'cc', 'gpu', 'v8.execute'] } });
  await fn();
  const done = new Promise(r=>c.onMsg(m=>{ if(m.method === 'Tracing.tracingComplete') r(); }));
  await c.send('Tracing.end'); await done;
  const sum = {}, cnt = {}, big = [];
  for(const e of events){ if(e.ph !== 'X' || !e.dur) continue; const n = e.name; sum[n] = (sum[n] || 0) + e.dur; cnt[n] = (cnt[n] || 0) + 1;
    if(['Paint', 'RasterTask', 'Layout', 'UpdateLayoutTree', 'Decode Image', 'ImageDecodeTask', 'PrePaint', 'Layerize', 'CompositeLayers'].includes(n) && e.dur > 30000) big.push(n + ' ' + Math.round(e.dur / 1000) + 'ms' + (e.args && e.args.data && e.args.data.elementCount ? ' els=' + e.args.data.elementCount : '')); }
  const keys = ['UpdateLayoutTree', 'Layout', 'PrePaint', 'Paint', 'PaintImage', 'RasterTask', 'ImageDecodeTask', 'Decode Image', 'Layerize', 'CompositeLayers', 'UpdateLayer', 'FunctionCall', 'EvaluateScript', 'TimerFire', 'EventDispatch', 'GPUTask', 'ScrollLayer', 'HitTest', 'ParseHTML'];
  const out = { label, ms:Object.fromEntries(keys.filter(k=>sum[k]).map(k=>[k, Math.round(sum[k] / 1000) + 'ms/' + cnt[k]])), big:big.slice(0, 15) };
  console.log(JSON.stringify(out));
  return out;
}
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:['ساعة سوشل ميديا','تطلب أكل تحبه','سفرة ثلاثة أيام للمنتجع الكبير','فلم بالسينما','The','1'][i % 6] + ' ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  const all = [];
  all.push(await trace(c, 'boot (returning)', async()=>{ await c.load(); await c.sleep(3000); }));
  all.push(await trace(c, 'home idle 3s', async()=>{ await c.sleep(3000); }));
  all.push(await trace(c, 'store open', async()=>{ await c.evaluate(`econOpenStore()`); await c.sleep(2500); }));
  all.push(await trace(c, 'store scroll', async()=>{ for(let i = 0; i < 4; i++){ await c.swipe(200, 700, 200, 14); await c.sleep(250); } await c.sleep(500); }));
  all.push(await trace(c, 'store idle 3s', async()=>{ await c.sleep(3000); }));
  all.push(await trace(c, 'peek', async()=>{ await c.press('#eco-store-body .shop-card[data-id]', 700); await c.sleep(1200); await c.evaluate(`CodisCardPeek.close()`); await c.sleep(900); }));
  all.push(await trace(c, 'cinema', async()=>{ await c.evaluate(`(()=>{ window.codisConfirm = async()=>true; let best = null; data.settings.rewardItems.forEach(i=>{ if(i.enabled){ const p = CodisEconomy.storePrice(i); if(!best || p > best.p) best = { id:i.id, p }; } }); econBuy(best.id); return 1; })()`); await c.sleep(4500); }));
  all.push(await trace(c, 'cinema close', async()=>{ await c.evaluate(`document.querySelector('.bcx-keep') && document.querySelector('.bcx-keep').click()`); await c.sleep(2000); }));
  writeFileSync('C:/tmp/cx/trace_312.json', JSON.stringify(all, null, 1));
}
