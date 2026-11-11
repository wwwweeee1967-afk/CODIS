/* ================= CODIS-FINANCE (3.28.0) — محرك الإدارة المالية الشخصية =================
   نظام مالي مستقل محاسبياً عن data.wallet (الكوينز والفضة): بيانات data.finance ودفتر حركاته بالدينار العراقي (أعداد صحيحة).
   الرصيد = مجموع الدفتر دائماً (لا يُخزَّن ولا يُعدَّل مباشرة): افتتاحي + إيداعات + رواتب − مصروفات − خصم مكافآت مالية.
   الوقت: وقت الجهاز الحقيقي بتوقيت Asia/Baghdad (UTC+3 ثابت) — لا يمرّ بـCodisClock، فمحاكاة أيام المطوّر لا تولّد رواتب ولا تستهلك سماحية سعر الصرف.
   كل ما يُستدعى وقت التحميل (codisFinNormalize) function declaration فقط ولا يقرأ const/let لاحقة ولا يرمي خطأً أبداً (قاعدة 3.17.2). */

/* ---------- ثوابت (دوال لا const: تُستدعى وقت التحميل) ---------- */
function codisFinRates(){ return [20, 40, 80, 120, 160, 200]; }                 /* دينار لكل كوين — الستة المعتمدة */
function codisFinMinCoin(){ return 10; }
function codisFinMaxCoin(){ return 30000; }
function codisFinTypes(){ return ['OPENING_BALANCE', 'DEPOSIT', 'SALARY', 'EXPENSE', 'REWARD_REDEMPTION']; }
function codisFinTypeLabel(t){ return ({ OPENING_BALANCE:'رصيد افتتاحي', DEPOSIT:'إيداع', SALARY:'راتب', EXPENSE:'مصروف', REWARD_REDEMPTION:'استخدام مكافأة' })[t] || t; }
function codisFinDefaultCats(){
  return [{ id:'food', name:'الطعام والمواد الغذائية' }, { id:'personal', name:'الاحتياجات الشخصية' }, { id:'health', name:'الصحة' }, { id:'transport', name:'المواصلات' },
    { id:'home', name:'المنزل' }, { id:'shopping', name:'التسوق' }, { id:'fun', name:'الترفيه' }, { id:'other', name:'أخرى' }];
}
function codisFinBlank(){
  return { v:1, setup:{ done:false, doneAt:null }, work:null, source:'', avgIncome:null, cur:'IQD', salary:{ rules:[] }, fx:{ rate:null, setAt:null }, fxLog:[], cats:[], ledger:[] };
}

/* ---------- الوقت الحقيقي (بغداد) ---------- */
function codisFinNowMs(){
  try{ if(!CODIS_SEALED && typeof window !== 'undefined' && typeof window.__CODIS_FIN_NOW__ === 'number' && isFinite(window.__CODIS_FIN_NOW__)) return window.__CODIS_FIN_NOW__; }catch(e){}   /* خطّاف اختبار: محلي فقط */
  return Date.now();
}
function codisFinPad(n){ return (n < 10 ? '0' : '') + n; }
function codisFinDateKey(ms){ const d = new Date(ms + 10800000); return d.getUTCFullYear() + '-' + codisFinPad(d.getUTCMonth() + 1) + '-' + codisFinPad(d.getUTCDate()); }
function codisFinToday(){ return codisFinDateKey(codisFinNowMs()); }
function codisFinIso(){ return new Date(codisFinNowMs()).toISOString(); }
function codisFinMonthOf(dateKey){ return String(dateKey).slice(0, 7); }
function codisFinDaysIn(y, m){ return new Date(Date.UTC(y, m, 0)).getUTCDate(); }
function codisFinDateOk(s){
  if(typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const p = s.split('-').map(Number); return p[1] >= 1 && p[1] <= 12 && p[2] >= 1 && p[2] <= codisFinDaysIn(p[0], p[1]);
}
function codisFinNextMonth(mk){ const p = mk.split('-').map(Number); let y = p[0], m = p[1] + 1; if(m > 12){ m = 1; y++; } return y + '-' + codisFinPad(m); }
function codisFinMonthStart(mk){ return mk + '-01'; }
function codisFinMonthName(mk){ const M = ['كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران', 'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول'], p = String(mk).split('-').map(Number); return (M[(p[1] || 1) - 1] || '') + ' ' + p[0]; }
/* تاريخ استحقاق شهر: اليوم المطلوب، أو آخر يوم متاح بالشهر إن لم يوجد */
function codisFinDueOf(mk, day){ const p = mk.split('-').map(Number); return mk + '-' + codisFinPad(Math.min(day, codisFinDaysIn(p[0], p[1]))); }
function codisFinIsoOk(v){ return typeof v === 'string' && !isNaN(Date.parse(v)); }
function codisFinInt(v, min, max){ let n = (v === null || v === '' || typeof v === 'boolean' || v === undefined) ? NaN : Number(v); if(!isFinite(n)) return null; n = Math.round(n); return (n < min || n > max) ? null : n; }

/* ---------- التطبيع (آمن وقت التحميل) ---------- */
function codisFinNormalize(d){
  try{
    const src = (d.finance && typeof d.finance === 'object' && !Array.isArray(d.finance)) ? d.finance : {};
    const f = codisFinBlank(), types = codisFinTypes(), rates = codisFinRates();
    f.v = 1;
    const st = (src.setup && typeof src.setup === 'object') ? src.setup : {};
    f.setup = { done:st.done === true, doneAt:codisFinIsoOk(st.doneAt) ? st.doneAt : null };
    f.work = (src.work === 'employee' || src.work === 'freelance') ? src.work : null;
    f.source = typeof src.source === 'string' ? src.source.slice(0, 80) : '';
    f.avgIncome = codisFinInt(src.avgIncome, 0, 1e12);
    const rules = [], seenR = {};
    (src.salary && Array.isArray(src.salary.rules) ? src.salary.rules : []).forEach(r=>{
      if(!r || typeof r !== 'object' || typeof r.id !== 'string' || !r.id || seenR[r.id]) return;
      const amount = codisFinInt(r.amount, 0, 1e12), day = codisFinInt(r.day, 1, 31);
      if(amount === null || day === null || !codisFinDateOk(r.from)) return;
      seenR[r.id] = true; rules.push({ id:r.id.slice(0, 60), amount:amount, day:day, from:r.from, createdAt:codisFinIsoOk(r.createdAt) ? r.createdAt : '1970-01-01T00:00:00.000Z' });
    });
    rules.sort((a, b)=>a.from < b.from ? -1 : a.from > b.from ? 1 : (a.createdAt < b.createdAt ? -1 : a.createdAt > b.createdAt ? 1 : (a.id < b.id ? -1 : 1)));
    f.salary = { rules:rules };
    const fx = (src.fx && typeof src.fx === 'object') ? src.fx : {};
    f.fx = { rate:rates.indexOf(fx.rate) !== -1 ? fx.rate : null, setAt:codisFinIsoOk(fx.setAt) ? fx.setAt : null };
    const seenL = {}, log = [];
    (Array.isArray(src.fxLog) ? src.fxLog : []).forEach(x=>{
      if(!x || typeof x !== 'object' || typeof x.id !== 'string' || !x.id || seenL[x.id] || rates.indexOf(x.to) === -1 || !codisFinIsoOk(x.at)) return;
      seenL[x.id] = true;
      log.push({ id:x.id.slice(0, 60), kind:x.kind === 'initial' ? 'initial' : 'change', from:rates.indexOf(x.from) !== -1 ? x.from : null, to:x.to, at:x.at, month:/^\d{4}-\d{2}$/.test(x.month) ? x.month : codisFinMonthOf(codisFinDateKey(Date.parse(x.at))) });
    });
    log.sort((a, b)=>a.at < b.at ? -1 : a.at > b.at ? 1 : 0);
    f.fxLog = log;
    const seenC = {}, cats = [];
    (Array.isArray(src.cats) ? src.cats : []).forEach(c=>{
      if(!c || typeof c !== 'object' || typeof c.id !== 'string' || !/^c_[a-z0-9_]{1,30}$/.test(c.id) || seenC[c.id] || typeof c.name !== 'string' || !c.name.trim() || cats.length >= 30) return;
      seenC[c.id] = true; cats.push({ id:c.id, name:c.name.trim().slice(0, 40) });
    });
    f.cats = cats;
    const seenId = {}, seenRef = {}, seenSal = {}, led = [];
    (Array.isArray(src.ledger) ? src.ledger : []).forEach(e=>{
      if(!e || typeof e !== 'object' || typeof e.id !== 'string' || !e.id || seenId[e.id] || types.indexOf(e.type) === -1) return;
      let a = codisFinInt(e.amount, -1e12, 1e12); if(a === null) return;
      const ref = typeof e.ref === 'string' && e.ref ? e.ref.slice(0, 120) : e.id;
      if(seenRef[ref]) return;
      if(e.type === 'SALARY'){ if(!codisFinDateOk(e.due)) return; if(seenSal[codisFinMonthOf(e.due)]) return; }
      /* إشارة المبلغ يحدّدها النوع (الدفتر المحاسبي): دخل موجب · مصروف سالب */
      if(e.type === 'EXPENSE' || e.type === 'REWARD_REDEMPTION') a = -Math.abs(a); else a = Math.abs(a);
      if(a === 0 && e.type !== 'OPENING_BALANCE') return;
      const date = codisFinDateOk(e.date) ? e.date : (codisFinIsoOk(e.at) ? codisFinDateKey(Date.parse(e.at)) : null); if(!date) return;
      seenId[e.id] = true; seenRef[ref] = true; if(e.type === 'SALARY') seenSal[codisFinMonthOf(e.due)] = true;
      const o = { id:e.id.slice(0, 120), ref:ref, type:e.type, amount:a, cur:'IQD', desc:typeof e.desc === 'string' ? e.desc.slice(0, 120) : '', cat:typeof e.cat === 'string' ? e.cat.slice(0, 40) : '', src:typeof e.src === 'string' ? e.src.slice(0, 80) : '',
        date:date, at:codisFinIsoOk(e.at) ? e.at : date + 'T00:00:00.000Z' };
      if(e.type === 'SALARY') o.due = e.due;
      if(typeof e.note === 'string' && e.note) o.note = e.note.slice(0, 300);
      if(e.type === 'REWARD_REDEMPTION' && e.meta && typeof e.meta === 'object') o.meta = { uid:String(e.meta.uid || '').slice(0, 80), coins:Math.max(0, Math.min(1e9, Math.round((Number(e.meta.coins) || 0) * 100) / 100)), rewardId:String(e.meta.rewardId || '').slice(0, 80) };
      led.push(o);
    });
    f.ledger = led;
    d.finance = f;
  }catch(err){ if(!d.finance || typeof d.finance !== 'object') d.finance = codisFinBlank(); }
  return d.finance;
}

/* ---------- الدفتر والحسابات ---------- */
function codisFin(){ if(!data.finance || typeof data.finance !== 'object' || !Array.isArray(data.finance.ledger)) codisFinNormalize(data); return data.finance; }
function codisFinBalance(f){ f = f || codisFin(); let s = 0; for(let i = 0; i < f.ledger.length; i++) s += f.ledger[i].amount; return s; }
function codisFinCmp(a, b){ if(a.type === 'OPENING_BALANCE' && b.type !== 'OPENING_BALANCE') return -1; if(b.type === 'OPENING_BALANCE' && a.type !== 'OPENING_BALANCE') return 1;   /* الافتتاحي أول قيد دائماً (رصيد البداية) */
  return a.date < b.date ? -1 : a.date > b.date ? 1 : (a.at < b.at ? -1 : a.at > b.at ? 1 : (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)); }
function codisFinSorted(f){ return (f || codisFin()).ledger.slice().sort(codisFinCmp); }
/* الرصيد بعد كل حركة (يُعاد بناؤه من الدفتر مرتّباً — لا يُخزَّن فلا يفسد بالمزامنة) */
function codisFinRunning(f){ let b = 0; return codisFinSorted(f).map(e=>{ b += e.amount; return { e:e, bal:b }; }); }
function codisFinVerify(f){
  f = f || codisFin();
  const by = { OPENING_BALANCE:0, DEPOSIT:0, SALARY:0, EXPENSE:0, REWARD_REDEMPTION:0 }; let badSign = 0;
  f.ledger.forEach(e=>{ by[e.type] += e.amount; if(((e.type === 'EXPENSE' || e.type === 'REWARD_REDEMPTION') && e.amount > 0) || ((e.type !== 'EXPENSE' && e.type !== 'REWARD_REDEMPTION') && e.amount < 0)) badSign++; });
  const expect = by.OPENING_BALANCE + by.DEPOSIT + by.SALARY - Math.abs(by.EXPENSE) - Math.abs(by.REWARD_REDEMPTION);
  return { ok:badSign === 0 && expect === codisFinBalance(f), opening:by.OPENING_BALANCE, deposits:by.DEPOSIT, salary:by.SALARY, expenses:Math.abs(by.EXPENSE), redemptions:Math.abs(by.REWARD_REDEMPTION), balance:codisFinBalance(f), expected:expect, badSign:badSign };
}
/* معاملة مالية: لقطة قبل العملية، وأي فشل (استثناء/رفض/فشل الحفظ) يعيد كل شيء كما كان */
function codisFinTx(fn, wide){
  const snap = JSON.stringify(codisFin()), sI = wide ? JSON.stringify(data.settings.rewardItems) : null, sV = wide ? JSON.stringify(data.inventory.items) : null;
  const restore = ()=>{ try{ data.finance = JSON.parse(snap); if(wide){ data.settings.rewardItems = JSON.parse(sI); data.inventory.items = JSON.parse(sV); } }catch(e){} };
  let res;
  try{ res = fn(); }catch(err){ console.error('finance transaction failed:', err); restore(); return { ok:false, reason:'error' }; }
  if(!res || res.ok === false){ restore(); return res || { ok:false, reason:'failed' }; }
  if(res.noop) return res;
  if(!saveData()){ restore(); return { ok:false, reason:'save' }; }
  return res;
}
function codisFinUid(p){ return p + '_' + codisFinNowMs().toString(36) + Math.random().toString(36).slice(2, 8); }
/* إضافة قيد (داخل معاملة فقط): يمنع تكرار المرجع */
function codisFinPush(f, e){
  if(f.ledger.some(x=>x.ref === e.ref || x.id === e.id)) return null;
  f.ledger.push(e); return e;
}
function codisFinNeedSetup(f){ return !f.setup.done; }

/* ---------- الإيداع ---------- */
function codisFinDepositNow(o){
  o = o || {}; const f = codisFin();
  const amount = codisFinInt(o.amount, 1, 1e12); if(amount === null) return { ok:false, reason:'amount' };
  const date = o.date || codisFinToday(); if(!codisFinDateOk(date)) return { ok:false, reason:'date' };
  if(date > codisFinToday()) return { ok:false, reason:'future' };
  const desc = String(o.desc || '').trim().slice(0, 120); if(!desc) return { ok:false, reason:'desc' };
  const ref = String(o.ref || codisFinUid('dep')).slice(0, 120);
  return codisFinTx(()=>{
    const e = codisFinPush(f, { id:ref, ref:ref, type:'DEPOSIT', amount:amount, cur:'IQD', desc:desc, cat:'', src:String(o.src || '').trim().slice(0, 80), date:date, at:codisFinIso(), note:String(o.note || '').trim().slice(0, 300) || undefined });
    if(!e) return { ok:false, reason:'dup' };
    if(e.note === undefined) delete e.note;
    return { ok:true, entry:e, balance:codisFinBalance(f) };
  });
}
/* ---------- المصروف / السحب اليدوي ---------- */
function codisFinExpenseNow(o){
  o = o || {}; const f = codisFin();
  const amount = codisFinInt(o.amount, 1, 1e12); if(amount === null) return { ok:false, reason:'amount' };
  const date = o.date || codisFinToday(); if(!codisFinDateOk(date)) return { ok:false, reason:'date' };
  if(date > codisFinToday()) return { ok:false, reason:'future' };
  const name = String(o.name || '').trim().slice(0, 120); if(!name) return { ok:false, reason:'desc' };
  const cat = String(o.cat || 'other').slice(0, 40);
  const ref = String(o.ref || codisFinUid('exp')).slice(0, 120);
  if(codisFinBalance(f) - amount < 0 && !CodisLimits.bypass('fin.nonnegative')) return { ok:false, reason:'funds', need:amount - codisFinBalance(f), balance:codisFinBalance(f) };
  return codisFinTx(()=>{
    const e = codisFinPush(f, { id:ref, ref:ref, type:'EXPENSE', amount:-amount, cur:'IQD', desc:name, cat:cat, src:'', date:date, at:codisFinIso(), note:String(o.note || '').trim().slice(0, 300) || undefined });
    if(!e) return { ok:false, reason:'dup' };
    if(e.note === undefined) delete e.note;
    return { ok:true, entry:e, balance:codisFinBalance(f) };
  });
}
/* ---------- خصم مكافأة مالية (يُستدعى داخل CodisWallet.transact؛ يرجع كائناً بلا حفظ ذاتي) ---------- */
function codisFinRedeemIn(o){
  const f = codisFin(); o = o || {};
  if(codisFinNeedSetup(f)) return { ok:false, reason:'nosetup' };
  const amount = codisFinInt(o.iqd, 1, 1e12); if(amount === null) return { ok:false, reason:'amount' };
  const ref = 'rwd|' + String(o.uid || '');
  if(!o.uid) return { ok:false, reason:'amount' };
  if(f.ledger.some(x=>x.ref === ref)) return { ok:false, reason:'dup' };
  if(codisFinBalance(f) - amount < 0 && !CodisLimits.bypass('fin.nonnegative')) return { ok:false, reason:'funds', need:amount - codisFinBalance(f), balance:codisFinBalance(f) };
  const e = codisFinPush(f, { id:ref, ref:ref, type:'REWARD_REDEMPTION', amount:-amount, cur:'IQD', desc:String(o.name || 'مكافأة').slice(0, 120), cat:'rewards', src:'reward', date:codisFinToday(), at:codisFinIso(),
    meta:{ uid:String(o.uid), coins:Number(o.coins) || 0, rewardId:String(o.rewardId || '') } });
  if(!e) return { ok:false, reason:'dup' };
  return { ok:true, entry:e, balance:codisFinBalance(f) };
}

/* ---------- الراتب ---------- */
/* القاعدة السارية على شهر: من الأحدث للأقدم، أول قاعدة يقع استحقاقها (بيومها) في ذلك الشهر عند/بعد تاريخ بدايتها */
function codisFinSalaryFor(f, mk){
  const rules = f.salary.rules;
  for(let i = rules.length - 1; i >= 0; i--){
    const due = codisFinDueOf(mk, rules[i].day);
    if(due >= rules[i].from) return rules[i].amount > 0 ? { rule:rules[i], due:due } : null;
  }
  return null;
}
/* تعويض المستحق الفائت: كل شهر حلّ استحقاقه ولم يُسجَّل يُضاف مرة واحدة (مرجع sal|YYYY-MM)، بتاريخ الاستحقاق الأصلي. لا رواتب قبل بداية الجدولة */
function codisFinCatchUpIn(f, todayKey){
  todayKey = todayKey || codisFinToday();
  if(!f.setup.done || f.work !== 'employee' || !f.salary.rules.length) return [];
  const added = []; let mk = codisFinMonthOf(f.salary.rules[0].from), guard = 0; const endMk = codisFinMonthOf(todayKey);
  while(mk <= endMk && guard++ < 1200){
    const hit = codisFinSalaryFor(f, mk);
    if(hit && hit.due <= todayKey){
      const ref = 'sal|' + mk;
      if(!f.ledger.some(x=>x.ref === ref || (x.type === 'SALARY' && codisFinMonthOf(x.due) === mk))){
        const e = codisFinPush(f, { id:ref, ref:ref, type:'SALARY', amount:hit.rule.amount, cur:'IQD', desc:'راتب ' + codisFinMonthName(mk), cat:'', src:'salary', date:hit.due, due:hit.due, at:codisFinIso() });
        if(e) added.push(e);
      }
    }
    mk = codisFinNextMonth(mk);
  }
  return added;
}
function codisFinCatchUp(){
  const f = codisFin(); if(!f.setup.done || f.work !== 'employee') return 0;
  const r = codisFinTx(()=>{ const a = codisFinCatchUpIn(f); return a.length ? { ok:true, added:a.length } : { ok:true, noop:true, added:0 }; });
  return (r && r.added) || 0;
}
/* تغيير الراتب: قاعدة جديدة تسري على الاستحقاقات من تاريخ يحدده المستخدم (≥ اليوم)؛ السجلات السابقة لا تُمس */
function codisFinSetSalary(o){
  o = o || {}; const f = codisFin();
  const amount = codisFinInt(o.amount, 0, 1e12), day = codisFinInt(o.day, 1, 31); if(amount === null) return { ok:false, reason:'amount' }; if(day === null) return { ok:false, reason:'day' };
  const from = o.from || codisFinMonthStart(codisFinNextMonth(codisFinMonthOf(codisFinToday())));
  if(!codisFinDateOk(from)) return { ok:false, reason:'date' }; if(from < codisFinToday()) return { ok:false, reason:'past' };
  return codisFinTx(()=>{
    f.salary.rules.push({ id:codisFinUid('rule'), amount:amount, day:day, from:from, createdAt:codisFinIso() });
    f.salary.rules.sort((a, b)=>a.from < b.from ? -1 : a.from > b.from ? 1 : (a.createdAt < b.createdAt ? -1 : 1));
    return { ok:true, added:codisFinCatchUpIn(f).length };
  });
}
function codisFinNextSalary(f){
  f = f || codisFin(); if(!f.setup.done || f.work !== 'employee' || !f.salary.rules.length) return null;
  const today = codisFinToday(); let mk = codisFinMonthOf(today), guard = 0;
  while(guard++ < 30){ const hit = codisFinSalaryFor(f, mk); if(hit && hit.due >= today && !f.ledger.some(x=>x.ref === 'sal|' + mk)) return { due:hit.due, amount:hit.rule.amount }; mk = codisFinNextMonth(mk); }
  return null;
}

/* الملف المالي: طبيعة العمل ومصدر الدخل والمتوسط التقديري (للعلم فقط — لا يدخل الرصيد). التحوّل إلى «موظف» يتطلب راتباً يسري من اليوم فصاعداً (لا أثر رجعي) */
function codisFinSetProfile(o){
  o = o || {}; const f = codisFin(); if(!f.setup.done) return { ok:false, reason:'nosetup' };
  const work = o.work === 'employee' ? 'employee' : 'freelance'; let rule = null;
  if(work === 'employee' && !f.salary.rules.length){
    const s2 = o.salary || {}, amount = codisFinInt(s2.amount, 1, 1e12), day = codisFinInt(s2.day, 1, 31);
    if(amount === null || day === null) return { ok:false, reason:'amount' }; if(!codisFinDateOk(s2.from)) return { ok:false, reason:'date' }; if(s2.from < codisFinToday()) return { ok:false, reason:'past' };
    rule = { id:codisFinUid('rule'), amount:amount, day:day, from:s2.from, createdAt:codisFinIso() };
  }
  return codisFinTx(()=>{
    f.work = work; f.source = String(o.source || '').trim().slice(0, 80); f.avgIncome = o.avg ? codisFinInt(o.avg, 0, 1e12) : null;
    if(rule) f.salary.rules.push(rule);
    return { ok:true, added:codisFinCatchUpIn(f).length };
  });
}

/* ---------- سعر الصرف ---------- */
function codisFinRate(){ return codisFin().fx.rate || 0; }
function codisFinCoinOfIqd(iqd, rate){ rate = rate || codisFinRate() || 40; return Math.round(Number(iqd) * 100 / rate) / 100; }
function codisFinCoinOfMinutes(min){ return Math.round(Number(min) * 100 / 2) / 100; }   /* 1 كوين = دقيقتان ثابتة — لا علاقة لها بسعر الصرف */
function codisFinFxStatus(){
  const f = codisFin(), cur = codisFinMonthOf(codisFinToday());
  const changes = f.fxLog.filter(x=>x.kind === 'change'), last = changes.length ? changes[changes.length - 1] : null;
  const used = !!last && last.month === cur;
  return { rate:f.fx.rate, canChange:!used, usedThisMonth:used, last:last, nextAllowed:used ? codisFinMonthStart(codisFinNextMonth(cur)) : codisFinToday(), month:cur, log:f.fxLog.slice() };
}
/* تغيير السعر: مرة واحدة بالشهر التقويمي (بتوقيت بغداد). بعدها يعاد تسعير المكافآت المالية بقيمتها بالدينار الثابتة */
function codisFinChangeRate(newRate){
  const f = codisFin(), rates = codisFinRates();
  if(rates.indexOf(newRate) === -1) return { ok:false, reason:'rate' };
  if(!f.setup.done) return { ok:false, reason:'nosetup' };
  if(newRate === f.fx.rate) return { ok:false, reason:'same' };
  const st = codisFinFxStatus();
  if(st.usedThisMonth && !CodisLimits.bypass('fin.fxMonthly')) return { ok:false, reason:'monthly', nextAllowed:st.nextAllowed };
  const prev = f.fx.rate;
  return codisFinTx(()=>{
    const at = codisFinIso();
    f.fx = { rate:newRate, setAt:at };
    f.fxLog.push({ id:codisFinUid('fx'), kind:'change', from:prev, to:newRate, at:at, month:codisFinMonthOf(codisFinToday()) });
    const rp = codisFinReprice();
    return { ok:true, from:prev, to:newRate, repriced:rp };
  }, true);
}

/* ================= مصفوفة نطاقات البطاقات الـ23 =================
   المرجع = سعر البطاقة الفعلي من النموذج (أو من codisFixedDefs). النطاق [min, max] بالكوينز، الحدّان شاملان.
   القاعدة: الحد الأعلى = أقرب سعر مرجعي أعلى بين الـ23 (يتداخل عمداً مع بطاقة ثانية حيث حدّد المالك ذلك)، والجدول التالي هو ما حدّده المالك حرفياً:
     أستاذ 10–12.5 · محطة 7 أيام 12.5–18.75 · حدثية عادية 18.75–37.5 · حدثية مهمة 37.5–50 · يومية C 25–37.5 · شهرية عادية 75–100 · شهرية مهمة 100–125 · حدثية حرجة 125–150 · شهرية حرجة 200–375
     واستثناء الأعلى: الشهرية S 11,250–18,750 والشهرية SS من 30,000 نزولاً إلى 18,750 (الحد المشترك 18,750).
   الاتحاد يغطي [10, 30000] بلا فجوة (يفحصه codisFinMatrixCheck). */
function codisFinCards(){
  if(codisFinCards.c) return codisFinCards.c;
  const RN = { C:'شائعة', B:'غير شائعة', A:'نادرة', S:'نادرة جداً', SS:'أسطورية' };
  const pool = (scope, room, rid, ref, min, max)=>({ id:scope + '_' + rid, name:({ daily:'يومية', weekly:'أسبوعية', monthly:'شهرية' })[scope] + ' ' + rid + ' — ' + RN[rid], room:room, rarity:rid, scope:scope, roomKey:room === 'tasks' ? 'tasks' : room, ref:ref, min:min, max:max, fixed:false, fixedId:null, type:'pool' });
  const fx = (fid, name, ref, min, max, o)=>({ id:fid, name:name, room:'habits', rarity:null, scope:'habit', roomKey:'habits', ref:ref, min:min, max:max, fixed:true, fixedId:fid, type:'fixed', group:o.group, imp:o.imp || null, period:o.period || null });
  const cf = (scope, rid)=>econCoinFor(rid, scope);
  const L = [
    { id:'learn', name:'مكافأة غرفة الأستاذ', room:'learn', rarity:null, scope:'learn', roomKey:'learn', ref:10, min:10, max:12.5, fixed:false, fixedId:null, type:'pool' },
    fx('fx_station7', 'محطة السبعة أيام', 12.5, 12.5, 18.75, { group:'station', period:'7d' }),
    fx('fx_rs_normal', 'مكافأة حدثية عادية', 18.75, 18.75, 37.5, { group:'event', imp:'normal' }),
    pool('daily', 'tasks', 'C', cf('daily', 'C'), cf('daily', 'C'), 37.5),
    fx('fx_rs_important', 'مكافأة حدثية مهمة', 37.5, 37.5, 50, { group:'event', imp:'important' }),
    pool('daily', 'tasks', 'B', cf('daily', 'B'), cf('daily', 'B'), 75),
    fx('fx_ms_normal', 'مكافأة المحطة الشهرية — عادية', 75, 75, 100, { group:'station', period:'30d', imp:'normal' }),
    fx('fx_ms_important', 'مكافأة المحطة الشهرية — مهمة', 100, 100, 125, { group:'station', period:'30d', imp:'important' }),
    fx('fx_rs_critical', 'مكافأة حدثية حرجة', 125, 125, 150, { group:'event', imp:'critical' }),
    pool('daily', 'tasks', 'A', cf('daily', 'A'), cf('daily', 'A'), cf('weekly', 'C')),
    pool('weekly', 'weekly', 'C', cf('weekly', 'C'), cf('weekly', 'C'), 200),
    fx('fx_ms_critical', 'مكافأة المحطة الشهرية — حرجة', 200, 200, 375, { group:'station', period:'30d', imp:'critical' }),
    pool('weekly', 'weekly', 'B', cf('weekly', 'B'), cf('weekly', 'B'), cf('daily', 'S')),
    pool('daily', 'tasks', 'S', cf('daily', 'S'), cf('daily', 'S'), cf('monthly', 'C')),
    pool('monthly', 'monthly', 'C', cf('monthly', 'C'), cf('monthly', 'C'), cf('daily', 'SS')),
    pool('daily', 'tasks', 'SS', cf('daily', 'SS'), cf('daily', 'SS'), cf('weekly', 'A')),
    pool('weekly', 'weekly', 'A', cf('weekly', 'A'), cf('weekly', 'A'), cf('monthly', 'B')),
    pool('monthly', 'monthly', 'B', cf('monthly', 'B'), cf('monthly', 'B'), cf('weekly', 'S')),
    pool('weekly', 'weekly', 'S', cf('weekly', 'S'), cf('weekly', 'S'), cf('monthly', 'A')),
    pool('monthly', 'monthly', 'A', cf('monthly', 'A'), cf('monthly', 'A'), cf('weekly', 'SS')),
    pool('weekly', 'weekly', 'SS', cf('weekly', 'SS'), cf('weekly', 'SS'), cf('monthly', 'S')),
    pool('monthly', 'monthly', 'S', cf('monthly', 'S'), cf('monthly', 'S'), 18750),
    pool('monthly', 'monthly', 'SS', cf('monthly', 'SS'), 18750, cf('monthly', 'SS'))   /* الاتجاه العكسي: المرجع 30,000 هو الحد الأعلى */
  ];
  L.forEach(c=>{ c.reversed = c.ref === c.max && c.min !== c.max; Object.freeze(c); });
  return (codisFinCards.c = Object.freeze(L));
}
function codisFinCardById(id){ return codisFinCards().find(c=>c.id === id) || null; }
function codisFinInRange(c, coin){ const v = Math.round(Number(coin) * 100) / 100; return v >= c.min - 1e-9 && v <= c.max + 1e-9; }
function codisFinCardsFor(coin){ return codisFinCards().filter(c=>codisFinInRange(c, coin)); }
/* فحص المصفوفة: 23 بطاقة · المراجع تطابق النموذج · لا فجوة بين 10 و30,000 */
function codisFinMatrixCheck(){
  const cards = codisFinCards(), out = { ok:true, count:cards.length, problems:[] };
  if(cards.length !== 23) out.problems.push('count ' + cards.length);
  const D = codisFixedDefs();
  cards.forEach(c=>{
    if(c.min > c.max) out.problems.push('min>max ' + c.id);
    if(c.fixed){ const d = D.rewards.find(x=>x.id === c.fixedId); if(!d || d.coin !== c.ref) out.problems.push('fixed ref ' + c.id); }
    else if(c.id === 'learn'){ if(c.ref !== ECON_LEARN_COIN) out.problems.push('learn ref'); }
    else if(econCoinFor(c.rarity, c.scope) !== c.ref) out.problems.push('pool ref ' + c.id);
    if(c.ref < c.min - 1e-9 || c.ref > c.max + 1e-9) out.problems.push('ref outside ' + c.id);
  });
  const edges = cards.slice().sort((a, b)=>a.min - b.min || a.max - b.max); let reach = codisFinMinCoin();
  if(edges[0].min > reach) out.problems.push('start gap ' + edges[0].min);
  edges.forEach(c=>{ if(c.min > reach + 1e-9) out.problems.push('gap ' + reach + '→' + c.min); if(c.max > reach) reach = c.max; });
  if(reach < codisFinMaxCoin()) out.problems.push('end gap at ' + reach);
  out.ok = out.problems.length === 0; return out;
}

/* ================= التصنيف الذكي (محلي، بلا خدمة خارجية) =================
   عاملان معاً: (1) المعنى: قاموس مجالات ← تقارب كل مجال مع كل غرفة · (2) السعر: البطاقات التي يقع السعر الدقيق داخل نطاقها فقط (لا «أقرب سعر»).
   الدرجة = 0.65 × تقارب المعنى + 0.35 × تقارب السعر داخل النطاق. غير الغامض يُحسم؛ الغامض (لا مجال معروف + أكثر من غرفة ممكنة) يعرض اقتراحات. */
function codisFinLex(){
  return codisFinLex.c || (codisFinLex.c = [
    { dom:'food', label:'طعام', aff:{ tasks:.92, learn:.08, weekly:.55, monthly:.12, habits:.3 }, kw:['شاورم', 'برجر', 'برغر', 'بيتزا', 'ساندويج', 'ساندوتش', 'فلافل', 'سمك', 'دجاج', 'كباب', 'تكه', 'مطعم', 'وجبه', 'اكل', 'غدا', 'عشا', 'فطور', 'لفه', 'صمون', 'مشاوي', 'باجه', 'برياني', 'تمن', 'دولمه', 'بيض', 'ستيك', 'مندي', 'فروج', 'كنتاكي'] },
    { dom:'sweet', label:'حلويات', aff:{ tasks:.86, learn:.2, weekly:.5, monthly:.1, habits:.45 }, kw:['حلوي', 'حلو', 'ايس', 'ايسكريم', 'كيك', 'شوكولات', 'شوكلات', 'كنافه', 'بقلاو', 'دونات', 'وافل', 'كريب', 'بسكوت', 'معجنات', 'جكليت', 'كاكاو', 'لقيمات', 'زلابيه', 'مهلبيه'] },
    { dom:'drink', label:'مشروبات', aff:{ tasks:.9, learn:.36, weekly:.4, monthly:.05, habits:.3 }, kw:['قهوه', 'جاي', 'شاي', 'عصير', 'كولا', 'بيبسي', 'مشروب', 'نسكافيه', 'كابتشينو', 'لاتيه', 'سموذي', 'ميلك', 'شيك', 'مايه', 'نرجيله', 'ارجيله'] },
    { dom:'market', label:'سوق وتسوّق صغير', aff:{ tasks:.82, learn:.05, weekly:.6, monthly:.2, habits:.2 }, kw:['سوق', 'ماركت', 'بقاله', 'تسوق', 'تبضع', 'مول', 'متجر', 'محل', 'خضار', 'فاكهه'] },
    { dom:'shopping', label:'ملابس ومقتنيات', aff:{ tasks:.12, learn:.02, weekly:.45, monthly:.88, habits:.15 }, kw:['ملابس', 'قميص', 'بنطلون', 'حذاء', 'جزمه', 'ساعه يد', 'عطر', 'شنطه', 'جاكيت', 'نظارات', 'خاتم', 'قلاده', 'ثوب', 'دشداشه', 'بدله', 'كوتي', 'ملبس', 'فستان'] },
    { dom:'tech', label:'أجهزة', aff:{ tasks:.03, learn:.02, weekly:.2, monthly:.92, habits:.1 }, kw:['موبايل', 'جوال', 'ايفون', 'لابتوب', 'حاسبه', 'حاسوب', 'سماعه', 'سماعات', 'تابلت', 'كاميرا', 'شاشه', 'تلفزيون', 'بلايستيشن', 'كونسول', 'ماوس', 'كيبورد', 'ساعه ذكيه', 'شاحن', 'راوتر', 'طابعه'] },
    { dom:'watch', label:'مشاهدة وترفيه', aff:{ tasks:.9, learn:.26, weekly:.5, monthly:.1, habits:.3 }, kw:['مشاهد', 'فلم', 'فيلم', 'مسلسل', 'مباراه', 'ماتش', 'يوتيوب', 'نتفلكس', 'نتفليكس', 'انمي', 'كارتون', 'بث', 'تلفزيون', 'سهره', 'مسرحيه', 'برنامج'] },
    { dom:'game', label:'ألعاب', aff:{ tasks:.86, learn:.12, weekly:.5, monthly:.2, habits:.3 }, kw:['قيمنق', 'لعب', 'العاب', 'لعبه', 'ببجي', 'فورتنايت', 'فيفا', 'دومينو', 'شطرنج', 'طاوله', 'ورق', 'بلوت', 'بلياردو', 'بلاي'] },
    { dom:'learn', label:'ثقافة وهدوء', aff:{ tasks:.38, learn:.95, weekly:.12, monthly:.05, habits:.1 }, kw:['موسيق', 'استماع', 'اغنيه', 'اغاني', 'بودكاست', 'كتاب', 'قراءه', 'رواي', 'مجله', 'شعر', 'اذاعه', 'تأمل', 'تامل', 'رسم', 'تلوين', 'تعلم', 'دوره', 'كورس'] },
    { dom:'outing', label:'طلعة', aff:{ tasks:.3, learn:.04, weekly:.9, monthly:.45, habits:.25 }, kw:['طلعه', 'طلعات', 'كافيه', 'كوفي', 'حديقه', 'متنزه', 'سينما', 'بولينج', 'كورنيش', 'نزهه', 'تمشي', 'ملاهي', 'العاب مائيه', 'سباحه', 'مسبح', 'كرنفال', 'مقهى', 'مقهي'] },
    { dom:'trip', label:'سفر ورحلات', aff:{ tasks:.02, learn:0, weekly:.32, monthly:.95, habits:.2 }, kw:['سفر', 'رحله', 'سياحه', 'فندق', 'مخيم', 'تخييم', 'شمال', 'زياره', 'عمره', 'بحر', 'طيران', 'تذكره', 'اجازه'] },
    { dom:'rest', label:'راحة', aff:{ tasks:.86, learn:.3, weekly:.45, monthly:.2, habits:.4 }, kw:['نوم', 'قيلوله', 'راحه', 'استرخاء', 'نايم', 'ارتياح', 'سرير', 'يوم راحه', 'اجازه قصيره'] },
    { dom:'care', label:'عناية وصحة', aff:{ tasks:.55, learn:.1, weekly:.62, monthly:.45, habits:.5 }, kw:['مساج', 'تدليك', 'حلاقه', 'حلاق', 'صالون', 'عنايه', 'جيم', 'نادي', 'رياضه', 'علاج', 'طبيب', 'سبا', 'بشره', 'استحمام', 'حمام', 'ساونا', 'تجميل', 'مانيكير'] },
    { dom:'social', label:'اجتماعيات وهدايا', aff:{ tasks:.3, learn:.04, weekly:.85, monthly:.5, habits:.25 }, kw:['عزومه', 'ضيافه', 'اصدقاء', 'صحاب', 'هديه', 'هدايا', 'وليمه', 'حفله', 'عرس', 'عيد', 'جمعه', 'ضيوف', 'لمه'] },
    { dom:'habit', label:'عادات وإنجازات', aff:{ tasks:.22, learn:.1, weekly:.3, monthly:.35, habits:.95 }, kw:['تدخين', 'سيجاره', 'مقاومه', 'عاده', 'محطه', 'انجاز', 'امتناع', 'اقلاع', 'تخلص'] }
  ]);
}
function codisFinNormText(s){
  return codisNormText(s).replace(/[چ]/g, 'ج').replace(/[گ]/g, 'ك').replace(/[پ]/g, 'ب').replace(/[ڤ]/g, 'ف').replace(/ؤ/g, 'و').replace(/ئ/g, 'ي').replace(/[^a-z0-9ء-ي\s]/g, ' ').replace(/\s+/g, ' ').trim();
}
function codisFinTokens(name){
  const out = []; codisFinNormText(name).split(' ').forEach(t=>{
    if(!t) return; out.push(t);
    let u = t; if(u.length > 3 && u.indexOf('ال') === 0){ u = u.slice(2); out.push(u); }
    if(u.length > 3 && /^[ولب]/.test(u)){ out.push(u.slice(1)); if(u.length > 4 && u.indexOf('لل') === 0) out.push(u.slice(2)); }
  });
  return out;
}
/* المجالات المطابقة للاسم مرتبة بعدد الكلمات المطابقة */
function codisFinDomains(name){
  const toks = codisFinTokens(name), full = ' ' + codisFinNormText(name) + ' ', res = [];
  codisFinLex().forEach(d=>{
    let n = 0;
    d.kw.forEach(k=>{
      const nk = codisFinNormText(k);
      if(nk.indexOf(' ') !== -1){ if(full.indexOf(' ' + nk) !== -1) n += 2; return; }
      if(toks.some(t=>t.length >= nk.length - 1 && t.indexOf(nk) === 0)) n++;
    });
    if(n > 0) res.push({ dom:d.dom, label:d.label, n:n, aff:d.aff });
  });
  return res.sort((a, b)=>b.n - a.n);
}
function codisFinPriceFit(c, coin){
  const w = c.max - c.min; if(w <= 0) return 1;
  const pos = c.reversed ? (c.max - coin) / w : (coin - c.min) / w;   /* قرب السعر من المرجع داخل النطاق */
  return 1 - Math.max(0, Math.min(1, pos)) * 0.5;
}
function codisFinDefaultAff(){ return { tasks:.5, learn:.4, weekly:.5, monthly:.4, habits:.3 }; }
/* name + coin(الدقيق) → { ok, reason?, coin, domains, candidates:[{card,score,sem,fit}], best, ambiguous, suggestions } */
function codisFinClassify(name, coin){
  coin = Math.round(Number(coin) * 100) / 100;
  if(!isFinite(coin) || coin < codisFinMinCoin() - 1e-9) return { ok:false, reason:'low', coin:coin };
  if(coin > codisFinMaxCoin() + 1e-9) return { ok:false, reason:'high', coin:coin };
  const doms = codisFinDomains(name), known = doms.length > 0;
  let aff = codisFinDefaultAff();
  if(known){   /* مزج المجالات المطابقة بأوزان عدد الكلمات */
    const tot = doms.reduce((s, d)=>s + d.n, 0); aff = { tasks:0, learn:0, weekly:0, monthly:0, habits:0 };
    doms.forEach(d=>{ Object.keys(aff).forEach(k=>{ aff[k] += d.aff[k] * d.n / tot; }); });
  }
  const cands = codisFinCardsFor(coin).map(c=>{
    const sem = aff[c.roomKey] === undefined ? .3 : aff[c.roomKey], fit = codisFinPriceFit(c, coin);
    return { card:c, sem:sem, fit:fit, score:Math.round((0.65 * sem + 0.35 * fit) * 1e6) / 1e6 };
  }).sort((a, b)=>b.score - a.score || (a.card.max - a.card.min) - (b.card.max - b.card.min) || (a.card.id < b.card.id ? -1 : 1));
  if(!cands.length) return { ok:false, reason:'nocard', coin:coin };
  const rooms = {}; cands.forEach(c=>{ rooms[c.card.roomKey] = 1; });
  const multiRoom = Object.keys(rooms).length > 1;
  const ambiguous = multiRoom && (!known || (cands.length > 1 && cands[0].score - cands[1].score < 0.06 && cands[0].card.roomKey !== cands[1].card.roomKey));
  return { ok:true, coin:coin, domains:doms.map(d=>({ dom:d.dom, label:d.label })), candidates:cands, best:cands[0], ambiguous:ambiguous, suggestions:cands.slice(0, 3) };
}

/* ================= المكافآت التلقائية (مالية / وقتية) =================
   كل عنصر تلقائي في data.settings.rewardItems يحمل fin = { v:1, kind:'financial'|'time', iqd|minutes, card, dom }.
   القيمة الدقيقة بالكوين مشتقة دائماً (دينار ÷ السعر الحالي، أو دقائق ÷ 2) ولا تُقرَّب لأقرب فئة. القيمة بالدينار/الدقائق هي الأصل. */
function codisFinItemOk(v){
  try{
    if(!v || typeof v !== 'object' || v.v !== 1) return null;
    const kind = v.kind === 'financial' ? 'financial' : v.kind === 'time' ? 'time' : null; if(!kind) return null;
    const o = { v:1, kind:kind, card:typeof v.card === 'string' ? v.card.slice(0, 40) : '', dom:typeof v.dom === 'string' ? v.dom.slice(0, 20) : '' };
    if(kind === 'financial'){ const iqd = codisFinInt(v.iqd, 1, 1e12); if(iqd === null) return null; o.iqd = iqd; }
    else { const m = codisFinInt(v.minutes, 1, 1440); if(m === null) return null; o.minutes = m; }
    const c = Number(v.coin); o.coin = isFinite(c) && c >= 0 && c <= 1e6 ? Math.round(c * 100) / 100 : 0;   /* لقطة آخر قيمة (احتياط إن لم يُضبط سعر صرف) */
    if(v.oor === true) o.oor = true;
    return o;
  }catch(e){ return null; }
}
/* قيمة العنصر الحالية بالكوين (مصدر وحيد لـeconEffCoin) */
function codisFinItemCoin(item){
  const fin = item && item.fin; if(!fin) return 0;
  if(fin.kind === 'time') return codisFinCoinOfMinutes(fin.minutes);
  const rate = codisFinRate(); return rate ? codisFinCoinOfIqd(fin.iqd, rate) : (fin.coin || 0);
}
/* نوع استخدام عنصر مخزون/كتالوج: 'FINANCIAL' | 'TIME' | 'LEGACY' */
function codisFinUseKind(it){ return (it && it.fin && it.fin.kind === 'financial') ? 'FINANCIAL' : (it && it.fin && it.fin.kind === 'time') ? 'TIME' : 'LEGACY'; }
/* مدة العنصر للمؤقت: الصريحة المحفوظة للتلقائي، وإلا استخراج الاسم للقديم (لا يُستخرج أبداً لمكافأة مالية) */
function codisDurOf(it){
  if(it && it.fin) return it.fin.kind === 'time' ? { min:it.fin.minutes, why:'مدة محفوظة' } : null;
  return CodisDuration.parse(it && it.name);
}
/* حقول التموضع للبطاقة: كتالوج عادي ← room/rarity · كرت خاص ← variantOf */
function codisFinPlacement(card){
  if(card.fixed) return { room:'habits', rarity:econCfg().rarities[0].id, variantOf:card.fixedId, weight:0 };
  if(card.room === 'learn') return { room:'learn', rarity:econCfg().rarities[0].id, variantOf:null, weight:10 };
  return { room:card.room, rarity:card.rarity, variantOf:null, weight:10 };
}
function codisFinApplyPlacement(item, card){
  const p = codisFinPlacement(card);
  item.room = p.room; item.rarity = p.rarity; item.weight = p.weight;
  if(p.variantOf){ item.variantOf = p.variantOf; item.fixed = false; const d = codisFixedById(p.variantOf); if(d){ item.cardKind = 'special'; item.cardGroup = d.group; item.stationPeriod = d.period || null; item.habitImp = d.imp || null; } }
  else { delete item.variantOf; delete item.cardKind; delete item.cardGroup; delete item.stationPeriod; delete item.habitImp; }
  if(item.fin) item.fin.card = card.id;
}
/* يُستدعى من econNormalizeItems: يتحقق من حقول العنصر التلقائي ويشتق الباقي (آمن وقت التحميل) */
function codisFinReconcileItems(s){
  try{
    (s.rewardItems || []).forEach(it=>{
      if(!it || typeof it !== 'object') return;
      it.fin = codisFinItemOk(it.fin) || undefined; if(it.fin === undefined) delete it.fin;
      if(!it.fin){ delete it.variantOf; return; }
      const card = codisFinCardById(it.fin.card);
      if(card){ if(card.fixed){ it.room = 'habits'; it.weight = 0; it.variantOf = card.fixedId; const d = codisFixedById(card.fixedId); if(d){ it.cardKind = 'special'; it.cardGroup = d.group; it.stationPeriod = d.period || null; it.habitImp = d.imp || null; } } else { delete it.variantOf; } }
      else delete it.variantOf;
    });
  }catch(e){}
}
/* إنشاء مكافأة تلقائية. o = { name, kind, iqd|minutes, cardId?, stickerId? } — يحفظ الدقيق ولا يقرّب لأقرب فئة */
function codisFinCreateReward(o){
  o = o || {}; const f = codisFin();
  const name = String(o.name || '').trim().slice(0, 120); if(!name) return { ok:false, reason:'name' };
  const kind = o.kind === 'financial' ? 'financial' : o.kind === 'time' ? 'time' : null; if(!kind) return { ok:false, reason:'kind' };
  let iqd = null, minutes = null, coin;
  if(kind === 'financial'){
    if(!f.setup.done || !f.fx.rate) return { ok:false, reason:'nosetup' };
    iqd = codisFinInt(o.iqd, 1, 1e12); if(iqd === null) return { ok:false, reason:'amount' };
    coin = codisFinCoinOfIqd(iqd, f.fx.rate);
  } else { minutes = codisFinInt(o.minutes, 1, 1440); if(minutes === null) return { ok:false, reason:'amount' }; coin = codisFinCoinOfMinutes(minutes); }
  const cls = codisFinClassify(name, coin); if(!cls.ok) return { ok:false, reason:cls.reason, coin:coin, min:codisFinMinCoin(), max:codisFinMaxCoin() };
  let pick = cls.best;
  if(o.cardId){ pick = cls.candidates.find(c=>c.card.id === o.cardId); if(!pick) return { ok:false, reason:'range', coin:coin }; }
  else if(cls.ambiguous && !o.force) return { ok:false, reason:'ambiguous', coin:coin, suggestions:cls.suggestions };
  const card = pick.card, now = econNowIso(), taken = {}; data.settings.rewardItems.forEach(x=>{ if(x && x.id) taken[x.id] = true; });
  const p = codisFinPlacement(card), id = econStableId('reward', p.room, name, taken);
  const dom = cls.domains.length ? cls.domains[0].dom : '';
  const item = { id:id, name:name, rarity:p.rarity, weight:p.weight, coinValue:null, storePrice:null, stickerId:codisStickerIdOk(o.stickerId), enabled:true, room:p.room, createdAt:now, updatedAt:now,
    fin:{ v:1, kind:kind, card:card.id, dom:dom, coin:coin } };
  if(kind === 'financial') item.fin.iqd = iqd; else item.fin.minutes = minutes;
  return codisFinTx(()=>{
    data.settings.rewardItems.push(item);
    codisFinReconcileItems(data.settings);
    return { ok:true, item:item, card:card, coin:coin };
  }, true);
}
/* إعادة التسعير بعد تغيير سعر الصرف (يُستدعى داخل معاملة): القيمة بالدينار ثابتة؛ القيمة بالكوين تُشتق من السعر الجديد؛ البطاقة تُعاد تقييمها.
   كتالوج + مخزون غير مستخدم فقط — المستخدمة والسجلات التاريخية لا تُمس. لا يضيع اسم ولا وصف ولا ستيكر ولا إعداد. */
function codisFinReprice(){
  const rate = codisFinRate(); const res = { moved:0, items:0, inv:0, oor:0 };
  if(!rate) return res;
  const cardOf = (fin)=>codisFinCardById(fin.card);
  data.settings.rewardItems.forEach(it=>{
    if(!it || !it.fin || it.fin.kind !== 'financial') return;
    const coin = codisFinCoinOfIqd(it.fin.iqd, rate); it.fin.coin = coin; res.items++;
    const cur = cardOf(it.fin);
    if(cur && codisFinInRange(cur, coin)){ delete it.fin.oor; return; }
    const cls = codisFinClassify(it.name, Math.max(codisFinMinCoin(), Math.min(codisFinMaxCoin(), coin)));
    let target = null;
    if(cls.ok && coin >= codisFinMinCoin() - 1e-9 && coin <= codisFinMaxCoin() + 1e-9){ target = cls.best.card; delete it.fin.oor; }
    else { /* خارج المجال 10–30,000: تبقى بأقرب بطاقة ممكنة بقيمتها الدقيقة مع علامة */
      target = coin < codisFinMinCoin() ? codisFinCardById('learn') : codisFinCardById('monthly_SS'); it.fin.oor = true; res.oor++;
    }
    if(target && (!cur || target.id !== cur.id)){ codisFinApplyPlacement(it, target); it.updatedAt = econNowIso(); res.moved++; }
  });
  codisFinReconcileItems(data.settings);
  (data.inventory.items || []).forEach(x=>{
    if(!x || x.status !== 'owned' || !x.fin || x.fin.kind !== 'financial') return;
    x.fin.coin = codisFinCoinOfIqd(x.fin.iqd, rate); x.coinValue = econCN(x.fin.coin, 0, 0, 1000000); res.inv++;
    const cat = x.rewardId ? data.settings.rewardItems.find(r=>r && r.id === x.rewardId) : null;
    if(cat && cat.fin && !codisSlotOf(x)){ const rar = econRarityById(cat.rarity); if(rar){ x.rarity = rar.id; x.rarityName = rar.name; x.rarityTone = rar.tone; x.rarityOrder = rar.order; x.room = cat.room; } }
  });
  return res;
}
