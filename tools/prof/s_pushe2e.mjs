// Real end-to-end Web Push: keys generated exactly like the Edge Function (WebCrypto), browser subscribes through FCM,
// Node sends with web-push (same library the function uses), the service worker receives it and shows the notification.
import { createRequire } from 'node:module';
const require = createRequire('C:/tmp/wp/');
const webpush = require('web-push');
const b64url = u=>Buffer.from(u).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
export default async function(c){
  const kp = await crypto.subtle.generateKey({ name:'ECDSA', namedCurve:'P-256' }, true, ['sign', 'verify']);
  const pub = b64url(new Uint8Array(await crypto.subtle.exportKey('raw', kp.publicKey))), priv = (await crypto.subtle.exportKey('jwk', kp.privateKey)).d;
  await c.send('Browser.grantPermissions', { permissions:['notifications'] }).catch(()=>{});
  await c.load(); await c.sleep(2500);
  const sub = await c.evaluate(`(async()=>{ const r = await navigator.serviceWorker.ready; const old = await r.pushManager.getSubscription(); if(old) await old.unsubscribe();
    const s = await r.pushManager.subscribe({ userVisibleOnly:true, applicationServerKey:Uint8Array.from(atob('${pub}'.replace(/-/g,'+').replace(/_/g,'/') + '='), ch=>ch.charCodeAt(0)) });
    data.notifications.settings.browserEnabled = true; return s.toJSON(); })()`);
  console.log('subscribed', sub.endpoint.slice(0, 45));
  webpush.setVapidDetails('mailto:codis@codis.app', pub, priv);
  const res = await webpush.sendNotification(sub, JSON.stringify({ title:'انتهى الوقت', body:'انتهى الوقت المحدد لمهمة تمرين', tag:'ev_e2etest1', url:'./' }), { TTL:3600, urgency:'high' });
  console.log('push service answered', res.statusCode);
  let got = null;
  for(let i = 0; i < 40 && !got; i++){ await c.sleep(500); got = await c.evaluate(`(async()=>{ const r = await navigator.serviceWorker.ready; const n = await r.getNotifications(); return n.length ? n.map(x=>x.title + ' | ' + x.body + ' | ' + x.tag) : null; })()`); }
  console.log('service worker showed:', JSON.stringify(got));
}
