"""Profile photo: Google avatar taken automatically after login, shown instead of the account-row icon and the
settings tab icon; replaceable by a cropped photo from the device, or removable. Run AFTER tools/patch_profile.py.
Usage: python tools/patch_avatar.py <in.html> <out.html>      (refuses to run twice: marker CODIS-AVATAR)"""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-AVATAR' not in t, 'avatar patch already applied'
assert 'CODIS-PROFILE' in t, 'run tools/patch_profile.py first'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

# 1) module: the Google photo URL comes from the JWT claims (https only); repaint hook for the page-level code
rep("name:(c.user_metadata && (c.user_metadata.full_name || c.user_metadata.name)) || '' };",
    "name:(c.user_metadata && (c.user_metadata.full_name || c.user_metadata.name)) || '',\n"
    "      avatar:(function(m){ const u = m && (m.avatar_url || m.picture); return typeof u === 'string' && /^https:\\/\\//i.test(u) && u.length < 600 ? u : ''; })(c.user_metadata) };   // CODIS-AVATAR")
rep("  function paint(){\n    const b = document.getElementById('home-account-state');\n",
    "  function paint(){\n    try{ if(typeof window.codisAvatarSync === 'function') window.codisAvatarSync(); }catch(e){}   // CODIS-AVATAR\n    const b = document.getElementById('home-account-state');\n")

# 2) edit-profile must keep the photo fields
rep("data.profile = Object.assign({}, r.profile, { v:1, completedAt:old.completedAt || now, updatedAt:now });",
    "data.profile = Object.assign({}, old, r.profile, { v:1, completedAt:old.completedAt || now, updatedAt:now });")

# 3) styles
rep(".prof-btns [hidden]{display:none !important;}\n",
    ".prof-btns [hidden]{display:none !important;}\n"
    "/* CODIS-AVATAR — الصورة الشخصية */\n"
    ".codis-avatar{display:block;width:100%;height:100%;object-fit:cover;border-radius:50%;}\n"
    ".navicon.has-avatar,.ios-row-icon.has-avatar{overflow:visible;}\n"
    ".navicon.has-avatar > svg,.ios-row-icon.has-avatar > svg{display:none;}\n"
    ".navicon.has-avatar .codis-avatar{width:26px;height:26px;box-shadow:0 0 0 1.5px var(--glass-border);transition:box-shadow var(--dur-normal,.2s) var(--ease,ease);}\n"
    ".navbtn.active .navicon.has-avatar .codis-avatar{box-shadow:0 0 0 2px var(--aqua);}\n"
    ".ios-row-icon.has-avatar{background:none;box-shadow:none;border-radius:50%;}\n"
    ".ios-row-icon.has-avatar .codis-avatar{box-shadow:0 0 0 1px var(--aqua-a40);}\n"
    ".acct-avatar{position:relative;align-self:center;width:96px;height:96px;margin:2px 0 6px;padding:0;border:0;border-radius:50%;display:grid;place-items:center;background:var(--aqua-a14);color:var(--aqua);box-shadow:0 0 0 2px var(--aqua-a40);cursor:pointer;-webkit-tap-highlight-color:transparent;transition:transform var(--dur-fast,.15s) var(--ease,ease);}\n"
    ".acct-card .acct-id{display:flex;flex-direction:column;align-items:center;text-align:center;gap:2px;}\n"
    ".acct-card .acct-id .acct-mail{text-align:center;}\n"
    ".acct-avatar:active{transform:scale(.96);}\n"
    ".acct-avatar:focus-visible{outline:2px solid var(--aqua);outline-offset:4px;}\n"
    ".acct-avatar-ini{font-size:38px;font-weight:600;line-height:1;}\n"
    ".acct-avatar-cam{position:absolute;inset-inline-end:-2px;bottom:-2px;width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:var(--aqua);color:var(--on-aqua);border:3px solid var(--bg);}\n"
    "#codis-av-sheet,#codis-av-crop{position:fixed;inset:0;z-index:10002;display:flex;align-items:flex-end;justify-content:center;}\n"
    "#codis-av-crop{align-items:center;padding:24px;background:rgb(0 0 0 / .72);}\n"
    ".av-back{position:absolute;inset:0;background:rgb(0 0 0 / .55);animation:gateIn .18s ease both;}\n"
    ".av-panel{position:relative;width:min(100%,460px);display:flex;flex-direction:column;gap:10px;padding:10px 18px calc(var(--safe-b,0px) + 18px);background:var(--bg);border:1px solid var(--glass-border);border-bottom:0;border-radius:22px 22px 0 0;animation:avUp .22s var(--ease,ease-out) both;}\n"
    "@keyframes avUp{from{transform:translateY(24px);opacity:0}to{transform:none;opacity:1}}\n"
    ".av-grab{align-self:center;width:38px;height:4px;border-radius:2px;background:var(--glass-border);margin-bottom:4px;}\n"
    ".av-title{margin:0 0 4px;font-size:17px;text-align:center;}\n"
    ".av-remove{color:var(--danger-ink,var(--danger));}\n"
    ".av-crop-card{position:relative;width:min(100%,340px);display:flex;flex-direction:column;align-items:center;gap:14px;padding:18px;background:var(--bg);border:1px solid var(--glass-border);border-radius:var(--r-lg,20px);}\n"
    ".av-crop-view{width:260px;height:260px;border-radius:50%;overflow:hidden;box-shadow:0 0 0 2px var(--aqua);touch-action:none;cursor:grab;background:#000;}\n"
    ".av-crop-view canvas{display:block;width:260px;height:260px;}\n"
    ".av-zoom{width:100%;accent-color:var(--aqua);}\n"
    ".av-crop-btns{display:flex;gap:8px;width:100%;}.av-crop-btns .btn{flex:1;}\n"
    "@media (prefers-reduced-motion:reduce){.av-back,.av-panel{animation:none;}}\n")

# 4) page-level code (outside the module so module tests stay isolated)
rep("const CODIS_PROFILE_GENDERS = {",
r"""/* CODIS-AVATAR: الصورة الشخصية. المصدر بالأولوية: صورة مخصّصة (data.profile.photo، 256px، تُزامَن مع الحساب) ← صورة Google (من بيانات الجلسة)
   ← الأيقونة الأصلية. data.profile.photoMode: 'google' (افتراضي) | 'custom' | 'none'. تظهر للمسجّلين فقط؛ الضيف يبقى بالأيقونات. */
const CODIS_AV_MAX_FILE = 15 * 1024 * 1024;
let codisAvBad = '';   // رابط صورة Google الذي فشل تحميله (حظر شبكة/ريفيرر…) فنرجع للأيقونة بدل صورة مكسورة
function codisAvGoogle(){
  const u = CodisAccount.state && CodisAccount.state.user, a = u && u.avatar;
  if(!a || a === codisAvBad) return '';
  return a.replace(/=s\d+(-c)?$/, '=s256-c');
}
function codisAvSrc(){
  const S = CodisAccount.state; if(!S || !S.user) return '';
  const p = data && data.profile, mode = (p && p.photoMode) || 'google';
  if(mode === 'none') return '';
  if(mode === 'custom' && p.photo) return p.photo;
  return codisAvGoogle();
}
function codisAvImg(){
  const src = codisAvSrc(); if(!src) return '';
  return '<img class="codis-avatar" alt="" referrerpolicy="no-referrer" decoding="async" src="' + escapeHtml(src) + '" onerror="codisAvError()">';
}
function codisAvError(){
  const p = data && data.profile;
  if(!(p && p.photoMode === 'custom' && p.photo)){ const u = CodisAccount.state.user; codisAvBad = (u && u.avatar) || ''; }
  codisApplyAvatar();
}
function codisApplyAvatar(){
  try{
    const html = codisAvImg();
    const targets = [document.querySelector('.navbtn[data-page="settings"] .navicon'), document.querySelector('button.ios-row[onclick*="openSettingsCategory(\'account\')"] .ios-row-icon')];
    targets.forEach(el => {
      if(!el) return;
      const old = el.querySelector(':scope > img.codis-avatar'); if(old) old.remove();
      if(html){ el.insertAdjacentHTML('afterbegin', html); el.classList.add('has-avatar'); } else el.classList.remove('has-avatar');
    });
  }catch(e){ console.warn('[CODIS avatar]', e && e.message); }
}
window.codisAvatarSync = codisApplyAvatar;
function codisAvatarBlock(){
  const S = CodisAccount.state, nm = String((data.profile && data.profile.name) || (S.user && S.user.name) || '').trim();
  const inner = codisAvImg() || '<span class="acct-avatar-ini" aria-hidden="true">' + escapeHtml(Array.from(nm)[0] || '•') + '</span>';
  return '<button type="button" class="acct-avatar" onclick="codisOpenAvatarSheet()" aria-label="تغيير الصورة الشخصية">' + inner +
    '<span class="acct-avatar-cam" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h3l1.6-2h6.8L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg></span></button>';
}
function codisAvRefresh(){
  codisApplyAvatar();
  try{ const pg = document.getElementById('settings-page-account'); if(pg && pg.style.display !== 'none') codisRenderAccountPage(); }catch(e){}
}
function codisAvSave(patch){
  data.profile = Object.assign({}, data.profile || {}, patch, { updatedAt:Date.now() });
  if(saveData() === false){ showToast('تعذّر الحفظ على هذا الجهاز — حاول مجدداً.', 'var(--danger)'); return false; }   // يُزامَن تلقائياً
  codisAvRefresh(); return true;
}
function codisCloseAvatarSheet(){ const s = document.getElementById('codis-av-sheet'); if(s) s.remove(); }
function codisOpenAvatarSheet(){
  codisCloseAvatarSheet();
  const S = CodisAccount.state; if(!S || !S.user) return;
  const mode = (data.profile && data.profile.photoMode) || 'google', hasG = !!(S.user.avatar && S.user.avatar !== codisAvBad), cur = codisAvSrc();
  const s = document.createElement('div'); s.id = 'codis-av-sheet'; s.setAttribute('role', 'dialog'); s.setAttribute('aria-modal', 'true'); s.setAttribute('aria-labelledby', 'av-title');
  s.innerHTML = '<div class="av-back" data-av="close"></div><div class="av-panel"><div class="av-grab" aria-hidden="true"></div><h2 class="av-title" id="av-title">الصورة الشخصية</h2>' +
    '<button type="button" class="btn btn-primary" data-av="pick">اختيار صورة من جهازك</button>' +
    (hasG && !(mode === 'google') ? '<button type="button" class="btn btn-secondary" data-av="google">استخدام صورة حساب Google</button>' : '') +
    (cur ? '<button type="button" class="btn btn-secondary av-remove" data-av="none">إزالة الصورة</button>' : '') +
    '<button type="button" class="btn btn-secondary" data-av="close">إلغاء</button>' +
    '<input type="file" id="av-file" accept="image/*" hidden></div>';
  document.body.appendChild(s);
  const f = s.querySelector('#av-file');
  f.addEventListener('change', () => { const file = f.files && f.files[0]; codisCloseAvatarSheet(); if(file) codisOpenCrop(file); });
  s.addEventListener('click', ev => {
    const b = ev.target.closest('[data-av]'); if(!b) return; const a = b.getAttribute('data-av');
    if(a === 'close') codisCloseAvatarSheet();
    else if(a === 'pick') f.click();
    else if(a === 'google'){ codisCloseAvatarSheet(); codisAvBad = ''; if(codisAvSave({ photoMode:'google', photo:'' })) showToast('تم استخدام صورة Google', 'var(--success)', 'check'); }
    else if(a === 'none'){ codisCloseAvatarSheet(); if(codisAvSave({ photoMode:'none', photo:'' })) showToast('تمت إزالة الصورة', 'var(--success)', 'check'); }
  });
  s.addEventListener('keydown', ev => { if(ev.key === 'Escape') codisCloseAvatarSheet(); });
  setTimeout(() => { try{ s.querySelector('[data-av="pick"]').focus(); }catch(e){} }, 50);
}
async function codisOpenCrop(file){
  if(!/^image\//.test(file.type || '')){ showToast('اختر ملف صورة.', 'var(--warning)'); return; }
  if(file.size > CODIS_AV_MAX_FILE){ showToast('الصورة كبيرة جداً (الحد الأقصى 15 ميغابايت).', 'var(--warning)'); return; }
  let img;
  try{ img = await createImageBitmap(file, { imageOrientation:'from-image' }); }
  catch(e){
    try{ img = await new Promise((ok, no) => { const u = URL.createObjectURL(file), i = new Image(); i.onload = () => { URL.revokeObjectURL(u); ok(i); }; i.onerror = () => { URL.revokeObjectURL(u); no(new Error('decode')); }; i.src = u; }); }
    catch(e2){ showToast('تعذّرت قراءة الصورة — جرّب صيغة JPG أو PNG.', 'var(--danger)'); return; }
  }
  const W = img.width, H = img.height, V = 260; if(!W || !H){ showToast('تعذّرت قراءة الصورة.', 'var(--danger)'); return; }
  const base = V / Math.min(W, H); let s = base, ox = (V - W * s) / 2, oy = (V - H * s) / 2;
  const el = document.createElement('div'); el.id = 'codis-av-crop'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('aria-labelledby', 'avc-title');
  el.innerHTML = '<div class="av-crop-card"><h2 class="av-title" id="avc-title">اضبط الصورة</h2><div class="av-crop-view"><canvas id="avc-cv" width="' + V + '" height="' + V + '"></canvas></div>' +
    '<input class="av-zoom" id="avc-zoom" dir="ltr" type="range" min="1" max="3" step="0.01" value="1" aria-label="تكبير الصورة">' +
    '<div class="av-crop-btns"><button type="button" class="btn btn-primary" id="avc-ok">حفظ</button><button type="button" class="btn btn-secondary" id="avc-cancel">إلغاء</button></div></div>';
  document.body.appendChild(el);
  const cv = el.querySelector('#avc-cv'), ctx = cv.getContext('2d'), zoom = el.querySelector('#avc-zoom');
  const clamp = () => { ox = Math.min(0, Math.max(V - W * s, ox)); oy = Math.min(0, Math.max(V - H * s, oy)); };
  const draw = () => { ctx.fillStyle = '#05070B'; ctx.fillRect(0, 0, V, V); ctx.drawImage(img, ox, oy, W * s, H * s); };
  const close = () => { el.remove(); try{ if(img.close) img.close(); }catch(e){} };
  draw();
  zoom.addEventListener('input', () => { const cx = (V / 2 - ox) / s, cy = (V / 2 - oy) / s; s = base * parseFloat(zoom.value); ox = V / 2 - cx * s; oy = V / 2 - cy * s; clamp(); draw(); });
  let drag = null; const view = el.querySelector('.av-crop-view');
  view.addEventListener('pointerdown', ev => { drag = { x:ev.clientX, y:ev.clientY }; try{ view.setPointerCapture(ev.pointerId); }catch(e){} view.style.cursor = 'grabbing'; });
  view.addEventListener('pointermove', ev => { if(!drag) return; ox += ev.clientX - drag.x; oy += ev.clientY - drag.y; drag = { x:ev.clientX, y:ev.clientY }; clamp(); draw(); });
  const end = () => { drag = null; view.style.cursor = ''; };
  view.addEventListener('pointerup', end); view.addEventListener('pointercancel', end);
  el.querySelector('#avc-cancel').addEventListener('click', close);
  el.addEventListener('keydown', ev => { if(ev.key === 'Escape') close(); });
  el.querySelector('#avc-ok').addEventListener('click', () => {
    const out = document.createElement('canvas'); out.width = out.height = 256; const o = out.getContext('2d'), r = 256 / V;
    o.fillStyle = '#05070B'; o.fillRect(0, 0, 256, 256); o.drawImage(img, ox * r, oy * r, W * s * r, H * s * r);
    let url = ''; try{ url = out.toDataURL('image/jpeg', 0.86); }catch(e){}
    if(!url || url.length < 200){ showToast('تعذّر تجهيز الصورة.', 'var(--danger)'); return; }
    if(codisAvSave({ photoMode:'custom', photo:url })){ close(); showToast('تم تغيير الصورة', 'var(--success)', 'check'); }
  });
  setTimeout(() => { try{ zoom.focus(); }catch(e){} }, 50);
}
window.codisOpenAvatarSheet = codisOpenAvatarSheet;
const CODIS_PROFILE_GENDERS = {""")

# 5) account page: big avatar on top of the card
rep("acct-card\"><div class=\"acct-id\">", "acct-card\">' + codisAvatarBlock() + '<div class=\"acct-id\">")

open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
