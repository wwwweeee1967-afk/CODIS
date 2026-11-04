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
await b.close(); console.log(bad ? bad + ' FAILED' : 'ALL BOOTS OK'); process.exit(bad ? 1 : 0);
