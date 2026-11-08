/* ===== CODIS-USE-VOICE v2 (3.23.0) — محرّك فهم اسم المكافأة وصياغة عبارة الاستخدام =====
   • محلي بالكامل: لا شبكة ولا خدمة خارجية ولا يُخزَّن شيء في بيانات الحساب (ذاكرة «لا تكرار» صغيرة بالجهاز فقط: localStorage codis_voice_recent).
   • الفهم: تطبيع عربي/عراقي/خليجي/شامي/مصري (همزات، ة/ه، گ/چ/پ، تكرار الحروف، سوابق الأفعال «اشوف/نشوف/بشوف/هاكل»، «ال» وحروف الجر واللواحق)
     ← قاموس مفاهيم (كل مفهوم: مجال + اسم معروض + مرادفات بلهجات) بمطابقة عبارات أطول أولاً ثم كلمة ثم تصحيح خطأ إملائي واحد
     ← نوايا (مشاهدة/لعب/أكل/شرب/طلعة/شراء/سماع/قراءة) تُطبَّق على المفهوم التالي (مشاهدة + مباراة = متابعة مباراة، شراء + لعبة = تسوّق، لعب + كرة = رياضة)
     ← أُطر مرتبة بموضعها بالاسم (حتى 3) + المرافقون («مع الأهل/الربع») + الفرق المذكورة فعلاً (الغامض منها يحتاج سياق مباراة).
   • الصياغة: جزء لكل إطار يذكر الشيء نفسه («بالعافية على البيتزا»، «مشاهدة ممتعة للفلم») ثم ربط طبيعي بالواو، والمرافق بالنهاية؛ بلا اختراع (لا فرق/نتائج غير مكتوبة).
     الغامض ← عبارة عامة أنيقة تذكر اسم المكافأة نفسه. صياغة محايدة جنسياً قدر الإمكان.
   • التوسعة بلا إعادة بناء: CodisRewardVoice.extend({ domain, label, terms:[...], say:[...] }) أو extend({ domain, name, x:[...], n:[...] }). */
const CodisRewardVoice = (function(){
  'use strict';
  /* ---------- 1) التطبيع ---------- */
  const DIG = '٠١٢٣٤٥٦٧٨٩', DIG2 = '۰۱۲۳۴۵۶۷۸۹';
  function norm(s){
    s = String(s === undefined || s === null ? '' : s).toLowerCase();
    s = s.replace(/[ً-ٰٟۖ-ۭـ‌‍‎‏]/g, '');
    s = s.replace(/[٠-٩]/g, d=>String(DIG.indexOf(d))).replace(/[۰-۹]/g, d=>String(DIG2.indexOf(d)));
    s = s.replace(/[أإآٱ]/g, 'ا').replace(/[ىی]/g, 'ي').replace(/ة/g, 'ه').replace(/ؤ/g, 'و').replace(/ئ/g, 'ي').replace(/ء/g, '');
    s = s.replace(/[گک]/g, 'ك').replace(/چ/g, 'ج').replace(/پ/g, 'ب').replace(/ڤ/g, 'ف').replace(/ژ/g, 'ز');
    s = s.replace(/[^a-z0-9ء-ي]+/g, ' ');
    s = s.replace(/([ء-يa-z])\1{2,}/g, '$1');   /* «حلووو» ← «حلو» */
    return s.replace(/\s+/g, ' ').trim();
  }
  function stripAlWord(w){ return w.replace(/^(و|ف|ب|ل|ك)?ال(?=..)/, '').replace(/^لل(?=..)/, ''); }
  function variants(t){
    const v = [t]; let x = t;
    const m = /^(و|ف|ب|ل|ك)?ال(.{2,})$/.exec(t);
    if(m){ v.push('ال' + m[2]); v.push(m[2]); x = m[2]; }
    else if(/^لل.{2,}/.test(t)){ x = t.slice(2); v.push(x); }
    else if(/^[وفبلك].{3,}/.test(t)){ x = t.slice(1); v.push(x); }
    if(/^(رح|راح)./.test(x)) v.push(x.replace(/^(رح|راح)/, ''));
    [t, x].forEach(y=>{ if(y.length >= 4 && /^[انيتبهح]/.test(y)) v.push(y.slice(1)); });   /* اشوف/نشوف/بشوف/هاكل ← شوف/اكل */
    if(x.length > 4){
      const y = x.replace(/(ها|هم|نا|كم|ك|ه|ي)$/, ''); if(y !== x && y.length >= 3){ v.push(y); v.push(y + 'ه'); }
      if(/(ات|ين|ون)$/.test(x)){ const z = x.slice(0, -2); v.push(z); v.push(z + 'ه'); }
    }
    return v.filter((e, i)=>e && v.indexOf(e) === i);
  }
  const STOP = new Set(norm('مع ويا وي ويه وياهم ويانا وياي ويه و في فد على عل من الى لل ساعه ساعتين ساعات دقيقه دقايق دقائق نص نصف ربع كامل كامله شوي شويه بس كلش جدا مره حق مال مالت ماله بالبيت بيت عندي عدنا ثاني هم اني انا احنا اريد ابي ابغى بدي عايز حابب حاب the a an with and of for to time وقت').split(' '));

  /* ---------- 2) المجالات وقوالبها ---------- */
  const DOM = {
    eat:{ name:'أكل', x:['بالعافية على {x}', 'صحتين وعافية على {x}', '{x} بالهنا والشفا', 'ألف عافية على {x}'], n:['بالعافية', 'صحتين وعافية', 'بالهنا والشفا', 'شهيّة طيبة وألف عافية'] },
    sweet:{ name:'حلو', x:['بالعافية على {x}', '{x} على القلب حلاوة', 'صحتين على {x}، الله يحلّيها'], n:['الله يحلّيها عليك', 'حلاوة على القلب وبالعافية'] },
    drink:{ name:'مشروب', x:['{x} على المزاج', 'بالعافية على {x}', 'صحتين على {x}'], n:['مشروب على المزاج', 'صحتين وعلى المزاج'] },
    watch:{ name:'مشاهدة', x:['مشاهدة ممتعة {lx}', 'فرجة حلوة {lx}', 'وقت ممتع ويا {x}'], n:['مشاهدة ممتعة', 'فرجة حلوة وسهرة رايقة', 'مشاهدة ممتعة ووقت رايق'] },
    match:{ name:'مباراة', n:['مشاهدة ممتعة للمباراة', 'ماتش ممتع وأعصاب هادية', 'مباراة حلوة، والله يوفّق الفريق اللي تشجّعه', 'فرجة حلوة للماتش، ونتمنى الفوز للفريق اللي تشجّعه'],
      t1:['مشاهدة ممتعة، والله يوفّق {t}', 'ماتش ممتع، ونتمنى الفوز {lt}', 'الله يوفّق {t}، ومشاهدة ممتعة'], t2:['مباراة نارية بين {t1} و{t2}، ومشاهدة ممتعة', '{t1} ضد {t2}… ماتش ممتع وأعصاب هادية'] },
    sport:{ name:'رياضة', x:['الله يعطيك العافية على {x}'], n:['الله يعطيك العافية', 'تمرين موفق وهمّة عالية', 'نشاط وهمّة وصحة'] },
    games:{ name:'لعب', x:['لعب ممتع {bx}', 'جولة {x} موفقة', 'حظ سعيد {bx}، والفوز إلك'], n:['لعب ممتع والفوز إلك', 'جولات موفقة وتحدي حلو', 'لعب ممتع ووقت حلو'] },
    sleep:{ name:'نوم', n:['نومة هنية', 'نوم العافية وأحلام حلوة', 'نومة مريحة وصحوة نشيطة'] },
    rest:{ name:'راحة', n:['راحة مستحقة', 'راحة بال وهدوء', 'استرخاء وراحة بال'] },
    dayoff:{ name:'عطلة', n:['عطلة سعيدة', 'يوم إلك بلا شغل ولا هم', 'إجازة مستحقة وأيام حلوة'] },
    outing:{ name:'طلعة', x:['وقت حلو {bx}'], n:['طلعة موفقة', 'كزدرة حلوة', 'طلعة حلوة وترجع بالسلامة'] },
    travel:{ name:'سفر', n:['سفرة سعيدة وترجع بالسلامة', 'رحلة سعيدة وذكريات حلوة', 'سفر موفق وأيام حلوة'] },
    gather:{ name:'لمّة', n:['لمّة حلوة', 'سهرة هنية والضحك ما يخلص', 'قعدة حلوة الله يديمها'] },
    companion:{ name:'ويا', x:['وقت حلو ويا {x}', 'الله يديم اللمّة ويا {x}', 'أحلى شي إنها ويا {x}'], solo:['وقت حلو ويا {x}', 'لمّة حلوة ويا {x}، الله يديمها'] },
    shopping:{ name:'تسوّق', x:['مبروك {x}', 'مبروك عليك {x}، بالهنا', '{x} مبروك وبالهنا'], n:['تسوّق موفق ومشتريات حلوة', 'تسوّق موفق وبالهنا'] },
    learn:{ name:'تعلّم', n:['قراءة ممتعة', 'وقت مفيد ومعلومة جديدة', 'تعلّم موفق'] },
    music:{ name:'موسيقى', x:['عزف حلو على {x}'], n:['أغاني على المزاج', 'طرب ومزاج رايق', 'موسيقى تريّح الروح'] },
    cook:{ name:'طبخ', n:['طبخة موفقة ونكهة مضبوطة', 'طبخة حلوة وبالعافية مقدماً'] },
    art:{ name:'رسم', n:['إبداع موفق وألوان حلوة', 'لوحة حلوة وإبداع'] },
    photo:{ name:'تصوير', n:['لقطات حلوة وإبداع', 'تصوير موفق ولقطات تستاهل'] },
    write:{ name:'كتابة', n:['كتابة ملهمة', 'أفكار حلوة وقلم سيّال'] },
    craft:{ name:'شغل يدوي', n:['شغلة حلوة بإيدك', 'إبداع يدوي موفق'] },
    garden:{ name:'زراعة', n:['زراعة مثمرة', 'زرع أخضر وبال رايق'] },
    cars:{ name:'سيارة', x:['مشوار حلو {bx}'], n:['مشوار حلو بالسيارة', 'سواقة ممتعة وطريق سالك'] },
    pets:{ name:'أليف', n:['وقت حلو ويا حيوانك الأليف', 'لعب ودلع للأليف'] },
    care:{ name:'عناية', n:['عناية مستحقة', 'دلع بمحله وراحة'] },
    celebrate:{ name:'مناسبة', n:['فرحة حلوة ووقت ممتع', 'مناسبة سعيدة وفرحة تتم'] },
    sm:{ name:'سوشل', x:['وقت ممتع على {x}', 'سكرول ممتع على {x}'], n:['تصفّح ممتع', 'سكرول على المزاج'] },
    chat:{ name:'سوالف', n:['سوالف حلوة', 'مكالمة حلوة وسوالف تطوّل'] },
    smoke:{ name:'استراحة', n:['استراحة قصيرة ومزاج رايق'] },
    money:{ name:'مصروف', n:['مصروف مبارك وينصرف بمحله', 'رزق مبارك'] },
    free:{ name:'وقت حر', n:['وقت إلك بلا التزامات', 'وقتك إلك وعلى كيفك'] }
  };
  const GENERIC = { named:['«{name}» صارت إلك، بالهنا', 'بالهنا عليك «{name}»', '«{name}»… مكافأة مستحقة وبالهنا'], plain:['بالهنا والسرور', 'مكافأة مستحقة، وبالهنا', 'تعبك ما راح، وهاي ثمرته'] };
  const TIMED = ['بدأ وقتك', 'الوقت بدأ', 'انطلق العدّاد'];
  const SAY = {
    'eat/الفطور':['فطور هني وبداية يوم حلوة', 'فطور بالعافية'], 'eat/الغدا':['غدا هني وعافية', 'غدا بالعافية'], 'eat/العشا':['عشا هني وعافية', 'عشا بالعافية'],
    'eat/المطعم':['قعدة مطعم حلوة وبالعافية'], 'eat/الطلبية':['بالعافية، والطلبية توصل حارّة'], 'eat/المسكوف':['مسكوف على أصوله، بالعافية'], 'eat/الباجة':['باجة على أصولها، بالعافية'],
    'drink/الشاي':['استكان شاي على المزاج', 'شاي يعدّل المزاج'], 'drink/القهوة':['قهوة على المزاج', 'فنجان قهوة يصحصح الراس'], 'drink/الكافيه':['قعدة كافيه رايقة', 'كافيه ومزاج حلو'], 'drink/العصير':['عصير بارد وبالعافية'],
    'watch/الفلم':['فلم ممتع وسهرة حلوة', 'مشاهدة ممتعة للفلم'], 'watch/المسلسل':['حلقات ممتعة', 'عسى الحلقة تشدّك'], 'watch/الأنمي':['حلقات أنمي ممتعة'], 'watch/السينما':['سينما ممتعة وشاشة كبيرة'], 'watch/الوثائقي':['وثائقي ممتع ومعلومة جديدة'],
    'match/الكلاسيكو':['كلاسيكو ممتع وأعصاب هادية'], 'match/الديربي':['ديربي ناري ومشاهدة ممتعة'],
    'sport/الطوبة':['طوبة حلوة والأهداف إلك', 'لعب موفق بالملعب'], 'sport/الجيم':['تمرين قوي ونتايج أقوى', 'الله يعطيك العافية على التمرين'], 'sport/المشي':['خطوات خفيفة ونفَس طويل', 'مشية حلوة وصحة'],
    'sport/السباحة':['سباحة ممتعة ومي باردة'], 'sport/الدراجة':['مشوار دراجة ممتع'],
    'sleep/القيلولة':['قيلولة ترد الروح', 'غفوة خفيفة وصحوة نشيطة'],
    'outing/البحر':['وقت حلو عالبحر'], 'outing/الشط':['قعدة حلوة عالشط'], 'outing/المول':['كزدرة حلوة بالمول'], 'outing/الحديقة':['وقت حلو بالحديقة'], 'outing/الصيد':['صيد وفير ورزق حلو'],
    'outing/الكشتة':['كشتة حلوة وسهرة تحت النجوم'], 'outing/الملاهي':['وقت مرح بالملاهي'], 'outing/الشمال':['طلعة حلوة للشمال وجو يرد الروح'],
    'shopping/الهدية':['هدية تفرّح القلب'],
    'learn/الكتاب':['قراءة ممتعة وصفحات تستاهل'], 'learn/الكورس':['تعلّم موفق ومعلومة جديدة'], 'learn/البودكاست':['حلقة ممتعة ومفيدة'], 'learn/اللغة':['كلمة جديدة كل يوم، وتعلّم موفق'],
    'care/الحلاقة':['حلاقة نظيفة وطلّة جديدة'], 'care/المساج':['مساج يرد الروح', 'راحة للجسم والروح'], 'care/العناية':['عناية مستحقة ودلع بمحله'],
    'celebrate/عيد الميلاد':['حفلة عيد ميلاد حلوة وفرحة كبيرة'], 'celebrate/العيد':['عيد مبارك وأيام سعيدة'], 'celebrate/التخرج':['فرحة التخرج تتم، وعقبال الأعلى'], 'celebrate/الزواج':['فرحة تتم على خير'],
    'celebrate/الحفلة':['حفلة حلوة ووقت ممتع'], 'celebrate/النجاح':['نجاح يستاهل الاحتفال'], 'smoke/الأركيلة':['قعدة أركيلة رايقة']
  };
  /* ---------- 3) القاموس: «الاسم المعروض=مرادف,مرادف;…» — «-» = بلا اسم معروض · «~» قبل المرادف = غامض (فريق يحتاج سياق مباراة) ---------- */
  const LEX = {
    eat:'البرجر=برجر,بركر,برغر,همبرغر,همبركر,هامبرغر,برجرات,burger;البيتزا=بيتزا,بيتزه,بيزا,pizza;الشاورما=شاورما,شاورمه,شورمه,shawarma;الكباب=كباب,كبابات,معلاك,kebab;التكة=تكه,تكا;المشاوي=مشاوي,مشويات,grill,bbq,باربكيو;' +
      'الدجاج=دجاج,جاج,فراخ,دجاجه;البروستد=بروستد,بروستيد,كرسبي,زنجر,ناكتس,نكتس,nuggets;المسكوف=مسكوف,سمك مسكوف;السمك=سمك,سمج,اسماك,fish;البرياني=برياني;الكبسة=كبسه,مجبوس;المندي=مندي,حنيذ;القوزي=قوزي,غوزي;' +
      'الدولمة=دولمه,ضولمه,دولما,محشي,يبرق;الكبة=كبه,كبب,كبه حلب;الباجة=باجه,باتشه,كوارع;التشريب=تشريب,ثريد;القيمة=قيمه;الفلافل=فلافل,طعميه,فلافيل;السندويش=سندويج,سندويش,ساندويج,ساندويتش,صمونه,لفه,sandwich;' +
      'الباستا=باستا,معكرونه,مكرونه,سباكيتي,سباغيتي,بشاميل,pasta;السوشي=سوشي,sushi;النودلز=نودلز,اندومي,noodles;الستيك=ستيك,steak;البطاطا=بطاطا,بطاطس,فرايز,جبس,شبس,fries,chips;الفشار=فشار,بوب كورن,popcorn,شاميه;' +
      'المكسرات=مكسرات,كرزات;الكص=كص,دونر;الفطائر=فطيره,فطاير,معجنات,سمبوسه,منقوشه,مناقيش;الكنتاكي=كنتاكي,kfc;الماكدونالدز=ماكدونالدز,مكدونالدز,mcdonalds;الشوربة=شوربه,حساء;السلطة=سلطه,سلطات,فتوش,تبوله;' +
      'الفواكه=فواكه,فاكهه,بطيخ,رقي,موز,مانجو,عنب;الكيمر=كيمر,قيمر,قشطه;-=اكله,اكلات,وجبه,وجبات,طعام,meal,food,اكله دسمه;الفطور=فطور,ريوك,صبوحي,برانش,فطار,breakfast;الغدا=غدا,غداء,lunch;العشا=عشا,عشاء,عشوه,dinner;' +
      'المطعم=مطعم,مطاعم,restaurant;الطلبية=ديليفري,دليفري,توصيل,طلبات,طلبيه,delivery',
    sweet:'الكيك=كيك,كيكه,كعكه,cake;الشوكولاتة=شوكولاته,شوكلت,شوكولا,جكليت,جوكليت,chocolate,نوتيلا;الآيس كريم=ايس كريم,ايسكريم,موطه,دوندرمه,بوظه,جيلاتي,مثلجات,icecream;الكنافة=كنافه;البقلاوة=بقلاوه,باقلاوه;' +
      'الدونات=دونات,donut;الكليجة=كليجه,معمول;الزلابية=زلابيه,لقيمات,عوامه,داطلي;الكوكيز=كوكيز,بسكوت,بسكت,كوكي,cookies;الوافل=وافل,waffle;الكريب=كريب,crepe;البان كيك=بان كيك,بانكيك,pancake;' +
      'التشيز كيك=تشيز كيك,تشيزكيك,cheesecake;المحلبي=كاسترد,محلبي,مهلبيه,رز بحليب,بودينغ;-=حلويات,حلوى,حلو,سويت,ديزرت,dessert,حلاوه,من السما',
    drink:'الشاي=جاي,شاي,چاي,استكان,tea,كرك;القهوة=قهوه,كهوه,coffee,كوفي,نسكافيه,نسكافي,لاتيه,لاتي,كابتشينو,كابوتشينو,اسبريسو,موكا,امريكانو,ترك,سبانش لاتيه;العصير=عصير,عصاير,عصائر,juice,ليمون,شربت;' +
      'الموهيتو=موهيتو,mojito;الميلك شيك=ميلك شيك,ميلكشيك,سموذي,smoothie,فرابيه,فرابتشينو;-=مشروب,مشروبات,بيبسي,ببسي,كولا,كوكا,سفن,ميرندا,غازيه,ستنج,ردبول,ريدبول,مشروب طاقه;' +
      'الكافيه=كافيه,كافي,كوفي شوب,مقهى,مقهي,جايخانه,قهوه شعبيه,ستاربكس,starbucks,cafe',
    watch:'الفلم=فلم,فيلم,افلام,فلمين,movie,film;المسلسل=مسلسل,مسلسلات,حلقه,حلقات,سيزون,series,دراما,كيدراما;الأنمي=انمي,انيمي,anime,مانجا,مانغا,ون بيس,ناروتو;الكارتون=كارتون,كرتون,رسوم متحركه,cartoon,ديزني;' +
      'السينما=سينما,سنما,cinema,imax,ايماكس;الوثائقي=وثائقي,وثائقيات,documentary;نتفلكس=نتفلكس,نتفليكس,netflix;شاهد=شاهد vip;البرنامج=برنامج,برامج,show;البث=ستريم,بث مباشر,لايف,twitch,تويتش',
    match:'-=مباراه,مبارات,مباريات,ماتش,ماتشات,match,دوري,الدوري,دوري ابطال,ابطال اوروبا,تشامبيونز,كاس العالم,كاس اسيا,كاس الخليج,مونديال,نهائي,نص نهائي,اليورو,خليجي;الكلاسيكو=كلاسيكو,clasico;الديربي=ديربي,derby',
    team:'ريال مدريد=ريال مدريد,~الريال,~ريال,real madrid,~مدريد;برشلونة=برشلونه,برشا,بارسا,barcelona,barca;ليفربول=ليفربول,liverpool;مانشستر سيتي=مان سيتي,مانشستر سيتي,~السيتي;مانشستر يونايتد=مان يونايتد,مانشستر يونايتد,~اليونايتد;' +
      'أرسنال=ارسنال,arsenal;تشيلسي=تشيلسي,chelsea;بايرن ميونخ=بايرن,بايرن ميونخ,bayern;يوفنتوس=يوفنتوس,اليوفي,juventus;ميلان=~ميلان,milan;إنتر=~انتر,inter milan;باريس سان جيرمان=باريس سان جيرمان,psg;' +
      'المنتخب العراقي=المنتخب العراقي,منتخب العراق,اسود الرافدين,منتخبنا,~العراق;الزوراء=الزوراء;القوة الجوية=القوه الجويه,~الجويه;الشرطة=~الشرطه;الطلبة=~الطلبه;الهلال=~الهلال;النصر=~النصر;الاتحاد=~الاتحاد;الأهلي=~الاهلي;الزمالك=الزمالك',
    sport:'الطوبة=طوبه,كره قدم,~كره,فوتبول,football,خماسي,خماسيات,فوتسال,سباعي;الجيم=جيم,نادي رياضي,حديد,كمال اجسام,gym,تمرين,تمارين,workout,كارديو,لياقه,كروسفت,crossfit;' +
      'المشي=مشي,تمشي,هروله,ركض,جري,running,walk,جوكينغ;السباحة=سباحه,مسبح,swimming,pool;البادل=بادل,padel,تنس,tennis,تنس طاوله,بنج بونج;السلة=كره سله,باسكت,basketball;الطائرة=كره طايره,فولي,volleyball;' +
      'الدراجة=دراجه,بايسكل,بسكليت,سيكل,bike,cycling;اليوغا=يوغا,yoga,تامل,بيلاتس,pilates;الملاكمة=ملاكمه,بوكس,boxing,كيك بوكسنغ,كاراتيه,تايكوندو,جوجيتسو,مصارعه;-=رياضه,sport,sports',
    games:'-=العاب,لعبه,كيم,كيمز,كيمنك,كيمنج,game,games,gaming,جيمنج,قيمز;البلايستيشن=بلايستيشن,بلاستيشن,بليستيشن,بلي ستيشن,بلاي ستيشن,سوني,ps,ps4,ps5,playstation;الإكس بوكس=اكس بوكس,اكسبوكس,xbox;' +
      'السويتش=نينتندو,سويتش,nintendo,switch;ببجي=ببجي,pubg;فري فاير=فري فاير,freefire,free fire;فورتنايت=فورتنايت,فورت نايت,fortnite;فيفا=فيفا,fifa,fc24,fc25,اي فوتبول,بيس,pes,efootball;' +
      'كول أوف ديوتي=كول اوف ديوتي,cod,وارزون,warzone;ماينكرافت=ماينكرافت,ماين كرافت,minecraft;روبلوكس=روبلوكس,roblox;جي تي أي=جاتا,جي تي اي,gta;فالورانت=فالورانت,valorant;ليج أوف ليجندز=ليج اوف ليجندز,league of legends;' +
      'كلاش=كلاش,كلاش اوف كلانس,clash;ألعاب الكمبيوتر=بي سي,pc,steam,ستيم;الدومينو=دومينو,دومنه;الطاولي=طاولي,طاوله زهر,زهر,باكمون,نرد;الشطرنج=شطرنج,chess;الورق=ورق لعب,لعب ورق,كونكان,بلوت,تريكس,اونو,uno;' +
      'المحيبس=محيبس,محيبسي;البولينغ=بولنغ,بولينج,bowling;البلياردو=بليارد,بلياردو,سنوكر,snooker',
    sleep:'-=نوم,نومه,نايم,رقاد,ارقد,اتمدد,sleep;القيلولة=قيلوله,غفوه,نومه الظهر,nap',
    rest:'-=راحه,استراحه,استرخاء,استرخا,ريلاكس,relax,تشل,chill,هدوء,كسل,تكاسل',
    dayoff:'-=عطله,اجازه,يوم اوف,اوف,off,day off,ويكند,weekend,بدون دوام,يوم راحه,يوم كسل',
    outing:'-=طلعه,طلعات,كزدره,مشوار,مشاوير,فسحه,خروجه,خرجه,روحه,نزهه,تمشايه,outing;البحر=بحر,شاطي,شاطئ,بيج,beach;الشط=شط,دجله,الفرات,نهر,كورنيش;المول=مول,مولات,mall;الحديقة=حديقه,منتزه,متنزه,بارك,park;' +
      'الصيد=صيد,صيد سمك,رحله صيد,سناره;الكشتة=كشته,كمب,كامب,camp,camping,تخييم,بريه,طلعه بر;الملاهي=ملاهي,مدينه العاب,مدينه الالعاب,العاب مائيه,اكوا بارك;الشمال=الشمال,كردستان,اربيل,دهوك,السليمانيه,شقلاوه,جبل,جبال,شلال',
    travel:'-=سفر,سفره,رحله,رحلات,ترافل,travel,trip,سياحه',
    gather:'-=لمه,قعده,جلسه,سهره,عزيمه,عزومه,دعوه,زياره,ديوانيه,تجمع,اجتماع,gathering',
    companion:'الأصدقاء=اصدقاء,اصدقائي,الشباب,شباب,الربع,ربعي,الجماعه,جماعه,اصحاب,صحاب,صحابي,خلان,الكروب,كروب,رفاق,صديق,صديقي,صديقتي,صديقه,البنات,صاحبي,صاحبتي,friends;' +
      'الأهل=اهل,اهلي,عائله,عايله,عيله,بيت اهلي,امي,ابوي,بابا,ماما,اخوي,اختي,اخواني,خواتي,جدتي,جدي,عمي,خالي,family;اللي تحب=حبيبي,حبيبتي,زوجي,زوجتي,مرتي,خطيبي,خطيبتي,partner;الأطفال=اطفال,الجهال,جهال,ولادي,اولادي,الصغار,kids',
    shopping:'-=تسوق,شوبنك,شوبنج,شوبينغ,shopping,تبضع,مشتريات;الملابس=ملابس,هدوم,تيشيرت,تيشرت,قميص,بنطرون,بنطلون,جينز,دشداشه,عبايه,فستان,جاكيت,ستره,clothes;الحذاء=حذاء,قندره,كندره,جوتي,سنيكرز,shoes,بوت;' +
      'الشنطة=شنطه,جنطه,حقيبه,bag;العطر=عطر,عطور,برفان,بارفان,perfume,بخور;الموبايل=موبايل,تلفون,جوال,ايفون,iphone,سامسونك,سامسونج,phone;اللابتوب=لابتوب,لاب توب,laptop,ماك بوك,ايباد,تابلت,ipad;' +
      'السماعة=سماعه,سماعات,ايربودز,airpods,هيدفون,headphones;الساعة=ساعه يد,ساعه ذكيه,ابل واتش,apple watch,smartwatch;الهدية=هديه,هدايا,gift;الإكسسوارات=اكسسوار,اكسسوارات,خاتم,سوار,قلاده,نظاره,نظارات;' +
      'الطلبية=امازون,شي ان,علي اكسبريس,تيمو,اونلاين,online',
    learn:'-=قراءه,reading;الكتاب=كتاب,كتب,روايه,قصه,مجله,book,novel;الكورس=كورس,دوره,course,كورسات,محاضره,درس,ورشه;اللغة=لغه,لغات,~انكليزي,~انجليزي,~english,~فرنسي,~الماني,~كوري,~اسباني;البرمجة=برمجه,coding,programming;البودكاست=بودكاست,podcast',
    music:'-=موسيقى,موسيقي,اغاني,اغنيه,غنا,طرب,مقام,سماع,music,playlist,بلاي لست,سبوتيفاي,spotify,انغامي,anghami;العود=عزف عود,عود عزف,عزف;الجيتار=جيتار,كيتار,guitar;البيانو=بيانو,اورك,piano;الحفلة=كونسيرت,concert,حفله غنائيه',
    cook:'-=طبخ,اطبخ,طبخه,مطبخ,وصفه,cooking,اسوي اكل',
    art:'-=رسم,ارسم,تلوين,لوحه,خط عربي,تصميم,فن,art,drawing,painting',
    photo:'-=تصوير,كاميرا,photography',
    write:'-=كتابه,تدوين,يوميات,شعر,خواطر,writing',
    craft:'-=اشغال يدويه,خياطه,حياكه,كروشيه,تطريز,نجاره,ديكور,diy',
    garden:'-=زراعه,ازرع,نباتات,زرع',
    cars:'السيارة=سياره,سيارات,درفت,تفحيط,car,موتور,دراجه ناريه,غسل سياره',
    pets:'-=قطه,بزونه,بزون,كلب,طيور,حيوانات اليفه,اسماك زينه,pets',
    care:'الحلاقة=حلاقه,حلاق,زيان,barber;المساج=مساج,تدليك,سبا,spa,massage,حمام مغربي,ساونا,سونا,جاكوزي;العناية=عنايه,سكن كير,skincare,ماسك,بشره,مكياج,مناكير,مانيكير,باديكير,اظافر,صالون,كوافير',
    celebrate:'عيد الميلاد=عيد ميلاد,birthday,بيرثدي;العيد=عيد,عيديه,eid;التخرج=تخرج,حفل تخرج,graduation;الزواج=زواج,عرس,زفاف,خطوبه,ملجه,wedding;الحفلة=حفله,بارتي,party,احتفال;النجاح=نجاح,تفوق,انجاز,ترقيه',
    sm:'تيك توك=تيك توك,تكتوك,تيكتوك,tiktok;إنستغرام=انستا,انستغرام,انستقرام,انستكرام,instagram,insta,ريلز,reels;سناب=سناب,سناب شات,snapchat;يوتيوب=يوتيوب,يوتوب,youtube;إكس=تويتر,twitter;فيسبوك=فيسبوك,فيس,facebook;' +
      'واتساب=واتساب,واتس,whatsapp;تلغرام=تلغرام,تيليكرام,telegram;ديسكورد=ديسكورد,discord;السوشل ميديا=سوشل,سوشيال,سوشل ميديا,سوشيال ميديا,social media,مواقع التواصل,تصفح,سكرول,scroll,النت,انترنت',
    chat:'-=مكالمه,كول,فيديو كول,call,دردشه,سوالف,شات,chat',
    smoke:'الأركيلة=اركيله,نركيله,نرجيله,نارجيله,شيشه,معسل,hookah,shisha;السيجارة=سيجاره,سكاير,جكاره,جكايره,سجاير,دخان,تتن,cigarette;الفيب=فيب,vape',
    money:'-=مصروف,فلوس,خرجيه,مبلغ,كاش,دينار,دولار,money,راتب,بونص',
    free:'-=وقت حر,وقت فراغ,فراغ,وقت خاص,وقت لنفسي,me time,ساعه حره,بلا التزامات,وقت شخصي'
  };
  const INTENT = {
    watch:'مشاهده,شاهد,اشاهد,نشاهد,شوف,تفرج,اتفرج,فرجه,نتفرج,متابعه,اتابع,watch,watching',
    play:'لعب,العب,نلعب,play,playing',
    eat:'اكل,اكلي,ناكل,اتغدى,اتعشى,افطر,eat',
    drink:'شرب,اشرب,نشرب,drink',
    go:'اطلع,نطلع,اروح,نروح,اسافر',
    buy:'شراء,اشتري,نشتري,اشتريلي,اطلب,شري,buy,order',
    listen:'اسمع,نسمع,listen',
    read:'اقرا,نقرا,read'
  };
  const EXTRA = [];   /* إضافات extend */

  /* ---------- 4) الفهرس ---------- */
  let IDX = null;
  function build(){
    const map = new Map(), singles = []; let maxN = 1;
    const put = (key, e)=>{ if(!key) return; if(!map.has(key)) map.set(key, e); maxN = Math.max(maxN, key.split(' ').length); if(key.indexOf(' ') < 0 && key.length >= 4 && e.kind === 'c' && !e.c.amb) singles.push([key, e]); };
    const addTerm = (raw, e)=>{ const amb = raw.charAt(0) === '~', n = norm(raw.replace(/^~/, '')); if(!n) return; const ee = amb ? Object.assign({}, e, { c:Object.assign({}, e.c, { amb:true }) }) : e;
      put(n, ee); put(n.split(' ').map(stripAlWord).join(' '), ee); };
    const feed = (d, spec)=>String(spec).split(';').forEach(part=>{ const k = part.indexOf('='); if(k < 0) return; const lab = part.slice(0, k).trim(), terms = part.slice(k + 1).split(',');
      const e = { kind:'c', c:{ d:d, label:lab === '-' ? null : lab } }; terms.forEach(t=>addTerm(t.trim(), e)); if(lab !== '-' && d !== 'companion' && d !== 'team') addTerm(lab, e); });
    Object.keys(INTENT).forEach(k=>INTENT[k].split(',').forEach(t=>{ const n = norm(t); if(n && !map.has(n)) map.set(n, { kind:'i', intent:k }); }));
    ['companion'].concat(Object.keys(LEX).filter(d=>d !== 'companion')).forEach(d=>feed(d, LEX[d]));
    EXTRA.forEach(x=>{ (x.terms || []).forEach(t=>addTerm(String(t), { kind:'c', c:{ d:x.domain, label:x.label || null } })); });
    IDX = { map:map, singles:singles, maxN:Math.min(5, maxN) };
  }
  function extend(o){
    if(!o) return false;
    if(o.domain && (o.x || o.n || o.name) && !o.terms){ const d = DOM[o.domain] || (DOM[o.domain] = { name:o.name || o.domain, n:[] }); if(o.name) d.name = o.name; if(o.x) d.x = (d.x || []).concat(o.x); if(o.n) d.n = (d.n || []).concat(o.n); return true; }
    if(!o.domain || !Array.isArray(o.terms)) return false;
    if(!DOM[o.domain]) DOM[o.domain] = { name:o.name || o.domain, n:o.n || ['بالهنا'] };
    EXTRA.push({ domain:o.domain, label:o.label || null, terms:o.terms });
    if(o.say && o.label) SAY[o.domain + '/' + o.label] = (SAY[o.domain + '/' + o.label] || []).concat(o.say);
    IDX = null; return true;
  }
  function dist1(a, b){   /* هل المسافة ≤ 1 (حذف/إضافة/استبدال/تبديل متجاورين) */
    if(a === b) return true; const la = a.length, lb = b.length; if(Math.abs(la - lb) > 1) return false;
    let i = 0; while(i < la && i < lb && a[i] === b[i]) i++;
    if(la === lb){ if(a.slice(i + 1) === b.slice(i + 1)) return true; return a[i] === b[i + 1] && a[i + 1] === b[i] && a.slice(i + 2) === b.slice(i + 2); }
    return la > lb ? a.slice(i + 1) === b.slice(i) : a.slice(i) === b.slice(i + 1);
  }
  function look(k){ return k ? IDX.map.get(k) || null : null; }

  /* ---------- 5) التحليل ---------- */
  function analyze(name){
    if(!IDX) build();
    let src = String(name === undefined || name === null ? '' : name);
    try{ if(typeof CodisDuration !== 'undefined' && CodisDuration.strip){ const st = CodisDuration.strip(src); if(st && norm(st)) src = st; } }catch(e){}
    const text = norm(src), out = { norm:text, frames:[], companions:[], teams:[], ctx:null, conf:'none', tags:[] };
    if(!text) return out;
    const toks = text.split(' '), ms = [];
    for(let i = 0; i < toks.length;){
      let hit = null;
      for(let n = Math.min(IDX.maxN, toks.length - i); n >= 2 && !hit; n--){ const k = toks.slice(i, i + n).join(' '); const r = look(k) || look(k.split(' ').map(stripAlWord).join(' ')); if(r) hit = { r:r, n:n }; }
      if(!hit && !STOP.has(toks[i])){ const vs = variants(toks[i]); for(let j = 0; j < vs.length && !hit; j++){ const r = look(vs[j]); if(r) hit = { r:r, n:1 }; } }
      if(!hit && !STOP.has(toks[i]) && toks[i].length >= 5){ const w = stripAlWord(toks[i]); for(let j = 0; j < IDX.singles.length; j++){ const s = IDX.singles[j]; if(s[0].length >= 4 && s[0][0] === w[0] && dist1(w, s[0]) && !s[1].c.amb){ hit = { r:s[1], n:1, fuzzy:true }; break; } } }
      if(hit){ ms.push({ i:i, n:hit.n, e:hit.r }); i += hit.n; } else i++;
    }
    const frames = [], comps = [], teams = []; let pend = null;
    const iFrame = k=>({ d:{ watch:'watch', play:'games', eat:'eat', drink:'drink', go:'outing', buy:'shopping', listen:'music', read:'learn' }[k], labels:[], i:0 });
    function apply(f, k){
      if(k === 'watch'){ if(f.d === 'sport' || f.d === 'match'){ f.d = 'match'; f.labels = f.labels.filter(l=>l === 'الكلاسيكو' || l === 'الديربي'); } else if(f.d === 'games' && f.labels.length) f.d = 'watch'; }
      else if(k === 'play'){ if(f.d === 'match'){ f.d = 'sport'; f.labels = ['الطوبة']; } }
      else if(k === 'buy'){ if(f.d === 'games' || f.d === 'cars' || f.d === 'music' && f.labels.length){ f.d = 'shopping'; if(!f.labels.length) f.labels = ['اللعبة']; } }
      f.intent = k;
    }
    ms.forEach(m=>{
      if(m.e.kind === 'i'){ if(pend){ const pf = iFrame(pend.k); pf.i = pend.i; frames.push(pf); } pend = { k:m.e.intent, i:m.i }; return; }
      const c = m.e.c;
      if(c.d === 'companion'){ if(comps.indexOf(c.label) < 0) comps.push(c.label); return; }
      if(c.d === 'team'){ teams.push(c); return; }
      const f = { d:c.d, labels:c.label ? [c.label] : [], i:m.i, amb:!!c.amb };
      if(pend){ if(m.i - pend.i <= 3){ apply(f, pend.k); f.amb = false; } else { const pf = iFrame(pend.k); pf.i = pend.i; frames.push(pf); } pend = null; }
      frames.push(f);
    });
    if(pend){ const pf = iFrame(pend.k); pf.i = pend.i; frames.push(pf); }
    const hasMatch = ()=>frames.some(f=>f.d === 'match');
    const okTeams = teams.filter(t=>!t.amb || hasMatch() || frames.some(f=>f.d === 'sport' && !f.labels.length)), tl = [];
    okTeams.forEach(t=>{ if(tl.indexOf(t.label) < 0) tl.push(t.label); });
    if(tl.length){ if(!hasMatch()){ const sp = frames.findIndex(f=>f.d === 'sport'); if(sp > -1 && !frames[sp].labels.length) frames[sp].d = 'match'; else frames.push({ d:'match', labels:[], i:okTeams[0] ? 0 : 0 }); } }
    { const sure = frames.filter(f=>!f.amb).map(f=>f.d); for(let k = frames.length - 1; k >= 0; k--) if(frames[k].amb && sure.indexOf(frames[k].d) < 0) frames.splice(k, 1); }
    /* دمج نفس المجال بترتيب أول ظهور */
    const merged = [];
    frames.forEach(f=>{ const g = merged.find(x=>x.d === f.d); if(g){ f.labels.forEach(l=>{ if(g.labels.indexOf(l) < 0) g.labels.push(l); }); } else merged.push({ d:f.d, labels:f.labels.slice(), i:f.i }); });
    let fr = merged.filter(f=>DOM[f.d]);
    if(fr.length > 1) fr = fr.filter(f=>f.d !== 'free');
    if(fr.some(f=>f.d === 'games') && fr.some(f=>f.d === 'match') && !tl.length && !frames.some(f=>f.intent === 'watch')) fr = fr.filter(f=>f.d !== 'match');   /* «مباراة بلايستيشن» = لعبة */
    if(fr.some(f=>f.d === 'sleep')) fr = fr.filter(f=>f.d !== 'rest');
    if(fr.some(f=>f.d === 'outing') && fr.some(f=>f.d === 'travel')){ const o = fr.find(f=>f.d === 'outing'); if(o.labels.length) fr = fr.filter(f=>f.d !== 'travel'); else fr = fr.filter(f=>f.d !== 'outing'); }
    if(fr.some(f=>f.d === 'dayoff')) fr = fr.filter(f=>f.d !== 'rest');
    if(fr.some(f=>f.d === 'gather') && comps.length && fr.length > 1) fr = fr.filter(f=>f.d !== 'gather');
    fr = fr.slice(0, 3);
    out.frames = fr; out.companions = comps; out.teams = tl;
    out.ctx = fr.length ? fr[0].d : (comps.length ? 'companion' : null);
    out.conf = fr.length || comps.length ? (fr.length + (comps.length ? 1 : 0) > 1 ? 'multi' : 'clear') : 'none';
    out.tags = fr.map(f=>DOM[f.d].name).concat(comps.length ? ['ويا ' + joinAr(comps)] : []);
    return out;
  }

  /* ---------- 6) الصياغة ---------- */
  function joinAr(a){ return a.length <= 1 ? (a[0] || '') : a.slice(0, -1).join('، ') + ' و' + a[a.length - 1]; }
  function pre(p, x){ return /^ال/.test(x) ? (p === 'ل' ? 'لل' + x.slice(2) : p + x) : p + 'ـ' + x; }
  function fill(t, v){ return t.replace(/\{(\w+)\}/g, (m, k)=>(v[k] !== undefined ? v[k] : m)); }
  function fnv(s){ let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function mulberry(a){ return function(){ a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const RK = 'codis_voice_recent';
  function recentGet(){ try{ const a = JSON.parse(localStorage.getItem(RK) || '[]'); return Array.isArray(a) ? a : []; }catch(e){ return []; } }
  function recentPut(ids){ try{ const a = recentGet().concat(ids).slice(-40); localStorage.setItem(RK, JSON.stringify(a)); }catch(e){} }
  function compose(name, seed, o){
    o = o || {};
    try{
      const a = analyze(name), rng = mulberry(fnv(String(seed === undefined ? '' : seed) + '|' + a.norm)), recent = o.memo ? recentGet() : [], used = [];
      const pick = (arr, id)=>{ const ix = arr.map((_, i)=>i), fresh = ix.filter(i=>recent.indexOf(id + ':' + i) < 0), pool = fresh.length ? fresh : ix, k = pool[Math.floor(rng() * pool.length) % pool.length]; used.push(id + ':' + k); return arr[k]; };
      const vals = x=>({ x:x, lx:pre('ل', x), bx:pre('ب', x) });
      function frag(f){
        if(f.d === 'match'){
          const sp = f.labels.find(l=>SAY['match/' + l]);
          if(a.teams.length >= 2) return fill(pick(DOM.match.t2, 'm2'), { t1:a.teams[0], t2:a.teams[1] });
          if(a.teams.length === 1) return fill(pick(DOM.match.t1, 'm1'), { t:a.teams[0], lt:pre('ل', a.teams[0]) });
          if(sp) return pick(SAY['match/' + sp], 's:match/' + sp);
          return pick(DOM.match.n, 'n:match');
        }
        const D = DOM[f.d], L = f.labels;
        const said = L.filter(l=>SAY[f.d + '/' + l]), things = L.filter(l=>!SAY[f.d + '/' + l]);
        if(said.length && (!things.length || !D.x) && (L.length > 1 || !D.x || rng() < .65)) return pick(SAY[f.d + '/' + said[0]], 's:' + f.d + '/' + said[0]);
        if(L.length && D.x) return fill(pick(D.x, 'x:' + f.d), vals(joinAr(things.length ? things : L)));
        return pick(D.n, 'n:' + f.d);
      }
      let parts = a.frames.map(frag);
      while(parts.length > 1 && parts.join('، و').length > 78) parts.pop();   /* عبارة مقروءة: أهم الأشياء أولاً */
      if(a.companions.length){ const cx = joinAr(a.companions); parts.push(fill(pick(parts.length ? DOM.companion.x : DOM.companion.solo, parts.length ? 'cx' : 'cs'), { x:cx })); }
      let text;
      if(!parts.length){
        const nm = String(name || '').trim();
        text = nm && nm.length <= 26 && !o.timed ? fill(pick(GENERIC.named, 'gn'), { name:nm }) : pick(GENERIC.plain, 'gp');
      } else {
        text = parts[0]; for(let i = 1; i < parts.length; i++) text += '، و' + parts[i];
      }
      if(o.timed) text = pick(TIMED, 'tm') + '، ' + text;
      else if(parts.length === 1 && text.length < 34 && !/صبح|صباح|ليل|ظهر|عصر|مسا|فطور|ريوك|غدا|عشا|نوم|قيلول|سهر/.test(a.norm) && rng() < .3){ const h = (o.hour !== undefined ? o.hour : new Date().getHours()); text += h >= 5 && h < 12 ? '، ويومك حلو' : (h >= 18 || h < 3) ? '، وليلتك حلوة' : ''; }
      if(o.memo) recentPut(used);
      return { text:text, ctx:a.ctx, conf:a.conf, tags:a.tags, frames:a.frames, companions:a.companions, teams:a.teams, norm:a.norm };
    }catch(e){ return { text:o && o.timed ? 'بدأ وقتك، بالهنا' : 'بالهنا والسرور', ctx:null, conf:'error', tags:[], frames:[], companions:[], teams:[], norm:'' }; }
  }
  return { norm:norm, analyze:analyze, compose:compose, extend:extend, domains:()=>Object.keys(DOM), _dom:DOM };
})();
