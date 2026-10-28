"""CODIS-SYNC-HOLD: a hard guard so the Developer Tools add-on can never upload preview data to the cloud.
The add-on (admin only, loaded from the private bucket) previews screens on a SANDBOX copy of `data` with an in-memory localStorage.
While window.CODIS_SYNC_HOLD is true the account module: records no change, never pushes, never reconciles/overwrites local data,
never rotates the refresh token (the rotated token would be written to the sandbox storage and the real one would be lost).
Run AFTER tools/patch_toast.py:  python tools/patch_dev.py <in> <out>"""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-SYNC-HOLD' not in t, 'sync-hold patch already applied'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

H = "window.CODIS_SYNC_HOLD"
rep("  function noteChange(){\n    changeCtr++;\n", "  function noteChange(){\n    if(" + H + ") return;   /* CODIS-SYNC-HOLD */\n    changeCtr++;\n")
rep("  async function push(){\n    if(pushing || !ready()) return;\n", "  async function push(){\n    if(" + H + " || pushing || !ready()) return;   /* CODIS-SYNC-HOLD */\n")
rep("  async function reconcile(){\n    S.reconciling = true; setStatus('syncing');\n", "  async function reconcile(){\n    if(" + H + ") return;   /* CODIS-SYNC-HOLD */\n    S.reconciling = true; setStatus('syncing');\n")
rep("  function syncNow(){ if(!S.user || S.reconciling) return;", "  function syncNow(){ if(!S.user || S.reconciling || " + H + ") return;")
rep("  async function refreshOnce(){\n", "  async function refreshOnce(){\n    if(" + H + ") throw Object.assign(new Error('sync hold'), { net:true });   /* CODIS-SYNC-HOLD: لا تجديد رمز بينما التخزين وهمي */\n")
open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
