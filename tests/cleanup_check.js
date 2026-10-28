'use strict';
/* فحص الإزالات (patch_v2): لا مسار للمستخدم لتعديل قواعد المكافآت، لا نسخ احتياطي يدوي، لا عبارة «بجهازك بس»، والحساب/المزامنة سليمان.
   Usage: node tests/cleanup_check.js [app.html] */
const fs = require('fs'), path = require('path');
const file = process.argv[2] || path.join(__dirname, '..', 'app', 'CODIS_FINAL.html'), html = fs.readFileSync(file, 'utf8');
let bad = 0; const fail = m=>{ bad++; console.log('FAIL', m); }, has = re=>re.test(html);
[
  [/settings-page-eco-periods|openSettingsCategory\('eco-periods'\)|econRenderPeriods|econResetRules/, 'Reward Rules page/handlers still present'],
  [/settings-page-thresholds|saveThresholds|set-reward-threshold|set-punish-threshold|updateThresholdBar/, 'Thresholds editor still present'],
  [/renderAchievementSettings|achSetPath|achReset|ach-settings-body/, 'task-weight settings editor still present'],
  [/function econSetPath|function econSwitch|function econNumInput/, 'generic economy-config writer still present'],
  [/codisExportBackup|codisImportBackup|codisValidateBackup|BACKUP_FORMAT|PRE_RESTORE_KEY|backup-file|settings-page-data/, 'manual backup feature still present'],
  [/ما تنرسل لأي مكان|محفوظة بجهازك بس/, 'outdated "device-only" claim still present'],
  [/صدّر نسخة احتياطية/, 'text telling the user to export a backup still present'],
].forEach(([re, m])=>{ if(has(re)) fail(m); });
/* must remain */
[
  [/const CodisAccount = /, 'CodisAccount (auth + sync)'], [/save_progress/, 'save_progress RPC'], [/function backupLocal\(/, 'sync safety copies (backupLocal)'],
  [/function econThresholds\(\)/, 'internal thresholds'], [/function econDefaults\(\)/, 'internal reward defaults'], [/s\.rulesLockedV2/, 'rules-lock migration'],
  [/function econReportsListHtml\(\)/, 'saved reports renderer'], [/eco-sec-title">التقارير المحفوظة/, 'saved reports shown in the coin log'],
].forEach(([re, m])=>{ if(!has(re)) fail('missing: ' + m); });
console.log(bad ? '\nFAILED ' + bad : 'OK — reward-rules UI, manual backup and the outdated storage claim are gone; account sync intact');
process.exit(bad ? 1 : 0);
