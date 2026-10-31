#!/usr/bin/env python3
"""CODIS-GRACE (بعد patch_v14.py): مهلة تسجيل الأسبوع الماضي + إعادة فتح خطة أُرشفت تلقائياً.
 الخلل: بمجرد دخول أسبوع جديد (الأحد) كان فتح التطبيق يؤرشف خطة الأسبوع الماضي فوراً ويحسب عقوبة الأسبوع (ثم الشهر عند تغيّر الشهر) من المسجَّل فقط،
        فمن سوّى مهامه بالواقع ولم يسجّلها بعد (نسيها يومين) يدخل فيلقى عقوبات والخطة مؤرشفة.
 الحل: • الخطة القديمة التي فيها مهام بلا جواب تبقى مفتوحة «للتسوية» 3 أيام بعد نهاية أسبوعها (ينقضي الأربعاء 00:00) ولا تُؤرشف ولا تُحسم، ولا يُحسم شهرها قبلها.
       • شريط تنبيه بغرف التخطيط/العمليات/الأستاذ + ورقة «تسوية الأسبوع الماضي» لتسجيل خلصتها/نصها/ما سويتها لكل مهمة؛ إذا اكتمل التسجيل ينحسم الأسبوع بنتيجته الحقيقية (مكتمل).
       • «أنهِ الأسبوع الآن» يحسم فوراً كالسابق. بعد انقضاء المهلة يرجع السلوك التلقائي القديم.
       • «أعد فتح الخطة» بتفاصيل الأرشيف لخطة أُرشفت تلقائياً (stale): إن كانت نتيجة أسبوعها وشهرها لم تُحسم بعد (معلّقة) تُلغى (void مع الأثر) وتعود الخطة مفتوحة 3 أيام. المحسومة لا تُمسّ.
 لا مكافآت يومية تُمنح عن التسجيل المتأخر (يُحتسب فقط بنتيجة الأسبوع والشهر)."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-GRACE' in s: sys.exit('already patched (CODIS-GRACE)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

# 1) منع حسم الشهر قبل أسبوعه المعلّق
rep("""    while(st.nextMonth < cur && guard++ < 36){
      const m = st.nextMonth;""",
"""    const holdMonths = (typeof codisGraceMonthKeys === 'function') ? codisGraceMonthKeys() : new Set();   /* CODIS-GRACE: شهر فيه أسبوع بانتظار التسوية لا يُحسم بعد */
    while(st.nextMonth < cur && guard++ < 36){
      const m = st.nextMonth;
      if(holdMonths.has(m)) break;""", 'processMonths hold')
rep("        if(cnt[mk] >= 4 && mk <= cur && !L()['monthly|' + mk]){", "        if(cnt[mk] >= 4 && mk <= cur && !holdMonths.has(mk) && !L()['monthly|' + mk]){", 'early settle hold')

# 2) دوال المهلة + أرشفة الأسابيع القديمة بعد انقضائها
old_fn = s[s.index("function archiveStaleWeeksIfAny(){"):s.index("/* ---- تتفحص بعد كل تغيير حالة مهمة")]
new_fn = r"""/* ===== CODIS-GRACE ===== */
const GRACE_DAYS = 3;   /* أيام التسجيل بعد نهاية الأسبوع: ينقضي الأربعاء 00:00 */
function graceOpenTasks(w){
  const out = []; if(!w || !w.days) return out;
  for(let d = 0; d < 7; d++){
    if(d === w.holidayDay || holidayExtras(w).indexOf(d) !== -1) continue;
    (w.days[d] || []).forEach(t=>{ if(t && !t.status) out.push({ t:t, d:d }); });
  }
  return out;
}
function graceEndKey(id, tw, lw){
  const base = dateForWeekDay(id, 7 + GRACE_DAYS), ex = [tw && tw.graceUntil, lw && lw.graceUntil].filter(Boolean).sort().pop();
  return ex && ex > base ? ex : base;
}
function graceWeeks(){
  const cur = currentWeekId(), ids = new Set([].concat(Object.keys(data.weeks || {}), Object.keys(data.learnWeeks || {}))), out = [];
  ids.forEach(id=>{
    if(!(id < cur)) return;
    const tw = data.weeks[id], lw = data.learnWeeks[id], open = graceOpenTasks(tw).length + graceOpenTasks(lw).length, until = graceEndKey(id, tw, lw);
    if(open > 0 && todayKey() < until) out.push({ id:id, tw:tw, lw:lw, open:open, until:until });
  });
  return out.sort((a, b)=>a.id < b.id ? -1 : 1);
}
function codisGraceMonthKeys(){ return new Set(graceWeeks().map(g=>g.id.slice(0, 7))); }
function archiveStaleWeeksIfAny(){
  const wk = currentWeekId();
  const staleIds = new Set([
    ...Object.keys(data.weeks||{}),
    ...Object.keys(data.learnWeeks||{})
  ].filter(id=>id!==wk));
  if(staleIds.size===0) return 0;
  const grace = new Set(graceWeeks().map(g=>g.id));   /* بانتظار التسجيل: لا أرشفة ولا عقوبة */
  let count=0;
  staleIds.forEach(id=>{ if(grace.has(id)) return; if(archivePlanForWeek(id,'stopped','stale')) count++; });
  try{ codisGraceBanner(); }catch(e){}
  return count;
}
function codisGraceBanner(){
  const gw = graceWeeks();
  ['page-planning', 'page-tasks', 'page-learn'].forEach(pid=>{
    const pg = document.getElementById(pid); if(!pg) return;
    let b = pg.querySelector('.grace-banner');
    if(!gw.length){ if(b) b.remove(); return; }
    const g = gw[0], last = DAYS_AR[parseKey(addDaysKey(g.until, -1)).getDay()];
    if(!b){
      b = document.createElement('button'); b.type = 'button'; b.className = 'grace-banner'; b.onclick = ()=>openGraceSheet();
      const head = pg.querySelector('.page-head'); if(head) head.insertAdjacentElement('afterend', b); else pg.insertBefore(b, pg.firstChild);
    }
    b.innerHTML = '<span class="gb-t"><b>أسبوعك الماضي ينتظر التسجيل</b><span>' + g.open + ' مهمة بدون جواب — سجّلها قبل نهاية يوم ' + last + ' وإلا تنحسم تلقائياً</span></span><span class="gb-go">سجّل الآن</span>';
  });
}
var graceSheet = null;
function closeGraceSheet(){
  const g = graceSheet; if(!g) return; graceSheet = null;
  document.removeEventListener('keydown', g.onKey, true); g.root.classList.remove('is-open'); codisSfx('close', { ctx:'sheet' });
  setTimeout(()=>g.root.remove(), 220); try{ g.opener && g.opener.isConnected && g.opener.focus({ preventScroll:true }); }catch(e){}
}
function openGraceSheet(){
  if(graceSheet) return; if(!graceWeeks().length) return;
  const root = document.createElement('div'); root.className = 'cd-ov gs-ov';
  root.innerHTML = '<div class="cd-back"></div><div class="cd-sheet" role="dialog" aria-modal="true" aria-label="تسوية الأسبوع الماضي"><div class="cd-grab" aria-hidden="true"></div>' +
    '<div class="cd-head"><h2 class="cd-title">تسوية الأسبوع الماضي</h2><button type="button" class="cd-close" aria-label="إغلاق">' + ICONS.close + '</button></div><div class="cd-body gs-body"></div></div>';
  document.body.appendChild(root);
  const s0 = { root:root, opener:document.activeElement, onKey:ev=>{ if(ev.key === 'Escape'){ ev.stopPropagation(); closeGraceSheet(); } } };
  graceSheet = s0; document.addEventListener('keydown', s0.onKey, true); codisSfx('open', { ctx:'sheet' });
  const body = root.querySelector('.gs-body'); let pendingHalf = null;
  const find = (g, room, id)=>{ const w = room === 'learn' ? g.lw : g.tw; if(!w) return null; for(let d = 0; d < 7; d++){ const t = (w.days[d] || []).find(x=>x && x.id === id); if(t) return t; } return null; };
  const finish = (g, reason)=>{
    const ok = archivePlanForWeek(g.id, reason === 'completed' ? 'completed' : 'stopped', reason === 'completed' ? 'completed' : 'stale');
    try{ renderTasksPage(); renderLearnPage(); renderPlanningPage(); }catch(e){}
    codisGraceBanner();
    if(ok) showToast(reason === 'completed' ? 'اكتمل تسجيل الأسبوع وانحسمت نتيجته' : 'انحسم الأسبوع الماضي', 'var(--success)', 'check');
    return ok;
  };
  const paint = ()=>{
    const gw = graceWeeks(), g = gw[0];
    if(!g){ closeGraceSheet(); return; }
    const last = DAYS_AR[parseKey(addDaysKey(g.until, -1)).getDay()];
    let html = '<p class="gs-note">أسبوع ' + escapeHtml(formatArDate(g.id)) + ' — سجّل اللي سويته فعلاً. ينحسم تلقائياً بنهاية يوم ' + last + '، أو أنهِه الآن.</p>';
    [['tasks', 'غرفة العمليات', g.tw], ['learn', 'غرفة الأستاذ', g.lw]].forEach(r=>{
      const items = graceOpenTasks(r[2]); if(!items.length) return;
      html += '<section class="cd-group"><h3 class="cd-gh"><span>' + r[1] + '</span><span class="cd-gn">' + items.length + '</span></h3>';
      let curD = -1;
      items.forEach(o=>{
        if(o.d !== curD){ curD = o.d; html += '<div class="gs-day">' + DAYS_AR[o.d] + '</div>'; }
        const half = pendingHalf && pendingHalf.id === o.t.id;
        html += '<div class="gs-row" data-room="' + r[0] + '" data-id="' + escapeHtml(String(o.t.id)) + '"><div class="gs-t">' + escapeHtml(o.t.text) + '</div>' +
          (half ? '<div class="gs-btns gs-half"><span>كم أنجزت؟</span>' + [25, 50, 75].map(v=>'<button type="button" data-s="half" data-p="' + v + '">' + v + '%</button>').join('') + '<button type="button" data-s="cancel">إلغاء</button></div>'
                : '<div class="gs-btns"><button type="button" data-s="done" class="is-done">خلصتها</button><button type="button" data-s="half">نصها</button><button type="button" data-s="none" class="is-none">ما سويتها</button></div>') + '</div>';
      });
      html += '</section>';
    });
    html += '<div class="gs-foot"><button type="button" class="btn btn-secondary" id="gs-end">أنهِ الأسبوع الآن</button><button type="button" class="btn btn-quiet" id="gs-later">لاحقاً</button></div>';
    body.innerHTML = html;
    body.querySelectorAll('.gs-btns button').forEach(b=>{ b.onclick = ()=>{
      const row = b.closest('.gs-row'), room = row.dataset.room, id = row.dataset.id, st = b.dataset.s;
      if(st === 'cancel'){ pendingHalf = null; paint(); return; }
      if(st === 'half' && !b.dataset.p){ pendingHalf = { id:id }; paint(); return; }
      const t = find(g, room, id); if(!t || t.status) { paint(); return; }
      codisApplyTaskStatus(t, st, st === 'half' ? { progress:Number(b.dataset.p) } : undefined); t.lateRecorded = true; pendingHalf = null; saveData();
      try{ codisSfx(codisTaskSoundFor(st)); }catch(e){}
      if(!graceWeeks().length || !graceWeeks().some(x=>x.id === g.id)){ closeGraceSheet(); finish(g, 'completed'); return; }
      codisGraceBanner(); paint();
    }; });
    body.querySelector('#gs-end').onclick = async()=>{
      const ok = await codisConfirm({ title:'إنهاء الأسبوع الماضي', icon:'archive', message:'ينحسم الأسبوع الآن بما سجّلته؛ المهام بدون جواب تُحسب غير منجزة، وتظهر نتيجة الأسبوع (والشهر إن انتهى). تكمل؟', confirmText:'أنهِ الأسبوع' });
      if(!ok) return; closeGraceSheet(); finish(g, 'stale');
    };
    body.querySelector('#gs-later').onclick = closeGraceSheet;
  };
  paint();
  root.querySelector('.cd-back').onclick = closeGraceSheet; root.querySelector('.cd-close').onclick = closeGraceSheet;
  requestAnimationFrame(()=>{ root.classList.add('is-open'); });
  setTimeout(()=>root.classList.add('is-open'), 60);
}
/* إعادة فتح خطة أُرشفت تلقائياً (stale) قبل أن تُحسم نتيجتها: تُلغى النتائج المعلّقة (تُحفظ كأثر) وتعود الخطة بمهلة 3 أيام */
function reopenArchiveReason(p){
  if(!p || isArchivedHabit(p) || p.cause !== 'stale' || !p.weekId) return 'ليست خطة أُرشفت تلقائياً';
  if(!(p.weekId < currentWeekId())) return 'خطة الأسبوع الحالي';
  if(data.weeks[p.weekId] || data.learnWeeks[p.weekId]) return 'يوجد أسبوع مفتوح بنفس التاريخ';
  const L = data.outcomeLedger || {}, wid = ['weekly', p.weekId, p.startedAt || ''].join('|'), mid = 'monthly|' + p.weekId.slice(0, 7);
  if(L[wid] && L[wid].status === 'resolved') return 'نتيجة الأسبوع انحسمت بقرارك';
  if(L[mid] && L[mid].status === 'resolved') return 'نتيجة الشهر انحسمت بقرارك';
  return '';
}
function reopenArchivedPlan(id){
  const p = (data.archive || []).find(x=>x.id === id); const why = reopenArchiveReason(p);
  if(why){ codisSfx('invalid', { ctx:'unavailable' }); showToast('ما ينفع إعادة الفتح: ' + why, 'var(--warning)'); return false; }
  const L = data.outcomeLedger, wid = ['weekly', p.weekId, p.startedAt || ''].join('|'), mid = 'monthly|' + p.weekId.slice(0, 7), stamp = Date.now();
  [wid, mid].forEach(k=>{ const e = L[k]; if(e){ L[k + '|reopened|' + stamp] = Object.assign({}, e, { status:'void', voidedBy:'reopen', voidedAt:new Date().toISOString() }); delete L[k]; } });
  const until = addDaysKey(todayKey(), GRACE_DAYS);
  if(p.tasksWeek){ data.weeks[p.weekId] = JSON.parse(JSON.stringify(p.tasksWeek)); data.weeks[p.weekId].graceUntil = until; }
  if(p.learnWeek){ data.learnWeeks[p.weekId] = JSON.parse(JSON.stringify(p.learnWeek)); data.learnWeeks[p.weekId].graceUntil = until; }
  data.archive = data.archive.filter(x=>x.id !== id);
  /* الشهر الذي ينتظر هذا الأسبوع يرجع للمعالجة من جديد (لا نتيجة قديمة تبقى) */
  try{ const m = p.weekId.slice(0, 7); if(data.economyState && data.economyState.nextMonth > m) data.economyState.nextMonth = m; }catch(e){}
  if(!saveData()){ showToast('تعذّر الحفظ — بقيت الخطة بالأرشيف', 'var(--danger)'); return false; }
  closeArchiveDetail(); try{ renderArchiveList(); }catch(e){}
  codisSfx('confirm', { ctx:'restore' }); showToast('رجعت الخطة مفتوحة للتسجيل', 'var(--success)', 'check');
  codisGraceBanner(); setTimeout(openGraceSheet, 350);
  return true;
}
function reopenArchiveDetailPlan(){ if(archiveDetailId) reopenArchivedPlan(archiveDetailId); }

"""
s = s.replace(old_fn, new_fn)

# 3) زر إعادة الفتح بتفاصيل الأرشيف
rep("""      <button type="button" class="btn btn-primary" id="archive-detail-restore" style="display:none;" onclick="restoreArchiveDetailHabit()">استرجاع العادة</button>""",
"""      <button type="button" class="btn btn-primary" id="archive-detail-restore" style="display:none;" onclick="restoreArchiveDetailHabit()">استرجاع العادة</button>
      <button type="button" class="btn btn-primary" id="archive-detail-reopen" style="display:none;" onclick="reopenArchiveDetailPlan()">أعد فتح الخطة للتسجيل</button>""", 'reopen btn')
rep("  if(_restoreBtn) _restoreBtn.style.display = isArchivedHabit(p) ? '' : 'none';",
    "  if(_restoreBtn) _restoreBtn.style.display = isArchivedHabit(p) ? '' : 'none';\n  { const rb = document.getElementById('archive-detail-reopen'); if(rb){ const why = reopenArchiveReason(p); rb.style.display = (!isArchivedHabit(p) && p.cause === 'stale' && p.weekId < currentWeekId()) ? '' : 'none'; rb.disabled = !!why; rb.title = why; rb.textContent = why ? 'إعادة الفتح غير متاحة — ' + why : 'أعد فتح الخطة للتسجيل'; } }", 'detail show reopen')
# 4) الرجوع + البانر عند التنقّل
rep("  if(econBulkZoomEl) return { act:econBulkZoomClose, el:econBulkZoomEl };", "  if(econBulkZoomEl) return { act:econBulkZoomClose, el:econBulkZoomEl };\n  if(graceSheet) return { act:closeGraceSheet, el:graceSheet.root };", 'back grace')
rep("  if(pageChanged) codisSfx('nav', { ctx:page });", "  try{ codisGraceBanner(); }catch(e){}\n  if(pageChanged) codisSfx('nav', { ctx:page });", 'nav banner')

css = r"""
/* CODIS-GRACE */
.grace-banner{ display:flex; align-items:center; justify-content:space-between; gap:12px; width:100%; margin:0 0 var(--sp-md, 12px); padding:12px 14px; border-radius:14px; text-align:start; font:inherit; cursor:pointer; color:var(--text); background:rgb(var(--warning-rgb) / .10); border:1px solid rgb(var(--warning-rgb) / .38); }
.grace-banner:focus-visible{ outline:2px solid var(--warning); outline-offset:2px; }
.gb-t{ display:grid; gap:2px; min-width:0; } .gb-t b{ font-size:14px; } .gb-t span{ font-size:12px; line-height:1.55; color:var(--text-2); }
.gb-go{ flex:none; padding:7px 12px; border-radius:999px; font-size:12.5px; font-weight:800; color:#1a1405; background:var(--warning); }
.gs-note{ margin:0; font-size:12.5px; line-height:1.7; color:var(--text-2); }
.gs-day{ margin:8px 2px 2px; font-size:12px; font-weight:700; color:var(--text-3, var(--text-2)); }
.gs-row{ display:grid; gap:8px; padding:12px; border-radius:14px; background:rgb(var(--hi-rgb) / .04); border:1px solid rgb(var(--hi-rgb) / .07); }
.gs-t{ font-size:14.5px; line-height:1.5; overflow-wrap:anywhere; }
.gs-btns{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:6px; }
.gs-btns button{ min-height:42px; border-radius:10px; border:1px solid rgb(var(--hi-rgb) / .14); background:none; color:var(--text); font:inherit; font-size:13px; font-weight:700; cursor:pointer; }
.gs-btns button.is-done{ border-color:rgb(var(--success-rgb, 80 200 140) / .5); color:var(--success); } .gs-btns button.is-none{ color:var(--danger-ink, var(--danger)); }
.gs-half{ grid-template-columns:auto repeat(4, minmax(0, 1fr)); align-items:center; } .gs-half span{ font-size:12.5px; color:var(--text-2); }
.gs-foot{ display:grid; gap:8px; margin-top:6px; } .gs-foot .btn{ min-height:46px; }
"""
rep("</style>", css + "</style>", 'css')
s = s.replace('<!-- CODIS-PLANCARD -->', '<!-- CODIS-PLANCARD -->\n<!-- CODIS-GRACE -->', 1)
if 'CODIS-GRACE -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v15 OK')
