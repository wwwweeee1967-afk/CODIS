// Scenario: cold boot as a new guest → second boot (returning user with data) → store open/scroll → peek → expensive purchase cinema.
export default async function(c){
  const ms = await c.load();
  await c.sleep(1500);
  const nav = await c.evaluate(`(()=>{ const n = performance.getEntriesByType('navigation')[0]; return { dcl:Math.round(n.domContentLoadedEventEnd), load:Math.round(n.loadEventEnd), transfer:n.transferSize, decoded:n.decodedBodySize }; })()`);
  await c.snap('boot-1 (first visit)', { wallMs:ms, nav });
  const g = await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`);
  if(g){ await c.tap('#gate-guest'); await c.sleep(2500); await c.snap('after guest entry'); }
  // seed realistic heavy data (isolated test profile): many rewards + coins + owned cards
  await c.evaluate(`(async()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly']; const rar = ['C','B','A','S','SS'];
    for(let i = 0; i < 45; i++) R.push({ id:'pf_' + i, name:['ساعة سوشل ميديا','تطلب أكل تحبه','سفرة ثلاثة أيام للمنتجع الكبير','فلم بالسينما','The','1'][i % 6] + ' ' + i, rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString() });
    data.wallet.balance = 800000; saveData(); return R.length; })()`);
  await c.sleep(800);
  const ms2 = await c.load(); await c.sleep(2500);
  await c.snap('boot-2 (returning, heavy data)', { wallMs:ms2 });
  await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  await c.snap('store open');
  for(let i = 0; i < 6; i++){ await c.swipe(200, 700, 200, 14); await c.sleep(250); }
  await c.sleep(600);
  await c.snap('store scroll x6');
  await c.evaluate(`(()=>{ const t = document.querySelector('#eco-store-body .shop-card[data-id]'); t.scrollIntoView({block:'center'}); return 1; })()`); await c.sleep(400);
  await c.press('#eco-store-body .shop-card[data-id]', 700); await c.sleep(1200);
  await c.snap('peek open', { peek:await c.evaluate(`!!document.querySelector('.peek')`) });
  await c.evaluate(`CodisCardPeek.close()`); await c.sleep(900);
  await c.snap('peek closed');
  // purchase the most expensive item through the real flow (confirm auto-accepted only in this test profile)
  const bought = await c.evaluate(`(()=>{ window.codisConfirm = async()=>true; let best = null; data.settings.rewardItems.forEach(i=>{ if(i.enabled){ const p = CodisEconomy.storePrice(i); if(!best || p > best.p) best = { id:i.id, p }; } }); econBuy(best.id); return best; })()`);
  await c.sleep(1200); await c.snap('cinema t+1.2s', { bought, lv:await c.evaluate(`(document.querySelector('.bcx')||{}).className`) });
  await c.sleep(3500); await c.snap('cinema t+4.7s');
  await c.evaluate(`document.querySelector('.bcx-keep') && document.querySelector('.bcx-keep').click()`); await c.sleep(1500);
  await c.snap('after cinema closed');
}
