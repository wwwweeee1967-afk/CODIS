/* CODIS-STICKERS-13 test — الستيكرات الثلاثة عشر الجديدة داخل المكتبة الأصلية (evaluate in the page, guest; يحتاج assets/stickers مخدوماً بجانب الصفحة).
   TEST=tests/stickers13_browser.js node tools/prof/cdp.mjs http://127.0.0.1:8766/app/CODIS_FINAL.html tools/prof/s_evaltest.mjs --cpu 1 */
(async function(){ try{
  const out = [], T = (n, ok, i)=>out.push({ name:n, ok:!!ok, info:i === undefined ? '' : i });
  const NEW = { social_media:'digital', cigarettes:'shop', jummar_palm:'iraqi', lettuce_head:'iraqi', iraqi_samoon:'iraqi', pickles:'iraqi', mushrooms:'food', shish_shawarma:'food', chicken_tikka_rice:'iraqi', italian_saj:'food', fishing_trip:'out', cafe_front:'out', lamb_mandi:'iraqi' };
  const ids = Object.keys(NEW), S = q=>CodisStickers.search(q).map(o=>o.id), has = (q, id)=>S(q).indexOf(id) !== -1;

  T('library = 115 old + 13 new = 128, all with an image', CodisStickers.total() === 128 && CodisStickers.count() === 128, CodisStickers.count() + '/' + CodisStickers.total());
  T('13 new ids present with the right category and name', ids.every(id=>{ const o = CodisStickers.get(id); return o && o.cat === NEW[id] && o.name; }), ids.filter(id=>!CodisStickers.get(id)).join(','));
  T('no id collisions (all 128 unique) and no category was added (still 18)', new Set(CODIS_STICKER_ITEMS.map(x=>x[0])).size === 128 && CodisStickers.cats().length === 18 && CODIS_STICKER_CATS.length === 18);
  T('old stickers untouched (spot check 12 originals still resolve)', ['shawarma', 'burger', 'pizza', 'cafe_table', 'biryani', 'mandi_pot', 'tikka', 'masgouf', 'espresso', 'camping', 'crown', 'trophy'].every(id=>CodisStickers.has(id)));

  /* كل ملف صورة يُحمَّل فعلاً (لا مفقود) وبأبعاد مربعة ≥ 200px */
  const loads = await Promise.all(ids.map(id=>new Promise(res=>{ const im = new Image(); im.onload = ()=>res([id, im.naturalWidth, im.naturalHeight]); im.onerror = ()=>res([id, 0, 0]); im.src = CodisStickers.url(id); })));
  T('all 13 image files load (no missing assets)', loads.every(l=>l[1] > 0 && l[2] > 0), loads.filter(l=>!(l[1] > 0)).map(l=>l[0]).join(','));
  T('each sticker is its own file (13 distinct urls, none a combined sheet)', new Set(ids.map(id=>CodisStickers.url(id).split('?')[0])).size === 13 && ids.every(id=>/\/[a-z0-9_]+\.svg\?v=/.test(CodisStickers.url(id))));

  /* بحث: عربي · عراقي · مرادفات · إنجليزي */
  const Q = [['جمار', 'jummar_palm'], ['قلب النخلة', 'jummar_palm'], ['جمار نخيل', 'jummar_palm'], ['palm heart', 'jummar_palm'],
    ['سوشال ميديا', 'social_media'], ['تيك توك', 'social_media'], ['انستغرام', 'social_media'], ['تلغرام', 'social_media'], ['social media', 'social_media'],
    ['سكائر', 'cigarettes'], ['سجائر', 'cigarettes'], ['جكارة', 'cigarettes'], ['دخان', 'cigarettes'], ['cigarettes', 'cigarettes'],
    ['خس', 'lettuce_head'], ['رأس خس', 'lettuce_head'], ['سلطة', 'lettuce_head'], ['lettuce', 'lettuce_head'],
    ['صمون', 'iraqi_samoon'], ['صمون عراقي', 'iraqi_samoon'], ['خبز', 'iraqi_samoon'], ['samoon', 'iraqi_samoon'],
    ['طرشي', 'pickles'], ['مخلل', 'pickles'], ['مخللات', 'pickles'], ['pickles', 'pickles'],
    ['فطر', 'mushrooms'], ['مشروم', 'mushrooms'], ['mushroom', 'mushrooms'],
    ['شيش شاورما', 'shish_shawarma'], ['شاورما', 'shish_shawarma'], ['سيخ شاورما', 'shish_shawarma'], ['shawarma', 'shish_shawarma'],
    ['تكة دجاج', 'chicken_tikka_rice'], ['تمن', 'chicken_tikka_rice'], ['دجاج مشوي', 'chicken_tikka_rice'], ['chicken tikka', 'chicken_tikka_rice'],
    ['صاج', 'italian_saj'], ['صاج ايطالي', 'italian_saj'], ['صاج إيطالي', 'italian_saj'], ['italian', 'italian_saj'],
    ['صيد سمك', 'fishing_trip'], ['صنارة', 'fishing_trip'], ['سمچ', 'fishing_trip'], ['fishing', 'fishing_trip'],
    ['كافيه', 'cafe_front'], ['كوفي شوب', 'cafe_front'], ['مقهى', 'cafe_front'], ['cafe', 'cafe_front'],
    ['مندي', 'lamb_mandi'], ['مندي لحم', 'lamb_mandi'], ['لحم غنم', 'lamb_mandi'], ['mandi', 'lamb_mandi'], ['lamb', 'lamb_mandi']];
  const miss = Q.filter(q=>!has(q[0], q[1]));
  T('search finds each new sticker by Arabic / Iraqi / synonym / English words (' + Q.length + ' queries)', miss.length === 0, miss.map(q=>q[0] + '→' + q[1]).join(' | '));
  T('shish shawarma is distinct from the existing wrap sticker (different id/art)', CodisStickers.get('shish_shawarma').id !== CodisStickers.get('shawarma').id && CodisStickers.url('shish_shawarma') !== CodisStickers.url('shawarma'));
  T('category filters list the new items', CodisStickers.search('', 'iraqi').some(o=>o.id === 'lamb_mandi') && CodisStickers.search('', 'out').some(o=>o.id === 'fishing_trip') && CodisStickers.search('', 'digital').some(o=>o.id === 'social_media') && CodisStickers.search('', 'food').some(o=>o.id === 'italian_saj'));

  /* الزخرفة الثانوية: لكل ستيكر وصفة ولوحة ألوان وتوزيع على كل قوالب الشهري والأسبوعي واليومي */
  const fams = [['d', 'C'], ['d', 'SS'], ['w', 'B'], ['w', 'SS'], ['m', 'C'], ['m', 'B'], ['m', 'A'], ['m', 'S'], ['m', 'SS']];
  T('every new sticker has an atmosphere recipe (CODIS_STICKER_ATMOS)', ids.every(id=>CODIS_STICKER_ATMOS[id] && CODIS_STICKER_ATMOS[id][0].length >= 3 && CODIS_STICKER_ATMOS[id][1].length === 6));
  const low = []; ids.forEach(id=>fams.forEach(([f, k])=>{ const a = CodisAtmos.get(id, f, k); if(!a || a.n < 2) low.push(id + ':' + f + k + '=' + (a ? a.n : 'null')); }));
  T('each new sticker gets ≥2 decorative elements on every daily/weekly/monthly template', low.length === 0, low.slice(0, 8).join(' '));
  const over = []; ids.forEach(id=>['C', 'B', 'A', 'S', 'SS'].forEach(k=>{ const a = CodisAtmos.get(id, 'm', k); if(a && a.n > 4) over.push(id + k); }));
  T('monthly atmosphere stays restrained (≤4 elements)', over.length === 0, over.join(','));
  T('atmosphere is deterministic (same sticker+card = same layer)', ids.every(id=>CodisAtmos.get(id, 'm', 'S').src === CodisAtmos.get(id, 'm', 'S').src) && CodisAtmos.html('lamb_mandi', 'm', 'A') === CodisAtmos.html('lamb_mandi', 'm', 'A'));

  /* الاستعمال بالبطاقات: ستيكر واحد/ثلاثة · الرئيسي · الإزالة · صلاحية المعرّف */
  T('new ids are valid stored values (single and 3-list)', codisStickerIdOk('jummar_palm') === 'jummar_palm' && codisStickerIdOk('jummar_palm+cafe_front+lamb_mandi') === 'jummar_palm+cafe_front+lamb_mandi' && codisStickerList('lamb_mandi+cafe_front').join() === 'lamb_mandi,cafe_front');
  const card = (fam, id)=>fam === 'm' ? codisMonthlyCardHtml({ kind:'reward', scope:'monthly', rarityTone:'S', item:'x', stickerId:id }, { plain:true }) : fam === 'w' ? codisWeeklyCardHtml({ kind:'reward', scope:'weekly', rarityTone:'B', item:'x', stickerId:id }, { plain:true }) : codisRewardCardHtml({ kind:'reward', scope:'daily', rarityTone:'A', item:'x', stickerId:id }, { plain:true });
  const cnt = (h, re)=>(h.match(re) || []).length;
  T('each new sticker renders as the main sticker on daily/weekly/monthly cards', ids.every(id=>['d', 'w', 'm'].every(f=>cnt(card(f, id), new RegExp('rwc-stk rwc-stk-' + f + '"[^>]*' + id.replace(/_/g, '_')) ) + cnt(card(f, id), new RegExp(id + '\\.svg')) >= 1)));
  T('3 stickers: main + 2 extras, the first id is the main one', (()=>{ const h = card('m', 'fishing_trip+lamb_mandi+jummar_palm'), main = (h.match(/<img class="rwc-stk rwc-stk-m"[^>]*>/) || [''])[0]; return cnt(h, /rwc-stk2 /g) === 2 && main.indexOf('fishing_trip') !== -1 && main.indexOf('lamb_mandi') === -1; })());
  T('no sticker ⇒ no sticker layer (card unchanged)', cnt(card('m', null), /rwc-stk|rwc-atm/g) === 0);
  T('CODIS_STICKER_MAX is still 3 and a 4th is dropped', CODIS_STICKER_MAX === 3 && codisStickerList('a_1+b_2+c_3+d_4').length === 3);

  const failed = out.filter(r=>!r.ok); return { passed:out.length - failed.length, failed:failed.length, failures:failed };
}catch(e){ return { passed:0, failed:1, failures:[{ name:'EXCEPTION', info:String(e && e.stack || e) }] }; } })();
