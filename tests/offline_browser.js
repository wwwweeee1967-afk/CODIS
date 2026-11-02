/* CODIS-OFFLINE test (patch_v20.py) — evaluate in the page on a FRESH guest origin served from the project root (fetch+eval).
   Part A: pure three-way merge (no network). Part B: inventory/timer lock + completion retry. Part C: sync loop against an IN-PAGE FAKE backend
   (simulated: real PostgREST/Supabase can only be verified by the user). Mutates local test data only. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>{ out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }); try{ sessionStorage.setItem('codis_test_log', out.length + ': ' + n); if(!ok){ const f = JSON.parse(sessionStorage.getItem('codis_test_fail') || '[]'); f.push(n + ' :: ' + (i === undefined ? '' : String(i).slice(0, 160))); sessionStorage.setItem('codis_test_fail', JSON.stringify(f)); } }catch(e){} }, sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const M = CodisMerge.merge, cl = v=>JSON.parse(JSON.stringify(v));
  let confirms = 0; codisConfirm = async()=>{ confirms++; return true; };

  /* ================= A) merge ================= */
  const tx = (id, type, amount, ref)=>({ id:id, type:type, amount:amount, reason:'', source:'', referenceId:ref || '', createdAt:'2026-01-01T00:00:00Z' });
  const W = (bal, list)=>({ balance:bal, lifetimeEarned:0, lifetimeSpent:0, transactions:list });
  const base = { wallet:W(100, [tx('t1', 'ADMIN_ADJUSTMENT', 100)]), inventory:{ items:[{ uid:'u1', status:'owned', name:'a' }, { uid:'u2', status:'owned', name:'b' }] }, settings:{ rewardItems:[{ id:'r1', name:'x', weight:10 }] }, outcomeLedger:{}, codisTimers:{ v:1, items:[] }, habits:{ build:[{ id:'h1', text:'x' }], quit:[] } };
  { const L = cl(base), R = cl(base); L.wallet.balance = 70; L.wallet.transactions.push(tx('tL', 'PURCHASE_REWARD', -30, 'purchase|r1|L')); R.wallet.balance = 150; R.wallet.transactions.push(tx('tR', 'EARN_REWARD_EXCHANGE', 50, 'e1'));
    const m = M(base, L, R, {});
    T('wallet: balance = account + this device\'s NEW transactions only (never summed from two copies)', m.wallet.balance === 120, m.wallet.balance);
    T('wallet: both devices\' transactions kept, no duplicates', m.wallet.transactions.length === 3 && new Set(m.wallet.transactions.map(t=>t.id)).size === 3); }
  { const L = cl(base), R = cl(base); [L, R].forEach((x, i)=>{ x.wallet.balance = 100 + 40; x.wallet.transactions.push(tx('s' + i, 'SELL_REWARD', 40, 'sell|u1')); x.inventory.items[0].status = 'sold'; });
    const m = M(base, L, R, {});
    T('same logical sale on two devices counts ONCE (type+referenceId dedupe)', m.wallet.balance === 140 && m.wallet.transactions.filter(t=>t.referenceId === 'sell|u1').length === 1, m.wallet.balance); }
  { const L = cl(base), R = cl(base); L.inventory.items[0].status = 'used'; R.inventory.items[0].status = 'sold'; R.wallet.balance = 140; R.wallet.transactions.push(tx('sx', 'SELL_REWARD', 40, 'sell|u1'));
    const m = M(base, L, R, {}); T('used vs sold: the one backed by a wallet transaction wins (sold)', m.inventory.items[0].status === 'sold'); }
  { const L = cl(base), R = cl(base); L.inventory.items[1].status = 'used'; const m = M(base, L, R, {}); T('one-way status: owned → used from the device survives', m.inventory.items[1].status === 'used' && m.inventory.items[0].status === 'owned'); }
  { const L = cl(base), R = cl(base); L.inventory.items.push({ uid:'u3', status:'owned', name:'new-L' }); R.inventory.items.push({ uid:'u4', status:'owned', name:'new-R' });
    const m = M(base, L, R, {}); T('items added on both devices are both kept', m.inventory.items.map(x=>x.uid).sort().join() === 'u1,u2,u3,u4'); }
  { const L = cl(base), R = cl(base); R.inventory.items = R.inventory.items.filter(x=>x.uid !== 'u2'); L.inventory.items[1].name = 'edited';
    const m = M(base, L, R, {}); T('edit beats delete (nothing is lost silently)', m.inventory.items.some(x=>x.uid === 'u2' && x.name === 'edited')); }
  { const L = cl(base), R = cl(base); R.inventory.items = R.inventory.items.filter(x=>x.uid !== 'u2'); const m = M(base, L, R, {}); T('delete on one device + untouched on the other = deleted', !m.inventory.items.some(x=>x.uid === 'u2')); }
  { const L = cl(base), R = cl(base); L.outcomeLedger.e1 = { id:'e1', kind:'reward', status:'resolved', decision:'item', resolvedAt:'2026-01-02' }; L.inventory.items.push({ uid:'own|e1', status:'owned' });
    R.outcomeLedger.e1 = { id:'e1', kind:'reward', status:'resolved', decision:'coins', resolvedAt:'2026-01-02' }; R.wallet.balance = 160; R.wallet.transactions.push(tx('c1', 'EARN_REWARD_EXCHANGE', 60, 'e1'));
    const m = M(base, L, R, {});
    T('reward decided "item" on one device and "coins" on the other → exactly ONE reward (no double payout)', !(m.inventory.items.some(x=>x.uid === 'own|e1') && m.wallet.transactions.some(t=>t.referenceId === 'e1')), JSON.stringify([m.inventory.items.map(x=>x.uid), m.wallet.balance])); }
  { const L = cl(base), R = cl(base); L.codisTimers.items.push({ id:'tm1', ev:'ev_a', kind:'reward', ref:'u1', state:'running' }); R.codisTimers.items.push({ id:'tm1', ev:'ev_a', kind:'reward', ref:'u1', state:'done' });
    const m = M(base, L, R, {}); T('timer: running vs done → done; never duplicated', m.codisTimers.items.length === 1 && m.codisTimers.items[0].state === 'done'); }
  { const L = cl(base), R = cl(base); L.habits.build.push({ id:'h2', text:'L' }); R.habits.build.push({ id:'h3', text:'R' }); const m = M(base, L, R, {}); T('habits from both devices kept', m.habits.build.length === 3); }
  { const L = cl(base), R = cl(base); L.settings.rewardItems[0].weight = 20; R.settings.rewardItems[0].name = 'renamed'; const m = M(base, L, R, {});
    T('different fields of the same record merge field by field', m.settings.rewardItems[0].weight === 20 && m.settings.rewardItems[0].name === 'renamed'); }
  { const L = cl(base), R = cl(base); L.settings.theme = 'a'; R.settings.theme = 'b'; T('true scalar conflict: newer side wins by time, deterministic', M(base, L, R, { localNewer:true }).settings.theme === 'a' && M(base, L, R, { localNewer:false }).settings.theme === 'b'); }
  { const g = { wallet:W(30, [tx('g1', 'ADMIN_ADJUSTMENT', 30)]), inventory:{ items:[{ uid:'gi', status:'owned' }] } }, acct = { wallet:W(500, [tx('a1', 'ADMIN_ADJUSTMENT', 500)]), inventory:{ items:[{ uid:'ai', status:'owned' }] } };
    const m = M(null, g, acct, {}); T('guest → account without a base: union, balance 530, both items', m.wallet.balance === 530 && m.inventory.items.length === 2); }
  { const a = M(base, cl(base), cl(base), {}); T('no change on either side → identical result', CodisMerge.same(a, base)); }
  { const L = cl(base), R = cl(base); L.wallet.balance = 70; L.wallet.transactions.push(tx('tL', 'PURCHASE_REWARD', -30, 'purchase|r1|L')); R.wallet.balance = 150; R.wallet.transactions.push(tx('tR', 'EARN_REWARD_EXCHANGE', 50, 'e1'));
    const once = M(base, L, R, {}), twice = M(base, once, R, {}); T('idempotent: re-merging the result with the account changes nothing', CodisMerge.same(once.wallet, twice.wallet), twice.wallet.balance); }

  /* ================= B) inventory + timers ================= */
  const grantTimed = (uid, name)=>CodisInventory.grant({ uid:uid, name:name, rarity:'C', rarityName:'عادية', rarityTone:'c', rarityOrder:1, room:'tasks', source:'store', coinValue:200, paid:200 });
  const it = grantTimed('own|tm1', 'ساعة سوشل ميديا'); T('timed reward granted', !!it);
  T('before use: sellable', CodisEconomy.sell && CodisEconomy.sellPlan(['own|tm1']).list.length === 1);
  const r1 = codisRewardTimerStart('own|tm1'); T('timer started once', r1.ok && !r1.existed);
  const again = codisRewardTimerStart('own|tm1'); T('second start returns the SAME timer (no duplicate)', again.ok && again.existed && CodisTimers.all().filter(t=>t.ref === 'own|tm1').length === 1);
  T('running: single sell refused (inuse)', CodisEconomy.sell('own|tm1').reason === 'inuse');
  T('running: bulk sell skips it', CodisEconomy.sellPlan(['own|tm1']).list.length === 0 && CodisEconomy.sellMany(['own|tm1']).ok === false);
  { grantTimed('own|dupA', 'مكافأة مكررة'); grantTimed('own|dupB', 'مكافأة مكررة'); grantTimed('own|tm2', 'ساعة سوشل ميديا'); codisRewardTimerStart('own|tm2');
    T('running: not offered in the duplicates sale', !CodisEconomy.dupPlan().uids.some(u=>/tm/.test(u))); }
  T('running: UI offers no sell for it (disabled) and shows the countdown', (()=>{ const h = codisOwnUseBtnHtml(CodisInventory.get('own|tm1'), 'own|tm1', false); return /data-tmr-end/.test(h); })());
  const tm = CodisTimers.active('reward', 'own|tm1'); CodisTimers._shift(tm.id, -2 * 3600e3);
  /* failure while completing: markUsed fails once */
  const real = CodisEconomy.markUsed; let failures = 1; CodisEconomy.markUsed = u=>{ if(failures-- > 0) return { ok:false, reason:'save' }; return real(u); };
  CodisTimers.tick();
  const t1 = CodisTimers.all().find(t=>t.id === tm.id);
  T('timer ended but completion failed → state done, NOT yet confirmed (fin=false)', t1.state === 'done' && t1.fin === false);
  T('…and the reward is STILL locked against selling', CodisEconomy.sell('own|tm1').reason === 'inuse' && CodisInventory.get('own|tm1').status === 'owned');
  CodisTimers.tick();
  T('retry completes it exactly once → used', CodisInventory.get('own|tm1').status === 'used' && CodisTimers.all().find(t=>t.id === tm.id).fin === true);
  CodisEconomy.markUsed = real;
  T('after completion: cannot be sold', CodisEconomy.sell('own|tm1').reason === 'used');
  T('after completion: timer cannot be restarted', codisRewardTimerStart('own|tm1').ok === false);
  T('after completion: cannot be marked used again', CodisEconomy.markUsed('own|tm1').ok === false);
  T('inventory screen: «استخدام» (primary) comes before «بيع» (secondary)', (()=>{ grantTimed('own|plain1', 'مكافأة عادية'); const h = econInventoryHtml(), a = h.indexOf('own-go'), b = h.indexOf('own-sell'); return a > 0 && b > a && /<span>استخدام<\/span>/.test(h) && /btn btn-primary own-use own-go/.test(h) && /btn btn-secondary own-sell/.test(h); })());
  T('timed reward button reads «ابدأ · المدة» (starts the timer, shows its length)', /ابدأ · ساعة/.test(codisOwnUseBtnHtml({ uid:'zz', name:'ساعة قراءة' }, 'zz', false)));
  { const saved = JSON.parse(JSON.stringify(data.codisTimers)); T('timer state survives save/reload (absolute endsAt + fin flag persisted)', saved.items.every(t=>typeof t.endsAt === 'number') && saved.items.some(t=>t.fin === true)); }

  /* ================= C) sync loop against an in-page fake backend ================= */
  const hasCfg = CodisAccount.configured;
  T('backend configured in this test page (override)', hasCfg);
  if(hasCfg){
    const uid = 'u-test-1', S = CodisAccount.state;
    const b64u = o=>btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    const jwt = b64u({ alg:'none' }) + '.' + b64u({ sub:uid, email:'t@test', exp:Math.floor(Date.now() / 1000) + 7200 }) + '.sig';
    S.session = { access_token:jwt, refresh_token:'r', expires_at:Date.now() + 7200e3 }; S.user = { id:uid, email:'t@test', name:'', avatar:'' };
    sessionStorage.setItem('codis_reload_n', '3');   /* يمنع إعادة التحميل داخل الاختبار (تُسجَّل كخطأ إعادة تحميل بدل أن تقتل الصفحة) */
    const SV = { row:null, online:true, calls:[], failNext:0 };
    const realFetch = window.fetch.bind(window);
    window.fetch = async (url, o)=>{
      url = String(url);
      if(url.indexOf('127.0.0.1:8766/rest/v1') < 0 && url.indexOf('127.0.0.1:8766/auth') < 0 && url.indexOf('127.0.0.1:8766/storage') < 0) return realFetch(url, o);
      if(!SV.online) throw new TypeError('offline');
      const J = (obj, st)=>new Response(JSON.stringify(obj), { status:st || 200, headers:{ 'Content-Type':'application/json' } });
      if(/\/rest\/v1\/progress\?/.test(url)) return J(SV.row ? [SV.row] : []);
      if(/\/rest\/v1\/rpc\/save_progress/.test(url)){
        const b = JSON.parse(o.body); SV.calls.push(b.p_base_version);
        if(SV.failNext > 0){ SV.failNext--; throw new TypeError('dropped'); }
        const ver = SV.row ? SV.row.version : 0;
        if(b.p_base_version !== ver) return J({ ok:false, conflict:true, version:ver, data:SV.row ? SV.row.data : null, updated_at:SV.row ? SV.row.updated_at : null });
        SV.row = { data:b.p_data, version:ver + 1, updated_at:new Date().toISOString() }; return J({ ok:true, version:SV.row.version });
      }
      if(/\/rest\/v1\/rpc\/push_/.test(url)) return J(null);
      return J([], 200);
    };
    const meta = ()=>CodisAccount.meta(), setMeta = m=>localStorage.setItem('codis_sync_meta', JSON.stringify(m));
    const waitSync = async (ms)=>{ const t0 = Date.now(); while(Date.now() - t0 < ms){ if(!meta().dirty && S.status === 'synced') return true; await sleep(60); } return false; };
    setMeta({ owner:uid, base:0, dirty:true, lastSync:0, changedAt:Date.now() });

    /* 1) first push (account empty) */
    CodisAccount.syncNow(); T('first sync uploads and marks synced', await waitSync(4000) && !!SV.row && SV.row.version === 1, JSON.stringify([meta(), S.status]));
    T('base snapshot stored locally after a confirmed upload', !!(await CodisAccount._test.loadBase(uid)));

    /* 2) offline edits: persisted locally, status says "saved on device, waiting" */
    SV.online = false; const bal0 = data.wallet.balance; CodisWallet.adjust(25, 'offline-1'); CodisWallet.adjust(5, 'offline-2');
    T('offline edit: saved locally + flagged pending (not claimed as account-saved)', meta().dirty === true && JSON.parse(localStorage.getItem(STORE_KEY)).wallet.balance === bal0 + 30 && ['pending', 'offline'].indexOf(S.status) !== -1, S.status);
    await sleep(300); await CodisLocalDB.flush(); const w = await CodisLocalDB.get('work');
    T('offline edit mirrored to IndexedDB (survives localStorage loss)', !!w && JSON.parse(w.json).wallet.balance === bal0 + 30 && w.owner === uid);
    T('status labels are distinct for "device" vs "account"', CodisAccount.LABELS.pending !== CodisAccount.LABELS.synced && /الجهاز/.test(CodisAccount.LABELS.offline) && /الحساب/.test(CodisAccount.LABELS.synced));

    /* 3) back online → automatic upload, once */
    SV.online = true; SV.calls.length = 0; window.dispatchEvent(new Event('online'));
    T('connection returns → uploads automatically (no click)', await waitSync(5000) && SV.row.data.wallet.balance === bal0 + 30, JSON.stringify([SV.row && SV.row.data.wallet.balance, S.status, SV.calls]));
    T('uploaded exactly once (no duplicate request storm)', SV.calls.length === 1, SV.calls.join());

    /* 4) the network drops DURING the upload → retried, no duplicate effect */
    CodisWallet.adjust(7, 'during-upload'); SV.failNext = 1; SV.calls.length = 0; CodisAccount.syncNow(); await sleep(400);
    T('upload dropped mid-flight: change still pending locally', meta().dirty === true);
    SV.online = true; window.dispatchEvent(new Event('online')); const okRetry = await waitSync(8000);
    T('…and completes on retry with the amount counted once', okRetry && SV.row.data.wallet.balance === bal0 + 37, SV.row && SV.row.data.wallet.balance);

    /* 5) another device changed the account while this one was offline → merged, nothing lost, no dialog */
    const before = cl(SV.row.data); SV.online = false; CodisWallet.adjust(11, 'dev-A');
    const remote = cl(before); remote.wallet.balance += 100; remote.wallet.transactions.push(tx('devB-1', 'ADMIN_ADJUSTMENT', 100, '')); remote.inventory.items.push({ uid:'own|devB', status:'owned', name:'من الجهاز الثاني', rarity:'C', rarityName:'ع', rarityTone:'c', rarityOrder:1, room:'tasks', coinValue:10, acquiredAt:new Date().toISOString(), statusAt:new Date().toISOString(), source:'store', sourceRef:'', scope:'', paid:null });
    SV.row = { data:remote, version:SV.row.version + 1, updated_at:new Date().toISOString() }; SV.online = true; confirms = 0;
    window.dispatchEvent(new Event('online')); await sleep(1500);
    const srv = SV.row.data;
    T('conflict resolved automatically: account now holds BOTH devices\' balance changes', srv.wallet.balance === before.wallet.balance + 100 + 11, srv.wallet.balance + ' vs ' + (before.wallet.balance + 111));
    T('…and both devices\' items/transactions', srv.inventory.items.some(x=>x.uid === 'own|devB') && srv.wallet.transactions.some(t=>t.id === 'devB-1') && srv.wallet.transactions.some(t=>/dev-A/.test(t.reason)));
    T('no choice dialog was shown', confirms === 0 && !document.querySelector('.cd-ov:not(.stk-ov):not(.gs-ov)'));
    T('device copy was adopted into local storage (account is the source of truth)', JSON.parse(localStorage.getItem(STORE_KEY)).wallet.balance === srv.wallet.balance);

    /* 6) account isolation: another owner's pending changes are parked under THEIR id and never adopted */
    sessionStorage.setItem('codis_reload_n', '3'); setMeta({ owner:'u-other', base:3, dirty:true, lastSync:0, changedAt:Date.now() }); const mark = JSON.parse(localStorage.getItem(STORE_KEY)).wallet.balance;
    SV.online = true; await CodisAccount.syncNow(); await sleep(600);
    const stash = JSON.parse(localStorage.getItem('codis_acct_u-other') || 'null');
    T('another account\'s unsynced changes are parked under its own id (not merged into this account)', !!stash && stash.meta.owner === 'u-other' && SV.row.data.wallet.balance !== undefined);
    localStorage.removeItem('codis_acct_u-other');
    SV.online = false;
    window.fetch = realFetch;
  }
  const failed = out.filter(r=>!r.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
