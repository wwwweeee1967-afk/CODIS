#!/bin/sh
# يعيد بناء app/CODIS_FINAL.html: (قبل v41) <- v41 <- v42 <- v43 <- v44 <- v45 <- ختم الإصدار 3.32.0
set -e
cd "$(dirname "$0")/.."
cp backups/before_v41/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v41.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v42.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v43.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v44.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/patch_v45.py app/CODIS_FINAL.html app/CODIS_FINAL.html
py -3 tools/set_version.py 3.32.0
node tests/syntax.js app/CODIS_FINAL.html
