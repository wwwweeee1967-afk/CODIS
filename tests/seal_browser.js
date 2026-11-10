/* CODIS-SEAL (3.27.0): انتحال المطوّر من الكونسول لا يعمل على المضيف المحصَّن.
   التشغيل (لازم PRELOAD يفرض التحصين لأن الاختبار يعمل على 127.0.0.1 حيث الأجسام قابلة للتعديل عمداً):
   PRELOAD='window.CODIS_SEAL_FORCE=true' TEST=tests/seal_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1
   وبدون PRELOAD يفحص الاتجاه المعاكس (الوضع المحلي قابل للتعديل = ما تعتمد عليه الاختبارات الأخرى). */
(async()=>{
  const results = []; const T = (n, ok, d)=>results.push({ name:n, ok:!!ok, detail:d === undefined ? '' : String(d) });
  const sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const forced = window.CODIS_SEAL_FORCE === true;
  try{
    const g = document.getElementById('gate-guest'); if(g && g.offsetParent){ g.click(); await sleep(1200); }
    T('وضع الاختبار: ' + (forced ? 'محصَّن (CODIS_SEAL_FORCE)' : 'محلي'), true);
    if(forced){
      T('CodisAccount مجمَّد', Object.isFrozen(CodisAccount));
      T('CodisAccount._test مجمَّد', Object.isFrozen(CodisAccount._test));
      T('CodisLimits مجمَّد', Object.isFrozen(CodisLimits));
      T('CodisClock مجمَّد', Object.isFrozen(CodisClock));
      /* الهجوم نفسه: استبدال isAdmin ثم سؤال الأنظمة التي تعتمد عليه */
      let threw = null; try{ 'use strict'; CodisAccount.isAdmin = ()=>true; }catch(e){ threw = e; }
      T('استبدال isAdmin لا يغيّر شيئاً', CodisAccount.isAdmin() === false, 'threw=' + (threw && threw.name));
      T('CodisLimits.on() يبقى false', CodisLimits.on() === false);
      T('CodisLimits.bypass() يبقى false', CodisLimits.bypass('buy.insufficient') === false);
      T('CodisLimits.afford يرفض الرصيد الناقص', CodisLimits.afford(1, 100) === false);
      T('CodisLimits.num يعيد القيمة العادية رغم adminOverrides', (()=>{ const o = data.adminOverrides; data.adminOverrides = { constants:{ 'box.price.1':1 } }; const v = CodisLimits.num('box.price.1', 777); data.adminOverrides = o; return v === 777; })());
      try{ CodisLimits.bypass = ()=>true; }catch(e){}
      T('استبدال CodisLimits.bypass لا يغيّر شيئاً', CodisLimits.bypass('x.y') === false);
      T('CodisClock.begin يرفض غير الموثَّق', (()=>{ try{ const r = CodisClock.begin(); return r === false || r === undefined || (r && r.ok === false) || CodisClock.active() === false; }catch(e){ return CodisClock.active() === false; } })(), 'active=' + CodisClock.active());
      /* state للقراءة فقط */
      const st = CodisAccount.state; let before = JSON.stringify(Object.keys(st));
      try{ st.admin = true; st.user = { id:'x', name:'hacker' }; st.session = { access_token:'forged' }; delete st.status; }catch(e){}
      T('CodisAccount.state: الكتابة والحذف مُتجاهَلان', !st.admin && !(st.user && st.user.name === 'hacker') && !(st.session && st.session.access_token === 'forged') && JSON.stringify(Object.keys(st)) === before);
      T('adminCall لا يقبل غير admin_*', await CodisAccount.adminCall('save_progress', {}).then(()=>false, e=>/bad function|not signed in/.test(e.message)));
      T('window.__codisDevLoaded لا يمنح صلاحية', (()=>{ window.__codisDevLoaded = true; const ok = CodisAccount.isAdmin() === false && !window.CodisHub; delete window.__codisDevLoaded; return ok; })());
      T('التطبيق يعمل مختوماً (إقلاع + حفظ)', typeof saveData === 'function' && saveData() !== false);
    }else{
      T('محلي: CodisAccount قابل للتعديل (لازم للاختبارات ووضع المطوّر المحلي)', !Object.isFrozen(CodisAccount));
      T('محلي: CodisLimits قابل للتعديل', !Object.isFrozen(CodisLimits));
    }
  }catch(e){ T('EXCEPTION', false, (e && e.stack) || e); }
  return { results, passed:results.filter(r=>r.ok).length, failed:results.filter(r=>!r.ok).length };
})()
