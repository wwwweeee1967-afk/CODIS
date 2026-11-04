#!/usr/bin/env python3
"""CODIS-MULTI-STICKER (بعد patch_v29.py) — 3.17.0 — حتى 3 ستيكرات على بطاقة المكافأة الواحدة.
 - البيانات: نفس الحقل stickerId يحمل قائمة مرتّبة 'falafel+tea_glass+kunafa' (الأول = الرئيسي). كل مسارات اللقطة الحالية
   (المكافأة ← النتيجة ← المملوكة ← الشراء ← البكج) تنسخ الحقل كما هو ⇒ البطاقات القديمة تحتفظ بستيكراتها بلا ترحيل.
   codisStickerIdOk ينظّف القائمة (معرّفات صالحة، بلا تكرار، 3 كحد أقصى)؛ القيمة المفردة القديمة تبقى كما هي حرفياً.
 - العرض: الرئيسي بوسمه وقواعده نفسها حرفياً (.rwc-stk)؛ الثاني والثالث (.rwc-stk2) عمود متدرّج تحته على الحافة اليسرى بموضع
   من CodisAtmos (STK2) لكل عائلة بطاقة، وزخرفة الجو تتجنّب مكانهما وتمزج بطل كل ستيكر إضافي.
 - المنتقي: اختيار متعدد مرتّب (حتى 3) بأرقام على الخانات، شريط المختارة بالأسفل (النقر = اجعله الرئيسي، ✕ = إزالة)، معاينة البطاقة الكاملة.
 الاستعمال: py -3 tools/patch_v30.py app/CODIS_FINAL.html app/CODIS_FINAL.html (بعد v29) ثم py -3 tools/build_stickers.py"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
if 'const CODIS_STICKER_MAX' in s: sys.exit('already patched (CODIS-MULTI-STICKER)')
if 'CODIS-STICKER-ATMOS' not in s: sys.exit('apply patch_v29.py first')

def rep(old, new, label, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit('anchor "%s" matched %d times (expected %d)' % (label, c, n))
    s = s.replace(old, new)

# ---------------------------------------------------------------- 1. قاعدة البيانات: قائمة مرتّبة بنفس الحقل
rep("""function codisStickerIdOk(v){ return (typeof v === 'string' && /^[a-z0-9_]{2,32}$/.test(v)) ? v : null; }""",
    """/* CODIS-MULTI-STICKER: stickerId = معرّف واحد أو قائمة مرتّبة 'a+b+c' (الأول هو الرئيسي، 3 كحد أقصى). المفرد القديم يرجع كما هو حرفياً */
const CODIS_STICKER_MAX = 3;
function codisStickerIdOk(v){
  if(typeof v !== 'string') return null;
  if(/^[a-z0-9_]{2,32}$/.test(v)) return v;
  const a = []; v.split('+').forEach(x=>{ if(/^[a-z0-9_]{2,32}$/.test(x) && a.indexOf(x) === -1 && a.length < CODIS_STICKER_MAX) a.push(x); });
  return a.length ? a.join('+') : null;
}
function codisStickerList(v){ const ok = codisStickerIdOk(v); return ok ? ok.split('+') : []; }""", 'id ok')

# ---------------------------------------------------------------- 2. طبقة البطاقة: الرئيسي بوسمه نفسه + الإضافيان تحته
rep("""function codisStickerLayerHtml(e, fam, k){
  const id = codisStickerIdOk(e && e.stickerId), u = id ? CodisStickers.url(id) : '';
  return u ? CodisAtmos.html(id, fam, k) + '<img class="rwc-stk rwc-stk-' + fam + '" src="' + escapeHtml(u) + '" alt="" draggable="false" decoding="async" onerror="this.remove()">' : '';
}""", """function codisStickerLayerHtml(e, fam, k){
  const ids = codisStickerList(e && e.stickerId).filter(x=>CodisStickers.url(x));   /* ما له صورة فقط؛ أول المتوفر هو الرئيسي */
  if(!ids.length) return '';
  const u = CodisStickers.url(ids[0]);
  return CodisAtmos.html(ids.join('+'), fam, k) + CodisAtmos.extras(ids, fam) + '<img class="rwc-stk rwc-stk-' + fam + '" src="' + escapeHtml(u) + '" alt="" draggable="false" decoding="async" onerror="this.remove()">';
}""", 'layer')

rep(""".cfp > .rwc-atm{ z-index:2; }""", """.cfp > .rwc-atm{ z-index:2; }
/* CODIS-MULTI-STICKER: الستيكر الثاني والثالث — نفس معالجة الرئيسي (ظل/حافة) بحجم وميل من موضعهما؛ الرئيسي يعلوهما بترتيب الوسم */
.rwc-stk2{ position:absolute; z-index:3; aspect-ratio:1; object-fit:contain; pointer-events:none; -webkit-user-drag:none; user-select:none; transform:rotate(var(--r, 0deg)); transform-origin:50% 50%; filter:drop-shadow(0 1px 0 rgba(255,255,255,.22)) drop-shadow(0 3px 5px rgba(0,0,0,.5)); }
.stk-th.has.n2 img, .stk-th.has.n3 img{ position:absolute; width:74%; height:74%; }
.stk-th.has.n2, .stk-th.has.n3{ position:relative; }
.stk-th.has.n2 img:nth-child(1), .stk-th.has.n3 img:nth-child(1){ left:0; top:0; z-index:3; }
.stk-th.has.n2 img:nth-child(2), .stk-th.has.n3 img:nth-child(2){ right:-4px; bottom:-2px; z-index:2; transform:rotate(8deg); }
.stk-th.has.n3 img:nth-child(3){ left:6px; bottom:-6px; width:56%; height:56%; z-index:1; transform:rotate(-10deg); }
.stk-mini + .stk-mini{ margin-inline-start:-12px; }
.stk-tile .stk-ord{ position:absolute; top:5px; inset-inline-start:5px; min-width:22px; height:22px; padding:0 5px; border-radius:11px; display:grid; place-items:center; background:var(--aqua); color:#04121a; font:800 12px/1 system-ui, sans-serif; box-shadow:0 2px 6px rgba(0,0,0,.35); }
.stk-tile .stk-ord.is-main{ background:#f2c35a; }
.stk-sel{ display:flex; gap:6px; flex-wrap:wrap; }
.stk-sel button{ display:flex; align-items:center; gap:6px; min-height:40px; padding:3px 6px 3px 10px; border-radius:20px; border:1px solid rgb(var(--hi-rgb) / .16); background:rgb(var(--hi-rgb) / .05); color:var(--text); font:inherit; font-size:12.5px; cursor:pointer; }
.stk-sel button.is-main{ border-color:#f2c35a; background:rgb(242 195 90 / .12); }
.stk-sel button img{ width:28px; height:28px; object-fit:contain; }
.stk-sel button b{ font-size:11px; color:var(--text-3); font-weight:700; }
.stk-sel button i{ font-style:normal; width:24px; height:24px; display:grid; place-items:center; border-radius:50%; color:var(--text-2); }
.stk-sel button i svg{ width:14px; height:14px; }""", 'css')

# ---------------------------------------------------------------- 3. صف المحرر + الأيقونة المصغّرة بقائمة المكافآت
rep("""function codisStickerThumbHtml(id){ const u = CodisStickers.url(codisStickerIdOk(id)); return u ? '<img class="stk-mini" src="' + escapeHtml(u) + '" alt="" draggable="false" loading="lazy" onerror="this.remove()">' : ''; }""",
    """function codisStickerThumbHtml(id){ return codisStickerList(id).map(x=>CodisStickers.url(x)).filter(Boolean).map(u=>'<img class="stk-mini" src="' + escapeHtml(u) + '" alt="" draggable="false" loading="lazy" onerror="this.remove()">').join(''); }""", 'thumb')

rep("""function codisStickerRowInner(prefix, id){
  const o = id ? CodisStickers.get(id) : null, u = id ? CodisStickers.url(id) : '';
  const th = u ? '<img src="' + escapeHtml(u) + '" alt="" draggable="false" onerror="this.remove()">' : codisIcon('gift');
  const label = !id ? 'إضافة ستيكر' : (u ? 'تغيير الستيكر' : 'ستيكر محفوظ');
  const sub = !id ? 'اختياري — صورة تُلصق على بطاقة المكافأة' : (u && o ? o.name : 'صورته غير متوفرة حالياً');
  return '<button type="button" class="stk-pick" onclick="codisOpenStickerPicker(\\'' + prefix + '\\')"><span class="stk-th' + (u ? ' has' : '') + '">' + th + '</span><span class="stk-tx"><b>' + label + '</b><i>' + escapeHtml(sub) + '</i></span></button>' +
    (id ? '<button type="button" class="stk-x" aria-label="إزالة الستيكر" onclick="codisSetSticker(\\'' + prefix + '\\', \\'\\')">' + ICONS.close + '</button>' : '');
}""", """function codisStickerRowInner(prefix, id){
  const ids = codisStickerList(id), av = ids.filter(x=>CodisStickers.url(x)), n = av.length;
  const th = n ? av.map(x=>'<img src="' + escapeHtml(CodisStickers.url(x)) + '" alt="" draggable="false" onerror="this.remove()">').join('') : codisIcon('gift');
  const label = !ids.length ? 'إضافة ستيكر' : (n ? (n > 1 ? 'تغيير الستيكرات (' + n + ')' : 'تغيير الستيكر') : 'ستيكر محفوظ');
  const sub = !ids.length ? 'اختياري — حتى ' + CODIS_STICKER_MAX + ' ستيكرات تُلصق على بطاقة المكافأة' : (n ? av.map(x=>(CodisStickers.get(x) || {}).name || '').filter(Boolean).join(' · ') : 'صورته غير متوفرة حالياً');
  return '<button type="button" class="stk-pick" onclick="codisOpenStickerPicker(\\'' + prefix + '\\')"><span class="stk-th' + (n ? ' has' : '') + (n > 1 ? ' n' + n : '') + '">' + th + '</span><span class="stk-tx"><b>' + label + '</b><i>' + escapeHtml(sub) + '</i></span></button>' +
    (ids.length ? '<button type="button" class="stk-x" aria-label="' + (ids.length > 1 ? 'إزالة الستيكرات' : 'إزالة الستيكر') + '" onclick="codisSetSticker(\\'' + prefix + '\\', \\'\\')">' + ICONS.close + '</button>' : '');
}""", 'row')

# ---------------------------------------------------------------- 4. المنتقي: اختيار متعدد مرتّب
rep("""  const cur = codisStickerIdOk(hid.value) || '', root = document.createElement('div'); root.className = 'cd-ov stk-ov';""",
    """  const cur = codisStickerIdOk(hid.value) || '', root = document.createElement('div'); root.className = 'cd-ov stk-ov';
  const curIds = codisStickerList(cur);""", 'picker cur')
rep("""  let cat = '', sel = cur;""", """  let cat = '', sel = curIds.filter(x=>CodisStickers.has(x));   /* قائمة مرتّبة: الأول هو الرئيسي */""", 'picker sel')
rep("""    grid.innerHTML = list.map(o=>'<button type="button" class="stk-tile' + (o.id === cur ? ' is-cur' : '') + '" role="option" data-id="' + o.id + '" aria-selected="' + (o.id === sel ? 'true' : 'false') + '"><img src="' + escapeHtml(CodisStickers.url(o.id)) + '" alt="" loading="lazy" decoding="async" draggable="false" onerror="this.remove()"><span>' + escapeHtml(o.name) + '</span></button>').join('');
  };""", """    grid.innerHTML = list.map(o=>{ const i = sel.indexOf(o.id);
      return '<button type="button" class="stk-tile' + (curIds.indexOf(o.id) !== -1 ? ' is-cur' : '') + '" role="option" data-id="' + o.id + '" aria-selected="' + (i !== -1 ? 'true' : 'false') + '"><img src="' + escapeHtml(CodisStickers.url(o.id)) + '" alt="" loading="lazy" decoding="async" draggable="false" onerror="this.remove()"><span>' + escapeHtml(o.name) + '</span>' +
        (i !== -1 ? '<b class="stk-ord' + (i === 0 ? ' is-main' : '') + '" aria-hidden="true">' + (i + 1) + '</b>' : '') + '</button>'; }).join('');
  };
  const syncTiles = ()=>grid.querySelectorAll('.stk-tile').forEach(b=>{
    const i = sel.indexOf(b.dataset.id), old = b.querySelector('.stk-ord'); b.setAttribute('aria-selected', i !== -1 ? 'true' : 'false'); if(old) old.remove();
    if(i !== -1) b.insertAdjacentHTML('beforeend', '<b class="stk-ord' + (i === 0 ? ' is-main' : '') + '" aria-hidden="true">' + (i + 1) + '</b>');
  });""", 'picker grid')
rep("""  const paintFoot = ()=>{
    const o = sel ? CodisStickers.get(sel) : null, ok = !!(o && CodisStickers.has(sel));
    foot.innerHTML = (ok ? '<div class="stk-pv" aria-hidden="true">' + codisStickerPreviewHtml(prefix, sel) + '</div>' : '') +
      '<div class="stk-fx">' + (ok ? '<div class="stk-name">' + escapeHtml(o.name) + '</div>' : '<div class="stk-hint">اختر ستيكراً لمعاينته على بطاقة المكافأة</div>') +
      '<div class="stk-act">' + (ok ? '<button type="button" class="btn btn-primary" data-a="ok">اعتماد الستيكر</button>' : '') +
      (cur ? '<button type="button" class="btn btn-secondary" data-a="rm">إزالة الستيكر</button>' : '') + '</div></div>';
  };""", """  const paintFoot = ()=>{
    const ok = sel.length > 0, val = sel.join('+');
    const chips = sel.map((x, i)=>'<button type="button" class="' + (i === 0 ? 'is-main' : '') + '" data-mk="' + x + '" aria-label="' + escapeHtml((CodisStickers.get(x) || {}).name || x) + (i === 0 ? ' — الرئيسي' : ' — اجعله الرئيسي') + '"><img src="' + escapeHtml(CodisStickers.url(x)) + '" alt="" draggable="false"><b>' + (i === 0 ? 'الرئيسي' : (i + 1)) + '</b>' +
      '<i data-rmk="' + x + '" role="button" aria-label="إزالة">' + ICONS.close + '</i></button>').join('');
    foot.innerHTML = (ok ? '<div class="stk-pv" aria-hidden="true">' + codisStickerPreviewHtml(prefix, val) + '</div>' : '') +
      '<div class="stk-fx">' + (ok ? '<div class="stk-sel">' + chips + '</div>' : '<div class="stk-hint">اختر حتى ' + CODIS_STICKER_MAX + ' ستيكرات — الأول هو الرئيسي ويبقى بمكانه</div>') +
      '<div class="stk-act">' + (ok ? '<button type="button" class="btn btn-primary" data-a="ok">' + (sel.length > 1 ? 'اعتماد الستيكرات' : 'اعتماد الستيكر') + '</button>' : '') +
      (cur ? '<button type="button" class="btn btn-secondary" data-a="rm">' + (curIds.length > 1 ? 'إزالة الكل' : 'إزالة الستيكر') + '</button>' : '') + '</div></div>';
  };""", 'picker foot')
rep("""    if(t.classList.contains('stk-tile')){
      sel = t.dataset.id; codisSfx('open', { ctx:'select' });
      grid.querySelectorAll('.stk-tile').forEach(b=>b.setAttribute('aria-selected', b.dataset.id === sel ? 'true' : 'false')); paintFoot(); return;
    }
    if(t.dataset.a === 'ok'){ codisSetSticker(prefix, sel); codisSfx('confirm', { ctx:'switch' }); closeStickerPicker(); return; }""",
    """    if(t.classList.contains('stk-tile')){
      const id = t.dataset.id, i = sel.indexOf(id);
      if(i !== -1) sel.splice(i, 1);
      else if(sel.length < CODIS_STICKER_MAX) sel.push(id);
      else { showToast('الحد ' + CODIS_STICKER_MAX + ' ستيكرات للبطاقة — شيل واحد أولاً', 'var(--warning)'); return; }
      codisSfx('open', { ctx:'select' }); syncTiles(); paintFoot(); return;
    }
    if(t.dataset.mk){   /* شريط المختارة: ✕ يزيل، والنقر يجعله الرئيسي */
      const rm = ev.target.closest('[data-rmk]'), id = t.dataset.mk;
      sel = sel.filter(x=>x !== id); if(!rm) sel.unshift(id);
      codisSfx('open', { ctx:'select' }); syncTiles(); paintFoot(); return;
    }
    if(t.dataset.a === 'ok'){ codisSetSticker(prefix, sel.join('+')); codisSfx('confirm', { ctx:'switch' }); closeStickerPicker(); return; }""", 'picker click')

open(dst, 'w', encoding='utf-8', newline='').write(s)
print('CODIS-MULTI-STICKER applied ->', dst)
