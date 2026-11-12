/* CODIS-CLARITY (patch_v28.py) — in-browser regression test.
   Run: serve the project root over http, open app/CODIS_FINAL.html on a FRESH origin, continue as guest, then evaluate this file in the page
   (it mutates local test data only). Returns {passed, failed, results[]}. */
(async function(){
  /* 3.30.0: نموذج الإضافة اليدوي أُزيل من الواجهة (الإضافة الجديدة تلقائية فقط)؛ الاختبار يركّبه كأداة لاختبار المحرر/الستيكر/الحفظ */
  const legacyAdd = (period)=>{ let h = document.getElementById('reward-add-box'); if(!h){ h = document.createElement('div'); h.id = 'reward-add-box'; h.style.cssText = 'position:fixed;left:-9999px;top:0'; document.body.appendChild(h); } h.innerHTML = econRewardEditor('eco-new-r', null) + '<button type="button" class="btn btn-primary eco-full" onclick="econAddReward()">إضافة المكافأة</button>'; h.dataset.ready = '1'; const sel = document.getElementById('eco-new-r-room'); sel.value = period === 'daily' ? settingsDailyRoom : period; econRewardRarityChanged('eco-new-r'); };
  const out = [], T = (name, ok, info)=>out.push({ name, ok:!!ok, info:info === undefined ? '' : String(info) });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const realConfirm = codisConfirm; codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  try{
    /* ---- 1. layering: sheets under the confirm, lock/startup above both ---- */
    const z = sel=>{ const e = document.createElement('div'); e.className = sel; document.body.appendChild(e); const v = +getComputedStyle(e).zIndex; e.remove(); return v; };
    const zc = +getComputedStyle(document.getElementById('codis-confirm-modal')).zIndex, zs = z('cd-ov'), zl = z('codis-lock');
    T('completed/grace/sticker sheets sit below the confirm dialog', zs < zc, zs + ' < ' + zc);
    T('lock screen stays above sheets and confirm', zl > zc && zl > zs, zl);

    /* ---- 2. rewards / punishments: one page, three periods ---- */
    document.querySelector('nav button[data-page="settings"]').click(); await sleep(400);
    rpOpenHub('reward'); await sleep(500);
    const R = data.settings.rewardItems, P = data.settings.punishItems, before = JSON.stringify([R.map(x=>[x.id, x.room]), P.map(x=>[x.id, x.room])]);
    ['reward-list', 'reward-list-weekly', 'reward-list-monthly'].forEach((id, i)=>T('rewards page has the ' + ['daily', 'weekly', 'monthly'][i] + ' list', !!document.getElementById(id)));
    const cnt = id=>document.querySelectorAll('#' + id + ' .eco-item').length;
    T('weekly list = weekly items', cnt('reward-list-weekly') === R.filter(x=>x.room === 'weekly').length);
    T('monthly list = monthly items', cnt('reward-list-monthly') === R.filter(x=>x.room === 'monthly').length);
    setSettingsRoom('learn'); await sleep(50);
    T('daily room switch filters daily list only', cnt('reward-list') === R.filter(x=>x.room === 'learn').length && cnt('reward-list-weekly') === R.filter(x=>x.room === 'weekly').length);
    T('monthly settlement card present', !!document.querySelector('#rpu-r-monthly [data-month] button'));
    legacyAdd('weekly'); await sleep(50);
    T('weekly add form targets weekly', document.getElementById('eco-new-r-room').value === 'weekly');
    document.getElementById('eco-new-r-name').value = 'clarity-weekly'; document.querySelector('#reward-add-box .btn-primary').click(); await sleep(100);
    const nw = R.find(x=>x.name === 'clarity-weekly');
    T('added reward lands in weekly', nw && nw.room === 'weekly' && !!Array.from(document.querySelectorAll('#reward-list-weekly .eco-item-name')).find(e=>e.textContent === 'clarity-weekly'));
    if(nw){ await econDeleteReward(nw.id); }
    setSettingsRoom('tasks');
    rpGo('rp'); await sleep(350); rpOpenHub('punish'); await sleep(500);
    T('punish page shows punish block only', document.getElementById('rp-punish-block').style.display === '' && document.getElementById('rp-reward-block').style.display === 'none');
    T('punish cost table rendered once', document.querySelectorAll('#punish-costs .eco-ptable').length === 1);
    const S2 = data.settings;   /* الحذف يعيد إسناد المصفوفة (filter) ⇒ نقرأ الحالية */
    T('no reward/punish records changed', JSON.stringify([S2.rewardItems.map(x=>[x.id, x.room]), S2.punishItems.map(x=>[x.id, x.room])]) === before);

    /* ---- 3. box details use CodisBoxes.effective verbatim ---- */
    CodisBoxes.tiers().forEach(t=>{
      econPackId = t.id; econPackPaint();
      const eff = CodisBoxes.effective(t).filter(o=>o.items.length), dom = Array.from(document.querySelectorAll('#econ-pack-body .pkx-grp'));
      let ok = dom.length === eff.length && eff.reduce((q, o)=>q + o.pm, 0) === 1000;
      dom.forEach(d=>{ const o = eff.find(x=>'pk-g-' + x.id === d.id); if(!o){ ok = false; return; }
        if(d.querySelector('.pkx-gp').textContent !== econPm(o.pm)) ok = false;
        const ids = Array.from(d.querySelectorAll('.pk-tile')).map(x=>x.dataset.id).sort().join(), eids = o.items.map(i=>i.id).sort().join(); if(ids !== eids) ok = false;
        const each = o.pm / 10 / o.items.length, tol = each >= 1 ? .051 : .0051;
        d.querySelectorAll('.pkx-cp').forEach(c=>{ if(Math.abs(parseFloat(c.textContent) - each) > tol) ok = false; }); });
      T('pack ' + t.id + ': groups/probabilities/items match effective()', ok);
      T('pack ' + t.id + ': groups collapsed initially', document.querySelectorAll('#econ-pack-body .pkx-grp[open]').length === 0);
    });
    econPackId = null;

    /* ---- 4. card backs: nothing clipped ---- */
    const back = codisCardBackHtml('اسم مكافأة طويل جداً جداً لاختبار الالتفاف داخل ظهر البطاقة بدون أي قص', [['الفئة', 'نادرة جداً جداً'], ['المصدر', 'بكج خرافي من المتجر'], ['التاريخ', '3 نوفمبر 2026']], { tone:'s', note:'ملاحظة طويلة تشرح طريقة الاستعمال والقيود بالتفصيل حتى تتجاوز سطرين بسهولة' });
    const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:110px;aspect-ratio:4/5;'; host.innerHTML = back; document.body.appendChild(host); await sleep(50);
    const cs = el=>getComputedStyle(el);
    T('card back title not line-clamped', cs(host.querySelector('.cbk-t')).webkitLineClamp === 'none' || cs(host.querySelector('.cbk-t')).display === 'block');
    T('card back values wrap (no ellipsis)', Array.from(host.querySelectorAll('dd')).every(d=>cs(d).textOverflow !== 'ellipsis' && cs(d).whiteSpace !== 'nowrap'));
    T('card back panel scrolls instead of hiding overflow', cs(host.querySelector('.cbk-in')).overflowY === 'auto');
    host.remove();

    /* ---- 5. coin log ---- */
    econOpenStore(); await sleep(700); openSettingsCategory('eco-log'); await sleep(400);
    const w = data.wallet, real = w.transactions, rl = econLogLimit;
    try{
      w.transactions = Array.from({ length:50 }, (_, i)=>({ id:'c' + i, amount:i % 2 ? -5 : 7, reason:'r' + i, createdAt:new Date(Date.now() - (49 - i) * 36e5).toISOString() }));
      econLogLimit = 40; econRenderLog();
      const reasons = Array.from(document.querySelectorAll('.ecl-row .eco-log-reason')).map(e=>e.textContent);
      T('coin log newest first, paginated at 40', reasons.length === 40 && reasons[0] === 'r49' && reasons[39] === 'r10');
      T('coin log grouped by day', document.querySelectorAll('.ecl-day').length >= 2);
      T('more button shows remaining count', /10/.test((document.querySelector('.ecl-more') || {}).textContent || ''));
      w.transactions = []; econRenderLog(); T('coin log empty state', !!document.querySelector('.ecl-empty'));
    } finally { w.transactions = real; econLogLimit = rl; econRenderLog(); }

    /* ---- 6. sold / used ---- */
    const H = CodisHolidayCards;
    H.grant({ uid:'clr_exp', kind:'extra', source:'box', acquiredAt:new Date(Date.now() - 3 * 864e5).toISOString() }); H.sweep(Date.now());
    const rows = econClosedRows(), ex = rows.filter(r=>r.st === 'expired');
    T('expired holiday card classified as expired, not used', ex.length >= 1 && !econMostUsed(rows).some(e=>e.key === 'h:extra' && e.n > rows.filter(r=>r.st === 'used' && r.rk && r.rk.key === 'h:extra').length));
    const mu = econMostUsed([{ st:'used', t:'2', rk:{ key:'r:a', name:'A', type:'x' } }, { st:'used', t:'3', rk:{ key:'r:a', name:'A2', type:'x' } }, { st:'sold', t:'4', rk:null }, { st:'expired', t:'5', rk:null }, { st:'used', t:'1', rk:{ key:'p:daily:HIGH', name:'P', type:'y' } }]);
    T('most-used counts real uses only, merged by stable id', mu.length === 2 && mu[0].key === 'r:a' && mu[0].n === 2 && mu[0].name === 'A2');
    econClosedOpen = true; econClosedView = 'sold'; econRenderStore(); await sleep(100);
    const seen = JSON.stringify(data.closedSeen.used);
    T('opening Sold leaves Used read-state untouched', JSON.stringify(data.closedSeen.used) === seen);
    econClosedSetView('used'); await sleep(100);
    T('used view shows expired section', !!document.querySelector('#eco-cpanel .hx-exp'));
    econClosedOpen = false;
  }catch(e){ T('exception', false, e && e.stack || e); }
  finally{ codisConfirm = realConfirm; }
  const failed = out.filter(x=>!x.ok).length;
  return { passed:out.length - failed, failed, results:out };
})();
