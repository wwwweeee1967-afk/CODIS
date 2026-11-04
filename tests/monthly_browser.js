/* CODIS-MONTHLY-V2 test — الكروت الشهرية الخمسة الجديدة (evaluate in the page, guest). يقيس الأصول والهندسة الفعلية المرسومة.
   TEST=tests/monthly_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1 */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i }), sleep = ms=>new Promise(r=>setTimeout(r, ms));
  const K = ['C', 'B', 'A', 'S', 'SS'];
  T('monthly art/slots keys are exactly C,B,A,S,SS', JSON.stringify(Object.keys(CODIS_MONTHLY_ART)) === JSON.stringify(K) && JSON.stringify(Object.keys(CODIS_MONTHLY_SLOTS)) === JSON.stringify(K));
  T('rarity names untouched (CODIS_MONTHLY_NAMES)', codisMonthlyName('C') === 'سلفرية' && codisMonthlyName('B') === 'فضية' && codisMonthlyName('A', 'x') === 'x');

  /* ---- 1) الأصول: نفس اللوحة الموحّدة 4:5، شفافية الأركان، بلا هالة داكنة على الحافة، لون الإطار = لون الندرة ---- */
  const dec = {}, px = {};
  for(const k of K){
    const im = new Image(); im.src = CODIS_MONTHLY_ART[k]; await im.decode();
    const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight; const g = c.getContext('2d', { willReadFrequently:true }); g.drawImage(im, 0, 0);
    dec[k] = im; px[k] = { c:c, g:g, d:g.getImageData(0, 0, c.width, c.height).data };
  }
  const S0 = CODIS_MONTHLY_SLOTS.C;
  T('all five assets share one canvas size', K.every(k=>dec[k].naturalWidth === dec.C.naturalWidth && dec[k].naturalHeight === dec.C.naturalHeight), K.map(k=>dec[k].naturalWidth + 'x' + dec[k].naturalHeight).join(' '));
  T('canvas is 4:5 and SLOTS describe the real asset size', K.every(k=>{ const s = CODIS_MONTHLY_SLOTS[k]; return s.w === dec[k].naturalWidth && s.h === dec[k].naturalHeight && Math.abs(s.ar - 0.8) < 0.005 && Math.abs(s.w / s.h - s.ar) < 0.002; }));
  const A = (k, x, y)=>px[k].d[(Math.round(y) * px[k].c.width + Math.round(x)) * 4 + 3];
  T('corners are transparent, centre opaque (no dark rectangle left from the composite sheet)', K.every(k=>{ const W = px[k].c.width, H = px[k].c.height; return A(k, 1, 1) === 0 && A(k, W - 2, 1) === 0 && A(k, 1, H - 2) === 0 && A(k, W - 2, H - 2) === 0 && A(k, W / 2, H / 2) === 255; }));
  const halo = K.map(k=>{ const d = px[k].d; let n = 0, s = 0; for(let i = 0; i < d.length; i += 4){ if(d[i + 3] > 12 && d[i + 3] < 240){ n++; s += Math.max(d[i], d[i + 1], d[i + 2]); } } return n ? s / n : 255; });
  T('edge band has no dark halo (mean brightness of semi-transparent pixels)', halo.every(v=>v > 95), halo.map(v=>v.toFixed(0)).join(','));
  /* لون الإطار: متوسط البكسلات الداكنة الملوّنة (حشوة الإطار) بالربع السفلي ⇒ درجة اللون (hue) */
  const hue = ([r, g, b])=>{ const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn || 1; let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h *= 60; return h < 0 ? h + 360 : h; };
  const frame = k=>{ const W = px[k].c.width, H = px[k].c.height; let r = 0, g = 0, b = 0, n = 0; for(let y = Math.round(H * .70); y < H * .96; y++) for(let x = 0; x < W; x++){ const i = (y * W + x) * 4, R = px[k].d[i], G = px[k].d[i + 1], B = px[k].d[i + 2], mx = Math.max(R, G, B), mn = Math.min(R, G, B); if(px[k].d[i + 3] > 250 && mx < 110 && mx > 25 && (mx - mn) / mx > .22){ r += R; g += G; b += B; n++; } } return [r / n, g / n, b / n]; };
  const F = {}, Hh = {}; K.forEach(k=>{ F[k] = frame(k); Hh[k] = hue(F[k]); });
  T('C frame is green', Hh.C > 50 && Hh.C < 170, Hh.C.toFixed(0));
  T('B frame is blue', Hh.B > 170 && Hh.B < 260, Hh.B.toFixed(0));
  T('A frame is purple', Hh.A > 290 && Hh.A < 356, Hh.A.toFixed(0));
  T('S frame is gold/amber', Hh.S > 12 && Hh.S < 48, Hh.S.toFixed(0));
  T('SS frame is red', Hh.SS < 12 || Hh.SS > 356, Hh.SS.toFixed(0));

  /* ---- 2) خانات النص: داخل اللوحة، فوق/تحت بلا تداخل، بعيداً عن الميدالية المركزية ---- */
  K.forEach(k=>{
    const s = CODIS_MONTHLY_SLOTS[k], n = s.name, i = s.info, inb = a=>a[0] >= 0 && a[1] >= 0 && a[0] + a[2] <= 100 && a[1] + a[3] <= 100;
    T(k + ': both plates inside the card', inb(n) && inb(i));
    T(k + ': name plate above info plate, no overlap', n[1] + n[3] < i[1]);
    T(k + ': name plate is clear of the centre medallion (x ≥ 50%)', n[0] >= 50, 'left=' + n[0]);
    T(k + ': plates are big enough for text (name ≥ 20% × 5%, info ≥ 45% × 5%)', n[2] >= 20 && n[3] >= 5 && i[2] >= 45 && i[3] >= 5, n.join(',') + ' | ' + i.join(','));
  });
  const nh = K.map(k=>CODIS_MONTHLY_SLOTS[k].name[3]), ih = K.map(k=>CODIS_MONTHLY_SLOTS[k].info[3]);
  T('plate heights are consistent across the five cards (equal text size)', Math.max.apply(0, nh) - Math.min.apply(0, nh) < 1 && Math.max.apply(0, ih) - Math.min.apply(0, ih) < 1, nh.join(',') + ' | ' + ih.join(','));

  /* ---- 3) العرض الفعلي: 4:5 بأي عرض، النص داخل لوحاته، الندرة والكوين حاضران ---- */
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:1000px;opacity:0;pointer-events:none'; document.body.appendChild(host);
  const names = ['سهرة', 'قهوة مع الأصدقاء', 'طلعة عشاء فاخرة في مطعم جديد مع العائلة', 'ساعة راحة'], bad = [], geo = [];
  for(const w of [150, 230, 340]) for(const k of K) for(const nm of names){
    host.innerHTML = '<div style="width:' + w + 'px">' + codisMonthlyCardHtml({ kind:'reward', scope:'monthly', rarityTone:k, item:nm, rarityName:'سلفرية', coinValue:12500 }, { plain:true }) + '</div>';
    codisFitRewardCard(host); await sleep(15);
    const rwc = host.querySelector('.rwc'), art = host.querySelector('.rwc-art'), r = rwc.getBoundingClientRect(), ar = art.getBoundingClientRect();
    geo.push(Math.abs(r.width / r.height - 0.8) < 0.01 && Math.abs(ar.width - r.width) < 1.5 && Math.abs(ar.height - r.height) < 1.5);
    const nb = host.querySelector('.wkc-name'), ns = nb.firstElementChild, ib = host.querySelector('.wkc-info'), is = ib.firstElementChild;
    if(ns.scrollWidth > nb.clientWidth + 1 || ns.offsetHeight > nb.clientHeight + 1) bad.push('name ' + k + ' ' + w + ' ' + nm);
    if(is.offsetWidth > ib.clientWidth + 1) bad.push('info ' + k + ' ' + w);
    if(!/12,?500/.test(ib.textContent) || ib.textContent.indexOf(k) === -1) bad.push('info text ' + k);
    const R = nb.getBoundingClientRect(), Rs = rwc.getBoundingClientRect(), rel = [(R.left - Rs.left) / Rs.width * 100, (R.top - Rs.top) / Rs.height * 100, (R.right - Rs.left) / Rs.width * 100, (R.bottom - Rs.top) / Rs.height * 100];
    if(!(rel[0] >= 50 && rel[2] <= 100 && rel[1] > 70 && rel[3] < 95)) bad.push('name rect ' + k + ' ' + rel.map(Math.round));
    const col = getComputedStyle(ns).color; if(/^rgb\((24[0-9]|25[0-5]), (24[0-9]|25[0-5])/.test(col)) bad.push('name ink is light on parchment ' + k + ' ' + col);
  }
  T('monthly card is 4:5 and the art fills it at 150/230/340px', geo.every(Boolean), geo.length + ' renders');
  T('names (short→long) and info rows stay inside their plates; coin + rarity shown; ink is dark', bad.length === 0, bad.slice(0, 6).join(' / '));
  host.remove();

  /* ---- 4) الستيكر والزخرفة فوق الكروت الجديدة ---- */
  K.forEach(k=>{
    const h = codisMonthlyCardHtml({ kind:'reward', scope:'monthly', rarityTone:k, item:'x', stickerId:'cafe_front+lamb_mandi+fishing_trip' }, { plain:true });
    T(k + ': 3 stickers + atmosphere render on the monthly card', (h.match(/rwc-stk rwc-stk-m/g) || []).length === 1 && (h.match(/rwc-stk2 /g) || []).length === 2 && h.indexOf('rwc-atm rwc-atm-m') !== -1);
  });
  T('monthly sticker uses the same corner box as daily/weekly (33%)', (()=>{ const el = document.createElement('div'); el.innerHTML = codisMonthlyCardHtml({ kind:'reward', scope:'monthly', rarityTone:'B', item:'x', stickerId:'cafe_front' }, { plain:true }); document.body.appendChild(el); const w = getComputedStyle(el.querySelector('.rwc-stk-m')).width; const ok = el.querySelector('.rwc-stk-m'); const pw = el.querySelector('.rwc-stage').clientWidth; const r = parseFloat(w) / pw; el.remove(); return Math.abs(r - .33) < .02 || !pw; })());

  /* ---- 5) كشف الشهري (CodisCardFX): كل بطاقة تبدأ بلا أخطاء ومناطق الحركة داخل البطاقة ---- */
  for(const k of K){
    const host2 = document.createElement('div'); host2.style.cssText = 'position:fixed;left:0;top:0;width:300px;opacity:0;pointer-events:none'; document.body.appendChild(host2);
    const e = { kind:'reward', scope:'monthly', rarityTone:k, item:'سهرة', rarityName:'x', coinValue:5000 }; host2.innerHTML = codisMonthlyCardHtml(e);
    let ok = true, err = ''; try{ const r = CodisCardFX.start(host2, e); ok = !!r; await sleep(120); const figs = host2.querySelectorAll('.rvx-figw').length; if(figs < 2){ ok = false; err = 'figs=' + figs; } CodisCardFX.cancel(); }catch(x){ ok = false; err = String(x); }
    T(k + ': reveal FX starts on the new art with figure regions', ok, err); host2.remove();
  }

  /* ---- 6) الأنظمة الأخرى لم تُمسّ ---- */
  const sig = o=>{ const s = JSON.stringify(o); let h = 5381; for(let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0; return h; };
  T('daily/weekly slots + art untouched (hash)', sig(CODIS_CARD_SLOTS) === 337909859 && sig(CODIS_WEEKLY_SLOTS) === -1070265034 && sig(CODIS_CARD_ART) === -808024406 && sig(CODIS_WEEKLY_ART) === -1471912614, [sig(CODIS_CARD_SLOTS), sig(CODIS_WEEKLY_SLOTS), sig(CODIS_CARD_ART), sig(CODIS_WEEKLY_ART)].join(','));
  T('monthly card remains display-only (no economy/inventory write)', (()=>{ const b = JSON.stringify([data.wallet, data.inventory, data.outcomeLedger]); codisMonthlyCardHtml({ kind:'reward', scope:'monthly', rarityTone:'S', item:'x', coinValue:900 }, { plain:true }); return b === JSON.stringify([data.wallet, data.inventory, data.outcomeLedger]); })());

  const failed = out.filter(r=>!r.ok); return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
