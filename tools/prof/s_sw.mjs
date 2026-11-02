// Service worker v5 on a GitHub-like layout: precache completes, then OFFLINE reload still boots with every image; slow network → cached page after timeout.
export default async function(c){
  await c.load(); await c.sleep(2000);
  const reg = await c.evaluate(`(async()=>{ const r = await navigator.serviceWorker.ready; for(let i = 0; i < 60; i++){ const k = await caches.keys(); if(k.includes('codis-pwa-v5')){ const n = (await (await caches.open('codis-pwa-v5')).keys()).length; if(n >= 100) return { keys:k, cached:n }; } await new Promise(r=>setTimeout(r, 500)); } const k = await caches.keys(); return { keys:k, cached:k.includes('codis-pwa-v5') ? (await (await caches.open('codis-pwa-v5')).keys()).length : 0 }; })()`);
  console.log('sw cache', JSON.stringify(reg));
  if(await c.evaluate(`!!document.getElementById('gate-guest') && document.getElementById('gate-guest').offsetParent !== null`)){ await c.tap('#gate-guest'); await c.sleep(2000); }
  await c.send('Network.enable');
  await c.send('Network.emulateNetworkConditions', { offline:true, latency:0, downloadThroughput:-1, uploadThroughput:-1 });
  await c.load(); await c.sleep(3000);
  await c.evaluate(`econOpenStore()`); await c.sleep(3000);
  const r = await c.evaluate(`(async()=>{ const sc = econStoreScroller(); for(let y = 0; y < sc.scrollHeight; y += 400){ sc.scrollTop = y; await new Promise(r=>setTimeout(r, 120)); } await new Promise(r=>setTimeout(r, 1500));
    const imgs = Array.prototype.filter.call(document.querySelectorAll('img'), i=>(i.getAttribute('src') || '').indexOf('assets/img/') >= 0);
    return { ver:document.querySelector('meta[name=codis-version]').content, imgs:imgs.length, broken:imgs.filter(i=>i.complete && !i.naturalWidth).length, notLoaded:imgs.filter(i=>!i.complete).length }; })()`);
  console.log('offline boot', JSON.stringify(r));
  await c.screenshot('C:/tmp/cx/offline_store.png');
  // slow network: page should come from cache after ~3.5 s instead of waiting the full download
  await c.send('Network.emulateNetworkConditions', { offline:false, latency:9000, downloadThroughput:20000, uploadThroughput:20000 });
  const o0 = await c.evaluate(`performance.timeOrigin`);
  const t0 = Date.now(); await c.send('Page.navigate', { url:c.url });
  let shown = -1;
  for(let i = 0; i < 160; i++){ await c.sleep(250); try{ const o = await c.evaluate(`performance.timeOrigin`, false); if(o !== o0 && await c.evaluate(`!!document.querySelector('meta[name=codis-version]')`, false)){ shown = Date.now() - t0; break; } }catch(e){} }
  console.log('slow-network page shown after ms', shown);
}
