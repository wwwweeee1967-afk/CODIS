#!/usr/bin/env python3
"""CODIS-AUDIO-V2 (بعد patch_v10.py): إعادة بناء الصوت.
 المحرك: نواقل لكل قناة (ui/xp/reward/discipline) مع خفض تلقائي (ducking) للواجهة وقت الأحداث المهمة، توزيع ستيريو لكل صوت،
   أدوات توليد جديدة: رنين مادي (خشب/زجاج/معدن/فضة/ذهب/حجر/بلاستيك/برونز/كريستال)، FM، حبيبات قلم/ورق، هواء؛ تنويع ضد التكرار (vars) ؛
   سياق الحدث name@ctx (نفس الاسم العام يأخذ هوية مختلفة حسب مكانه)؛ تسجيل آخر الأحداث (trace) وتصيير offline للاختبار.
 الكتالوج: هويات جديدة للواجهة والتنقّل والمهام/القلم والعادات والعملات (ذهب ≠ فضة) والمتجر والصناديق (مادة حسب المستوى) و×10 والانضباط.
 الربط: كل استدعاء عام (open/close/invalid/confirm/success/press/coins.take/store.buy/task.delete) يأخذ ctx من الدالة التي يقع فيها (جدول صريح قابل للتتبّع)،
   وأحداث بلا صوت سابقاً: قلم المهام، نافذة المنجزة، لوحة النسبة، طيّ تفاصيل العادة، مسرح ×10 (طيران/خانة/ختام/تخطّي/تسريع)، تسليم الصندوق المفرد.
 هويات الكروت (CS/CX/CL) والعقوبات (PN) المتزامنة مع أنيميشنها تبقى، مع طبقة توقيع لكل عائلة كرت (يومي ورق/خشب · أسبوعي زجاج · شهري معدن)."""
import sys, re
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-AUDIO-V2' in s: sys.exit('already patched (CODIS-AUDIO-V2)')

def rep(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('anchor "%s" matched %d times (want %d)' % (label, n, count))
    s = s.replace(old, new)

# ================= 1) المحرك =================
# نواقل القنوات + ستيريو + سياق + تنويع + تتبّع + تصيير offline
rep("""  let ctx = null, master = null, reverbIn = null, noiseBuf = null;""",
"""  let ctx = null, master = null, reverbIn = null, noiseBuf = null, bus = {};   /* CODIS-AUDIO-V2: bus = ناقل لكل قناة */
  const lastVar = Object.create(null), trace = [];""", 'engine vars')
rep("""      master.connect(comp); comp.connect(ctx.destination);""",
"""      master.connect(comp); comp.connect(ctx.destination);
      makeBuses();""", 'buses init')
rep("""  /* ---------- فك القفل بعد أول تفاعل حقيقي (autoplay policy) ---------- */""",
"""  /* CODIS-AUDIO-V2: ناقل لكل قناة (مستواها) → master. الخفض يمسّ الناقل لا الأصوات */
  function makeBuses(){ bus = {}; ['ui','xp','reward','discipline'].forEach(k=>{ const g = ctx.createGain(); g.gain.value = curve(cfg().channels[k] == null ? 1 : cfg().channels[k]); g.connect(master); bus[k] = g; }); }
  function duck(chs, depth, hold){
    if(!ctx) return; const t = ctx.currentTime;
    chs.forEach(k=>{ const b = bus[k]; if(!b) return; const v = curve(cfg().channels[k] == null ? 1 : cfg().channels[k]);
      try{ b.gain.cancelScheduledValues(t); b.gain.setTargetAtTime(v * depth, t, .025); b.gain.setTargetAtTime(v, t + hold, .18); }catch(e){} });
  }
  /* ---------- فك القفل بعد أول تفاعل حقيقي (autoplay policy) ---------- */""", 'duck')
rep("""  function newVoice(def, t0, level, opts){
    const out = ctx.createGain();
    out.gain.value = level;
    out.connect(master);
    const v = { t0, out, nodes:[out], pending:0, endsAt:t0, dead:false, srcs:[], group:(opts && opts.group) || null };""",
"""  function newVoice(def, t0, level, opts){
    const out = ctx.createGain();
    out.gain.value = level;
    let dest = (bus[def.ch]) || master, pan = null;
    if(ctx.createStereoPanner){ try{ pan = ctx.createStereoPanner(); pan.pan.value = clamp((opts && opts.pan != null) ? opts.pan : (def.pan || 0), -1, 1); out.connect(pan); pan.connect(dest); }catch(e){ pan = null; } }
    if(!pan) out.connect(dest);
    const v = { t0, out, nodes:pan ? [out, pan] : [out], pending:0, endsAt:t0, dead:false, srcs:[], group:(opts && opts.group) || null, panNode:pan };
    v.pan = x=>{ if(pan) try{ pan.pan.setValueAtTime(clamp(x, -1, 1), t0); }catch(e){} };
    v.panTo = (x, at)=>{ if(pan) try{ pan.pan.linearRampToValueAtTime(clamp(x, -1, 1), t0 + at); }catch(e){} };""", 'voice bus+pan')
rep("""    v.tone = sp=>tone(v, sp);
    v.noise = sp=>noiseHit(v, sp);""",
"""    v.tone = sp=>tone(v, sp);
    v.noise = sp=>noiseHit(v, sp);
    v.fm = sp=>fmTone(v, sp);
    v.strike = (mat, f, peak, t, o)=>strike(v, mat, f, peak, t, o);
    v.grains = sp=>grains(v, sp);
    v.air = sp=>noiseHit(v, Object.assign({ type:'bandpass', q:.8, a:(sp.dur || .2) * .45 }, sp));""", 'voice api')
rep("""    src.buffer = noiseBuf;                      // نفس الـ buffer دائماً — لا تخصيص جديد""",
"""    src.buffer = noiseBuf; src.loop = true;     // نفس الـ buffer دائماً — لا تخصيص جديد (loop: أصوات الهواء الطويلة لا تنقطع)""", 'noise loop')

prims = r"""
  /* تلاشٍ قصير (40ms) بدل القطع — بلا نقرة. يخرج الصوت من العدّ فوراً */
  function fadeOut(v){
    if(!v || v.dead || v.fading || !ctx) return; v.fading = true; voices.delete(v);
    const t = ctx.currentTime; try{ v.out.gain.cancelScheduledValues(t); v.out.gain.setTargetAtTime(0, t, .012); }catch(e){}
    v.srcs.forEach(src=>{ try{ src.stop(t + .06); }catch(e){} });
    setTimeout(()=>killVoice(v), 140);
  }
  function steal(p){ let pick = null; voices.forEach(x=>{ if(x.fading) return; if(!pick || (x.p || 1) < (pick.p || 1) || ((x.p || 1) === (pick.p || 1) && x.t0 < pick.t0)) pick = x; }); if(!pick || (pick.p || 1) > p) return false; fadeOut(pick); return true; }
  /* ===== CODIS-AUDIO-V2 · أدوات توليد ===== */
  /* رنين مادي: مجموع أنماط جيبية بنسب غير توافقية وتلاشٍ لكل نمط + ضربة إثارة قصيرة. المادة تحدد النسب والتلاشي واللمعة */
  const MAT = {
    wood:   { r:[1, 2.57, 4.21, 6.64],      d:[.16, .07, .045, .03],     g:[1, .5, .3, .14],      ex:3200 },
    hollow: { r:[1, 1.71, 2.95],            d:[.24, .12, .06],           g:[1, .45, .22],         ex:1300 },
    glass:  { r:[1, 2.76, 5.4, 8.93],       d:[.85, .45, .28, .16],      g:[1, .42, .22, .1],     ex:7000 },
    metal:  { r:[1, 1.47, 2.09, 2.56, 3.16], d:[1.1, .8, .6, .45, .35],  g:[1, .6, .42, .3, .18], ex:5200 },
    silver: { r:[1, 2.32, 3.87, 5.6],       d:[.42, .3, .2, .14],        g:[1, .55, .35, .2],     ex:9000 },
    gold:   { r:[1, 1.6, 2.31, 3.02],       d:[.7, .5, .36, .24],        g:[1, .6, .4, .22],      ex:4200 },
    stone:  { r:[1, 1.83, 2.9],             d:[.1, .055, .035],          g:[1, .4, .2],           ex:1800 },
    poly:   { r:[1, 1.93, 3.1],             d:[.05, .03, .02],           g:[1, .32, .14],         ex:6000 },
    bronze: { r:[1, 2, 2.42, 3, 4.07],      d:[1.6, 1.2, 1, .8, .6],     g:[1, .5, .4, .3, .15],  ex:3000 },
    crystal:{ r:[1, 2.93, 4.98, 7.1],       d:[1.1, .6, .4, .25],        g:[1, .5, .3, .18],      ex:10000 },
    iron:   { r:[1, 2.21, 3.36, 4.9],       d:[.5, .3, .2, .12],         g:[1, .5, .3, .15],      ex:2400 }
  };
  function strike(v, mat, f, peak, t, o){
    o = o || {}; const M = MAT[mat] || MAT.wood, T = t || 0, ds = o.decay || 1, br = o.bright == null ? 1 : o.bright;
    M.r.forEach((r, k)=>{ const ff = f * r; if(ff > 15000) return; v.tone({ t:T, f:ff, dur:Math.max(.035, M.d[k] * ds), a:.0015, peak:peak * M.g[k] * (k ? br : 1) }); });
    if(o.ex !== 0) v.noise({ t:T, dur:o.exDur || .01, peak:peak * (o.ex == null ? .55 : o.ex), type:'bandpass', f:o.exF || M.ex, q:1.3, a:.0006 });
  }
  /* FM: ناقل + معدِّل بمؤشر يتلاشى (أجراس/أوتار معدنية/نبضات) */
  function fmTone(v, sp){
    const t = v.t0 + (sp.t || 0), dur = Math.max(.04, sp.dur);
    const car = ctx.createOscillator(), mod = ctx.createOscillator(), mg = ctx.createGain(), g = ctx.createGain();
    car.frequency.setValueAtTime(sp.f, t); if(sp.f2) car.frequency.exponentialRampToValueAtTime(sp.f2, t + dur);
    mod.frequency.setValueAtTime(sp.f * (sp.ratio || 2), t);
    mg.gain.setValueAtTime(sp.f * (sp.index == null ? 2 : sp.index), t); mg.gain.exponentialRampToValueAtTime(Math.max(.5, sp.f * (sp.index2 == null ? .05 : sp.index2)), t + dur);
    g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(.0002, sp.peak), t + Math.min(sp.a || .003, dur * .5)); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
    mod.connect(mg); mg.connect(car.frequency); car.connect(g);
    let last = g; if(sp.lp){ const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = sp.lp; g.connect(f); last = f; v.nodes.push(f); }
    last.connect(v.out); v.nodes.push(mg, g);
    [car, mod].forEach(o=>{ o.start(t); o.stop(t + dur + .03); v.srcs.push(o); v.pending++; o.onended = ()=>{ try{ o.disconnect(); }catch(e){} srcDone(v); }; });
    v.endsAt = Math.max(v.endsAt, t + dur + .03);
  }
  /* حبيبات: قلم على ورق، شرار، عملات تتساقط — n حبة بتوقيت/طبقة/شدة عشوائية محدودة */
  function grains(v, sp){
    const n = Math.max(1, Math.round(sp.n || ((sp.dur || .2) * (sp.rate || 40)))), dur = sp.dur || n / (sp.rate || 40);
    for(let k = 0; k < n; k++){
      const p = n > 1 ? k / (n - 1) : 0, env = sp.shape === 'swell' ? Math.sin(p * Math.PI) : sp.shape === 'fade' ? 1 - p * .8 : 1;
      v.noise({ t:Math.max(0, (sp.t || 0) + p * dur + (Math.random() - .5) * (dur / n) * .6), dur:sp.gd || .018, peak:Math.max(.0004, (sp.peak || .02) * env * (.6 + Math.random() * .4)), type:sp.type || 'bandpass', f:(sp.f || 3000) * (.85 + Math.random() * .3), q:sp.q || .9, a:.0008 });
    }
  }
"""
rep("""  /* ---------- التشغيل ---------- */
  function resumeAndRetry(name, opts){""", prims + """
  /* ---------- التشغيل ---------- */
  function resumeAndRetry(name, opts){""", 'prims')

# play(): سياق + تنويع + خفض + تتبّع + نواقل
rep("""      opts = opts || {};
      const def = SOUNDS[name];
      if(!def || !supported || failed) return false;""",
"""      opts = opts || {};
      const key = (opts.ctx && SOUNDS[name + '@' + opts.ctx]) ? name + '@' + opts.ctx : name, def = SOUNDS[key];   /* CODIS-AUDIO-V2: هوية حسب السياق */
      if(!def || !supported || failed) return false;""", 'play ctx')
rep("""      const last = lastPlayed[name];
      if(def.cd && last !== undefined && t - last < def.cd) return false;     // cooldown لكل صوت""",
"""      const last = lastPlayed[key];
      if(def.cd && last !== undefined && t - last < def.cd) return false;     // cooldown لكل صوت""", 'play cd key')
rep("""      const v = newVoice(def, ctx.currentTime + 0.006 + (opts.delay || 0), curve(chVol) * (opts.gain == null ? 1 : opts.gain), opts);
      try{ def.fn(v, opts); }catch(e){ killVoice(v); throw e; }
      if(v.pending === 0) killVoice(v);
      lastPlayed[name] = t;""",
"""      if(voices.size >= MAX_VOICES){ if(def.p < 3) return false; if(!steal(def.p)) return false; }   /* CODIS-AUDIO-V2: سرقة الأقدم الأقل أهمية بتلاشٍ قصير */
      { const same = []; voices.forEach(x=>{ if(x.key === key && !x.fading) same.push(x); }); if(same.length >= (def.max || 4)) fadeOut(same[0]); }
      if(def.vars > 1){ const pv = lastVar[key]; let k = Math.floor(Math.random() * def.vars); if(k === pv) k = (k + 1) % def.vars; lastVar[key] = k; opts.vr = k; } else opts.vr = 0;   /* تنويع بلا تكرار متتالٍ */
      opts.j = def.jit ? 1 + (Math.random() * 2 - 1) * def.jit : 1;
      if(!bus[def.ch]) makeBuses();
      const v = newVoice(def, ctx.currentTime + 0.006 + (opts.delay || 0), (opts.gain == null ? 1 : opts.gain), opts); v.key = key; v.p = def.p;
      try{ def.fn(v, opts); }catch(e){ killVoice(v); throw e; }
      if(v.pending === 0) killVoice(v);
      if(def.duck) duck(def.duck === true ? ['ui', 'xp'] : def.duck, .42, Math.min(1.2, (v.endsAt - ctx.currentTime) * .6 + .15));
      lastPlayed[key] = t;
      trace.push({ name:name, key:key, ctx:opts.ctx || null, at:Math.round(t) }); if(trace.length > 60) trace.shift();""", 'play voice')
rep("""    const g = s.enabled ? curve(s.master) : 0;                      // Mute فوري حتى للأصوات الجارية
    try{ master.gain.setTargetAtTime(g, ctx.currentTime, 0.02); }catch(e){ try{ master.gain.value = g; }catch(e2){} }""",
"""    const g = s.enabled ? curve(s.master) : 0;                      // Mute فوري حتى للأصوات الجارية
    try{ master.gain.setTargetAtTime(g, ctx.currentTime, 0.02); }catch(e){ try{ master.gain.value = g; }catch(e2){} }
    Object.keys(bus).forEach(k=>{ const v = curve(s.channels[k] == null ? 1 : s.channels[k]); try{ bus[k].gain.setTargetAtTime(v, ctx.currentTime, .02); }catch(e){} });""", 'applySettings buses')


rep("""      for(let i = holds.length - 1; i >= 0; i--){                              // الأقل أهمية يتنازل للأهم
        if(holds[i].until <= t) holds.splice(i, 1);
        else if(holds[i].p > def.p) return false;
      }""", """      for(let i = holds.length - 1; i >= 0; i--){                              // الأقل أهمية يتنازل للأهم
        if(holds[i].until <= t) holds.splice(i, 1);
        else if(holds[i].p > def.p && !opts.seq) return false;              /* CODIS-AUDIO-V2: seq = طبقة من تسلسل الفعل نفسه (قلم المهمة…) */
      }""", 'seq holds')

# تصيير offline + تتبّع + قائمة الأحداث (للاختبار والتشخيص)
rep("""  const api = {
    play, preview, xpBegin, beginClick, endClick, applySettings, unlockNow, stopGroup, hasCue, measureCue,""",
"""  /* تصيير حدث داخل OfflineAudioContext بنفس الوصفات (اختبار: صمت/تشبّع/تمايز). يبدّل السياق مؤقتاً أثناء البناء المتزامن فقط */
  function render(name, opts, secs){
    opts = Object.assign({}, opts || {});
    const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext; if(!OAC) return Promise.reject(new Error('no offline'));
    const key = (opts.ctx && SOUNDS[name + '@' + opts.ctx]) ? name + '@' + opts.ctx : name, def = SOUNDS[key]; if(!def) return Promise.reject(new Error('unknown ' + name));
    const off = new OAC(2, Math.round(44100 * (secs || 2.5)), 44100), keep = { ctx, master, reverbIn, noiseBuf, bus };
    try{
      ctx = off; master = off.createGain(); master.connect(off.destination); reverbIn = null; noiseBuf = makeNoiseBuffer(); bus = {};
      ['ui','xp','reward','discipline'].forEach(k=>{ const g = off.createGain(); g.connect(master); bus[k] = g; });
      if(opts.vr == null) opts.vr = 0; if(opts.j == null) opts.j = 1;
      const v = newVoice(def, .01, opts.gain == null ? 1 : opts.gain, opts); def.fn(v, opts); voices.delete(v);
    } finally { ctx = keep.ctx; master = keep.master; reverbIn = keep.reverbIn; noiseBuf = keep.noiseBuf; bus = keep.bus; }
    return off.startRendering();
  }
  const api = {
    play, preview, xpBegin, beginClick, endClick, applySettings, unlockNow, stopGroup, hasCue, measureCue,
    render, events:()=>Object.keys(SOUNDS), trace:()=>trace.slice(), def:k=>SOUNDS[k] ? { ch:SOUNDS[k].ch, p:SOUNDS[k].p, cd:SOUNDS[k].cd || 0, vars:SOUNDS[k].vars || 1 } : null,""", 'api')

# ================= 2) الكتالوج =================
catalog = r"""
  /* ===================== CODIS-AUDIO-V2 · الكتالوج =====================
     اللغة الصوتية: داكنة، ملموسة، مادية. كل نظام له مادة: الواجهة زجاج/بوليمر · المهام قلم وورق وخشب ماريمبا · العادات خشب مجوّف وجلد ·
     الذهب معدن دافئ ثقيل · الفضة معدن لامع قصير · الصناديق مادة كل مستوى (خشب/فضة/كريستال/ذهب/برونز) · الانضباط حجر وحديد ومطرقة.
     التسمية: اسم@سياق — السياق يُمرَّر من موضع الاستدعاء (ctx) فلا يتشارك حدثان غير مرتبطين الصوت نفسه. vars = بدائل بلا تكرار متتالٍ. */
  const R = { D3:146.83, A3:220, B3:246.94, D4:293.66, E4:329.63, Fs4:369.99, G4:392, A4:440, B4:493.88, D5:587.33, E5:659.25, Fs5:739.99, A5:880, B5:987.77, D6:1174.66, E6:1318.51, A6:1760 };
  const ROOM = { planning:R.D4, tasks:R.E4, learn:R.Fs4, habits:R.B3, settings:R.A3 };
  const V2 = {
    /* ---- واجهة: لمسات بوليمر/زجاج، صغيرة ومختلفة حسب المكان ---- */
    'press':          { ch:'ui', p:1, cd:60, vars:3, jit:.02, fn(v,o){ const f = [1650, 1820, 1540][o.vr] * o.j; v.strike('poly', f, .045, 0, { ex:.5 }); v.tone({ f:210 * o.j, f2:150, dur:.04, a:.002, peak:.035, lp:900 }); } },
    'press@tab':      { ch:'ui', p:1, cd:80, vars:2, jit:.015, fn(v,o){ v.strike('glass', [R.A5, R.Fs5][o.vr] * o.j, .022, 0, { decay:.25, bright:.5, ex:.3 }); v.air({ dur:.07, f:1800, f2:3000, peak:.012 }); } },
    'press@step':     { ch:'ui', p:1, cd:40, vars:2, jit:.01, fn(v,o){ v.strike('poly', (o.vr ? 2300 : 2050) * o.j, .04, 0, { ex:.7 }); } },
    'press@select':   { ch:'ui', p:1, cd:50, fn(v){ v.strike('glass', R.E6, .02, 0, { decay:.2, bright:.4 }); v.strike('poly', 1900, .03); } },
    'press@box':      { ch:'reward', p:2, cd:120, fn(v){ v.strike('wood', 180, .07, 0, { decay:1.2 }); v.strike('metal', 820, .018, .01, { decay:.4 }); } },
    'select':         { ch:'ui', p:1, cd:50, vars:2, jit:.01, fn(v,o){ v.strike('glass', (o.vr ? R.B5 : R.A5) * o.j, .024, 0, { decay:.22 }); } },
    'nav':            { ch:'ui', p:1, cd:160, fn(v,o){ const f = ROOM[o.ctx] || R.D4; v.air({ dur:.22, f:500, f2:1700, peak:.03, q:.7 }); v.tone({ t:.02, f:f, f2:f * 1.5, dur:.2, a:.05, peak:.03, lp:1400, partials:[[1,1,1],[2,.2,.6]] }); v.panTo(.2, .2); } },
    'toggle.on':      { ch:'ui', p:2, cd:80, hold:120, fn(v){ v.strike('poly', 1400, .05, 0, { ex:.8 }); v.strike('glass', R.A5, .02, .025, { decay:.3 }); } },
    'toggle.off':     { ch:'ui', p:2, cd:80, hold:120, fn(v){ v.strike('poly', 1100, .05, 0, { ex:.8 }); v.tone({ t:.02, f:R.D5, f2:R.A4, dur:.08, a:.003, peak:.018, lp:1800 }); } },
    'expand':         { ch:'ui', p:1, cd:90, fn(v){ v.air({ dur:.16, f:700, f2:2400, peak:.026 }); v.strike('wood', 520, .02, .05, { decay:.5 }); } },
    'collapse':       { ch:'ui', p:1, cd:90, fn(v){ v.air({ dur:.13, f:2200, f2:650, peak:.022 }); v.strike('wood', 440, .018, .07, { decay:.5 }); } },
    /* ---- فتح/إغلاق: كل مكان مادته ---- */
    'open':           { ch:'ui', p:2, cd:120, hold:120, fn(v){ v.air({ dur:.18, f:600, f2:1900, peak:.03 }); v.tone({ t:.03, f:R.D4, f2:R.A4, dur:.16, a:.03, peak:.03, lp:1800 }); } },
    'close':          { ch:'ui', p:2, cd:120, hold:120, fn(v){ v.air({ dur:.14, f:1800, f2:550, peak:.026 }); v.tone({ t:.02, f:R.A4, f2:R.D4, dur:.12, a:.01, peak:.026, lp:1400 }); } },
    'open@store':     { ch:'ui', p:2, cd:150, hold:150, fn(v){ v.air({ dur:.28, f:300, f2:1100, peak:.035, q:.6 }); v.strike('hollow', 160, .06, .05, { decay:1.4 }); v.strike('gold', R.A5, .014, .16, { decay:.5, bright:.5 }); } },
    'close@store':    { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.air({ dur:.2, f:1100, f2:300, peak:.03, q:.6 }); v.strike('hollow', 140, .05, .12, { decay:1.1 }); } },
    'open@box':       { ch:'reward', p:2, cd:150, hold:150, fn(v){ v.strike('iron', 620, .03, 0, { decay:.6 }); v.air({ t:.04, dur:.22, f:900, f2:3200, peak:.022 }); v.strike('wood', 170, .05, .02, { decay:1.1 }); } },
    'close@box':      { ch:'reward', p:2, cd:150, hold:120, fn(v){ v.strike('wood', 150, .06, 0, { decay:1.2 }); v.strike('iron', 540, .02, .03, { decay:.4 }); } },
    'open@archive':   { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.grains({ dur:.14, rate:70, peak:.02, f:2400, type:'bandpass', shape:'swell' }); v.strike('hollow', 220, .035, .09, { decay:.8 }); } },
    'close@archive':  { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.strike('hollow', 200, .04, 0, { decay:.9 }); v.grains({ t:.01, dur:.08, rate:70, peak:.014, f:2000, shape:'fade' }); } },
    'open@report':    { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.air({ dur:.2, f:3500, f2:1400, peak:.03, q:1.3 }); v.grains({ t:.06, dur:.12, rate:60, peak:.012, f:4000, shape:'fade' }); } },
    'close@report':   { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.air({ dur:.16, f:1300, f2:3600, peak:.026, q:1.3 }); } },
    'open@notif':     { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.strike('crystal', R.B5, .02, 0, { decay:.5 }); v.strike('crystal', R.E6, .016, .07, { decay:.5 }); v.air({ dur:.2, f:2500, f2:5000, peak:.012 }); } },
    'close@notif':    { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.strike('crystal', R.E6, .015, 0, { decay:.35 }); v.strike('crystal', R.B5, .014, .06, { decay:.35 }); } },
    'open@dialog':    { ch:'ui', p:2, cd:150, hold:150, fn(v){ v.strike('glass', R.D5, .03, 0, { decay:.5 }); v.strike('glass', R.A5, .022, .05, { decay:.6 }); } },
    'open@card':      { ch:'reward', p:2, cd:150, hold:120, fn(v){ v.air({ dur:.16, f:1800, f2:5200, peak:.03, q:1.2 }); v.strike('glass', R.E6, .012, .08, { decay:.4 }); } },
    'close@card':     { ch:'reward', p:2, cd:150, hold:120, fn(v){ v.air({ dur:.12, f:4800, f2:1600, peak:.024, q:1.2 }); } },
    'open@pouch':     { ch:'reward', p:2, cd:150, hold:120, fn(v){ v.grains({ dur:.16, rate:55, peak:.018, f:1100, q:.7, shape:'swell' }); v.strike('silver', 2600, .012, .1, { decay:.4 }); } },
    'open@dismantle': { ch:'reward', p:2, cd:150, hold:120, fn(v){ v.strike('crystal', R.A5, .02, 0, { decay:.6 }); v.air({ dur:.2, f:4000, f2:1500, peak:.018 }); } },
    'open@holiday':   { ch:'reward', p:2, cd:150, hold:120, fn(v){ v.strike('wood', R.D5, .03, 0); v.strike('wood', R.Fs5, .026, .06); v.strike('glass', R.A5, .015, .12, { decay:.6 }); } },
    'close@holiday':  { ch:'reward', p:2, cd:150, hold:120, fn(v){ v.strike('wood', R.Fs5, .025, 0); v.strike('wood', R.D5, .022, .06); } },
    'open@outcome':   { ch:'reward', p:2, cd:150, hold:150, fn(v){ v.strike('gold', R.D5, .022, 0, { decay:.6 }); v.air({ dur:.22, f:700, f2:2000, peak:.02 }); } },
    'open@settings':  { ch:'ui', p:1, cd:120, fn(v){ v.air({ dur:.14, f:900, f2:2200, peak:.02 }); v.strike('poly', 1500, .03, .03); } },
    'close@settings': { ch:'ui', p:1, cd:120, fn(v){ v.air({ dur:.12, f:2000, f2:800, peak:.018 }); } },
    'close@lock':     { ch:'ui', p:2, cd:150, fn(v){ v.strike('iron', 760, .03, 0, { decay:.4 }); } },
    'open@sheet':     { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.air({ dur:.22, f:400, f2:1600, peak:.03, q:.7 }); v.grains({ t:.1, dur:.08, n:4, peak:.008, f:3600, shape:'fade' }); } },
    'close@sheet':    { ch:'ui', p:2, cd:150, hold:120, fn(v){ v.air({ dur:.17, f:1500, f2:420, peak:.026, q:.7 }); } },
    'open@partial':   { ch:'ui', p:2, cd:120, fn(v){ v.strike('wood', R.Fs5, .022, 0, { decay:.6 }); v.air({ dur:.12, f:1200, f2:2600, peak:.014 }); } },
    'open@editor':    { ch:'ui', p:1, cd:120, fn(v){ v.grains({ dur:.06, n:3, peak:.012, f:3800 }); v.strike('poly', 1700, .03, .02); } },
    'close@editor':   { ch:'ui', p:1, cd:120, fn(v){ v.strike('poly', 1400, .03); } },
    'open@select':    { ch:'ui', p:1, cd:120, fn(v){ v.strike('glass', R.A5, .02, 0, { decay:.3 }); v.strike('glass', R.D6, .016, .05, { decay:.3 }); } },
    'close@select':   { ch:'ui', p:1, cd:120, fn(v){ v.strike('glass', R.D6, .016, 0, { decay:.25 }); v.strike('glass', R.A5, .014, .05, { decay:.25 }); } },
    'confirm@dialog':   { ch:'ui', p:2, cd:150, hold:200, fn(v){ v.strike('glass', R.E5, .03, 0, { decay:.35 }); v.strike('poly', 1500, .035, .005); v.strike('glass', R.B5, .024, .06, { decay:.5 }); } },
    'close@dialog':   { ch:'ui', p:2, cd:120, fn(v){ v.strike('glass', R.A5, .02, 0, { decay:.3 }); v.tone({ t:.03, f:R.D5, f2:R.A4, dur:.1, a:.004, peak:.012, lp:1600 }); } },
    /* ---- رفض/خطأ: سبب الرفض يسمع (مال/قفل/إدخال/غير متاح/حدّ/دخول) ---- */
    'invalid':             { ch:'ui', p:2, cd:220, hold:180, fn(v){ v.strike('hollow', 196, .06, 0, { decay:.6 }); v.strike('hollow', 165, .05, .08, { decay:.6 }); } },
    'invalid@funds':       { ch:'ui', p:2, cd:260, hold:200, fn(v){ v.strike('gold', 330, .03, 0, { decay:.18, bright:.3 }); v.strike('stone', 140, .06, .02); v.strike('gold', 247, .022, .11, { decay:.14, bright:.25 }); v.pan(-.1); } },
    'invalid@locked':      { ch:'ui', p:2, cd:260, hold:200, fn(v){ v.strike('iron', 520, .03, 0, { decay:.25 }); v.strike('iron', 470, .028, .06, { decay:.22 }); v.strike('stone', 120, .04, .07); } },
    'invalid@input':       { ch:'ui', p:2, cd:220, hold:180, fn(v){ v.strike('poly', 520, .05, 0); v.strike('poly', 440, .045, .07); } },
    'invalid@unavailable': { ch:'ui', p:2, cd:240, hold:180, fn(v){ v.strike('hollow', 180, .06, 0, { decay:.9 }); v.air({ t:.02, dur:.14, f:900, f2:400, peak:.012 }); } },
    'invalid@limit':       { ch:'ui', p:2, cd:200, hold:150, fn(v){ v.strike('poly', 900, .04, 0); v.strike('poly', 900, .03, .05); } },
    'invalid@auth':        { ch:'ui', p:3, cd:300, hold:250, fn(v){ v.strike('iron', 300, .045, 0, { decay:.4 }); v.strike('stone', 110, .07, .01); v.strike('iron', 280, .04, .12, { decay:.35 }); } },
    /* ---- تأكيد/نجاح بحسب الفعل ---- */
    'confirm':          { ch:'ui', p:2, cd:150, hold:200, fn(v){ v.strike('glass', R.E5, .028, 0, { decay:.4 }); } },
    'confirm@task':     { ch:'ui', p:2, cd:120, hold:150, vars:2, fn(v,o){ v.grains({ dur:.05, n:3, peak:.014, f:3600 }); v.strike('wood', o.vr ? R.A5 : R.E5, .03, .03); } },
    'confirm@switch':   { ch:'ui', p:2, cd:100, hold:120, fn(v){ v.strike('poly', 1600, .045, 0, { ex:.8 }); v.strike('poly', 1250, .03, .03); } },
    'confirm@lock':     { ch:'ui', p:2, cd:200, hold:200, fn(v){ v.strike('iron', 760, .035, 0, { decay:.5 }); v.strike('glass', R.A5, .016, .06, { decay:.5 }); } },
    'confirm@habit':    { ch:'ui', p:2, cd:150, hold:150, fn(v){ v.strike('hollow', 280, .05, 0, { decay:1.2 }); v.strike('wood', R.B4, .025, .05); } },
    'confirm@restore':  { ch:'ui', p:2, cd:150, hold:200, fn(v){ v.air({ dur:.2, f:2600, f2:700, peak:.022 }); v.strike('wood', R.D5, .028, .14); v.strike('wood', R.A5, .022, .2); } },
    'confirm@use':      { ch:'reward', p:3, cd:200, hold:250, fn(v){ v.strike('gold', R.A5, .022, 0, { decay:.6 }); v.air({ t:.02, dur:.2, f:1500, f2:4000, peak:.016 }); } },
    'confirm@pouch':    { ch:'reward', p:3, cd:200, hold:250, fn(v){ v.grains({ dur:.32, rate:30, peak:.02, f:5200, gd:.02, shape:'fade' }); [0, 1, 2, 3].forEach(k=>v.strike('silver', 2800 + k * 230, .012, .03 + k * .06, { decay:.45 })); } },
    'confirm@dismantle':{ ch:'reward', p:3, cd:250, hold:300, duck:true, fn(v){ v.strike('crystal', R.A5, .03, 0, { decay:.8 }); v.grains({ t:.05, dur:.32, rate:45, peak:.022, f:6500, gd:.012, shape:'fade' }); [0, 1, 2].forEach(k=>v.strike('silver', 2400 + k * 410, .014, .2 + k * .07, { decay:.5 })); } },
    'success':          { ch:'ui', p:2, cd:200, hold:250, fn(v){ v.strike('glass', R.A4, .028, 0, { decay:.5 }); v.strike('glass', R.E5, .03, .075, { decay:.6 }); } },
    'success@lock':     { ch:'ui', p:2, cd:250, hold:250, fn(v){ v.strike('iron', 880, .035, 0, { decay:.6 }); v.strike('iron', 660, .03, .07, { decay:.5 }); v.strike('glass', R.D6, .02, .14, { decay:.7 }); } },
    'success@plan':     { ch:'ui', p:2, cd:250, hold:250, fn(v){ v.grains({ dur:.18, rate:60, peak:.016, f:2600, shape:'swell' }); v.strike('wood', R.D5, .032, .14); v.strike('wood', R.A5, .028, .21); v.strike('glass', R.D6, .014, .27, { decay:.8 }); } },
    'success@settings': { ch:'ui', p:2, cd:200, hold:200, fn(v){ v.strike('glass', R.Fs5, .022, 0, { decay:.4 }); } },
    'success@holiday':  { ch:'reward', p:3, cd:250, hold:250, fn(v){ v.strike('wood', R.D5, .03, 0); v.strike('wood', R.Fs5, .03, .07); v.strike('bronze', R.A4, .018, .14, { decay:.6 }); } },
    /* ---- المهام: قلم، ورق، ماريمبا خشب ---- */
    'task.done':      { ch:'ui', p:3, cd:60, hold:160, vars:3, jit:.01, fn(v,o){ v.grains({ dur:.07, rate:90, peak:.02, f:4200, gd:.012 }); v.strike('wood', R.A5 * [1, 1.0595, .9439][o.vr] * o.j, .045, .045); v.strike('wood', R.D5 * o.j, .02, .06, { decay:.6 }); } },
    'task.half':      { ch:'ui', p:3, cd:60, hold:160, vars:2, fn(v,o){ v.grains({ dur:.05, rate:90, peak:.016, f:3800, gd:.012 }); v.strike('wood', R.Fs5 * (o.vr ? 1.0595 : 1), .04, .04, { decay:.45 }); } },
    'task.none':      { ch:'ui', p:3, cd:60, hold:160, vars:2, fn(v,o){ v.grains({ dur:.09, rate:80, peak:.02, f:2800, gd:.014 }); v.strike('hollow', o.vr ? 196 : 185, .05, .05, { decay:.7 }); } },
    'task.undo':      { ch:'ui', p:3, cd:60, hold:160, fn(v){ v.grains({ dur:.16, rate:55, peak:.016, f:1300, q:.6, shape:'swell' }); v.tone({ t:.1, f:R.A4, f2:R.E5, dur:.12, a:.01, peak:.014, lp:2200 }); } },
    'task.restore':   { ch:'ui', p:3, cd:150, hold:200, fn(v){ v.air({ dur:.2, f:2600, f2:700, peak:.022 }); v.strike('wood', R.D5, .03, .14); v.strike('wood', R.A5, .024, .2); } },
    'task.delete':    { ch:'ui', p:3, cd:80, hold:160, fn(v){ v.grains({ dur:.16, rate:110, peak:.024, f:2200, q:.6, shape:'fade' }); v.strike('hollow', 150, .04, .1, { decay:.6 }); } },
    'task.delete@habit':{ ch:'ui', p:3, cd:80, hold:160, fn(v){ v.air({ dur:.2, f:1600, f2:500, peak:.022 }); v.strike('hollow', 170, .05, .12, { decay:1 }); } },
    'task.delete@card': { ch:'reward', p:3, cd:80, hold:160, fn(v){ v.grains({ dur:.2, rate:90, peak:.022, f:3200, shape:'fade' }); v.strike('glass', R.E5, .012, .06, { decay:.3 }); } },
    'task.delete@archive':{ ch:'ui', p:3, cd:80, hold:160, fn(v){ v.grains({ dur:.24, rate:120, peak:.026, f:1900, q:.5, shape:'fade' }); v.strike('stone', 120, .05, .16); } },
    'task.delete@plan': { ch:'ui', p:3, cd:80, hold:160, fn(v){ v.grains({ dur:.22, rate:100, peak:.024, f:2400, q:.6, shape:'fade' }); v.strike('hollow', 160, .045, .14, { decay:.7 }); } },
    'pen.stroke':     { ch:'ui', p:1, cd:0, fn(v,o){ const d = o.dur || .3, x = o.kind === 'x'; v.grains({ dur:d, rate:x ? 70 : 55, peak:x ? .014 : .012, f:x ? 2600 : 3400, gd:.016, shape:'swell' }); v.pan(o.pan || 0); if(!x) v.panTo(.25, d); } },
    'pen.scribble':   { ch:'ui', p:1, cd:0, fn(v,o){ const d = o.dur || .5; v.grains({ dur:d, rate:95, peak:.009, f:3000, gd:.012, shape:'swell' }); v.pan(-.15); v.panTo(.15, d); } },
    'pen.fill':       { ch:'ui', p:1, cd:0, fn(v,o){ const d = o.dur || .6; v.grains({ dur:d, rate:65, peak:.011, f:1900, q:.6, gd:.022, shape:'swell' }); v.pan(.2); v.panTo(-.2 + .4 * (1 - (o.pct || 50) / 100), d); } },
    'task.leave':     { ch:'ui', p:1, cd:80, fn(v){ v.air({ dur:.24, f:1500, f2:400, peak:.012, q:.7 }); v.pan(0); v.panTo(-.3, .24); } },
    /* ---- العادات ---- */
    'task.done@habit':{ ch:'ui', p:3, cd:80, hold:160, vars:2, fn(v,o){ v.strike('hollow', o.vr ? 262 : 247, .06, 0, { decay:1.4 }); v.strike('wood', o.vr ? R.Fs5 : R.E5, .03, .04, { decay:.8 }); } },
    'task.undo@habit':{ ch:'ui', p:3, cd:80, hold:160, fn(v){ v.strike('hollow', 220, .045, 0, { decay:1 }); v.grains({ t:.04, dur:.12, rate:50, peak:.012, f:1200, shape:'fade' }); } },
    /* ---- العملات: الذهب دافئ ثقيل، الفضة لامعة قصيرة ---- */
    'coins.take':        { ch:'reward', p:3, cd:250, hold:250, fn(v){ [0, 1, 2].forEach(k=>v.strike('gold', 1180 + k * 170, .02, k * .06, { decay:.5 })); } },
    'coins.take@sell':   { ch:'reward', p:3, cd:250, hold:250, duck:true, fn(v){ v.strike('stone', 160, .03, 0); for(let k = 0; k < 6; k++) v.strike('gold', 1050 + Math.random() * 520, .016 + (k === 5 ? .006 : 0), .04 + k * .045 + Math.random() * .015, { decay:.55 }); } },
    'coins.take@silver': { ch:'reward', p:3, cd:250, hold:250, fn(v){ for(let k = 0; k < 5; k++) v.strike('silver', 2500 + Math.random() * 900, .014, k * .05 + Math.random() * .02, { decay:.5 }); } },
    'coins.take@silverpour':{ ch:'reward', p:3, cd:250, hold:250, fn(v){ v.grains({ dur:.3, rate:40, peak:.016, f:6000, gd:.015, shape:'fade' }); for(let k = 0; k < 7; k++) v.strike('silver', 2400 + Math.random() * 1200, .012, k * .045, { decay:.4 }); } },
    /* ---- الشراء: نوع البضاعة يسمع ---- */
    'store.buy':         { ch:'reward', p:3, cd:250, hold:250, fn(v){ v.strike('gold', 1250, .022, 0, { decay:.5 }); v.strike('glass', R.B5, .022, .08, { decay:.6 }); } },
    'store.buy@card':    { ch:'reward', p:3, cd:250, hold:250, fn(v){ v.strike('gold', 1250, .02, 0, { decay:.4 }); v.air({ t:.05, dur:.16, f:2000, f2:6000, peak:.02, q:1.2 }); v.strike('glass', R.E6, .016, .16, { decay:.6 }); } },
    'store.buy@box':     { ch:'reward', p:3, cd:250, hold:250, fn(v){ v.strike('gold', 1100, .02, 0, { decay:.4 }); v.strike('wood', 120, .07, .08, { decay:1.4 }); v.strike('iron', 700, .018, .1, { decay:.4 }); } },
    'store.buy@bulk':    { ch:'reward', p:3, cd:250, hold:250, fn(v){ for(let k = 0; k < 4; k++) v.strike('wood', 110 + k * 6, .05, k * .07, { decay:1 }); v.strike('gold', 1250, .02, .3, { decay:.6 }); } },
    'store.buy@cosmetic':{ ch:'reward', p:3, cd:250, hold:250, fn(v){ v.strike('gold', 1250, .018, 0, { decay:.4 }); [0, 1, 2].forEach(k=>v.strike('crystal', [R.A5, R.D6, R.Fs5 * 2][k], .014, .08 + k * .06, { decay:.7 })); } },
    'store.buy@holiday': { ch:'reward', p:3, cd:250, hold:250, fn(v){ v.strike('gold', 1250, .02, 0, { decay:.4 }); v.strike('wood', R.D5, .03, .09); v.strike('wood', R.A5, .026, .15); } },
    /* ---- صناديق: مادة كل مستوى (n = 1 برونزي خشب … 5 خرافي برونز/كريستال) ---- */
    'box.thud':     { ch:'reward', p:3, cd:0, fn(v,o){ const g = o.g == null ? 1 : o.g, M = ['wood','wood','silver','crystal','gold','bronze'][o.n || 1]; v.strike('wood', 72, .13 * g, 0, { decay:1.8, ex:.4 }); v.strike(M === 'wood' ? 'hollow' : M, M === 'wood' ? 140 : 420, .03 * g, .01, { decay:.5 }); } },
    'box.creak':    { ch:'reward', p:3, cd:0, fn(v,o){ const g = o.g == null ? 1 : o.g, b = o.f || 150; v.grains({ dur:.3, rate:26, peak:.02 * g, f:b * 3, q:6, gd:.03, shape:'swell' }); v.strike('hollow', b, .03 * g, .02, { decay:1 }); } },
    'box.latch':    { ch:'reward', p:3, cd:0, fn(v,o){ const g = o.g == null ? 1 : o.g; v.strike('iron', 1300, .04 * g, 0, { decay:.35, ex:.9 }); v.strike('stone', 220, .03 * g, .006); } },
    'box.unlock':   { ch:'reward', p:3, cd:0, fn(v,o){ const g = o.g == null ? 1 : o.g, M = ['iron','wood','silver','crystal','gold','bronze'][o.n || 1]; v.strike('iron', 1500, .035 * g, 0, { decay:.3 }); v.strike(M, M === 'wood' ? 420 : 880, .03 * g, .04, { decay:.8 }); v.air({ t:.05, dur:.2, f:900, f2:3000, peak:.02 * g }); } },
    'box.charge':   { ch:'reward', p:3, cd:0, fn(v,o){ const lv = o.lv || 1, d = o.dur || 1.2, base = 52 + lv * 9;
        v.tone({ f:base, f2:base * 1.9, dur:d, a:d * .7, peak:.04 + lv * .004, lp:260 + lv * 90, lp2:900 + lv * 380, partials:[[1,1,1],[1.5,.3,.9]] });
        v.air({ dur:d, f:400, f2:2400 + lv * 400, peak:.012 + lv * .003, a:d * .8, q:1.4 });
        if(lv >= 3) v.fm({ t:d * .3, f:R.A5, ratio:1.5, index:.8, index2:3, dur:d * .7, a:d * .6, peak:.008 + lv * .0015 });
        if(lv >= 5) v.tone({ t:d * .1, f:base * 2.02, f2:base * 4, dur:d * .9, a:d * .75, peak:.018, lp:1200, lp2:2600, det:6 }); } },
    'box.release':  { ch:'reward', p:4, cd:0, duck:true, fn(v,o){ const lv = o.lv || 1, g = .7 + lv * .12, M = ['wood','wood','silver','crystal','gold','bronze'][o.n || 1];
        v.noise({ dur:.16, peak:.07 * g, type:'lowpass', f:1400, f2:300, a:.002 }); v.strike('wood', 90, .1 * g, 0, { decay:1.6, ex:.3 });
        v.strike(M === 'wood' ? 'iron' : M, M === 'wood' ? 700 : 620 + lv * 40, .03, .01, { decay:1 + lv * .1 });
        if(lv >= 3) v.air({ t:.02, dur:.3, f:900, f2:5200, peak:.03 + lv * .004 });
        if(lv >= 4) v.tone({ f:46, f2:34, dur:.9, a:.01, peak:.09, lp:160 }); } },
    'box.reveal':   { ch:'reward', p:4, cd:0, wet:.16, fn(v,o){ const lv = o.lv || 1, S5 = [R.E5, R.A5, R.D6, R.E6];
        v.strike('glass', R.E5, .04, 0, { decay:.6 + lv * .1 });
        if(lv >= 2) v.strike('glass', R.A5, .036, .08, { decay:.7 });
        if(lv >= 3) [0, 1, 2].forEach(i=>v.strike('crystal', S5[i] * 1.5, .02, .16 + i * .07, { decay:.9 }));
        if(lv >= 4){ v.fm({ t:.04, f:R.D4, ratio:2, index:1.2, index2:.2, dur:1.4, a:.1, peak:.04 }); v.air({ t:.05, dur:.4, f:3000, f2:8000, peak:.02 }); }
        if(lv >= 5){ v.strike('bronze', 98, .07, 0, { decay:1.2 }); [0, 1, 2, 3].forEach(i=>v.strike('crystal', S5[i], .024, .2 + i * .11, { decay:1.4 })); } } },
    /* ---- مسرح ×10 ---- */
    'bulk.fly':     { ch:'reward', p:2, cd:0, fn(v,o){ const g = o.g || 1; v.air({ dur:.3, f:2400 + g * 300, f2:700, peak:.012 + g * .003, q:.9 }); v.pan(0); v.panTo(.35, .3); } },
    'bulk.slot':    { ch:'reward', p:2, cd:0, vars:3, jit:.02, fn(v,o){ const g = o.g || 1, M = g >= 4 ? 'gold' : g >= 3 ? 'crystal' : 'glass'; v.strike(M, [R.D6, R.E6, R.B5][o.vr] * o.j, .016 + g * .003, 0, { decay:.4 + g * .08 }); v.strike('wood', 300, .02, 0); } },
    'bulk.finale':  { ch:'reward', p:4, cd:600, wet:.18, duck:true, fn(v,o){ const g = o.g || 1; [R.D5, R.A5, R.D6].forEach((f, k)=>v.strike(g >= 4 ? 'gold' : 'glass', f, .03, k * .07, { decay:1 + g * .2 })); if(g >= 3) v.air({ t:.1, dur:.5, f:2000, f2:7000, peak:.02 }); if(g >= 4) v.strike('bronze', 147, .05, .05, { decay:1.4 }); } },
    'bulk.skip':    { ch:'reward', p:2, cd:200, fn(v){ v.air({ dur:.22, f:4000, f2:900, peak:.028, q:.8 }); v.grains({ dur:.18, rate:60, peak:.008, f:5000, shape:'fade' }); } },
    'bulk.advance': { ch:'reward', p:1, cd:90, fn(v){ v.air({ dur:.12, f:3000, f2:1200, peak:.016 }); } },
    'bulk.reveal':  { ch:'reward', p:3, cd:0, fn(v,o){ const g = o.g || 1; v.strike(g >= 2 ? 'glass' : 'wood', g >= 2 ? R.A5 : R.E5, .03 + g * .004, 0, { decay:.5 + g * .1 }); if(g >= 2) v.strike('glass', R.E6, .018, .07, { decay:.6 }); } },
    'card.flip':    { ch:'ui', p:1, cd:90, vars:2, jit:.03, fn(v,o){ v.air({ dur:.11, f:2200 * o.j, f2:6200, peak:.05, q:1.1 }); v.grains({ t:.03, dur:.05, n:3, peak:.012, f:5200, gd:.01 }); v.pan(o.vr ? .15 : -.15); } },
    /* ---- انضباط: حجر وحديد ومطرقة؛ التجاوز = دفع وفكّ سلسلة ---- */
    'discipline.penalty': { ch:'discipline', p:4, cd:500, hold:350, duck:true, fn(v){ v.strike('wood', 110, .11, 0, { decay:1.6, ex:.8, exF:900 }); v.strike('stone', 82, .07, .005, { decay:2 }); v.tone({ t:.03, f:R.D3, f2:110, dur:.6, a:.02, peak:.05, lp:500 }); } },
    'discipline.unlock':  { ch:'discipline', p:3, cd:300, hold:400, fn(v){ v.strike('iron', 640, .04, 0, { decay:.4 }); v.grains({ t:.05, dur:.14, rate:40, peak:.014, f:1600, q:3 }); v.strike('iron', 960, .035, .2, { decay:.6 }); v.strike('glass', R.A5, .014, .26, { decay:.8 }); } },
    'penalty.bypass':     { ch:'discipline', p:3, cd:300, hold:300, fn(v){ [0, 1, 2].forEach(k=>v.strike('gold', 1250 - k * 90, .02, k * .05, { decay:.4 })); v.strike('iron', 520, .03, .2, { decay:.5 }); v.grains({ t:.22, dur:.2, rate:35, peak:.012, f:2400, q:4, shape:'fade' }); v.air({ t:.3, dur:.25, f:700, f2:2200, peak:.014 }); } },
    'reward.unlock':      { ch:'reward', p:4, cd:500, hold:350, wet:.16, duck:true, fn(v){ v.strike('glass', R.A4, .04, 0, { decay:1 }); v.strike('glass', R.E5, .04, .02, { decay:1 }); v.strike('crystal', R.A5, .03, .12, { decay:1.2 }); v.strike('crystal', R.D6, .022, .19, { decay:1.2 }); v.air({ t:.1, dur:.4, f:3000, f2:8000, peak:.012 }); } },
    'reward.achievement': { ch:'reward', p:4, cd:500, hold:350, wet:.22, duck:true, fn(v){ v.strike('bronze', R.A4, .05, 0, { decay:1 }); v.strike('crystal', R.A5, .04, .05, { decay:1.2 }); v.strike('crystal', R.E6, .032, .16, { decay:1.2 }); v.fm({ t:.16, f:R.D5, ratio:3, index:1.4, index2:.1, dur:1.2, peak:.02 }); } },
    'startup':            { ch:'ui', p:2, cd:1000, wet:.12, fn(v){ v.air({ dur:.6, f:300, f2:1800, peak:.02, a:.4 }); v.strike('glass', R.D4, .03, .2, { decay:1 }); v.strike('glass', R.A4, .03, .32, { decay:1 }); v.strike('crystal', R.D5, .025, .44, { decay:1.4 }); } }
  };
  /* بطاقات الكروت: طبقة توقيع العائلة فوق هوية CS عند البداية والذروة (يومي ورق/خشب · أسبوعي زجاج · شهري معدن) */
  const CARD_FAM = { d:(v, c)=>{ if(c === 'start') v.grains({ dur:.12, rate:70, peak:.01, f:3200, shape:'swell' }); else v.strike('wood', R.A5, .02, 0, { decay:.6 }); },
                     w:(v, c)=>{ if(c === 'start') v.air({ dur:.3, f:2000, f2:6000, peak:.01 }); else v.strike('glass', R.E6, .018, 0, { decay:1 }); },
                     m:(v, c)=>{ if(c === 'start') v.strike('metal', 196, .02, 0, { decay:1.2 }); else v.strike('bronze', 147, .03, 0, { decay:1.4 }); } };
  const cardBase = SOUNDS['card.cue'] && SOUNDS['card.cue'].fn;
  if(cardBase) SOUNDS['card.cue'].fn = function(v, o){ cardBase(v, o); try{ if(!o.nolift && (o.cue === 'start' || o.cue === 'climax')){ const fam = CARD_FAM[String(o.key || 'd').charAt(0)]; if(fam) fam(v, o.cue); } }catch(e){} };
  Object.assign(SOUNDS, V2);
"""
rep("""  const PREVIEW = { master:['confirm'], ui:['success'], xp:['xp.chime', {dir:1, n:3}], reward:['reward.unlock'], discipline:['discipline.unlock'] };""",
    catalog + """  const PREVIEW = { master:['success', { ctx:'plan' }], ui:['task.done'], xp:['xp.chime', {dir:1, n:3}], reward:['store.buy', { ctx:'cosmetic' }], discipline:['discipline.unlock'] };""", 'catalog')

# ================= 3) ربط السياق (codemod) =================
CTX = {
 'open':   {'openArchiveDetail':'archive','archOpen':'archive','openNotifCenter':'notif','codisOpenReport':'report','econOpenVault':'store','econOpenLayer':'store','econOpenPending':'outcome',
            'rpOpenHub':'settings','rpOpenLeaf':'settings','econOpenVaultLegacy':'store','econOpenDetail':'card','econDismantle':'dismantle','econPouchSheet':'pouch','econPouchUse':'pouch',
            'hcdPickOpen':'holiday','econBulkShow':'box','econBoxOpenFor':'box','econBoxNext':'box','econPackOpen':'box','codisConfirm':'dialog'},
 'close':  {'closeArchiveDetail':'archive','closeNotifCenter':'notif','codisCloseReport':'report','econCloseOwn':'store','econCloseStore':'store','rpGo':'settings','econCloseDetail':'card',
            'dqCancel':'dialog','dqClose':'dialog','hcdPickClose':'holiday','econBulkClose':'box','econBoxClose':'box','econPackClose':'box','appLockFaceToggle':'lock'},
 'confirm':{'codisEditTaskWeight':'task','appLockRecoveryCopy':'lock','appLockForgotFace':'lock','appLockForgotKeySubmit':'lock','notifToggleEnabled':'switch','notifToggleCategory':'switch',
            'notifToggleQuietHours':'switch','addManualTask':'task','addManualLearnTask':'task','restore':'restore','econToggleReward':'switch','econTogglePunish':'switch','dqConfirm':'dismantle',
            'pqConfirm':'pouch','econUse':'use','addHabit':'habit','restoreArchivedHabit':'restore'},
 'invalid':{'econBuyBox':'funds','econBuyBox10':'funds','econCosBuy':'funds','hcdBuy':'funds','econBuy':'funds','decide':'funds','econSell':'unavailable','econSellBatch':'unavailable',
            'hcdUse':'locked','dqAdd':'limit','openPassPicker':'unavailable','econReadReward':'unavailable','econReadPunish':'unavailable','resistEventHabit':'limit','appLockFail':'auth',
            'appLockSubmitAny':'auth','appLockTryFace':'auth','appLockForgotReject':'auth','appLockForgotFace':'auth','setLockStatus':'auth','openSavePlanPrompt':'input','confirmSavePlan':'input',
            'distributePlan':'input','replanWeek':'input','addManualTask':'input','addManualLearnTask':'input','codisEditTaskWeight':'input','codisTaskDayLocked':'locked','econSettleMonthNow':'unavailable',
            'econDismantle':'unavailable','dqConfirm':'unavailable','pqConfirm':'unavailable','econPouchUse':'unavailable','econCosApply':'unavailable','econSelToggle':'limit','hcdPickConfirm':'input',
            'econBoxOpenFor':'unavailable','econBoxDo':'unavailable','econPackOpen':'unavailable','econUse':'unavailable'},
 'success':{'appLockSuccess':'lock','appLockRecoveryIssue':'lock','appLockForgotSaveNew':'lock','setLockStatus':'lock','disableAppLock':'lock','confirmSavePlan':'plan','distributePlan':'plan',
            'replanWeek':'plan','planSortByImportance':'plan','econSave':'settings','hcdPickConfirm':'holiday'},
 'press':  {'setSettingsPeriod':'tab','codisFlipToggle':'flip','econOwnJump':'tab','econClosedSetView':'tab','econStoreJump':'tab','dqAdd':'step','dqSub':'step','dqMax':'step',
            'econSelToggle':'select','econSelAll':'select','hcdPickPaint':'select','econBoxDo':'box'},
 'coins.take':{'econSell':'sell','econSellBatch':'sell','econPouchUse':'silverpour','dqShowResult':'silver'},
 'store.buy':{'econBuy':'card','econCosBuy':'cosmetic','hcdBuy':'holiday','econBuyBox':'box','econBuyBox10':'bulk','econBulkCue':'bulk','econBoxDo':'box'},
 'task.delete':{'deleteSavedPlan':'plan','deleteTask':'task','deleteArchivedPlan':'archive','clearArchive':'archive','econDeleteReward':'card','econDeletePunish':'card','removeHabit':'habit','deleteLearnTask':'task'},
}
FUNDS = re.compile('الرصيد|ينقصك|كوين')
lines = s.split('\n'); fnre = re.compile(r'^\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(|^\s+function\s+([A-Za-z0-9_$]+)\s*\(')
cur = None; stats = {}
for i, l in enumerate(lines):
    m = re.search(r'function\s+([A-Za-z0-9_$]+)\s*\(', l)
    if m: cur = m.group(1)
    if 'codisSfx(' not in l or cur is None: continue
    def sub(mm):
        name, tail = mm.group(1), mm.group(2)
        table = CTX.get(name)
        if not table or cur not in table: return mm.group(0)
        c = table[cur]
        if name == 'invalid' and FUNDS.search(l) and c not in ('auth',): c = 'funds'
        stats[name] = stats.get(name, 0) + 1
        return "codisSfx('%s', { ctx:'%s' }" % (name, c) + (')' if tail == ')' else ', ')
    nl = re.sub(r"codisSfx\('([a-z.]+)'(\)|,\s*(?=\{))", lambda mm: sub(mm) if mm.group(2) == ')' else mm.group(0), l)
    # دمج ctx داخل كائن خيارات موجود: codisSfx('x', { … })
    def sub2(mm):
        name = mm.group(1); table = CTX.get(name)
        if not table or cur not in table: return mm.group(0)
        stats[name] = stats.get(name, 0) + 1
        return "codisSfx('%s', { ctx:'%s', " % (name, table[cur])
    nl = re.sub(r"codisSfx\('([a-z.]+)',\s*\{(?!\s*ctx)\s*", sub2, nl)
    lines[i] = nl
s = '\n'.join(lines)
print('ctx rewrites:', stats)

# استدعاءات ثلاثية بأسماء عامة
TERN = [
 ("codisSfx(econEditing ? 'open' : 'close');", "codisSfx(econEditing ? 'open' : 'close', { ctx:'editor' });"),
 ("codisSfx(econClosedOpen ? 'open' : 'close');", "codisSfx(econClosedOpen ? 'expand' : 'collapse');"),
 ("codisSfx(on ? 'close' : 'reward.achievement');", "codisSfx(on ? 'close' : 'reward.achievement', { ctx:'card' });"),
 ("codisSfx(econSelMode ? 'open' : 'close');", "codisSfx(econSelMode ? 'open' : 'close', { ctx:'select' });"),
 ("  if(!o.silent) codisSfx(open ? 'open' : 'close');", "  if(!o.silent) codisSfx(open ? 'expand' : 'collapse');"),
 ("  if(!celebrated) codisSfx(was ? 'task.undo' : 'task.done');", "  if(!celebrated) codisSfx(was ? 'task.undo' : 'task.done', { ctx:'habit' });"),
 ("saveData(); codisSfx(delta > 0 ? 'task.done' : 'task.undo'); renderHabitsPage();", "saveData(); codisSfx(delta > 0 ? 'task.done' : 'task.undo', { ctx:'habit' }); renderHabitsPage();"),
 ("  if(modal){ if(CodisMotion.isOpen(modal)) codisSfx(v ? 'confirm' : 'close'); CodisMotion.modalOut(modal); }", "  if(modal){ if(CodisMotion.isOpen(modal)) codisSfx(v ? 'confirm' : 'close', { ctx:'dialog' }); CodisMotion.modalOut(modal); }"),
 ("codisSfx(t.checked ? 'toggle.on' : 'toggle.off');", "codisSfx(t.checked ? 'toggle.on' : 'toggle.off', { ctx:'switch' });"),
]
for a, b in TERN: rep(a, b, 'tern ' + a[:30])

# ================= 4) أحداث بلا صوت سابقاً + إصلاح استدعاءات صامتة =================
# صندوق مفرد: لحظة الفتح كانت 'open' عام، والكشف من المستوى 2 كان 'card.cue' بلا مفتاح (= صمت)
rep("      const m = mouthPos(), lift = T.lift;\n      codisSfx('open');","      const m = mouthPos(), lift = T.lift;\n      codisSfx('box.release', { lv:Math.min(5, n), n:n });", 'single open')
rep("    codisSfx(g === 1 ? 'store.buy' : g === 2 ? 'card.cue' : g === 3 ? 'reward.unlock' : 'reward.achievement');", "    codisSfx('box.reveal', { lv:g, n:s.n });", 'single reveal')
# مسرح ×10
rep("    if(p.g >= 2) codisSfx('box.thud');", "    codisSfx('box.thud', { n:s.n, g:p.g === 1 ? .45 : .8 });", 'bulk thud')
rep("    if(p.g >= 3){ const R = rl(p); el.stage.style.setProperty('--cb-rgb', R.rgb); el.stage.style.setProperty('--cb-rgb2', R.rgb2); codisSfx('box.charge'); }",
    "    if(p.g >= 2) codisSfx('box.charge', { lv:p.g, dur:p.ant / 1000, n:s.n });\n    if(p.g >= 3){ const R = rl(p); el.stage.style.setProperty('--cb-rgb', R.rgb); el.stage.style.setProperty('--cb-rgb2', R.rgb2); }", 'bulk charge')
rep("    codisSfx('box.creak'); try{ codisHaptic([10]); }catch(e){}", "    codisSfx('box.creak', { n:S.n }); try{ codisHaptic([10]); }catch(e){}", 'bulk creak')
rep("    codisSfx(g >= 3 ? 'box.release' : 'box.unlock');", "    codisSfx(g >= 3 ? 'box.release' : 'box.unlock', { lv:g, n:s.n, g:g === 1 ? .55 : .85 });", 'bulk open')
rep("    codisSfx(g === 1 ? 'box.reveal' : g === 2 ? 'card.cue' : g === 3 ? 'reward.unlock' : 'reward.achievement');", "    codisSfx(g >= 3 ? 'box.reveal' : 'bulk.reveal', { lv:g, g:g, n:s.n });", 'bulk reveal')
rep("    A(card, [{ transform:'translate(0,0) scale(1)', opacity:1 }", "    codisSfx('bulk.fly', { g:p.g });\n    A(card, [{ transform:'translate(0,0) scale(1)', opacity:1 }", 'bulk fly')
rep("    A(slot.firstChild, [{ transform:'scale(1.18)' }, { transform:'scale(1)' }], { duration:300, easing:E().spring });", "    A(slot.firstChild, [{ transform:'scale(1.18)' }, { transform:'scale(1)' }], { duration:300, easing:E().spring });\n    if(!s.done) codisSfx('bulk.slot', { g:p.g });", 'bulk slot')
rep("    const target = next ? next.start : s.plan.total - 380;", "    codisSfx('bulk.advance');\n    const target = next ? next.start : s.plan.total - 380;", 'bulk advance')
rep("function econBulkSkip(){ const s = econBulkState; if(!s || s.phase !== 'opening') return; econBulkFinish(s.token); }", "function econBulkSkip(){ const s = econBulkState; if(!s || s.phase !== 'opening') return; codisSfx('bulk.skip'); econBulkFinish(s.token); }", 'bulk skip')
rep("function econBulkCue(s){ codisSfx('store.buy', { ctx:'bulk' }); if(s.res.items.some(r=>r.pass || r.holiday)) codisSfx('reward.achievement'); }",
    "function econBulkCue(s){ let g = 1; try{ s.res.items.forEach(r=>{ g = Math.max(g, CodisBoxCinema.groupOf(CodisRevealLevels.levelOfResult(r))); }); }catch(e){} codisSfx('bulk.finale', { g:g }); }", 'bulk finale')
# قلب البطاقة
rep("  try{ codisSfx('press', { ctx:'flip' }); }catch(x){}", "  try{ codisSfx('card.flip'); }catch(x){}", 'flip')
# قلم المهام: أصوات على زمن الخطوط نفسها (فقط عند بداية الحركة، لا عند إعادة البناء)
rep("  function mount(item, spec, elapsed){ item.classList.add('is-answering'); build(item, spec, elapsed || 0); leave(item, spec.status, elapsed || 0); }",
"""  function penSound(spec){
    if(reduced()){ codisSfx('task.leave', { delay:.5, seq:true }); return; }
    if(spec.status === 'done'){ codisSfx('pen.stroke', { kind:'check', delay:.08, dur:.54, seq:true }); codisSfx('pen.scribble', { delay:.56, dur:.62, seq:true }); }
    else if(spec.status === 'none'){ codisSfx('pen.stroke', { kind:'x', delay:.08, dur:.32, pan:-.1, seq:true }); codisSfx('pen.stroke', { kind:'x', delay:.36, dur:.3, pan:.1, seq:true }); codisSfx('pen.scribble', { delay:.7, dur:.5, seq:true }); }
    else { codisSfx('pen.fill', { delay:.08, dur:.68, pct:spec.pct, seq:true }); codisSfx('pen.scribble', { delay:.7, dur:.45, seq:true }); }
    codisSfx('task.leave', { delay:spec.status === 'none' ? 1.2 : 1.25, seq:true });
  }
  function mount(item, spec, elapsed){ item.classList.add('is-answering'); build(item, spec, elapsed || 0); leave(item, spec.status, elapsed || 0); }""", 'pen sounds')
rep("  return { mount, total };", "  return { mount, total, sound:penSound };", 'pen export')
rep("    play(k, id, status, pct);\n  }", "    try{ CodisPen.sound({ status:status, pct:pct }); }catch(e){}   /* أصوات القلم مرة واحدة لكل حسم، بتوقيت الخطوط */\n    play(k, id, status, pct);\n  }", 'pen sound once')
# نافذة المنجزة + لوحة النسبة + اختيار نسبة
rep("    sheet = s0; document.addEventListener('keydown', s0.onKey, true);", "    sheet = s0; document.addEventListener('keydown', s0.onKey, true); codisSfx('open', { ctx:'sheet' });", 'done sheet open')
rep("  function closeDone(){ if(!sheet) return; const s0 = sheet; sheet = null;", "  function closeDone(){ if(!sheet) return; codisSfx('close', { ctx:'sheet' }); const s0 = sheet; sheet = null;", 'done sheet close')
rep("    item.appendChild(panel);\n    const range = panel.querySelector('.pp-range')", "    item.appendChild(panel); codisSfx('open', { ctx:'partial' });\n    const range = panel.querySelector('.pp-range')", 'partial open')
rep("    panel.querySelectorAll('.pp-chip').forEach(c=>{ c.onclick = ()=>set(c.dataset.v); });", "    panel.querySelectorAll('.pp-chip').forEach(c=>{ c.onclick = ()=>{ codisSfx('select'); set(c.dataset.v); }; });", 'partial chip')
rep("    panel.querySelector('.pp-cancel').onclick = ()=>{ panel.remove(); };", "    panel.querySelector('.pp-cancel').onclick = ()=>{ codisSfx('close', { ctx:'editor' }); panel.remove(); };", 'partial cancel')
rep("      codisSfx('confirm', { ctx:'restore' }); showToast('رجعت المهمة للقائمة', 'var(--success)', 'check');", "      codisSfx('task.restore'); showToast('رجعت المهمة للقائمة', 'var(--success)', 'check');", 'restore sound')
# طيّ تفاصيل العادة + قفز المعاينة + فتح بطاقة ×10 المكبّرة
rep("    tg.onclick = ()=>{ const on = !row.classList.contains('is-open'); row.classList.toggle('is-open', on);", "    tg.onclick = ()=>{ const on = !row.classList.contains('is-open'); codisSfx(on ? 'expand' : 'collapse'); row.classList.toggle('is-open', on);", 'habit details')
rep("function econPackJump(id){ const d = document.getElementById('pk-g-' + id); if(!d) return; d.open = true;", "function econPackJump(id){ const d = document.getElementById('pk-g-' + id); if(!d) return; codisSfx('select'); d.open = true;", 'pack jump')
rep("  m.appendChild(z); z._opener = opener || null; econBulkZoomEl = z;", "  m.appendChild(z); z._opener = opener || null; econBulkZoomEl = z; codisSfx('open', { ctx:'card' });", 'zoom open')
rep("  document.removeEventListener('keydown', z._key, true); z.classList.remove('is-open');", "  document.removeEventListener('keydown', z._key, true); z.classList.remove('is-open'); codisSfx('close', { ctx:'card' });", 'zoom close')
# التنقّل بين الغرف: كل غرفة لها جذر نغمي
rep("  if(pageChanged) codisSfx('nav');", "  if(pageChanged) codisSfx('nav', { ctx:page });", 'nav room')

s = s.replace('<!-- CODIS-BULK-V3 -->', '<!-- CODIS-BULK-V3 -->\n<!-- CODIS-AUDIO-V2 -->', 1)
if 'CODIS-AUDIO-V2 -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v11 OK')
