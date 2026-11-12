/* CODIS-STICKERS test — evaluate in the page on a FRESH guest origin, with a few fixture images present in assets/stickers
   (needs the shipped library in assets/stickers, served next to the page). */
(async function(){ try{
  /* 3.30.0: نموذج الإضافة اليدوي أُزيل من الواجهة (الإضافة الجديدة تلقائية فقط)؛ الاختبار يركّبه كأداة لاختبار المحرر/الستيكر/الحفظ */
  const legacyAdd = (period)=>{ let h = document.getElementById('reward-add-box'); if(!h){ h = document.createElement('div'); h.id = 'reward-add-box'; h.style.cssText = 'position:fixed;left:-9999px;top:0'; document.body.appendChild(h); } h.innerHTML = econRewardEditor('eco-new-r', null) + '<button type="button" class="btn btn-primary eco-full" onclick="econAddReward()">إضافة المكافأة</button>'; h.dataset.ready = '1'; const sel = document.getElementById('eco-new-r-room'); sel.value = period === 'daily' ? settingsDailyRoom : period; econRewardRarityChanged('eco-new-r'); };
  legacyAdd('daily');
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  const S = q=>CodisStickers.search(q).map(o=>o.id).join(',');
  const realIs = CodisAccount.isAdmin;

  /* ---- 1) library + search ---- */
  T('library has 80+ images + full metadata', CodisStickers.count() >= 80 && CodisStickers.total() >= 80, CodisStickers.count() + '/' + CodisStickers.total());
  T('stickers without an image file are not offered', CodisStickers.search('').every(o=>CodisStickers.has(o.id)));
  ['جاي', 'چاي', 'شاي', 'استكان', 'ستكان'].forEach(w=>T('tea variants find the tea glass: ' + w, S(w).split(',').indexOf('tea_glass') !== -1, S(w)));
  ['شاورمة', 'شاورما', 'الشاورمة', 'لفة شاورمة'].forEach(w=>T('shawarma variants: ' + w, S(w).split(',').indexOf('shawarma') !== -1, S(w)));
  T('category word: حلويات finds kunafa', S('حلويات').split(',').indexOf('kunafa') !== -1 && S('حلويات').split(',').length >= 9, S('حلويات'));
  T('«كلاص» / «كوب» / «مشروب» find drinks', /iced_coffee/.test(S('كلاص')) && /tea_glass/.test(S('كوب')) && /iced_coffee/.test(S('مشروب')));
  T('no result for nonsense', S('qqxxzz') === '');
  T('category filter works', CodisStickers.search('', 'tea').every(o=>o.cat === 'tea') && CodisStickers.cats().length >= 5);
  T('sticker id validator', codisStickerIdOk('tea_glass') === 'tea_glass' && codisStickerIdOk('<x>') === null && codisStickerIdOk('') === null && codisStickerIdOk(5) === null && codisStickerIdOk('a') === null);

  /* ---- 2) editor: add with / without sticker, edit, change, remove ---- */
  openSettingsCategory('rewards'); settingsRoom = 'tasks'; econRenderRewards(); await sleep(200);
  const f = (id, v)=>{ document.getElementById('eco-new-r-' + id).value = v; };
  const N = ()=>data.settings.rewardItems.length, n0 = N();
  f('name', 'مكافأة بلا ستيكر'); econAddReward();
  const a = data.settings.rewardItems.find(x=>x.name === 'مكافأة بلا ستيكر');
  T('reward without sticker still works (stickerId null)', N() === n0 + 1 && a && a.stickerId === null);
  econRenderRewards();
  f('name', 'ستكان جاي عالفحم'); codisSetSticker('eco-new-r', 'tea_glass');
  T('picker row reflects the choice', /تغيير الستيكر/.test(document.getElementById('eco-new-r-stk-row').innerText) && !!document.querySelector('#eco-new-r-stk-row img'));
  econAddReward();
  const b = data.settings.rewardItems.find(x=>x.name === 'ستكان جاي عالفحم');
  T('reward saved with stickerId', b && b.stickerId === 'tea_glass');
  T('persisted to storage', (JSON.parse(localStorage.getItem(STORE_KEY)).settings.rewardItems.find(x=>x.id === b.id) || {}).stickerId === 'tea_glass');
  const bid = b.id, B = ()=>data.settings.rewardItems.find(x=>x.id === bid);   /* econNormalizeItems rebuilds the objects on every save */
  econEdit(b.id); await sleep(150);
  T('editor of an existing reward shows its sticker', document.getElementById('eco-edit-r-sticker').value === 'tea_glass');
  document.getElementById('eco-edit-r-name').value = 'ستكان جاي مهيل'; econSaveReward(b.id);
  T('renaming keeps the sticker', B().name === 'ستكان جاي مهيل' && B().stickerId === 'tea_glass');
  econEdit(bid); await sleep(150); codisSetSticker('eco-edit-r', 'kunafa'); econSaveReward(bid);
  T('changing the sticker works', B().stickerId === 'kunafa');
  econEdit(bid); await sleep(150); codisSetSticker('eco-edit-r', ''); econSaveReward(bid);
  T('removing the sticker works', B().stickerId === null);
  B().stickerId = 'tea_glass'; econNormalizeItems(data.settings); const okKeep = B().stickerId === 'tea_glass'; B().stickerId = '../x'; econNormalizeItems(data.settings);
  T('normalization keeps a valid id and cleans a bad one', okKeep && B().stickerId === null);
  B().stickerId = 'tea_glass'; saveData();

  /* ---- 3) card integration: same layer on every card family ---- */
  const e = { kind:'reward', room:'tasks', rarityTone:'c', item:'اختبار', coinValue:10, stickerId:'tea_glass' }, cnt = h=>(h.match(/class="rwc-stk /g) || []).length;
  T('daily card carries the sticker', cnt(codisRewardCardHtml(Object.assign({ scope:'daily' }, e), { plain:true })) === 1);
  T('weekly card carries the sticker', cnt(codisWeeklyCardHtml(Object.assign({ scope:'weekly' }, e, { rarityTone:'b' }), { plain:true })) === 1);
  T('monthly card carries the sticker', cnt(codisMonthlyCardHtml(Object.assign({ scope:'monthly' }, e, { rarityTone:'a' }), { plain:true })) === 1);
  T('teacher card carries the sticker', cnt(codisRewardCardHtml(Object.assign({ scope:'daily' }, e, { room:'learn' }), { plain:true })) === 1);
  T('plain (no-art) card carries the sticker', cnt(codisPlainCardHtml('خالية', econCfg().rarities[0], { stickerId:'tea_glass' })) === 1);
  T('no sticker / missing image ⇒ card unchanged', cnt(codisRewardCardHtml(Object.assign({ scope:'daily' }, e, { stickerId:null }), { plain:true })) === 0 && cnt(codisRewardCardHtml(Object.assign({ scope:'daily' }, e, { stickerId:'no_such_one' }), { plain:true })) === 0);
  T('name and price slots untouched', /rwc-name/.test(codisRewardCardHtml(Object.assign({ scope:'daily' }, e), { plain:true })) && /rwc-price/.test(codisRewardCardHtml(Object.assign({ scope:'daily' }, e), { plain:true })));
  const pun = codisPunishCardHtml ? codisPunishCardHtml({ kind:'punish', scope:'daily', item:'ع', severity:'LOW', stickerId:'tea_glass' }, { plain:true }) : '';
  T('punishment cards never get a sticker', cnt(pun) === 0);
  T('store face / pack tile / inventory path pass the id', cnt(econStoreFaceHtml({ room:'tasks', name:'x', stickerId:'tea_glass' }, econRarityById('C') || econCfg().rarities[0], {})) === 1 && cnt(econPackTileHtml({ id:'u1', room:'tasks', name:'x', stickerId:'tea_glass' }, { id:'C', name:'x', tone:'c', order:1 })) === 1);

  /* ---- 4) snapshots: roll → decision → inventory ---- */
  /* every rarity gets a real tasks reward, so the roll never falls back to a generic (sticker-less) reward */
  econCfg().rarities.forEach(r=>data.settings.rewardItems.push({ id:'stk_t_' + r.id, name:'ستيكر ' + r.id, rarity:r.id, weight:10, room:'tasks', enabled:true, stickerId:'tea_glass' }));
  econNormalizeItems(data.settings);
  data.settings.rewardItems.filter(x=>x.room === 'tasks').forEach(x=>{ x.stickerId = 'tea_glass'; x.enabled = true; });
  const r = CodisEconomy.daily('tasks', new Date().getDay(), 'reward', 100);
  const ent = r && r.entry;
  T('outcome entry snapshots stickerId at roll time', !!ent && ent.stickerId === 'tea_glass', ent && ent.stickerId);
  const rid = ent && ent.rewardId; const src = data.settings.rewardItems.find(x=>x.id === rid);
  if(src) src.stickerId = 'kunafa';   /* user edits the reward AFTER the roll */
  const d = CodisEconomy.decideReward(ent.id, 'item');
  T('taking the reward grants an owned copy', d.ok && d.owned);
  T('owned copy keeps the sticker from the moment of getting it', d.owned && d.owned.stickerId === 'tea_glass', d.owned && d.owned.stickerId);
  T('editing the reward later does not change the owned card', CodisInventory.get(d.owned.uid).stickerId === 'tea_glass');
  const art = econPackTileHtml({ id:d.owned.uid, room:d.owned.room, name:d.owned.name, stickerId:d.owned.stickerId }, { id:d.owned.rarity, name:d.owned.rarityName, tone:d.owned.rarityTone, order:d.owned.rarityOrder });
  T('inventory tile renders the historical sticker', /tea_glass/.test(art));
  if(src){ data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.id !== rid); econNormalizeItems(data.settings); }
  T('deleting the reward does not remove the owned card or its sticker', !!CodisInventory.get(d.owned.uid) && CodisInventory.get(d.owned.uid).stickerId === 'tea_glass');
  /* store purchase snapshot (developer path: unlimited coins) */
  const it2 = data.settings.rewardItems.find(x=>x.room === 'tasks' && x.enabled); it2.stickerId = 'shawarma';
  CodisAccount.isAdmin = ()=>true; let pr; try{ CodisWallet.apply('TEST_GRANT', 100000, 'test', 'test', 'tg|' + Date.now(), {}); pr = CodisEconomy.purchase(it2.id); } finally { CodisAccount.isAdmin = realIs; }
  T('store purchase snapshots the sticker', pr && pr.ok && pr.owned.stickerId === 'shawarma', pr && (pr.reason || pr.owned && pr.owned.stickerId));
  it2.stickerId = 'cinema';
  T('purchased copy unaffected by a later edit', CodisInventory.get(pr.owned.uid).stickerId === 'shawarma');

  /* ---- 5) legacy data + persistence round-trip ---- */
  const raw = JSON.parse(localStorage.getItem(STORE_KEY)); raw.settings.rewardItems.forEach(x=>delete x.stickerId); (raw.inventory.items || []).forEach(x=>delete x.stickerId);
  localStorage.setItem(STORE_KEY, JSON.stringify(raw));
  const norm = normalizeData(JSON.parse(localStorage.getItem(STORE_KEY)));
  T('old rewards/inventory without stickerId load as null (no forced choice)', norm.settings.rewardItems.every(x=>x.stickerId === null) && (norm.inventory.items || []).every(x=>x.stickerId === null));
  T('rewards totals untouched by the feature (no coin fields changed)', norm.settings.rewardItems.every(x=>x.coinValue === null && x.storePrice === null));

  /* ---- 6) picker UI ---- */
  openSettingsCategory('rewards'); econRenderRewards(); await sleep(150);
  codisOpenStickerPicker('eco-new-r'); await sleep(350);
  T('picker opens as a dialog with search + grid', !!document.querySelector('.stk-sheet[role="dialog"]') && !!document.querySelector('.stk-q') && document.querySelectorAll('.stk-tile').length === CodisStickers.count());
  const q = document.querySelector('.stk-q'); q.value = 'كنافة'; q.dispatchEvent(new Event('input'));
  T('search narrows the grid', document.querySelectorAll('.stk-tile').length >= 1 && document.querySelectorAll('.stk-tile').length < 5);
  q.value = 'ازرق ما موجود'; q.dispatchEvent(new Event('input'));
  T('empty search shows a clear message', !!document.querySelector('.stk-empty') && /ما لكينا/.test(document.querySelector('.stk-empty').innerText));
  q.value = ''; q.dispatchEvent(new Event('input'));
  document.querySelector('.stk-tile').click();
  T('selecting shows a preview + confirm', !!document.querySelector('.stk-pv .rwc-stk') && !!document.querySelector('.stk-foot [data-a="ok"]') && document.querySelector('.stk-tile[aria-selected="true"]'));
  document.querySelector('.stk-foot [data-a="ok"]').click(); await sleep(350);
  T('confirm stores the choice and closes the picker', !document.querySelector('.stk-sheet') && !!document.getElementById('eco-new-r-sticker').value);
  codisOpenStickerPicker('eco-new-r'); await sleep(300);
  T('removal button appears when a sticker is set', !!document.querySelector('.stk-foot [data-a="rm"]'));
  document.querySelector('.stk-foot [data-a="rm"]').click(); await sleep(350);
  T('remove clears the sticker', document.getElementById('eco-new-r-sticker').value === '');
  codisOpenStickerPicker('eco-new-r'); await sleep(300);
  T('Esc / back layer close the picker', (typeof codisBackLayer === 'function' ? !!(codisBackLayer() || {}).act : true));
  closeStickerPicker(); await sleep(350);
  T('picker removed from the DOM', !document.querySelector('.stk-ov'));
  const failed = out.filter(x=>!x.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
