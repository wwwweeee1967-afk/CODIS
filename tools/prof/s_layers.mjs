// Composited-layer census of the store (what forces GPU layers: 3D, backface, filters, will-change, animations) + LayerTree if available.
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  await c.evaluate(`econOpenStore()`); await c.sleep(3500);
  const r = await c.evaluate(`(()=>{ const g = {}; let n = 0; const add = (k, e)=>{ const cls = String(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className).split(' ').slice(0, 2).join('.') || e.tagName; const kk = k + ' @' + cls; g[kk] = (g[kk] || 0) + 1; n++; };
    for(const e of document.querySelectorAll('*')){ const s = getComputedStyle(e);
      if(s.transformStyle === 'preserve-3d') add('preserve-3d', e);
      if(s.backfaceVisibility === 'hidden') add('backface-hidden', e);
      if(s.willChange !== 'auto') add('will-change:' + s.willChange, e);
      if(s.filter !== 'none') add('filter', e);
      if(s.backdropFilter !== 'none' || (s.webkitBackdropFilter && s.webkitBackdropFilter !== 'none')) add('backdrop', e);
      if(s.mixBlendMode !== 'normal') add('blend:' + s.mixBlendMode, e);
      if(s.contentVisibility && s.contentVisibility !== 'visible') add('content-visibility:' + s.contentVisibility, e);
      if(/(^|\\s)(translateZ|translate3d|rotate[XY]|perspective)/.test(s.transform) || (s.transform !== 'none' && s.transform.indexOf('matrix3d') === 0)) add('3d-transform', e);
      if(s.perspective !== 'none') add('perspective', e);
      for(const p of ['::before', '::after']){ const ps = getComputedStyle(e, p); if(ps.content !== 'none' && ps.animationName !== 'none') add('anim' + p + ':' + ps.animationName, e); if(ps.content !== 'none' && ps.filter !== 'none') add('filter' + p, e); }
    }
    return { total:n, groups:Object.entries(g).sort((a,b)=>b[1]-a[1]).slice(0, 40), dom:document.getElementsByTagName('*').length, imgs:document.querySelectorAll('#eco-store-body img').length,
      imgPx:Array.prototype.reduce.call(document.querySelectorAll('#eco-store-body img'), (a, i)=>a + (i.naturalWidth * i.naturalHeight || 0), 0) }; })()`);
  console.log(JSON.stringify(r, null, 1));
  try{ const lt = c.layers(); console.log('layerTree layers', lt.length, JSON.stringify(c.layerMem())); }catch(e){}
}
