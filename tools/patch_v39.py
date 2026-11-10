"""CODIS-CLOCK (3.26.0) — ساعة منطقية مركزية لمختبر الزمن في إضافة المطوّر.

  py -3 tools/patch_v39.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (after patch_v38; then set_version.py 3.26.0 + build_sw.py)

  • CodisClock (tools/identity/v39.js): الإزاحة 0 للجميع؛ لا تُضبط إلا من مطوّر موثَّق بعد begin()، ولا تُحفظ بأي تخزين.
  • كل موضع «وقت عمل منطقي» (اليوم/الأسبوع/الشهر/الخطط/العادات/المكافآت/انتهاء البطاقات/المؤقتات/ختم الأرشيف والسجل) يقرأ من الساعة.
    مواضع الوقت الحقيقي (الجلسة، المزامنة، الاتصال، الحركة، الإشعارات الفعلية، ساعات الهدوء) لم تُمس.
  • إصلاح كامن: مرآة IndexedDB كانت تُكتب حتى أثناء عزل المعاينة (CODIS_SYNC_HOLD) ⇒ الآن تتوقف.
  • إشعارات النظام الفعلية (CodisPush.show) لا تُرسل أثناء المحاكاة.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-CLOCK' not in s, 'already applied'
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:110])
    s = s.replace(old, new)
def many(old, new, n):
    global s
    assert s.count(old) == n, ('anchor count', s.count(old), n, old[:110])
    s = s.replace(old, new)

clock = open(os.path.join(HERE, 'identity', 'v39.js'), encoding='utf-8').read().rstrip() + '\n'
once("function loadData(){", clock + "function loadData(){")

# --- الوقت المنطقي ---
once("function econNowIso(){ return new Date().toISOString(); }", "function econNowIso(){ return CodisClock.iso(); }")
once("function econThisMonthKey(){ return localDateStr(new Date()).slice(0,7); }", "function econThisMonthKey(){ return localDateStr(CodisClock.date()).slice(0,7); }")
once("function currentWeekId(){ return getWeekId(new Date()); }", "function currentWeekId(){ return getWeekId(CodisClock.date()); }")
once("function dateKeyOffset(offset){ const d=new Date(); d.setDate(d.getDate()+offset); return localDateStr(d); }",
     "function dateKeyOffset(offset){ const d=CodisClock.date(); d.setDate(d.getDate()+offset); return localDateStr(d); }")
many("new Date().getDay()", "CodisClock.day()", 12)
once("nowMs = Date.now(), dayOk", "nowMs = CodisClock.now(), dayOk")
once("expiresMs(c) <= (nowMs === undefined ? Date.now() : nowMs)", "expiresMs(c) <= (nowMs === undefined ? CodisClock.now() : nowMs)")
once("const remainingMs = c=>Math.max(0, expiresMs(c) - Date.now());", "const remainingMs = c=>Math.max(0, expiresMs(c) - CodisClock.now());")
once("const n = new Date(), next = new Date(n.getFullYear(), n.getMonth(), n.getDate()+1, 0, 0, 5);",
     "const n = CodisClock.date(), next = new Date(n.getFullYear(), n.getMonth(), n.getDate()+1, 0, 0, 5);")
once("const diffMin = Math.max(0, Math.floor((Date.now() - t) / 60000));", "const diffMin = Math.max(0, Math.floor((CodisClock.now() - t) / 60000));")
once("createdAt: new Date().toISOString(),", "createdAt: CodisClock.iso(),")
once("const startedAt = new Date().toISOString();", "const startedAt = CodisClock.iso();")
once("const nowIso = new Date().toISOString();", "const nowIso = CodisClock.iso();")
once("new Date().toDateString(), Math.floor(Date.now() / 600000)", "CodisClock.date().toDateString(), Math.floor(CodisClock.now() / 600000)")
once("const ms = Date.parse(el.getAttribute('data-exp')) - Date.now()", "const ms = Date.parse(el.getAttribute('data-exp')) - CodisClock.now()")
once("createdAt:new Date().toISOString(), read:false", "createdAt:CodisClock.iso(), read:false")
once("archivedAt: new Date().toISOString(),", "archivedAt: CodisClock.iso(),")
once("voidedAt:new Date().toISOString()", "voidedAt:CodisClock.iso()")
once("t.restoredAt = new Date().toISOString()", "t.restoredAt = CodisClock.iso()")
many("t.answeredAt = new Date().toISOString()", "t.answeredAt = CodisClock.iso()", 2)
many("CodisTimers.fmt(t.endsAt - Date.now())", "CodisTimers.fmt(t.endsAt - CodisClock.now())", 2)
once("CodisTimers.fmt(_run.endsAt - Date.now())", "CodisTimers.fmt(_run.endsAt - CodisClock.now())")

# --- المؤقتات: داخل وحدة CodisTimers فقط ---
a = s.index("const CodisTimers = (function(){")
b = s.index("_shift:(id, ms)=>", a); b = s.index("\n})();", b)
blk = s[a:b]; assert blk.count('Date.now()') >= 6, blk.count('Date.now()')
s = s[:a] + blk.replace('Date.now()', 'CodisClock.now()') + s[b:]

# --- حماية العزل ---
once("function mirror(raw){\n    pend = raw;", "function mirror(raw){\n    if(window.CODIS_SYNC_HOLD) return;   /* CODIS-CLOCK: لا تُكتب بيانات معزولة (معاينة/محاكاة) بالمرآة الدائمة */\n    pend = raw;")
once("async function show(title, body, tag){\n", "async function show(title, body, tag){\n    if(CodisClock.active()) return false;   /* CODIS-CLOCK: لا إشعارات فعلية أثناء محاكاة الزمن */\n")
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v39 ok', len(s))
