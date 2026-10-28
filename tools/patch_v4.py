#!/usr/bin/env python3
"""CODIS-V4 (يعمل بعد patch_v3.py): مسار المهام الجديد في غرفتي العمليات والأستاذ
  • «نصها» تفتح لوحة نسبة: لا تغيّر حالة ولا تكشف نتيجة قبل اختيار نسبة صالحة (1–99) + تأكيد صريح
  • حركات قلم: علامة ✓ (خلصتها) · ✕ (ما سويتها) · تظليل نسبي (نصها) ثم تشطيب وخروج من القائمة النشطة
  • المهام المحسومة تختفي من القائمة النشطة وتبقى بنافذة «المنجزة» (زر صغير تحت القائمة) مع استرجاع آمن
  الحالة تُحفظ فوراً قبل الحركة (الحركة عرض فقط ولا تتحكم بأي معاملة). الاستخدام: python tools/patch_v4.py <in> <out>"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-V4-TASKFLOW' in s: sys.exit('already patched (CODIS-V4-TASKFLOW)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

# ---- 1) وقت الحسم يُسجَّل مع الحالة (للسجل) ----
rep("""  if(opts && typeof opts.progress === 'number' && isFinite(opts.progress)){ t.status = 'half'; t.progress = Math.max(0, Math.min(100, Math.round(opts.progress))); delete t.doneOn; return t.status; }
  const prev = t.status;
  t.status = (t.status === status) ? null : status;""",
"""  if(opts && typeof opts.progress === 'number' && isFinite(opts.progress)){ t.status = 'half'; t.progress = Math.max(0, Math.min(100, Math.round(opts.progress))); delete t.doneOn; t.answeredAt = new Date().toISOString(); return t.status; }
  const prev = t.status;
  t.status = (t.status === status) ? null : status;
  if(t.status) t.answeredAt = new Date().toISOString(); else delete t.answeredAt;   /* CODIS-V4: وقت الحسم يظهر في سجل «المنجزة» */""", 'applyTaskStatus answeredAt')

# ---- 2) الوحدة: CodisPen + CodisTaskFlow ----
js = r"""/* ================= CODIS-V4-TASKFLOW — مسار حسم المهام =================
   • answer(): الحالة تُطبَّق وتُحفظ فوراً عبر setTaskStatus/setLearnTaskStatus (نفس المنطق والمعاملات)، ثم تُعرَض الحركة. الحركة لا تستدعي أي معاملة.
   • busy: يمنع النقر المتكرر على نفس المهمة؛ anim: مهام تحت الحركة تبقى ظاهرة حتى تنتهي ثم تخرج من القائمة النشطة.
   • restore(): يعيد المهمة غير محسومة. نتيجة اليوم المعلّقة (لم تُحسم) تُلغى بآلية void الموجودة؛ المحسومة تبقى كما سُجّلت (لا انعكاس مالي ولا تكرار). */
const CodisPen = (function(){
  const NS = 'http://www.w3.org/2000/svg';
  const reduced = ()=>{ try{ return window.matchMedia('(prefers-reduced-motion: reduce)').matches; }catch(e){ return false; } };
  const TOTAL = { done:1700, none:1600, half:1700 };
  function rng(seed){ let x = 2166136261; String(seed).split('').forEach(c=>{ x ^= c.charCodeAt(0); x = Math.imul(x, 16777619) >>> 0; }); return ()=>{ x = (Math.imul(x, 1664525) + 1013904223) >>> 0; return x / 4294967296; }; }
  function el(name, attrs){ const n = document.createElementNS(NS, name); Object.keys(attrs || {}).forEach(k=>n.setAttribute(k, attrs[k])); return n; }
  /* مسار كتابة: pathLength=1 + stroke-dashoffset (يتحكّم به CSS؛ التأخير السالب يستأنف الحركة لو أُعيد بناء العنصر) */
  function stroke(svg, d, cls, delay, dur, elapsed){
    const p = el('path', { d:d, class:'pen-p ' + cls, pathLength:'1' });
    p.style.animationDuration = dur + 'ms'; p.style.animationDelay = (delay - elapsed) + 'ms'; svg.appendChild(p); return p;
  }
  function scribble(w, h, x0, x1, y0, y1, passes, r){
    let d = 'M' + x0 + ',' + y0, dir = 1;
    for(let i=0;i<passes;i++){ const y = y0 + (y1 - y0) * (i / Math.max(1, passes - 1)), xa = dir > 0 ? x1 : x0, jy = (r() - .5) * 5; d += ' L' + (xa + (r() - .5) * 8).toFixed(1) + ',' + (y + jy).toFixed(1) + ' L' + (dir > 0 ? x1 : x0) + ',' + (y + 7 + jy).toFixed(1); dir = -dir; }
    return d;
  }
  function hatch(x0, x1, y0, y1, n, r){
    let d = ''; const step = (x1 - x0) / n;
    for(let i=0;i<n;i++){ const x = x0 + i * step + (r() - .5) * 4; d += ' M' + x.toFixed(1) + ',' + y1.toFixed(1) + ' L' + (x + (y1 - y0) * .55).toFixed(1) + ',' + y0.toFixed(1); }
    return d.trim();
  }
  function build(item, spec, elapsed){
    const w = Math.max(160, item.clientWidth || 320), h = Math.max(70, item.clientHeight || 120), r = rng(spec.id + spec.status), red = reduced();
    const svg = el('svg', { class:'pen-ov pen-' + spec.status, viewBox:'0 0 ' + w + ' ' + h, 'aria-hidden':'true', focusable:'false' });
    const k = red ? .35 : 1, cx = w / 2, cy = h * .46, sz = Math.min(h * .62, 86, w * .3);
    const tx0 = w * .07, tx1 = w * .93, ty0 = h * .16, ty1 = h * .42;
    if(spec.status === 'done'){
      stroke(svg, 'M' + (cx - .50 * sz) + ',' + (cy + .02 * sz) + ' C' + (cx - .38 * sz) + ',' + (cy + .14 * sz) + ' ' + (cx - .26 * sz) + ',' + (cy + .30 * sz) + ' ' + (cx - .16 * sz) + ',' + (cy + .42 * sz) + ' C' + (cx + .06 * sz) + ',' + (cy + .05 * sz) + ' ' + (cx + .30 * sz) + ',' + (cy - .26 * sz) + ' ' + (cx + .56 * sz) + ',' + (cy - .50 * sz), 'pen-check', 80 * k, 540 * k, elapsed);
      stroke(svg, scribble(w, h, tx0, tx1, ty0, ty1, 8, r), 'pen-scr', 560 * k, 640 * k, elapsed);
      stroke(svg, hatch(tx0, tx1, ty0, ty1 + 10, 14, r), 'pen-hat', 760 * k, 460 * k, elapsed);
    } else if(spec.status === 'none'){
      stroke(svg, 'M' + (cx - .48 * sz) + ',' + (cy - .46 * sz) + ' C' + (cx - .2 * sz) + ',' + (cy - .16 * sz) + ' ' + (cx + .2 * sz) + ',' + (cy + .18 * sz) + ' ' + (cx + .50 * sz) + ',' + (cy + .50 * sz), 'pen-x', 80 * k, 320 * k, elapsed);
      stroke(svg, 'M' + (cx + .50 * sz) + ',' + (cy - .48 * sz) + ' C' + (cx + .2 * sz) + ',' + (cy - .18 * sz) + ' ' + (cx - .2 * sz) + ',' + (cy + .16 * sz) + ' ' + (cx - .48 * sz) + ',' + (cy + .48 * sz), 'pen-x', 360 * k, 300 * k, elapsed);
      stroke(svg, scribble(w, h, tx0, tx1, ty0, ty1, 5, r), 'pen-scr pen-soft', 700 * k, 520 * k, elapsed);
    } else {
      const pct = Math.max(1, Math.min(99, spec.pct || 50)), bx1 = w - 14, bw = (w - 28) * pct / 100, bx0 = bx1 - bw, by0 = h * .14, by1 = h * .46;
      const rc = el('rect', { x:bx0, y:by0, width:bw, height:by1 - by0, rx:6, class:'pen-fill' }); rc.style.animationDelay = (80 * k - elapsed) + 'ms'; rc.style.animationDuration = 680 * k + 'ms'; svg.appendChild(rc);
      stroke(svg, 'M' + bx1 + ',' + (by1 + 9) + ' C' + (bx1 - bw * .3) + ',' + (by1 + 4) + ' ' + (bx1 - bw * .6) + ',' + (by1 + 14) + ' ' + bx0 + ',' + (by1 + 9), 'pen-half', 140 * k, 620 * k, elapsed);
      if(pct < 99) stroke(svg, 'M' + bx0 + ',' + (by1 + 9) + ' L' + (14) + ',' + (by1 + 9), 'pen-rest', 700 * k, 360 * k, elapsed);
      stroke(svg, hatch(bx0 + 4, bx1 - 4, by0 + 3, by1 - 3, Math.max(3, Math.round(bw / 16)), r), 'pen-hat pen-warm', 700 * k, 460 * k, elapsed);
      const tx = el('text', { x:bx0 + bw / 2, y:(by0 + by1) / 2 + 5, class:'pen-lab', 'text-anchor':'middle' }); tx.textContent = pct + '%'; tx.style.animationDelay = (520 * k - elapsed) + 'ms'; svg.appendChild(tx);
    }
    item.appendChild(svg);
    return svg;
  }
  /* خروج المهمة: يبدأ بعد انتهاء الخطوط (تلاشٍ + انزلاق + طيّ الارتفاع) */
  function leave(item, status, elapsed){
    const at = (reduced() ? 600 : (status === 'none' ? 1200 : 1250)) - elapsed;
    item.style.setProperty('--pen-h', item.offsetHeight + 'px');
    item.classList.add('pen-leaving'); item.style.animationDelay = at + 'ms';
  }
  function mount(item, spec, elapsed){ item.classList.add('is-answering'); build(item, spec, elapsed || 0); leave(item, spec.status, elapsed || 0); }
  function total(status){ return reduced() ? 1000 : TOTAL[status] || 1600; }
  return { mount, total };
})();

const CodisTaskFlow = (function(){
  const busy = new Set(), anim = new Map();
  const key = (k, id)=>k + ':' + id;
  const roomOf = k=>k === 'learn' ? 'learn' : 'tasks';
  const weekOf = k=>k === 'learn' ? learnCurrentWeek() : currentWeek();
  const dayIdx = k=>k === 'learn' ? activeLearnDayIdx : activeDayIdx;
  const render = k=>{ if(k === 'learn') renderLearnPage(); else renderTasksPage(); };
  function find(k, id){
    const w = weekOf(k); if(!w || !w.days) return null;
    for(const d in w.days){ const t = (w.days[d] || []).find(x=>x.id === id); if(t) return { t:t, day:Number(d), week:w }; }
    return null;
  }
  const listEl = k=>document.getElementById(k === 'learn' ? 'learn-day-task-list' : 'day-task-list');
  const itemEl = (k, id)=>{ const l = listEl(k); return l ? l.querySelector('.task-item[data-tid="' + String(id).replace(/"/g, '') + '"]') : null; };
  /* هل تظهر المهمة بالقائمة النشطة؟ غير المحسومة، أو التي تجري حركتها الآن */
  function visible(k, t){ return !t.status || anim.has(key(k, t.id)); }
  function finalize(kk){
    const a = anim.get(kk); if(!a || a.done) return;
    a.done = true; clearTimeout(a.timer); anim.delete(kk); busy.delete(kk);
    try{ render(a.kind); }catch(e){ console.error('task flow render failed:', e); }
  }
  function play(k, id, status, pct){
    const kk = key(k, id), a = anim.get(kk); if(!a) return;
    const item = itemEl(k, id);
    a.timer = setTimeout(()=>finalize(kk), CodisPen.total(status) + 700);   /* مهلة أمان: لو فشل رسم الحركة تُحسم القائمة على أي حال */
    if(!item){ finalize(kk); return; }
    try{ if(!item.querySelector('.pen-ov')) CodisPen.mount(item, { id:id, status:status, pct:pct }, performance.now() - a.t0); item.addEventListener('animationend', function onEnd(ev){ if(ev.target === item && ev.animationName === 'penLeave'){ item.removeEventListener('animationend', onEnd); finalize(kk); } }); }
    catch(e){ console.error('pen animation failed:', e); finalize(kk); }
  }
  /* إعادة بناء القائمة أثناء الحركة (مثلاً تحديث شريط الإنجاز): نستأنف الحركة من الزمن المنقضي بدل أن تُقطع */
  function reattach(k, t, item){
    const a = anim.get(key(k, t.id)); if(!a || a.done) return;
    item.dataset.tid = t.id;
    try{ CodisPen.mount(item, { id:t.id, status:a.status, pct:a.pct }, performance.now() - a.t0); }catch(e){}
  }
  function apply(k, id, status, pct){
    const kk = key(k, id); if(busy.has(kk)) return;
    const f = find(k, id); if(!f || f.t.status) return;
    busy.add(kk); anim.set(kk, { kind:k, status:status, pct:pct, t0:performance.now(), done:false, timer:0 });
    const want = status;
    try{ (k === 'learn' ? setLearnTaskStatus : setTaskStatus)(id, status, pct === null ? undefined : { progress:pct }); }
    catch(e){ console.error('task status failed:', e); }
    const f2 = find(k, id);
    if(!f2 || f2.t.status !== want){ anim.delete(kk); busy.delete(kk); return; }   /* رُفض الحسم (مثل يوم لم يأتِ بعد): لا حركة ولا أثر */
    play(k, id, status, pct);
  }
  function previewPct(f, p){
    const list = (f.week.days[f.day] || []).map(x=>x === f.t ? Object.assign({}, x, { status:'half', progress:p }) : x);
    return codisWeightedProgress(list);
  }
  function previewText(f, p){
    const st = previewPct(f, p), pct = st.pct === null ? 0 : st.pct, th = { r:data.settings.rewardThreshold, p:data.settings.punishThreshold };
    let line = (st.unanswered > 0 ? 'إنجاز يومك حتى الآن سيصير <b>' : 'إنجاز يومك سيصير <b>') + pct + '%</b>.';
    if(st.unanswered > 0) line += ' باقي ' + st.unanswered + ' مهام تنحسم قبل ما تتحدد نتيجة اليوم.';
    else if(pct >= th.r) line += ' يتجاوز حدّ المكافأة (' + th.r + '%) ← تُسجَّل مكافأة اليوم.';
    else if(pct < th.p) line += ' تحت حدّ العقوبة (' + th.p + '%) ← تُسجَّل عقوبة اليوم.';
    else line += ' بين الحدّين: لا مكافأة ولا عقوبة.';
    return line;
  }
  function openPartial(k, id, item){
    const f = find(k, id); if(!f || f.t.status || !item) return;
    const l = listEl(k); if(l) l.querySelectorAll('.pp-panel').forEach(p=>p.remove());
    const panel = document.createElement('div'); panel.className = 'pp-panel'; panel.setAttribute('role', 'group'); panel.setAttribute('aria-label', 'نسبة الإنجاز');
    panel.innerHTML = '<div class="pp-head"><span class="pp-q">كم أنجزت منها؟</span><output class="pp-val" aria-live="polite">اختر النسبة</output></div>' +
      '<div class="pp-chips">' + [25, 50, 75].map(v=>'<button type="button" class="pp-chip" data-v="' + v + '">' + v + '%</button>').join('') + '</div>' +
      '<input type="range" class="tp-range pp-range is-unset" min="1" max="99" step="1" value="50" aria-label="نسبة الإنجاز" aria-valuetext="لم تُختر بعد">' +
      '<div class="pp-preview" aria-live="polite" hidden></div>' +
      '<div class="pp-actions"><button type="button" class="btn btn-primary pp-ok" disabled>تأكيد</button><button type="button" class="btn btn-quiet pp-cancel">إلغاء</button></div>';
    item.appendChild(panel);
    const range = panel.querySelector('.pp-range'), val = panel.querySelector('.pp-val'), pv = panel.querySelector('.pp-preview'), ok = panel.querySelector('.pp-ok');
    let chosen = null;
    const set = v=>{
      v = Math.round(Number(v)); if(!(v >= 1 && v <= 99)) return;
      chosen = v; range.value = v; range.classList.remove('is-unset'); range.style.setProperty('--tp', v + '%'); range.setAttribute('aria-valuetext', v + '%');
      val.textContent = v + '%'; pv.hidden = false; pv.innerHTML = previewText(f, v); ok.disabled = false;
      panel.querySelectorAll('.pp-chip').forEach(c=>c.classList.toggle('is-on', Number(c.dataset.v) === v));
    };
    range.addEventListener('input', ()=>set(range.value));
    range.addEventListener('change', ()=>set(range.value));
    panel.querySelectorAll('.pp-chip').forEach(c=>{ c.onclick = ()=>set(c.dataset.v); });
    panel.querySelector('.pp-cancel').onclick = ()=>{ panel.remove(); };
    ok.onclick = ()=>{ if(chosen === null || ok.disabled) return; ok.disabled = true; panel.querySelectorAll('button,input').forEach(x=>{ x.disabled = true; }); apply(k, id, 'half', chosen); };
    try{ panel.scrollIntoView({ block:'nearest', behavior:'smooth' }); }catch(e){}
  }
  function answer(k, id, status, item){
    if(busy.has(key(k, id))) return;
    if(status === 'half'){
      const f = find(k, id); if(!f || f.t.status) return;
      if(codisTaskDayLocked(currentWeekId(), f.day, f.t, 'half')) return;   /* يوم لم يأتِ: نفس القاعدة القديمة (المطوّر معفى) */
      openPartial(k, id, item); return;
    }
    apply(k, id, status, null);
  }

  /* ---- نافذة المنجزة + الاسترجاع ---- */
  const OUT = { done:'خلصتها', half:'نصها', none:'ما سويتها' };
  const answered = (k, day)=>{ const w = weekOf(k); return ((w && w.days && w.days[day]) || []).filter(t=>t.status && !anim.has(key(k, t.id))); };
  function dayEntries(k, weekId, day){
    const L = data.outcomeLedger || {};
    return Object.keys(L).map(x=>L[x]).filter(e=>e && e.scope === 'daily' && e.room === roomOf(k) && e.weekId === weekId && e.day === day && e.status !== 'void');
  }
  function outcomeLine(e){
    const st = e.status === 'pending' ? ' — بانتظار قرارك' : '', coins = Number(e.coinsAwarded) > 0 ? ' · +' + econFmt(e.coinsAwarded) + ' كوين' : (Number(e.coinsSpent) > 0 ? ' · −' + econFmt(e.coinsSpent) + ' كوين' : '');
    return (e.kind === 'reward' ? 'مكافأة اليوم: ' : 'عقوبة اليوم: ') + (e.item || '—') + coins + st;
  }
  function doneBar(k, day){
    const n = answered(k, day).length; if(!n) return null;
    const b = document.createElement('button'); b.type = 'button'; b.className = 'cd-trigger'; b.setAttribute('aria-haspopup', 'dialog');
    b.innerHTML = '<span class="cd-ico" aria-hidden="true">' + codisIcon('archive', { size:'sm' }) + '</span><span class="cd-lab">المنجزة</span><span class="cd-n">' + n + '</span>';
    b.setAttribute('aria-label', 'المهام المحسومة: ' + n);
    b.onclick = ()=>openDone(k, day, b);
    return b;
  }
  let sheet = null;
  function closeDone(){ if(!sheet) return; const s0 = sheet; sheet = null; document.removeEventListener('keydown', s0.onKey, true); s0.root.classList.remove('is-open'); setTimeout(()=>s0.root.remove(), 220); try{ s0.opener && s0.opener.isConnected && s0.opener.focus({ preventScroll:true }); }catch(e){} }
  function sheetBody(k, day){
    const w = weekOf(k), weekId = currentWeekId(), list = answered(k, day);
    if(!list.length) return '<div class="cd-empty">ماكو مهام محسومة هنا</div>';
    const ents = dayEntries(k, weekId, day), out = ents.map(e=>'<div class="cd-day-out ' + (e.kind === 'reward' ? 'is-reward' : 'is-punish') + '">' + escapeHtml(outcomeLine(e)) + '</div>').join('');
    const groups = ['done', 'half', 'none'].map(st=>{
      const g = list.filter(t=>t.status === st); if(!g.length) return '';
      return '<section class="cd-group"><h3 class="cd-gh"><span>' + OUT[st] + '</span><span class="cd-gn">' + g.length + '</span></h3>' + g.map(t=>{
        const when = t.answeredAt ? (formatArDate(t.answeredAt) + ' · ' + new Date(t.answeredAt).toLocaleTimeString('ar', { hour:'2-digit', minute:'2-digit' })) : 'وقت الحسم غير مسجّل';
        const pct = st === 'half' ? '<span class="cd-pct">' + Math.round(Number(t.progress) || 0) + '%</span>' : '';
        return '<div class="cd-row is-' + st + '"><div class="cd-main"><div class="cd-t">' + escapeHtml(t.text) + '</div><div class="cd-meta">' + pct + '<span>' + escapeHtml(when) + '</span></div></div>' +
          '<button type="button" class="cd-restore" data-id="' + escapeHtml(String(t.id)) + '">استرجاع</button></div>';
      }).join('') + '</section>';
    }).join('');
    return (out ? '<div class="cd-outs">' + out + '<div class="cd-note">النتيجة المسجّلة لا تتغيّر باسترجاع مهمة.</div></div>' : '') + groups;
  }
  function openDone(k, day, opener){
    closeDone();
    const root = document.createElement('div'); root.className = 'cd-ov';
    root.innerHTML = '<div class="cd-back"></div><div class="cd-sheet" role="dialog" aria-modal="true" aria-label="المهام المحسومة"><div class="cd-grab" aria-hidden="true"></div><div class="cd-head"><h2 class="cd-title">المنجزة · ' + DAYS_AR[day] + '</h2><button type="button" class="cd-close" aria-label="إغلاق">' + ICONS.close + '</button></div><div class="cd-body"></div></div>';
    document.body.appendChild(root);
    const body = root.querySelector('.cd-body'), s0 = { root:root, opener:opener, onKey:ev=>{ if(ev.key === 'Escape'){ ev.stopPropagation(); closeDone(); } } };
    sheet = s0; document.addEventListener('keydown', s0.onKey, true);
    const paint = ()=>{
      body.innerHTML = sheetBody(k, day);
      body.querySelectorAll('.cd-restore').forEach(b=>{ b.onclick = async ()=>{ b.disabled = true; await restore(k, b.dataset.id); if(sheet === s0) paint(); }; });
    };
    paint();
    root.querySelector('.cd-back').onclick = closeDone; root.querySelector('.cd-close').onclick = closeDone;
    requestAnimationFrame(()=>{ root.classList.add('is-open'); try{ root.querySelector('.cd-close').focus({ preventScroll:true }); }catch(e){} });
  }
  async function restore(k, id){
    const kk = key(k, id); if(busy.has(kk)) return false;
    const f = find(k, id); if(!f || !f.t.status) return false;   /* غير محسومة أصلاً ← لا شيء (يمنع تكرار الاسترجاع) */
    busy.add(kk);
    try{
      const weekId = currentWeekId(), ents = dayEntries(k, weekId, f.day), pend = ents.filter(e=>e.status === 'pending'), done = ents.filter(e=>e.status !== 'pending');
      let msg = 'ترجع المهمة للقائمة بدون حسم، وتقدر تحسمها من جديد.';
      if(pend.length) msg += ' نتيجة اليوم اللي كانت بانتظار قرارك تُلغى لأن اليوم صار غير مكتمل، وتُسجَّل من جديد إذا حسمت كل المهام.';
      if(done.length) msg += ' نتيجة اليوم اللي انحسمت سابقاً تبقى كما سُجّلت (ما تنسحب ولا تنكرر).';
      const ok = await codisConfirm({ title:'استرجاع مهمة', icon:'archive', message:msg, confirmText:'استرجاع' });
      if(!ok) return false;
      const f2 = find(k, id); if(!f2 || !f2.t.status) return false;   /* تغيّرت الحالة أثناء نافذة التأكيد */
      const t = f2.t, from = t.status;
      t.status = null; t.progress = 0; delete t.doneOn; delete t.answeredAt;
      t.restoredAt = new Date().toISOString(); t.restores = (Number(t.restores) || 0) + 1; t.restoredFrom = from;
      pend.forEach(e=>{ try{ CodisEconomy.voidIfPending(e.id); }catch(x){ console.error(x); } });
      saveData();
      try{ render(k); }catch(e){ console.error(e); }
      codisSfx('confirm'); showToast('رجعت المهمة للقائمة', 'var(--success)', 'check');
      return true;
    }finally{ busy.delete(kk); }
  }
  return { visible, answer, reattach, doneBar, restore, openDone, closeDone, _anim:anim, _busy:busy };
})();

"""
rep("function codisTaskItemHtml(task, withHint){", js + "function codisTaskItemHtml(task, withHint){", 'module insert')

# ---- 3) الرسم: العمليات ----
rep("""  } else {
    dayTasks.forEach(task=>{
      const item = document.createElement('div');
      item.className = 'task-item' + (task.status ? ' is-' + task.status : '') + (task.id === codisJustChangedId ? ' just-changed' : '');
      item.innerHTML = codisTaskItemHtml(task, true);
      item.querySelectorAll('.stat-btn').forEach(b=>{
        b.onclick = ()=>setTaskStatus(task.id, b.dataset.status);
      });
      codisBindTaskExtras(item, task, 'tasks');
      item.querySelector('.task-del').onclick = ()=>deleteTask(task.id);
      listWrap.appendChild(item);
      CodisMotion.taskSettle(item, task);
    });
  }""",
"""  } else {
    let shown = 0;
    dayTasks.forEach(task=>{
      if(!CodisTaskFlow.visible('tasks', task)) return;   /* المحسومة تنتقل إلى «المنجزة» */
      shown++;
      const item = document.createElement('div');
      item.className = 'task-item' + (task.status ? ' is-' + task.status : '') + (task.id === codisJustChangedId ? ' just-changed' : '');
      item.dataset.tid = task.id;
      item.innerHTML = codisTaskItemHtml(task, true);
      item.querySelectorAll('.stat-btn').forEach(b=>{
        b.onclick = ()=>CodisTaskFlow.answer('tasks', task.id, b.dataset.status, item);
      });
      codisBindTaskExtras(item, task, 'tasks');
      item.querySelector('.task-del').onclick = ()=>deleteTask(task.id);
      listWrap.appendChild(item);
      CodisMotion.taskSettle(item, task);
      CodisTaskFlow.reattach('tasks', task, item);
    });
    if(!shown) listWrap.insertAdjacentHTML('beforeend', `<div class="empty-state is-clear"><div class="es-mark">${ICONS.celebrate}</div><div class="es-copy">كل مهام اليوم محسومة</div></div>`);
    { const bar = CodisTaskFlow.doneBar('tasks', activeDayIdx); if(bar) listWrap.appendChild(bar); }
  }""", 'tasks render')

# ---- 4) الرسم: الأستاذ ----
rep("""  } else {
    dayTasks.forEach(task=>{
      const item = document.createElement('div');
      item.className = 'task-item' + (task.status ? ' is-' + task.status : '') + (task.id === codisJustChangedId ? ' just-changed' : '');
      item.innerHTML = codisTaskItemHtml(task, false);
      item.querySelectorAll('.stat-btn').forEach(b=>{ b.onclick = ()=>setLearnTaskStatus(task.id, b.dataset.status); });
      codisBindTaskExtras(item, task, 'learn');
      item.querySelector('.task-del').onclick = ()=>deleteLearnTask(task.id);
      listWrap.appendChild(item);
      CodisMotion.taskSettle(item, task);
    });
  }""",
"""  } else {
    let shown = 0;
    dayTasks.forEach(task=>{
      if(!CodisTaskFlow.visible('learn', task)) return;
      shown++;
      const item = document.createElement('div');
      item.className = 'task-item' + (task.status ? ' is-' + task.status : '') + (task.id === codisJustChangedId ? ' just-changed' : '');
      item.dataset.tid = task.id;
      item.innerHTML = codisTaskItemHtml(task, false);
      item.querySelectorAll('.stat-btn').forEach(b=>{ b.onclick = ()=>CodisTaskFlow.answer('learn', task.id, b.dataset.status, item); });
      codisBindTaskExtras(item, task, 'learn');
      item.querySelector('.task-del').onclick = ()=>deleteLearnTask(task.id);
      listWrap.appendChild(item);
      CodisMotion.taskSettle(item, task);
      CodisTaskFlow.reattach('learn', task, item);
    });
    if(!shown) listWrap.insertAdjacentHTML('beforeend', `<div class="empty-state is-clear"><div class="es-mark">${ICONS.celebrate}</div><div class="es-copy">كل عناصر اليوم محسومة</div></div>`);
    { const bar = CodisTaskFlow.doneBar('learn', activeLearnDayIdx); if(bar) listWrap.appendChild(bar); }
  }""", 'learn render')


# الشريط القديم داخل البطاقة لم يعد يُعرض: المهام الجزئية تخرج من القائمة النشطة والنسبة تُختار قبل الحسم (لوحة pp-panel)
rep("const partial = st==='half' ? `<div class=\"task-partial\"", "const partial = (false && st==='half') ? `<div class=\"task-partial\"", 'old partial slider off')

# ---- 5) CSS ----
css = r"""
/* CODIS-V4-TASKFLOW — حركات القلم + لوحة النسبة + نافذة المنجزة */
.task-item{ position:relative; }
.task-item.is-answering{ pointer-events:none; }
.pen-ov{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible; z-index:4; }
.pen-p{ fill:none; stroke-linecap:round; stroke-linejoin:round; stroke-dasharray:1 1; stroke-dashoffset:1.01; animation:penDraw 600ms cubic-bezier(.45,.05,.25,1) both; will-change:stroke-dashoffset; }
.pen-check{ stroke:var(--success); stroke-width:6; filter:none; }
.pen-x{ stroke:var(--danger); stroke-width:6; }
.pen-scr, .pen-hat{ stroke:var(--text-2); stroke-width:2.2; opacity:.55; }
.pen-soft{ stroke:var(--danger-ink, var(--danger)); opacity:.4; stroke-width:2; }
.pen-half{ stroke:var(--warning); stroke-width:4; }
.pen-rest{ stroke:var(--warning); stroke-width:2; stroke-dasharray:.012 .02; opacity:.5; animation-name:penFade; }
.pen-hat.pen-warm{ stroke:var(--warning-ink, var(--warning)); opacity:.5; }
.pen-fill{ fill:var(--warning); opacity:.22; transform-box:fill-box; transform-origin:100% 50%; animation:penFill 680ms cubic-bezier(.3,.0,.2,1) both; }
.pen-lab{ fill:var(--warning-ink, var(--warning)); font-size:15px; font-weight:700; opacity:0; animation:penFade 300ms ease-out both; }
@keyframes penDraw{ from{ stroke-dashoffset:1.01; } to{ stroke-dashoffset:0; } }
@keyframes penFill{ from{ transform:scaleX(0); } to{ transform:scaleX(1); } }
@keyframes penFade{ from{ opacity:0; } to{ opacity:1; } }
.task-item.pen-leaving{ animation:penLeave 420ms cubic-bezier(.4,0,.6,1) both; overflow:hidden; }
@keyframes penLeave{
  0%{ opacity:1; transform:none; max-height:var(--pen-h, 400px); }
  55%{ opacity:0; transform:translateX(-14px); max-height:var(--pen-h, 400px); }
  100%{ opacity:0; transform:translateX(-14px); max-height:0; margin-block:0; padding-block:0; border-width:0; }
}
@media (prefers-reduced-motion:reduce){
  .pen-p, .pen-fill, .pen-lab{ animation-duration:1ms !important; animation-delay:0ms !important; }
  .task-item.pen-leaving{ animation-duration:260ms; }
  @keyframes penLeave{ 0%{ opacity:1; max-height:var(--pen-h, 400px); } 100%{ opacity:0; max-height:0; margin-block:0; padding-block:0; border-width:0; } }
}
/* لوحة النسبة الجزئية */
.pp-panel{ display:flex; flex-direction:column; gap:12px; margin-top:10px; padding:14px; border-radius:14px; background:var(--warning-a12); border:1px solid rgb(var(--warning-rgb) / .28); }
.pp-head{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; }
.pp-q{ font-size:14px; font-weight:600; color:var(--text); }
.pp-val{ font-size:22px; font-weight:800; color:var(--warning-ink, var(--warning)); font-variant-numeric:tabular-nums; }
.pp-chips{ display:flex; gap:8px; }
.pp-chip{ flex:1; min-height:40px; border-radius:10px; border:1px solid rgb(var(--hi-rgb) / .16); background:rgb(var(--hi-rgb) / .05); color:var(--text-2); font:inherit; font-weight:600; cursor:pointer; }
.pp-chip.is-on{ background:var(--warning); color:#1a1405; border-color:var(--warning); }
.pp-range.is-unset::-webkit-slider-thumb{ background:rgb(var(--hi-rgb) / .4); }
.pp-range.is-unset::-moz-range-thumb{ background:rgb(var(--hi-rgb) / .4); }
.pp-preview{ font-size:13px; line-height:1.7; color:var(--text-2); }
.pp-preview b{ color:var(--text); font-size:15px; }
.pp-actions{ display:flex; gap:8px; }
.pp-actions .btn{ flex:1; min-height:44px; }
.pp-actions .pp-ok:disabled{ opacity:.45; }
/* زر المنجزة */
.cd-trigger{ display:flex; align-items:center; gap:8px; margin:14px auto 0; min-height:40px; padding:0 14px; border-radius:999px; border:1px solid rgb(var(--hi-rgb) / .14); background:rgb(var(--hi-rgb) / .04); color:var(--text-2); font:inherit; font-size:13px; font-weight:600; cursor:pointer; }
.cd-trigger:focus-visible{ outline:2px solid var(--aqua); outline-offset:2px; }
.cd-n{ min-width:22px; padding:1px 7px; border-radius:999px; background:var(--aqua-a14, rgb(var(--hi-rgb) / .1)); color:var(--text); font-size:12px; font-weight:700; text-align:center; font-variant-numeric:tabular-nums; }
.cd-ico svg{ width:16px; height:16px; }
/* نافذة المنجزة */
.cd-ov{ position:fixed; inset:0; z-index:9000; display:flex; align-items:flex-end; justify-content:center; pointer-events:none; }
.cd-back{ position:absolute; inset:0; background:rgb(var(--lo-rgb) / .55); opacity:0; transition:opacity .2s ease; pointer-events:auto; }
.cd-sheet{ position:relative; width:min(560px, 100%); max-height:82vh; display:flex; flex-direction:column; border-radius:22px 22px 0 0; background:var(--surface, #0d1117); border:1px solid rgb(var(--hi-rgb) / .1); border-bottom:0; transform:translateY(100%); transition:transform .24s cubic-bezier(.2,.8,.2,1); pointer-events:auto; padding-bottom:env(safe-area-inset-bottom); }
.cd-ov.is-open .cd-back{ opacity:1; } .cd-ov.is-open .cd-sheet{ transform:none; }
.cd-grab{ width:38px; height:4px; border-radius:4px; background:rgb(var(--hi-rgb) / .18); margin:8px auto 0; }
.cd-head{ display:flex; align-items:center; justify-content:space-between; padding:10px 16px 8px; }
.cd-title{ margin:0; font-size:17px; font-weight:700; }
.cd-close{ width:40px; height:40px; border-radius:50%; border:0; background:rgb(var(--hi-rgb) / .06); color:var(--text-2); cursor:pointer; }
.cd-body{ overflow:auto; padding:4px 16px 18px; display:flex; flex-direction:column; gap:14px; overscroll-behavior:contain; }
.cd-group{ display:flex; flex-direction:column; gap:8px; }
.cd-gh{ display:flex; align-items:center; gap:8px; margin:0; font-size:13px; color:var(--text-3); font-weight:600; }
.cd-gn{ font-variant-numeric:tabular-nums; }
.cd-row{ display:flex; align-items:center; gap:12px; padding:12px; border-radius:14px; background:rgb(var(--hi-rgb) / .04); border:1px solid rgb(var(--hi-rgb) / .07); }
.cd-row.is-done{ border-inline-start:3px solid var(--success); } .cd-row.is-half{ border-inline-start:3px solid var(--warning); } .cd-row.is-none{ border-inline-start:3px solid var(--danger); }
.cd-main{ flex:1; min-width:0; } .cd-t{ font-size:15px; line-height:1.5; overflow-wrap:anywhere; }
.cd-meta{ display:flex; flex-wrap:wrap; gap:4px 10px; margin-top:2px; font-size:12px; color:var(--text-3); }
.cd-pct{ color:var(--warning-ink, var(--warning)); font-weight:700; }
.cd-restore{ flex:none; min-height:40px; padding:0 14px; border-radius:10px; border:1px solid rgb(var(--hi-rgb) / .16); background:none; color:var(--text); font:inherit; font-size:13px; font-weight:600; cursor:pointer; }
.cd-restore:disabled{ opacity:.45; }
.cd-outs{ display:flex; flex-direction:column; gap:6px; padding:12px; border-radius:14px; background:rgb(var(--hi-rgb) / .04); }
.cd-day-out{ font-size:13px; line-height:1.6; } .cd-day-out.is-reward{ color:var(--gold, var(--warning-ink)); } .cd-day-out.is-punish{ color:var(--danger-ink, var(--danger)); }
.cd-note{ font-size:12px; color:var(--text-3); }
.cd-empty{ padding:30px 0; text-align:center; color:var(--text-3); }
@media (prefers-reduced-motion:reduce){ .cd-sheet, .cd-back{ transition:none; } }
"""
rep("</style>", css + "</style>", 'css')
rep('<!-- CODIS-V3-ROOM -->', '<!-- CODIS-V3-ROOM -->\n<!-- CODIS-V4-TASKFLOW -->', 'marker')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v4 OK')
