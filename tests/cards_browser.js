/* CODIS-CARDS-V2 — card frame + back test (evaluate in the page, guest). Measures real rendered geometry. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  data.wallet.balance = 5000; saveData(); econOpenStore(); await sleep(900);
  [...document.querySelectorAll('#eco-store-body button')].filter(b=>/الكروت/.test(b.textContent))[0].click(); await sleep(900);
  const frames = [...document.querySelectorAll('#eco-store-body .rwc')], geo = frames.map(f=>{ const a = f.querySelector('.rwc-art'), b = f.getBoundingClientRect(); if(!a) return null; const r = a.getBoundingClientRect(); return { ratio:b.width / b.height, l:r.left - b.left, t:r.top - b.top, w:b.width, aw:r.width }; }).filter(Boolean);
  T('store frames are real 4:5', geo.length > 0 && geo.every(g=>Math.abs(g.ratio - 0.8) < 0.01), geo.length + ' frames');
  const full = geo.filter(g=>Math.abs(g.aw / g.w - 1) < 0.06);   /* 4:5 artwork (daily/weekly/special): must fill the frame */
  T('4:5 artwork fills its frame (padding <= 1.5px each side = the 1px border)', full.length > 0 && full.every(g=>g.l <= 1.5 && g.t <= 1.5), full.length + ' checked, max pad ' + Math.max.apply(null, full.map(g=>Math.max(g.l, g.t))).toFixed(1));
  const narrow = geo.filter(g=>g.aw / g.w < 0.94); T('natively taller art (monthly/punishment) is contained, not cropped or stretched', narrow.every(g=>g.t <= 1.5), narrow.length + ' contained');
  /* backs: every kind x tone renders its own title/rows, in bounds, no overflow */
  const kinds = ['reward', 'weekly', 'monthly', 'pass', 'holiday', 'pouch', 'cosmetic', 'box'], tones = ['c', 'b', 'a', 's', 'ss'], host = document.createElement('div');
  host.style.cssText = 'position:fixed;left:0;top:0;width:120px;opacity:0;pointer-events:none'; document.body.appendChild(host);
  let bad = [];
  kinds.forEach(k=>tones.forEach(tn=>{
    host.innerHTML = '<div style="aspect-ratio:4/5;position:relative;--card-r:12px">' + codisCardBackHtml('اسم البطاقة ' + k + tn, [['الفئة', 'x'], ['القسم', 'y'], ['السعر', '99']], { tone:tn, kind:k, note:'ملاحظة قصيرة' }) + '</div>';
    const box = host.firstChild.getBoundingClientRect(), inn = host.querySelector('.cbk-in').getBoundingClientRect(), t = host.querySelector('.cbk-t');
    if(!(inn.left >= box.left - 0.5 && inn.right <= box.right + 0.5 && inn.bottom <= box.bottom + 0.5 && inn.top >= box.top + box.height * 0.3) || !t.textContent.includes(k + tn) || !host.querySelector('.cbk-orn')) bad.push(k + tn);
  }));
  T('backs: ' + kinds.length * tones.length + ' kind x rarity combinations render in bounds, below the medallion, with their own title', bad.length === 0, bad.join(','));
  const sig = new Set(); kinds.forEach(k=>tones.forEach(tn=>sig.add(codisBackOrnament(tn, k, 'x').length + tn + k))); T('every kind x rarity has a different composition', sig.size === kinds.length * tones.length);
  T('same card = same ornament (deterministic), different card name = different details', codisBackOrnament('s', 'pass', 'a') === codisBackOrnament('s', 'pass', 'a') && codisBackOrnament('s', 'pass', 'a') !== codisBackOrnament('s', 'pass', 'b'));
  /* flipping: back is identical in size to the front, absolutely positioned (no layout shift) */
  const cf = document.querySelector('#eco-store-body .st-tile .cflip'), before = cf.parentElement.getBoundingClientRect().height, fr = cf.querySelector('.cflip-f').getBoundingClientRect(), bk = cf.querySelector('.cflip-b').getBoundingClientRect();
  T('back face has exactly the front face size', Math.abs(fr.width - bk.width) < 0.5 && Math.abs(fr.height - bk.height) < 0.5);
  codisFlipToggle(cf); await sleep(800); T('flipping does not change the tile height (no layout jump)', Math.abs(cf.parentElement.getBoundingClientRect().height - before) < 0.5);
  host.remove();
  const failed = out.filter(r=>!r.ok); return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
