#!/usr/bin/env python3
"""CODIS-PUSH-AUTO (بعد patch_v23.py) — 3.13.0 — إشعارات المؤقتات والتطبيق مسكّر بلا أي مفتاح يدوي.
 • المفتاح العام VAPID: من <meta> إن وُجد، وإلا من الخادم (rpc push_vapid_public — يولّده الخادم نفسه بأول تشغيل ويحفظه بـVault) ويُخزَّن بالجهاز.
 • الأجهزة التي فعّلت «إشعارات المتصفح» سابقاً (والمفتاح كان فارغاً فلم تُسجَّل بالخادم) تُسجَّل تلقائياً مرة بالجلسة بعد الدخول.
 • حُذفت عبارة «(والتطبيق مفتوح فقط)» ورسالة «مفتاح VAPID العام فارغ» بلا بديل (طلب المالك).
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-PUSH-AUTO' in s: sys.exit('already patched (CODIS-PUSH-AUTO)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

rep("""  const vapid = ()=>{ try{ const m = document.querySelector('meta[name="codis-vapid-public-key"]'); return m ? String(m.getAttribute('content') || '').trim() : ''; }catch(e){ return ''; } };""",
    """  /* CODIS-PUSH-AUTO: المفتاح العام من <meta> أو من الخادم (يولّده بنفسه ويحفظه بـVault) — نسخة محفوظة بالجهاز */
  const VK = 'codis.push.vapid';
  const vapid = ()=>{ try{ const m = document.querySelector('meta[name="codis-vapid-public-key"]'); const v = m ? String(m.getAttribute('content') || '').trim() : ''; return v || String(localStorage.getItem(VK) || ''); }catch(e){ return ''; } };
  async function fetchVapid(){
    try{ const v = await CodisAccount.pushCall('push_vapid_public', {}); const k = typeof v === 'string' ? v.trim() : '';
      if(/^[A-Za-z0-9_-]{80,100}$/.test(k)){ localStorage.setItem(VK, k); return k; } }catch(e){ console.warn('CODIS push key:', e && e.message); }
    return '';
  }""", 'vapid')

rep("""    const r = await registration();
    if(!vapid() || !signedIn() || !r || !r.pushManager) return { ok:true, push:false };
    try{
      let sub = await r.pushManager.getSubscription();
      if(!sub) sub = await r.pushManager.subscribe({ userVisibleOnly:true, applicationServerKey:b64(vapid()) });""",
    """    const r = await registration();
    if(!signedIn() || !r || !r.pushManager) return { ok:true, push:false };
    const key = vapid() || await fetchVapid();
    if(!key) return { ok:true, push:false };
    try{
      let sub = await r.pushManager.getSubscription();
      if(!sub) sub = await r.pushManager.subscribe({ userVisibleOnly:true, applicationServerKey:b64(key) });""", 'enable key')

rep("""    if(!vapid()) return { ok:false, code:'no-vapid', msg:'إشعارات الخلفية غير مهيّأة على الخادم بعد (مفتاح VAPID العام فارغ) — تصلك التنبيهات والتطبيق مفتوح فقط إلى أن يُضبط الخادم (راجع docs/CODIS_PUSH_SETUP.md).' };
""", "", 'status no-vapid')

rep("""  window.addEventListener('load', ()=>{ setTimeout(()=>{ registration(); try{ CodisTimers.tick(); }catch(e){} }, 300); });""",
    """  window.addEventListener('load', ()=>{ setTimeout(()=>{ registration(); try{ CodisTimers.tick(); }catch(e){} }, 300); });
  /* CODIS-PUSH-AUTO: جهاز فعّل الإشعارات (إذن ممنوح + مفعّلة بالإعدادات) يُسجَّل/يُجدَّد اشتراكه بالخادم مرة بالجلسة بعد الدخول —
     يشمل الأجهزة التي فعّلتها قبل تهيئة الخادم. عملية idempotent (upsert بنفس endpoint) */
  let autoDone = false;
  function autoSubscribe(){
    if(autoDone) return;
    try{ if(!granted() || !(data.notifications && data.notifications.settings && data.notifications.settings.browserEnabled) || !signedIn()) return; }catch(e){ return; }
    autoDone = true;
    enable().then(r=>{ if(!r || !r.push) autoDone = false; }).catch(()=>{ autoDone = false; });
  }
  setInterval(autoSubscribe, 15000); setTimeout(autoSubscribe, 4000);
  document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) autoSubscribe(); });""", 'auto subscribe')

rep("""        else { const st = CodisPush.status(); showToast('انفعلت إشعارات الجهاز' + (st.ok ? '' : ' (والتطبيق مفتوح فقط): ' + st.msg), st.ok ? 'var(--success)' : 'var(--warning)', st.ok ? 'check' : undefined); }""",
    """        else { const st = CodisPush.status(); showToast('انفعلت إشعارات الجهاز' + (st.ok ? '' : ' — ' + st.msg), st.ok ? 'var(--success)' : 'var(--warning)', st.ok ? 'check' : undefined); }   /* CODIS-PUSH-AUTO */""", 'toggle toast')

open(dst, 'w', encoding='utf-8', newline='').write(s)
print('ok')
