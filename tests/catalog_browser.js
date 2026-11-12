/* CODIS-V35 catalog test — evaluate in the page (guest). Mutates local test data only.
   TEST=tests/catalog_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1 */
(async function(){
  /* 3.30.0: نموذج الإضافة اليدوي أُزيل من الواجهة (الإضافة الجديدة تلقائية فقط)؛ الاختبار يركّبه كأداة لاختبار المحرر/الستيكر/الحفظ */
  const legacyAdd = (period)=>{ let h = document.getElementById('reward-add-box'); if(!h){ h = document.createElement('div'); h.id = 'reward-add-box'; h.style.cssText = 'position:fixed;left:-9999px;top:0'; document.body.appendChild(h); } h.innerHTML = econRewardEditor('eco-new-r', null) + '<button type="button" class="btn btn-primary eco-full" onclick="econAddReward()">إضافة المكافأة</button>'; h.dataset.ready = '1'; const sel = document.getElementById('eco-new-r-room'); sel.value = period === 'daily' ? settingsDailyRoom : period; econRewardRarityChanged('eco-new-r'); };
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : String(i) });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const L = ()=>data.outcomeLedger, key = (...a)=>a.join('|'), bal = ()=>CodisWallet.balance();
  const ri = id=>data.settings.rewardItems.find(x=>x.id === id), pi = id=>data.settings.punishItems.find(x=>x.id === id);
  const mkH = (id, imp)=>({ id:id, text:'حدثية ' + id, type:'H', importance:imp, createdAt:dateKeyOffset(-3), log:{}, occurrences:[], lastOccurrence:null, bestDays:0, monthlyMilestones:{}, resists:{} });
  const renorm = ()=>{ const copy = JSON.parse(JSON.stringify(data.settings)); econNormalizeItems(copy); return copy; };
  codisConfirm = ()=>Promise.resolve(true);
  const D = codisFixedDefs();

  /* ---- structure ---- */
  T('13 catalog cards exist with ids', D.rewards.length === 7 && D.punish.length === 6 && D.rewards.every(d=>ri(d.id)) && D.punish.every(d=>pi(d.id)));
  T('cards carry group/period/importance fields', ri('fx_ms_important').cardGroup === 'station' && ri('fx_ms_important').stationPeriod === '30d' && ri('fx_ms_important').habitImp === 'important' && ri('fx_rs_critical').cardGroup === 'event' && ri('fx_station7').stationPeriod === '7d' && pi('fxp_ev_critical').cardGroup === 'event' && pi('fxp_st7_low').cardGroup === 'station');
  T('exactly 3 monthly-station + 1 weekly-station + 3 event reward cards', D.rewards.filter(d=>d.tag === 'monthlyEvent').length === 3 && D.rewards.filter(d=>d.tag === 'station7').length === 1 && D.rewards.filter(d=>d.tag === 'resist').length === 3);
  T('values preserved', ri('fx_station7').fixedCoin === 12.5 && ri('fx_ms_normal').fixedCoin === 75 && ri('fx_ms_important').fixedCoin === 100 && ri('fx_ms_critical').fixedCoin === 200);
  T('cards stay out of random pools/boxes', !CodisBoxes.pool().some(x=>x.fixed) && ![].concat(D.rewards).some(d=>CodisEconomy && CodisBoxes.pool().some(p=>p.id === d.id)));

  /* ---- user edits survive reload/normalize, no default names re-forced, no duplicates ---- */
  ri('fx_rs_normal').name = 'قاومتُ وانتصرت'; ri('fx_rs_normal').stickerId = codisStickerIdOk('pizza') || null; pi('fxp_ev_normal').enabled = false; pi('fxp_ev_normal').name = 'عقوبة مخصصة';
  const stk = ri('fx_rs_normal').stickerId;
  let c = renorm();
  const cr = id=>c.rewardItems.find(x=>x.id === id), cp = id=>c.punishItems.find(x=>x.id === id);
  T('renamed reward keeps name after normalize', cr('fx_rs_normal').name === 'قاومتُ وانتصرت');
  T('sticker survives normalize', cr('fx_rs_normal').stickerId === stk, stk);
  T('disabled + renamed penalty survive', cp('fxp_ev_normal').enabled === false && cp('fxp_ev_normal').name === 'عقوبة مخصصة');
  T('structure fields survive normalize', cr('fx_ms_critical').fixed && cr('fx_ms_critical').fixedCoin === 200 && cp('fxp_ev_critical').fixedCost === 750);
  c.rewardItems.push(JSON.parse(JSON.stringify(c.rewardItems.find(x=>x.id === 'fx_station7')))); econNormalizeItems(c);
  T('duplicate card collapses to one', c.rewardItems.filter(x=>x.id === 'fx_station7').length === 1);
  econNormalizeItems(c); econNormalizeItems(c);
  T('repeated normalization never duplicates', D.rewards.every(d=>c.rewardItems.filter(x=>x.id === d.id).length === 1) && D.punish.every(d=>c.punishItems.filter(x=>x.id === d.id).length === 1));
  T('migration flag set once', data.settings.catalogV35 === 1);
  { const w = JSON.parse(JSON.stringify(data.settings)); w.rewardItems = w.rewardItems.filter(x=>x.id !== 'fx_rs_critical'); econNormalizeItems(w); T('deleted card is not re-forced on normalize', !w.rewardItems.some(x=>x.id === 'fx_rs_critical')); }
  { const o = JSON.parse(JSON.stringify(data.settings)); delete o.catalogV35; o.rewardItems.find(x=>x.id === 'fx_ms_normal').name = 'مكافأة حدثية عادية محسّنة'; o.rewardItems.find(x=>x.id === 'fx_ms_important').name = 'اسمي'; econNormalizeItems(o);
    T('migration renames only the old default name', o.rewardItems.find(x=>x.id === 'fx_ms_normal').name === 'مكافأة المحطة الشهرية — عادية' && o.rewardItems.find(x=>x.id === 'fx_ms_important').name === 'اسمي'); }

  /* ---- settings UI: two rooms, add flow ---- */
  rpOpenHub('reward'); await sleep(50);
  const rooms = Array.from(document.querySelectorAll('#rpu-r-daily .room-sel .arch-filter-btn')).map(b=>b.dataset.room);
  T('discipline room is its own separate room', rooms.join() === 'tasks,learn,habits', rooms.join());
  setSettingsRoom('habits'); await sleep(30);
  T('discipline room = a normal list with the 7 cards, importance chips, no rarity badge', document.querySelectorAll('#reward-list .eco-item').length >= 7 && document.querySelectorAll('#reward-list .cat-chip').length >= 7 && !document.querySelector('#reward-list .rar-badge, #reward-list [class*="rbadge"]'));
  setSettingsRoom('tasks'); T('operations list has none of the discipline cards', !document.querySelector('#reward-list .cat-chip'));
  setSettingsRoom('habits');
  ri('fx_rs_critical') || 0;
  data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.id !== 'fx_rs_critical'); econRenderAll();
  legacyAdd('daily'); await sleep(30);
  const g = id=>document.getElementById('eco-new-r-' + id);
  T('place picker visible for discipline room', g('place-wrap') && !g('place-wrap').hidden);
  T('rarity hidden + room switcher hidden in discipline add form', g('rarity-wrap').style.display === 'none' && getComputedStyle(g('room').closest('.eco-field')).display === 'none');
  g('place').value = 'event'; codisV35PlaceSync('eco-new-r', 'reward');
  T('importance picker shows for event, rarity hidden', !g('imp-wrap').hidden && g('sp-wrap').hidden);
  g('place').value = 'station'; g('sp').value = '30d'; codisV35PlaceSync('eco-new-r', 'reward');
  T('station+monthly shows importance', !g('sp-wrap').hidden && !g('imp-wrap').hidden);
  g('sp').value = '7d'; codisV35PlaceSync('eco-new-r', 'reward'); T('station weekly hides importance', g('imp-wrap').hidden);
  g('place').value = 'event'; g('imp').value = 'critical'; codisV35PlaceSync('eco-new-r', 'reward');
  g('name').value = 'حرجة جديدة'; g('sticker').value = codisStickerIdOk('pizza') || '';
  econAddReward(); await sleep(30);
  T('added event card recreates canonical id with chosen name', ri('fx_rs_critical') && ri('fx_rs_critical').name === 'حرجة جديدة' && ri('fx_rs_critical').fixedCoin === 125 && ri('fx_rs_critical').room === 'habits');
  legacyAdd('daily'); g('place').value = 'event'; g('imp').value = 'critical'; codisV35PlaceSync('eco-new-r', 'reward'); g('name').value = 'نسخة ثانية'; econAddReward(); await sleep(20);
  T('adding an existing slot never duplicates', data.settings.rewardItems.filter(x=>x.id === 'fx_rs_critical').length === 1 && ri('fx_rs_critical').name === 'حرجة جديدة');
  rpuAddDone('reward');
  /* Ostaz room = regular rewards only, no catalog UI */
  rpuAddDone('reward'); setSettingsRoom('learn'); legacyAdd('daily'); await sleep(20); T('Ostaz room has no catalog/place picker', document.getElementById('reward-cat').hidden && document.getElementById('eco-new-r-place-wrap').hidden); g('name').value = 'مكافأة أستاذ عادية'; econAddReward(); await sleep(20); setSettingsRoom('habits');
  { const r = data.settings.rewardItems.find(x=>x.name === 'مكافأة أستاذ عادية'); T('regular Ostaz reward unaffected', r && r.room === 'learn' && !r.fixed && r.weight > 0); }
  /* edit / toggle / delete */
  econEdit('fx_rs_normal'); await sleep(20);
  { const f = id=>document.getElementById('eco-edit-r-' + id);
    T('discipline editor = same editor as other rooms (name+sticker+switch) with classification instead of rarity', f('name') && f('sticker') && f('on') && f('place') && f('rarity-wrap').style.display === 'none' && getComputedStyle(f('room').closest('.eco-field')).display === 'none' && f('place').value === 'event' && f('imp').value === 'normal');
    T('closed tiles have one tap target only (no extra buttons)', !document.querySelector('#reward-list [onclick*="Pv"]') && [...document.querySelectorAll('#reward-list .rpt:not(.is-editing)')].every(x=>x.querySelectorAll('button').length === 1));
    T('opened tile = full-width with toggle/close/delete + editor', document.querySelector('#reward-list .rpt.is-editing .eco-item-acts') && document.querySelectorAll('#reward-list .rpt.is-editing .eco-item-acts > button').length === 3 && getComputedStyle(document.querySelector('#reward-list .rpt.is-editing')).gridColumnStart !== 'auto');
    const pv = codisStickerPreviewHtml('eco-edit-r', codisStickerIdOk('pizza') || 'pizza');
    T('sticker picker preview = the real discipline card (no rarity card)', pv.indexOf('scx') > -1 && pv.indexOf('rwc-c') > -1 && pv.indexOf('شائعة') === -1);
    f('name').value = 'اسم معدّل'; econSaveReward('fx_rs_normal'); await sleep(20);
    T('edited special card saved without touching value/room', ri('fx_rs_normal').name === 'اسم معدّل' && ri('fx_rs_normal').fixedCoin === 18.75 && ri('fx_rs_normal').room === 'habits'); }
  { const keepImp = ri('fx_rs_important'); data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.id !== 'fx_rs_important'); econEditing = 'fx_rs_normal'; econRenderRewards();
    const f = id=>document.getElementById('eco-edit-r-' + id); f('imp').value = 'important'; codisV35PlaceSync('eco-edit-r', 'reward'); econSaveReward('fx_rs_normal'); await sleep(20);
    T('changing classification on edit moves the card to that slot (like changing rarity)', !ri('fx_rs_normal') && ri('fx_rs_important') && ri('fx_rs_important').name === 'اسم معدّل' && ri('fx_rs_important').fixedCoin === 37.5);
    econEditing = 'fx_rs_important'; econRenderRewards(); f('imp').value = 'critical'; codisV35PlaceSync('eco-edit-r', 'reward'); econSaveReward('fx_rs_important'); await sleep(20);
    T('moving onto an occupied slot is refused', ri('fx_rs_important') && ri('fx_rs_critical').name === 'حرجة جديدة');
    econEditing = null; ri('fx_rs_important').id = 'fx_rs_normal'; data.settings.rewardItems.push(keepImp); econNormalizeItems(data.settings); econRenderRewards(); }
  econToggleReward('fx_ms_normal'); T('toggle disables card', ri('fx_ms_normal').enabled === false); econToggleReward('fx_ms_normal'); T('toggle re-enables', ri('fx_ms_normal').enabled === true);
  await econDeleteReward('fx_ms_important'); T('delete (confirmed) removes card', !ri('fx_ms_important')); codisV35QuickAdd('reward', 'fx_ms_important'); T('slot can be re-added', !!ri('fx_ms_important') && ri('fx_ms_important').fixedCoin === 100);
  { const keep = data.settings.rewardItems.slice(); data.settings.rewardItems = keep.filter(x=>x.room !== 'habits'); econRenderRewards(); T('empty discipline room shows the standard empty message', /ماكو مكافآت/.test(document.getElementById('reward-list').textContent)); data.settings.rewardItems = keep; econRenderRewards(); }

  /* ---- penalty settings ---- */
  rpOpenHub('punish'); setSettingsRoom('habits'); await sleep(30);
  T('penalty list for discipline room (station 3 + event 3)', document.querySelectorAll('#punish-list .eco-item').length >= 6);
  rpuAdd('punish', 'daily'); await sleep(20);
  const p = id=>document.getElementById('eco-new-p-' + id);
  T('penalty place picker visible', p('place-wrap') && !p('place-wrap').hidden);
  data.settings.punishItems = data.settings.punishItems.filter(x=>x.id !== 'fxp_ev_important'); econRenderAll(); rpuAdd('punish', 'daily');
  p('place').value = 'event'; p('imp').value = 'important'; codisV35PlaceSync('eco-new-p', 'punish'); p('name').value = 'حدثية مهمة جديدة'; econAddPunish(); await sleep(20);
  T('added event penalty = canonical slot, cost 225', pi('fxp_ev_important') && pi('fxp_ev_important').name === 'حدثية مهمة جديدة' && econPenaltyCost(pi('fxp_ev_important')) === 225);
  rpuAdd('punish', 'daily'); p('place').value = 'station'; p('sev').value = 'HIGH'; codisV35PlaceSync('eco-new-p', 'punish'); p('name').value = 'تكرار'; econAddPunish(); await sleep(20);
  T('existing station penalty not duplicated', data.settings.punishItems.filter(x=>x.id === 'fxp_st7_high').length === 1);
  rpuAddDone('punish');
  econEdit('fxp_ev_important'); econRenderPunish(); { const f = id=>document.getElementById('eco-edit-p-' + id); T('discipline penalty editor = same editor, event hides severity', f('name') && f('on') && f('place').value === 'event' && getComputedStyle(f('sev').closest('.eco-field')).display === 'none'); f('name').value = 'اسم مختلف'; econSavePunish('fxp_ev_important'); T('penalty rename saved', pi('fxp_ev_important').name === 'اسم مختلف'); }
  T('no preview button on penalty rows', !document.querySelector('#punish-list [onclick*="Pv"]'));

  econTogglePunish('fxp_st7_low'); T('penalty toggle', pi('fxp_st7_low').enabled === false); econTogglePunish('fxp_st7_low');
  await econDeletePunish('fxp_ev_critical'); T('penalty delete', !pi('fxp_ev_critical')); codisV35QuickAdd('punish', 'fxp_ev_critical'); T('penalty slot re-add', econPenaltyCost(pi('fxp_ev_critical')) === 750);

  /* ---- separate period pages + «الكل» ---- */
  { const pg = document.getElementById('settings-page-rewards'), vis = sel=>[...document.querySelectorAll(sel)].filter(x=>getComputedStyle(x).display !== 'none' && !x.closest('[hidden]') && getComputedStyle(x.closest('.rpu-block') || x).display !== 'none');
    const dupIds = ()=>{ const s = {}; let d = 0; document.querySelectorAll('[id]').forEach(e=>{ if(s[e.id]) d++; s[e.id] = 1; }); return d; };
    rpOpenHub('reward'); await sleep(50);
    T('hub opens on the daily page only', pg.dataset.view === 'daily' && vis('#rp-reward-block .rpu-sec:not(.rpu-free)').map(s=>s.dataset.period).join() === 'daily');   /* CODIS-V44: قسم الصندوق المجاني يلي صفحة اليومي بآخرها */
    setSettingsPeriod('weekly'); await sleep(20); T('weekly = its own page', vis('#rp-reward-block .rpu-sec').map(s=>s.dataset.period).join() === 'weekly');
    setSettingsPeriod('monthly'); await sleep(20); T('monthly = its own page with the month card', vis('#rp-reward-block .rpu-sec').map(s=>s.dataset.period).join() === 'monthly' && !!vis('#rpu-r-monthly [data-month] button').length);
    /* typed text survives switching pages */
    setSettingsPeriod('daily'); setSettingsRoom('tasks'); legacyAdd('daily'); document.getElementById('eco-new-r-name').value = 'نص محفوظ'; setSettingsPeriod('weekly'); setSettingsPeriod('daily');
    T('add-form text survives page switches', document.getElementById('eco-new-r-name').value === 'نص محفوظ'); rpuAddDone('reward');
    setSettingsPeriod('all'); await sleep(30);
    const grps = [...document.querySelectorAll('#rpu-all-list .rpu-all-grp')].map(g=>g.dataset.g);
    T('«كل المكافآت» = all rewards grouped tasks→learn→habits→weekly→monthly', grps.join() === ['tasks', 'learn', 'habits', 'weekly', 'monthly'].filter(g=>data.settings.rewardItems.some(x=>x.room === g)).join(), grps.join());
    T('all page shows every reward exactly once', document.querySelectorAll('#rpu-all-list .rpt').length === data.settings.rewardItems.length && new Set([...document.querySelectorAll('#rpu-all-list .rpt')].map(x=>x.querySelector('.rpt-face').getAttribute('onclick'))).size === data.settings.rewardItems.length);
    T('all page: no group titles, no add buttons, period sections hidden', !document.querySelector('#rpu-all-list h3, #rpu-all-list .rpu-h') && !vis('#settings-page-rewards .rpu-add').length && !vis('#rp-reward-block .rpu-sec').length);
    T('label switches with kind', document.getElementById('rpu-all-t').textContent === 'كل المكافآت');
    T('no duplicate ids on the all page', dupIds() === 0, dupIds());
    const q = document.getElementById('rpu-q'); q.value = 'حدثية'; rpuFind();
    const shown = [...document.querySelectorAll('#rpu-all-list .rpt')].filter(x=>!x.hidden);
    T('search finds across every group (discipline included)', shown.length > 0 && shown.every(x=>x.dataset.name.indexOf(codisNormText('حدثية')) > -1) && shown.some(x=>x.closest('.rpu-all-grp').dataset.g === 'habits'));
    T('groups without matches hide', [...document.querySelectorAll('#rpu-all-list .rpu-all-grp')].every(g=>g.hidden === !g.querySelector('.rpt:not([hidden])')));
    q.value = 'zzzz'; rpuFind(); T('no-match message', /ما لكينا/.test(document.getElementById('rpu-all-list').textContent));
    rpuFindClear(); T('clear restores everything', ![...document.querySelectorAll('#rpu-all-list .rpt')].some(x=>x.hidden) && !document.querySelector('#rpu-all-list .rpu-nomatch'));
    econEdit('fx_rs_normal'); await sleep(20); T('editing inside all page works (one editor, no dup ids)', document.querySelectorAll('#eco-edit-r-name').length === 1 && dupIds() === 0); econEdit('fx_rs_normal');
    rpOpenHub('punish'); setSettingsPeriod('all'); await sleep(30);
    T('«كل العقوبات» shows penalties only', document.getElementById('rpu-all-t').textContent === 'كل العقوبات' && document.querySelectorAll('#rpu-all-list .rpt').length === data.settings.punishItems.length);
    setSettingsPeriod('daily'); rpOpenHub('reward'); }
  /* ---- single price source ---- */
  const exp = { fxp_st7_low:31.25, fxp_st7_med:62.5, fxp_st7_high:125, fxp_ev_normal:112.5, fxp_ev_important:225, fxp_ev_critical:750 };
  T('penalty settings costs match table', Object.keys(exp).every(id=>econPenaltyCost(pi(id)) === exp[id]), JSON.stringify(Object.keys(exp).map(id=>econPenaltyCost(pi(id)))));
  T('pass price = station table', CodisPasses.price({ scope:'habit', severity:'LOW' }) === 31.25 && CodisPasses.price({ scope:'habit', severity:'MEDIUM' }) === 62.5 && CodisPasses.price({ scope:'habit', severity:'HIGH' }) === 125);
  T('regular penalty formula untouched', econBypassFor('MEDIUM', 'daily') === 135 && CodisPasses.price({ scope:'daily', severity:'MEDIUM' }) === 135);

  /* ---- outcomes use the matching catalog card (name/sticker/value), shown price = deducted ---- */
  pi('fxp_ev_normal').enabled = true; ri('fx_rs_normal').enabled = true; ri('fx_rs_normal').name = 'مقاومة مسمّاة'; ri('fx_rs_normal').stickerId = codisStickerIdOk('pizza') || null;
  const hN = mkH('c_n', 'normal'), hC = mkH('c_c', 'critical'); data.habits.quit.push(hN, hC);
  resistEventHabit('c_n'); await sleep(30); resistEventHabit('c_c'); await sleep(30);
  const eN = L()[key('habit', 'c_n', 'rs:' + todayKey(), 'reward')], eC = L()[key('habit', 'c_c', 'rs:' + todayKey(), 'reward')];
  T('resist uses importance-matched card (normal)', eN && eN.fixedId === 'fx_rs_normal' && eN.item === 'مقاومة مسمّاة' && eN.coinValue === 18.75 && eN.stickerId === ri('fx_rs_normal').stickerId);
  T('resist uses importance-matched card (critical)', eC && eC.fixedId === 'fx_rs_critical' && eC.coinValue === 125 && eC.rarityTone && true);
  T('result card html has no rarity badge and keeps name', codisHabitSpecialCardHtml(eN).indexOf('مقاومة مسمّاة') > -1 && codisHabitSpecialCardHtml(eN).indexOf('rar-') === -1);
  if(ri('fx_rs_normal').stickerId) T('result card shows sticker', codisHabitSpecialCardHtml(eN).indexOf('rwc-stk') > -1);
  ri('fx_rs_important').enabled = false; const hI = mkH('c_i', 'important'); data.habits.quit.push(hI); resistEventHabit('c_i'); T('disabled card produces no outcome', !L()[key('habit', 'c_i', 'rs:' + todayKey(), 'reward')]);
  { const b = bal(), r = CodisEconomy.decideReward(eN.id, 'coins'); T('coin exchange = card value', r.ok && bal() === econAddC(b, 18.75)); }
  { const r = CodisEconomy.decideReward(eC.id, 'item'); const inv = r.owned; T('taking item → inventory with catalog id + sticker slot', r.ok && inv && inv.rewardId === 'fx_rs_critical');
    const face = econStoreFaceHtml({ name:inv.name, rewardId:inv.rewardId, stickerId:inv.stickerId }, econCfg().rarities[0], { label:inv.name });
    T('inventory face is the special card (no plain rarity card)', face.indexOf('scx') > -1 && face.indexOf('rwc-c') > -1);
    T('inventory tile resolves slot label', econPackTileHtml({ id:inv.uid, room:inv.room, name:inv.name, rewardId:inv.rewardId }, econCfg().rarities[0]).indexOf('scx') > -1); }

  /* ---- penalties: shown price = deducted ---- */
  { const hv = mkH('c_p', 'critical'); data.habits.quit.push(hv); await recordEventHabit('c_p'); const e = L()[key('habit', 'c_p', 'ev:' + todayKey(), 'punish')];
    T('event penalty entry cost 750 and noPass', e && e.bypassCost === 750 && e.noPass === true);
    CodisWallet.transact([], ()=>({ ok:!!CodisWallet.apply('ADMIN_ADJUSTMENT', 1000, 't', 'test', econUid('t')) }));
    CodisPasses.grant({ uid:'p_t1', scope:'habit', severity:'HIGH', tier:'bx1', sourceRef:'t' });
    T('habit pass cannot clear an event penalty', !CodisPasses.fits(CodisPasses.get('p_t1'), e) && CodisEconomy.usePassCard(e.id, 'p_t1').ok === false);
    const b = bal(), r = CodisEconomy.decidePenalty(e.id, 'bypass'); T('bypass deducts exactly displayed 750', r.ok && bal() === econAddC(b, -750));
    T('no second deduction', !CodisEconomy.decidePenalty(e.id, 'bypass').ok && bal() === econAddC(b, -750)); }
  { const cc = 'c_exec'; const ent = codisFixedOutcome(key('habit', cc, 'c7:x', 'punish'), 'punish', codisFixedById('fxp_st7_med'), {}).entry; const b = bal();
    T('station penalty entry 62.5', ent && ent.bypassCost === 62.5 && !ent.noPass);
    CodisPasses.grant({ uid:'p_t2', scope:'habit', severity:'LOW', tier:'bx1', sourceRef:'t' });
    T('LOW pass cannot clear MEDIUM station penalty', !CodisPasses.fits(CodisPasses.get('p_t2'), ent));
    CodisPasses.grant({ uid:'p_t3', scope:'daily', severity:'MEDIUM', tier:'bx1', sourceRef:'t' }); T('daily pass cannot clear habit penalty', !CodisPasses.fits(CodisPasses.get('p_t3'), ent));
    const x = CodisEconomy.decidePenalty(ent.id, 'execute'); T('executing deducts nothing', x.ok && bal() === b); }

  /* ---- store & purchase ---- */
  { const rows = econStoreCardRows().filter(r=>r.it && r.it.fixed); T('enabled catalog cards listed in store', rows.length >= 5);
    const it = ri('fx_ms_normal'), html = econStoreCardHtml(it, econCfg().rarities[0], 1e6, 0);
    T('store tile: special card, name, no rarity label', html.indexOf('scx') > -1 && html.indexOf(escapeHtml(it.name)) > -1 && html.indexOf('الفئة') > -1 && html.indexOf('شائعة') === -1);
    CodisWallet.transact([], ()=>({ ok:!!CodisWallet.apply('ADMIN_ADJUSTMENT', 500, 't', 'test', econUid('t')) }));
    const b = bal(), r = CodisEconomy.purchase('fx_ms_normal'); T('purchase deducts store price (84)', r.ok && r.price === 84 && bal() === econAddC(b, -84), r.price);
    T('purchased card in inventory with rewardId', r.owned && r.owned.rewardId === 'fx_ms_normal');
    const s7 = CodisEconomy.purchase('fx_station7'); T('weekly station price 12.5 (no markup)', s7.ok && s7.price === 12.5); }

  /* ---- reload simulation: full normalizeData round trip keeps everything ---- */
  { const raw = JSON.parse(JSON.stringify(data)); const keepNames = D.rewards.map(d=>(ri(d.id) || {}).name).join('|'); const norm = typeof normalizeData === 'function' ? normalizeData(raw) : null;
    const st = (norm || raw).settings; T('full normalize round trip keeps edited names', !norm || D.rewards.map(d=>((st.rewardItems.find(x=>x.id === d.id)) || {}).name).join('|') === keepNames);
    T('ledger entries untouched by normalize', !norm || Object.keys(L()).every(k=>(norm.outcomeLedger[k] || {}).bypassCost === L()[k].bypassCost)); }

  return JSON.stringify({ passed:out.filter(x=>x.ok).length, failed:out.filter(x=>!x.ok).length, failures:out.filter(x=>!x.ok) });
})();
