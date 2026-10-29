#!/usr/bin/env python3
"""CODIS-BULK-V2 (بعد patch_v8.py): فتح ×10 بتسلسل حقيقي مرتبط بقيمة الجائزة.
 • جدول زمني اشتقاقي: كل صندوق يُفتح بدوره بترتيب القيمة التصاعدي (الأفضل أخيراً)؛ مدة كل صندوق وتوقّفه قبل الكشف تكبر مع مستوى القيمة (CodisRevealLevels) — لا مهلة ثابتة.
 • شدّة الحركة تتبع المستوى: اهتزاز أطول/مزدوج، إضاءة تسليط (bkSpot) للمستوى 5+، انفجار أكبر للـ6+، نغمة واهتزاز جهاز للجوائز العالية.
 • العرض فقط: لا شراء ولا سحب ولا منح هنا (كلها داخل CodisBoxes.buyOpenMany قبل ظهور النافذة)؛ التخطّي/الإغلاق لا يمسّ البيانات؛ كل المؤقّتات تُمسح عند الإغلاق/إعادة الفتح (token).
 • قراءة النتائج: بطاقات الشبكة 5×2 صغيرة، فالنقر عليها بعد الانتهاء يفتح بطاقة مكبّرة قابلة للقلب (ظهر مقروء بقياس 300px) بدل قلب مجهري داخل الخلية."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-BULK-V2' in s: sys.exit('already patched (CODIS-BULK-V2)')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1: sys.exit('anchor "%s" matched %d times' % (label, n))
    s = s.replace(old, new)

rep("function econBulkTotalMs(res){ return ECON_BULK_LEAD + res.items.length * ECON_BULK_STEP + ECON_BULK_TAIL; }",
"""/* CODIS-BULK-V2 — الجدول الزمني: at[i] = لحظة فتح الصندوق i (ms)، dur[i] = مدة بقائه قبل التالي. المستويات العالية تتوقف قبل الكشف (ترقّب) وتأخذ وقتاً أطول */
let econBulkSch = null;
function econBulkSchedule(res){
  const ord = econBulkOrder(res), at = {}, dur = {}; let t = ECON_BULK_LEAD;
  ord.forEach(o=>{
    const lv = o.lv, hold = lv <= 2 ? 280 : lv <= 4 ? 400 : lv <= 5 ? 540 : lv <= 7 ? 860 : 1250, pre = lv >= 8 ? 420 : lv >= 6 ? 240 : 0;
    t += pre; at[o.i] = t; dur[o.i] = hold; t += hold;
  });
  return { at:at, dur:dur, total:t + ECON_BULK_TAIL };
}
function econBulkTotalMs(res){ return econBulkSchedule(res).total; }""", 'total ms')

rep("RL = CodisRevealLevels.info(lv), d = ECON_BULK_LEAD + ord * ECON_BULK_STEP;", "RL = CodisRevealLevels.info(lv), d = econBulkSch ? econBulkSch.at[i] : ECON_BULK_LEAD + ord * ECON_BULK_STEP, hold = econBulkSch ? econBulkSch.dur[i] : 300;", 'cell d')
rep("';--d:' + d + 'ms;", "';--d:' + d + 'ms;--hold:' + hold + 'ms;", 'cell style')

rep("  const sheet = m.querySelector('.bk-modal'), run = s.phase !== 'done', ord = {}; econBulkOrder(s.res)", "  econBulkSch = econBulkSchedule(s.res);\n  const sheet = m.querySelector('.bk-modal'), run = s.phase !== 'done', ord = {}; econBulkOrder(s.res)", 'paint sch')
rep("  codisFitRewardCard(body); codisWatchRewardCards(body);\n}\nfunction econBulkWorld(m, tier){",
"""  codisFitRewardCard(body); codisWatchRewardCards(body);
  /* النقر على خلية: لا قلب مجهري داخلها — أثناء الفتح لا يحدث شيء، وبعد الانتهاء تُفتح بطاقة مكبّرة */
  const grid = body.querySelector('.bk-grid');
  if(grid) grid.addEventListener('click', e=>{
    const c = e.target.closest ? e.target.closest('.bk-cell') : null; if(!c) return;
    e.stopPropagation(); e.preventDefault();
    if(econBulkState && econBulkState.phase === 'done') econBulkZoom(Array.prototype.indexOf.call(grid.children, c), c);
  }, true);
}
var econBulkZoomEl = null;
function econBulkZoomClose(){
  const z = econBulkZoomEl; if(!z) return; econBulkZoomEl = null;
  document.removeEventListener('keydown', z._key, true); z.classList.remove('is-open');
  window.setTimeout(()=>{ z.remove(); }, 200);
  try{ if(z._opener && z._opener.isConnected) z._opener.focus({ preventScroll:true }); }catch(e){}
}
function econBulkZoom(i, opener){
  const s = econBulkState, m = econBulkModal(); if(!s || !m || s.phase !== 'done') return; econBulkZoomClose();
  const r = s.res.items[i]; if(!r) return;
  const inf = econBulkInfo(r), it = r.item, rar = r.rarity;
  const art = r.pouch ? '<div class="pk-tile is-pouch"><div class="pch-art">' + econPouchSvg(r.pouch.type) + '</div></div>' : econPackTileHtml(it, rar).replace(' role="listitem"', '');
  const back = codisCardBackHtml(inf.name, [['الفئة', rar.name], ['من', r.tier.name], ['البكج رقم', econFmt(i + 1)]], { tone:rar.tone, kind:inf.kind });
  const z = document.createElement('div'); z.className = 'bk-zoom'; z.setAttribute('data-tone', rar.tone);
  z.innerHTML = '<div class="bk-zoom-back"></div><div class="bk-zoom-card" role="dialog" aria-modal="true" aria-label="' + escapeHtml(inf.name) + '">' + codisFlipHtml(art, back, { label:inf.name }) +
    '<p class="bk-zoom-name" dir="auto">' + escapeHtml(inf.name) + '</p><p class="bk-zoom-hint">اضغط البطاقة لقلبها</p><button type="button" class="btn btn-secondary bk-zoom-x">إغلاق</button></div>';
  m.appendChild(z); z._opener = opener || null; econBulkZoomEl = z;
  z._key = ev=>{ if(ev.key === 'Escape'){ ev.stopPropagation(); ev.preventDefault(); econBulkZoomClose(); } };
  document.addEventListener('keydown', z._key, true);
  z.querySelector('.bk-zoom-back').onclick = econBulkZoomClose; z.querySelector('.bk-zoom-x').onclick = econBulkZoomClose;
  try{ codisFitRewardCard(z); codisWatchRewardCards(z); }catch(e){}
  requestAnimationFrame(()=>{ z.classList.add('is-open'); try{ z.querySelector('.bk-zoom-x').focus({ preventScroll:true }); }catch(e){} });
  window.setTimeout(()=>{ z.classList.add('is-open'); }, 60);
}
function econBulkWorld(m, tier){""", 'zoom + click capture')

rep("  const calm = econCalm(), token = ++econBulkToken;\n", "  const calm = econCalm(), token = ++econBulkToken; econBulkZoomClose();\n", 'show close zoom')
rep("best:econBulkBest(res) };   /* تقليل الحركة", "best:econBulkBest(res) }; econBulkSch = econBulkSchedule(res);   /* تقليل الحركة", 'show sch')
rep("""    res.items.map((r, i)=>({ i:i, lv:CodisRevealLevels.levelOfResult(r) })).filter(o=>o.lv >= 6).sort((a, b)=>b.lv - a.lv).slice(0, 3).forEach(o=>{
      s.cues.push(window.setTimeout(()=>{ if(econBulkState && econBulkState.token === token && econBulkState.phase === 'opening') codisSfx(o.lv >= 8 ? 'reward.achievement' : 'reward.unlock'); }, ECON_BULK_LEAD + ord[o.i] * ECON_BULK_STEP + 240));
    });""",
"""    res.items.map((r, i)=>({ i:i, lv:CodisRevealLevels.levelOfResult(r) })).filter(o=>o.lv >= 5).sort((a, b)=>b.lv - a.lv).slice(0, 5).forEach(o=>{
      s.cues.push(window.setTimeout(()=>{ if(econBulkState && econBulkState.token === token && econBulkState.phase === 'opening'){ codisSfx(o.lv >= 8 ? 'reward.achievement' : 'reward.unlock'); try{ codisHaptic(o.lv >= 8 ? [14, 50, 30] : o.lv >= 6 ? [12, 40] : [8]); }catch(x){} } }, econBulkSch.at[o.i] + 240));
    });
    /* الصندوق الجاري فتحه يبقى ظاهراً (التمرير فقط إن خرج من الشاشة) */
    res.items.forEach((r, i)=>{ s.cues.push(window.setTimeout(()=>{ if(!(econBulkState && econBulkState.token === token && econBulkState.phase === 'opening')) return; const c = m.querySelectorAll('.bk-cell')[i]; if(c){ try{ c.scrollIntoView({ block:'nearest', behavior:'smooth' }); }catch(x){} } }, Math.max(0, econBulkSch.at[i] - 380))); });""", 'cues')
rep("function econBulkClose(silent){\n  const m = econBulkModal(); if(!m) return;", "function econBulkClose(silent){\n  const m = econBulkModal(); if(!m) return; econBulkZoomClose();", 'close zoom')
rep("  if(open('codis-confirm-modal')) return L('codis-confirm-modal', ()=>resolveCodisConfirm(false));", "  if(econBulkZoomEl) return { act:econBulkZoomClose, el:econBulkZoomEl };\n  if(open('codis-confirm-modal')) return L('codis-confirm-modal', ()=>resolveCodisConfirm(false));", 'back layer zoom')

css = r"""
/* CODIS-BULK-V2 — شدّة الحركة حسب مستوى القيمة + تسليط + بطاقة مكبّرة */
.bk-modal.is-run .bk-chest .cb-rig{ animation:bkShake var(--sh, .3s) linear; animation-delay:calc(var(--d) - var(--sh, .3s)); }
.bk-cell[data-lv="1"], .bk-cell[data-lv="2"]{ --sh:.22s; } .bk-cell[data-lv="3"], .bk-cell[data-lv="4"]{ --sh:.34s; } .bk-cell[data-lv="5"]{ --sh:.5s; }
.bk-cell[data-lv="6"], .bk-cell[data-lv="7"]{ --sh:.72s; } .bk-cell[data-lv="8"], .bk-cell[data-lv="9"]{ --sh:1s; }
.bk-modal.is-run .bk-cell[data-lv="8"] .cb-rig, .bk-modal.is-run .bk-cell[data-lv="9"] .cb-rig{ animation-iteration-count:2; }
.bk-modal.is-run .bk-cell:is([data-lv="5"], [data-lv="6"], [data-lv="7"], [data-lv="8"], [data-lv="9"]){ z-index:4; animation:bkSpot var(--hold, 540ms) ease-in-out calc(var(--d) - 220ms) both; }
.bk-modal.is-run .bk-cell[data-hot]:is([data-lv="6"], [data-lv="7"], [data-lv="8"], [data-lv="9"]){ animation:bkSpot var(--hold, 860ms) ease-in-out calc(var(--d) - 220ms) both, bkHot 1.1s ease-out calc(var(--d) + 240ms) both; }
@keyframes bkSpot{ 0%{ transform:none; } 38%{ transform:scale(1.09); } 100%{ transform:none; } }
.bk-modal.is-done .bk-cell{ cursor:pointer; }
.bk-zoom{ position:fixed; inset:0; z-index:12; display:grid; place-items:center; opacity:0; transition:opacity .18s ease; }
.bk-zoom.is-open{ opacity:1; }
.bk-zoom-back{ position:absolute; inset:0; background:rgb(var(--lo-rgb) / .84); }
.bk-zoom-card{ position:relative; width:min(78vw, 300px); display:grid; gap:12px; justify-items:center; }
.bk-zoom-card .cflip{ width:100%; --card-r:16px; } .bk-zoom-card .cflip .pk-tile{ width:100%; }
.bk-zoom-name{ margin:0; text-align:center; font-size:16px; font-weight:800; overflow-wrap:anywhere; } .bk-zoom-hint{ margin:-6px 0 0; font-size:12px; color:var(--text-3, var(--text-2)); }
.bk-zoom-x{ min-height:44px; min-width:140px; }
@media (prefers-reduced-motion:reduce){ .bk-zoom{ transition:none; } .bk-modal.is-run .bk-cell{ animation:none !important; } }
"""
rep("</style>", css + "</style>", 'css')
s = s.replace('<!-- CODIS-PACKUI -->', '<!-- CODIS-PACKUI -->\n<!-- CODIS-BULK-V2 -->', 1)
if 'CODIS-BULK-V2 -->' not in s: sys.exit('marker missing')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v9 OK')
