/* ===== CODIS-USE-CINE v2 (3.23.0) — مشهد استخدام المكافأة المملوكة =====
   • عرض فقط: يُستدعى بعد نجاح CodisEconomy.markUsed أو بدء المؤقت وحفظه (من «بحوزتك» ومن زر «استخدام» بمشهد الشراء). لا يمنح ولا يخصم ولا يغيّر بيانات؛
     فشله لا يمسّ العملية (play ترجع false ← التنبيه القديم).
   • الشكل: بطاقة ثلاثية الأبعاد (ظهر حبري بنقش غيوشيه ذهبي ← وجه ورقي فاخر) تطير وتنقلب، إطار رقائقي تتدرج خامته بالمستوى (حبر · نحاس · ذهب · هولوغرافي · طيفي)،
     ميلان تفاعلي مع الإصبع/المؤشر وانعكاس ضوء ولمعة هولوغرافية تتبعه، ختم يُضغط (انضغاط البطاقة + موجة + اهتزاز خفيف + غبار ذهبي)، ووسوم «فهم» المكافأة ثم العبارة كلمة كلمة.
   • الجسيمات والأشعة على لوحتي canvas (خلف/أمام البطاقة) بحلقة rAF واحدة تتوقف وحدها عند الفراغ. تقليل الحركة ⇒ بلا قلب ولا جسيمات، ظهور هادئ.
   • القوة من السعر: paid المحفوظ (>0) وإلا coinValue المحفوظ وقت الحصول وإلا مستوى 1 — بحدود CodisRevealLevels نفسها. الرسالة من الاسم فقط (CodisRewardVoice).
   • لا إغلاق سريع: يبقى حتى «تمام»/النقر خارج البطاقة/Esc/رجوع، وإغلاق تلقائي فقط بعد وقت قراءة طويل. كل شيء يُنظَّف عند الإغلاق. */
const CodisUseCine = (function(){
  'use strict';
  /* flip 0 ظهور مباشر · 1 قلبة · 2 قلبة ودورة كاملة | foil خامة الإطار | shine مرات لمعة الإطار | dust غبار ذهبي · sparks شرر طويل · conf شرائط احتفال
     rings موجات · rays أشعة (1/2) · glow توهج · aurora شفق · flash وميض | fly مدة الطيران | buzz اهتزاز الجهاز */
  const R = [null,
    { flip:0, foil:'ink',    shine:0, dust:8,  sparks:0,  conf:0,  rings:1, rays:0, glow:.16, aurora:0, flash:0, fly:640,  buzz:6 },
    { flip:1, foil:'ink',    shine:1, dust:16, sparks:0,  conf:0,  rings:1, rays:0, glow:.2,  aurora:0, flash:0, fly:780,  buzz:8 },
    { flip:1, foil:'copper', shine:1, dust:24, sparks:6,  conf:0,  rings:1, rays:0, glow:.26, aurora:0, flash:0, fly:820,  buzz:8 },
    { flip:1, foil:'copper', shine:2, dust:32, sparks:10, conf:0,  rings:2, rays:0, glow:.3,  aurora:0, flash:0, fly:860,  buzz:10 },
    { flip:1, foil:'gold',   shine:1, dust:40, sparks:12, conf:30, rings:2, rays:0, glow:.36, aurora:0, flash:0, fly:900,  buzz:12 },
    { flip:1, foil:'gold',   shine:2, dust:50, sparks:16, conf:40, rings:2, rays:1, glow:.42, aurora:0, flash:0, fly:940,  buzz:14 },
    { flip:2, foil:'holo',   shine:2, dust:60, sparks:20, conf:55, rings:3, rays:1, glow:.48, aurora:0, flash:0, fly:1080, buzz:16 },
    { flip:2, foil:'holo',   shine:3, dust:72, sparks:26, conf:70, rings:3, rays:2, glow:.54, aurora:0, flash:0, fly:1140, buzz:18 },
    { flip:2, foil:'prism',  shine:3, dust:90, sparks:34, conf:95, rings:3, rays:2, glow:.6,  aurora:1, flash:1, fly:1240, buzz:22 }
  ];
  const GOLD = ['255,226,150', '255,200,90', '255,244,214', '240,170,70'];
  const CONF = ['#f5cf6b', '#e8873a', '#c8423a', '#2f8f83', '#f6eedb', '#6f7fd8', '#d65d95'];
  let s = null;
  const ease = { out:'cubic-bezier(.16,1,.3,1)', spring:'cubic-bezier(.34,1.45,.64,1)', io:'cubic-bezier(.65,0,.35,1)' };
  const rnd = (a, b)=>a + Math.random() * (b - a);
  const later = (fn, ms)=>{ if(!s) return; const st = s; st.tm.push(setTimeout(()=>{ if(s === st && !st.closing) fn(); }, Math.max(0, ms))); };
  function snap(it){ return it ? { uid:String(it.uid), name:String(it.name || ''), paid:it.paid, coinValue:it.coinValue, rewardId:it.rewardId || null } : null; }
  function priceOf(sn){ const p = Number(sn && sn.paid), c = Number(sn && sn.coinValue); if(sn && typeof sn.paid === 'number' && isFinite(p) && p > 0) return p; if(isFinite(c) && c > 0) return c; return NaN; }
  function levelOf(sn){ const v = priceOf(sn); return isFinite(v) ? CodisRevealLevels.levelOfValue(v) : 1; }
  const ROSETTE = '<svg viewBox="0 0 100 100" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="50" cy="50" r="44"/><circle cx="50" cy="50" r="38" stroke-dasharray="2 3"/><circle cx="50" cy="50" r="18"/>' +
    '<path d="M50 6v14M50 80v14M6 50h14M80 50h14M19 19l10 10M71 71l10 10M81 19L71 29M29 71L19 81"/></g><path d="M50 34l4.2 11.3 11.8.6-9.3 7.4 3.2 11.5L50 58.2l-9.9 6.6 3.2-11.5-9.3-7.4 11.8-.6z" fill="currentColor"/></svg>';
  const CORNER = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 22V9a7 7 0 0 1 7-7h13M2 15a13 13 0 0 1 13-13" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><circle cx="6" cy="6" r="1.5" fill="currentColor"/></svg>';
  const CHECK = '<svg class="ucx-chk" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg>';
  const CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="13" r="8" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M12 9v4.4l2.8 1.7M9.5 2.8h5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';

  /* ---------- طبقة الجسيمات (canvas) ---------- */
  function fxInit(st, rc, lite){
    const mk = cls=>{ const c = st.root.querySelector(cls); const ctx = c && c.getContext ? c.getContext('2d') : null; return ctx ? { cv:c, ctx:ctx } : null; };
    const F = { back:mk('.ucx-cv-b'), front:mk('.ucx-cv-f'), ps:[], rings:[], raf:0, w:0, h:0, dpr:Math.min(lite ? 1 : 2, window.devicePixelRatio || 1), rays:null, glow:null, aurora:null, t0:performance.now() };
    if(!F.back || !F.front) return null;
    function size(){ const r = st.root.getBoundingClientRect(); F.w = r.width; F.h = r.height; [F.back, F.front].forEach(L=>{ L.cv.width = Math.max(1, Math.round(F.w * F.dpr)); L.cv.height = Math.max(1, Math.round(F.h * F.dpr)); }); }
    size(); F.size = size;
    return F;
  }
  function fxCenter(st){ const F = st.fx; if(!F) return; const rb = st.root.getBoundingClientRect(), sb = st.root.querySelector('.ucx-stage').getBoundingClientRect(), f = st.fly;
    F.c = { x:sb.left - rb.left + f.offsetLeft + f.offsetWidth / 2, y:sb.top - rb.top + f.offsetTop + f.offsetHeight / 2 }; }
  function fxKick(){ const F = s && s.fx; if(F && !F.raf) F.raf = requestAnimationFrame(fxTick); }
  function fxTick(now){
    const st = s, F = st && st.fx; if(!F) return; F.raf = 0;
    const B = F.back.ctx, T = F.front.ctx, d = F.dpr, W = F.w, H = F.h;
    B.setTransform(d, 0, 0, d, 0, 0); T.setTransform(d, 0, 0, d, 0, 0); B.clearRect(0, 0, W, H); T.clearRect(0, 0, W, H);
    let alive = false;
    if(!F.c) fxCenter(st);
    const cx = F.c.x, cy = F.c.y;   /* مركز البطاقة مخزّن (موضعها التخطيطي بلا تحويلات) — لا قراءة تخطيط بكل إطار */
    /* توهج + أشعة + شفق خلف البطاقة */
    if(F.glow){ const g = F.glow, t = (now - g.t0) / g.dur; if(t < 1){ alive = true; const a = g.a * (t < .2 ? t / .2 : 1 - (t - .2) / .8 * .55);
      const rg = B.createRadialGradient(cx, cy, 0, cx, cy, Math.max(W, H) * .55); rg.addColorStop(0, 'rgba(' + g.rgb + ',' + a + ')'); rg.addColorStop(.45, 'rgba(' + g.rgb + ',' + a * .35 + ')'); rg.addColorStop(1, 'rgba(' + g.rgb + ',0)'); B.fillStyle = rg; B.fillRect(0, 0, W, H); } else F.glow = null; }
    if(F.aurora){ const g = F.aurora, t = (now - g.t0) / g.dur; if(t < 1){ alive = true; const a = .32 * Math.sin(Math.PI * t);
      [['120,90,255', -.3], ['40,220,200', .35], ['255,120,180', 0]].forEach((c, i)=>{ const x = cx + Math.cos(now / 900 + i * 2.1) * W * .32, y = cy + c[1] * H + Math.sin(now / 1100 + i) * H * .08, r = Math.max(W, H) * .42;
        const rg = B.createRadialGradient(x, y, 0, x, y, r); rg.addColorStop(0, 'rgba(' + c[0] + ',' + a + ')'); rg.addColorStop(1, 'rgba(' + c[0] + ',0)'); B.fillStyle = rg; B.fillRect(0, 0, W, H); }); } else F.aurora = null; }
    if(F.rays){ const g = F.rays, t = (now - g.t0) / g.dur; if(t < 1){ alive = true; const a = (t < .15 ? t / .15 : 1 - (t - .15) / .85) * g.a, rot = (now - g.t0) / 9000 * Math.PI * 2, R0 = Math.max(W, H) * .75, n = g.n;
      B.save(); B.translate(cx, cy); B.globalCompositeOperation = 'lighter';
      for(let k = 0; k < n; k++){ const an = rot + k * Math.PI * 2 / n, w = (k % 2 ? .05 : .09);
        const lg = B.createRadialGradient(0, 0, 0, 0, 0, R0); lg.addColorStop(0, 'rgba(255,230,160,' + a + ')'); lg.addColorStop(1, 'rgba(255,230,160,0)'); B.fillStyle = lg;
        B.beginPath(); B.moveTo(0, 0); B.arc(0, 0, R0, an - w, an + w); B.closePath(); B.fill(); }
      B.restore(); } else F.rays = null; }
    /* موجات */
    F.rings = F.rings.filter(r=>{ const t = (now - r.t0) / r.dur; if(t < 0){ alive = true; return true; } if(t >= 1) return false; alive = true;
      const e = 1 - Math.pow(1 - t, 3); T.beginPath(); T.arc(r.x, r.y, r.r0 + (r.r1 - r.r0) * e, 0, Math.PI * 2); T.strokeStyle = 'rgba(' + r.rgb + ',' + (1 - t) * .8 + ')'; T.lineWidth = r.w * (1 - t) + .5; T.stroke(); return true; });
    /* جسيمات */
    T.globalCompositeOperation = 'source-over';
    F.ps = F.ps.filter(p=>{
      if(p.delay > 0){ p.delay--; alive = true; return true; }
      p.life++; if(p.life > p.max) return false; alive = true;
      p.vx *= p.drag; p.vy = p.vy * p.drag + p.g; p.x += p.vx + (p.sway ? Math.sin((p.life + p.ph) / 14) * p.sway : 0); p.y += p.vy; p.rot += p.vr;
      const k = p.life / p.max, a = p.kind === 'conf' ? Math.min(1, (1 - k) * 3) : (1 - k) * (p.kind === 'dust' ? (.55 + .45 * Math.sin(p.life / 3 + p.ph)) : 1);
      if(p.kind === 'conf'){ T.save(); T.translate(p.x, p.y); T.rotate(p.rot); T.scale(1, Math.cos(p.life / 6 + p.ph)); T.globalAlpha = a; T.fillStyle = p.c; T.fillRect(-p.s / 2, -p.s * .9, p.s, p.s * 1.8); T.restore(); }
      else if(p.kind === 'spark'){ T.globalAlpha = a; T.strokeStyle = 'rgb(' + p.c + ')'; T.lineWidth = p.s; T.lineCap = 'round'; T.beginPath(); T.moveTo(p.x, p.y); T.lineTo(p.x - p.vx * 3.2, p.y - p.vy * 3.2); T.stroke(); }
      else { T.globalAlpha = a; T.fillStyle = 'rgb(' + p.c + ')'; T.beginPath(); T.arc(p.x, p.y, p.s, 0, Math.PI * 2); T.fill(); if(p.s > 1.8){ T.globalAlpha = a * .25; T.beginPath(); T.arc(p.x, p.y, p.s * 3, 0, Math.PI * 2); T.fill(); } }
      return true; });
    T.globalAlpha = 1;
    if(alive) F.raf = requestAnimationFrame(fxTick);
  }
  function burst(rc, lite){
    const st = s, F = st && st.fx; if(!F) return;
    const rb = st.root.getBoundingClientRect(), sr = st.root.querySelector('.ucx-seal').getBoundingClientRect(), cr = st.card.getBoundingClientRect();
    const x = sr.left + sr.width / 2 - rb.left, y = sr.top + sr.height / 2 - rb.top, n = k=>lite ? Math.ceil(k * .5) : k, now = performance.now();
    for(let i = 0; i < rc.rings; i++) F.rings.push({ x:x, y:y, r0:sr.width * .4, r1:sr.width * (1.6 + i * .9), w:3 - i * .6, t0:now + i * 110, dur:700 + i * 160, rgb:i ? '255,226,150' : '255,246,224' });
    if(rc.rings > 1) F.rings.push({ x:cr.left + cr.width / 2 - rb.left, y:cr.top + cr.height / 2 - rb.top, r0:cr.width * .5, r1:cr.width * 1.5, w:2, t0:now + 60, dur:900, rgb:'255,214,130' });
    for(let i = 0; i < n(rc.dust); i++){ const a = rnd(0, Math.PI * 2), v = rnd(1.2, 5.4); F.ps.push({ kind:'dust', x:x, y:y, vx:Math.cos(a) * v, vy:Math.sin(a) * v - 1.2, g:.035, drag:.955, life:0, max:rnd(55, 110) | 0, s:rnd(.8, 2.6), c:GOLD[i % GOLD.length], ph:rnd(0, 9), rot:0, vr:0, delay:0 }); }
    for(let i = 0; i < n(rc.sparks); i++){ const a = rnd(0, Math.PI * 2), v = rnd(5, 9.5); F.ps.push({ kind:'spark', x:x, y:y, vx:Math.cos(a) * v, vy:Math.sin(a) * v, g:.05, drag:.93, life:0, max:rnd(24, 40) | 0, s:rnd(1.1, 2), c:'255,236,190', ph:0, rot:0, vr:0, delay:0 }); }
    for(let i = 0; i < n(rc.conf); i++){ F.ps.push({ kind:'conf', x:rnd(0, F.w), y:rnd(-60, -10), vx:rnd(-.6, .6), vy:rnd(1.6, 3.4), g:.012, drag:.995, sway:rnd(.4, 1.3), life:0, max:rnd(170, 260) | 0, s:rnd(5, 8), c:CONF[i % CONF.length], ph:rnd(0, 30), rot:rnd(0, 6), vr:rnd(-.12, .12), delay:rnd(0, 26) | 0 }); }
    if(rc.rays) F.rays = { t0:now, dur:3200, a:rc.rays > 1 ? .2 : .14, n:rc.rays > 1 ? 18 : 12 };
    if(rc.aurora && !lite) F.aurora = { t0:now, dur:4200 };
    fxKick();
  }

  /* ---------- الميلان التفاعلي ---------- */
  function tiltOn(st){
    const tilt = st.root.querySelector('.ucx-tilt'), card = st.card; let raf = 0, px = 0, py = 0;
    const apply = ()=>{ raf = 0; if(!st.ready || st.closing) return; const r = card.getBoundingClientRect(); if(!r.width) return;
      const nx = Math.max(-1, Math.min(1, (px - (r.left + r.width / 2)) / (r.width * .75))), ny = Math.max(-1, Math.min(1, (py - (r.top + r.height / 2)) / (r.height * .75)));
      tilt.style.transform = 'rotateX(' + (-ny * 13).toFixed(2) + 'deg) rotateY(' + (nx * 15).toFixed(2) + 'deg)';
      card.style.setProperty('--mx', (50 + nx * 42).toFixed(1) + '%'); card.style.setProperty('--my', (50 + ny * 42).toFixed(1) + '%'); };
    st.onMove = e=>{ px = e.clientX; py = e.clientY; if(!raf) raf = requestAnimationFrame(apply); };
    st.onLeave = ()=>{ tilt.style.transform = ''; card.style.setProperty('--mx', '50%'); card.style.setProperty('--my', '30%'); };
    st.root.addEventListener('pointermove', st.onMove); st.root.addEventListener('pointerleave', st.onLeave); st.root.addEventListener('pointerup', e=>{ if(e.pointerType !== 'mouse') st.onLeave(); });
  }

  function play(sn, o){
    try{
      o = o || {};
      if(!sn || !sn.uid || !sn.name) return false;
      if(s) cleanup();
      const timed = !!o.timed, lv = levelOf(sn), rc = R[lv];
      const reduced = CodisMotion.isReduced(), lite = reduced || (navigator.hardwareConcurrency || 8) <= 4;
      const v = CodisRewardVoice.compose(sn.name, sn.uid, { timed:timed, memo:true });
      const bx = document.body.getBoundingClientRect(), vw = Math.min(innerWidth, bx.width || innerWidth);
      const W = Math.round(Math.max(168, Math.min(236, vw * .6, (innerHeight - 340) / 1.4)));
      const nl = sn.name.length, nCls = nl <= 12 ? 'n1' : nl <= 22 ? 'n2' : nl <= 40 ? 'n3' : 'n4';
      const root = document.createElement('div');
      root.className = 'ucx lv-' + lv + ' f-' + rc.foil + (reduced ? ' is-reduced' : ' is-anim') + (timed ? ' is-timed' : '');
      root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true'); root.setAttribute('aria-label', (timed ? 'بدأت المكافأة: ' : 'استُخدمت المكافأة: ') + sn.name); root.setAttribute('aria-describedby', 'ucx-msg');
      root.style.setProperty('--w', W + 'px');
      const words = v.text.split(' ').map((w, i)=>'<span class="ucx-w" style="--i:' + i + '">' + escapeHtml(w) + '</span>').join(' ');
      const tags = (v.tags || []).slice(0, 4).map(t=>'<span class="ucx-tag">' + escapeHtml(t) + '</span>').join('');
      const dur = timed && o.dur ? CodisDuration.label(o.dur.min) : '';
      let corners = ''; for(let i = 1; i <= 4; i++) corners += '<i class="ucx-cn c' + i + '" aria-hidden="true">' + CORNER + '</i>';
      root.innerHTML = '<div class="ucx-bg"></div><canvas class="ucx-cv ucx-cv-b" aria-hidden="true"></canvas>' +
        '<div class="ucx-stage"><div class="ucx-fly"><div class="ucx-float"><div class="ucx-tilt"><div class="ucx-card" style="width:' + W + 'px">' +
          '<div class="ucx-back" aria-hidden="true"><i class="ucx-guil"></i><span class="ucx-ros">' + ROSETTE + '</span><b class="ucx-mark">CODIS</b></div>' +
          '<div class="ucx-paper"><i class="ucx-foil" aria-hidden="true"></i><i class="ucx-rule" aria-hidden="true"></i>' + corners +
            '<div class="ucx-brand" aria-hidden="true"><i></i>CODIS<i></i></div>' +
            '<span class="ucx-medal" aria-hidden="true">' + ROSETTE + '</span>' +
            '<div class="ucx-name ' + nCls + '" dir="auto">' + escapeHtml(sn.name) + '</div>' +
            '<div class="ucx-kicker">' + (timed ? 'بدأ وقت المكافأة' : 'مكافأة مستخدَمة') + '</div>' +
            '<div class="ucx-seal" aria-hidden="true"><span class="ucx-seal-in">' + (timed ? CLOCK : CHECK) + '<b>' + (timed ? 'بدأت' : 'استُخدمت') + '</b></span></div>' +
            '<i class="ucx-holo" aria-hidden="true"></i><i class="ucx-spec" aria-hidden="true"></i><i class="ucx-shine" aria-hidden="true"></i>' +
          '</div></div></div></div></div>' +
          '<div class="ucx-tags" aria-hidden="true">' + tags + '</div>' +
          '<p class="ucx-msg" id="ucx-msg" dir="auto">' + words + '</p>' +
          (timed ? '<div class="ucx-chip">' + CLOCK + '<b>' + escapeHtml(dur) + '</b><span>العدّاد شغّال</span></div>' : '') +
          '<div class="ucx-acts"><button type="button" class="ucx-ok">تمام</button></div>' +
        '</div><canvas class="ucx-cv ucx-cv-f" aria-hidden="true"></canvas>' +
        '<button type="button" class="ucx-x" aria-label="إغلاق"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none"/></svg></button>';
      document.body.appendChild(root);
      s = { root:root, card:root.querySelector('.ucx-card'), fly:root.querySelector('.ucx-fly'), tm:[], closing:false, ready:false, t0:Date.now(), prev:document.activeElement, lv:lv, text:v.text, ctx:v.ctx, tags:v.tags, uid:sn.uid, timed:timed, fx:null };
      const st = s;
      st.fx = reduced ? null : fxInit(st, rc, lite);
      st.onKey = e=>{ if(e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); dismiss(); } else if(e.key === 'Tab'){ e.preventDefault(); const b = st.root.querySelector(st.ready ? '.ucx-ok' : '.ucx-x'); try{ b.focus(); }catch(x){} } };
      st.onResize = ()=>{ if(st.fx){ st.fx.size(); fxCenter(st); } };
      root.addEventListener('keydown', st.onKey); window.addEventListener('resize', st.onResize);
      root.querySelector('.ucx-x').addEventListener('click', e=>{ e.stopPropagation(); dismiss(); });
      root.querySelector('.ucx-ok').addEventListener('click', e=>{ e.stopPropagation(); dismiss(); });
      root.addEventListener('click', e=>{ if(st.ready && !e.target.closest('.ucx-card, .ucx-acts, .ucx-msg')) dismiss(); });
      if(!reduced) tiltOn(st);
      try{ root.querySelector('.ucx-x').focus({ preventScroll:true }); }catch(e){}
      try{ CodisCrumb.mark('use:cine', 'lv' + lv); }catch(e){}

      /* ---- التسلسل ---- */
      const A = codisAnim, FLY = reduced ? 0 : rc.fly;
      A(root.querySelector('.ucx-bg'), [{ opacity:0 }, { opacity:1 }], { dur:380, ease:'linear', fill:'both' });
      if(st.fx){ st.fx.glow = { t0:performance.now(), dur:FLY + 5200, a:rc.glow, rgb:rc.foil === 'holo' || rc.foil === 'prism' ? '200,190,255' : '255,206,120' }; fxKick(); }
      A(st.fly, [{ transform:'translateY(58vh) scale(.62)', opacity:0 }, { transform:'translateY(-14px) scale(1.04)', opacity:1, offset:.72 }, { transform:'translateY(0) scale(1)', opacity:1 }], { dur:FLY || 300, ease:ease.out, fill:'both' });
      /* الصوت: كل حركة لها صوتها بنفس لحظتها (هويات use.* بمحرك الصوت؛ قناة المكافآت وإعدادات المستخدم) */
      if(!reduced){ codisSfx('use.whoosh', { lv:lv, seq:true }); }
      if(rc.flip && !reduced){
        const from = rc.flip > 1 ? 540 : 180;
        A(st.card, [{ transform:'rotateY(' + from + 'deg) rotateZ(-6deg)' }, { transform:'rotateY(-14deg) rotateZ(1.5deg)', offset:.74 }, { transform:'rotateY(4deg) rotateZ(0deg)', offset:.88 }, { transform:'rotateY(0deg) rotateZ(0deg)' }], { dur:FLY, ease:ease.out, fill:'both' });
        later(()=>{ codisSfx('use.flip', { n:rc.flip, seq:true }); }, Math.round(FLY * .22));
      } else if(!reduced){ later(()=>{ codisSfx('use.land', { seq:true }); }, Math.round(FLY * .62)); }
      /* الختم: يبدأ نزوله والبطاقة تستقر (لا انتظار بعد الهبوط) — نزول متسارع ثقيل ثم ارتداد ناعم؛ لحظة الارتطام = منتصف الحركة */
      const seal = root.querySelector('.ucx-seal-in'), tStamp = reduced ? 80 : Math.max(0, FLY - 70), impact = tStamp + (reduced ? 0 : 150);
      A(seal, [{ transform:'scale(2.4) rotate(-30deg)', opacity:0, easing:'cubic-bezier(.55,0,.85,.35)' }, { transform:'scale(.9) rotate(-10deg)', opacity:1, offset:.5, easing:'cubic-bezier(.2,.9,.3,1)' }, { transform:'scale(1.04) rotate(-13deg)', opacity:1, offset:.75 }, { transform:'scale(1) rotate(-12deg)', opacity:1 }], { dur:reduced ? 140 : 300, delay:tStamp, ease:'linear', fill:'both' });
      if(!reduced) later(()=>{ codisSfx('use.drop', { seq:true }); }, tStamp);
      const chk = root.querySelector('.ucx-chk path'); if(chk && !reduced) A(chk, [{ strokeDashoffset:1 }, { strokeDashoffset:0 }], { dur:280, delay:impact + 50, ease:ease.out, fill:'both' });
      later(()=>{
        codisSfx('use.stamp', { lv:lv, foil:rc.foil, seq:true });
        if(reduced) return;
        A(st.fly, [{ transform:'scale(1)' }, { transform:'scale(.962,.948) translateY(3px)' }, { transform:'scale(1.012)' }, { transform:'scale(1)' }], { dur:300, ease:'ease-out', fill:'none' });
        if(rc.flash){ const f = document.createElement('i'); f.className = 'ucx-flash'; root.appendChild(f); A(f, [{ opacity:0 }, { opacity:.75, offset:.2 }, { opacity:0 }], { dur:700, ease:'ease-out', fill:'both' }); }
        burst(rc, lite);
        try{ if(navigator.vibrate) navigator.vibrate(rc.buzz); }catch(e){}
        codisSfx('use.sparkle', { lv:lv, delay:.05, seq:true });
      }, impact);
      if(!reduced){ if(timed){ later(()=>{ codisSfx('use.tick', { seq:true }); }, impact + 120); } else { later(()=>{ codisSfx('use.check', { seq:true }); }, impact + 50); } }
      /* لمعة الإطار والوجه بعد الارتطام */
      const sh = root.querySelector('.ucx-shine');
      for(let i = 0; i < rc.shine && !reduced; i++) A(sh, [{ transform:'translateX(-130%) skewX(-16deg)', opacity:1 }, { transform:'translateX(230%) skewX(-16deg)', opacity:1 }], { dur:900, delay:impact + 140 + i * 760, ease:'cubic-bezier(.5,0,.3,1)', fill:'none' });
      if(rc.shine > 1 && !reduced) A(root.querySelector('.ucx-foil'), [{ backgroundPosition:'0% 50%' }, { backgroundPosition:'100% 50%' }, { backgroundPosition:'0% 50%' }], { dur:2600, delay:impact, ease:ease.io, fill:'none' });
      /* الوسوم ثم العبارة كلمة كلمة (مقروءة) */
      const tTags = reduced ? 0 : impact + 170;
      root.querySelectorAll('.ucx-tag').forEach((t, i)=>{ A(t, [{ transform:'translateY(8px) scale(.85)', opacity:0 }, { transform:'translateY(0) scale(1)', opacity:1 }], { dur:420, delay:tTags + i * 110, ease:ease.spring, fill:'both' });
        if(!reduced) later(()=>{ codisSfx('use.tag', { i:i, seq:true }); }, tTags + i * 110 + 40); });
      const ws = root.querySelectorAll('.ucx-w'), tMsg = reduced ? 0 : tTags + 200, step = 95;
      ws.forEach((w, i)=>{ A(w, [{ transform:'translateY(12px)', opacity:0, filter:'blur(6px)' }, { transform:'translateY(0)', opacity:1, filter:'blur(0px)' }], { dur:560, delay:tMsg + i * step, ease:ease.out, fill:'both' });
        if(!reduced) later(()=>{ codisSfx('use.word', { i:i, seq:true }); }, tMsg + i * step + 60); });
      const chip = root.querySelector('.ucx-chip'); if(chip) A(chip, [{ transform:'translateY(8px)', opacity:0 }, { transform:'translateY(0)', opacity:1 }], { dur:420, delay:tMsg + ws.length * step + 120, ease:ease.out, fill:'both' });
      const tEnd = tMsg + ws.length * step + 560;
      const acts = root.querySelector('.ucx-acts');
      A(acts, [{ transform:'translateY(10px)', opacity:0 }, { transform:'translateY(0)', opacity:1 }], { dur:380, delay:reduced ? 0 : tEnd, ease:ease.out, fill:'both' });
      later(()=>{ root.classList.remove('is-anim'); }, impact + 700);
      later(()=>{ st.ready = true; root.classList.add('is-ready'); try{ root.querySelector('.ucx-ok').focus({ preventScroll:true }); }catch(e){} if(!reduced) root.querySelector('.ucx-float').classList.add('is-idle'); }, reduced ? 200 : tEnd + 200);
      later(dismiss, Math.max(tEnd + 9000, 12000 + v.text.length * 60));   /* إغلاق تلقائي فقط بعد وقت قراءة طويل */
      return true;
    }catch(e){ console.error('CodisUseCine:', e); try{ cleanup(); }catch(x){} return false; }
  }
  function cleanup(){
    const st = s; if(!st) return; s = null;
    st.closing = true; st.tm.forEach(clearTimeout);
    if(st.fx){ if(st.fx.raf) cancelAnimationFrame(st.fx.raf); st.fx.ps = []; try{ [st.fx.back, st.fx.front].forEach(L=>{ L.cv.width = 1; L.cv.height = 1; }); }catch(e){} st.fx = null; }
    try{ window.removeEventListener('resize', st.onResize); st.root.removeEventListener('keydown', st.onKey); if(st.onMove){ st.root.removeEventListener('pointermove', st.onMove); st.root.removeEventListener('pointerleave', st.onLeave); } st.root.remove(); }catch(e){}
    try{ if(st.prev && st.prev.focus && document.contains(st.prev)) st.prev.focus({ preventScroll:true }); }catch(e){}
    try{ CodisCrumb.idle(); }catch(e){}
  }
  function dismiss(){
    if(!s || s.closing) return; const st = s; st.closing = true; st.tm.forEach(clearTimeout); st.root.classList.add('is-out');
    codisSfx('use.close', { seq:true });
    let fin = false; const end = ()=>{ if(fin) return; fin = true; if(s === st){ st.closing = false; cleanup(); } };
    const a = codisAnim(st.root, [{ opacity:1 }, { opacity:0 }], { dur:260, ease:'linear', fill:'forwards', done:end });
    if(!a) end(); else setTimeout(end, 380);
  }
  return { play:play, snap:snap, levelOf:levelOf, priceOf:priceOf, dismiss:dismiss, isOpen:()=>!!s, el:()=>s && s.root, _state:()=>s, _recipes:R };
})();
