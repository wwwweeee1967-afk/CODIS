#!/usr/bin/env python3
"""CODIS-RAYS (بعد patch_v26.py) — 3.14.2 — نفس أشعة مشهد الشراء بذاكرة GPU أقل بكثير، بلا تغيير بالشكل أو الحركة.
تشخيص الجهاز (iPhone 12، iOS 18.7، بطاقة CodisCrumb): آخر مرحلة قبل موت الصفحة = cine:buttons — كل مراحل المشهد اكتملت بلا خطأ JS،
والموت لحظة الذروة (الأشعة + الوهج + الجزيئات) ⇒ ذاكرة طبقات الرسم. أكبر طبقة: الأشعة = مربع 140vmax (~1180px ⇒ ~3540px على ×3 ≈ 50MB)
يدور، + طبقة قناع التلاشي بنفس الحجم.
الآن: <canvas> بحجم المشهد نفسه (~1170×2532 ≈ 12MB، بلا طبقة قناع) يرسم كل إطار نفس الشيء حرفياً:
 • نفس التدرّج المخروطي المتكرر (نفس الزوايا/الألوان/الشفافية، x1: 7°/22° · x2: 5°/15°/21°/30°) من الأعلى مع عقارب الساعة،
 • نفس المركز (50%, 46%) ونفس التلاشي الدائري بالمسافات المطلقة (1 → .6 عند 29.557vmax → 0 عند 69.862vmax)،
 • نفس الدوران الخطي (دورة كل 26ث من لحظة الظهور)، ونفس ظهور الشفافية (bcx-rays-in .9s بعد .55s)، وتقليل الحركة = ثابتة بشفافية .8.
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-RAYS' in s: sys.exit('already patched (CODIS-RAYS)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

rep("""(rc.rays ? '<div class="bcx-rays' + (rc.rays > 1 ? ' is-x2' : '') + '" aria-hidden="true"></div>' : '')""",
    """(rc.rays ? '<canvas class="bcx-rays-cv" aria-hidden="true"></canvas>' : '')""", 'rays markup')

RAYS = r"""  /* CODIS-RAYS: الأشعة نفسها على canvas بحجم المشهد (بدل طبقة 140vmax دوّارة + طبقة قناع) — نفس الهندسة والألوان والدوران حرفياً */
  function raysStart(st, cv, rgb1, rgb2, x2, still){
    const ctx = cv.getContext && cv.getContext('2d'); if(!ctx || !ctx.createConicGradient){ return null; }
    const R = { cv:cv, ctx:ctx, t0:performance.now(), raf:0, w:0, h:0, dpr:0, on:true };
    const stops = [];   /* [deg0, deg1, rgba] لكل قطعة ملوّنة؛ الباقي شفاف — نفس repeating-conic-gradient */
    if(x2){ for(let a = 0; a < 360; a += 30){ stops.push([a, a + 5, 'rgba(' + rgb2 + ',.2)']); stops.push([a + 15, a + 21, 'rgba(' + rgb1 + ',.16)']); } }
    else { for(let a = 0; a < 360; a += 22) stops.push([a, a + 7, 'rgba(' + rgb1 + ',.16)']); }
    const CLR = 'rgba(0,0,0,0)';
    function size(){
      const w = cv.clientWidth, h = cv.clientHeight, d = window.devicePixelRatio || 1;
      if(w === R.w && h === R.h && d === R.dpr) return; R.w = w; R.h = h; R.dpr = d;
      cv.width = Math.max(1, Math.round(w * d)); cv.height = Math.max(1, Math.round(h * d));
    }
    function draw(now){
      if(!R.on) return;
      size();
      const w = R.w, h = R.h, d = R.dpr, cx = w * .5, cy = h * .46, vmax = Math.max(window.innerWidth, window.innerHeight) / 100;
      const ang = still ? 0 : ((((R.at !== undefined ? R.at : now - R.t0)) % 26000) / 26000) * Math.PI * 2;   /* R.at: تثبيت زمن للاختبار فقط */
      ctx.setTransform(d, 0, 0, d, 0, 0); ctx.globalCompositeOperation = 'source-over'; ctx.clearRect(0, 0, w, h);
      const g = ctx.createConicGradient(-Math.PI / 2 + ang, cx, cy);
      let last = 0;
      stops.forEach(p=>{ const a0 = Math.min(p[0], 360) / 360, a1 = Math.min(p[1], 360) / 360; if(a0 >= 1) return;
        g.addColorStop(Math.max(last, a0), CLR); g.addColorStop(a0, p[2]); g.addColorStop(a1, p[2]); g.addColorStop(a1, CLR); last = a1; });
      if(last < 1) g.addColorStop(1, CLR);
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'destination-in';
      const r1 = 69.862 * vmax, m = ctx.createRadialGradient(cx, cy, 0, cx, cy, r1);
      m.addColorStop(0, 'rgba(0,0,0,1)'); m.addColorStop(29.557 / 69.862, 'rgba(0,0,0,.6)'); m.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = m; ctx.fillRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'source-over';
      if(!still) R.raf = requestAnimationFrame(draw);
    }
    draw(R.t0);
    return R;
  }
  function raysStop(R){ if(!R) return; R.on = false; if(R.raf) cancelAnimationFrame(R.raf); try{ R.cv.width = 1; R.cv.height = 1; }catch(e){} }
  function play(r, it){"""
rep("  function play(r, it){", RAYS, 'rays fn')
rep("      document.body.appendChild(root);",
    "      document.body.appendChild(root);\n      { const rcv = root.querySelector('.bcx-rays-cv'); if(rcv) root._rays = raysStart(null, rcv, info.rgb, info.rgb2, rc.rays > 1, CodisMotion.isReduced()); }   /* CODIS-RAYS */", 'rays start')
rep("    const end = ()=>{ if(fin) return; fin = true; st.tm.forEach(clearTimeout); try{ st.root.remove(); }catch(e){}",
    "    const end = ()=>{ if(fin) return; fin = true; st.tm.forEach(clearTimeout); raysStop(st.root._rays); try{ st.root.remove(); }catch(e){}", 'rays stop')
rep("    }catch(e){ console.error('CodisBuyCine:', e); try{ if(s && s.root) s.root.remove(); }catch(x){} s = null; return false; }",
    "    }catch(e){ console.error('CodisBuyCine:', e); try{ if(s && s.root){ raysStop(s.root._rays); s.root.remove(); } }catch(x){} s = null; return false; }", 'rays stop on error')

CSS = """
/* CODIS-RAYS: الأشعة على canvas بحجم المشهد — نفس ظهور الشفافية؛ تقليل الحركة = ثابتة بشفافية .8 كما كانت */
.bcx-rays-cv{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; opacity:0; animation:bcx-rays-in .9s .55s ease-out forwards; }
@media (prefers-reduced-motion:reduce){ .bcx-rays-cv{ animation:none; opacity:.8; } }
"""
i = s.index("</style>"); s = s[:i] + CSS + s[i:]
s = s.replace('<meta name="codis-version"', '<!-- CODIS-RAYS --><meta name="codis-version"', 1)
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('ok')
