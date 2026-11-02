// Pixel-equivalence screenshots (SHOT env = file prefix): store at several scroll offsets, a flipped card, flip mid-animation transform samples.
export default async function(c){
  const P = process.env.SHOT;
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly','master']; const rar = ['C','B','A','S','SS'];
    const names = ['ساعة سوشل ميديا','تطلب أكل تحبه','سفرة ثلاثة أيام للمنتجع الكبير مع العائلة كلها','فلم بالسينما','The','1','مكافأة باسم طويل جداً جداً حتى نشوف شلون يلتف ويصغر الخط','iPhone 15 Pro Max','نص ساعة مشي','عشاء'];
    for(let i = 0; i < 60; i++) R.push({ id:'pf_' + i, name:names[i % names.length], rarity:rar[i % 5], room:rooms[i % 4], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  // freeze all animations at t=0 so screenshots are deterministic
  await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  await c.evaluate(`(async()=>{ const sc = econStoreScroller(); for(let y = 0; y < sc.scrollHeight; y += 300){ sc.scrollTop = y; await new Promise(r=>setTimeout(r, 120)); } sc.scrollTop = 0; return 1; })()`);
  await c.sleep(6000);
  const freeze = `document.getAnimations().forEach(a=>{ try{ a.pause(); a.currentTime = 0; }catch(e){} })`;
  const H = await c.evaluate(`econStoreScroller().scrollHeight`);
  for(let i = 0, y = 0; y < H && i < 12; i++, y += 700){ await c.evaluate(`econStoreScroller().scrollTop = ${y}`); await c.sleep(500); await c.evaluate(freeze); await c.sleep(150); await c.screenshot(P + '_s' + i + '.png'); }
  // flip a reward card and sample the animation
  await c.evaluate(`econStoreScroller().scrollTop = 0`); await c.sleep(300);
  const sel = await c.evaluate(`(()=>{ const f = document.querySelector('#eco-store-body .shop-card .cflip'); f.scrollIntoView({ block:'center' }); f.id = 'flipme'; return !!f; })()`);
  await c.sleep(300);
  const samples = await c.evaluate(`(async()=>{ const f = document.getElementById('flipme'), inn = f.querySelector('.cflip-in'), out = [];
    codisFlipToggle(f); for(const t of [0, 120, 320, 700]){ await new Promise(r=>setTimeout(r, t ? t - (out.length ? [0,120,320,700][out.length-1] : 0) : 0)); out.push(getComputedStyle(inn).transform.slice(0, 60) + ' ts=' + getComputedStyle(inn).transformStyle + ' bv=' + getComputedStyle(f.querySelector('.cflip-b')).visibility); }
    return out; })()`);
  console.log('flip samples', JSON.stringify(samples));
  await c.sleep(800); await c.evaluate(freeze); await c.screenshot(P + '_flipped.png');
  const back = await c.evaluate(`(async()=>{ const f = document.getElementById('flipme'); codisFlipToggle(f); const inn = f.querySelector('.cflip-in'); await new Promise(r=>setTimeout(r, 200)); const mid = getComputedStyle(inn).transform.slice(0, 60); await new Promise(r=>setTimeout(r, 1200)); return { mid, end:getComputedStyle(inn).transform, cls:f.className }; })()`);
  console.log('unflip', JSON.stringify(back));
}
