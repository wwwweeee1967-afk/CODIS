/* ================= CODIS-V45 (3.32.0): «سلفني» — اقتراض الكوينز واستقطاع تلقائي =================
   • دفتر القروض `data.loans = { v:1, events:[…] }` دائم ومستقل عن سجل المعاملات المقلَّم (1500): الأحداث لا تُقلَّم ولا تُعدَّل (إلحاق فقط).
       حدث سلفة  { id, kind:'borrow', amount, at, ref:'borrow|<requestId>', tx:<معاملة المحفظة> }
       حدث سداد  { id:'rp|<معرّف معاملة الدخول>', kind:'repay', amount, at, ref:'repay|<معرّف معاملة الدخول>', tx:<معاملة السداد>, from:<معاملة الدخول> }
   • الدين **مشتق دائماً** = Σ السلف − Σ السدادات (لا قيمة مخزّنة تُنسى أو تتكرر). دمج الأجهزة = اتحاد الأحداث بمعرّفاتها (CodisMerge يدمج مصفوفة بـid)،
     فلا تتكرر سلفة/دفعة ولا يعود دين سُدِّد.
   • نقطة التنفيذ المركزية = CodisWallet.apply: أي إضافة موجبة (type ≠ LOAN_BORROW/LOAN_REPAY، وبلا meta.noRepay) تُسدِّد من نفسها فقط
     (min(الدين، مبلغ الإضافة)) داخل **نفس** transact — الرصيد القديم لا يُمسّ. معاملة السداد LOAN_REPAY سالبة وليست مصدراً للسداد (لا حلقة).
   • السلفة LOAN_BORROW موجبة لكنها **لا** ترفع lifetimeEarned (ليست دخلاً مكتسباً).
   • الحدّ 400 يمرّ بـCodisLimits (المطوّر بلا قيود): 'loan.cap' ثابت رقمي + 'loan.limit' منع صارم.
   • كل ما قبل `const CodisLoans` دوال آمنة وقت التحميل (لا تقرأ const ولا data). */

const CODIS_LOAN_CAP = 400;   /* القيمة العادية للحد الأعلى للدين القائم */
function codisLoansNorm(v){
  const out = { v:1, events:[] };
  try{
    if(!v || typeof v !== 'object' || Array.isArray(v) || !Array.isArray(v.events)) return out;
    const ids = {}, refs = {};
    v.events.forEach(function(e){
      if(!e || typeof e !== 'object' || (e.kind !== 'borrow' && e.kind !== 'repay')) return;
      if(typeof e.id !== 'string' || !e.id || e.id.length > 90 || ids[e.id]) return;
      const a = Math.round(Number(e.amount) * 100) / 100;
      if(!isFinite(a) || a <= 0 || a > 1e7) return;
      const ref = (typeof e.ref === 'string' && e.ref.length <= 120) ? e.ref : '';
      if(ref && refs[ref]) return;
      const at = (typeof e.at === 'string' && e.at.length <= 40) ? e.at : '';
      ids[e.id] = 1; if(ref) refs[ref] = 1;
      const o = { id:e.id, kind:e.kind, amount:a, at:at, ref:ref };
      if(typeof e.tx === 'string' && e.tx.length <= 90) o.tx = e.tx;
      if(e.kind === 'repay' && typeof e.from === 'string' && e.from.length <= 90) o.from = e.from;
      out.events.push(o);
    });
  }catch(err){ return { v:1, events:[] }; }
  return out;
}

const CodisLoans = (function(){
  try{
    CodisLimits.reg('loan.cap', 'الحد الأعلى لدين «سلفني» القائم', CODIS_LOAN_CAP);
    CodisLimits.reg('loan.limit', 'منع الاقتراض فوق الحد الأعلى لـ«سلفني»');
  }catch(e){}
  const r2 = x=>Math.round((Number(x) || 0) * 100) / 100;
  function L(){ if(!data.loans || typeof data.loans !== 'object' || !Array.isArray(data.loans.events)) data.loans = { v:1, events:[] }; return data.loans; }
  function sums(){ let b = 0, r = 0; L().events.forEach(e=>{ if(e.kind === 'borrow') b += e.amount; else r += e.amount; }); return { borrowed:r2(b), repaid:r2(r) }; }
  function debt(){ const s = sums(); return Math.max(0, r2(s.borrowed - s.repaid)); }
  function cap(){ return CodisLimits.num('loan.cap', CODIS_LOAN_CAP); }
  function room(){ return Math.max(0, r2(cap() - debt())); }
  function state(){ const d = debt(), c = cap(); return d <= 0 ? 'clear' : (d >= c ? 'maxed' : 'active'); }
  function events(){ return L().events.slice(); }
  /* سلفة جديدة: ذرّية (محفظة + دفتر القروض + حفظ). requestId يمنع التكرار عند إعادة المحاولة */
  function borrow(amount, requestId){
    amount = Number(amount);
    if(!isFinite(amount) || amount < 1 || Math.floor(amount) !== amount || amount > 1e7) return { ok:false, reason:'amount' };
    const rid = String(requestId || econUid('lb')).slice(0, 60), ref = 'borrow|' + rid;
    return CodisWallet.transact([], ()=>{
      const led = L();
      if(led.events.some(e=>e.ref === ref)) return { ok:false, reason:'dup' };
      const left = room();
      if(amount > left && !CodisLimits.bypass('loan.limit')) return { ok:false, reason:left > 0 ? 'cap' : 'maxed', room:left };
      const evId = 'ln_' + rid;
      const tx = CodisWallet.apply('LOAN_BORROW', amount, 'سلفة مستلمة — سلفني', 'loan', ref, { name:'سلفة', loan:evId });
      if(!tx) return { ok:false, reason:'tx' };
      led.events.push({ id:evId, kind:'borrow', amount:r2(amount), at:tx.createdAt, ref:ref, tx:tx.id });
      return { ok:true, tx:tx, amount:amount, debt:debt(), room:room() };
    });
  }
  /* يُستدعى من CodisWallet.apply بعد تسجيل إضافة موجبة. يُسدّد من مبلغ هذه الإضافة فقط ويُرجع مبلغ السداد (أو 0) */
  function repayFrom(tx){
    const d = debt(); if(!(d > 0) || !tx || !(tx.amount > 0)) return 0;
    const evId = 'rp|' + tx.id, ref = 'repay|' + tx.id, led = L();
    if(led.events.some(e=>e.id === evId || e.ref === ref)) return 0;
    const pay = r2(Math.min(d, tx.amount)); if(!(pay > 0)) return 0;
    const rt = CodisWallet.apply('LOAN_REPAY', -pay, 'سداد تلقائي من «سلفني»', 'loan', ref, { name:'سداد سلفة', from:tx.id, fromType:tx.type });
    if(!rt) return 0;
    led.events.push({ id:evId, kind:'repay', amount:pay, at:tx.createdAt, ref:ref, tx:rt.id, from:tx.id });
    tx.meta = Object.assign({}, tx.meta || {}, { debtPaid:pay });
    return pay;
  }
  /* فحص سلامة قابل لإعادة البناء: الدين من الأحداث، ومعاملات المحفظة الحالية (غير المقلَّمة) تطابق الأحداث */
  function verify(){
    const probs = [], led = L(), ids = {}, byTx = {};
    data.wallet.transactions.forEach(t=>{ byTx[t.id] = t; });
    led.events.forEach(e=>{
      if(ids[e.id]) probs.push('حدث مكرر ' + e.id); ids[e.id] = 1;
      const t = e.tx ? byTx[e.tx] : null;
      if(t){
        if(e.kind === 'borrow' && !(t.type === 'LOAN_BORROW' && Math.abs(t.amount - e.amount) < 0.005)) probs.push('سلفة لا تطابق معاملتها ' + e.id);
        if(e.kind === 'repay' && !(t.type === 'LOAN_REPAY' && Math.abs(-t.amount - e.amount) < 0.005)) probs.push('سداد لا يطابق معاملته ' + e.id);
      }
    });
    const s = sums(); if(s.repaid > s.borrowed + 0.005) probs.push('المسدَّد أكبر من المقترَض');
    data.wallet.transactions.forEach(t=>{
      if(t.type === 'LOAN_BORROW' && !led.events.some(e=>e.tx === t.id)) probs.push('معاملة سلفة بلا حدث ' + t.id);
      if(t.type === 'LOAN_REPAY' && !led.events.some(e=>e.tx === t.id)) probs.push('معاملة سداد بلا حدث ' + t.id);
    });
    return { ok:!probs.length, problems:probs, debt:debt(), borrowed:s.borrowed, repaid:s.repaid };
  }
  return { cap, debt, room, state, events, borrow, repayFrom, verify, sums, CAP:CODIS_LOAN_CAP };
})();
