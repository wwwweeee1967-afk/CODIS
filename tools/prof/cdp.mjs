// CODIS mobile-like profiler over the Chrome DevTools Protocol (no dependencies; Node >= 22 global WebSocket).
// Emulates an iPhone-class device: 393x852 @DPR3, touch, iOS UA, CPU throttled (default 6x), and measures
// boot time, long tasks, JS heap, style/layout/script time, DOM size, composited layer memory per scenario step.
// Usage: node tools/prof/cdp.mjs <url> <steps.mjs> [--cpu 6] [--w 393 --h 852 --dpr 3] [--out file.json]
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const opt = (k, d)=>{ const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const URL_ = args[0], STEPS = args[1];
const CPU = Number(opt('cpu', 6)), W = Number(opt('w', 393)), H = Number(opt('h', 852)), DPR = Number(opt('dpr', 3)), OUT = opt('out', '');
const CHROME = opt('chrome', 'C:/Program Files/Google/Chrome/Application/chrome.exe');
const PORT = 9300 + Math.floor(Math.random() * 500);
const prof = mkdtempSync(path.join(tmpdir(), 'codis-prof-'));
const ch = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + PORT, '--user-data-dir=' + prof, '--no-first-run', '--no-default-browser-check',
  '--enable-precise-memory-info', '--js-flags=--expose-gc', 'about:blank'], { stdio:'ignore' });
const sleep = ms=>new Promise(r=>setTimeout(r, ms));

async function target(){
  for(let i = 0; i < 60; i++){ try{ const r = await fetch('http://127.0.0.1:' + PORT + '/json/list'); const l = await r.json(); const p = l.find(t=>t.type === 'page'); if(p) return p; }catch(e){} await sleep(250); }
  throw new Error('chrome did not start');
}
const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r=>ws.addEventListener('open', r, { once:true }));
let id = 0; const pend = new Map(), handlers = [];
ws.addEventListener('message', ev=>{ const m = JSON.parse(ev.data); if(m.id && pend.has(m.id)){ const p = pend.get(m.id); pend.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } else handlers.forEach(h=>h(m)); });
const send = (method, params = {})=>new Promise((res, rej)=>{ const i = ++id; pend.set(i, { res, rej }); ws.send(JSON.stringify({ id:i, method, params })); });
const on = h=>handlers.push(h);

const consoleErrors = [];
on(m=>{ if(m.method === 'Runtime.exceptionThrown') consoleErrors.push(m.params.exceptionDetails.exception ? m.params.exceptionDetails.exception.description : m.params.exceptionDetails.text);
  if(m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') consoleErrors.push(m.params.args.map(a=>a.value || a.description).join(' ')); });

await send('Page.enable'); await send('Runtime.enable'); await send('Performance.enable', { timeDomain:'timeTicks' }); await send('DOM.enable'); await send('LayerTree.enable');
await send('Emulation.setDeviceMetricsOverride', { width:W, height:H, deviceScaleFactor:DPR, mobile:true });
await send('Emulation.setTouchEmulationEnabled', { enabled:true, maxTouchPoints:5 });
if(!process.env.DESKTOPUA) await send('Emulation.setUserAgentOverride', { userAgent:'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1', platform:'iPhone' });
await send('Emulation.setCPUThrottlingRate', { rate:CPU });
// long-task + frame recorder installed before any page script
if(process.env.NOZOOM) await send('Page.addScriptToEvaluateOnNewDocument', { source:'window.__codisNoZoom = 1;' });
/* PRELOAD=<js>: runs before the app's own scripts (e.g. offline_browser.js needs the in-page fake backend:
   PRELOAD='window.CODIS_BACKEND_OVERRIDE={url:"http://127.0.0.1:8766",anonKey:"test-anon"}' — keeps test traffic off the real Supabase) */
if(process.env.PRELOAD) await send('Page.addScriptToEvaluateOnNewDocument', { source:process.env.PRELOAD });
if(process.env.SAFARI) await send('Page.addScriptToEvaluateOnNewDocument', { source:`(()=>{ try{ window.requestIdleCallback = undefined; window.cancelIdleCallback = undefined; }catch(e){} ${process.env.SAFARI === 'nocv' ? "try{ delete HTMLElement.prototype.oncontentvisibilityautostatechange; }catch(e){}" : ''} })();` });
await send('Page.addScriptToEvaluateOnNewDocument', { source:`(()=>{ window.__lt=[]; try{ new PerformanceObserver(l=>{ for(const e of l.getEntries()) window.__lt.push({ s:Math.round(e.startTime), d:Math.round(e.duration) }); }).observe({ type:'longtask', buffered:true }); }catch(e){}
  window.__fr=[]; if(${process.env.NORAF ? 1 : 0}) return; let last=0; const tick=t=>{ if(last) window.__fr.push(t-last); last=t; if(window.__fr.length>20000) window.__fr.splice(0,10000); requestAnimationFrame(tick); }; requestAnimationFrame(tick); })();` });

let layers = [];
on(m=>{ if(m.method === 'LayerTree.layerTreeDidChange' && m.params.layers) layers = m.params.layers; });

const metrics = async()=>{ const r = await send('Performance.getMetrics'); const o = {}; r.metrics.forEach(x=>{ o[x.name] = x.value; }); return o; };
const evaluate = async (expr, awaitPromise = true)=>{ const r = await send('Runtime.evaluate', { expression:expr, awaitPromise, returnByValue:true }); if(r.exceptionDetails) throw new Error(r.exceptionDetails.exception ? r.exceptionDetails.exception.description : r.exceptionDetails.text); return r.result.value; };
const layerMem = ()=>{ let px = 0, n = 0, big = []; for(const l of layers){ if(!l.drawsContent) continue; n++; const a = l.width * l.height * DPR * DPR; px += a; if(l.width * l.height > 200000) big.push(Math.round(l.width) + 'x' + Math.round(l.height)); } return { layers:n, mb:Math.round(px * 4 / 1048576), big:big.slice(0, 12) }; };

const results = [];
let m0 = await metrics();
async function snap(label, extra){
  const m = await metrics(); await sleep(50);
  const page = await evaluate(`(()=>{ const lt = window.__lt || [], fr = (window.__fr || []); window.__lt = []; const f = fr.splice(0); const s = f.slice().sort((a,b)=>a-b);
    const p = q=>s.length ? Math.round(s[Math.min(s.length-1, Math.floor(s.length*q))]) : 0;
    return { dom:document.getElementsByTagName('*').length, heapMB:performance.memory ? Math.round(performance.memory.usedJSHeapSize/1048576) : null,
      longTasks:lt.length, longMs:lt.reduce((a,b)=>a+b.d,0), worstTask:lt.reduce((a,b)=>Math.max(a,b.d),0),
      frames:f.length, p50:p(.5), p95:p(.95), p99:p(.99), jank:f.filter(x=>x>50).length, worstFrame:Math.round(s[s.length-1]||0) }; })()`);
  const d = k=>Math.round(((m[k] || 0) - (m0[k] || 0)) * 1000);
  const row = Object.assign({ step:label, scriptMs:d('ScriptDuration'), styleMs:d('RecalcStyleDuration'), layoutMs:d('LayoutDuration'), taskMs:d('TaskDuration'),
    layoutCount:Math.round((m.LayoutCount || 0) - (m0.LayoutCount || 0)), styleCount:Math.round((m.RecalcStyleCount || 0) - (m0.RecalcStyleCount || 0)), jsHeapMB:Math.round((m.JSHeapUsedSize || 0) / 1048576) }, page, { gpu:layerMem() }, extra || {});
  m0 = m; results.push(row); console.log(JSON.stringify(row));
}

const ctx = { send, evaluate, sleep, snap, onMsg:on, url:URL_, W, H, DPR, CPU, layers:()=>layers, layerMem,
  async load(u){ const t0 = Date.now(); await send('Page.navigate', { url:u || URL_ }); await new Promise(r=>{ const h = m=>{ if(m.method === 'Page.loadEventFired'){ r(); } }; on(h); }); return Date.now() - t0; },
  async tap(sel){ const r = await evaluate(`(()=>{ const e = document.querySelector(${JSON.stringify(sel)}); if(!e) return null; e.scrollIntoView({block:'center'}); const b = e.getBoundingClientRect(); return { x:b.left + b.width/2, y:b.top + b.height/2 }; })()`); if(!r) throw new Error('no element ' + sel);
    await send('Input.dispatchTouchEvent', { type:'touchStart', touchPoints:[{ x:r.x, y:r.y }] }); await sleep(40); await send('Input.dispatchTouchEvent', { type:'touchEnd', touchPoints:[] }); },
  async press(sel, ms){ const r = await evaluate(`(()=>{ const e = document.querySelector(${JSON.stringify(sel)}); if(!e) return null; e.scrollIntoView({block:'center'}); const b = e.getBoundingClientRect(); return { x:b.left + b.width/2, y:b.top + b.height/2 }; })()`); if(!r) throw new Error('no element ' + sel);
    await send('Input.dispatchTouchEvent', { type:'touchStart', touchPoints:[{ x:r.x, y:r.y }] }); await sleep(ms || 600); await send('Input.dispatchTouchEvent', { type:'touchEnd', touchPoints:[] }); },
  async swipe(x, y0, y1, steps){ steps = steps || 12; await send('Input.dispatchTouchEvent', { type:'touchStart', touchPoints:[{ x, y:y0 }] }); for(let i = 1; i <= steps; i++){ await send('Input.dispatchTouchEvent', { type:'touchMove', touchPoints:[{ x, y:y0 + (y1 - y0) * i / steps }] }); await sleep(16); } await send('Input.dispatchTouchEvent', { type:'touchEnd', touchPoints:[] }); },
  async screenshot(file){ const r = await send('Page.captureScreenshot', { format:'png' }); writeFileSync(file, Buffer.from(r.data, 'base64')); } };

try{
  const mod = await import(pathToFileURL(path.resolve(STEPS)).href);
  await mod.default(ctx);
}catch(e){ console.error('SCENARIO ERROR:', e.message); results.push({ step:'ERROR', error:e.message }); }
results.push({ step:'consoleErrors', list:consoleErrors.slice(0, 40) });
if(OUT) writeFileSync(OUT, JSON.stringify(results, null, 1));
try{ ws.close(); }catch(e){} ch.kill(); process.exit(0);
