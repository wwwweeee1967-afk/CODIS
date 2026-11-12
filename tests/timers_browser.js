/* CODIS-TIMERS test (patch_v18.py) — evaluate in the page on a FRESH guest origin (fetch+eval). Mutates local test data only.
   Covers: duration parser · reward timers via the real purchase path · purchase cinematic level = paid price · Use/Store ·
   no double timer / no selling while running · completion → used + exactly one notification · task timers · drag commit · store peek. */
(async function(){ try{
  /* 3.30.0: نموذج الإضافة اليدوي أُزيل من الواجهة (الإضافة الجديدة تلقائية فقط)؛ الاختبار يركّبه كأداة لاختبار المحرر/الستيكر/الحفظ */
  const legacyAdd = (period)=>{ let h = document.getElementById('reward-add-box'); if(!h){ h = document.createElement('div'); h.id = 'reward-add-box'; h.style.cssText = 'position:fixed;left:-9999px;top:0'; document.body.appendChild(h); } h.innerHTML = econRewardEditor('eco-new-r', null) + '<button type="button" class="btn btn-primary eco-full" onclick="econAddReward()">إضافة المكافأة</button>'; h.dataset.ready = '1'; const sel = document.getElementById('eco-new-r-room'); sel.value = period === 'daily' ? settingsDailyRoom : period; econRewardRarityChanged('eco-new-r'); };
  legacyAdd('daily');
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};

  /* ---- 1) parser ---- */
  const P = t=>{ const d = CodisDuration.parse(t); return d ? d.min : null; };
  [['ساعة سوشل ميديا', 60], ['ساعة سوشيال ميديا', 60], ['نصف ساعة قراءة', 30], ['نص ساعة مشي', 30], ['30 دقيقة راحة', 30], ['ساعتان لعب', 120], ['ساعتين لعب', 120],
   ['تمرين 10 دقايق', 10], ['10 دقائق تأمل', 10], ['قراءة 20 دقيقة', 20], ['دراسة ساعة', 60], ['مشي نصف ساعة', 30], ['1 hour', 60], ['2 hours gaming', 120], ['10 minutes', 10],
   ['ساعة ونص نتفلكس', 90], ['ربع ساعة', 15], ['عشر دقايق', 10], ['ثلاث ساعات', 180], ['٣٠ دقيقة', 30], ['20 min walk', 20], ['half an hour', 30], ['1.5 ساعة', 90]
  ].forEach(([t, m])=>T('parse «' + t + '» = ' + m, P(t) === m, P(t)));
  ['بركر', 'سيارة 2020', 'قراءة 20 صفحة', 'ساعة يد', 'ساعة جديدة', 'iPhone 15', '5 كيلو', 'ساعه ابل', ''].forEach(t=>T('no timer for «' + t + '»', P(t) === null, P(t)));
  T('strip «تمرين 10 دقايق» → تمرين', CodisDuration.strip('تمرين 10 دقايق') === 'تمرين', CodisDuration.strip('تمرين 10 دقايق'));
  T('strip «ساعة سوشل ميديا» → سوشل ميديا', CodisDuration.strip('ساعة سوشل ميديا') === 'سوشل ميديا', CodisDuration.strip('ساعة سوشل ميديا'));
  T('plan task «20 دقيقة قراءة» (qty in text)', (CodisDuration.forTask({ text:'20 دقيقة قراءة', unit:'دقيقة قراءة', qty:20 }) || {}).min === 20);
  T('task weight estimate unchanged by the new layer', typeof codisParseMinutes === 'function' && codisParseMinutes('ساعة قراءة', 2).min === 120);

  /* ---- 2) a timed reward bought in the store ---- */
  openSettingsCategory('rewards'); settingsRoom = 'tasks'; econRenderRewards(); await sleep(200);
  const f = (id, v)=>{ document.getElementById('eco-new-r-' + id).value = v; };
  const addR = name=>{ f('name', name); econAddReward(); return data.settings.rewardItems.find(x=>x.name === name); };
  const timed = addR('ساعة سوشل ميديا'), plain = addR('بركر تجربة');
  T('timed reward added in settings', !!timed && !!plain);
  T('settings list shows the duration badge', !!document.querySelector('.dur-badge'));
  data.wallet.balance = 500000; saveData(); econOpenStore(); await sleep(900);
  const inv0 = CodisInventory.all().length, bal0 = data.wallet.balance, price = CodisEconomy.storePrice(timed);
  await econBuy(timed.id); await sleep(150);
  const st = CodisBuyCine._state(), copies = CodisInventory.all().slice(inv0);
  T('balance deducted exactly once (price ' + price + ')', data.wallet.balance === bal0 - price, bal0 - data.wallet.balance);
  T('exactly one owned copy added', copies.length === 1 && copies[0].status === 'owned' && copies[0].paid === price);
  T('cinematic opened after the purchase completed', !!st && st.uid === copies[0].uid);
  T('cinematic level = level of the PAID price', !!st && st.root.classList.contains('lv-' + CodisRevealLevels.levelOfValue(price)), st && st.root.className);
  T('scene announces the timer', !!st && /مؤقت ساعة/.test(st.root.querySelector('.bcx-ticket').textContent) && /يبدأ مؤقت ساعة/.test(st.root.querySelector('.bcx-use').getAttribute('aria-label')));
  await sleep(2600);
  T('Use / Store appear after the reveal', !!st && !st.root.querySelector('.bcx-acts').hidden);
  const uid = copies[0].uid;
  st.root.querySelector('.bcx-use').click(); st.root.querySelector('.bcx-use').click(); await sleep(450);
  const run = CodisTimers.active('reward', uid);
  T('Use started one 60-minute timer on that copy', !!run && run.minutes === 60 && CodisTimers.all().filter(t=>t.ref === uid).length === 1);
  T('cinematic closed and cleaned up', !document.querySelector('.bcx') && !CodisBuyCine.isOpen());
  T('timer uses absolute endsAt', !!run && Math.abs(run.endsAt - run.startedAt - 3600000) < 5);
  T('selling while running is refused', CodisEconomy.sell(uid).reason === 'inuse');
  econRenderAll(); await sleep(100);
  T('owned card shows a live countdown, sell disabled', !!document.querySelector('#eco-store-body .tmr-chip[data-tmr-end="' + run.endsAt + '"]'));
  await econUse(uid); await sleep(50);
  T('using again does not start a second timer', CodisTimers.all().filter(t=>t.ref === uid).length === 1);
  T('timer persisted in storage', (JSON.parse(CodisStorage.read(STORE_KEY)).codisTimers.items || []).some(t=>t.id === run.id && t.state === 'running'));
  /* انتهاء: نقدّم الوقت (نفس endsAt المطلق) ثم tick مرتين */
  const nBefore = data.notifications.items.filter(n=>n.uniqueKey === 'timer|' + run.ev).length;
  CodisTimers._shift(run.id, -3601000); CodisTimers.tick(); CodisTimers.tick(); await sleep(50);
  const done = CodisTimers.all().find(t=>t.id === run.id);
  T('timer completed', done && done.state === 'done' && done.notified);
  T('reward marked used on completion', CodisInventory.get(uid).status === 'used');
  T('exactly one notification record for the event', nBefore === 0 && data.notifications.items.filter(n=>n.uniqueKey === 'timer|' + run.ev).length === 1 &&
    /انتهى وقت مكافأة ساعة سوشل ميديا/.test(data.notifications.items.find(n=>n.uniqueKey === 'timer|' + run.ev).message));

  /* ---- 3) Store keeps it owned · a plain reward is used at once ---- */
  await econBuy(timed.id); await sleep(150);
  const st2 = CodisBuyCine._state(), uid2 = st2 && st2.uid; await sleep(2600);
  st2.root.querySelector('.bcx-keep').click(); await sleep(450);
  T('Store: closed, still owned, no timer', !CodisBuyCine.isOpen() && CodisInventory.get(uid2).status === 'owned' && !CodisTimers.active('reward', uid2));
  await econBuy(plain.id); await sleep(150);
  const st3 = CodisBuyCine._state(), uid3 = st3 && st3.uid; await sleep(2600);
  T('plain reward: no timer label', st3 && !st3.root.querySelector('.bcx-tmr') && !st3.root.querySelector('.bcx-use').getAttribute('aria-label'));
  st3.root.querySelector('.bcx-use').click(); await sleep(450);
  T('plain reward: Use marks it used immediately', CodisInventory.get(uid3).status === 'used' && !CodisTimers.latest('reward', uid3));
  /* closing with Escape = store */
  await econBuy(timed.id); await sleep(200);
  const st4 = CodisBuyCine._state(); st4.root.dispatchEvent(new KeyboardEvent('keydown', { key:'Escape', bubbles:true })); await sleep(450);
  T('Escape mid-reveal keeps the reward owned', !CodisBuyCine.isOpen() && CodisInventory.get(st4.uid).status === 'owned');

  /* ---- 4) levels escalate by price ---- */
  const lv = [];
  for(const p of [50, 150, 300, 500, 700, 1000, 2000, 5000, 9000]){ const ok = CodisBuyCine.play({ ok:true, price:p, owned:{ uid:'fake', name:'x' } }, plain); lv.push(ok && CodisBuyCine._state().root.className); CodisBuyCine.keep(); await sleep(380); }
  T('nine price levels map to lv-1 … lv-9', lv.every((c, i)=>c && c.indexOf('lv-' + (i + 1)) !== -1), lv.join(' | '));

  /* ---- 5) task timers ---- */
  if(!currentWeek()){
    const btn = (root, txt)=>[...document.querySelectorAll(root + ' button')].find(b=>b.getClientRects().length && b.innerText.includes(txt));
    document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(600);
    btn('#page-planning', 'ابدأ بناء الخطة').click(); await sleep(500);
    const ti = document.getElementById('plan-tasks-input'); ti.value = '1- 40 دقيقة قراءة\n2- مراجعة الملاحظات'; ti.dispatchEvent(new Event('input', { bubbles:true }));
    document.getElementById('plan-learn-input').value = ''; switchWriteTab('tasks'); distributePlan(); await sleep(800);
  }
  { const w = currentWeek(), all = w ? Object.keys(w.days).reduce((a, k)=>a.concat(w.days[k] || []), []) : [];
    const pt = all.find(t=>/دقيقة قراءة/.test(t.text));
    T('plan-distributed timed task gets a timer', !!pt && codisTaskTimerHtml(pt).indexOf('ابدأ المهمة') !== -1, pt && pt.text);
    const pn = all.find(t=>/مراجعة الملاحظات/.test(t.text));
    T('plan task without duration gets none', !!pn && codisTaskTimerHtml(pn) === ''); }
  navigateToPage('tasks'); await sleep(400);
  activeDayIdx = new Date().getDay(); renderTasksPage(); await sleep(200);
  const week = currentWeek();
  if(week){
    const inp = document.getElementById('manual-task-input');
    const add = t=>{ inp.value = t; addManualTask(); };
    add('تمرين 10 دقايق'); add('قراءة كتاب'); add('مشي نصف ساعة'); await sleep(300);
    const day = week.days[activeDayIdx], tEx = day.find(t=>t.text === 'تمرين 10 دقايق'), tNo = day.find(t=>t.text === 'قراءة كتاب');
    const rowOf = t=>document.querySelector('#day-task-list .task-item[data-tid="' + t.id + '"]');
    T('timed task shows «ابدأ المهمة»', !!rowOf(tEx).querySelector('.tt-start') && /10 دقائق/.test(rowOf(tEx).querySelector('.tt-start').textContent));
    T('task without a duration has no timer button', !rowOf(tNo).querySelector('.tt-row'));
    rowOf(tEx).querySelector('.tt-start').click(); rowOf(tEx).querySelector('.tt-start, .tt-stop') && 0; await sleep(80);
    const tr = CodisTimers.active('task', tEx.id);
    T('start → running 10 minutes, row switches to countdown', !!tr && tr.minutes === 10 && !!rowOf(tEx).querySelector('.tt-row.is-run [data-tmr-left]'));
    T('task label for the notification', tr && tr.label === 'تمرين', tr && tr.label);
    renderTasksPage(); await sleep(50);
    T('after re-render the countdown is restored (same endsAt)', !!rowOf(tEx).querySelector('.tt-clock[data-tmr-end="' + tr.endsAt + '"]'));
    T('task status untouched by starting', tEx.status === null);
    CodisTimers._shift(tr.id, -601000); CodisTimers.tick(); CodisTimers.tick(); await sleep(50);
    T('task timer done, row shows finished state', CodisTimers.latest('task', tEx.id).state === 'done' && !!rowOf(tEx).querySelector('.tt-row.is-done'));
    T('finishing the timer does not mark the task done', tEx.status === null);
    T('one notification for the task event', data.notifications.items.filter(n=>n.uniqueKey === 'timer|' + tr.ev).length === 1 && /انتهى الوقت المحدد لمهمة تمرين/.test(data.notifications.items.find(n=>n.uniqueKey === 'timer|' + tr.ev).message));

    /* ---- 6) drag reorder commits to the day array ---- */
    const ids0 = week.days[activeDayIdx].map(t=>t.id), vis = Array.prototype.map.call(document.querySelectorAll('#day-task-list > .task-item'), e=>e.dataset.tid);
    const last = vis.length - 1, movedId = vis[last];
    T('drag: moved via the same save path', CodisTaskDrag._move('tasks', last, 0));
    const ids1 = week.days[activeDayIdx].map(t=>t.id);
    T('drag: the task is first among visible tasks in data', ids1.filter(id=>vis.indexOf(id) !== -1)[0] === movedId);
    T('drag: same set of tasks, nothing lost', ids1.length === ids0.length && ids1.slice().sort().join() === ids0.slice().sort().join());
    { const sv = JSON.parse(CodisStorage.read(STORE_KEY)), sd = Object.keys(sv.weeks).map(k=>sv.weeks[k]).map(w=>w.days && w.days[activeDayIdx]).find(dd=>dd && dd.some(t=>t.id === movedId));
      T('drag: persisted to storage', !!sd && sd.map(t=>t.id).filter(id=>vis.indexOf(id) !== -1)[0] === movedId); }
    renderTasksPage(); await sleep(50);
    T('drag: order survives a re-render', document.querySelector('#day-task-list > .task-item').dataset.tid === movedId);
    T('task cards do not allow text selection', getComputedStyle(document.querySelector('#day-task-list .task-item')).userSelect === 'none');
    T('input still allows text selection', getComputedStyle(document.getElementById('manual-task-input')).userSelect !== 'none');
  } else T('a running week exists for task tests (start a plan first)', false);

  /* ---- 7) store peek ---- */
  econOpenStore(); await sleep(900);
  const card = document.querySelector('#eco-store-body .shop-card[data-id]');
  if(card){
    const grid = card.parentNode, idx = Array.prototype.indexOf.call(grid.children, card);
    CodisCardPeek._open(card); await sleep(650); document.getAnimations().forEach(a=>{ try{ a.finish(); }catch(e){} });   /* الجزء المخفي من الجلسة لا يرسم إطارات: نُنهي الحركة يدوياً */
    T('peek: overlay open with the real card', CodisCardPeek.isOpen() && document.querySelector('.peek .shop-card') === card && !!grid.querySelector('.peek-ph'));
    const flyEl = document.querySelector('.peek-fly'), r = (flyEl || card).getBoundingClientRect();   /* CODIS-OFFLINE: الغلاف peek-fly هو المقيس (البطاقة بداخله zoom) */
    const ob = document.querySelector('.peek').getBoundingClientRect();
    T('peek: card centred in the app frame and enlarged', Math.abs((r.left + r.width / 2) - (ob.left + ob.width / 2)) < 30 && r.width > 120, Math.round(r.left + r.width / 2) + ' / ' + Math.round(ob.left + ob.width / 2));
    CodisCardPeek.close(); await sleep(500);
    T('peek: card back in its slot, overlay removed', !CodisCardPeek.isOpen() && !document.querySelector('.peek') && !grid.querySelector('.peek-ph') && grid.children[idx] === card && !card.style.transform && !card.style.zoom && !grid.querySelector('.peek-fly'));
  } else T('store has a card to peek', false);
  /* CODIS-PEEK-ALL: كل أنواع عناصر المتجر + عنصر «مستقبلي» يُضاف لقائمة + النقرة القصيرة على البكج باقية */
  { const body = document.getElementById('eco-store-body'), kinds = {};
    Array.prototype.forEach.call(body.querySelectorAll('[role="list"] > *'), it=>{ const k = String(it.className).split(' ').filter(c=>/^(bx-card|cos-tile|hcd-shop|shop-card)$/.test(c)).pop() || String(it.className).split(' ')[0]; if(!kinds[k] && it.getBoundingClientRect().height > 40) kinds[k] = it; });
    for(const k of Object.keys(kinds)){
      const it = kinds[k], grid = it.parentNode, idx = Array.prototype.indexOf.call(grid.children, it);
      CodisCardPeek._open(it); await sleep(600);
      const okOpen = CodisCardPeek.isOpen() && Array.prototype.every.call(it.querySelectorAll('.btn, .chip-act'), b=>getComputedStyle(b).visibility === 'hidden');
      CodisCardPeek.close(); await sleep(520);
      T('peek works for store item kind: ' + k, okOpen && grid.children[idx] === it && !document.querySelector('.peek, .peek-ph'));
    }
    const list = body.querySelector('[role="list"]'), fut = document.createElement('div');
    fut.setAttribute('role', 'listitem'); fut.className = 'future-tile'; fut.innerHTML = '<div style="height:90px;background:#334">جديد</div><button type="button" class="btn">شراء</button>';
    list.appendChild(fut); fut.scrollIntoView({ block:'center' }); await sleep(250);
    const fr = fut.firstChild.getBoundingClientRect(), o = { bubbles:true, cancelable:true, pointerId:31, pointerType:'touch', clientX:fr.left + fr.width / 2, clientY:fr.top + 30, isPrimary:true };
    fut.firstChild.dispatchEvent(new PointerEvent('pointerdown', o)); await sleep(520); fut.firstChild.dispatchEvent(new PointerEvent('pointerup', o)); await sleep(600);
    T('a future item added to any store list gets the preview automatically', CodisCardPeek.isOpen() && getComputedStyle(fut.querySelector('.btn')).visibility === 'hidden');
    CodisCardPeek.close(); await sleep(520); fut.remove();
    const btnFut = document.createElement('div'); btnFut.setAttribute('role', 'listitem'); btnFut.innerHTML = '<div style="height:90px"></div><button type="button" class="btn">x</button>'; list.appendChild(btnFut);
    const br = btnFut.querySelector('.btn').getBoundingClientRect(), ob = { bubbles:true, cancelable:true, pointerId:32, pointerType:'touch', clientX:br.left + 5, clientY:br.top + 5, isPrimary:true };
    btnFut.querySelector('.btn').dispatchEvent(new PointerEvent('pointerdown', ob)); await sleep(520); btnFut.querySelector('.btn').dispatchEvent(new PointerEvent('pointerup', ob));
    T('long press on a buy/action button never opens the preview', !CodisCardPeek.isOpen()); btnFut.remove();
    const bx = body.querySelector('.bx-card .bx-open');
    if(bx){ bx.scrollIntoView({ block:'center' }); await sleep(250); const rr = bx.getBoundingClientRect(), oo = { bubbles:true, cancelable:true, pointerId:33, pointerType:'touch', clientX:rr.left + rr.width / 2, clientY:rr.top + rr.height / 2, isPrimary:true };
      bx.dispatchEvent(new PointerEvent('pointerdown', oo)); await sleep(90); bx.dispatchEvent(new PointerEvent('pointerup', oo)); bx.click(); await sleep(700);
      const m = document.getElementById('econ-pack-modal'), opened = !!m && CodisMotion.isOpen(m);   /* النقر على البكج يفتح معاينة البكج (econPackOpen) */
      T('a short tap on a pack still opens its preview (long press did not steal taps)', opened && !CodisCardPeek.isOpen());
      if(opened){ try{ econPackClose(); }catch(e){} await sleep(500); } } }

  const failed = out.filter(x=>!x.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed, results:out };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
