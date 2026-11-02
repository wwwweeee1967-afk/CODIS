// Trace of the SECOND store open (steady state): which rendering phase dominates, and per-section DOM size.
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(3000);
  await c.evaluate(`econOpenStore()`); await c.sleep(3000);
  console.log(JSON.stringify(await c.evaluate(`(()=>{ const b = document.getElementById('eco-store-body'); return Array.prototype.map.call(b.children, ch=>[ch.id || String(ch.className).slice(0, 30), ch.getElementsByTagName('*').length, getComputedStyle(ch).contentVisibility, Math.round(ch.getBoundingClientRect().top)]); })()`)));
  await c.evaluate(`CodisNav.back()`); await c.sleep(1500);
  const events = []; c.onMsg(m=>{ if(m.method === 'Tracing.dataCollected') events.push(...m.params.value); });
  await c.send('Tracing.start', { transferMode:'ReportEvents', traceConfig:{ includedCategories:['devtools.timeline', 'disabled-by-default-devtools.timeline', 'v8', 'blink.user_timing'] } });
  await c.evaluate(`econOpenStore()`); await c.sleep(3000);
  const done = new Promise(r=>c.onMsg(m=>{ if(m.method === 'Tracing.tracingComplete') r(); })); await c.send('Tracing.end'); await done;
  const sum = {}, cnt = {}; for(const e of events){ if(e.ph !== 'X' || !e.dur) continue; sum[e.name] = (sum[e.name] || 0) + e.dur; cnt[e.name] = (cnt[e.name] || 0) + 1; }
  console.log(JSON.stringify(Object.entries(sum).sort((a, b)=>b[1] - a[1]).slice(0, 25).map(([k, v])=>k + ' ' + Math.round(v / 1000) + '/' + cnt[k])));
  const big = events.filter(e=>e.ph === 'X' && e.dur > 40000 && ['UpdateLayoutTree', 'Layout', 'Paint', 'ParseHTML', 'MajorGC', 'MinorGC', 'V8.GC_MC_BACKGROUND_MARKING', 'Layerize'].includes(e.name)).map(e=>e.name + ' ' + Math.round(e.dur / 1000) + (e.args && e.args.elementCount ? ' els=' + e.args.elementCount : '') + (e.args && e.args.beginData && e.args.beginData.dirtyObjects ? ' dirty=' + e.args.beginData.dirtyObjects : ''));
  console.log(JSON.stringify(big));
}
