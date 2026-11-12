/* ================= CODIS-V43: إضافة المكافآت التلقائية — جلسة إضافة واحدة تتكرر =================
   النوعان `time` و`financial` كما هما؛ التخزين كله عبر codisFinCreateReward (فيه codisFinTx) بلا أي مسار ثانٍ.
   الخطوات: 0 اختيار النوع · 1 التفاصيل (اسم + قيمة/مدة + ستيكر اختياري) · 2 المراجعة والوجهة. بعد الحفظ الناجح: يرجع للخطوة 1 بنفس النوع وحقول فارغة. */
let finAuto = null;
function finAutoBlank(kind){ return { step:kind ? 1 : 0, kind:kind || null, name:'', iqd:'', min:'', stickerId:'', cardId:null, err:'', busy:false, saved:0, flash:'', lockUntil:0 }; }
function finAutoOpen(){
  finAuto = finAutoBlank();
  return CodisFinUI.open({ title:'إضافة مكافأة تلقائية', cls:'is-wide fa-ov', body:'<div id="fa-root"></div>', mount:(root)=>{ finAutoPaint(root); }, onClose:()=>{ finAuto = null; } });
}
/* الستيكر يعيش بحقل مخفي (#fa-sticker) يكتبه codisSetSticker — يُقرأ للحالة قبل أي إعادة رسم أو حفظ */
function finAutoSync(){ const h = document.getElementById('fa-sticker'); if(h && finAuto) finAuto.stickerId = codisStickerIdOk(h.value) || ''; }
function finAutoKindLabel(k){ return k === 'financial' ? 'مكافأة مالية' : 'مكافأة وقتية'; }
function finAutoPaint(root){
  const a = finAuto; if(!a) return; const b = root.querySelector('#fa-root'); if(!b) return; const f = codisFin();
  const bar = '<div class="fa-prog"><div class="fin-prog" role="progressbar" aria-valuemin="1" aria-valuemax="3" aria-valuenow="' + (a.step + 1) + '"><i style="--p:' + ((a.step + 1) / 3 * 100) + '%"></i></div><span class="fin-prog-t">الخطوة ' + (a.step + 1) + ' من 3</span></div>';
  let h = bar, foot = '';
  if(a.step === 0){
    h += '<h3 class="fin-wq">ما نوع المكافأة التي تريد إضافتها؟</h3><div class="fa-types" role="group" aria-label="نوع المكافأة">' +
      '<button type="button" class="fa-type' + (a.kind === 'time' ? ' is-on' : '') + '" onclick="finAutoPick(\'time\')"><span class="fa-type-ic" aria-hidden="true">' + codisIcon('hourglass', { size:'lg' }) + '</span><b>مكافأة وقتية</b><small>مدة زمنية بالدقائق، ويشتغل لها مؤقت عند الاستخدام</small></button>' +
      '<button type="button" class="fa-type' + (a.kind === 'financial' ? ' is-on' : '') + '" onclick="finAutoPick(\'financial\')"><span class="fa-type-ic" aria-hidden="true">' + codisIcon('coin', { size:'lg' }) + '</span><b>مكافأة مالية</b><small>قيمة حقيقية بالدينار العراقي تُخصم من محفظتك المالية</small></button></div>';
  } else if(a.step === 1){
    h += '<div class="fa-top"><span class="fa-kind">' + codisIcon(a.kind === 'financial' ? 'coin' : 'hourglass') + '<b>' + finAutoKindLabel(a.kind) + '</b>' + (a.saved ? '<i class="fa-n">أُضيف ' + finFmt(a.saved) + '</i>' : '') + '</span></div>';
    if(a.flash) h += '<p class="fa-ok" role="status">' + codisIcon('check') + '<span>' + escapeHtml(a.flash) + '</span></p>';
    h += '<label class="fin-f"><span>اسم المكافأة</span><input id="fa-name" class="fin-in" maxlength="120" autocomplete="off" enterkeyhint="next" placeholder="' + (a.kind === 'financial' ? 'مثلاً: لفة شاورما' : 'مثلاً: مشاهدة مباراة') + '" value="' + escapeHtml(a.name) + '" oninput="finAuto.name=this.value;finAutoCalc()"></label>';
    if(a.kind === 'financial'){
      h += f.setup.done ? '<label class="fin-f"><span>قيمتها بالدينار العراقي</span><div class="fin-amt"><input id="fa-iqd" class="fin-in" inputmode="numeric" dir="ltr" autocomplete="off" placeholder="2,000" value="' + escapeHtml(a.iqd) + '" oninput="finAmtInput(this);finAuto.iqd=this.value;finAutoCalc()"><i>د.ع</i></div></label>' :
        '<p class="fin-lock">' + codisIcon('hourglass') + ' المكافآت المالية تحتاج إعداد الإدارة المالية أولاً (الرصيد وسعر الكوين). <button type="button" class="fin-link" onclick="CodisFinUI.close();finOpen()">افتح الإدارة المالية</button></p>';
    } else h += '<label class="fin-f"><span>مدة المكافأة بالدقائق</span><div class="fin-amt"><input id="fa-min" class="fin-in" type="number" min="1" max="1440" inputmode="numeric" dir="ltr" placeholder="90" value="' + escapeHtml(a.min) + '" oninput="finAuto.min=this.value;finAutoCalc()"><i>دقيقة</i></div></label>';
    h += '<div class="fin-f fa-stk"><span>الستيكر <em>اختياري</em></span>' + codisStickerRowHtml('fa', a.stickerId) + '</div>' +
      '<input type="hidden" id="fa-room" value="tasks"><input type="hidden" id="fa-rarity" value="C"><input type="hidden" id="fa-trarity" value="bronze">' +
      '<div class="fin-calc" id="fa-calc" aria-live="polite"></div>';
  } else {
    const c = finAutoCalc(true);
    h += '<h3 class="fin-wq">المراجعة</h3>' + (c.html || '');
  }
  h += '<p class="fin-err" role="alert"' + (a.err ? '' : ' hidden') + '>' + escapeHtml(a.err) + '</p>';
  foot = '<div class="fin-wbtns fa-foot">' + (a.step > 0 ? '<button type="button" class="btn btn-secondary" onclick="finAutoBack()">' + (a.step === 1 ? 'تغيير النوع' : 'السابق') + '</button>' : '<span></span>') +
    (a.step === 0 ? '' : '<button type="button" class="btn btn-primary" id="fa-next" onclick="finAutoNext()"' + (a.busy ? ' disabled aria-disabled="true"' : '') + '>' + (a.step === 2 ? 'حفظ المكافأة' : 'التالي') + '</button>') + '</div>';
  b.innerHTML = h + foot; codisHydrateIcons(b);
  if(a.step === 1){ finAutoCalc(); setTimeout(()=>{ const i = b.querySelector('#fa-name'); if(i && finAuto === a && !a.name) try{ i.focus({ preventScroll:true }); }catch(e){} }, 60); }
  if(a.step === 2){ b.querySelectorAll('[data-card]').forEach(x=>{ x.onclick = ()=>{ finAuto.cardId = x.dataset.card; finAutoPaint(root); }; }); }
}
function finAutoPick(kind){ const a = finAuto; if(!a) return; finAutoSync(); a.kind = kind; a.step = 1; a.err = ''; a.cardId = null; codisSfx('open', { ctx:'select' }); finAutoPaint(CodisFinUI.el()); }
function finAutoSet(k, v){ finAutoSync(); finAuto[k] = v; finAuto.err = ''; finAutoPaint(CodisFinUI.el()); }
function finAutoBack(){ const a = finAuto; if(!a || a.step <= 0 || a.busy) return; finAutoSync(); a.step--; a.err = ''; a.flash = ''; finAutoPaint(CodisFinUI.el()); }
/* الحساب والتصنيف: يُرجع { ok, coin, cls, html } ويحدّث سطر الحساب بالخطوة 1 */
function finAutoCalc(full){
  const a = finAuto; if(!a) return {}; const f = codisFin();
  let coin = null, line = '', iqd = null, min = null;
  if(a.kind === 'financial'){ iqd = finParseAmt(a.iqd); if(iqd && f.fx.rate){ coin = codisFinCoinOfIqd(iqd, f.fx.rate); line = finFmt(iqd) + ' ÷ ' + finFmt(f.fx.rate) + ' = <b>' + finFmt(coin) + '</b> كوين'; } }
  else { min = codisFinInt(a.min, 1, 1440); if(min){ coin = codisFinCoinOfMinutes(min); line = finFmt(min) + ' دقيقة ÷ 2 = <b>' + finFmt(coin) + '</b> كوين'; } }
  const name = String(a.name || '').trim(); let cls = null, warn = '';
  if(coin !== null){ cls = codisFinClassify(name || '—', coin); if(!cls.ok) warn = cls.reason === 'low' ? 'القيمة أقل من الحد الأدنى (10 كوين' + (a.kind === 'financial' ? ' = ' + finFmt(10 * f.fx.rate) + ' د.ع بالسعر الحالي' : ' = 20 دقيقة') + ')' : cls.reason === 'high' ? 'القيمة أعلى من الحد الأقصى (30,000 كوين)' : 'لا توجد بطاقة مناسبة لهذي القيمة'; }
  const el = document.getElementById('fa-calc'); if(el && !full) el.innerHTML = line ? '<span>' + line + '</span>' + (warn ? '<em class="fin-bad">' + warn + '</em>' : '') : '';
  { /* معاينة الستيكر على الوجهة الأرجح (حقول مخفية يقرؤها codisStickerPreviewHtml) */
    const best = cls && cls.ok ? cls.best.card : null, set = (id, v)=>{ const e = document.getElementById(id); if(e) e.value = v; };
    set('fa-room', best && !best.fixed ? best.room : 'tasks'); set('fa-rarity', best && !best.fixed && best.room !== 'learn' && best.rarity ? best.rarity : 'C'); set('fa-trarity', best && best.room === 'learn' ? best.rarity : 'bronze');
  }
  const o = { coin:coin, cls:cls, warn:warn, iqd:iqd, min:min, line:line };
  if(full){
    if(!cls || !cls.ok){ o.html = '<p class="fin-bad">' + (warn || 'أكمل البيانات') + '</p>'; return o; }
    const cand = cls.candidates, pick = cand.find(c=>c.card.id === a.cardId) || (cls.ambiguous ? null : cls.best);
    if(pick && !a.cardId) a.cardId = pick.card.id;
    o.pick = pick;
    const stk = codisStickerList(a.stickerId).filter(x=>CodisStickers.url(x)).slice(0, CODIS_STICKER_MAX).map(x=>'<img src="' + escapeHtml(CodisStickers.url(x)) + '" alt="" draggable="false">').join('');
    o.html = '<div class="fa-sum"><div class="fa-sum-m"><b dir="auto">' + escapeHtml(name) + '</b><span>' + line + '</span></div>' + (stk ? '<div class="fa-sum-s" aria-label="الستيكر">' + stk + '</div>' : '') + '</div>' +
      '<p class="fin-hint fa-q">' + (cls.ambiguous ? 'وين تريد المكافأة تظهر لك؟' : 'الوجهة المقترحة حسب المعنى والسعر معاً' + (cls.domains.length ? ' (' + cls.domains.map(d=>escapeHtml(d.label)).join('، ') + ')' : '') + ':') + '</p>' +
      '<div class="fin-dests" role="radiogroup" aria-label="الوجهة">' + cand.map(c=>'<button type="button" role="radio" aria-checked="' + (pick && pick.card.id === c.card.id) + '" class="fin-dest' + (pick && pick.card.id === c.card.id ? ' is-on' : '') + '" data-card="' + c.card.id + '"><b>' + escapeHtml(c.card.name) + '</b><small>' + econRoomLabel(c.card.room) + ' · نطاق ' + finFmt(c.card.min) + '–' + finFmt(c.card.max) + ' كوين</small></button>').join('') + '</div>';
  }
  return o;
}
function finAutoNext(){
  const a = finAuto, root = CodisFinUI.el(); if(!a || !root || a.busy || Date.now() < a.lockUntil) return;
  finAutoSync(); a.err = '';
  if(a.step === 0){ if(!a.kind) a.err = 'اختر نوع المكافأة'; }
  else if(a.step === 1){
    const c = finAutoCalc();
    if(!String(a.name).trim()) a.err = 'اكتب اسم المكافأة'; else if(a.kind === 'financial' && !codisFin().setup.done) a.err = 'أكمل إعداد الإدارة المالية أولاً';
    else if(c.coin === null) a.err = a.kind === 'financial' ? 'اكتب القيمة بالدينار' : 'اكتب المدة بالدقائق'; else if(c.warn) a.err = c.warn;
  } else {
    const c = finAutoCalc(true);
    if(!c.pick){ a.err = 'اختر وجهة المكافأة'; }
    else {
      a.busy = true; const btn = document.getElementById('fa-next'); if(btn){ btn.disabled = true; btn.setAttribute('aria-disabled', 'true'); }
      let r; try{ r = codisFinCreateReward({ name:a.name, kind:a.kind, iqd:finParseAmt(a.iqd), minutes:codisFinInt(a.min, 1, 1440), cardId:c.pick.card.id, stickerId:a.stickerId || null }); }
      catch(e){ console.error('finAuto save', e); r = { ok:false, reason:'error' }; }
      finally{ a.busy = false; }
      if(!r.ok){ a.err = ({ name:'اكتب الاسم', kind:'اختر النوع', nosetup:'أكمل إعداد الإدارة المالية أولاً', amount:'القيمة غير صالحة', low:'القيمة أقل من 10 كوين', high:'القيمة أعلى من 30,000 كوين', range:'القيمة خارج نطاق البطاقة', save:'تعذّر الحفظ — ما انضافت', error:'تعذّر التنفيذ' })[r.reason] || 'تعذّر التنفيذ'; }
      else {   /* نجاح فعلي: الآن فقط تُفرَّغ الحقول ويبقى النوع */
        const nm = r.item.name; a.saved++; a.flash = 'انضافت «' + nm + '» (' + finFmt(r.coin) + ' كوين) إلى ' + r.card.name + ' — تقدر تضيف التالية'; a.lockUntil = Date.now() + 500;
        a.name = ''; a.iqd = ''; a.min = ''; a.stickerId = ''; a.cardId = null; a.err = ''; a.step = 1;
        codisSfx('success', { ctx:'settings' }); showToast('انضافت «' + nm + '»', 'var(--success)', 'check');
        finAutoPaint(root); try{ econRenderAll(); }catch(e){ console.error(e); } return;
      }
    }
  }
  if(a.err){ codisSfx('invalid', { ctx:'unavailable' }); finAutoPaint(root); return; }
  a.step++; a.flash = ''; finAutoPaint(root);
}
