// Every main page: navigation cost + idle cost (3 s) + running animations; realistic data (plan with tasks, habits) via the app's own sample flow if present.
async function trace(c, fn){
  const events = []; const h = m=>{ if(m.method === 'Tracing.dataCollected') events.push(...m.params.value); }; c.onMsg(h);
  await c.send('Tracing.start', { transferMode:'ReportEvents', traceConfig:{ includedCategories:['devtools.timeline', 'disabled-by-default-devtools.timeline'] } });
  await fn();
  const done = new Promise(r=>c.onMsg(m=>{ if(m.method === 'Tracing.tracingComplete') r(); })); await c.send('Tracing.end'); await done;
  const s = {}, n = {}; let worst = 0; for(const e of events){ if(e.ph !== 'X' || !e.dur) continue; if(['Layout', 'UpdateLayoutTree', 'Paint', 'FunctionCall', 'TimerFire', 'Layerize', 'PrePaint'].includes(e.name)){ s[e.name] = (s[e.name] || 0) + e.dur; n[e.name] = (n[e.name] || 0) + 1; } if(e.name === 'RunTask' && e.dur > worst) worst = e.dur; }
  return Object.fromEntries(Object.entries(s).map(([k, v])=>[k, Math.round(v / 1000) + '/' + n[k]])).toString && { ms:Object.fromEntries(Object.entries(s).map(([k, v])=>[k, Math.round(v / 1000) + '/' + n[k]])), worstTask:Math.round(worst / 1000) };
}
export default async function(c){
  await c.load(); await c.sleep(1500);
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2500); }
  for(const p of ['tasks', 'learn', 'habits', 'planning', 'settings', 'tasks']){
    const nav = await trace(c, async()=>{ await c.evaluate(`navigateToPage('${p}')`); await c.sleep(1200); });
    const idle = await trace(c, ()=>c.sleep(3000));
    const anims = await c.evaluate(`document.getAnimations().filter(a=>a.playState === 'running').map(a=>(a.animationName || a.transitionProperty || 'waapi') + (a.effect.getTiming().iterations === Infinity ? '∞' : '')).join(',')`);
    console.log(p.padEnd(9), 'NAV', JSON.stringify(nav), '| IDLE', JSON.stringify(idle), '| anims:', anims.slice(0, 160));
  }
}
