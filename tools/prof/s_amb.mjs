// Ambient cache: values identical across sessions, and the second session does no canvas decode work (make) at store open.
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly','master']; for(let i = 0; i < 24; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:['C','B','A','S','SS'][i % 5], room:rooms[i % 4], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' }); data.wallet.balance = 800000; saveData(); return 1; })()`);
  const grab = `(async()=>{ const sc = econStoreScroller(); for(let y = 0; y < sc.scrollHeight; y += 300){ sc.scrollTop = y; await new Promise(r=>setTimeout(r, 100)); } await new Promise(r=>setTimeout(r, 2500));
    return Array.prototype.map.call(document.querySelectorAll('#eco-store-body .rwc, #eco-store-body .scx-hc-art'), f=>f.style.getPropertyValue('--amb')).filter(Boolean).map(v=>v.length + ':' + v.slice(-40)).sort(); })()`;
  const runs = [];
  for(let s = 0; s < 2; s++){
    await c.load(); await c.sleep(2500);
    await c.send('Profiler.enable'); await c.send('Profiler.start');
    await c.evaluate(`econOpenStore()`);
    const v = await c.evaluate(grab);
    const { profile } = await c.send('Profiler.stop');
    let makeUs = 0; const ids = new Set(profile.nodes.filter(n=>n.callFrame.functionName === 'make').map(n=>n.id));
    profile.samples.forEach((id, i)=>{ if(ids.has(id)) makeUs += profile.timeDeltas[i] || 0; });
    runs.push(v); console.log('session', s + 1, 'amb values', v.length, 'make self ms', Math.round(makeUs / 1000), 'stored', await c.evaluate(`(localStorage.getItem('codis_amb_v1') || '').length`));
  }
  console.log('identical across sessions:', JSON.stringify(runs[0]) === JSON.stringify(runs[1]));
}
