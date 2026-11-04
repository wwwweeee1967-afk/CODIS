#!/usr/bin/env python3
"""CODIS-MONTHLY-V2 (بعد patch_v30.py) — 3.18.0 — الكروت الشهرية الخمسة الجديدة (رسم ورقي بإطار مزخرف 4:5) + ستيكرات CODIS-STICKERS-13.
 الأصول: tools/build_monthly_cards.py (يستخرج الكروت من assets/monthly_source/monthly_cards_new.webp ويحقن CODIS_MONTHLY_ART / CODIS_MONTHLY_SLOTS).
 هذا الـpatch يضبط العرض فقط حول الأصول الجديدة — بلا تغيير بالمكافآت/الكوين/المخزون/البيانات ولا بنظام الكروت اليومية والأسبوعية:
  1) الصندوق: الشهري يستعمل الآن بنية «الصورة هي البطاقة» نفسها (rwc-d wkc) كاليومي/الأسبوعي — 4:5 بلا حشوة/حدّ/خلفية محيطة، نفس مقاس المتجر والنتيجة والتفاصيل.
  2) ألوان النص: لوحتا الكرت الجديد ورقيتان فاتحتان ⇒ حبر داكن بلون ندرة كل كرت (كانت لوحات داكنة بحبر فاتح).
  3) ملاءمة الاسم: لوحة الاسم الجديدة أصغر (فص واحد بجانب الميدالية) ⇒ للشهري فقط يبدأ الخط أصغر وينزل لحدّ أدنى أقل (الأسبوعي كما هو).
  4) ستيكر الشهري: موضع/مقاس اليومي نفسه (كان لبطاقة طويلة 0.54) + مناطق الزخرفة الآمنة وحمايتها للتصاميم الجديدة (tools/atmos_engine.js ← يُستبدل بالمحرّك المضمَّن).
  5) نافذة النتيجة: الشهري يأخذ is-dcard (بلا حشوة) كاليومي/الأسبوعي.
  6) CodisCardFX (كشف الشهري): إحداثيات REC و MFIG أُعيد ضبطها على الرسم الجديد (الميدالية، السيف، القمر، الرأس…) بنفس الأزمنة والعمليات؛ حُذف فقط فقاعة الكلام (لا وجود لها بالتصميم الجديد).
 الاستعمال: py -3 tools/patch_v31.py app/CODIS_FINAL.html app/CODIS_FINAL.html ثم py -3 tools/build_monthly_cards.py ثم py -3 tools/build_stickers.py ثم py -3 tools/set_version.py"""
import sys, os, re
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-MONTHLY-V2' in s: sys.exit('already patched (CODIS-MONTHLY-V2)')
if 'const CODIS_STICKER_MAX' not in s: sys.exit('apply patch_v30.py first')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

def rep_re(pat, new, label):
    global s
    m = list(re.finditer(pat, s, re.M))
    if len(m) != 1: sys.exit('regex "%s" matched %d times' % (label, len(m)))
    s = s[:m[0].start()] + new + s[m[0].end():]

# ---------------------------------------------------------------- 1+2. CSS: حبر داكن بلون الندرة (الأصل: حبر فاتح للوحات داكنة) + ألوان النص على الورق
rep(""".mtc.rwc-c { --rwc-ink:#8ff0a9; --rwc-glow:rgb(var(--success-rgb) / .45); }
.mtc.rwc-b { --rwc-ink:#7cc4ff; --rwc-glow:rgba(56,142,255,.5); }
.mtc.rwc-a { --rwc-ink:#c9a2ff; --rwc-glow:rgba(150,84,255,.5); }
.mtc.rwc-s { --rwc-ink:#ffd070; --rwc-glow:rgba(255,184,40,.5); }
.mtc.rwc-ss{ --rwc-ink:#ff9a9a; --rwc-glow:rgba(255,64,64,.55); }""",
""".mtc.rwc-c { --rwc-ink:#1d5a30; --rwc-glow:rgb(var(--success-rgb) / .45); }
.mtc.rwc-b { --rwc-ink:#14478a; --rwc-glow:rgba(56,142,255,.5); }
.mtc.rwc-a { --rwc-ink:#54298f; --rwc-glow:rgba(150,84,255,.5); }
.mtc.rwc-s { --rwc-ink:#7a4f00; --rwc-glow:rgba(255,184,40,.5); }
.mtc.rwc-ss{ --rwc-ink:#8a1818; --rwc-glow:rgba(255,64,64,.55); }
/* CODIS-MONTHLY-V2: لوحتا الكرت الجديد ورقيتان فاتحتان ⇒ الاسم بالحبر الداكن (--rwc-txt) والمعلومات بالحبر الثانوي (--rwc-sub) ورمز الندرة بلون ندرته؛ بلا توهج نص */
.mtc .wkc-name span{ color:var(--rwc-txt); text-shadow:none; }
.mtc .wkc-row{ color:var(--rwc-sub); }
.mtc .wkc-tier b{ color:var(--rwc-ink); text-shadow:none; }
.mtc .wkc-coin{ border-inline-start-color:color-mix(in srgb, var(--rwc-sub) 45%, transparent); }""", 'monthly ink css')

# ---------------------------------------------------------------- 4. موضع ستيكر الشهري = اليومي/الأسبوعي (التصميم الجديد 4:5)
rep(".rwc-stk-m{ left:-4%; top:-1.5%; width:44%; }", ".rwc-stk-m{ left:-2.5%; top:-2%; width:33%; }   /* CODIS-MONTHLY-V2: كان 44% لبطاقة طويلة 0.54 */", 'stk-m')

# ---------------------------------------------------------------- 1. بنية الصندوق = «الصورة هي البطاقة»
rep("""'<div class="rwc mtc rwc-' + tone + '" role="img" """, """'<div class="rwc rwc-d wkc mtc rwc-' + tone + '" role="img" """, 'monthly class')

# ---------------------------------------------------------------- 5. نافذة النتيجة
rep("(rew && (codisUseRewardCard(e) || codisUseWeeklyCard(e)) ? ' is-dcard' : '')", "(rew && (codisUseRewardCard(e) || codisUseWeeklyCard(e) || codisUseMonthlyCard(e)) ? ' is-dcard' : '')", 'is-dcard')

# ---------------------------------------------------------------- 3. ملاءمة الاسم للشهري
rep("""  codisFitEach(root.querySelectorAll('.wkc-name'), box=>{
    const t = box.firstElementChild; if(!t || !box.clientHeight) return;
    let size = 7; t.style.fontSize = size + 'cqw';
    size = codisFitShrink(t, size, 0.25, 4.2, 40, ()=>((t.offsetHeight > box.clientHeight || t.scrollWidth > box.clientWidth)));
  });""", """  codisFitEach(root.querySelectorAll('.wkc-name'), box=>{
    const t = box.firstElementChild; if(!t || !box.clientHeight) return;
    const mt = !!box.closest('.mtc');   /* CODIS-MONTHLY-V2: لوحة الاسم الشهرية أصغر (فص بجانب الميدالية) ⇒ بداية أصغر وحدّ أدنى أقل؛ الأسبوعي كما كان */
    let size = mt ? 5.6 : 7; t.style.fontSize = size + 'cqw';
    size = codisFitShrink(t, size, mt ? 0.2 : 0.25, mt ? 2.2 : 4.2, 40, ()=>((t.offsetHeight > box.clientHeight || t.scrollWidth > box.clientWidth)));
  });""", 'fit name')

# ---------------------------------------------------------------- 6. CodisCardFX: إحداثيات الشهري على الرسم الجديد (نسب % من البطاقة). الأزمنة/العمليات كما هي
rep_re(r"^    'm:C':\{ sig:'Quiet bite.*$", """    'm:C':{ sig:'Quiet bite · لقمة هادئة', a:'40,170,90', b:'160,245,185', wet:.12, ops:[['ring',.10,.42],['fig','body',.05,.64,'breath',1,0],['fig','hand',.08,.50,'grip',1,0],['parts','leaf','top',.20,.40,0,0,1],['fig','head',.22,.30,'nod',1,1],['sweep',.46,100],['fig','head',.52,.20,'look',1,1],['glint',.64,22,55,10],['glint',.70,86,22,11],['glint',.72,50,68,12],['after',.72,.28]] },""", 'rec C')
rep_re(r"^    'm:B':\{ sig:'Blade glint.*$", """    'm:B':{ sig:'Blade glint · لمعة النصل', a:'30,120,230', b:'140,205,255', wet:.16, ops:[['ring',.08,.50],['scan',.16,.30,1],['fig','body',.05,.64,'breath',1.1,0],['fig','hair',.12,.50,'sway',1,0],['charge',.30,.38],['beat',.30,.30,3],['parts','spark','side',.26,.40,0,0,1],['fig','blade',.40,.30,'shiver',1,1],['path',.44,.22,12,55,52,38,14],['sweep',.52,60],['fig','head',.46,.24,'look',1,1],['pulse',.58,50,68,18,2],['glint',.68,76,40,12],['glint',.72,50,68,13],['after',.72,.28]] },""", 'rec B')
rep_re(r"^    'm:A':\{ sig:'Moonlight.*$", """    'm:A':{ sig:'Moonlight · ضوء القمر', a:'130,70,230', b:'205,165,255', wet:.20, ops:[['ring',.08,.50],['dim',.14,.40],['fig','body',.05,.64,'breath',1.15,0],['pulse',.18,80,24,34,3],['charge',.28,.42],['beat',.30,.34,3],['parts','petal','top',.20,.50,0,0,1],['fig','head',.30,.30,'look',1.2,1],['fig','hand',.44,.24,'grip',1,1],['sweep',.46,95],['path',.54,.18,64,66,96,57,13],['pulse',.60,50,68,24,2],['glint',.66,86,54,12],['shock',.72,80,24],['glint',.74,66,24,12],['after',.72,.28]] },""", 'rec A')
rep_re(r"^    'm:S':\{ sig:'Sunrise.*$", """    'm:S':{ sig:'Sunrise · شروق ذهبي', a:'230,150,30', b:'255,225,120', wet:.24, rays:[50,30], ops:[['heat',.10,.55],['ring',.08,.50],['fig','body',.04,.66,'breath',1.25,0],['fig','armL',.12,.40,'rise',1,1],['fig','armR',.14,.40,'rise',1,0],['charge',.20,.50],['beat',.26,.40,4],['dim',.30,.38],['sweep',.34,120],['fig','head',.40,.26,'look',1,1],['fig','chest',.50,.20,'surge',1.1,1],['pulse',.56,50,70,24,2],['parts','ember','bottom',.30,.42,0,0,1],['glint',.68,78,14,12],['glint',.72,50,70,18],['shock',.72,50,70],['parts','star','burst',.72,.10,50,64,.6],['after',.72,.28]] },""", 'rec S')
rep_re(r"^    'm:SS':\{ sig:'Crimson crown.*$", """    'm:SS':{ sig:'Crimson crown · التاج القرمزي', a:'220,30,40', b:'255,120,110', wet:.30, rays:[50,62], ops:[['heat',.04,.60],['ring',.06,.60],['dim',.08,.30],['fig','body',.03,.66,'breath',1.3,0],['fig','hair',.10,.50,'sway',1.4,0],['charge',.14,.56],['beat',.20,.46,5],['parts','ember','bottom',.20,.50,0,0,1],['sweep',.28,70],['fig','head',.30,.26,'look',1.2,1],['sweep',.36,110],['fig','blade',.40,.30,'shiver',1.4,1],['path',.44,.20,22,64,90,34,16],['pulse',.50,50,70,28,3],['fig','arm',.50,.22,'lunge',1.4,1],['dim',.52,.18],['glint',.66,58,48,14],['glint',.70,55,20,16],['glint',.72,50,70,22],['shock',.72,50,70],['parts','star','burst',.72,.14,50,70,.6],['parts','ember','burst',.72,.20,50,46,.5],['after',.72,.28]] }""", 'rec SS')

a = s.index("  const MFIG = {"); b = s.index("  function mkFig(c, name){")
s = s[:a] + """  const MFIG = {   /* CODIS-MONTHLY-V2: مناطق الحركة على الكروت الشهرية الجديدة (نسب % من البطاقة 4:5) */
    C:{ body:{ m:[50, 48, 44, 26], o:[50, 68] }, head:{ m:[48, 25, 22, 16], o:[48, 38], p:'body' }, hand:{ m:[40, 36, 13, 9], o:[42, 41], p:'body' } },
    B:{ body:{ m:[52, 56, 46, 24], o:[52, 72] }, head:{ m:[50, 28, 22, 16], o:[50, 40], p:'body' }, hair:{ m:[50, 12, 24, 10], o:[50, 22] }, blade:{ m:[40, 46, 30, 9], o:[36, 44] } },
    A:{ body:{ m:[48, 52, 46, 26], o:[48, 70] }, head:{ m:[45, 22, 20, 14], o:[46, 34] , p:'body' }, hand:{ m:[86, 56, 12, 10], o:[80, 58], p:'body' } },
    S:{ body:{ m:[50, 50, 46, 24], o:[50, 70] }, head:{ m:[49, 28, 20, 14], o:[49, 38], p:'body' }, armL:{ m:[16, 30, 16, 12], o:[30, 36] }, armR:{ m:[84, 30, 16, 12], o:[70, 36] }, chest:{ m:[50, 52, 24, 13], o:[50, 58], p:'body' } },
    SS:{ body:{ m:[50, 52, 44, 24], o:[50, 68] }, head:{ m:[53, 28, 22, 16], o:[53, 40], p:'body' }, hair:{ m:[53, 12, 20, 10], o:[53, 22] }, blade:{ m:[55, 50, 36, 12], o:[24, 62] }, arm:{ m:[28, 62, 16, 10], o:[34, 64], p:'body' } }
  };
""" + s[b:]

# ---------------------------------------------------------------- 4. المحرّك المضمَّن (CodisAtmos): قوالب m:* الجديدة + موضع الستيكر
old_engine = open(os.path.join(root, 'backups', 'monthly_before_new', 'atmos_engine.js'), encoding='utf-8').read().rstrip() + '\n'
new_engine = open(os.path.join(here, 'atmos_engine.js'), encoding='utf-8').read().rstrip() + '\n'
rep(old_engine, new_engine, 'atmos engine')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('CODIS-MONTHLY-V2 applied ->', dst)
