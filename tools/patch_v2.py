#!/usr/bin/env python3
"""CODIS-V2 (يعمل بعد patch_rules.py):
  1) حذف صفحتي «قواعد المكافآت» و«حدود الإنجاز» (لا مسار للمستخدم لتعديل قواعد المكافآت) + تثبيت القيم الداخلية مرة وحدة (ترحيل)
  2) حذف النسخ الاحتياطي اليدوي (تصدير/استيراد)
  3) حذف عبارة «بياناتك بجهازك بس…» + تصحيح رسائل مشابهة
  4) مصدر واحد للإصدار: <meta name="codis-version"> (يكتبه tools/set_version.py من ملف VERSION)
  الاستخدام: python tools/patch_v2.py <in.html> <out.html>
  كل استبدال يجب أن يطابق مرة واحدة بالضبط وإلا يفشل السكربت."""
import sys, re

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-V2' in s:
    sys.exit('already patched (CODIS-V2)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

def cut(start, end, label):
    """يحذف من أول start حتى قبل end (end يبقى). start مرة وحدة."""
    global s
    if s.count(start) != 1: sys.exit('cut start "%s" matched %d' % (label, s.count(start)))
    i = s.index(start)
    j = s.find(end, i + len(start))
    if j < 0: sys.exit('cut end "%s" missing' % label)
    s = s[:i] + s[j:]

# ---------- 1) قواعد المكافآت + حدود الإنجاز ----------
cut('            <button type="button" class="ios-row" onclick="openSettingsCategory(\'eco-periods\')">',
    '          </div>\n        </div>\n\n        <div role="group" aria-label="الصوت">', 'row eco-periods')
cut('            <button type="button" class="ios-row" onclick="openSettingsCategory(\'thresholds\')">',
    '            <button type="button" class="ios-row" onclick="openSettingsCategory(\'rp\')">', 'row thresholds')
cut('    <!-- ============ قسم: حدود الإنجاز ============ -->', '    <div id="settings-page-rp"', 'page thresholds')
cut('    <div id="settings-page-eco-periods"', '    <!-- ============ قسم: الصوت ============ -->    <!-- ============ قسم: الصوت ============ -->', 'page eco-periods')
rep('    <!-- ============ قسم: الصوت ============ -->    <!-- ============ قسم: الصوت ============ -->', '    <!-- ============ قسم: الصوت ============ -->', 'dup comment')
s, n1 = re.subn(r'#settings-page-eco-periods \.settings-section-head::before\{[^\n]*\n', '', s, count=1)
s, n2 = re.subn(r'#settings-page-thresholds \.settings-section-head::before\{[^\n]*\n', '', s, count=1)
if n1 != 1 or n2 != 1: sys.exit('css heads not found')
rep("'eco-periods':'econRenderPeriods', ", '', 'ECON_PAGES')
cut('/* ---- إعدادات وزن المهام والإنجاز الجزئي (data.settings.achievement) ---- */', 'function renderSettings(){', 'ach settings fns')
rep("  renderAchievementSettings();\n  const rEl = document.getElementById('set-reward-threshold');\n  const pEl = document.getElementById('set-punish-threshold');\n  if(rEl) rEl.value = data.settings.rewardThreshold;\n  if(pEl) pEl.value = data.settings.punishThreshold;\n  updateThresholdBar();\n", '', 'renderSettings thresholds')
cut('function updateThresholdBar(){', '/* Toast: رسالة قصيرة', 'updateThresholdBar')
cut('function saveThresholds(){', '/* ================= REWARD ECONOMY — UI =================', 'saveThresholds')
cut('/* ---- قواعد المكافآت: صفحة واحدة بسيطة.', '/* ---- المتجر: كل المكافآت من كل الغرف', 'econRenderPeriods block')
cut('function econNumInput(path, val, o){', 'function econRarityOptions(){', 'econNumInput/econSwitch')
cut('/* يكتب قيمة إعداد بمسارها داخل data.settings.economy', 'function econRenderAll(){', 'econSetPath')
# التقارير المحفوظة (عرض فقط) تنتقل إلى سجل الكوينز
rep("  const up = CodisPasses.used().sort(", "  html += '<div class=\"eco-sec-title\">التقارير المحفوظة</div><div class=\"settings-card\">' + econReportsListHtml() + '</div>';\n  const up = CodisPasses.used().sort(", 'reports into log')

# تثبيت القواعد الداخلية (ترحيل مرة وحدة). العناصر والمحفظة والسجل وتكاليف العقوبات لا تُمسّ
rep("  s.economy = econNormalizeConfig(s.economy);\n  const legacy =",
    "  s.economy = econNormalizeConfig(s.economy);\n"
    "  if(!s.rulesLockedV2){   /* CODIS-V2: قواعد المكافآت داخلية ثابتة — يُعاد ضبط ما كان قابلاً للتعديل مرة وحدة */\n"
    "    const keepCosts = s.economy.penaltyCosts, def = econDefaults();\n"
    "    s.economy = econNormalizeConfig(Object.assign(def, keepCosts ? { penaltyCosts:keepCosts } : {}));\n"
    "    s.rewardThreshold = 90; s.punishThreshold = 70; s.achievement = codisNormalizeAchievement(null); s.rulesLockedV2 = 1;\n"
    "    window.__econMigrated = true;\n"
    "  }\n  const legacy =", 'rules lock migration')

# ---------- 2) النسخ الاحتياطي اليدوي ----------
cut('            <button type="button" class="ios-row" onclick="openSettingsCategory(\'data\')">', '          </div>\n        </div>\n\n      </div>\n\n      <div class="settings-foot">', 'row backup')
cut('    <!-- ============ قسم: النسخ الاحتياطي ============ -->', '  </div>\n</div>\n\n<!-- ===================== ARCHIVE DETAIL MODAL', 'page backup')
cut('/* ================= BACKUP / RESTORE (النسخ الاحتياطي) =================', '/* ================= OUTCOME LEDGER (سجل النتائج) =================', 'backup fns')
s, n3 = re.subn(r'#settings-page-data \.settings-section-head::before\{[^\n]*\n', '', s, count=1)
if n3 != 1: sys.exit('css data head not found')
rep("    step('backup', function(){ const el = document.getElementById('backup-schema-version'); if(el) el.textContent = SCHEMA_VERSION; });\n", '', 'boot backup step')
rep("showToast('مساحة التخزين تقترب من الامتلاء — صدّر نسخة احتياطية من الإعدادات', 'var(--warning)');", "showToast('مساحة التخزين تقترب من الامتلاء — فكّر بحذف الأرشيف القديم', 'var(--warning)');", 'storage toast')
rep("message:'صدّر نسخة احتياطية من الإعدادات، ثم فكّر بحذف الأرشيف ا", "message:'فكّر بحذف الأرشيف ا", 'storage event msg')

# ---------- 3) عبارة الخصوصية القديمة + 4) الإصدار ----------
rep('        <span class="eyebrow">CODIS 3.1</span>\n        <span>كل بياناتك محفوظة بجهازك بس، ما تنرسل لأي مكان.</span>\n',
    '        <span class="eyebrow" id="app-version-label">CODIS</span>\n', 'footer')
rep('<meta name="codis-supabase-url"', '<meta name="codis-version" content="0.0.0">\n<meta name="codis-supabase-url"', 'version meta')
rep('function renderSettings(){',
    '/* CODIS-V2: الإصدار يأتي من <meta name="codis-version"> فقط (يكتبه tools/set_version.py من ملف VERSION) */\n'
    'const CODIS_VERSION = (function(){ const m = document.querySelector(\'meta[name="codis-version"]\'); return (m && m.content) || \'\'; })();\n'
    'function renderSettings(){\n  { const el = document.getElementById(\'app-version-label\'); if(el) el.textContent = CODIS_VERSION ? \'CODIS \' + CODIS_VERSION : \'CODIS\'; }\n', 'version label')

s = s.replace('<!DOCTYPE html>', '<!DOCTYPE html>\n<!-- CODIS-V2 -->', 1) if '<!DOCTYPE html>' in s else '<!-- CODIS-V2 -->\n' + s
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v2 OK')
