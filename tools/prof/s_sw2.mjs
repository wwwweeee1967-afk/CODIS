// SW v5 page timeout: after a first (cached) visit, a 9 s server delay must not keep the app on a blank screen.
import fs from 'node:fs';
export default async function(c){
  try{ fs.unlinkSync('C:/tmp/site/SLOW'); }catch(e){}
  await c.load(); await c.sleep(2000);
  await c.evaluate(`(async()=>{ await navigator.serviceWorker.ready; for(let i = 0; i < 40; i++){ if(navigator.serviceWorker.controller) return 1; await new Promise(r=>setTimeout(r, 250)); } return 0; })()`);
  await c.load(); await c.sleep(1500);   // controlled visit (page now in cache)
  fs.writeFileSync('C:/tmp/site/SLOW', '1');
  const o0 = await c.evaluate(`performance.timeOrigin`);
  const t0 = Date.now(); c.send('Page.navigate', { url:c.url });
  let shown = -1;
  for(let i = 0; i < 80; i++){ await c.sleep(200); try{ const o = await c.evaluate(`performance.timeOrigin`, false); if(o !== o0 && await c.evaluate(`!!document.querySelector('meta[name=codis-version]')`, false)){ shown = Date.now() - t0; break; } }catch(e){} }
  console.log('server delayed 9000 ms → app shown after', shown, 'ms');
  fs.unlinkSync('C:/tmp/site/SLOW');
}
