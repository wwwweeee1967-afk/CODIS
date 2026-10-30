#!/usr/bin/env python3
"""CODIS-PLAN-EXTEND (بعد patch_v12.py): الخطة الشغّالة قابلة للإكمال والحفظ بدون حذفها.
 • «أضف للخطة»: نفس المحرّر بوضع إضافة؛ العناصر الجديدة (مهام/تعلّم) تتوزّع على الأيام المتبقية فقط من دورة الخطة نفسها
   (نفس العطلة وأول يوم)، وتُلحق بالأيام بدون تغيير ترتيب الموجود. لو الغرفة ما فيها خطة (نسيت التعلّم كله) تنبني لها خطة بنفس الإيقاع.
   اليوم الحالي يدخل فقط إذا ما انحسمت نتيجته بعد (لا تُغيَّر نتيجة يوم محسوم).
 • «احفظ الخطة»: يحفظ الخطة الشغّالة كقالب في «خططي المحفوظة» من نصّها الأصلي المحفوظ مع الأسبوع (sourceRaw) + ما أُضيف لاحقاً."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-PLAN-EXTEND' in s: sys.exit('already patched (CODIS-PLAN-EXTEND)')

def rep(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('anchor "%s" matched %d times (want %d)' % (label, n, count))
    s = s.replace(old, new)

# ---- markup: أزرار الخطة الشغّالة + صف حفظ ----
rep("""        <div class="plan-actions">
          <button type="button" class="btn btn-destructive" onclick="stopCurrentPlan()">إيقاف الخطة</button>
          <button type="button" class="btn btn-primary" onclick="startNewPlanFromActive()">سوي خطة جديدة</button>
        </div>""",
"""        <div class="plan-tools">
          <button type="button" class="btn btn-secondary" onclick="startExtendPlan()"><svg data-icon="next" data-size="md"></svg>أضف للخطة</button>
          <button type="button" class="btn btn-secondary" onclick="openSaveActivePlan()">احفظ الخطة</button>
        </div>
        <div class="plan-save-active" id="plan-save-active" style="display:none;">
          <div class="row-input">
            <input type="text" id="plan-save-active-name" aria-label="اسم الخطة" placeholder="اسم الخطة" maxlength="60" onkeydown="if(event.key==='Enter') confirmSaveActivePlan()">
            <button type="button" class="btn btn-primary" onclick="confirmSaveActivePlan()">حفظ</button>
            <button type="button" class="btn btn-secondary" onclick="cancelSaveActivePlan()">إلغاء</button>
          </div>
        </div>
        <div class="plan-actions">
          <button type="button" class="btn btn-destructive" onclick="stopCurrentPlan()">إيقاف الخطة</button>
          <button type="button" class="btn btn-primary" onclick="startNewPlanFromActive()">سوي خطة جديدة</button>
        </div>""", 'active card tools')
# ---- markup: شريط وضع الإضافة داخل المحرّر + زر إلغاء ----
rep("""      <div class="write-actions">
        <button type="button" class="btn btn-primary" onclick="handleDistributeClick()">رتّب خطتي<svg data-icon="next" data-size="md"></svg></button>
        <button type="button" class="btn btn-secondary" onclick="openSavePlanPrompt()">حفظ الخطة</button>
      </div>""",
"""      <div class="write-actions">
        <button type="button" class="btn btn-primary" id="plan-distribute-btn" onclick="handleDistributeClick()"><span id="plan-distribute-label">رتّب خطتي</span><svg data-icon="next" data-size="md"></svg></button>
        <button type="button" class="btn btn-secondary" id="plan-save-draft-btn" onclick="openSavePlanPrompt()">حفظ الخطة</button>
        <button type="button" class="btn btn-secondary" id="plan-extend-cancel" style="display:none;" onclick="cancelExtendPlan()">إلغاء</button>
      </div>""", 'editor actions')
rep("""      <div class="write-head">
        <div class="write-head-row">
          <div class="write-title">شنو تريد تنجز؟</div>""",
"""      <div class="plan-extend-note" id="plan-extend-note" style="display:none;" role="status">تُضاف للخطة الشغّالة على أيامها المتبقية — ترتيبك الحالي ما يتغيّر.</div>
      <div class="write-head">
        <div class="write-head-row">
          <div class="write-title" id="plan-write-title">شنو تريد تنجز؟</div>""", 'extend note')

# ---- JS ----
js = r"""
/* ===== CODIS-PLAN-EXTEND — إكمال الخطة الشغّالة وحفظها ===== */
let planExtend = false;
/* نص الخطة كأسطر من عناصر الأسبوع (احتياط للخطط القديمة بلا sourceRaw) */
function planLinesFromWeek(w){
  if(!w) return '';
  if(typeof w.sourceRaw === 'string' && w.sourceRaw.trim()) return w.sourceRaw;
  const lines = Object.keys(w.items || {}).map(k=>{ const it = w.items[k] || {}; if(!it.unit) return ''; return (it.priority === 'high' ? '!' : '') + (Number(it.qty) > 1 ? it.qty + ' ' : '') + it.unit; }).filter(Boolean);
  Object.keys(w.days || {}).forEach(d=>(w.days[d] || []).forEach(t=>{ if(t && !t.itemId && t.text && lines.indexOf(t.text) === -1) lines.push(t.text); }));
  return lines.join('\n');
}
/* أيام الخطة المتبقية بترتيب دورتها: اليوم يدخل فقط إن ما انحسمت نتيجته لتلك الغرفة */
function planRemainingDays(host, room){
  const start = getPlanStartDay(host), hol = host.holidayDay === undefined ? -1 : host.holidayDay, today = new Date().getDay(), wk = currentWeekId();
  const cyc = []; for(let i = 0; i < 7; i++) cyc.push((start + i) % 7);
  const pos = cyc.indexOf(today), L = data.outcomeLedger || {};
  const decided = Object.keys(L).some(k=>{ const e = L[k]; return e && e.scope === 'daily' && e.room === room && e.weekId === wk && e.day === today && e.status !== 'void'; });
  return cyc.filter((d, i)=>i >= pos && d !== hol && holidayExtras(host).indexOf(d) === -1 && !(d === today && decided));
}
function startExtendPlan(){
  if(!currentPlanActive()){ codisSfx('invalid', { ctx:'unavailable' }); return; }
  planExtend = true;
  data.planningDraftPrev = data.planningDraft || { tasksRaw:'', learnRaw:'' };
  data.planningDraft = { tasksRaw:'', learnRaw:'' };
  saveData();
  planningMode = 'authoring';
  activePlanTab = currentWeek() && !learnCurrentWeek() ? 'learn' : 'tasks';   /* نسيت التعلّم؟ يفتح عليه مباشرة */
  closeSavedPlansPanel();
  codisSfx('open', { ctx:'editor' });
  renderPlanningPage();
}
function endExtendPlan(){
  planExtend = false;
  if(data.planningDraftPrev){ data.planningDraft = data.planningDraftPrev; delete data.planningDraftPrev; }
  planningMode = 'idle';
  saveData();
}
function cancelExtendPlan(){ codisSfx('close', { ctx:'editor' }); endExtendPlan(); renderPlanningPage(); }
function paintExtendMode(){
  const on = planExtend && planningMode === 'authoring';
  const set = (id, fn)=>{ const e = document.getElementById(id); if(e) fn(e); };
  set('plan-extend-note', e=>{ e.style.display = on ? '' : 'none'; });
  set('plan-extend-cancel', e=>{ e.style.display = on ? '' : 'none'; });
  set('plan-save-draft-btn', e=>{ e.style.display = on ? 'none' : ''; });
  set('saved-plans-toggle', e=>{ e.style.display = on ? 'none' : ''; });
  set('plan-distribute-label', e=>{ e.textContent = on ? 'أضف للخطة' : 'رتّب خطتي'; });
  set('plan-write-title', e=>{ e.textContent = on ? 'شنو نسيت تضيف؟' : 'شنو تريد تنجز؟'; });
}
/* الإضافة الفعلية: لا أرشفة ولا مسح — إلحاق بالأيام المتبقية فقط */
function extendActivePlan(){
  saveDraftFromInputs();
  const draft = data.planningDraft, taskItems = parsePlanLines(draft.tasksRaw), learnItems = parsePlanLines(draft.learnRaw);
  if(!taskItems.length && !learnItems.length){ codisSfx('invalid', { ctx:'input' }); showToast('اكتب عنصر وحد على الأقل', 'var(--warning)'); return; }
  const wk = currentWeekId(), host = data.weeks[wk] || data.learnWeeks[wk];
  if(!host){ endExtendPlan(); renderPlanningPage(); return; }
  const add = (store, items, raw, room)=>{
    if(!items.length) return 0;
    let w = store[wk];
    if(!w){ const full = {}; for(let i = 0; i < 7; i++) full[i] = []; w = store[wk] = { days:full, startedAt:host.startedAt, items:{}, holidayDay:host.holidayDay, planStartDay:getPlanStartDay(host), planName:host.planName || currentPlanName() }; if(Array.isArray(host.extraHolidays)) w.extraHolidays = host.extraHolidays.slice(); }
    const days = planRemainingDays(w, room); if(!days.length) return -1;
    const r = distributeItemsToDays(items, days);
    Object.keys(r.days).forEach(d=>{ w.days[d] = (w.days[d] || []).concat(r.days[d]); });
    w.items = Object.assign(w.items || {}, r.items_meta);
    w.sourceRaw = [planLinesFromWeek(w === host || w.sourceRaw ? w : null), raw].filter(x=>x && x.trim()).join('\n');
    return items.length;
  };
  const before = { t:data.weeks[wk] ? planLinesFromWeek(data.weeks[wk]) : '', l:data.learnWeeks[wk] ? planLinesFromWeek(data.learnWeeks[wk]) : '' };
  if(data.weeks[wk] && !data.weeks[wk].sourceRaw) data.weeks[wk].sourceRaw = before.t;
  if(data.learnWeeks[wk] && !data.learnWeeks[wk].sourceRaw) data.learnWeeks[wk].sourceRaw = before.l;
  const nt = add(data.weeks, taskItems, draft.tasksRaw, 'tasks'), nl = add(data.learnWeeks, learnItems, draft.learnRaw, 'learn');
  if(nt < 0 || nl < 0){ codisSfx('invalid', { ctx:'unavailable' }); showToast('ما باقي أيام بهالخطة تنضاف لها عناصر', 'var(--warning)'); return; }
  endExtendPlan();
  codisSfx('success', { ctx:'plan' });
  showToast('انضاف للخطة: ' + [nt > 0 ? nt + ' مهمة' : '', nl > 0 ? nl + ' عنصر تعلّم' : ''].filter(Boolean).join(' و'), 'var(--success)', 'check');
  renderTasksPage(); renderLearnPage(); renderPlanningPage();
  if(nl > 0 && !(nt > 0)) navigateToPage('learn'); else goToExecution();
}
/* حفظ الخطة الشغّالة كقالب */
function openSaveActivePlan(){
  const row = document.getElementById('plan-save-active'), inp = document.getElementById('plan-save-active-name'); if(!row || !inp) return;
  const nm = currentPlanName(); inp.value = nm === 'بدون اسم' ? '' : nm;
  row.style.display = ''; playAnim(row); try{ inp.focus(); }catch(e){}
}
function cancelSaveActivePlan(){ const row = document.getElementById('plan-save-active'); if(row) row.style.display = 'none'; }
function confirmSaveActivePlan(){
  const inp = document.getElementById('plan-save-active-name'), name = inp ? inp.value.trim() : '';
  if(!name){ codisSfx('invalid', { ctx:'input' }); showToast('اكتب اسم الخطة', 'var(--warning)'); return; }
  const wk = currentWeekId(), tw = data.weeks[wk], lw = data.learnWeeks[wk];
  const tasksRaw = planLinesFromWeek(tw), learnRaw = planLinesFromWeek(lw);
  if(!tasksRaw.trim() && !learnRaw.trim()){ codisSfx('invalid', { ctx:'unavailable' }); showToast('ماكو عناصر بالخطة تنحفظ', 'var(--warning)'); return; }
  if(!data.plans) data.plans = {};
  const same = Object.keys(data.plans).find(k=>data.plans[k] && data.plans[k].name === name);
  const id = same || ('p' + Date.now());
  data.plans[id] = { name:name, tasksRaw:tasksRaw, learnRaw:learnRaw };
  [tw, lw].forEach(w=>{ if(w) w.planName = name; });
  saveData(); cancelSaveActivePlan(); renderPlanningPage();
  codisSfx('success', { ctx:'plan' });
  showToast((same ? 'تحدّثت الخطة "' : 'انحفظت الخطة "') + name + '"', 'var(--success)', 'check');
}
"""
rep("function goToPlanning(tab){", js.strip('\n') + "\nfunction goToPlanning(tab){", 'js insert')

# الإضافة تعترض التوزيع بدل الأرشفة+الاستبدال
rep("""function distributePlan(){
  saveDraftFromInputs();""", """function distributePlan(){
  if(planExtend && currentPlanActive()) return extendActivePlan();   /* CODIS-PLAN-EXTEND */
  saveDraftFromInputs();""", 'distribute intercept')
# نص الخطة الأصلي يُحفظ مع الأسبوع وقت التوزيع (لحفظها لاحقاً كقالب كما كُتبت)
rep("    data.weeks[wk] = { days: full, startedAt, items: items_meta, holidayDay, planStartDay: todayIdx, planName: planNameAtDistribution };",
    "    data.weeks[wk] = { days: full, startedAt, items: items_meta, holidayDay, planStartDay: todayIdx, planName: planNameAtDistribution, sourceRaw: draft.tasksRaw || '' };", 'tasks sourceRaw')
rep("    data.learnWeeks[wk] = { days: full, startedAt, items: items_meta, holidayDay, planStartDay: todayIdx, planName: planNameAtDistribution };",
    "    data.learnWeeks[wk] = { days: full, startedAt, items: items_meta, holidayDay, planStartDay: todayIdx, planName: planNameAtDistribution, sourceRaw: draft.learnRaw || '' };", 'learn sourceRaw')
# وضع الإضافة يرسم المحرّر بنصوصه الخاصة
rep("""    switchWriteTab(activePlanTab);
    cancelSavePlan();
    return;
  }""", """    switchWriteTab(activePlanTab);
    cancelSavePlan();
    paintExtendMode();
    return;
  }
  if(planExtend){ planExtend = false; paintExtendMode(); }""", 'render extend')
# الرجوع للخلف من المحرّر بوضع الإضافة يلغيه (لا يبقى عالقاً)
rep("  const ha = document.getElementById('habit-add'); if(ha && ha.getAttribute('aria-hidden') === 'false') return { act:closeAddHabit, el:null };",
    "  const ha = document.getElementById('habit-add'); if(ha && ha.getAttribute('aria-hidden') === 'false') return { act:closeAddHabit, el:null };\n  if(planExtend && planningMode === 'authoring'){ const pp = document.getElementById('page-planning'); if(pp && getComputedStyle(pp).display !== 'none') return { act:cancelExtendPlan, el:null }; }", 'back cancels extend')

css = r"""
/* CODIS-PLAN-EXTEND */
#planning-active .plan-tools{ display:grid; grid-template-columns:1fr 1fr; gap:var(--sp-sm, 8px); padding:0 var(--pl-pad, 16px); }
#planning-active .plan-tools .btn{ min-height:44px; display:inline-flex; align-items:center; justify-content:center; gap:6px; white-space:nowrap; }
#planning-active .plan-tools .btn svg{ width:16px; height:16px; }
#planning-active .plan-save-active{ padding:var(--sp-sm, 8px) var(--pl-pad, 16px) 0; }
/* هدف لمس شريحة وزن المهمة كان 28px (أقل من 30) */
.task-item .task-wt{ min-height:32px; }
.plan-extend-note{ margin:0 0 var(--sp-md, 12px); padding:10px 14px; border-radius:12px; font-size:13px; line-height:1.6; color:var(--text-2); background:rgb(var(--hi-rgb) / .05); border:1px solid var(--aqua-a24, rgb(var(--hi-rgb) / .12)); }
"""
rep("</style>", css + "</style>", 'css')
s = s.replace('<!-- CODIS-AUDIT-1 -->', '<!-- CODIS-AUDIT-1 -->\n<!-- CODIS-PLAN-EXTEND -->', 1)
if 'CODIS-PLAN-EXTEND -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v13 OK')
