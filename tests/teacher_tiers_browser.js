/* CODIS-TEACHER-TIERS (3.29.0) — in-browser regression test: tests/teacher_tiers_browser.js
   Run: TEST=tests/teacher_tiers_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   يعدّل بيانات ملف الاختبار المحلي فقط. Returns { passed, failed, results[] }. */
(async function(){
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : String(info) });
  const eq = (name, a, b)=>T(name, JSON.stringify(a) === JSON.stringify(b), JSON.stringify(a) + ' vs ' + JSON.stringify(b));
  const near = (name, a, b, e)=>T(name, Math.abs(a - b) <= (e || 1e-9), a + ' vs ' + b);
  const snap = o=>JSON.stringify(o);
  const origItems = JSON.stringify(data.settings.rewardItems);
  const mk = (id, tier, w, on, extra)=>Object.assign({ id:id, name:'مكافأة ' + id, room:'learn', rarity:tier, weight:w === undefined ? 10 : w, enabled:on !== false, coinValue:null, storePrice:null }, extra || {});
  const setLearn = list=>{ data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.room !== 'learn').concat(list); };
  const E = CodisRewardEngine;
  const seq = arr=>{ let i = 0; E.setRng(()=>arr[Math.min(i++, arr.length - 1)]); };
  const T3 = codisTeacherTiers();

  /* ===== البنية والاحتمالات الابتدائية ===== */
  eq('tiers ids/order', T3.map(t=>t.id + ':' + t.order), ['bronze:1', 'silver:2', 'gold:3']);
  eq('tiers names', T3.map(t=>t.ar + '/' + t.en), ['برونزية/Bronze', 'فضية/Silver', 'ذهبية/Gold']);
  const od = econModel().odds, bo = codisTeacherBaseOdds();
  near('base odds sum 100', bo.bronze + bo.silver + bo.gold, 100, 1e-9);
  near('base bronze = C+B (88)', bo.bronze, od.C + od.B, 1e-9); near('base silver = A (9)', bo.silver, od.A, 1e-9); near('base gold = S+SS (3)', bo.gold, od.S + od.SS, 1e-9);
  T('tier ids are not global rarity ids', T3.every(t=>econCfg().rarities.every(r=>r.id !== t.id)));
  T('global rarities untouched (5, C..SS)', econCfg().rarities.map(r=>r.id).join() === 'C,B,A,S,SS');

  /* ===== التكيّف: نفس econAdaptiveOdds ونفس daily/weekly ===== */
  const ad = econCfg().adaptive;
  const sumW = a=>Object.keys(a.weights).reduce((s, k)=>s + a.weights[k], 0);
  T('count == base → no change', codisTeacherAdaptive('daily', ad.daily.base) === null);
  T('count < base → no change', codisTeacherAdaptive('daily', 0) === null);
  const a1 = codisTeacherAdaptive('daily', ad.daily.base + 1);
  near('base+1: bronze drops by step', a1.weights.bronze, 88 - ad.daily.step, 1e-9);
  near('base+1: sum stays 100', sumW(a1), 100, 1e-9);
  near('base+1: split silver:gold = 9:3', (a1.weights.silver - 9) / (a1.weights.gold - 3), 3, 1e-9);
  const a2 = codisTeacherAdaptive('daily', 5000);
  T('huge count: no negative, bronze floor 0', Object.keys(a2.weights).every(k=>a2.weights[k] >= 0) && a2.weights.bronze === 0);
  near('huge count: sum 100', sumW(a2), 100, 1e-9);
  const aw = codisTeacherAdaptive('weekly', ad.weekly.base + 6);
  near('weekly params used (step .5 × 6 = 3)', aw.dec, 3 * 1, 1e-9);
  T('adaptive disabled → null', (()=>{ const was = ad.enabled; ad.enabled = false; const r = codisTeacherAdaptive('daily', 50); ad.enabled = was; return r === null; })());
  /* مطابقة مع المعادلة العامة على نفس العدد: التخفيض نفسه */
  const g = econAdaptiveOdds('daily', 10); near('same decrease as global C reduction', a1.dec, econAdaptiveOdds('daily', ad.daily.base + 1).dec, 1e-9); T('global adaptive still works', !!g && g.cOdds < econCfg().rarities[0].weight);

  /* ===== السحب: مرحلتان ===== */
  setLearn([mk('b1', 'bronze', 10), mk('b2', 'bronze', 30), mk('s1', 'silver', 10), mk('s2', 'silver', 0), mk('g1', 'gold', 10), mk('g2', 'gold', 10, false)]);
  const tb = E.teacherTable('daily');
  near('table p sums to 1', tb.reduce((s, x)=>s + x.p, 0), 1, 1e-9);
  near('table bronze p = .88', tb[0].p, .88, 1e-9);
  seq([0.0, 0.0]); let r = E.roll('learn', 'daily'); T('rng low → bronze', r.rarity.id === 'bronze' && r.reward.rarity === 'bronze', r.rarity.id);
  seq([0.9, 0.0]); r = E.roll('learn', 'daily'); T('rng .9 → silver, only s1 (s2 weight 0)', r.rarity.id === 'silver' && r.reward.id === 's1', r.reward && r.reward.id);
  seq([0.99, 0.5]); r = E.roll('learn', 'daily'); T('rng .99 → gold, only enabled g1', r.rarity.id === 'gold' && r.reward.id === 'g1', r.reward && r.reward.id);
  seq([0.0, 0.0]); r = E.roll('learn', 'daily'); T('bronze weights: low rng → b1 (10:30)', r.reward.id === 'b1');
  seq([0.0, 0.9]); r = E.roll('learn', 'daily'); T('bronze weights: high rng → b2', r.reward.id === 'b2');
  T('tier value matches econEffCoin / range min', (()=>{ seq([0.9, 0]); const s = E.roll('learn', 'daily'); seq([0.99, 0]); const gg = E.roll('learn', 'daily'); return s.coinValue === 12.5 && gg.coinValue === 20; })());
  /* عدّاد التكيّف يغيّر الجدول الفعلي */
  const tAd = E.teacherTable('daily', { adaptive:{ period:'daily', count:ad.daily.base + 10 } });
  T('adaptive lowers bronze in the real table', tAd[0].p < tb[0].p && tAd[1].p > tb[1].p && tAd[2].p > tb[2].p);
  near('adaptive table sums 1', tAd.reduce((s, x)=>s + x.p, 0), 1, 1e-9);
  T('adaptive period must match context (weekly opts ignored on daily)', E.teacherTable('daily', { adaptive:{ period:'weekly', count:500 } })[0].p === tb[0].p);
  /* عيّنة إحصائية */
  E.setRng(null); { const N = 20000, c = { bronze:0, silver:0, gold:0 }; for(let i = 0; i < N; i++) c[E.roll('learn', 'daily').rarity.id]++; T('sampled frequencies near 88/9/3', Math.abs(c.bronze / N - .88) < .015 && Math.abs(c.silver / N - .09) < .012 && Math.abs(c.gold / N - .03) < .01, JSON.stringify(c)); }
  { const N = 8000, c = { bronze:0, silver:0, gold:0 }; for(let i = 0; i < N; i++) c[E.roll('learn', 'daily', { adaptive:{ period:'daily', count:ad.daily.base + 20 } }).rarity.id]++; T('adaptive sample: bronze share falls to ~28%', Math.abs(c.bronze / N - .28) < .03, JSON.stringify(c)); }

  /* ===== فراغ/تعطيل/وزن صفر ===== */
  setLearn([mk('b1', 'bronze'), mk('g1', 'gold')]);
  let t0 = E.teacherTable('daily'); near('empty silver folds down: bronze .97', t0[0].p, .97, 1e-9); near('silver p = 0', t0[1].p, 0, 1e-9);
  setLearn([mk('s1', 'silver'), mk('g1', 'gold')]);
  t0 = E.teacherTable('daily'); near('empty bronze stays (generic bronze, no upward concentration)', t0[0].p, .88, 1e-9);
  seq([0.1]); r = E.roll('learn', 'daily'); T('empty bronze → generic bronze value 10 (no other room)', r.generic !== true ? (r.reward === null && r.rarity.id === 'bronze' && r.coinValue === 10) : false, JSON.stringify([r.generic, r.coinValue]));
  setLearn([mk('b1', 'bronze', 0, true), mk('s1', 'silver', 10, false)]);
  r = E.roll('learn', 'daily'); T('all zero/disabled → safe generic bronze', r.reward === null && r.rarity.id === 'bronze' && r.coinValue === 10);
  setLearn([]); r = E.roll('learn', 'daily'); T('no teacher rewards → generic bronze', r.reward === null && r.rarity.id === 'bronze' && r.emptyPool === true);
  /* المطوّر: إعادة موازنة نسبية */
  { const realIs = CodisAccount.isAdmin; setLearn([mk('s1', 'silver'), mk('g1', 'gold')]); CodisAccount.isAdmin = ()=>true; let tt; try{ tt = E.teacherTable('daily'); }finally{ CodisAccount.isAdmin = realIs; }
    near('admin: proportional rebalance (silver 9/12)', tt[1].p, .75, 1e-9); near('admin: bronze 0', tt[0].p, 0, 1e-9); }

  /* ===== عزل الحالة ===== */
  setLearn([mk('b1', 'bronze'), mk('b2', 'bronze'), mk('s1', 'silver'), mk('g1', 'gold')]);
  const stBefore = snap({ pity:data.economyState.pity, rec:data.economyState.recent.filter(x=>x.room !== 'learn') });
  const oddsTasks = snap(E.explain('tasks', 'daily')), oddsW = snap(E.explain('weekly', 'weekly'));
  for(let i = 0; i < 30; i++){ const rr = E.roll('learn', 'daily', { adaptive:{ period:'daily', count:7 } }); E.commit('learn', rr); }
  eq('pity + other rooms recents untouched after 30 teacher draws', snap({ pity:data.economyState.pity, rec:data.economyState.recent.filter(x=>x.room !== 'learn') }), stBefore);
  eq('global tasks odds unchanged', snap(E.explain('tasks', 'daily')), oddsTasks); eq('global weekly odds unchanged', snap(E.explain('weekly', 'weekly')), oddsW);
  T('teacher recents only in room learn', data.economyState.recent.filter(x=>x.room === 'learn').every(x=>/^(b1|b2|s1|g1)$/.test(x.id)));
  seq([0.0, 0.0]); E.commit('learn', E.roll('learn', 'daily')); const last = data.economyState.recent.find(x=>x.room === 'learn').id;
  seq([0.0, 0.0]); r = E.roll('learn', 'daily'); T('anti-repeat (independent): immediate repeat blocked inside tier', r.reward.id !== last || false, last + '→' + r.reward.id);
  E.setRng(null);

  /* ===== إنشاء نتيجة كاملة (create) ===== */
  setLearn([mk('s1', 'silver')]);
  seq([0.9, 0.0]);
  const cr = CodisEconomy.create('tt|test|1', 'reward', 'daily', 'learn', 'daily', {}, { adaptive:{ period:'daily', count:9 } }); E.setRng(null);
  const en = cr.entry;
  T('entry stores tier fields', en.rarity === 'silver' && en.rarityName === 'فضية' && en.rarityTone === 'silver' && en.rarityOrder === 2 && en.coinValue === 12.5 && en.adaptive && en.adaptive.count === 9, JSON.stringify([en.rarity, en.coinValue, en.adaptive]));
  const dec = CodisEconomy.decideReward('tt|test|1', 'item'); T('decide item → inventory snapshot keeps silver', dec.ok && dec.owned.rarity === 'silver' && dec.owned.rarityTone === 'silver' && dec.owned.coinValue === 12.5, JSON.stringify(dec.owned && [dec.owned.rarity, dec.owned.rarityTone]));
  const it = data.inventory.items.find(x=>x.uid === 'own|tt|test|1');
  T('inventory normalize keeps tier tone/id', (()=>{ const d2 = JSON.parse(JSON.stringify(data)); econNormalizeInventory(d2); const x = d2.inventory.items.find(y=>y.uid === it.uid); return x.rarity === 'silver' && x.rarityTone === 'silver'; })());
  T('sell value consistent (12.5 → ≤ 80%, < value)', CodisInventory.sellValue(it) > 0 && CodisInventory.sellValue(it) < 12.5, CodisInventory.sellValue(it));

  /* ===== الاقتصاد ===== */
  const ecoItems = [mk('eb', 'bronze'), mk('es', 'silver'), mk('eg', 'gold')]; setLearn(ecoItems); econNormalizeItems(data.settings);
  const cat = id=>data.settings.rewardItems.find(x=>x.id === id);
  eq('coin per tier', ['eb', 'es', 'eg'].map(i=>econEffCoin(cat(i), econRarityById(cat(i).rarity))), [10, 12.5, 20]);
  eq('store = round(coin × 1.12)', ['eb', 'es', 'eg'].map(i=>econEffStore(cat(i), econRarityById(cat(i).rarity))), [10, 12.5, 20].map(c=>Math.round(c * econCfg().storeMarkup)));
  T('each tier inside its finance range', [[10, 'bronze'], [12.5, 'silver'], [20, 'gold']].every(p=>{ const c = codisFinCardById('learn_' + p[1]); return codisFinInRange(c, p[0]); }));
  T('plain teacher reward ≠ fin (fin value untouched)', (()=>{ const f = mk('ef', 'silver', 10, true, { fin:{ v:1, kind:'financial', iqd:600000, card:'learn_silver', coin:15 } }); f.fin = codisFinItemOk(f.fin); return econEffCoin(f, econRarityById('silver')) === codisFinItemCoin(f); })());

  /* ===== النطاقات المالية ===== */
  const mc = codisFinMatrixCheck(); T('matrix check ok (25 cards)', mc.ok && mc.count === 25, mc.problems.join(' | '));
  const tierOf = v=>codisFinCardsFor(v).filter(c=>c.room === 'learn').map(c=>c.id.replace('learn_', ''));
  eq('range 10', tierOf(10), ['bronze']); eq('range 12.49', tierOf(12.49), ['bronze']); eq('range 12.5', tierOf(12.5), ['silver']); eq('range 19.99', tierOf(19.99), ['silver']);
  eq('range 20', tierOf(20), ['gold']); eq('range 29.99', tierOf(29.99), ['gold']); eq('range 30', tierOf(30), ['gold']); eq('range 9.99', tierOf(9.99), []); eq('range 30.01', tierOf(30.01), []);
  T('never two teacher tiers for one value', [10, 11, 12.4999, 12.5, 15, 19.995, 20, 25, 30].every(v=>tierOf(v).length === 1));
  eq('codisTeacherTierForCoin', [10, 12.49, 12.5, 19.99, 20, 30].map(codisTeacherTierForCoin), ['bronze', 'bronze', 'silver', 'silver', 'gold', 'gold']);
  const other = codisFinCards().filter(c=>c.room !== 'learn'); eq('other 22 cards unchanged count', other.length, 22);
  const sn = codisFinClassify('فلم', 14); T('classify keeps semantic path (silver is a candidate for 14)', sn.ok && sn.candidates.some(c=>c.card.id === 'learn_silver'));
  T('legacy card id alias', codisFinCardById('learn').id === 'learn_bronze');

  /* ===== الترحيل ===== */
  const legacy = [{ id:'old1', name:'قديمة 1', room:'learn', rarity:'C', weight:7, enabled:false, stickerId:'pizza', coinValue:null, storePrice:null }, { id:'old2', name:'قديمة 2', room:'learn', rarity:'SS', weight:3, enabled:true }, { id:'old3', name:'قديمة 3', room:'learn', weight:5 }];
  data.settings.rewardItems = data.settings.rewardItems.filter(x=>x.room !== 'learn').concat(JSON.parse(JSON.stringify(legacy)));
  econNormalizeItems(data.settings);
  const l1 = cat('old1'), l2 = cat('old2'), l3 = cat('old3');
  T('legacy → bronze', [l1, l2, l3].every(x=>x.rarity === 'bronze'));
  T('ids/names/weight/enabled kept', l1.id === 'old1' && l1.name === 'قديمة 1' && l1.weight === 7 && l1.enabled === false && l2.weight === 3 && l3.weight === 5);
  const once1 = snap(data.settings.rewardItems.filter(x=>x.room === 'learn')); econNormalizeItems(data.settings); eq('normalize is idempotent (no re-migration side effects)', snap(data.settings.rewardItems.filter(x=>x.room === 'learn')), once1);
  cat('old2').rarity = 'gold'; econNormalizeItems(data.settings); T('user-chosen tier survives reload normalize', cat('old2').rarity === 'gold');
  T('no duplicates', data.settings.rewardItems.filter(x=>x.id === 'old1').length === 1);
  T('legacy fin card id migrated', (()=>{ const s2 = { rewardItems:[{ id:'f1', name:'x', room:'learn', rarity:'C', fin:{ v:1, kind:'financial', iqd:500000, card:'learn', coin:11 } }] }; codisFinReconcileItems(s2); return s2.rewardItems[0].fin.card === 'learn_bronze' && s2.rewardItems[0].rarity === 'bronze'; })());
  T('legacy history entry renders as bronze teacher card', (()=>{ const h = codisRewardCardHtml({ kind:'reward', scope:'daily', room:'learn', rarity:'C', rarityTone:'c', rarityName:'شائعة', item:'قديمة', coinValue:10 }); return h.indexOf('scx-t-bronze') !== -1 && h.indexOf('>10<') !== -1; })());

  /* ===== المحرر ===== */
  const host = document.createElement('div'); host.id = 'tt-host'; document.body.appendChild(host);
  host.innerHTML = econRewardEditor('tt-ed', { name:'اختبار', rarity:'silver', weight:10, enabled:true, room:'learn' });
  const q = id=>document.getElementById('tt-ed-' + id);
  T('editor shows tier select for learn (3 options, no C/B/A/S/SS)', q('trarity') && q('trarity-wrap').style.display !== 'none' && q('trarity').options.length === 3 && q('rarity-wrap').style.display === 'none');
  T('editor pre-selects silver', q('trarity').value === 'silver');
  q('trarity').value = 'gold'; econRewardRarityChanged('tt-ed'); T('hint follows tier (gold 20)', q('hint').textContent.indexOf('ذهبية') !== -1 && q('hint').textContent.indexOf('20') !== -1, q('hint').textContent);
  const rd = econReadReward('tt-ed'); T('read → real data rarity gold', rd && rd.rarity === 'gold' && rd.room === 'learn', JSON.stringify(rd && [rd.rarity, rd.room]));
  q('room').value = 'tasks'; econRewardRarityChanged('tt-ed'); T('other room: global rarity select back, tier hidden', q('rarity-wrap').style.display === '' && q('trarity-wrap').style.display === 'none');
  q('rarity').value = 'B'; const rd2 = econReadReward('tt-ed'); T('other room reads global rarity', rd2 && rd2.rarity === 'B' && rd2.room === 'tasks');
  host.remove();
  /* إضافة ونقل وتعطيل عبر الدوال نفسها */
  setLearn([]); { const now = econNowIso(); data.settings.rewardItems.push(Object.assign({ id:'mv1', createdAt:now, updatedAt:now }, { name:'تنقّل', room:'learn', rarity:'gold', weight:10, enabled:true })); econNormalizeItems(data.settings); }
  T('added gold item kept gold', cat('mv1').rarity === 'gold');
  cat('mv1').rarity = 'silver'; econNormalizeItems(data.settings); T('moved gold → silver', cat('mv1').rarity === 'silver');
  econToggleReward('mv1'); T('disabled', cat('mv1').enabled === false); econToggleReward('mv1'); T('re-enabled', cat('mv1').enabled === true);
  T('persisted through JSON save/load roundtrip', (()=>{ const d2 = JSON.parse(JSON.stringify(data)); econNormalizeAll(d2); return d2.settings.rewardItems.find(x=>x.id === 'mv1').rarity === 'silver'; })());

  /* ===== البطاقات ===== */
  const faces = T3.map(t=>codisRewardCardHtml({ kind:'reward', scope:'daily', room:'learn', rarity:t.id, rarityTone:t.tone, item:'X', coinValue:t.ref }));
  T('3 distinct card faces w/ own art + label', faces.every((h, i)=>h.indexOf('scx-t-' + T3[i].id) !== -1 && h.indexOf('>' + T3[i].en + '<') !== -1) && new Set(faces.map(h=>(h.match(/src="([^"]{40})/) || [])[1])).size === 3);
  T('tier art differs per tier (data URIs)', CODIS_SPECIAL_CARD_ART.teacher_bronze !== CODIS_SPECIAL_CARD_ART.teacher_silver && CODIS_SPECIAL_CARD_ART.teacher_silver !== CODIS_SPECIAL_CARD_ART.teacher_gold);
  const rar = econRarityById('gold'), item = { id:'z', name:'Z', room:'learn', rarity:'gold', enabled:true };
  T('store face = same identity', econStoreFaceHtml(item, rar, { price:22 }).indexOf('scx-t-gold') !== -1);
  T('store tile renders gold, kind is-dl, name label', (()=>{ const h = econStoreCardHtml(Object.assign({ stickerId:null }, item), rar, 100, 0); return h.indexOf('scx-t-gold') !== -1 && h.indexOf('is-dl') !== -1; })());
  T('pack tile (inventory) renders gold', econPackTileHtml({ id:'q', room:'learn', name:'Z', stickerId:null }, { id:'gold', name:'ذهبية', tone:'gold', order:3 }).indexOf('scx-t-gold') !== -1);
  T('result uses card path for tier tones', codisUseRewardCard({ kind:'reward', scope:'daily', room:'learn', rarityTone:'silver' }) === true);
  T('other rooms card path unchanged', codisCardKey({ rarityTone:'ss' }) === 'SS' && codisCardKey({ rarityTone:'zz' }) === null);
  T('rows tag shows tier', codisRptTag('reward', Object.assign({ stickerId:null }, item)).indexOf('Gold') !== -1);
  T('no JS errors collected', !(window.__ttErr && window.__ttErr.length));

  data.settings.rewardItems = JSON.parse(origItems);
  const passed = out.filter(x=>x.ok).length, failed = out.filter(x=>!x.ok);
  return { passed:passed, failed:failed.length, results:failed.concat(out.length > 0 ? [] : []) };
})();
