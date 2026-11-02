// Hunt the idle layout loop: count content-visibility state flips, ResizeObserver callbacks, scroll events, mutations while idle.
export default async function(c){
  await c.send('Page.addScriptToEvaluateOnNewDocument', { source:`(()=>{ window.__ro = 0; window.__roT = {}; const RO = window.ResizeObserver; if(!RO) return;
    window.ResizeObserver = class extends RO{ constructor(cb){ const tag = (new Error().stack.split('\\n')[2] || '').trim().slice(0, 120); super((e, o)=>{ window.__ro++; window.__roT[tag] = (window.__roT[tag] || 0) + 1; return cb(e, o); }); } }; })();` });
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  await c.evaluate(`econOpenStore()`); await c.sleep(3500);
  const r = await c.evaluate(`(async()=>{ const o = { cv:0, cvEls:{}, scroll:0, mut:0, mutT:{}, raf:0 };
    document.addEventListener('contentvisibilityautostatechange', e=>{ o.cv++; const k = (e.target.id || String(e.target.className).split(' ')[0]) + (e.skipped ? ':skip' : ':show'); o.cvEls[k] = (o.cvEls[k] || 0) + 1; }, true);
    document.addEventListener('scroll', ()=>o.scroll++, true);
    const mo = new MutationObserver(l=>{ l.forEach(m=>{ o.mut++; const t = m.target.nodeType === 1 ? m.target : m.target.parentElement; const k = m.type + ':' + (m.attributeName || '') + ':' + (t && (t.id || String(t.className).split(' ').slice(0,2).join('.'))); o.mutT[k] = (o.mutT[k] || 0) + 1; }); });
    mo.observe(document.body, { subtree:true, childList:true, attributes:true, characterData:true });
    const ro0 = window.__ro; const roT0 = Object.assign({}, window.__roT);
    await new Promise(r=>setTimeout(r, 3000)); mo.disconnect();
    o.ro = window.__ro - ro0; o.roT = Object.fromEntries(Object.entries(window.__roT).map(([k,v])=>[k, v - (roT0[k] || 0)]).filter(x=>x[1] > 0));
    o.mutT = Object.entries(o.mutT).sort((a,b)=>b[1]-a[1]).slice(0, 15);
    o.scrollTop = (document.scrollingElement || {}).scrollTop; const sc = document.querySelector('.main'); o.mainScroll = sc && sc.scrollTop;
    return o; })()`);
  console.log(JSON.stringify(r, null, 1));
}
