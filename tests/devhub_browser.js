/* CODIS-HUB + CODIS-CLOCK browser test (headless Chrome through tools/prof/cdp.mjs):
   TEST=tests/devhub_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   Needs a static server rooted at the project (so /addons/dev-addon.js is fetchable) — the add-on is private; never serve it publicly.
   The admin flag is faked ONLY inside this test page (CodisAccount.isAdmin override) to exercise the add-on; server authorisation is covered by tests/run_admin_sqltest.js. */
(async function(){
  const results = []; const T = (name, ok, info)=>{ results.push({ name, ok:!!ok, info:info === undefined ? '' : String(info) }); };
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const realDate = Date, realNow = Date.now;
  try{
    /* ---------- 0) قبل أي إضافة: الساعة للمستخدم العادي ---------- */
    T('ساعة المستخدم العادي: إزاحة 0 وغير مفعّلة', CodisClock.offset() === 0 && CodisClock.active() === false);
    T('begin() مرفوض لغير الموثَّق', CodisClock.begin() === false && CodisClock.active() === false);
    T('shiftDays/setDay مرفوضتان بلا begin', CodisClock.shiftDays(1) === false && CodisClock.setDay('2030-01-01') === false);
    T('Date.now لم تُبدَّل', Date.now === realNow && /native code/.test(Function.prototype.toString.call(Date.now)));
    T('todayKey = ساعة الجهاز', todayKey() === localDateStr(new Date()));

    /* ---------- 1) تحميل الإضافة كمطوّر (محاكاة محلية فقط) ---------- */
    CodisAccount.isAdmin = ()=>true;
    window.codisConfirm = async ()=>true;
    const code = await (await fetch('/addons/dev-addon.js')).text();
    const sc = document.createElement('script'); sc.textContent = code + '\n//# sourceURL=codis-dev-addon.js'; document.head.appendChild(sc); await sleep(400);
    const HUB = window.CodisHub;
    T('المركز مُحمَّل', !!HUB && typeof HUB.go === 'function');
    T('أقسام المركز الستة', JSON.stringify(HUB.tabs().map(t=>t.id)) === JSON.stringify(['home', 'time', 'settings', 'gifts', 'diag', 'preview']), HUB.tabs().map(t=>t.id).join(','));
    T('باب واحد في الإعدادات (القديمة مخفية/محذوفة)', document.getElementById('hub-panel-group') && !document.getElementById('adm-panel-group') && !document.getElementById('pwr-panel-group') && getComputedStyle(document.getElementById('dev-panel-group')).display === 'none');
    T('begin() للموثَّق يعمل ثم end()', CodisClock.begin() === true && CodisClock.active() === true && CodisClock.end() === true && CodisClock.offset() === 0);

    /* ---------- 2) حدود الزمن مباشرة على الساعة ---------- */
    CodisClock.begin();
    CodisClock.setDay('2028-02-28'); const a = CodisClock.key(); CodisClock.shiftDays(1); const b = CodisClock.key(); CodisClock.shiftDays(1); const c = CodisClock.key();
    T('سنة كبيسة: 28 فبراير ← 29 ← 1 مارس', a === '2028-02-28' && b === '2028-02-29' && c === '2028-03-01', [a, b, c].join(' '));
    CodisClock.setDay('2027-02-28'); CodisClock.shiftDays(1);
    T('سنة غير كبيسة: 28 فبراير ← 1 مارس', CodisClock.key() === '2027-03-01', CodisClock.key());
    CodisClock.setDay('2026-12-31'); CodisClock.shiftDays(1);
    T('حد السنة: 31 ديسمبر ← 1 يناير', CodisClock.key() === '2027-01-01' && todayKey() === '2027-01-01' && localDateStr(CodisClock.date()) === '2027-01-01');
    T('تاريخ مستحيل مرفوض', CodisClock.setDay('2026-02-30') === false && CodisClock.setDay('2026-13-01') === false && CodisClock.setDay('x') === false);
    CodisClock.setDay('2026-03-28'); CodisClock.shiftDays(3);   /* عبور تغيّر التوقيت الصيفي في معظم المناطق */
    T('عبور تغيّر التوقيت: +3 أيام تقويمية بالضبط', CodisClock.key() === '2026-03-31', CodisClock.key());
    T('حد أقصى للقفزة', CodisClock.shiftDays(99999) === false);
    CodisClock.end();
    T('end(): إزاحة 0 ومفتاح اليوم الحقيقي', CodisClock.offset() === 0 && todayKey() === localDateStr(new Date()));

    /* ---------- 3) مختبر الزمن: يوم / 7 أيام بالتتابع + العزل + الاستعادة ---------- */
    const hab = { id:'hsim1', text:'عادة اختبار مختبر الزمن', type:'E', importance:'normal', createdAt:dateKeyOffset(-3), log:{} };
    data.habits.build.push(hab); normalizeHabit(hab, 'build'); hab.checkedThrough = dateKeyOffset(-1); saveData();
    const rawBefore = localStorage.getItem(STORE_KEY), jsonBefore = JSON.stringify(data), realKey = todayKey();
    const TL = HUB.get('time');
    await TL._start();
    T('المحاكاة بدأت', TL.state().on === true && CodisClock.active() === true);
    T('CODIS_SYNC_HOLD = true أثناء المحاكاة', window.CODIS_SYNC_HOLD === true);
    T('نسخة العمل غير الأصل', typeof data === 'object' && JSON.stringify(data) === jsonBefore && data.habits.build.some(h=>h.id === 'hsim1'));
    const h1 = ()=>data.habits.build.find(h=>h.id === 'hsim1');
    const m0 = h1().misses.length;
    await TL._advance(1);
    const k1 = CodisClock.key();
    T('تمرير يوم: التاريخ +1', k1 === addDaysKey(realKey, 1), k1 + ' vs ' + realKey);
    T('تمرير يوم: فاتت عادة اليوم الفائت مرة واحدة', h1().misses.length === m0 + 1, m0 + ' → ' + h1().misses.length);
    const logLen1 = TL._log().length;
    await TL._advance(7);
    const k8 = CodisClock.key();
    T('تمرير 7 أيام: +8 إجمالاً', k8 === addDaysKey(realKey, 8), k8);
    T('تمرير 7 أيام: سجل 8 أيام متتالية بلا فجوات', TL._log().length === logLen1 + 7 && TL._log().slice().reverse().every((r, i, arr)=>i === 0 || r.key === addDaysKey(arr[i - 1].key, 1)), TL._log().map(r=>r.key).join(' '));
    T('تمرير 7 أيام: خمس فواتات متتابعة بلا تكرار', h1().misses.length === m0 + 8 && new Set(h1().misses.map(m=>m.date)).size === h1().misses.length, h1().misses.length);
    const txBefore = data.wallet.transactions.length, missBefore = h1().misses.length;
    runHabitChecks(); runHabitChecks(); econTick(); codisCheckDayChange();
    T('إعادة تشغيل الفحوص لا تكرر شيئاً (idempotent)', h1().misses.length === missBefore && data.wallet.transactions.length === txBefore);
    const ids = data.wallet.transactions.map(t=>t.type + '|' + t.referenceId).filter(x=>!/\|$/.test(x));
    T('لا معاملات مكررة بالدفتر', new Set(ids).size === ids.length);
    T('لا تسرب للتخزين الحقيقي أثناء المحاكاة', U_real().getItem(STORE_KEY) === rawBefore);
    function U_real(){ return HUB.util.REAL_LS; }
    T('علَم المحاكاة موجود أثناء العمل (للانقطاع)', !!U_real().getItem('codis_timelab_flag_v1') && !!U_real().getItem('codis_timelab_restore_v1'));
    T('الساعة الحقيقية لم تُمس (Date.now ≈ الآن)', Math.abs(realNow.call(Date) - realNow()) < 50 && Math.abs(CodisClock.real() - realNow()) < 50);
    await TL._end('test');
    T('إنهاء: بيانات الأصل مطابقة حرفياً', JSON.stringify(data) === jsonBefore);
    T('إنهاء: التخزين الحقيقي كما كان', U_real().getItem(STORE_KEY) === rawBefore && localStorage === U_real());
    T('إنهاء: الساعة والعزل والعلم عادوا', CodisClock.offset() === 0 && !CodisClock.active() && window.CODIS_SYNC_HOLD === false && !U_real().getItem('codis_timelab_flag_v1') && !U_real().getItem('codis_timelab_restore_v1') && todayKey() === realKey);
    T('إنهاء: لا يزال فحص العادات الأصلي سليماً', data.habits.build.find(h=>h.id === 'hsim1').misses.length === m0);

    /* ---------- 4) الإعدادات: بحث/تحقق/حفظ/استعادة ---------- */
    HUB.go('settings'); await sleep(60);
    const root = document.getElementById('hub-root'), input = (el, v)=>{ el.value = v; el.dispatchEvent(new Event('input', { bubbles:true })); };
    const q = root.querySelector('#st-q'); input(q, 'تفكيك'); await sleep(30);
    T('بحث الإعدادات يجد نتائج', root.querySelectorAll('.st-row').length >= 2, root.querySelectorAll('.st-row').length);
    const rate = root.querySelector('[data-n="dismantle.rate"]');
    input(rate, '-5'); await sleep(20);
    T('قيمة خارج النطاق ترفض الحفظ', root.querySelector('[data-act="save"]').disabled === true && rate.getAttribute('aria-invalid') === 'true');
    input(rate, '2'); await sleep(20);
    T('قيمة صالحة تفعّل الحفظ وتظهر «غير محفوظ»', root.querySelector('[data-act="save"]').disabled === false && /غير محفوظ/.test(root.querySelector('#st-bar').textContent));
    T('لا تطبيق قبل الحفظ', CodisLimits.num('dismantle.rate', 1.5) === 1.5);
    root.querySelector('[data-act="save"]').click(); await sleep(40);
    T('الحفظ يطبّق على المنطق الفعلي (CodisLimits.num)', CodisLimits.num('dismantle.rate', 1.5) === 2 && data.adminOverrides.constants['dismantle.rate'] === 2);
    root.querySelector('[data-act="reset"][data-id="const.dismantle.rate"]').click(); await sleep(20);
    root.querySelector('[data-act="save"]').click(); await sleep(40);
    T('الاستعادة الافتراضية تزيل التعديل', CodisLimits.num('dismantle.rate', 1.5) === 1.5 && !('dismantle.rate' in data.adminOverrides.constants));
    HUB.go('settings'); await sleep(30); input(root.querySelector('#st-q'), 'العطلة'); await sleep(20);
    const tg = root.querySelector('input[data-t="limit.holiday.weekly"]'); tg.checked = false; tg.dispatchEvent(new Event('change', { bubbles:true })); await sleep(20);
    root.querySelector('[data-act="save"]').click(); await sleep(40);
    T('إبقاء قيد يعيده فعلياً للتطبيق', CodisLimits.bypass('holiday.weekly') === false && data.adminPower.keep['holiday.weekly'] === true);
    HUB.go('settings'); input(root.querySelector('#st-q'), 'العطلة'); await sleep(20);
    root.querySelector('[data-act="reset"][data-id="limit.holiday.weekly"]').click(); root.querySelector('[data-act="save"]').click(); await sleep(40);
    T('إرجاع القيد يعيد التجاوز', CodisLimits.bypass('holiday.weekly') === true && !data.adminPower.keep['holiday.weekly']);
    const ctrlN = HUB.perms().length; T('سجل الصلاحيات غير فارغ وكل عنصر بمعرّف ونظام ونطاق', ctrlN > 20 && HUB.perms().every(p=>p.id && p.name && p.system && p.scope), ctrlN);

    /* ---------- 5) الهدايا: معرّف طلب ثابت، لا تكرار عند انقطاع الشبكة ---------- */
    const U1 = '11111111-1111-4111-8111-111111111111', U2 = '22222222-2222-4222-8222-222222222222', calls = [];
    const users = [{ user_id:U1, email:'a@test.local', full_name:'أحمد', coins:5, silver:1, total_count:2 }, { user_id:U2, email:'b@test.local', full_name:'سارة', coins:7, silver:0, total_count:2 }];
    let failNext = true, v2 = true;
    CodisAccount.adminCall = async (fn, body)=>{
      calls.push({ fn, body });
      if(fn === 'admin_list_users') return users;
      if(fn === 'admin_stats') return { users:2, active_7d:1, pending_grants:3, pending_messages:1, banned:0 };
      if(fn === 'admin_grant_v2'){ if(!v2) throw Object.assign(new Error('Could not find the function'), { code:'PGRST202' }); if(failNext){ failNext = false; throw Object.assign(new Error('net'), { net:true }); } return { n:2, duplicate:false }; }
      if(fn === 'admin_grant'){ return 2; }
      if(fn === 'admin_list_grants') return [];
      return null;
    };
    HUB.go('gifts'); await sleep(120);
    const gr = ()=>document.getElementById('hub-root');
    gr().querySelector('#gf-all').click(); await sleep(20);
    gr().querySelector('#gf-coins').value = '50'; gr().querySelector('#gf-coins').dispatchEvent(new Event('input', { bubbles:true }));
    gr().querySelector('#gf-note').value = 'اختبار'; gr().querySelector('#gf-note').dispatchEvent(new Event('input', { bubbles:true }));
    gr().querySelector('[data-act="preview"]').click(); await sleep(30);
    T('معاينة الهدية تعرض التفاصيل قبل الإرسال', /تفاصيل العملية/.test(gr().textContent) && /\+50/.test(gr().textContent) && /هدية من المطوّر/.test(gr().textContent));
    gr().querySelector('[data-act="send"]').click(); await sleep(80);
    T('انقطاع الشبكة ← «غير مؤكدة» (لا تُعدّ ناجحة)', /غير مؤكدة/.test(gr().textContent));
    gr().querySelector('[data-act="send"]').click(); await sleep(80);
    const g2 = calls.filter(c=>c.fn === 'admin_grant_v2');
    T('إعادة المحاولة بنفس معرّف الطلب (لا تكرار)', g2.length === 2 && g2[0].body.p_request === g2[1].body.p_request && /UUID|[0-9a-f-]{36}/i.test(g2[0].body.p_request), g2.map(x=>x.body.p_request).join(' / '));
    T('بعد النجاح: حالة «تم الإرسال»', /تم الإرسال/.test(gr().textContent));
    gr().querySelector('[data-act="mode"][data-m="deduct"]').click(); await sleep(20);
    gr().querySelector('#gf-silver').value = '9'; gr().querySelector('#gf-silver').dispatchEvent(new Event('input', { bubbles:true }));
    gr().querySelector('[data-act="preview"]').click(); await sleep(30);
    T('وضع الخصم منفصل: يرسل سالباً ويصنّفه تعديلاً', /تعديل من المطوّر/.test(gr().textContent) && /−9/.test(gr().textContent) || /-9/.test(gr().textContent), gr().textContent.slice(gr().textContent.indexOf('تفاصيل'), gr().textContent.indexOf('تفاصيل') + 200));
    v2 = false; failNext = false;
    gr().querySelector('[data-act="send"]').click(); await sleep(80);
    const legacy = calls.filter(c=>c.fn === 'admin_grant');
    T('خادم بلا v2: يرجع للنظام القديم مرة واحدة', legacy.length === 1 && legacy[0].body.p_silver === -9 && legacy[0].body.p_coins === 0, JSON.stringify(legacy.map(l=>l.body)));

    /* ---------- 6) لوحة التحكم: أرقام حقيقية فقط ---------- */
    HUB.go('home'); await sleep(150);
    T('لوحة التحكم تعرض إحصاءات الخادم الفعلية (لا أرقام وهمية)', /هدايا بانتظار الاستلام/.test(gr().textContent) && /\b3\b/.test(gr().textContent));
    CodisAccount.adminCall = async ()=>{ throw Object.assign(new Error('x'), { net:true }); };
    await HUB.refreshStats(); await sleep(60);
    T('فشل الخادم: رسالة صريحة بدل أرقام', /لا يوجد اتصال بالخادم/.test(gr().textContent));

    /* ---------- 7) التشخيص ---------- */
    HUB.go('diag'); await sleep(30);
    gr().querySelector('[data-act="check"]').click(); await sleep(60);
    const rows = gr().querySelectorAll('.hub-list .hub-badge');
    T('فحص السلامة يعمل ويعرض نتائج', rows.length >= 8, rows.length);
    let blobText = null; const oc = URL.createObjectURL; URL.createObjectURL = b=>{ b.text().then(t=>{ blobText = t; }); return 'blob:x'; };
    gr().querySelector('[data-act="export"]').click(); await sleep(150); URL.createObjectURL = oc;
    T('التقرير المصدَّر منقّح (بلا رموز/مفاتيح/إيميلات/بيانات شخصية)', blobText && !/eyJ|sb_|service_role|access_token|refresh_token|@/.test(blobText) && /"checks"/.test(blobText), blobText ? blobText.length : 'لا تقرير');

    /* ---------- 8) الأمان: غير الموثَّق لا يبني شيئاً ---------- */
    T('CodisLimits يفشل مغلقاً لغير الموثَّق', (()=>{ const f = CodisAccount.isAdmin; CodisAccount.isAdmin = ()=>false; const r = CodisLimits.on() === false && CodisLimits.bypass('x.y') === false && CodisClock.begin() === false; CodisAccount.isAdmin = f; return r; })());
  }catch(e){ T('EXCEPTION', false, (e && e.stack) || e); }
  try{ CodisClock.end(); }catch(e){}
  return { results, passed:results.filter(r=>r.ok).length, failed:results.filter(r=>!r.ok).length };
})()
