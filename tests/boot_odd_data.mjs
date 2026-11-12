/* CODIS boot test with odd/legacy/hostile saved data — real WebKit (the iPhone engine) AND Chromium-free.
   Guards the whole class "the app dies at load for ONE user because of something in THEIR saved data" (3.17.0 TDZ crash: any account with a saved multi-sticker list 'a+b' could not open the app).
   Needs: npm i playwright-core@1.49.1 (in a scratch folder) + installed webkit (see CLAUDE.md 3.17.1).
   Run:  node tests/boot_odd_data.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html        (exit 1 on any page error / failed boot) */
import { webkit, devices } from 'playwright-core';
const url = process.argv[2] || 'http://127.0.0.1:8766/app/CODIS_FINAL.html';
const K = 'life_organizer_data_v1';
const b = await webkit.launch(); let bad = 0;
async function boot(name, mutate){
  const ctx = await b.newContext({ ...devices['iPhone 12'] }); const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(url); await p.waitForTimeout(2500);
  if(mutate){ await p.evaluate(`(${mutate})(${JSON.stringify(K)})`); errs.length = 0; await p.reload(); await p.waitForTimeout(3000); }
  const r = await p.evaluate(() => { try{ return { ok: !!CodisLimits && !!CodisEconomy && typeof codisRewardCardHtml === 'function', n: (data.settings.rewardItems || []).length }; }catch(e){ return { ok:false, why:e.message }; } });
  const ok = r.ok && !errs.length; if(!ok) bad++;
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (ok ? ' (' + r.n + ' rewards)' : ' ' + JSON.stringify({ r, errs: errs.slice(0, 2) })));
  await ctx.close();
}
const seed = (vals) => `(K)=>{ const d = JSON.parse(localStorage.getItem(K) || '{}'); d.settings = d.settings || {}; const L = d.settings.rewardItems = d.settings.rewardItems || [];
  while(L.length < 6) L.push({ id:'seed_' + L.length, name:'م' + L.length, rarity:'C', weight:10, room:'tasks', enabled:true });
  const V = ${JSON.stringify(vals)}; L.forEach((x, i) => { x.stickerId = V[i % V.length]; });
  d.inventory = d.inventory || { items: [] }; (d.inventory.items = d.inventory.items || []).push({ uid:'own|t|1', rewardId:null, name:'x', rarity:'C', rarityName:'C', rarityTone:'c', rarityOrder:0, room:'tasks', stickerId:V[0], status:'owned', state:'owned' });
  localStorage.setItem(K, JSON.stringify(d)); }`;
await boot('fresh guest');
await boot("stickerId '' (empty)", seed(['']));
await boot('saved multi-sticker list (the 3.17.0 crash: fresh page load read it before CODIS_STICKER_MAX existed)', seed(['falafel+tea_glass', 'kunafa+falafel+tea_glass']));
await boot('single / list / garbage mix', seed(['falafel', 'falafel+tea_glass+kunafa', 'bad id!', null, '', '+', 'a+b+c+d+e']));
await boot('numbers / objects / arrays instead of strings', seed([0, 5, {}, [], ['falafel'], true]));
await boot('very long ids', seed(['x'.repeat(5000), 'falafel+'.repeat(500)]));
/* CODIS-FINANCE (3.28.0): data.finance / مكافآت تلقائية بقيم مشوّهة لا تُسقط الإقلاع (التطبيع وقت التحميل لا يرمي) */
const fin = (v) => `(K)=>{ const d = JSON.parse(localStorage.getItem(K) || '{}'); d.finance = ${JSON.stringify(v)}; localStorage.setItem(K, JSON.stringify(d)); }`;
await boot('finance: null / string / number / array', fin(null)); await boot('finance: string', fin('x')); await boot('finance: array', fin([1, 2])); await boot('finance: number', fin(5));
await boot('finance: ledger garbage', fin({ ledger:[null, 1, 'x', { id:5 }, { id:'a', type:'EXPENSE', amount:'abc' }, { id:'b', type:'DEPOSIT', amount:1e30, date:'bad' }], salary:{ rules:'x' }, fx:{ rate:'7' }, fxLog:{ }, cats:[{}] }));
await boot('finance: huge ledger', fin({ setup:{ done:true }, ledger:Array.from({ length:3000 }, (_, i) => ({ id:'e' + i, type:'DEPOSIT', amount:i + 1, date:'2026-01-01', at:'2026-01-01T00:00:00Z', desc:'x' })) }));
const finItems = (v) => `(K)=>{ const d = JSON.parse(localStorage.getItem(K) || '{}'); d.settings = d.settings || {}; const L = d.settings.rewardItems = d.settings.rewardItems || []; L.push({ id:'fin_t', name:'ت', rarity:'C', weight:10, room:'tasks', enabled:true, fin:${JSON.stringify(v)} }); L.push({ id:'fin_t2', name:'ت٢', rarity:'C', weight:0, room:'habits', enabled:true, fin:${JSON.stringify(v)}, variantOf:'nope' });
  d.inventory = d.inventory || { items: [] }; (d.inventory.items = d.inventory.items || []).push({ uid:'own|t|fin', rewardId:'fin_t', name:'x', rarity:'C', rarityName:'C', rarityTone:'c', rarityOrder:1, room:'tasks', status:'owned', fin:${JSON.stringify(v)} }); localStorage.setItem(K, JSON.stringify(d)); }`;
await boot('fin item: garbage values', finItems({ v:1, kind:'financial', iqd:'x', card:5 })); await boot('fin item: valid financial', finItems({ v:1, kind:'financial', iqd:2000, card:'daily_C', dom:'food', coin:50 })); await boot('fin item: valid time', finItems({ v:1, kind:'time', minutes:90, card:'fx_rs_important' })); await boot('fin item: array/number/null', finItems([1])); await boot('fin item: null', finItems(null));
/* CODIS-V44 (3.31.0): حالة الصندوق المجاني + مكافآت بعلامة freebox مشوّهة لا تُسقط الإقلاع */
const fbState = (v) => `(K)=>{ const d = JSON.parse(localStorage.getItem(K) || '{}'); d.economyState = d.economyState || {}; d.economyState.freeBox = ${JSON.stringify(v)}; localStorage.setItem(K, JSON.stringify(d)); }`;
for (const v of [null, 'x', 5, [], { at: 12, n: 'q' }, { at: 'zzz', n: -1 }, { at: '2999-01-01T00:00:00Z', n: 9e9 }, { at: '2026-11-01T00:00:00.000Z', n: 3 }]) await boot('freeBox state: ' + JSON.stringify(v), fbState(v));
const fbItems = (list) => `(K)=>{ const d = JSON.parse(localStorage.getItem(K) || '{}'); d.settings = d.settings || {}; const L = d.settings.rewardItems = d.settings.rewardItems || []; ${JSON.stringify(list)}.forEach(x => L.push(x)); localStorage.setItem(K, JSON.stringify(d)); }`;
await boot('freebox items: orphan flag / bad fin / wrong card / valid', fbItems([
  { id: 'fb_o', name: 'يتيم', rarity: 'C', weight: 10, room: 'tasks', enabled: true, freebox: true },
  { id: 'fb_g', name: 'تالف', rarity: 'C', weight: 10, room: 'learn', enabled: true, freebox: true, fin: { v: 1, kind: 'financial', iqd: 'x', card: 'free_box' } },
  { id: 'fb_w', name: 'بطاقة اخرى', rarity: 'C', weight: 10, room: 'tasks', enabled: true, freebox: true, fin: { v: 1, kind: 'time', minutes: 8, card: 'daily_C', coin: 4 } },
  { id: 'fb_v', name: 'سليم', rarity: 'ZZ', weight: 99, room: 'monthly', enabled: true, fin: { v: 1, kind: 'time', minutes: 8, card: 'free_box', coin: 4 }, stickerId: 'falafel' },
  { id: 'fb_s', name: 'نص', rarity: 'C', enabled: 'yes', freebox: 'true', fin: { v: 1, kind: 'time', minutes: 8, card: 'free_box' } }]));
await b.close(); console.log(bad ? bad + ' FAILED' : 'ALL BOOTS OK'); process.exit(bad ? 1 : 0);
