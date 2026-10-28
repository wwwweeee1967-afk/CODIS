#!/usr/bin/env python3
"""مصدر الإصدار الوحيد = ملف VERSION. هذا السكربت يختم قيمته في <meta name="codis-version"> داخل app/CODIS_FINAL.html (ولا مكان آخر).
  الاستخدام:  python tools/set_version.py            ← يختم القيمة الحالية من VERSION (بعد تشغيل سلسلة patch_*)
              python tools/set_version.py 3.3.0      ← إصدار جديد: يكتب VERSION ثم يختمه
  الواجهة تقرأ الوسم وقت التشغيل (لا رقم مكتوب في الكود، ولا يتغيّر مع كل تحميل). صيغة الإصدار: MAJOR.MINOR.PATCH."""
import re, sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
vf, app = os.path.join(root, 'VERSION'), os.path.join(root, 'app', 'CODIS_FINAL.html')
if len(sys.argv) > 1:
    v = sys.argv[1].strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', v): sys.exit('صيغة غير صالحة (المطلوب x.y.z): ' + v)
    open(vf, 'w', encoding='utf-8', newline='\n').write(v + '\n')
v = open(vf, encoding='utf-8').read().strip()
if not re.fullmatch(r'\d+\.\d+\.\d+', v): sys.exit('VERSION غير صالح: ' + v)
s = open(app, encoding='utf-8').read()
n = len(re.findall(r'<meta name="codis-version" content="[^"]*">', s))
if n != 1: sys.exit('وسم codis-version يجب أن يظهر مرة واحدة (وُجد %d) — شغّل patch_v2.py أولاً' % n)
s = re.sub(r'<meta name="codis-version" content="[^"]*">', '<meta name="codis-version" content="%s">' % v, s)
open(app, 'w', encoding='utf-8', newline='').write(s)
print('CODIS version =', v)
