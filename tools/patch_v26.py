#!/usr/bin/env python3
"""CODIS-CRUMBS (بعد patch_v25.py) — 3.14.1 — تشخيص انهيار الآيفون من الجهاز نفسه، بلا أي تغيير بالشكل أو الحركات.
iOS يقتل الصفحة عند امتلاء الذاكرة بلا أي رسالة للجافاسكربت، والكمبيوتر لا يكرر حدّ ذاكرة iPhone 12. لذلك:
 • CodisCrumb.mark(step) يكتب آخر مرحلة وصلها التطبيق (localStorage، متزامن) في المسارات الثقيلة: الإقلاع، المتجر، الشراء ومراحل
   مشهد الشراء، المعاينة. الخروج الطبيعي (الخلفية/الإغلاق/نهاية المشهد) يكتب 'idle'.
 • عند الإقلاع: إن كانت آخر مرحلة ليست 'idle' (= الصفحة ماتت أثناءها) تظهر بطاقة صغيرة بالمرحلة والإصدار والشاشة وآخر أخطاء الجافاسكربت،
   ليصوّرها المستخدم. لا تظهر إطلاقاً في الاستعمال العادي. لا تُرسل أي بيانات لأي مكان.
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-CRUMBS' in s: sys.exit('already patched (CODIS-CRUMBS)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

CRUMB = r"""/* CODIS-CRUMBS: آخر مرحلة قبل أي توقف مفاجئ (iOS يقتل الصفحة عند امتلاء الذاكرة بلا رسالة). محلي فقط، لا يُرسل لأي مكان */
const CodisCrumb = (function(){
  'use strict';
  const K = 'codis_crumb', E = 'codis_crumb_err';
  let prev = null; try{ prev = JSON.parse(localStorage.getItem(K) || 'null'); }catch(e){}
  let errs = []; try{ errs = JSON.parse(localStorage.getItem(E) || '[]') || []; }catch(e){}
  const ver = ()=>{ try{ return document.querySelector('meta[name="codis-version"]').content; }catch(e){ return '?'; } };
  let seq = 0;
  function mark(step, extra){ seq++; try{ localStorage.setItem(K, JSON.stringify({ s:step, x:extra === undefined ? '' : String(extra).slice(0, 60), t:Date.now(), v:ver() })); }catch(e){} }
  /* مرحلة قصيرة انتهت بسلام: ترجع idle بعد ms ما لم تُسجَّل مرحلة أخرى بعدها */
  function settle(ms){ const n = seq; setTimeout(()=>{ if(seq === n) mark('idle'); }, ms || 2000); }
  const idle = ()=>mark('idle');
  function err(m){ try{ errs.push(new Date().toISOString().slice(11, 19) + ' ' + String(m).slice(0, 160)); errs = errs.slice(-5); localStorage.setItem(E, JSON.stringify(errs)); }catch(e){} }
  window.addEventListener('error', e=>err((e.message || 'error') + ' @' + String(e.filename || '').split('/').pop() + ':' + (e.lineno || 0)));
  window.addEventListener('unhandledrejection', e=>err('promise: ' + (e.reason && (e.reason.message || e.reason))));
  document.addEventListener('visibilitychange', ()=>{ if(document.hidden) idle(); });
  window.addEventListener('pagehide', idle);
  /* بطاقة التشخيص: فقط إن ماتت الصفحة آخر مرة أثناء مرحلة (ليست idle) خلال آخر 20 دقيقة */
  function report(){
    if(!prev || prev.s === 'idle' || Date.now() - prev.t > 20 * 60 * 1000) return;
    const box = document.createElement('div');
    box.id = 'codis-crumb-card'; box.setAttribute('role', 'alert');
    box.style.cssText = 'position:fixed;left:12px;right:12px;bottom:calc(env(safe-area-inset-bottom, 0px) + 12px);z-index:9999;padding:12px 14px;border-radius:14px;background:#1b1f27;color:#f2f4f7;font:13px/1.5 system-ui,sans-serif;direction:rtl;box-shadow:0 8px 24px rgba(0,0,0,.5);border:1px solid #3a4150';
    const when = new Date(prev.t).toLocaleTimeString('ar-IQ', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
    box.innerHTML = '<b style="display:block;margin-bottom:4px">تشخيص: التطبيق توقّف آخر مرة</b>' +
      '<div dir="ltr" style="text-align:left;font:12px/1.5 ui-monospace,Menlo,monospace;white-space:pre-wrap;word-break:break-all">' +
      ('step: ' + prev.s + (prev.x ? ' (' + prev.x + ')' : '') + '\nversion: ' + prev.v + ' · at ' + when + '\nscreen: ' + screen.width + 'x' + screen.height + ' @' + (window.devicePixelRatio || 1) + 'x\n' + (navigator.userAgent.match(/OS [\d_]+/) || [''])[0] + (errs.length ? '\nerrors:\n' + errs.join('\n') : '')).replace(/[<>&]/g, c=>({ '<':'&lt;', '>':'&gt;', '&':'&amp;' })[c]) +
      '</div><div style="margin-top:6px;color:#aab2c0">صوّر هذي البطاقة وابعثها حتى يتصلّح السبب بالضبط.</div>' +
      '<button type="button" style="margin-top:8px;width:100%;min-height:40px;border:0;border-radius:10px;background:#2e3644;color:#fff;font:600 14px system-ui,sans-serif">تم</button>';
    box.querySelector('button').onclick = ()=>{ box.remove(); try{ localStorage.removeItem(E); }catch(e){} errs = []; };
    document.body.appendChild(box);
  }
  return { mark:mark, idle:idle, settle:settle, report:report, last:()=>prev };
})();
CodisCrumb.mark('boot');
let data = loadData();"""
rep("let data = loadData();", CRUMB, 'crumb module')

# الإقلاع اكتمل
rep("window.addEventListener('load', ()=>{ setTimeout(()=>{ registration(); try{ CodisTimers.tick(); }catch(e){} }, 300); });",
    "window.addEventListener('load', ()=>{ setTimeout(()=>{ registration(); try{ CodisTimers.tick(); }catch(e){} }, 300); setTimeout(()=>{ try{ CodisCrumb.report(); CodisCrumb.mark('idle'); }catch(e){} }, 1500); });   /* CODIS-CRUMBS */", 'boot done')

# المتجر
rep("function econOpenStore(){ econStoreEnterAt = Date.now(); econOpenLayer('eco-store', econStoreReopen); }",
    "function econOpenStore(){ CodisCrumb.mark('store:open'); econStoreEnterAt = Date.now(); econOpenLayer('eco-store', econStoreReopen); CodisCrumb.settle(3000); }", 'store open')
rep("  box._codisSig = econStoreSig();", "  box._codisSig = econStoreSig(); CodisCrumb.mark('store:built', box.getElementsByTagName('*').length); CodisCrumb.settle(2000);", 'store built')

# الشراء
rep("    const ok = await codisConfirm(CodisCopy.buy(it.name, econFmt(price), econFmt(data.wallet.balance - price)));\n    if(!ok) return;",
    "    const ok = await codisConfirm(CodisCopy.buy(it.name, econFmt(price), econFmt(data.wallet.balance - price)));\n    if(!ok) return;\n    CodisCrumb.mark('buy:confirmed', price);", 'buy confirmed')
rep("    const r = CodisEconomy.purchase(id);", "    const r = CodisEconomy.purchase(id); CodisCrumb.mark('buy:saved', r && r.ok ? 'ok' : (r && r.reason));", 'buy saved')

# مراحل مشهد الشراء
rep("      const price = Math.max(0, Number(r.price) || 0), lv = CodisRevealLevels.levelOfValue(price), info = CodisRevealLevels.info(lv), rc = R[lv];",
    "      const price = Math.max(0, Number(r.price) || 0), lv = CodisRevealLevels.levelOfValue(price), info = CodisRevealLevels.info(lv), rc = R[lv];\n      CodisCrumb.mark('cine:build', 'lv' + lv);", 'cine build')
rep("      document.body.appendChild(root);",
    "      document.body.appendChild(root);\n      CodisCrumb.mark('cine:shown', 'lv' + lv); requestAnimationFrame(()=>requestAnimationFrame(()=>{ if(s && s.root === root) CodisCrumb.mark('cine:frame', 'lv' + lv); }));", 'cine shown')
rep("  function burst(rc, lite, cx, cy){", "  function burst(rc, lite, cx, cy){\n    CodisCrumb.mark('cine:burst', 'conf' + rc.conf + ' scr' + rc.scraps + ' rain' + rc.rain);", 'cine burst')
rep("        const a = root.querySelector('.bcx-acts'); a.hidden = false; s.acts = true;",
    "        const a = root.querySelector('.bcx-acts'); a.hidden = false; s.acts = true; CodisCrumb.mark('cine:buttons');", 'cine buttons')
rep("    const end = ()=>{ if(fin) return; fin = true; st.tm.forEach(clearTimeout); try{ st.root.remove(); }catch(e){} if(s === st) s = null;",
    "    const end = ()=>{ if(fin) return; fin = true; st.tm.forEach(clearTimeout); try{ st.root.remove(); }catch(e){} if(s === st) s = null; CodisCrumb.idle();", 'cine end')

# المعاينة
rep("    card.classList.add('is-peek'); CodisArt.full(card);   /* CODIS-BUTTER */\n",
    "    card.classList.add('is-peek'); CodisArt.full(card);   /* CODIS-BUTTER */\n    CodisCrumb.mark('peek:open');\n", 'peek open')
rep("      st.ph.remove(); st.ov.remove(); if(s === st) s = null;", "      st.ph.remove(); st.ov.remove(); if(s === st) s = null; CodisCrumb.idle();", 'peek close')

s = s.replace('<meta name="codis-version"', '<!-- CODIS-CRUMBS --><meta name="codis-version"', 1)
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('ok')
