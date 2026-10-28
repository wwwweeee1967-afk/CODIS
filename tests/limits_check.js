'use strict';
/* ADMIN-EXEMPTION GUARD — fails when a restriction that blocks the user is not routed through CodisLimits (so the developer account would be limited).
   Usage: node tests/limits_check.js [app.html]      (default app/CODIS_FINAL.html)
   It checks (1) every known hard-block pattern is on a line that uses CodisLimits, (2) the required bypass sites still exist, (3) the module is verified-only. */
const fs = require('fs'), path = require('path');
const file = process.argv[2] || path.join(__dirname, '..', 'app', 'CODIS_FINAL.html');
const lines = fs.readFileSync(file, 'utf8').split('\n');
let bad = 0;
const fail = (m, i)=>{ bad++; console.log('FAIL', i ? 'line ' + (i + 1) + ': ' : '', m); };

/* (1) hard-block patterns: a returned refusal must sit on / right after a line that consults CodisLimits */
const PATTERNS = [
  [/reason:'insufficient'/, 'insufficient funds refusal'],
  [/reason:'weeklimit'/, 'weekly purchase lock refusal'],
  [/reason:'expired'/, 'expired-card refusal'],
  [/reason:'unsellable'/, 'unsellable refusal'],
  [/(balance|silverBalance\(\)) *\+ *amount *< *0/, 'negative balance guard'],
  [/هذا اليوم لم يأتِ بعد/, 'future-day task lock'],
  [/سجّلت هذي العادة اليوم/, 'same-day weekly-habit lock'],
];
const BEFORE = 1, AFTER = 1;   // the check may be on the same line, up to 2 lines above (multi-line ifs) or inside the block right below
lines.forEach((ln, i)=>{
  if(/showToast\(|econFmt\(res\.need|r\.reason ===|res\.reason ===|\.reason === '/.test(ln) && !/return \{ ?ok:false/.test(ln)) return;   // UI message mapping, not a block
  PATTERNS.forEach(([re, name])=>{
    if(!re.test(ln)) return;
    const ctx = lines.slice(Math.max(0, i - BEFORE), i + 1 + AFTER).join('\n');
    if(!/CodisLimits\./.test(ctx)) fail(name + ' without CodisLimits (developer would be limited): ' + ln.trim().slice(0, 110), i);
  });
});

/* (2) required sites: removing one silently limits the developer */
const html = lines.join('\n');
const need = [
  [/CodisLimits\.afford\(CodisWallet\.balance\(\)/g, 4, 'afford(CodisWallet.balance(), …) purchase checks'], [/CodisLimits\.afford\(bal/g, 4, 'afford(bal, …) UI enable-states'], [/CodisLimits\.bypass\('holiday\.weekly'\)/g, 3, 'holiday weekly lock'],
  [/CodisLimits\.bypass\('holiday\.expireduse'\)/g, 3, 'expired holiday card use'], [/CodisLimits\.bypass\('wallet\.nonnegative'\)/g, 2, 'wallet floor (coins + silver)'], [/CodisLimits\.bypass\('box\.empty'\)/g, 1, 'empty box gate'],
  [/CodisLimits\.bypass\('box\.rtpGate'\)/g, 1, 'box RTP gate'], [/CodisLimits\.bypass\('sell\.unsellable'\)/g, 1, 'unsellable'], [/CodisLimits\.num\('box\.price\.'/g, 1, 'box price override'], [/overridePm\(t,/g, 1, 'box probability override'],
  [/CodisLimits\.bypass\('task\.futureDay'\)/g, 1, 'future-day task lock'], [/CodisLimits\.bypass\('habit\.sameDay'\)/g, 2, 'weekly habit same-day rule'], [/CodisLimits\.bypass\('claim\.crossPlan'\)/g, 2, 'cross-plan duplicate claims'],
  [/CodisLimits\.bypass\('claim\.lateCap'\)/g, 1, 'catch-up reward cap'], [/CodisLimits\.bypass\('claim\.burst'\)/g, 1, 'weekly reward needs several days'], [/CodisLimits\.bypass\('habit\.resistCap'\)/g, 1, 'resist reward daily cap'],
  [/CodisLimits\.bypass\('reward\.protectedOdds'\)/g, 1, 'protected rarity odds'], [/CodisLimits\.num\('box\.refTop'/g, 1, 'box reference top-class probability'],
];
need.forEach(([re, min, name])=>{ const n = (html.match(re) || []).length; if(n < min) fail('missing exemption site: ' + name + ' (found ' + n + ', need ' + min + ')'); });

/* (3) the flag must be verified-only and not settable through exported state */
if(!/isAdmin:\(\) => adminOK === true/.test(html.replace(/\s+/g, ' ').replace('isAdmin:() =>', 'isAdmin:() =>')) && !/isAdmin:\s*\(\)\s*=>\s*adminOK === true/.test(html)) fail('CodisAccount.isAdmin must return the private adminOK flag');
/* adminOK must be set (a) only inside loadAdmin, (b) after the server allowed the private download (storage fetch ok + code received), and (c) BEFORE the add-on script is injected,
   because the add-on's own panels check CodisLimits.verified() while loading (this ordering bug once hid the control panel). */
{ const m = html.match(/async function loadAdmin\(\)\{[\s\S]*?\n  \}\n/);
  if(!m) fail('loadAdmin not found');
  else {
    const b = m[0], iFetch = b.indexOf('/storage/v1/object/authenticated/dev-addon/'), iCode = b.indexOf('const code = await f.text()'), iOK = b.search(/adminOK\s*=\s*true/), iInject = b.indexOf('appendChild(sc)');
    if(iOK < 0) fail('adminOK is never set in loadAdmin');
    else if(!(iFetch >= 0 && iCode > iFetch && iOK > iCode)) fail('adminOK must be set only after the private add-on download succeeded');
    else if(!(iInject > iOK)) fail('adminOK must be set BEFORE the add-on script is injected (its panels verify on load)');
  } }
if((html.match(/adminOK\s*=\s*true/g) || []).length !== 1) fail('adminOK must be assigned true in exactly one place');

console.log(bad ? '\nFAILED: ' + bad + ' problem(s). Route the restriction through CodisLimits (see CLAUDE.md → Admin exemption rule).' : 'OK — every user restriction is exempt for the verified developer; guard intact.');
process.exit(bad ? 1 : 0);
