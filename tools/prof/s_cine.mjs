// Deterministic purchase-cinema screenshots (seeded Math.random, all animations frozen at fixed times) for pixel comparison (SHOT env).
export default async function(c){
  await c.send('Page.addScriptToEvaluateOnNewDocument', { source:`(()=>{ let x = 123456789; Math.random = ()=>{ x ^= x << 13; x ^= x >>> 17; x ^= x << 5; return ((x >>> 0) % 1e9) / 1e9; }; })();` });
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ data.settings.rewardItems.push({ id:'pf_big', name:'سفرة ثلاثة أيام', rarity:'SS', room:'monthly', enabled:true, storePrice:33600, coinValue:null, stickerId:null, weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' }); data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  await c.evaluate(`window.codisConfirm = async()=>true; econBuy('pf_big'); 1`);
  for(const t of [700, 1600, 3000]){
    await c.sleep(t === 700 ? 700 : (t === 1600 ? 900 : 1400));
    await c.evaluate(`(()=>{ document.getAnimations().forEach(a=>{ try{ a.pause(); const d = a.effect.getComputedTiming(); a.currentTime = Math.min(${t}, (d.endTime === Infinity ? ${t} : d.endTime)); }catch(e){} }); return 1; })()`);
    await c.sleep(300);
    await c.screenshot(process.env.SHOT + '_t' + t + '.png');
    console.log('rays', JSON.stringify(await c.evaluate(`(()=>{ const r = document.querySelector('.bcx-rays'); if(!r) return null; const b = r.getBoundingClientRect(); return [Math.round(r.offsetWidth), Math.round(b.width)]; })()`)));
    await c.evaluate(`document.getAnimations().forEach(a=>{ try{ a.play(); }catch(e){} })`);
  }
}
