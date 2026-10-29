/* CODIS UI sweep — visits every room, settings page, store tab, pack preview and main modals; collects layout/accessibility/runtime defects.
   Evaluate in the page (guest, fresh origin). Returns { states, counts, sample }. Read-only except opening screens and seeding sample data. */
(async function(){ try{
  const sleep = ms=>new Promise(r=>setTimeout(r, ms)), issues = [], errs = [];
  const oe = window.onerror; window.onerror = (m, s, l)=>{ errs.push(String(m) + ' @' + l); return false; };
  const ce = console.error; console.error = function(){ errs.push([].map.call(arguments, String).join(' ').slice(0, 200)); return ce.apply(console, arguments); };
  codisConfirm = async()=>true;
  const vis = el=>{
    if(!el || !el.getClientRects().length) return false;
    for(let p = el; p && p !== document.body; p = p.parentElement){ const c = getComputedStyle(p); if(c.display === 'none' || c.visibility === 'hidden' || +c.opacity === 0) return false; }
    return true;
  };
  const scrollerX = el=>{ for(let p = el.parentElement; p && p !== document.body; p = p.parentElement){ const c = getComputedStyle(p); if(/(auto|scroll|hidden|clip)/.test(c.overflowX)) return p; } return null; };
  const label = el=>(el.id ? '#' + el.id : '') + '.' + String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').split(' ').slice(0, 2).join('.') + ' "' + String(el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 30) + '"';
  function audit(state){
    const W = innerWidth, found = [];
    if(document.documentElement.scrollWidth > W + 1) found.push(['h-overflow-page', document.documentElement.scrollWidth + ' > ' + W]);
    let n = 0;
    for(const el of document.querySelectorAll('body *')){
      if(n++ > 5000) break;
      if(el.closest('svg') && el.tagName.toLowerCase() !== 'svg') continue;
      const r = el.getBoundingClientRect(); if(!r.width || !r.height) continue;
      if((r.right > W + 2 || r.left < -2) && vis(el)){ const sx = scrollerX(el); if(!sx && !el.closest('.cb-world,.bk-world')) found.push(['offscreen', label(el) + ' L' + Math.round(r.left) + ' R' + Math.round(r.right)]); }
      if(el.tagName === 'IMG' && vis(el) && el.complete && el.naturalWidth === 0) found.push(['broken-img', label(el) + ' ' + String(el.src).slice(0, 60)]);
      if((el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') && vis(el)){
        const name = (el.getAttribute('aria-label') || el.getAttribute('title') || el.innerText || '').trim();
        if(!name) found.push(['no-name-btn', label(el)]);
        if((r.width < 30 || r.height < 30) && !el.closest('.cflip')) found.push(['small-target', label(el) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height)]);
      }
      if(el.children.length === 0 && !el.classList.contains('sr') && (el.innerText || '').trim().length > 2){   /* .sr = screen-reader only, clipped by design */
        const cs = getComputedStyle(el);
        if(/(hidden|clip)/.test(cs.overflowX) && cs.textOverflow !== 'ellipsis' && !(cs.webkitLineClamp && /\d/.test(cs.webkitLineClamp)) && el.scrollWidth > el.clientWidth + 2 && vis(el)) found.push(['clipped-text', label(el) + ' ' + el.scrollWidth + '>' + el.clientWidth]);
      }
    }
    const ids = {}; document.querySelectorAll('[id]').forEach(e=>{ ids[e.id] = (ids[e.id] || 0) + 1; });
    Object.keys(ids).filter(k=>ids[k] > 1 && k !== 'codis-mark').forEach(k=>found.push(['dup-id', k + ' x' + ids[k]]));
    found.forEach(f=>issues.push({ state:state, kind:f[0], info:f[1] }));
  }
  const states = [];
  const go = async(name, fn, wait)=>{ try{ await fn(); }catch(e){ issues.push({ state:name, kind:'exception', info:String(e && e.message || e) }); } await sleep(wait || 700); audit(name); states.push(name); };
  /* sample data so screens are not empty */
  const wk = currentWeekId(), di = new Date().getDay(), days = {}; for(let i = 0; i < 7; i++) days[i] = [];
  days[di] = ['قراءة فصل كامل من كتاب طويل الاسم جداً حتى نختبر الالتفاف', 'تمرين', 'اتصال'].map((x, i)=>({ id:'sw' + i, text:x, status:null, itemId:null, qty:1, unit:null, priority:i ? 'low' : 'high' }));
  days[(di + 1) % 7] = [{ id:'swx', text:'غداً', status:null, qty:1, priority:'low' }];
  data.weeks[wk] = { days:days, startedAt:todayKey(), items:[], holidayDay:null, planStartDay:di, planName:'خطة' };
  data.learnWeeks[wk] = { days:JSON.parse(JSON.stringify(days)), startedAt:todayKey(), items:[], holidayDay:null, planStartDay:di, planName:'خطة' };
  Object.keys(data.learnWeeks[wk].days).forEach(d=>data.learnWeeks[wk].days[d].forEach(t=>{ t.id = 'l' + t.id; }));
  const t0 = todayKey(), mk = o=>Object.assign({ createdAt:t0, log:{}, importance:'normal' }, o);
  data.habits.build = [mk({ id:'hs1', text:'قراءة 20 صفحة يومياً', type:'E', milestones:{}, misses:[], doneEvents:{}, checkedThrough:yesterdayKey() }), mk({ id:'hs2', text:'رياضة', type:'W', importance:'critical', requiredPerWeek:3, weeklyLogs:{}, weekHistory:[], firstFullWeek:firstFullWeekFor(t0) })];
  data.habits.quit = [mk({ id:'hs3', text:'التدخين', type:'H', importance:'important', occurrences:[], lastOccurrence:null, bestDays:0, monthlyMilestones:{} })];
  data.wallet.balance = 3000; saveData();
  for(const p of ['planning', 'tasks', 'learn', 'habits', 'settings']) await go('room:' + p, ()=>document.querySelector('.navbtn[data-page="' + p + '"]').click());
  const secs = [...document.querySelectorAll('#page-settings .settings-page-section')].map(s=>s.id.replace('settings-page-', '')).filter(x=>!/^(eco-store|eco-log|acct-delete)$/.test(x));
  for(const c of secs) await go('settings:' + c, ()=>{ document.querySelector('.navbtn[data-page="settings"]').click(); openSettingsCategory(c); }, 650);
  await go('store:boxes', ()=>econOpenStore(), 900);
  for(const tab of ['المظاهر', 'الكروت']) await go('store:' + tab, ()=>{ const b = [...document.querySelectorAll('#eco-store-body button')].find(x=>x.textContent.includes(tab)); if(b) b.click(); }, 800);
  await go('coinlog', ()=>{ econCloseStore({ silent:true }); econOpenLog(); }, 800);
  try{ econCloseStore({ silent:true }); }catch(e){}
  for(const t of ['bx1', 'bx3', 'bx5']){ await go('pack:' + t, ()=>econPackOpen(t), 900); econPackClose(); await sleep(300); }
  await go('notif', ()=>openNotifCenter(), 700); try{ closeNotifCenter(); }catch(e){}
  await go('tasks:partial', async()=>{ document.querySelector('.navbtn[data-page="tasks"]').click(); await sleep(500); CodisTaskFlow.answer('tasks', 'sw1', 'half', document.querySelector('[data-tid="sw1"]')); }, 500);
  await go('tasks:done-sheet', async()=>{ const d = document.querySelector('[data-tid="sw0"] [data-status="done"]'); if(d) d.click(); await sleep(2700); const b = document.querySelector('.cd-trigger'); if(b) b.click(); }, 600);
  CodisTaskFlow.closeDone(); await sleep(300);
  await go('habits:details', async()=>{ document.querySelector('.navbtn[data-page="habits"]').click(); await sleep(500); const t = document.querySelector('.hb-more-toggle'); if(t) t.click(); }, 600);
  window.onerror = oe; console.error = ce;
  errs.forEach(e=>issues.push({ state:'runtime', kind:'console-error', info:e }));
  const byKind = {}; issues.forEach(i=>{ (byKind[i.kind] = byKind[i.kind] || []).push(i.state + ' :: ' + i.info); });
  return { states:states.length, W:innerWidth, counts:Object.fromEntries(Object.keys(byKind).map(k=>[k, byKind[k].length])), sample:Object.fromEntries(Object.keys(byKind).map(k=>[k, [...new Set(byKind[k])].slice(0, 16)])) };
}catch(e){ return { error:String(e && e.stack || e) }; } })();
