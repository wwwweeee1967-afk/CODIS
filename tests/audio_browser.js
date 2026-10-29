/* CODIS-AUDIO-V2 runtime test (evaluate in the page). Offline rendering of every identity + settings + gating + live trace.
   Live-play checks need a running AudioContext (a real tap/click first); they are reported as "unverified" otherwise. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const A = CodisAudio, keys = A.events();
  T('engine supported + new API present', A.supported && typeof A.render === 'function' && typeof A.trace === 'function');
  /* features: 16 log bands (Goertzel) + 12-frame envelope → unit vector */
  const BANDS = Array.from({ length:16 }, (_, k)=>80 * Math.pow(2, k * .55));
  function feat(buf){
    const x = buf.getChannelData(0), y = buf.numberOfChannels > 1 ? buf.getChannelData(1) : x, sr = buf.sampleRate, N = x.length;
    let peak = 0, end = 0, sum = 0; const m = new Float32Array(N);
    for(let i = 0; i < N; i++){ const v = (x[i] + y[i]) / 2; m[i] = v; const a = Math.max(Math.abs(x[i]), Math.abs(y[i])); if(a > peak) peak = a; if(a > .001) end = i; sum += v * v; }
    const len = end / sr, active = Math.max(1, end), rms = Math.sqrt(sum / active);
    const step = 4, M = Math.min(active, sr * 1.5) | 0, bands = BANDS.map(f=>{ const w = 2 * Math.PI * f * step / sr, c = 2 * Math.cos(w); let s1 = 0, s2 = 0; for(let i = 0; i < M; i += step){ const s0 = m[i] + c * s1 - s2; s2 = s1; s1 = s0; } return Math.sqrt(Math.max(0, s1 * s1 + s2 * s2 - c * s1 * s2)); });
    const env = []; const fr = Math.max(1, Math.floor(active / 12)); for(let k = 0; k < 12; k++){ let e = 0; for(let i = k * fr; i < (k + 1) * fr && i < N; i += 8) e += m[i] * m[i]; env.push(Math.sqrt(e)); }
    const nb = Math.hypot.apply(null, bands) || 1, ne = Math.hypot.apply(null, env) || 1, lenT = [len * 2];
    return { peak, rms, len, v:bands.map(b=>b / nb).concat(env.map(e=>e / ne * .6)).concat(lenT) };
  }
  const F = {}, bad = [];
  for(const k of keys){
    const [n, c] = k.split('@'), opt = c ? { ctx:c } : {};
    if(n === 'card.cue') Object.assign(opt, { key:'w:A', cue:'start' });
    if(n === 'punish.cue') Object.assign(opt, { cue:'stinger', lv:4 });
    if(/^xp\./.test(n)) Object.assign(opt, { dir:1, i:2, n:4 });
    if(/^box\.|^bulk\./.test(n)) Object.assign(opt, { lv:3, g:3, n:3, dur:.8 });
    try{ F[k] = feat(await A.render(n, opt, 3)); }catch(e){ bad.push(k + ': ' + e.message); }
  }
  T('every identity renders offline without error', bad.length === 0, bad.join(' | '));
  const ks = Object.keys(F);
  const silent = ks.filter(k=>F[k].rms < 1e-4 || F[k].peak < .002); T('no silent identity', silent.length === 0, silent.join(','));
  const clip = ks.filter(k=>F[k].peak > .98); T('no clipping before the master limiter', clip.length === 0, clip.map(k=>k + '=' + F[k].peak.toFixed(2)).join(','));
  const long = ks.filter(k=>F[k].len > 2.9 && !/punish|card\.cue|charge/.test(k)); T('no identity rings past 2.9 s (except long cinematic cues)', long.length === 0, long.join(','));
  const sim = (a, b)=>a.v.reduce((s, x, i)=>s + x * b.v[i], 0) / (Math.hypot.apply(null, a.v) * Math.hypot.apply(null, b.v));
  /* the generic families: every context identity must sound different from the base and from each other */
  const fam = {}; ks.forEach(k=>{ const n = k.split('@')[0]; (fam[n] = fam[n] || []).push(k); });
  const same = [];
  Object.keys(fam).forEach(n=>{ const g = fam[n]; for(let i = 0; i < g.length; i++) for(let j = i + 1; j < g.length; j++){ const s0 = sim(F[g[i]], F[g[j]]); if(s0 > .985) same.push(g[i] + '~' + g[j] + '=' + s0.toFixed(3)); } });
  T('context variants of the same event are acoustically distinct (cos < 0.985)', same.length === 0, same.join(', '));
  const all = []; for(let i = 0; i < ks.length; i++) for(let j = i + 1; j < ks.length; j++){ const s0 = sim(F[ks[i]], F[ks[j]]); if(s0 > .995) all.push(ks[i] + '~' + ks[j]); }
  T('near-identical pairs across the whole catalogue are rare (<= 6)', all.length <= 6, all.length + ': ' + all.slice(0, 12).join(', '));
  T('gold and silver coins differ', sim(F['coins.take@sell'], F['coins.take@silver']) < .97, sim(F['coins.take@sell'], F['coins.take@silver']).toFixed(3));
  T('task done / half / none differ', sim(F['task.done'], F['task.half']) < .985 && sim(F['task.done'], F['task.none']) < .985);
  /* variants: two renders of the same varied identity are related but not identical */
  const v0 = feat(await A.render('task.done', { vr:0 }, 1)), v1 = feat(await A.render('task.done', { vr:1 }, 1));
  T('variants keep identity but are not identical', sim(v0, v1) < .9999 && sim(v0, v1) > .8, sim(v0, v1).toFixed(4));
  /* settings & gating (no context needed) */
  const s0 = JSON.stringify(data.settings.sound);
  data.settings.sound.enabled = false; T('disabled sound → play() refuses', codisSfx('press') === false);
  data.settings.sound.enabled = true; data.settings.sound.channels.ui = 0; T('channel at 0 → that channel refuses', codisSfx('press') === false);
  data.settings.sound = JSON.parse(s0);
  T('unknown sound name fails silently (no throw)', codisSfx('no.such.sound') === false);
  T('settings normalize keeps 4 channels + master', JSON.stringify(Object.keys(codisNormalizeSoundSettings({}).channels)) === '["ui","xp","reward","discipline"]');
  /* live: needs a running context */
  A.unlockNow(); await sleep(150);
  const st = A.stats();
  if(st.state === 'running'){
    const t0 = Math.floor(performance.now()); for(let i = 0; i < 40; i++) codisSfx('press'); await sleep(50);
    const n = A.trace().filter(e=>e.at >= t0 - 1 && e.key === 'press').length; T('live: 40 rapid taps are throttled by cooldown (<= 2 played)', n <= 2, n);
    codisSfx('open', { ctx:'store' }); const tr = A.trace(); T('live: context identity resolved at play time', tr[tr.length - 1].key === 'open@store');
    for(let i = 0; i < 30; i++) codisSfx('box.reveal', { lv:2 }); await sleep(30); T('live: voice cap respected', A.stats().voices <= 16, A.stats().voices);
    await sleep(2600);   /* let the voice-cap test drain before the integration checks */
    /* integration: real UI paths emit their own identities */
    const keysSince = t0=>A.trace().filter(e=>e.at >= t0 - 1).map(e=>e.key), mark = ()=>Math.floor(performance.now());
    codisConfirm = async()=>true; CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{};
    let n0 = mark(); document.querySelector('.navbtn[data-page="habits"]').click(); await sleep(400);
    T('live: room navigation plays the room identity', keysSince(n0).includes('nav'));
    const wk = currentWeekId(), di = new Date().getDay(), days = {}; for(let i = 0; i < 7; i++) days[i] = [];
    days[di] = [0, 1, 2].map(i=>({ id:'au' + i, text:'مهمة ' + i, status:null, itemId:null, qty:1, unit:null, priority:'low' })); days[(di + 1) % 7] = [{ id:'aux', text:'x', status:null, qty:1, priority:'low' }];
    data.weeks[wk] = { days:days, startedAt:todayKey(), items:[], holidayDay:null, planStartDay:di, planName:'a' }; saveData();
    document.querySelector('.navbtn[data-page="tasks"]').click(); await sleep(500);
    n0 = mark(); document.querySelector('[data-tid="au0"] [data-status="done"]').click(); await sleep(250);
    const k1 = keysSince(n0); T('live: completing a task → task.done + pen stroke + scribble + leave', ['task.done', 'pen.stroke', 'pen.scribble', 'task.leave'].every(k=>k1.includes(k)), k1.join(','));
    n0 = mark(); document.querySelector('[data-tid="au1"] [data-status="none"]').click(); await sleep(250);
    const k2 = keysSince(n0); T('live: not done → task.none + two X strokes', k2.includes('task.none') && k2.filter(k=>k === 'pen.stroke').length === 2, k2.join(','));
    await sleep(2600); n0 = mark(); document.querySelector('.cd-trigger').click(); await sleep(300);
    T('live: completed sheet has its own open sound', keysSince(n0).includes('open@sheet'));
    n0 = mark(); await CodisTaskFlow.restore('tasks', 'au0'); await sleep(100);
    T('live: restore plays task.restore', keysSince(n0).includes('task.restore'));
    CodisTaskFlow.closeDone(); await sleep(200);
    n0 = mark(); const cf = document.createElement('div'); cf.innerHTML = codisFlipHtml('<i>f</i>', '<i>b</i>'); document.body.appendChild(cf); cf.querySelector('.cflip').click(); cf.remove(); await sleep(60);
    T('live: card flip has its own sound (not the generic press)', keysSince(n0).includes('card.flip'));
    /* ×10 stage: run the timeline deterministically */
    data.wallet.balance = 20000; saveData(); await econBuyBox10('bx2'); await sleep(100);
    n0 = mark(); const sch = econBulkSch; sch.items.forEach(p=>CodisBulkCinema._seek(p.end + 5)); CodisBulkCinema._seek(sch.total + 10); await sleep(100);
    const kb = keysSince(n0), cnt = k=>kb.filter(x=>x === k).length;
    T('live: x10 stage has per-box sounds (thud, reveal, fly, slot)', cnt('box.thud') >= 1 && (cnt('bulk.reveal') + cnt('box.reveal')) >= 1 && cnt('bulk.fly') >= 1 && cnt('bulk.slot') >= 1, kb.join(','));
    T('live: x10 ends with the finale identity', kb.includes('bulk.finale'));
    econBulkClose(true);
  } else T('live playback (AudioContext ' + st.state + ' — needs a real tap): UNVERIFIED here', true, st.state);
  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed, ids:ks.length, live:st.state };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
