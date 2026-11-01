#!/usr/bin/env python3
"""CODIS-TIMERS (3.11.0، بعد patch_v17.py): طبقة مشتركة لاستخراج المدة من النص (CodisDuration) ومؤقتات حقيقية بطابع زمني مطلق (CodisTimers)
 للمكافآت ذات المدة («ساعة سوشل ميديا» ← 60 د: «استخدام» يبدأ العد وعند الانتهاء تُعلَّم مستخدمة) وللمهام ذات المدة (زر «ابدأ المهمة»)،
 إشعارات النظام عبر Service Worker + اشتراك Web Push (CodisPush) والخادم في sql/codis_push.sql و supabase/functions/codis-push،
 مشهد شراء سينمائي يتصاعد بمستوى السعر المدفوع فعلاً (CodisRevealLevels) مع «استخدام / تخزين» (CodisBuyCine)،
 سحب المهام لإعادة ترتيبها بالضغط المطوّل مع منع تحديد النص (CodisTaskDrag)، ومعاينة بطاقة المتجر بالضغط المطوّل (CodisCardPeek).
 الاقتصاد والمخزون والصناديق لا تُمَسّ إلا بحارسين: لا بيع لمكافأة مؤقتها شغّال (عبر CodisLimits) و econUse يوجّه المؤقتة للمؤقت.
 الاستعمال: py -3 tools/patch_v18.py <in> <out>"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-TIMERS' in s: sys.exit('already patched (CODIS-TIMERS)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# ---------- 1) PWA: روابط المانيفست/الآيفون (فُقدت مع استبدال index.html في 2026-10-21) + المفتاح العام لـ Web Push ----------
rep('<title>CODIS</title>', '''<title>CODIS</title>
<!-- CODIS-TIMERS: PWA (التثبيت على الشاشة الرئيسية شرط إشعارات الآيفون) — المفتاح العام VAPID فقط هنا؛ الخاص في أسرار Supabase -->
<meta name="codis-vapid-public-key" content="">
<link rel="manifest" href="manifest.webmanifest">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="CODIS">
<link rel="apple-touch-icon" href="icon.svg">''', 'head')

# ---------- 2) الحساب: استدعاء دوال push_* فقط (نفس نمط adminCall) ----------
rep('adminCall(name, body){', '''pushCall(name, body){
    if(!S.user) throw Object.assign(new Error('not signed in'), { code:'28000' });
    if(!/^push_[a-z_]+$/.test(String(name))) throw new Error('bad function');
    return rpc(name, body || {});
  }
  async function adminCall(name, body){''', 'pushCall def')
rep('adminCall, state:S,', 'adminCall, pushCall, state:S,', 'pushCall export')

# ---------- 3) الاقتصاد: لا بيع لمكافأة مؤقتها شغّال (المطوّر معفى عبر CodisLimits) ----------
rep("    if(it.status === 'sold') return { ok:false, reason:'sold' };\n    if(it.status !== 'owned') return { ok:false, reason:'used' };",
    "    if(it.status === 'sold') return { ok:false, reason:'sold' };\n    if(it.status !== 'owned') return { ok:false, reason:'used' };\n    if(codisTimerBlocksSell(uid)) return { ok:false, reason:'inuse' };", 'sellCheck guard')
rep("  if(r.reason === 'empty' || r.reason === 'sold' || r.reason === 'used' || r.reason === 'notowned') return 'هذي المكافآت ما عادت بحوزتك';",
    "  if(r.reason === 'empty' || r.reason === 'sold' || r.reason === 'used' || r.reason === 'notowned') return 'هذي المكافآت ما عادت بحوزتك';\n  if(r.reason === 'inuse') return 'مكافأة مؤقتها شغّال — تنباع بعد ما يخلص';", 'sell fail text')
rep("(r.reason === 'sold' || r.reason === 'used' || r.reason === 'notowned') ? 'هذي المكافأة ما عدت بحوزتك' : 'تعذّر البيع'",
    "(r.reason === 'sold' || r.reason === 'used' || r.reason === 'notowned') ? 'هذي المكافأة ما عدت بحوزتك' : r.reason === 'inuse' ? 'مؤقتها شغّال — تنباع بعد ما يخلص' : 'تعذّر البيع'", 'sell toast')

# ---------- 4) الشراء: بعد نجاح العملية الفعلية فقط يبدأ المشهد بسعرها ونسختها ----------
rep("showToast('تم الشراء: ' + it.name + ' (−' + econFmt(r.price) + ') — صارت بحوزتك', 'var(--success)', 'gift');",
    "if(!CodisBuyCine.play(r, it)) showToast('تم الشراء: ' + it.name + ' (−' + econFmt(r.price) + ') — صارت بحوزتك', 'var(--success)', 'gift');", 'buy cinema')

# ---------- 5) الاستخدام: المكافأة ذات المدة تبدأ مؤقتاً بدل «استخدمتها» الفورية ----------
rep("""    if(!it || it.status !== 'owned'){ codisSfx('invalid', { ctx:'unavailable' }); return; }
    const ok = await codisConfirm(CodisCopy.useReward(it.name));""", """    if(!it || it.status !== 'owned'){ codisSfx('invalid', { ctx:'unavailable' }); return; }
    const _dur = CodisDuration.parse(it.name);
    if(_dur){   /* CODIS-TIMERS: مكافأة ذات مدة ← مؤقت حقيقي مرتبط بالنسخة نفسها */
      const _run = CodisTimers.active('reward', uid);
      if(_run){ showToast('مؤقتها شغّال — باقي ' + CodisTimers.fmt(_run.endsAt - Date.now()), 'var(--warning)'); return; }
      const okT = await codisConfirm({ title:'تبدأ «' + it.name + '»؟', message:'يبدأ مؤقت ' + CodisDuration.label(_dur.min) + ' من الآن.', detail:'لما يخلص الوقت تنعلَّم المكافأة كمستخدَمة ويوصلك إشعار. ما تنباع وهي شغّالة.', icon:'check', confirmText:'ابدأ الآن', danger:false });
      if(!okT) return;
      const rt = codisRewardTimerStart(uid);
      if(rt.ok){ codisSfx('confirm', { ctx:'use' }); showToast('بدأ المؤقت: ' + CodisDuration.label(_dur.min), 'var(--success)', 'check'); CodisPush.nudge(); }
      else { codisSfx('invalid', { ctx:'unavailable' }); showToast(rt.reason === 'save' ? 'تعذّر الحفظ — ما بدأ المؤقت' : 'تعذّر بدء المؤقت', 'var(--warning)'); }
      return;
    }
    const ok = await codisConfirm(CodisCopy.useReward(it.name));""", 'econUse timed')

# ---------- 6) المخزون: زر الاستخدام/العد التنازلي + منع البيع أثناء المؤقت ----------
rep("const sv = CodisInventory.sellValue(it), busy = econSellBusy, can = sv > 0, on = !!econSelSet[it.uid], uid = escapeHtml(it.uid);",
    "const sv = CodisInventory.sellValue(it), busy = econSellBusy, can = sv > 0 && !codisTimerBlocksSell(it.uid), on = !!econSelSet[it.uid], uid = escapeHtml(it.uid);", 'owned can')
rep("""'<button type="button" class="chip-act" ' + (busy ? 'disabled' : '') + ' onclick="econUse(\\'' + uid + '\\')">استخدمتها</button></div></div>';""",
    """codisOwnUseBtnHtml(it, uid, busy) + '</div></div>';""", 'owned use btn')
cap_old = "'<div class=\"st-cap\"><span class=\"shop-name\" dir=\"auto\">' + escapeHtml(it.name) + '</span></div>'"
rep(cap_old, "'<div class=\"st-cap\"><span class=\"shop-name\" dir=\"auto\">' + escapeHtml(it.name) + '</span>' + codisDurBadgeHtml(it.name) + '</div>'", 'caption badge', 2)
rep("codisStickerThumbHtml(it.stickerId) + '<span class=\"eco-item-name\">' + escapeHtml(it.name) + '</span></div>'",
    "codisStickerThumbHtml(it.stickerId) + '<span class=\"eco-item-name\">' + escapeHtml(it.name) + '</span>' + codisDurBadgeHtml(it.name) + '</div>'", 'settings badge')

# ---------- 7) المهام: سطر المؤقت داخل البطاقة (العمليات والأستاذ) ----------
rep("""    ${meta}
    ${partial}""", """    ${meta}
    ${codisTaskTimerHtml(task)}
    ${partial}""", 'task timer row')

# ---------- 8) الإشعارات: إشعار النظام عبر Service Worker بدل new Notification + نص الدعم ----------
rep("new Notification(notif.title || 'CODIS', { body: notif.message || '', tag: notif.groupKey || notif.id });",
    "CodisPush.show(notif.title || 'CODIS', notif.message || '', notif.groupKey || notif.id);", 'browser notify')
rep("  if(browserNote) browserNote.style.display = supported ? 'none' : 'block';",
    "  if(browserNote){ browserNote.style.display = supported ? 'none' : 'block'; if(!supported) browserNote.textContent = CodisPush.unsupportedText(); }", 'note text')
rep("""      data.notifications.settings.browserEnabled = true;
    }catch(e){ el.checked = false; data.notifications.settings.browserEnabled = false; }""", """      data.notifications.settings.browserEnabled = true;
      CodisPush.enable().then(r=>{ showToast(r.ok ? 'انفعلت الإشعارات على هذا الجهاز' + (r.push ? ' — وتوصل حتى لو التطبيق مسكّر' : '') : 'انفعلت إشعارات الجهاز', 'var(--success)', 'check'); });
    }catch(e){ el.checked = false; data.notifications.settings.browserEnabled = false; }""", 'enable push')
rep("""      if(perm !== 'granted'){
        el.checked = false;""", """      if(perm !== 'granted'){
        if(perm === 'denied') showToast('الإذن مرفوض من المتصفح — فعّله من إعدادات الموقع/التطبيق ثم ارجع', 'var(--warning)');
        el.checked = false;""", 'denied hint')
rep('<div class="settings-card-desc">تظهر والتطبيق مفتوح بالخلفية فقط، ولا تصل بعد إغلاقه.</div>',
    '<div class="settings-card-desc">تنبيهات الجهاز لانتهاء المؤقتات والأحداث المهمة. على الآيفون: ثبّت CODIS على الشاشة الرئيسية أولاً.</div>', 'notif desc')

# ---------- 9) رجوع النظام يسكّر المشاهد الجديدة أولاً ----------
rep("  if(econBulkZoomEl) return { act:econBulkZoomClose, el:econBulkZoomEl };",
    "  if(CodisBuyCine.isOpen()) return { act:CodisBuyCine.keep, el:CodisBuyCine.el() };\n  if(CodisCardPeek.isOpen()) return { act:CodisCardPeek.close, el:CodisCardPeek.el() };\n  if(econBulkZoomEl) return { act:econBulkZoomClose, el:econBulkZoomEl };", 'back layer')

JS = r"""/* ===== CODIS-TIMERS (3.11.0) ===== */
/* — حركة WAAPI بنفس قواعد CodisMotion (الداخلي غير مُصدَّر): تقليل الحركة ← تلاشٍ قصير فقط بلا تحريك، والمنتهية تُبلَّغ مرة — */
function codisAnim(el, kf, o){
  o = o || {};
  if(!el || !el.animate){ if(o.done) o.done(null); return null; }
  if(CodisMotion.isReduced()){
    if(!kf.some(k=>k.opacity !== undefined)){ if(o.done) o.done(null); return null; }
    kf = kf.map(k=>{ const c = {}; if(k.opacity !== undefined) c.opacity = k.opacity; if(k.offset !== undefined) c.offset = k.offset; return c; });
    o = Object.assign({}, o, { dur:Math.min(o.dur || 140, 140), delay:0, ease:'linear' });
  }
  let a; try{ a = el.animate(kf, { duration:Math.max(1, o.dur || 1), delay:o.delay || 0, easing:o.ease || 'linear', fill:o.fill || 'backwards' }); }catch(e){ if(o.done) o.done(null); return null; }
  if(o.done) a.addEventListener('finish', ()=>o.done(a));
  return a;
}
/* — المدة من النص: طبقة واحدة للمكافآت والمهام. تحتاج وحدة زمنية صريحة (رقم وحده لا يكفي)؛ «ساعة يد/ساعة جديدة» ليست مدة — */
const CodisDuration = (function(){
  'use strict';
  const S = '(?:^|[^\\u0600-\\u06FFa-z0-9])', B = '(?![\\u0600-\\u06FFa-z])';
  const HR = '(?:ساعات|ساعه|hours?|hrs?|hr|h)', MN = '(?:دقيقتين|دقيقه|دقائق|دقايق|minutes?|mins?|min|m)';
  const NUMW = { 'واحده':1, 'وحده':1, 'واحد':1, 'اثنتين':2, 'اثنين':2, 'ثنتين':2, 'ثلاثه':3, 'ثلاث':3, 'تلاث':3, 'اربعه':4, 'اربع':4, 'خمسه':5, 'خمس':5,
    'سته':6, 'ست':6, 'سبعه':7, 'سبع':7, 'ثمانيه':8, 'ثماني':8, 'ثمان':8, 'تسعه':9, 'تسع':9, 'عشره':10, 'عشر':10, 'ربعطعش':14, 'خمسطعش':15, 'عشرين':20, 'ثلاثين':30, 'اربعين':40, 'خمسين':50, 'ستين':60, 'تسعين':90 };
  const WORDS = Object.keys(NUMW).sort((a, b)=>b.length - a.length);
  const WATCH = /ساعه\s*(?:يد|ابل|ذكيه|جديده|حائط|جدار|منبه|رمليه|جيب|سمارت|رولكس|كاسيو|ماركه|رجاليه|نسائيه|كلاسيك)/;
  const re = (p)=>new RegExp(S + p + B);
  function mk(v, why){ v = Math.round(v); return (v >= 1 && v <= 1440) ? { min:v, why:why } : null; }
  function parse(text){
    const t = ' ' + codisNormText(text).replace(/\s+/g, ' ').trim() + ' ';
    if(!t.trim()) return null;
    let m;
    if((m = t.match(re('(\\d+(?:\\.\\d+)?)\\s*' + HR + '\\s*و\\s*(\\d+)\\s*' + MN)))) return mk(parseFloat(m[1]) * 60 + parseFloat(m[2]), m[1] + ' ساعة و' + m[2] + ' دقيقة');
    if((m = t.match(re('(\\d+)\\s*' + HR + '\\s*و\\s*(?:نص|نصف)')))) return mk(parseFloat(m[1]) * 60 + 30, m[1] + ' ساعة ونصف');
    if(re('(?:ساعتين|ساعتان)\\s*و\\s*(?:نص|نصف)').test(t)) return mk(150, 'ساعتان ونصف');
    if(re('(?:ساعتين|ساعتان)\\s*و\\s*ربع').test(t)) return mk(135, 'ساعتان وربع');
    if(re('ساعه\\s*و\\s*(?:نص|نصف)').test(t)) return mk(90, 'ساعة ونصف');
    if(re('ساعه\\s*و\\s*ربع').test(t)) return mk(75, 'ساعة وربع');
    if(re('ساعه\\s*(?:الا|إلا)\\s*ربع').test(t)) return mk(45, 'ساعة إلا ربع');
    if(/(^|[^a-z])half (an )?hour/.test(t)) return mk(30, 'half hour');
    if(/(^|[^a-z])(a )?quarter (of an )?hour/.test(t)) return mk(15, 'quarter hour');
    if(/(^|[^a-z])(an|one) hour([^a-z]|$)/.test(t)) return mk(60, 'one hour');
    if((m = t.match(re('(\\d+(?:\\.\\d+)?)\\s*' + HR)))) return mk(parseFloat(m[1]) * 60, m[1] + ' ساعة');
    if((m = t.match(re('(\\d+(?:\\.\\d+)?)\\s*' + MN)))) return mk(parseFloat(m[1]), m[1] + ' دقيقة');
    for(let i = 0; i < WORDS.length; i++){
      const w = WORDS[i];
      if(re(w + '\\s*' + HR).test(t)) return mk(NUMW[w] * 60, w + ' ساعات');
      if(re(w + '\\s*' + MN).test(t)) return mk(NUMW[w], w + ' دقائق');
    }
    if(re('(?:ساعتين|ساعتان)').test(t)) return mk(120, 'ساعتان');
    if(re('(?:نص|نصف)\\s*ساعه').test(t)) return mk(30, 'نصف ساعة');
    if(re('ربع\\s*ساعه').test(t)) return mk(15, 'ربع ساعة');
    if(re('دقيقتين').test(t)) return mk(2, 'دقيقتان');
    if(!WATCH.test(t) && re('ساعه').test(t)) return mk(60, 'ساعة');
    return null;
  }
  /* المهمة: النص أولاً (يحمل الكمية في مهام الخطة: «20 دقيقة قراءة»)، ثم الوحدة × الكمية بالمحلل القديم نفسه */
  function forTask(task){
    if(!task) return null;
    const a = parse(task.text); if(a) return a;
    if(task.unit && typeof codisParseMinutes === 'function'){ const r = codisParseMinutes(task.unit, task.qty); if(r && r.min > 0) return mk(r.min, r.why); }
    return null;
  }
  /* اسم الحدث بلا عبارة المدة: «تمرين 10 دقايق» ← «تمرين» */
  function strip(text){
    const o = String(text || '');
    const u = '(?:ساعات|ساعة|ساعه|ساعتين|ساعتان|دقيقتين|دقيقة|دقيقه|دقائق|دقايق|hours?|hrs?|minutes?|mins?)';
    const n = '(?:[0-9٠-٩]+(?:[.,٫][0-9٠-٩]+)?|نص|نصف|ربع|' + WORDS.join('|') + ')';
    const r = o.replace(new RegExp('(?:' + n + '\\s*)?' + u + '(?:\\s*(?:و|إلا|الا)\\s*(?:نص|نصف|ربع|[0-9٠-٩]+\\s*' + u + '))?', 'gi'), ' ').replace(/\s+/g, ' ').replace(/^[\s\-–—:،,.]+|[\s\-–—:،,.]+$/g, '').trim();
    return r || o.trim();
  }
  function label(min){
    min = Math.round(min);
    if(min === 30) return 'نص ساعة';
    if(min === 15) return 'ربع ساعة';
    if(min === 60) return 'ساعة';
    if(min === 90) return 'ساعة ونص';
    if(min === 120) return 'ساعتين';
    if(min < 60) return min === 1 ? 'دقيقة' : min === 2 ? 'دقيقتين' : min <= 10 ? min + ' دقائق' : min + ' دقيقة';
    const h = Math.floor(min / 60), r = min % 60;
    const hs = h === 1 ? 'ساعة' : h === 2 ? 'ساعتين' : h + (h <= 10 ? ' ساعات' : ' ساعة');
    return r ? hs + ' و' + label(r) : hs;
  }
  return { parse:parse, forTask:forTask, strip:strip, label:label };
})();

/* — المؤقتات: سجل واحد في البيانات (data.codisTimers) يُحفظ ويُزامَن مع الحساب. الوقت الحقيقي = endsAt − Date.now() دائماً؛
     setTimeout/setInterval للتنبيه والرسم فقط، فإغلاق التطبيق أو تجميد الصفحة لا يعيد المؤقت ولا يوقفه. كل انتهاء له معرّف حدث فريد (ev) — */
const CodisTimers = (function(){
  'use strict';
  const KEEP = 14 * 864e5, MAX = 300, H = {};
  let tmo = 0, ivl = 0, checked = null;
  function clean(x){
    if(!x || typeof x !== 'object') return null;
    const n = v=>{ v = Number(v); return isFinite(v) ? v : 0; };
    const t = { id:String(x.id || ''), ev:String(x.ev || ''), kind:(x.kind === 'reward' || x.kind === 'task') ? x.kind : '', ref:String(x.ref || ''), room:x.room === 'learn' ? 'learn' : x.room === 'tasks' ? 'tasks' : null,
      label:String(x.label || '').slice(0, 140), minutes:n(x.minutes), startedAt:n(x.startedAt), endsAt:n(x.endsAt), state:['running', 'done', 'cancelled'].indexOf(x.state) !== -1 ? x.state : 'cancelled',
      doneAt:n(x.doneAt) || null, notified:!!x.notified, server:!!x.server };
    return (t.id && t.ev && t.kind && t.ref && t.minutes > 0 && t.endsAt > t.startedAt) ? t : null;
  }
  function all(){
    let st = data.codisTimers;
    if(!st || typeof st !== 'object' || !Array.isArray(st.items)) st = data.codisTimers = { v:1, items:[] };
    if(checked !== st){ st.items = st.items.map(clean).filter(Boolean); checked = st; }
    return st.items;
  }
  const active = (kind, ref)=>all().find(t=>t.kind === kind && t.ref === String(ref) && t.state === 'running') || null;
  function latest(kind, ref){ const l = all().filter(t=>t.kind === kind && t.ref === String(ref) && t.state !== 'cancelled'); return l.length ? l[l.length - 1] : null; }
  const rid = p=>p + Date.now().toString(36) + Math.random().toString(36).slice(2, 9);
  function prune(){
    const now = Date.now(), L = all();
    for(let i = L.length - 1; i >= 0; i--) if(L[i].state !== 'running' && now - (L[i].doneAt || L[i].endsAt) > KEEP) L.splice(i, 1);
    while(L.length > MAX){ const k = L.findIndex(t=>t.state !== 'running'); if(k < 0) break; L.splice(k, 1); }
  }
  /* بدء: عملية واحدة قابلة للتكرار بأمان — إن وُجد مؤقت شغّال لنفس الهدف يُعاد هو نفسه */
  function start(o){
    const ex = active(o.kind, o.ref); if(ex) return { ok:true, timer:ex, existed:true };
    const min = Math.round(Number(o.minutes)); if(!(min >= 1 && min <= 1440)) return { ok:false, reason:'duration' };
    const now = Date.now();
    const t = { id:rid('tm_'), ev:rid('ev_'), kind:o.kind, ref:String(o.ref), room:o.room || null, label:String(o.label || '').slice(0, 140), minutes:min, startedAt:now, endsAt:now + min * 60000, state:'running', doneAt:null, notified:false, server:false };
    all().push(t); prune();
    if(!saveData()){ all().splice(all().indexOf(t), 1); return { ok:false, reason:'save' }; }
    CodisPush.schedule(t); arm(); paint();
    return { ok:true, timer:t };
  }
  function cancel(id){
    const t = all().find(x=>x.id === id); if(!t || t.state !== 'running') return false;
    t.state = 'cancelled'; t.doneAt = Date.now(); saveData(); CodisPush.unschedule(t); arm(); paint(); return true;
  }
  function announce(t, now){
    const h = H[t.kind], msg = h.message(t);
    CodisNotifications.add({ type:'TIMER_DONE', category:t.kind === 'task' ? 'task' : 'system', priority:'NORMAL', title:msg.title, message:msg.body, icon:'check', tone:'success',
      actionPage:t.kind === 'task' ? (t.room === 'learn' ? 'learn' : 'tasks') : null, uniqueKey:'timer|' + t.ev });
    if(t.notified) return;
    t.notified = true;
    /* إشعار النظام مرة واحدة: إذا كان الخادم مسؤولاً والتطبيق مسكّراً وقت الانتهاء فهو أرسله أصلاً */
    if(!(t.server && now - t.endsAt > 90000)) CodisPush.show(msg.title, msg.body, t.ev);
    CodisPush.unschedule(t);
    if(document.visibilityState === 'visible'){ showToast(msg.body, 'var(--success)', 'check'); try{ codisSfx('confirm', { ctx:'use' }); }catch(e){} }
  }
  function tick(){
    const now = Date.now(); let changed = false, kinds = {};
    all().forEach(t=>{
      if(t.state !== 'running') return;
      const h = H[t.kind];
      if(!h || (h.alive && !h.alive(t))){ t.state = 'cancelled'; t.doneAt = now; changed = true; kinds[t.kind] = 1; CodisPush.unschedule(t); return; }
      if(now < t.endsAt) return;
      t.state = 'done'; t.doneAt = t.endsAt; changed = true; kinds[t.kind] = 1;
      let ok = true; try{ ok = h.done(t) !== false; }catch(e){ console.error('CodisTimers.done:', e); }
      if(ok) announce(t, now);
    });
    if(changed){ saveData(); Object.keys(kinds).forEach(k=>{ try{ H[k].changed && H[k].changed(); }catch(e){} }); }
    arm(); paint();
  }
  function arm(){
    if(tmo){ clearTimeout(tmo); tmo = 0; }
    const run = all().filter(t=>t.state === 'running');
    if(run.length){ const next = Math.min.apply(null, run.map(t=>t.endsAt)); tmo = setTimeout(tick, Math.max(50, Math.min(next - Date.now() + 60, 2147483000))); }
    const want = run.length > 0 && document.visibilityState === 'visible';
    if(want && !ivl) ivl = setInterval(paint, 1000);
    if(!want && ivl){ clearInterval(ivl); ivl = 0; }
  }
  function fmt(ms){
    const s = Math.max(0, Math.ceil(ms / 1000)), h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60, p = v=>String(v).padStart(2, '0');
    return h ? h + ':' + p(m) + ':' + p(x) : p(m) + ':' + p(x);
  }
  /* الرسم المرئي فقط: يقرأ endsAt المطلق من العنصر */
  function paint(){
    const now = Date.now();
    document.querySelectorAll('[data-tmr-end]').forEach(el=>{
      const end = Number(el.getAttribute('data-tmr-end')), tot = Number(el.getAttribute('data-tmr-total')) || 1, left = end - now;
      const b = el.querySelector('[data-tmr-left]') || el; b.textContent = fmt(left);
      el.style.setProperty('--tp', Math.max(0, Math.min(1, 1 - left / tot)).toFixed(4));
    });
  }
  document.addEventListener('visibilitychange', ()=>{ if(document.visibilityState === 'visible') tick(); else arm(); });
  window.addEventListener('pageshow', ()=>tick());
  window.addEventListener('focus', ()=>tick());
  return { start:start, cancel:cancel, active:active, latest:latest, all:all, tick:tick, fmt:fmt, paint:paint, on:(k, h)=>{ H[k] = h; },
    _shift:(id, ms)=>{ const t = all().find(x=>x.id === id); if(t){ t.startedAt += ms; t.endsAt += ms; saveData(); arm(); } return t; } };
})();

function codisFindTaskAny(id){
  const scan = (weeks, room)=>{ if(!weeks || typeof weeks !== 'object') return null;
    for(const k in weeks){ const w = weeks[k]; if(!w || !w.days) continue; for(const d in w.days){ const t = (w.days[d] || []).find(x=>x && x.id === id); if(t) return { t:t, room:room, week:w, day:Number(d) }; } } return null; };
  return scan(data.weeks, 'tasks') || scan(data.learnWeeks, 'learn');
}
/* حارس البيع: المطوّر معفى (CodisLimits) — المؤقت عندها يكتمل بلا تعليم إن بيعت */
function codisTimerBlocksSell(uid){ return !!CodisTimers.active('reward', uid) && !CodisLimits.bypass('timer.sellActive'); }
try{ CodisLimits.reg('timer.sellActive', 'منع بيع مكافأة مؤقتها شغّال'); }catch(e){}
function codisRewardTimerStart(uid){
  const it = CodisInventory.get(uid); if(!it || it.status !== 'owned') return { ok:false, reason:'notowned' };
  const d = CodisDuration.parse(it.name); if(!d) return { ok:false, reason:'notimed' };
  return CodisTimers.start({ kind:'reward', ref:uid, label:it.name, minutes:d.min });
}
CodisTimers.on('reward', {
  alive:t=>{ const it = CodisInventory.get(t.ref); return !!it && it.status === 'owned'; },
  done:t=>{ const r = CodisEconomy.markUsed(t.ref); return !!(r && r.ok); },
  message:t=>({ title:'انتهى الوقت', body:'انتهى وقت مكافأة ' + t.label }),
  changed:()=>{ try{ econRenderAll(); }catch(e){} }
});
CodisTimers.on('task', {
  alive:t=>!!codisFindTaskAny(t.ref),
  done:()=>true,
  message:t=>({ title:'انتهى الوقت', body:'انتهى الوقت المحدد لمهمة ' + t.label }),
  changed:()=>codisTaskTimerRefresh()
});
const CODIS_TMR_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="13" r="8" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 9v4.2l2.6 1.6M9.5 2.8h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
const CODIS_PLAY_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z" fill="currentColor"/></svg>';
function codisDurBadgeHtml(name){ const d = CodisDuration.parse(name); return d ? '<span class="dur-badge" title="مكافأة بمؤقت">' + CODIS_TMR_SVG + CodisDuration.label(d.min) + '</span>' : ''; }
function codisOwnUseBtnHtml(it, uid, busy){
  const t = CodisTimers.active('reward', it.uid);
  if(t) return '<span class="chip-act tmr-chip is-run" role="timer" data-tmr-end="' + t.endsAt + '" data-tmr-total="' + (t.minutes * 60000) + '" aria-label="مؤقت المكافأة شغّال">' + CODIS_TMR_SVG + '<b data-tmr-left dir="ltr">' + CodisTimers.fmt(t.endsAt - Date.now()) + '</b></span>';
  const d = CodisDuration.parse(it.name);
  return '<button type="button" class="chip-act' + (d ? ' tmr-go' : '') + '" ' + (busy ? 'disabled' : '') + ' onclick="econUse(\'' + uid + '\')">' + (d ? CODIS_PLAY_SVG + 'ابدأ · ' + CodisDuration.label(d.min) : 'استخدمتها') + '</button>';
}
function codisTaskTimerHtml(task){
  const d = CodisDuration.forTask(task); if(!d || !task || !task.id) return '';
  const id = escapeHtml(String(task.id)), t = CodisTimers.latest('task', String(task.id)), lab = CodisDuration.label(d.min);
  if(t && t.state === 'running') return '<div class="tt-row is-run" data-tt="' + id + '"><div class="tt-clock" role="timer" data-tmr-end="' + t.endsAt + '" data-tmr-total="' + (t.minutes * 60000) + '"><span class="tt-ring" aria-hidden="true"></span>' +
    '<span class="tt-txt"><b data-tmr-left dir="ltr">' + CodisTimers.fmt(t.endsAt - Date.now()) + '</b><i>باقي من ' + escapeHtml(CodisDuration.label(t.minutes)) + '</i></span></div>' +
    '<button type="button" class="tt-stop" data-tt-stop="' + id + '">إيقاف</button></div>';
  if(t && t.state === 'done') return '<div class="tt-row is-done" data-tt="' + id + '"><span class="tt-done">' + ICONS.check + 'انتهى الوقت · ' + escapeHtml(CodisDuration.label(t.minutes)) + '</span>' +
    '<button type="button" class="tt-again" data-tt-start="' + id + '">من جديد</button></div>';
  return '<div class="tt-row" data-tt="' + id + '"><button type="button" class="tt-start" data-tt-start="' + id + '">' + CODIS_PLAY_SVG + '<span>ابدأ المهمة</span><span class="tt-dur">' + escapeHtml(lab) + '</span></button></div>';
}
/* تحديث سطر المؤقت وحده بلا إعادة بناء المهمة */
function codisTaskTimerRefresh(id){
  document.querySelectorAll(id ? '.tt-row[data-tt="' + String(id).replace(/"/g, '') + '"]' : '.tt-row[data-tt]').forEach(row=>{
    const f = codisFindTaskAny(row.getAttribute('data-tt')); if(!f) return;
    const h = codisTaskTimerHtml(f.t); if(h) row.outerHTML = h; else row.remove();
  });
  CodisTimers.paint();
}
function codisTaskTimerStart(id){
  const f = codisFindTaskAny(id); if(!f) return;
  const d = CodisDuration.forTask(f.t); if(!d) return;
  const r = CodisTimers.start({ kind:'task', ref:id, room:f.room, label:CodisDuration.strip(f.t.text), minutes:d.min });
  if(r.ok){ if(!r.existed){ codisSfx('confirm', { ctx:'task' }); CodisPush.nudge(); } codisTaskTimerRefresh(id); }
  else showToast(r.reason === 'save' ? 'تعذّر الحفظ — ما بدأ المؤقت' : 'تعذّر بدء المؤقت', 'var(--warning)');
}
document.addEventListener('click', e=>{
  const t = e.target; if(!t || !t.closest) return;
  const go = t.closest('[data-tt-start]'); if(go){ e.preventDefault(); codisTaskTimerStart(go.getAttribute('data-tt-start')); return; }
  const st = t.closest('[data-tt-stop]');
  if(st){ e.preventDefault(); const run = CodisTimers.active('task', st.getAttribute('data-tt-stop')); if(run && CodisTimers.cancel(run.id)){ showToast('توقّف المؤقت', 'var(--text-2)'); codisTaskTimerRefresh(st.getAttribute('data-tt-stop')); } }
});

/* — إشعارات النظام: Service Worker ‏showNotification (الأساس على الموبايل)، واشتراك Web Push ليصل الإشعار والتطبيق مسكّر.
     الإرسال بعد الإغلاق يحتاج الخادم (sql/codis_push.sql + supabase/functions/codis-push) — بدونه يعمل المؤقت والإشعار ما دامت الصفحة حيّة — */
const CodisPush = (function(){
  'use strict';
  const LS = 'codis.push.on';
  let regP = null, nudged = false;
  const vapid = ()=>{ try{ const m = document.querySelector('meta[name="codis-vapid-public-key"]'); return m ? String(m.getAttribute('content') || '').trim() : ''; }catch(e){ return ''; } };
  const ios = ()=>/iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const standalone = ()=>{ try{ return (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; }catch(e){ return false; } };
  const granted = ()=>('Notification' in window) && Notification.permission === 'granted';
  function unsupportedText(){
    if(ios() && !standalone()) return 'على الآيفون: افتح CODIS من Safari ← مشاركة ← «إضافة إلى الشاشة الرئيسية»، ثم افتحه من أيقونته وفعّل الإشعارات (iOS 16.4 أو أحدث).';
    if(!window.isSecureContext) return 'إشعارات الجهاز تحتاج اتصالاً آمناً (https).';
    return 'هذا المتصفح لا يدعم إشعارات النظام.';
  }
  function registration(){
    if(regP) return regP;
    if(!('serviceWorker' in navigator) || !window.isSecureContext || location.protocol === 'file:') return (regP = Promise.resolve(null));
    regP = navigator.serviceWorker.register('./sw.js', { scope:'./' }).then(r=>navigator.serviceWorker.ready.then(()=>r)).catch(()=>navigator.serviceWorker.getRegistration().catch(()=>null));
    return regP;
  }
  async function show(title, body, tag){
    if(!granted() || !(data.notifications && data.notifications.settings && data.notifications.settings.browserEnabled)) return false;
    const opts = { body:body || '', tag:tag || 'codis', renotify:false, icon:'icon.svg', badge:'icon.svg', lang:'ar', dir:'rtl', data:{ url:'./' } };
    try{ const r = await registration(); if(r && r.showNotification){ await r.showNotification(title || 'CODIS', opts); return true; } }catch(e){}
    try{ new Notification(title || 'CODIS', opts); return true; }catch(e){ return false; }
  }
  const b64 = s=>{ const p = '='.repeat((4 - s.length % 4) % 4), b = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')), o = new Uint8Array(b.length); for(let i = 0; i < b.length; i++) o[i] = b.charCodeAt(i); return o; };
  const signedIn = ()=>{ try{ return !!(CodisAccount.state && CodisAccount.state.user); }catch(e){ return false; } };
  const ready = ()=>{ try{ return localStorage.getItem(LS) === '1' && signedIn() && !!vapid(); }catch(e){ return false; } };
  /* بعد إذن المستخدم الصريح فقط (زر الإعدادات) */
  async function enable(){
    const r = await registration();
    if(!vapid() || !signedIn() || !r || !r.pushManager) return { ok:true, push:false };
    try{
      let sub = await r.pushManager.getSubscription();
      if(!sub) sub = await r.pushManager.subscribe({ userVisibleOnly:true, applicationServerKey:b64(vapid()) });
      const j = sub.toJSON();
      await CodisAccount.pushCall('push_subscribe', { p_endpoint:j.endpoint, p_p256dh:j.keys.p256dh, p_auth:j.keys.auth, p_ua:String(navigator.userAgent).slice(0, 200) });
      localStorage.setItem(LS, '1');
      all_pending();
      return { ok:true, push:true };
    }catch(e){ console.warn('CODIS push subscribe:', e && e.message); return { ok:true, push:false }; }
  }
  function all_pending(){ try{ CodisTimers.all().filter(t=>t.state === 'running' && !t.server).forEach(schedule); }catch(e){} }
  async function schedule(t){
    if(!ready() || !t || t.state !== 'running') return false;
    const m = { title:'انتهى الوقت', body:t.kind === 'task' ? 'انتهى الوقت المحدد لمهمة ' + t.label : 'انتهى وقت مكافأة ' + t.label };
    try{ await CodisAccount.pushCall('push_schedule', { p_event_id:t.ev, p_fire_at:new Date(t.endsAt).toISOString(), p_title:m.title, p_body:m.body }); t.server = true; saveData(); return true; }
    catch(e){ console.warn('CODIS push schedule:', e && e.message); return false; }
  }
  async function unschedule(t){ if(!t || !t.server || !signedIn()) return; try{ await CodisAccount.pushCall('push_cancel', { p_event_id:t.ev }); }catch(e){} }
  /* تذكير لطيف مرة بالجلسة إذا بدأ مؤقت وإشعارات الجهاز غير مفعّلة */
  function nudge(){
    if(nudged || granted()) return; nudged = true;
    setTimeout(()=>showToast(('Notification' in window) ? 'حتى يوصلك تنبيه لما يخلص الوقت: فعّل «إشعارات المتصفح» من الإعدادات' : unsupportedText(), 'var(--text-2)'), 1600);
  }
  window.addEventListener('load', ()=>{ setTimeout(()=>{ registration(); try{ CodisTimers.tick(); }catch(e){} }, 300); });
  return { show:show, enable:enable, schedule:schedule, unschedule:unschedule, nudge:nudge, unsupportedText:unsupportedText, ready:ready, registration:registration, standalone:standalone };
})();

/* — مشهد الشراء: يُشغَّل بعد نجاح CodisEconomy.purchase فقط، بسعرها المدفوع (r.price) ونسختها (r.owned.uid). لا يمنح ولا يخصم شيئاً.
     المستوى من CodisRevealLevels.levelOfValue(السعر) — نفس حدود كشف الصناديق التسعة — والحركة عبر CodisMotion.run (يحترم تقليل الحركة) — */
const CodisBuyCine = (function(){
  'use strict';
  /* لكل مستوى وصفة تصاعدية: مدة السحب، المسكة، قصاصات الورق، الحلقات، اللمعة، الثقب الورقي، الأشعة، المطر، القصاصات الملونة، الاهتزاز، الوهج */
  const R = [null,
    { pull:640, grip:160, scraps:0,  ring:0, sheen:1, hole:0, rays:0, rain:0,  conf:0,  shake:0, spin:0, flare:0, hold:160 },
    { pull:680, grip:200, scraps:6,  ring:1, sheen:1, hole:0, rays:0, rain:0,  conf:0,  shake:0, spin:0, flare:0, hold:180 },
    { pull:720, grip:240, scraps:10, ring:1, sheen:1, hole:1, rays:0, rain:0,  conf:0,  shake:0, spin:0, flare:0, hold:200 },
    { pull:760, grip:260, scraps:14, ring:2, sheen:2, hole:1, rays:0, rain:0,  conf:0,  shake:0, spin:0, flare:0, hold:220 },
    { pull:800, grip:280, scraps:18, ring:2, sheen:2, hole:1, rays:1, rain:0,  conf:14, shake:0, spin:0, flare:0, hold:240 },
    { pull:840, grip:300, scraps:18, ring:2, sheen:2, hole:1, rays:1, rain:22, conf:0,  shake:0, spin:0, flare:0, hold:260 },
    { pull:900, grip:320, scraps:22, ring:3, sheen:2, hole:1, rays:1, rain:34, conf:0,  shake:0, spin:1, flare:0, hold:300 },
    { pull:960, grip:360, scraps:26, ring:3, sheen:3, hole:1, rays:2, rain:0,  conf:40, shake:1, spin:1, flare:0, hold:340 },
    { pull:1060, grip:440, scraps:30, ring:3, sheen:3, hole:1, rays:2, rain:0, conf:64, shake:2, spin:1, flare:1, hold:420 }
  ];
  let s = null;
  const tok = n=>{ try{ return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }catch(e){ return ''; } };
  const later = (fn, ms)=>{ if(!s) return; const st = s; st.tm.push(setTimeout(()=>{ if(s === st) fn(); }, ms)); };
  const rnd = (a, b)=>a + Math.random() * (b - a);
  function el(cls, parent, css){ const e = document.createElement('div'); e.className = cls; if(css) e.style.cssText = css; (parent || s.fx).appendChild(e); return e; }
  function burst(rc, lite, cx, cy){
    const n = k=>lite ? Math.ceil(k / 2) : k;
    for(let i = 0; i < rc.ring; i++){
      const r = el('bcx-ring', null, 'left:' + cx + 'px;top:' + cy + 'px');
      codisAnim(r, [{ transform:'translate(-50%,-50%) scale(.25)', opacity:.95 }, { transform:'translate(-50%,-50%) scale(' + (2.2 + i * .7) + ')', opacity:0 }], { dur:760 + i * 200, delay:i * 120, ease:tok('--ease') || 'ease-out', fill:'both' });
    }
    for(let i = 0; i < n(rc.scraps); i++){
      const a = rnd(0, Math.PI * 2), d = rnd(110, 250), w = rnd(8, 18), sp = el('bcx-scrap' + (i % 3 === 0 ? ' is-tint' : ''), null, 'left:' + cx + 'px;top:' + cy + 'px;width:' + w + 'px;height:' + (w * rnd(.6, 1.2)) + 'px;clip-path:polygon(' +
        [0, 1, 2, 3, 4].map(k=>Math.round(rnd(0, 100)) + '% ' + Math.round([0, 30, 100, 70, 10][k] + rnd(-10, 10)) + '%').join(',') + ')');
      const x = Math.cos(a) * d, y = Math.sin(a) * d;
      codisAnim(sp, [{ transform:'translate(-50%,-50%) rotate(0)', opacity:1 }, { transform:'translate(calc(-50% + ' + x * .7 + 'px),calc(-50% + ' + (y * .7 - 30) + 'px)) rotate(' + rnd(-200, 200) + 'deg)', opacity:1, offset:.55 },
        { transform:'translate(calc(-50% + ' + x + 'px),calc(-50% + ' + (y + 90) + 'px)) rotate(' + rnd(-360, 360) + 'deg)', opacity:0 }], { dur:rnd(900, 1400), ease:'cubic-bezier(.2,.7,.4,1)', fill:'both' });
    }
    for(let i = 0; i < n(rc.rain); i++){
      const r = el('bcx-drop', null, 'left:' + rnd(2, 98) + '%;height:' + rnd(40, 120) + 'px');
      codisAnim(r, [{ transform:'translateY(-20vh)', opacity:0 }, { opacity:.9, offset:.15 }, { transform:'translateY(110vh)', opacity:0 }], { dur:rnd(900, 1700), delay:rnd(0, 700), ease:'linear', fill:'both' });
    }
    const pal = ['rgb(var(--c1))', 'rgb(var(--c2))', '#ffd76a', '#fff6dc'];
    for(let i = 0; i < n(rc.conf); i++){
      const c = el('bcx-conf', null, 'left:' + rnd(0, 100) + '%;background:' + pal[i % pal.length] + ';width:' + rnd(5, 9) + 'px;height:' + rnd(9, 15) + 'px');
      codisAnim(c, [{ transform:'translate3d(0,-12vh,0) rotate(0)', opacity:1 }, { transform:'translate3d(' + rnd(-60, 60) + 'px,108vh,0) rotate(' + rnd(-720, 720) + 'deg)', opacity:.9 }], { dur:rnd(1600, 2600), delay:rnd(0, 500), ease:'cubic-bezier(.25,.6,.5,1)', fill:'both' });
    }
    if(rc.flare){ const f = el('bcx-flare'); codisAnim(f, [{ opacity:0 }, { opacity:.85, offset:.25 }, { opacity:0 }], { dur:620, ease:'ease-out', fill:'both' }); }
    if(rc.shake){ const a = rc.shake * 3; codisAnim(s.stage, [{ transform:'translate(0,0)' }, { transform:'translate(' + a + 'px,-' + a + 'px)' }, { transform:'translate(-' + a + 'px,' + (a - 1) + 'px)' }, { transform:'translate(' + (a - 1) + 'px,' + a + 'px)' }, { transform:'translate(0,0)' }], { dur:340, ease:'linear' }); }
    const sh = s.root.querySelector('.bcx-sheen i');
    for(let i = 0; sh && i < rc.sheen; i++) codisAnim(sh, [{ transform:'translateX(-170%) skewX(-18deg)' }, { transform:'translateX(330%) skewX(-18deg)' }], { dur:820, delay:i * 700, ease:'cubic-bezier(.5,0,.3,1)', fill:'none' });
  }
  function play(r, it){
    try{
      if(s || !r || !r.ok || !r.owned || !it) return false;
      const rar = econRarityById(it.rarity); if(!rar) return false;
      const price = Math.max(0, Number(r.price) || 0), lv = CodisRevealLevels.levelOfValue(price), info = CodisRevealLevels.info(lv), rc = R[lv];
      const reduced = CodisMotion.isReduced(), lite = reduced || (navigator.hardwareConcurrency || 8) <= 4;
      const src = Array.prototype.find.call(document.querySelectorAll('#eco-store-body .shop-card'), c=>c.dataset.id === it.id);
      const sr = src ? (src.querySelector('.cflip') || src).getBoundingClientRect() : null;
      const origin = (sr && sr.width > 20 && sr.bottom > 0 && sr.top < innerHeight) ? sr : null;
      const dur = CodisDuration.parse(r.owned.name);
      const bx = document.body.getBoundingClientRect(), W = Math.round(Math.min(250, Math.min(innerWidth, bx.width || innerWidth) * .6, (innerHeight - 260) * .8));
      const root = document.createElement('div');
      root.className = 'bcx lv-' + lv + (reduced ? ' is-reduced' : ''); root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true'); root.setAttribute('aria-label', 'حصلت على ' + r.owned.name);
      root.style.setProperty('--c1', info.rgb); root.style.setProperty('--c2', info.rgb2);
      let pips = ''; for(let i = 1; i <= 9; i++) pips += '<i class="' + (i <= lv ? 'on' : '') + '"></i>';
      root.innerHTML = '<div class="bcx-scrim"></div>' + (rc.rays ? '<div class="bcx-rays' + (rc.rays > 1 ? ' is-x2' : '') + '" aria-hidden="true"></div>' : '') + '<div class="bcx-fx" aria-hidden="true"></div>' +
        '<div class="bcx-stage"><div class="bcx-card" style="width:' + W + 'px"><div class="bcx-face">' + econStoreFaceHtml(it, rar, { price:price }) + '</div><span class="bcx-sheen" aria-hidden="true"><i></i></span></div>' +
        '<div class="bcx-ticket"><b>صارت إلك</b><span class="bcx-name" dir="auto">' + escapeHtml(r.owned.name) + '</span><span class="bcx-paid">دفعت ' + econCoin(price) + '</span>' + (dur ? '<span class="bcx-tmr">' + CODIS_TMR_SVG + 'مؤقت ' + escapeHtml(CodisDuration.label(dur.min)) + ' يبدأ عند الاستخدام</span>' : '') + '<span class="bcx-pips" role="img" aria-label="مستوى الكشف ' + lv + ' من 9">' + pips + '</span></div>' +
        '<div class="bcx-acts" hidden><button type="button" class="btn btn-primary bcx-use"' + (dur ? ' aria-label="استخدام — يبدأ مؤقت ' + escapeHtml(CodisDuration.label(dur.min)) + '"' : '') + '>' + (dur ? CODIS_PLAY_SVG : '') + '<span>استخدام</span></button>' +
        '<button type="button" class="btn btn-secondary bcx-keep"><span>تخزين</span></button></div></div>';
      document.body.appendChild(root);
      s = { root:root, uid:r.owned.uid, fx:root.querySelector('.bcx-fx'), stage:root.querySelector('.bcx-stage'), card:root.querySelector('.bcx-card'), tm:[], acting:false, prev:document.activeElement, acts:false };
      root.querySelector('.bcx-use').onclick = useNow; root.querySelector('.bcx-keep').onclick = keep;
      root.querySelector('.bcx-scrim').onclick = ()=>{ if(s && s.acts) keep(); };
      root.addEventListener('keydown', onKey);
      codisAnim(root.querySelector('.bcx-scrim'), [{ opacity:0 }, { opacity:1 }], { dur:260, ease:'linear', fill:'both' });
      const fr = s.card.getBoundingClientRect(), ease = tok('--ease-glide') || 'cubic-bezier(.25,1.08,.4,1)';
      let dx = 0, dy = innerHeight * .45, k0 = .55;
      if(origin){ dx = (origin.left + origin.width / 2) - (fr.left + fr.width / 2); dy = (origin.top + origin.height / 2) - (fr.top + fr.height / 2); k0 = origin.width / fr.width; }
      const T = rc.grip + rc.pull, g = rc.grip / T, spin = rc.spin && !lite ? ' rotateY(360deg)' : ' rotateY(0deg)';
      const rb = root.getBoundingClientRect();
      if(origin && rc.hole){ const h = el('bcx-hole', root, 'left:' + (origin.left - rb.left) + 'px;top:' + (origin.top - rb.top) + 'px;width:' + origin.width + 'px;height:' + origin.height + 'px'); codisAnim(h, [{ opacity:0 }, { opacity:1, offset:.15 }, { opacity:0 }], { dur:T + 900, ease:'linear', fill:'both' }); }
      codisAnim(s.card, [
        { transform:'translate(' + dx + 'px,' + dy + 'px) scale(' + k0 + ') rotate(0deg) rotateY(0deg)', offset:0 },
        { transform:'translate(' + dx + 'px,' + (dy - 3) + 'px) scale(' + (k0 * .96) + ') rotate(-3deg) rotateY(0deg)', offset:g * .55 },
        { transform:'translate(' + dx + 'px,' + (dy - 12) + 'px) scale(' + (k0 * 1.05) + ') rotate(4deg) rotateY(0deg)', offset:g },
        { transform:'translate(0px,-16px) scale(1.07) rotate(-2deg)' + spin, offset:.86 },
        { transform:'translate(0px,0px) scale(1) rotate(0deg)' + spin, offset:1 }
      ], { dur:T, ease:ease, fill:'both' });
      const tk = root.querySelector('.bcx-ticket');
      codisAnim(tk, [{ transform:'translateY(18px) rotate(-3deg)', opacity:0 }, { transform:'translateY(-3px) rotate(1deg)', opacity:1, offset:.7 }, { transform:'translateY(0) rotate(0)', opacity:1 }], { dur:420, delay:T * .86, ease:ease, fill:'both' });
      later(()=>{ if(!reduced){ const fr2 = s.card.getBoundingClientRect(), fb = s.fx.getBoundingClientRect(); burst(rc, lite, fr2.left + fr2.width / 2 - fb.left, fr2.top + fr2.height / 2 - fb.top); } }, Math.round(T * .86));
      later(()=>{
        const a = root.querySelector('.bcx-acts'); a.hidden = false; s.acts = true;
        codisAnim(a, [{ transform:'translateY(14px)', opacity:0 }, { transform:'translateY(0)', opacity:1 }], { dur:300, ease:ease, fill:'both' });
        try{ root.querySelector('.bcx-use').focus({ preventScroll:true }); }catch(e){}
      }, T + rc.hold + 200);
      return true;
    }catch(e){ console.error('CodisBuyCine:', e); try{ if(s && s.root) s.root.remove(); }catch(x){} s = null; return false; }
  }
  function onKey(e){ if(e.key === 'Escape'){ e.preventDefault(); keep(); } else if(e.key === 'Tab' && s){ const b = Array.prototype.filter.call(s.root.querySelectorAll('button'), x=>!x.closest('[hidden]')); if(!b.length) return; const i = b.indexOf(document.activeElement); if(e.shiftKey && i <= 0){ e.preventDefault(); b[b.length - 1].focus(); } else if(!e.shiftKey && i === b.length - 1){ e.preventDefault(); b[0].focus(); } } }
  function close(after){
    if(!s || s.closing) return; const st = s; st.closing = true;
    st.root.classList.add('is-out');
    st.root.querySelectorAll('button').forEach(b=>{ b.disabled = true; });
    let fin = false;
    const end = ()=>{ if(fin) return; fin = true; st.tm.forEach(clearTimeout); try{ st.root.remove(); }catch(e){} if(s === st) s = null; try{ if(st.prev && st.prev.focus) st.prev.focus({ preventScroll:true }); }catch(e){} if(after) after(); };
    const a = codisAnim(st.root, [{ opacity:1 }, { opacity:0 }], { dur:220, ease:'linear', fill:'forwards', done:end });
    if(!a) end(); else setTimeout(end, 320);   /* صفحة بالخلفية لا تُكمل الحركة — التنظيف مضمون */
  }
  /* «تخزين»: المكافأة أصلاً مملوكة منذ نجاح الشراء — الإغلاق لا يستهلك شيئاً */
  function keep(){ if(!s || s.acting) return; s.acting = true; close(()=>{ try{ econRenderAll(); }catch(e){} showToast('انحفظت ببحوزتك', 'var(--success)', 'gift'); }); }
  function useNow(){
    if(!s || s.acting) return; s.acting = true;
    const uid = s.uid, it = CodisInventory.get(uid); let ok = false, msg = 'هذي المكافأة ما عدت بحوزتك';
    if(it && it.status === 'owned'){
      const d = CodisDuration.parse(it.name);
      if(d){ const rt = codisRewardTimerStart(uid); ok = rt.ok; msg = ok ? 'بدأ المؤقت: ' + CodisDuration.label(d.min) : 'تعذّر بدء المؤقت'; if(ok) CodisPush.nudge(); }
      else { const r2 = CodisEconomy.markUsed(uid); ok = !!(r2 && r2.ok); msg = ok ? 'انسجّلت كمستخدَمة' : (r2 && r2.reason === 'save' ? 'تعذّر الحفظ — بقيت كما هي' : 'تعذّر التنفيذ'); }
    }
    if(ok){ try{ codisSfx('confirm', { ctx:'use' }); }catch(e){} }
    close(()=>{ try{ econRenderAll(); }catch(e){} showToast(msg, ok ? 'var(--success)' : 'var(--warning)', ok ? 'check' : undefined); });
  }
  return { play:play, keep:keep, isOpen:()=>!!s, el:()=>s && s.root, _state:()=>s };
})();

/* — معاينة بطاقة المتجر بالضغط المطوّل: البطاقة الحقيقية نفسها (لا نسخة) تُنقل لطبقة أمامية بحركة FLIP من موضعها ثم تعود له.
     الضغطة الطويلة لا تتحول لنقرة قلب أو شراء — */
const CodisCardPeek = (function(){
  'use strict';
  const HOLD = 420, SLOP = 10;
  let p = null, s = null, blockUntil = 0;
  const clearP = ()=>{ if(p){ clearTimeout(p.t); p = null; } };
  const tok = n=>{ try{ return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }catch(e){ return ''; } };
  document.addEventListener('pointerdown', e=>{
    if(s || (e.pointerType === 'mouse' && e.button !== 0)) return;
    const card = e.target.closest && e.target.closest('#eco-store-body .shop-card'); if(!card || !card.querySelector('.cflip') || card.classList.contains('is-selectable')) return;
    if(e.target.closest('button, a, input, select, textarea')) return;
    clearP(); p = { id:e.pointerId, x:e.clientX, y:e.clientY, card:card, t:setTimeout(()=>{ const c = p && p.card; p = null; if(c) open(c); }, HOLD) };
  });
  document.addEventListener('pointermove', e=>{ if(p && e.pointerId === p.id && Math.hypot(e.clientX - p.x, e.clientY - p.y) > SLOP) clearP(); });
  document.addEventListener('pointerup', clearP); document.addEventListener('pointercancel', clearP);
  /* التمرير باللمس يُطلق pointercancel من المتصفح نفسه؛ والفأرة تُلغى بالحركة (SLOP) */
  document.addEventListener('contextmenu', e=>{ if(p || (e.target.closest && e.target.closest('.peek'))) e.preventDefault(); });
  document.addEventListener('click', e=>{ if(blockUntil && Date.now() < blockUntil){ e.preventDefault(); e.stopPropagation(); blockUntil = 0; } }, true);
  function open(card){
    if(s || !card.isConnected) return;
    const r = card.getBoundingClientRect(); if(!(r.width > 0)) return;
    blockUntil = Date.now() + 800;
    try{ navigator.vibrate && navigator.vibrate(8); }catch(e){}
    const ph = document.createElement('div'); ph.className = 'peek-ph'; ph.style.width = r.width + 'px'; ph.style.height = r.height + 'px';
    const ov = document.createElement('div'); ov.className = 'peek'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true'); ov.setAttribute('aria-label', 'معاينة البطاقة');
    ov.innerHTML = '<div class="peek-scrim"></div><div class="peek-host store-sec"></div><button type="button" class="peek-x" aria-label="إغلاق المعاينة">' + ICONS.close + '</button><p class="peek-hint">اضغط البطاقة لتنقلب · اضغط خارجها للرجوع</p>';
    document.body.appendChild(ov);
    card.parentNode.insertBefore(ph, card);
    ov.querySelector('.peek-host').appendChild(card);
    card.classList.add('is-peek');
    /* body مُحوَّل (إطار التطبيق) فهو حاوية fixed: كل الإحداثيات نسبةً لصندوق الطبقة نفسها لا للنافذة */
    const o = ov.getBoundingClientRect();
    Object.assign(card.style, { position:'fixed', left:(r.left - o.left) + 'px', top:(r.top - o.top) + 'px', width:r.width + 'px', margin:'0', zIndex:'2' });
    const vw = o.width, vh = o.height, k = Math.max(1, Math.min(2.3, vw * .8 / r.width, vh * .64 / r.height));
    const dx = (o.left + vw / 2) - (r.left + r.width / 2), dy = (o.top + vh / 2) - (r.top + r.height / 2) - 12, to = 'translate3d(' + dx + 'px,' + dy + 'px,0) scale(' + k + ')';
    s = { card:card, ph:ph, ov:ov, r:r, prev:document.activeElement };
    card.style.transform = to;
    codisAnim(card, [{ transform:'translate3d(0,0,0) scale(1)' }, { transform:'translate3d(' + dx * .9 + 'px,' + (dy * .9 - 10) + 'px,0) scale(' + k * 1.04 + ')', offset:.7 }, { transform:to }], { dur:560, ease:tok('--ease-glide') || 'cubic-bezier(.25,1.08,.4,1)' });
    requestAnimationFrame(()=>ov.classList.add('is-in'));
    ov.querySelector('.peek-scrim').onclick = close; ov.querySelector('.peek-x').onclick = close;
    ov.addEventListener('keydown', e=>{ if(e.key === 'Escape'){ e.preventDefault(); close(); } });
    try{ ov.querySelector('.peek-x').focus({ preventScroll:true }); }catch(e){}
  }
  function close(){
    if(!s || s.closing) return; const st = s; st.closing = true;
    const back = st.ph.isConnected; let to = 'translate3d(0,0,0) scale(1)';
    if(back){ const pr = st.ph.getBoundingClientRect(); to = 'translate3d(' + (pr.left - st.r.left) + 'px,' + (pr.top - st.r.top) + 'px,0) scale(1)'; }
    st.ov.classList.remove('is-in'); st.ov.classList.add('is-out');
    let fin = false;
    const done = ()=>{
      if(fin) return; fin = true;
      try{ st.card.getAnimations().forEach(a=>a.cancel()); }catch(e){}
      st.card.classList.remove('is-peek'); ['position', 'left', 'top', 'width', 'margin', 'zIndex', 'transform', 'opacity'].forEach(k=>{ st.card.style[k] = ''; });
      if(back) st.ph.parentNode.insertBefore(st.card, st.ph); else st.card.remove();
      st.ph.remove(); st.ov.remove(); if(s === st) s = null;
      try{ if(st.prev && st.prev.isConnected && st.prev.focus) st.prev.focus({ preventScroll:true }); }catch(e){}
    };
    const kf = back ? [{ transform:st.card.style.transform }, { transform:to }] : [{ transform:st.card.style.transform, opacity:1 }, { transform:st.card.style.transform + ' scale(.9)', opacity:0 }];
    const a = codisAnim(st.card, kf, { dur:360, ease:tok('--ease-ios') || 'cubic-bezier(.32,.72,0,1)', fill:'forwards', done:done });
    if(!a) done(); else setTimeout(done, 460);
  }
  return { close:close, isOpen:()=>!!s, el:()=>s && s.ov, _open:open };
})();

/* — ترتيب المهام بالسحب: ضغطة مطوّلة على سطح البطاقة (لا على الأزرار) ثم سحب؛ البقية تفسح المكان، تمرير تلقائي قرب الحواف،
     والحفظ في مصفوفة اليوم نفسها (week.days[day]) عبر saveData — الحالة والوزن والارتباط بالخطة لا تتغيّر — */
const CodisTaskDrag = (function(){
  'use strict';
  const LISTS = { 'day-task-list':'tasks', 'learn-day-task-list':'learn' };
  const SLOP = 9, EDGE = 76, BLOCK = 'button, a, input, textarea, select, label, [contenteditable], .status-group, .task-meta, .tt-row, .task-partial';
  let p = null, d = null;
  const clearP = ()=>{ if(p){ clearTimeout(p.t); p = null; } };
  const rows = list=>Array.prototype.filter.call(list.children, c=>c.classList && c.classList.contains('task-item'));
  function scroller(el){ let n = el.parentElement; while(n && n !== document.body){ const cs = getComputedStyle(n); if(/(auto|scroll)/.test(cs.overflowY) && n.scrollHeight > n.clientHeight + 4) return n; n = n.parentElement; } return document.scrollingElement || document.documentElement; }
  document.addEventListener('pointerdown', e=>{
    if(d || (e.pointerType === 'mouse' && e.button !== 0)) return;
    const item = e.target.closest && e.target.closest('.task-item'); if(!item) return;
    const list = item.parentElement; if(!list || !LISTS[list.id]) return;
    if(e.target.closest(BLOCK) || rows(list).length < 2) return;
    clearP();
    const id = e.pointerId, x = e.clientX, y = e.clientY;
    p = { id:id, x:x, y:y, item:item, list:list, t:setTimeout(()=>begin(), e.pointerType === 'mouse' ? 260 : 380) };
  });
  document.addEventListener('pointermove', e=>{
    if(p && !d && e.pointerId === p.id){ if(Math.hypot(e.clientX - p.x, e.clientY - p.y) > SLOP) clearP(); return; }
    if(d && e.pointerId === d.id){ d.y = e.clientY; if(e.cancelable) e.preventDefault(); frame(); }
  }, { passive:false });
  document.addEventListener('pointerup', e=>{ if(p && e.pointerId === p.id) clearP(); if(d && e.pointerId === d.id) drop(); });
  document.addEventListener('pointercancel', e=>{ if(p && e.pointerId === p.id) clearP(); if(d && e.pointerId === d.id) abort(); });
  document.addEventListener('touchmove', e=>{ if(d && e.cancelable) e.preventDefault(); }, { passive:false });
  document.addEventListener('contextmenu', e=>{ if(p || d) e.preventDefault(); });
  document.addEventListener('selectstart', e=>{ const t = e.target && e.target.nodeType === 1 ? e.target : e.target && e.target.parentElement; if(t && t.closest && t.closest('.task-item') && !t.closest('input, textarea, [contenteditable]')) e.preventDefault(); });
  function begin(){
    if(!p) return; const pp = p; p = null;
    const items = rows(pp.list), from = items.indexOf(pp.item); if(from < 0 || !pp.item.isConnected) return;
    items.forEach(c=>{ try{ c.getAnimations().forEach(a=>a.cancel()); }catch(x){} });
    const rects = items.map(c=>c.getBoundingClientRect()), sc = scroller(pp.list);
    const gap = items.length > 1 ? Math.max(0, (from + 1 < items.length ? rects[from + 1].top - rects[from].bottom : rects[from].top - rects[from - 1].bottom)) : 0;
    d = { id:pp.id, item:pp.item, list:pp.list, kind:LISTS[pp.list.id], items:items, from:from, to:from, rects:rects, y0:pp.y, y:pp.y, sc:sc, st0:sc.scrollTop, slot:rects[from].height + gap, raf:0 };
    try{ pp.item.setPointerCapture(pp.id); }catch(x){}
    pp.list.classList.add('is-sorting'); pp.item.classList.add('is-drag');
    try{ const sel = window.getSelection && window.getSelection(); if(sel && sel.removeAllRanges) sel.removeAllRanges(); }catch(x){}
    try{ navigator.vibrate && navigator.vibrate(12); }catch(x){}
    frame();
  }
  function frame(){ if(!d || d.raf) return; d.raf = requestAnimationFrame(()=>{ if(d){ d.raf = 0; layout(); } }); }
  function layout(){
    const dy = d.y - d.y0 + (d.sc.scrollTop - d.st0), r0 = d.rects[d.from], mid = r0.top + dy + r0.height / 2;
    d.item.style.transform = 'translate3d(0,' + dy + 'px,0) scale(1.02)';
    let to = d.from;
    for(let i = 0; i < d.items.length; i++){ if(i === d.from) continue; const m = d.rects[i].top + d.rects[i].height / 2; if(i < d.from && mid < m) to = Math.min(to, i); if(i > d.from && mid > m) to = Math.max(to, i); }
    d.to = to;
    d.items.forEach((c, i)=>{ if(i === d.from) return; const sft = (d.from < to && i > d.from && i <= to) ? -d.slot : (d.from > to && i >= to && i < d.from) ? d.slot : 0; c.style.transform = sft ? 'translate3d(0,' + sft + 'px,0)' : ''; });
    const vh = window.innerHeight; let v = 0;
    if(d.y < EDGE) v = -Math.ceil((EDGE - d.y) / 5); else if(d.y > vh - EDGE) v = Math.ceil((d.y - (vh - EDGE)) / 5);
    if(v){ const b = d.sc.scrollTop; d.sc.scrollTop = b + v; if(d.sc.scrollTop !== b) frame(); }
  }
  function settle(st, cb){
    let target = 0;
    if(st.to > st.from) target = st.rects[st.to].bottom - st.rects[st.from].bottom; else if(st.to < st.from) target = st.rects[st.to].top - st.rects[st.from].top;
    st.item.style.transition = 'transform 190ms cubic-bezier(.22,1,.36,1)'; st.item.style.transform = 'translate3d(0,' + target + 'px,0)';
    setTimeout(cb, 200);
  }
  function reset(st){ st.items.forEach(c=>{ c.style.transform = ''; c.style.transition = ''; }); st.item.classList.remove('is-drag'); st.list.classList.remove('is-sorting'); }
  function drop(){
    const st = d; d = null; if(st.raf) cancelAnimationFrame(st.raf);
    const moved = st.to !== st.from;
    settle(st, ()=>{
      st.list.classList.add('no-anim'); reset(st);
      if(moved){ const ref = st.items[st.to]; if(st.to > st.from) ref.after(st.item); else ref.before(st.item); commit(st); }
      requestAnimationFrame(()=>st.list.classList.remove('no-anim'));
    });
  }
  function abort(){ const st = d; d = null; if(st.raf) cancelAnimationFrame(st.raf); st.to = st.from; settle(st, ()=>reset(st)); }
  /* الحفظ: ترتيب الظاهر كما في الواجهة، والمخفية (المحسومة) تبقى بخاناتها */
  function commit(st){
    const week = st.kind === 'learn' ? learnCurrentWeek() : currentWeek(), di = st.kind === 'learn' ? activeLearnDayIdx : activeDayIdx;
    if(!week || !week.days) return false;
    const arr = week.days[di] || [], order = rows(st.list).map(c=>c.dataset.tid), byId = {};
    arr.forEach(t=>{ if(t && t.id) byId[t.id] = t; });
    if(!order.length || order.some(id=>!byId[id])) return false;
    const set = new Set(order); let k = 0;
    week.days[di] = arr.map(t=>(t && set.has(t.id)) ? byId[order[k++]] : t);
    saveData();
    try{ codisSfx('confirm', { ctx:'task' }); }catch(e){}
    return true;
  }
  /* للاختبار: نقل مباشر بالفهرس عبر نفس مسار الحفظ */
  function _move(kind, from, to){
    const list = document.getElementById(kind === 'learn' ? 'learn-day-task-list' : 'day-task-list'); if(!list) return false;
    const items = rows(list); if(!items[from] || !items[to]) return false;
    if(to > from) items[to].after(items[from]); else items[to].before(items[from]);
    return commit({ kind:kind, list:list });
  }
  return { _move:_move, active:()=>!!d };
})();
/* ===== /CODIS-TIMERS ===== */
"""
rep("function econRewardHintText(rarityId, room){", JS + "function econRewardHintText(rarityId, room){", 'timers js')

css = r"""
/* CODIS-TIMERS */
.dur-badge{ display:inline-flex; align-items:center; gap:3px; margin-inline-start:6px; padding:1px 7px 1px 6px; border-radius:999px; font-size:10.5px; font-weight:700; line-height:18px; vertical-align:middle; white-space:nowrap;
  color:var(--aqua); background:rgb(var(--hi-rgb) / .07); border:1px solid color-mix(in srgb, var(--aqua) 34%, transparent); }
.dur-badge svg{ width:11px; height:11px; }
.st-cap .dur-badge{ margin:3px auto 0; display:flex; width:max-content; }
.chip-act.tmr-go, .chip-act.tmr-chip{ display:inline-flex; align-items:center; gap:5px; }
.chip-act.tmr-go svg{ width:12px; height:12px; }
.chip-act.tmr-chip{ cursor:default; color:var(--aqua); border-color:color-mix(in srgb, var(--aqua) 45%, transparent);
  background:linear-gradient(90deg, color-mix(in srgb, var(--aqua) 16%, transparent) calc(var(--tp, 0) * 100%), transparent 0); }
.chip-act.tmr-chip svg{ width:13px; height:13px; }
.chip-act.tmr-chip b{ font-variant-numeric:tabular-nums; letter-spacing:.02em; }
/* سطر مؤقت المهمة */
.tt-row{ display:flex; align-items:center; gap:8px; margin:2px 0 8px; }
.tt-start, .tt-stop, .tt-again{ font:inherit; cursor:pointer; -webkit-tap-highlight-color:transparent; }
.tt-start{ display:inline-flex; align-items:center; gap:7px; min-height:40px; padding:0 14px 0 12px; border-radius:12px; border:1px solid color-mix(in srgb, var(--aqua) 40%, transparent);
  background:color-mix(in srgb, var(--aqua) 10%, transparent); color:var(--text); font-size:13.5px; font-weight:700; transition:transform var(--dur-micro, 110ms) var(--ease), background var(--dur-fast, 160ms); }
.tt-start:active{ transform:scale(.97); background:color-mix(in srgb, var(--aqua) 18%, transparent); }
.tt-start svg{ width:14px; height:14px; color:var(--aqua); }
.tt-dur{ font-weight:600; font-size:12px; color:var(--text-3); padding-inline-start:7px; border-inline-start:1px solid rgb(var(--hi-rgb) / .14); }
.tt-row.is-run .tt-clock{ flex:1; min-width:0; display:flex; align-items:center; gap:10px; min-height:44px; padding:0 12px 0 8px; border-radius:12px; background:rgb(var(--hi-rgb) / .05); border:1px solid color-mix(in srgb, var(--aqua) 32%, transparent); }
.tt-ring{ flex:none; width:28px; height:28px; border-radius:50%; background:conic-gradient(var(--aqua) calc(var(--tp, 0) * 360deg), rgb(var(--hi-rgb) / .12) 0); -webkit-mask:radial-gradient(circle, transparent 9px, #000 10px); mask:radial-gradient(circle, transparent 9px, #000 10px); }
.tt-txt{ display:flex; flex-direction:column; line-height:1.2; min-width:0; }
.tt-txt b{ font-size:17px; font-variant-numeric:tabular-nums; letter-spacing:.03em; color:var(--text); }
.tt-txt i{ font-style:normal; font-size:11.5px; color:var(--text-3); }
.tt-stop, .tt-again{ flex:none; min-height:40px; padding:0 12px; border-radius:12px; border:1px solid rgb(var(--hi-rgb) / .14); background:none; color:var(--text-2); font-size:12.5px; font-weight:600; }
.tt-row.is-done .tt-done{ flex:1; display:inline-flex; align-items:center; gap:6px; font-size:13px; font-weight:700; color:var(--success); }
.tt-row.is-done .tt-done svg{ width:15px; height:15px; }
/* منع تحديد النص على أسطح بطاقات المهام فقط — الحقول تبقى قابلة للتحديد */
#day-task-list .task-item, #learn-day-task-list .task-item{ -webkit-user-select:none; user-select:none; -webkit-touch-callout:none; }
#day-task-list .task-item :is(input, textarea, [contenteditable]), #learn-day-task-list .task-item :is(input, textarea, [contenteditable]){ -webkit-user-select:text; user-select:text; -webkit-touch-callout:default; }
.is-sorting > .task-item{ transition:transform 210ms cubic-bezier(.22,1,.36,1); will-change:transform; }
.is-sorting > .task-item.is-drag{ transition:none; position:relative; z-index:6; cursor:grabbing;
  box-shadow:0 18px 38px -12px rgba(0,0,0,.55), 0 0 0 1.5px color-mix(in srgb, var(--aqua) 55%, transparent); background-color:var(--surface-2, rgba(30,34,40,.96)); opacity:.97; }
.no-anim > .task-item{ transition:none !important; }
/* معاينة بطاقة المتجر */
.peek{ position:fixed; inset:0; z-index:640; }
.peek-scrim{ position:absolute; inset:0; background:radial-gradient(120% 90% at 50% 45%, rgba(8,10,14,.55), rgba(4,5,8,.86)); -webkit-backdrop-filter:blur(7px) saturate(.9); backdrop-filter:blur(7px) saturate(.9);
  opacity:0; transition:opacity 260ms linear; }
.peek.is-in .peek-scrim{ opacity:1; }
.peek.is-out .peek-scrim{ opacity:0; transition-duration:220ms; }
.peek-host{ position:static; }
.peek .shop-card.is-peek{ transform-origin:50% 50%; will-change:transform; filter:drop-shadow(0 26px 40px rgba(0,0,0,.55)); }
.peek .shop-card.is-peek .store-meta, .peek .shop-card.is-peek .shop-acts, .peek .shop-card.is-peek .st-cap{ visibility:hidden; }
.peek-x{ position:absolute; top:calc(var(--safe-t, 0px) + 14px); inset-inline-end:14px; width:44px; height:44px; border-radius:50%; border:0; display:grid; place-items:center; cursor:pointer;
  background:rgb(255 255 255 / .12); color:#fff; opacity:0; transition:opacity 220ms linear 120ms; }
.peek-x svg{ width:18px; height:18px; }
.peek-hint{ position:absolute; left:0; right:0; bottom:calc(var(--safe-b, 0px) + 22px); margin:0; text-align:center; font-size:13px; color:rgb(255 255 255 / .7); opacity:0; transition:opacity 220ms linear 200ms; pointer-events:none; }
.peek.is-in .peek-x, .peek.is-in .peek-hint{ opacity:1; }
.peek.is-out .peek-x, .peek.is-out .peek-hint{ opacity:0; transition-delay:0ms; }
/* مشهد الشراء: ورق وحبر بطابع ريترو كرتوني، والقوة من مستوى السعر */
.bcx{ --c1:236,240,248; --c2:190,200,220; position:fixed; inset:0; z-index:650; display:flex; align-items:center; justify-content:center; overflow:hidden; }
.bcx-scrim{ position:absolute; inset:0; background:
  radial-gradient(circle at 50% 46%, rgba(var(--c1), .22), transparent 58%),
  radial-gradient(rgba(var(--c1), .10) 1.1px, transparent 1.6px) 0 0 / 9px 9px,
  radial-gradient(130% 100% at 50% 45%, rgba(14,12,10,.80), rgba(4,4,6,.94)); }
.bcx-rays{ position:absolute; left:50%; top:46%; width:190vmax; height:190vmax; margin:-95vmax 0 0 -95vmax; pointer-events:none; opacity:.0;
  background:repeating-conic-gradient(from 0deg, rgba(var(--c1), .16) 0deg 7deg, transparent 7deg 22deg);
  -webkit-mask:radial-gradient(circle, #000 0, rgba(0,0,0,.6) 22%, transparent 52%); mask:radial-gradient(circle, #000 0, rgba(0,0,0,.6) 22%, transparent 52%);
  animation:bcx-rays-in .9s .55s ease-out forwards, bcx-spin 26s linear infinite; }
.bcx-rays.is-x2{ background:repeating-conic-gradient(from 0deg, rgba(var(--c2), .2) 0deg 5deg, transparent 5deg 15deg, rgba(var(--c1), .16) 15deg 21deg, transparent 21deg 30deg); }
@keyframes bcx-spin{ to{ transform:rotate(360deg); } }
@keyframes bcx-rays-in{ to{ opacity:1; } }
.bcx-fx{ position:absolute; inset:0; pointer-events:none; }
.bcx-stage{ position:relative; display:flex; flex-direction:column; align-items:center; gap:16px; padding:0 18px; perspective:1100px; }
.bcx-card{ position:relative; transform-origin:50% 50%; transform-style:preserve-3d; will-change:transform; }
.bcx-face{ position:relative; border-radius:var(--card-r, 12px); filter:drop-shadow(7px 9px 0 rgba(10,8,6,.55)) drop-shadow(0 0 26px rgba(var(--c1), .35)); }
.bcx-face > *{ width:100%; }
.bcx-sheen{ position:absolute; inset:0; border-radius:var(--card-r, 12px); overflow:hidden; pointer-events:none; mix-blend-mode:screen; }
.bcx-sheen i{ position:absolute; top:-10%; bottom:-10%; left:0; width:38%; background:linear-gradient(90deg, transparent, rgba(255,255,255,.55), rgba(var(--c1), .35), transparent); transform:translateX(-170%) skewX(-18deg); }
.bcx-ticket{ position:relative; display:flex; flex-direction:column; align-items:center; gap:3px; min-width:min(78vw, 270px); padding:12px 18px 13px; color:#2b1d14;
  background:radial-gradient(rgba(43,29,20,.07) 1px, transparent 1.4px) 0 0 / 6px 6px, linear-gradient(#fbf3df, #f1e2c0);
  border:2px solid #2b1d14; border-radius:6px; box-shadow:5px 6px 0 rgba(10,8,6,.6), inset 0 0 0 3px #fbf3df, inset 0 0 0 4px rgba(var(--c2), .9);
  -webkit-mask:radial-gradient(circle 7px at 0 50%, transparent 98%, #000) left / 51% 100% no-repeat, radial-gradient(circle 7px at 100% 50%, transparent 98%, #000) right / 51% 100% no-repeat;
  mask:radial-gradient(circle 7px at 0 50%, transparent 98%, #000) left / 51% 100% no-repeat, radial-gradient(circle 7px at 100% 50%, transparent 98%, #000) right / 51% 100% no-repeat; }
.bcx-ticket b{ font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:rgb(var(--c2)); filter:brightness(.62) saturate(1.4); }
.bcx-name{ font-size:17px; font-weight:800; max-width:72vw; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bcx-paid{ font-size:12.5px; color:#5b4632; display:inline-flex; align-items:center; gap:4px; }
.bcx-paid .eco-coin{ color:#5b4632; }
.bcx-tmr{ display:inline-flex; align-items:center; gap:4px; font-size:12px; font-weight:700; color:#2f6f6a; }
.bcx-tmr svg{ width:12px; height:12px; }
.bcx-pips{ display:flex; gap:4px; margin-top:4px; }
.bcx-pips i{ width:7px; height:7px; border-radius:50%; border:1.5px solid #2b1d14; background:transparent; }
.bcx-pips i.on{ background:rgb(var(--c2)); box-shadow:0 0 6px rgba(var(--c1), .9); }
.bcx-acts{ display:flex; gap:10px; width:min(84vw, 320px); }
.bcx-acts[hidden]{ display:none; }
.bcx-acts .btn{ flex:1; min-height:52px; font-size:15px; font-weight:800; display:inline-flex; align-items:center; justify-content:center; gap:7px; }
.bcx-acts .bcx-use svg{ width:14px; height:14px; }
.bcx-acts .bcx-keep{ flex:.72; }
.bcx-ring{ position:absolute; width:180px; height:180px; border-radius:50%; border:3px solid rgba(var(--c1), .9); box-shadow:0 0 22px rgba(var(--c1), .7), inset 0 0 18px rgba(var(--c2), .6); }
.bcx-scrap{ position:absolute; background:#f6ecd6; box-shadow:inset 0 0 0 1.5px #2b1d14; }
.bcx-scrap.is-tint{ background:rgb(var(--c2)); }
.bcx-drop{ position:absolute; top:0; width:2px; border-radius:2px; background:linear-gradient(transparent, rgba(var(--c1), .95)); box-shadow:0 0 8px rgba(var(--c1), .8); }
.bcx-conf{ position:absolute; top:0; border-radius:2px; }
.bcx-flare{ position:absolute; inset:0; background:radial-gradient(circle at 50% 46%, rgba(255,250,230,.95), rgba(var(--c1), .55) 30%, transparent 62%); }
.bcx-hole{ position:absolute; border-radius:var(--card-r, 12px); border:2px dashed rgba(var(--c1), .75); background:radial-gradient(rgba(0,0,0,.45), rgba(0,0,0,.2));
  clip-path:polygon(0 3%, 6% 0, 14% 2%, 22% 0, 31% 3%, 40% 0, 50% 2%, 60% 0, 70% 3%, 79% 0, 88% 2%, 96% 0, 100% 4%, 98% 14%, 100% 24%, 97% 35%, 100% 46%, 98% 57%, 100% 68%, 97% 79%, 100% 90%, 97% 100%, 86% 97%, 75% 100%, 63% 97%, 52% 100%, 41% 97%, 30% 100%, 19% 97%, 8% 100%, 0 96%, 2% 85%, 0 74%, 3% 62%, 0 50%, 2% 38%, 0 26%, 3% 14%); }
.bcx.lv-6 .bcx-face, .bcx.lv-7 .bcx-face{ filter:drop-shadow(7px 9px 0 rgba(10,8,6,.55)) drop-shadow(0 0 30px rgba(var(--c1), .55)); }
.bcx.lv-8 .bcx-face, .bcx.lv-9 .bcx-face{ filter:drop-shadow(7px 9px 0 rgba(10,8,6,.55)) drop-shadow(0 0 34px rgba(var(--c1), .7)) drop-shadow(0 0 70px rgba(var(--c2), .45)); }
.bcx.lv-9 .bcx-ticket{ box-shadow:5px 6px 0 rgba(10,8,6,.6), inset 0 0 0 3px #fbf3df, inset 0 0 0 4px rgb(var(--c2)), 0 0 30px rgba(var(--c1), .6); }
.bcx.is-out{ pointer-events:none; }
@media (prefers-reduced-motion:reduce){ .bcx-rays{ animation:none; opacity:.8; } }
"""
rep("</style>", css + "</style>", 'css')
rep("<!-- CODIS-STICKERS -->", "<!-- CODIS-STICKERS -->\n<!-- CODIS-TIMERS -->", 'marker')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('CODIS-TIMERS applied')
