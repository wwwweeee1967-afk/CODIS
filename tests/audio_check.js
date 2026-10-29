'use strict';
/* CODIS-AUDIO-V2 static check: every sound call resolves to a defined identity; context identities exist; generic leftovers listed; defined-but-unused listed.
   Usage: node tests/audio_check.js [app.html] */
const fs = require('fs'), path = require('path');
const html = fs.readFileSync(process.argv[2] || path.join(__dirname, '..', 'app', 'CODIS_FINAL.html'), 'utf8');
const defs = new Set(); for(const m of html.matchAll(/^\s*'([a-z][a-z0-9.]*(?:@[a-z]+)?)':\s*\{\s*ch:'(ui|xp|reward|discipline)'/gm)) defs.add(m[1]);
let bad = 0; const fail = m=>{ bad++; console.log('FAIL', m); };
const used = new Set(), fallback = [], generic = {}, GEN = ['open','close','invalid','confirm','success','press'];
const lines = html.split('\n');
lines.forEach((l, i)=>{
  for(const m of l.matchAll(/codisSfx\(\s*([^;]*?)\)\s*[;}]/g)){
    const a = m[1], head = a.split('{')[0], names = [...head.matchAll(/'([a-z][a-z0-9.]*)'/g)].map(x=>x[1]).filter(n=>/^[a-z]/.test(n) && !/^(ctx|kind|cue|key|check|x)$/.test(n));
    const ctx = (a.match(/ctx:\s*'([a-z]+)'/) || [])[1], ctxVar = /ctx:\s*page/.test(a);
    names.forEach(n=>{
      if(n === ctx) return;
      if(!defs.has(n) && !defs.has(n + '@' + ctx)) { if(!/^(start|climax|settle|stinger|enter)$/.test(n)) fail('line ' + (i + 1) + ': unknown sound "' + n + '"'); return; }
      used.add(n); if(ctx){ used.add(n + '@' + ctx); if(!defs.has(n + '@' + ctx)){ if(GEN.includes(n)) fail('line ' + (i + 1) + ': context identity missing ' + n + '@' + ctx); else fallback.push(n + '@' + ctx); } }
      if(GEN.includes(n) && !ctx && !ctxVar) generic[n] = (generic[n] || 0) + 1;
    });
  }
});
['xp.start','xp.tick','xp.settle','xp.chime','xp.milestone','card.cue','punish.cue','task.half','task.none','task.undo','toggle.on','toggle.off','nav','expand','collapse'].forEach(k=>used.add(k));
const unused = [...defs].filter(k=>!used.has(k) && !/^nav$/.test(k));
console.log('identities defined:', defs.size, '· generic calls without context:', JSON.stringify(generic));
if(fallback.length) console.log('intentional fallback to the family identity:', [...new Set(fallback)].join(', '));
if(unused.length) console.log('defined but not referenced literally (preview/dynamic or spare):', unused.join(', '));
const genTotal = Object.values(generic).reduce((a, b)=>a + b, 0);
if(genTotal > 12) fail('too many generic sound calls left without context: ' + genTotal);
console.log(bad ? '\nFAILED ' + bad : 'OK — every sound call resolves to a defined identity');
process.exit(bad ? 1 : 0);
