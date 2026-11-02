// While scrolling the store (fast swipes), sample cards in the viewport that are still waiting for their name fit (visible unfitted names).
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly','master']; const rar = ['C','B','A','S','SS'];
    const names = ['ساعة سوشل ميديا','تطلب أكل تحبه','سفرة ثلاثة أيام للمنتجع الكبير مع العائلة كلها','فلم بالسينما','The','1','مكافأة باسم طويل جداً جداً حتى نشوف شلون يلتف ويصغر الخط','iPhone 15 Pro Max','نص ساعة مشي','عشاء'];
    for(let i = 0; i < 60; i++) R.push({ id:'pf_' + i, name:names[i % names.length], rarity:rar[i % 5], room:rooms[i % 4], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  await c.evaluate(`econOpenStore()`); await c.sleep(600);
  await c.evaluate(`(()=>{ window.__uf = { samples:0, maxVisibleWaiting:0, overflowSeen:0, cv:${'typeof codisCvOK'} === 'undefined' ? null : codisCvOK }; const tick = ()=>{ const vh = innerHeight; let w = 0, ov = 0;
      document.querySelectorAll('#eco-store-body .rwc').forEach(r=>{ const b = r.getBoundingClientRect(); if(b.bottom < 0 || b.top > vh || !b.width) return; if(r.classList.contains('fit-wait')) w++;
        r.querySelectorAll('.rwc-name, .wkc-name, .pnc-name, .pwc-name, .mwc-name').forEach(box=>{ const t = box.firstElementChild; if(t && box.clientHeight && (t.offsetHeight > box.clientHeight + 1 || t.scrollWidth > box.clientWidth + 1)) ov++; }); });
      __uf.samples++; __uf.maxVisibleWaiting = Math.max(__uf.maxVisibleWaiting, w); __uf.overflowSeen = Math.max(__uf.overflowSeen, ov); if(__uf.samples < 400) setTimeout(tick, 50); }; tick(); return 1; })()`);
  for(let i = 0; i < 8; i++){ await c.swipe(200, 760, 120, 8); await c.sleep(120); }
  await c.sleep(1500);
  console.log(JSON.stringify(await c.evaluate(`window.__uf`)));
}
