// Visual-equivalence check: collect every fitted inline font-size/display in the store (all cards, after all lazy fits) → JSON file (OUTFIT env).
import { writeFileSync } from 'node:fs';
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly','master']; const rar = ['C','B','A','S','SS'];
    const names = ['ساعة سوشل ميديا','تطلب أكل تحبه','سفرة ثلاثة أيام للمنتجع الكبير مع العائلة كلها','فلم بالسينما','The','1','مكافأة باسم طويل جداً جداً حتى نشوف شلون يلتف ويصغر الخط','iPhone 15 Pro Max','نص ساعة مشي','عشاء'];
    for(let i = 0; i < 60; i++) R.push({ id:'pf_' + i, name:names[i % names.length], rarity:rar[i % 5], room:rooms[i % 4], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  // visit every section so content-visibility / lazy fits complete, then wait for the idle queue
  await c.evaluate(`(async()=>{ const sc = econStoreScroller(); for(let y = 0; y < sc.scrollHeight; y += 300){ sc.scrollTop = y; await new Promise(r=>setTimeout(r, 120)); } sc.scrollTop = 0; await new Promise(r=>setTimeout(r, 400)); return 1; })()`);
  await c.sleep(9000);
  const r = await c.evaluate(`(()=>{ const out = []; document.querySelectorAll('#eco-store-body *').forEach((e, i)=>{ const fs = e.style.fontSize, d = e.style.display; if(fs || (d && e.closest('.wkc-tier'))) out.push(i + ':' + String(e.className).slice(0, 30) + ':' + fs + ':' + d); }); return { n:out.length, waits:document.querySelectorAll('#eco-store-body .fit-wait').length, list:out }; })()`);
  writeFileSync(process.env.OUTFIT, JSON.stringify(r));
  console.log('fitted', r.n, 'fit-wait left', r.waits);
}
