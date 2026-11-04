/* CODIS-STICKER-ATMOS test — evaluate in the page (served next to assets/stickers). Display-only feature: no data is written.
   Run: TEST=tests/atmos_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1 */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i });
  const cnt = (h, c)=>(String(h).match(new RegExp(c, 'g')) || []).length;
  const e = { kind:'reward', scope:'daily', rarityTone:'C', item:'لفة فلافل', coinValue:120, stickerId:'falafel' };
  const card = x=>codisRewardCardHtml(Object.assign({}, e, x), { plain:true });

  /* 1) only with a valid sticker; the sticker tag itself is byte-identical to the original layer */
  T('no sticker ⇒ no atmosphere', cnt(card({ stickerId:null }), 'rwc-atm') === 0);
  T('unknown sticker ⇒ no atmosphere', cnt(card({ stickerId:'no_such_one' }), 'rwc-atm') === 0);
  T('valid sticker ⇒ exactly one atmosphere layer + one sticker', cnt(card({}), 'class="rwc-atm ') === 1 && cnt(card({}), 'rwc-stk ') === 1);
  const u = CodisStickers.url('falafel');
  T('sticker tag unchanged (same class/src/attrs as before)', card({}).indexOf('<img class="rwc-stk rwc-stk-d" src="' + escapeHtml(u) + '" alt="" draggable="false" decoding="async" onerror="this.remove()">') !== -1);
  T('atmosphere sits before the sticker (under it) and before the text slots', card({}).indexOf('rwc-atm') < card({}).indexOf('rwc-stk') && card({}).indexOf('rwc-atm') < card({}).indexOf('rwc-name'));
  T('punishment cards never get an atmosphere', cnt(codisPunishCardHtml({ kind:'punish', scope:'daily', item:'ع', severity:'LOW', stickerId:'falafel' }, { plain:true }), 'rwc-atm') === 0);

  /* 2) deterministic + distinct */
  const a1 = CodisAtmos.get('falafel', 'd', 'C').src, a2 = CodisAtmos.get('falafel', 'd', 'C').src;
  T('deterministic: same sticker+template ⇒ same image', a1 === a2 && card({}) === card({}));
  T('different stickers ⇒ different atmospheres', a1 !== CodisAtmos.get('tea_glass', 'd', 'C').src && CodisAtmos.get('tea_glass', 'd', 'C').src !== CodisAtmos.get('gamepad', 'd', 'C').src);
  T('same sticker on different templates adapts its layout', a1 !== CodisAtmos.get('falafel', 'd', 'B').src);

  /* 3) every sticker × every template: nothing lands on a protected zone (faces, plates, badges, sticker) */
  const fams = [['d', 'C'], ['d', 'B'], ['d', 'A'], ['d', 'S'], ['d', 'SS'], ['w', 'C'], ['w', 'B'], ['w', 'A'], ['w', 'S'], ['w', 'SS'], ['m', 'C'], ['m', 'B'], ['m', 'A'], ['m', 'S'], ['m', 'SS'], ['s', 'teacher'], ['p', '']];
  const bad = [], empty = []; let tot = 0;
  CodisStickers.search('').forEach(o=>fams.forEach(([f, k])=>{
    const g = CodisAtmos.get(o.id, f, k); if(!g || !g.n){ empty.push(o.id + '@' + f + k); return; }
    tot += g.n;
    g.pts.forEach(p=>g.block.forEach(b=>{
      const x1 = b[0], y1 = b[1] * g.H / 100, x2 = b[2], y2 = b[3] * g.H / 100, r = p.s * .48 - .01;
      const cx = Math.max(x1, Math.min(p.x, x2)), cy = Math.max(y1, Math.min(p.y, y2));
      if((p.x - cx) * (p.x - cx) + (p.y - cy) * (p.y - cy) < r * r) bad.push(o.id + '@' + f + k);
    }));
  }));
  T('all stickers × all templates render an atmosphere', empty.length === 0, empty.slice(0, 6).join(' '));
  T('no main element overlaps a protected zone', bad.length === 0, bad.slice(0, 6).join(' '));
  T('restrained: ≤ 6 main elements per card (≤ 4 on monthly)', fams.every(([f, k])=>CodisStickers.search('').every(o=>CodisAtmos.get(o.id, f, k).n <= (f === 'm' ? 4 : 6))), tot);

  /* 4) hold interaction only where a safe hand exists, only for holdable stickers */
  const w = (id, k)=>codisWeeklyCardHtml({ kind:'reward', scope:'weekly', rarityTone:k, item:'x', coinValue:5, stickerId:id }, { plain:true });
  T('hold: weekly B/SS get the held object for food', cnt(w('falafel', 'B'), 'rwc-atm-hold') === 1 && cnt(w('falafel', 'SS'), 'rwc-atm-hold') === 1);
  T('hold: never on daily or hand-less weekly cards', cnt(card({}), 'rwc-atm-hold') === 0 && cnt(w('falafel', 'S'), 'rwc-atm-hold') === 0 && cnt(w('falafel', 'C'), 'rwc-atm-hold') === 0);
  T('hold: non-holdable sticker (park) is never held', cnt(w('park_picnic', 'B'), 'rwc-atm-hold') === 0);

  /* 5) every palette/recipe is real build-time data */
  const ids = CodisStickers.search('').map(o=>o.id);
  T('every sticker has a recipe + 6-colour palette', ids.every(id=>CODIS_STICKER_ATMOS[id] && CODIS_STICKER_ATMOS[id][1].length === 6 && CODIS_STICKER_ATMOS[id][1].every(c=>/^#[0-9a-f]{6}$/.test(c))));
  T('every recipe motif exists in the engine', ids.every(id=>CODIS_STICKER_ATMOS[id][0].every(m=>CodisAtmos.motifs().indexOf(m) !== -1)));

  /* 6) live DOM */
  const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:300px;height:375px;container-type:size;opacity:0;pointer-events:none';
  box.innerHTML = card({}); document.body.appendChild(box); await new Promise(r=>setTimeout(r, 200));
  const at = box.querySelector('.rwc-atm'), sa = getComputedStyle(at);
  T('layer is inert (pointer-events:none, aria-hidden)', sa.pointerEvents === 'none' && at.getAttribute('aria-hidden') === 'true');
  const sk = getComputedStyle(box.querySelector('.rwc-stk')), sw = box.querySelector('.rwc-stage').getBoundingClientRect().width;
  T('sticker keeps its rules (z3, -9deg, 33% wide, -2.5% left)', sk.zIndex === '3' && /0\.98768/.test(sk.transform) && Math.abs(parseFloat(sk.width) / sw - .33) < .01 && Math.abs(parseFloat(sk.left) / sw + .025) < .005, sk.width + ' ' + sk.left);
  box.innerHTML = card({ stickerId:null });
  T('removing the sticker removes every trace', !box.querySelector('.rwc-atm, .rwc-atm-hold, .rwc-stk'));
  box.remove();

  return { passed:out.filter(x=>x.ok).length, failed:out.filter(x=>!x.ok).length, failures:out.filter(x=>!x.ok) };
}catch(err){ return { passed:0, failed:1, failures:[{ name:'crash', info:String(err && err.stack || err) }] }; } })();
