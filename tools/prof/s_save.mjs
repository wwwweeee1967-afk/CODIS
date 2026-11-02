// Cost of saveData() as data grows (a heavy year-long user): stringify + localStorage write + IndexedDB mirror, and how often saves happen per action.
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  const r = await c.evaluate(`(()=>{ const out = [];
    const measure = label=>{ const t0 = performance.now(); for(let i = 0; i < 5; i++) saveData(); const ms = (performance.now() - t0) / 5; const sz = JSON.stringify(data).length; const parts = Object.keys(data).map(k=>[k, JSON.stringify(data[k] === undefined ? null : data[k]).length]).sort((a,b)=>b[1]-a[1]).slice(0, 6); out.push({ label, kb:Math.round(sz / 1024), saveMs:Math.round(ms * 10) / 10, top:parts.map(p=>p[0] + ':' + Math.round(p[1] / 1024) + 'k') }); };
    measure('fresh');
    const W = data.wallet; for(let i = 0; i < 3000; i++) W.transactions.push({ id:'tx_' + i, type:i % 2 ? 'EARN_REWARD_EXCHANGE' : 'PURCHASE_REWARD', amount:i % 2 ? 40 : -120, reason:'سبب المعاملة رقم ' + i, source:'store', referenceId:'ref|' + i, createdAt:new Date(Date.now() - i * 3600e3).toISOString() });
    measure('+3000 transactions');
    data.inventory = data.inventory || { items:[] }; for(let i = 0; i < 800; i++) data.inventory.items.push({ uid:'own|' + i, status:['owned','used','sold'][i % 3], name:'مكافأة ' + i, rarity:'A', rarityName:'نادرة', rarityTone:'a', rarityOrder:3, room:'weekly', price:300, acquiredAt:new Date().toISOString(), source:'store', stickerId:null });
    measure('+800 inventory');
    return out; })()`);
  console.log(JSON.stringify(r, null, 1));
  // how many saves per common action
  const n = await c.evaluate(`(()=>{ let k = 0; const o = saveData; window.saveData = function(){ k++; return o.apply(this, arguments); }; try{ navigateToPage('tasks'); }catch(e){} const a = k; try{ navigateToPage('habits'); }catch(e){} return { navTasks:a, navHabits:k - a }; })()`);
  console.log('saves per action', JSON.stringify(n));
}
