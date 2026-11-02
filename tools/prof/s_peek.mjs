// Peek screenshots per card kind (SHOT env prefix): finished animation, frozen; reports card box vs viewport and name overflow.
export default async function(c){
  const P = process.env.SHOT;
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(()=>{ const R = data.settings.rewardItems; const rooms = ['daily','weekly','monthly','master']; const rar = ['C','B','A','S','SS'];
    const names = ['مشاهدة مقطع مع الاكل 📽️','تطلب أكل تحبه','سفرة ثلاثة أيام للمنتجع الكبير مع العائلة كلها','فلم بالسينما'];
    for(let i = 0; i < 16; i++) R.push({ id:'pf_' + i, name:names[i % names.length], rarity:rar[i % 5], room:rooms[i % 4], enabled:true, storePrice:null, coinValue:null, stickerId:null, weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' });
    data.wallet.balance = 800000; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  const kinds = await c.evaluate(`(()=>{ const seen = {}, out = []; document.querySelectorAll('#eco-store-body [role="list"] > *').forEach((t, i)=>{ const k = t.className.split(' ').slice(0, 2).join('.') + (t.querySelector('.rwc-mtc, .mtc, .mwc, .scx-hc') ? '+' + (t.querySelector('.scx-hc') ? 'holiday' : 'monthly') : ''); if(seen[k] || t.getBoundingClientRect().height < 40) return; seen[k] = 1; t.setAttribute('data-pk', out.length); out.push(k); }); return out; })()`);
  console.log('kinds', JSON.stringify(kinds));
  for(let i = 0; i < kinds.length; i++){
    await c.press('[data-pk="' + i + '"]', 650); await c.sleep(1400);
    const info = await c.evaluate(`(()=>{ document.getAnimations().forEach(a=>{ try{ if(a.effect && a.effect.getTiming().iterations !== Infinity) a.finish(); }catch(e){} });
      const pk = document.querySelector('.peek .is-peek'); if(!pk) return { open:false }; const b = pk.getBoundingClientRect(), vw = innerWidth, vh = innerHeight;
      const over = []; pk.querySelectorAll('.rwc-name, .wkc-name, .mwc-name, .scx-plate, .cfp-name').forEach(box=>{ const t = box.firstElementChild; if(t && box.clientHeight && (t.offsetHeight > box.clientHeight * 1.02 + 1 || t.scrollWidth > box.clientWidth + 1)) over.push(box.className.split(' ')[0]); });
      return { open:true, mode:pk.style.zoom ? 'zoom' : 'width', box:[Math.round(b.left), Math.round(b.top), Math.round(b.right), Math.round(b.bottom)], inside:b.left >= -1 && b.right <= vw + 1 && b.top >= -1 && b.bottom <= vh + 1, nameOverflow:over }; })()`);
    console.log(kinds[i], JSON.stringify(info));
    await c.evaluate(`document.getAnimations().forEach(a=>{ try{ a.pause(); }catch(e){} })`);
    await c.screenshot(P + '_peek' + i + '.png');
    await c.evaluate(`CodisCardPeek.close()`); await c.sleep(900);
  }
}
