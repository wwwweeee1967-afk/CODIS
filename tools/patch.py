import re,sys
import sys
src=sys.argv[1] if len(sys.argv)>1 else "src/CODIS_9-7-3.html"
out=sys.argv[2] if len(sys.argv)>2 else "app/CODIS_FINAL.html"
t=open(src,'rb').read().decode('utf-8')
orig_len=len(t)
def rep(old,new,count=1):
    global t
    n=t.count(old)
    assert n==count, f'expected {count} got {n} for: {old[:90]!r}'
    t=t.replace(old,new)

# L: head meta
rep('<meta name="color-scheme" content="dark">\n',
'<meta name="color-scheme" content="dark">\n'
'<!-- CODIS accounts (Supabase). Fill ONLY the public values: Project URL + anon/publishable key. NEVER put service_role / secret keys here. -->\n'
'<meta name="codis-supabase-url" content="">\n'
'<meta name="codis-supabase-key" content="">\n')

# header comment
rep('   الإعداد: ضع Project URL و anon key في CODIS_BACKEND أدناه (المفتاح العام فقط — لا تضع service_role أبداً).\n',
    '   الإعداد: يُقرأ بالأولوية من window.CODIS_BACKEND_OVERRIDE ثم وسمَي <meta name="codis-supabase-url|key"> في <head> ثم CODIS_BACKEND أدناه — Project URL والمفتاح العام (anon/publishable) فقط؛ لا تضع service_role أبداً (يُرفض تلقائياً).\n')

# A: config + validation
old_cfg="""const CODIS_BACKEND = { url: '', anonKey: '' };
const CodisAccount = (function(){
  'use strict';
  const cfg = window.CODIS_BACKEND_OVERRIDE || CODIS_BACKEND;
  const configured = !!(cfg && cfg.url && cfg.anonKey);
"""
new_cfg="""const CODIS_BACKEND = { url: '', anonKey: '' };   // بديل أخير — الأفضل وسما <meta> في <head> (codis-supabase-url / codis-supabase-key)
const CodisAccount = (function(){
  'use strict';
  /* ---------- إعداد الخادم + تحقّق صارم قبل أي مصادقة ---------- */
  function readBackendCfg(){
    const meta = n => { try{ const e = document.querySelector('meta[name="' + n + '"]'); return e ? String(e.getAttribute('content') || '').trim() : ''; }catch(e){ return ''; } };
    const o = window.CODIS_BACKEND_OVERRIDE;
    if(o && (o.url || o.anonKey)) return { url:String(o.url || '').trim(), anonKey:String(o.anonKey || '').trim() };
    const mu = meta('codis-supabase-url'), mk = meta('codis-supabase-key');
    if(mu || mk) return { url:mu, anonKey:mk };
    return { url:String(CODIS_BACKEND.url || '').trim(), anonKey:String(CODIS_BACKEND.anonKey || '').trim() };
  }
  function checkBackend(c, loc){
    loc = loc || location;
    const bad = (code, msg) => ({ ok:false, code:code, msg:msg, cfg:null });
    if(!c.url && !c.anonKey) return bad('missing', 'خدمة الحسابات غير مهيّأة بعد: لم يُدخَل عنوان مشروع Supabase ولا المفتاح العام.');
    if(!c.url || !c.anonKey) return bad('incomplete', 'إعداد الحسابات ناقص: يلزم عنوان المشروع (Project URL) والمفتاح العام (anon / publishable) معاً.');
    let u; try{ u = new URL(c.url); }catch(e){ return bad('url', 'عنوان مشروع Supabase غير صالح. الشكل الصحيح: https://xxxx.supabase.co'); }
    const isLocal = h => h === 'localhost' || h === '127.0.0.1' || h === '[::1]';
    if(!(u.protocol === 'https:' || (isLocal(u.hostname) && u.protocol === 'http:')) || u.pathname.replace(/\\/+$/, '') !== '' || u.search || u.hash)
      return bad('url', 'عنوان مشروع Supabase غير صالح. الشكل الصحيح: https://xxxx.supabase.co (بدون مسار بعده).');
    const k = c.anonKey;
    if(/^sb_secret_/i.test(k)) return bad('secretkey', 'المفتاح المُدخل مفتاح خادم سري (secret) ولا يجوز وجوده في التطبيق. استخدم المفتاح العام (anon / publishable) فقط.');
    if(!/^sb_publishable_/i.test(k)){
      if(k.split('.').length !== 3) return bad('key', 'المفتاح العام غير صالح (يجب أن يبدأ بـ sb_publishable_ أو يكون anon JWT).');
      const cl = jwt(k);
      if(!cl) return bad('key', 'المفتاح العام غير صالح (تعذّرت قراءته).');
      if(cl.role && cl.role !== 'anon') return bad('secretkey', 'المفتاح المُدخل ليس المفتاح العام (الدور: ' + String(cl.role).slice(0, 20) + '). لا تضع service_role في التطبيق أبداً؛ استخدم anon / publishable.');
    }
    const pr = loc && loc.protocol, host = loc && loc.hostname;
    if(!(pr === 'https:' || (pr === 'http:' && isLocal(host)))) return bad('origin', 'تسجيل الدخول بـ Google لا يعمل عند فتح الملف مباشرة (file://). شغّل CODIS من رابط https:// أو من http://localhost.');
    return { ok:true, code:'', msg:'', cfg:{ url:u.origin, anonKey:k } };
  }
  const CHK = checkBackend(readBackendCfg());
  const cfg = CHK.cfg || { url:'', anonKey:'' };
  const configured = CHK.ok;
  if(!CHK.ok && CHK.code !== 'missing') console.warn('[CODIS auth] backend config rejected:', CHK.code);
"""
rep(old_cfg,new_cfg)

# B: flags
rep("  let pushing = false, changeCtr = 0, timer = null, retryMs = 0;\n",
    "  let pushing = false, changeCtr = 0, timer = null, retryMs = 0, refreshing = null, signingIn = false;\n")

# C: refresh single-flight
rep("""  async function refresh(){
    if(!S.session || !S.session.refresh_token) throw Object.assign(new Error('no refresh'), { expired:true });
""","""  function refresh(){ if(!refreshing) refreshing = refreshOnce().finally(() => { refreshing = null; }); return refreshing; }   // طلب تجديد واحد في آنٍ واحد
  async function refreshOnce(){
    /* تبويب آخر قد يكون جدّد الرمز فعلاً (الرمز يُدوَّر): نتبنّى الجلسة المخزّنة بدل استهلاك رمز مستهلَك */
    const st = jparse(rd(K_SESSION), null);
    if(st && st.access_token && S.session && st.refresh_token !== S.session.refresh_token && st.expires_at - Date.now() > 60000){ loadSession(); return; }
    if(!S.session || !S.session.refresh_token) throw Object.assign(new Error('no refresh'), { expired:true });
""")

# D: errors
rep("""  async function rpc(name, body){
    const r = await api('/rest/v1/rpc/' + name, { method:'POST', body:body || {} });
    if(!r.ok) throw Object.assign(new Error(await errMsg(r)), { http:r.status });
""","""  async function httpErr(r){
    let j = null; try{ j = await r.json(); }catch(e){}
    const er = new Error((j && (j.message || j.msg || j.error_description || j.error)) || ('HTTP ' + r.status));
    er.http = r.status; er.code = String((j && (j.code || j.error_code)) || ''); return er;
  }
  /* تصنيف الأخطاء: رسالة عربية للمستخدم + تشخيص تقني في الكونسول (بلا رموز أو أسرار) */
  function classify(e){
    e = e || {}; const code = String(e.code || ''), http = e.http || 0, msg = String(e.message || '');
    if(e.expired) return { st:'expired', msg:'', perm:true };
    if(e.net) return { st:'offline', msg:'', perm:false };
    if(code === 'PGRST202' || code === '42883' || (http === 404 && /function/i.test(msg))) return { st:'error', msg:'دالة المزامنة غير موجودة في Supabase — شغّل ملف codis_supabase_setup.sql.', perm:true };
    if(code === '42P01' || code === 'PGRST205' || /relation .* does not exist|schema cache/i.test(msg)) return { st:'error', msg:'جداول المزامنة غير موجودة في Supabase — شغّل ملف codis_supabase_setup.sql.', perm:true };
    if(code === '42501' || (http === 403 && code !== '28000')) return { st:'error', msg:'لا تملك صلاحية الوصول لبياناتك على الخادم (سياسات RLS/الصلاحيات) — راجع codis_supabase_setup.sql.', perm:true };
    if(http === 401 || code === 'PGRST301' || code === '28000' || (http === 403 && code === '28000')) return { st:'expired', msg:'', perm:true };
    if(http === 413 || code === '54000') return { st:'error', msg:'حجم بياناتك أكبر من الحد المسموح للمزامنة.', perm:true };
    if(http >= 500 || http === 429 || http === 408) return { st:'error', msg:'الخادم مشغول مؤقتاً — ستُعاد المحاولة.', perm:false };
    return { st:'error', msg:'تعذّرت المزامنة — ستُعاد المحاولة.', perm:false };
  }
  async function rpc(name, body){
    const r = await api('/rest/v1/rpc/' + name, { method:'POST', body:body || {} });
    if(!r.ok) throw await httpErr(r);
""")
rep("""    const r = await api('/rest/v1/progress?select=data,version,updated_at&user_id=eq.' + encodeURIComponent(S.user.id));
    if(!r.ok) throw Object.assign(new Error(await errMsg(r)), { http:r.status });
""","""    const r = await api('/rest/v1/progress?select=data,version,updated_at&user_id=eq.' + encodeURIComponent(S.user.id));
    if(!r.ok) throw await httpErr(r);
""")

# arabic messages instead of raw codes
rep("setStatus('error', 'loop'); return; }","setStatus('error', 'تعذّر تحميل بيانات الحساب بعد عدة محاولات — أعد فتح التطبيق.'); return; }")
rep("{ codisSaveSuspended = false; setStatus('error', 'storage'); return false; }","{ codisSaveSuspended = false; setStatus('error', 'تعذّر حفظ بيانات الحساب على هذا الجهاز (التخزين ممتلئ أو معطّل).'); return false; }")

# netFail
rep("""  function netFail(e){
    if(e && e.expired){ setStatus('expired'); return; }
    if(e && e.net){ setStatus('offline'); } else setStatus('error', e && e.message);
    retryMs = Math.min(retryMs ? retryMs * 2 : 5000, 120000); schedule(retryMs);
  }
""","""  function netFail(e){
    const c = classify(e);
    try{ console.warn('[CODIS sync]', c.st, (e && e.code) || '', (e && e.http) || '', e && e.message ? String(e.message).slice(0, 200) : ''); }catch(_){}
    if(c.st === 'expired'){ setStatus('expired'); return; }
    if(c.st === 'offline') setStatus('offline'); else setStatus('error', c.msg);
    if(c.perm) return;   // خطأ دائم (إعداد/صلاحيات): لا إعادة محاولة تلقائية — يدوياً عبر «مزامنة الآن»
    retryMs = Math.min(retryMs ? retryMs * 2 : 5000, 120000); schedule(retryMs);
  }
""")

# E: reload guard in reconcile
rep("codisSaveSuspended = true; try{ location.reload(); }catch(e){} return;","reloadGuarded(); return;")

# F: signIn / handleReturn
i0=t.index("  async function signIn(){\n    if(!configured)")
i1=t.index("  /* ---------- شاشة الدخول ---------- */")
new_auth = """  function authErrMsg(code, desc){
    const c = String(code || '').toLowerCase(), d = String(desc || '').toLowerCase();
    if(c === 'access_denied' || /access.denied|user denied|cancel/.test(d)) return 'تم إلغاء تسجيل الدخول.';
    if(/provider is not enabled|unsupported provider/.test(d)) return 'تسجيل الدخول بحساب Google غير مفعّل في إعدادات Supabase.';
    if(/exchange external code|invalid_client|client secret|client_id/.test(d)) return 'إعداد Google في Supabase غير صحيح (Client ID / Client Secret).';
    if(/redirect/.test(d)) return 'عنوان الرجوع غير مسموح في إعدادات Supabase (Redirect URLs).';
    if(/signups? not allowed|signup/.test(d)) return 'إنشاء حسابات جديدة معطّل في Supabase.';
    return 'تعذّر تسجيل الدخول — حاول مجدداً.';
  }
  const PKCE_TTL = 10 * 60 * 1000;
  async function signIn(){
    if(!configured){ showToast(CHK.msg || 'خدمة الحسابات غير مهيّأة بعد', 'var(--warning)'); return; }
    if(signingIn) return;
    signingIn = true;
    try{
      if(navigator.onLine === false){ showToast('لا يوجد اتصال بالإنترنت — تسجيل الدخول يحتاج اتصالاً.', 'var(--warning)'); signingIn = false; return; }
      /* فحص مسبق: يمنع الانتقال إلى صفحة خطأ JSON خام إن كان المزوّد غير مفعّل أو المفتاح مرفوضاً */
      let pre;
      try{ pre = await raw('/auth/v1/settings', { auth:false, timeout:8000 }); }
      catch(e){ showToast('تعذّر الوصول إلى خادم الحسابات — تحقق من الاتصال ومن عنوان المشروع.', 'var(--danger)'); signingIn = false; return; }
      if(pre.status === 401 || pre.status === 403){ showToast('المفتاح العام مرفوض من Supabase — تحقق من anon / publishable key.', 'var(--danger)'); signingIn = false; return; }
      if(pre.ok){
        let j = null; try{ j = await pre.json(); }catch(e){}
        if(j && j.external && j.external.google === false){ showToast(authErrMsg('', 'provider is not enabled'), 'var(--danger)'); signingIn = false; return; }
      }
      const ver = b64u(crypto.getRandomValues(new Uint8Array(48)));
      const ch = b64u(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ver)));
      if(!wr(K_PKCE, JSON.stringify({ v:ver, t:Date.now() }))){ showToast('تعذّر حفظ بيانات الدخول على الجهاز (التخزين ممتلئ أو معطّل).', 'var(--danger)'); signingIn = false; return; }
      const back = location.origin + location.pathname;
      const g = document.getElementById('codis-gate');
      if(g && g.classList.contains('is-open')) gateBusy(true); else showToast('جارٍ التحويل إلى Google…', 'var(--success)');
      location.href = cfg.url + '/auth/v1/authorize?provider=google&flow_type=pkce&code_challenge=' + ch + '&code_challenge_method=s256&redirect_to=' + encodeURIComponent(back);
    }catch(e){ console.warn('[CODIS auth] signIn failed:', e && e.message); showToast('تعذّر بدء تسجيل الدخول', 'var(--danger)'); signingIn = false; }
  }
  async function handleReturn(){
    const q = new URLSearchParams(location.search), h = new URLSearchParams((location.hash || '').replace(/^#/, ''));
    const errCode = q.get('error_code') || q.get('error') || h.get('error_code') || h.get('error');
    const errDesc = q.get('error_description') || h.get('error_description');
    const code = q.get('code');
    if(!errCode && !errDesc && !code && !h.get('access_token')) return false;
    try{ history.replaceState(null, '', location.pathname); }catch(e){}   // لا نترك code/tokens في العنوان (يمنع المعالجة المكرّرة عند إعادة التحميل)
    if(errCode || errDesc){ rm(K_PKCE); console.warn('[CODIS auth] callback error:', errCode || '', String(errDesc || '').slice(0, 200)); showToast(authErrMsg(errCode, errDesc), 'var(--danger)'); return false; }
    if(!code){ console.warn('[CODIS auth] ignored tokens in URL fragment (PKCE flow only)'); return false; }   // لا نقبل رموزاً وصلت عبر الرابط
    const pk = jparse(rd(K_PKCE), null); rm(K_PKCE);
    if(!pk || !pk.v || Date.now() - (pk.t || 0) > PKCE_TTL){ showToast('انتهت محاولة تسجيل الدخول أو لم تبدأ من هذا الجهاز — اضغط «تسجيل الدخول» مجدداً.', 'var(--warning)'); return false; }
    gateBusy(true);
    try{
      const r = await raw('/auth/v1/token?grant_type=pkce', { method:'POST', auth:false, body:{ auth_code:code, code_verifier:pk.v } });
      if(!r.ok) throw await httpErr(r);
      storeSession(await r.json());
      rm(K_GUEST); return true;
    }catch(e){
      console.warn('[CODIS auth] code exchange failed:', (e && e.http) || '', (e && e.code) || '', e && e.message ? String(e.message).slice(0, 200) : '');
      showToast(e && e.net ? 'تعذّر إكمال تسجيل الدخول — تحقق من الاتصال.' : (e && e.http === 400 ? 'رمز الدخول غير صالح أو انتهت صلاحيته — أعد المحاولة.' : 'تعذّر إكمال تسجيل الدخول — حاول مجدداً.'), 'var(--danger)');
      gateBusy(false); if(rd(K_GUEST) === '1') hideGate(); return false;
    }
  }

"""
t=t[:i0]+new_auth+t[i1:]

# G: hideGate reset
rep("function hideGate(){ const g = document.getElementById('codis-gate'); if(g) g.classList.remove('is-open'); document.documentElement.classList.remove('gate-open'); }",
    "function hideGate(){ const g = document.getElementById('codis-gate'); if(g){ g.classList.remove('is-open', 'is-busy'); ['gate-google','gate-guest'].forEach(i => { const e = g.querySelector('#' + i); if(e) e.disabled = false; }); const st = g.querySelector('#gate-status'); if(st) st.textContent = ''; } document.documentElement.classList.remove('gate-open'); }")

# H: signOut
rep("""      try{ await raw('/auth/v1/logout?scope=local', { method:'POST', headers:{ Authorization:'Bearer ' + S.session.access_token }, timeout:5000 }); }catch(e){}
      rm(STORE_KEY); rm(K_SESSION); rm(K_GUEST); saveMeta""","""      try{ const lo = await raw('/auth/v1/logout?scope=local', { method:'POST', headers:{ Authorization:'Bearer ' + S.session.access_token }, timeout:5000 }); if(!lo.ok) console.warn('[CODIS auth] server logout HTTP', lo.status, '(session cleared locally)'); }
      catch(e){ console.warn('[CODIS auth] server logout failed (session cleared locally):', e && e.message); }
      rm(STORE_KEY); rm(K_SESSION); rm(K_GUEST); rm(K_PKCE); saveMeta""")

# I: admin
rep("""    if(S.admin || window.__codisDevLoaded) return;
    try{
      const r = await api('/rest/v1/admins?select=user_id'); if(!r.ok) return;
      const rows = await r.json(); if(!rows || !rows.length) return;""","""    if(S.admin || window.__codisDevLoaded || !S.user) return;
    try{
      const r = await api('/rest/v1/admins?select=user_id'); if(!r.ok) return;
      const rows = await r.json(); if(!Array.isArray(rows) || !rows.some(x => x && x.user_id === S.user.id)) return;   // دفاع إضافي: صفّي أنا حصراً""")
rep("    }catch(e){ /* بدون شبكة: لا إضافة مطوّر */ }","    }catch(e){ console.debug('[CODIS] dev add-on not loaded:', e && e.message); }   // بدون شبكة: لا إضافة مطوّر")

# init: pageshow
rep("    window.addEventListener('online', () => {","    window.addEventListener('pageshow', ev => { if(ev.persisted){ signingIn = false; const g = document.getElementById('codis-gate'); if(g && g.classList.contains('is-busy')) gateBusy(false); } });\n    window.addEventListener('online', () => {")

# K: return object
rep("return { init, signIn, signOut, deleteAccount, syncNow, noteChange, state:S, configured, LABELS, fmt, meta, isAdmin:() => S.admin, _test:{ hasProgress } };",
    "return { init, signIn, signOut, deleteAccount, syncNow, noteChange, state:S, configured, configError: CHK.ok ? null : { code:CHK.code, msg:CHK.msg }, LABELS, fmt, meta, isAdmin:() => S.admin, _test:{ hasProgress, checkBackend, authErrMsg, classify, b64u, jwt } };")

# J: account page UI
rep("""    el.innerHTML = '<div class="settings-card"><p class="eco-note" style="margin:0">خدمة الحسابات والمزامنة غير مهيّأة في هذه النسخة بعد. يُضاف عنوان المشروع والمفتاح العام في إعداد CODIS_BACKEND (راجع دليل الإعداد). تبقى بياناتك محفوظة على هذا الجهاز كالمعتاد.</p></div>'; return;""",
"""    const why = A.configError && A.configError.msg ? esc(A.configError.msg) : 'خدمة الحسابات والمزامنة غير مهيّأة في هذه النسخة بعد.';
    el.innerHTML = '<div class="settings-card"><p class="eco-note" style="margin:0" role="status">' + why + ' (راجع دليل الإعداد). تبقى بياناتك محفوظة على هذا الجهاز كالمعتاد.</p></div>'; return;""")
rep("""    (m.lastSync ? '<div class="acct-last">آخر مزامنة: ' + esc(A.fmt(m.lastSync)) + '</div>' : '') +""",
"""    (m.lastSync ? '<div class="acct-last">آخر مزامنة: ' + esc(A.fmt(m.lastSync)) + '</div>' : '') +
    (S.err && S.status === 'error' ? '<div class="acct-last" role="alert">' + esc(S.err) + '</div>' : '') +""")

open(out,'wb').write(t.encode('utf-8'))
print('ok', orig_len, len(t))
