/* ================= CODIS-TEACHER-TIERS (3.29.0): ندرة غرفة الأستاذ المستقلة — برونزية · فضية · ذهبية =================
   • مستقلة عن C/B/A/S/SS: معرّفات ثابتة (bronze · silver · gold) لا تظهر في econCfg().rarities ولا تغيّر أوزانها ولا Pity ولا سجلات غرفة العمليات.
   • الاحتمالات الابتدائية مشتقة من econModel().odds (المصدر الوحيد): برونزية = C+B (88%) · فضية = A (9%) · ذهبية = S+SS (3%).
   • التكيّف = نفس econAdaptiveOdds ونفس econCfg().adaptive (daily/weekly) — مُمرَّرة بلائحة الدرجات الثلاث بدل الخمس؛ لا معادلة جديدة.
   • كل ما هنا function declarations: آمن وقت التحميل (لا يقرأ const ولا data) — باستثناء الدوال التي تقرأ econCfg() وقت التشغيل فقط.
   • قيمة المكافأة العادية = مرجع الدرجة (ref) = حدّها الأدنى 10 / 12.5 / 20 (نفس قاعدة بطاقات المصفوفة: المرجع = أول النطاق). المصدر الوحيد: codisTeacherCoin. */
function codisTeacherTiers(){
  if(codisTeacherTiers.c) return codisTeacherTiers.c;
  const od = econModel().odds, r6 = x=>Math.round(x * 1e6) / 1e6;
  const L = [
    { id:'bronze', ar:'برونزية', en:'Bronze', order:1, tone:'bronze', min:10,   max:12.5, maxOpen:true,  weight:r6(od.C + od.B),  from:'C+B' },
    { id:'silver', ar:'فضية',    en:'Silver', order:2, tone:'silver', min:12.5, max:20,   maxOpen:true,  weight:r6(od.A),         from:'A' },
    { id:'gold',   ar:'ذهبية',   en:'Gold',   order:3, tone:'gold',   min:20,   max:30,   maxOpen:false, weight:r6(od.S + od.SS), from:'S+SS' }
  ];
  L.forEach(t=>{ t.name = t.ar; t.ref = t.min; t.coinValue = t.ref; t.enabled = true; Object.freeze(t); });
  return (codisTeacherTiers.c = Object.freeze(L));
}
function codisTeacherTierById(id){ const L = codisTeacherTiers(); for(let i = 0; i < L.length; i++) if(L[i].id === id) return L[i]; return null; }
function codisTeacherTierOk(id){ return (typeof id === 'string' && codisTeacherTierById(id)) ? id : ''; }
function codisTeacherToneOk(tone){ return typeof tone === 'string' && !!tone && codisTeacherTierOk(tone) !== ''; }
/* درجة عنصر/نتيجة/ممتلك: معرّف الدرجة إن وُجد، وإلا (سجلات قديمة C/c) = برونزية */
function codisTeacherTierOf(x){ return (x && (codisTeacherTierOk(x.rarity) || (codisTeacherToneOk(x.rarityTone) ? x.rarityTone : ''))) || 'bronze'; }
function codisTeacherCoin(id){ return (codisTeacherTierById(id) || codisTeacherTiers()[0]).ref; }
/* الدرجة التي يقع فيها مبلغ (كوين) بنطاقات غير متداخلة: [10,12.5) · [12.5,20) · [20,30]. خارج 10–30 يرجع الأقرب (للأقل برونزية وللأعلى ذهبية) */
function codisTeacherTierForCoin(coin){
  const v = Math.round(Number(coin) * 100) / 100, L = codisTeacherTiers();
  if(!isFinite(v) || v < L[1].min - 1e-9) return L[0].id;
  return v < L[2].min - 1e-9 ? L[1].id : L[2].id;
}
/* تنقية لون الندرة المخزّن: الخمسة العامة + ألوان الأستاذ، وإلا 'c' (السلوك القديم) */
function codisToneOk(t){ return (econTones().indexOf(t) !== -1 || codisTeacherToneOk(t)) ? t : 'c'; }
/* الاحتمالات الابتدائية للدرجات (%) — مجموعها 100 */
function codisTeacherBaseOdds(){
  const L = codisTeacherTiers(), tot = L.reduce((s, t)=>s + t.weight, 0), o = {};
  L.forEach(t=>{ o[t.id] = t.weight / tot * 100; });
  return o;
}
/* التكيّف: econAdaptiveOdds نفسها بإعدادات econCfg().adaptive نفسها، على لائحة الدرجات الثلاث (الأولى = البرونزية تُخفَّض وتُوزَّع على الباقيتين بنسبة أوزانهما) */
function codisTeacherAdaptive(period, count){
  const cfg = { adaptive:econCfg().adaptive, rarities:codisTeacherTiers().map(t=>({ id:t.id, order:t.order, weight:t.weight })) };
  return econAdaptiveOdds(period, count, cfg);
}
