// Visual tour (SHOT env = output prefix): seeds a realistic plan/learn/habits/rewards through the real UI, then screenshots
// every room, settings sub-page, store, notification center, confirm dialog, toast and the add-habit form.
// node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_tour.mjs --cpu 1
export default async function(c){
  const P = process.env.SHOT || 'tour';
  const ONLY = (process.env.ONLY || '').split(',').filter(Boolean);
  const want = n=>!ONLY.length || ONLY.some(o=>n.startsWith(o));
  if(process.env.THEME){ await c.load(); await c.evaluate(`localStorage.setItem('codis_theme_v1', '${process.env.THEME}'); 1`); }
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  await c.evaluate(`(async()=>{ const sleep = ms=>new Promise(r=>setTimeout(r, ms));
    codisConfirm = async()=>true; try{ CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{}; }catch(e){}
    const btn = (root, txt)=>[...document.querySelectorAll(root + ' button')].find(b=>b.getClientRects().length && b.innerText.includes(txt));
    if(!data.weeks[currentWeekId()]){
      document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(500);
      const b = btn('#page-planning', 'إضافة خطة'); if(b){ b.click(); await sleep(400); }
      const ti = document.getElementById('plan-tasks-input'); ti.value = '1- 14 صفحة مراجعة\\n2- !تقرير المبيعات\\n3- اتصال بالعائلة\\n4- ساعة رياضة\\n5- ترتيب الغرفة\\n6- قراءة 20 صفحة\\n7- غسل السيارة\\n8- دفع الفواتير'; ti.dispatchEvent(new Event('input', { bubbles:true }));
      const li = document.getElementById('plan-learn-input'); li.value = '1- درس الرياضيات\\n2- فصل الفيزياء\\n3- تمارين الإنجليزي\\n4- مراجعة الكيمياء'; li.dispatchEvent(new Event('input', { bubbles:true }));
      switchWriteTab('tasks'); distributePlan(); await sleep(700);
    }
    if(!data.habits.build.length){
      const add = (mode, text, type)=>{ habitMode = mode; newHabitType = type; const i = document.getElementById('new-habit-text'); if(i){ i.value = text; addHabit(); } };
      try{ add('build', 'شرب ماء كل صباح', HABIT_TYPES.build[0][0]); add('build', 'رياضة أسبوعية', HABIT_TYPES.build[HABIT_TYPES.build.length - 1][0]); add('quit', 'السكائر', HABIT_TYPES.quit[0][0]); }catch(e){ console.log('habit seed', e); }
    }
    const R = data.settings.rewardItems || [];
    if(R && !R.some(r=>String(r.id).startsWith('tour_'))){ const rar = ['C','B','A','S','SS'], rooms = ['daily','weekly','monthly'];
      for(let i = 0; i < 15; i++) R.push({ id:'tour_' + i, name:['تطلب أكل تحبه','ساعة سوشل ميديا','سفرة للمنتجع','فلم بالسينما','عشاء برّه'][i % 5], rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:['lamb_mandi','cafe_front',null][i % 3], weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' }); }
    data.wallet.balance = 2450; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  const freeze = `document.getAnimations().forEach(a=>{ try{ if(a.effect && a.effect.getTiming().iterations !== Infinity) a.finish(); else a.pause(); }catch(e){} })`;
  const shot = async(n)=>{ await c.sleep(450); await c.evaluate(freeze); await c.sleep(120); await c.screenshot(P + '_' + n + '.png'); };
  const scrollShot = async(n)=>{ await shot(n); const more = await c.evaluate(`(()=>{ const s = [...document.querySelectorAll('.main, .page.active, .settings-page.active, #eco-store-body, .settings-pages')].find(e=>e.scrollHeight > e.clientHeight + 40 && getComputedStyle(e).overflowY !== 'visible'); if(!s) { if(document.scrollingElement.scrollHeight > innerHeight + 40){ scrollTo(0, innerHeight * .85); return 1; } return 0; } s.scrollTop = s.clientHeight * .85; return 1; })()`); if(more) await shot(n + '_b'); await c.evaluate(`(()=>{ document.querySelectorAll('*').forEach(e=>{ if(e.scrollTop) e.scrollTop = 0; }); scrollTo(0,0); })()`); };
  for(const p of ['tasks', 'learn', 'habits', 'planning', 'settings']){
    if(!want(p)) continue;
    await c.evaluate(`navigateToPage('${p}')`); await c.sleep(900); await scrollShot(p);
  }
  if(want('habitadd')){ await c.evaluate(`navigateToPage('habits')`); await c.sleep(700); await c.evaluate(`(()=>{ try{ setAddOpen(true); }catch(e){} })()`); await c.sleep(500); await shot('habitadd'); await c.evaluate(`(()=>{ try{ setAddOpen(false, { silent:true }); }catch(e){} })()`); }
  for(const s of ['account', 'rewards', 'sound', 'notifications', 'app-lock', 'archive', 'eco-log', 'appearance']){
    if(!want('set-' + s)) continue;
    await c.evaluate(`navigateToPage('settings')`); await c.sleep(600);
    await c.evaluate(`openSettingsCategory('${s}')`); await c.sleep(900); await scrollShot('set-' + s);
    await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(500);
  }
  if(want('store')){ await c.evaluate(`navigateToPage('tasks')`); await c.sleep(400); await c.evaluate(`econOpenStore()`); await c.sleep(2500);
    for(let i = 0; i < 4; i++){ await c.evaluate(`econStoreScroller().scrollTop = ${i * 760}`); await c.sleep(600); await shot('store_' + i); }
    await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(600); }
  if(want('notif')){ await c.evaluate(`openNotifCenter()`); await c.sleep(900); await shot('notif'); await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(600); }
  if(want('confirm')){ await c.evaluate(`navigateToPage('tasks')`); await c.sleep(500); await c.evaluate(`(()=>{ const f = window.__codisConfirmOrig; })()`);
    await c.evaluate(`(()=>{ const d = document.querySelector('#confirm-modal, .confirm-modal, [id*=confirm]'); return !!d; })()`); }
  if(want('toast')){ await c.evaluate(`navigateToPage('tasks')`); await c.sleep(500); await c.evaluate(`showToast('تم حفظ الخطة بنجاح', 'var(--success)')`); await c.sleep(500); await c.screenshot(P + '_toast.png'); }
}
