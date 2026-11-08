/* ===== CODIS-PAPER-BACK (3.24.0) — ظهر البطاقة الخاص بالمظهر الورقي =====
   • التركيبة واحدة للمظهرين (الصنف is-paper = «ظهر الأتيليه»)؛ الورقي حبر على ورق والداكن طبعة ليلية بحبر معدني — الألوان كلها متغيرات CSS.
   • تصميم وثيقة محفورة عتيقة (ورقة نقدية × طابع بريد): ورق وحبر لكل ندرة (C سيبيا/عاجي مضلّع · B نيلي/ورق رسائل · A باذنجاني/وردي · S بنّي+رقائق ذهب/رق · SS دموي+ذهب)،
     نقش خلفية وشريط حدود لكل ندرة، ميدالية «غيوشيه» تتولّد من اسم البطاقة نفسه (عدد البتلات والطور مختلف لكل بطاقة) وفي قلبها ستيكر البطاقة إن وُجد،
     ختم بريد بزاوية وموضع ثابتين لكل بطاقة (أو ختم شمع لـS/SS)، رقم تسلسلي وطباعة دقيقة، وزخارف خاصة بالنوع (أسبوعية/شهرية/تجاوز/عطلة/كيس/مظهر/بكج).
   • حتمي (لا Math.random) وبلا فلاتر SVG. تبديل المظهر وقت التشغيل يعيد رسم الظهور المبنية (MutationObserver على data-theme). */
function codisCbkPaper(){ try{ return document.documentElement.getAttribute('data-theme') !== 'dark'; }catch(e){ return true; } }
/* سلسلة البطاقة (سطر الترويسة) — على طريقة ظهور بطاقات السجائر العتيقة: «سلسلة» ثم «رقم» ثم الرسم ثم العنوان ثم التفاصيل ثم «صادرة عن» */
const CBK_KIND_AR = { reward:'سلسلة المكافآت', weekly:'المكافآت الأسبوعية', monthly:'المكافآت الشهرية', pass:'بطاقات التجاوز', holiday:'بطاقات العطلة', pouch:'أكياس الفضة', cosmetic:'المظاهر', box:'البكجات' };
function codisPaperBackSvg(tone, kind, seed, stk){
  try{
    const f = n=>Math.round(n * 100) / 100, P = [], PI = Math.PI;
    let h = 2166136261; String(seed || '').concat('|', tone, '|', kind).split('').forEach(ch=>{ h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; });
    const H0 = h; let x0 = h || 1; const rnd = ()=>{ x0 = (Math.imul(x0, 1664525) + 1013904223) >>> 0; return x0 / 4294967296; };
    const gold = tone === 's' || tone === 'ss', rank = { c:0, b:1, a:2, s:3, ss:4 }[tone] || 0;
    const AR = '٠١٢٣٤٥٦٧٨٩', num = String(100 + H0 % 900).replace(/\d/g, d=>AR[d]);
    const code = (typeof CBK_CODE !== 'undefined' && CBK_CODE[tone]) || 'C';
    const poly = pts=>'M' + pts.map(p=>f(p[0]) + ' ' + f(p[1])).join('L');
    const FR = gold ? 'p-foil-s' : 'p-ink';   /* حبر واحد لكل ندرة؛ الذهب لإطار S/SS فقط */
    /* ---- 0) تعريفات ---- */
    P.push('<defs><linearGradient id="cbkFoilG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5a1a"/><stop offset=".3" stop-color="#f3d987"/><stop offset=".48" stop-color="#b48528"/><stop offset=".68" stop-color="#fff0bd"/><stop offset="1" stop-color="#946c22"/></linearGradient>' +
      '<radialGradient id="cbkFoxG"><stop offset="0" stop-color="#8a5a2b" stop-opacity=".55"/><stop offset=".6" stop-color="#8a5a2b" stop-opacity=".18"/><stop offset="1" stop-color="#8a5a2b" stop-opacity="0"/></radialGradient></defs>');
    /* ---- 1) هامش الكرتون + تعتيق: بقع «فوكسينغ» قليلة بمواضع ثابتة من الاسم ---- */
    for(let i = 0, n = 4 + H0 % 4; i < n; i++){ const r = .6 + rnd() * 1.8; P.push('<circle class="p-fox" cx="' + f(9 + rnd() * 82) + '" cy="' + f(10 + rnd() * 105) + '" r="' + f(r) + '" fill="url(#cbkFoxG)"/>'); }
    /* ---- 2) خلفية منقّطة محفورة (stipple) داخل الإطار + نقش الندرة الخافت ---- */
    const IN = { x:8, y:8, w:84, h:109 };
    const B = [];
    if(tone === 'c'){ for(let y = IN.y + 1.2; y < IN.y + IN.h; y += 1.5) B.push('M' + IN.x + ' ' + f(y) + 'H' + (IN.x + IN.w)); }
    else if(tone === 'b'){ const wl = 9 + (H0 % 4); for(let y = IN.y + 2, r = 0; y < IN.y + IN.h; y += 3.4, r++){ const pts = []; for(let x = IN.x; x <= IN.x + IN.w; x += 1.4) pts.push([x, y + Math.sin((x / wl + r * .3) * PI * 2) * .9]); B.push(poly(pts)); } }
    else if(tone === 'a'){ for(let k = -110; k <= 200; k += 5){ B.push('M' + f(k) + ' ' + IN.y + 'L' + f(k + IN.h) + ' ' + (IN.y + IN.h)); B.push('M' + f(k) + ' ' + (IN.y + IN.h) + 'L' + f(k + IN.h) + ' ' + IN.y); } }
    else { const n = tone === 'ss' ? 64 : 48; for(let i = 0; i < n; i++){ const a = i / n * PI * 2; B.push('M' + f(50 + Math.cos(a) * 16) + ' ' + f(34 + Math.sin(a) * 16) + 'L' + f(50 + Math.cos(a) * 130) + ' ' + f(34 + Math.sin(a) * 130)); } }
    P.push('<clipPath id="cbkIn"><rect x="' + IN.x + '" y="' + IN.y + '" width="' + IN.w + '" height="' + IN.h + '" rx="1.6"/></clipPath><path class="p-bg" clip-path="url(#cbkIn)" d="' + B.join('') + '"/>');
    /* ---- 3) الإطار: خطّان متوازيان وشريط زخرفي متناظر بينهما ---- */
    P.push('<rect class="' + FR + ' p-fr" x="4.6" y="4.6" width="90.8" height="115.8" rx="3"/><rect class="p-ink p-fr2" x="7.4" y="7.4" width="85.2" height="110.2" rx="1.8"/>');
    const sides = [[[9.5, 6], [90.5, 6]], [[94, 9.5], [94, 115.5]], [[90.5, 119], [9.5, 119]], [[6, 115.5], [6, 9.5]]], band = [];
    if(tone === 'c'){ sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.round(L / 2.4); for(let i = 0; i <= n; i++){ const t = i / n; band.push('<circle class="p-dot" cx="' + f(a[0] + (b[0] - a[0]) * t) + '" cy="' + f(a[1] + (b[1] - a[1]) * t) + '" r=".36"/>'); } }); }
    else if(tone === 'a'){ sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.round(L / 3.2); for(let i = 0; i <= n; i++){ const t = i / n, cx = a[0] + (b[0] - a[0]) * t, cy = a[1] + (b[1] - a[1]) * t; band.push('<path class="p-dia" d="M' + f(cx) + ' ' + f(cy - .8) + 'L' + f(cx + .8) + ' ' + f(cy) + 'L' + f(cx) + ' ' + f(cy + .8) + 'L' + f(cx - .8) + ' ' + f(cy) + 'Z"/>'); } }); }
    else if(tone === 's'){ const d = []; sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L; for(let l = 0; l < L - .5; l += 1.6){ const px = a[0] + ux * l, py = a[1] + uy * l; d.push('M' + f(px - uy * .8) + ' ' + f(py + ux * .8) + 'Q' + f(px + ux * .8) + ' ' + f(py + uy * .8) + ' ' + f(px + ux * 1.3 + uy * .8) + ' ' + f(py + uy * 1.3 - ux * .8)); } }); band.push('<path class="p-foil-s p-rope" d="' + d.join('') + '"/>'); }
    else { const d = []; sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L; [0, PI].forEach(ph=>{ const pts = []; for(let l = 0; l <= L; l += .7){ const w = Math.sin(l / 2 * PI + ph) * .75; pts.push([a[0] + ux * l - uy * w, a[1] + uy * l + ux * w]); } d.push(poly(pts)); }); });
      band.push('<path class="' + (tone === 'ss' ? 'p-foil-s' : 'p-ink') + ' p-band" d="' + d.join('') + '"/>'); }
    P.push(band.join(''));
    /* ---- 4) زوايا فيكتورية موحّدة (لفة + ورقة)، أثقل مع الندرة ---- */
    const corner = '<path class="' + FR + ' p-cn2" d="M0 11V4.4Q0 0 4.4 0H11"/><path class="p-ink p-cn" d="M2.1 8.6C2.1 4.8 4.8 2.1 8.6 2.1"/>' +
      '<path class="p-ink p-cn" d="M3.2 3.2c1.7-.8 3.2.4 2.4 1.9-.7 1.3-2.5.7-2.1-.5.3-.7 1.2-.6 1.2.1"/>' + (rank >= 2 ? '<path class="' + (gold ? 'p-foil' : 'p-inkf') + '" d="M9.6 .9q1.6-.4 2.3 1-1.4.5-2.3-1zM.9 9.6q-.4 1.6 1 2.3.5-1.4-1-2.3z"/>' : '') + (rank >= 3 ? '<circle class="p-foil" cx="5.6" cy="5.6" r=".55"/>' : '');
    [[7.4, 7.4, 1, 1], [92.6, 7.4, -1, 1], [7.4, 117.6, 1, -1], [92.6, 117.6, -1, -1]].forEach(c=>P.push('<g transform="translate(' + c[0] + ' ' + c[1] + ') scale(' + c[2] + ' ' + c[3] + ')">' + corner + '</g>'));
    /* ---- 5) الترويسة: السلسلة + الرقم (متناظر حول المحور) ---- */
    P.push('<text class="p-hd" x="50" y="15.4" text-anchor="middle">' + (CBK_KIND_AR[kind] || CBK_KIND_AR.reward) + '</text>');
    P.push('<path class="p-ink p-rule" d="M15 14.2H25.5M74.5 14.2H85"/><path class="p-inkf" d="M25.5 13.5l.7.7-.7.7-.7-.7zM74.5 13.5l.7.7-.7.7-.7-.7z"/>');
    P.push('<text class="p-no" x="50" y="19.6" text-anchor="middle">رقم ' + num + ' · ' + code + '</text>');
    /* ---- 6) الرسم: ميدالية غيوشيه بحبر واحد، بقلبها الستيكر ---- */
    const MX = 50, MY = 34, k = 7 + H0 % 7, ph0 = (H0 % 360) / 180 * PI, layers = [1, 2, 2, 3, 3][rank];
    if(kind === 'pass') P.push('<path class="p-ink p-tear" d="M10 21.8H90"/>');
    for(let j = 0; j < layers; j++){ const pts = [], r0 = 10.2 - j * .4, A = 1.1 + j * .28, ph = ph0 + j * PI / k;
      for(let i = 0; i <= 150; i++){ const t = i / 150 * PI * 2, r = r0 + A * Math.cos(k * t + ph) + A * .3 * Math.cos(2 * k * t - ph); pts.push([MX + Math.cos(t) * r, MY + Math.sin(t) * r]); }
      P.push('<path class="p-ink p-gu" d="' + poly(pts) + 'Z"/>'); }
    P.push('<circle class="' + FR + ' p-ring" cx="' + MX + '" cy="' + MY + '" r="12.6"/><circle class="p-ink p-dash" cx="' + MX + '" cy="' + MY + '" r="13.6"/>');
    const KX = {
      weekly:()=>{ let d = ''; for(let i = 0; i < 7; i++){ const a = i / 7 * PI * 2 - PI / 2, x = MX + Math.cos(a) * 15.2, y = MY + Math.sin(a) * 15.2; d += 'M' + f(x) + ' ' + f(y - .7) + 'L' + f(x + .7) + ' ' + f(y) + 'L' + f(x) + ' ' + f(y + .7) + 'L' + f(x - .7) + ' ' + f(y) + 'Z'; } return '<path class="p-inkf" d="' + d + '"/>'; },
      monthly:()=>{ let d = ''; for(let i = 0; i < 30; i++){ const a = i / 30 * PI * 2 - PI / 2, r2 = i % 5 ? 15.2 : 16; d += 'M' + f(MX + Math.cos(a) * 14.4) + ' ' + f(MY + Math.sin(a) * 14.4) + 'L' + f(MX + Math.cos(a) * r2) + ' ' + f(MY + Math.sin(a) * r2); } return '<path class="p-ink p-tick" d="' + d + '"/>'; },
      holiday:()=>{ let d = ''; for(let i = 0; i < 16; i++){ const a = i / 16 * PI * 2 - PI / 2, w = .07; d += 'M' + f(MX + Math.cos(a - w) * 14.4) + ' ' + f(MY + Math.sin(a - w) * 14.4) + 'L' + f(MX + Math.cos(a) * (i % 2 ? 16 : 17.2)) + ' ' + f(MY + Math.sin(a) * (i % 2 ? 16 : 17.2)) + 'L' + f(MX + Math.cos(a + w) * 14.4) + ' ' + f(MY + Math.sin(a + w) * 14.4) + 'Z'; } return '<path class="p-inkf p-soft" d="' + d + '"/>'; },
      pouch:()=>{ let d = ''; for(let i = 0; i < 60; i++){ const a = i / 60 * PI * 2; d += 'M' + f(MX + Math.cos(a) * 14.3) + ' ' + f(MY + Math.sin(a) * 14.3) + 'L' + f(MX + Math.cos(a) * 15.1) + ' ' + f(MY + Math.sin(a) * 15.1); } return '<path class="p-ink p-tick" d="' + d + '"/>'; },
      cosmetic:()=>[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(s=>{ const x = MX + s[0] * 12.6, y = MY + s[1] * 11.4; return '<path class="p-inkf p-soft" d="M' + f(x) + ' ' + f(y - 1.5) + 'Q' + f(x + .2) + ' ' + f(y - .2) + ' ' + f(x + 1.5) + ' ' + f(y) + 'Q' + f(x + .2) + ' ' + f(y + .2) + ' ' + f(x) + ' ' + f(y + 1.5) + 'Q' + f(x - .2) + ' ' + f(y + .2) + ' ' + f(x - 1.5) + ' ' + f(y) + 'Q' + f(x - .2) + ' ' + f(y - .2) + ' ' + f(x) + ' ' + f(y - 1.5) + 'Z"/>'; }).join('')
    };
    if(KX[kind]) P.push(KX[kind]());
    P.push('<circle class="p-disc" cx="' + MX + '" cy="' + MY + '" r="8.2"/><circle class="p-ink p-thin" cx="' + MX + '" cy="' + MY + '" r="7.5"/>');
    let url = ''; try{ if(stk && typeof CodisStickers !== 'undefined') url = CodisStickers.url(stk) || ''; }catch(e){}
    if(url){ const cid = 'cbkC' + (H0 % 100000); P.push('<clipPath id="' + cid + '"><circle cx="' + MX + '" cy="' + MY + '" r="7.2"/></clipPath><image class="p-stk" href="' + String(url).replace(/"/g, '&quot;') + '" x="' + (MX - 7) + '" y="' + (MY - 7) + '" width="14" height="14" preserveAspectRatio="xMidYMid meet" clip-path="url(#' + cid + ')"/>'); }
    else { const G = typeof codisBackOrnament === 'function' ? (codisBackOrnament(tone, kind, seed).match(/<g class="o-glyph">([\s\S]*?)<\/g><\/g>/) || [])[1] : ''; if(G) P.push('<g class="p-glyph" transform="translate(50 34) scale(.62) translate(-50 -32)">' + G + '</g>'); }
    /* ---- 7) «صادرة عن» أسفل الإطار (مكان اسم المُصدِر في البطاقات العتيقة) ---- */
    P.push('<path class="p-ink p-rule" d="M24 113.9H38M62 113.9H76"/><text class="p-imp" x="50" y="114.8" text-anchor="middle">صادرة عن كوديس</text>');
    return '<svg class="cbk-orn cbk-orn-p" viewBox="0 0 100 125" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' + P.join('') + '</svg>';
  }catch(e){ try{ return codisBackOrnament(tone, kind, seed); }catch(x){ return ''; } }
}
function codisCardBackHtml(title, rows, o){
  o = o || {};
  const tone = econTones().indexOf(o.tone) !== -1 ? o.tone : 'c', kind = o.kind || 'reward', paper = true;   /* المظهران يستعملان نفس التركيبة؛ الألوان من CSS حسب data-theme */
  let stk = ''; try{ const l = typeof codisStickerList === 'function' ? codisStickerList(o.sticker) : []; if(l && l[0] && CodisStickers.url(l[0])) stk = l[0]; }catch(e){}
  return '<div class="cbk rwc-' + tone + (paper ? ' is-paper' : '') + '" data-tone="' + tone + '" data-kind="' + escapeHtml(kind) + '" data-seed="' + escapeHtml(String(title || '')) + '"' + (stk ? ' data-stk="' + escapeHtml(stk) + '"' : '') + '>' +
    (paper ? codisPaperBackSvg(tone, kind, title, stk) : codisBackOrnament(tone, kind, title)) +
    '<div class="cbk-in"><b class="cbk-t" dir="auto">' + escapeHtml(title) + '</b>' +
    '<dl class="cbk-rows">' + rows.filter(r=>r && r[1] !== '' && r[1] !== null && r[1] !== undefined).map(r=>'<div><dt>' + escapeHtml(r[0]) + '</dt><dd' + (r[2] ? ' ' + r[2] : '') + '>' + (r[3] ? r[1] : escapeHtml(String(r[1]))) + '</dd></div>').join('') + '</dl>' +
    (o.note ? '<p class="cbk-note" dir="auto">' + escapeHtml(o.note) + '</p>' : '') + '</div></div>';
}
