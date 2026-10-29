#!/usr/bin/env python3
"""CODIS-BULK-V3 (بعد patch_v9.py): فتح ×10 سينمائي على مسرح واحد (بديل الشبكة المصغّرة).
 • مسرح كبير بالوسط: كل صندوق يدخل ← يهتز ويترقّب ← يُفتح ← يظهر الكرت كبيراً ← يطير إلى خانته في الشريط السفلي ← الصندوق التالي.
 • الترتيب تصاعدي بالقيمة (الأقوى أخيراً). الإيقاع والشدّة من مستوى القيمة الفعلية (CodisRevealLevels → 5 مجموعات):
     1 عادي: سريع وخفيف · 2 متوسط: حلقة ونجوم · 3 نادر: لون الجائزة يتسرّب من الدرزة قبل الفتح + أشعة + اهتزاز
     4 عالي: إعتام + ترقّب طويل + وميض + عمود ضوء + اهتزاز شاشة · 5 أعلى: نبضات قلب + وميض مزدوج + دائرة رونية + جمر + دوران الكرت.
 • النقر على المسرح يسرّع الصندوق الحالي؛ «تخطّي» ينقل للنتائج فوراً. عرض فقط: لا شراء ولا سحب ولا منح (كلها تمّت في CodisBoxes.buyOpenMany).
 • كل الحركات Web Animations + Canvas جسيمات واحد + حلقة rAF واحدة؛ stop() يلغي كل شيء (إغلاق/تخطّي/إعادة فتح)."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-BULK-V3' in s: sys.exit('already patched (CODIS-BULK-V3)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

def cut_fn(name, new):
    """يستبدل دالة كاملة (من سطر 'function name(' حتى السطر الذي يبدأ بـ 'function ' أو 'let '/'var '/'const ' أو تعليق بعدها)."""
    global s
    start = '\nfunction ' + name + '('
    if s.count(start) != 1: sys.exit('fn "%s" matched %d' % (name, s.count(start)))
    i = s.index(start) + 1
    j = i + 1
    while True:
        k = s.index('\n', j)
        nxt = s[k + 1:k + 40]
        if nxt.startswith('function ') or nxt.startswith('let ') or nxt.startswith('var ') or nxt.startswith('const ') or nxt.startswith('/*'):
            break
        j = k + 1
    s = s[:i] + new.rstrip('\n') + '\n' + s[k + 1:]

# CodisBoxCinema: تصدير محرّك الجسيمات والتيسير لإعادة استعماله
rep("return { play:play, skip:skip, abort:abort, reset:abort, active:()=>!!S, idleHtml:idleHtml, bindIdle:bindIdle, rigHtml:rigHtml, tierOf:n=>TIER[Math.max(1, Math.min(5, n | 0))], groupOf:groupOf };",
    "return { play:play, skip:skip, abort:abort, reset:abort, active:()=>!!S, idleHtml:idleHtml, bindIdle:bindIdle, rigHtml:rigHtml, tierOf:n=>TIER[Math.max(1, Math.min(5, n | 0))], groupOf:groupOf, Fx:Fx, E:E };", 'cinema exports')

# 1) الجدول الزمني (مصدر واحد: المسرح + الاختبارات + المهلة الاحتياطية)
cut_fn('econBulkSchedule', r"""function econBulkSchedule(res){
  /* CODIS-BULK-V3 — مراحل كل صندوق (ms) حسب مجموعة القيمة g (1..5): دخول · ترقّب · فتح→كرت · ظهور الكرت · بقاء · طيران للشريط */
  const G = [null,
    { enter:200, ant:90,   gap:80,  cardIn:300,  hold:270,  fly:300 },
    { enter:240, ant:210,  gap:120, cardIn:380,  hold:420,  fly:320 },
    { enter:320, ant:650,  gap:230, cardIn:620,  hold:1000, fly:360 },
    { enter:400, ant:1050, gap:360, cardIn:800,  hold:1500, fly:380 },
    { enter:480, ant:1650, gap:560, cardIn:1080, hold:2300, fly:420 }];
  const ord = econBulkOrder(res), at = {}, dur = {}, items = []; let t = 560, streak = 0;
  ord.forEach((o, k)=>{
    const g = CodisBoxCinema.groupOf(o.lv), B = G[g]; streak = g === 1 ? streak + 1 : 0;
    const f = g === 1 && streak > 1 ? .76 : 1;   /* تتابع كروت عادية: الإيقاع يتسارع قليلاً حتى لا يملّ */
    const p = { i:o.i, k:k, lv:o.lv, g:g, start:t, enter:B.enter * f, ant:B.ant * f, gap:B.gap * f, cardIn:B.cardIn * f, hold:B.hold * f, fly:B.fly };
    p.open = p.start + p.enter + p.ant; p.reveal = p.open + p.gap; p.flyAt = p.reveal + p.cardIn + p.hold; p.end = p.flyAt + p.fly;
    at[o.i] = p.open; dur[o.i] = p.end - p.start; items.push(p); t = p.flyAt + p.fly * .35;
  });
  return { at:at, dur:dur, items:items, total:(items.length ? items[items.length - 1].end : t) + 420 };
}""")

cinema = r"""
/* ===== CODIS-BULK-V3 · CodisBulkCinema — مسرح فتح ×10 (عرض فقط) ===== */
const CodisBulkCinema = (function(){
  'use strict';
  let S = null;
  const E = ()=>CodisBoxCinema.E;
  function A(el, kf, opt, tag){
    if(!S || !el || !el.animate) return null;
    const a = el.animate(kf, Object.assign({ fill:'both' }, opt)); S.anims.push(a); if(tag) (S.tags[tag] = S.tags[tag] || []).push(a); return a;
  }
  function cancelTag(tag){ if(!S || !S.tags[tag]) return; S.tags[tag].forEach(a=>{ try{ a.cancel(); }catch(e){} }); S.tags[tag] = []; }
  function rel(el){ const r0 = S.root.getBoundingClientRect(), r = el.getBoundingClientRect(); return { x:r.left - r0.left, y:r.top - r0.top, w:r.width, h:r.height, cx:r.left - r0.left + r.width / 2, cy:r.top - r0.top + r.height / 2 }; }
  function stageXY(el){ const w = S.el.stage.getBoundingClientRect(), r = el.getBoundingClientRect(); return { x:r.left - w.left + r.width / 2, y:r.top - w.top + r.height / 2, w:r.width, h:r.height }; }
  function mouth(){ const r = S.el.box.getBoundingClientRect(), w = S.el.stage.getBoundingClientRect(), a = econBoxArtMeta(S.n); return { x:r.left - w.left + r.width / 2, y:r.top - w.top + r.height * ((a.seam[0] + a.seam[1]) / 2), w:r.width }; }
  function artHtml(r){ return r.pouch ? '<div class="pk-tile is-pouch"><div class="pch-art">' + econPouchSvg(r.pouch.type) + '</div></div>' : econPackTileHtml(r.item, r.rarity).replace(' role="listitem"', ''); }

  /* ---------- الهيكل ---------- */
  function html(res, plan){
    const n = Math.max(1, Math.min(5, res.tier.index | 0)), u = econBoxArtUrl(n);
    return '<div class="bkc" data-n="' + n + '">' +
      '<div class="bkc-top"><span class="bkc-count" aria-live="polite"><b>0</b> / ' + res.items.length + '</span><span class="bkc-tap">اضغط المسرح للتسريع</span></div>' +
      '<div class="bkc-stage cb-world" aria-hidden="true"><div class="cb-bg"></div><div class="cb-rays"></div><canvas class="cb-fx"></canvas>' +
        '<div class="cb-cam"><div class="cb-floor"></div><div class="cb-box">' + CodisBoxCinema.rigHtml(n) + '</div></div><div class="bkc-aura"></div><div class="cb-flash"></div><div class="cb-vig"></div></div>' +
      '<div class="bkc-banner" aria-live="polite"></div>' +
      '<div class="bkc-tray" role="list" aria-label="ترتيب الفتح">' + plan.items.map(p=>'<div class="bkc-slot" role="listitem" data-k="' + p.k + '"><img class="bkc-mini" alt="" src="' + u + '" draggable="false"><span class="bkc-no" dir="ltr">' + (p.i + 1) + '</span></div>').join('') + '</div>' +
      '<div class="bkc-layer" aria-hidden="true"></div></div>';
  }

  /* ---------- التشغيل ---------- */
  function play(root, res, plan, onDone){
    stop();
    const st = root && root.querySelector('.bkc'); if(!st || !st.animate) return false;
    const q = sel=>st.querySelector(sel), nav = navigator, low = (nav.hardwareConcurrency || 8) <= 4 || (nav.deviceMemory || 8) <= 2;
    const el = { stage:q('.bkc-stage'), bg:q('.cb-bg'), rays:q('.cb-rays'), cv:q('.cb-fx'), cam:q('.cb-cam'), floor:q('.cb-floor'), box:q('.cb-box'), rig:q('.cb-rig'), glow:q('.cb-glow'), mouth:q('.cb-mouth'), beam:q('.cb-beam'), lid:q('.cb-lid'),
      aura:q('.bkc-aura'), flash:q('.cb-flash'), vig:q('.cb-vig'), banner:q('.bkc-banner'), tray:q('.bkc-tray'), layer:q('.bkc-layer'), count:q('.bkc-count b') };
    const n = Math.max(1, Math.min(5, res.tier.index | 0)), T = CodisBoxCinema.tierOf(n);
    S = { root:st, res:res, plan:plan, onDone:onDone, el:el, n:n, T:T, low:low, anims:[], tags:{}, cues:[], ci:0, t0:0, skew:0, last:0, raf:0, cur:null, filled:{}, cards:{}, done:false };
    S.fx = CodisBoxCinema.Fx(el.cv, low ? .55 : 1, kick);
    el.stage.style.setProperty('--cb-rgb', T.rgb); el.stage.style.setProperty('--cb-rgb2', T.rgb2);
    st.addEventListener('click', onTap);
    /* افتتاح: المسرح يضيء، الشريط ينزل بالتتابع */
    A(el.bg, [{ opacity:0 }, { opacity:1 }], { duration:520, easing:E().out });
    A(el.floor, [{ opacity:0, transform:'scale(.5)' }, { opacity:1, transform:'scale(1)' }], { duration:620, easing:E().out });
    Array.prototype.forEach.call(el.tray.children, (c, i)=>A(c, [{ opacity:0, transform:'translateY(14px) scale(.8)' }, { opacity:1, transform:'none' }], { duration:360, delay:60 + i * 35, easing:E().spring }));
    plan.items.forEach(p=>schedule(p));
    cue(plan.total - 380, -1, ()=>end());
    S.t0 = performance.now(); S.last = S.t0; kick();
    /* احتياط: لو توقّف rAF (WebView مقيّد/تبويب مخفي) تتقدّم الإشارات بمؤقّت خفيف فلا يعلق الفتح */
    const me = S; S.iv = window.setInterval(()=>{ if(S !== me){ window.clearInterval(me.iv); return; } const n = performance.now(); if(n - me.last > 160){ me.last = n; runCues(elapsed(n)); } }, 120);
    return true;
  }
  function cue(t, k, fn){ S.cues.push({ t:t, k:k, fn:fn }); }
  function sortCues(){ S.cues.sort((a, b)=>a.t - b.t); }
  function elapsed(nowT){ return nowT - S.t0 + S.skew; }
  function kick(){ if(S && !S.raf) S.raf = requestAnimationFrame(tick); }
  /* تنفيذ الإشارات حتى t. false = انتهت الجلسة أثناءها */
  function runCues(t){
    const s = S; if(!s) return false; if(!s.sorted){ sortCues(); s.sorted = true; }
    while(s.ci < s.cues.length && s.cues[s.ci].t <= t){ const c = s.cues[s.ci++]; if(c.dead) continue; try{ c.fn(); }catch(e){ try{ console.warn('CodisBulkCinema', e); }catch(x){} } if(!S || S !== s) return false; }
    return true;
  }
  function tick(nowT){
    const s = S; if(!s) return; s.raf = 0;
    const dt = Math.min(.05, Math.max(0, (nowT - s.last) / 1000)); s.last = nowT;
    if(!runCues(elapsed(nowT))) return;
    const alive = s.fx.step(dt);
    if(!s.done || alive) s.raf = requestAnimationFrame(tick);
  }

  /* ---------- صندوق واحد ---------- */
  function schedule(p){
    const k = p.k;
    cue(p.start, k, ()=>enter(p));
    cue(p.start + p.enter, k, ()=>charge(p));
    if(p.g >= 2){ const n = p.g >= 4 ? 4 : 2; for(let j = 1; j <= n; j++) cue(p.start + p.enter + p.ant * j / (n + 1), k, ()=>{ const m = mouth(); S.fx.em('spark', m.x, m.y, 3 + p.g * 2, { ang:[-2.9, -.25], sp:[80, 220], life:[.3, .6], size:[2, 3.4], rgb:p.g >= 3 ? rl(p).rgb2 : S.T.rgb2, g:240, jx:m.w * .3 }); }); }
    if(p.g >= 5){ cue(p.start + p.enter + p.ant * .35, k, ()=>beat(p)); cue(p.start + p.enter + p.ant * .7, k, ()=>beat(p)); }
    cue(p.open, k, ()=>open(p));
    cue(p.reveal, k, ()=>reveal(p));
    cue(p.flyAt, k, ()=>fly(p));
    cue(p.end, k, ()=>commit(p));
  }
  const rl = p=>CodisRevealLevels.info(p.lv);
  function enter(p){
    const s = S, el = s.el; s.cur = p; cancelTag('box'); cancelTag('scene');
    if(el.count) el.count.textContent = String(p.k + 1);
    Array.prototype.forEach.call(el.tray.children, c=>c.classList.toggle('is-now', Number(c.dataset.k) === p.k));
    el.stage.style.setProperty('--cb-rgb', s.T.rgb); el.stage.style.setProperty('--cb-rgb2', s.T.rgb2);
    el.lid.style.transform = ''; el.mouth.style.opacity = ''; el.beam.style.opacity = '';
    A(el.box, [{ opacity:0, transform:'translateY(60px) scale(.8)' }, { opacity:1, transform:'translateY(0) scale(1)' }], { duration:p.enter, easing:E().spring }, 'box');
    A(el.glow, [{ opacity:0 }, { opacity:.3 }], { duration:p.enter, easing:E().out }, 'box');
    if(p.g >= 2) codisSfx('box.thud');
  }
  function charge(p){
    const s = S, el = s.el, amp = [0, 1.2, 1.9, 2.8, 3.8, 5][p.g], N = 12, kf = [];
    for(let i = 0; i <= N; i++){ const t = i / N, a = Math.pow(t, 1.5) * amp, sg = i % 2 ? 1 : -1; kf.push({ offset:t, transform:'translate(' + (sg * a).toFixed(2) + 'px,' + (-Math.abs(a) * .3).toFixed(2) + 'px) rotateZ(' + (sg * a * .55).toFixed(2) + 'deg)' }); }
    A(el.rig, kf, { duration:p.ant, easing:'linear' }, 'box');
    /* لون الجائزة يتسرّب من الدرزة للمستويات النادرة فما فوق (تلميح مثل الألعاب) */
    if(p.g >= 3){ const R = rl(p); el.stage.style.setProperty('--cb-rgb', R.rgb); el.stage.style.setProperty('--cb-rgb2', R.rgb2); codisSfx('box.charge'); }
    A(el.glow, [{ opacity:.3 }, { opacity:p.g >= 3 ? 1 : .6 }], { duration:p.ant, easing:E().in }, 'box');
    A(el.mouth, [{ opacity:0 }, { opacity:p.g >= 3 ? .6 : .3 }], { duration:p.ant, easing:E().in }, 'box');
    A(el.lid, [{ transform:'translateY(0)' }, { transform:'translateY(' + (-1.2 - p.g * .3) + '%)' }], { duration:p.ant, easing:E().in }, 'box');
    if(p.g >= 4){
      A(el.vig, [{ opacity:0 }, { opacity:p.g >= 5 ? .92 : .7 }], { duration:p.ant * .8, easing:E().io }, 'scene');
      A(el.tray, [{ opacity:1 }, { opacity:.35 }], { duration:p.ant * .6, easing:E().io }, 'scene');
      A(el.cam, [{ transform:'scale(1)' }, { transform:'scale(' + (p.g >= 5 ? 1.14 : 1.08) + ')' }], { duration:p.ant, easing:E().io }, 'scene');
    }
  }
  function beat(p){
    const el = S.el; A(el.glow, [{ opacity:.6 }, { opacity:1, offset:.3 }, { opacity:.7 }], { duration:420, easing:E().out }, 'box');
    A(el.box, [{ transform:'scale(1)' }, { transform:'scale(1.06)', offset:.3 }, { transform:'scale(1)' }], { duration:420, easing:E().out }, 'box');
    codisSfx('box.creak'); try{ codisHaptic([10]); }catch(e){}
  }
  function open(p){
    const s = S, el = s.el, m = mouth(), R = rl(p), g = p.g, lift = s.T.lift, rot = s.T.rot;
    codisSfx(g >= 3 ? 'box.release' : 'box.unlock');
    A(el.lid, [{ transform:'translateY(' + (-1.2 - g * .3) + '%)' }, { transform:'translate3d(0,' + lift + '%,-24px) rotateX(' + rot + 'deg) rotateZ(-2.4deg)' }], { duration:g >= 3 ? 540 : 360, easing:E().out }, 'box');
    A(el.mouth, [{ opacity:.5 }, { opacity:1 }], { duration:260, easing:E().out }, 'box');
    A(el.flash, [{ opacity:[0, .35, .5, .7, .9, 1][g] }, { opacity:0 }], { duration:280 + g * 60, easing:E().out }, 'scene');
    if(g >= 2){ A(el.beam, [{ opacity:0, transform:'scaleY(.05)' }, { opacity:1, transform:'scaleY(1)' }], { duration:420, easing:E().out }, 'box'); ring(m.x, m.y, 2.4 + g * .5, 560 + g * 60, false); }
    const base = (s.low ? .55 : 1) * [0, 10, 22, 38, 56, 80][g];
    s.fx.em('spark', m.x, m.y, base, { ang:[-2.9, -.25], sp:[120, 300 + g * 40], life:[.4, .9 + g * .1], size:[2, 4], rgb:g >= 3 ? R.rgb2 : s.T.rgb2, g:380, drag:.4, jx:m.w * .3 });
    if(g >= 3) s.fx.em('shard', m.x, m.y, base * .5, { ang:[-2.9, -.25], sp:[120, 340], life:[.7, 1.4], size:[2.4, 4.6], rgb:R.rgb, g:240, jx:m.w * .3 });
    if(g >= 4){ shake(5 + g, 420); try{ codisHaptic(g >= 5 ? [18, 40, 28, 40, 40] : [14, 40, 24]); }catch(e){} }
    else if(g === 3){ try{ codisHaptic([12, 30]); }catch(e){} }
  }
  function ring(x, y, sc, du, lv){
    const r = document.createElement('div'); r.className = 'cb-ring' + (lv ? ' is-lv' : ''); r.style.left = x + 'px'; r.style.top = y + 'px'; S.el.stage.insertBefore(r, S.el.flash);
    const a = A(r, [{ opacity:.9, transform:'translate(-50%,-50%) scale(.2)' }, { opacity:0, transform:'translate(-50%,-50%) scale(' + sc + ')' }], { duration:du, easing:E().out }, 'scene'); if(a) a.onfinish = ()=>r.remove();
  }
  function shake(amp, du){ const kf = []; for(let i = 0; i <= 8; i++){ const t = i / 8, a = amp * (1 - t), sg = i % 2 ? 1 : -1; kf.push({ offset:t, transform:'translate(' + (sg * a).toFixed(2) + 'px,' + (-sg * a * .5).toFixed(2) + 'px)' }); } A(S.el.stage, kf, { duration:du, easing:'linear' }, 'scene'); }
  function reveal(p){
    const s = S, el = s.el, r = s.res.items[p.i], R = rl(p), g = p.g, inf = econBulkInfo(r);
    el.stage.style.setProperty('--cb-rgb', R.rgb); el.stage.style.setProperty('--cb-rgb2', R.rgb2);
    /* الصندوق ينسحب، الكرت يتقدّم في طبقة فوق المسرح (لا يُقصّ عند الطيران للشريط) */
    A(el.box, [{ opacity:1, transform:'translateY(0) scale(1)' }, { opacity:0, transform:'translateY(40px) scale(.84)' }], { duration:Math.min(420, p.cardIn), easing:E().in }, 'box');
    const sr = rel(el.stage), w = Math.min(196, sr.w * .48), card = document.createElement('div');
    card.className = 'bkc-card'; card.setAttribute('data-g', String(g)); card.style.cssText = 'left:' + (sr.cx - w / 2) + 'px;top:' + (sr.y + sr.h * .47 - w * .625) + 'px;width:' + w + 'px;--k:' + R.rgb;
    card.innerHTML = '<div class="bkc-card-in">' + artHtml(r) + '</div>'; el.layer.appendChild(card); s.cards[p.k] = card;
    try{ codisFitRewardCard(card); }catch(e){}
    const KF = [null,
      [{ opacity:0, transform:'translateY(30px) scale(.86)' }, { opacity:1, transform:'none' }],
      [{ opacity:0, transform:'translateY(50px) scale(.7) rotateX(18deg)' }, { opacity:1, transform:'translateY(-4px) scale(1.04)', offset:.7 }, { opacity:1, transform:'none' }],
      [{ opacity:0, transform:'translateY(70px) scale(.5)' }, { opacity:1, transform:'translateY(-8px) scale(1.08)', offset:.62 }, { opacity:1, transform:'none' }],
      [{ opacity:0, transform:'scale(1.55)', filter:'brightness(2.6)' }, { opacity:1, transform:'scale(.95)', filter:'brightness(1.35)', offset:.6 }, { opacity:1, transform:'none', filter:'brightness(1)' }],
      [{ opacity:0, transform:'perspective(700px) rotateY(540deg) scale(.3)' }, { opacity:1, transform:'perspective(700px) rotateY(40deg) scale(1.16)', offset:.66 }, { opacity:1, transform:'perspective(700px) rotateY(0deg) scale(1)' }]][g];
    A(card.firstChild, KF, { duration:p.cardIn, easing:g === 1 ? E().out : g === 4 ? E().out : E().spring }, 'card' + p.k);
    if(g >= 3) A(card.firstChild, [{ transform:'translateY(0)' }, { transform:'translateY(-5px)' }, { transform:'translateY(0)' }], { duration:1600, delay:p.cardIn, iterations:Infinity, easing:E().io, composite:'add' }, 'card' + p.k);
    /* هالة + أشعة + حلقات + عمود ضوء + رونية حسب المجموعة */
    A(el.aura, [{ opacity:0, transform:'scale(.6)' }, { opacity:[0, .25, .45, .7, .85, 1][g], transform:'scale(1)' }], { duration:600, easing:E().out }, 'scene');
    if(g >= 2) A(el.rays, [{ opacity:0, transform:'rotate(0deg) scale(.7)' }, { opacity:[0, 0, .28, .45, .62, .8][g], transform:'rotate(' + (g * 18) + 'deg) scale(1)', offset:.4 }, { opacity:[0, 0, .16, .3, .45, .6][g], transform:'rotate(' + (g * 40) + 'deg) scale(1.05)' }], { duration:p.cardIn + p.hold, easing:E().out }, 'scene');
    const c = stageXY(card);
    if(g >= 2) ring(c.x, c.y, 3 + g * .4, 700 + g * 80, true);
    if(g >= 3){ ring(c.x, c.y, 4.6 + g * .4, 900 + g * 80, true); s.fx.em('star', c.x, c.y, (s.low ? 8 : 16) + g * 3, { sp:[40, 180], life:[.8, 1.6], size:[2, 4.2], rgb:R.rgb2, g:-14, jx:c.w * .3, jy:c.h * .25 }); }
    if(g >= 4){
      const pl = document.createElement('div'); pl.className = 'cb-pillar'; pl.style.left = c.x + 'px'; pl.style.top = c.y + 'px'; el.stage.insertBefore(pl, el.flash);
      const a = A(pl, [{ opacity:0, transform:'translate(-50%,-50%) scaleY(.1)' }, { opacity:.85, transform:'translate(-50%,-50%) scaleY(1)', offset:.3 }, { opacity:0, transform:'translate(-50%,-50%) scaleY(1.1)' }], { duration:1500, easing:E().out }, 'scene'); if(a) a.onfinish = ()=>pl.remove();
      s.fx.em('ember', c.x, c.y, s.low ? 16 : 34, { ang:[-2.8, -.35], sp:[60, 260], life:[1, 2.2], size:[2, 4.4], rgb:R.rgb, g:-60, drag:.5, jx:c.w * .3 });
    }
    if(g >= 5){
      A(el.flash, [{ opacity:0 }, { opacity:1, offset:.45 }, { opacity:0 }], { duration:800, easing:E().io }, 'scene'); shake(8, 640); ring(c.x, c.y, 7.4, 1500, true);
      const rn = document.createElement('div'); rn.className = 'cb-rune'; rn.style.left = c.x + 'px'; rn.style.top = c.y + 'px'; el.stage.insertBefore(rn, el.flash);
      const a = A(rn, [{ opacity:0, transform:'translate(-50%,-50%) rotate(0deg) scale(.5)' }, { opacity:.9, transform:'translate(-50%,-50%) rotate(120deg) scale(1)', offset:.4 }, { opacity:0, transform:'translate(-50%,-50%) rotate(240deg) scale(1.2)' }], { duration:2200, easing:E().out }, 'scene'); if(a) a.onfinish = ()=>rn.remove();
      s.fx.em('mote', c.x, c.y, s.low ? 14 : 30, { sp:[20, 110], life:[1.6, 3], size:[1.8, 3.4], rgb:'255,240,190', g:-30, jx:c.w * .5 });
    }
    codisSfx(g === 1 ? 'box.reveal' : g === 2 ? 'card.cue' : g === 3 ? 'reward.unlock' : 'reward.achievement');
    /* لافتة الاسم + الفئة */
    el.banner.style.setProperty('--k', R.rgb); el.banner.setAttribute('data-g', String(g));
    el.banner.innerHTML = '<b dir="auto">' + escapeHtml(inf.name) + '</b><span>' + inf.chip + '</span>';
    A(el.banner, [{ opacity:0, transform:'translateY(10px)' }, { opacity:1, transform:'none' }], { duration:320, delay:Math.min(260, p.cardIn * .5), easing:E().out }, 'scene');
  }
  function fly(p){
    const s = S, card = s.cards[p.k], slot = s.el.tray.querySelector('.bkc-slot[data-k="' + p.k + '"]'); if(!card || !slot) return;
    A(s.el.banner, [{ opacity:1 }, { opacity:0 }], { duration:220, easing:E().in }, 'scene');
    A(s.el.aura, [{ opacity:.6 }, { opacity:0 }], { duration:p.fly, easing:E().in }, 'scene');
    if(p.g >= 4){ A(s.el.vig, [{ opacity:.8 }, { opacity:0 }], { duration:p.fly, easing:E().out }, 'scene'); A(s.el.tray, [{ opacity:.35 }, { opacity:1 }], { duration:p.fly, easing:E().out }, 'scene'); A(s.el.cam, [{ transform:'scale(1.1)' }, { transform:'scale(1)' }], { duration:p.fly, easing:E().out }, 'scene'); }
    const a = rel(card), b = rel(slot), sc = b.w / a.w;
    (s.tags['card' + p.k] || []).forEach(x=>{ try{ x.finish(); }catch(e){} });
    A(card, [{ transform:'translate(0,0) scale(1)', opacity:1 }, { transform:'translate(' + (b.cx - a.cx) + 'px,' + (b.cy - a.cy) + 'px) scale(' + sc + ')', opacity:.95 }], { duration:p.fly, easing:E().io }, 'fly' + p.k);
  }
  function commit(p){
    const s = S; if(!s || s.filled[p.k]) return; s.filled[p.k] = true;
    const card = s.cards[p.k]; if(card){ cancelTagOf(card); card.remove(); delete s.cards[p.k]; }
    const slot = s.el.tray.querySelector('.bkc-slot[data-k="' + p.k + '"]'), r = s.res.items[p.i]; if(!slot) return;
    slot.classList.remove('is-now'); slot.classList.add('is-filled'); slot.setAttribute('data-g', String(p.g)); slot.style.setProperty('--k', rl(p).rgb);
    slot.innerHTML = '<div class="bkc-thumb">' + artHtml(r) + '</div><span class="bkc-no" dir="ltr">' + (p.i + 1) + '</span>';
    try{ codisFitRewardCard(slot); }catch(e){}
    A(slot.firstChild, [{ transform:'scale(1.18)' }, { transform:'scale(1)' }], { duration:300, easing:E().spring });
  }
  function cancelTagOf(card){ Object.keys(S.tags).forEach(k=>{ if(/^(card|fly)/.test(k)) S.tags[k] = S.tags[k].filter(a=>{ const t = a.effect && a.effect.target; if(t && (t === card || card.contains(t))){ try{ a.cancel(); }catch(e){} return false; } return true; }); }); }
  /* النقر على المسرح: إنهاء الصندوق الحالي فوراً والانتقال للتالي */
  function onTap(ev){
    const s = S; if(!s || s.done || !s.cur) return;
    if(ev.target.closest && ev.target.closest('button')) return;
    const p = s.cur, next = s.plan.items[p.k + 1], t = elapsed(performance.now());
    s.cues.forEach(c=>{ if(c.k === p.k && c.t > t) c.dead = true; });
    cancelTag('box'); cancelTag('scene'); s.fx.clear();
    commit(p);
    const target = next ? next.start : s.plan.total - 380;
    if(target > t + 60) s.skew += target - t - 60;
    kick();
  }
  function end(){ const s = S; if(!s || s.done) return; s.done = true; const cb = s.onDone; s.plan.items.forEach(p=>commit(p)); if(cb) cb(); }
  function stop(){
    const s = S; if(!s) return; S = null;
    cancelAnimationFrame(s.raf); window.clearInterval(s.iv); s.anims.forEach(a=>{ try{ a.cancel(); }catch(e){} }); s.anims.length = 0;
    try{ s.fx.clear(); }catch(e){}
    try{ s.root.removeEventListener('click', onTap); }catch(e){}
  }
  /* للاختبار فقط: تقديم الزمن الافتراضي وتنفيذ الإشارات حتى t (لا يغيّر أي بيانات) */
  function _seek(t){ if(!S) return; S.skew = t - (performance.now() - S.t0); if(S.raf) cancelAnimationFrame(S.raf); S.raf = 0; tick(performance.now()); }
  return { html:html, play:play, stop:stop, active:()=>!!S, _state:()=>S, _seek:_seek };
})();
"""
rep("function econBulkModal(){ return document.getElementById('econ-bulk-modal'); }", cinema.strip('\n') + "\nfunction econBulkModal(){ return document.getElementById('econ-bulk-modal'); }", 'insert cinema')

# 2) الرسم: أثناء الفتح المسرح بدل الشبكة
rep("  CodisArt.set(body, ()=>'<div class=\"bk-head\">' + econBulkHeadHtml(s) + '</div><div class=\"bk-grid\" role=\"list\" aria-label=\"المكافآت المستلمة\">'",
    "  if(run && !econCalm()){ CodisArt.set(body, ()=>'<div class=\"bk-head\">' + econBulkHeadHtml(s) + '</div>' + CodisBulkCinema.html(s.res, econBulkSch) + '<div class=\"bk-actions\">' + econBulkActionsHtml(s) + '</div>'); return; }\n  CodisArt.set(body, ()=>'<div class=\"bk-head\">' + econBulkHeadHtml(s) + '</div><div class=\"bk-grid\" role=\"list\" aria-label=\"المكافآت المستلمة\">'", 'paint stage')

# 3) البدء
cut_fn('econBulkShow', r"""function econBulkShow(res){
  const m = econBulkModal(); if(!m || !res || !res.ok || !res.items || !res.items.length) return false;
  if(econBulkState) econBulkClose(true);
  const calm = econCalm(), token = ++econBulkToken; econBulkZoomClose(); CodisBulkCinema.stop();
  const s = econBulkState = { res:res, phase:calm ? 'done' : 'opening', token:token, timer:0, cues:[], at:Date.now(), best:econBulkBest(res) }; econBulkSch = econBulkSchedule(res);   /* تقليل الحركة: النتائج فوراً بلا حركة ولا زر تخطّي */
  econBulkPaint(); codisSfx('open');
  m.setAttribute('aria-hidden', 'false'); CodisMotion.modalIn(m);
  const f = m.querySelector('.bk-skip, .bk-done'); if(f){ try{ f.focus({ preventScroll:true }); }catch(x){} }
  if(calm){ econBulkCue(s); return true; }
  const ok = CodisBulkCinema.play(document.getElementById('econ-bulk-body'), res, econBulkSch, ()=>{ if(econBulkState && econBulkState.token === token) econBulkFinish(token); });
  if(!ok){ econBulkFinish(token); return true; }
  s.timer = window.setTimeout(()=>econBulkFinish(token), econBulkSch.total + 4000);   /* مهلة أمان فقط: لا تُترك النافذة عالقة لو تعطّل الرسم */
  return true;
}""")

# 4) الإنهاء: إيقاف المسرح ثم شاشة النتائج كاملة
cut_fn('econBulkFinish', r"""function econBulkFinish(token){
  const s = econBulkState, m = econBulkModal(); if(!s || !m || (token !== undefined && token !== s.token) || s.phase === 'done') return;
  econBulkClearTimers(s); CodisBulkCinema.stop();
  s.phase = 'done';
  econBulkPaint();
  const sheet = m.querySelector('.bk-modal'); if(sheet){ sheet.classList.add('is-arrive'); window.setTimeout(()=>{ if(sheet) sheet.classList.remove('is-arrive'); }, 1400); }
  const f = m.querySelector('.bk-done'); if(f){ try{ f.focus({ preventScroll:true }); }catch(x){} }
  econBulkCue(s);
}""")
rep("function econBulkClose(silent){\n  const m = econBulkModal(); if(!m) return; econBulkZoomClose();", "function econBulkClose(silent){\n  const m = econBulkModal(); if(!m) return; econBulkZoomClose(); CodisBulkCinema.stop();", 'close stop')

css = r"""
/* CODIS-BULK-V3 — مسرح فتح ×10 */
.bk-modal.is-run .bk-prog{ display:none; }
.bkc{ position:relative; display:grid; gap:10px; margin:2px 0 6px; user-select:none; -webkit-user-select:none; }
.bkc-top{ display:flex; align-items:center; justify-content:space-between; gap:10px; font-size:12.5px; color:var(--text-2); }
.bkc-count{ font-variant-numeric:tabular-nums; font-weight:700; } .bkc-count b{ font-size:17px; color:var(--text); }
.bkc-tap{ font-size:11.5px; color:var(--text-3, var(--text-2)); }
.bkc-stage.cb-world{ position:relative; inset:auto; height:min(40vh, 340px); min-height:260px; border-radius:20px; overflow:hidden; pointer-events:auto; cursor:pointer; --cb-w:min(220px, 58%);
  background:radial-gradient(80% 60% at 50% 40%, rgba(var(--cb-rgb),.10), transparent 70%), #07090d; border:1px solid rgb(var(--hi-rgb) / .08); }
.bkc-stage .cb-box{ top:46%; }
.bkc-stage .cb-floor{ top:calc(46% + var(--cb-w) * .4); }
.bkc-aura{ position:absolute; left:50%; top:47%; width:120%; aspect-ratio:1; margin:-60% 0 0 -60%; opacity:0; pointer-events:none; border-radius:50%; mix-blend-mode:screen;
  background:radial-gradient(closest-side, rgba(var(--cb-rgb),.55), rgba(var(--cb-rgb2),.18) 55%, transparent 72%); }
.bkc-layer{ position:absolute; inset:0; pointer-events:none; z-index:6; overflow:visible; }
.bkc-card{ position:absolute; z-index:6; pointer-events:none; }
.bkc-card-in{ width:100%; transform-origin:50% 60%; will-change:transform, opacity; }
.bkc-card[data-g="3"] .bkc-card-in{ filter:drop-shadow(0 0 14px rgba(var(--k),.45)); } .bkc-card[data-g="4"] .bkc-card-in, .bkc-card[data-g="5"] .bkc-card-in{ filter:drop-shadow(0 0 22px rgba(var(--k),.7)); }
.bkc-card .pk-tile{ width:100%; }
.bkc-banner{ min-height:46px; display:grid; justify-items:center; align-content:center; gap:4px; text-align:center; opacity:0; }
.bkc-banner b{ font-size:16px; font-weight:800; line-height:1.3; max-width:100%; overflow-wrap:anywhere; color:var(--text); }
.bkc-banner[data-g="4"] b, .bkc-banner[data-g="5"] b{ color:color-mix(in srgb, rgb(var(--k)) 55%, #fff); text-shadow:0 0 14px rgba(var(--k),.55); font-size:18px; }
.bkc-tray{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:6px; direction:rtl; }
.bkc-slot{ position:relative; aspect-ratio:4 / 5; border-radius:10px; display:grid; place-items:center; background:rgb(var(--hi-rgb) / .04); border:1px solid rgb(var(--hi-rgb) / .08); overflow:hidden; }
.bkc-mini{ width:70%; opacity:.42; filter:saturate(.6); }
.bkc-slot.is-now{ border-color:rgba(var(--sec-rgb),.8); box-shadow:0 0 0 1px rgba(var(--sec-rgb),.5), 0 0 14px rgba(var(--sec-rgb),.35); }
.bkc-slot.is-now .bkc-mini{ opacity:.9; filter:none; }
.bkc-slot.is-filled{ border-color:rgba(var(--k),.55); background:rgba(var(--k),.08); }
.bkc-slot.is-filled[data-g="4"], .bkc-slot.is-filled[data-g="5"]{ box-shadow:0 0 12px rgba(var(--k),.5); }
.bkc-thumb{ width:100%; height:100%; display:grid; place-items:center; padding:2px; }
.bkc-thumb .pk-tile{ width:100%; }
.bkc-no{ position:absolute; top:2px; inset-inline-start:3px; z-index:2; min-width:14px; height:14px; padding:0 3px; display:grid; place-items:center; font-size:9px; font-weight:800; border-radius:7px; color:var(--text-2); background:rgb(var(--lo-rgb) / .7); }
.bk-modal.is-done.is-arrive .bk-cell{ animation:bkResIn .42s cubic-bezier(.16,1,.3,1) both; animation-delay:calc(var(--i) * 40ms); }
@keyframes bkResIn{ from{ opacity:0; transform:translateY(12px) scale(.94); } to{ opacity:1; transform:none; } }
@media (prefers-reduced-motion:reduce){ .bk-modal.is-done.is-arrive .bk-cell{ animation:none; } }
"""
rep("</style>", css + "</style>", 'css')
s = s.replace('<!-- CODIS-BULK-V2 -->', '<!-- CODIS-BULK-V2 -->\n<!-- CODIS-BULK-V3 -->', 1)
if 'CODIS-BULK-V3 -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v10 OK')
