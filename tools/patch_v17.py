#!/usr/bin/env python3
"""CODIS-STICKERS (بعد patch_v16.py): مكتبة ستيكرات للمكافآت — اختيار من محرر المكافأة، حفظ بمعرّف ثابت (stickerId) مع لقطة عند الحصول،
 وطبقة ستيكر موحّدة تُلصق على بطاقات المكافآت (يومي/أسبوعي/شهري/الأستاذ/بلا صورة) في النتيجة والمتجر والتفاصيل والمخزون والبكجات.
 العقوبات والاقتصاد لا تُمَسّ. الصور ملفات منفصلة في assets/stickers/ (لا تُخزَّن ببيانات المستخدم) وبيانات المكتبة تُبنى بـ tools/build_stickers.py."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'CODIS-STICKERS' in s: sys.exit('already patched (CODIS-STICKERS)')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# ---------- 1) البيانات: معرّف الستيكر (دالة تصريحية قبل loadData) ----------
rep("function econNormalizeItems(settings){", """/* CODIS-STICKERS: معرّف ستيكر صالح أو null — دالة تصريحية لأنها تُستعمل أثناء loadData قبل تعريف المكتبة */
function codisStickerIdOk(v){ return (typeof v === 'string' && /^[a-z0-9_]{2,32}$/.test(v)) ? v : null; }
function econNormalizeItems(settings){""", 'normalize head')
rep("return { id:id, name:name, rarity:rarity, weight:econNum(x.weight, 10, 0, 1000000), coinValue:null, storePrice:null,",
    "return { id:id, name:name, rarity:rarity, weight:econNum(x.weight, 10, 0, 1000000), coinValue:null, storePrice:null, stickerId:codisStickerIdOk(x.stickerId),", 'reward item field')
# مخزون: تطبيع + منح
rep("const it = { uid:x.uid, rewardId:(typeof x.rewardId === 'string' && x.rewardId) ? x.rewardId : null, name:x.name.trim().slice(0,120),",
    "const it = { uid:x.uid, rewardId:(typeof x.rewardId === 'string' && x.rewardId) ? x.rewardId : null, stickerId:codisStickerIdOk(x.stickerId), name:x.name.trim().slice(0,120),", 'inventory normalize')
rep("const it = { uid:o.uid, rewardId:o.rewardId || null, name:String(o.name || 'مكافأة').slice(0,120),",
    "const it = { uid:o.uid, rewardId:o.rewardId || null, stickerId:codisStickerIdOk(o.stickerId), name:String(o.name || 'مكافأة').slice(0,120),", 'inventory grant')
# سجل النتائج: تطبيع
rep("    if(!e.scope) e.scope = 'daily';\n    if(!e.type)", "    if(!e.scope) e.scope = 'daily';\n    if(e.stickerId !== undefined) e.stickerId = codisStickerIdOk(e.stickerId);\n    if(!e.type)", 'ledger normalize')
# لقطات الحصول
rep("Object.assign(e, { item:r.reward ? r.reward.name : (r.genericName || 'مكافأة'), rewardId:r.reward ? r.reward.id : null,",
    "Object.assign(e, { item:r.reward ? r.reward.name : (r.genericName || 'مكافأة'), rewardId:r.reward ? r.reward.id : null, stickerId:r.reward ? codisStickerIdOk(r.reward.stickerId) : null,", 'roll snapshot')
rep("owned = CodisInventory.grant({ uid:'own|' + e.id, rewardId:e.rewardId, name:e.item,", "owned = CodisInventory.grant({ uid:'own|' + e.id, rewardId:e.rewardId, stickerId:e.stickerId, name:e.item,", 'outcome grant')
rep("CodisInventory.grant({ uid:'own|store|' + tx.id, rewardId:item.id, name:item.name,", "CodisInventory.grant({ uid:'own|store|' + tx.id, rewardId:item.id, stickerId:item.stickerId, name:item.name,", 'store grant')
rep("CodisInventory.grant({ uid:'own|box|' + uid, rewardId:it.id, name:it.name,", "CodisInventory.grant({ uid:'own|box|' + uid, rewardId:it.id, stickerId:it.stickerId, name:it.name,", 'box grant')

# ---------- 2) المحرر ----------
rep("""placeholder="مثلاً: تطلب أكل تحبه">') +""", """placeholder="مثلاً: تطلب أكل تحبه">') +
    codisStickerRowHtml(prefix, d.stickerId) +""", 'editor row')
rep("coinValue:null, storePrice:null, enabled:g('on').checked };", "coinValue:null, storePrice:null, enabled:g('on').checked, stickerId:codisStickerIdOk((g('sticker') || {}).value) };", 'read reward')
rep("(it.room === 'learn' ? '' : econRarityBadge(rar.tone, rar.id, rar.name, rar.order)) + '<span class=\"eco-item-name\">'",
    "(it.room === 'learn' ? '' : econRarityBadge(rar.tone, rar.id, rar.name, rar.order)) + codisStickerThumbHtml(it.stickerId) + '<span class=\"eco-item-name\">'", 'list thumb')

# ---------- 3) المكتبة + المنتقي + طبقة البطاقة ----------
JS = r"""/* ===== CODIS-STICKERS: مكتبة الستيكرات =====
   البيانات (المعرّف · التصنيف · الاسم · الكلمات المفتاحية · الملف) تُبنى بـ tools/build_stickers.py من tools/stickers_meta.py وملفات assets/stickers/.
   ملف الصورة غير موجود ⇒ الستيكر لا يظهر بالمنتقي ولا على البطاقة. المعرّف وحده يُخزَّن بالبيانات (لا صور ولا Base64) */
/* CODIS-STICKERS-DATA */const CODIS_STICKER_CATS=[];const CODIS_STICKER_ITEMS=[];/* /CODIS-STICKERS-DATA */
const CODIS_STK_BASE = 'assets/stickers/';
const CodisStickers = (function(){
  let idx = null;
  /* توحيد الكتابة العراقية/العربية: تشكيل وتطويل · أ إ آ ← ا · ى ← ي · ة ← ه · چ ← ج · گ ← ك · پ ← ب · ڤ ← ف */
  function norm(s){ return String(s == null ? '' : s).toLowerCase().replace(/[ً-ٰٟـ]/g, '').replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه').replace(/ؤ/g, 'و').replace(/ئ/g, 'ي').replace(/چ/g, 'ج').replace(/گ/g, 'ك').replace(/پ/g, 'ب').replace(/ڤ/g, 'ف').replace(/[^a-z0-9ء-ي\s]/g, ' ').replace(/\s+/g, ' ').trim(); }
  const strip = t=>(t.length > 3 && t.indexOf('ال') === 0) ? t.slice(2) : t;
  function build(){
    if(idx) return idx;
    const cn = {}, ck = {}; CODIS_STICKER_CATS.forEach(c=>{ cn[c[0]] = c[1]; ck[c[0]] = c[2] || ''; });
    idx = { cats:CODIS_STICKER_CATS.map(c=>({ id:c[0], name:c[1] })), byId:{}, list:[] };
    CODIS_STICKER_ITEMS.forEach(r=>{
      const o = { id:r[0], cat:r[1], name:r[2], file:r[4] || null, nameN:norm(r[2]), hay:norm(r[2] + ' ' + r[3] + ' ' + (cn[r[1]] || '') + ' ' + (ck[r[1]] || '') + ' ' + r[0].replace(/_/g, ' ')) };
      idx.byId[o.id] = o; if(o.file) idx.list.push(o);
    });
    return idx;
  }
  const url = id=>{ const o = id ? build().byId[id] : null; return o && o.file ? CODIS_STK_BASE + o.file : ''; };
  function search(q, cat){
    const I = build(), toks = norm(q).split(' ').filter(Boolean).map(strip);
    const out = I.list.filter(o=>(!cat || o.cat === cat) && toks.every(t=>o.hay.indexOf(t) !== -1));
    if(toks.length) out.sort((a, b)=>(b.nameN.indexOf(toks[0]) !== -1 ? 1 : 0) - (a.nameN.indexOf(toks[0]) !== -1 ? 1 : 0));
    return out;
  }
  function cats(){ const I = build(), n = {}; I.list.forEach(o=>{ n[o.cat] = (n[o.cat] || 0) + 1; }); return I.cats.filter(c=>n[c.id]).map(c=>({ id:c.id, name:c.name, n:n[c.id] })); }
  return { norm:norm, url:url, has:id=>!!url(id), get:id=>build().byId[id] || null, search:search, cats:cats, count:()=>build().list.length, total:()=>CODIS_STICKER_ITEMS.length };
})();
/* طبقة الستيكر على البطاقة — مصدر واحد لكل أنواع البطاقات. fam: d يومي · w أسبوعي · m شهري · s الأستاذ · p بلا صورة. بلا ستيكر/بلا صورة ⇒ نص فارغ فيبقى ناتج البطاقة كما كان */
function codisStickerLayerHtml(e, fam){
  const id = codisStickerIdOk(e && e.stickerId), u = id ? CodisStickers.url(id) : '';
  return u ? '<img class="rwc-stk rwc-stk-' + fam + '" src="' + escapeHtml(u) + '" alt="" draggable="false" decoding="async" onerror="this.remove()">' : '';
}
function codisStickerThumbHtml(id){ const u = CodisStickers.url(codisStickerIdOk(id)); return u ? '<img class="stk-mini" src="' + escapeHtml(u) + '" alt="" draggable="false" loading="lazy" onerror="this.remove()">' : ''; }
/* صف الاختيار داخل محرر المكافأة */
function codisStickerRowInner(prefix, id){
  const o = id ? CodisStickers.get(id) : null, u = id ? CodisStickers.url(id) : '';
  const th = u ? '<img src="' + escapeHtml(u) + '" alt="" draggable="false" onerror="this.remove()">' : codisIcon('gift');
  const label = !id ? 'إضافة ستيكر' : (u ? 'تغيير الستيكر' : 'ستيكر محفوظ');
  const sub = !id ? 'اختياري — صورة تُلصق على بطاقة المكافأة' : (u && o ? o.name : 'صورته غير متوفرة حالياً');
  return '<button type="button" class="stk-pick" onclick="codisOpenStickerPicker(\'' + prefix + '\')"><span class="stk-th' + (u ? ' has' : '') + '">' + th + '</span><span class="stk-tx"><b>' + label + '</b><i>' + escapeHtml(sub) + '</i></span></button>' +
    (id ? '<button type="button" class="stk-x" aria-label="إزالة الستيكر" onclick="codisSetSticker(\'' + prefix + '\', \'\')">' + ICONS.close + '</button>' : '');
}
function codisStickerRowHtml(prefix, id){
  id = codisStickerIdOk(id) || '';
  return '<div class="stk-row" id="' + prefix + '-stk-row">' + codisStickerRowInner(prefix, id) + '</div><input type="hidden" id="' + prefix + '-sticker" value="' + id + '">';
}
function codisSetSticker(prefix, id){
  const h = document.getElementById(prefix + '-sticker'); if(!h) return;
  h.value = codisStickerIdOk(id) || ''; const r = document.getElementById(prefix + '-stk-row'); if(r) r.innerHTML = codisStickerRowInner(prefix, h.value);
}
/* معاينة: نفس وجه البطاقة الحقيقي بقيم الفورم الحالية (الاسم/الندرة/القائمة) مع الستيكر المحدد */
function codisStickerPreviewHtml(prefix, id){
  const g = k=>document.getElementById(prefix + '-' + k), room = g('room') ? g('room').value : 'tasks', cfg = econCfg().rarities;
  const rar = (room === 'learn' ? cfg[0] : (econRarityById(g('rarity') ? g('rarity').value : '') || cfg[0])), nm = (g('name') && g('name').value.trim()) || 'اسم المكافأة';
  try{ return econStoreFaceHtml({ room:room, name:nm, stickerId:id }, rar, { label:nm }); }catch(x){ return ''; }
}
var stickerSheet = null;
function closeStickerPicker(){
  const s = stickerSheet; if(!s) return; stickerSheet = null;
  document.removeEventListener('keydown', s.onKey, true); s.root.classList.remove('is-open'); codisSfx('close', { ctx:'sheet' });
  setTimeout(()=>s.root.remove(), 220); try{ s.opener && s.opener.isConnected && s.opener.focus({ preventScroll:true }); }catch(e){}
}
function codisOpenStickerPicker(prefix){
  if(stickerSheet) return;
  const hid = document.getElementById(prefix + '-sticker'); if(!hid) return;
  const cur = codisStickerIdOk(hid.value) || '', root = document.createElement('div'); root.className = 'cd-ov stk-ov';
  root.innerHTML = '<div class="cd-back"></div><div class="cd-sheet stk-sheet" role="dialog" aria-modal="true" aria-label="مكتبة الستيكرات"><div class="cd-grab" aria-hidden="true"></div>' +
    '<div class="cd-head"><h2 class="cd-title">مكتبة الستيكرات</h2><button type="button" class="cd-close" aria-label="إغلاق">' + ICONS.close + '</button></div>' +
    '<div class="stk-bar"><input type="search" class="stk-q" placeholder="ابحث: شاورمة، چاي، كنافة…" aria-label="بحث بالستيكرات" autocomplete="off" enterkeyhint="search"><div class="stk-cats" role="group" aria-label="التصنيفات"></div></div>' +
    '<div class="cd-body stk-body"><div class="stk-grid" role="listbox" aria-label="الستيكرات"></div></div><div class="stk-foot"></div></div>';
  document.body.appendChild(root);
  const st = { root:root, opener:document.activeElement, onKey:ev=>{ if(ev.key === 'Escape'){ ev.stopPropagation(); closeStickerPicker(); } } };
  stickerSheet = st; document.addEventListener('keydown', st.onKey, true); codisSfx('open', { ctx:'sheet' });
  const q = root.querySelector('.stk-q'), cats = root.querySelector('.stk-cats'), grid = root.querySelector('.stk-grid'), foot = root.querySelector('.stk-foot');
  let cat = '', sel = cur;
  const paintCats = ()=>{
    const cs = CodisStickers.cats(); cats.style.display = cs.length ? '' : 'none';
    cats.innerHTML = '<button type="button" class="stk-chip' + (cat ? '' : ' is-on') + '" data-c="" aria-pressed="' + (cat ? 'false' : 'true') + '">الكل</button>' +
      cs.map(c=>'<button type="button" class="stk-chip' + (cat === c.id ? ' is-on' : '') + '" data-c="' + c.id + '" aria-pressed="' + (cat === c.id ? 'true' : 'false') + '">' + escapeHtml(c.name) + '</button>').join('');
  };
  const paintGrid = ()=>{
    const list = CodisStickers.search(q.value, cat);
    if(!CodisStickers.count()){ grid.innerHTML = '<div class="stk-empty">المكتبة فاضية حالياً — صور الستيكرات تنضاف قريباً.</div>'; return; }
    if(!list.length){ grid.innerHTML = '<div class="stk-empty">ما لكينا ستيكر بهالاسم — جرّب كلمة ثانية أو شيل التصنيف.</div>'; return; }
    grid.innerHTML = list.map(o=>'<button type="button" class="stk-tile' + (o.id === cur ? ' is-cur' : '') + '" role="option" data-id="' + o.id + '" aria-selected="' + (o.id === sel ? 'true' : 'false') + '"><img src="' + escapeHtml(CodisStickers.url(o.id)) + '" alt="" loading="lazy" decoding="async" draggable="false" onerror="this.remove()"><span>' + escapeHtml(o.name) + '</span></button>').join('');
  };
  const paintFoot = ()=>{
    const o = sel ? CodisStickers.get(sel) : null, ok = !!(o && CodisStickers.has(sel));
    foot.innerHTML = (ok ? '<div class="stk-pv" aria-hidden="true">' + codisStickerPreviewHtml(prefix, sel) + '</div>' : '') +
      '<div class="stk-fx">' + (ok ? '<div class="stk-name">' + escapeHtml(o.name) + '</div>' : '<div class="stk-hint">اختر ستيكراً لمعاينته على بطاقة المكافأة</div>') +
      '<div class="stk-act">' + (ok ? '<button type="button" class="btn btn-primary" data-a="ok">اعتماد الستيكر</button>' : '') +
      (cur ? '<button type="button" class="btn btn-secondary" data-a="rm">إزالة الستيكر</button>' : '') + '</div></div>';
  };
  root.addEventListener('click', ev=>{
    const t = ev.target.closest('button, .cd-back'); if(!t) return;
    if(t.classList.contains('cd-back') || t.classList.contains('cd-close')){ closeStickerPicker(); return; }
    if(t.classList.contains('stk-chip')){ cat = t.dataset.c || ''; codisSfx('open', { ctx:'select' }); paintCats(); paintGrid(); return; }
    if(t.classList.contains('stk-tile')){
      sel = t.dataset.id; codisSfx('open', { ctx:'select' });
      grid.querySelectorAll('.stk-tile').forEach(b=>b.setAttribute('aria-selected', b.dataset.id === sel ? 'true' : 'false')); paintFoot(); return;
    }
    if(t.dataset.a === 'ok'){ codisSetSticker(prefix, sel); codisSfx('confirm', { ctx:'switch' }); closeStickerPicker(); return; }
    if(t.dataset.a === 'rm'){ codisSetSticker(prefix, ''); codisSfx('close', { ctx:'editor' }); closeStickerPicker(); }
  });
  q.addEventListener('input', paintGrid);
  paintCats(); paintGrid(); paintFoot();
  requestAnimationFrame(()=>root.classList.add('is-open'));
}
function econRewardHintText(rarityId, room){"""
rep("function econRewardHintText(rarityId, room){", JS, 'library js')

# ---------- 4) البطاقات ----------
rep("""'<img class="rwc-art" src="' + CodisArt.src(codisCardArtSrc(k, o.cosmetic)) + '" alt="" draggable="false">' + codisCosmeticLayerHtml(k, o.cosmetic) +""",
    """'<img class="rwc-art" src="' + CodisArt.src(codisCardArtSrc(k, o.cosmetic)) + '" alt="" draggable="false">' + codisCosmeticLayerHtml(k, o.cosmetic) + codisStickerLayerHtml(e, 'd') +""", 'daily card')
rep("""'<img class="rwc-art" src="' + CodisArt.src(CODIS_WEEKLY_ART[k]) + '" alt="" draggable="false">' +""",
    """'<img class="rwc-art" src="' + CodisArt.src(CODIS_WEEKLY_ART[k]) + '" alt="" draggable="false">' + codisStickerLayerHtml(e, 'w') +""", 'weekly card')
rep("""'<img class="rwc-art" src="' + CodisArt.src(CODIS_MONTHLY_ART[k]) + '" alt="" draggable="false">' +""",
    """'<img class="rwc-art" src="' + CodisArt.src(CODIS_MONTHLY_ART[k]) + '" alt="" draggable="false">' + codisStickerLayerHtml(e, 'm') +""", 'monthly card')
rep("return codisSpecialCardHtml('teacher', { name:e.item, coin:(o.price !== undefined ? o.price : e.coinValue), plain:o.plain, label:o.label });",
    "return codisSpecialCardHtml('teacher', { name:e.item, coin:(o.price !== undefined ? o.price : e.coinValue), plain:o.plain, label:o.label, stickerId:e.stickerId });", 'teacher call')
rep("""'<img class="rwc-art scx-art" src="' + CodisArt.src(CODIS_SPECIAL_CARD_ART[k]) + '" alt="" draggable="false">' +""",
    """'<img class="rwc-art scx-art" src="' + CodisArt.src(CODIS_SPECIAL_CARD_ART[k]) + '" alt="" draggable="false">' + codisStickerLayerHtml(o, 's') +""", 'special card')
rep("""  return '<div class="cfp rwc-' + tone + '" role="img" aria-label="' + escapeHtml(o.label || name) + '"><span class="cfp-in">""",
    """  return '<div class="cfp rwc-' + tone + '" role="img" aria-label="' + escapeHtml(o.label || name) + '">' + codisStickerLayerHtml(o, 'p') + '<span class="cfp-in">""", 'plain card')
# المتجر/التفاصيل/البكجات/المخزون: الكائنات المركّبة تحمل stickerId
rep("codisMonthlyCardHtml({ kind:'reward', scope:'monthly', room:it.room, rarityTone:rar.tone, item:it.name, rarityName:rar.name }, { plain:true,",
    "codisMonthlyCardHtml({ kind:'reward', scope:'monthly', room:it.room, rarityTone:rar.tone, item:it.name, rarityName:rar.name, stickerId:it.stickerId }, { plain:true,", 'store monthly')
rep("codisWeeklyCardHtml({ kind:'reward', scope:'weekly', room:it.room, rarityTone:rar.tone, item:it.name }, { plain:true,",
    "codisWeeklyCardHtml({ kind:'reward', scope:'weekly', room:it.room, rarityTone:rar.tone, item:it.name, stickerId:it.stickerId }, { plain:true,", 'store weekly')
rep("codisRewardCardHtml({ kind:'reward', scope:'daily', room:it.room, rarityTone:rar.tone, item:it.name }, { plain:true, price:o.price, label:o.label });",
    "codisRewardCardHtml({ kind:'reward', scope:'daily', room:it.room, rarityTone:rar.tone, item:it.name, stickerId:it.stickerId }, { plain:true, price:o.price, label:o.label });", 'store daily')
rep("return codisPlainCardHtml(it.name, rar, { label:o.label });", "return codisPlainCardHtml(it.name, rar, { label:o.label, stickerId:it.stickerId });", 'store plain')
rep("'<div class=\"pk-plain\">' + codisPlainCardHtml(it.name, rar) + '</div>'", "'<div class=\"pk-plain\">' + codisPlainCardHtml(it.name, rar, { stickerId:it.stickerId }) + '</div>'", 'pack plain')
rep("econPackTileHtml({ id:it.uid, room:it.room, name:it.name }, { id:it.rarity,", "econPackTileHtml({ id:it.uid, room:it.room, name:it.name, stickerId:it.stickerId }, { id:it.rarity,", 'inventory tile')

# ---------- 5) رجوع + CSS ----------
rep("  if(graceSheet) return { act:closeGraceSheet, el:graceSheet.root };", "  if(stickerSheet) return { act:closeStickerPicker, el:stickerSheet.root };\n  if(graceSheet) return { act:closeGraceSheet, el:graceSheet.root };", 'back layer')
css = r"""
/* CODIS-STICKERS */
.stk-row{ display:flex; align-items:center; gap:8px; margin:2px 0 10px; }
.stk-pick{ flex:1; min-width:0; display:flex; align-items:center; gap:12px; min-height:56px; padding:8px 12px; border-radius:14px; border:1px dashed rgb(var(--hi-rgb) / .24); background:rgb(var(--hi-rgb) / .04); color:var(--text); font:inherit; text-align:start; cursor:pointer; -webkit-tap-highlight-color:transparent; }
.stk-pick:active{ background:rgb(var(--hi-rgb) / .09); }
.stk-pick:focus-visible, .stk-x:focus-visible, .stk-tile:focus-visible, .stk-chip:focus-visible, .stk-q:focus-visible{ outline:2px solid var(--aqua); outline-offset:2px; }
.stk-th{ flex:none; width:44px; height:44px; border-radius:12px; display:grid; place-items:center; background:rgb(var(--hi-rgb) / .07); color:var(--text-3); overflow:hidden; }
.stk-th svg{ width:22px; height:22px; }
.stk-th.has{ background:none; overflow:visible; }
.stk-th img{ width:100%; height:100%; object-fit:contain; transform:rotate(-6deg); filter:drop-shadow(0 2px 3px rgba(0,0,0,.4)); }
.stk-tx{ display:flex; flex-direction:column; min-width:0; }
.stk-tx b{ font-size:14.5px; font-weight:700; }
.stk-tx i{ font-style:normal; font-size:12px; color:var(--text-3); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stk-x{ flex:none; width:44px; height:44px; border-radius:50%; border:0; background:rgb(var(--hi-rgb) / .06); color:var(--text-2); cursor:pointer; display:grid; place-items:center; }
.stk-x svg{ width:18px; height:18px; }
.stk-mini{ width:28px; height:28px; object-fit:contain; flex:none; transform:rotate(-6deg); filter:drop-shadow(0 1px 2px rgba(0,0,0,.4)); }
.stk-sheet{ max-height:88vh; }
.stk-bar{ padding:0 16px 8px; display:flex; flex-direction:column; gap:8px; }
.stk-q{ width:100%; min-height:46px; padding:0 14px; border-radius:12px; border:1px solid rgb(var(--hi-rgb) / .14); background:rgb(var(--hi-rgb) / .05); color:var(--text); font:inherit; font-size:16px; }
.stk-cats{ display:flex; gap:6px; overflow-x:auto; padding-bottom:2px; scrollbar-width:none; }
.stk-cats::-webkit-scrollbar{ display:none; }
.stk-chip{ flex:none; min-height:40px; padding:0 14px; border-radius:20px; border:1px solid rgb(var(--hi-rgb) / .14); background:none; color:var(--text-2); font:inherit; font-size:13px; font-weight:600; cursor:pointer; white-space:nowrap; }
.stk-chip.is-on{ background:var(--aqua); color:#04121a; border-color:transparent; }
.stk-body{ min-height:170px; padding-top:4px; }
.stk-grid{ display:grid; grid-template-columns:repeat(auto-fill, minmax(88px, 1fr)); gap:8px; }
.stk-tile{ position:relative; display:flex; flex-direction:column; align-items:center; gap:4px; padding:8px 4px 6px; border-radius:14px; border:1.5px solid transparent; background:rgb(var(--hi-rgb) / .04); color:var(--text-2); font:inherit; cursor:pointer; -webkit-tap-highlight-color:transparent; }
.stk-tile img{ width:100%; aspect-ratio:1; object-fit:contain; display:block; }
.stk-tile span{ font-size:11.5px; line-height:1.3; text-align:center; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stk-tile[aria-selected="true"]{ border-color:var(--aqua); background:rgb(var(--hi-rgb) / .09); color:var(--text); }
.stk-tile.is-cur::after{ content:''; position:absolute; top:6px; inset-inline-end:6px; width:8px; height:8px; border-radius:50%; background:var(--success); }
.stk-empty{ grid-column:1 / -1; padding:34px 8px; text-align:center; color:var(--text-3); font-size:14px; line-height:1.7; }
.stk-foot{ flex:none; display:flex; align-items:center; gap:14px; padding:10px 16px calc(12px + env(safe-area-inset-bottom)); border-top:1px solid rgb(var(--hi-rgb) / .08); min-height:84px; }
.stk-pv{ flex:none; width:74px; position:relative; aspect-ratio:4 / 5; }
.stk-pv .rwc-wrap, .stk-pv .cfp{ position:absolute; inset:0; }
.stk-fx{ flex:1; min-width:0; display:flex; flex-direction:column; gap:8px; }
.stk-name{ font-weight:700; font-size:14px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stk-hint{ font-size:13px; color:var(--text-3); }
.stk-act{ display:flex; gap:8px; flex-wrap:wrap; }
.stk-act .btn{ min-height:44px; padding:0 14px; font-size:14px; }
/* طبقة الستيكر على البطاقة: ملصق مائل عند الزاوية العليا فوق إطار الرسم، بعيداً عن الاسم والقيمة والندرة */
.rwc-stk{ position:absolute; z-index:3; aspect-ratio:1; object-fit:contain; pointer-events:none; -webkit-user-drag:none; transform:rotate(-9deg); transform-origin:50% 50%; filter:drop-shadow(0 1px 0 rgba(255,255,255,.22)) drop-shadow(0 3px 5px rgba(0,0,0,.5)); }
.rwc-stk-d, .rwc-stk-w, .rwc-stk-s{ left:-2.5%; top:-2%; width:33%; }
.rwc-stk-m{ left:-4%; top:-1.5%; width:44%; }
.rwc-stk-p{ left:3%; top:2%; width:36%; }
.cfp{ position:relative; }
"""
rep("</style>", css + "</style>", 'css')
rep("<!-- CODIS-CYCLE -->", "<!-- CODIS-CYCLE -->\n<!-- CODIS-STICKERS -->", 'marker')
open(dst, 'w', encoding='utf-8', newline='').write(s)
print('patch_v17 OK')
