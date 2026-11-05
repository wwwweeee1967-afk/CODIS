// Contrast audit capture (env: SHOT=out prefix, THEME=paper|dark). For every screen/state: collects each visible text node / icon / placeholder
// (rect, computed colour, ancestor opacity, size, weight), then hides all text and screenshots, so tools/contrast_report.py can sample the REAL
// background behind each item (gradients, grain, glass included) and compute WCAG ratios.
//   THEME=paper SHOT=tmp/ct node tools/prof/cdp.mjs <url> tools/prof/s_contrast.mjs --cpu 1 --dpr 2
import { writeFileSync } from 'node:fs';
const COLLECT = `(()=>{
  const vw = innerWidth, vh = innerHeight, out = [];
  const op = e=>{ let o = 1; for(let n = e; n && n.nodeType === 1; n = n.parentElement){ const s = getComputedStyle(n); if(s.display === 'none' || s.visibility === 'hidden') return 0; o *= parseFloat(s.opacity); } return o; };
  const sel = e=>{ let s = e.tagName.toLowerCase(); if(e.id) s += '#' + e.id; else if(typeof e.className === 'string' && e.className.trim()) s += '.' + e.className.trim().split(/\\s+/).slice(0, 2).join('.');
    const p = e.parentElement; if(p){ let ps = p.tagName.toLowerCase(); if(p.id) ps += '#' + p.id; else if(typeof p.className === 'string' && p.className.trim()) ps += '.' + p.className.trim().split(/\\s+/)[0]; s = ps + ' > ' + s; } return s; };
  const clipped = (e, r)=>{ for(let n = e.parentElement; n && n !== document.body; n = n.parentElement){ const s = getComputedStyle(n); if(/(hidden|clip|auto|scroll)/.test(s.overflowX + s.overflowY)){ const b = n.getBoundingClientRect(); if(r.right < b.left || r.left > b.right || r.bottom < b.top || r.top > b.bottom) return true; } } return false; };
  const OV = [...document.querySelectorAll('.modal-overlay, .cd-ov, .codis-lock, #codis-gate, .own-sheet')].filter(o=>{ const s = getComputedStyle(o); const r = o.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > .3 && r.width > vw * .8 && r.height > vh * .5; });
  const ART = '.rwc, .wkc, .mtc, .cbk, .pcd, .scx, .pwc, .pnc, .cfp, .cflip-b, .rv, .bcx, #outcome-overlay, #codis-aura, .bk-zoom, .peek, .cb-world, .bk-world, .rwc-wrap';
  const covered = (e, r)=>{ const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + Math.min(6, r.width / 3), r.top + r.height / 2], [r.right - Math.min(6, r.width / 3), r.top + r.height / 2]];
    let hit = 0; for(const [x, y] of pts){ if(x < 0 || y < 0 || x >= vw || y >= vh) { hit++; continue; } const t = document.elementFromPoint(x, y); if(t && (e.contains(t) || t.contains(e))) hit++; } return hit === 0; };
  const push = (k, e, r, t, col)=>{ if(r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > vh || r.right < 0 || r.left > vw) return; const o = op(e); if(o < 0.05) return; if(clipped(e, r)) return; if(e.closest(ART)) return; if(OV.length && !OV.some(o=>o.contains(e))) return; if(covered(e, r)) return; const s = getComputedStyle(e);
    out.push({ k, s:sel(e), t, r:[r.left, r.top, r.width, r.height], c:col, o, fs:parseFloat(s.fontSize), fw:parseInt(s.fontWeight) || 400, tag:e.tagName.toLowerCase(), cls:(typeof e.className === 'string' ? e.className : '').slice(0, 60) }); };
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for(let n = tw.nextNode(); n; n = tw.nextNode()){
    const t = n.textContent.trim(); if(!t) continue; const e = n.parentElement; if(!e || e.closest('script,style,template,noscript')) continue;
    const s = getComputedStyle(e); if(s.display === 'none' || s.visibility === 'hidden') continue;
    const rg = document.createRange(); rg.selectNodeContents(n); const r = rg.getBoundingClientRect();
    push('text', e, r, t.slice(0, 40), s.webkitTextFillColor && s.webkitTextFillColor !== '' ? s.webkitTextFillColor : s.color);
  }
  for(const e of document.querySelectorAll('input[placeholder], textarea[placeholder]')){ if(e.value) continue; const s = getComputedStyle(e); if(s.display === 'none') continue; push('placeholder', e, e.getBoundingClientRect(), e.placeholder.slice(0, 40), getComputedStyle(e, '::placeholder').color); }
  for(const e of document.querySelectorAll('svg.ico')){ const s = getComputedStyle(e); if(s.display === 'none' || s.visibility === 'hidden') continue; let c = s.color; const sc = s.stroke; if(sc && sc !== 'none' && !sc.startsWith('url')) c = sc; push('icon', e, e.getBoundingClientRect(), e.getAttribute('data-icon') || '', c); }
  return out; })()`;
const HIDE = `(()=>{ let st = document.getElementById('__hide'); if(!st){ st = document.createElement('style'); st.id = '__hide'; document.head.appendChild(st); }
  st.textContent = '*,*::before,*::after{ color:transparent !important; -webkit-text-fill-color:transparent !important; text-shadow:none !important; caret-color:transparent !important; } ::placeholder{ color:transparent !important; -webkit-text-fill-color:transparent !important; } svg.ico, svg.ico *{ visibility:hidden !important; }'; return 1; })()`;
const UNHIDE = `(()=>{ const st = document.getElementById('__hide'); if(st) st.remove(); return 1; })()`;
export default async function(c){
  const P = process.env.SHOT || 'ct';
  if(process.env.THEME){ await c.load(); await c.evaluate(`localStorage.setItem('codis_theme_v1', '${process.env.THEME}'); 1`); }
  await c.load(); await c.sleep(1800);
  const freeze = `document.getAnimations().forEach(a=>{ try{ if(a.effect && a.effect.getTiming().iterations !== Infinity) a.finish(); else a.pause(); }catch(e){} })`;
  async function audit(n){
    await c.sleep(500); await c.evaluate(freeze); await c.sleep(150);
    const items = await c.evaluate(COLLECT);
    await c.evaluate(HIDE); await c.sleep(250); await c.screenshot(P + '_' + n + '.png');
    await c.evaluate(UNHIDE);
    writeFileSync(P + '_' + n + '.json', JSON.stringify({ theme:process.env.THEME || 'paper', name:n, dpr:Number(process.env.DPR || 2), items }));
  }
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await audit('gate'); await c.tap('#gate-guest'); await c.sleep(2500); }
  const go = async (p)=>{ await c.evaluate(`navigateToPage('${p}')`); await c.sleep(900); };
  // empty states first (fresh data)
  for(const p of ['tasks', 'learn', 'habits', 'planning']){ await go(p); await audit('empty_' + p); }
  // seed a plan, habits, rewards
  await c.evaluate(`(async()=>{ const sleep = ms=>new Promise(r=>setTimeout(r, ms)); codisConfirm = async()=>true; try{ CodisOutcomeUI.show = ()=>{}; CodisOutcomeUI.enqueue = ()=>{}; }catch(e){}
    const btn = (root, txt)=>[...document.querySelectorAll(root + ' button')].find(b=>b.getClientRects().length && b.innerText.includes(txt));
    document.querySelector('.navbtn[data-page="planning"]').click(); await sleep(500);
    const b = btn('#page-planning', 'ابدأ بناء الخطة'); if(b){ b.click(); await sleep(400); }
    const ti = document.getElementById('plan-tasks-input'); ti.value = '1- 14 صفحة مراجعة\\n2- !تقرير المبيعات\\n3- اتصال بالعائلة\\n4- ساعة رياضة\\n5- ترتيب الغرفة\\n6- قراءة 20 صفحة'; ti.dispatchEvent(new Event('input', { bubbles:true }));
    const li = document.getElementById('plan-learn-input'); li.value = '1- درس الرياضيات\\n2- فصل الفيزياء\\n3- تمارين الإنجليزي'; li.dispatchEvent(new Event('input', { bubbles:true }));
    switchWriteTab('tasks'); distributePlan(); await sleep(800);
    const add = (mode, text, type)=>{ habitMode = mode; newHabitType = type; const i = document.getElementById('new-habit-text'); if(i){ i.value = text; addHabit(); } };
    try{ add('build', 'شرب ماء كل صباح', HABIT_TYPES.build[0][0]); add('build', 'رياضة أسبوعية', HABIT_TYPES.build[HABIT_TYPES.build.length - 1][0]); add('quit', 'السكائر', HABIT_TYPES.quit[0][0]); }catch(e){}
    const R = data.settings.rewardItems || []; const rar = ['C','B','A','S','SS'], rooms = ['daily','weekly','monthly'];
    for(let i = 0; i < 15; i++) R.push({ id:'ct_' + i, name:['تطلب أكل تحبه','ساعة سوشل ميديا','سفرة للمنتجع','فلم بالسينما','عشاء برّه'][i % 5], rarity:rar[i % 5], room:rooms[i % 3], enabled:true, storePrice:null, coinValue:null, stickerId:['lamb_mandi','cafe_front',null][i % 3], weight:10, createdAt:'2026-01-01T00:00:00.000Z', updatedAt:'2026-01-01T00:00:00.000Z' });
    data.wallet.balance = 2450; saveData(); return 1; })()`);
  await c.load(); await c.sleep(2500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  for(const p of ['tasks', 'learn', 'habits', 'planning', 'settings']){ await go(p); await audit(p);
    await c.evaluate(`(()=>{ const s = [...document.querySelectorAll('.main')].find(e=>e.scrollHeight > e.clientHeight + 40); if(s) s.scrollTop = s.clientHeight * .8; })()`); await audit(p + '_b');
    await c.evaluate(`document.querySelectorAll('.main').forEach(e=>e.scrollTop = 0)`); }
  await go('habits'); await c.evaluate(`try{ setAddOpen(true); }catch(e){}`); await audit('habit_add'); await c.evaluate(`try{ setAddOpen(false, { silent:true }); }catch(e){}`);
  for(const s of ['account', 'rewards', 'sound', 'notifications', 'app-lock', 'archive', 'eco-log', 'appearance']){
    await go('settings'); await c.evaluate(`openSettingsCategory('${s}')`); await c.sleep(900); await audit('set_' + s);
    await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(500); }
  await go('tasks'); await c.evaluate(`econOpenStore()`); await c.sleep(2500);
  for(let i = 0; i < 5; i++){ await c.evaluate(`econStoreScroller().scrollTop = ${i * 760}`); await c.sleep(600); await audit('store_' + i); }
  const id = await c.evaluate(`(data.settings.rewardItems.find(x=>x.enabled !== false) || {}).id`);
  await c.evaluate(`econOpenDetail(${JSON.stringify(id)})`); await c.sleep(1200); await audit('store_detail');
  await c.evaluate(`(()=>{ try{ econCloseDetail(); }catch(e){} })()`); await c.sleep(600);
  const tier = await c.evaluate(`econBoxTierIds()[0]`);
  await c.evaluate(`econOpenBoxPreview ? econOpenBoxPreview(${JSON.stringify(tier)}) : 0`, false).catch(()=>{});
  await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(600);
  await go('settings'); await c.evaluate(`openSettingsCategory('rewards')`); await c.sleep(900);
  await c.evaluate(`(()=>{ const b = document.querySelector('.rpu-add'); if(b) b.click(); })()`); await c.sleep(700); await audit('rewards_add');
  await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(400);
  await go('tasks'); await c.evaluate(`econOpenStore()`); await c.sleep(2200);
  await c.evaluate(`econStoreScroller().scrollTop = 0; (()=>{ const t = document.querySelector('#eco-store-body .bx-card .bx-art, #eco-store-body .bx-card'); if(t) t.click(); })()`); await c.sleep(1200); await audit('box_detail');
  await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(600); await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(600);
  await go('tasks'); await c.evaluate(`codisConfirm({ title:'حذف المكافأة؟', message:'راح تنحذف المكافأة من القائمة.', danger:true, okText:'حذف' })`, false); await c.sleep(900); await audit('confirm_danger');
  await c.evaluate(`(()=>{ const b = [...document.querySelectorAll('#codis-confirm-modal button')].find(x=>/إلغاء/.test(x.textContent)); if(b) b.click(); })()`); await c.sleep(600);
  await c.evaluate(`codisConfirm({ title:'متأكد من الإجراء؟', message:'تقدر ترجع عنه لاحقاً.' })`, false); await c.sleep(900); await audit('confirm_neutral');
  await c.evaluate(`(()=>{ const b = [...document.querySelectorAll('#codis-confirm-modal button')].find(x=>/إلغاء/.test(x.textContent)); if(b) b.click(); })()`); await c.sleep(600);
  await go('tasks'); await c.evaluate(`openNotifCenter()`); await c.sleep(900); await audit('notif');
  await c.evaluate(`(()=>{ try{ CodisNav.back(); }catch(e){} })()`); await c.sleep(600);
  await c.evaluate(`window.__cf = window.__cf || null; showToast('تم حفظ الخطة بنجاح', 'var(--success)')`); await c.sleep(500); await audit('toast_success');
  await c.evaluate(`showToast('تعذّر الحفظ، حاول مرة ثانية', 'var(--danger)')`); await c.sleep(500); await audit('toast_danger');
  await c.evaluate(`showToast('تنبيه: رصيدك قليل', 'var(--warning)')`); await c.sleep(500); await audit('toast_warning');
}
