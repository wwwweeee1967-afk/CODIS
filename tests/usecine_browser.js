/* CODIS-USE-CINE test (patch_v36.py) — evaluate in the page on a FRESH guest origin. Mutates local test data only.
   Covers: level boundaries · paid/coinValue/invalid price · scene only after a successful use · cancel · save failure · double tap · timed reward ·
   reduced motion · cleanup/no leftovers · all nine levels render · name safety (escaping) · wallet unchanged by the scene. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const errs = []; window.addEventListener('error', e=>errs.push(String(e.message)));
  let confirmAnswer = true; codisConfirm = async()=>confirmAnswer;
  const L = CodisUseCine.levelOf;
  /* ---- 1) levels from the paid price ---- */
  [[100,1],[101,2],[200,2],[201,3],[350,3],[351,4],[551,4],[552,5],[853,5],[854,6],[1300,6],[1301,7],[2500,7],[2501,8],[8000,8],[8001,9]].forEach(([p, l])=>T('paid ' + p + ' → level ' + l, L({ paid:p, coinValue:1 }) === l, L({ paid:p })));
  T('paid wins over coinValue', L({ paid:150, coinValue:9000 }) === 2);
  T('no paid → coinValue (box/outcome source)', L({ paid:null, coinValue:600 }) === 5 && L({ coinValue:3000 }) === 8);
  T('invalid price → safe level 1', L({ paid:null, coinValue:NaN }) === 1 && L({}) === 1 && L({ paid:-5, coinValue:0 }) === 1 && L({ paid:'x' }) === 1);
  T('recipes escalate (nine, each stronger)', CodisUseCine._recipes.length === 10 && (()=>{ const r = CodisUseCine._recipes, F = ['ink','copper','gold','holo','prism'], sc = x=>x.dust + x.sparks * 2 + x.conf + x.rings * 20 + x.rays * 40 + x.glow * 100 + x.flip * 30 + x.shine * 10 + F.indexOf(x.foil) * 25 + x.aurora * 40 + x.flash * 40; for(let i = 2; i <= 9; i++){ const a = r[i - 1], b = r[i]; if(!(sc(b) > sc(a) && b.dust >= a.dust && b.conf >= a.conf && b.fly >= a.fly && F.indexOf(b.foil) >= F.indexOf(a.foil))) return false; } return true; })());

  /* ---- 2) real purchase path → owned copies ---- */
  openSettingsCategory('rewards'); settingsRoom = 'tasks'; econRenderRewards(); await sleep(200);
  const f = (id, v)=>{ document.getElementById('eco-new-r-' + id).value = v; };
  const addR = name=>{ f('name', name); econAddReward(); return data.settings.rewardItems.find(x=>x.name === name); };
  const burger = addR('برجر تجربة'), match = addR('مشاهدة مباراة'), timed = addR('ساعة سوشل ميديا'), xss = addR('<img src=x onerror=window.__pwn=1> اكل');
  data.wallet.balance = 900000; saveData(); econOpenStore(); await sleep(900);
  async function own(item){ const n0 = CodisInventory.all().length; await econBuy(item.id); await sleep(120); if(CodisBuyCine.isOpen()){ CodisBuyCine.keep(); await sleep(450); } return CodisInventory.all().slice(n0)[0]; }
  const cBurger = await own(burger), cMatch = await own(match), cTimed = await own(timed), cXss = await own(xss);
  T('four owned copies', [cBurger, cMatch, cTimed, cXss].every(c=>c && c.status === 'owned'));

  /* ---- 3) cancel: nothing happens ---- */
  confirmAnswer = false; await econUse(cBurger.uid); await sleep(150);
  T('cancel → still owned, no scene', CodisInventory.get(cBurger.uid).status === 'owned' && !CodisUseCine.isOpen() && !document.querySelector('.ucx'));
  confirmAnswer = true;

  /* ---- 4) save failure: no scene, stays owned ---- */
  codisSaveSuspended = 'fail'; await econUse(cBurger.uid); await sleep(150); codisSaveSuspended = false;
  T('save failure → no scene, still owned', CodisInventory.get(cBurger.uid).status === 'owned' && !document.querySelector('.ucx'));

  /* ---- 5) successful use → scene, once, level from paid price ---- */
  const lvExpect = L(cBurger), bal = data.wallet.balance, tx0 = data.wallet.transactions.length;
  econUse(cBurger.uid); econUse(cBurger.uid); econUse(cBurger.uid); await sleep(250);
  const st = CodisUseCine._state();
  T('scene opened after success', !!st && CodisUseCine.isOpen());
  T('only one scene in the DOM (double tap)', document.querySelectorAll('.ucx').length === 1);
  T('marked used exactly once', CodisInventory.get(cBurger.uid).status === 'used' && CodisInventory.all().filter(x=>x.uid === cBurger.uid).length === 1);
  T('level class = paid price level', st && st.root.classList.contains('lv-' + lvExpect), st && st.root.className);
  T('wallet untouched by use/scene', data.wallet.balance === bal && data.wallet.transactions.length === tx0);
  T('name is on the card', st && st.root.querySelector('.ucx-name').textContent === 'برجر تجربة');
  T('message is food-aware', st && st.ctx === 'eat' && /البرجر|بالعافية|صحتين|عافية|الشفا/.test(st.text), st && [st.ctx, st.text]);
  const msg1 = st.text; await sleep(300); econRenderAll(); await sleep(100);
  T('message stable across re-render', CodisUseCine._state().text === msg1 && st.root.querySelector('#ucx-msg').textContent.replace(/\s+/g, ' ').trim() === msg1.replace(/\s+/g, ' ').trim());
  T('page behind not clickable (scene on top)', document.elementFromPoint(innerWidth / 2, innerHeight / 2).closest('.ucx') !== null);
  T('back layer targets the scene', codisBackLayer().act === CodisUseCine.dismiss);
  await sleep(500); CodisUseCine.dismiss(); await sleep(450);
  T('closed and removed', !document.querySelector('.ucx') && !CodisUseCine.isOpen());

  /* ---- 6) other context + escaping ---- */
  await econUse(cMatch.uid); await sleep(200);
  let s2 = CodisUseCine._state();
  T('match reward → match, no invented teams', s2 && s2.ctx === 'match' && !/ريال|برشلونة/.test(s2.text), s2 && [s2.ctx, s2.text]);
  CodisUseCine.dismiss(); await sleep(400);
  await econUse(cXss.uid); await sleep(200);
  T('dynamic name is escaped (no injected element, no handler ran)', !document.querySelector('.ucx img') && !window.__pwn && /<img/.test(document.querySelector('.ucx-name').textContent));
  CodisUseCine.dismiss(); await sleep(400);

  /* ---- 7) timed reward ---- */
  const run0 = CodisTimers.all().length;
  await econUse(cTimed.uid); await sleep(250);
  const s3 = CodisUseCine._state(), run = CodisTimers.active('reward', cTimed.uid);
  T('timed: timer started, copy NOT consumed', !!run && CodisInventory.get(cTimed.uid).status === 'owned' && CodisTimers.all().length === run0 + 1);
  T('timed: scene says the time started (not used)', s3 && s3.timed && /بدأ/.test(s3.root.querySelector('.ucx-kicker').textContent) && /بدأت/.test(s3.root.querySelector('.ucx-seal').textContent) && !/انتهى/.test(s3.text) && !!s3.root.querySelector('.ucx-chip'), s3 && s3.text);
  T('timed: endsAt untouched (absolute, 60 min)', Math.abs(run.endsAt - run.startedAt - 3600000) < 5);
  CodisUseCine.dismiss(); await sleep(400);
  const n = CodisTimers.all().length; await econUse(cTimed.uid); await sleep(200);
  T('timed: already running → no scene, no second timer', !document.querySelector('.ucx') && CodisTimers.all().length === n);

  /* ---- 8) all nine levels render and clean up ---- */
  const extra = []; for(let l = 1; l <= 9; l++){ extra.push(CodisInventory.grant({ uid:'own|test|lv' + l, name:'جائزة تجربة ' + l, rarity:cBurger.rarity, rarityName:cBurger.rarityName, rarityTone:cBurger.rarityTone, rarityOrder:cBurger.rarityOrder, room:'tasks', source:'box', coinValue:[50,150,300,500,800,1200,2000,5000,9000][l - 1], paid:null })); }
  saveData();
  for(let l = 1; l <= 9; l++){
    const e0 = errs.length; await econUse(extra[l - 1].uid); await sleep(120);
    const sx = CodisUseCine._state(); T('level ' + l + ' opens', !!sx && sx.root.classList.contains('lv-' + l));
    await sleep(1400 + l * 200);
    const rc = CodisUseCine._recipes[l];
    T('level ' + l + ' foil = recipe (' + rc.foil + ')', sx && sx.root.classList.contains('f-' + rc.foil), sx && sx.root.className);
    T('level ' + l + ' no JS error', errs.length === e0, errs.slice(e0));
    const card = sx && sx.root.querySelector('.ucx-paper').getBoundingClientRect();
    T('level ' + l + ' card fits the screen', card && card.left >= 0 && card.right <= innerWidth + 1 && card.top >= -1 && card.bottom <= innerHeight + 1, card && [card.left, card.right, card.top, card.bottom, innerWidth, innerHeight]);
    CodisUseCine.dismiss(); await sleep(420);
    T('level ' + l + ' cleaned (no scene, no fx leftovers)', !document.querySelector('.ucx') && !document.querySelector('.ucx-scrap, .ucx-conf, .ucx-ring'));
  }
  /* ---- 9) auto close + a new scene replaces a stale one ---- */
  const autoU = CodisInventory.grant({ uid:'own|test|auto', name:'نوم', rarity:cBurger.rarity, rarityName:cBurger.rarityName, rarityTone:cBurger.rarityTone, rarityOrder:cBurger.rarityOrder, room:'tasks', source:'box', coinValue:40, paid:null }); saveData();
  await econUse(autoU.uid); await sleep(6000);
  T('stays open long enough to read (6s)', !!document.querySelector('.ucx') && CodisUseCine._state().ready); document.querySelector('.ucx-ok').click(); await sleep(450); T('«تمام» closes it', !document.querySelector('.ucx'));
  CodisUseCine.play({ uid:'a', name:'اكل', paid:50 }); CodisUseCine.play({ uid:'b', name:'نوم', paid:50 }); await sleep(50);
  T('a second play replaces the first (one root)', document.querySelectorAll('.ucx').length === 1 && CodisUseCine._state().uid === 'b'); CodisUseCine.dismiss(); await sleep(420);

  /* ---- 10) reduced motion ---- */
  const origR = CodisMotion.isReduced; CodisMotion.isReduced = ()=>true;
  CodisUseCine.play({ uid:'r', name:'برجر', paid:5000 }); await sleep(250);
  const sr = CodisUseCine._state();
  T('reduced: scene + message shown, no heavy fx', !!sr && sr.root.classList.contains('is-reduced') && sr.root.querySelector('.ucx-msg').textContent.trim().length > 2 && !document.querySelector('.ucx-conf, .ucx-scrap'));
  await sleep(300); T('reduced: no particle layer, words visible, ready at once', !sr.fx && Number(getComputedStyle(sr.root.querySelector('.ucx-w')).opacity) > .9 && sr.ready);
  CodisUseCine.dismiss(); await sleep(420); T('reduced: closed', !document.querySelector('.ucx')); CodisMotion.isReduced = origR;

  /* ---- 10b) «استخدام» inside the purchase scene also plays the use scene ---- */
  { const n0 = CodisInventory.all().length; await econBuy(burger.id); await sleep(150); const bs = CodisBuyCine._state(), cp = CodisInventory.all().slice(n0)[0];
    T('purchase scene opened', !!bs && CodisBuyCine.isOpen()); await sleep(2900);
    const u = bs && bs.root.querySelector('.bcx-use'); if(u) u.click(); await sleep(800);
    T('purchase «استخدام» → marked used', !!cp && CodisInventory.get(cp.uid).status === 'used');
    T('purchase «استخدام» → use scene plays after the purchase scene closes', !CodisBuyCine.isOpen() && CodisUseCine.isOpen() && CodisUseCine._state().uid === cp.uid);
    CodisUseCine.dismiss(); await sleep(420); }
  /* ---- 11) other systems untouched ---- */
  T('CodisBuyCine closed', !CodisBuyCine.isOpen());
  T('used once in the log', CodisInventory.all().filter(x=>x.uid === cBurger.uid && x.status === 'used').length === 1);
  T('no page errors', errs.length === 0, errs);
  const failed = out.filter(x=>!x.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed, results:out };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
