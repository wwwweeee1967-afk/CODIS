/* CODIS sticker-atmosphere contact sheet — evaluate in the app page (any account). Read-only: builds an overlay, touches no data.
   Usage (browser console or CDP): paste/evaluate, then window.__atmosSheet(tpl, from, count)  — from may be an array of sticker ids
   tpl: 'd:C' (daily C) · 'w:B' · 'm:S' · 'teacher' · 'resist' — cards render at real store-tile width (110px) with the live engine. */
(function(){
  const close = ()=>{ const o = document.getElementById('atmos-sheet'); if(o) o.remove(); };
  window.__atmosSheet = function(tpl, from, count){
    close(); tpl = tpl || 'd:C'; from = from || 0; count = count || 30;
    let ids = CodisStickers.all ? CodisStickers.all().map(s=>s.id) : CodisStickers.search('', '').map(s=>s.id);
    if(Array.isArray(from)){ ids = from.filter(x=>ids.indexOf(x) !== -1); from = 0; count = ids.length; }   /* قائمة معرّفات محددة */
    const rar = k=>econCfg().rarities.find(r=>r.tone === k.toLowerCase()) || econCfg().rarities[0];
    const card = id=>{
      const nm = (CodisStickers.get(id) || {}).name || id;
      if(tpl === 'teacher') return econStoreFaceHtml({ room:'learn', name:nm, stickerId:id }, econCfg().rarities[0], { label:nm });
      if(tpl === 'resist') return econStoreFaceHtml({ fixed:true, id:'fx_rs_normal', room:'habits', name:nm, stickerId:id }, econCfg().rarities[0], { label:nm });
      const fam = tpl[0], tone = tpl.slice(2);
      return econStoreFaceHtml({ room:fam === 'w' ? 'weekly' : fam === 'm' ? 'monthly' : 'tasks', name:nm, stickerId:id }, rar(tone), { label:nm });
    };
    const o = document.createElement('div'); o.id = 'atmos-sheet';
    o.style.cssText = 'position:fixed;inset:0;z-index:99999;overflow:auto;background:#efe6d2;padding:8px;display:grid;grid-template-columns:repeat(auto-fill,110px);gap:8px 6px;justify-content:center;align-content:start';
    o.innerHTML = ids.slice(from, from + count).map(id=>'<div style="width:110px"><div class="store-art is-card">' + card(id) + '</div><div style="font:600 9px/1.3 system-ui;color:#333;text-align:center;direction:ltr">' + id + '</div></div>').join('');
    o.addEventListener('dblclick', close);
    document.body.appendChild(o);
    try{ codisFitRewardCard(o); codisWatchRewardCards(o); }catch(e){}
    return ids.length;
  };
  window.__atmosSheetClose = close;
  return 'ready';
})();
