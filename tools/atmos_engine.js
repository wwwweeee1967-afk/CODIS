/* ===== CODIS-STICKER-ATMOS — «جو الستيكر»: طبقة زخرفة إضافية على بطاقة المكافأة حين يكون لها ستيكر.
   • الستيكر نفسه (.rwc-stk) لا يُمسّ: نفس الصورة/المقاس/الموضع/الميل. هذه طبقة مستقلة تحته (وتحت نصوص البطاقة).
   • مصدر واحد: تُرسم داخل codisStickerLayerHtml نفسها ⇒ تتبع الستيكر في كل مكان (المعاينة، النتيجة، المتجر، بحوزتك، البكج، القلب…)
     ومن stickerId المحفوظ مع كل بطاقة (اللقطة القديمة تبقى كما هي).
   • حتمية: التخطيط من (المعرّف + القالب) ببذرة ثابتة — نفس البطاقة تبدو نفسها في كل مكان وكل إعادة رسم. لا Math.random.
   • خفيفة: صورة SVG واحدة (data URI) مخزّنة لكل (ستيكر × قالب) + عنصر «باليد» اختياري ⇒ 1–2 عقدة DOM فقط، بلا مؤقّتات ولا canvas.
   • الألوان من رسم الستيكر نفسه (CODIS_STICKER_ATMOS، تُحسب وقت البناء: tools/sticker_atmos.py) والعناصر من وصفته (stickers_meta.ATMOS).
   • مواضع آمنة لكل قالب بعد فحص الرسم الفعلي: لا وجه ولا لوحة اسم/سعر ولا شارة ندرة ولا الستيكر. ما لا يتسع يُحذف بدل الحشر. ===== */
const CodisAtmos = (function(){
  const cache = new Map();
  function h32(s){ let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(seed){ let a = seed | 0; return ()=>{ a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const rgb = h=>[parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  function mix(a, b, t){ const x = rgb(a), y = rgb(b); return '#' + x.map((v, i)=>Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join(''); }
  const f = n=>Math.round(n * 100) / 100;

  /* ---- مكتبة العناصر: كل عنصر مرسوم بوحدات ±5 (يتحجّم لاحقاً)، بخط حبر رفيع ولمعة — نفس روح رسم الستيكرات (حبر + ظل) لا أيقونات مسطحة.
     c: الألوان { p أساسي, s ثانوي, a لمسة, hi إضاءة, sh ظل, g توهّج, k حبر, n(لون طبيعي) ⇒ يميل للوحة الستيكر } */
  const S = (k, w)=>' stroke="' + k + '" stroke-width="' + (w || .5) + '" stroke-linejoin="round" stroke-linecap="round"';
  const L = (d, col, w, o, x)=>'<path d="' + d + '" fill="none" stroke="' + col + '" stroke-width="' + (w || .6) + '" stroke-linecap="round" stroke-linejoin="round"' + (o ? ' opacity="' + o + '"' : '') + (x || '') + '/>';
  const P = (d, fill, c, w, extra)=>'<path d="' + d + '" fill="' + fill + '"' + S(c.k, w) + (extra || '') + '/>';
  const C = (x, y, r, fill, c, w)=>'<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + fill + '"' + (c ? S(c.k, w) : '') + '/>';
  const E = (x, y, rx, ry, fill, c, rot, w)=>'<ellipse cx="' + x + '" cy="' + y + '" rx="' + rx + '" ry="' + ry + '" fill="' + fill + '"' + (c ? S(c.k, w) : '') + (rot ? ' transform="rotate(' + rot + ' ' + x + ' ' + y + ')"' : '') + '/>';
  const shine = (d, c, o)=>L(d, c.hi, .55, o || .85);
  const leafD = 'M-4.4 2.6C-3.2-1.8.2-4.2 4.4-3.8 3.6.4.6 3.2-4.4 2.6Z';
  const dropD = 'M0-4.6C1.6-1.9 3.2-.1 3.2 1.6A3.2 3.2 0 0 1-3.2 1.6C-3.2-.1-1.6-1.9 0-4.6Z';
  const starD = (o, i, n)=>{ let d = ''; for(let j = 0; j < n * 2; j++){ const r = j % 2 ? i : o, a = Math.PI * j / n - Math.PI / 2; d += (j ? 'L' : 'M') + f(Math.cos(a) * r) + ' ' + f(Math.sin(a) * r); } return d + 'Z'; };
  const sparkD = 'M0-4.8C.5-1.3 1.3-.5 4.8 0 1.3.5.5 1.3 0 4.8-.5 1.3-1.3.5-4.8 0-1.3-.5-.5-1.3 0-4.8Z';
  const M = {
    crumb:c=>P('M-2.4-1.3L.4-2.4 2.5-.6 1.7 1.9-1.2 2.3-2.7.4Z', c.p, c, .45) + shine('M-1.2-1.2L.5-1.7', c),
    falafel:c=>C(0, 0, 4, c.p, c, .55) + C(-1.4, 1.2, .55, c.sh) + C(1.5, -.4, .5, c.sh) + C(.3, 2.2, .45, c.sh) + C(-.6, -1.5, .4, c.sh) + E(1.6, 1.8, .55, .9, '#f4e4bf', c, 30, .3) + E(-2, -.4, .5, .85, '#f4e4bf', c, -20, .3) + shine('M-2.6-1.6A3 3 0 0 1 .2-2.9', c),
    herb:c=>P(leafD, c.n('#5c9a3c'), c, .5) + L('M-3.6 2.1C-1 .2 1.4-1.6 3.6-3.1', '#e8f4c8', .4, .7),
    basil:c=>P('M-4 3C-4-1.5-.6-4.2 4-4 4 .5.8 3.6-4 3Z', c.n('#3f8f3a'), c, .5) + L('M-3.4 2.5L3.2-3.3', '#d8f0b8', .4, .7),
    lettuce:c=>P('M-4.4 1.8C-3.6-1 -2-2.6-.4-2.2.4-3.6 2.4-3.4 3-2 4.4-1.6 4.8.6 3.8 1.8 2.6 3.2-2.8 3.4-4.4 1.8Z', c.n('#8cc65a'), c, .5) + L('M-3.2 1.6C-1 .6 1 .4 3.2.8', '#e6f6c4', .4, .7),
    vineleaf:c=>P('M0-4.6C1.6-3 4.6-2.6 4.2.2 3.4 2.4 1.4 2.6 0 4.6-1.4 2.6-3.4 2.4-4.2.2-4.6-2.6-1.6-3 0-4.6Z', c.n('#4d7a34'), c, .5) + L('M0 4.4V-3.6M0 0L2.6-1.8M0 1.6L-2.6-.2', '#cfe3a8', .35, .7),
    tealeaf:c=>P('M-4.2 2.2C-2.4-1.8 1.4-3.6 4.2-3.4 3.2.4-.4 2.8-4.2 2.2Z', c.n('#4f7a3a'), c, .45) + L('M-3.4 1.8L3.4-2.9', '#cfe3a8', .35, .7),
    mint:c=>P('M0-4.6C2.8-3.6 4.2-.8 3.4 1.8 2.4 3.8 0 4.6 0 4.6S-2.4 3.8-3.4 1.8C-4.2-.8-2.8-3.6 0-4.6Z', c.n('#46b85a'), c, .5) + L('M0 4.2V-3.8M0 0L2-1.6M0 2L-2 .4', '#d8f8d0', .35, .75),
    leaf:c=>P(leafD, c.n('#6aa046'), c, .5) + L('M-3.6 2.1C-1 .2 1.4-1.6 3.6-3.1', c.hi, .4, .6),
    palm:c=>L('M-4 4C-1.6 1-.2-1 3.6-4.4', c.n('#4f8a3a'), .7) + P('M-3 2.4L-4.6.4M-1.6.8L-3.4-1.4M-.2-.6L-1.6-3M1.4-2L.6-4.4M-2.4 3.4L-.4 4.2M-1 1.8L1.2 2.6M.4.2L2.8.8M1.8-1.4L4.2-1', 'none', { k:c.n('#5ea64a') }, .7),
    pickle:c=>E(0, 0, 4.2, 2.8, c.n('#7aa63c'), c, 0, .5) + E(0, 0, 2.8, 1.6, c.n('#c4dc8a')) + C(-1, 0, .35, c.n('#7aa63c')) + C(.4, .4, .35, c.n('#7aa63c')) + C(1.2, -.4, .35, c.n('#7aa63c')),
    tomato:c=>C(0, 0, 3.8, c.n('#d8432f'), c, .5) + C(0, 0, 2.7, c.n('#ef7a5c')) + E(-1.1, -.3, .55, .9, '#fbe0a8', null, 30) + E(1.1, .4, .55, .9, '#fbe0a8', null, 30) + E(0, 1.4, .5, .8, '#fbe0a8') + shine('M-2.4-2.2A3 3 0 0 1 0-3.2', c),
    pepperoni:c=>C(0, 0, 4, c.n('#b8321f'), c, .5) + C(-1.4, -1, .7, c.n('#7e1d12')) + C(1.4, .4, .6, c.n('#7e1d12')) + C(-.3, 1.8, .55, c.n('#7e1d12')) + shine('M-2.8-2.2A3.4 3.4 0 0 1 0-3.4', c),
    cheese:c=>P('M-4-2.6H4V-.6C4 .6 3 .8 2.6 0 2.2 2.6.6 2.8.4.6-.2 3.4-2 3.8-2.2.6-2.6 1.6-4 1.4-4 0Z', c.n('#f3c443'), c, .5) + shine('M-3-1.8H1.6', c),
    garlic:c=>P(dropD, c.n('#f5ecd5'), c, .5) + shine('M-1.6 1.2A1.8 1.8 0 0 1-.6-1.2', c),
    ketchup:c=>P(dropD, c.n('#c8301c'), c, .5) + L('M-1.6 1.4A1.8 1.8 0 0 1-.7-1.1', '#ffd4c4', .5, .8),
    mustard:c=>L('M-4.4-1.4L-2.6 1.4-.8-1.4 1 1.4 2.8-1.4 4.4 1', c.k, 1.9) + L('M-4.4-1.4L-2.6 1.4-.8-1.4 1 1.4 2.8-1.4 4.4 1', c.n('#efc22a'), 1.1),
    syrup:c=>P(dropD, c.n('#c9801c'), c, .5) + L('M-1.6 1.4A1.8 1.8 0 0 1-.7-1.1', '#ffe6a8', .5, .85),
    drip:c=>P('M-3.6-3.4H3.6V-1.6C3.6.2 2.6.4 2.2-.6 2 2.8.2 3-.1.1-.5 3.6-2.6 3.8-2.7-.3-3.2.6-3.6.2-3.6-1.4Z', c.s, c, .5) + shine('M-2.6-2.6H1.4', c),
    glaze:c=>P(dropD, c.n('#f08cb0'), c, .5) + L('M-1.6 1.4A1.8 1.8 0 0 1-.7-1.1', '#ffe2ee', .5, .85),
    drop:c=>P(dropD, c.a, c, .5) + L('M-1.6 1.4A1.8 1.8 0 0 1-.7-1.1', c.hi, .5, .85),
    chocdrip:c=>P('M-3.6-3.4H3.6V-1.6C3.6.2 2.6.4 2.2-.6 2 2.8.2 3-.1.1-.5 3.6-2.6 3.8-2.7-.3-3.2.6-3.6.2-3.6-1.4Z', c.n('#4a2414'), c, .5) + shine('M-2.6-2.6H1.4', c, .5),
    sesame:c=>E(0, 0, 1.4, 2.4, '#f3e1b0', c, 25, .4),
    salt:c=>P('M-2.6-1.6h1.4v1.4h-1.4zM.6-2.4h1.2v1.2H.6zM-.4.8h1.5v1.5H-.4zM2 .6h1v1H2z', '#fbf8f0', c, .3),
    spice:c=>C(-1.6, -.6, 1, c.n('#c63b1c'), c, .35) + C(1.2, -1.4, .8, c.n('#e0742a'), c, .35) + C(.6, 1.4, .9, c.n('#a8321a'), c, .35),
    fry:c=>P('M-1.1-4.4H1.1V4.4H-1.1Z', c.n('#f2c04c'), c, .5, ' transform="rotate(18)"') + L('M-.4-3.6V3', '#fff0b8', .4, .8),
    crunch:c=>P('M-3.8-.6L-2.2-2.8-.4-2 1-3.6 2.8-2.2 3.8.2 2.6 2.6.2 3.4-2.2 2.6-3.2 1.4Z', c.p, c, .5) + P('M-2-1.2L-.6-.4.6-1.8 1.8-.2.4 1.2-1.4.6Z', c.hi, c, .3, ' opacity=".7"'),
    noodle:c=>L('M-4.4 1.6C-3 -2.4-1.6 3.6 0-.4 1.6-4 2.8 2.4 4.4-1.6', c.k, 1.7) + L('M-4.4 1.6C-3 -2.4-1.6 3.6 0-.4 1.6-4 2.8 2.4 4.4-1.6', c.n('#f3d98c'), 1),
    scallion:c=>'<circle r="2.4" fill="#e7f4c4"' + S(c.k, .45) + '/>' + '<circle r="1.4" fill="none" stroke="' + c.n('#5ea64a') + '" stroke-width=".8"/>',
    pastry:c=>P('M0-4L4 3.2H-4Z', c.p, c, .55) + L('M0-4L-.6 3.2', c.sh, .45, .7) + shine('M-.6-2.4L-2.6 1.6', c),
    croquette:c=>P('M-4.4 0C-2.6-3.2 2.6-3.2 4.4 0 2.6 3.2-2.6 3.2-4.4 0Z', c.p, c, .55) + C(-1, -.4, .4, c.sh) + C(1, .6, .4, c.sh) + shine('M-2.6-1.4C-1-2.4 1-2.4 2.2-1.6', c),
    meatcube:c=>'<rect x="-3.2" y="-3.2" width="6.4" height="6.4" rx="1.6" fill="' + c.p + '"' + S(c.k, .55) + '/>' + L('M-2.4-1.6L-.8-2.4M.6 2.2L2.4 1.2M-2 1.6L-.6.8', c.sh, .6, .9) + shine('M-2.2-2.2H.8', c),
    onion:c=>E(0, 0, 4, 3.2, 'none', c, 0, 1.8) + E(0, 0, 4, 3.2, 'none', { k:'#f3ead2' }, 0, 1) ,
    ember:c=>C(0, 0, 3.6, c.n('#ff9a3a'), null) + '<circle r="3.6" fill="' + c.n('#ffb24a') + '" opacity=".35"/>' + C(0, 0, 1.9, c.n('#ffd36a')) + C(0, 0, .8, '#fff4c8'),
    smoke:c=>L('M-1 4.4C-3.4 2.2 1.6 .6-.6-1.6-2-3 .6-4 1.6-4.6', c.hi, .9, .55) + L('M1.6 4C.2 2.6 3 1.2 1.6-.4', c.hi, .7, .4),
    steam:c=>L('M-1.6 4.4C-3.6 2 0 .6-1.8-1.8-2.8-3.2-1.6-4.2-.8-4.8', c.k, 1.4, .25) + L('M-1.6 4.4C-3.6 2 0 .6-1.8-1.8-2.8-3.2-1.6-4.2-.8-4.8', c.hi, .75, .9) + L('M1.8 4C.4 2.2 3.2 1 1.8-.8', c.hi, .6, .7),
    lemon:c=>C(0, 0, 4, c.n('#f6d23a'), c, .5) + C(0, 0, 3.1, '#fff4b8') + P('M0 0L0-3M0 0L2.6-1.5M0 0L2.6 1.5M0 0L0 3M0 0L-2.6 1.5M0 0L-2.6-1.5', 'none', { k:c.n('#f6d23a') }, .5),
    lime:c=>C(0, 0, 4, c.n('#6fb83a'), c, .5) + C(0, 0, 3.1, '#e2f4a8') + P('M0 0L0-3M0 0L2.6-1.5M0 0L2.6 1.5M0 0L0 3M0 0L-2.6 1.5M0 0L-2.6-1.5', 'none', { k:c.n('#6fb83a') }, .5),
    orange:c=>C(0, 0, 4, c.n('#f08a1c'), c, .5) + C(0, 0, 3.1, '#ffd08a') + P('M0 0L0-3M0 0L2.6-1.5M0 0L2.6 1.5M0 0L0 3M0 0L-2.6 1.5M0 0L-2.6-1.5', 'none', { k:c.n('#f08a1c') }, .5),
    rice:c=>E(-1.8, .6, .8, 1.8, '#fbf6ea', c, -30, .35) + E(1, -1, .8, 1.8, '#fbf6ea', c, 20, .35) + E(1.4, 1.8, .75, 1.7, '#fbf6ea', c, 75, .35),
    anise:c=>P(starD(4, 1.4, 8), c.n('#7a3e1c'), c, .45) + C(0, 0, .9, c.n('#c27a3a')),
    chickpea:c=>C(0, 0, 2.6, c.n('#e3c27e'), c, .45) + L('M-.6-2.2C.6-1 .6.6-.4 2', c.sh, .4, .5) + shine('M-1.6-1.2A2 2 0 0 1-.4-2', c),
    wave:c=>L('M-4.6-.6C-3.4-2.2-2.2-2.2-1-.6S1.4 1 2.6-.6 4 -1.6 4.8-.8', c.n('#5fa8d0'), .8) + L('M-3.6 1.8C-2.4.4-1.2.4 0 1.8S2.4 3.2 3.6 1.8', c.n('#8fcde8'), .65, .8),
    pistachio:c=>E(0, 0, 2.2, 3.2, c.n('#86b84a'), c, 25, .45) + L('M-.6-2.4L.6 2.4', c.n('#4f7a2a'), .45, .8, ' transform="rotate(25)"') + E(-.5, -.8, .5, 1, '#d8f0a8', null, 25),
    flake:c=>P('M-4.4 1.6C-2-2 2-2.6 4.4-1 2.4 0-1 .8-4.4 1.6Z', c.p, c, .45) + L('M-3 .6C-1-.8 1-1.2 2.8-1', c.hi, .4, .75),
    sugar:c=>P(sparkD, c.hi, c, .3),
    cherry:c=>L('M.4-1.2C.6-3 1.6-4.2 3-4.6', c.n('#5a7a2a'), .6) + C(-.4, 1.2, 2.8, c.n('#c8202a'), c, .5) + C(-1.4, .2, .7, '#ff9a9a'),
    chocshard:c=>P('M-3.8 1.4L-1.8-3.4 3.6-1.6 2.6 3.2Z', c.n('#4a2414'), c, .45) + L('M-1.8-3.4L3.6-1.6', '#a8704a', .5, .8),
    chocchip:c=>P('M0-3C1.4-1 2.8.6 2.4 2 1.8 3.4-1.8 3.4-2.4 2-2.8.6-1.4-1 0-3Z', c.n('#3e1e10'), c, .4) + shine('M-1.2 1.2L-.4-.6', c, .5),
    cocoa:c=>E(0, 0, 2.4, 3.8, c.n('#6a3a1c'), c, 30, .45) + L('M0-3.4C-.8-1 .8 1 0 3.4', c.n('#3a1c0c'), .4, .9, ' transform="rotate(30)"'),
    sprinkle:(c, r)=>{ const cols = [c.a, '#f07aa0', '#7cc6f0', '#f6d36a', '#9ad86a']; let o = ''; for(let i = 0; i < 3; i++){ const a = r() * 180, x = (i - 1) * 2.4, y = (r() - .5) * 3; o += '<rect x="-.55" y="-1.6" width="1.1" height="3.2" rx=".55" fill="' + cols[Math.floor(r() * cols.length)] + '"' + S(c.k, .3) + ' transform="translate(' + f(x) + ' ' + f(y) + ') rotate(' + f(a) + ')"/>'; } return o; },
    berry:c=>C(0, 0, 3.2, c.n('#3c4fa0'), c, .5) + P('M-.8-1.6L0-.6.8-1.6.4-.2', 'none', { k:'#1c2560' }, .5) + C(-1.2, -1.2, .6, '#b8c4f0'),
    strawberry:c=>P('M0 4.4C-3.4 2-4 -.6-3.2-2 -2.2-3.4 2.2-3.4 3.2-2 4-.6 3.4 2 0 4.4Z', c.n('#e0303c'), c, .5) + P('M-2.4-2.6L-1-3.2 0-4.4 1-3.2 2.4-2.6 1-2.2 0-2.6-1-2.2Z', c.n('#4f9a3a'), c, .35) + C(-1, 0, .3, '#fde7a0') + C(1, .4, .3, '#fde7a0') + C(0, 2, .3, '#fde7a0') + C(-1.6, 1.6, .3, '#fde7a0'),
    cream:c=>P('M-3.6 2.6C-4.2.6-2.4-.4-1.8-.4-2-2.6.4-3.6 1.2-2.2 2.6-2.6 4.2-1 3.6 1 4.2 2.2 3 3-3.6 2.6Z', '#fffaf0', c, .5) + L('M-2.2 1.4C-.6.4 1 .4 2.4 1.2', '#e8dcc6', .45),
    butter:c=>'<rect x="-2.6" y="-2" width="5.2" height="4" rx=".8" fill="#f8e07a"' + S(c.k, .45) + '/>' + shine('M-1.8-1.2H1.2', c),
    pastel:c=>C(0, 0, 2.4, c.hi, c, .4) + C(-.7, -.7, .5, '#ffffff'),
    ice:c=>'<rect x="-3" y="-3" width="6" height="6" rx="1.4" fill="#d6f0fb" fill-opacity=".85"' + S(c.k, .45) + ' transform="rotate(14)"/>' + L('M-1.8-1.4L.2-2', '#ffffff', .7, .9),
    bubble:c=>'<circle r="3" fill="' + c.hi + '" fill-opacity=".18"' + S(c.n('#bfe8f6'), .6) + '/>' + L('M-1.8-1.2A2.2 2.2 0 0 1-.4-2.2', '#ffffff', .6, .9) + '<circle cx="3.4" cy="2.6" r="1.1" fill="none"' + S(c.n('#bfe8f6'), .45) + '/>',
    pomseed:c=>P('M0-2.8L2.2-.6 1.4 2.4-1.4 2.4-2.2-.6Z', c.n('#c8203a'), c, .45) + C(-.5, -.3, .5, '#ffb0c0'),
    flower:c=>[0, 72, 144, 216, 288].map(a=>'<g transform="rotate(' + a + ')">' + E(0, -2, 1.3, 2, c.n('#f4a6b8'), c, 0, .35) + '</g>').join('') + C(0, 0, 1.1, c.n('#f6cf4a'), c, .3),
    petal:c=>P('M0 4.2C-3.4 2-3-2.4 0-4.2 3-2.4 3.4 2 0 4.2Z', c.n('#f08aa6'), c, .45, ' transform="rotate(-28)"') + L('M0 3.4C-.6 1 -.4-1.4 0-3.2', '#ffd4e0', .4, .8),
    sugarcube:c=>P('M-2.6-1.2L0-2.6 2.6-1.2 2.6 1.8 0 3.2-2.6 1.8Z', '#fbfaf4', c, .45) + L('M-2.6-1.2L0 .2 2.6-1.2M0 .2V3.2', '#ddd6c6', .4),
    cardamom:c=>P('M0-4C2 -2.4 2.2 2 0 4-2.2 2-2-2.4 0-4Z', c.n('#8fae5a'), c, .45) + L('M0-3.4V3.4', c.n('#5f7a34'), .4, .8),
    saffron:c=>L('M-2.6 3.4C-2.2.6-1.2-1.6-.2-4M.4 3.6C.8 1 1.6-1.4 2.8-3.4M-1 3.8C-.4 1.4 0-.6.2-2.4', c.n('#c8301c'), .55),
    bean:c=>E(0, 0, 2.6, 3.6, c.n('#6a3a1c'), c, 28, .45) + L('M0-3C-.9-1 .9 1 0 3', c.n('#2e160a'), .45, .9, ' transform="rotate(28)"') + E(-1, -1.2, .5, 1, '#c8946a', null, 28),
    marshmallow:c=>'<rect x="-2.4" y="-2" width="4.8" height="4" rx="1.4" fill="#fff6f8"' + S(c.k, .45) + ' transform="rotate(-12)"/>' + L('M-1.6-1.2H1', '#f2c8d4', .5),
    popcorn:c=>C(-1.4, .4, 1.8, '#fff4dc', c, .4) + C(1.2, .8, 1.7, '#fff4dc', c, .4) + C(0, -1.2, 1.9, '#fffaf0', c, .4) + C(.2, .6, .7, '#f6cf5a'),
    ticket:c=>P('M-4.4-2.4H4.4V-1A1 1 0 0 0 4.4 1V2.4H-4.4V1A1 1 0 0 0-4.4-1Z', c.a, c, .5) + L('M1.6-2V2', c.hi, .4, .8, ' stroke-dasharray=".6 .6"') + L('M-3-.8H.2M-3 .8H-.6', c.hi, .45, .8),
    film:c=>'<rect x="-4.6" y="-2.6" width="9.2" height="5.2" rx=".5" fill="#2a2a30"' + S(c.k, .45) + '/>' + [-3.4, -1.7, 0, 1.7, 3.4].map(x=>'<rect x="' + (x - .45) + '" y="-2.2" width=".9" height=".8" fill="#f2efe6"/><rect x="' + (x - .45) + '" y="1.4" width=".9" height=".8" fill="#f2efe6"/>').join('') + '<rect x="-3.4" y="-1" width="3" height="2" fill="' + c.a + '" opacity=".85"/><rect x=".4" y="-1" width="3" height="2" fill="' + c.p + '" opacity=".85"/>',
    spot:c=>'<path d="M-1-4.6L1-4.6 4.4 4.4-4.4 4.4Z" fill="' + c.g + '" opacity=".22"/>' + C(0, -4.2, 1.1, c.g),
    pin:c=>P('M0-4.4C1-4.4 1.2-3 .8-2 .6-1.4 1.8 0 1.8 1.8 1.8 3.4 1 4.4 0 4.4-1 4.4-1.8 3.4-1.8 1.8-1.8 0-.6-1.4-.8-2-1.2-3-1-4.4 0-4.4Z', '#fbf8f2', c, .45) + L('M-.8-1.6H.8M-.9-1H.9', '#d8302c', .45),
    bulb:c=>L('M-4.6-3.6C-2-1.6 2-1.6 4.6-3.6', c.k, .4, .7) + [-2.6, 0, 2.6].map((x, i)=>'<circle cx="' + x + '" cy="' + (i === 1 ? -1.1 : -2.1) + '" r="2" fill="' + c.g + '" opacity=".35"/>' + C(x, (i === 1 ? -.6 : -1.6), .9, c.g, c, .3)).join(''),
    tag:c=>P('M-4.2-1.6L-1.6-3.6H4.2V3.6H-1.6L-4.2 1.6Z', c.a, c, .5) + C(-2, 0, .7, c.hi, c, .3) + L('M.2-1H2.8M.2 1H2', c.hi, .45, .8),
    ribbon:c=>L('M-4.4 2C-2.6-2.4-.6 3.4 1 -.6 2-3 3.2-2.8 4.4-1', c.k, 1.6) + L('M-4.4 2C-2.6-2.4-.6 3.4 1 -.6 2-3 3.2-2.8 4.4-1', c.a, 1),
    confetti:(c, r)=>{ const cols = [c.a, c.g, c.s, '#f07aa0']; let o = ''; for(let i = 0; i < 3; i++){ const x = (i - 1) * 2.8 + (r() - .5), y = (r() - .5) * 4; o += '<rect x="-.9" y="-.5" width="1.8" height="1" fill="' + cols[i % cols.length] + '"' + S(c.k, .25) + ' transform="translate(' + f(x) + ' ' + f(y) + ') rotate(' + f(r() * 180) + ')"/>'; } return o + L('M1.6 3C2.6 2 3.4 3 4.2 2', c.a, .45); },
    spark:c=>P(sparkD, c.g, c, .25),
    star:c=>P(starD(4.2, 1.8, 5), c.g, c, .4) + L('M-.8-2.4L0-3.4', '#ffffff', .4, .7),
    burst:c=>[0, 45, 90, 135, 180, 225, 270, 315].map(a=>L('M0-1.6V-4.4', a % 90 ? c.a : c.g, .55).replace('/>', ' transform="rotate(' + a + ')"/>')).join('') + C(0, 0, .8, c.hi),
    moon:c=>P('M1.6-4.2A4.4 4.4 0 1 0 4.2 2.4 3.6 3.6 0 1 1 1.6-4.2Z', c.n('#f6d77a'), c, .45),
    z:c=>L('M-2.4-2.2H2.2L-2.2 2.2H2.6', c.k, 1.5) + L('M-2.4-2.2H2.2L-2.2 2.2H2.6', c.hi, .8),
    cloud:c=>P('M-4 2.4C-4.8 2.4-4.8.4-3.4.4-3.6-1.6-1.2-2.2-.4-.8.2-2.6 3.2-2.6 3.2-.4 4.8-.4 4.8 2.4 3.6 2.4Z', '#f6f8fc', c, .45),
    sun:c=>[0, 45, 90, 135, 180, 225, 270, 315].map(a=>L('M0-2.8V-4.2', c.n('#f6b93a'), .6).replace('/>', ' transform="rotate(' + a + ')"/>')).join('') + C(0, 0, 2.1, c.n('#f8cf4a'), c, .4),
    paw:c=>E(0, 1.2, 2, 1.7, c.p, c, 0, .4) + C(-2, -1.4, .8, c.p, c, .35) + C(-.7, -2.4, .8, c.p, c, .35) + C(.8, -2.4, .8, c.p, c, .35) + C(2.1, -1.4, .8, c.p, c, .35),
    ripple:c=>E(0, 0, 4.4, 1.6, 'none', c, 0, 1.2) + E(0, 0, 4.4, 1.6, 'none', { k:c.n('#8fd0e8') }, 0, .7) + E(0, 0, 2.6, .9, 'none', { k:c.n('#d6f2fb') }, 0, .6),
    button:c=>C(0, 0, 3, c.a, c, .5) + L('M-1.1-1.1L1.1 1.1M1.1-1.1L-1.1 1.1', c.hi, .6) + shine('M-2-1.4A2.4 2.4 0 0 1-.6-2.4', c),
    dpad:c=>P('M-1.2-4H1.2V-1.2H4V1.2H1.2V4H-1.2V1.2H-4V-1.2H-1.2Z', '#30323a', c, .45) + L('M-.4-3.2V-1.6', '#8a8e98', .4),
    pixel:c=>'<rect x="-3.4" y="-1" width="2.2" height="2.2" fill="' + c.a + '"' + S(c.k, .3) + '/><rect x="-1" y="-3.2" width="2.2" height="2.2" fill="' + c.g + '"' + S(c.k, .3) + '/><rect x="1.4" y=".4" width="2.2" height="2.2" fill="' + c.s + '"' + S(c.k, .3) + '/>',
    eq:c=>[[-3, 2.4], [-1, 4], [1, 3], [3, 1.8]].map(b=>'<rect x="' + (b[0] - .7) + '" y="' + (2.6 - b[1] * 1.2) + '" width="1.4" height="' + f(b[1] * 1.2) + '" rx=".4" fill="' + c.a + '"' + S(c.k, .3) + '/>').join(''),
    note:c=>P('M1.2-4.4V1.6A1.9 1.5-20 1 1-.6.2V-4.4Z', c.g, c, .4) + P('M1.2-4.4C2.6-3.8 3.6-2.8 3.4-1.2 2.8-2.2 2-2.6 1.2-2.6Z', c.g, c, .35),
    pawn:c=>C(0, -2.6, 1.4, '#f4ead6', c, .45) + P('M-1.2-1.2H1.2L1.8 2.4H2.6V3.6H-2.6V2.4H-1.8Z', '#f4ead6', c, .45),
    dice:c=>'<rect x="-3" y="-3" width="6" height="6" rx="1.3" fill="#fbf6ea"' + S(c.k, .45) + ' transform="rotate(12)"/>' + [[-1.3, -1.3], [0, 0], [1.3, 1.3]].map(p=>C(p[0], p[1], .55, '#2a1c14')).join(''),
    pip:c=>'<rect x="-1.9" y="-3.6" width="3.8" height="7.2" rx=".8" fill="#fbf6ea"' + S(c.k, .45) + '/>' + L('M-1.4 0H1.4', '#8a7a68', .35) + C(-.7, -2.2, .45, '#2a1c14') + C(.7, -1, .45, '#2a1c14') + C(0, 1.8, .45, '#2a1c14'),
    checker:c=>C(0, 0, 3, c.n('#b8322a'), c, .5) + C(0, 0, 2, 'none', { k:'#f4c2a8' }, .4),
    piece:c=>P('M-3-3H-.8C-1.4-4.6 1.4-4.6.8-3H3V-.8C4.6-1.4 4.6 1.4 3 .8V3H-3Z', c.a, c, .5) + shine('M-2.2-2.2H-1', c),
    turf:c=>L('M-4.4 2L-3.4-1.4-2.6 2-1.4-2-.4 2 .8-1.6 1.8 2 3-1 4 2', c.n('#4f9a3a'), .7),
    speed:c=>L('M-4.4-2H2.4M-3.4 0H4.4M-4.4 2H1.4', c.k, 1.3, .55) + L('M-4.4-2H2.4M-3.4 0H4.4M-4.4 2H1.4', c.a, .7),
    ball8:c=>C(0, 0, 3.2, '#1e1e24', c, .45) + C(.6, -.6, 1.3, '#fbf8f0') + C(-1.2, -1.4, .5, '#8a8a96'),
    chalk:c=>'<rect x="-1.8" y="-1.8" width="3.6" height="3.6" rx=".5" fill="' + c.n('#5f9fe0') + '"' + S(c.k, .4) + ' transform="rotate(20)"/>',
    target:c=>C(0, 0, 3.8, '#fbf6ea', c, .45) + C(0, 0, 2.5, c.n('#d8302c')) + C(0, 0, 1.2, '#fbf6ea') + C(0, 0, .5, c.n('#d8302c')),
    play:c=>C(0, 0, 3.6, c.a, c, .5) + P('M-1-1.8L1.8 0-1 1.8Z', c.hi, c, .3),
    paintdrop:c=>P(dropD, c.a, c, .5) + L('M-1.6 1.4A1.8 1.8 0 0 1-.7-1.1', '#ffffff', .5, .7),
    brush:c=>P('M-4.4 1.8C-2.4-1 1.2-2.8 4.4-2.2 2.2-1.2.4.6-.6 2.6-1.8 2.4-3.4 2.6-4.4 1.8Z', c.s, c, .4) + L('M-3 1.2C-1-.6 1.2-1.6 3-1.8', c.hi, .4, .6),
    splat:c=>C(0, 0, 1.9, c.g, c, .4) + C(2.6, -1.4, .7, c.g, c, .3) + C(-2.4, 1.8, .6, c.g, c, .3) + C(1.8, 2.2, .45, c.g),
    aperture:c=>C(0, 0, 3.6, '#2c2e36', c, .45) + C(0, 0, 2.4, c.n('#5f8fd0')) + C(-.8, -.8, .7, '#d8ecff'),
    clay:c=>L('M-3 3C-4.4 0-2.4-3.4 .4-3.4 3-3.4 4 -.6 2.4 1.2 1 2.6-1 1.6-.6.2-.2-1 1.4-.8 1.2.2', c.k, 1.5) + L('M-3 3C-4.4 0-2.4-3.4 .4-3.4 3-3.4 4 -.6 2.4 1.2 1 2.6-1 1.6-.6.2-.2-1 1.4-.8 1.2.2', c.p, .85),
    tick:c=>C(0, 0, 3.6, c.hi, c, .5) + L('M0 0V-2.4M0 0L1.6 1', c.k, .55) + [0, 90, 180, 270].map(a=>L('M0-3V-2.5', c.k, .45).replace('/>', ' transform="rotate(' + a + ')"/>')).join(''),
    gear:c=>P(starD(3.8, 2.8, 8), c.s, c, .45) + C(0, 0, 1.2, c.hi, c, .35),
    facet:c=>P('M-3.6-1.2L-2-3H2L3.6-1.2 0 3.8Z', c.n('#8fd4f6'), c, .45) + L('M-3.6-1.2H3.6M-2-3L-.8-1.2 0 3.8M2-3L.8-1.2', '#e8f8ff', .35, .85),
    gem:c=>P('M-3-1L-1.6-2.8H1.6L3-1 0 3Z', c.n('#e04a6a'), c, .45) + L('M-3-1H3M-1.6-2.8L-.6-1 0 3', '#ffd0dc', .35, .85),
    coin:c=>C(0, 0, 3.2, c.n('#f2c23a'), c, .5) + C(0, 0, 2.2, 'none', { k:'#b8862a' }, .4) + shine('M-2-1.6A2.4 2.4 0 0 1-.4-2.6', c),
    mist:c=>C(-2.4, 1, .9, c.hi) + C(-.4, -.6, 1.2, c.hi) + C(1.8, -1.8, .8, c.hi) + C(2.6, .6, .55, c.hi) + C(.8, 1.6, .5, c.hi),
    chat:c=>P('M-4.2-2.4C-4.2-3.6-3.4-4-2.4-4H2.6C3.6-4 4.2-3.4 4.2-2.4V.6C4.2 1.6 3.6 2.2 2.6 2.2H-.6L-2.8 4.2-2.4 2.2C-3.4 2.2-4.2 1.6-4.2.6Z', c.hi, c, .5) + C(-1.8, -.9, .5, c.a) + C(0, -.9, .5, c.a) + C(1.8, -.9, .5, c.a),
    heart:c=>P('M0 3.8C-3.6 1.2-4.4-1-3.4-2.6-2.4-4 -.8-3.6 0-2.2.8-3.6 2.4-4 3.4-2.6 4.4-1 3.6 1.2 0 3.8Z', c.n('#e0485e'), c, .5) + shine('M-2.6-1.8A1.2 1.2 0 0 1-1.6-2.6', c),
    page:c=>P('M-3-4H1.6L3 -2.6V4H-3Z', '#fbf6ea', c, .45) + L('M-1.8-1.6H1.8M-1.8 0H1.8M-1.8 1.6H.8', '#b8ab94', .4),
    bookmark:c=>P('M-1.6-4.4H1.6V4.4L0 2.6-1.6 4.4Z', c.a, c, .45),
    pencil:c=>P('M-4.2 3.2L2.6-3.6 4-2.2-2.8 4.6-4.6 4.6Z', c.n('#f2c23a'), c, .45) + P('M-4.2 3.2L-2.8 4.6-4.6 4.6Z', '#3a2a20', c, .3),
    mappath:c=>L('M-4.4 3.4C-2.6 1.4-1.2 3-.2.8S2 -1.6 3.2-2.6', c.k, .55, .8) .replace('/>', ' stroke-dasharray=".9 .9"/>') + P('M3.6-4.2L4.6-3.2M4.6-4.2L3.6-3.2', 'none', { k:c.n('#d8302c') }, .6) + C(-4.4, 3.4, .55, c.a),
    pine:c=>P('M0-4.6L2.4-1.2H1.2L3.2 1.8H.6V3.6H-.6V1.8H-3.2L-1.2-1.2H-2.4Z', c.n('#3f7a4a'), c, .45),
    butterfly:c=>E(-1.5, 1.5, 1.1, 1.3, c.g, c, 20, .3) + E(1.5, 1.5, 1.1, 1.3, c.g, c, -20, .3) + E(-2, -.9, 1.9, 2.3, c.a, c, -25, .35) + E(2, -.9, 1.9, 2.3, c.a, c, 25, .35) + C(-2.2, -1.3, .5, c.hi) + C(2.2, -1.3, .5, c.hi) + L('M0-2.4V2.8', c.k, .7) + L('M0-2.4L-1-4.2M0-2.4L1-4.2', c.k, .4),
  };

  /* ---- القوالب: مواضع آمنة بالنسبة المئوية لعرض/ارتفاع البطاقة (x%, y%, حجم% من العرض)، مأخوذة بعد فحص الرسم الفعلي لكل بطاقة.
     no: مستطيلات محمية [x1,y1,x2,y2] (الوجه/الرأس، الجسم المهم، شارة الندرة، الزخارف الرئيسية) — اللوحات والستيكر تُضاف آلياً.
     hold: موضع «باليد» [x%, y%, حجم%, ميل] فقط حيث توجد يد مرئية بمكان آمن بعيد عن الوجه. max: أقصى عدد عناصر للبطاقة. */
  const D = 'd', W = 'w', MO = 'm';
  const T = {
    'd:C':  { slots:[[12, 45, 9], [88, 34, 8.5], [87, 53, 7], [16, 61, 6], [84, 64, 6], [37, 5, 4.5], [64, 5, 4.5], [10, 88, 5], [90, 88, 5]], no:[[25, 6, 80, 56], [30, 56, 74, 69], [38, 79, 62, 99]] },
    'd:B':  { slots:[[86, 24, 8], [14, 35, 7], [88, 64, 6], [12, 66, 6], [37, 5, 4.5], [64, 5, 4.5], [10, 90, 5], [90, 90, 5]], no:[[25, 8, 80, 57], [30, 56, 74, 69], [38, 78, 62, 99], [4, 40, 22, 62], [78, 40, 96, 62]] },
    'd:A':  { slots:[[15, 40, 8.5], [87, 30, 8], [88, 50, 6.5], [15, 56, 6], [36, 5, 4.5], [65, 5, 4.5], [10, 90, 5], [90, 90, 5]], no:[[27, 8, 80, 56], [30, 56, 74, 69], [38, 78, 62, 99], [1, 40, 9, 50], [91, 40, 99, 50]] },
    'd:S':  { slots:[[16, 36, 8], [85, 30, 8], [84, 50, 6], [37, 4, 4.2], [64, 4, 4.2], [11, 92, 4.6], [89, 92, 4.6]], no:[[24, 8, 80, 56], [28, 56, 72, 67], [36, 74, 64, 99], [4, 44, 18, 66], [82, 44, 96, 66]] },
    'd:SS': { slots:[[84, 22, 7.5], [17, 33, 7], [85, 36, 6], [38, 4, 4], [63, 4, 4], [12, 93, 4.4], [88, 93, 4.4]], no:[[26, 2, 78, 56], [26, 56, 76, 66], [36, 74, 64, 99], [0, 38, 22, 58], [78, 38, 100, 58]] },
    'w:C':  { slots:[[86, 32, 8.5], [85, 50, 7], [87, 63, 5.5], [62, 6, 4.5], [37, 6, 4.5], [10, 90, 5], [90, 90, 5]], no:[[29, 8, 77, 50], [12, 26, 40, 71], [24, 40, 80, 71], [38, 78, 62, 99]] },
    'w:B':  { slots:[[88, 42, 7.5], [87, 59, 6], [13, 33, 6.5], [37, 6, 4.5], [10, 90, 5], [90, 90, 5]], no:[[32, 10, 71, 49], [62, 11, 81, 47], [18, 40, 82, 71], [38, 78, 62, 99]], hold:[79.6, 12.2, 11, -16] },
    'w:A':  { slots:[[86, 30, 8], [87, 50, 7], [13, 36, 6.5], [37, 6, 4.5], [64, 6, 4.5], [10, 90, 5], [90, 90, 5]], no:[[30, 8, 77, 52], [20, 40, 82, 71], [38, 78, 62, 99]] },
    'w:S':  { slots:[[88, 30, 7], [88, 47, 6.5], [86, 60, 5], [66, 4.5, 4], [12, 94, 4], [88, 94, 4]], no:[[36, 6, 76, 46], [16, 33, 44, 60], [26, 44, 82, 64], [36, 74, 64, 99], [6, 79, 15, 86], [85, 79, 94, 86]] },
    'w:SS': { slots:[[80, 38, 6.5], [82, 54, 6], [64, 9, 4], [37, 9, 4], [13, 92, 4.2], [87, 92, 4.2]], no:[[33, 12, 74, 46], [14, 46, 88, 64], [36, 74, 64, 99], [86, 10, 100, 70], [0, 10, 14, 70]], hold:[20.4, 51.6, 9.5, 10] },
    'm:C':  { slots:[[84, 6, 8], [24, 66, 7], [76, 66, 7], [88, 18, 5]], no:[[30, 8, 82, 42], [36, 60, 64, 72], [74, 18, 100, 38]] },
    'm:B':  { slots:[[84, 6, 8], [24, 66, 7], [76, 66, 7], [90, 22, 5]], no:[[30, 4, 80, 38], [36, 60, 64, 72]] },
    'm:A':  { slots:[[84, 6, 8], [24, 66, 7], [76, 66, 7], [90, 22, 5]], no:[[28, 2, 82, 38], [36, 60, 64, 72], [76, 38, 96, 50]] },
    'm:S':  { slots:[[84, 6, 8], [24, 66, 7], [76, 66, 7]], no:[[24, 6, 78, 34], [36, 60, 64, 72], [18, 8, 44, 20], [70, 8, 96, 20]] },
    'm:SS': { slots:[[84, 6, 8], [24, 66, 7], [76, 66, 7], [90, 22, 5]], no:[[28, 4, 78, 34], [36, 60, 64, 72]] },
    's:teacher': { slots:[[87, 24, 7], [16, 63, 6.5], [85, 62, 6.5], [9, 72, 5], [91, 72, 5], [70, 5, 4], [40, 5, 4]], no:[[13, 13, 82, 66], [20, 78, 80, 92], [0, 0, 12, 12], [88, 0, 100, 12], [0, 88, 12, 100], [88, 88, 100, 100]] },
    'p':    { slots:[[82, 10, 7.5], [88, 32, 6], [12, 52, 6], [88, 54, 6], [12, 74, 5], [88, 74, 5]], no:[[26, 22, 74, 66], [4, 78, 96, 98], [36, 2, 64, 12]] }
  };
  /* موضع الستيكر بكل عائلة (من قواعد .rwc-stk-* نفسها، للقراءة فقط) */
  const STK = { d:[-2.5, -2, 33], w:[-2.5, -2, 33], s:[-2.5, -2, 33], m:[-4, -1.5, 44], p:[3, 2, 36] };
  /* CODIS-MULTI-STICKER: الستيكر الثاني والثالث — عمود متدرّج تحت الرئيسي على الحافة اليسرى (بعيد عن الوجه واللوحات في كل القوالب):
     يطلّ كلٌّ منها من تحت الذي فوقه بتداخل صغير، بحجم أصغر وميل متعاكس، فيبدو كمجموعة ستيكرات ملصوقة لا كأيقونات مبعثرة.
     [يسار% من العرض، أعلى% من الارتفاع، عرض% من العرض، ميل°]. المصدر الوحيد للموضع (وسم الصور + منع الزخرفة من مكانها) */
  const STK2 = {
    d:[[.5, 21.5, 22, 7], [-1.5, 36.5, 18, -6]], w:[[.5, 21.5, 22, 7], [-1.5, 36.5, 18, -6]], s:[[.5, 21.5, 22, 7], [-1.5, 36.5, 18, -6]],
    m:[[-2, 20, 28, 7], [0, 32.5, 23, -6]], p:[[5, 28, 22, 7], [3.5, 42.5, 18, -6]]
  };
  function plates(fam, k){
    const src = fam === 'd' ? CODIS_CARD_SLOTS : fam === 'w' ? CODIS_WEEKLY_SLOTS : fam === 'm' ? CODIS_MONTHLY_SLOTS : null;
    const S = src && src[k], out = [];
    if(S) ['name', 'price', 'solo', 'info'].forEach(n=>{ const a = S[n]; if(a) out.push([a[0] - 1.5, a[1] - 1.2, a[0] + a[2] + 1.5, a[1] + a[3] + 1.2]); });
    if(fam === 's'){ const p = CODIS_SPECIAL_CARD_SLOTS[k] && CODIS_SPECIAL_CARD_SLOTS[k].plate; if(p) out.push([p[0] - 1.5, p[1] - 1.2, p[0] + p[2] + 1.5, p[1] + p[3] + 1.2]); }
    return out;
  }
  function arOf(fam, k){
    const src = fam === 'd' ? CODIS_CARD_SLOTS : fam === 'w' ? CODIS_WEEKLY_SLOTS : fam === 'm' ? CODIS_MONTHLY_SLOTS : fam === 's' ? CODIS_SPECIAL_CARD_SLOTS : null;
    return (src && src[k] && src[k].ar) || .8;
  }
  function palOf(id){
    const d = typeof CODIS_STICKER_ATMOS === 'object' && CODIS_STICKER_ATMOS[id];
    if(d) return d;
    const o = CodisStickers.get(id), fam = { food:'crumb herb', iraqi:'herb ember', sweets:'sugar crumb', cold:'drop bubble', tea:'steam bean', games:'pixel star', watch:'star spark', create:'paintdrop spark', travel:'star leaf', care:'bubble spark', social:'heart spark', rest:'star cloud' };
    return [String((o && fam[o.cat]) || 'spark star').split(' '), ['#c9a46a', '#8a5a3a', '#e0a050', '#f6ead2', '#3a2516', '#ffd98a'], 0, 0];   /* بلا وصفة: عام هادئ حسب التصنيف */
  }
  /* تقاطع دائرة/مستطيل بوحدات المشهد */
  const hit = (x, y, r, b, H)=>{ const x1 = b[0], y1 = b[1] * H / 100, x2 = b[2], y2 = b[3] * H / 100; const cx = Math.max(x1, Math.min(x, x2)), cy = Math.max(y1, Math.min(y, y2)); return (x - cx) * (x - cx) + (y - cy) * (y - cy) < r * r; };

  function build(id, fam, k){
    const key = fam + ':' + (fam === 'p' ? '' : k), T0 = T[fam === 'p' ? 'p' : key];
    if(!T0) return null;
    const ids = String(id).split('+'), d = palOf(ids[0]), motifs = d[0].filter(m=>M[m]), pal = d[1], ar = arOf(fam, k), H = 100 / ar, r = rng(h32(id + '|' + key));
    if(!motifs.length) return null;
    /* عدة ستيكرات: الجو من الرئيسي (ألوانه وبطله)، ويدخل بطل كل ستيكر إضافي كعنصر ثانوي واحد ⇒ مزيج متناسق لا خليط */
    ids.slice(1).forEach((x, i)=>{ const e2 = palOf(x)[0].find(m=>M[m] && motifs.indexOf(m) === -1); if(e2) motifs.splice(Math.min(1 + i, motifs.length), 0, e2); });
    const ink = mix(pal[4], '#140c08', .55);
    const c = { p:pal[0], s:pal[1], a:pal[2], hi:pal[3], sh:pal[4], g:pal[5], k:ink, n:h=>mix(h, pal[0], .18) };
    const st = STK[fam], sx = st[0] + st[2] / 2, sy = st[1] * H / 100 + st[2] / 2;
    const block = (T0.no || []).concat(plates(fam, k)).concat([[st[0] - 1, st[1] - 1, st[0] + st[2] + 1, st[1] + (st[2] + 2) * 100 / H]])
      .concat(STK2[fam].slice(0, ids.length - 1).map(b=>[b[0] - 1.5, b[1] - 1, b[0] + b[2] + 1.5, b[1] + (b[2] + 2) * 100 / H]));
    const free = (x, y, rad)=>x - rad > 1 && x + rad < 99 && y - rad > 1 && y + rad < H - 1 && !block.some(b=>hit(x, y, rad, b, H));
    /* البطل في أحد أكبر ثلاثة مواضع (حسب البذرة) ثم البقية بترتيب مخلوط ثابت */
    const slots = T0.slots.map((s, i)=>({ x:s[0], y:s[1] * H / 100, s:s[2], i:i }));
    const lead = slots.slice(0, 3).sort((a, b)=>b.s - a.s), hero = lead[Math.floor(r() * Math.min(2, lead.length))];
    const rest = slots.filter(s=>s !== hero).map(s=>({ s:s, k:r() + (s.s >= 6 ? 0 : .35) })).sort((a, b)=>a.k - b.k).map(o=>o.s);
    const cap = Math.min(d[3] || 99, fam === 'm' ? 4 : 6, slots.length), order = [hero].concat(rest).slice(0, cap);
    const tiny = motifs[motifs.length - 1];
    let body = '', placed = [];
    /* تسلسل العناصر: البطل، ثم الثاني، ثم البطل مصغّراً (قطع صغيرة منه موزّعة)، ثم البقية بالتناوب */
    const seq = [motifs[0]]; for(let j = 1; seq.length < 12; j++){ seq.push(motifs[1 + (j - 1) % Math.max(1, motifs.length - 1)] || motifs[0]); if(j % 2 === 1) seq.push(motifs[0]); }
    order.forEach((s, j)=>{
      const m = seq[j], again = j > 0 && m === motifs[0];
      const sz = s.s * 1.6 * (j === 0 ? 1.2 : again ? .72 : (.86 + r() * .2)), x = s.x + (r() - .5) * 2.2, y = s.y + (r() - .5) * 2.2, rad = sz * .48;
      if(!free(x, y, rad)) return;
      placed.push({ x:x, y:y, s:sz });
      body += '<g transform="translate(' + f(x) + ' ' + f(y) + ') rotate(' + f((r() - .5) * 46) + ') scale(' + f(sz / 10) + ')">' + M[m](c, r) + '</g>';
      /* حبيبات صغيرة حول أول عنصرين فقط: تجمّع مقصود بدل نثر عشوائي */
      if(j < 2) for(let q = 0; q < 2; q++){
        const a = r() * Math.PI * 2, dist = sz * (.7 + r() * .35), px = x + Math.cos(a) * dist, py = y + Math.sin(a) * dist, ps = sz * (.26 + r() * .1);
        if(free(px, py, ps * .5)) body += '<g transform="translate(' + f(px) + ' ' + f(py) + ') rotate(' + f(r() * 360) + ') scale(' + f(ps / 10) + ')" opacity=".9">' + M[tiny](c, r) + '</g>';
      }
    });
    /* أثر صغير ينزل من الستيكر بمحاذاة الحافة (يربطه بالبطاقة) — فقط ما يقع بمكان آمن */
    const tx = sx - st[2] * .12, ty0 = sy + st[2] * .62;
    for(let q = 0; q < 3; q++){
      const px = tx - q * 1.1 + (r() - .5) * 1.4, py = ty0 + q * 3.4 + r() * 1.2, ps = 2.6 - q * .45;
      if(free(px, py, ps * .5)) body += '<g transform="translate(' + f(px) + ' ' + f(py) + ') rotate(' + f(r() * 360) + ') scale(' + f(ps / 10) + ')" opacity="' + f(.95 - q * .2) + '">' + M[tiny](c, r) + '</g>';
    }
    /* ضوء ناعم: هالة خلف الستيكر تربطه بالبطاقة + لمعة خفيفة عند العنصر البطل. لا تلوين كامل للبطاقة */
    const lt = mix(pal[5], '#fff1d2', .4);   /* ضوء دافئ مشتق من لون الستيكر — لا بقعة لون مشبعة */
    const glow = '<radialGradient id="g"><stop offset=".45" stop-color="' + lt + '" stop-opacity=".42"/><stop offset=".72" stop-color="' + lt + '" stop-opacity=".12"/><stop offset="1" stop-color="' + lt + '" stop-opacity="0"/></radialGradient>' +
      '<radialGradient id="h"><stop offset="0" stop-color="' + lt + '" stop-opacity=".3"/><stop offset="1" stop-color="' + lt + '" stop-opacity="0"/></radialGradient>' +
      '<filter id="s" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy=".35" stdDeviation=".38" flood-color="#0b0604" flood-opacity=".5"/></filter>';
    const lights = '<circle cx="' + f(sx) + '" cy="' + f(sy) + '" r="' + f(st[2] * .86) + '" fill="url(#g)"/>' + (placed[0] ? '<circle cx="' + f(placed[0].x) + '" cy="' + f(placed[0].y) + '" r="' + f(placed[0].s * 1.25) + '" fill="url(#h)"/>' : '');
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 ' + f(H) + '" preserveAspectRatio="none"><defs>' + glow + '</defs>' + lights + '<g filter="url(#s)">' + body + '</g></svg>';
    const hold = (T0.hold && d[2]) ? T0.hold : null;
    return { src:'data:image/svg+xml,' + encodeURIComponent(svg), hold:hold, file:d[2], n:placed.length, pts:placed, H:H, block:block };
  }
  function get(id, fam, k){
    const key = id + '|' + fam + '|' + (k || '');
    if(!cache.has(key)){ let v = null; try{ v = build(id, fam, k); }catch(x){ v = null; } cache.set(key, v); }
    return cache.get(key);
  }
  /* HTML الطبقة: صورة الجو + (اختياري) العنصر «باليد». بلا ستيكر صالح ⇒ نص فارغ (البطاقة كما كانت تماماً) */
  function html(id, fam, k){
    const a = id ? get(id, fam, k) : null; if(!a) return '';
    let h = '<img class="rwc-atm rwc-atm-' + fam + '" src="' + a.src + '" alt="" aria-hidden="true" draggable="false" decoding="async">';
    if(a.hold) h += '<img class="rwc-atm-hold" src="' + escapeHtml(CODIS_STK_BASE + a.file) + '" alt="" aria-hidden="true" draggable="false" decoding="async" onerror="this.remove()" style="left:' + (a.hold[0] - a.hold[2] / 2) + '%;top:calc(' + a.hold[1] + '% - ' + (a.hold[2] / 2) + 'cqw);width:' + a.hold[2] + '%;--r:' + a.hold[3] + 'deg">';
    return h;
  }
  /* وسم الستيكرات الإضافية (2 و3) بموضعها من STK2 — الرئيسي يبقى بوسمه وقواعده كما هي حرفياً */
  function extras(ids, fam){
    return ids.slice(1, 3).map((x, i)=>{ const b = STK2[fam][i], u = CodisStickers.url(x);
      return u ? '<img class="rwc-stk2 rwc-stk2-' + (i + 2) + '" src="' + escapeHtml(u) + '" alt="" draggable="false" decoding="async" onerror="this.remove()" style="left:' + b[0] + '%;top:' + b[1] + '%;width:' + b[2] + '%;--r:' + b[3] + 'deg">' : ''; }).reverse().join('');   /* الأسفل أولاً ⇒ كل ستيكر يطلّ من تحت الذي فوقه */
  }
  return { html:html, get:get, extras:extras, motifs:()=>Object.keys(M), templates:()=>Object.keys(T), _M:M };
})();
