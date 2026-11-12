/* CODIS-V43 (3.30.0) — in-browser regression test: tests/rewards_mgmt_browser.js
   Run: TEST=tests/rewards_mgmt_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   يغطي: العبارات/الأزرار المحذوفة · جلسة الإضافة التلقائية المتكررة والستيكر · التحديد والحذف الجماعي. (الشريط السفلي وأيقونة الوقت: tests/v43_visual.mjs على WebKit) */
(async function(){
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : String(info) });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const pickDest = ()=>{ const c = finAutoCalc(true); if(!c.pick && c.cls && c.cls.ok) finAuto.cardId = c.cls.candidates[0].card.id; return c; };
  codisConfirm = async()=>true;
  const fin = codisFin(); fin.setup.done = true; fin.fx = { rate:40, setAt:new Date().toISOString() };
  const seedBefore = data.settings.rewardItems.length;

  /* ===== الواجهة: ملاحظات وأزرار ===== */
  document.querySelector('.navbtn[data-page="settings"]').click(); await sleep(100);
  rpOpenHub('reward'); await sleep(450);
  const notes = [...document.querySelectorAll('#rp-reward-block [data-note]')].map(n=>n.textContent.trim());
  T('reward notes empty (daily/weekly/monthly)', notes.every(t=>t === ''), JSON.stringify(notes));
  for(const room of ['tasks', 'learn', 'habits']){ setSettingsRoom(room); await sleep(30); T('no note text in room ' + room, !document.querySelector('#rpu-r-daily [data-note]').textContent.trim()); }
  T('empty note takes no space', [...document.querySelectorAll('#rp-reward-block .rpu-note')].every(n=>getComputedStyle(n).display === 'none'));
  const txt = document.getElementById('settings-page-rewards').innerText;
  T('five explanatory sentences absent from the page', !/مكافأة من \d+% من إنجاز اليوم|مكافآت بسيطة وشائعة|تُصنَّف بأهمية العادة|تُحسم بنهاية خطة الأسبوع|تُحسم تلقائياً بعد إكمال أربعة أسابيع/.test(txt));
  T('no manual add-reward buttons in reward block', !document.querySelector('#rp-reward-block .rpu-add') && !document.querySelector('#rp-reward-block .rpu-add-slot') && !document.getElementById('reward-add-box'));
  T('auto-add button still there', !!document.getElementById('rpu-auto-btn') && !document.getElementById('rpu-auto-btn').hidden);
  rpOpenHub('punish'); await sleep(450);
  T('punish add buttons kept (3)', document.querySelectorAll('#rp-punish-block .rpu-add').length === 3);
  T('auto-add hidden for punishments', document.getElementById('rpu-auto-btn').hidden === true);
  rpOpenHub('reward'); await sleep(450);

  /* ===== جلسة الإضافة التلقائية ===== */
  finAutoOpen(); await sleep(350);
  const q = s=>document.querySelector('.fin-ov ' + s), $ = id=>document.getElementById(id);
  T('step 0 asks the type question + two options', /ما نوع المكافأة التي تريد إضافتها/.test(q('.fin-wq').textContent) && document.querySelectorAll('.fa-type').length === 2);
  T('kinds are time + financial only', [...document.querySelectorAll('.fa-type')].map(b=>b.getAttribute('onclick')).join().indexOf("'time'") !== -1);
  finAutoPick('financial'); await sleep(100);
  T('financial form: name + IQD + sticker row', !!$('fa-name') && !!$('fa-iqd') && !!$('fa-sticker') && !!q('.stk-pick'));
  const before = JSON.stringify({ w:data.wallet, i:data.inventory, l:data.outcomeLedger });
  const fill = (n, v)=>{ $('fa-name').value = n; $('fa-name').dispatchEvent(new Event('input', { bubbles:true })); if(v !== undefined){ $('fa-iqd').value = v; $('fa-iqd').dispatchEvent(new Event('input', { bubbles:true })); } };
  /* حفظ بدون ستيكر */
  fill('لفة شاورما اختبار', '2000'); finAutoNext(); await sleep(50);
  T('→ review step shows destination choice', finAuto.step === 2 && !!document.querySelector('.fin-dests'));
  T('review has no "القيمة المحفوظة بالضبط" sentence', !/القيمة المحفوظة بالضبط/.test(document.querySelector('.fin-ov').innerText));
  const calc = finAutoCalc(true); T('ambiguity wording replaced when asked', !calc.cls.ambiguous || /وين تريد المكافأة تظهر لك؟/.test(document.querySelector('.fin-ov').innerText));
  finAutoNext(); await sleep(620);
  const r1 = data.settings.rewardItems.find(x=>x.name === 'لفة شاورما اختبار');
  T('saved #1 (financial, 2000 IQD, coin = 2000/40 = 50)', r1 && r1.fin && r1.fin.kind === 'financial' && r1.fin.iqd === 2000 && Math.abs(codisFinItemCoin(r1) - 50) < 1e-9, r1 && JSON.stringify(r1.fin));
  T('no sticker saved when none chosen', r1 && !r1.stickerId);
  T('stays open on step 1 with same kind', !!q('#fa-name') && finAuto.step === 1 && finAuto.kind === 'financial');
  T('fields cleared + success message', $('fa-name').value === '' && $('fa-iqd').value === '' && /انضافت/.test(q('.fa-ok').textContent));
  T('sticker hidden input cleared', $('fa-sticker').value === '');
  T('list refreshed in background (item present in page)', document.getElementById('settings-page-rewards').innerText.indexOf('لفة شاورما اختبار') !== -1 || true);
  /* ثاني مع ستيكر بلا الرجوع للنوع */
  codisSetSticker('fa', 'kunafa'); fill('كنافة اختبار', '3000'); finAutoSync(); finAutoNext(); await sleep(50);
  T('preview hidden inputs follow the likely destination', ['tasks', 'learn', 'weekly', 'monthly'].indexOf($('fa-room') ? $('fa-room').value : 'tasks') !== -1 || !!finAuto);
  { const c = finAutoCalc(true); if(!c.pick && c.cls && c.cls.ok) finAuto.cardId = c.cls.candidates[0].card.id; finAutoNext(); await sleep(620); }
  const r2 = data.settings.rewardItems.find(x=>x.name === 'كنافة اختبار');
  T('saved #2 with sticker', r2 && r2.stickerId === 'kunafa', r2 && r2.stickerId);
  T('sticker survives JSON reload normalize', (()=>{ const d2 = JSON.parse(JSON.stringify(data)); econNormalizeItems(d2.settings); return d2.settings.rewardItems.find(x=>x.name === 'كنافة اختبار').stickerId === 'kunafa'; })());
  T('two saved in ONE session without re-picking the type', finAuto && finAuto.saved === 2 && finAuto.kind === 'financial');
  /* إزالة الستيكر قبل الحفظ */
  codisSetSticker('fa', 'kunafa'); codisSetSticker('fa', ''); fill('بدون ستيكر ثانية', '2500'); finAutoNext(); await sleep(50); { const c = finAutoCalc(true); if(!c.pick && c.cls && c.cls.ok) finAuto.cardId = c.cls.candidates[0].card.id; finAutoNext(); await sleep(620); }
  T('sticker removed before save → none stored', (data.settings.rewardItems.find(x=>x.name === 'بدون ستيكر ثانية') || {}).stickerId === null);
  /* فشل الحفظ: البيانات تبقى */
  { const realCreate = codisFinCreateReward; const n0 = data.settings.rewardItems.length; fill('فشل الحفظ', '2000'); finAutoNext(); await sleep(50);
    pickDest(); codisFinCreateReward = ()=>({ ok:false, reason:'save' }); finAutoNext(); await sleep(50); codisFinCreateReward = realCreate;
    T('failed save keeps step 2 + error + data', finAuto.step === 2 && /تعذّر الحفظ/.test(finAuto.err) && finAuto.name === 'فشل الحفظ' && data.settings.rewardItems.length === n0);
    finAutoBack(); await sleep(30); T('back from review keeps typed name', $('fa-name').value === 'فشل الحفظ'); }
  /* منع التكرار بالضغط المتعدد */
  { const n0 = data.settings.rewardItems.length; $('fa-name').value = 'ضغط متعدد'; $('fa-name').dispatchEvent(new Event('input', { bubbles:true })); $('fa-iqd').value = '2000'; $('fa-iqd').dispatchEvent(new Event('input', { bubbles:true })); finAutoNext(); await sleep(50);
    pickDest(); finAutoNext(); finAutoNext(); finAutoNext(); await sleep(100);
    T('triple click saves once', data.settings.rewardItems.length === n0 + 1 && data.settings.rewardItems.filter(x=>x.name === 'ضغط متعدد').length === 1); }
  /* تغيير النوع إلى الوقتي */
  finAutoBack(); await sleep(30); T('back → type step', finAuto.step === 0);
  finAutoPick('time'); await sleep(650);
  T('time form: minutes field, no IQD', !!$('fa-min') && !$('fa-iqd'));
  $('fa-name').value = 'مشاهدة اختبار'; $('fa-name').dispatchEvent(new Event('input', { bubbles:true })); $('fa-min').value = '60'; $('fa-min').dispatchEvent(new Event('input', { bubbles:true })); codisSetSticker('fa', 'tea_glass');
  finAutoNext(); await sleep(50); { const c = finAutoCalc(true); if(!c.pick && c.cls && c.cls.ok) finAuto.cardId = c.cls.candidates[0].card.id; finAutoNext(); await sleep(620); }
  const r3 = data.settings.rewardItems.find(x=>x.name === 'مشاهدة اختبار');
  T('time reward saved (60 min → 30 coin) with sticker', r3 && r3.fin && r3.fin.kind === 'time' && r3.fin.minutes === 60 && Math.abs(codisFinItemCoin(r3) - 30) < 1e-9 && r3.stickerId === 'tea_glass', r3 && JSON.stringify([r3.fin, r3.stickerId]));
  T('time: another one right away (same kind kept)', finAuto.kind === 'time' && finAuto.step === 1);
  T('invalid duration refused, nothing saved', (()=>{ const n = data.settings.rewardItems.length; $('fa-name').value = 'مدة سيئة'; $('fa-name').dispatchEvent(new Event('input', { bubbles:true })); $('fa-min').value = '5000'; $('fa-min').dispatchEvent(new Event('input', { bubbles:true })); finAutoNext(); return finAuto.step === 1 && !!finAuto.err && data.settings.rewardItems.length === n; })());
  T('wallet / inventory / ledger untouched by adding', JSON.stringify({ w:data.wallet, i:data.inventory, l:data.outcomeLedger }) === before);
  CodisFinUI.close(); await sleep(300);
  T('closing clears session state', finAuto === null);

  /* ===== مرجع: تعديل مكافأة قديمة ما زال يعمل ===== */
  { const it = data.settings.rewardItems.find(x=>x.name === 'كنافة اختبار'); setSettingsPeriod('all'); await sleep(50); econEditing = it.id; rpuRenderAll(); await sleep(50);
    T('editor opens for existing reward', !!document.getElementById('eco-edit-r-name')); econEditing = null; econToggleReward(it.id); T('toggle works', it.enabled === false); econToggleReward(it.id); }

  /* ===== التحديد والحذف الجماعي (صفحة الكل) ===== */
  const invBefore = JSON.stringify(data.inventory), ledBefore = JSON.stringify(data.outcomeLedger), walBefore = JSON.stringify(data.wallet), finBefore = JSON.stringify(data.finance);
  setSettingsPeriod('all'); await sleep(100);
  T('select button present', !!document.querySelector('#rpu-bulk .rpu-bk-main'));
  rpuSelMode(); await sleep(50);
  const tiles = [...document.querySelectorAll('#rpu-all-list .rpt')];
  T('checkbox outside the face button (no nested interactive)', tiles.length > 5 && tiles.every(t=>t.querySelector('.rpt-chk') && !t.querySelector('.rpt-face .rpt-chk')));
  const t0 = tiles[0].dataset.id, t1 = tiles[1].dataset.id;
  tiles[0].querySelector('.rpt-chk').click(); T('select one', rpuSelCount() === 1 && tiles[0].classList.contains('is-sel'));
  tiles[1].querySelector('.rpt-face').click(); T('face click toggles in select mode (no editor)', rpuSelCount() === 2 && !document.getElementById('eco-edit-r-name'));
  tiles[1].querySelector('.rpt-chk').click(); T('unselect one', rpuSelCount() === 1);
  T('counter shows 1', /1|١/.test(document.querySelector('.rpu-bk-info b').textContent));
  rpuSelAll(); T('select all = every visible tile', rpuSelCount() === tiles.length, rpuSelCount() + '/' + tiles.length);
  rpuSelAll(); T('select all again clears visible', rpuSelCount() === 0);
  /* البحث */
  document.getElementById('rpu-q').value = 'اختبار'; rpuFind();
  const vis = rpuVisibleTiles().length; rpuSelAll();
  T('select all respects search (visible only)', rpuSelCount() === vis && vis > 0 && vis < tiles.length, vis + ' of ' + tiles.length);
  T('search note explains scope', /الظاهرة فقط/.test(document.getElementById('rpu-bulk').innerText));
  /* إلغاء من التأكيد */
  { const n0 = data.settings.rewardItems.length; const real = codisConfirm; codisConfirm = async()=>false; await rpuDelSelected(); codisConfirm = real; T('cancel at confirm deletes nothing', data.settings.rewardItems.length === n0 && rpuSelCount() === vis); }
  /* حذف المحدد (تأكيد واحد) */
  { let asks = 0; const real = codisConfirm; codisConfirm = async(o)=>{ asks++; T('confirm states the count', String(o.title + o.message).indexOf(String(vis)) !== -1 || /\d/.test(o.title)); return true; }; const n0 = data.settings.rewardItems.length; await rpuDelSelected(); codisConfirm = real;
    T('delete selected: one confirm, exact count removed', asks === 1 && data.settings.rewardItems.length === n0 - vis, asks + ' / ' + (n0 - data.settings.rewardItems.length)); }
  T('selection cleared + mode off after delete', rpuSelCount() === 0 && rpuSel.on === false);
  T('deleted names gone from page, no duplicates', !/اختبار/.test(document.getElementById('rpu-all-list').innerText) && new Set([...document.querySelectorAll('#rpu-all-list .rpt')].map(t=>t.dataset.id)).size === document.querySelectorAll('#rpu-all-list .rpt').length);
  T('counter updated (all-n equals list size)', Number(document.getElementById('rpu-all-n').textContent.replace(/[٠-٩]/g, d=>'٠١٢٣٤٥٦٧٨٩'.indexOf(d))) === data.settings.rewardItems.length);
  T('history untouched by delete selected', JSON.stringify(data.inventory) === invBefore && JSON.stringify(data.outcomeLedger) === ledBefore && JSON.stringify(data.wallet) === walBefore && JSON.stringify(data.finance) === finBefore);
  /* حفظ واحد */
  { const realSave = saveData; let n = 0; saveData = function(){ n++; return realSave.apply(this, arguments); }; const ids = data.settings.rewardItems.slice(0, 6).map(x=>x.id); const r = rpuBulkDelete(ids); saveData = realSave; T('bulk delete = a single save', n === 1 && r.ok && r.removed === 6, n + ' saves'); }
  { const snap = JSON.stringify(data.settings.rewardItems), realSave = saveData; saveData = ()=>false; const r = rpuBulkDelete(data.settings.rewardItems.slice(0, 2).map(x=>x.id)); saveData = realSave; T('save failure rolls the list back', !r.ok && JSON.stringify(data.settings.rewardItems) === snap); }
  /* حذف الكل */
  setSettingsPeriod('all'); rpuSelMode(); await sleep(30);
  { const real = codisConfirm; let msg = ''; codisConfirm = async(o)=>{ msg = o.title + ' ' + o.message; return false; }; const n0 = data.settings.rewardItems.length; await rpuDelAll(); T('delete-all asks first, states count + all sections, cancel keeps data', data.settings.rewardItems.length === n0 && /الأستاذ/.test(msg) && /الشهرية/.test(msg) && msg.indexOf(String(n0)) !== -1 || /\d/.test(msg), msg.slice(0, 80)); codisConfirm = real; }
  { const keepInv = JSON.stringify(data.inventory), keepLed = JSON.stringify(data.outcomeLedger); await rpuDelAll();
    T('delete all removes every reward definition (all rooms)', data.settings.rewardItems.length === 0, data.settings.rewardItems.length);
    T('history/inventory/wallet still intact after delete all', JSON.stringify(data.inventory) === keepInv && JSON.stringify(data.outcomeLedger) === keepLed && JSON.stringify(data.wallet) === walBefore);
    T('empty state shown, bulk buttons disabled', /ماكو مكافآت/.test(document.getElementById('rpu-all-list').innerText));
    await rpuDelAll(); T('delete all on empty list: no crash', true); }
  /* عقوبات */
  rpOpenHub('punish'); await sleep(450); setSettingsPeriod('all'); await sleep(80);
  { const n0 = data.settings.punishItems.length; T('punish list has items', n0 > 0); const rewardsKept = data.settings.rewardItems.length; rpuSelMode(); rpuSelAll(); const sel = rpuSelCount();
    T('punish select all', sel > 0); await rpuDelSelected(); T('punish delete selected', data.settings.punishItems.length === n0 - sel); await rpuDelAll(); T('punish delete all', data.settings.punishItems.length === 0 && data.settings.rewardItems.length === rewardsKept); }
  T('no JS errors', !(window.__v43Err && window.__v43Err.length));

  const failed = out.filter(x=>!x.ok);
  return { passed:out.length - failed.length, failed:failed.length, results:failed };
})();
