#!/bin/sh
# يعيد بناء app/CODIS_FINAL.html من النسخة النظيفة قبل v41 ثم يطبّق patch_v41 ويختم الإصدار (استعمل بعد أي تعديل على tools/identity/v41*.js|css)
set -e
cd "$(dirname "$0")/.."
cp backups/before_v41/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v41.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/set_version.py 3.28.0
node tests/syntax.js app/CODIS_FINAL.html
