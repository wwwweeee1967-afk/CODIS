/* CODIS-V44 (3.31.0) — in-browser regression test: tests/freebox_browser.js  (الصندوق المجاني + كرت 1–10)
   Run: TEST=tests/freebox_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   يعدّل بيانات ملف الاختبار المحلي فقط ويستعيدها. Returns { passed, failed, results[] }. */
(async function(){
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : String(info) });
  const eq = (name, a, b)=>T(name, JSON.stringify(a) === JSON.stringify(b), JSON.stringify(a) + ' vs ' + JSON.stringify(b));
  const keepItems = JSON.stringify(data.settings.rewardItems), keepInv = JSON.stringify(data.inventory), keepEco = JSON.stringify(data.economyState), keepWallet = JSON.stringify(data.wallet);
  const isAdminNow = (()=>{ try{ return CodisAccount.isAdmin() === true; }catch(e){ return false; } })();
  T('guest is not admin (limits apply)', !isAdminNow);
  const add = (name, min, extra)=>codisFinCreateReward(Object.assign({ name:name, kind:'time', minutes:min, cardId:'free_box' }, extra || {}));   /* دقائق = 2 × كوين */

  /* ===== الكرت والتصنيف ===== */
  const fc = codisFreeCard();
  T('card range 1..10 inclusive', fc.min === 1 && fc.max === 10 && !fc.maxOpen && fc.id === 'free_box');
  T('card is outside the 25-card matrix', codisFinCards().length === 25 && !codisFinCards().some(c=>c.id === 'free_box'));
  T('matrix check still ok', codisFinMatrixCheck().ok, JSON.stringify(codisFinMatrixCheck().problems));
  T('codisFinClassify unchanged: 5 coin → low', codisFinClassify('شاي', 5).reason === 'low');
  T('codisFinClassify unchanged: 0.5 → low', codisFinClassify('شاي', 0.5).reason === 'low');
  for(const v of [10, 12, 100, 37.5, 11250, 30000]){
    const a = codisFinClassify('شاي', v), b = codisFinClassifyAuto('شاي', v);
    T('Auto keeps best/ambiguous/suggestions at ' + v, a.ok && b.ok && a.best.card.id === b.best.card.id && a.ambiguous === b.ambiguous && JSON.stringify(a.suggestions.map(c=>c.card.id)) === JSON.stringify(b.suggestions.map(c=>c.card.id)));
    T('Auto adds free candidate ONLY ≤10 (v=' + v + ')', b.candidates.some(c=>c.card.free) === (v <= 10));
  }
  T('coin 10 → free is an explicit extra (last) candidate', (()=>{ const r = codisFinClassifyAuto('شاي', 10); return r.candidates[r.candidates.length - 1].card.free && !r.best.card.free; })());
  T('coin 7 → only free card, auto-picked', (()=>{ const r = codisFinClassifyAuto('شاي', 7); return r.ok && r.candidates.length === 1 && r.best.card.free && !r.ambiguous; })());
  T('coin 0.99 → low', codisFinClassifyAuto('شاي', 0.99).reason === 'low');
  T('codisFinCardById free', codisFinCardById('free_box') === fc && codisFinInRange(fc, 1) && codisFinInRange(fc, 10) && !codisFinInRange(fc, 10.01) && !codisFinInRange(fc, 0.99));

  /* ===== إنشاء مكافآت 1/4/5/7/10 + الرفض ===== */
  data.settings.rewardItems = data.settings.rewardItems.filter(x=>!x.freebox);
  const made = {};
  for(const [nm, coin] of [['فرصة واحد', 1], ['شاي اربعة', 4], ['شي خمسة', 5], ['شي سبعة', 7], ['شي عشرة', 10]]){
    const r = add(nm, coin * 2, nm === 'شي سبعة' ? { stickerId:'pizza' } : {});
    made[coin] = r;
    T('create ' + coin + ' coin ok', r.ok && r.card.free && r.coin === coin, JSON.stringify(r).slice(0, 120));
    T('  item flagged + isolated (' + coin + ')', r.ok && r.item.freebox === true && r.item.fin.card === 'free_box' && r.item.weight === 0 && r.item.room === 'tasks');
  }
  T('reject <1 (0.5 coin)', add('x', 1).reason === 'low');
  T('reject >10 with free card (10.5)', add('x', 21).reason === 'range');
  T('reject >10 auto (11)', (()=>{ const r = codisFinCreateReward({ name:'شي', kind:'time', minutes:22 }); if(r.ok){ data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.id !== r.item.id); } return r.ok && !r.item.freebox && r.card.id !== 'free_box'; })());
  T('auto 4 coin without card → lands in free section', (()=>{ const r = codisFinCreateReward({ name:'تجربة اربعة', kind:'time', minutes:8 }); return r.ok && r.card.free && r.item.freebox; })());
  T('auto 10 coin without card → NOT free', (()=>{ const r = codisFinCreateReward({ name:'تجربة عشرة', kind:'time', minutes:20, force:true }); const ok = r.ok && !r.item.freebox; if(r.ok) data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.id !== r.item.id); return ok; })());
  data.settings.rewardItems = data.settings.rewardItems.filter(x=>!(x.freebox && x.name === 'تجربة اربعة'));
  T('five items stored', data.settings.rewardItems.filter(x=>x.freebox).length === 5);

  /* ===== الحفظ والاسترجاع وبعد إعادة التحميل (تطبيع) ===== */
  const clone = JSON.parse(JSON.stringify(data)); normalizeData(clone, false);
  const fb = clone.settings.rewardItems.filter(x=>x.freebox);
  T('normalize keeps all 5 + card + sticker', fb.length === 5 && fb.every(x=>x.fin && x.fin.card === 'free_box' && x.weight === 0) && fb.some(x=>x.stickerId === 'pizza'));
  T('normalize twice is stable', (()=>{ const a = JSON.stringify(clone.settings.rewardItems); normalizeData(clone, false); return a === JSON.stringify(clone.settings.rewardItems); })());
  T('normalize drops orphan freebox flag (no fin)', (()=>{ const d = JSON.parse(JSON.stringify(data)); d.settings.rewardItems.push({ id:'orph', name:'يتيم', room:'tasks', rarity:'C', weight:10, enabled:true, freebox:true }); normalizeData(d, false); const o = d.settings.rewardItems.find(x=>x.id === 'orph'); return o && !o.freebox; })());
  T('normalize tolerates garbage freeBox state', [null, 5, 'x', [], { at:'zzz', n:'q' }, { at:12, n:-4 }].every(v=>{ const d = JSON.parse(JSON.stringify(data)); d.economyState.freeBox = v; normalizeData(d, false); return d.economyState.freeBox && d.economyState.freeBox.at === '' && d.economyState.freeBox.n === 0; }));

  /* ===== العزل عن النتائج اليومية والبكجات والقوائم ===== */
  const fbIds = data.settings.rewardItems.filter(x=>x.freebox).map(x=>x.id);
  let leaked = 0; for(let i = 0; i < 400; i++){ const r = CodisRewardEngine.roll('tasks', 'daily'); if(r.reward && fbIds.indexOf(r.reward.id) !== -1) leaked++; }
  T('400 daily rolls never return a free reward', leaked === 0, leaked);
  const wasFixed = data.settings.rewardItems.filter(x=>!x.freebox && x.room === 'tasks').length;
  T('CodisBoxes.pool excludes free items', !CodisBoxes.pool().some(x=>fbIds.indexOf(x.id) !== -1));
  rpKind = 'reward'; rpuView = 'daily'; settingsDailyRoom = 'tasks'; settingsRoom = 'tasks'; econRenderRewards();
  const html = id=>(document.getElementById(id) || {}).innerHTML || '';
  T('free items NOT in daily list', fbIds.every(id=>html('reward-list').indexOf(id) === -1) && html('reward-list-weekly').indexOf('free') === -1);
  T('free items in free list', fbIds.every(id=>html('free-list').indexOf('data-id="' + id + '"') !== -1));
  const sec = document.getElementById('rpu-r-free'), blk = document.getElementById('rp-reward-block');
  T('free section is the LAST section of the reward block', sec && blk && blk.lastElementChild === sec && sec.closest('.room-sel') === null);
  T('free section not inside a room list', !document.getElementById('reward-list').contains(sec) && !document.getElementById('punish-list').contains(sec));
  T('section title', (document.getElementById('rpu-r-free-h') || {}).textContent === 'مكافآت الصندوق المجاني');
  rpuView = 'all'; econRenderRewards(); T('"all" view omits free items', fbIds.every(id=>html('rpu-all-list').indexOf(id) === -1));
  rpuView = 'daily'; econRenderRewards();
  T('tile tag says free box', html('free-list').indexOf('صندوق مجاني') !== -1);

  /* ===== التفعيل/التعطيل/التعديل/الحذف/الستيكر ===== */
  const one = data.settings.rewardItems.find(x=>x.freebox && x.name === 'شاي اربعة');
  econToggleReward(one.id); T('disable', data.settings.rewardItems.find(x=>x.id === one.id).enabled === false && !CodisFreeBox.pool().some(x=>x.id === one.id));
  econToggleReward(one.id); T('enable', CodisFreeBox.pool().some(x=>x.id === one.id));
  econEdit(one.id); const nameEl = document.getElementById('eco-edit-r-name');
  T('editor opens inside free list', !!nameEl && document.getElementById('free-list').contains(nameEl));
  if(nameEl){ nameEl.value = 'شاي اربعة معدّل'; const st = document.getElementById('eco-edit-r-sticker'); if(st) st.value = 'tea'; econSaveReward(one.id); }
  const after = data.settings.rewardItems.find(x=>x.id === one.id);
  T('edit saved + stays free (flag/card/room/weight)', after.name === 'شاي اربعة معدّل' && after.freebox === true && after.fin.card === 'free_box' && after.weight === 0 && after.room === 'tasks', JSON.stringify(after).slice(0, 200));
  T('sticker saved', after.stickerId === 'tea', after.stickerId);
  window.codisConfirm = async ()=>true;
  await econDeleteReward(one.id); T('delete', !data.settings.rewardItems.some(x=>x.id === one.id) && !CodisFreeBox.pool().some(x=>x.id === one.id));

  /* ===== الشراء الفردي من المتجر (ليس مرتبطاً بقيمة الكرت) ===== */
  const buyable = data.settings.rewardItems.find(x=>x.freebox && x.name === 'شي خمسة');
  T('store rows include free reward', econStoreCardRows().some(r=>r.it && r.it.id === buyable.id));
  const price = CodisEconomy.storePrice(buyable), coin = econEffCoin(buyable, econRarityById(buyable.rarity));
  T('store price is separate from card value', price > 0 && price !== coin, price + ' vs ' + coin);
  const bal0 = data.wallet.balance; data.wallet.balance = bal0 + price + 5;
  const invN = data.inventory.items.length, pr = CodisEconomy.purchase(buyable.id);
  T('individual purchase works (price deducted)', pr.ok && data.inventory.items.length === invN + 1 && data.inventory.items[data.inventory.items.length - 1].source === 'store', JSON.stringify(pr).slice(0, 100));
  data.wallet.balance = bal0;

  /* ===== الصندوق ===== */
  data.economyState.freeBox = { at:'', n:0 };
  data.inventory.items = data.inventory.items.filter(x=>x.source !== 'free');
  let s = CodisFreeBox.status();
  T('first time: ready', s.ready && s.poolN === 4, JSON.stringify(s));
  econRenderStore(); T('store shows free box tile when ready', !!document.getElementById('eco-free') && !!document.getElementById('fb-card'));
  const balB = data.wallet.balance, txB = data.wallet.transactions.length, silverB = JSON.stringify(data.wallet.silver);
  const invB = data.inventory.items.length;
  const r1 = CodisFreeBox.claim();
  T('claim ok', r1.ok && r1.owned && r1.owned.source === 'free', JSON.stringify(r1).slice(0, 160));
  T('exactly one item added with reward data', data.inventory.items.length === invB + 1 && r1.owned.rewardId === r1.item.id && r1.owned.name === r1.item.name && r1.owned.coinValue === r1.coin && r1.owned.stickerId === r1.item.stickerId);
  T('no coins deducted/added (balance + ledger + silver)', data.wallet.balance === balB && data.wallet.transactions.length === txB && JSON.stringify(data.wallet.silver) === silverB);
  T('claim time stored', data.economyState.freeBox.at === r1.at && data.economyState.freeBox.n === 1);
  s = CodisFreeBox.status(); T('not ready right after claim', !s.ready && s.waitMs > 23.9 * 3600e3, s.waitMs);
  econRenderStore(); T('tile disappears immediately', !document.getElementById('eco-free'));
  const r2 = CodisFreeBox.claim(); T('second claim refused (wait)', !r2.ok && r2.reason === 'wait' && data.inventory.items.length === invB + 1);
  T('rapid double call cannot create two', (()=>{ const a = CodisFreeBox.claim(), b = CodisFreeBox.claim(); return !a.ok && !b.ok && data.inventory.items.filter(x=>x.source === 'free').length === 1; })());
  T('owned item shows in inventory with free source label', econSourceLabel(r1.owned) === 'من الصندوق المجاني' && CodisInventory.owned().some(x=>x.uid === r1.owned.uid));
  /* إعادة تحميل: الحالة تبقى */
  const re = JSON.parse(JSON.stringify(data)); normalizeData(re, false);
  T('state survives reload normalize (at/n/inventory source)', re.economyState.freeBox.at === r1.at && re.economyState.freeBox.n === 1 && re.inventory.items.some(x=>x.source === 'free'));
  /* 24 ساعة من وقت المطالبة (لا يوم تقويمي) */
  let sq = 0; const ago = h=>new Date(Date.now() - h * 3600e3 - (++sq) * 1000).toISOString(), inv1 = data.inventory.items.find(x=>x.source === 'free');
  data.economyState.freeBox.at = ago(23.9); inv1.acquiredAt = ago(23.9); T('23.9h → still locked', !CodisFreeBox.status().ready);
  data.economyState.freeBox.at = ago(24.05); inv1.acquiredAt = ago(24.05); T('24.05h → returns', CodisFreeBox.status().ready);
  data.economyState.freeBox.at = ago(30); inv1.acquiredAt = ago(1); T('merge protection: newest free item in inventory counts', !CodisFreeBox.status().ready);
  data.economyState.freeBox.at = new Date(Date.now() + 3 * 86400e3).toISOString(); inv1.acquiredAt = data.economyState.freeBox.at; T('future clock never locks > 24h', CodisFreeBox.status().waitMs <= 86400e3);
  data.economyState.freeBox.at = ago(30); inv1.acquiredAt = ago(30);
  /* مطالبة ثانية بعد 24 ساعة */
  const r3 = CodisFreeBox.claim(); T('claim again after 24h', r3.ok && r3.owned.uid !== r1.owned.uid && data.economyState.freeBox.n === 2);
  /* فشل الحفظ لا يستهلك الفرصة */
  data.economyState.freeBox.at = ago(30); inv1.acquiredAt = ago(30); data.inventory.items.forEach(x=>{ if(x.source === 'free') x.acquiredAt = ago(30); });
  const nFree = data.inventory.items.filter(x=>x.source === 'free').length, atBefore = data.economyState.freeBox.at;
  codisSaveSuspended = 'fail'; const rf = CodisFreeBox.claim(); codisSaveSuspended = false;
  T('failed save → refused + chance not consumed', !rf.ok && rf.reason === 'save' && data.economyState.freeBox.at === atBefore && data.inventory.items.filter(x=>x.source === 'free').length === nFree && CodisFreeBox.status().ready, JSON.stringify(rf));
  /* بلا مكافآت مؤهلة */
  const hold = data.settings.rewardItems.filter(x=>x.freebox); hold.forEach(x=>{ x.enabled = false; });
  const rE = CodisFreeBox.claim(); T('no eligible rewards → refused, nothing consumed', !rE.ok && rE.reason === 'empty' && data.economyState.freeBox.at === atBefore && data.inventory.items.filter(x=>x.source === 'free').length === nFree);
  econRenderStore(); T('tile still shown when ready (message on press)', !!document.getElementById('fb-card'));
  hold.forEach(x=>{ x.enabled = true; });
  /* مكافأة خارج 1–10 بعد تغيير السعر لا تدخل السحب */
  hold[0].fin.oor = true; T('out-of-range (oor) excluded from draw', !CodisFreeBox.pool().some(x=>x.id === hold[0].id)); delete hold[0].fin.oor;

  /* ===== السحب متساوٍ ===== */
  data.settings.rewardItems.forEach(x=>{ if(x.freebox) x.enabled = false; });
  const vals = [1, 4, 5, 7, 10], ids = [];
  vals.forEach(v=>{ const r = codisFinCreateReward({ name:'متساوية ' + v, kind:'time', minutes:v * 2, cardId:'free_box' }); ids.push(r.item.id); });
  T('pool is the 5 enabled', CodisFreeBox.pool().length === 5);
  const cnt = {}; ids.forEach(i=>{ cnt[i] = 0; }); const N = 20000;
  for(let i = 0; i < N; i++){ const p = CodisRewardEngine.pick(CodisFreeBox.pool(), ()=>1); cnt[p.id]++; }
  T('uniform ±6% over 20000 draws', ids.every(i=>Math.abs(cnt[i] - N / 5) < N / 5 * 0.06), JSON.stringify(Object.values(cnt)));
  T('independent of value (10-coin ≈ 1-coin)', Math.abs(cnt[ids[0]] - cnt[ids[4]]) < N / 5 * 0.1);
  let k = 0; CodisRewardEngine.setRng(()=>[0, .21, .41, .61, .81, .999][k++ % 6]);
  const seen = []; for(let i = 0; i < 5; i++){ data.economyState.freeBox.at = ago(30); data.inventory.items.forEach(x=>{ if(x.source === 'free') x.acquiredAt = ago(30); }); const r = CodisFreeBox.claim(); seen.push(r.ok ? r.item.id : 'x'); }
  CodisRewardEngine.setRng(null);
  T('seeded rng hits each of 5 records once (by sorted id)', new Set(seen).size === 5, seen.join());

  /* ===== بطاقة خاصة بالصندوق المجاني ===== */
  { const fi = data.settings.rewardItems.find(x=>x.freebox && x.enabled), ni = data.settings.rewardItems.find(x=>!x.freebox && x.room === 'tasks'), rr = econRarityById(fi.rarity);
    const fh = econStoreFaceHtml(fi, rr, { price:3 }), nh = econStoreFaceHtml(ni, econRarityById(ni.rarity), { price:3 });
    T('free reward uses its OWN card face (fgc), not the daily card', /class=\"rwc scx scx-free fgc/.test(fh) && fh.indexOf('rwc-d') === -1, fh.slice(0, 120));
    T('normal daily reward keeps the daily card', nh.indexOf('rwc-d') !== -1 && nh.indexOf('fgc') === -1);
    T('owned copy (inventory shape) also gets the free card', /scx-free/.test(econStoreFaceHtml({ id:'u', room:'tasks', name:'x', rewardId:null, fin:fi.fin, source:'free' }, rr, {})));
    T('legacy codisRewardCardHtml path too', /scx-free/.test(codisRewardCardHtml({ kind:'reward', scope:'daily', room:'tasks', rarityTone:'c', item:'x', fin:fi.fin }, { plain:true })));
    econRenderStore(); const tiles = [].slice.call(document.querySelectorAll('#eco-store-body .st-tile')).filter(t=>t.dataset.id === fi.id);
    T('store tile renders the free card', tiles.length === 1 && !!tiles[0].querySelector('.fgc') && /الصندوق المجاني/.test(tiles[0].textContent)); }

  /* ===== مشهد الفتح (واجهة) ===== */
  data.economyState.freeBox.at = ago(30); data.inventory.items.forEach(x=>{ if(x.source === 'free') x.acquiredAt = ago(30); });
  econRenderStore(); const card = document.getElementById('fb-card'); T('tile present for UI test', !!card);
  const nBefore = data.inventory.items.filter(x=>x.source === 'free').length;
  const toasts = []; const _st = window.showToast; window.showToast = (m)=>{ toasts.push(m); };
  codisFreeBoxOpen(); codisFreeBoxOpen(); codisFreeBoxOpen(); window.showToast = _st;
  T('overlay opened once; 3 rapid presses = 1 claim', document.querySelectorAll('#fb-ov').length === 1 && data.inventory.items.filter(x=>x.source === 'free').length === nBefore + 1, toasts.join('|') + ' n=' + document.querySelectorAll('#fb-ov').length + ' inv=' + (data.inventory.items.filter(x=>x.source === 'free').length - nBefore));
  await new Promise(r=>setTimeout(r, 1500));
  const rev = document.getElementById('fb-rev'); T('reward revealed with name + value', !!rev && !rev.hidden && rev.querySelector('.fb-name').textContent.length > 0 && !!rev.querySelector('.fb-val .eco-coin') && !!rev.querySelector('.store-art'), 'ov=' + !!document.getElementById('fb-ov') + ' st=' + JSON.stringify(CodisFreeBox.status()));
  T('reveal says no deduction', !!rev && /بلا أي خصم/.test(rev.textContent));
  codisFreeBoxClose(); T('closed + tile gone', !document.getElementById('fb-ov') && !document.getElementById('eco-free'));
  /* مظهر + هاتف: لا تجاوز أفقي */
  T('no horizontal overflow', document.documentElement.scrollWidth <= innerWidth + 1);

  /* ===== حدود المستخدم عبر CodisLimits ===== */
  T('cooldown registered in CodisLimits', (()=>{ try{ return JSON.stringify(CodisLimits).length > 0 && /freebox\.cooldown/.test(document.documentElement.innerHTML.slice(0, 1) + CodisFreeBox.status.toString()); }catch(e){ return false; } })());

  /* ===== استعادة ===== */
  data.settings.rewardItems = JSON.parse(keepItems); data.inventory = JSON.parse(keepInv); data.economyState = JSON.parse(keepEco); data.wallet = JSON.parse(keepWallet);
  try{ saveData(); }catch(e){}
  const bad = out.filter(x=>!x.ok);
  return { passed:out.length - bad.length, failed:bad.length, results:out };
})()
