// Client push flow (server simulated in-page): key fetched from push_vapid_public, cached, device auto-subscribed, push_subscribe called with the real subscription.
export default async function(c){
  await c.send('Browser.grantPermissions', { permissions:['notifications'] }).catch(()=>{});
  await c.load(); await c.sleep(2500);
  const r = await c.evaluate(`(async()=>{
    const calls = []; const key = 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U';
    localStorage.removeItem('codis.push.vapid');
    Object.defineProperty(CodisAccount, 'state', { configurable:true, get:()=>({ user:{ id:'u1' } }) });
    CodisAccount.pushCall = async (n, b)=>{ calls.push(n); if(n === 'push_vapid_public') return key; return null; };
    data.notifications.settings.browserEnabled = true;
    const st = CodisPush.status();
    const res = await CodisPush.enable();
    const sub = await (await navigator.serviceWorker.ready).pushManager.getSubscription().catch(e=>'ERR ' + e.message);
    return { perm:Notification.permission, status:st, enable:res, calls, cached:localStorage.getItem('codis.push.vapid') === key, sub:sub && sub.endpoint ? sub.endpoint.slice(0, 40) : String(sub) };
  })()`);
  console.log(JSON.stringify(r, null, 1));
}
