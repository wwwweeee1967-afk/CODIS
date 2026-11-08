/* ===== CODIS-PAPER-BACK (3.24.0) — ظهر البطاقة الخاص بالمظهر الورقي =====
   • المظهر الداكن لا يتغيّر إطلاقاً: نفس codisBackOrnament ونفس الوسوم. الورقي فقط يأخذ codisPaperBackSvg + الصنف is-paper.
   • تصميم وثيقة محفورة عتيقة (ورقة نقدية × طابع بريد): ورق وحبر لكل ندرة (C سيبيا/عاجي مضلّع · B نيلي/ورق رسائل · A باذنجاني/وردي · S بنّي+رقائق ذهب/رق · SS دموي+ذهب)،
     نقش خلفية وشريط حدود لكل ندرة، ميدالية «غيوشيه» تتولّد من اسم البطاقة نفسه (عدد البتلات والطور مختلف لكل بطاقة) وفي قلبها ستيكر البطاقة إن وُجد،
     ختم بريد بزاوية وموضع ثابتين لكل بطاقة (أو ختم شمع لـS/SS)، رقم تسلسلي وطباعة دقيقة، وزخارف خاصة بالنوع (أسبوعية/شهرية/تجاوز/عطلة/كيس/مظهر/بكج).
   • حتمي (لا Math.random) وبلا فلاتر SVG. تبديل المظهر وقت التشغيل يعيد رسم الظهور المبنية (MutationObserver على data-theme). */
function codisCbkPaper(){ try{ return document.documentElement.getAttribute('data-theme') !== 'dark'; }catch(e){ return true; } }
const CBK_KIND_AR = { reward:'مكافأة', weekly:'أسبوعية', monthly:'شهرية', pass:'بطاقة تجاوز', holiday:'بطاقة عطلة', pouch:'كيس فضة', cosmetic:'مظهر', box:'بكج' };
function codisPaperBackSvg(tone, kind, seed, stk){
  try{
    const f = n=>Math.round(n * 100) / 100, P = [], PI = Math.PI;
    let h = 2166136261; String(seed || '').concat('|', tone, '|', kind).split('').forEach(ch=>{ h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; });
    const H0 = h; let x0 = h || 1; const rnd = ()=>{ x0 = (Math.imul(x0, 1664525) + 1013904223) >>> 0; return x0 / 4294967296; };
    const gold = tone === 's' || tone === 'ss', rank = { c:0, b:1, a:2, s:3, ss:4 }[tone] || 0;
    const serial = String(1000 + H0 % 9000);
    const poly = pts=>'M' + pts.map(p=>f(p[0]) + ' ' + f(p[1])).join('L');
    /* ---- 0) تعريفات: رقائق الذهب + الشمع ---- */
    P.push('<defs><linearGradient id="cbkFoilG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5a1a"/><stop offset=".3" stop-color="#f3d987"/><stop offset=".48" stop-color="#b48528"/><stop offset=".68" stop-color="#fff0bd"/><stop offset="1" stop-color="#946c22"/></linearGradient>' +
      '<radialGradient id="cbkWaxG" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="#c8483b"/><stop offset=".55" stop-color="#93271f"/><stop offset="1" stop-color="#5e1410"/></radialGradient></defs>');
    /* ---- 1) نقش الخلفية (محفور، خافت) ---- */
    const B = [];
    if(tone === 'c'){ for(let y = 8; y < 118; y += 1.6) B.push('M7 ' + f(y) + 'H93'); P.push('<path class="p-bg p-laid" d="' + B.join('') + '"/>'); const C = []; for(let x = 12; x < 92; x += 13) C.push('M' + x + ' 7V118'); P.push('<path class="p-bg p-chain" d="' + C.join('') + '"/>'); }
    else if(tone === 'b'){ const wl = 8 + rnd() * 5; for(let y = 9, r = 0; y < 118; y += 3.6, r++){ const pts = []; for(let x = 7; x <= 93; x += 1.2) pts.push([x, y + Math.sin((x / wl + r * .35) * PI * 2) * 1.05]); B.push(poly(pts)); } P.push('<path class="p-bg" d="' + B.join('') + '"/>'); }
    else if(tone === 'a'){ for(let k = -120; k <= 220; k += 5.5){ B.push('M' + f(k) + ' 0L' + f(k + 125) + ' 125'); B.push('M' + f(k) + ' 125L' + f(k + 125) + ' 0'); } P.push('<path class="p-bg" d="' + B.join('') + '"/>'); }
    else { const n = tone === 'ss' ? 72 : 56; for(let i = 0; i < n; i++){ const a = i / n * PI * 2, r1 = i % 2 ? 26 : 18; B.push('M' + f(50 + Math.cos(a) * r1) + ' ' + f(28 + Math.sin(a) * r1) + 'L' + f(50 + Math.cos(a) * 140) + ' ' + f(28 + Math.sin(a) * 140)); } P.push('<path class="p-bg p-ray" d="' + B.join('') + '"/>');
      if(tone === 'ss'){ const k = 9 + H0 % 5; for(let j = 0; j < 5; j++){ const pts = [], r0 = 22 + j * 11; for(let i = 0; i <= 180; i++){ const t = i / 180 * PI * 2; const r = r0 + 1.4 * Math.cos(k * t + j * .7); pts.push([50 + Math.cos(t) * r, 28 + Math.sin(t) * r]); } P.push('<path class="p-bg p-ring" d="' + poly(pts) + 'Z"/>'); } } }
    /* ---- 2) الإطار + شريط الحدود ---- */
    P.push('<rect class="' + (gold ? 'p-foil-s' : 'p-ink') + ' p-fr" x="3.5" y="3.5" width="93" height="118" rx="4"/><rect class="p-ink p-fr2" x="6.5" y="6.5" width="87" height="112" rx="2.4"/>');
    const band = [];
    const sides = [[[7, 5], [93, 5]], [[95, 7], [95, 118]], [[93, 120], [7, 120]], [[5, 118], [5, 7]]];
    if(tone === 'c'){ sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.floor(L / 2.6); for(let i = 0; i <= n; i++){ const t = i / n; band.push('<circle class="p-dot" cx="' + f(a[0] + (b[0] - a[0]) * t) + '" cy="' + f(a[1] + (b[1] - a[1]) * t) + '" r=".42"/>'); } }); }
    else if(tone === 'b' || tone === 'ss'){ const d = []; sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L; [0, PI].forEach(ph=>{ const pts = []; for(let l = 0; l <= L; l += .8){ const w = Math.sin(l / 2.2 * PI + ph) * .9; pts.push([a[0] + ux * l - uy * w, a[1] + uy * l + ux * w]); } d.push(poly(pts)); }); });
      band.push('<path class="' + (tone === 'ss' ? 'p-foil-s' : 'p-acc') + ' p-band" d="' + d.join('') + '"/>'); }
    else if(tone === 'a'){ sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.floor(L / 3.4); for(let i = 0; i <= n; i++){ const t = i / n, cx = a[0] + (b[0] - a[0]) * t, cy = a[1] + (b[1] - a[1]) * t; band.push('<path class="p-dia" d="M' + f(cx) + ' ' + f(cy - .95) + 'L' + f(cx + .95) + ' ' + f(cy) + 'L' + f(cx) + ' ' + f(cy + .95) + 'L' + f(cx - .95) + ' ' + f(cy) + 'Z"/>'); } }); }
    else { const d = []; sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L; for(let l = 0; l < L; l += 1.7){ const px = a[0] + ux * l, py = a[1] + uy * l; d.push('M' + f(px - uy * 1) + ' ' + f(py + ux * 1) + 'Q' + f(px + ux * .9) + ' ' + f(py + uy * .9) + ' ' + f(px + ux * 1.4 + uy * 1) + ' ' + f(py + uy * 1.4 - ux * 1)); } }); band.push('<path class="p-foil-s p-rope" d="' + d.join('') + '"/>'); }
    P.push(band.join(''));
    if(tone === 'ss') sides.forEach(s=>{ const [a, b] = s, L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.floor(L / 6); for(let i = 1; i < n; i++){ const t = i / n; P.push('<circle class="p-foil" cx="' + f(a[0] + (b[0] - a[0]) * t) + '" cy="' + f(a[1] + (b[1] - a[1]) * t) + '" r=".55"/>'); } });
    /* ---- 3) زوايا (شكل لكل ندرة، تنويع من الاسم) ---- */
    const vr = H0 % 2, CN = {
      c:'<path class="p-ink p-cn" d="M0 7.5A7.5 7.5 0 0 1 7.5 0"/><circle class="p-inkf" cx="2.4" cy="2.4" r=".75"/>',
      b:'<path class="p-acc p-cn" d="M0 3.5A3.5 3.5 0 0 1 3.5 0M0 6A6 6 0 0 1 6 0M0 8.5A8.5 8.5 0 0 1 8.5 0"/>' + (vr ? '<circle class="p-inkf" cx="1.6" cy="1.6" r=".6"/>' : ''),
      a:'<path class="p-ink p-cn" d="M0 9H2.2V2.2H9M0 6H5V0M3.6 3.6H6.4V6.4H3.6Z"/>',
      s:'<path class="p-foil-s p-cn2" d="M0 12C0 4.6 4.6 0 12 0"/><path class="p-foil-s p-cn" d="M2.6 2.6c2.6-1.4 5 .6 3.6 3-1.2 2-3.8 1-3-1 .5-1.1 2-.9 1.9.2"/>' + (vr ? '<path class="p-foil" d="M10 1.4l1 1-1 1-1-1z"/>' : ''),
      ss:'<path class="p-foil-s p-cn2" d="M0 13C0 5 5 0 13 0"/><path class="p-foil-s p-cn" d="M2.4 2.4c2.8-1.6 5.6.6 4 3.2-1.3 2.2-4.2 1.1-3.3-1.1.5-1.2 2.2-1 2.1.2M8 2.2q3-2.2 5.2.6q-3 1.2-5.2-.6M2.2 8q-2.2 3 .6 5.2q1.2-3-.6-5.2"/><circle class="p-foil" cx="11" cy="11" r=".8"/>'
    };
    [[6.5, 6.5, 1, 1], [93.5, 6.5, -1, 1], [6.5, 118.5, 1, -1], [93.5, 118.5, -1, -1]].forEach(c=>P.push('<g transform="translate(' + c[0] + ' ' + c[1] + ') scale(' + c[2] + ' ' + c[3] + ')">' + CN[tone] + '</g>'));
    /* ---- 4) الترويسة: نوع البطاقة + رقم تسلسلي + رمز الندرة ---- */
    const code = (typeof CBK_CODE !== 'undefined' && CBK_CODE[tone]) || 'C';
    P.push('<path class="p-acc p-rule" d="M21 12.2H35M65 12.2H79"/><path class="p-inkf" d="M35 11.4l.8.8-.8.8-.8-.8zM65 11.4l.8.8-.8.8-.8-.8z"/>');
    P.push('<text class="p-hd" x="50" y="13.2" text-anchor="middle">' + (CBK_KIND_AR[kind] || CBK_KIND_AR.reward) + '</text>');
    P.push('<text class="p-sn" x="10" y="13.1" text-anchor="start" direction="ltr">№ ' + serial + '</text>');
    P.push('<path class="' + (gold ? 'p-foil-s' : 'p-ink') + ' p-lz" d="M86.2 9.4l3.3 3.1-3.3 3.1-3.3-3.1z"/><text class="p-code" x="86.2" y="13.55" text-anchor="middle" direction="ltr">' + code + '</text>');
    if(kind === 'pass'){ P.push('<path class="p-acc p-tear" d="M8 18.6H92"/><circle class="p-notch" cx="3.5" cy="18.6" r="2.4"/><circle class="p-notch" cx="96.5" cy="18.6" r="2.4"/>'); }
    /* ---- 5) الميدالية: غيوشيه من الاسم ---- */
    const MX = 50, MY = 33, k = 7 + H0 % 7, ph0 = (H0 % 360) / 180 * PI, layers = [1, 2, 2, 3, 4][rank];
    for(let j = 0; j < layers; j++){ const pts = [], r0 = 13.6 - j * .45, A = 1.6 + j * .38, ph = ph0 + j * PI / k;
      for(let i = 0; i <= 160; i++){ const t = i / 160 * PI * 2, r = r0 + A * Math.cos(k * t + ph) + A * .3 * Math.cos(2 * k * t - ph); pts.push([MX + Math.cos(t) * r, MY + Math.sin(t) * r]); }
      P.push('<path class="' + (gold ? 'p-foil-s' : 'p-acc') + ' p-gu" d="' + poly(pts) + 'Z"/>'); }
    P.push('<circle class="' + (gold ? 'p-foil-s' : 'p-ink') + ' p-ring" cx="' + MX + '" cy="' + MY + '" r="16.6"/>');
    if(rank >= 2) P.push('<circle class="p-ink p-dash" cx="' + MX + '" cy="' + MY + '" r="17.9"/>');
    const KX = {
      weekly:()=>{ let d = ''; for(let i = 0; i < 7; i++){ const a = i / 7 * PI * 2 - PI / 2, x = MX + Math.cos(a) * 19.4, y = MY + Math.sin(a) * 19.4; d += '<path class="p-inkf" d="M' + f(x) + ' ' + f(y - .9) + 'L' + f(x + .9) + ' ' + f(y) + 'L' + f(x) + ' ' + f(y + .9) + 'L' + f(x - .9) + ' ' + f(y) + 'Z"/>'; } return d; },
      monthly:()=>{ let d = ''; for(let i = 0; i < 30; i++){ const a = i / 30 * PI * 2, r1 = 18.4, r2 = i % 5 ? 19.4 : 20.3; d += 'M' + f(MX + Math.cos(a) * r1) + ' ' + f(MY + Math.sin(a) * r1) + 'L' + f(MX + Math.cos(a) * r2) + ' ' + f(MY + Math.sin(a) * r2); } return '<path class="p-ink p-tick" d="' + d + '"/>'; },
      holiday:()=>{ let d = ''; for(let i = 0; i < 12; i++){ const a = i / 12 * PI * 2, a1 = a - .09, a2 = a + .09; d += 'M' + f(MX + Math.cos(a1) * 18.4) + ' ' + f(MY + Math.sin(a1) * 18.4) + 'L' + f(MX + Math.cos(a) * 21.6) + ' ' + f(MY + Math.sin(a) * 21.6) + 'L' + f(MX + Math.cos(a2) * 18.4) + ' ' + f(MY + Math.sin(a2) * 18.4) + 'Z'; } return '<path class="' + (gold ? 'p-foil' : 'p-accf') + '" d="' + d + '"/>'; },
      pouch:()=>{ let d = ''; for(let i = 0; i < 56; i++){ const a = i / 56 * PI * 2; d += 'M' + f(MX + Math.cos(a) * 18.2) + ' ' + f(MY + Math.sin(a) * 18.2) + 'L' + f(MX + Math.cos(a) * 19.2) + ' ' + f(MY + Math.sin(a) * 19.2); } return '<path class="p-ink p-tick" d="' + d + '"/>'; },
      cosmetic:()=>[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(s=>{ const x = MX + s[0] * 16.4, y = MY + s[1] * 15.2; return '<path class="' + (gold ? 'p-foil' : 'p-accf') + '" d="M' + f(x) + ' ' + f(y - 1.8) + 'Q' + f(x + .25) + ' ' + f(y - .25) + ' ' + f(x + 1.8) + ' ' + f(y) + 'Q' + f(x + .25) + ' ' + f(y + .25) + ' ' + f(x) + ' ' + f(y + 1.8) + 'Q' + f(x - .25) + ' ' + f(y + .25) + ' ' + f(x - 1.8) + ' ' + f(y) + 'Q' + f(x - .25) + ' ' + f(y - .25) + ' ' + f(x) + ' ' + f(y - 1.8) + 'Z"/>'; }).join('')
    };
    if(KX[kind]) P.push(KX[kind]());
    P.push('<circle class="p-disc" cx="' + MX + '" cy="' + MY + '" r="10.4"/><circle class="p-ink p-thin" cx="' + MX + '" cy="' + MY + '" r="9.5"/>');
    let url = ''; try{ if(stk && typeof CodisStickers !== 'undefined') url = CodisStickers.url(stk) || ''; }catch(e){}
    if(url){ const cid = 'cbkC' + (H0 % 100000); P.push('<clipPath id="' + cid + '"><circle cx="' + MX + '" cy="' + MY + '" r="9.2"/></clipPath><image href="' + String(url).replace(/"/g, '&quot;') + '" x="' + (MX - 8.8) + '" y="' + (MY - 8.8) + '" width="17.6" height="17.6" preserveAspectRatio="xMidYMid meet" clip-path="url(#' + cid + ')"/>'); }
    else { const G = typeof codisBackOrnament === 'function' ? (codisBackOrnament(tone, kind, seed).match(/<g class="o-glyph">([\s\S]*?)<\/g><\/g>/) || [])[1] : ''; if(G) P.push('<g class="p-glyph" transform="translate(50 33) scale(.78) translate(-50 -32)">' + G + '</g>'); }
    /* ---- 6) ختم بريد مُلغٍ (C/B/A) أو ختم شمع (S/SS) — زاوية وموضع ثابتان لكل بطاقة ---- */
    if(!gold){
      const px = f(73.5 + rnd() * 4), py = f(22 + rnd() * 5), rot = f(-24 + rnd() * 30), waves = [];
      for(let j = -1; j <= 1; j++){ const pts = []; for(let x = -24; x <= -6.2; x += .8) pts.push([x, j * 2.3 + Math.sin(x / 1.9) * .55]); waves.push(poly(pts)); }
      P.push('<g class="p-pm" transform="translate(' + px + ' ' + py + ') rotate(' + rot + ')"><circle class="p-pmr" r="5.9"/><circle class="p-pmr p-thin" r="4.5"/><path class="p-pmr" d="' + waves.join('') + '"/>' +
        '<text class="p-pmt" y="1.1" text-anchor="middle" direction="ltr">' + code + '·' + serial.slice(-2) + '</text></g>');
    } else {
      const sx = 64.6, sy = 46.2, pts = []; for(let i = 0; i < 18; i++){ const a = i / 18 * PI * 2, r = 6.3 * (1 + .07 * Math.sin(i * 2.3 + (H0 % 7))); pts.push([sx + Math.cos(a) * r, sy + Math.sin(a) * r]); }
      if(tone === 'ss') P.push('<path class="p-foil" d="M61.6 49.6L58.4 58 60.8 56.7 62.1 59.3 64.4 50.6ZM67.6 49.6L70.8 58 68.4 56.7 67.1 59.3 64.8 50.6Z"/>');
      P.push('<path class="p-wax" d="' + poly(pts) + 'Z"/><circle class="p-waxr" cx="' + sx + '" cy="' + sy + '" r="4.4"/><path class="p-waxs" d="M' + sx + ' ' + (sy - 2.9) + 'l.85 1.8 1.95.25-1.45 1.35.36 1.95-1.71-.98-1.71.98.36-1.95-1.45-1.35 1.95-.25z"/>');
    }
    /* ---- 7) طباعة دقيقة أسفل الإطار ---- */
    P.push('<text class="p-micro" x="50" y="117.3" text-anchor="middle" direction="ltr">CODIS · ATELIER · № ' + serial + ' · ' + code + '</text>');
    return '<svg class="cbk-orn cbk-orn-p" viewBox="0 0 100 125" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' + P.join('') + '</svg>';
  }catch(e){ try{ return codisBackOrnament(tone, kind, seed); }catch(x){ return ''; } }
}
function codisCardBackHtml(title, rows, o){
  o = o || {};
  const tone = econTones().indexOf(o.tone) !== -1 ? o.tone : 'c', kind = o.kind || 'reward', paper = codisCbkPaper();
  let stk = ''; try{ const l = typeof codisStickerList === 'function' ? codisStickerList(o.sticker) : []; if(l && l[0] && CodisStickers.url(l[0])) stk = l[0]; }catch(e){}
  return '<div class="cbk rwc-' + tone + (paper ? ' is-paper' : '') + '" data-tone="' + tone + '" data-kind="' + escapeHtml(kind) + '" data-seed="' + escapeHtml(String(title || '')) + '"' + (stk ? ' data-stk="' + escapeHtml(stk) + '"' : '') + '>' +
    (paper ? codisPaperBackSvg(tone, kind, title, stk) : codisBackOrnament(tone, kind, title)) +
    '<div class="cbk-in"><b class="cbk-t" dir="auto">' + escapeHtml(title) + '</b>' +
    '<dl class="cbk-rows">' + rows.filter(r=>r && r[1] !== '' && r[1] !== null && r[1] !== undefined).map(r=>'<div><dt>' + escapeHtml(r[0]) + '</dt><dd' + (r[2] ? ' ' + r[2] : '') + '>' + (r[3] ? r[1] : escapeHtml(String(r[1]))) + '</dd></div>').join('') + '</dl>' +
    (o.note ? '<p class="cbk-note" dir="auto">' + escapeHtml(o.note) + '</p>' : '') + '</div></div>';
}
/* تبديل المظهر وقت التشغيل: الظهور المبنية تُعاد رسم زخرفتها لتطابق المظهر الجديد (القوالب الكسولة تُبنى بالمظهر الحالي عند القلب) */
(function(){
  try{
    new MutationObserver(()=>{ const paper = codisCbkPaper();
      document.querySelectorAll('.cbk').forEach(el=>{ try{ if(el.classList.contains('is-paper') === paper) return; const svg = el.querySelector('.cbk-orn'), t = el.dataset.tone || 'c', k = el.dataset.kind || 'reward', s = el.dataset.seed || '', st = el.dataset.stk || '';
        if(svg) svg.outerHTML = paper ? codisPaperBackSvg(t, k, s, st) : codisBackOrnament(t, k, s); el.classList.toggle('is-paper', paper); }catch(e){} }); })
      .observe(document.documentElement, { attributes:true, attributeFilter:['data-theme'] });
  }catch(e){}
})();
