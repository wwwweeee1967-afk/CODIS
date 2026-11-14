"""CODIS-V45 (3.32.0) — «سلفني» (اقتراض الكوينز + استقطاع تلقائي) + إعادة تصميم الإدارة المالية (رئيسية مختصرة + قائمة جانبية).
  py -3 tools/patch_v45.py app/CODIS_FINAL.html app/CODIS_FINAL.html     (بعد patch_v44؛ ثم set_version.py 3.32.0) — أو: sh tools/rebuild_v45.sh"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'CODIS-V45' not in s, 'already applied'
def rd(p): return open(os.path.join(HERE, 'identity', p), encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:140])
    s = s.replace(old, new)

# ---------- 1) أنواع المعاملات + تطبيع دفتر القروض ----------
once("function econTxTypes(){ return ['EARN_REWARD_EXCHANGE'", "function econTxTypes(){ return ['LOAN_BORROW','LOAN_REPAY','EARN_REWARD_EXCHANGE'")   # CODIS-V45
once("transactions:txs, silver:econNormSilver(w.silver) };", "transactions:txs, silver:econNormSilver(w.silver) };\n  d.loans = codisLoansNorm(d.loans);   /* CODIS-V45: دفتر سلفني (آمن وقت التحميل) */")

# ---------- 2) CodisWallet: السلفة ليست مكسباً + نقطة الاستقطاع المركزية + اللقطة الذرّية ----------
once("    if(amount > 0) w.lifetimeEarned = econAddC(w.lifetimeEarned, amount); else w.lifetimeSpent = econAddC(w.lifetimeSpent, -amount);\n    w.transactions.push(tx);\n    return tx;",
     "    if(amount > 0){ if(type !== 'LOAN_BORROW') w.lifetimeEarned = econAddC(w.lifetimeEarned, amount); } else w.lifetimeSpent = econAddC(w.lifetimeSpent, -amount);   /* CODIS-V45: السلفة ليست دخلاً مكتسباً */\n    w.transactions.push(tx);\n    /* CODIS-V45: استقطاع سلفني — كل إضافة موجبة جديدة (غير السلفة/السداد، وبلا meta.noRepay) تُسدّد من نفسها فقط، داخل المعاملة الذرّية نفسها */\n    if(amount > 0 && type !== 'LOAN_BORROW' && !(meta && meta.noRepay)) CodisLoans.repayFrom(tx);\n    return tx;")
once("fz = JSON.stringify(data.finance || null);", "fz = JSON.stringify(data.finance || null), ln = JSON.stringify(data.loans || null);   /* CODIS-V45 */")
once("if(fz !== 'null') data.finance = JSON.parse(fz);", "if(fz !== 'null') data.finance = JSON.parse(fz);\n      if(ln !== 'null') data.loans = JSON.parse(ln); else delete data.loans;   /* CODIS-V45: دفتر القروض جزء من نفس المعاملة */")
once("econUid('adj')); return tx", "econUid('adj'), { noRepay:true }); return tx")   # تعديل المطوّر اليدوي لا يُستقطع (الهدايا بـ ref 'grant|' تُستقطع)

# ---------- 3) الدمج بين الأجهزة: السلفة لا ترفع المكتسب ----------
once("add += t.amount; if(t.amount > 0) earned += t.amount; else spent += -t.amount;", "add += t.amount; if(t.amount > 0){ if(t.type !== 'LOAN_BORROW') earned += t.amount; } else spent += -t.amount;   /* CODIS-V45 */")

# ---------- 4) نتيجة استبدال المكافأة تُظهر المسدَّد ----------
once("let owned = null;\n      if(choice === 'coins'){", "let owned = null, dp = 0;\n      if(choice === 'coins'){")
once("e.coinsAwarded = amount;", "e.coinsAwarded = amount; dp = (tx.meta && tx.meta.debtPaid) || 0;   /* CODIS-V45 */")
once("amount:choice === 'coins' ? amount : 0, owned:owned }", "amount:choice === 'coins' ? amount : 0, owned:owned, debtPaid:dp }")
once("$('outcome-copy').innerHTML = '+' + econFmt(res.amount) + ' كوين · الرصيد ' + econFmt(CodisWallet.balance()); }", "$('outcome-copy').textContent = codisCoinsCopy(res); }")

# ---------- 5) سجل الكوينز: بطاقة سلفني + صفوف القروض ----------
once("  const txs = w.transactions.slice().reverse();\n  html += '<section class=\"ecl-sec\" aria-labelledby=\"ecl-h-tx\">", "  html += codisLoanCardHtml();   /* CODIS-V45 */\n  const txs = w.transactions.slice().reverse();\n  html += '<section class=\"ecl-sec\" aria-labelledby=\"ecl-h-tx\">")
once("'<div class=\"eco-log-row ecl-row ' + (up ? 'is-up' : 'is-down') + '\">", "'<div class=\"eco-log-row ecl-row ' + (up ? 'is-up' : 'is-down') + codisLoanRowCls(t) + '\">")
once("(up ? 'مكتسب ' : 'مصروف ')", "codisTxWord(t, up)")
once("(t.meta && t.meta.name ? '<span class=\"eco-log-sub ecl-item\">' + escapeHtml(t.meta.name) + '</span>' : '') + '</div>' +", "(t.meta && t.meta.name ? '<span class=\"eco-log-sub ecl-item\">' + escapeHtml(t.meta.name) + '</span>' : '') + codisLoanRowSub(t) + '</div>' +")

# ---------- 6) الأيقونات (نفس نظام CODIS_ICONS: شبكة 24 وخط موحّد) ----------
ICONS = """  menu: { id:'icon-menu', meaning:'القائمة الجانبية', size:'md',
    body:'<path d="M4 7h16M4 12h16M4 17h16"/>' },
  deposit: { id:'icon-deposit', meaning:'إيداع: مال يدخل المحفظة', size:'lg',
    body:'<path d="M12 3.4v8.4"/><path d="M8.5 8.4l3.5 3.5 3.5-3.5"/><path d="M4.6 14.2h4l1.2 2.1h4.4l1.2-2.1h4"/><path d="M4.6 14.2v4a1.8 1.8 0 0 0 1.8 1.8h11.2a1.8 1.8 0 0 0 1.8-1.8v-4"/>' },
  withdraw: { id:'icon-withdraw', meaning:'سحب: مال يخرج من المحفظة', size:'lg',
    body:'<path d="M12 11.8V3.4"/><path d="M8.5 6.9L12 3.4l3.5 3.5"/><path d="M4.6 14.2h4l1.2 2.1h4.4l1.2-2.1h4"/><path d="M4.6 14.2v4a1.8 1.8 0 0 0 1.8 1.8h11.2a1.8 1.8 0 0 0 1.8-1.8v-4"/>' },
  loan: { id:'icon-loan', meaning:'سلفني: سلفة كوينز', size:'lg',
    body:'<path d="M19.6 12a7.6 7.6 0 1 1-2.5-5.6"/><path d="M19.8 4.4v3.6h-3.6"/><circle cx="12" cy="12" r="3.2"/><path d="M12 10.7v2.6"/>' },
"""
once("  expand: { id:'icon-expand'", ICONS + "  expand: { id:'icon-expand'")

# ---------- 7) الإدارة المالية: استبدال الرئيسية القديمة ----------
i = s.index('function finRender(){'); j = s.index('function finRowHtml(')
assert 0 < i < j
s = s[:i] + s[j:]
once("function finSetPeriod(p){ finPeriod = p; finRender(); }\n", "")

# ---------- 8) الكود الجديد (بعد CodisInventory) ----------
once("  return { get, owned, closed, sellValue, grant, all };\n})();",
     "  return { get, owned, closed, sellValue, grant, all };\n})();\n\n" + rd('v45_core.js').rstrip() + "\n\n" + rd('v45_loans_ui.js').rstrip() + "\n\n" + rd('v45_fin.js').rstrip() + "\n")

# ---------- 9) الرجوع/الإغلاق ----------
once("  if(CodisFinUI.isOpen()) return { act:CodisFinUI.closeTop, el:CodisFinUI.el() };   /* CODIS-FINANCE */",
     "  if(CodisFinUI.isOpen()) return { act:CodisFinUI.closeTop, el:CodisFinUI.el() };   /* CODIS-FINANCE */\n  if(finDrawerIsOpen()) return { act:()=>finDrawerClose(), el:finDrawer.root };   /* CODIS-V45 */")
once("  const quiet = !!(opts && opts.silent);", "  const quiet = !!(opts && opts.silent);\n  try{ finDrawerClose(true); }catch(e){}   /* CODIS-V45 */")

# ---------- 10) CSS ----------
css = rd('v45.css'); assert '</style' not in css and '<!--' not in css
i = s.index('<style id="codis-v44-css">'); j = s.index('</style>', i) + len('</style>')
s = s[:j] + '\n<style id="codis-v45-css">\n' + css + '</style>' + s[j:]
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('v45 applied')
