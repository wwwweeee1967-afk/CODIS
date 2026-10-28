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
];
need.forEach(([re, min, name])=>{ const n = (html.match(re) || []).length; if(n < min) fail('missing exemption site: ' + name + ' (found ' + n + ', need ' + min + ')'); });

/* (3) the flag must be verified-only and not settable through exported state */
if(!/isAdmin:\(\) => adminOK === true/.test(html.replace(/\s+/g, ' ').replace('isAdmin:() =>', 'isAdmin:() =>')) && !/isAdmin:\s*\(\)\s*=>\s*adminOK === true/.test(html)) fail('CodisAccount.isAdmin must return the private adminOK flag');
if(/S\.admin\s*=\s*true;\s*adminOK\s*=\s*true/.test(html) === false) fail('adminOK must be set only after the add-on download succeeded (loadAdmin)');
if((html.match(/adminOK\s*=\s*true/g) || []).length !== 1) fail('adminOK must be assigned true in exactly one place');

console.log(bad ? '\nFAILED: ' + bad + ' problem(s). Route the restriction through CodisLimits (see CLAUDE.md → Admin exemption rule).' : 'OK — every user restriction is exempt for the verified developer; guard intact.');
process.exit(bad ? 1 : 0);
