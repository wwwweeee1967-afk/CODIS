#!/bin/sh
# يعيد بناء app/CODIS_FINAL.html: (قبل v41) ← patch_v41 ← patch_v42 ← ختم الإصدار 3.29.0. استعمله بدل rebuild_v41.sh بعد الآن.
set -e
cd "$(dirname "$0")/.."
cp backups/before_v41/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v41.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v42.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/set_version.py 3.29.0
node tests/syntax.js app/CODIS_FINAL.html
