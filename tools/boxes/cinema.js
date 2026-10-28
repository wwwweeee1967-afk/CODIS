/* =====================================================================
   CODIS · CodisBoxCinema v3 — طقس فتح الصندوق ثلاثي الأبعاد + كشف المكافأة (CODIS-BOXES-V3)
   • عرض فقط: المكافأة تُسحب وتُمنح داخل CodisBoxes.open() قبل بدء أي حركة. هذا الملف لا يلمس الاقتصاد ولا المحفظة ولا الحفظ.
   • المجسّم: رسم الصندوق الفعلي يُقسَم عند خط غطائه إلى جسم + غطاء (clip-path) داخل منظور CSS 3D؛ الغطاء يدور حول خط الدرزة، وقالب ضوء بشكل الغطاء نفسه (mask) يملأ الفتحة. لا مكتبة 3D خارجية.
   • شخصية كل مستوى (TIER): لون الضوء، شدة الاهتزاز، مدة الترقّب، رفع الغطاء، نوع الجسيمات، مدار الكاميرا — مع هيكل واحد مشترك.
   • الكشف: مستواه من CodisRevealLevels (القيمة الفعلية للجائزة الممنوحة) فقط، خمس مجموعات بصرية: 1–2 · 3–4 · 5–6 · 7–8 · 9.
   • حركة بـ Web Animations (transform/opacity) + Canvas واحد للجسيمات + حلقة rAF واحدة تتوقف عند الفراغ؛ كل شيء يُلغى في cleanup() (إغلاق/تخطّي/فتح آخر).
   ===================================================================== */
const CodisBoxCinema = (function(){
  'use strict';
  const E = { out:'cubic-bezier(.16,1,.3,1)', in:'cubic-bezier(.5,0,.9,.4)', io:'cubic-bezier(.65,0,.35,1)', spring:'cubic-bezier(.34,1.56,.64,1)', lin:'linear' };
  /* rgb = لون ضوء الفتحة (مأخوذ من ألوان رسم الصندوق نفسه) · rgb2 = لون الحافة/الشرر · shake = شدة الاهتزاز · ant = مدة الترقّب (ms) · lift = رفع الغطاء % · rot = زاوية دورانه ·
     parts = نوع الجسيمات · n = كثافتها · cam = دفع الكاميرا · orbit = مدار الكاميرا قبل الفتح (درجات) */
  const TIER = [null,
    { rgb:'255,176,92',  rgb2:'104,228,236', shake:.9,  ant:640,  lift:-15, rot:52, parts:'dust',    n:24, cam:1.05, orbit:0,  gap:.8 },
    { rgb:'128,204,255', rgb2:'196,238,255', shake:1.1, ant:780,  lift:-17, rot:58, parts:'shard',   n:34, cam:1.07, orbit:0,  gap:1  },
    { rgb:'104,172,255', rgb2:'178,126,255', shake:1.25,ant:930,  lift:-19, rot:62, parts:'crystal', n:44, cam:1.08, orbit:9,  gap:1.1 },
    { rgb:'255,192,86',  rgb2:'255,122,62',  shake:1.5, ant:1020, lift:-19, rot:60, parts:'ember',   n:54, cam:1.10, orbit:0,  gap:1.3 },
    { rgb:'255,224,142', rgb2:'112,230,255', shake:1.75,ant:1260, lift:-22, rot:66, parts:'aura',    n:72, cam:1.12, orbit:16, gap:1.5 }
  ];
  let S = null;

  /* ---------- بناء المجسّم (مشترك: السكون + الطقس + الصناديق المصغّرة بالعشرة) ---------- */
  function rigStyle(n){
    const a = econBoxArtMeta(n), u = econBoxArtUrl(n), T = TIER[Math.max(1, Math.min(5, n | 0))];
    return '--ar:' + a.w + '/' + a.h + ';--wf:' + a.wf + ';--sm:' + ((a.seam[0] + a.seam[1]) * 50).toFixed(2) + '%;--sl:' + (a.seam[0] * 100).toFixed(2) + '%;--sr:' + (a.seam[1] * 100).toFixed(2) + '%;--mask:url(' + u + ');--cb-rgb:' + T.rgb + ';--cb-rgb2:' + T.rgb2;
  }
  function rigHtml(n, mini){
    const u = econBoxArtUrl(n);
    return '<div class="cb-rig' + (mini ? ' is-mini' : '') + '" style="' + rigStyle(n) + '">' + (mini ? '' : '<div class="cb-glow"></div>') +
      '<div class="cb-body"><img class="cb-img" alt="" draggable="false" src="' + u + '"></div><div class="cb-mouth"></div>' + (mini ? '' : '<div class="cb-beam"></div>') +
      '<div class="cb-lid"><img class="cb-img" alt="" draggable="false" src="' + u + '"></div></div>';
  }
  /* شاشة الجاهزية: الصندوق مغلق على منصّة ويستجيب للمس/الفأرة بميلان منظوري خفيف */
  function idleHtml(n){
    return '<div class="bx-stage cb-idle" data-n="' + n + '"><div class="cb-floor is-static" aria-hidden="true"></div><div class="cb-box is-idle">' + rigHtml(n) + '</div></div>';
  }
  function bindIdle(root){
    const st = root && root.querySelector('.cb-idle'); if(!st) return;
    const box = st.querySelector('.cb-box'); let raf = 0, rx = 0, ry = 0;
    const apply = ()=>{ raf = 0; box.style.setProperty('--rx', rx.toFixed(2) + 'deg'); box.style.setProperty('--ry', ry.toFixed(2) + 'deg'); };
    const move = ev=>{ const r = st.getBoundingClientRect(); if(!r.width) return; ry = ((ev.clientX - r.left) / r.width - .5) * 26; rx = -((ev.clientY - r.top) / r.height - .5) * 16; if(!raf) raf = requestAnimationFrame(apply); };
    const leave = ()=>{ rx = 0; ry = 0; if(!raf) raf = requestAnimationFrame(apply); st.classList.remove('is-hot'); };
    st.addEventListener('pointermove', ev=>{ st.classList.add('is-hot'); move(ev); }); st.addEventListener('pointerleave', leave); st.addEventListener('pointercancel', leave);
  }

  /* ---------- جسيمات (Canvas واحد) ---------- */
  function Fx(cv, q, kick){
    const ctx = cv.getContext('2d'), P = []; let W = 0, H = 0, dpr = 1;
    function size(){ const r = cv.getBoundingClientRect(); dpr = Math.min(window.devicePixelRatio || 1, q > .8 ? 1.75 : 1.25); W = r.width; H = r.height; cv.width = Math.max(1, Math.round(W * dpr)); cv.height = Math.max(1, Math.round(H * dpr)); }
    const rnd = (a, b)=>a + Math.random() * (b - a);
    /* kind: spark | dust | shard | ember | star | mote — o: ang[min,max] rad · sp[min,max] px/s · life · size · rgb · g · drag · jx */
    function em(kind, x, y, n, o){
      o = o || {}; n = Math.max(1, Math.round(n * q)); kick();
      for(let i = 0; i < n; i++){
        const a = rnd((o.ang || [0, 6.283])[0], (o.ang || [0, 6.283])[1]), s = rnd((o.sp || [60, 180])[0], (o.sp || [60, 180])[1]), l = rnd((o.life || [.5, 1])[0], (o.life || [.5, 1])[1]);
        P.push({ k:kind, x:x + rnd(-(o.jx || 0), o.jx || 0), y:y + rnd(-(o.jy || 0), o.jy || 0), vx:Math.cos(a) * s, vy:Math.sin(a) * s, life:l, max:l, sz:rnd((o.size || [2, 4])[0], (o.size || [2, 4])[1]), rgb:o.rgb || '255,255,255', g:o.g == null ? 0 : o.g, drag:o.drag == null ? .6 : o.drag, rot:rnd(0, 6.283), vr:rnd(-4, 4) });
      }
      if(P.length > 420) P.splice(0, P.length - 420);
    }
    function step(dt){
      if(!W) size(); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H); if(!P.length) return 0;
      ctx.globalCompositeOperation = 'lighter';
      for(let i = P.length - 1; i >= 0; i--){
        const p = P[i]; p.life -= dt; if(p.life <= 0){ P.splice(i, 1); continue; }
        const d = Math.pow(p.drag, dt); p.vx *= d; p.vy = p.vy * d + p.g * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.vr * dt;
        const t = p.life / p.max, al = Math.min(1, t * 2.2) * (p.k === 'mote' ? .55 : 1), c = p.rgb;
        if(p.k === 'dust'){ const r = p.sz * (2.4 - t); const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r); g.addColorStop(0, 'rgba(' + c + ',' + (al * .5) + ')'); g.addColorStop(1, 'rgba(' + c + ',0)'); ctx.fillStyle = g; ctx.fillRect(p.x - r, p.y - r, r * 2, r * 2); }
        else if(p.k === 'spark'){ ctx.strokeStyle = 'rgba(' + c + ',' + al + ')'; ctx.lineWidth = Math.max(1, p.sz * .5); ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - p.vx * .035, p.y - p.vy * .035); ctx.stroke(); }
        else if(p.k === 'shard' || p.k === 'crystal'){ ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.fillStyle = 'rgba(' + c + ',' + (al * .85) + ')'; ctx.beginPath(); ctx.moveTo(0, -p.sz * 1.7); ctx.lineTo(p.sz * .8, 0); ctx.lineTo(0, p.sz * 1.7); ctx.lineTo(-p.sz * .8, 0); ctx.closePath(); ctx.fill(); ctx.restore(); }
        else if(p.k === 'star'){ ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot * .3); const r = p.sz * (1.2 + Math.sin(t * 6.28) * .3); ctx.fillStyle = 'rgba(' + c + ',' + al + ')'; ctx.beginPath(); ctx.moveTo(0, -r * 2); ctx.lineTo(r * .3, -r * .3); ctx.lineTo(r * 2, 0); ctx.lineTo(r * .3, r * .3); ctx.lineTo(0, r * 2); ctx.lineTo(-r * .3, r * .3); ctx.lineTo(-r * 2, 0); ctx.lineTo(-r * .3, -r * .3); ctx.closePath(); ctx.fill(); ctx.restore(); }
        else { const r = p.sz * (p.k === 'ember' ? 1.3 : 1); const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 2.2); g.addColorStop(0, 'rgba(' + c + ',' + al + ')'); g.addColorStop(1, 'rgba(' + c + ',0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, r * 2.2, 0, 6.283); ctx.fill(); }
      }
      ctx.globalCompositeOperation = 'source-over'; return P.length;
    }
    return { em:em, step:step, size:size, clear:()=>{ P.length = 0; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height); }, get n(){ return P.length; }, get w(){ return W; }, get h(){ return H; } };
  }

  /* ---------- أدوات ---------- */
  const A = (el, kf, opt)=>{ const a = el.animate(kf, Object.assign({ fill:'both' }, opt)); S.anims.push(a); return a; };
  const cue = (t, fn)=>{ S.cues.push({ t:t, fn:fn }); S.cues.sort((a, b)=>a.t - b.t); kick(); };
  const now = ()=>S.t0 ? performance.now() - S.t0 : 0;
  const mk = (cls, css)=>{ const d = document.createElement('div'); d.className = cls; if(css) d.style.cssText = css; S.world.insertBefore(d, S.el.flash); return d; };
  /* موضع نقطة داخل world (px) من عنصر */
  function centerOf(el){ const w = S.world.getBoundingClientRect(), r = el.getBoundingClientRect(); return { x:r.left - w.left + r.width / 2, y:r.top - w.top + r.height / 2, w:r.width, h:r.height }; }
  function mouthPos(){ const r = S.el.box.getBoundingClientRect(), w = S.world.getBoundingClientRect(), a = econBoxArtMeta(S.n); return { x:r.left - w.left + r.width / 2, y:r.top - w.top + r.height * ((a.seam[0] + a.seam[1]) / 2), w:r.width }; }

  /* ---------- التشغيل ---------- */
  function play(o){
    if(S){ if(S.state !== 'done') return false; cleanup(); }
    const sheet = document.querySelector('#econ-box-modal .bx-modal'), t = o.tier, rar = o.result && o.result.rarity;
    if(!sheet || !t || !rar || !sheet.animate || !document.getElementById('econ-box-body')) return false;
    const n = Math.max(1, Math.min(5, t.index | 0)), T = TIER[n], h0 = sheet.offsetHeight;
    const world = document.createElement('div'); world.className = 'cb-world'; world.setAttribute('aria-hidden', 'true'); world.setAttribute('data-n', String(n));
    world.innerHTML = '<div class="cb-bg"></div><div class="cb-rays"></div><canvas class="cb-fx"></canvas><div class="cb-cam"><div class="cb-floor"></div><div class="cb-box">' + rigHtml(n) + '</div></div><div class="cb-flash"></div><div class="cb-vig"></div>';
    sheet.insertBefore(world, sheet.firstChild); sheet.classList.add('is-cine', 'is-opening'); o.state.cine = true;
    const h1 = sheet.offsetHeight; try{ sheet.animate([{ height:h0 + 'px' }, { height:h1 + 'px' }], { duration:480, easing:E.out }); }catch(e){}
    const q = s=>world.querySelector(s), nav = navigator, low = (nav.hardwareConcurrency || 8) <= 4 || (nav.deviceMemory || 8) <= 2 || window.innerWidth <= 520;
    const el = { bg:q('.cb-bg'), rays:q('.cb-rays'), cv:q('.cb-fx'), cam:q('.cb-cam'), floor:q('.cb-floor'), box:q('.cb-box'), rig:q('.cb-rig'), glow:q('.cb-glow'), body:q('.cb-body'), mouth:q('.cb-mouth'), beam:q('.cb-beam'), lid:q('.cb-lid'), flash:q('.cb-flash'), vig:q('.cb-vig') };
    const lv = CodisRevealLevels.levelOfResult(o.result), RL = CodisRevealLevels.info(lv);
    world.style.setProperty('--cb-rgb', T.rgb); world.style.setProperty('--cb-rgb2', T.rgb2);
    S = { o:o, sheet:sheet, world:world, el:el, n:n, T:T, lv:lv, RL:RL, low:low, anims:[], cues:[], ci:0, state:'play', raf:0, t0:0, last:0, wd:0, fx:null, ov:document.getElementById('econ-box-modal') };
    S.fx = Fx(el.cv, low ? .6 : 1, kick);
    if(S.ov) S.ov.classList.add('cb-live');
    window.addEventListener('resize', onResize);
    try{ script(); }catch(e){ try{ console.warn('CodisBoxCinema', e); }catch(x){} o.state.cine = false; cleanup(); sheet.classList.remove('is-cine', 'is-opening'); return false; }
    S.wd = window.setTimeout(()=>{ if(S && S.state === 'play') handoff(true); }, S.openAt + 3200);
    S.t0 = performance.now(); S.last = S.t0; kick();
    return true;
  }
  let rzT = 0; function onResize(){ clearTimeout(rzT); rzT = setTimeout(()=>{ if(S) S.fx.size(); }, 120); }
  function kick(){ if(S && !S.raf) S.raf = requestAnimationFrame(tick); }
  function tick(nowT){
    const s = S; if(!s) return; s.raf = 0;
    const dt = Math.min(.05, Math.max(0, (nowT - s.last) / 1000)); s.last = nowT; const el = nowT - s.t0;
    while(s.ci < s.cues.length && s.cues[s.ci].t <= el){ const c = s.cues[s.ci++]; try{ c.fn(); }catch(e){ try{ console.warn('CodisBoxCinema', e); }catch(x){} if(S && S.state === 'play'){ handoff(true); } if(!S) return; } }
    const alive = s.fx.step(dt);
    if(s.state !== 'done' || alive || s.ci < s.cues.length) s.raf = requestAnimationFrame(tick);
  }
  function cancelAnims(){ if(!S) return; S.anims.forEach(a=>{ try{ a.cancel(); }catch(e){} }); S.anims.length = 0; }
  function cleanup(){
    const s = S; if(!s) return; S = null; cancelAnimationFrame(s.raf); clearTimeout(s.wd); clearTimeout(rzT); window.removeEventListener('resize', onResize);
    s.anims.forEach(a=>{ try{ a.cancel(); }catch(e){} }); s.fx.clear();
    if(s.ov) s.ov.classList.remove('cb-live');
    if(s.sheet){ s.sheet.removeAttribute('data-lv'); s.sheet.style.removeProperty('--cb-lrgb'); s.sheet.style.removeProperty('--cb-lrgb2'); }
    if(s.world.parentNode) s.world.parentNode.removeChild(s.world);
  }
  function abort(){ if(S) cleanup(); }

  /* ---------- سيناريو الفتح: دخول ← ترقّب ← فتح ← تسليم للكشف ---------- */
  function script(){
    const s = S, el = s.el, T = s.T, n = s.n, k = T.shake;
    const enterMs = 640, openAt = enterMs + T.ant, handAt = openAt + 420;
    s.openAt = openAt;
    /* دخول */
    A(el.bg, [{ opacity:0 }, { opacity:1 }], { duration:560, easing:E.out });
    A(el.floor, [{ opacity:0, transform:'scale(.55)' }, { opacity:1, transform:'scale(1)' }], { duration:720, easing:E.out });
    A(el.box, [{ opacity:0, transform:'translateY(78px) scale(.78)' }, { opacity:1, transform:'translateY(0) scale(1)' }], { duration:enterMs, easing:E.spring });
    if(T.orbit) A(el.rig, [{ transform:'rotateY(' + (-T.orbit * 2.2) + 'deg)' }, { transform:'rotateY(0deg)' }], { duration:enterMs + 260, easing:E.out });
    A(el.glow, [{ opacity:0 }, { opacity:.35 }], { duration:enterMs, easing:E.out });
    cue(enterMs - 80, ()=>{ s.fx.em('mote', s.fx.w / 2, s.fx.h * .62, 10, { ang:[-2.6, -.5], sp:[14, 46], life:[1.2, 2.2], size:[1.6, 3], rgb:T.rgb2, jx:s.fx.w * .16 }); });
    /* ترقّب: اهتزاز يتصاعد + ضوء يتسرّب من الدرزة + شرر */
    const kf = [], N = 14; for(let i = 0; i <= N; i++){ const p = i / N, amp = Math.pow(p, 1.6) * 3.2 * k, sg = i % 2 ? 1 : -1; kf.push({ offset:p, transform:'translate(' + (sg * amp * .9).toFixed(2) + 'px,' + (-Math.abs(amp) * .35).toFixed(2) + 'px) rotateZ(' + (sg * amp * .55).toFixed(2) + 'deg)' }); }
    cue(enterMs, ()=>{
      A(el.rig, kf, { duration:T.ant, easing:E.lin });
      A(el.glow, [{ opacity:.35 }, { opacity:.9 }, { opacity:.45 }, { opacity:1 }], { duration:T.ant, easing:E.io });
      A(el.mouth, [{ opacity:0 }, { opacity:.42 }], { duration:T.ant, easing:E.in });
      A(el.lid, [{ transform:'translateY(0)' }, { transform:'translateY(' + (-1.4 * T.gap) + '%)' }], { duration:T.ant, easing:E.in });
      A(el.cam, [{ transform:'scale(1)' }, { transform:'scale(' + (1 + (T.cam - 1) * .45) + ')' }], { duration:T.ant, easing:E.io });
    });
    const sparkAt = n >= 4 ? 5 : 3;
    for(let i = 1; i <= sparkAt; i++) cue(enterMs + T.ant * (i / (sparkAt + 1)), ()=>{ const m = mouthPos(); s.fx.em('spark', m.x, m.y, 4 + n * 2, { ang:[-2.9, -.25], sp:[90, 220], life:[.3, .65], size:[2, 3.4], rgb:T.rgb2, g:240, jx:m.w * .34 }); });
    /* فتح */
    cue(openAt, ()=>{
      const m = mouthPos(), lift = T.lift;
      codisSfx('open');
      A(el.lid, [{ transform:'translateY(' + (-1.4 * T.gap) + '%)' }, { transform:'translate3d(0,' + lift + '%,-24px) rotateX(' + T.rot + 'deg) rotateZ(-2.4deg)' }], { duration:560, easing:E.out });
      A(el.rig, [{ transform:'translateY(6px) scale(1.035)' }, { transform:'translateY(0) scale(1)' }], { duration:520, easing:E.out });
      A(el.mouth, [{ opacity:.5 }, { opacity:1 }], { duration:300, easing:E.out });
      A(el.beam, [{ opacity:0, transform:'scaleY(.05)' }, { opacity:1, transform:'scaleY(1)' }], { duration:520, easing:E.out });
      A(el.flash, [{ opacity:.75 }, { opacity:0 }], { duration:420, easing:E.out });
      A(el.cam, [{ transform:'scale(' + (1 + (T.cam - 1) * .45) + ')' }, { transform:'scale(' + T.cam + ') translateY(' + (-n * 1.2) + 'px)' }], { duration:620, easing:E.out });
      const rg = mk('cb-ring', 'left:' + m.x + 'px;top:' + m.y + 'px'); A(rg, [{ opacity:.9, transform:'translate(-50%,-50%) scale(.2)' }, { opacity:0, transform:'translate(-50%,-50%) scale(' + (3.4 + n * .3) + ')' }], { duration:680, easing:E.out });
      burst(m, T, n);
    });
    /* تسليم: نغيّر لون الضوء إلى لون مستوى الكشف (تلميح) ثم نبدّل الشاشة */
    cue(handAt, ()=>handoff(false));
  }
  function burst(m, T, n){
    const s = S, f = s.fx, base = T.n;
    f.em('spark', m.x, m.y, base * .8, { ang:[-2.9, -.25], sp:[160, 420], life:[.5, 1.1], size:[2, 4.2], rgb:T.rgb2, g:420, drag:.35, jx:m.w * .3 });
    if(T.parts === 'dust') f.em('dust', m.x, m.y, 12, { ang:[-3, -.15], sp:[30, 110], life:[.7, 1.3], size:[5, 11], rgb:'214,176,128', g:-30, jx:m.w * .3 });
    if(T.parts === 'shard') f.em('shard', m.x, m.y, base * .6, { ang:[-2.9, -.25], sp:[120, 340], life:[.7, 1.4], size:[2.4, 4.4], rgb:'200,236,255', g:260, jx:m.w * .3 });
    if(T.parts === 'crystal'){ f.em('shard', m.x, m.y, base * .7, { ang:[-2.9, -.25], sp:[120, 380], life:[.8, 1.5], size:[2.6, 5], rgb:'150,206,255', g:220, jx:m.w * .3 }); f.em('star', m.x, m.y, 10, { ang:[-2.9, -.25], sp:[40, 150], life:[.8, 1.5], size:[2.2, 4], rgb:'210,190,255', g:-20, jx:m.w * .35 }); }
    if(T.parts === 'ember'){ f.em('ember', m.x, m.y, base * .8, { ang:[-2.8, -.35], sp:[60, 260], life:[1, 2], size:[2, 4.4], rgb:'255,150,60', g:-70, drag:.5, jx:m.w * .34 }); f.em('star', m.x, m.y, 12, { ang:[-2.9, -.25], sp:[50, 190], life:[.8, 1.5], size:[2.4, 4.4], rgb:'255,226,150', g:-10, jx:m.w * .34 }); }
    if(T.parts === 'aura'){ f.em('ember', m.x, m.y, base * .7, { ang:[-2.8, -.35], sp:[50, 240], life:[1.2, 2.4], size:[2, 4.6], rgb:'255,214,120', g:-60, drag:.5, jx:m.w * .38 }); f.em('star', m.x, m.y, 22, { ang:[-3, -.15], sp:[40, 200], life:[1, 1.9], size:[2.4, 5], rgb:'160,238,255', g:-14, jx:m.w * .4 }); f.em('mote', m.x, m.y, 20, { ang:[-3.1, -.05], sp:[20, 90], life:[1.4, 2.6], size:[1.6, 3.2], rgb:'255,236,180', g:-26, jx:m.w * .46 }); }
  }
  function handoff(fast){
    const s = S; if(!s || s.state !== 'play') return; clearTimeout(s.wd); s.state = 'enter';
    if(fast) snapOpen(); s.cues.length = 0; s.ci = 0;
    s.world.style.setProperty('--cb-rgb2', s.RL.rgb2); s.world.style.setProperty('--cb-rgb', s.RL.rgb);
    let ok = false; try{ ok = s.o.reveal(); }catch(e){ ok = false; }
    if(!ok){ cleanup(); return; }
    try{ reveal(fast); }catch(e){ try{ console.warn('CodisBoxCinema', e); }catch(x){} finish(); }
  }
  /* تخطّي/مهلة: الغطاء مفتوح فوراً بلا حركة */
  function snapOpen(){
    const s = S, el = s.el, T = s.T; cancelAnims(); s.cues.length = 0;
    el.box.style.opacity = 1; el.bg.style.opacity = 1; el.floor.style.opacity = 1; el.mouth.style.opacity = 1; el.glow.style.opacity = 1;
    el.lid.style.transform = 'translate3d(0,' + T.lift + '%,-24px) rotateX(' + T.rot + 'deg) rotateZ(-2.4deg)'; el.beam.style.opacity = 1;
  }
  function finish(){ if(S) S.state = 'done'; }

  /* ---------- الكشف: خمس مجموعات بصرية من مستوى القيمة الفعلية (CodisRevealLevels) ---------- */
  function groupOf(lv){ return lv <= 2 ? 1 : lv <= 4 ? 2 : lv <= 6 ? 3 : lv <= 8 ? 4 : 5; }
  function reveal(fast){
    const s = S, el = s.el, lv = s.lv, RL = s.RL, g = groupOf(lv), body = document.getElementById('econ-box-body'), sheet = s.sheet;
    sheet.setAttribute('data-lv', String(lv)); sheet.style.setProperty('--cb-lrgb', RL.rgb); sheet.style.setProperty('--cb-lrgb2', RL.rgb2);
    const kids = Array.prototype.slice.call(body.children), hero = kids.find(c=>c.matches('.bx-stage, .hcd-reveal, .bx-reveal')) || kids[0] || body;
    const rest = kids.filter(c=>c !== hero), f = fast ? .22 : 1, t0 = now();
    /* الصندوق ينسحب والجائزة تتقدّم */
    A(el.box, [{ opacity:1, transform:'translateY(0) scale(1)' }, { opacity:0, transform:'translateY(46px) scale(.82)' }], { duration:520 * f, delay:120 * f, easing:E.in });
    A(el.floor, [{ opacity:1 }, { opacity:.35 }], { duration:600 * f, easing:E.io });
    A(el.cam, [{ transform:'scale(' + s.T.cam + ') translateY(' + (-s.n * 1.2) + 'px)' }, { transform:'scale(1) translateY(0)' }], { duration:900 * f, delay:120 * f, easing:E.out });
    /* ضوء الخلف: ثابت للمجموعات الدنيا، أشعة تدور مرة واحدة للأعلى */
    const rayOp = [0, .26, .4, .55, .7, .85][g];
    A(el.rays, [{ opacity:0, transform:'rotate(0deg) scale(.7)' }, { opacity:rayOp, transform:'rotate(' + (g >= 3 ? 70 : 28) + 'deg) scale(1)', offset:.35 }, { opacity:rayOp * .5, transform:'rotate(' + (g >= 3 ? 160 : 60) + 'deg) scale(1.05)' }], { duration:(3600 + g * 500) * f, easing:E.out });
    const delay = [0, 0, 80, 140, 260, 420][g] * f;   /* تأخير البطاقة: كلما علا المستوى طال «التعليق» قبل الظهور */
    heroIn(hero, g, delay, f);
    rest.forEach((c, i)=>{ A(c, [{ opacity:0, transform:'translateY(14px)' }, { opacity:1, transform:'none' }], { duration:420 * f, delay:delay + (380 + i * 70) * f, easing:E.out }); });
    codisSfx(g === 1 ? 'store.buy' : g === 2 ? 'card.cue' : g === 3 ? 'reward.unlock' : 'reward.achievement');
    if(!fast) world(g, delay, hero);
    else if(g >= 2){ const c = centerOf(hero); s.fx.em('star', c.x, c.y, 10, { sp:[60, 200], life:[.5, 1], size:[2, 4], rgb:RL.rgb2, g:20 }); }
    cue(t0 + (delay + 1500 + g * 280) * (fast ? .3 : 1), finish);
  }
  function heroIn(hero, g, delay, f){
    const kf = [
      null,
      [{ opacity:0, transform:'translateY(46px) scale(.9)' }, { opacity:1, transform:'none' }],
      [{ opacity:0, transform:'translateY(70px) scale(.8) rotateX(16deg)' }, { opacity:1, transform:'none' }],
      [{ opacity:0, transform:'translateY(90px) scale(.55)' }, { opacity:1, transform:'translateY(-6px) scale(1.04)', offset:.72 }, { opacity:1, transform:'none' }],
      [{ opacity:0, transform:'scale(1.4)' }, { opacity:1, transform:'scale(.96)', offset:.66 }, { opacity:1, transform:'none' }],
      [{ opacity:0, transform:'scale(.35)' }, { opacity:0, transform:'scale(.4)', offset:.2 }, { opacity:1, transform:'scale(1.12)', offset:.7 }, { opacity:1, transform:'none' }]
    ][g], dur = [0, 560, 640, 720, 560, 920][g] * f;
    A(hero, kf, { duration:dur, delay:delay, easing:g === 4 ? E.out : E.spring });
  }
  /* طبقات العالم لكل مجموعة (حلقات، عمود ضوء، وميض، اهتزاز كاميرا، جسيمات) — تتصاعد ولا تتكرر */
  function world(g, delay, hero){
    const s = S, RL = s.RL, c = centerOf(hero), cx = c.x, cy = Math.max(c.y, 120), f = s.fx;
    const ring = (dl, sc, du)=>{ const r = mk('cb-ring is-lv', 'left:' + cx + 'px;top:' + cy + 'px'); A(r, [{ opacity:.85, transform:'translate(-50%,-50%) scale(.15)' }, { opacity:0, transform:'translate(-50%,-50%) scale(' + sc + ')' }], { duration:du, delay:dl, easing:E.out }); };
    const pillar = (dl, op, du)=>{ const p = mk('cb-pillar', 'left:' + cx + 'px;top:' + cy + 'px'); A(p, [{ opacity:0, transform:'translate(-50%,-50%) scaleY(.1)' }, { opacity:op, transform:'translate(-50%,-50%) scaleY(1)', offset:.3 }, { opacity:0, transform:'translate(-50%,-50%) scaleY(1.05)' }], { duration:du, delay:dl, easing:E.out }); };
    const shake = (dl, amp, du)=>{ const kf = []; for(let i = 0; i <= 8; i++){ const p = i / 8, a = amp * (1 - p), sg = i % 2 ? 1 : -1; kf.push({ offset:p, transform:'translate(' + (sg * a).toFixed(2) + 'px,' + (-sg * a * .5).toFixed(2) + 'px)' }); } A(s.sheet.querySelector('#econ-box-body') || s.el.cam, kf, { duration:du, delay:dl, easing:E.lin }); };
    const part = (dl, kind, n, o)=>cue(now() + dl, ()=>f.em(kind, cx, cy, n, Object.assign({ jx:c.w * .3, jy:c.h * .25 }, o)));
    A(s.el.vig, [{ opacity:0 }, { opacity:[0, .25, .45, .6, .8, .95][g] }], { duration:700, delay:delay, easing:E.out });
    if(g === 1){ part(delay + 160, 'star', 12, { sp:[30, 130], life:[.6, 1.2], size:[2, 3.6], rgb:RL.rgb2, g:-16 }); }
    if(g >= 2){ ring(delay + 80, 3.2, 760); pillar(delay + 60, .55, 1100); part(delay + 140, 'spark', 26, { sp:[100, 320], life:[.5, 1], size:[2, 3.6], rgb:RL.rgb2, g:240 }); part(delay + 200, 'star', 14, { sp:[40, 160], life:[.8, 1.5], size:[2, 4], rgb:RL.rgb, g:-14 }); }
    if(g >= 3){ ring(delay + 200, 4.4, 900); shake(delay + 90, 3.2, 420); part(delay + 180, 'dust', 8, { sp:[30, 120], life:[.8, 1.4], size:[7, 14], rgb:RL.rgb, g:-20 }); part(delay + 240, 'shard', 22, { sp:[110, 360], life:[.8, 1.5], size:[2.4, 4.8], rgb:RL.rgb2, g:200 }); }
    if(g >= 4){ A(s.el.flash, [{ opacity:.9 }, { opacity:0 }], { duration:520, delay:delay - 40, easing:E.out }); ring(delay + 320, 5.4, 1000); pillar(delay + 160, .8, 1500); part(delay + 260, 'spark', 40, { sp:[160, 460], life:[.6, 1.3], size:[2, 4.4], rgb:RL.rgb2, g:300 }); part(delay + 340, 'star', 26, { sp:[60, 240], life:[1, 1.9], size:[2.6, 5], rgb:'255,244,200', g:-24 }); }
    if(g >= 5){
      A(s.el.flash, [{ opacity:0 }, { opacity:1, offset:.5 }, { opacity:0 }], { duration:760, delay:delay - 60, easing:E.io });
      ring(delay + 420, 6.4, 1200); ring(delay + 560, 7.6, 1400); shake(delay + 300, 5.4, 640);
      const rn = mk('cb-rune', 'left:' + cx + 'px;top:' + cy + 'px'); A(rn, [{ opacity:0, transform:'translate(-50%,-50%) rotate(0deg) scale(.5)' }, { opacity:.9, transform:'translate(-50%,-50%) rotate(110deg) scale(1)', offset:.4 }, { opacity:0, transform:'translate(-50%,-50%) rotate(260deg) scale(1.25)' }], { duration:2400, delay:delay + 260, easing:E.out });
      part(delay + 380, 'ember', 44, { sp:[60, 300], life:[1.4, 2.8], size:[2.4, 5], rgb:'255,214,120', g:-60 }); part(delay + 520, 'mote', 30, { sp:[20, 110], life:[1.6, 3], size:[1.8, 3.4], rgb:'255,240,190', g:-30 });
      cue(now() + delay + 640, ()=>codisSfx('reward.achievement'));
    }
  }
  function skip(){
    const s = S; if(!s) return;
    if(s.state === 'play'){ handoff(true); }
    else if(s.state === 'enter'){ s.anims.forEach(a=>{ try{ if(a.effect && a.effect.getTiming().iterations !== Infinity) a.finish(); }catch(e){} }); s.cues.length = 0; s.ci = 0; finish(); }
  }
  return { play:play, skip:skip, abort:abort, reset:abort, active:()=>!!S, idleHtml:idleHtml, bindIdle:bindIdle, rigHtml:rigHtml, tierOf:n=>TIER[Math.max(1, Math.min(5, n | 0))], groupOf:groupOf };
})();
