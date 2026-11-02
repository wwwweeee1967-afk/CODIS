// CODIS performance guard (CODIS-BUTTER). Fails if a change brings back the causes of mobile jank/crashes.
// Run (serve the project root first, e.g. `py -3 -m http.server 8766`):
//   node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tests/perf_guard.mjs --cpu 4
// Emulates an installed iPhone web app (iPhone UA, DPR3, navigator.standalone, CPU ×4). Budgets are for that throttled CPU.
const BUDGET = {
  storeNodes: 3200,          // 4717 before lazy card backs; each card back must stay in <template> until flipped
  storeReopenWorstFrame: 600, // ms at CPU×4; was ~1800 before keep-alive + per-tile content-visibility
  decodedStoreImageMB: 30,    // unique decoded bitmaps in the store; was 51 with full-size art in the grid
};
export default async function(c){
  const fail = [], ok = [];
  const check = (name, cond, info)=>(cond ? ok : fail).push(name + ' — ' + info);
  await c.send('Page.addScriptToEvaluateOnNewDocument', { source:`try{ Object.defineProperty(navigator, 'standalone', { get:()=>true }); }catch(e){}` });
  await c.load(); await c.sleep(2000);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2000); }
  // 1) nothing may make touch scrolling wait for JavaScript
  const blocking = [];
  for(const tgt of ['document', 'window', 'document.body', 'document.documentElement']){
    const o = await c.send('Runtime.evaluate', { expression:tgt, returnByValue:false });
    const l = await c.send('DOMDebugger.getEventListeners', { objectId:o.result.objectId });
    l.listeners.filter(x=>(x.type === 'touchstart' || x.type === 'touchmove') && !x.passive).forEach(x=>blocking.push(tgt + ' ' + x.type + ' line ' + (x.lineNumber + 1)));
  }
  check('no scroll-blocking touch listeners (installed app)', blocking.length === 0, blocking.join(', ') || 'none');
  // 2) store size / images / reopen smoothness with realistic data
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pg_' + i, name:'مكافأة ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(3000);
  await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  await c.evaluate(`(async()=>{ const sc = econStoreScroller(); for(let y = 0; y < sc.scrollHeight; y += 300){ sc.scrollTop = y; await new Promise(r=>setTimeout(r, 100)); } sc.scrollTop = 0; return 1; })()`); await c.sleep(1500);
  const st = await c.evaluate(`(()=>{ const b = document.getElementById('eco-store-body'); const m = new Map(); Array.prototype.forEach.call(b.querySelectorAll('img'), i=>{ if(i.naturalWidth) m.set(i.currentSrc || i.src, i.naturalWidth * i.naturalHeight); });
    return { nodes:b.getElementsByTagName('*').length, imgMB:Math.round([...m.values()].reduce((a, v)=>a + v * 4, 0) / 1048576) }; })()`);
  check('store DOM size', st.nodes <= BUDGET.storeNodes, st.nodes + ' nodes (budget ' + BUDGET.storeNodes + ')');
  check('store decoded image memory', st.imgMB <= BUDGET.decodedStoreImageMB, st.imgMB + ' MB (budget ' + BUDGET.decodedStoreImageMB + ')');
  await c.evaluate(`CodisNav.back()`); await c.sleep(1200);
  await c.snap('before reopen');
  await c.evaluate(`econOpenStore()`); await c.sleep(2000);
  const r = await c.evaluate(`(()=>{ const f = (window.__fr || []).slice(); return f.length ? Math.round(Math.max(...f)) : -1; })()`);
  check('store reopen worst frame', r >= 0 && r <= BUDGET.storeReopenWorstFrame, r + ' ms (budget ' + BUDGET.storeReopenWorstFrame + ')');
  console.log('PERF GUARD ' + (fail.length ? 'FAILED' : 'PASSED'));
  ok.forEach(x=>console.log('  ok   ' + x)); fail.forEach(x=>console.log('  FAIL ' + x));
}
