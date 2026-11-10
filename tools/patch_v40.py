#!/usr/bin/env python3
"""CODIS-SEAL (3.27.0، بعد patch_v39 + إصلاح no-cache): إغلاق ثغرة «انتحال المطوّر من الكونسول».

المشكلة: CodisAccount وCodisLimits كائنان قابلان للتعديل، وCodisLimits/CodisClock يسألان CodisAccount.isAdmin() ديناميكياً،
فيكفي أي مستخدم أن يكتب في الكونسول  CodisAccount.isAdmin = () => true  لتُرفَع قيود التطبيق عن جهازه ويُفتح زر الزمن.
(الخادم لم يكن معرَّضاً: كل دوال admin_* تتحقق من public.admins، والإضافة لا تُنزَّل إلا للمطوّر.) لكنها خالفت قاعدة CLAUDE.md
«لا تعرّض علامة المطوّر على كائن قابل للتعديل».

الحل (تحصين، لا بديل عن الخادم):
  1) codisSeal(): تجميد CodisAccount وCodisLimits (وـ_test) على أي مضيف غير محلي ⇒ الاستبدال من الكونسول لا يغيّر شيئاً.
  2) CodisAccount.state يُكشف للقراءة فقط (Proxy يتجاهل الكتابة/الحذف) على المضيف المحصَّن.
  3) codisFetch: مرجع fetch الأصلي يُلتقط وقت التحميل فلا يستطيع سكربت لاحق من الكونسول اعتراض فحص admins وتنزيل الإضافة.
  «محصَّن» = أي مضيف غير localhost/127.0.0.1/[::1]/*.localhost (يشمل file:// وgithub.io) أو window.CODIS_SEAL_FORCE===true قبل التحميل
  (الأخير لا يمكن أن يُضعف الحماية، يقوّيها فقط ويستعمله tests/seal_browser.js).
  على المضيف المحلي تبقى الأجسام قابلة للتعديل عمداً: هذا ما تعتمد عليه اختبارات المتصفح ووضع المطوّر المحلي (tools/dev_local.html)،
  ومن يشغّل نسخة على جهازه يتحكم بها كلياً أصلاً.
حدّ لا يمكن إزالته من جهة العميل: من يعدّل ملف الصفحة نفسه (DevTools Overrides) أو يستدعي دوال الاقتصاد مباشرة يتحكم ببياناته المحلية؛
الحماية الفعلية للآخرين = الخادم (RLS + codis_require_admin)."""
import sys, re

src, out = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ('app/CODIS_FINAL.html', 'app/CODIS_FINAL.html')
s = open(src, encoding='utf-8').read()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, 'expected %d got %d for: %r' % (n, c, a[:80])
    s = s.replace(a, b)

# 0) تعريف الختم قبل CodisClock (أول ما يلزم) — لا يقرأ أي const لاحق (قاعدة load-time safety)
SEAL = r"""/* ================= CODIS-SEAL (3.27.0): تحصين كائنات الصلاحية ضد التعديل من الكونسول =================
   محصَّن = أي مضيف غير محلي (أو CODIS_SEAL_FORCE===true). التفاصيل والحدود: tools/patch_v40.py وdocs/DEV_HUB.md. */
const CODIS_SEALED = (function(){ try{ const h = String(location.hostname || ''); const local = h === 'localhost' || h === '127.0.0.1' || h === '[::1]' || /\.localhost$/.test(h); return !local || window.CODIS_SEAL_FORCE === true; }catch(e){ return true; } })();
const codisSeal = o=>{ if(!CODIS_SEALED) return o; try{ return Object.freeze(o); }catch(e){ return o; } };
const codisFetch = (function(){ if(!CODIS_SEALED) return null; try{ return window.fetch.bind(window); }catch(e){ return null; } })();
"""
rep("const CodisClock = (function(){", SEAL + "const CodisClock = (function(){")

# 1) CodisLimits
rep("return { on, verified, bypass, afford, num, reg, registry:()=>Object.keys(REG).map(k=>REG[k]), constants:()=>Object.keys(CONST).map(k=>CONST[k]) };\n})();",
    "return codisSeal({ on, verified, bypass, afford, num, reg, registry:()=>Object.keys(REG).map(k=>REG[k]), constants:()=>Object.keys(CONST).map(k=>CONST[k]) });\n})();")

# 2) CodisAccount: الكائن + _test مجمّدان، state للقراءة فقط
OLD = "return { init, signIn, signOut, deleteAccount, syncNow, noteChange, pullInbox, adminCall, pushCall, state:S, configured,"
NEW = "return codisSeal({ init, signIn, signOut, deleteAccount, syncNow, noteChange, pullInbox, adminCall, pushCall, state:(CODIS_SEALED ? new Proxy(S, { set:()=>true, defineProperty:()=>true, deleteProperty:()=>true }) : S), configured,"
rep(OLD, NEW)
rep("_test:{ merge:CodisMerge.merge, loadBase, saveBase, mergeAndAdopt, hasProgress, checkBackend, authErrMsg, classify, b64u, jwt } };",
    "_test:codisSeal({ merge:CodisMerge.merge, loadBase, saveBase, mergeAndAdopt, hasProgress, checkBackend, authErrMsg, classify, b64u, jwt }) });")

# 3) fetch الملتقَط: فحص admins وتنزيل الإضافة يمرّان من raw()
rep("try{ return await fetch(cfg.url + path, {", "try{ return await (codisFetch || fetch)(cfg.url + path, {")

open(out, 'w', encoding='utf-8', newline='').write(s)
print('patch_v40 ok')
