/* ================= CODIS-V45 — واجهة «سلفني» داخل سجل الكوينز (عرض وربط فقط؛ المنطق كله في CodisLoans) ================= */
let codisLoanBusy = false, codisLoanSheet = null;
const CODIS_LOAN_TYPES = { LOAN_BORROW:1, LOAN_REPAY:1 };
function codisLoanRowCls(t){ return t && t.type === 'LOAN_BORROW' ? ' is-loan is-borrow' : (t && t.type === 'LOAN_REPAY' ? ' is-loan is-repay' : ''); }
function codisTxWord(t, up){ return t && t.type === 'LOAN_BORROW' ? 'سلفة ' : (t && t.type === 'LOAN_REPAY' ? 'سداد دين ' : (up ? 'مكتسب ' : 'مصروف ')); }
function codisLoanRowSub(t){
  if(!t) return '';
  if(t.type === 'LOAN_BORROW') return '<span class="eco-log-sub ecl-loan-tag">سلفني · ليست دخلاً مكتسباً</span>';
  if(t.type === 'LOAN_REPAY') return '<span class="eco-log-sub ecl-loan-tag">سلفني · سداد تلقائي</span>';
  if(t.meta && t.meta.debtPaid > 0) return '<span class="eco-log-sub ecl-loan-tag">حُجز ' + escapeHtml(econFmt(t.meta.debtPaid)) + ' منها لسداد سلفني</span>';
  return '';
}
function codisCoinsCopy(res){
  const dp = res && res.debtPaid > 0 ? res.debtPaid : 0, net = econC(res.amount - dp);
  if(!dp) return '+' + econFmt(res.amount) + ' كوين · الرصيد ' + econFmt(CodisWallet.balance());
  return econFmt(res.amount) + ' كوين: سُدِّد ' + econFmt(dp) + ' من سلفني' + (net > 0 ? ' · أُضيف ' + econFmt(net) + ' لرصيدك' : '') + ' · الرصيد ' + econFmt(CodisWallet.balance());
}
function codisLoanStateText(){
  const s = CodisLoans.state();
  return s === 'clear' ? 'لا دين عليك' : s === 'maxed' ? 'بلغت الحد — يُسدَّد تلقائياً' : 'قيد السداد التلقائي';
}
/* بطاقة «سلفني» داخل سجل الكوينز: زر يفتح الورقة الكاملة */
function codisLoanCardHtml(){
  const d = CodisLoans.debt(), c = CodisLoans.cap(), pct = c > 0 ? Math.min(100, Math.round(d / c * 100)) : 0, st = CodisLoans.state();
  return '<section class="ecl-sec" aria-labelledby="ecl-h-ln"><header class="ecl-sh"><h3 id="ecl-h-ln" class="ecl-h eco-sec-title">سلفني</h3></header>' +
    '<button type="button" class="ln-card is-' + st + '" onclick="codisLoanOpen()" aria-label="سلفني — ' + escapeHtml(codisLoanStateText()) + '">' +
      '<span class="ln-ico" aria-hidden="true">' + codisIcon('loan', { size:'lg' }) + '</span>' +
      '<span class="ln-mid"><b>سلفني</b><small>' + escapeHtml(codisLoanStateText()) + '</small>' +
        '<span class="ln-bar" aria-hidden="true"><i style="width:' + pct + '%"></i></span></span>' +
      '<span class="ln-nums"><b dir="ltr">' + econFmt(d) + '</b><small>من ' + econFmt(c) + '</small></span>' +
    '</button></section>';
}
function codisLoanHistoryHtml(){
  const ev = CodisLoans.events().reverse();
  if(!ev.length) return '<div class="fin-empty">ماكو سلف بعد — أول سلفة تظهر هنا مع كل دفعة تُستقطع.</div>';
  return '<ul class="fin-txs ln-hist">' + ev.slice(0, 60).map(e=>{
    const up = e.kind === 'borrow', d = new Date(e.at), ok = !isNaN(d.getTime());
    return '<li class="fin-tx ' + (up ? 'is-up' : 'is-down') + '"><span class="fin-tx-ic" aria-hidden="true">' + (up ? '↓' : '↑') + '</span><div class="fin-tx-m"><b>' + (up ? 'سلفة مستلمة' : 'سداد تلقائي') + '</b><small>' +
      (ok ? escapeHtml(formatArDate(e.at)) + ' · ' + escapeHtml(d.toLocaleTimeString('ar', { hour:'2-digit', minute:'2-digit' })) : '') + '</small></div>' +
      '<div class="fin-tx-a"><b dir="ltr" class="' + (up ? 'fin-up' : 'fin-down') + '">' + (up ? '+' : '−') + econFmt(e.amount) + '</b></div></li>';
  }).join('') + '</ul>' + (ev.length > 60 ? '<p class="fin-hint">يظهر آخر 60 حدثاً.</p>' : '');
}
function codisLoanSheetBody(){
  const d = CodisLoans.debt(), c = CodisLoans.cap(), room = CodisLoans.room(), s = CodisLoans.sums(), pct = c > 0 ? Math.min(100, Math.round(d / c * 100)) : 0, st = CodisLoans.state();
  return '<div class="ln-hero is-' + st + '"><span class="ln-hero-ico" aria-hidden="true">' + codisIcon('loan', { size:'hero' }) + '</span>' +
      '<div class="ln-hero-t"><small>الدين الحالي</small><b dir="ltr" id="ln-debt">' + econFmt(d) + '</b><span class="ln-state">' + escapeHtml(codisLoanStateText()) + '</span></div></div>' +
    '<div class="ln-meter" role="img" aria-label="استُخدم ' + pct + '٪ من حد الاقتراض"><i style="width:' + pct + '%"></i></div>' +
    '<div class="ln-tiles"><div><small>الحد الأعلى</small><b dir="ltr">' + econFmt(c) + '</b></div><div><small>المتبقي للاقتراض</small><b dir="ltr" id="ln-room">' + econFmt(room) + '</b></div><div><small>إجمالي ما سُدِّد</small><b dir="ltr">' + econFmt(s.repaid) + '</b></div></div>' +
    '<p class="fin-hint">بلا فوائد ولا رسوم. يُسدَّد الدين تلقائياً من أي كوينز جديدة تدخل محفظتك (استبدال مكافأة، بيع، تعويض، منحة)، ولا يُسحب من رصيدك القديم. الكوينز المقترضة ليست دخلاً مكتسباً.</p>' +
    (room > 0 ? '<label class="fin-f"><span>مبلغ السلفة (كوين)</span><div class="fin-amt"><input id="ln-amt" class="fin-in" inputmode="numeric" autocomplete="off" dir="ltr" placeholder="0" maxlength="5"><i>كوين</i></div></label>' +
      '<div class="fin-chips ln-chips" role="group" aria-label="مبالغ سريعة">' + [50, 100, 200].filter(v=>v < room).map(v=>'<button type="button" class="fin-chip" data-v="' + v + '">' + v + '</button>').join('') + '<button type="button" class="fin-chip" data-v="' + room + '">الكل (' + econFmt(room) + ')</button></div>' +
      '<p class="fin-err" role="alert" hidden></p><button type="button" class="btn btn-primary eco-full fin-go" id="ln-go">اطلب السلفة</button>'
      : '<p class="fin-lock">' + codisIcon('warning') + ' وصلت الحد الأعلى للدين — لا اقتراض إضافي حتى يُسدَّد جزء منه تلقائياً من كوينز جديدة.</p>') +
    '<h3 class="fin-sub">سجل السلف والدفعات</h3>' + codisLoanHistoryHtml();
}
function codisLoanFail(r){
  if(!r) return 'تعذّر التنفيذ — ما تغيّر شيء';
  if(r.reason === 'cap') return 'الحد الأعلى للدين ' + econFmt(CodisLoans.cap()) + ' — أقصى ما تقدر تستلمه الآن ' + econFmt(r.room);
  if(r.reason === 'maxed') return 'وصلت الحد الأعلى للدين — سدّد أولاً';
  if(r.reason === 'amount') return 'اكتب عدداً صحيحاً من الكوينز (1 فأكثر)';
  if(r.reason === 'dup') return 'هذي السلفة انسجّلت قبل';
  if(r.reason === 'save') return 'تعذّر الحفظ — ما تغيّر شيء';
  return 'تعذّر التنفيذ — ما تغيّر شيء';
}
function codisLoanPaint(root){
  const sb = root.querySelector('.fin-sb'); if(!sb) return;
  sb.innerHTML = codisLoanSheetBody(); codisHydrateIcons(sb);
  const inp = sb.querySelector('#ln-amt'), go = sb.querySelector('#ln-go'), err = sb.querySelector('.fin-err');
  if(!go) return;
  let rid = econUid('lb');   /* معرّف الطلب: ضغطتان لنفس الطلب = سلفة واحدة؛ يتجدد بعد النجاح أو تغيير المبلغ */
  const show = m=>{ err.textContent = m || ''; err.hidden = !m; if(m) codisSfx('invalid', { ctx:'unavailable' }); };
  inp.addEventListener('input', ()=>{ inp.value = inp.value.replace(/[٠-٩]/g, c=>String(c.charCodeAt(0) - 1632)).replace(/\D/g, '').slice(0, 5); rid = econUid('lb'); show(''); });
  sb.querySelectorAll('.ln-chips .fin-chip').forEach(b=>{ b.onclick = ()=>{ inp.value = b.getAttribute('data-v'); rid = econUid('lb'); show(''); }; });
  go.onclick = ()=>{
    if(codisLoanBusy) return; codisLoanBusy = true; go.disabled = true;
    try{
      const amt = parseInt(inp.value, 10);
      const r = CodisLoans.borrow(isFinite(amt) ? amt : 0, rid);
      if(!r.ok){ show(codisLoanFail(r)); go.disabled = false; return; }
      codisSfx('coins.take', { ctx:'loan' });
      showToast('وصلتك سلفة +' + econFmt(r.amount) + ' كوين — دينك الآن ' + econFmt(r.debt), 'var(--success)', 'check');
      try{ if(econPageVisible('settings-page-eco-log')) econRenderLog(); }catch(e){}
      codisLoanPaint(root);
    }finally{ codisLoanBusy = false; }
  };
}
function codisLoanOpen(){
  if(codisLoanSheet && CodisFinUI.isOpen()) return;
  codisLoanSheet = CodisFinUI.open({ title:'سلفني', cls:'ln-ov', body:'', onClose:()=>{ codisLoanSheet = null; }, mount:root=>codisLoanPaint(root) });
}
