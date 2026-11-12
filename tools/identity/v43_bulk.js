/* ================= CODIS-V43: التحديد والحذف الجماعي (صفحة «كل المكافآت/العقوبات») =================
   يحذف تعريفات الكتالوج فقط (data.settings.rewardItems / punishItems) بحفظ واحد وإعادة رسم واحدة.
   لا يمس: سجل النتائج (outcomeLedger) · المخزون (inventory) · المحفظة/سجل الكوينز · الإدارة المالية · العقوبات المحسومة. */
const rpuSel = { on:false, ids:{} };   /* حالة واجهة فقط — لا تُحفظ */
function rpuSelCount(){ return Object.keys(rpuSel.ids).length; }
function rpuSelReset(){ rpuSel.on = false; rpuSel.ids = {}; }
/* عناصر محمية من الحذف: لا يوجد فعلياً (كروت الكتالوج الثابتة تُحذف أصلاً بالحذف الفردي) — نقطة واحدة تُعدَّل إن ظهر ما يجب حمايته */
function rpuProtected(it){ return false; }
function rpuKindItems(){ return rpKind === 'punish' ? data.settings.punishItems : data.settings.rewardItems; }
function rpuSelHtml(id){
  if(!rpuSel.on || rpuView !== 'all') return '';
  const on = !!rpuSel.ids[id];
  return '<button type="button" class="rpt-chk' + (on ? ' is-on' : '') + '" role="checkbox" aria-checked="' + (on ? 'true' : 'false') + '" aria-label="تحديد" onclick="rpuSelToggle(\'' + escapeHtml(id) + '\')"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 12.5l4.2 4.2L18.5 7.8"/></svg></button>';
}
function rpuVisibleTiles(){ return Array.prototype.slice.call(document.querySelectorAll('#rpu-all-list .rpu-all-grp:not([hidden]) .rpt:not([hidden])')); }
function rpuSelToggle(id){
  if(!rpuSel.on) return;
  if(rpuSel.ids[id]) delete rpuSel.ids[id]; else rpuSel.ids[id] = true;
  codisSfx('open', { ctx:'select' }); rpuSelSync();
}
function rpuSelSync(){   /* تحديث بالمكان بلا إعادة رسم القائمة */
  document.querySelectorAll('#rpu-all-list .rpt[data-id]').forEach(t=>{
    const on = !!rpuSel.ids[t.dataset.id]; t.classList.toggle('is-sel', on);
    const c = t.querySelector('.rpt-chk'); if(c){ c.classList.toggle('is-on', on); c.setAttribute('aria-checked', on ? 'true' : 'false'); }
  });
  rpuBulkPaint();
}
function rpuSelMode(){
  rpuSel.on = !rpuSel.on; if(!rpuSel.on) rpuSel.ids = {};
  econEditing = null; codisSfx(rpuSel.on ? 'open' : 'close', { ctx:'editor' }); rpuRenderAll();
}
function rpuSelAll(){
  const tiles = rpuVisibleTiles(); if(!tiles.length) return;
  const all = tiles.every(t=>rpuSel.ids[t.dataset.id]);
  tiles.forEach(t=>{ if(all) delete rpuSel.ids[t.dataset.id]; else rpuSel.ids[t.dataset.id] = true; });
  codisSfx('open', { ctx:'select' }); rpuSelSync();
}
function rpuBulkPaint(){
  const box = document.getElementById('rpu-all-list'); if(!box || !box.parentNode) return;
  let bar = document.getElementById('rpu-bulk');
  if(!bar){ bar = document.createElement('div'); bar.id = 'rpu-bulk'; bar.className = 'rpu-bulk'; box.parentNode.insertBefore(bar, box); }
  const isP = rpKind === 'punish', total = rpuKindItems().length, q = (document.getElementById('rpu-q') || {}).value, searching = !!(q && q.trim());
  const vis = rpuVisibleTiles(), sel = rpuSelCount(), allVis = vis.length > 0 && vis.every(t=>rpuSel.ids[t.dataset.id]);
  if(!rpuSel.on){
    bar.innerHTML = '<button type="button" class="rpu-bk rpu-bk-main" onclick="rpuSelMode()"' + (total ? '' : ' disabled aria-disabled="true"') + '>' + codisIcon('check') + '<span>تحديد</span></button>';
    return;
  }
  bar.innerHTML = '<div class="rpu-bk-info" role="status" aria-live="polite"><b>' + finFmt(sel) + '</b><span>محدد' + (searching ? ' · الظاهر ' + finFmt(vis.length) : '') + '</span></div>' +
    '<div class="rpu-bk-row">' +
    '<button type="button" class="rpu-bk" onclick="rpuSelAll()"' + (vis.length ? '' : ' disabled aria-disabled="true"') + '><span>' + (allVis ? 'إلغاء تحديد الكل' : (searching ? 'تحديد كل الظاهر' : 'تحديد الكل')) + '</span></button>' +
    '<button type="button" class="rpu-bk is-danger" onclick="rpuDelSelected()"' + (sel ? '' : ' disabled aria-disabled="true"') + '><span>حذف المحدد' + (sel ? ' (' + finFmt(sel) + ')' : '') + '</span></button>' +
    '<button type="button" class="rpu-bk is-danger is-all" onclick="rpuDelAll()"' + (total ? '' : ' disabled aria-disabled="true"') + '><span>حذف الكل</span></button>' +
    '<button type="button" class="rpu-bk" onclick="rpuSelMode()"><span>إلغاء</span></button></div>' +
    (searching ? '<p class="rpu-bk-note">«تحديد الكل» يشمل نتائج البحث الظاهرة فقط. «حذف الكل» يشمل كل ' + (isP ? 'العقوبات' : 'المكافآت') + ' بكل الأقسام.</p>' : '');
}
/* الحذف الفعلي: تعريفات الكتالوج فقط، حفظ واحد، تراجع كامل عند فشل الحفظ. يُرجع عدد المحذوف */
function rpuBulkDelete(ids){
  const key = rpKind === 'punish' ? 'punishItems' : 'rewardItems', set = {}; (ids || []).forEach(i=>{ set[i] = true; });
  const snap = data.settings[key], keep = [], gone = [];
  snap.forEach(x=>{ if(x && set[x.id] && !rpuProtected(x)) gone.push(x); else keep.push(x); });
  if(!gone.length) return { ok:true, removed:0, skipped:0 };
  data.settings[key] = keep;
  if(!saveData()){ data.settings[key] = snap; return { ok:false, reason:'save', removed:0 }; }
  econEditing = null; rpuSelReset();
  try{ econRenderAll(); }catch(e){ console.error('rpuBulkDelete render', e); }
  return { ok:true, removed:gone.length, skipped:Object.keys(set).length - gone.length };
}
async function rpuDelSelected(){
  const live = {}; rpuKindItems().forEach(x=>{ if(x) live[x.id] = x; });
  const ids = Object.keys(rpuSel.ids).filter(i=>live[i] && !rpuProtected(live[i])), isP = rpKind === 'punish';
  if(!ids.length){ showToast('ما حددت شي', 'var(--warning)'); return; }
  const ok = await codisConfirm({ title:'حذف ' + finFmt(ids.length) + (isP ? ' عقوبة؟' : ' مكافأة؟'), message:'تنحذف ' + finFmt(ids.length) + (isP ? ' عقوبة محددة من قائمة العقوبات.' : ' مكافأة محددة من قائمة المكافآت.') + (isP ? '' : ' مكافآتك السابقة ومخزونك وسجل كوينزك يبقون محفوظين.'), detail:'الحذف نهائي ولا يمكن التراجع عنه.', irreversible:true, icon:'trash', confirmText:'حذف ' + finFmt(ids.length) });
  if(!ok) return;
  const r = rpuBulkDelete(ids);
  if(!r.ok){ codisSfx('invalid', { ctx:'unavailable' }); showToast('تعذّر الحفظ — ما انحذف شي', 'var(--warning)'); return; }
  codisSfx('task.delete', { ctx:'card' }); showToast('انحذفت ' + finFmt(r.removed) + (isP ? ' عقوبة' : ' مكافأة'), 'var(--success)', 'check');
}
async function rpuDelAll(){
  const isP = rpKind === 'punish', all = rpuKindItems().filter(x=>x), del = all.filter(x=>!rpuProtected(x)), prot = all.length - del.length;
  if(!all.length){ showToast(isP ? 'ماكو عقوبات لتنحذف' : 'ماكو مكافآت لتنحذف', 'var(--warning)'); return; }
  if(!del.length){ showToast('كل العناصر محمية — ما انحذف شي', 'var(--warning)'); return; }
  const ok = await codisConfirm({ title:isP ? 'حذف كل العقوبات؟' : 'حذف كل المكافآت؟', message:'تنحذف ' + finFmt(del.length) + (isP ? ' عقوبة' : ' مكافأة') + ' من كل الأقسام: العمليات · الأستاذ · التأديب · الأسبوعية · الشهرية.' + (prot ? ' (' + finFmt(prot) + ' عناصر محمية تبقى)' : '') + (isP ? '' : ' مكافآتك السابقة ومخزونك وسجل كوينزك يبقون محفوظين.'), detail:'الحذف نهائي ولا يمكن التراجع عنه.', irreversible:true, icon:'trash', confirmText:'حذف الكل (' + finFmt(del.length) + ')' });
  if(!ok) return;
  const r = rpuBulkDelete(del.map(x=>x.id));
  if(!r.ok){ codisSfx('invalid', { ctx:'unavailable' }); showToast('تعذّر الحفظ — ما انحذف شي', 'var(--warning)'); return; }
  codisSfx('task.delete', { ctx:'card' }); showToast('انحذفت ' + finFmt(r.removed) + (isP ? ' عقوبة' : ' مكافأة') + (prot ? ' — وبقيت ' + finFmt(prot) + ' محمية' : ''), 'var(--success)', 'check');
}
