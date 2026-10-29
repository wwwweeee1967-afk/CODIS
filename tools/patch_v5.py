#!/usr/bin/env python3
"""CODIS-V5 (بعد patch_v4.py): الرجوع والسحب كنظام واحد.
 الجذر: (1) التطبيق لا يستعمل History API إطلاقاً، فسحب Safari الأصلي/زر الرجوع يعبر سجل المتصفح (Google/Supabase/صفحة ما قبل الدخول) بدل الرجوع داخل التطبيق،
        (2) سحب التطبيق اليدوي يعمل بالتوازي مع الأصلي ⇒ رجوع مزدوج، (3) تسجيل الدخول كان location.href (يترك مدخلاً قديماً ببوابة الدخول) وpageshow المسترجَع لا يخفي البوابة عند وجود جلسة.
 الحل: حارس History (مدخلان: base/top) + popstate يحوّل أي رجوع أصلي إلى رجوع داخلي واحد ويعيد حارس top · CodisNav.back() مالك وحيد مع قفل ضد التكرار ·
       سحب تفاعلي يتبع الإصبع (عند عدم وجود سحب أصلي) · signIn بـlocation.replace · pageshow/visibility يعيدان تقييم البوابة من الجلسة الفعلية."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-V5-NAV' in s: sys.exit('already patched (CODIS-V5-NAV)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

# 1) استبدال كتلة SWIPE BACK كاملة
a = s.index('/* ================= SWIPE BACK (مثل iPhone) =================')
b = s.index('/* ================= iPhone keyboard-safe input scroll')
new_block = r"""/* ================= CODIS-V5-NAV — الرجوع والسحب (مالك واحد) =================
   • codisBackLayer(): أعلى طبقة مفتوحة {act, el} بترتيب ثابت (تأكيد ← نوافذ ← المتجر ← صفحة فرعية بالإعدادات)؛ الغرف الرئيسية ← null (لا رجوع ولا خروج).
   • CodisNav.back(): التنفيذ الوحيد للرجوع (قفل 380ms) — يستعمله السحب وpopstate وزر الرجوع؛ لا يلمس الجلسة ولا البيانات.
   • حارس History: مدخلان {codis:'base'} ثم {codis:'top'}. أي popstate يعني أن المستخدم ضغط رجوع (سحب Safari/زر Android) فننفّذ رجوعاً داخلياً واحداً ثم نعيد حارس top.
     لا مدخلات تُضاف عند التنقل بين الغرف أو فتح النوافذ ⇒ لا مدخلات وهمية.
   • السحب التفاعلي يعمل فقط حيث لا يوجد سحب أصلي (تطبيق مثبَّت/غير iOS Safari)؛ في Safari المتصفح يتولى النظام السحب ويصلنا popstate. */
function codisBackLayer(){
  const open = id=>{ const el = document.getElementById(id); return !!el && el.style.display !== 'none' && el.style.display !== ''; };
  const L = (id, act)=>({ act:act, el:document.getElementById(id) });
  if(open('codis-confirm-modal')) return L('codis-confirm-modal', ()=>resolveCodisConfirm(false));
  if(open('dq-modal')) return L('dq-modal', ()=>dqEsc());
  const rep = document.getElementById('report-overlay'); if(rep && rep.classList.contains('is-open')) return { act:codisCloseReport, el:rep };
  const oc = document.getElementById('outcome-overlay'); if(oc && oc.classList.contains('is-visible')) return { act:closeOutcomeOverlay, el:oc };
  if(open('holiday-pick-modal')) return L('holiday-pick-modal', hcdPickClose);
  if(open('econ-pack-modal')) return L('econ-pack-modal', econPackClose);
  if(open('econ-box-modal')) return L('econ-box-modal', econBoxClose);
  if(open('econ-bulk-modal')) return L('econ-bulk-modal', econBulkClose);
  if(open('econ-detail-modal')) return L('econ-detail-modal', econCloseDetail);
  if(open('archive-detail-modal')) return L('archive-detail-modal', closeArchiveDetail);
  if(open('notif-center-modal')) return L('notif-center-modal', closeNotifCenter);
  const ha = document.getElementById('habit-add'); if(ha && ha.getAttribute('aria-hidden') === 'false') return { act:closeAddHabit, el:null };
  const pg = document.getElementById('page-settings');
  if(pg && getComputedStyle(pg).display !== 'none'){
    const sec = Array.prototype.find.call(pg.children, c=>c.classList.contains('settings-page-section') && getComputedStyle(c).display !== 'none');
    if(econStoreIsOpen()) return { act:econCloseStore, el:sec || null };
    const btn = sec && sec.querySelector('.settings-back-btn'); if(btn) return { act:()=>btn.click(), el:sec };
  } else if(econStoreIsOpen()) return { act:econCloseStore, el:null };
  return null;
}
function codisBackTarget(){ const l = codisBackLayer(); return l ? l.act : null; }
const CodisNav = (function(){
  const standalone = ()=>{ try{ return window.navigator.standalone === true || matchMedia('(display-mode: standalone)').matches; }catch(e){ return false; } };
  const reduced = ()=>{ try{ return matchMedia('(prefers-reduced-motion: reduce)').matches; }catch(e){ return false; } };
  const nativeSwipe = /iP(hone|ad|od)/.test(navigator.userAgent) && !standalone();   /* Safari المتصفح: السحب الأصلي موجود ويصلنا كـpopstate */
  let lastBack = 0, busyDrag = false;
  function back(){
    const now = Date.now(); if(now - lastBack < 380) return false;
    const l = codisBackLayer(); if(!l) return false;
    lastBack = now;
    try{ codisHaptic([8]); }catch(e){}
    try{ l.act(); }catch(e){ console.error('back failed:', e); }
    return true;
  }
  /* ---- حارس History ---- */
  function guard(){
    try{
      const st = history.state;
      if(st && st.codis === 'top') return;                    /* إعادة تحميل: الحارس موجود أصلاً */
      history.replaceState({ codis:'base' }, '', location.href);
      history.pushState({ codis:'top' }, '', location.href);
    }catch(e){}
  }
  window.addEventListener('popstate', e=>{
    const st = e.state || {};
    if(st.codis === 'top') return;                            /* وصلنا لمدخلنا نفسه (أمام): لا شيء */
    back();                                                   /* رجوع داخلي واحد (أو لا شيء في الغرف الرئيسية) */
    try{ history.pushState({ codis:'top' }, '', location.href); }catch(x){}   /* لا نغادر التطبيق ولا نكشف بوابة الدخول */
  });
  /* ---- السحب التفاعلي ---- */
  const EDGE = 28, MIN = 72;
  let g = null;
  const clear = el=>{ if(!el) return; el.style.transition = ''; el.style.transform = ''; el.style.willChange = ''; };
  function settle(done){
    const s0 = g; g = null; if(!s0) return;
    const el = s0.el; busyDrag = false;
    if(!s0.active || !el){ return; }
    const w = el.getBoundingClientRect().width || window.innerWidth, sign = s0.side === 'l' ? 1 : -1;
    const go = done && s0.dx >= Math.max(MIN, w * .3);
    if(reduced()){ clear(el); if(go) back(); return; }
    el.style.transition = 'transform 200ms cubic-bezier(.2,.8,.2,1)';
    el.style.transform = go ? 'translate3d(' + sign * w + 'px,0,0)' : 'translate3d(0,0,0)';
    let fin = false;
    const end = ()=>{ if(fin) return; fin = true; el.removeEventListener('transitionend', end); if(go) back(); setTimeout(()=>clear(el), 0); };
    el.addEventListener('transitionend', end); setTimeout(end, 260);
  }
  if(!nativeSwipe){
    document.addEventListener('touchstart', e=>{
      if(g){ settle(false); return; }
      if(e.touches.length !== 1) return;
      const t = e.touches[0], b = document.body.getBoundingClientRect(), side = t.clientX <= b.left + EDGE ? 'l' : (t.clientX >= b.right - EDGE ? 'r' : '');
      if(!side) return;
      const l = codisBackLayer(); if(!l) return;
      g = { side:side, x:t.clientX, y:t.clientY, dx:0, dy:0, active:false, el:l.el };
    }, { passive:true });
    document.addEventListener('touchmove', e=>{
      if(!g) return;
      if(e.touches.length !== 1){ settle(false); return; }
      const t = e.touches[0]; g.dx = g.side === 'l' ? t.clientX - g.x : g.x - t.clientX; g.dy = Math.abs(t.clientY - g.y);
      if(!g.active){
        if(g.dx < -14 || (g.dy > 12 && g.dy > g.dx)){ g = null; return; }      /* عمودي أو للخارج: ليس رجوعاً */
        if(g.dx > 12 && g.dx > g.dy * 1.2){ g.active = true; busyDrag = true; if(g.el){ g.el.style.transition = 'none'; g.el.style.willChange = 'transform'; } }
      }
      if(g.active){
        if(e.cancelable) e.preventDefault();
        if(g.el && !reduced()){ const sign = g.side === 'l' ? 1 : -1; g.el.style.transform = 'translate3d(' + sign * Math.max(0, g.dx) + 'px,0,0)'; }
      }
    }, { passive:false });
    document.addEventListener('touchend', ()=>{ if(!g) return; if(!g.active){ g = null; return; } const done = true; if(!g.el){ const ok = g.dx >= MIN; g = null; busyDrag = false; if(ok) back(); return; } settle(done); }, { passive:true });
    document.addEventListener('touchcancel', ()=>settle(false), { passive:true });
    document.addEventListener('visibilitychange', ()=>{ if(document.hidden && g) settle(false); });
    window.addEventListener('blur', ()=>{ if(g) settle(false); });
  }
  guard();
  return { back, guard, nativeSwipe, _lock:()=>lastBack };
})();

"""
s = s[:a] + new_block + s[b:]

# 2) تسجيل الدخول: replace (لا مدخل قديم ببوابة الدخول)
rep("      location.href = cfg.url + '/auth/v1/authorize?provider=google&flow_type=pkce&code_challenge='", "      location.replace(cfg.url + '/auth/v1/authorize?provider=google&flow_type=pkce&code_challenge='", 'signIn replace')
rep("+ encodeURIComponent(back);\n    }catch(e){ console.warn('[CODIS auth] signIn failed:'", "+ encodeURIComponent(back));\n    }catch(e){ console.warn('[CODIS auth] signIn failed:'", 'signIn replace close')

# 3) إعادة تقييم البوابة من الجلسة الفعلية عند استرجاع الصفحة (bfcache/رجوع)
rep("window.addEventListener('pageshow', ev => { if(ev.persisted){ signingIn = false; const g = document.getElementById('codis-gate'); if(g && g.classList.contains('is-busy')) gateBusy(false); } });",
    "window.addEventListener('pageshow', ev => { if(ev.persisted){ signingIn = false; const g = document.getElementById('codis-gate'); if(g && g.classList.contains('is-busy')) gateBusy(false);\n        /* CODIS-V5: صفحة مستعادة من الكاش قد تحمل بوابة قديمة — الحقيقة هي الجلسة المخزَّنة لا لقطة الصفحة */\n        try{ loadSession(); if(S.session || rd(K_GUEST) === '1'){ hideGate(); paint(); } }catch(e){} } });", 'pageshow settle')
s = s.replace('<!-- CODIS-V4-TASKFLOW -->', '<!-- CODIS-V4-TASKFLOW -->\n<!-- CODIS-V5-NAV -->', 1)
if 'CODIS-V5-NAV -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v5 OK')
