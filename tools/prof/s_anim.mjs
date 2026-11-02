// Inventory of running animations + layer-promoting styles per screen (what keeps the page busy while idle).
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  const inv = label=>c.evaluate(`(()=>{ const vh = innerHeight, g = {};
    document.getAnimations().forEach(a=>{ if(a.playState !== 'running') return; const t = a.effect && a.effect.target; if(!t) return; const tm = a.effect.getTiming(); const name = (a.animationName || a.transitionProperty || (a.id || 'waapi')) + (tm.iterations === Infinity ? ' ∞' : '');
      const r = t.getBoundingClientRect(); const vis = r.bottom > 0 && r.top < vh && r.width > 0 && r.height > 0 && getComputedStyle(t).visibility !== 'hidden';
      const k = name + ' @' + (t.className && t.className.baseVal === undefined ? String(t.className).split(' ').slice(0,2).join('.') : t.tagName); g[k] = g[k] || { n:0, offscreen:0 }; g[k].n++; if(!vis) g[k].offscreen++; });
    let wc = 0, bf = 0, fl = 0; const wcs = {};
    for(const e of document.querySelectorAll('*')){ const s = getComputedStyle(e); if(s.willChange !== 'auto'){ wc++; const k = String(e.className).split(' ')[0] + ':' + s.willChange; wcs[k] = (wcs[k] || 0) + 1; } if(s.backdropFilter !== 'none' || s.webkitBackdropFilter && s.webkitBackdropFilter !== 'none') bf++; if(s.filter !== 'none') fl++; }
    return { label:${JSON.stringify(label)}, anims:Object.entries(g).sort((a,b)=>b[1].n-a[1].n).slice(0, 30).map(([k,v])=>k+' ×'+v.n+(v.offscreen?' (offscreen '+v.offscreen+')':'')), willChange:wc, willChangeTop:Object.entries(wcs).sort((a,b)=>b[1]-a[1]).slice(0,12), backdrop:bf, filters:fl, dom:document.getElementsByTagName('*').length }; })()`);
  console.log(JSON.stringify(await inv('home'), null, 1));
  await c.evaluate(`econOpenStore()`); await c.sleep(3000);
  console.log(JSON.stringify(await inv('store'), null, 1));
  for(let i = 0; i < 3; i++){ await c.swipe(200, 700, 200, 14); await c.sleep(300); }
  await c.sleep(1500);
  console.log(JSON.stringify(await inv('store after scroll'), null, 1));
}
