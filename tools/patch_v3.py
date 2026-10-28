#!/usr/bin/env python3
"""CODIS-V3 (يعمل بعد patch_v2.py): إعادة تصميم غرفة التأديب — بطاقة عادة بتسلسل بصري واضح:
  الصف الأول: حلقة السلسلة · الاسم + الوسوم + الحالة + 3 أرقام أساسية · زر الإجراء الرئيسي الكبير
  تحته: أزرار «قاومت / نجحت / أخفقت» عند وجودها، ثم زر «التفاصيل» يفتح (طيّ سلس) الإحصاءات الكاملة والسجل ونقل العادة للأرشيف.
  الوظائف كلها باقية (نفس الدوال والمعرّفات). الاستخدام: python tools/patch_v3.py <in.html> <out.html>"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-V3-ROOM' in s: sys.exit('already patched (CODIS-V3-ROOM)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

# ---- markup ----
rep("""  row.innerHTML = `
    <div class="streak-ring">${habitRingSvg(frac)}<span class="streak-num">${ringNum}</span></div>
    <div class="habit-body">
      <div class="habit-name ${nameDone?'done':''}">${escapeHtml(h.text)} ${pills}</div>
      ${extra}
      <div class="habit-meta is-ar">${meta}</div>
      ${habitHistoryHtml(h)}
    </div>
    ${action}
    <button type="button" class="task-del" aria-label="نقل العادة للأرشيف" title="نقل العادة للأرشيف">${ICONS.trash}</button>
    ${acts}`;""",
"""  /* CODIS-V3-ROOM: 3 أرقام أساسية ظاهرة؛ الباقي داخل «التفاصيل» (إفصاح تدريجي) */
  let glance = '';
  if(h.type==='E'){ const sk = buildStreak(h); glance = '<span>سلسلة <b>'+sk+'</b></span><span>الأفضل <b>'+Math.max(bestStreak(h),sk)+'</b></span><span>أيام <b>'+habitDoneDays(h).length+'</b></span>'; }
  else if(h.type==='W'){ glance = '<span>هذا الأسبوع <b>'+weekCount(h,currentWeekId())+' / '+h.requiredPerWeek+'</b></span>'; }
  else { glance = '<span>أفضل <b>'+Math.max(h.bestDays||0, hDays(h))+'</b> يوم</span><span>وقوع <b>'+h.occurrences.length+'</b></span>'; }
  const openNow = hbOpenSet.has(h.id);
  if(openNow) row.classList.add('is-open');
  row.innerHTML = `
    <div class="streak-ring">${habitRingSvg(frac)}<span class="streak-num">${ringNum}</span></div>
    <div class="habit-body">
      <div class="habit-name ${nameDone?'done':''}">${escapeHtml(h.text)}</div>
      <div class="hb-tags">${pills}</div>
      ${extra}
      <div class="hb-glance">${glance}</div>
    </div>
    ${action}
    ${acts}
    <button type="button" class="hb-more-toggle" aria-expanded="${openNow}"><span>التفاصيل</span><span class="hb-chev" aria-hidden="true">${ICONS.forward}</span></button>
    <div class="hb-more" aria-hidden="${!openNow}"${openNow ? '' : ' inert'}><div class="hb-more-clip">
      <div class="habit-meta is-ar">${meta}</div>
      ${habitHistoryHtml(h)}
      <button type="button" class="task-del hb-archive" aria-label="نقل العادة للأرشيف" title="نقل العادة للأرشيف">${ICONS.trash}<span>نقل للأرشيف</span></button>
    </div></div>`;
  { const tg = row.querySelector('.hb-more-toggle'), mo = row.querySelector('.hb-more');
    tg.onclick = ()=>{ const on = !row.classList.contains('is-open'); row.classList.toggle('is-open', on); tg.setAttribute('aria-expanded', on); mo.setAttribute('aria-hidden', !on); if(on){ mo.removeAttribute('inert'); hbOpenSet.add(h.id); } else { mo.setAttribute('inert', ''); hbOpenSet.delete(h.id); } }; }""", 'row template')
rep("function renderHabitRow(h){", "const hbOpenSet = new Set();   /* بطاقات «التفاصيل» المفتوحة (حالة واجهة فقط، لا تُحفظ) */\nfunction renderHabitRow(h){", 'hbOpenSet')

# ---- css ----
css = r"""
/* CODIS-V3-ROOM — غرفة التأديب: تسلسل بصري واضح، تباعد مريح، تفاصيل قابلة للطي */
#page-habits #build-habit-list, #page-habits #quit-habit-list{ display:flex; flex-direction:column; gap:14px; }
#page-habits .disc-toolbar{ margin:18px 0 14px; }
#page-habits .habit-card{ grid-template-columns:auto minmax(0,1fr) auto; column-gap:14px; row-gap:12px; padding:18px 16px 12px; align-items:center; }
#page-habits .habit-card.is-abstain{ grid-template-columns:auto minmax(0,1fr) auto; }
#page-habits .habit-body{ display:flex; flex-direction:column; gap:6px; grid-column:2; grid-row:1; min-width:0; }
#page-habits .habit-body{ text-align:start; align-items:flex-start; }
#page-habits .habit-body > *{ grid-column:auto; }
#page-habits .hb-chev svg{ width:14px; height:14px; }
#page-habits .habit-card .habit-name{ grid-column:auto; grid-row:auto; align-self:flex-start; font-size:17px; font-weight:700; line-height:1.4; }
#page-habits .hb-tags{ display:flex; flex-wrap:wrap; gap:6px; }
#page-habits .hb-tags .pill{ margin:0; padding:3px 9px; font-size:11px; }
#page-habits .habit-body .hb-state{ margin-top:0; font-size:13px; line-height:1.55; color:var(--text-2); }
#page-habits .hb-glance{ display:flex; flex-wrap:wrap; gap:4px 14px; font-size:12.5px; color:var(--text-3); }
#page-habits .hb-glance b{ color:var(--text); font-weight:700; font-variant-numeric:tabular-nums; }
#page-habits .habit-card > .stat-btn, #page-habits .habit-card > .hb-fell{ grid-column:3; grid-row:1; width:52px; height:52px; min-width:52px; border-radius:50%; }
#page-habits .habit-card > .hb-fell{ width:auto; min-width:88px; height:44px; border-radius:var(--disc-r-field); padding:0 14px; }
#page-habits .habit-card > .hb-acts{ grid-column:1 / -1; grid-row:2; margin:0; }
#page-habits .hb-acts .hb-act{ flex:1; min-height:46px; }
#page-habits .hb-more-toggle{ grid-column:1 / -1; justify-self:center; display:inline-flex; align-items:center; gap:6px; min-height:36px; padding:0 14px; border:0; background:none; color:var(--text-3); font:inherit; font-size:12.5px; cursor:pointer; border-radius:var(--disc-r-ctl); }
#page-habits .hb-more-toggle .hb-chev{ display:inline-flex; width:14px; height:14px; transform:rotate(-90deg); transition:transform .24s var(--ease); }
#page-habits .habit-card.is-open .hb-more-toggle .hb-chev{ transform:rotate(90deg); }
#page-habits .hb-more-toggle:focus-visible{ outline:2px solid var(--disc-accent); outline-offset:2px; }
#page-habits .hb-more{ grid-column:1 / -1; display:grid; grid-template-rows:0fr; transition:grid-template-rows .26s var(--ease); margin-top:-12px; }
#page-habits .habit-card.is-open .hb-more{ grid-template-rows:1fr; margin-top:0; }
#page-habits .hb-more-clip{ overflow:hidden; min-height:0; display:flex; flex-direction:column; gap:12px; }
#page-habits .habit-card.is-open .hb-more-clip{ padding-top:4px; }
#page-habits .hb-more .habit-meta{ grid-column:auto; }
#page-habits .habit-card > .task-del{ grid-column:auto; }
#page-habits .hb-archive{ position:static; align-self:flex-start; display:inline-flex; align-items:center; gap:8px; width:auto; height:auto; min-height:40px; padding:0 12px; border-radius:var(--disc-r-ctl); font-size:12.5px; opacity:.85; }
@media (prefers-reduced-motion:reduce){ #page-habits .hb-more, #page-habits .hb-more-toggle .hb-chev{ transition:none; } }
@media (max-width:420px){
  #page-habits .habit-card{ padding:16px 12px 10px; column-gap:10px; }
  #page-habits .habit-card .habit-name{ font-size:16px; }
  #page-habits .habit-card > .stat-btn{ width:48px; height:48px; min-width:48px; }
}
"""
rep("</style>", css + "</style>", 'css')
rep('<!-- CODIS-V2 -->', '<!-- CODIS-V2 -->\n<!-- CODIS-V3-ROOM -->', 'marker')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v3 OK')
