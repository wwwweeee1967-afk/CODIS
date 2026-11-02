#!/usr/bin/env python3
"""CODIS-ASSETS (بعد patch_v22.py) — 3.13.0 — نفس الصور بالبايت، لكن كملفات بدل نصوص base64 داخل الجافاسكربت.
السبب (مقاس): 7.1MB من أصل 8.9MB كانت صوراً مدفونة كنصوص داخل السكربت ⇒ كل فتح للتطبيق يحمّل ويحلّل ويحفظ بالذاكرة كل الصور
(حتى غير المعروضة)، وعلى iOS يُخزَّن نص السكربت (فيه عربي) بترميز 16-bit ⇒ عشرات الميغابايت قبل أول رسم. الآن:
 • كل صورة > 2KB تُكتب مرة كملف assets/img/<sha1>.<ext> (البايتات نفسها حرفياً) والنص يُستبدل بمسارها النسبي.
 • CODIS_PASS_ART (base64 خام) و CODIS_BOX_ART.b64 ← مسارات ملفات، ودالتا الاستعمال تقبلان المسار.
 • CodisCardAmb: مفتاح الحفظ الدائم = مسار الصورة (ثابت) عند غياب مفتاح blob.
 • sw.js يحمّل كل الصور مسبقاً للعمل بلا إنترنت (يُحدَّث بقائمة الملفات تلقائياً بواسطة هذا السكربت).
Usage: py -3 tools/patch_v23.py <in.html> <out.html> <assets_root_dir>   (الملفات تُكتب في <assets_root_dir>/img)
"""
import sys, re, os, base64, hashlib
src, dst, root = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(src, encoding='utf-8').read()
if 'CODIS-ASSETS' in s: sys.exit('already patched (CODIS-ASSETS)')
imgdir = os.path.join(root, 'img'); os.makedirs(imgdir, exist_ok=True)
EXT = { 'webp':'webp', 'png':'png', 'jpeg':'jpg', 'gif':'gif' }
written = {}

def store(b64, ext):
    data = base64.b64decode(b64)
    name = hashlib.sha1(data).hexdigest()[:16] + '.' + ext
    p = os.path.join(imgdir, name)
    if not os.path.exists(p): open(p, 'wb').write(data)
    written[name] = len(data)
    return 'assets/img/' + name

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# 1) data: URIs كبيرة
n_uri = 0
def sub_uri(m):
    global n_uri
    n_uri += 1
    return store(m.group(2), EXT[m.group(1)])
s = re.sub(r'data:image/(webp|png|jpeg|gif);base64,([A-Za-z0-9+/]{2048,}={0,2})', sub_uri, s)

# 2) CODIS_PASS_ART: قيم base64 خام (webp)
i = s.index('const CODIS_PASS_ART = {'); j = s.index('};', i)
seg = s[i:j]; cnt = [0]
def sub_pass(m):
    cnt[0] += 1
    return '"' + m.group(1) + '":"' + store(m.group(2), 'webp') + '"'
seg2 = re.sub(r'"([a-z]+:[A-Z]+)":"([A-Za-z0-9+/]{1000,}={0,2})"', sub_pass, seg)
if cnt[0] < 6: sys.exit('pass art values replaced: %d' % cnt[0])
s = s[:i] + seg2 + s[j:]
rep("function codisPassArtSrc(key){ return codisPassArtUrls[key] || (codisPassArtUrls[key] = 'data:image/webp;base64,' + CODIS_PASS_ART[key]); }",
    "function codisPassArtSrc(key){ const v = CODIS_PASS_ART[key]; return codisPassArtUrls[key] || (codisPassArtUrls[key] = /^assets\\//.test(v) ? v : 'data:image/webp;base64,' + v); }   /* CODIS-ASSETS */", 'pass src')

# 3) CODIS_BOX_ART: b64 → src
cb = [0]
def sub_box(m):
    cb[0] += 1
    return "src:'" + store(re.sub(r'\s', '', m.group(1)), 'webp') + "'"
s = re.sub(r"b64:'([A-Za-z0-9+/=\s]{1000,}?)'", sub_box, s)
if cb[0] != 5: sys.exit('box art replaced: %d (expected 5)' % cb[0])
rep("  const a = CODIS_BOX_ART[n]; let u = 'data:image/webp;base64,' + a.b64;",
    "  const a = CODIS_BOX_ART[n]; if(a.src) return CODIS_BOX_URLS[n] = a.src;   /* CODIS-ASSETS: ملف بدل base64 */\n  let u = 'data:image/webp;base64,' + a.b64;", 'box url')

# 4) مفتاح الخلفية المحيطة الدائم للصور الملفّية
rep("    const key = img._codisAk || '';", "    const key = img._codisAk || (/^(blob|data):/.test(src) ? '' : src);   /* CODIS-ASSETS: مسار الملف ثابت */", 'amb key')

left = re.findall(r'data:image/(?:webp|png|jpeg|gif);base64,[A-Za-z0-9+/]{2048,}', s)
if left: sys.exit('big data URIs left: %d' % len(left))
s = s.replace('<meta name="codis-version"', '<!-- CODIS-ASSETS --><meta name="codis-version"', 1)
open(dst, 'w', encoding='utf-8', newline='').write(s)
open(os.path.join(root, 'img', 'index.txt'), 'w', encoding='utf-8').write('\n'.join(sorted(written)) + '\n')
print('ok uris=%d pass=%d box=%d files=%d bytes=%d out_chars=%d' % (n_uri, cnt[0], cb[0], len(written), sum(written.values()), len(s)))
