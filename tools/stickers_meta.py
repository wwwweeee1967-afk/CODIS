# -*- coding: utf-8 -*-
"""CODIS-STICKERS — المصدر الوحيد لبيانات مكتبة الستيكرات (المعرّف · التصنيف · الاسم · الكلمات المفتاحية · وصف الرسم).
 الصور نفسها لا تُكتب هنا: ملف لكل ستيكر باسم معرّفه داخل assets/stickers/ (webp/png). أضف ستيكراً جديداً = سطر هنا + صورته، ثم py -3 tools/build_stickers.py"""

CATS = [   # (id, الاسم, كلمات بحث للتصنيف كله)
    ('food', 'أكل سريع', 'اكل وجبة طلب مطعم سريع'), ('iraqi', 'أكلات عراقية', 'اكل عراقي اكلة وجبة بيتي تراثي'),
    ('sweets', 'حلويات', 'حلويات حلو حلا سكر معجنات'), ('cold', 'مشروبات باردة', 'كلاص كوب كاس مشروب مشروبات عصير بارد ثلج'),
    ('tea', 'چاي وقهوة', 'كوب مشروب ساخن حار فنجان استكان كاس قعده'), ('out', 'طلعات', 'طلعة طلعات خروج برا تجربة'),
    ('rest', 'راحة', 'راحة استراحة دلال هدوء وقت'), ('games', 'ألعاب', 'لعبة العاب لعب ترفيه'),
    ('watch', 'أفلام ومحتوى', 'فلم فيلم مشاهدة مسلسل ترفيه محتوى'), ('create', 'هوايات', 'هواية هوايات ابداع فن'),
    ('shop', 'مشتريات', 'شراء مشتريات غرض تسوق'), ('care', 'عناية', 'عناية دلال اهتمام بالنفس'),
    ('social', 'أصدقاء وعائلة', 'اصدقاء عائلة اهل قعدة لمة'), ('learn', 'تعلّم', 'تعلم تطوير دراسة قراءة'),
    ('travel', 'سفر', 'سفر رحلة سياحة تغيير جو'), ('digital', 'رقمي', 'رقمي اشتراك تطبيق انترنت'),
    ('surprise', 'مفاجآت', 'مفاجأة هدية صندوق بوكس'), ('celebrate', 'احتفال', 'احتفال انجاز فرحة مناسبة'),
]

# (id, cat, الاسم العربي, كلمات مفتاحية عراقية/عربية/إنجليزية, وصف الرسم بالإنجليزية للمولّد, لوحة الألوان)
S = [
 # --- أكل سريع ---
 ('shawarma', 'food', 'لفة شاورمة', 'شاورمة شاورما لفة صاج رول دجاج لحم سندويچ ساندويش samoon shawarma wrap roll', 'a hand-drawn shawarma wrap half-unwrapped from crinkled paper, charred pita, pickles, lettuce and garlic sauce spilling out', 'warm toasted orange, cream, olive green'),
 ('burger', 'food', 'بركر', 'بركر برگر همبرغر دبل جيز تشيز burger cheeseburger', 'a tall double cheeseburger with sesame bun, melting cheese, tomato slices, lettuce, with a toothpick flag', 'mustard yellow, tomato red, bun brown'),
 ('pizza', 'food', 'بيتزا', 'بيتزا بيتزه جبن بيبروني خضرة شريحة pizza slice pepperoni', 'one pizza slice with stretching mozzarella strand, pepperoni discs and basil leaves on a checkered paper tray', 'tomato red, cheese gold, basil green'),
 ('fries', 'food', 'بطاطا مقلية', 'بطاطا بطاطس فرايز ودجز جبن chips fries potato wedges', 'a red paper cone overflowing with golden fries, a puddle of cheese sauce, salt sparkles', 'golden yellow, red stripes'),
 ('falafel', 'food', 'صمون فلافل', 'فلافل صمون عمبة طعمية falafel sandwich', 'a loaf of samoon bread stuffed with falafel balls, tahini drizzle, pickled turnip and tomato', 'bread tan, herb green, tahini cream'),
 ('fried_chicken', 'food', 'دجاج كرسبي', 'كريسبي زنجر مسحب دجاج مقلي بروستد fried chicken crispy zinger', 'a stack of crispy fried chicken drumsticks in a striped bucket with a hot pepper', 'crunchy amber, red and white stripes'),
 ('noodles', 'food', 'نودلز', 'نودلز نودلس اندومي معكرونة نودل حارة noodles ramen', 'a steaming bowl of spicy noodles with chopsticks lifting a twirl, a soft egg and chili flakes', 'chili red, broth brown, bowl indigo'),
 ('sambusa', 'food', 'سمبوسة', 'سمبوسة سمبوسك كبة مقلية مقرمشات فطائر samosa pastry', 'three golden triangular fried pastries with a lemon wedge and a dipping sauce cup', 'fried gold, lemon yellow, mint green'),
 # --- أكلات عراقية ---
 ('dolma', 'iraqi', 'دولمة', 'دولمة دولمه ورق عنب محشي صينية dolma stuffed grape leaves', 'a round copper tray of rolled vine-leaf dolma arranged in a spiral with onions and a lemon', 'copper, vine green, lemon'),
 ('kebab', 'iraqi', 'كباب وتكة', 'كباب تكة شيش مشاوي لحم فحم مشويات kebab tikka grill skewer', 'two long skewers of grilled kebab and tikka over glowing charcoal with grilled tomato and onion rings', 'charcoal black, ember orange, meat brown'),
 ('masgouf', 'iraqi', 'مسگوف', 'مسكوف مسگوف سمك سمچ شواء نهر دجلة masgouf fish carp', 'a butterflied carp fish standing by an open fire on wooden stakes, with tomatoes, onions and flatbread', 'fire orange, river blue, fish silver'),
 ('biryani', 'iraqi', 'برياني ورز', 'برياني ريزو رز تمن تمّن مندي مقلوبة صينية دجاج rice biryani mandi', 'a steaming platter of saffron rice heaped with roasted chicken, almonds and raisins, a ladle of broth beside it', 'saffron yellow, roast brown, white platter'),
 ('tashreeb', 'iraqi', 'تشريب', 'تشريب تشريب باقلاء باجة قيمة مرگة مرقة شوربة stew soup tashreeb', 'a deep clay bowl of tashreeb stew with torn bread soaking in rich red broth, chickpeas and herbs', 'terracotta, stew red, bread beige'),
 ('kubba', 'iraqi', 'كبة', 'كبة كبه حامض كبة موصلية كبة رز kubba kibbeh', 'a tray of oval kubba croquettes, one cut open to show spiced meat filling, beside a small bowl of pickles', 'golden brown, spice red, cream'),
 ('mandi_pot', 'iraqi', 'قدر بيتي', 'اكل بيتي مرگة بامية فاصوليا طبخة قدر ست البيت قوزي home cooking stew pot', 'a big dented cooking pot with lid ajar releasing steam, a wooden spoon, okra and tomatoes around it', 'pot silver-blue, okra green, tomato red'),
 # --- حلويات ---
 ('kunafa', 'sweets', 'كنافة', 'كنافة كنافه قشطة بالقشطة جبن فستق knafeh kunafa', 'a round tray of kunafa with golden shredded-pastry top, a slice lifted showing stretchy cheese, pistachio crumbs and syrup', 'deep gold, orange blossom syrup, pistachio green'),
 ('baklava', 'sweets', 'بقلاوة', 'بقلاوة بقلاوه زلابية قطايف لقيمات حلو شرقي baklava', 'a stack of diamond-shaped baklava with flaky layers, honey drizzle and chopped pistachios', 'honey amber, pistachio green, pastry cream'),
 ('cheesecake', 'sweets', 'تشيز كيك', 'تشيز كيك تشيزكيك كيك جبن فراولة cheesecake', 'a creamy cheesecake slice with a strawberry sauce top, a fork and a mint leaf on a small plate', 'cream white, strawberry red, plate blue'),
 ('donut', 'sweets', 'دونات', 'دونات دوناتس دونت كرزة رشات donut doughnut sprinkles', 'two glazed donuts, one pink frosted with colorful sprinkles and one chocolate, one with a bite taken', 'bubblegum pink, chocolate brown, confetti colors'),
 ('ice_cream', 'sweets', 'آيس كريم', 'ايس كريم آيس كريم بوظة بوزة جيلاتو كون icecream gelato cone', 'a waffle cone with three melting scoops in mismatched flavors, drips running down, a wafer stick', 'vanilla cream, strawberry pink, pistachio mint'),
 ('waffle', 'sweets', 'وافل وبان كيك', 'وافل بان كيك كريب نوتيلا عسل pancake waffle crepe nutella', 'a tall stack of fluffy pancakes with a butter pat, maple syrup flowing down, and berries on top', 'pancake tan, maple amber, berry blue'),
 ('croissant', 'sweets', 'كرواسون', 'كرواسون كرواسان معجنات سينابون مخبز فطور croissant pastry bakery', 'a flaky golden croissant on a bakery paper bag with a few crumbs and a wheat sprig', 'butter gold, paper bag brown, wheat yellow'),
 ('choco_cake', 'sweets', 'كيك شوكولاتة', 'كيك شوكلاته شوكولاتة براوني موس تيراميسو كوكيز chocolate cake brownie', 'a dark chocolate layer cake slice with glossy ganache, a cherry on top and a dusting of cocoa', 'cocoa brown, cherry red, cream filling'),
 ('rice_pudding', 'sweets', 'مهلبية ورز بحليب', 'مهلبية رز بحليب حلا بالحليب بودينغ مهلبيه pudding milk dessert', 'a small glass cup of milky pudding with cinnamon dust, rose petals and crushed nuts, with a tiny spoon', 'milk white, cinnamon tan, rose pink'),
 # --- مشروبات باردة ---
 ('iced_coffee', 'cold', 'آيس كوفي', 'ايس كوفي آيس كوفي قهوة باردة لاتيه ايس لاتيه فرابيه iced coffee latte frappe', 'a tall clear glass of iced coffee with visible milk layers swirling, ice cubes and a bent paper straw', 'coffee brown, milk cream, icy blue'),
 ('pomegranate', 'cold', 'عصير رمان', 'رمان عصير رمان عصير فريش juice pomegranate', 'a glass of ruby pomegranate juice beside a split pomegranate spilling jewel-like seeds', 'ruby red, deep magenta, leaf green'),
 ('orange_juice', 'cold', 'عصير برتقال', 'برتقال عصير برتقال فريش ليمون عصير حمضيات orange juice citrus', 'a juice glass of fresh orange juice with an orange slice on the rim and a halved orange with leaves', 'sunny orange, leaf green, white pulp'),
 ('mojito', 'cold', 'موهيتو وليمون', 'موهيتو ليمون نعناع ليمون نعناع سلاش آيس تي mojito lemonade mint', 'a highball glass of mojito packed with lime wheels, muddled mint leaves, crushed ice and a striped straw', 'lime green, mint teal, ice white'),
 ('milkshake', 'cold', 'ميلك شيك', 'ميلك شيك ميلكشيك شيك شوكولاتة فراولة milkshake shake', 'a tall diner-style milkshake with whipped cream swirl, a cherry, a long spoon and a straw', 'strawberry pink, whipped cream white, cherry red'),
 ('smoothie', 'cold', 'سموذي فواكه', 'سموذي سموثي فواكه كوكتيل عصير مانگو فراولة smoothie fruit mango', 'a blended smoothie jar with layered mango and berry, fruit chunks floating beside it', 'mango yellow, berry purple, fresh green'),
 ('coconut', 'cold', 'جوز هند', 'جوز هند ماء جوز الهند ماء جوزه قصب مشروب استوائي coconut water tropical', 'a whole green coconut with a hole and straw, a small umbrella and a hibiscus flower', 'coconut green, hibiscus red, sand beige'),
 # --- چاي وقهوة ---
 ('tea_glass', 'tea', 'استكان جاي', 'جاي چاي شاي استكان ستكان استكان جاي مهيل دارسين هيل عالفحم tea glass istikan', 'a curvy waisted glass istikan of amber tea on a small gilded saucer with a sugar cube, thin steam curls and cardamom pods', 'amber, gold rim, soft glass blue'),
 ('teapot', 'tea', 'قوري وسماور', 'قوري ابريق سماور جاي شاي قوري تقديم ابريق teapot kettle samovar', 'an ornate dark teapot with a curved spout on a charcoal brazier-style stand, steam, and two small glasses', 'brass gold, dark teal, ember glow'),
 ('arabic_coffee', 'tea', 'قهوة عربية', 'قهوة عربية قهوة تركية دلة فنجان هيل قهوة مرة arabic coffee dallah turkish coffee', 'a tall brass dallah coffee pot pouring into a tiny handleless finjan cup, dates and cardamom beside', 'brass, coffee brown, date maroon'),
 ('espresso', 'tea', 'إسبريسو وكابتشينو', 'اسبريسو كابتشينو لاتيه سبانش لاتيه قهوة بندق نسكافيه espresso cappuccino latte', 'a cappuccino cup seen from a slight angle with leaf latte art, a spoon and coffee beans scattered', 'espresso brown, foam cream, cup terracotta'),
 ('hot_choc', 'tea', 'هوت چوكليت', 'هوت شوكليت شوكولاتة ساخنة چوكليت كاكاو مارشميلو hot chocolate cocoa marshmallow', 'a chunky mug of hot chocolate topped with marshmallows and a cinnamon stick, wisps of steam', 'cocoa brown, marshmallow white, mug red'),
 ('cafe_table', 'tea', 'قعدة كافيه', 'كافيه قعدة كافيه مقهى قعدة هادئة فطور بكافيه cafe coffee shop sit', 'a tiny round cafe table with two cups, a croissant plate and a small vase with a flower, a chair back peeking in', 'cafe green, wood brown, cream'),
 ('tea_cardamom', 'tea', 'چاي بالهيل', 'هيل زعفران چاي بالهيل زعفران دارسين نكهة cardamom saffron tea spice', 'a small jar of green cardamom pods, saffron threads in a dish and a cinnamon stick laid around a tea glass', 'saffron orange, cardamom green, cinnamon brown'),
 # --- طلعات ---
 ('cinema', 'out', 'سينما', 'سينما فلم فيلم تذكرة فشار طلعة سينما cinema movie ticket popcorn', 'a striped popcorn box overflowing, two torn cinema tickets and a tiny film clapperboard without any writing', 'cinema red, popcorn butter, midnight blue'),
 ('bowling', 'out', 'بولينگ', 'بولينج بولينگ بولنك بليارد بلياردو كرات bowling billiards pins', 'a bowling ball mid-roll toward ten scattering pins with motion swooshes', 'lane wood, ball indigo, pin white-red'),
 ('park_picnic', 'out', 'حديقة ونزهة', 'حديقة نزهة بيكنك طلعة نهر تمشية غروب منتزه park picnic walk river', 'a checkered picnic blanket with a basket, a thermos and a tree casting soft shade, butterflies around', 'meadow green, gingham red, sky blue'),
 ('dinner_out', 'out', 'غدا وعشا بمطعم', 'مطعم غدا عشا فطور برا مطعم جديد وجبة فاخرة restaurant dinner dine out', 'a restaurant table with a candle, a covered silver cloche being lifted, wine-less glasses and folded napkin', 'candle gold, tablecloth navy, silver'),
 ('arcade', 'out', 'ألعاب أركيد', 'اركيد صالة ألعاب ملاهي مدينة ألعاب arcade amusement', 'a chunky retro arcade cabinet with a joystick and glowing pixel-like screen and a stack of tokens', 'neon violet, screen cyan, token gold'),
 ('mall_bag', 'out', 'مول وتسوق', 'مول تسوق زيارة مول جولة اسواق shopping mall bags', 'two paper shopping bags with ribbon handles tipping over, tissue paper sprouting out', 'bag pink, bag teal, tissue yellow'),
 # --- راحة ---
 ('armchair', 'rest', 'ساعة راحة', 'راحة استراحة ساعة راحة كرسي مريح ارجوحة هدوء جلسة استرخاء relax armchair rest', 'a cozy armchair with a plump cushion, a knitted blanket draped over and a small side table with a plant', 'calm sage green, wool cream, wood brown'),
 ('nap', 'rest', 'غفوة ونوم', 'غفوة نوم نومة قيلولة مخدة وسادة نوم مبچر نوم زيادة sleep nap pillow', 'a fluffy pillow with a sleeping crescent moon resting on it, tiny stars and floating zzz-shaped clouds without letters', 'night blue, moon yellow, pillow white'),
 ('bath', 'rest', 'حمام دافي', 'حمام دافئ استحمام سبا مياه فقاعات bath spa bubbles tub', 'a clawfoot bathtub brimming with bubbles, a rubber duck, rolled towel and a candle on the edge', 'bubble white, brass faucet, soft aqua'),
 ('no_phone', 'rest', 'بدون موبايل', 'بدون موبايل ساعة بدون موبايل هدوء وحدك فصل ديجيتال offline unplug phone', 'a smartphone resting face-down inside a small glass dome like a museum piece, a book and tea nearby', 'glass teal, dusk purple, paper cream'),
 ('sleep_in', 'rest', 'صباح بدون منبه', 'منبه صباح بدون منبه نومة زيادة الصبح تأخير يوم خفيف alarm clock sleep in', 'a retro twin-bell alarm clock wearing a tiny sleep mask on its face, with a sunbeam and a quilt corner', 'sunrise peach, clock mint, quilt coral'),
 ('candle_spa', 'rest', 'عناية بالبشرة', 'ماسك وجه سبا شمعة معطرة عناية بالبشرة ماسك face mask spa candle', 'a lit scented candle in a glass, a clay face mask bowl with a brush and cucumber slices', 'clay beige, candle amber, cucumber green'),
 # --- ألعاب ---
 ('gamepad', 'games', 'يد تحكم', 'لعبة يد تحكم بلايستيشن ايدي جهاز العاب كونسول gamepad console controller ps', 'a chunky game controller with colorful round buttons and a tiny sparkle trail, one thumbstick tilted', 'controller charcoal, button primary colors'),
 ('board_game', 'games', 'لعبة لوحية', 'العاب لوحية شطرنج طاولة دومينو ورق شدة لودو ليلة العاب board game chess dominoes cards', 'a board with chess pieces and a pair of dice, a fan of playing cards behind, a domino tile', 'wood brown, felt green, ivory'),
 ('handheld', 'games', 'لعبة موبايل', 'لعبة موبايل جهاز محمول لعبة جديدة شراء لعبة تحميل لعبة mobile game handheld', 'a handheld console with a glowing screen and a small pixel heart, a charging cable curled around it', 'console teal, screen lime, cable white'),
 ('puzzle', 'games', 'ألغاز', 'لغز بازل ألغاز جلسة الغاز تركيب puzzle jigsaw', 'a half-finished jigsaw puzzle with one piece floating in, mismatched pastel colored pieces', 'pastel mix, board brown'),
 ('headset', 'games', 'سماعة ألعاب', 'سماعة رأس سماعة العاب هيدفون هيدست جهاز اضافي headset gaming headphones', 'big over-ear gaming headphones with a curved mic and glowing ear cups', 'headset black, accent orange, glow cyan'),
 # --- أفلام ومحتوى ---
 ('tv_show', 'watch', 'مسلسل وحلقة', 'مسلسل حلقة تلفزيون شاشة ماراثون مسلسل نتفلكس فلم تلفزيون tv series show', 'a retro television set with rabbit-ear antennas, a blanket-covered couch edge and a bowl of snacks in front', 'tv wood, screen blue glow, blanket red'),
 ('movie_night', 'watch', 'ليلة أفلام', 'ليلة أفلام فلم سناك بروجكتر ليلة افلام movie night projector', 'a small film projector casting a beam on a screen with silhouettes of two snack bowls and a blanket', 'beam amber, dark room blue, popcorn gold'),
 ('podcast', 'watch', 'بودكاست وموسيقى', 'بودكاست موسيقى اغاني سماع سماعات راديو podcast music radio', 'a vintage microphone beside a vinyl record and floating music-note shapes, headphones hanging on it', 'mic chrome, vinyl black, note mint'),
 ('anime', 'watch', 'أنمي وكرتون', 'انمي كرتون رسوم متحركة ماراثون انمي anime cartoon', 'a bubbly cartoon-style character-less scene: a bowl of ramen with a speech-cloud-shaped steam and sparkle stars, manga-screentone dots', 'sakura pink, ramen orange, ink black'),
 # --- هوايات ---
 ('paint', 'create', 'جلسة رسم', 'رسم فرشاة الوان لوحة تلوين دفتر رسم paint palette brush draw', 'a wooden painter palette with dollops of color, two brushes crossed and a small canvas on an easel corner', 'palette wood, vivid pigments'),
 ('camera', 'create', 'تصوير', 'تصوير كاميرا صور طلعة تصوير ألبوم صور camera photo', 'a vintage film camera with a leather strap, a few instant photos fanning out, one with a tiny paper clip', 'camera black-silver, photo white, strap tan'),
 ('oud', 'create', 'عود وموسيقى', 'عود جيتار عزف موسيقى اغنية آلة oud guitar music instrument', 'a beautiful pear-shaped oud with a decorative rosette and bent neck, a few music-note swirls', 'oud wood amber, rosette cream, strings gold'),
 ('pottery', 'create', 'فخار وحرف', 'فخار يدوي كروشيه حرفة صناعة يدوية خط عربي pottery craft handmade crochet', 'a clay pot on a spinning wheel with wet hands shaping it, a ball of yarn and crochet hook beside', 'clay terracotta, yarn teal, wood brown'),
 # --- مشتريات ---
 ('gift_bag', 'shop', 'هدية صغيرة', 'هدية قطعة صغيرة اكسسوار مشتريات صغيرة ميدالية gift small treat accessory', 'a small kraft gift bag with tissue sprouting, a keychain charm and a tiny wrapped trinket beside', 'kraft brown, tissue pink, charm gold'),
 ('shoes', 'shop', 'حذاء وملابس', 'حذاء جزمة ملابس قميص بدلة ملابس جديدة shoes sneakers clothes', 'a pair of stylish sneakers with mismatched laces and a folded shirt with a hanger hook above', 'sneaker white-red, shirt denim blue'),
 ('wristwatch', 'shop', 'ساعة يد', 'ساعة يد ساعة اكسسوار محفظة شنطة حقيبة watch accessory', 'a classic wristwatch with a leather strap partly unrolled, gears peeking from the back and a small wallet', 'steel silver, strap brown, wallet navy'),
 ('backpack', 'shop', 'شنطة', 'شنطة حقيبة ظهر شنطة يومية حامل لابتوب backpack bag laptop', 'a rugged backpack with buckles and pockets, a laptop corner sticking out of the top flap', 'bag forest green, buckle brass, laptop silver'),
 # --- عناية ---
 ('perfume', 'care', 'عطر', 'عطر برفان بخور عود عطور لوشن perfume fragrance cologne', 'an elegant faceted perfume bottle with a bulb sprayer and a spray mist cloud with floating petals', 'bottle amber, mist lilac, petal rose'),
 ('hair_care', 'care', 'شعر وحلاقة', 'حلاقة قص شعر تسريحة مشط حلاق ترتيب شعر زيت haircut barber comb', 'a barber scene: scissors, a comb and a striped barber pole, a hand mirror reflecting a sparkle', 'barber red-blue stripe, steel, mirror silver'),
 ('skincare', 'care', 'كريم ولوشن', 'كريم لوشن مرطب عناية منتج عناية جلسة قدمين skincare cream lotion', 'a round jar of cream with a lid leaning beside it, a lotion tube and a soft towel roll, a daisy', 'cream pastel, towel mint, daisy yellow'),
 # --- أصدقاء وعائلة ---
 ('friends_cups', 'social', 'قعدة أصدقاء', 'اصدقاء قعدة سوالف ليلة سوالف شاي مع الاصدقاء جلسة friends hangout', 'three mismatched mugs clinking together over a low table with a plate of snacks and a speech-bubble shape (blank)', 'warm mix, table wood, bubble white'),
 ('phone_call', 'social', 'مكالمة', 'مكالمة اتصال تلفون شخص عزيز دردشة رسالة call phone chat', 'a retro telephone with a long curly cord forming a heart shape and a few small hearts drifting upward', 'phone teal, cord cream, heart pink'),
 ('family_table', 'social', 'غدا عائلي', 'عائلة اهل غدا عائلي سفرة مائدة لمة family lunch table', 'a big round table spread with shared dishes and a pot in the center, many hands reaching in (no faces)', 'tablecloth red-white, dishes varied, wood brown'),
 # --- تعلّم ---
 ('new_book', 'learn', 'كتاب جديد', 'كتاب جديد رواية قراءة مكتبة قراءة تخصصية مجلة book novel reading', 'an open book with aged pages, a ribbon bookmark, pressed leaf and ink-pen curls, a stack of two books beneath', 'paper sepia, ink blue, leaf green'),
 ('notebook', 'learn', 'دفتر وقلم', 'دفتر قلم قرطاسية دفتر تخطيط دفتر انيق stationery notebook pen planner', 'a leather-bound notebook with an elastic strap, a fountain pen and a few washi tapes and stickers', 'leather brown, ink navy, washi coral'),
 ('graduation', 'learn', 'دورة وتعلم', 'دورة تعلم لغة ورشة شهادة جامعة تطوير مهارة course learning graduation', 'a graduation cap resting on a stack of books with a small lightbulb and a rolled certificate (blank)', 'cap black, tassel gold, books maroon'),
 # --- سفر ---
 ('suitcase', 'travel', 'حقيبة سفر', 'سفر رحلة حقيبة سفرة ويكند سفرة يوم suitcase trip travel luggage', 'a vintage hard-shell suitcase covered with blank travel-label shapes, a passport shape and a sun hat on top', 'case teal, strap tan, hat straw'),
 ('camping', 'travel', 'تخييم ونزهة', 'تخييم خيمة طلعة برية كشتة مخيم نار camping tent bonfire', 'a small tent glowing from inside, a campfire with sparks and a few pine trees under a star sky', 'tent orange, night navy, fire gold'),
 ('landmark', 'travel', 'مكان سياحي', 'سياحة مكان سياحي متحف معرض زيارة مدينة فندق landmark museum hotel', 'a stylized domed building with arches and a minaret-like tower, a tiny bridge and a map pin shape', 'sandstone, dome turquoise, sky pale blue'),
 # --- رقمي ---
 ('subscription', 'digital', 'اشتراك رقمي', 'اشتراك شهر اشتراك منصة تطبيق برنامج اداة رقمية subscription app streaming', 'a floating glowing app-card with a play triangle and a cloud, small key and calendar page shapes orbiting', 'screen glow violet, cloud white, key gold'),
 ('ebook', 'digital', 'كتاب إلكتروني', 'كتاب الكتروني تابلت قراءة رقمية اشتراك قراءة ebook tablet reader', 'a tablet showing blank text lines resting against a stack of paper books with a cozy mug', 'tablet slate, paper cream, mug orange'),
 # --- مفاجآت ---
 ('mystery_box', 'surprise', 'بوكس مفاجأة', 'مفاجأة بوكس صندوق هدية مفاجأة عشوائي صندوق سناكات mystery box surprise', 'a mysterious box with a big question-mark-shaped keyhole glow (no letters), ribbons springing out and confetti', 'box violet, glow gold, ribbon pink'),
 ('wrapped_gift', 'surprise', 'هدية ملفوفة', 'هدية لنفسك هدية تغليف شريط علبة هدية gift wrapped present ribbon', 'a wrapped present with a big ribbon bow, curly ribbon tails and a handful of falling confetti', 'wrap red, ribbon gold, confetti mix'),
 ('treasure', 'surprise', 'صندوق كنز', 'كنز صندوق كنز ذهب جواهر عملات كنز treasure chest gold coins gems', 'an old wooden treasure chest overflowing with coins and gems with a skeleton-key lying in front', 'chest wood, gold, gem green-blue'),
 # --- احتفال ---
 ('trophy', 'celebrate', 'كأس إنجاز', 'كأس انجاز جائزة بطولة نجاح فوز ميدالية trophy award winner medal', 'a gleaming golden trophy cup with laurel wreath and a star on a small pedestal, light rays behind', 'trophy gold, laurel green, ray yellow'),
 ('fireworks', 'celebrate', 'ألعاب نارية', 'احتفال العاب نارية فرحة طلعة احتفالية مناسبة fireworks celebration party', 'a night sky bursting with a cluster of colorful fireworks over a tiny skyline silhouette', 'night navy, firework mix'),
 ('party_cake', 'celebrate', 'كيكة احتفال', 'كيكة حفلة عيد ميلاد شمعة بالونات حفلة مناسبة birthday party cake balloons', 'a small layered celebration cake with lit candles, a party hat and a bunch of balloons tied to it', 'cake pink-white, balloons bright mix, candle flame'),
]

# ---- أسلوب الهوية العام: يُلصق قبل وصف كل ستيكر في ملف المطالبات ----
STYLE = ("Modern vintage paper cartoon sticker, premium collectible sticker style, antique illustration feel: hand-drawn cartoon linework with slightly uneven ink outlines, "
         "aged paper grain and subtle halftone/letterpress print texture, rich saturated colors, a thick die-cut white border around the subject with a soft paper drop shadow, "
         "slightly tilted composition, centered single subject, fully transparent background, square 1024x1024, high detail that still reads clearly at 96 px.")
NEGATIVE = ("NO text of any kind: no letters, no numbers, no Arabic or English words, no logos, no watermarks, no labels, no captions, no signatures. "
            "Not a photo, not realistic, not a flat app icon, not an emoji. One subject only, no contact sheet, no grid, no background scene rectangle.")
