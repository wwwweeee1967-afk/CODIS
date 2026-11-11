/* ================= CODIS-FINANCE — الواجهة (3.28.0) =================
   عرض وربط فقط: كل منطق مالي في v41_core.js (codisFin*). الصفحة طبقة «eco-fin» بنفس نظام طبقة المتجر/سجل الكوينز.
   التواريخ والمواعيد بتوقيت بغداد الحقيقي؛ لا تمرّ بـCodisClock. */
const FIN_RATES_NAMES = { 20:'الأول', 40:'الثاني', 80:'الثالث', 120:'الرابع', 160:'الخامس', 200:'السادس' };
let finPeriod = 'month', finAllLimit = 40, finWiz = null, finSheets = [];
const FIN_MONTHS = ['كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران', 'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول'];

function finFmt(n){ return econFmt(n); }
function finIqd(n){ return '<span class="fin-iqd" dir="ltr"><b>' + finFmt(n) + '</b><i>د.ع</i></span>'; }
function finDateAr(key){ if(!codisFinDateOk(key)) return ''; const p = key.split('-').map(Number); return p[2] + ' ' + FIN_MONTHS[p[1] - 1] + ' ' + p[0]; }
function finMonthAr(mk){ const p = String(mk).split('-').map(Number); return FIN_MONTHS[(p[1] || 1) - 1] + ' ' + p[0]; }
function finCatName(id){ const f = codisFin(); const d = codisFinDefaultCats().concat(f.cats).find(c=>c.id === id); return d ? d.name : (id === 'rewards' ? 'مكافآت مالية' : 'أخرى'); }
/* مبلغ من نص: أرقام عربية/فارسية وفواصل → عدد صحيح موجب، أو null (الدينار بلا كسور) */
function finParseAmt(s){
  let t = String(s == null ? '' : s).replace(/[٠-٩]/g, c=>String(c.charCodeAt(0) - 1632)).replace(/[۰-۹]/g, c=>String(c.charCodeAt(0) - 1776)).replace(/[,٬،\s]/g, '');
  if(!/^\d{1,13}$/.test(t)) return null; const n = parseInt(t, 10); return n > 0 ? n : null;
}
function finAmtInput(el){ const raw = el.value.replace(/[٠-٩]/g, c=>String(c.charCodeAt(0) - 1632)).replace(/[^\d]/g, '').slice(0, 13); el.value = raw ? raw.replace(/\B(?=(\d{3})+(?!\d))/g, ',') : ''; }
function finAmtOf(el){ return el ? finParseAmt(el.value) : null; }

/* ---------- الأوراق السفلية (Sheets) ---------- */
const CodisFinUI = (function(){
  function isOpen(){ return finSheets.length > 0; }
  function el(){ return finSheets.length ? finSheets[finSheets.length - 1].root : null; }
  function close(s){
    s = s || finSheets[finSheets.length - 1]; if(!s) return;
    finSheets = finSheets.filter(x=>x !== s); s.root.classList.add('is-out');
    const done = ()=>{ try{ s.root.remove(); }catch(e){} if(s.onClose) try{ s.onClose(); }catch(e){} try{ if(s.prev && s.prev.focus && document.contains(s.prev)) s.prev.focus({ preventScroll:true }); }catch(e){} };
    if(window.CODIS_REDUCED_MOTION) done(); else setTimeout(done, 200);
  }
  function open(o){
    const root = document.createElement('div'); root.className = 'fin-ov' + (o.cls ? ' ' + o.cls : '');
    root.innerHTML = '<div class="fin-sheet" role="dialog" aria-modal="true" aria-label="' + escapeHtml(o.title || '') + '"><div class="fin-grab" aria-hidden="true"></div><header class="fin-sh"><h2>' + escapeHtml(o.title || '') + '</h2>' +
      '<button type="button" class="fin-x" aria-label="إغلاق">' + codisIcon('close', { size:'md' }) + '</button></header><div class="fin-sb"></div></div>';
    const s = { root:root, prev:document.activeElement, onClose:o.onClose };
    root.addEventListener('mousedown', e=>{ if(e.target === root) close(s); });
    root.querySelector('.fin-x').addEventListener('click', ()=>close(s));
    root.querySelector('.fin-sb').innerHTML = o.body || '';
    document.body.appendChild(root); finSheets.push(s);
    codisHydrateIcons(root); codisSfx('open', { ctx:'sheet' });
    requestAnimationFrame(()=>root.classList.add('is-in'));
    setTimeout(()=>{ const f = root.querySelector('[data-autofocus]'); if(f) try{ f.focus({ preventScroll:true }); }catch(e){} }, 80);
    if(o.mount) o.mount(root, s);
    return s;
  }
  document.addEventListener('keydown', e=>{ if(e.key === 'Escape' && isOpen() && !CodisMotion.isOpen(document.getElementById('codis-confirm-modal'))){ e.preventDefault(); close(); } });
  return { open:open, close:close, closeTop:()=>close(), isOpen:isOpen, el:el };
})();
function finBody(s){ return s.root.querySelector('.fin-sb'); }
function finErr(root, msg){ const e = root.querySelector('.fin-err'); if(e){ e.textContent = msg || ''; e.hidden = !msg; if(msg) codisSfx('invalid', { ctx:'unavailable' }); } }

/* ---------- الصفحة الرئيسية ---------- */
function finOpen(){ econOpenLayer('eco-fin', finRender); }
function finStats(f, from, to){
  const o = { income:0, expense:0, salary:0, deposit:0, reward:0, byCat:{}, n:0 };
  f.ledger.forEach(e=>{
    if(e.type === 'OPENING_BALANCE') return; if(from && e.date < from) return; if(to && e.date > to) return; o.n++;
    if(e.amount > 0){ o.income += e.amount; if(e.type === 'SALARY') o.salary += e.amount; else o.deposit += e.amount; }
    else { const a = -e.amount; o.expense += a; if(e.type === 'REWARD_REDEMPTION') o.reward += a; const k = e.type === 'REWARD_REDEMPTION' ? 'rewards' : (e.cat || 'other'); o.byCat[k] = (o.byCat[k] || 0) + a; }
  });
  o.net = o.income - o.expense; return o;
}
function finWeekStart(key){ const p = key.split('-').map(Number), d = new Date(Date.UTC(p[0], p[1] - 1, p[2])); d.setUTCDate(d.getUTCDate() - d.getUTCDay()); return d.getUTCFullYear() + '-' + codisFinPad(d.getUTCMonth() + 1) + '-' + codisFinPad(d.getUTCDate()); }
function finRange(period){
  const t = codisFinToday();
  if(period === 'day') return [t, t]; if(period === 'week') return [finWeekStart(t), t]; if(period === 'month') return [codisFinMonthOf(t) + '-01', t]; return [null, null];
}
function finTxRowHtml(r){
  const e = r.e, up = e.amount > 0, ico = ({ OPENING_BALANCE:'flag', DEPOSIT:'plus', SALARY:'calendar', EXPENSE:'minus', REWARD_REDEMPTION:'gift' })[e.type] || 'coin';
  return '<li class="fin-tx ' + (up ? 'is-up' : 'is-down') + '"><span class="fin-tx-ic" aria-hidden="true">' + (up ? '↓' : '↑') + '</span><div class="fin-tx-m"><b>' + escapeHtml(e.desc || codisFinTypeLabel(e.type)) + '</b>' +
    '<small>' + escapeHtml(codisFinTypeLabel(e.type)) + (e.type === 'EXPENSE' ? ' · ' + escapeHtml(finCatName(e.cat)) : '') + (e.src && e.type === 'DEPOSIT' ? ' · ' + escapeHtml(e.src) : '') + ' · ' + escapeHtml(finDateAr(e.date)) + (e.type === 'SALARY' && e.due !== e.date ? '' : '') + '</small></div>' +
    '<div class="fin-tx-a"><b dir="ltr" class="' + (up ? 'fin-up' : 'fin-down') + '">' + (up ? '+' : '−') + finFmt(Math.abs(e.amount)) + '</b><small dir="ltr">' + finFmt(r.bal) + '</small></div></li>';
}
function finRender(){
  const box = document.getElementById('fin-body'); if(!box) return;
  const f = codisFin();
  if(!f.setup.done){ finRenderWizard(box); return; }
  const bal = codisFinBalance(f), per = finRange(finPeriod), st = finStats(f, per[0], per[1]), run = codisFinRunning(f).reverse();
  const ns = codisFinNextSalary(f), fx = codisFinFxStatus();
  box.innerHTML =
    '<div class="fin-card" role="group" aria-label="الرصيد المالي"><div class="fin-card-top"><span class="fin-card-brand">CODIS · محفظتي</span><span class="fin-card-chip" aria-hidden="true"></span></div>' +
      '<div class="fin-card-lab">رصيدك الحالي</div><div class="fin-card-bal" dir="ltr"><b id="fin-bal">' + finFmt(bal) + '</b><span>د.ع</span></div>' +
      '<div class="fin-card-foot"><span>الدينار العراقي · IQD</span><span>1 كوين = ' + finFmt(fx.rate || 0) + ' د.ع</span></div></div>' +
    '<div class="fin-actions"><button type="button" class="fin-btn-main is-in" onclick="finDepositOpen()">' + codisIcon('plus') + '<span>إيداع</span></button><button type="button" class="fin-btn-main is-out" onclick="finExpenseOpen()">' + codisIcon('minus') + '<span>مصروف / سحب</span></button></div>' +
    '<div class="fin-seg" role="tablist" aria-label="الفترة">' + [['day', 'اليوم'], ['week', 'الأسبوع'], ['month', 'الشهر'], ['all', 'الكل']].map(p=>'<button type="button" role="tab" class="' + (finPeriod === p[0] ? 'is-on' : '') + '" aria-selected="' + (finPeriod === p[0]) + '" onclick="finSetPeriod(\'' + p[0] + '\')">' + p[1] + '</button>').join('') + '</div>' +
    '<div class="fin-sum"><div class="fin-sum-i is-in"><small>إجمالي الدخل</small>' + finIqd(st.income) + '</div><div class="fin-sum-i is-out"><small>إجمالي المصروفات</small>' + finIqd(st.expense) + '</div><div class="fin-sum-i is-net"><small>صافي الحركة</small>' + finIqd(st.net) + '</div></div>' +
    (ns ? '<div class="fin-note">' + codisIcon('calendar') + '<span>الراتب القادم <b>' + finFmt(ns.amount) + '</b> د.ع — ' + escapeHtml(finDateAr(ns.due)) + '</span></div>' : '') +
    '<section class="fin-sec"><header class="fin-sec-h"><h3>أحدث الحركات</h3>' + (run.length > 8 ? '<button type="button" class="fin-link" onclick="finAllTx()">كل الحركات (' + finFmt(run.length) + ')</button>' : '') + '</header>' +
      (run.length ? '<ul class="fin-txs">' + run.slice(0, 8).map(finTxRowHtml).join('') + '</ul>' : '<div class="fin-empty">ماكو حركات بعد</div>') + '</section>' +
    '<nav class="fin-rows" aria-label="أقسام الإدارة المالية">' +
      finRowHtml('scale', 'سعر صرف الكوينز', '1 كوين = ' + finFmt(fx.rate || 0) + ' د.ع' + (fx.canChange ? '' : ' · تغيّر هذا الشهر'), 'finRateOpen()') +
      finRowHtml('calendar', 'إدارة الراتب', f.work === 'employee' ? (f.salary.rules.length ? finFmt(f.salary.rules[f.salary.rules.length - 1].amount) + ' د.ع شهرياً' : 'غير مضبوط') : 'عمل حر — أدخل أرباحك بالإيداع', 'finSalaryOpen()') +
      finRowHtml('user', 'ملفي المالي', (f.work === 'employee' ? 'موظف' : 'عمل حر') + (f.source ? ' · ' + f.source : ''), 'finProfileOpen()') +
      finRowHtml('report', 'التقارير المالية', 'دخل · مصروفات · تصنيفات · رصيد', 'finReportsOpen()') +
    '</nav>' +
    (f.work === 'freelance' ? '' : '');
  codisHydrateIcons(box);
}
function finRowHtml(ic, t, s, fn){ return '<button type="button" class="fin-row" onclick="' + fn + '"><span class="fin-row-ic">' + codisIcon(ic) + '</span><span class="fin-row-t"><b>' + t + '</b><small>' + escapeHtml(s) + '</small></span><svg class="ios-chevron fin-row-ch" data-icon="back" aria-hidden="true"></svg></button>'; }
function finSetPeriod(p){ finPeriod = p; finRender(); }
function finRefresh(){ try{ finRender(); }catch(e){ console.error('finRender', e); } try{ finTopbar(); }catch(e){} }
function finAllTx(){
  const run = codisFinRunning().reverse();
  const s = CodisFinUI.open({ title:'كل الحركات', body:'<ul class="fin-txs" id="fin-all"></ul><button type="button" class="fin-more btn btn-secondary eco-full" hidden>عرض المزيد</button>', mount:(root)=>{
    let n = 30; const ul = root.querySelector('#fin-all'), more = root.querySelector('.fin-more');
    const paint = ()=>{ ul.innerHTML = run.slice(0, n).map(finTxRowHtml).join('') || '<li class="fin-empty">ماكو حركات</li>'; more.hidden = n >= run.length; more.textContent = 'عرض المزيد · باقي ' + finFmt(run.length - n); };
    more.onclick = ()=>{ n += 40; paint(); }; paint();
  } });
  return s;
}

/* ---------- نماذج الإيداع والمصروف ---------- */
function finFieldAmt(id, lab, val){ return '<label class="fin-f"><span>' + lab + '</span><div class="fin-amt"><input id="' + id + '" class="fin-in" inputmode="numeric" autocomplete="off" dir="ltr" placeholder="0" value="' + (val || '') + '" oninput="finAmtInput(this)" data-autofocus><i>د.ع</i></div></label>'; }
function finDepositOpen(){
  const f = codisFin(); if(!f.setup.done){ finRender(); return; }
  const ref = codisFinUid('dep');
  CodisFinUI.open({ title:'إيداع', body:
    finFieldAmt('fd-amt', 'المبلغ بالدينار العراقي') +
    '<label class="fin-f"><span>مصدر الدخل</span><input id="fd-src" class="fin-in" maxlength="80" placeholder="مثلاً: ربح مشروع، هدية، مبيعات" autocomplete="off"></label>' +
    '<label class="fin-f"><span>اسم العملية</span><input id="fd-desc" class="fin-in" maxlength="120" placeholder="مثلاً: ربح صافٍ" autocomplete="off"></label>' +
    '<label class="fin-f"><span>التاريخ</span><input id="fd-date" class="fin-in" type="date" value="' + codisFinToday() + '" max="' + codisFinToday() + '"></label>' +
    '<label class="fin-f"><span>ملاحظات (اختياري)</span><textarea id="fd-note" class="fin-in" rows="2" maxlength="300"></textarea></label>' +
    '<p class="fin-err" role="alert" hidden></p><button type="button" class="btn btn-primary eco-full fin-go" id="fd-go">تسجيل الإيداع</button>',
    mount:(root, s)=>{
      root.querySelector('#fd-go').onclick = ()=>{
        const amt = finAmtOf(root.querySelector('#fd-amt')); if(!amt) return finErr(root, 'اكتب مبلغاً صحيحاً (دينار بلا كسور)');
        const desc = root.querySelector('#fd-desc').value.trim() || root.querySelector('#fd-src').value.trim(); if(!desc) return finErr(root, 'اكتب اسم العملية أو مصدر الدخل');
        const r = codisFinDepositNow({ amount:amt, desc:desc, src:root.querySelector('#fd-src').value, date:root.querySelector('#fd-date').value, note:root.querySelector('#fd-note').value, ref:ref });
        if(!r.ok) return finErr(root, finFailText(r));
        codisSfx('coins.take', { ctx:'deposit' }); CodisFinUI.close(s); showToast('تم الإيداع +' + finFmt(amt) + ' د.ع — رصيدك الآن ' + finFmt(r.balance) + ' د.ع', 'var(--success)', 'check'); finRefresh();
      };
    } });
}
function finFailText(r){
  return ({ amount:'المبلغ غير صالح', date:'التاريخ غير صالح', future:'لا يمكن تسجيل عملية بتاريخ مستقبلي', desc:'اكتب الاسم', funds:'رصيدك لا يكفي — ينقصك ' + finFmt(r.need || 0) + ' د.ع (رصيدك ' + finFmt(r.balance || 0) + ')',
    dup:'هذي العملية انسجّلت قبل', save:'تعذّر الحفظ — ما تغيّر شيء', error:'تعذّر التنفيذ — ما تغيّر شيء', nosetup:'أكمل إعداد الإدارة المالية أولاً', monthly:'سعر الصرف يتغيّر مرة واحدة بالشهر', rate:'سعر غير معتمد', same:'هذا هو السعر الحالي' })[r.reason] || 'تعذّر التنفيذ';
}
function finExpenseOpen(){
  const f = codisFin(); if(!f.setup.done){ finRender(); return; }
  const ref = codisFinUid('exp'), cats = codisFinDefaultCats().concat(f.cats); let sel = 'food';
  CodisFinUI.open({ title:'تسجيل مصروف / سحب', body:
    '<div class="fin-bal-line">رصيدك الحالي ' + finIqd(codisFinBalance(f)) + '</div>' +
    '<label class="fin-f"><span>اسم المصروف</span><input id="fe-name" class="fin-in" maxlength="120" placeholder="مثلاً: مسواك، طماطم" autocomplete="off" data-autofocus></label>' +
    finFieldAmt('fe-amt', 'المبلغ بالدينار العراقي').replace(' data-autofocus', '') +
    '<div class="fin-f"><span>التصنيف</span><div class="fin-chips" id="fe-cats" role="radiogroup" aria-label="التصنيف"></div>' +
      '<div class="fin-addcat"><input id="fe-newcat" class="fin-in" maxlength="40" placeholder="تصنيف جديد" autocomplete="off"><button type="button" class="btn btn-secondary" id="fe-addcat">إضافة</button></div></div>' +
    '<label class="fin-f"><span>التاريخ</span><input id="fe-date" class="fin-in" type="date" value="' + codisFinToday() + '" max="' + codisFinToday() + '"></label>' +
    '<label class="fin-f"><span>ملاحظات (اختياري)</span><textarea id="fe-note" class="fin-in" rows="2" maxlength="300"></textarea></label>' +
    '<p class="fin-err" role="alert" hidden></p><button type="button" class="btn btn-primary eco-full fin-go" id="fe-go">تسجيل المصروف</button>',
    mount:(root, s)=>{
      const paintCats = ()=>{ const all = codisFinDefaultCats().concat(codisFin().cats); root.querySelector('#fe-cats').innerHTML = all.map(c=>'<button type="button" role="radio" aria-checked="' + (sel === c.id) + '" class="fin-chip' + (sel === c.id ? ' is-on' : '') + '" data-c="' + escapeHtml(c.id) + '">' + escapeHtml(c.name) + '</button>').join(''); };
      paintCats();
      root.querySelector('#fe-cats').onclick = e=>{ const b = e.target.closest('[data-c]'); if(!b) return; sel = b.dataset.c; paintCats(); };
      root.querySelector('#fe-addcat').onclick = ()=>{
        const nm = root.querySelector('#fe-newcat').value.trim(); if(!nm) return;
        const id = 'c_' + (econHash(codisFinNormText(nm)) || '0').slice(0, 8);
        const r = codisFinTx(()=>{ const ff = codisFin(); if(ff.cats.some(c=>c.id === id) || codisFinDefaultCats().some(c=>codisFinNormText(c.name) === codisFinNormText(nm))) return { ok:true, noop:true }; if(ff.cats.length >= 30) return { ok:false, reason:'full' }; ff.cats.push({ id:id, name:nm.slice(0, 40) }); return { ok:true }; });
        if(!r.ok) return finErr(root, r.reason === 'full' ? 'وصلت حد التصنيفات المخصصة' : finFailText(r));
        sel = id; root.querySelector('#fe-newcat').value = ''; paintCats(); finErr(root, '');
      };
      root.querySelector('#fe-go').onclick = ()=>{
        const amt = finAmtOf(root.querySelector('#fe-amt')), name = root.querySelector('#fe-name').value.trim();
        if(!name) return finErr(root, 'اكتب اسم المصروف'); if(!amt) return finErr(root, 'اكتب مبلغاً صحيحاً (دينار بلا كسور)');
        const r = codisFinExpenseNow({ name:name, amount:amt, cat:sel, date:root.querySelector('#fe-date').value, note:root.querySelector('#fe-note').value, ref:ref });
        if(!r.ok) return finErr(root, finFailText(r));
        codisSfx('coins.take', { ctx:'expense' }); CodisFinUI.close(s); showToast('تم تسجيل المصروف −' + finFmt(amt) + ' د.ع — رصيدك الآن ' + finFmt(r.balance) + ' د.ع', 'var(--success)', 'check'); finRefresh();
      };
    } });
}

/* ---------- سعر الصرف ---------- */
function finRateOptionsHtml(sel){
  return '<div class="fin-rates" role="radiogroup" aria-label="سعر صرف الكوين">' + codisFinRates().map(r=>'<button type="button" role="radio" aria-checked="' + (sel === r) + '" class="fin-rate' + (sel === r ? ' is-on' : '') + '" data-r="' + r + '"><b>' + (FIN_RATES_NAMES[r]) + '</b>' +
    '<span>1 كوين = <em dir="ltr">' + finFmt(r) + '</em> د.ع</span><span>25 كوين = <em dir="ltr">' + finFmt(r * 25) + '</em> د.ع</span></button>').join('') + '</div>';
}
function finRateOpen(){
  const f = codisFin(), st = codisFinFxStatus(); let sel = f.fx.rate;
  const noteHtml = '<p class="fin-hint">القيمة بالدينار هي الأصل: عند تغيير السعر تبقى قيمة كل مكافأة مالية بالدينار كما هي وتتغير قيمتها بالكوين وفئتها. <b>1 كوين = دقيقتان</b> ثابت ولا يتأثر بالسعر.</p>';
  CodisFinUI.open({ title:'سعر صرف الكوينز', body:noteHtml + finRateOptionsHtml(sel) +
    '<p class="fin-lock" ' + (st.canChange ? 'hidden' : '') + '>' + codisIcon('hourglass') + ' غيّرت السعر هذا الشهر — التغيير القادم متاح ابتداءً من <b>' + escapeHtml(finDateAr(st.nextAllowed)) + '</b></p>' +
    '<p class="fin-err" role="alert" hidden></p><button type="button" class="btn btn-primary eco-full fin-go" id="fr-go" ' + (st.canChange ? '' : 'disabled') + '>تطبيق السعر</button>',
    mount:(root, s)=>{
      const pk = root.querySelector('.fin-rates');
      pk.onclick = e=>{ const b = e.target.closest('[data-r]'); if(!b) return; sel = Number(b.dataset.r); pk.querySelectorAll('.fin-rate').forEach(x=>{ const on = Number(x.dataset.r) === sel; x.classList.toggle('is-on', on); x.setAttribute('aria-checked', on); }); };
      root.querySelector('#fr-go').onclick = async ()=>{
        if(sel === f.fx.rate) return finErr(root, 'هذا هو السعر الحالي');
        const n = data.settings.rewardItems.filter(x=>x && x.fin && x.fin.kind === 'financial').length;
        const ok = await codisConfirm({ title:'تغيير سعر الصرف؟', message:'تقدر تغيّر السعر مرة وحدة فقط بالشهر.', rows:[['السعر الحالي', '1 كوين = ' + finFmt(f.fx.rate) + ' د.ع'], ['السعر الجديد', '1 كوين = ' + finFmt(sel) + ' د.ع', true], ['مكافآت مالية يُعاد تسعيرها', finFmt(n)]],
          detail:'قيمة المكافآت المالية بالدينار تبقى كما هي، وقيمتها بالكوين وفئتها تُعاد حسب السعر الجديد. السجلات القديمة لا تتغير.', icon:'scale', confirmText:'غيّر السعر', danger:false });
        if(!ok) return;
        const r = codisFinChangeRate(sel); if(!r.ok) return finErr(root, finFailText(r));
        CodisFinUI.close(s); codisSfx('confirm', { ctx:'switch' });
        showToast('السعر الآن 1 كوين = ' + finFmt(sel) + ' د.ع' + (r.repriced && r.repriced.moved ? ' — انتقلت ' + finFmt(r.repriced.moved) + ' مكافأة لفئة أنسب' : ''), 'var(--success)', 'check'); finRefresh(); try{ econRenderAll(); }catch(e){}
      };
    } });
}

/* ---------- الراتب ---------- */
function finSalaryOpen(){
  const f = codisFin(); if(f.work !== 'employee'){ return CodisFinUI.open({ title:'الدخل', body:'<p class="fin-hint">حسابك «عمل حر»: لا يُضاف راتب تلقائي. سجّل أرباحك الفعلية من زر <b>إيداع</b> وقت حصولك عليها.' + (f.avgIncome ? ' المتوسط التقديري الذي كتبته (' + finFmt(f.avgIncome) + ' د.ع) للعلم فقط ولا يُضاف للرصيد.' : '') + '</p>' }); }
  const rules = f.salary.rules, cur = rules[rules.length - 1], ns = codisFinNextSalary(f), nextMonth = codisFinMonthStart(codisFinNextMonth(codisFinMonthOf(codisFinToday())));
  const pays = codisFinSorted(f).filter(e=>e.type === 'SALARY').reverse().slice(0, 6);
  CodisFinUI.open({ title:'إدارة الراتب', body:
    '<div class="fin-note">' + codisIcon('calendar') + '<span>' + (cur ? 'الراتب الحالي <b>' + finFmt(cur.amount) + '</b> د.ع — يوم <b>' + cur.day + '</b> من كل شهر' : 'لا يوجد راتب مضبوط') + (ns ? '<br>الاستحقاق القادم: ' + escapeHtml(finDateAr(ns.due)) : '') + '</span></div>' +
    '<h3 class="fin-sub">تعديل الراتب</h3><p class="fin-hint">التعديل يسري على الاستحقاقات من التاريخ الذي تختاره فقط؛ الرواتب المسجّلة سابقاً لا تتغير. اكتب 0 لإيقاف الراتب.</p>' +
    finFieldAmt('fs-amt', 'الراتب الشهري الجديد', cur ? String(cur.amount).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : '').replace(' data-autofocus', '') +
    '<label class="fin-f"><span>يوم نزول الراتب (1–31)</span><input id="fs-day" class="fin-in" type="number" min="1" max="31" inputmode="numeric" value="' + (cur ? cur.day : 1) + '" dir="ltr"></label>' +
    '<label class="fin-f"><span>يسري من تاريخ</span><input id="fs-from" class="fin-in" type="date" min="' + codisFinToday() + '" value="' + nextMonth + '"></label>' +
    '<p class="fin-err" role="alert" hidden></p><button type="button" class="btn btn-primary eco-full fin-go" id="fs-go">حفظ التعديل</button>' +
    (pays.length ? '<h3 class="fin-sub">آخر الرواتب</h3><ul class="fin-txs">' + pays.map(e=>finTxRowHtml({ e:e, bal:0 }).replace(/<small dir="ltr">[^<]*<\/small>/, '')).join('') + '</ul>' : ''),
    mount:(root, s)=>{
      root.querySelector('#fs-go').onclick = ()=>{
        const raw = root.querySelector('#fs-amt').value.replace(/[^\d٠-٩]/g, ''), amt = raw === '' ? null : (finParseAmt(raw) === null ? (/^[0٠]+$/.test(raw) ? 0 : null) : finParseAmt(raw));
        if(amt === null) return finErr(root, 'اكتب راتباً صحيحاً (أو 0 للإيقاف)');
        const r = codisFinSetSalary({ amount:amt, day:Number(root.querySelector('#fs-day').value), from:root.querySelector('#fs-from').value });
        if(!r.ok) return finErr(root, ({ day:'اليوم بين 1 و31', past:'التاريخ لا يكون في الماضي' })[r.reason] || finFailText(r));
        CodisFinUI.close(s); codisSfx('confirm', { ctx:'switch' }); showToast('انحفظ تعديل الراتب' + (r.added ? ' (+' + r.added + ' استحقاق)' : ''), 'var(--success)', 'check'); finRefresh();
      };
    } });
}

/* ---------- الملف المالي ---------- */
function finProfileOpen(){
  const f = codisFin(); let work = f.work || 'freelance'; const nextMonth = codisFinMonthStart(codisFinNextMonth(codisFinMonthOf(codisFinToday())));
  CodisFinUI.open({ title:'ملفي المالي', body:
    '<div class="fin-f"><span>طبيعة العمل</span><div class="fin-chips" id="fp-work" role="radiogroup" aria-label="طبيعة العمل"></div></div>' +
    '<div id="fp-emp" hidden>' + (f.salary.rules.length ? '<p class="fin-hint">الراتب يُعدَّل من «إدارة الراتب».</p>' :
      finFieldAmt('fp-amt', 'الراتب الشهري').replace(' data-autofocus', '') + '<label class="fin-f"><span>يوم نزول الراتب (1–31)</span><input id="fp-day" class="fin-in" type="number" min="1" max="31" dir="ltr" value="5"></label>' +
      '<label class="fin-f"><span>يسري من تاريخ</span><input id="fp-from" class="fin-in" type="date" min="' + codisFinToday() + '" value="' + nextMonth + '"></label>') + '</div>' +
    '<div id="fp-free" hidden><label class="fin-f"><span>طبيعة مصدر الدخل</span><input id="fp-src" class="fin-in" maxlength="80" value="' + escapeHtml(f.source) + '"></label>' +
      '<label class="fin-f"><span>متوسط الدخل التقديري (للعلم فقط)</span><div class="fin-amt"><input id="fp-avg" class="fin-in" inputmode="numeric" dir="ltr" value="' + (f.avgIncome ? String(f.avgIncome).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : '') + '" oninput="finAmtInput(this)"><i>د.ع</i></div></label></div>' +
    '<p class="fin-err" role="alert" hidden></p><button type="button" class="btn btn-primary eco-full fin-go" id="fp-go">حفظ</button>',
    mount:(root, s)=>{
      const paint = ()=>{ root.querySelector('#fp-work').innerHTML = [['employee', 'موظف'], ['freelance', 'عمل حر']].map(w=>'<button type="button" role="radio" aria-checked="' + (work === w[0]) + '" class="fin-chip' + (work === w[0] ? ' is-on' : '') + '" data-w="' + w[0] + '">' + w[1] + '</button>').join(''); root.querySelector('#fp-emp').hidden = work !== 'employee'; root.querySelector('#fp-free').hidden = work === 'employee'; };
      paint(); root.querySelector('#fp-work').onclick = e=>{ const b = e.target.closest('[data-w]'); if(b){ work = b.dataset.w; paint(); } };
      root.querySelector('#fp-go').onclick = ()=>{
        const o = { work:work, source:(root.querySelector('#fp-src') || {}).value, avg:finAmtOf(root.querySelector('#fp-avg')) };
        if(work === 'employee' && !f.salary.rules.length) o.salary = { amount:finAmtOf(root.querySelector('#fp-amt')), day:Number(root.querySelector('#fp-day').value), from:root.querySelector('#fp-from').value };
        const r = codisFinSetProfile(o); if(!r.ok) return finErr(root, ({ amount:'اكتب راتباً ويوماً صحيحين', date:'التاريخ غير صالح', past:'التاريخ لا يكون في الماضي' })[r.reason] || finFailText(r));
        CodisFinUI.close(s); codisSfx('confirm', { ctx:'switch' }); showToast('انحفظ ملفك المالي', 'var(--success)', 'check'); finRefresh();
      };
    } });
}

/* ---------- التقارير المالية ---------- */
function finSparkSvg(vals){
  if(vals.length < 2) return '';
  const W = 300, H = 70, mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals), rg = (mx - mn) || 1;
  const pts = vals.map((v, i)=>(i / (vals.length - 1) * W).toFixed(1) + ',' + (H - 6 - (v - mn) / rg * (H - 12)).toFixed(1)).join(' ');
  return '<svg class="fin-spark" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" aria-label="تسلسل الرصيد عبر الزمن"><polyline points="' + pts + '" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>';
}
function finReportsOpen(){
  const f = codisFin(), v = codisFinVerify(f), run = codisFinRunning(f), t = codisFinToday();
  const rows = [['اليوم', finRange('day')], ['هذا الأسبوع', finRange('week')], ['هذا الشهر', finRange('month')], ['الكل', [null, null]]];
  const cat = finStats(f, finRange('month')[0], t), cats = Object.keys(cat.byCat).map(k=>[k, cat.byCat[k]]).sort((a, b)=>b[1] - a[1]), tot = cat.expense || 1;
  const mx = Math.max.apply(null, cats.map(c=>c[1]).concat([1]));
  CodisFinUI.open({ title:'التقارير المالية', cls:'is-wide', body:
    '<div class="fin-tbl" role="table" aria-label="الدخل والمصروفات"><div class="fin-tr fin-th" role="row"><span></span><span>دخل</span><span>مصروف</span><span>صافي</span></div>' +
      rows.map(r=>{ const s = finStats(f, r[1][0], r[1][1]); return '<div class="fin-tr" role="row"><span>' + r[0] + '</span><span class="fin-up" dir="ltr">' + finFmt(s.income) + '</span><span class="fin-down" dir="ltr">' + finFmt(s.expense) + '</span><b dir="ltr">' + finFmt(s.net) + '</b></div>'; }).join('') + '</div>' +
    '<h3 class="fin-sub">المصروفات حسب التصنيف — هذا الشهر</h3>' + (cats.length ? '<ul class="fin-bars">' + cats.map(c=>'<li><div><span>' + escapeHtml(finCatName(c[0])) + '</span><b dir="ltr">' + finFmt(c[1]) + '</b></div><i style="--w:' + Math.round(c[1] / mx * 100) + '%" aria-hidden="true"></i><small>' + Math.round(c[1] / tot * 100) + '%</small></li>').join('') + '</ul>' : '<div class="fin-empty">ماكو مصروفات هذا الشهر</div>') +
    '<h3 class="fin-sub">مصروفات المكافآت المالية</h3><p class="fin-hint">الإجمالي: ' + finIqd(finStats(f, null, null).reward) + ' · هذا الشهر: ' + finIqd(cat.reward) + '</p>' +
    '<h3 class="fin-sub">تسلسل الرصيد</h3>' + (run.length > 1 ? finSparkSvg(run.slice(-60).map(r=>r.bal)) : '<div class="fin-empty">يلزم حركتان على الأقل</div>') +
    '<h3 class="fin-sub">الرواتب والإيداعات</h3>' + (function(){ const l = run.filter(r=>r.e.type === 'SALARY' || r.e.type === 'DEPOSIT').reverse().slice(0, 12); return l.length ? '<ul class="fin-txs">' + l.map(finTxRowHtml).join('') + '</ul>' : '<div class="fin-empty">ماكو رواتب أو إيداعات بعد</div>'; })() +
    '<h3 class="fin-sub">تحقق الدفتر</h3><div class="fin-verify ' + (v.ok ? 'is-ok' : 'is-bad') + '" role="status"><span dir="ltr">' + finFmt(v.opening) + ' + ' + finFmt(v.deposits + v.salary) + ' − ' + finFmt(v.expenses) + ' − ' + finFmt(v.redemptions) + ' = ' + finFmt(v.expected) + '</span><b>' + (v.ok ? 'يطابق الرصيد المعروض ✓' : 'عدم تطابق!') + '</b></div>' });
}

/* ---------- التهيئة الأولية (استبيان متتابع) ---------- */
function finWizNew(){
  return { step:0, work:null, source:'', avg:'', opening:'', salary:'', day:'5', start:codisFinToday(), rate:null, err:'' };
}
function finRenderWizard(box){
  if(!finWiz) finWiz = finWizNew(); const w = finWiz, steps = 4;
  const bar = '<div class="fin-prog" role="progressbar" aria-valuemin="1" aria-valuemax="' + steps + '" aria-valuenow="' + (w.step + 1) + '"><i style="--p:' + ((w.step + 1) / steps * 100) + '%"></i></div><div class="fin-prog-t">الخطوة ' + (w.step + 1) + ' من ' + steps + '</div>';
  let h = '';
  if(w.step === 0){
    h = '<h2 class="fin-wq">هل أنت موظف أم تعمل عملاً حراً (كاسب)؟</h2><div class="fin-opts">' +
      '<button type="button" class="fin-opt' + (w.work === 'employee' ? ' is-on' : '') + '" onclick="finWizSet(\'work\',\'employee\')">' + codisIcon('calendar', { size:'lg' }) + '<b>موظف</b><small>راتب شهري بتاريخ ثابت</small></button>' +
      '<button type="button" class="fin-opt' + (w.work === 'freelance' ? ' is-on' : '') + '" onclick="finWizSet(\'work\',\'freelance\')">' + codisIcon('star', { size:'lg' }) + '<b>عمل حر</b><small>دخل غير منتظم تسجّله بنفسك</small></button></div>';
  } else if(w.step === 1){
    const common = '<label class="fin-f"><span>رصيدك المالي الحالي الذي تريد البدء منه (اكتب 0 إن لم يكن لديك)</span><div class="fin-amt"><input id="fw-open" class="fin-in" inputmode="numeric" dir="ltr" autocomplete="off" placeholder="0" value="' + escapeHtml(w.opening) + '" oninput="finAmtInput(this);finWiz.opening=this.value"><i>د.ع</i></div></label>';
    if(w.work === 'employee') h = '<h2 class="fin-wq">بيانات الراتب</h2>' +
      '<label class="fin-f"><span>الراتب الشهري</span><div class="fin-amt"><input id="fw-sal" class="fin-in" inputmode="numeric" dir="ltr" autocomplete="off" placeholder="600,000" value="' + escapeHtml(w.salary) + '" oninput="finAmtInput(this);finWiz.salary=this.value"><i>د.ع</i></div></label>' +
      '<label class="fin-f"><span>يوم نزول الراتب من كل شهر (1–31)</span><input id="fw-day" class="fin-in" type="number" min="1" max="31" inputmode="numeric" dir="ltr" value="' + escapeHtml(w.day) + '" oninput="finWiz.day=this.value"></label>' +
      '<label class="fin-f"><span>تاريخ بداية الاستحقاق</span><input id="fw-start" class="fin-in" type="date" value="' + escapeHtml(w.start) + '" onchange="finWiz.start=this.value;finWizPreview()"></label><p class="fin-hint" id="fw-prev"></p>' + common;
    else h = '<h2 class="fin-wq">بيانات دخلك</h2>' +
      '<label class="fin-f"><span>طبيعة مصدر الدخل</span><input id="fw-src" class="fin-in" maxlength="80" placeholder="مثلاً: مبيعات، تصميم، توصيل" autocomplete="off" value="' + escapeHtml(w.source) + '" oninput="finWiz.source=this.value"></label>' +
      '<label class="fin-f"><span>متوسط الدخل التقديري (اختياري)</span><div class="fin-amt"><input id="fw-avg" class="fin-in" inputmode="numeric" dir="ltr" autocomplete="off" placeholder="—" value="' + escapeHtml(w.avg) + '" oninput="finAmtInput(this);finWiz.avg=this.value"><i>د.ع</i></div></label>' +
      '<p class="fin-hint">المتوسط للعلم فقط ولا يُضاف للرصيد أبداً. تسجّل أرباحك الفعلية بالإيداع حين تحصل عليها.</p>' + common;
  } else if(w.step === 2){
    h = '<h2 class="fin-wq">كم قيمة الكوين بالدينار؟</h2><p class="fin-hint">تقدر تغيّره لاحقاً مرة وحدة بالشهر. <b>1 كوين = دقيقتان</b> ثابتة دائماً.</p>' + finRateOptionsHtml(w.rate);
  } else {
    const sal = w.work === 'employee' ? finParseAmt(w.salary) : null;
    h = '<h2 class="fin-wq">مراجعة الإعدادات</h2><dl class="fin-review"><div><dt>طبيعة العمل</dt><dd>' + (w.work === 'employee' ? 'موظف' : 'عمل حر') + '</dd></div>' +
      '<div><dt>الرصيد الافتتاحي</dt><dd dir="ltr">' + finFmt(finParseAmt(w.opening) || 0) + ' د.ع</dd></div>' +
      (w.work === 'employee' ? '<div><dt>الراتب</dt><dd dir="ltr">' + finFmt(sal || 0) + ' د.ع</dd></div><div><dt>يوم الاستحقاق</dt><dd>' + escapeHtml(String(w.day)) + ' من كل شهر</dd></div><div><dt>بداية الاستحقاق</dt><dd>' + escapeHtml(finDateAr(w.start)) + '</dd></div>' : '<div><dt>مصدر الدخل</dt><dd>' + escapeHtml(w.source || '—') + '</dd></div>' + (finParseAmt(w.avg) ? '<div><dt>المتوسط التقديري</dt><dd dir="ltr">' + finFmt(finParseAmt(w.avg)) + ' د.ع</dd></div>' : '')) +
      '<div><dt>سعر الكوين</dt><dd dir="ltr">1 كوين = ' + finFmt(w.rate) + ' د.ع</dd></div></dl>';
  }
  box.innerHTML = '<div class="fin-wiz">' + bar + h + '<p class="fin-err" role="alert"' + (w.err ? '' : ' hidden') + '>' + escapeHtml(w.err) + '</p>' +
    '<div class="fin-wbtns">' + (w.step > 0 ? '<button type="button" class="btn btn-secondary" onclick="finWizBack()">السابق</button>' : '<span></span>') +
    '<button type="button" class="btn btn-primary" onclick="finWizNext()">' + (w.step === 3 ? 'تأكيد وإنشاء المحفظة' : 'التالي') + '</button></div></div>';
  codisHydrateIcons(box); if(w.step === 1) finWizPreview();
  if(w.step === 2){ const pk = box.querySelector('.fin-rates'); if(pk) pk.onclick = e=>{ const b = e.target.closest('[data-r]'); if(!b) return; finWiz.rate = Number(b.dataset.r); finWiz.err = ''; finRenderWizard(box); }; }
}
function finWizSet(k, v){ finWiz[k] = v; finWiz.err = ''; finRender(); }
function finWizPreview(){
  const el = document.getElementById('fw-prev'); if(!el || !finWiz) return;
  const day = codisFinInt(finWiz.day, 1, 31), st = finWiz.start; if(!day || !codisFinDateOk(st)){ el.textContent = ''; return; }
  let mk = codisFinMonthOf(st), g = 0; while(g++ < 3 && codisFinDueOf(mk, day) < st) mk = codisFinNextMonth(mk);
  el.textContent = 'أول راتب يُضاف يوم ' + finDateAr(codisFinDueOf(mk, day)) + (codisFinDueOf(mk, day) <= codisFinToday() ? ' (مستحق الآن ويُضاف عند التأكيد)' : '') + '.';
}
function finWizBack(){ if(finWiz && finWiz.step > 0){ finWiz.step--; finWiz.err = ''; finRender(); } }
function finWizNext(){
  const w = finWiz; w.err = '';
  if(w.step === 0){ if(!w.work) w.err = 'اختر طبيعة عملك'; }
  else if(w.step === 1){
    const open = String(w.opening).trim() === '' ? null : (/^[0٠,\s]+$/.test(w.opening) ? 0 : finParseAmt(w.opening));
    if(open === null) w.err = 'اكتب رصيدك الحالي (أو 0 إن لم يكن لديك رصيد)';
    else if(w.work === 'employee'){
      if(!finParseAmt(w.salary)) w.err = 'اكتب قيمة الراتب الشهري'; else if(!codisFinInt(w.day, 1, 31)) w.err = 'يوم الراتب بين 1 و31'; else if(!codisFinDateOk(w.start)) w.err = 'اختر تاريخ بداية صحيحاً';
    }
  } else if(w.step === 2){ if(!w.rate) w.err = 'اختر سعر الكوين'; }
  if(w.err){ codisSfx('invalid', { ctx:'unavailable' }); finRender(); return; }
  if(w.step < 3){ w.step++; finRender(); return; }
  const open = /^[0٠,\s]*$/.test(w.opening) ? 0 : finParseAmt(w.opening);
  const r = codisFinSetupNow({ work:w.work, source:w.source, avg:finParseAmt(w.avg), opening:open, salary:w.work === 'employee' ? { amount:finParseAmt(w.salary), day:codisFinInt(w.day, 1, 31), from:w.start } : null, rate:w.rate });
  if(!r.ok){ w.err = finFailText(r); finRender(); return; }
  finWiz = null; codisSfx('confirm', { ctx:'switch' }); showToast('تم إنشاء محفظتك المالية' + (r.added ? ' — أُضيف ' + finFmt(r.added) + ' راتب مستحق' : ''), 'var(--success)', 'check'); finRefresh();
}
/* إنشاء المحفظة: دفعة واحدة (رصيد افتتاحي + قاعدة راتب + سعر ابتدائي) ثم تعويض ما حلّ استحقاقه */
function codisFinSetupNow(o){
  const f = codisFin(); if(f.setup.done) return { ok:false, reason:'dup' };
  if(o.work !== 'employee' && o.work !== 'freelance') return { ok:false, reason:'amount' };
  const open = codisFinInt(o.opening, 0, 1e12); if(open === null) return { ok:false, reason:'amount' };
  if(codisFinRates().indexOf(o.rate) === -1) return { ok:false, reason:'rate' };
  if(o.work === 'employee'){ const s = o.salary || {}; if(codisFinInt(s.amount, 1, 1e12) === null || codisFinInt(s.day, 1, 31) === null || !codisFinDateOk(s.from)) return { ok:false, reason:'amount' }; }
  return codisFinTx(()=>{
    const now = codisFinIso(), today = codisFinToday();
    f.work = o.work; f.source = String(o.source || '').trim().slice(0, 80); f.avgIncome = o.avg ? codisFinInt(o.avg, 0, 1e12) : null;
    if(!codisFinPush(f, { id:'open', ref:'open', type:'OPENING_BALANCE', amount:open, cur:'IQD', desc:'رصيد افتتاحي', cat:'', src:'opening', date:today, at:now })) return { ok:false, reason:'dup' };
    if(o.work === 'employee') f.salary.rules.push({ id:codisFinUid('rule'), amount:o.salary.amount, day:o.salary.day, from:o.salary.from, createdAt:now });
    f.fx = { rate:o.rate, setAt:now }; f.fxLog.push({ id:codisFinUid('fx'), kind:'initial', from:null, to:o.rate, at:now, month:codisFinMonthOf(today) });
    f.setup = { done:true, doneAt:now };
    const added = codisFinCatchUpIn(f);
    return { ok:true, added:added.reduce((s, e)=>s + e.amount, 0), count:added.length };
  });
}

/* ---------- الشريط العلوي ---------- */
function finTopbar(){ const b = document.getElementById('fin-btn'); if(!b) return; const need = !codisFin().setup.done; b.classList.toggle('needs-setup', need); b.setAttribute('aria-label', need ? 'الإدارة المالية — أكمل الإعداد' : 'الإدارة المالية'); }

/* ---------- المتابعة: راتب مستحق · عودة للتطبيق · اتصال ---------- */
let finLastTick = 0;
function codisFinTick(){
  try{
    if(typeof data === 'undefined' || !data || !data.finance) return;
    finTopbar();
    const f = codisFin(); if(!f.setup.done) return;
    const n = codisFinCatchUp();
    if(n > 0){ showToast(n === 1 ? 'وصل راتبك — انضاف لمحفظتك المالية' : 'انضافت ' + n + ' رواتب مستحقة لمحفظتك المالية', 'var(--success)', 'check'); }
    if(n > 0 && econPageVisible('settings-page-eco-fin')) finRender();
    finLastTick = Date.now();
  }catch(e){ console.error('codisFinTick', e); }
}
(function(){
  try{
    document.addEventListener('visibilitychange', ()=>{ if(document.visibilityState === 'visible') codisFinTick(); });
    window.addEventListener('focus', codisFinTick); window.addEventListener('online', codisFinTick);
    setInterval(codisFinTick, 60000); setTimeout(codisFinTick, 1500);
  }catch(e){}
})();

/* ================= الإضافة التلقائية للمكافآت (مالية / وقتية) ================= */
let finAuto = null;
function finAutoOpen(){
  finAuto = { step:0, kind:null, name:'', iqd:'', min:'', cardId:null, err:'' };
  const s = CodisFinUI.open({ title:'إضافة مكافأة تلقائية', cls:'is-wide', body:'<div id="fa-root"></div>', mount:(root)=>{ finAutoPaint(root); }, onClose:()=>{ finAuto = null; } });
  return s;
}
function finAutoPaint(root){
  const a = finAuto; if(!a) return; const b = root.querySelector('#fa-root'), f = codisFin();
  let h = '<div class="fin-prog" role="progressbar" aria-valuemin="1" aria-valuemax="3" aria-valuenow="' + (a.step + 1) + '"><i style="--p:' + ((a.step + 1) / 3 * 100) + '%"></i></div>';
  if(a.step === 0){
    h += '<h3 class="fin-wq">ما نوع المكافأة؟</h3><div class="fin-opts">' +
      '<button type="button" class="fin-opt' + (a.kind === 'financial' ? ' is-on' : '') + '" onclick="finAutoSet(\'kind\',\'financial\')">' + codisIcon('coin', { size:'lg' }) + '<b>مكافأة مالية</b><small>شي تشتريه بفلوسك الحقيقية</small></button>' +
      '<button type="button" class="fin-opt' + (a.kind === 'time' ? ' is-on' : '') + '" onclick="finAutoSet(\'kind\',\'time\')">' + codisIcon('hourglass', { size:'lg' }) + '<b>مكافأة وقتية</b><small>وقت راحة أو متعة بمؤقت</small></button></div>';
  } else if(a.step === 1){
    h += '<label class="fin-f"><span>اسم المكافأة</span><input id="fa-name" class="fin-in" maxlength="120" autocomplete="off" placeholder="' + (a.kind === 'financial' ? 'مثلاً: لفة شاورما' : 'مثلاً: مشاهدة مباراة') + '" value="' + escapeHtml(a.name) + '" oninput="finAuto.name=this.value;finAutoCalc()" data-autofocus></label>';
    if(a.kind === 'financial'){
      h += f.setup.done ? '<label class="fin-f"><span>قيمتها الحقيقية بالدينار العراقي</span><div class="fin-amt"><input id="fa-iqd" class="fin-in" inputmode="numeric" dir="ltr" autocomplete="off" placeholder="2,000" value="' + escapeHtml(a.iqd) + '" oninput="finAmtInput(this);finAuto.iqd=this.value;finAutoCalc()"><i>د.ع</i></div></label>' :
        '<p class="fin-lock">' + codisIcon('hourglass') + ' المكافآت المالية تحتاج إعداد الإدارة المالية أولاً (الرصيد وسعر الكوين). <button type="button" class="fin-link" onclick="CodisFinUI.close();finOpen()">افتح الإدارة المالية</button></p>';
    } else h += '<label class="fin-f"><span>مدة المكافأة بالدقائق</span><div class="fin-amt"><input id="fa-min" class="fin-in" type="number" min="1" max="1440" inputmode="numeric" dir="ltr" placeholder="90" value="' + escapeHtml(a.min) + '" oninput="finAuto.min=this.value;finAutoCalc()"><i>دقيقة</i></div></label>';
    h += '<div class="fin-calc" id="fa-calc" aria-live="polite"></div>';
  } else {
    const c = finAutoCalc(true);
    h += '<h3 class="fin-wq">المراجعة</h3>' + (c.html || '');
  }
  h += '<p class="fin-err" role="alert"' + (a.err ? '' : ' hidden') + '>' + escapeHtml(a.err) + '</p><div class="fin-wbtns">' + (a.step > 0 ? '<button type="button" class="btn btn-secondary" onclick="finAutoBack()">السابق</button>' : '<span></span>') +
    '<button type="button" class="btn btn-primary" id="fa-next" onclick="finAutoNext()">' + (a.step === 2 ? 'حفظ المكافأة' : 'التالي') + '</button></div>';
  b.innerHTML = h; codisHydrateIcons(b);
  if(a.step === 1) finAutoCalc();
  if(a.step === 2){ b.querySelectorAll('[data-card]').forEach(x=>{ x.onclick = ()=>{ finAuto.cardId = x.dataset.card; finAutoPaint(root); }; }); }
}
function finAutoSet(k, v){ finAuto[k] = v; finAuto.err = ''; finAutoPaint(CodisFinUI.el()); }
function finAutoBack(){ if(finAuto.step > 0){ finAuto.step--; finAuto.err = ''; finAutoPaint(CodisFinUI.el()); } }
/* الحساب والتصنيف: يُرجع { ok, coin, cls, html } ويحدّث سطر الحساب بالخطوة 1 */
function finAutoCalc(full){
  const a = finAuto; if(!a) return {}; const f = codisFin();
  let coin = null, line = '', iqd = null, min = null;
  if(a.kind === 'financial'){ iqd = finParseAmt(a.iqd); if(iqd && f.fx.rate){ coin = codisFinCoinOfIqd(iqd, f.fx.rate); line = finFmt(iqd) + ' ÷ ' + finFmt(f.fx.rate) + ' = <b>' + finFmt(coin) + '</b> كوين'; } }
  else { min = codisFinInt(a.min, 1, 1440); if(min){ coin = codisFinCoinOfMinutes(min); line = finFmt(min) + ' دقيقة ÷ 2 = <b>' + finFmt(coin) + '</b> كوين'; } }
  const name = String(a.name || '').trim(); let cls = null, warn = '';
  if(coin !== null){ cls = codisFinClassify(name || '—', coin); if(!cls.ok) warn = cls.reason === 'low' ? 'القيمة أقل من الحد الأدنى (10 كوين' + (a.kind === 'financial' ? ' = ' + finFmt(10 * f.fx.rate) + ' د.ع بالسعر الحالي' : ' = 20 دقيقة') + ')' : cls.reason === 'high' ? 'القيمة أعلى من الحد الأقصى (30,000 كوين)' : 'لا توجد بطاقة مناسبة لهذي القيمة'; }
  const el = document.getElementById('fa-calc'); if(el && !full) el.innerHTML = line ? '<span>' + line + '</span>' + (warn ? '<em class="fin-bad">' + warn + '</em>' : '') : '';
  const o = { coin:coin, cls:cls, warn:warn, iqd:iqd, min:min, line:line };
  if(full){
    if(!cls || !cls.ok) { o.html = '<p class="fin-bad">' + (warn || 'أكمل البيانات') + '</p>'; return o; }
    const cand = cls.candidates, pick = cand.find(c=>c.card.id === a.cardId) || (cls.ambiguous ? null : cls.best);
    if(pick && !a.cardId) a.cardId = pick.card.id;
    o.pick = pick;
    o.html = '<div class="fin-calc"><span>' + escapeHtml(name) + ' — ' + line + '</span></div>' +
      (cls.ambiguous ? '<p class="fin-hint">اسم المكافأة ما يكفي لتحديد نوعها بثقة — اختر الوجهة المناسبة:</p>' : '<p class="fin-hint">الوجهة المقترحة حسب المعنى والسعر معاً' + (cls.domains.length ? ' (' + cls.domains.map(d=>escapeHtml(d.label)).join('، ') + ')' : '') + ':</p>') +
      '<div class="fin-dests" role="radiogroup" aria-label="الوجهة">' + cand.map(c=>'<button type="button" role="radio" aria-checked="' + (pick && pick.card.id === c.card.id) + '" class="fin-dest' + (pick && pick.card.id === c.card.id ? ' is-on' : '') + '" data-card="' + c.card.id + '"><b>' + escapeHtml(c.card.name) + '</b><small>' + econRoomLabel(c.card.room) + ' · نطاق ' + finFmt(c.card.min) + '–' + finFmt(c.card.max) + ' كوين</small></button>').join('') + '</div>' +
      '<p class="fin-hint">القيمة المحفوظة بالضبط: <b>' + finFmt(coin) + '</b> كوين' + (a.kind === 'financial' ? ' (القيمة الأصلية ' + finFmt(iqd) + ' د.ع ثابتة وتتغير قيمتها بالكوين مع سعر الصرف)' : ' (' + finFmt(min) + ' دقيقة بمؤقت حقيقي عند الاستخدام)') + '.</p>';
  }
  return o;
}
function finAutoNext(){
  const a = finAuto, root = CodisFinUI.el(); a.err = '';
  if(a.step === 0){ if(!a.kind) a.err = 'اختر نوع المكافأة'; }
  else if(a.step === 1){
    const c = finAutoCalc();
    if(!String(a.name).trim()) a.err = 'اكتب اسم المكافأة'; else if(a.kind === 'financial' && !codisFin().setup.done) a.err = 'أكمل إعداد الإدارة المالية أولاً';
    else if(c.coin === null) a.err = a.kind === 'financial' ? 'اكتب القيمة بالدينار' : 'اكتب المدة بالدقائق'; else if(c.warn) a.err = c.warn;
  } else {
    const c = finAutoCalc(true); if(!c.pick){ a.err = 'اختر وجهة المكافأة'; }
    else {
      const r = codisFinCreateReward({ name:a.name, kind:a.kind, iqd:finParseAmt(a.iqd), minutes:codisFinInt(a.min, 1, 1440), cardId:c.pick.card.id });
      if(!r.ok){ a.err = ({ name:'اكتب الاسم', kind:'اختر النوع', nosetup:'أكمل إعداد الإدارة المالية أولاً', amount:'القيمة غير صالحة', low:'القيمة أقل من 10 كوين', high:'القيمة أعلى من 30,000 كوين', range:'القيمة خارج نطاق البطاقة', save:'تعذّر الحفظ — ما انضافت', error:'تعذّر التنفيذ' })[r.reason] || 'تعذّر التنفيذ'; }
      else { CodisFinUI.close(); codisSfx('success', { ctx:'settings' }); showToast('انضافت «' + r.item.name + '» (' + finFmt(r.coin) + ' كوين) إلى ' + r.card.name, 'var(--success)', 'check'); try{ econRenderAll(); }catch(e){} return; }
    }
  }
  if(a.err){ codisSfx('invalid', { ctx:'unavailable' }); finAutoPaint(root); return; }
  a.step++; finAutoPaint(root);
}

/* ---------- استخدام مكافأة مالية: تأكيد صريح قبل أي خصم ---------- */
async function codisFinUseConfirm(it){
  const f = codisFin();
  if(!f.setup.done){ codisSfx('invalid', { ctx:'funds' }); showToast('أكمل إعداد الإدارة المالية أولاً حتى يُخصم المبلغ من محفظتك', 'var(--warning)'); return false; }
  const iqd = it.fin.iqd, bal = codisFinBalance(f);
  if(bal < iqd && !CodisLimits.bypass('fin.nonnegative')){ codisSfx('invalid', { ctx:'funds' }); showToast('رصيدك المالي غير كافٍ — ينقصك ' + finFmt(iqd - bal) + ' دينار، والمكافأة تبقى بحوزتك', 'var(--warning)'); return false; }
  return await codisConfirm({ title:'تستخدم «' + it.name + '»؟', message:'يتسحب ' + finFmt(iqd) + ' دينار من محفظتك المالية.',
    rows:[['رصيدك الحالي', finFmt(bal) + ' د.ع'], ['قيمة المكافأة', finFmt(iqd) + ' د.ع', true], ['رصيدك بعد الخصم', finFmt(bal - iqd) + ' د.ع']],
    detail:'يُسجَّل الخصم وتُعلَّم المكافأة كمستخدَمة معاً، ولا يتكرر الخصم.', icon:'check', confirmText:'استخدم واخصم', danger:false });
}
/* سطر «القيمة الحقيقية/المدة» لصف المكافأة بالإعدادات */
function codisFinMetaHtml(it){
  if(!it || !it.fin) return '';
  return it.fin.kind === 'financial' ? '<span>القيمة الحقيقية <b>' + finFmt(it.fin.iqd) + '</b> د.ع</span>' : '<span>المدة <b>' + finFmt(it.fin.minutes) + '</b> دقيقة</span>';
}

/* حدود المستخدم المالية تمرّ عبر CodisLimits فيبقى حساب المطوّر بلا قيود */
try{ CodisLimits.reg('fin.nonnegative', 'الإنفاق المالي (مصروف/استخدام مكافأة) لا يتجاوز الرصيد'); CodisLimits.reg('fin.fxMonthly', 'تغيير سعر صرف الكوينز مرة واحدة بالشهر'); }catch(e){}
