"""CODIS-TOAST-DEFER: the purchase toast ("تم شراء وفتح 10 بكجات… (−1,820)" / "تم الشراء: …") used to pop up at the very moment the opening
animation starts and covered the boxes and the reward cards. The confirmation is now held and shown AFTER the opening modal closes
(the result screen itself already shows the price and the count). Run AFTER tools/patch_boxes.py:  python tools/patch_toast.py <in> <out>"""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "app/CODIS_FINAL.html"
out = sys.argv[2] if len(sys.argv) > 2 else src
t = open(src, 'rb').read().decode('utf-8')
assert 'CODIS-TOAST-DEFER' not in t, 'toast patch already applied'
assert 'CODIS-BOXES-V3' in t, 'run tools/patch_boxes.py first'

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f'expected {count} got {n} for: {old[:90]!r}'
    t = t.replace(old, new)

# ---- x10: keep the message on the result, show it when the results modal closes (or immediately if the modal could not open) ----
rep("showToast('تم شراء وفتح ' + econFmt(res.n) + ' بكجات: ' + t.name + ' (−' + econFmt(res.total) + ')', 'var(--success)', 'gift');",
    "res.toastMsg = 'تم شراء وفتح ' + econFmt(res.n) + ' بكجات: ' + t.name + ' (−' + econFmt(res.total) + ')';   /* CODIS-TOAST-DEFER: لا إشعار فوق الحركة */")
rep("  if(res && res.ok) econBulkShow(res);\n}", "  if(res && res.ok && !econBulkShow(res) && res.toastMsg) showToast(res.toastMsg, 'var(--success)', 'gift');\n}")
rep("  if(silent !== true && s && s.phase === 'opening') showToast('انضافت ' + econFmt(s.res.items.length) + ' مكافآت إلى بحوزتك', 'var(--success)', 'gift');",
    "  if(silent !== true && s){ if(s.res.toastMsg) showToast(s.res.toastMsg, 'var(--success)', 'gift'); else if(s.phase === 'opening') showToast('انضافت ' + econFmt(s.res.items.length) + ' مكافآت إلى بحوزتك', 'var(--success)', 'gift'); }")

# ---- single box: buy then open immediately ----
rep("  let boughtBox = null;\n  try{\n    const t = CodisBoxes.tier(tierId);", "  let boughtBox = null, buyToast = '';\n  try{\n    const t = CodisBoxes.tier(tierId);")
rep("if(r.ok){ boughtBox = r.box; codisSfx('store.buy'); showToast('تم الشراء: ' + t.name + ' (−' + econFmt(r.price) + ')', 'var(--success)', 'gift');",
    "if(r.ok){ boughtBox = r.box; codisSfx('store.buy'); buyToast = 'تم الشراء: ' + t.name + ' (−' + econFmt(r.price) + ')';")
rep("  if(boughtBox) econBoxOpenFor(boughtBox.tier, boughtBox.uid, true);\n}",
    "  if(boughtBox){ econBoxOpenFor(boughtBox.tier, boughtBox.uid, true); if(buyToast){ if(econBoxState) econBoxState.buyToast = buyToast; else showToast(buyToast, 'var(--success)', 'gift'); } }\n}")
rep("showToast('انضافت «' + s.result.item.name + '» إلى بحوزتك', 'var(--success)', 'gift');\n  const opener",
    "showToast('انضافت «' + s.result.item.name + '» إلى بحوزتك', 'var(--success)', 'gift');\n  else if(s && s.buyToast) showToast(s.buyToast, 'var(--success)', 'gift');\n  const opener")
open(out, 'wb').write(t.encode('utf-8'))
print('ok', len(t))
