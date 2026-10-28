"""CODIS-BOXES-V3: the five supplied box artworks, a 3D opening cinema, level-based reveals, a new x10 presentation,
and per-tier minimum reward values (Silver 50 / Crystal 90 / Gold 165 / Legendary 245; Bronze unchanged).
Run AFTER tools/patch_avatar.py:   python tools/patch_boxes.py <in.html> <out.html>
Sources: tools/boxes/art.js · cinema.js · bulk.js · boxes.css · art/bx1..5.webp (originals kept in assets/box_art_original/).
Every anchor must match exactly once; refuses to run twice."""
import sys, os, re, base64
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxes')
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-BOXES-V3' not in t, 'boxes patch already applied'
assert 'CODIS-AVATAR' in t, 'run tools/patch_avatar.py first'
rd = lambda p: open(os.path.join(ROOT, p), 'rb').read().decode('utf-8')

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

def cut(start, end, new, keep_end=True):
    """replace [start, end) — both markers must be unique"""
    global t
    assert t.count(start) == 1, f'start x{t.count(start)}: {start[:70]!r}'
    a = t.index(start); b = t.index(end, a)
    assert t.count(end) >= 1
    t = t[:a] + new + (t[b:] if keep_end else t[b + len(end):])

# ---------- 1) artwork module replaces the old SVG art (materials, logo, econBoxSvg) ----------
art = rd('art.js')
for i in range(1, 6):
    b64 = base64.b64encode(open(os.path.join(ROOT, 'art', f'bx{i}.webp'), 'rb').read()).decode('ascii')
    art = art.replace(f'__B64_{i}__', b64)
assert '__B64_' not in art
cut('/* رسمة الصندوق: تتعقّد مع المستوى', 'function econBoxOddsHtml(rows){', art + '\n')

# ---------- 2) x10: replace the old chest/cell/paint/show/finish/close ----------
rep("const ECON_BULK_MS = 1750;   /* مدة الحركة الجماعية القصيرة؛ تتوافق مع تأخيرات CSS في .bk-modal.is-run */\n", "")
rep("function econBulkModal(){ return document.getElementById('econ-bulk-modal'); }\n", "")
cut('/* رسمة الصندوق للحركة الجماعية', '/* ---- نافذة الفتح: جاهز ← فتح', rd('bulk.js'))

# ---------- 3) cinema: replace the old box-specific animation module (CodisRevealLevels is kept: it drives the reveal) ----------
_a = t.rindex('/* ===', 0, t.index('   CODIS · CodisBoxCinema'))
_end = "  return { play:play, skip:skip, abort:abort, reset:abort, toggleMode:toggleMode, modeLabel:modeLabel, active:()=>!!S };\n})();\n"
assert t.count(_end) == 1
_b = t.index(_end) + len(_end)
t = t[:_a] + rd('cinema.js') + t[_b:]

# ---------- 4) single-box modal: closed-box stage with touch tilt, no mode button, renamed skip bar ----------
rep("""'<div class="bx-stage' + (opening ? ' is-shaking' : '') + '"><span class="bx-burst" aria-hidden="true"></span>' + econBoxSvg(t.index) + '</div>'""", "CodisBoxCinema.idleHtml(t.index)")
rep("""(!opening && !econCalm() ? '<button type="button" class="bxc-mode" onclick="CodisBoxCinema.toggleMode(this)">' + CodisBoxCinema.modeLabel() + '</button>' : '');""", "'';\n  CodisBoxCinema.bindIdle(body);")
rep("""<div class="bxc-skipbar"><button type="button" class="btn btn-secondary bxc-skip" onclick="CodisBoxCinema.skip()">تخطّي</button></div>'; const sk = body.querySelector('.bxc-skip');""",
    """<div class="cb-skipbar"><button type="button" class="btn btn-secondary cb-skip" onclick="CodisBoxCinema.skip()">تخطّي</button></div>'; const sk = body.querySelector('.cb-skip');""")

# ---------- 5) economy: minimum reward value per tier (inclusive), inside the one eligibility pipeline ----------
rep("  const VALUE_SPAN = 50, MAX_PRIZE_X = 12,",
    "  /* CODIS-BOXES-V3 — الحد الأدنى لقيمة الجائزة لكل مستوى (شامل: القيمة >= الحد). القيمة = valueOf(x): نفس الحقل الذي يصنّف به المحرك الجوائز أصلاً (قيمة الاستبدال بالكوين للمكافأة، وسعر بطاقة التجاوز/العطلة/الكيس/المظهر).\n"
    "     البرونزي بلا حد (سلوكه كما كان تماماً). يُطبَّق قبل تجميع الفئات داخل classes() فتتبعه كل النتائج تلقائياً: effective() ← الاحتمالات المعروضة والمسحوبة (roll) ← التوفّر (فارغ = غير متاح بسلوكه المعتاد) ← الإحصاءات. لا يغيّر أسعار الصناديق. */\n"
    "  const MIN_VALUE = Object.freeze({ bx1:0, bx2:50, bx3:90, bx4:165, bx5:245 });\n"
    "  function minValue(id){ const v = Number(MIN_VALUE[id]); return v > 0 ? v : 0; }\n"
    "  const VALUE_SPAN = 50, MAX_PRIZE_X = 12,")
rep("  function classes(){\n", "  function classes(minV){\n")
rep(".filter(o=>o.v > 0).sort((a,b)=>a.v - b.v || a.x.id.localeCompare(b.x.id))", ".filter(o=>o.v > 0 && o.v >= (minV || 0)).sort((a,b)=>a.v - b.v || a.x.id.localeCompare(b.x.id))")
rep("cs = classes().filter(c=>c.max <= MAX_PRIZE_X * t.basePrice || t.basePrice >= top)", "cs = classes(minValue(t.id)).filter(c=>c.max <= MAX_PRIZE_X * t.basePrice || t.basePrice >= top)")
rep("return { tiers, tier, pool, classes, effective, stats, valueOf, owned, get, roll, buy, open, buyOpenMany, BULK };", "return { tiers, tier, pool, classes, effective, stats, valueOf, minValue, owned, get, roll, buy, open, buyOpenMany, BULK };")
# pack details: say the real rule (not a fabricated number)
rep("econCoin(t.price) + '</p></div></div>';\n  const list = groups.length",
    "econCoin(t.price) + (CodisBoxes.minValue(t.id) ? '<span class=\"pk-dot\" aria-hidden=\"true\"></span><span>قيمة كل كرت ' + econFmt(CodisBoxes.minValue(t.id)) + ' كوين فأكثر</span>' : '') + '</p></div></div>';\n  const list = groups.length")

# ---------- 6) old SVG art callers -> new art ----------
t = t.replace('econBoxSvg', 'econBoxArt')
t = t.replace('econBulkChestSvg(', 'econBoxArt(')   # econBuyHeroHtml's stacked ghosts (the old definition was removed with the bulk block)

# ---------- 7) CSS ----------
# 7a) old single-line rules that belonged to the replaced art / bulk chest animation (dropped BEFORE the new css is inserted)
DROP = ('.bx-svg{ width:92px; height:86px;', '.bx-lid{', '.bk-chest{', '.bk-chest .bx-svg', '.bk-burst{', '.bk-modal.is-run .bk-chest', '.bk-modal.is-run .bk-card, .bk-modal.is-run .bk-name', '.bk-modal.is-run .bk-burst',
        '@keyframes bkChest', '@keyframes bkPop', '@keyframes bkBurst')
_lines = t.split('\n'); _nd = 0; _res = []
for _l in _lines:
    if _l.startswith(DROP):
        _nd += 1; continue
    _res.append(_l)
t = '\n'.join(_res); assert _nd >= 10, _nd
# 7b) the old box-opening css region is replaced (a few still-needed lines are kept)
css_new = rd('boxes.css')
a = t.index('/* نافذة الفتح */'); b = t.index('/* نافذة تفاصيل البكج: ورقة سفلية')
region = t[a:b].split('\n')
KEEP = ('.bx-modal .bx-stage{', '.bx-modal .bx-stage.is-done{', '.bx-modal .bx-modal-odds{', '.bx-card[data-tone="s"] .bx-svg, .bx-card[data-tone="ss"] .bx-svg{',
        '.bx-card, .bx-modal, .bx-own-chip, .bx-own-tile{ --bx-glow', '.bx-card[data-tone="b"], .bx-modal[data-tone="b"], .bx-own-tile[data-tone="b"]{ --bx-glow',
        '.bx-card[data-tone="s"], .bx-modal[data-tone="s"], .bx-own-tile[data-tone="s"]{ --bx-glow', '@keyframes bxSheen')
kept = [l for l in region if l.startswith(KEEP)]
assert len(kept) >= 8, len(kept)
t = t[:a] + '\n'.join(kept) + '\n' + css_new + '\n' + t[b:]
t = t.replace('bx-svg', 'bxa')

# ---------- 8) nothing of the old system may remain ----------
for bad in ('econBoxLogo', 'ECON_BOX_MAT', 'econBoxUid', 'econBoxSvg', 'bxc-', 'bxr-', 'bx-lid', 'bx-lock', 'CodisBoxCinema.toggleMode', 'modeLabel', 'ECON_BULK_MS', 'bx-burst', 'is-shaking'):
    assert bad not in t, 'leftover: ' + bad + ' @' + str(t.index(bad)) + ' ' + repr(t[max(0,t.index(bad)-80):t.index(bad)+80])
open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
