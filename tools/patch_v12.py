#!/usr/bin/env python3
"""CODIS-AUDIT-1 (بعد patch_v11.py): إصلاحات تدقيق شامل — كل بند مؤكَّد بالمتصفح قبل إصلاحه.
 1) شريط الأيام بغرفة العمليات: اليوم النشط كان خارج الجزء الظاهر (التمركز مطبّق لغرفة الأستاذ فقط).
 2) الإعدادات: مجموعة «اقتصاد المكافآت» صارت فارغة (صف القرارات المعلّقة مخفي) فظهرت كخط فاصل يتيم ← الصف ينضم لمجموعة المكافآت؛ الصوت والإشعارات مجموعة واحدة.
 3) ساعات الهدوء كانت بأيقونة قفل (معنى خاطئ) ← أيقونة قمر جديدة بنفس نظام الأيقونات.
 4) نص قفل التطبيق كان يدّعي «ينحفظ على هذا الجهاز بس» بينما الرمز المشفّر يتزامن مع الحساب عند الدخول (Face ID فقط يبقى محلياً) ← نص مطابق للتنفيذ.
 5) سجل الكوينز: «−0» و«+0» بلون الربح/الخسارة عند الصفر ← «0» محايد."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-AUDIT-1' in s: sys.exit('already patched (CODIS-AUDIT-1)')

def rep(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('anchor "%s" matched %d times (want %d)' % (label, n, count))
    s = s.replace(old, new)

# 1) تمركز اليوم النشط في كل الغرف
rep("    if(key === 'learn'){ const a = wrap.querySelector('.day-tab.active'); if(a && wrap.scrollWidth > wrap.clientWidth){",
    "    { const a = wrap.querySelector('.day-tab.active'); if(a && wrap.scrollWidth > wrap.clientWidth){   /* CODIS-AUDIT-1: كل الغرف (كان للأستاذ فقط) */", 'day tabs center')

# 2) مجموعات الإعدادات
rep("""              <span class="ios-row-title">المكافآت والعقوبات</span>
              <span class="ios-row-trailing"><svg class="ios-chevron" data-icon="forward"></svg></span>
            </button>
          </div>
        </div>

        <div role="group" aria-label="اقتصاد المكافآت">
          <div class="ios-list">
            <button type="button" class="ios-row" id="home-pending-row" style="display:none;" onclick="econOpenPending()">""",
"""              <span class="ios-row-title">المكافآت والعقوبات</span>
              <span class="ios-row-trailing"><svg class="ios-chevron" data-icon="forward"></svg></span>
            </button>
            <button type="button" class="ios-row" id="home-pending-row" style="display:none;" onclick="econOpenPending()">""", 'pending row into rewards group')
rep("""              <span class="ios-row-trailing"><span class="ios-row-badge" id="home-sound-state">مفعّلة</span><svg class="ios-chevron" data-icon="forward"></svg></span>
            </button>
          </div>
        </div>

        <div role="group" aria-label="الإشعارات">
          <div class="ios-list">
            <button type="button" class="ios-row" onclick="openSettingsCategory('notifications')">""",
"""              <span class="ios-row-trailing"><span class="ios-row-badge" id="home-sound-state">مفعّلة</span><svg class="ios-chevron" data-icon="forward"></svg></span>
            </button>
            <button type="button" class="ios-row" onclick="openSettingsCategory('notifications')">""", 'sound+notif group')
rep('<div role="group" aria-label="الصوت">', '<div role="group" aria-label="الصوت والإشعارات">', 'group label')

# 3) أيقونة قمر لساعات الهدوء
rep("""  bell: { id:'icon-bell', meaning:'إشعارات', size:'md',""",
"""  moon: { id:'icon-moon', meaning:'ساعات الهدوء', size:'md',
    body:'<path d="M19.2 14.6A7.6 7.6 0 0 1 9.4 4.8a7.6 7.6 0 1 0 9.8 9.8Z"/><path d="M16.4 4.2v2.6M15.1 5.5h2.6"/>' },
  bell: { id:'icon-bell', meaning:'إشعارات', size:'md',""", 'moon icon')
rep("""            <div class="settings-icon-badge tone-neutral"><svg data-icon="lock" data-size="md"></svg></div>
            <div style="flex:1; min-width:0;">
              <div class="settings-card-title">ساعات الهدوء</div>""",
"""            <div class="settings-icon-badge tone-neutral"><svg data-icon="moon" data-size="md"></svg></div>
            <div style="flex:1; min-width:0;">
              <div class="settings-card-title">ساعات الهدوء</div>""", 'quiet hours icon')

# 4) نص تخزين رمز القفل مطابق للتنفيذ
rep('<div class="settings-note">الرمز ما ينحفظ كما هو، ينحفظ مشفّر على هذا الجهاز بس.</div>',
    '<div class="settings-note">الرمز ما ينحفظ كما هو، ينحفظ مشفّر. إذا مسجّل دخول يتزامن مشفّراً مع حسابك، أما Face ID فيبقى على هذا الجهاز فقط.</div>', 'lock storage note')

# 5) أصفار سجل الكوينز
rep("""    '<div class="settings-card"><span class="eco-lab">إجمالي المكتسب</span><b class="eco-up">+' + econFmt(w.lifetimeEarned) + '</b></div>' +
    '<div class="settings-card"><span class="eco-lab">إجمالي المصروف</span><b class="eco-down">−' + econFmt(w.lifetimeSpent) + '</b></div></div>';""",
"""    '<div class="settings-card"><span class="eco-lab">إجمالي المكتسب</span>' + (w.lifetimeEarned > 0 ? '<b class="eco-up">+' + econFmt(w.lifetimeEarned) + '</b>' : '<b>0</b>') + '</div>' +
    '<div class="settings-card"><span class="eco-lab">إجمالي المصروف</span>' + (w.lifetimeSpent > 0 ? '<b class="eco-down">−' + econFmt(w.lifetimeSpent) + '</b>' : '<b>0</b>') + '</div></div>';""", 'coin log zeros')


# 6) نص يشير إلى صفحة محذوفة («حدود الإنجاز») ← الحدود الفعلية من مصدرها الواحد
rep("  return 'غرفة العمليات: تلقائية حسب حدود الإنجاز اليومية.';", "  { const th = econThresholds(); return 'غرفة العمليات: تلقائية — مكافأة من ' + th.reward + '% من إنجاز اليوم، وعقوبة تحت ' + th.punish + '%.'; }", 'rp note thresholds')

s = s.replace('<!-- CODIS-AUDIO-V2 -->', '<!-- CODIS-AUDIO-V2 -->\n<!-- CODIS-AUDIT-1 -->', 1)
if 'CODIS-AUDIT-1 -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v12 OK')
