"""CODIS-V43 (3.30.0) — إدارة المكافآت: إزالة الملاحظات وأزرار الإضافة اليدوية · إضافة تلقائية متكررة بستيكر · تحديد/حذف جماعي · إصلاح أيقونة الوقت · شريط سفلي زجاجي.
  py -3 tools/patch_v43.py app/CODIS_FINAL.html app/CODIS_FINAL.html     (بعد patch_v42؛ ثم set_version.py 3.30.0) — أو: sh tools/rebuild_v43.sh"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-V43' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:140])
    s = s.replace(old, new)

# ---------- 1) الملاحظات التوضيحية: مكافآت فقط ----------
once("function econRpNoteFor(settingsRoom){\n", "function econRpNoteFor(settingsRoom){\n  if(rpKind !== 'punish') return '';   /* CODIS-V43: لا عبارات توضيحية بأقسام المكافآت (العقوبات كما هي) */\n")

# ---------- 2) حذف أزرار الإضافة اليدوية للمكافآت (كتلة المكافآت فقط) ----------
a = s.index('id="rp-reward-block"'); b = s.index('id="rp-punish-block"')
blk = s[a:b]
blk, n1 = re.subn(r'\s*<button type="button" class="rpu-add" aria-expanded="false" onclick="rpuAdd\(\'reward\',\'(?:daily|weekly|monthly)\'\)">.*?</button>', '', blk, flags=re.S)
blk, n2 = re.subn(r'\n\s*<div class="rpu-add-slot"></div>', '', blk)
assert n1 == 3 and n2 == 3, (n1, n2)
s = s[:a] + blk + s[b:]
once('<div hidden id="rpu-stash"><div id="reward-add-box"></div><div id="punish-add-box"></div></div>', '<div hidden id="rpu-stash"><div id="punish-add-box"></div></div>')

# ---------- 3) الإضافة التلقائية (استبدال الكتلة كاملة) ----------
i0 = s.index("/* ================= الإضافة التلقائية للمكافآت (مالية / وقتية) ================= */\nlet finAuto = null;")
i1 = s.index("/* ---------- استخدام مكافأة مالية: تأكيد صريح قبل أي خصم ---------- */")
s = s[:i0] + rd('v43_auto.js').rstrip() + '\n\n' + s[i1:]

# ---------- 4) التحديد والحذف الجماعي ----------
bulk = rd('v43_bulk.js').rstrip().replace("const rpuSel = { on:false, ids:{} };", "var rpuSel = { on:false, ids:{} };", 1) + '\n'
once("var rpuView = 'daily';\n", "var rpuView = 'daily';\n" + bulk)
once("function setSettingsPeriod(p){\n  if(['daily', 'weekly', 'monthly', 'all'].indexOf(p) === -1) return;\n", "function setSettingsPeriod(p){\n  if(['daily', 'weekly', 'monthly', 'all'].indexOf(p) === -1) return;\n  if(p !== 'all') rpuSelReset();   /* CODIS-V43 */\n")
once("function rpOpenHub(kind){\n  rpKind = kind === 'punish' ? 'punish' : 'reward'; econEditing = null;", "function rpOpenHub(kind){\n  rpKind = kind === 'punish' ? 'punish' : 'reward'; econEditing = null; rpuSelReset();   /* CODIS-V43 */")
once("  else if(none) none.remove();\n}\nfunction rpuFindClear()", "  else if(none) none.remove();\n  rpuBulkPaint();   /* CODIS-V43: شريط التحديد يتبع الظاهر بعد البحث */\n}\nfunction rpuFindClear()")
once("(ed ? ' is-editing' : '') + '\" data-name=\"' + escapeHtml(codisNormText(it.name)) + '\">' +\n",
     "(ed ? ' is-editing' : '') + (rpuSel.on && rpuView === 'all' && rpuSel.ids[it.id] ? ' is-sel' : '') + '\" data-id=\"' + escapeHtml(it.id) + '\" data-name=\"' + escapeHtml(codisNormText(it.name)) + '\">' + rpuSelHtml(it.id) +\n")
once("function econEdit(id){ econEditing", "function econEdit(id){ if(rpuSel.on){ rpuSelToggle(id); return; }   /* CODIS-V43: بوضع التحديد النقر يحدّد */\n  econEditing")

# ---------- 5) CSS ----------
css = rd('v43.css'); assert '</style' not in css and '<!--' not in css
i = s.index('<style id="codis-v42-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v43-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('v43 applied')
