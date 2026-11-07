/* CODIS-ATMOS-V2 static guard — every motif in tools/atmos_engine.js renders, and every sticker recipe names only existing motifs.
   A motif that throws is swallowed by CodisAtmos.get ⇒ the whole card silently loses its decoration, so this must fail loudly.
   Run: node tests/atmos_motifs_check.js */
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const ROOT = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(ROOT, 'tools/atmos_engine.js'), 'utf8');
Object.assign(global, { CODIS_CARD_SLOTS:{}, CODIS_WEEKLY_SLOTS:{}, CODIS_MONTHLY_SLOTS:{}, CODIS_SPECIAL_CARD_SLOTS:{}, CodisStickers:{ get:()=>null }, escapeHtml:s=>s, CODIS_STK_BASE:'' });
const A = new Function(src + ';return CodisAtmos;')();
const c = { p:'#c98a44', s:'#8a5a3a', a:'#e0a050', hi:'#fff6dc', sh:'#3a2516', g:'#ffd98a', k:'#24160c', n:h=>h };
const bad = [];
for(const k of Object.keys(A._M)){ try{ const s = A._M[k](c, ()=>.5); if(!s || /undefined|NaN/.test(s)) bad.push(k + ': empty/NaN'); }catch(e){ bad.push(k + ': ' + e.message); } }
const app = fs.readFileSync(path.join(ROOT, 'app/CODIS_FINAL.html'), 'utf8');
const m = app.match(/\/\* CODIS-STICKER-ATMOS-DATA \*\/const CODIS_STICKER_ATMOS=(\{.*?\});/s);
if(!m) bad.push('CODIS_STICKER_ATMOS data block missing');
else { const data = JSON.parse(m[1]); Object.keys(data).forEach(id=>(data[id][0] || []).forEach(n=>{ if(!A._M[n]) bad.push(id + ': unknown motif ' + n); })); }
console.log(bad.length ? 'FAIL\n  ' + bad.join('\n  ') : 'OK — ' + Object.keys(A._M).length + ' motifs render; every recipe resolves');
process.exit(bad.length ? 1 : 0);
