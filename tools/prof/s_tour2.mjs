// Action layers (SHOT prefix): sign-in gate, store item detail, purchase scene, box opening ritual, confirm dialog.
export default async function(c){
  const P = process.env.SHOT || 'tour2';
  if(process.env.THEME){ await c.load(); await c.evaluate(`localStorage.setItem('codis_theme_v1', '${process.env.THEME}'); 1`); }
  await c.load(); await c.sleep(1800);
  await c.screenshot(P + '_gate.png');
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`data.wallet.balance = 9000; saveData(); 1`); await c.load(); await c.sleep(2500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  const shot = async (n, ms = 700)=>{ await c.sleep(ms); await c.screenshot(P + '_' + n + '.png'); };
  await c.evaluate(`window.__cf = codisConfirm; codisConfirm = async()=>true; 1`);
  await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  const id = await c.evaluate(`(data.settings.rewardItems.find(x=>x.enabled !== false) || {}).id`);
  await c.evaluate(`econOpenDetail(${JSON.stringify(id)})`); await shot('detail', 1200);
  await c.evaluate(`econBuy(${JSON.stringify(id)})`, false); await shot('buy1', 900); await shot('buy2', 1600); await shot('buy3', 2500);
  await c.evaluate(`(()=>{ document.querySelectorAll('.bcx button, .bcx [data-a]').forEach(b=>{ if(/تخزين|خزّن|إغلاق|لاحق/.test(b.textContent)) b.click(); }); try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(1200);
  const tier = await c.evaluate(`econBoxTierIds()[0]`);
  await c.evaluate(`econBuyBox(${JSON.stringify(tier)})`, false); await c.sleep(3500);
  await c.evaluate(`econBoxOpenFor(${JSON.stringify(tier)})`); await shot('box1', 1200);
  await c.evaluate(`(()=>{ const s = document.querySelector('.bx-stage, .cb-idle, .bx-open'); if(s) s.click(); })()`); await shot('box2', 2500); await shot('box3', 3000);
  await c.evaluate(`(()=>{ try{ econBoxClose(); }catch(e){} try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(800);
  await c.evaluate(`window.__cf({ title:'حذف المكافأة؟', message:'راح تنحذف المكافأة من القائمة.', danger:true, okText:'حذف' })`, false); await shot('confirm');
}
