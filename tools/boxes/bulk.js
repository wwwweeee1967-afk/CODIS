/* ===== CODIS-BOXES-V3 · الفتح الجماعي ×10 — عرض فقط =====
   • المعاملة (الشراء + السحب + المنح + الحفظ) تمّت بالكامل داخل CodisBoxes.buyOpenMany (CodisWallet.transact واحدة) قبل ظهور هذه النافذة؛ هنا نقرأ res.items فقط ولا نغيّر أي بيانات.
     إغلاق النافذة/تخطّي/إعادة الرسم لا يشتري ولا يمنح ولا يخصم: المكافآت العشر موجودة أصلاً في المخزون.
   • الإخراج: عشرة صناديق مصغّرة (نفس مجسّم الفتح الفردي) على شبكة 5×2، تدخل معاً بتتابع، ثم تُفتح بالتتابع. ترتيب الكشف تصاعدي بمستوى القيمة الفعلية (CodisRevealLevels)
     فتأتي أفضل الجوائز أخيراً، وتأخذ الجوائز العالية انفجاراً ولوناً أقوى. رقم صغير على كل خلية = رقم الصندوق بترتيب الفتح الأصلي، وأفضل جائزة تُميَّز في النهاية.
   • الحركة CSS فقط (animation-delay من --d لكل خلية) + مؤقّت واحد للإنهاء + مؤقّتات صوت قليلة، وكلها تُمسح في econBulkClose. */
const ECON_BULK_STEP = 150, ECON_BULK_LEAD = 780, ECON_BULK_TAIL = 820;
function econBulkModal(){ return document.getElementById('econ-bulk-modal'); }
function econBulkOrder(res){ return res.items.map((r, i)=>({ i:i, lv:CodisRevealLevels.levelOfResult(r) })).sort((a, b)=>a.lv - b.lv || a.i - b.i); }
function econBulkTotalMs(res){ return ECON_BULK_LEAD + res.items.length * ECON_BULK_STEP + ECON_BULK_TAIL; }
function econBulkCounts(res){
  const c = { reward:0, pass:0, holiday:0, pouch:0, cosmetic:0 };
  res.items.forEach(r=>{ if(r.cosmetic) c.cosmetic++; else if(r.pouch) c.pouch++; else if(r.pass) c.pass++; else if(r.holiday) c.holiday++; else c.reward++; });
  return c;
}
/* اسم الجائزة وشارتها (نفس ما كان يُعرض لكل نوع جائزة) */
function econBulkInfo(r){
  const rar = r.rarity, sp = '<span class="bk-chip is-special">' + ICONS.sparkle + escapeHtml(rar.name) + '</span>';
  if(r.cosmetic) return { name:CodisCosmetics.def(r.cosmetic.id).name, chip:sp, special:true, kind:'cosmetic' };
  if(r.pouch) return { name:CodisPouches.def(r.pouch.type).name, chip:sp, special:true, kind:'pouch' };
  if(r.pass) return { name:CodisPasses.label(r.pass), chip:sp, special:true, kind:'pass' };
  if(r.holiday){ const d = CodisHolidayCards.def(r.holiday.kind); return { name:d ? d.name : 'بطاقة عطلة', chip:sp, special:true, kind:'holiday' }; }
  return { name:r.item.name, chip:econRarityBadge(rar.tone, rar.id, rar.name, rar.order), special:false, kind:'reward' };
}
/* أفضل جائزة: أعلى مستوى قيمة، ثم أعلى قيمة، ثم الأسبق فتحاً */
function econBulkBest(res){
  let b = -1, bl = -1, bv = -1;
  res.items.forEach((r, i)=>{ const lv = CodisRevealLevels.levelOfResult(r), v = CodisRevealLevels.valueOfResult(r) || 0; if(lv > bl || (lv === bl && v > bv)){ b = i; bl = lv; bv = v; } });
  return b;
}
/* خلية واحدة. run=true: صندوق مصغّر فوق البطاقة يُفتح في موعد --d ثم تظهر البطاقة تحته. data-box = معرّف الصندوق الذي خرجت منه */
function econBulkCellHtml(r, i, run, ord, best){
  const it = r.item, rar = r.rarity, inf = econBulkInfo(r), lv = CodisRevealLevels.levelOfResult(r), RL = CodisRevealLevels.info(lv), d = ECON_BULK_LEAD + ord * ECON_BULK_STEP;
  const art = r.pouch ? '<div class="pk-tile is-pouch"><div class="pch-art">' + econPouchSvg(r.pouch.type) + '</div></div>' : econPackTileHtml(it, rar).replace(' role="listitem"', '');
  return '<div class="bk-cell' + (inf.special ? ' is-special' : '') + (best ? ' is-best' : '') + '" role="listitem" data-tone="' + escapeHtml(rar.tone) + '" data-kind="' + inf.kind + '" data-lv="' + lv + '"' + (lv >= 6 ? ' data-hot="1"' : '') + ' data-box="' + escapeHtml(r.box.uid) + '" style="--i:' + i + ';--d:' + d + 'ms;--lrgb:' + RL.rgb + ';--lrgb2:' + RL.rgb2 + '">' +
    '<span class="bk-no" dir="ltr" aria-label="البكج رقم ' + (i + 1) + '">' + (i + 1) + '</span>' + (best ? '<span class="bk-best">الأفضل</span>' : '') +
    (run ? '<div class="bk-chest" aria-hidden="true">' + CodisBoxCinema.rigHtml(r.tier.index, true) + '</div><span class="bk-burst" aria-hidden="true"></span>' : '') +
    '<div class="bk-card">' + codisFlipHtml(art, codisCardBackHtml(inf.name, [['الفئة', rar.name], ['من', r.tier.name]], { tone:rar.tone }), { label:inf.name }) + '</div><p class="bk-name" dir="auto">' + escapeHtml(inf.name) + '</p><div class="bk-meta">' + inf.chip + '</div></div>';
}
function econBulkHeadHtml(s){
  const r = s.res, t = r.tier;
  if(s.phase !== 'done') return '<h3 id="econ-bulk-title">جارٍ فتح ' + econFmt(r.n) + ' بكجات…</h3><p class="bk-sub">' + escapeHtml(t.name) + '</p><span class="bk-prog" aria-hidden="true"><i style="animation-duration:' + econBulkTotalMs(r) + 'ms"></i></span>';
  const c = econBulkCounts(r), parts = [];
  if(c.reward) parts.push(econFmt(c.reward) + ' مكافأة'); if(c.pass) parts.push(econFmt(c.pass) + ' بطاقة تجاوز'); if(c.holiday) parts.push(econFmt(c.holiday) + ' بطاقة عطلة'); if(c.pouch) parts.push(econFmt(c.pouch) + ' كيس فضة'); if(c.cosmetic) parts.push(econFmt(c.cosmetic) + ' مظهر بطاقة');
  const bi = s.best >= 0 ? econBulkInfo(r.items[s.best]) : null;
  return '<span class="bk-ok" role="status">' + ICONS.check + 'تمّت العملية بنجاح</span><h3 id="econ-bulk-title">استلمت ' + econFmt(r.items.length) + ' مكافآت</h3>' +
    '<p class="bk-sub">' + escapeHtml(t.name) + ' ×' + econFmt(r.n) + ' · دفعت ' + econCoin(r.total) + '</p><p class="bk-sub bk-parts">' + parts.join(' · ') + '</p>' +
    (bi && r.items.length > 1 ? '<p class="bk-sub bk-bestline">أفضل جائزة: <b>' + escapeHtml(bi.name) + '</b> (من البكج رقم ' + econFmt(s.best + 1) + ')</p>' : '');
}
function econBulkActionsHtml(s){
  return s.phase !== 'done' ? '<div class="modal-actions"><button type="button" class="btn btn-secondary bk-skip" onclick="econBulkSkip()">تخطّي</button></div>'
    : '<div class="modal-actions"><button type="button" class="btn btn-primary bk-done" onclick="econBulkDismiss()">العودة إلى المتجر</button></div>';
}
function econBulkPaint(){
  const m = econBulkModal(), body = document.getElementById('econ-bulk-body'), s = econBulkState; if(!m || !body || !s) return;
  const sheet = m.querySelector('.bk-modal'), run = s.phase !== 'done', ord = {}; econBulkOrder(s.res).forEach((o, k)=>{ ord[o.i] = k; });
  sheet.className = 'modal store-detail bk-modal' + (econCalm() ? ' is-calm' : '') + (run ? ' is-run' : ' is-done'); sheet.setAttribute('data-tone', s.res.tier.tone);
  CodisArt.set(body, ()=>'<div class="bk-head">' + econBulkHeadHtml(s) + '</div><div class="bk-grid" role="list" aria-label="المكافآت المستلمة">' + s.res.items.map((r, i)=>econBulkCellHtml(r, i, run, ord[i], !run && i === s.best && s.res.items.length > 1)).join('') + '</div><div class="bk-actions">' + econBulkActionsHtml(s) + '</div>');
  codisFitRewardCard(body); codisWatchRewardCards(body);
}
function econBulkWorld(m, tier){
  const sheet = m.querySelector('.bk-modal'), old = sheet.querySelector('.bk-world'); if(old) old.remove();
  const T = CodisBoxCinema.tierOf(tier.index), w = document.createElement('div'); w.className = 'bk-world'; w.setAttribute('aria-hidden', 'true'); w.setAttribute('data-n', String(tier.index));
  w.style.setProperty('--cb-rgb', T.rgb); w.style.setProperty('--cb-rgb2', T.rgb2); w.innerHTML = '<div class="cb-bg"></div><div class="cb-rays"></div>';
  sheet.insertBefore(w, sheet.firstChild);
}
function econBulkShow(res){
  const m = econBulkModal(); if(!m || !res || !res.ok || !res.items || !res.items.length) return false;
  if(econBulkState) econBulkClose(true);
  const calm = econCalm(), token = ++econBulkToken;
  const s = econBulkState = { res:res, phase:calm ? 'done' : 'opening', token:token, timer:0, cues:[], at:Date.now(), best:econBulkBest(res) };   /* تقليل الحركة: النتائج فوراً بلا حركة ولا زر تخطّي */
  if(!calm) econBulkWorld(m, res.tier);
  econBulkPaint(); codisSfx('open');
  m.setAttribute('aria-hidden', 'false'); CodisMotion.modalIn(m);
  const f = m.querySelector('.bk-skip, .bk-done'); if(f){ try{ f.focus({ preventScroll:true }); }catch(x){} }
  if(calm) econBulkCue(s);
  else {
    codisSfx('press'); s.timer = window.setTimeout(()=>econBulkFinish(token), econBulkTotalMs(res));
    /* نغمات الجوائز العالية بمواعيدها (3 كحد أقصى) — كلها تُمسح عند الإغلاق/التخطّي */
    const ord = {}; econBulkOrder(res).forEach((o, k)=>{ ord[o.i] = k; });
    res.items.map((r, i)=>({ i:i, lv:CodisRevealLevels.levelOfResult(r) })).filter(o=>o.lv >= 6).sort((a, b)=>b.lv - a.lv).slice(0, 3).forEach(o=>{
      s.cues.push(window.setTimeout(()=>{ if(econBulkState && econBulkState.token === token && econBulkState.phase === 'opening') codisSfx(o.lv >= 8 ? 'reward.achievement' : 'reward.unlock'); }, ECON_BULK_LEAD + ord[o.i] * ECON_BULK_STEP + 240));
    });
  }
  return true;
}
function econBulkCue(s){ codisSfx('store.buy'); if(s.res.items.some(r=>r.pass || r.holiday)) codisSfx('reward.achievement'); }
function econBulkClearTimers(s){ if(!s) return; if(s.timer){ window.clearTimeout(s.timer); s.timer = 0; } (s.cues || []).forEach(t=>window.clearTimeout(t)); if(s.cues) s.cues.length = 0; }
/* إنهاء الحركة (انتهاء المؤقّت أو التخطّي): يزيل طبقة الصناديق فقط ويُظهر عنوان النجاح وزر العودة وأفضل جائزة — الخلايا نفسها تبقى كما هي */
function econBulkFinish(token){
  const s = econBulkState, m = econBulkModal(); if(!s || !m || (token !== undefined && token !== s.token) || s.phase === 'done') return;
  econBulkClearTimers(s);
  s.phase = 'done';
  const sheet = m.querySelector('.bk-modal'); sheet.classList.remove('is-run'); sheet.classList.add('is-done');
  Array.prototype.forEach.call(m.querySelectorAll('.bk-chest, .bk-burst'), x=>x.remove());
  if(s.best >= 0 && s.res.items.length > 1){ const c = m.querySelectorAll('.bk-cell')[s.best]; if(c){ c.classList.add('is-best'); c.insertAdjacentHTML('afterbegin', '<span class="bk-best">الأفضل</span>'); } }
  const head = m.querySelector('.bk-head'), act = m.querySelector('.bk-actions'); if(head) head.innerHTML = econBulkHeadHtml(s); if(act) act.innerHTML = econBulkActionsHtml(s);
  const f = m.querySelector('.bk-done'); if(f){ try{ f.focus({ preventScroll:true }); }catch(x){} }
  econBulkCue(s);
}
/* إغلاق بالأزرار: يتجاهل أول 0.5 ثانية حتى لا تُغلق النتائج بنقرة ثانية من ضغطة مزدوجة على «شراء وفتح» (الزران يظهران تحت موضع زر التأكيد) */
function econBulkDismiss(){ if(econBulkState && Date.now() - econBulkState.at < 500) return; econBulkClose(); }
function econBulkSkip(){ const s = econBulkState; if(!s || s.phase !== 'opening') return; econBulkFinish(s.token); }
/* الإغلاق (زر/Esc/خلفية/سحب للخلف): لا يمسّ أي بيانات — المنح والحفظ تمّا قبل ظهور النافذة */
function econBulkClose(silent){
  const m = econBulkModal(); if(!m) return;
  const s = econBulkState; econBulkToken++; econBulkClearTimers(s);
  if(silent !== true && CodisMotion.isOpen(m)) codisSfx('close');
  CodisMotion.modalOut(m); m.setAttribute('aria-hidden', 'true'); econBulkState = null;
  const w = m.querySelector('.bk-world'); if(w) w.remove();
  if(silent !== true && s && s.phase === 'opening') showToast('انضافت ' + econFmt(s.res.items.length) + ' مكافآت إلى بحوزتك', 'var(--success)', 'gift');
  if(silent === true) return;
  const opener = document.querySelector('#eco-boxes .bx-buy10, #eco-boxes .bx-buy'); if(opener && opener.isConnected){ try{ opener.focus({ preventScroll:true }); }catch(x){} }
}
