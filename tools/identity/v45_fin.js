/* ================= CODIS-V45 — الإدارة المالية: واجهة رئيسية مختصرة + قائمة جانبية (Modal Drawer) =================
   عرض فقط: كل المنطق المالي كما هو (codisFin*). الرئيسية: بطاقة الرصيد + إيداع/سحب + أحدث الحركات.
   القائمة (يسار الشاشة الفعلي، فوق الواجهة، لا تدفع المحتوى): الملخص والتحليلات + الأدوات والإعدادات. */
let finDrawer = null;
function finDrawerIsOpen(){ return !!finDrawer; }
function finMainHtml(f){
  const bal = codisFinBalance(f), run = codisFinRunning(f).reverse(), fx = codisFinFxStatus();
  return '<div class="fin-bar"><button type="button" class="fin-menu" id="fin-menu" aria-label="قائمة الإدارة المالية" aria-haspopup="dialog" aria-expanded="false" aria-controls="fin-drawer" onclick="finDrawerOpen()">' + codisIcon('menu', { size:'md' }) + '</button>' +
      '<span class="fin-bar-t">دفتر الحسابات</span></div>' +
    '<div class="fin-card" role="group" aria-label="الرصيد المالي"><div class="fin-card-top"><span class="fin-card-brand">CODIS · محفظتي</span><span class="fin-card-chip" aria-hidden="true"></span></div>' +
      '<div class="fin-card-lab">رصيدك الحالي</div><div class="fin-card-bal" dir="ltr"><b id="fin-bal">' + finFmt(bal) + '</b><span>د.ع</span></div>' +
      '<div class="fin-card-foot"><span>الدينار العراقي · IQD</span><span>1 كوين = ' + finFmt(fx.rate || 0) + ' د.ع</span></div></div>' +
    '<div class="fin-actions"><button type="button" class="fin-btn-main is-in" onclick="finDepositOpen()"><span class="fin-act-ic" aria-hidden="true">' + codisIcon('deposit', { size:'lg' }) + '</span><span class="fin-act-t"><b>إيداع</b><small>أضف للمحفظة</small></span></button>' +
      '<button type="button" class="fin-btn-main is-out" onclick="finExpenseOpen()"><span class="fin-act-ic" aria-hidden="true">' + codisIcon('withdraw', { size:'lg' }) + '</span><span class="fin-act-t"><b>مصروف / سحب</b><small>اصرف منها</small></span></button></div>' +
    '<section class="fin-sec"><header class="fin-sec-h"><h3>أحدث الحركات</h3>' + (run.length > 8 ? '<button type="button" class="fin-link" onclick="finAllTx()">كل الحركات (' + finFmt(run.length) + ')</button>' : '') + '</header>' +
      (run.length ? '<ul class="fin-txs">' + run.slice(0, 8).map(finTxRowHtml).join('') + '</ul>' : '<div class="fin-empty">ماكو حركات بعد</div>') + '</section>';
}
function finRender(){
  const box = document.getElementById('fin-body'); if(!box) return;
  const f = codisFin();
  if(!f.setup.done){ if(finDrawer) finDrawerClose(true); finRenderWizard(box); return; }
  box.innerHTML = finMainHtml(f);
  codisHydrateIcons(box);
  if(finDrawer) finDrawerPaint();
}
function finDrawerBodyHtml(){
  const f = codisFin(), per = finRange(finPeriod), st = finStats(f, per[0], per[1]), ns = codisFinNextSalary(f), fx = codisFinFxStatus();
  const seg = '<div class="fin-seg" role="tablist" aria-label="الفترة">' + [['day', 'اليوم'], ['week', 'الأسبوع'], ['month', 'الشهر'], ['all', 'الكل']].map(p=>'<button type="button" role="tab" class="' + (finPeriod === p[0] ? 'is-on' : '') + '" aria-selected="' + (finPeriod === p[0]) + '" onclick="finSetPeriod(\'' + p[0] + '\')">' + p[1] + '</button>').join('') + '</div>';
  const sum = '<div class="fin-sum"><div class="fin-sum-i is-in"><small>إجمالي الدخل</small>' + finIqd(st.income) + '</div><div class="fin-sum-i is-out"><small>إجمالي المصروفات</small>' + finIqd(st.expense) + '</div><div class="fin-sum-i is-net"><small>صافي الحركة</small>' + finIqd(st.net) + '</div></div>';
  const detail = '<div class="fin-kv"><div><span>رواتب</span><b dir="ltr">' + finFmt(st.salary) + '</b></div><div><span>إيداعات</span><b dir="ltr">' + finFmt(st.deposit) + '</b></div><div><span>استبدال مكافآت مالية</span><b dir="ltr">' + finFmt(st.reward) + '</b></div><div><span>عدد الحركات</span><b dir="ltr">' + finFmt(st.n) + '</b></div></div>';
  const rows = '<nav class="fin-rows" aria-label="الأدوات والإعدادات المالية">' +
    finRowHtml('scale', 'سعر صرف الكوينز', '1 كوين = ' + finFmt(fx.rate || 0) + ' د.ع' + (fx.canChange ? '' : ' · تغيّر هذا الشهر'), 'finDrawerGo(finRateOpen)') +
    finRowHtml('calendar', 'إدارة الراتب', f.work === 'employee' ? (f.salary.rules.length ? finFmt(f.salary.rules[f.salary.rules.length - 1].amount) + ' د.ع شهرياً' : 'غير مضبوط') : 'عمل حر — أدخل أرباحك بالإيداع', 'finDrawerGo(finSalaryOpen)') +
    finRowHtml('user', 'ملفي المالي', (f.work === 'employee' ? 'موظف' : 'عمل حر') + (f.source ? ' · ' + f.source : ''), 'finDrawerGo(finProfileOpen)') +
    finRowHtml('report', 'التقارير المالية', 'دخل · مصروفات · تصنيفات · رصيد', 'finDrawerGo(finReportsOpen)') + '</nav>';
  return '<section class="fin-dr-g" aria-labelledby="fin-dr-h1"><h3 class="fin-dr-h" id="fin-dr-h1">الملخص والتحليلات</h3>' + seg + sum + detail +
      (ns ? '<div class="fin-note">' + codisIcon('calendar') + '<span>الراتب القادم <b>' + finFmt(ns.amount) + '</b> د.ع — ' + escapeHtml(finDateAr(ns.due)) + '</span></div>' : '') + '</section>' +
    '<section class="fin-dr-g" aria-labelledby="fin-dr-h2"><h3 class="fin-dr-h" id="fin-dr-h2">الأدوات والإعدادات</h3>' + rows + '</section>';
}
function finDrawerPaint(){
  if(!finDrawer) return; const b = finDrawer.root.querySelector('.fin-dr-body'); if(!b) return;
  b.innerHTML = finDrawerBodyHtml(); codisHydrateIcons(b);
}
function finDrawerOpen(){
  if(finDrawer || CodisFinUI.isOpen()) return;
  const f = codisFin(); if(!f.setup.done) return;
  const btn = document.getElementById('fin-menu'), root = document.createElement('div');
  root.className = 'fin-dr-ov';
  root.innerHTML = '<div class="fin-dr-scrim"></div><aside class="fin-drawer" id="fin-drawer" role="dialog" aria-modal="true" aria-label="قائمة الإدارة المالية" tabindex="-1">' +
    '<header class="fin-dr-top"><h2>الإدارة المالية</h2><button type="button" class="fin-x fin-dr-x" aria-label="إغلاق القائمة">' + codisIcon('close', { size:'md' }) + '</button></header><div class="fin-dr-body"></div></aside>';
  const s = { root:root, btn:btn };
  finDrawer = s; document.body.appendChild(root); finDrawerPaint(); codisHydrateIcons(root);
  if(btn) btn.setAttribute('aria-expanded', 'true');
  root.querySelector('.fin-dr-scrim').addEventListener('click', ()=>finDrawerClose());
  root.querySelector('.fin-dr-x').addEventListener('click', ()=>finDrawerClose());
  root.addEventListener('keydown', e=>{
    if(e.key !== 'Tab') return;
    const f = Array.prototype.filter.call(root.querySelectorAll('button, [href], input, [tabindex]:not([tabindex="-1"])'), x=>!x.disabled && x.offsetParent !== null);
    if(!f.length) return; const a = f[0], z = f[f.length - 1];
    if(e.shiftKey && (document.activeElement === a || document.activeElement === root.querySelector('.fin-drawer'))){ e.preventDefault(); z.focus(); }
    else if(!e.shiftKey && document.activeElement === z){ e.preventDefault(); a.focus(); }
  });
  codisSfx('open', { ctx:'sheet' });
  requestAnimationFrame(()=>{ root.classList.add('is-in'); try{ root.querySelector('.fin-drawer').focus({ preventScroll:true }); }catch(e){} });
}
function finDrawerClose(instant, after){
  const s = finDrawer; if(!s) return; finDrawer = null;
  s.root.classList.remove('is-in'); s.root.classList.add('is-out');
  const done = ()=>{
    try{ s.root.remove(); }catch(e){}
    if(s.btn){ s.btn.setAttribute('aria-expanded', 'false'); try{ if(document.contains(s.btn)) s.btn.focus({ preventScroll:true }); }catch(e){} }
    if(after) after();
  };
  if(instant === true || window.CODIS_REDUCED_MOTION) done(); else setTimeout(done, 280);
}
/* اختيار قسم من القائمة: تُغلق القائمة بسلاسة ثم يُفتح القسم (التركيز يعود لزر القائمة ثم تأخذه الورقة كمُفتح سابق) */
function finDrawerGo(fn){ finDrawerClose(false, ()=>{ try{ fn(); }catch(e){ console.error('finDrawerGo', e); } }); }
function finSetPeriod(p){ finPeriod = p; if(finDrawer) finDrawerPaint(); else finRender(); }
document.addEventListener('keydown', e=>{ if(e.key === 'Escape' && finDrawer && !CodisFinUI.isOpen()){ e.preventDefault(); e.stopPropagation(); finDrawerClose(); } }, true);
