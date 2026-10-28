"""Adds the post-login profile screen (name, age, optional gender/city) to CODIS_FINAL.html.
Usage: python tools/patch_profile.py <in.html> <out.html>      (run AFTER tools/patch.py)
Each anchor must match exactly once; the script refuses to run twice (marker CODIS-PROFILE)."""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-PROFILE' not in t, 'profile patch already applied'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

# 1) data model: data.profile is an object or null (kept by backup/restore + cloud sync like any other key)
rep("  if(!d.settings || typeof d.settings !== 'object' || Array.isArray(d.settings)) d.settings = {};\n",
    "  if(!d.profile || typeof d.profile !== 'object' || Array.isArray(d.profile)) d.profile = null;   // CODIS-PROFILE: معلومات المستخدم بعد الدخول (name, age, gender, city)\n"
    "  if(!d.settings || typeof d.settings !== 'object' || Array.isArray(d.settings)) d.settings = {};\n")

# 2) styles
rep("#codis-gate.is-busy .gate-card{opacity:.8;}\n",
    "#codis-gate.is-busy .gate-card{opacity:.8;}\n"
    "/* CODIS-PROFILE — شاشة معلومات المستخدم بعد الدخول */\n"
    "#codis-profile{position:fixed;inset:0;z-index:10001;display:none;align-items:center;justify-content:center;padding:calc(var(--safe-t,0px) + 24px) 24px calc(var(--safe-b,0px) + 24px);background:radial-gradient(60% 42% at 50% 40%,rgb(var(--aqua-rgb) / .10),transparent 72%),var(--bg);overflow:auto;}\n"
    "#codis-profile.is-open{display:flex;animation:gateIn .22s var(--ease,ease-out) both;}\n"
    ".prof-card{width:min(100%,400px);display:flex;flex-direction:column;gap:14px;text-align:start;}\n"
    ".prof-card .gate-mark,.prof-card .gate-title,.prof-card .gate-sub{text-align:center;}\n"
    ".prof-field{display:flex;flex-direction:column;gap:6px;font-size:14px;}\n"
    ".prof-field input,.prof-field select{min-height:46px;padding:10px 14px;font:inherit;font-size:16px;color:var(--text);background:rgb(var(--hi-rgb) / .05);border:1px solid var(--glass-border);border-radius:var(--r-md);width:100%;box-sizing:border-box;}\n"
    ".prof-field input:focus-visible,.prof-field select:focus-visible{outline:2px solid var(--aqua);outline-offset:2px;}\n"
    ".prof-opt{color:var(--text-2);font-size:12px;}\n"
    ".prof-err{margin:0;min-height:18px;color:var(--danger-ink,var(--danger));font-size:13px;}\n"
    ".prof-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;}\n"
    ".prof-btns{display:flex;flex-direction:column;gap:8px;}\n"
    ".prof-btns [hidden]{display:none !important;}\n")

# 3) module hook: after login + successful sync, let the page decide whether to ask for the profile
rep("    loadAdmin();\n    if(returned) showToast('تم تسجيل الدخول', 'var(--success)', 'check');\n  }\n",
    "    loadAdmin();\n    if(returned) showToast('تم تسجيل الدخول', 'var(--success)', 'check');\n"
    "    try{ if(typeof window.codisAfterLogin === 'function') window.codisAfterLogin(S.status); }catch(e){ console.warn('[CODIS profile]', e && e.message); }\n  }\n")

# 4) page-level UI (outside the module, so the module tests stay isolated)
rep("function codisRenderAccountPage(){\n",
r"""/* CODIS-PROFILE: شاشة «معلوماتك» — الاسم والعمر إلزاميان، الجنس والمدينة اختياريان. تُحفظ في data.profile فتُزامَن مع الحساب.
   تظهر مرة واحدة بعد أول دخول ناجح (ومزامنة ناجحة حتى لا تُسأل على جهاز ثانٍ وهي محفوظة بالسحابة)، وتُعدَّل لاحقاً من الإعدادات ← الحساب. */
const CODIS_PROFILE_GENDERS = { male:'ذكر', female:'أنثى' };
function codisProfileDone(){ return !!(data && data.profile && data.profile.completedAt); }
function codisProfileValidate(v){
  const toEn = s => String(s == null ? '' : s).replace(/[٠-٩]/g, c => String(c.charCodeAt(0) - 0x0660)).replace(/[۰-۹]/g, c => String(c.charCodeAt(0) - 0x06F0));
  const name = String(v.name || '').replace(/\s+/g, ' ').trim();
  if(name.length < 2) return { error:'اكتب اسمك (حرفان على الأقل).', field:'name' };
  if(name.length > 40) return { error:'الاسم طويل (الحد الأقصى 40 حرفاً).', field:'name' };
  const ageTxt = toEn(v.age).trim();
  if(!/^\d{1,3}$/.test(ageTxt)) return { error:'اكتب عمرك بالأرقام.', field:'age' };
  const age = parseInt(ageTxt, 10);
  if(age < 5 || age > 120) return { error:'العمر يجب أن يكون بين 5 و120.', field:'age' };
  const gender = CODIS_PROFILE_GENDERS[v.gender] ? v.gender : '';
  const city = String(v.city || '').replace(/\s+/g, ' ').trim();
  if(city.length > 40) return { error:'اسم المدينة طويل (الحد الأقصى 40 حرفاً).', field:'city' };
  return { ok:true, profile:{ name:name, age:age, gender:gender, city:city } };
}
function codisCloseProfile(){
  const p = document.getElementById('codis-profile'); if(p) p.classList.remove('is-open');
  document.documentElement.classList.remove('gate-open');
}
function codisOpenProfile(edit){
  let p = document.getElementById('codis-profile');
  if(!p){
    p = document.createElement('div'); p.id = 'codis-profile'; p.setAttribute('role', 'dialog'); p.setAttribute('aria-modal', 'true'); p.setAttribute('aria-labelledby', 'prof-title');
    p.innerHTML = '<form class="prof-card" id="prof-form" novalidate><div class="gate-mark" aria-hidden="true">CODIS</div><h1 id="prof-title" class="gate-title"></h1><p class="gate-sub" id="prof-sub"></p>' +
      '<label class="prof-field"><span>الاسم</span><input type="text" id="prof-name" maxlength="40" autocomplete="name" enterkeyhint="next"></label>' +
      '<div class="prof-row"><label class="prof-field"><span>العمر</span><input type="text" id="prof-age" inputmode="numeric" maxlength="3" autocomplete="off" enterkeyhint="next"></label>' +
      '<label class="prof-field"><span>الجنس <span class="prof-opt">(اختياري)</span></span><select id="prof-gender"><option value="">—</option><option value="male">ذكر</option><option value="female">أنثى</option></select></label></div>' +
      '<label class="prof-field"><span>المدينة <span class="prof-opt">(اختياري)</span></span><input type="text" id="prof-city" maxlength="40" autocomplete="address-level2" enterkeyhint="done"></label>' +
      '<p class="prof-err" id="prof-err" role="alert"></p>' +
      '<div class="prof-btns"><button type="submit" class="btn btn-primary" id="prof-save"></button><button type="button" class="btn btn-secondary" id="prof-cancel" hidden>إلغاء</button></div>' +
      '<p class="gate-note">معلوماتك تُحفظ في حسابك فقط وتُزامَن مع بياناتك، ويمكنك تعديلها لاحقاً من الإعدادات ← الحساب.</p></form>';
    document.body.appendChild(p);
    p.querySelector('#prof-form').addEventListener('submit', ev => { ev.preventDefault(); codisSubmitProfile(); });
    p.querySelector('#prof-cancel').addEventListener('click', codisCloseProfile);
    p.addEventListener('keydown', ev => { if(ev.key === 'Escape' && !p.querySelector('#prof-cancel').hidden) codisCloseProfile(); });
  }
  const cur = (data && data.profile) || {}, S = CodisAccount.state;
  p.dataset.edit = edit ? '1' : '';
  p.querySelector('#prof-title').textContent = edit ? 'تعديل معلوماتي' : 'عرّفنا عليك';
  p.querySelector('#prof-sub').textContent = edit ? 'غيّر ما تريد ثم احفظ.' : 'قبل ما تبدأ، اكتب معلوماتك الأساسية — تأخذ نصف دقيقة.';
  p.querySelector('#prof-save').textContent = edit ? 'حفظ التعديلات' : 'حفظ ومتابعة';
  p.querySelector('#prof-cancel').hidden = !edit;
  p.querySelector('#prof-name').value = cur.name || (S && S.user && S.user.name) || '';
  p.querySelector('#prof-age').value = cur.age != null ? String(cur.age) : '';
  p.querySelector('#prof-gender').value = cur.gender || '';
  p.querySelector('#prof-city').value = cur.city || '';
  p.querySelector('#prof-err').textContent = '';
  p.classList.add('is-open'); document.documentElement.classList.add('gate-open');
  setTimeout(() => { try{ p.querySelector(cur.name ? '#prof-age' : '#prof-name').focus(); }catch(e){} }, 60);
}
function codisSubmitProfile(){
  const p = document.getElementById('codis-profile'); if(!p) return;
  const r = codisProfileValidate({ name:p.querySelector('#prof-name').value, age:p.querySelector('#prof-age').value, gender:p.querySelector('#prof-gender').value, city:p.querySelector('#prof-city').value });
  const er = p.querySelector('#prof-err');
  if(!r.ok){ er.textContent = r.error; try{ p.querySelector('#prof-' + r.field).focus(); }catch(e){} return; }
  const now = Date.now(), old = data.profile || {};
  data.profile = Object.assign({}, r.profile, { v:1, completedAt:old.completedAt || now, updatedAt:now });
  if(saveData() === false){ er.textContent = 'تعذّر الحفظ على هذا الجهاز — حاول مجدداً.'; return; }   // يُزامَن تلقائياً عبر saveData ← CodisAccount.noteChange
  codisCloseProfile();
  showToast(p.dataset.edit ? 'تم حفظ التعديلات' : 'أهلاً ' + r.profile.name, 'var(--success)', 'check');
  try{ if(document.getElementById('settings-page-account') && document.getElementById('settings-page-account').style.display !== 'none') codisRenderAccountPage(); }catch(e){}
}
window.codisAfterLogin = function(status){
  try{
    const S = CodisAccount.state;
    if(!S || !S.user || status !== 'synced' || codisProfileDone()) return;   // لا نسأل قبل التأكد من المزامنة: قد تكون معلوماتك محفوظة بالسحابة
    codisOpenProfile(false);
  }catch(e){ console.warn('[CODIS profile]', e && e.message); }
};
window.codisOpenProfile = codisOpenProfile;
function codisRenderAccountPage(){
""")

# 5) account page: show profile line + edit button
rep("'<div class=\"settings-card acct-card\"><div class=\"acct-id\"><div class=\"acct-name\">' + esc(S.user.name || 'حسابي') + '</div>",
    "'<div class=\"settings-card acct-card\"><div class=\"acct-id\"><div class=\"acct-name\">' + esc((data.profile && data.profile.name) || S.user.name || 'حسابي') + '</div>"
    "' + (data.profile && data.profile.age ? '<div class=\"acct-last\">' + esc(String(data.profile.age)) + ' سنة' + (data.profile.city ? ' · ' + esc(data.profile.city) : '') + '</div>' : '') + '")
rep("'<div class=\"acct-actions\"><button type=\"button\" class=\"btn btn-secondary\" onclick=\"CodisAccount.syncNow()\">مزامنة الآن</button>' +",
    "'<div class=\"acct-actions\"><button type=\"button\" class=\"btn btn-secondary\" onclick=\"codisOpenProfile(true)\">تعديل معلوماتي</button><button type=\"button\" class=\"btn btn-secondary\" onclick=\"CodisAccount.syncNow()\">مزامنة الآن</button>' +")

open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
