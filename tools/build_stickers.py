#!/usr/bin/env python3
"""CODIS-STICKERS builder. يقرأ tools/stickers_meta.py ويفحص assets/stickers/ ثم:
  1) يحدّث كتلة البيانات داخل ملف التطبيق (بين علامتي CODIS-STICKERS-DATA) — المتاح فقط يظهر بالمنتقي
  2) يكتب docs/CODIS_STICKER_PROMPTS.md (مطالبة جاهزة لكل ستيكر لأداة توليد الصور)
الاستعمال: py -3 tools/build_stickers.py [ملف_التطبيق]   (الافتراضي app/CODIS_FINAL.html)"""
import sys, os, json, hashlib, re
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
sys.path.insert(0, here)
import stickers_meta as M

target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'app', 'CODIS_FINAL.html')
sdir = os.path.join(root, 'assets', 'stickers')
os.makedirs(sdir, exist_ok=True)

ids = [s[0] for s in M.S]
assert len(ids) == len(set(ids)), 'duplicate sticker id'
cats = {c[0] for c in M.CATS}
for s in M.S:
    assert re.match(r'^[a-z0-9_]{2,32}$', s[0]), 'bad id ' + s[0]
    assert s[1] in cats, 'bad cat ' + s[1]

files = {}
for fn in os.listdir(sdir):
    m = re.match(r'^([a-z0-9_]+)\.(webp|png|svg)$', fn)
    if not m or m.group(1) not in ids: continue
    h = hashlib.sha1(open(os.path.join(sdir, fn), 'rb').read()).hexdigest()[:6]
    files[m.group(1)] = '%s?v=%s' % (fn, h)

items = [[s[0], s[1], s[2], s[3], files.get(s[0], 0)] for s in M.S]
block = '/* CODIS-STICKERS-DATA */const CODIS_STICKER_CATS=%s;const CODIS_STICKER_ITEMS=%s;/* /CODIS-STICKERS-DATA */' % (
    json.dumps([list(c) for c in M.CATS], ensure_ascii=False, separators=(',', ':')),
    json.dumps(items, ensure_ascii=False, separators=(',', ':')))

html = open(target, encoding='utf-8').read()
pat = re.compile(r'/\* CODIS-STICKERS-DATA \*/.*?/\* /CODIS-STICKERS-DATA \*/', re.S)
if not pat.search(html): sys.exit('data block markers missing in ' + target)
html = pat.sub(lambda _m: block, html, count=1)
# CODIS-STICKER-ATMOS: لوحات الألوان (من رسم الستيكر نفسه) + الوصفات + نسخ «باليد» الصغيرة — تُحسب هنا مرة، لا داخل التطبيق
apat = re.compile(r'/\* CODIS-STICKER-ATMOS-DATA \*/.*?/\* /CODIS-STICKER-ATMOS-DATA \*/', re.S)
if apat.search(html):
    import sticker_atmos
    ablock = sticker_atmos.block(M, set(files))
    html = apat.sub(lambda _m: ablock, html, count=1)
open(target, 'w', encoding='utf-8', newline='').write(html)

lines = ['# مطالبات توليد ستيكرات CODIS', '',
         'كل ستيكر يُولَّد **بصورة مستقلة** (PNG أو WebP شفاف، مربع 1024×1024) ويُحفظ باسم **المعرّف** داخل `assets/stickers/` مثل `shawarma.webp`.',
         'بعد وضع الصور شغّل: `py -3 tools/build_stickers.py` (يحدّث المكتبة ويظهر المتاح فقط بالمنتقي). يمكن لاحقاً تبديل أي صورة بنفس الاسم.', '',
         '## الأسلوب العام (يُلصق قبل وصف كل ستيكر)', '', '```', M.STYLE, '```', '',
         '## الممنوعات (تُلصق بعد وصف كل ستيكر)', '', '```', M.NEGATIVE, '```', '',
         '> ملاحظة جودة: وزّع التنوّع فعلاً — كل ستيكر بتكوين وزاوية ولوحة ألوان وملمس مختلف، ضمن نفس العائلة الفنية. لا تستعمل قالباً واحداً.', '']
cname = {c[0]: c[1] for c in M.CATS}
for cid, cn, _kw in M.CATS:
    lines += ['## ' + cn, '']
    for s in M.S:
        if s[1] != cid: continue
        st = 'موجود' if s[0] in files else 'ناقص'
        lines += ['### `%s` — %s (%s)' % (s[0], s[2], st), '', '```', 'Subject: %s. Palette: %s.' % (s[4], s[5]), '```', '']
os.makedirs(os.path.join(root, 'docs'), exist_ok=True)
open(os.path.join(root, 'docs', 'CODIS_STICKER_PROMPTS.md'), 'w', encoding='utf-8').write('\n'.join(lines))
print('stickers: %d defined, %d with image, %d categories -> %s' % (len(ids), len(files), len(M.CATS), os.path.basename(target)))
