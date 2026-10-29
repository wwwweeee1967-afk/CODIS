#!/usr/bin/env python3
"""CODIS-CARDS-V2 (بعد patch_v6.py):
 (A) إزالة الحشوة الشفافة: الصور الأصلية بلا هوامش شفافة (قياس alpha فعلي: الحافة صفر لكل بطاقات اليومي/الأسبوعي 4:5؛ بطاقات العطلة/الخاصة 0.1–1.3% فقط) —
     المصدر الحقيقي للفراغ كان الحشوة المركزية (.rwc padding:3.5% + --card-pad:3.5%) + ظل داكن حول العمل. تُصفَّر الحشوة مركزياً ويُكبَّر عمل العطلة/الخاصة 3% ضمن إطار مقصوص.
 (B) ظهر البطاقة: تركيبة SVG مولّدة لكل (ندرة × نوع بطاقة): نقش خلفية حسب الندرة، إطار مزدوج وزخارف زوايا تتصاعد مع الندرة، وميدالية مركزية برمز النوع،
     والمعلومات على لوحة داكنة مقروءة. ليست نسخة من وجه البطاقة."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-CARDS-V2' in s: sys.exit('already patched (CODIS-CARDS-V2)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

a = s.index("function codisCardBackHtml(title, rows, o){")
b = s.index("function codisFlipToggle(el){")
js = r"""/* CODIS-CARDS-V2 — ظهر البطاقة: تركيبة مولّدة من هوية البطاقة (ندرتها + نوعها). kind: reward|weekly|monthly|pass|holiday|pouch|cosmetic|box */
const CBK_CODE = { c:'C', b:'B', a:'A', s:'S', ss:'SS' };
function codisBackOrnament(tone, kind, seed){
  const f = n=>Math.round(n * 10) / 10, P = [];
  let x0 = 2166136261; String(seed || '').split('').forEach(ch=>{ x0 ^= ch.charCodeAt(0); x0 = Math.imul(x0, 16777619) >>> 0; });
  const rnd = ()=>{ x0 = (Math.imul(x0, 1664525) + 1013904223) >>> 0; return x0 / 4294967296; };
  /* 1) نقش الخلفية حسب الندرة: C شرائط مائلة · B موجات · A معيّن · S أشعة · SS أشعة مضاعفة + حلقات */
  const L = [];
  if(tone === 'c'){ for(let x = -125; x <= 100; x += 7) L.push('M' + x + ' 0L' + (x + 125) + ' 125'); }
  else if(tone === 'b'){ for(let y = 10; y < 125; y += 8){ let d = 'M0 ' + y; for(let x = 0; x < 100; x += 10) d += 'q5 -6 10 0'; L.push(d); } }
  else if(tone === 'a'){ for(let k = -125; k <= 225; k += 12){ L.push('M' + k + ' 0L' + (k + 125) + ' 125'); L.push('M' + k + ' 125L' + (k + 125) + ' 0'); } }
  else { const n = tone === 'ss' ? 40 : 24; for(let i = 0; i < n; i++){ const a = i / n * Math.PI * 2; L.push('M50 32L' + f(50 + Math.cos(a) * 150) + ' ' + f(32 + Math.sin(a) * 150)); } }
  P.push('<path class="o-pat" d="' + L.join('') + '"/>');
  if(tone === 'ss'){ [26, 34, 42].forEach(r=>P.push('<circle class="o-pat o-ring" cx="50" cy="32" r="' + r + '"/>')); }
  /* 2) إطار: واحد للعادية، مزدوج من A فما فوق، وزخارف زوايا تتزايد */
  P.push('<rect class="o-fr" x="4" y="4" width="92" height="117" rx="7"/>');
  if(tone === 'a' || tone === 's' || tone === 'ss') P.push('<rect class="o-fr2" x="7.5" y="7.5" width="85" height="110" rx="4.5"/>');
  [[4, 4, 1, 1], [96, 4, -1, 1], [4, 121, 1, -1], [96, 121, -1, -1]].forEach(c=>{
    const x = c[0], y = c[1], sx = c[2], sy = c[3];
    P.push('<path class="o-dia" d="M' + x + ' ' + f(y + sy * 5) + 'L' + f(x + sx * 5) + ' ' + y + 'L' + f(x + sx * 10) + ' ' + f(y + sy * 5) + 'L' + f(x + sx * 5) + ' ' + f(y + sy * 10) + 'Z"/>');
    if(tone === 's' || tone === 'ss') P.push('<path class="o-fr2" d="M' + f(x + sx * 12) + ' ' + y + 'Q' + f(x + sx * 12) + ' ' + f(y + sy * 12) + ' ' + x + ' ' + f(y + sy * 12) + '"/>');
    if(tone === 'ss') P.push('<circle class="o-dia" cx="' + f(x + sx * 15) + '" cy="' + f(y + sy * 15) + '" r="1"/>');
  });
  /* 3) الميدالية المركزية + رمز النوع */
  const cx = 50, cy = 32;
  P.push('<g transform="translate(50 24) scale(.82) translate(-50 -32)"><circle class="o-em" cx="' + cx + '" cy="' + cy + '" r="17"/><circle class="o-em o-thin" cx="' + cx + '" cy="' + cy + '" r="13.5"/>');
  const G = {
    reward:()=>'<path class="o-emf" d="M50 21L61 32 50 43 39 32Z"/><path class="o-em" d="M50 21L61 32 50 43 39 32Z"/><text x="50" y="36.2" text-anchor="middle">' + (CBK_CODE[tone] || 'C') + '</text>',
    weekly:()=>{ let d = ''; for(let i = 0; i < 7; i++){ const a = i / 7 * Math.PI * 2 - Math.PI / 2; d += '<circle class="o-emf" cx="' + f(cx + Math.cos(a) * 9.5) + '" cy="' + f(cy + Math.sin(a) * 9.5) + '" r="1.9"/>'; } return d + '<text x="50" y="36.2" text-anchor="middle">7</text>'; },
    monthly:()=>{ let d = ''; for(let i = 0; i < 30; i++){ const a = i / 30 * Math.PI * 2; d += 'M' + f(cx + Math.cos(a) * 9) + ' ' + f(cy + Math.sin(a) * 9) + 'L' + f(cx + Math.cos(a) * 11.6) + ' ' + f(cy + Math.sin(a) * 11.6); } return '<path class="o-em o-thin" d="' + d + '"/><text x="50" y="36.2" text-anchor="middle">30</text>'; },
    pass:()=>'<path class="o-em" d="M40 25H60a2 2 0 0 1 2 2V29a3 3 0 0 0 0 6V37a2 2 0 0 1-2 2H40a2 2 0 0 1-2-2V35a3 3 0 0 0 0-6V27a2 2 0 0 1 2-2Z"/><path class="o-em o-thin" d="M50 26V38" stroke-dasharray="1.6 1.6"/>',
    holiday:()=>'<path class="o-emf" d="M55 22.5A10.5 10.5 0 1 0 55 41.5 8.4 8.4 0 0 1 55 22.5Z"/><path class="o-em" d="M55 22.5A10.5 10.5 0 1 0 55 41.5 8.4 8.4 0 0 1 55 22.5Z"/><circle class="o-dia" cx="57.5" cy="28" r="1.3"/>',
    pouch:()=>'<circle class="o-emf" cx="50" cy="32" r="9"/><circle class="o-em" cx="50" cy="32" r="9"/><circle class="o-em o-thin" cx="50" cy="32" r="5.6"/><path class="o-em o-thin" d="M50 28V36"/>',
    cosmetic:()=>'<path class="o-emf" d="M50 20Q51.6 30.4 62 32 51.6 33.6 50 44 48.4 33.6 38 32 48.4 30.4 50 20Z"/><path class="o-em" d="M50 20Q51.6 30.4 62 32 51.6 33.6 50 44 48.4 33.6 38 32 48.4 30.4 50 20Z"/>',
    box:()=>'<path class="o-em" d="M50 22L60.5 27.5V38.5L50 44 39.5 38.5V27.5Z"/><path class="o-em o-thin" d="M39.5 27.5L50 33 60.5 27.5M50 33V44"/>'
  };
  P.push('<g class="o-glyph">' + (G[kind] || G.reward)() + '</g></g>');
  /* 4) تفرّد خفيف لكل بطاقة: نقاط نجمية بمواضع ثابتة من اسمها (seed) */
  for(let i = 0; i < (tone === 'ss' ? 7 : tone === 's' ? 5 : 3); i++) P.push('<circle class="o-dia" cx="' + f(14 + rnd() * 72) + '" cy="' + f(50 + rnd() * 6) + '" r="' + f(0.5 + rnd() * 0.7) + '"/>');
  return '<svg class="cbk-orn" viewBox="0 0 100 125" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' + P.join('') + '</svg>';
}
function codisCardBackHtml(title, rows, o){
  o = o || {};
  const tone = econTones().indexOf(o.tone) !== -1 ? o.tone : 'c', kind = o.kind || 'reward';
  return '<div class="cbk rwc-' + tone + '" data-tone="' + tone + '" data-kind="' + escapeHtml(kind) + '">' + codisBackOrnament(tone, kind, title) +
    '<div class="cbk-in"><b class="cbk-t" dir="auto">' + escapeHtml(title) + '</b>' +
    '<dl class="cbk-rows">' + rows.filter(r=>r && r[1] !== '' && r[1] !== null && r[1] !== undefined).map(r=>'<div><dt>' + escapeHtml(r[0]) + '</dt><dd' + (r[2] ? ' ' + r[2] : '') + '>' + (r[3] ? r[1] : escapeHtml(String(r[1]))) + '</dd></div>').join('') + '</dl>' +
    (o.note ? '<p class="cbk-note" dir="auto">' + escapeHtml(o.note) + '</p>' : '') + '</div></div>';
}
"""
s = s[:a] + js + s[b:]

# تمرير نوع البطاقة من كل مواضع الاستدعاء
rep("['السعر', econCoin(price), '', true]], { tone:rar.tone });", "['السعر', econCoin(price), '', true]], { tone:rar.tone, kind:wk ? 'weekly' : mo ? 'monthly' : 'reward' });", 'store back kind')
rep("{ tone:it.rarityTone });", "{ tone:it.rarityTone, kind:(it.scope === 'weekly' ? 'weekly' : it.scope === 'monthly' ? 'monthly' : 'reward') });", 'inventory back kind')
rep("{ tone:sev === 'HIGH' ? 's' : sev === 'LOW' ? 'b' : 'a', note:'بطاقة حصرية · استعمال واحد' });", "{ tone:sev === 'HIGH' ? 's' : sev === 'LOW' ? 'b' : 'a', kind:'pass', note:'بطاقة حصرية · استعمال واحد' });", 'pass back kind')
rep("{ tone:d.kind === 'extra' ? 's' : 'b', note:d.desc });", "{ tone:d.kind === 'extra' ? 's' : 'b', kind:'holiday', note:d.desc });", 'holiday back kind')
rep("codisCardBackHtml(inf.name, [['الفئة', rar.name], ['من', r.tier.name]], { tone:rar.tone })", "codisCardBackHtml(inf.name, [['الفئة', rar.name], ['من', r.tier.name]], { tone:rar.tone, kind:inf.kind === 'reward' ? 'reward' : inf.kind })", 'bulk back kind')

css = r"""
/* CODIS-CARDS-V2 (A) — لا حشوة حول العمل الفني: الإطار 4:5 يملؤه الرسم (الحدّ 1px هو الإطار الفعلي) */
:root{ --card-pad:0%; }
.rwc{ padding:0; }
.scx-hc-in{ overflow:hidden; border-radius:inherit; }
.scx-hc-in .scx-art, .scx-hc-in img{ transform:scale(1.03); transform-origin:50% 50%; }
/* CODIS-CARDS-V2 (B) — ظهر البطاقة */
.cbk{ padding:0; justify-content:flex-end; gap:0; }
.cbk::after{ display:none; }
.cbk-orn{ position:absolute; inset:0; width:100%; height:100%; color:rgb(var(--k)); pointer-events:none; }
.cbk-orn .o-pat{ fill:none; stroke:currentColor; stroke-width:.28; opacity:.12; }
.cbk-orn .o-ring{ opacity:.2; stroke-width:.4; }
.cbk-orn .o-fr{ fill:none; stroke:currentColor; stroke-width:.6; opacity:.8; }
.cbk-orn .o-fr2{ fill:none; stroke:currentColor; stroke-width:.35; opacity:.4; }
.cbk-orn .o-dia{ fill:currentColor; opacity:.85; }
.cbk-orn .o-em{ fill:none; stroke:currentColor; stroke-width:.9; stroke-linecap:round; stroke-linejoin:round; }
.cbk-orn .o-thin{ stroke-width:.45; opacity:.7; }
.cbk-orn .o-emf{ fill:currentColor; opacity:.22; }
.cbk-orn text{ fill:currentColor; font:900 10px "Avenir Next", "Segoe UI", Arial, system-ui, sans-serif; letter-spacing:.02em; }
.cbk[data-tone="ss"] .o-fr{ stroke-width:.95; opacity:1; } .cbk[data-tone="s"] .o-fr{ stroke-width:.8; }
.cbk[data-tone="ss"], .cbk[data-tone="s"]{ box-shadow:inset 0 0 0 1px rgba(var(--k),.6), inset 0 0 22px rgba(var(--k),.16); }
.cbk-in{ position:relative; z-index:1; margin:0 7% 8%; padding:3.4cqw 4.4cqw 3.6cqw; display:flex; flex-direction:column; gap:1.4cqw; border-radius:3.2cqw; background:rgba(7,9,14,.78); border:1px solid rgba(var(--k),.32); max-height:60%; overflow:hidden; }
.cbk-in .cbk-t{ font-size:clamp(9px, 9.2cqw, 15px); -webkit-line-clamp:2; }
.cbk-in .cbk-rows dt{ font-size:clamp(7.5px, 6.6cqw, 11px); } .cbk-in .cbk-rows dd{ font-size:clamp(8px, 7.2cqw, 12px); }
.cbk-in .cbk-note{ font-size:clamp(7px, 6cqw, 10.5px); -webkit-line-clamp:2; margin:0; }
.cbk-in .cbk-t{ text-align:center; }
.cbk-in .cbk-rows{ margin:0; padding:2.6cqw 0 0; gap:2.2cqw; }
@media (prefers-reduced-motion:no-preference){ .cbk[data-tone="ss"]::before{ content:''; position:absolute; inset:0; z-index:2; pointer-events:none; background:linear-gradient(115deg, transparent 38%, rgba(255,236,170,.16) 50%, transparent 62%); transform:translateX(-120%); animation:cbkSheen 6s ease-in-out infinite; } }
@keyframes cbkSheen{ 0%,55%{ transform:translateX(-120%); } 85%,100%{ transform:translateX(120%); } }
"""
rep("</style>", css + "</style>", 'css')
s = s.replace('<!-- CODIS-BOXES-V4 -->', '<!-- CODIS-BOXES-V4 -->\n<!-- CODIS-CARDS-V2 -->', 1)
if 'CODIS-CARDS-V2 -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v7 OK')
