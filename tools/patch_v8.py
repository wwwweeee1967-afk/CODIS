#!/usr/bin/env python3
"""CODIS-PACKUI (بعد patch_v6.py): إعادة تصميم معاينة البكج (econPackPaint).
 هرمية: ترويسة (صورة+اسم+سعر+ملخص) ← شريط توزيع الاحتمالات + مفتاح قابل للنقر ← أقسام الفئات (الأغلى أولاً، قابلة للطي؛ أول قسمين مفتوحان) بصفوف أفقية للكروت مع احتمال كل كرت.
 الأرقام كلها من CodisBoxes.effective() نفسها (مصدر السحب)."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-PACKUI' in s: sys.exit('already patched (CODIS-PACKUI)')

a = s.index("  const hero = '<div class=\"pk-hero\">")
b = s.index("  body.innerHTML = hero + list + close;")
new = r"""  /* CODIS-PACKUI — الأرقام من CodisBoxes.effective(t) نفسها التي يسحب بها roll() */
  const TONE_RGB = { c:'154,160,170', b:'74,158,184', a:'62,118,228', s:'208,142,52', ss:'255,208,110' }, rgb = tn=>TONE_RGB[tn] || TONE_RGB.c;
  const pctTxt = x=>(x >= 10 ? x.toFixed(1) : x >= 1 ? x.toFixed(1) : x.toFixed(2)) + '%';   /* x بالنسبة المئوية */
  const rev = groups.slice().reverse(), topPrize = groups.length ? Math.max.apply(null, groups.map(g=>g.o.max)) : 0;
  const gem = '<span class="pk-gems" aria-hidden="true">' + [1,2,3,4,5].map(i=>'<i class="' + (i <= t.index ? 'on' : '') + '"></i>').join('') + '</span>';
  const hero = '<div class="pk-hero2"><div class="pk-hero2-art">' + econBoxArt(t.index) + '</div><div class="pk-hero2-txt"><h3 id="econ-pack-title">' + escapeHtml(t.name) + '</h3>' + gem +
    '<div class="pk-hero2-price">' + econCoin(t.price) + '</div></div></div>' +
    (total ? '<ul class="pk-facts"><li><b>' + econFmt(total) + '</b><span>كرت ممكن</span></li><li><b>' + econFmt(groups.length) + '</b><span>فئات</span></li><li><b>' + econFmt(topPrize) + '</b><span>أعلى قيمة</span></li></ul>' : '');
  const overview = groups.length ? '<section class="pk-ov" aria-label="احتمالات الفئات"><h4 class="pk-h">احتمال كل فئة</h4>' +
    '<div class="pk-seg" role="img" aria-label="' + escapeHtml(groups.map(g=>g.o.name + ' ' + econPm(g.o.pm)).join('، ')) + '">' + groups.map(g=>'<i style="flex:' + g.o.pm + ';--k:' + rgb(g.o.tone) + '"></i>').join('') + '</div>' +
    '<ul class="pk-leg">' + rev.map(g=>'<li><button type="button" class="pk-leg-b" style="--k:' + rgb(g.o.tone) + '" onclick="econPackJump(\'' + escapeHtml(g.o.id) + '\')"><i class="pk-lg-dot" aria-hidden="true"></i><span class="pk-ln">' + escapeHtml(g.o.name) + '</span>' +
      '<span class="pk-lr">' + econFmt(g.o.min) + (g.o.max !== g.o.min ? '–' + econFmt(g.o.max) : '') + '</span><b class="pk-lp" dir="ltr">' + econPm(g.o.pm) + '</b></button></li>').join('') + '</ul></section>' : '';
  const list = groups.length ? '<div class="pk-groups2">' + rev.map((g, gi)=>{
    const each = g.o.pm / 10 / g.items.length;
    return '<details class="pk-grp" id="pk-g-' + escapeHtml(g.o.id) + '" style="--k:' + rgb(g.o.tone) + '"' + (gi < 2 ? ' open' : '') + '><summary class="pk-gs"><span class="pk-gs-dot" aria-hidden="true"></span><span class="pk-gs-t"><b>' + escapeHtml(g.o.name) + '</b><small>' + econFmt(g.items.length) + ' كرت · لكل كرت ' + pctTxt(each) + '</small></span><b class="pk-gs-p" dir="ltr">' + econPm(g.o.pm) + '</b><span class="pk-gs-c" aria-hidden="true"></span></summary>' +
      '<div class="pk-row" role="list">' + g.items.map(it=>'<div class="pk-cell">' + econPackTileHtml(it, econRarityById(it.rarity)) + '<span class="pk-cap" dir="ltr">' + pctTxt(each) + '</span></div>').join('') + '</div></details>';
  }).join('') + '</div>' : '<div class="eco-empty pk-empty">ماكو كروت مؤهّلة حالياً — أضف مكافآت مفعّلة من الإعدادات ← المكافآت</div>';
"""
s = s[:a] + new + s[b:]
s = s.replace("  body.innerHTML = hero + list + close;", "  body.innerHTML = hero + overview + list + close;", 1)
s = s.replace("function econPackOpen(tierId, opener){", "function econPackJump(id){ const d = document.getElementById('pk-g-' + id); if(!d) return; d.open = true; try{ d.scrollIntoView({ block:'start', behavior:(matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth') }); }catch(e){} }\nfunction econPackOpen(tierId, opener){", 1)

css = r"""
/* CODIS-PACKUI — معاينة البكج: ترويسة · شريط توزيع · أقسام قابلة للطي بصفوف أفقية */
.pk-hero2{ display:flex; align-items:center; gap:14px; padding:6px 4px 2px; }
.pk-hero2-art{ flex:none; width:92px; } .pk-hero2-art img, .pk-hero2-art svg{ display:block; width:100%; height:auto; }
.pk-hero2-txt{ min-width:0; display:grid; gap:6px; } .pk-hero2-txt h3{ margin:0; font-size:21px; line-height:1.25; }
.pk-gems{ display:flex; gap:4px; } .pk-gems i{ width:8px; height:8px; border-radius:2px; transform:rotate(45deg); background:rgb(var(--hi-rgb) / .16); } .pk-gems i.on{ background:var(--gold, #e8bd5a); }
.pk-hero2-price{ font-size:16px; font-weight:800; }
.pk-facts{ display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; list-style:none; margin:14px 0 0; padding:0; }
.pk-facts li{ display:grid; justify-items:center; gap:2px; padding:10px 6px; border-radius:14px; background:rgb(var(--hi-rgb) / .05); border:1px solid rgb(var(--hi-rgb) / .08); }
.pk-facts b{ font-size:18px; font-variant-numeric:tabular-nums; } .pk-facts span{ font-size:11.5px; color:var(--text-3, var(--text-2)); }
.pk-ov{ margin-top:18px; }
.pk-h{ margin:0 0 10px; font-size:13px; font-weight:700; color:var(--text-2); letter-spacing:0; }
.pk-seg{ display:flex; height:12px; border-radius:999px; overflow:hidden; gap:2px; background:rgb(var(--hi-rgb) / .06); direction:ltr; }
.pk-seg i{ min-width:3px; background:rgb(var(--k)); opacity:.92; }
.pk-leg{ list-style:none; margin:10px 0 0; padding:0; display:grid; gap:2px; }
.pk-leg-b{ display:grid; grid-template-columns:auto 1fr auto auto; align-items:center; gap:10px; width:100%; min-height:44px; padding:0 8px; border:0; border-radius:10px; background:none; color:inherit; font:inherit; text-align:start; cursor:pointer; }
.pk-leg-b:focus-visible{ outline:2px solid rgb(var(--k)); outline-offset:1px; } @media (hover:hover){ .pk-leg-b:hover{ background:rgb(var(--k) / .08); } }
.pk-lg-dot{ width:10px; height:10px; border-radius:50%; background:rgb(var(--k)); }
.pk-ln{ font-weight:700; font-size:14px; } .pk-lr{ font-size:12px; color:var(--text-3, var(--text-2)); font-variant-numeric:tabular-nums; direction:ltr; }
.pk-lp{ min-width:54px; text-align:end; font-size:15px; font-variant-numeric:tabular-nums; color:color-mix(in srgb, rgb(var(--k)) 55%, #fff); }
.pk-groups2{ display:grid; gap:10px; margin-top:18px; }
.pk-grp{ border-radius:16px; border:1px solid rgb(var(--k) / .28); background:linear-gradient(180deg, rgb(var(--k) / .07), transparent 70%); }
.pk-gs{ display:grid; grid-template-columns:auto 1fr auto auto; align-items:center; gap:10px; min-height:56px; padding:8px 12px; cursor:pointer; list-style:none; }
.pk-gs::-webkit-details-marker{ display:none; } .pk-gs:focus-visible{ outline:2px solid rgb(var(--k)); outline-offset:-2px; border-radius:16px; }
.pk-gs-dot{ width:10px; height:10px; border-radius:50%; background:rgb(var(--k)); }
.pk-gs-t{ display:grid; gap:1px; min-width:0; } .pk-gs-t b{ font-size:15px; } .pk-gs-t small{ font-size:11.5px; color:var(--text-3, var(--text-2)); }
.pk-gs-p{ font-size:18px; font-variant-numeric:tabular-nums; color:color-mix(in srgb, rgb(var(--k)) 55%, #fff); }
.pk-gs-c{ width:9px; height:9px; border-inline-end:2px solid var(--text-3, #8a93a0); border-bottom:2px solid var(--text-3, #8a93a0); transform:rotate(45deg); transition:transform .2s ease; margin-inline:4px; }
.pk-grp[open] .pk-gs-c{ transform:rotate(-135deg); }
.pk-row{ display:flex; gap:10px; overflow-x:auto; padding:2px 12px 14px; scroll-snap-type:x proximity; -webkit-overflow-scrolling:touch; overscroll-behavior-x:contain; scrollbar-width:none; }
.pk-row::-webkit-scrollbar{ display:none; }
.pk-cell{ flex:none; width:96px; display:grid; gap:6px; justify-items:center; scroll-snap-align:start; }
.pk-cell .pk-tile{ width:100%; }
.pk-cap{ font-size:11.5px; font-weight:700; color:var(--text-2); font-variant-numeric:tabular-nums; }
@media (prefers-reduced-motion:reduce){ .pk-gs-c{ transition:none; } }
"""
s = s.replace("</style>", css + "</style>", 1)
s = s.replace('<!-- CODIS-BOXES-V4 -->', '<!-- CODIS-BOXES-V4 -->\n<!-- CODIS-PACKUI -->', 1)
if 'CODIS-PACKUI -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v8 OK')
