/* ===== CODIS-V35 · كتالوج كروت غرفة الأستاذ (محطة · حدثية) =====
   الكروت الخاصة عناصر حقيقية بالكتالوج (data.settings.rewardItems / punishItems) بمعرّفاتها التاريخية نفسها.
   codisFixedDefs() = مخطط الخانات فقط (القيمة/النوع/الصورة/الاسم الافتراضي) لا محتوى يُفرض عند كل تحميل.
   الاسم والستيكر والتفعيل وبقاء الكرت = بيانات المستخدم وتبقى. كل الدوال function (hoisted) ولا تقرأ const/let لاحقاً وقت التحميل (قاعدة 3.17.2). */

/* مصدر وحيد لتكلفة تجاوز عقوبات الأستاذ الخاصة (الإعدادات · النتيجة · الخصم · بطاقات التجاوز كلها تقرأ من هنا) */
function codisPenaltyPrice(group, key){
  const T = { station:{ LOW:31.25, MEDIUM:62.5, HIGH:125 }, event:{ normal:112.5, important:225, critical:750 } };
  return (T[group] && T[group][key]) || 0;
}
function codisImpAr(i){ return ({ normal:'عادية', important:'مهمة', critical:'حرجة' })[i] || ''; }

function codisFixedDefs(){
  if(codisFixedDefs.c) return codisFixedDefs.c;
  const R = (id, name, coin, o)=>Object.assign({ id:id, name:name, coin:coin, kind:'reward' }, o || {});
  const P = (id, name, sev, o)=>Object.assign({ id:id, name:name, sev:sev, kind:'punish' }, o, { cost:codisPenaltyPrice(o.group, o.group === 'event' ? o.imp : sev) });
  const sv = s=>({ LOW:'خفيفة', MEDIUM:'متوسطة', HIGH:'قوية' })[s];
  return (codisFixedDefs.c = {
    rewards:[
      R('fx_station7', 'محطة السبعة أيام', 12.5, { art:'milestone', store:12.5, tag:'station7', group:'station', period:'7d', label:'محطة · 7 أيام' }),
      R('fx_rs_normal', 'مكافأة حدثية عادية', 18.75, { art:'resistance', tag:'resist', group:'event', imp:'normal', label:'حدثية · عادية' }),
      R('fx_rs_important', 'مكافأة حدثية مهمة', 37.5, { art:'resistance', tag:'resist', group:'event', imp:'important', label:'حدثية · مهمة' }),
      R('fx_rs_critical', 'مكافأة حدثية حرجة', 125, { art:'resistance', tag:'resist', group:'event', imp:'critical', label:'حدثية · حرجة' }),
      R('fx_ms_normal', 'مكافأة المحطة الشهرية — عادية', 75, { art:'milestone', tag:'monthlyEvent', group:'station', period:'30d', imp:'normal', label:'محطة شهرية · عادية', oldName:'مكافأة حدثية عادية محسّنة' }),
      R('fx_ms_important', 'مكافأة المحطة الشهرية — مهمة', 100, { art:'milestone', tag:'monthlyEvent', group:'station', period:'30d', imp:'important', label:'محطة شهرية · مهمة', oldName:'مكافأة حدثية مهمة محسّنة' }),
      R('fx_ms_critical', 'مكافأة المحطة الشهرية — حرجة', 200, { art:'milestone', tag:'monthlyEvent', group:'station', period:'30d', imp:'critical', label:'محطة شهرية · حرجة', oldName:'مكافأة حدثية حرجة محسّنة' })
    ],
    punish:[
      P('fxp_st7_low', 'عقوبة محطة العادات — خفيفة', 'LOW', { tag:'st7', group:'station', label:'محطة · ' + sv('LOW') }),
      P('fxp_st7_med', 'عقوبة محطة العادات — متوسطة', 'MEDIUM', { tag:'st7', group:'station', label:'محطة · ' + sv('MEDIUM') }),
      P('fxp_st7_high', 'عقوبة محطة العادات — قوية', 'HIGH', { tag:'st7', group:'station', label:'محطة · ' + sv('HIGH') }),
      P('fxp_ev_normal', 'عقوبة حدثية عادية', 'LOW', { tag:'event', group:'event', imp:'normal', label:'حدثية · عادية' }),
      P('fxp_ev_important', 'عقوبة حدثية مهمة', 'MEDIUM', { tag:'event', group:'event', imp:'important', label:'حدثية · مهمة' }),
      P('fxp_ev_critical', 'عقوبة حدثية حرجة', 'HIGH', { tag:'event', group:'event', imp:'critical', label:'حدثية · حرجة' })
    ]
  });
}
function codisFixedById(id){ if(!id) return null; const d = codisFixedDefs(); return d.rewards.find(x=>x.id === id) || d.punish.find(x=>x.id === id) || null; }
function codisFixedFor(list, tag, imp){ return codisFixedDefs()[list].find(x=>x.tag === tag && (!imp || x.imp === imp)) || null; }
/* خانة الكرت الخاص لأي عنصر (كتالوج/مخزون/نتيجة)، أو null للعناصر العادية */
function codisSlotOf(x){
  if(!x || typeof x !== 'object') return null;
  return codisFixedById(x.fixedId) || (x.fixed ? codisFixedById(x.id) : null) || codisFixedById(x.rewardId) || null;
}
function codisCatalogItem(kind, id){ const l = kind === 'punish' ? data.settings.punishItems : data.settings.rewardItems; return l.find(x=>x && x.id === id) || null; }

/* ---------- ترحيل غير هدّام (يُستدعى من econNormalizeItems) ---------- */
function codisV35Dedupe(list){
  const seen = {};
  return list.filter(x=>{ if(!x || typeof x !== 'object' || !codisFixedById(x.id)) return true; if(seen[x.id]) return false; seen[x.id] = true; return true; });
}
/* حقول البنية مشتقة من المخطط دائماً (لا تُصدَّق من المخزَّن)؛ الاسم/الستيكر/التفعيل/التواريخ بيانات المستخدم ولا تُمس */
function codisV35Reconcile(s){
  try{
    const D = codisFixedDefs();
    D.rewards.forEach(d=>{
      const it = s.rewardItems.find(x=>x && x.id === d.id); if(!it) return;
      it.room = 'habits'; it.weight = 0; it.fixed = true; it.fixedCoin = d.coin; it.fixedStore = (d.store === undefined ? null : d.store);
      it.cardKind = 'special'; it.cardGroup = d.group; it.stationPeriod = d.period || null; it.habitImp = d.imp || null; it.coinValue = null; it.storePrice = null;
    });
    D.punish.forEach(d=>{
      const it = s.punishItems.find(x=>x && x.id === d.id); if(!it) return;
      it.room = 'habits'; it.severity = d.sev; it.fixed = true; it.fixedCost = d.cost; it.fixedGroup = d.tag;
      it.cardKind = 'special'; it.cardGroup = d.group; it.habitImp = d.imp || null; it.coinBypassCost = null;
    });
  }catch(e){}
}
/* مرة واحدة فقط لكل حساب (settings.catalogV35): يضمن وجود الخانات القديمة بمعرّفاتها، ويعيد تسمية الاسم الافتراضي القديم الملتبس فقط.
   بعدها لا يُعاد فرض أي اسم، وما حذفه المستخدم لا يعود. */
function codisV35Migrate(s){
  try{
    if(s.catalogV35 === 1) return;
    if(!s.economy || !Array.isArray(s.economy.rarities) || !s.economy.rarities.length) return;
    const rid = s.economy.rarities[0].id, now = econNowIso(), D = codisFixedDefs();
    D.rewards.forEach(d=>{
      const it = s.rewardItems.find(x=>x && x.id === d.id);
      if(!it) s.rewardItems.push({ id:d.id, name:d.name, rarity:rid, weight:0, coinValue:null, storePrice:null, stickerId:null, enabled:true, room:'habits', createdAt:now, updatedAt:now });
      else if(d.oldName && it.name === d.oldName) it.name = d.name;
    });
    D.punish.forEach(d=>{
      if(!s.punishItems.some(x=>x && x.id === d.id)) s.punishItems.push({ id:d.id, name:d.name, severity:d.sev, coinBypassCost:null, enabled:true, room:'habits', createdAt:now, updatedAt:now });
    });
    s.catalogV35 = 1;
  }catch(e){}
}
/* الاسم القديم لنقطة الدخول: صار ترحيلاً غير هدّام + اشتقاق الحقول (لا يفرض الأسماء) */
function codisV34Seed(s){
  try{ if(!s || !Array.isArray(s.rewardItems) || !Array.isArray(s.punishItems)) return; codisV35Migrate(s); codisV35Reconcile(s); }catch(e){}
}

/* ---------- نتيجة ببطاقة من الكتالوج (المعرّف فريد من نفس سجل النتائج ⇒ لا تكرار) ----------
   الاسم والستيكر من عنصر الكتالوج الحي؛ القيمة من المخطط. كرت محذوف/معطّل ⇒ لا نتيجة ولا خصم. */
function codisFixedOutcome(id, kind, def, extra){
  const L = data.outcomeLedger, ex = L[id];
  if(ex){ if(ex.status === 'void'){ ex.status = 'pending'; ex.decision = null; saveData(); return { entry:ex, isNew:true }; } return { entry:ex, isNew:false }; }
  const it = codisCatalogItem(kind, def.id);
  if(!it || it.enabled === false) return { entry:null, isNew:false, disabled:true, missing:!it };
  const rar = econCfg().rarities[0];
  const e = Object.assign({ id:id, room:'habits', kind:kind, scope:'habit', type:'habit_' + (kind === 'reward' ? 'reward' : 'punishment'), at:econNowIso(), status:'pending', decision:null, applied:true, celebrated:false, fixedId:def.id, periodic:def.tag, fixedLabel:def.label }, extra || {});
  if(kind === 'reward') Object.assign(e, { item:it.name, rewardId:def.id, stickerId:codisStickerIdOk(it.stickerId), rarity:rar.id, rarityName:rar.name, rarityTone:rar.tone, rarityOrder:rar.order, odds:null, coinValue:def.coin, storePrice:econEffStore(it, rar), coinsAwarded:0 });
  else Object.assign(e, { item:it.name, punishId:def.id, severity:def.sev, bypassCost:econPenaltyCost(it), coinsSpent:0, noPass:def.group === 'event' });
  L[id] = e; saveData();
  return { entry:e, isNew:true };
}

/* ---------- واجهة الإعدادات: غرفة التأديب = نفس قوائم ومحرّر وأزرار بقية الغرف تماماً ----------
   الفرق الوحيد: التصنيف (المحطة/الحدثية + أهمية العادة أو شدة المحطة) بدل الندرة. لا أزرار ولا ميزات إضافية. */
function codisV35DelCopy(it){ return { title:'حذف الكرت من القائمة؟', message:'«' + it.name + '» تنحذف من قائمة غرفة التأديب ولا تُمنح حتى تعيد إضافتها. ما حصلت عليه منها سابقاً يبقى محفوظاً بالسجل.', icon:'trash', confirmText:'حذف' }; }
/* حقول التصنيف داخل المحرّر نفسه (إضافة وتعديل). تظهر فقط حين تكون قائمة المحرّر غرفة التأديب */
function codisV35PlaceHtml(prefix, kind, it){
  const isR = kind === 'reward', d = it ? (codisSlotOf(it) || {}) : {}, fn = 'codisV35PlaceSync(\'' + prefix + '\',\'' + kind + '\')';
  const place = d.group || 'station', sp = d.period || '7d', imp = d.imp || 'normal';
  const opt = (v, t, cur)=>'<option value="' + v + '"' + (v === cur ? ' selected' : '') + '>' + t + '</option>';
  const room = it ? it.room : settingsRoom, on = room === 'habits';
  const showSp = isR && place === 'station', showImp = place === 'event' || (isR && place === 'station' && sp === '30d');
  return '<div class="cat-place" id="' + prefix + '-place-wrap" data-cur="' + escapeHtml(it && it.fixed ? it.id : '') + '"' + (on ? '' : ' hidden') + '>' +
    econField('التصنيف', '<select class="eco-sel" id="' + prefix + '-place" onchange="' + fn + '">' + opt('station', 'المحطة', place) + opt('event', 'الحدثية', place) + '</select>') +
    (isR ? '<div id="' + prefix + '-sp-wrap"' + (showSp ? '' : ' hidden') + '>' + econField('نوع المحطة', '<select class="eco-sel" id="' + prefix + '-sp" onchange="' + fn + '">' + opt('7d', 'أسبوعية — 7 أيام', sp) + opt('30d', 'شهرية — 30 يوماً', sp) + '</select>') + '</div>' : '') +
    '<div id="' + prefix + '-imp-wrap"' + (showImp ? '' : ' hidden') + '>' + econField('أهمية العادة', '<select class="eco-sel" id="' + prefix + '-imp" onchange="' + fn + '">' + opt('normal', 'عادية', imp) + opt('important', 'مهمة', imp) + opt('critical', 'حرجة', imp) + '</select>') + '</div>' +
    '<p class="eco-note" id="' + prefix + '-slot-hint">' + (on ? codisV35HintText(kind, codisV35DefOf(kind, place, sp, imp, it && it.severity), it && it.fixed ? it.id : '') : '') + '</p></div>';
}
function codisV35DefOf(kind, place, sp, imp, sev){
  const D = codisFixedDefs();
  if(kind === 'reward'){ if(place === 'station') return sp === '30d' ? D.rewards.find(d=>d.tag === 'monthlyEvent' && d.imp === imp) : D.rewards.find(d=>d.tag === 'station7'); return D.rewards.find(d=>d.tag === 'resist' && d.imp === imp); }
  if(place === 'station'){ const s = econNormSeverity(sev, 'MEDIUM'); return D.punish.find(d=>d.tag === 'st7' && d.sev === s); }
  return D.punish.find(d=>d.tag === 'event' && d.imp === imp);
}
function codisV35HintText(kind, d, cur){
  if(!d) return '';
  const have = codisCatalogItem(kind, d.id), taken = have && have.id !== cur;
  return (kind === 'reward' ? 'استبدال ' + econFmt(d.coin) + ' · متجر ' + econFmt(d.store !== undefined ? d.store : econAutoStore(d.coin)) + ' · بيع ' + econFmt(econSellValue(d.coin)) : 'تكلفة التجاوز ' + econFmt(d.cost) + ' كوين') +
    (taken ? ' — هذا التصنيف عنده كرت بالقائمة، عدّله من هناك' : '');
}
/* التصنيف المختار بالمحرّر (null = المحرّر ليس لغرفة التأديب) */
function codisV35FormDef(prefix, kind){
  const g = id=>document.getElementById(prefix + '-' + id), room = g('room'), pl = g('place');
  if(!room || room.value !== 'habits' || !pl) return null;
  return codisV35DefOf(kind, pl.value, (g('sp') || {}).value, (g('imp') || {}).value || 'normal', (g('sev') || {}).value) || null;
}
function codisV35PlaceSync(prefix, kind){
  const g = id=>document.getElementById(prefix + '-' + id), wrap = g('place-wrap'); if(!wrap) return;
  const room = g('room'), on = !!room && room.value === 'habits'; wrap.hidden = !on;
  const place = g('place').value, sp = g('sp');
  if(g('sp-wrap')) g('sp-wrap').hidden = place !== 'station';
  g('imp-wrap').hidden = !(place === 'event' || (kind === 'reward' && place === 'station' && sp && sp.value === '30d'));
  const form = wrap.parentNode, hint = g('hint');
  if(hint) hint.style.display = on ? 'none' : '';
  if(kind === 'reward'){ const more = form.querySelector('.rwe-more'), wt = form.querySelector('.rwe-wt'); if(more) more.style.display = on ? 'none' : ''; if(wt && on) wt.hidden = true; }
  else { const sev = g('sev'), f = sev && sev.closest('.eco-field'); if(f) f.style.display = (on && place === 'event') ? 'none' : ''; }
  const sh = g('slot-hint'); if(sh) sh.textContent = on ? codisV35HintText(kind, codisV35FormDef(prefix, kind), wrap.dataset.cur || '') : '';
}
/* قراءة المحرّر لغرفة التأديب: null = قائمة أخرى (القراءة العادية) */
function codisV35ReadPlace(prefix, kind, name, stickerId){
  const d = codisV35FormDef(prefix, kind); if(!d) return null;
  const g = id=>document.getElementById(prefix + '-' + id), v = { name:name, enabled:g('on').checked, slot:d.id };
  if(kind === 'reward') v.stickerId = stickerId;
  return v;
}
function codisV35AddSlot(kind, v){
  const d = codisFixedById(v.slot), list = kind === 'punish' ? data.settings.punishItems : data.settings.rewardItems;
  if(list.some(x=>x && x.id === d.id)){ codisSfx('invalid', { ctx:'unavailable' }); showToast('هذا التصنيف عنده كرت بالقائمة — عدّله من هناك', 'var(--warning)'); return; }
  const now = econNowIso();
  if(kind === 'reward') list.push({ id:d.id, name:v.name, rarity:econCfg().rarities[0].id, weight:0, coinValue:null, storePrice:null, stickerId:v.stickerId || null, enabled:v.enabled, room:'habits', createdAt:now, updatedAt:now });
  else list.push({ id:d.id, name:v.name, severity:d.sev, coinBypassCost:null, enabled:v.enabled, room:'habits', createdAt:now, updatedAt:now });
  econNormalizeItems(data.settings); settingsRoom = 'habits'; settingsDailyRoom = 'habits'; rpuAddDone(kind);
  econSave(kind === 'reward' ? 'انضافت المكافأة' : 'انضافت العقوبة'); econEditing = null; econRenderAll();
}
/* حفظ التعديل بغرفة التأديب: تغيير التصنيف ينقل الكرت لخانته (إن كانت فارغة) كما يغيّر تعديل الندرة مكافأة العمليات */
function codisV35SaveSlot(kind, it, v){
  const list = kind === 'punish' ? data.settings.punishItems : data.settings.rewardItems;
  if(v.slot !== it.id){
    if(list.some(x=>x && x.id === v.slot)){ codisSfx('invalid', { ctx:'unavailable' }); showToast('هذا التصنيف عنده كرت بالقائمة — عدّله من هناك', 'var(--warning)'); return; }
    it.id = v.slot; if(kind === 'reward') it.rarity = econCfg().rarities[0].id;
  }
  it.name = v.name; it.enabled = v.enabled; it.room = 'habits'; if(kind === 'reward') it.stickerId = v.stickerId || null;
  it.updatedAt = econNowIso(); econNormalizeItems(data.settings); econEditing = null;
  econSave(kind === 'reward' ? 'انحفظت المكافأة' : 'انحفظت العقوبة'); econRenderAll();
}
function codisV35QuickAdd(kind, id){ const d = codisFixedById(id); if(!d || codisCatalogItem(kind, id)) return; codisV35AddSlot(kind, { slot:id, name:d.name, enabled:true, stickerId:null }); }
/* شارة التصنيف بمكان شارة الندرة */
function codisV35Chip(sp){ return '<span class="cat-chip">' + escapeHtml(sp.label) + '</span>'; }
/* ---------- بلاطات قوائم المكافآت/العقوبات (كل الغرف والفترات بالشكل نفسه) ----------
   البلاطة: شارة التصنيف (ندرة/تصنيف التأديب/شدة) + الستيكر + الاسم + القيمة الأساسية. الضغط عليها يفتحها بعرض القائمة
   (كل القيم + تفعيل/تعطيل + حذف + المحرّر)، والضغط مرة ثانية يغلقها. الحقول والدوال نفسها (econEdit · econToggleReward · econDeleteReward · econSaveReward وما يقابلها للعقوبات). */
function codisRptShort(sp){ return sp.tag === 'station7' ? 'محطة 7 أيام' : sp.tag === 'monthlyEvent' ? 'شهرية · ' + codisImpAr(sp.imp) : sp.tag === 'resist' ? 'حدثية · ' + codisImpAr(sp.imp) : sp.tag === 'st7' ? 'محطة · ' + econSevLabel(sp.sev) : 'حدثية · ' + codisImpAr(sp.imp); }
function codisRptTag(kind, it){
  const sp = it.fixed ? codisSlotOf(it) : null;
  if(sp) return '<span class="rpt-tag cat-chip rpt-imp-' + escapeHtml(sp.imp || String(sp.sev || '').toLowerCase()) + '">' + escapeHtml(codisRptShort(sp)) + '</span>';
  if(kind === 'punish') return '<span class="rpt-tag sev-badge sev-' + it.severity + '">' + econSevLabel(it.severity) + '</span>';
  if(it.room === 'habits') return '<span class="rpt-tag cat-chip rpt-none">بدون تصنيف</span>';   /* عنصر قديم بقائمة «الحدثية» قبل التصنيف: يُصنَّف من التعديل أو يُحذف */
  if(it.room === 'learn') return '';
  const rar = econRarityById(it.rarity) || econCfg().rarities[0];
  return '<span class="rpt-tag rar-badge rar-' + escapeHtml(rar.tone) + '" title="' + escapeHtml(rar.name) + '"><b>' + escapeHtml(rar.id) + '</b><span>' + escapeHtml(rar.name) + '</span></span>';
}
function codisRptHtml(kind, it, val, meta, editor){
  const ed = econEditing === it.id, id = escapeHtml(it.id), isR = kind === 'reward';
  const tog = isR ? 'econToggleReward' : 'econTogglePunish', del = isR ? 'econDeleteReward' : 'econDeletePunish', save = isR ? 'econSaveReward' : 'econSavePunish';
  return '<div class="eco-item rpt' + (it.enabled ? '' : ' is-off') + (ed ? ' is-editing' : '') + '" data-name="' + escapeHtml(codisNormText(it.name)) + '">' +
    '<button type="button" class="rpt-face" onclick="econEdit(\'' + id + '\')" aria-expanded="' + (ed ? 'true' : 'false') + '" aria-label="' + escapeHtml(it.name + (it.enabled ? '' : ' — معطّلة') + ' — ' + (ed ? 'إغلاق' : 'فتح')) + '">' +
      '<span class="rpt-top">' + codisRptTag(kind, it) + (isR ? '<span class="rpt-stk">' + codisStickerThumbHtml(it.stickerId) + '</span>' + codisDurBadgeHtml(it.name) : '') + '</span>' +
      '<span class="eco-item-name rpt-name" dir="auto">' + escapeHtml(it.name) + '</span>' +
      '<span class="rpt-val">' + val + '</span>' + (it.enabled ? '' : '<span class="eco-off-tag rpt-off">معطّلة</span>') +
    '</button>' +
    (ed ? '<div class="rpt-open"><div class="eco-item-meta">' + meta + '</div>' +
      '<div class="eco-item-acts"><button type="button" class="chip-act" onclick="' + tog + '(\'' + id + '\')" aria-pressed="' + (it.enabled ? 'true' : 'false') + '">' + (it.enabled ? 'تعطيل' : 'تفعيل') + '</button>' +
      '<button type="button" class="chip-act" onclick="econEdit(\'' + id + '\')" aria-expanded="true">إغلاق</button>' +
      '<button type="button" class="chip-del" aria-label="حذف «' + escapeHtml(it.name) + '»" title="حذف" onclick="' + del + '(\'' + id + '\')">' + ICONS.trash + '</button></div>' +
      '<div class="eco-item-edit">' + editor + '<button type="button" class="btn btn-primary eco-full" onclick="' + save + '(\'' + id + '\')">حفظ التعديل</button></div></div>' : '') +
    '</div>';
}
function econRewardRowHtml(it){
  const rar = econRarityById(it.rarity) || econCfg().rarities[0], coin = econEffCoin(it, rar), price = econEffStore(it, rar);
  const ed = econEditing === it.id;
  return codisRptHtml('reward', it, codisIcon('coin') + '<b>' + econFmt(coin) + '</b>',
    '<span>استبدال <b>' + econFmt(coin) + '</b></span><span>متجر <b>' + econFmt(price) + '</b></span><span>بيع <b>' + econFmt(econSellValue(coin)) + '</b></span>',
    ed ? econRewardEditor('eco-edit-r', it) : '');
}
function econPunishRowHtml(it){
  const ed = econEditing === it.id, cost = econPenaltyCost(it), sp = it.fixed ? codisSlotOf(it) : null;
  return codisRptHtml('punish', it, '<small>تجاوز</small> ' + codisIcon('coin') + '<b>' + econFmt(cost) + '</b>',
    '<span>تكلفة التجاوز <b>' + econFmt(cost) + '</b> كوين' + (it.coinBypassCost === null && !sp ? ' (حسب الشدة)' : '') + '</span>',
    ed ? econPunishEditor('eco-edit-p', it) : '');
}
/* ---------- صفحة المكافآت/العقوبات: صفحات مستقلة (يومية · أسبوعية · شهرية · الكل) بدل التمرير بين الأقسام ----------
   الحالة واجهة فقط (لا تُحفظ). القوائم الأصلية تبقى كما هي؛ في «الكل» تُفرَّغ قوائم الفترات حتى لا يتكرر محرّر التعديل (لا IDs مكررة). */
var rpuView = 'daily';
function setSettingsPeriod(p){
  if(['daily', 'weekly', 'monthly', 'all'].indexOf(p) === -1) return;
  const was = rpuView; rpuView = p;
  if(p !== 'all') settingsRoom = p === 'daily' ? settingsDailyRoom : p;
  econEditing = null; if(was !== p) codisSfx('press', { ctx:'tab' });
  econRenderRewards(); econRenderPunish();
  if(p === 'all'){ const q = document.getElementById('rpu-q'); if(q && was !== 'all'){ q.value = ''; rpuFind(); } }
  const top = document.querySelector('#settings-page-rewards .rpu-jump');
  if(top && top.getBoundingClientRect().top < 0){ try{ top.scrollIntoView({ block:'start' }); }catch(e){} }
}
function rpuApplyView(){
  const pg = document.getElementById('settings-page-rewards'); if(!pg) return;
  pg.dataset.view = rpuView;
  pg.querySelectorAll('.rpu-jump-btn').forEach(b=>{ const on = b.dataset.period === rpuView; b.classList.toggle('is-on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
  const ab = document.getElementById('rpu-all-btn'); if(ab){ const on = rpuView === 'all'; ab.classList.toggle('is-on', on); ab.setAttribute('aria-pressed', on ? 'true' : 'false'); }
  const t = document.getElementById('rpu-all-t'); if(t) t.textContent = rpKind === 'punish' ? 'كل العقوبات' : 'كل المكافآت';
  const q = document.getElementById('rpu-q'); if(q) q.placeholder = rpKind === 'punish' ? 'ابحث باسم العقوبة…' : 'ابحث باسم المكافأة…';
  const box = document.getElementById('rpu-all'); if(box) box.hidden = rpuView !== 'all';
}
/* بعد كل رسم لقوائم نوع (rpuFill): الحالة + العدد + صفحة «الكل» للنوع المفتوح */
function rpuAfterFill(kind, n){
  if(kind !== rpKind) return;
  rpuApplyView();
  const c = document.getElementById('rpu-all-n'); if(c) c.textContent = (n.daily || 0) + (n.weekly || 0) + (n.monthly || 0);
  rpuRenderAll();
}
/* «الكل»: كل عناصر النوع المفتوح بمجموعات بترتيب ثابت (العمليات · الأستاذ · التأديب · الأسبوعية · الشهرية)، تفصلها مسافة فقط — بلا عناوين ولا إضافة */
function rpuRenderAll(){
  const box = document.getElementById('rpu-all-list'); if(!box) return;
  if(rpuView !== 'all'){ box.innerHTML = ''; return; }
  const isP = rpKind === 'punish', all = isP ? data.settings.punishItems : data.settings.rewardItems, row = isP ? econPunishRowHtml : econRewardRowHtml;
  const rank = r=>{ const x = econRarityById(r); return x ? x.order : 99; }, sv = econSeverities();
  const sortFn = isP ? (a, b)=>sv.indexOf(a.severity) - sv.indexOf(b.severity) || a.name.localeCompare(b.name, 'ar') : (a, b)=>rank(a.rarity) - rank(b.rarity) || a.name.localeCompare(b.name, 'ar');
  const names = { tasks:'غرفة العمليات', learn:'غرفة الأستاذ', habits:'غرفة التأديب', weekly:'الأسبوعية', monthly:'الشهرية' };
  const html = ['tasks', 'learn', 'habits', 'weekly', 'monthly'].map(g=>{
    const items = all.filter(x=>x && x.room === g).sort(g === 'habits' ? codisV35Sort : sortFn);
    return items.length ? '<div class="rpu-list rpu-all-grp" role="list" data-g="' + g + '" aria-label="' + names[g] + '">' + items.map(row).join('') + '</div>' : '';
  }).join('');
  box.innerHTML = html || '<div class="eco-empty">' + (isP ? 'ماكو عقوبات بعد' : 'ماكو مكافآت بعد') + '</div>';
  rpuFind();
}
/* بحث «الكل»: مباشر أثناء الكتابة بكل المجموعات، بتوحيد الكتابة العربية؛ لا يمس البيانات */
function rpuFind(){
  const inp = document.getElementById('rpu-q'), q = inp ? codisNormText(inp.value).trim() : '', box = document.getElementById('rpu-all-list'); if(!box) return;
  let any = 0;
  box.querySelectorAll('.rpu-all-grp').forEach(g=>{ let v = 0; g.querySelectorAll('.rpt').forEach(t=>{ const hit = !q || (t.dataset.name || '').indexOf(q) !== -1; t.hidden = !hit; if(hit) v++; }); g.hidden = !v; any += v; });
  const lab = document.querySelector('#rpu-all .rpu-find'); if(lab) lab.classList.toggle('has-q', !!q);
  let none = box.querySelector('.rpu-nomatch');
  if(q && !any){ if(!none){ none = document.createElement('div'); none.className = 'eco-empty rpu-nomatch'; box.appendChild(none); } none.textContent = 'ما لكينا شي بهالاسم'; }
  else if(none) none.remove();
}
function rpuFindClear(){ const q = document.getElementById('rpu-q'); if(!q) return; q.value = ''; rpuFind(); try{ q.focus({ preventScroll:true }); }catch(e){} }
/* ترتيب قائمة غرفة التأديب: بترتيب المخطط (محطة 7 أيام · محطة شهرية · حدثية) ثم الأهمية؛ غير المصنّفة أخيراً */
function codisV35Sort(a, b){
  const O = ['fx_station7', 'fx_ms_normal', 'fx_ms_important', 'fx_ms_critical', 'fx_rs_normal', 'fx_rs_important', 'fx_rs_critical', 'fxp_st7_low', 'fxp_st7_med', 'fxp_st7_high', 'fxp_ev_normal', 'fxp_ev_important', 'fxp_ev_critical'];
  const ix = x=>{ const i = O.indexOf(x.id); return i < 0 ? 99 : i; };   /* المحطات (أسبوعية ثم شهرية) ثم الحدثية؛ غير المصنّفة أخيراً */
  return ix(a) - ix(b) || String(a.name).localeCompare(String(b.name), 'ar');
}
/* توافق: الأسماء القديمة تبقى (لا أقسام إضافية؛ غرفة التأديب قائمة عادية عبر rpuFill) */
function codisV35Cat(kind){ const box = document.getElementById(kind === 'punish' ? 'punish-cat' : 'reward-cat'); if(box){ box.innerHTML = ''; box.hidden = true; } }
function codisFillEventPenalties(){ codisV35Cat('punish'); }
