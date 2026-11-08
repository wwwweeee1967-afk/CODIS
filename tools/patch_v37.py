"""CODIS-PAPER-BACK (3.24.0) — ظهر البطاقة الخاص بالمظهر الورقي (الداكن لا يتغيّر).

  py -3 tools/patch_v37.py app/CODIS_FINAL.html app/CODIS_FINAL.html      (بعد patch_v36؛ ثم set_version.py 3.24.0)

  • tools/identity/v37.js — codisPaperBackSvg (وثيقة محفورة: ورق/حبر لكل ندرة، غيوشيه من اسم البطاقة، ستيكرها بالميدالية، ختم بريد/شمع، رقم تسلسلي)
    + codisCardBackHtml الجديدة (نفس المدخلات، تختار الزخرفة حسب المظهر) + MutationObserver لتبديل المظهر وقت التشغيل.
  • tools/identity/v37.css — كل القواعد تحت html[data-theme="paper"] .cbk.is-paper.
  • المتجر وبحوزتك يمرّران stickerId للظهر.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-PAPER-BACK' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:110])
    s = s.replace(old, new)

a = 'function codisCardBackHtml(title, rows, o){'
b = '/* CODIS-CLARITY: لوح ظهر البطاقة'
assert s.count(a) == 1 and s.count(b) == 1
i = s.index(a); j = s.index(b, i)
s = s[:i] + rd('v37.js').rstrip() + chr(10) + s[j:]

once("{ tone:rar.tone, kind:wk ? 'weekly' : mo ? 'monthly' : 'reward' });",
     "{ tone:rar.tone, kind:wk ? 'weekly' : mo ? 'monthly' : 'reward', sticker:it.stickerId });   /* CODIS-PAPER-BACK */")
once("{ tone:it.rarityTone, kind:(it.scope === 'weekly' ? 'weekly' : it.scope === 'monthly' ? 'monthly' : 'reward') });",
     "{ tone:it.rarityTone, kind:(it.scope === 'weekly' ? 'weekly' : it.scope === 'monthly' ? 'monthly' : 'reward'), sticker:it.stickerId });   /* CODIS-PAPER-BACK */")

css = rd('v37.css'); assert '</style' not in css
i = s.index('<style id="codis-v36-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v37-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v37 ok', len(s))
