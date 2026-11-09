/* ===== CODIS-AUDIT-V38 · CodisTabGuard — حماية البيانات عند فتح CODIS بأكثر من نافذة/تبويب =====
   المشكلة (مُثبتة بتبويبين حقيقيين): كل نافذة تحمل نسخة بالذاكرة وتكتب كل البيانات فوق localStorage المشترك، فحفظ النافذة القديمة
   كان يمسح تغييرات الأحدث (+100 كوين وسجلّها اختفيا). الحل: «آخر من كتب هو المرجع» — حين تكتب نافذة أخرى، هذه النافذة تتوقف فوراً عن الحفظ
   (أي عملية تفشل بأمان وتتراجع داخل CodisWallet.transact بدل أن تكتب فوق الأحدث) وعن المزامنة (CODIS_SYNC_HOLD)، ثم تُحدَّث:
   مخفية ⇒ تحديث مباشر · ظاهرة ⇒ نافذة واضحة بزر «تحديث الآن». حدث storage لا يصل للنافذة الكاتبة نفسها، فالاستخدام بنافذة واحدة لا يتأثر. */
const CodisTabGuard = (function(){
  let stale = false;
  function lock(){
    if(stale) return; stale = true;
    try{ codisSaveSuspended = 'fail'; }catch(e){}
    try{ window.CODIS_SYNC_HOLD = true; }catch(e){}
    if(document.hidden){ try{ location.reload(); }catch(e){} return; }
    try{
      const el = document.createElement('div');
      el.className = 'codis-stale'; el.setAttribute('role', 'alertdialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('aria-labelledby', 'codis-stale-t'); el.setAttribute('aria-describedby', 'codis-stale-d');
      el.innerHTML = '<div class="codis-stale-card"><b id="codis-stale-t">CODIS مفتوح بنافذة ثانية</b><p id="codis-stale-d">تعدّلت بياناتك من نافذة أخرى. حدّث هذي النافذة حتى تكمل على آخر نسخة — ما راح يضيع شي.</p>' +
        '<button type="button" class="btn btn-primary">تحديث الآن</button></div>';
      el.querySelector('button').addEventListener('click', ()=>location.reload());
      el.addEventListener('keydown', e=>{ if(e.key === 'Tab'){ e.preventDefault(); el.querySelector('button').focus(); } });
      document.body.appendChild(el);
      try{ el.querySelector('button').focus({ preventScroll:true }); }catch(e){}
    }catch(e){ try{ location.reload(); }catch(x){} }
  }
  try{ window.addEventListener('storage', e=>{ if(e.key === STORE_KEY && e.newValue !== null && e.storageArea === window.localStorage) lock(); }); }catch(e){}
  return { isStale:()=>stale, _lock:lock };
})();
