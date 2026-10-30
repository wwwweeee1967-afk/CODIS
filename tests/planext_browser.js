/* CODIS-PLAN-EXTEND test — evaluate in the page (fresh guest origin). Drives the real planning UI. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
  const wk = currentWeekId(), today = new Date().getDay();
  const btn = (root, txt)=>[...document.querySelectorAll(root + ' button')].find(b=>b.getClientRects().length && b.innerText.includes(txt));
  /* 1) a tasks-only plan through the real editor */
  document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(600);
  btn('#page-planning', 'إضافة خطة').click(); await sleep(500);
  const ti = document.getElementById('plan-tasks-input'); ti.value = '1- 14 صفحة مراجعة\n2- !تقرير المبيعات\n3- اتصال بالعائلة'; ti.dispatchEvent(new Event('input', { bubbles:true }));
  document.getElementById('plan-learn-input').value = ''; switchWriteTab('tasks'); distributePlan(); await sleep(700);
  const tw0 = JSON.parse(JSON.stringify(data.weeks[wk]));
  T('plan distributed (tasks only), learn room empty', !!data.weeks[wk] && !data.learnWeeks[wk]);
  T('original plan text kept with the week', /تقرير المبيعات/.test(data.weeks[wk].sourceRaw || ''));
  document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(600);
  T('active plan shows «أضف للخطة» and «احفظ الخطة»', !!btn('#planning-active', 'أضف للخطة') && !!btn('#planning-active', 'احفظ الخطة'));
  /* 2) forgot the learning room: extend */
  btn('#planning-active', 'أضف للخطة').click(); await sleep(500);
  T('extend mode: editor opens on the learn tab with the right labels', planExtend && activePlanTab === 'learn' && document.getElementById('plan-distribute-label').textContent === 'أضف للخطة' && getComputedStyle(document.getElementById('plan-extend-note')).display !== 'none');
  T('extend mode starts with an empty editor', document.getElementById('plan-tasks-input').value === '' && document.getElementById('plan-learn-input').value === '');
  handleDistributeClick(); await sleep(300);
  T('empty extension is refused, plan untouched', JSON.stringify(data.weeks[wk]) === JSON.stringify(tw0) && !data.learnWeeks[wk]);
  const li = document.getElementById('plan-learn-input'); li.value = '1- 3 دروس إنجليزي\n2- قراءة مقال'; li.dispatchEvent(new Event('input', { bubbles:true }));
  handleDistributeClick(); await sleep(800);
  const lw = data.learnWeeks[wk], tw = data.weeks[wk];
  T('learn week created with the same rhythm (start day, holiday, name)', !!lw && lw.planStartDay === tw.planStartDay && lw.holidayDay === tw.holidayDay && lw.planName === tw.planName);
  T('tasks week unchanged (same tasks, same order)', JSON.stringify(tw.days) === JSON.stringify(tw0.days));
  const learnDays = Object.keys(lw.days).filter(d=>lw.days[d].length).map(Number);
  T('learn items only on remaining plan days, never on the holiday', learnDays.every(d=>d !== lw.holidayDay) && learnDays.length > 0, learnDays.join(','));
  T('extend mode closed, plan still active', !planExtend && planningMode === 'idle' && currentPlanActive());
  /* 3) add more tasks: appended, existing order kept */
  document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(500);
  btn('#planning-active', 'أضف للخطة').click(); await sleep(400);
  switchWriteTab('tasks'); const t2 = document.getElementById('plan-tasks-input'); t2.value = '1- غسل السيارة'; t2.dispatchEvent(new Event('input', { bubbles:true }));
  handleDistributeClick(); await sleep(700);
  const tw2 = data.weeks[wk]; let kept = true;
  Object.keys(tw0.days).forEach(d=>{ const a = tw0.days[d].map(t=>t.id), b = tw2.days[d].map(t=>t.id); if(JSON.stringify(b.slice(0, a.length)) !== JSON.stringify(a)) kept = false; });
  T('new task appended after the existing ones (nothing reordered)', kept && Object.values(tw2.days).some(l=>l.some(t=>t.text === 'غسل السيارة')));
  /* 4) a day whose outcome is decided does not receive new items */
  data.outcomeLedger['test|decided'] = { id:'test|decided', scope:'daily', room:'tasks', weekId:wk, day:today, kind:'reward', status:'resolved' }; saveData();
  document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(500);
  btn('#planning-active', 'أضف للخطة').click(); await sleep(400); switchWriteTab('tasks');
  const t3 = document.getElementById('plan-tasks-input'); t3.value = '1- مهمة بعد الحسم'; t3.dispatchEvent(new Event('input', { bubbles:true }));
  const todayBefore = (data.weeks[wk].days[today] || []).length; handleDistributeClick(); await sleep(700);
  T('today is skipped once its outcome is decided', (data.weeks[wk].days[today] || []).length === todayBefore && Object.values(data.weeks[wk].days).some(l=>l.some(t=>t.text === 'مهمة بعد الحسم')));
  delete data.outcomeLedger['test|decided']; saveData();
  /* 5) cancel restores the previous draft */
  data.planningDraft = { tasksRaw:'مسودة قديمة', learnRaw:'' }; saveData();
  document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(500);
  btn('#planning-active', 'أضف للخطة').click(); await sleep(400);
  CodisNav.back(); await sleep(400);
  T('back/cancel leaves extend mode and restores the old draft', !planExtend && planningMode === 'idle' && data.planningDraft.tasksRaw === 'مسودة قديمة');
  /* 6) save the running plan as a template */
  btn('#planning-active', 'احفظ الخطة').click(); await sleep(300);
  const nm = document.getElementById('plan-save-active-name'); nm.value = 'خطتي المرتبة'; confirmSaveActivePlan(); await sleep(300);
  const saved = Object.values(data.plans).find(p=>p.name === 'خطتي المرتبة');
  T('running plan saved as a template', !!saved);
  T('template has original + added tasks', saved && /تقرير المبيعات/.test(saved.tasksRaw) && /غسل السيارة/.test(saved.tasksRaw) && /مهمة بعد الحسم/.test(saved.tasksRaw), saved && saved.tasksRaw);
  T('template has the added learning items', saved && /دروس إنجليزي/.test(saved.learnRaw) && /قراءة مقال/.test(saved.learnRaw), saved && saved.learnRaw);
  T('plan name updated on the running plan', currentPlanName() === 'خطتي المرتبة');
  btn('#planning-active', 'احفظ الخطة').click(); await sleep(200); confirmSaveActivePlan(); await sleep(200);
  T('saving again with the same name updates, no duplicate', Object.values(data.plans).filter(p=>p.name === 'خطتي المرتبة').length === 1);
  const pid = Object.keys(data.plans).find(k=>data.plans[k].name === 'خطتي المرتبة'), lines = parsePlanLines(data.plans[pid].tasksRaw);
  T('template lines parse back (priority + quantity kept)', lines.some(l=>l.priority === 'high' && /تقرير/.test(l.unit)) && lines.some(l=>l.qty === 14), JSON.stringify(lines));
  T('everything persisted', JSON.parse(localStorage.getItem(STORE_KEY)).plans[pid].name === 'خطتي المرتبة');
  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
