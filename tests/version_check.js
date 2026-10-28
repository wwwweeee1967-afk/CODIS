'use strict';
/* فحص الإصدار: VERSION = <meta codis-version> بالتطبيق، لا أرقام إصدار مكتوبة في أي مكان آخر، والواجهة تقرأ الوسم فقط.
   Usage: node tests/version_check.js [app.html] */
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..'), file = process.argv[2] || path.join(root, 'app', 'CODIS_FINAL.html');
const V = fs.readFileSync(path.join(root, 'VERSION'), 'utf8').trim(), html = fs.readFileSync(file, 'utf8');
let bad = 0; const fail = m=>{ bad++; console.log('FAIL', m); };
if(!/^\d+\.\d+\.\d+$/.test(V)) fail('VERSION format: ' + V);
const metas = html.match(/<meta name="codis-version" content="[^"]*">/g) || [];
if(metas.length !== 1) fail('exactly one codis-version meta expected, found ' + metas.length);
else if(metas[0] !== '<meta name="codis-version" content="' + V + '">') fail('meta (' + metas[0] + ') != VERSION (' + V + ') — run: python tools/set_version.py');
if(/[>'"`]\s*CODIS\s+\d+\.\d+/.test(html)) fail('hardcoded "CODIS x.y" UI label found in the app (code comments are fine)');
if(!/const CODIS_VERSION = \(function\(\)\{ const m = document\.querySelector\('meta\[name="codis-version"\]'\)/.test(html)) fail('CODIS_VERSION must be read from the meta');
if(!/id="app-version-label"/.test(html)) fail('version label element missing');
const leaks = (html.match(/\b(?:APP_VERSION|appVersion|APP_VER)\b/g) || []).length; if(leaks) fail('stray version constants: ' + leaks);
console.log(bad ? '\nFAILED ' + bad : 'OK — version ' + V + ' comes only from VERSION → meta codis-version');
process.exit(bad ? 1 : 0);
