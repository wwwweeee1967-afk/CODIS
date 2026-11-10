/* ===== CODIS-CLOCK (3.26.0) — ساعة التطبيق المنطقية =====
   الفصل المقصود:
   • وقت العمل المنطقي (CodisClock.now/date/iso/day): تعتمد عليه الأيام والخطط والعادات والمكافآت والشهر وانتهاء البطاقات والمؤقتات.
   • وقت النظام الحقيقي (Date.now() مباشرة): جلسة الحساب، المزامنة، الاتصال، مؤقتات الواجهة، الحركة، الإشعارات الفعلية — لا تمرّ بهذه الساعة أبداً.
   في الاستعمال العادي الإزاحة = 0 فتطابق الساعة وقت الجهاز تماماً (لا أثر على أي مستخدم).
   الإزاحة لا تُضبط إلا بعد begin() وهي ترفض أي حساب غير موثَّق كمطوّر (CodisAccount.isAdmin، قرار الخادم) — فشل مغلق.
   لا تُحفظ في أي تخزين: إعادة تحميل الصفحة تعيد الإزاحة إلى 0 دائماً (لا يبقى حساب بوضع اختبار مجهول).
   لا تغيّر Date ولا Date.now ولا ساعة الجهاز. */
const CodisClock = (function(){
  'use strict';
  const realNow = ()=>Date.now();
  let off = 0, simOn = false;
  const verified = ()=>{ try{ return CodisAccount.isAdmin() === true; }catch(e){ return false; } };
  const pad = n=>String(n).padStart(2, '0');
  const keyOf = d=>d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  const now = ()=>realNow() + off;
  const MIN_Y = 2000, MAX_Y = 2200;
  function apply(target){
    const y = target.getFullYear(); if(!isFinite(target.getTime()) || y < MIN_Y || y > MAX_Y) return false;
    off += target.getTime() - now(); return true;
  }
  return Object.freeze({
    now, real:realNow,
    date:()=>new Date(now()),
    iso:()=>new Date(now()).toISOString(),
    day:()=>new Date(now()).getDay(),
    key:()=>keyOf(new Date(now())),
    keyOf,
    offset:()=>off,
    active:()=>simOn,
    /* يبدأ وضع المحاكاة (للمطوّر الموثَّق فقط). يرجع false إن لم يُسمح */
    begin(){ if(!verified()) return false; simOn = true; off = 0; return true; },
    /* ينهي المحاكاة ويعيد الساعة الحقيقية */
    end(){ simOn = false; off = 0; return true; },
    /* تمرير n يوماً تقويمياً (نفس الساعة المحلية — لا يتأثر بتغيّر التوقيت الصيفي) */
    shiftDays(n){
      if(!simOn || !verified()) return false;
      n = Math.trunc(Number(n)); if(!isFinite(n) || n === 0 || Math.abs(n) > 3700) return false;
      const t = new Date(now()); t.setDate(t.getDate() + n); return apply(t);
    },
    /* القفز إلى يوم محدد 'YYYY-MM-DD' (بنفس الساعة المحلية الحالية) */
    setDay(key){
      if(!simOn || !verified()) return false;
      const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(key || '')); if(!m) return false;
      const c = new Date(now()), y = +m[1], mo = +m[2] - 1, d = +m[3];
      const t = new Date(y, mo, d, c.getHours(), c.getMinutes(), c.getSeconds(), c.getMilliseconds());
      if(t.getFullYear() !== y || t.getMonth() !== mo || t.getDate() !== d) return false;   // 31 فبراير وأمثالها
      return apply(t);
    }
  });
})();
