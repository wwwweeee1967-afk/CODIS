/* CODIS-MULTI-STICKER test — evaluate in the page on a guest origin (served next to assets/stickers).
   Run: TEST=tests/multisticker_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1 */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i });
  const cnt = (h, c)=>(String(h).match(new RegExp(c, 'g')) || []).length;
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};

  /* 1) id rule: single ids unchanged; lists cleaned (valid, unique, max 3) */
  T('single id unchanged', codisStickerIdOk('falafel') === 'falafel');
  T('list kept in order', codisStickerIdOk('kunafa+falafel+tea_glass') === 'kunafa+falafel+tea_glass');
  T('list cleaned: bad/duplicate dropped, capped at 3', codisStickerIdOk('a+falafel+falafel+X!+tea_glass+kunafa+donut') === 'falafel+tea_glass+kunafa', codisStickerIdOk('a+falafel+falafel+X!+tea_glass+kunafa+donut'));
  T('garbage ⇒ null', codisStickerIdOk('++') === null && codisStickerIdOk(5) === null && codisStickerIdOk('') === null);

  /* 1b) LOAD-TIME SAFETY (3.17.2 regression): codisStickerIdOk runs inside loadData() BEFORE later consts exist, so it must never
     depend on one (TDZ crash that bricked accounts holding stickerId:'') and must never throw whatever the stored value is */
  T('codisStickerIdOk has no dependency on later-declared constants', !/CODIS_STICKER_MAX|CodisStickers|CodisAtmos/.test(String(codisStickerIdOk)));
  T('empty / odd stored values ⇒ null (no crash)', ['', ' ', '+', '++a', 'A', 'bad id!', 'x', '0', 'a+', '+falafel+'].every(v=>{ try{ const r = codisStickerIdOk(v); return r === null || r === 'falafel'; }catch(e){ return false; } }));
  T('non-string stored values never throw', [undefined, null, 0, 5, {}, [], ['falafel'], true, NaN, () => 1].every(v=>{ try{ return codisStickerIdOk(v) === null; }catch(e){ return false; } }));
  T('huge / hostile strings are safe', (()=>{ try{ return codisStickerIdOk('a'.repeat(1e5)) === null && codisStickerIdOk('falafel+'.repeat(5e4)) === 'falafel'; }catch(e){ return false; } })());
  T('layer survives an atmosphere failure (sticker still renders)', (()=>{ const real = CodisAtmos.html; CodisAtmos.html = ()=>{ throw new Error('boom'); };
    try{ return /class="rwc-stk rwc-stk-d"/.test(codisStickerLayerHtml({ stickerId:'falafel' }, 'd', 'C')); } finally { CodisAtmos.html = real; } })());

  /* 2) rendering: main sticker tag byte-identical; extras are separate, ordered under it */
  const e = { kind:'reward', scope:'daily', rarityTone:'C', item:'x', coinValue:5 };
  const one = codisRewardCardHtml(Object.assign({}, e, { stickerId:'falafel' }), { plain:true });
  const three = codisRewardCardHtml(Object.assign({}, e, { stickerId:'falafel+tea_glass+kunafa' }), { plain:true });
  const mainTag = '<img class="rwc-stk rwc-stk-d" src="' + escapeHtml(CodisStickers.url('falafel')) + '" alt="" draggable="false" decoding="async" onerror="this.remove()">';
  T('single sticker: no extras, main tag unchanged', cnt(one, 'rwc-stk2') === 0 && one.indexOf(mainTag) !== -1);
  T('three stickers: main tag identical + 2 extras', three.indexOf(mainTag) !== -1 && cnt(three, 'class="rwc-stk2 ') === 2);
  T('extras come before the main tag (main paints on top)', three.indexOf('rwc-stk2') < three.indexOf(mainTag));
  T('missing image in the list is skipped (next one becomes main)', codisRewardCardHtml(Object.assign({}, e, { stickerId:'no_such+tea_glass' }), { plain:true }).indexOf('rwc-stk rwc-stk-d" src="' + escapeHtml(CodisStickers.url('tea_glass'))) !== -1);
  ['w', 'm'].forEach(f=>{ const h = f === 'w' ? codisWeeklyCardHtml({ kind:'reward', scope:'weekly', rarityTone:'B', item:'x', stickerId:'falafel+soda+fries' }, { plain:true }) : codisMonthlyCardHtml({ kind:'reward', scope:'monthly', rarityTone:'C', item:'x', stickerId:'falafel+soda+fries' }, { plain:true });
    T('family ' + f + ' renders all three', cnt(h, 'class="rwc-stk2 ') === 2 && cnt(h, 'class="rwc-stk ') === 1); });
  T('teacher + plain render all three', cnt(codisRewardCardHtml(Object.assign({}, e, { room:'learn', stickerId:'falafel+soda+fries' }), { plain:true }), 'rwc-stk2 ') === 2 && cnt(codisPlainCardHtml('x', econCfg().rarities[0], { stickerId:'falafel+soda+fries' }), 'rwc-stk2 ') === 2);
  T('punishment cards still never get stickers', cnt(codisPunishCardHtml({ kind:'punish', scope:'daily', item:'ع', severity:'LOW', stickerId:'falafel+soda' }, { plain:true }), 'rwc-stk') === 0);

  /* 3) atmosphere avoids the extra stickers, mixes their heroes, stays deterministic */
  const fams = [['d', 'C'], ['d', 'B'], ['d', 'A'], ['d', 'S'], ['d', 'SS'], ['w', 'C'], ['w', 'B'], ['w', 'A'], ['w', 'S'], ['w', 'SS'], ['m', 'C'], ['m', 'B'], ['m', 'A'], ['m', 'S'], ['m', 'SS'], ['s', 'teacher'], ['p', '']];
  const bad = [];
  ['falafel+tea_glass+kunafa', 'gamepad+headset+puzzle', 'camping+landmark+backpack'].forEach(id=>fams.forEach(([f, k])=>{
    const g = CodisAtmos.get(id, f, k);
    if(!g || !g.n){ bad.push('empty ' + id + '@' + f + k); return; }
    g.pts.forEach(p=>g.block.forEach(b=>{ const x1 = b[0], y1 = b[1] * g.H / 100, x2 = b[2], y2 = b[3] * g.H / 100, r = p.s * .48 - .01;
      const cx = Math.max(x1, Math.min(p.x, x2)), cy = Math.max(y1, Math.min(p.y, y2)); if((p.x - cx) * (p.x - cx) + (p.y - cy) * (p.y - cy) < r * r) bad.push(id + '@' + f + k); }));
  }));
  T('atmosphere never overlaps the extra stickers or protected zones', bad.length === 0, bad.slice(0, 5).join(' '));
  T('order matters (different main ⇒ different card)', CodisAtmos.get('falafel+tea_glass', 'd', 'C').src !== CodisAtmos.get('tea_glass+falafel', 'd', 'C').src);
  T('deterministic', CodisAtmos.get('falafel+tea_glass', 'd', 'C').src === CodisAtmos.get('falafel+tea_glass', 'd', 'C').src);

  /* 4) data paths keep the list: settings normalize → roll snapshot → owned copy → later edit doesn't leak */
  econCfg().rarities.forEach(r=>data.settings.rewardItems.push({ id:'ms_' + r.id, name:'متعدد ' + r.id, rarity:r.id, weight:10, room:'tasks', enabled:true, stickerId:'falafel+tea_glass+kunafa' }));
  econNormalizeItems(data.settings);
  const mine = data.settings.rewardItems.filter(x=>String(x.id).indexOf('ms_') === 0);
  T('normalize keeps the list on reward definitions', mine.length && mine.every(x=>x.stickerId === 'falafel+tea_glass+kunafa'), mine.map(x=>x.stickerId).join(','));
  const others = data.settings.rewardItems.filter(x=>x.room === 'tasks' && String(x.id).indexOf('ms_') !== 0), was = others.map(x=>x.enabled);
  others.forEach(x=>{ x.enabled = false; });
  let r, d;
  try{ r = CodisEconomy.daily('tasks', new Date().getDay(), 'reward', 100); d = r && r.entry ? CodisEconomy.decideReward(r.entry.id, 'item') : null; }
  finally { others.forEach((x, i)=>{ x.enabled = was[i]; }); }
  T('roll snapshots the whole list', r && r.entry && r.entry.stickerId === 'falafel+tea_glass+kunafa', r && r.entry && r.entry.stickerId);
  mine.forEach(x=>{ x.stickerId = 'donut'; });
  T('owned copy keeps the list after the reward is edited', d && d.owned && CodisInventory.get(d.owned.uid).stickerId === 'falafel+tea_glass+kunafa');
  data.settings.rewardItems = data.settings.rewardItems.filter(x=>String(x.id).indexOf('ms_') !== 0); econNormalizeItems(data.settings);

  /* 5) picker: ordered multi-select, max 3, promote, remove, confirm */
  openSettingsCategory('rewards'); econRenderRewards(); await new Promise(q=>setTimeout(q, 200));
  codisSetSticker('eco-new-r', ''); codisOpenStickerPicker('eco-new-r'); await new Promise(q=>setTimeout(q, 300));
  const tile = id=>document.querySelector('.stk-tile[data-id="' + id + '"]'), S = ()=>[...document.querySelectorAll('.stk-sel button')].map(b=>b.dataset.mk).join('+');
  ['falafel', 'tea_glass', 'kunafa'].forEach(id=>tile(id).click());
  T('picker: three selected in order with numbered badges', S() === 'falafel+tea_glass+kunafa' && document.querySelectorAll('.stk-tile .stk-ord').length === 3);
  tile('donut').click();
  T('picker: a 4th is refused', S() === 'falafel+tea_glass+kunafa');
  document.querySelector('.stk-sel button[data-mk="kunafa"]').click();
  T('picker: tapping a chip makes it the main sticker', S() === 'kunafa+falafel+tea_glass' && document.querySelector('.stk-tile[data-id="kunafa"] .stk-ord.is-main'));
  document.querySelector('.stk-sel [data-rmk="falafel"]').click();
  T('picker: ✕ removes one', S() === 'kunafa+tea_glass');
  tile('tea_glass').click();
  T('picker: tapping a selected tile deselects it', S() === 'kunafa');
  tile('tea_glass').click();
  T('picker: preview shows the full stack', document.querySelectorAll('.stk-pv .rwc-stk2').length === 1 && document.querySelectorAll('.stk-pv .rwc-stk').length === 1);
  document.querySelector('.stk-foot [data-a="ok"]').click(); await new Promise(q=>setTimeout(q, 300));
  T('confirm stores the ordered list', document.getElementById('eco-new-r-sticker').value === 'kunafa+tea_glass');
  T('editor row shows the stack + names', document.querySelectorAll('#eco-new-r-stk-row .stk-th img').length === 2 && /\(2\)/.test(document.getElementById('eco-new-r-stk-row').textContent));
  codisSetSticker('eco-new-r', '');
  T('remove clears everything', document.getElementById('eco-new-r-sticker').value === '' && !document.querySelector('#eco-new-r-stk-row .stk-th img'));

  return { passed:out.filter(x=>x.ok).length, failed:out.filter(x=>!x.ok).length, failures:out.filter(x=>!x.ok) };
}catch(err){ return { passed:0, failed:1, failures:[{ name:'crash', info:String(err && err.stack || err) }] }; } })();
