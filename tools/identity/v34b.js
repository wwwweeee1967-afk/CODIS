function codisV34EventPenDef(h){ return codisFixedFor('punish', 'event', codisV34ImpKey(h)); }
function codisV34ResistDef(h){ return codisFixedFor('rewards', 'resist', codisV34ImpKey(h)); }
function codisV34Ms30Def(h){ return codisFixedFor('rewards', 'monthlyEvent', codisV34ImpKey(h)); }

async function recordEventHabit(id){   // H: «وقعت بها» — لا خصم تلقائي: تُنشأ عقوبة ثابتة بحسب الأهمية، والمستخدم يقرر (تنفيذ أو دفع)
  const h = data.habits.quit.find(x=>x.id === id); if(!h) return;
  const today = todayKey();
  if(h.lastOccurrence === today){ showToast('سجّلت الوقوع اليوم أصلاً', 'var(--danger)'); return; }
  const def = codisV34EventPenDef(h);
  const ok = await codisConfirm(CodisCopy.occurred(def ? def.cost : 0));
  if(!ok) return;
  codisJustChangedId = id; codisHaptic(8);
  const days = hDays(h);
  if(h.resists && h.resists[today]){ CodisEconomy.voidIfPending(['habit', h.id, 'rs:' + today, 'reward'].join('|')); delete h.resists[today]; }   // وقوع اليوم يلغي مقاومته غير المستلمة
  h.bestDays = Math.max(h.bestDays || 0, days);
  h.occurrences.push({ date:today, daysBefore:days, punishment:'', coins:0 }); h.lastOccurrence = today; h.log[today] = true;
  const pr = def ? codisFixedOutcome(['habit', h.id, 'ev:' + today, 'punish'].join('|'), 'punish', def, codisHabitFixedCtx(h, 'وقعت بـ«' + h.text + '»')) : null;
  saveData(); codisSfx('discipline.penalty');
  showToast('سُجّل الوقوع — تكمل من جديد', 'var(--warning)');
  CodisEvents.emit('HABIT_EVENT_OCCURRED', { id:h.id, text:h.text, importance:habitImportance(h), dateKey:today, detail:'' });
  if(pr && pr.entry && pr.isNew){ try{ CodisOutcomeUI.enqueue(pr.entry.id, 450); }catch(e){} }
  renderHabitsPage();
}
function resistEventHabit(id){   // H: «قاومت» — مكافأة ثابتة بحسب الأهمية، مرة لكل (عادة+يوم) بمعرّف ثابت rs:التاريخ. بلا احتمالات ولا سقف عام
  const h = data.habits.quit.find(x=>x.id === id && x.type === 'H'); if(!h) return;
  const today = todayKey(); if(!h.resists || typeof h.resists !== 'object') h.resists = {};
  if(h.resists[today]){ codisSfx('invalid', { ctx:'limit' }); showToast('سجّلت المقاومة اليوم أصلاً', 'var(--warning)'); return; }
  if(h.lastOccurrence === today){ codisSfx('invalid', { ctx:'limit' }); showToast('سجّلت وقوعاً اليوم — لا تُسجَّل مقاومة لنفس اليوم', 'var(--danger)'); return; }
  codisJustChangedId = id; codisHaptic(8);
  const def = codisV34ResistDef(h);
  const rr = def ? codisFixedOutcome(['habit', h.id, 'rs:' + today, 'reward'].join('|'), 'reward', def, codisHabitFixedCtx(h, 'قاومت «' + h.text + '»')) : null;
  h.resists[today] = { outcomeId:(rr && rr.entry) ? rr.entry.id : null };
  saveData();
  if(rr && rr.entry && rr.isNew){ try{ CodisOutcomeUI.enqueue(rr.entry.id, 250); }catch(e){} showToast('ممتاز! مقاومة اليوم — مكافأتك بانتظارك', 'var(--success)', 'check'); }
  else codisSfx('task.done');
  renderHabitsPage();
}
/* يُنفَّذ مع فحص العادات (إقلاع/عودة/تغيّر اليوم) — كله idempotent */
function codisV34Daily(){
  try{ codisV34Compensate(); }catch(e){ console.error('v34 comp', e); }
  try{ codisV34StationPenalties(); }catch(e){ console.error('v34 st7', e); }
  try{ setTimeout(codisV34CompNotice, 2600); }catch(e){}
  try{ CodisHabitPush.kick(); }catch(e){}
}

/* ---------- 8) تذكيرات الجهاز (Web Push الخلفي): الخادم يرسل وحده، والتطبيق مغلقاً ----------
   كل تذكير = صف في push_timers (نفس بنية مؤقتات CODIS) بمعرّف فريد (مستخدم+تاريخ / مستخدم+عادة+تاريخ) فلا يتكرر.
   يُجدوَل لـ7 أيام قادمة ويُحدَّث/يُلغى مع أي تغيير بالعادات (إكمال، إضافة، أرشفة، تغيير أيام). */
const CodisHabitPush = (function(){
  'use strict';
  const LS = 'codis_hpush_v1';
  let timer = 0, busy = false;
  const loadMap = ()=>{ try{ const m = JSON.parse(localStorage.getItem(LS) || '{}'); return (m && typeof m === 'object') ? m : {}; }catch(e){ return {}; } };
  const saveMap = m=>{ try{ localStorage.setItem(LS, JSON.stringify(m)); }catch(e){} };
  const uid8 = ()=>{ try{ return String(CodisAccount.state.user.id || '').replace(/[^a-z0-9]/gi, '').slice(0, 8).toLowerCase(); }catch(e){ return ''; } };
  const ymd = k=>String(k).replace(/-/g, '');
  const at = (k, hh)=>{ const p = parseKey(k); p.setHours(hh, 0, 0, 0); return p; };
  function inQuiet(d){
    try{ const q = data.notifications.settings.quietHours; if(!q || !q.enabled) return false;
      const m = d.getHours() * 60 + d.getMinutes(), t = s=>{ const a = String(s).split(':'); return Number(a[0]) * 60 + Number(a[1]); }, a = t(q.start), b = t(q.end);
      return a <= b ? (m >= a && m < b) : (m >= a || m < b); }catch(e){ return false; }
  }
  function enabled(){ try{ return CodisPush.ready() && !!(data.notifications && data.notifications.settings && data.notifications.settings.browserEnabled); }catch(e){ return false; } }
  function plan(){
    const out = {}, now = Date.now(), u = uid8(); if(!u) return out;
    const dailies = data.habits.build.filter(h=>h.type === 'E').concat(data.habits.quit.filter(isAbstainDaily));
    const weeklies = data.habits.build.filter(h=>h.type === 'W' && codisWDaysOk(h.days).length);
    for(let i = 0; i < 7; i++){
      const dk = addDaysKey(todayKey(), i), dt = parseKey(dk), f23 = at(dk, 23);
      if(f23.getTime() > now + 60000 && !inQuiet(f23)){
        const open = dailies.filter(h=>dk >= h.createdAt && !(i === 0 && (h.log[dk] || (h.failLog && h.failLog[dk]))));
        if(open.length){
          const names = open.slice(0, 3).map(h=>'«' + h.text + '»').join('، ') + (open.length > 3 ? ' و' + (open.length - 3) + ' أخرى' : '');
          out['ev_hn23' + u + ymd(dk)] = { at:f23.getTime(), title:'تذكير بالعادات اليومية', body:'باقي ساعة على نهاية اليوم. عندك عادات يومية لحد الآن ما سجلت إنجازها: ' + names };
        }
      }
      weeklies.forEach(h=>{
        if(codisWDaysOk(h.days).indexOf(dt.getDay()) === -1 || dk < h.createdAt) return;
        if(i === 0 && ((h.weeklyLogs[currentWeekId()] || []).indexOf(dk) !== -1)) return;
        const f9 = at(dk, 9); if(f9.getTime() <= now + 60000 || inQuiet(f9)) return;
        out['ev_hw' + u + econHash(h.id).slice(0, 6) + ymd(dk)] = { at:f9.getTime(), title:'موعد عادة اليوم', body:'اليوم موعد عادة ' + h.text };
      });
    }
    return out;
  }
  async function sync(){
    if(busy || !enabled()) return; busy = true;
    try{
      const want = plan(), have = loadMap(), next = {};
      for(const id of Object.keys(have)){
        if(want[id]) continue;
        if(have[id] && have[id].at > Date.now() - 3600000){ try{ await CodisAccount.pushCall('push_cancel', { p_event_id:id }); }catch(e){ next[id] = have[id]; } }
      }
      for(const id of Object.keys(want)){
        const w = want[id], h = have[id];
        if(h && h.at === w.at && h.body === w.body){ next[id] = h; continue; }
        try{ await CodisAccount.pushCall('push_schedule', { p_event_id:id, p_fire_at:new Date(w.at).toISOString(), p_title:w.title, p_body:w.body }); next[id] = { at:w.at, body:w.body }; }
        catch(e){ /* خارج نافذة الخادم أو بلا اتصال: تُعاد المحاولة بالمزامنة التالية */ }
      }
      saveMap(next);
    }finally{ busy = false; }
  }
  function kick(){ clearTimeout(timer); timer = setTimeout(()=>{ sync().catch(()=>{}); }, 4000); }
  async function notifyNow(title, body, kind){
    if(!enabled()) return false; const u = uid8(); if(!u) return false;
    try{ await CodisAccount.pushCall('push_schedule', { p_event_id:'ev_h' + String(kind || 'x') + u + '0001', p_fire_at:new Date(Date.now() + 20000).toISOString(), p_title:title, p_body:body }); return true; }catch(e){ return false; }
  }
  try{ document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) kick(); }); setInterval(kick, 20 * 60 * 1000); setTimeout(kick, 8000); }catch(e){}
  return { kick:kick, sync:sync, plan:plan, notifyNow:notifyNow, enabled:enabled };
})();
