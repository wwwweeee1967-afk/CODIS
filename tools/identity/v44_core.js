/* ================= CODIS-V44 (3.31.0): الصندوق المجاني + كرت مكافآت الصندوق المجاني =================
   • كرت مالي واحد مستقل `free_box` (1–10 كوين) خارج مصفوفة الـ25 (codisFinCards/codisFinMatrixCheck/codisFinClassify لم تُمس).
   • مكافآت الصندوق = عناصر عادية في data.settings.rewardItems بعلامة `freebox:true` (+ fin.card = 'free_box'): تبقى قابلة للشراء الفردي
     وتستعمل المخزون والتطبيع نفسهما، لكنها خارج poolOf(غرف النتائج اليومية) وخارج CodisBoxes.pool وخارج قوائم الغرف/الفترات.
   • حالة المطالبة data.economyState.freeBox = { at:ISO آخر مطالبة ناجحة, n:عدد } داخل لقطة CodisWallet.transact (ذرّية مع منح المخزون).
   • كل ما قبل `const CodisFreeBox` function declarations آمنة وقت التحميل (لا تقرأ const ولا data). */

function codisFreeCard(){
  if(codisFreeCard.c) return codisFreeCard.c;
  return (codisFreeCard.c = Object.freeze({ id:'free_box', name:'كرت مكافآت الصندوق المجاني', room:'tasks', rarity:null, scope:'free', roomKey:'free', ref:1, min:1, max:10, maxOpen:false, fixed:false, fixedId:null, type:'free', free:true, reversed:false }));
}
/* حالة المطالبة المخزّنة: آمنة وقت التحميل (تُستدعى من econNormalizeAll) */
function codisFreeBoxNorm(v){
  try{
    const o = { at:'', n:0 };
    if(v && typeof v === 'object' && !Array.isArray(v)){
      if(typeof v.at === 'string' && v.at.length <= 40 && isFinite(Date.parse(v.at))) o.at = v.at;
      const n = Number(v.n); if(isFinite(n) && n >= 0 && n <= 1e6) o.n = Math.floor(n);
    }
    return o;
  }catch(e){ return { at:'', n:0 }; }
}
/* تصنيف المكافآت التلقائية: codisFinClassify كما هي، ثم يُلحَق الكرت المجاني (1–10) كخيار صريح أخير.
   بلا تغيير على best/ambiguous/suggestions حين توجد بطاقات عادية (قيمة 10 بالضبط تتداخل مع برونزية الأستاذ فتبقى الأفضلية للعادية ويختار المستخدم المجاني صراحةً).
   قيمة 1 ≤ v < 10 لم يكن لها بطاقة (reason low): الآن وجهتها الوحيدة الكرت المجاني. */
function codisFinClassifyAuto(name, coin){
  const c = Math.round(Number(coin) * 100) / 100, fc = codisFreeCard(), base = codisFinClassify(name, coin);
  if(!isFinite(c) || !codisFinInRange(fc, c)) return base;
  const cand = { card:fc, sem:0, fit:1, score:0 };
  if(base.ok) return Object.assign({}, base, { candidates:base.candidates.concat([cand]) });
  if(base.reason === 'low') return { ok:true, coin:c, domains:[], candidates:[cand], best:cand, ambiguous:false, suggestions:[cand] };
  return base;
}

const CodisFreeBox = (function(){
  const DAY = 86400000;
  let busy = false;
  try{ CodisLimits.reg('freebox.cooldown', 'مهلة الصندوق المجاني (مطالبة واحدة كل 24 ساعة)'); }catch(e){}
  function st(){
    const e = data.economyState;
    if(!e.freeBox || typeof e.freeBox !== 'object') e.freeBox = { at:'', n:0 };
    return e.freeBox;
  }
  /* المكافآت المؤهلة: مفعّلة + علامة الصندوق + كرت free_box + قيمتها الحالية داخل 1–10. بلا تكرار معرّف */
  function pool(){
    const fc = codisFreeCard(), seen = {}, out = [];
    (data.settings.rewardItems || []).forEach(x=>{
      if(!x || !x.freebox || x.enabled === false || !x.fin || x.fin.card !== 'free_box' || x.fin.oor || seen[x.id]) return;
      if(!econRarityById(x.rarity)) return;
      if(!codisFinInRange(fc, codisFinItemCoin(x))) return;
      seen[x.id] = true; out.push(x);
    });
    return out.sort((a, b)=>(a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  }
  /* آخر مطالبة بالملّي ثانية: المخزّنة، وأحدث نسخة مصدرها 'free' بالمخزون (تحمي من تعارض دمج الأجهزة)، ولا تتجاوز «الآن» (ساعة مُقدَّمة خطأً لا تقفل أكثر من 24 ساعة) */
  function lastMs(now){
    let m = Date.parse(st().at); if(!isFinite(m)) m = 0;
    ((data.inventory && data.inventory.items) || []).forEach(x=>{ if(x && x.source === 'free'){ const a = Date.parse(x.acquiredAt); if(isFinite(a) && a > m) m = a; } });
    return Math.min(m, now);
  }
  function status(){
    const now = CodisClock.now(), last = lastMs(now), next = last ? last + DAY : 0;
    const free = CodisLimits.bypass('freebox.cooldown');
    const ready = !last || now >= next || free, n = pool().length;
    return { ready:ready, empty:n === 0, poolN:n, last:last, next:next, waitMs:ready ? 0 : Math.max(0, next - now), now:now };
  }
  /* مطالبة واحدة: السحب متساوٍ بين المؤهّلة (CodisRewardEngine.pick بوزن 1 لكل سجل — لا قيمة ولا ندرة ولا وزن)، والمنح + تسجيل المطالبة بمعاملة واحدة */
  function claim(){
    if(busy) return { ok:false, reason:'busy' };
    busy = true;
    try{
      const s0 = status(); if(!s0.ready) return { ok:false, reason:'wait', nextAt:s0.next };
      const rows = pool(); if(!rows.length) return { ok:false, reason:'empty' };
      const pick = CodisRewardEngine.pick(rows, ()=>1);
      if(!pick) return { ok:false, reason:'empty' };
      const res = CodisWallet.transact([], ()=>{
        const s1 = status(); if(!s1.ready) return { ok:false, reason:'wait', nextAt:s1.next };
        const rar = econRarityById(pick.rarity); if(!rar) return { ok:false, reason:'empty' };
        const f = st(), at = econNowIso(), coin = econEffCoin(pick, rar);
        /* المعرّف مشتق من المطالبة السابقة: جهازان بنفس الحالة ينتجان المعرّف نفسه فيُدمجان بنسخة واحدة */
        const owned = CodisInventory.grant({ uid:'own|free|' + (f.at || '0'), rewardId:pick.id, stickerId:pick.stickerId, fin:pick.fin, name:pick.name, rarity:rar.id, rarityName:rar.name, rarityTone:rar.tone, rarityOrder:rar.order,
          room:pick.room, source:'free', sourceRef:'freebox', scope:'', coinValue:coin, paid:null });
        if(!owned) return { ok:false, reason:'inventory' };
        f.at = at; f.n = (f.n | 0) + 1;
        return { ok:true, owned:owned, item:pick, rarity:rar, coin:coin, at:at };
      });
      return res;
    }catch(e){ console.error('freebox claim', e); return { ok:false, reason:'error' }; }
    finally{ busy = false; }
  }
  return { status, pool, claim, DAY };
})();

function codisFreeBoxFmtWait(ms){
  const m = Math.max(1, Math.ceil(ms / 60000)), h = Math.floor(m / 60), r = m % 60;
  return h ? (h + ' ساعة' + (r ? ' و' + r + ' دقيقة' : '')) : (m + ' دقيقة');
}
let codisFbTimer = 0;
/* ---------- المتجر: بطاقة الصندوق (تظهر فقط حين يكون متاحاً) ---------- */
function codisFreeBoxSig(){ try{ return CodisFreeBox.status().ready ? 1 : 0; }catch(e){ return 0; } }
function codisFreeBoxArt(){
  return '<svg class="fb-svg" viewBox="0 0 120 110" aria-hidden="true" focusable="false">' +
    '<g class="fb-glow"><ellipse cx="60" cy="58" rx="46" ry="30"/></g>' +
    '<g class="fb-body"><rect x="20" y="52" width="80" height="48" rx="5"/><rect x="54" y="52" width="12" height="48" class="fb-rib"/><path d="M20 62h80" class="fb-seam"/></g>' +
    '<g class="fb-lid"><rect x="14" y="36" width="92" height="20" rx="5"/><rect x="54" y="36" width="12" height="20" class="fb-rib"/>' +
    '<path d="M60 36c-10-16-28-12-22-3 3 4 14 4 22 3zM60 36c10-16 28-12 22-3-3 4-14 4-22 3z" class="fb-bow"/></g></svg>';
}
function codisFreeBoxStoreHtml(){
  let s; try{ s = CodisFreeBox.status(); }catch(e){ return ''; }
  if(!s.ready) return '';
  return '<section class="st-part st-free" id="eco-free" aria-labelledby="fb-h"><header class="st-part-head"><h4 class="st-part-title" id="fb-h">الصندوق المجاني</h4></header>' +
    '<button type="button" class="fb-card" id="fb-card" onclick="codisFreeBoxOpen()" aria-label="الصندوق المجاني — اضغط لفتحه وخذ مكافأة"><span class="fb-art">' + codisFreeBoxArt() + '</span>' +
    '<span class="fb-txt"><b>هديتك جاهزة</b><small>مكافأة عشوائية مجانية — بلا أي كوينز</small></span><span class="fb-cta">افتحه</span></button></section>';
}
/* عند فتح المتجر والصندوق غير متاح: مؤقّت واحد يعيد الرسم لحظة عودته (لا مؤقّت متكرر) */
function codisFreeBoxSchedule(){
  try{
    clearTimeout(codisFbTimer); codisFbTimer = 0;
    const s = CodisFreeBox.status(); if(s.ready || !s.waitMs) return;
    codisFbTimer = setTimeout(()=>{ codisFbTimer = 0; try{ if(document.getElementById('eco-store-body') && document.getElementById('eco-store-body').firstElementChild) econRenderStore(); }catch(e){} }, Math.min(s.waitMs + 400, 2147000000));
  }catch(e){}
}
/* ---------- فتح الصندوق: المطالبة تُنفَّذ فور الضغط (فتح الصفحة لا يعيد إتاحته)، والمشهد عرض فقط ---------- */
let codisFbOpening = false;
function codisFreeBoxClose(){
  const ov = document.getElementById('fb-ov'); if(ov) ov.remove();
  codisFbOpening = false;
  try{ econRenderStore(); }catch(e){}
}
function codisFreeBoxMsg(reason, r){
  return ({ wait:'الصندوق المجاني يرجع بعد ' + codisFreeBoxFmtWait((r && r.nextAt ? r.nextAt - CodisClock.now() : 0)), empty:'ماكو مكافآت مفعّلة بالصندوق المجاني حالياً — أضف مكافأة من الإعدادات ← المكافآت', save:'تعذّر الحفظ — ما انفتح الصندوق وتقدر تحاول مرة ثانية', inventory:'تعذّر إضافة المكافأة — ما انفتح الصندوق وتقدر تحاول مرة ثانية', busy:'', error:'تعذّر فتح الصندوق — حاول مرة ثانية' })[reason] || 'تعذّر فتح الصندوق';
}
function codisFreeBoxOpen(){
  if(codisFbOpening) return;
  codisFbOpening = true;
  const btn = document.getElementById('fb-card'); if(btn){ btn.disabled = true; btn.setAttribute('aria-disabled', 'true'); }
  let r; try{ r = CodisFreeBox.claim(); }catch(e){ console.error(e); r = { ok:false, reason:'error' }; }
  if(!r.ok){
    codisFbOpening = false;
    if(btn){ btn.disabled = false; btn.removeAttribute('aria-disabled'); }
    codisSfx('invalid', { ctx:'unavailable' }); const m = codisFreeBoxMsg(r.reason, r); if(m) showToast(m, 'var(--warning)');
    if(r.reason === 'wait') { try{ econRenderStore(); }catch(e){} }
    return;
  }
  const rar = r.rarity, it = r.item, calm = (typeof econCalm === 'function') && econCalm();
  const kind = (econStoreHasArt(it) && codisCardKey({ rarityTone:rar.tone })) ? 'is-dl' : 'is-plain';
  const ov = document.createElement('div'); ov.id = 'fb-ov'; ov.className = 'fb-ov' + (calm ? ' is-calm' : ''); ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true'); ov.setAttribute('aria-label', 'فتح الصندوق المجاني');
  ov.innerHTML = '<div class="fb-stage"><div class="fb-box is-shake" id="fb-box">' + codisFreeBoxArt() + '</div>' +
    '<div class="fb-rev" id="fb-rev" hidden><span class="fb-kick">مبروك — هذي هديتك</span><div class="fb-cardwrap"><span class="store-art is-card ' + kind + '">' + econStoreFaceHtml(it, rar, { price:r.coin }) + '</span></div>' +
    '<b class="fb-name" dir="auto">' + escapeHtml(it.name) + '</b><span class="fb-val">' + econCoin(r.coin) + '<em>قيمة المكافأة</em></span>' +
    '<p class="fb-note" role="status">انضافت لـ«بحوزتك» — بلا أي خصم كوينز. يرجع الصندوق بعد 24 ساعة.</p>' +
    '<button type="button" class="btn btn-primary fb-ok" onclick="codisFreeBoxClose()">تمام</button></div></div>';
  (document.getElementById('settings-page-eco-store') || document.body).appendChild(ov);
  codisHydrateIcons(ov);
  codisSfx('open', { ctx:'select' }); codisHaptic([12, 40, 18]);
  const show = ()=>{ const b = document.getElementById('fb-box'), v = document.getElementById('fb-rev'); if(!b || !v) return; b.classList.remove('is-shake'); b.classList.add('is-open'); codisSfx('success', { ctx:'settings' });
    setTimeout(()=>{ const v2 = document.getElementById('fb-rev'); if(v2){ const stg = v2.closest('.fb-stage'); if(stg) stg.classList.add('is-done'); v2.hidden = false; v2.classList.add('is-on'); try{ codisFitLazy(v2); }catch(e){} const ok = v2.querySelector('.fb-ok'); if(ok) try{ ok.focus({ preventScroll:true }); }catch(e){} } }, calm ? 0 : 520); };
  setTimeout(show, calm ? 0 : 700);
  showToast('انضافت «' + it.name + '» لممتلكاتك', 'var(--success)', 'check');
}

/* ---------- الإعدادات: قسم «مكافآت الصندوق المجاني» (أسفل أقسام المكافآت اليومية) ---------- */
function codisFreeMgmtRender(){
  const list = document.getElementById('free-list'); if(!list) return;
  const items = (data.settings.rewardItems || []).filter(x=>x && x.freebox).sort((a, b)=>econEffCoin(a, econRarityById(a.rarity) || econCfg().rarities[0]) - econEffCoin(b, econRarityById(b.rarity) || econCfg().rarities[0]) || String(a.name).localeCompare(String(b.name), 'ar'));
  list.innerHTML = items.length ? items.map(econRewardRowHtml).join('') : '<div class="eco-empty">ماكو مكافآت بالصندوق المجاني بعد</div>';
  const on = items.filter(x=>x.enabled).length, c = document.querySelector('#rpu-r-free [data-count]');
  if(c) c.textContent = items.length ? ('العدد ' + items.length + (on < items.length ? ' · ' + (items.length - on) + ' معطّلة' : '')) : 'فارغ';
}
function codisFreeAdd(){ finAutoOpen({ free:true }); }

/* ================= بطاقة الصندوق المجاني (وجه خاص مرسوم بالكود، لا يستعمل بطاقة اليومي) =================
   تُعرَف أي مكافأة بكرت free_box (علامة freebox بالكتالوج، أو fin.card على نسخة المخزون، أو مصدر 'free') ببطاقتها هذه
   في المتجر والمعاينة والتفاصيل والبكج/المخزون وشاشة الفتح. 4:5 بنفس إطار البطاقات الموحّد ولوحة الاسم/القيمة نفسها (scx-plate) فتعمل ملاءمة النص. */
function codisIsFreeReward(e){
  try{
    if(!e) return false;
    if(e.freebox === true || e.free === true || e.source === 'free') return true;
    if(e.fin && e.fin.card === 'free_box') return true;
    if(e.rewardId && data && data.settings){ const c = data.settings.rewardItems.find(x=>x && x.id === e.rewardId); return !!(c && c.freebox); }
  }catch(x){}
  return false;
}
function codisFreeGiftArt(){
  if(codisFreeGiftArt.c) return codisFreeGiftArt.c;
  let dots = '', conf = '';
  for(let i = 0; i < 40; i++){ dots += '<circle cx="' + (24 + (i % 8) * 50) + '" cy="' + (30 + Math.floor(i / 8) * 54) + '" r="1.6"/>'; }
  const C = ['#b8412f', '#1f6a70', '#c8923a', '#7a4fa0'];
  [[62,92,-20],[338,84,18],[46,196,30],[352,188,-35],[92,300,15],[318,296,-12],[148,64,40],[258,70,-25],[70,150,0],[332,142,0],[120,118,0],[286,112,0]].forEach((p, i)=>{
    conf += (i < 8 ? '<rect x="' + (p[0] - 7) + '" y="' + (p[1] - 3) + '" width="14" height="6" rx="1.5" transform="rotate(' + p[2] + ' ' + p[0] + ' ' + p[1] + ')" fill="' + C[i % 4] + '"/>' : '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="4.5" fill="' + C[i % 4] + '"/>');
  });
  return (codisFreeGiftArt.c = '<svg class="rwc-art fgc-art" viewBox="0 0 400 500" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' +
    '<defs><linearGradient id="fgcBg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f8ecce"/><stop offset="1" stop-color="#ead29b"/></linearGradient>' +
    '<radialGradient id="fgcRay" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff3bf" stop-opacity=".95"/><stop offset="1" stop-color="#f0c866" stop-opacity="0"/></radialGradient></defs>' +
    '<rect width="400" height="500" rx="20" fill="url(#fgcBg)"/><g fill="#a77a2a" opacity=".22">' + dots + '</g>' +
    '<circle cx="200" cy="262" r="150" fill="url(#fgcRay)"/>' + conf +
    '<ellipse cx="200" cy="392" rx="104" ry="11" fill="#5b3a0a" opacity=".22"/>' +
    '<rect x="112" y="268" width="176" height="122" rx="8" fill="#d09a45" stroke="#4b3210" stroke-width="3.5"/>' +
    '<rect x="100" y="228" width="200" height="46" rx="8" fill="#e2ae56" stroke="#4b3210" stroke-width="3.5"/>' +
    '<rect x="186" y="228" width="28" height="162" fill="#b43d2e" stroke="#4b3210" stroke-width="3"/>' +
    '<path d="M112 306h176" stroke="#4b3210" stroke-width="2" opacity=".35"/>' +
    '<path d="M200 228c-14-40-52-34-42-12 7 14 26 14 42 12zM200 228c14-40 52-34 42-12-7 14-26 14-42 12z" fill="#c34a3b" stroke="#4b3210" stroke-width="3.5" stroke-linejoin="round"/>' +
    '<circle cx="200" cy="228" r="9" fill="#a8362a" stroke="#4b3210" stroke-width="3"/>' +
    '<rect x="8" y="8" width="384" height="484" rx="18" fill="none" stroke="#6e4f17" stroke-width="3.5"/>' +
    '<rect x="20" y="20" width="360" height="460" rx="11" fill="none" stroke="#c8923a" stroke-width="1.6" stroke-dasharray="7 5"/>' +
    '<rect x="40" y="396" width="320" height="72" rx="10" fill="#fff6dc" stroke="#6e4f17" stroke-width="2.5"/>' +
    '<path d="M52 408h296M52 456h296" stroke="#c8923a" stroke-width="1.2" opacity=".7"/></svg>');
}
function codisFreeGiftCardHtml(name, coin, o){
  o = o || {}; coin = econC(Math.max(0, Number(coin) || 0)); name = String(name || '');
  let stk = ''; try{ const u = codisStickerList(o.stickerId).filter(x=>CodisStickers.url(x))[0]; if(u) stk = '<img class="fgc-stk" src="' + escapeHtml(CodisStickers.url(u)) + '" alt="" draggable="false">'; }catch(e){}
  return (o.plain ? '<div class="rwc-wrap is-on">' : '<div class="rv rwc-wrap" data-s="1">') + '<div class="rwc scx scx-free fgc rwc-c" role="img" aria-label="' + escapeHtml(o.label || ('الصندوق المجاني — ' + name + (coin > 0 ? ' — ' + econFmt(coin) : ''))) + '">' +
    '<div class="rwc-stage" style="--ar:.8;--ar-css:4 / 5">' + codisFreeGiftArt() + '<span class="fgc-tag" aria-hidden="true">الصندوق المجاني</span>' + stk +
    '<div class="rwc-slot scx-plate" style="left:10%;top:79.2%;width:80%;height:14.4%;"><span class="scx-row"><span class="scx-name" dir="auto">' + escapeHtml(name) + '</span>' +
    (coin > 0 ? '<span class="scx-coin">' + codisIcon('coin') + '<b>' + econFmt(coin) + '</b></span>' : '') + '</span></div></div></div></div>';
}
