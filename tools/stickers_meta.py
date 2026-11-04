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
 ('hot_dog', 'food', 'هوت دوك', 'هوت دوك هوتدوك نقانق سجق سوسج صمونة hot dog sausage', 'a grilled hot dog in a soft bun with a wavy mustard line', 'bun gold, sausage red, mustard yellow'),
 ('taco', 'food', 'تاكو', 'تاكو تاكوز مكسيكي تورتيلا لحم taco mexican tortilla', 'a crunchy taco shell packed with seasoned meat, lettuce, tomato and cheese', 'shell yellow, lettuce green, tomato red'),
 ('sandwich', 'food', 'سندويچ توست', 'سندويچ سندويش ساندويچ توست كلوب لفة sandwich club toast', 'a triangle toast club sandwich stacked with ham, cheese, lettuce and tomato', 'toast brown, lettuce green, tomato red'),
 # --- أكلات عراقية ---
 ('dolma', 'iraqi', 'دولمة', 'دولمة دولمه ورق عنب محشي صينية dolma stuffed grape leaves', 'a round copper tray of rolled vine-leaf dolma arranged in a spiral with onions and a lemon', 'copper, vine green, lemon'),
 ('kebab', 'iraqi', 'مشاوي كباب', 'كباب شيش مشاوي لحم فحم مشويات kebab grill skewer', 'four long skewers of grilled minced-meat kebab, glossy and charred', 'charcoal black, ember orange, meat brown'),
 ('tikka', 'iraqi', 'مشاوي تكة', 'تكة تكه تكة لحم تكة دجاج شيش مشاوي فحم مشويات tikka grill skewer cubes', 'four skewers of grilled meat cubes (tikka) with charred edges', 'ember orange, meat brown, wood tan'),
 ('masgouf', 'iraqi', 'مسگوف', 'مسكوف مسگوف سمك سمچ شواء نهر دجلة masgouf fish carp', 'a butterflied carp fish standing by an open fire on wooden stakes, with tomatoes, onions and flatbread', 'fire orange, river blue, fish silver'),
 ('biryani', 'iraqi', 'برياني ورز', 'برياني ريزو رز تمن تمّن مندي مقلوبة صينية دجاج rice biryani mandi', 'a steaming platter of saffron rice heaped with roasted chicken, almonds and raisins, a ladle of broth beside it', 'saffron yellow, roast brown, white platter'),
 ('tashreeb', 'iraqi', 'تشريب', 'تشريب تشريب باقلاء باجة قيمة مرگة مرقة شوربة stew soup tashreeb', 'a deep clay bowl of tashreeb stew with torn bread soaking in rich red broth, chickpeas and herbs', 'terracotta, stew red, bread beige'),
 ('kubba', 'iraqi', 'كبة', 'كبة كبه حامض كبة موصلية كبة رز kubba kibbeh', 'a tray of oval kubba croquettes, one cut open to show spiced meat filling, beside a small bowl of pickles', 'golden brown, spice red, cream'),
 ('mandi_pot', 'iraqi', 'قدر بيتي', 'اكل بيتي مرگة بامية فاصوليا طبخة قدر ست البيت قوزي home cooking stew pot', 'a big dented cooking pot with lid ajar releasing steam, a wooden spoon, okra and tomatoes around it', 'pot silver-blue, okra green, tomato red'),
 ('lunch', 'iraqi', 'صحن غدا', 'غدا غداء صحن غدا وجبة تمن ولحم كباب رز سلطة وجبة كاملة lunch plate meal rice', 'a full lunch plate: grilled meat, rice, salad and fried vegetables', 'meat brown, rice white, salad green'),
 # --- حلويات ---
 ('kunafa', 'sweets', 'كنافة', 'كنافة كنافه قشطة بالقشطة جبن فستق knafeh kunafa', 'a round tray of kunafa with golden shredded-pastry top, a slice lifted showing stretchy cheese, pistachio crumbs and syrup', 'deep gold, orange blossom syrup, pistachio green'),
 ('baklava', 'sweets', 'بقلاوة', 'بقلاوة بقلاوه زلابية قطايف لقيمات حلو شرقي baklava', 'a stack of diamond-shaped baklava with flaky layers, honey drizzle and chopped pistachios', 'honey amber, pistachio green, pastry cream'),
 ('cheesecake', 'sweets', 'تشيز كيك', 'تشيز كيك تشيزكيك كيك جبن فراولة cheesecake', 'a creamy cheesecake slice with a strawberry sauce top, a fork and a mint leaf on a small plate', 'cream white, strawberry red, plate blue'),
 ('donut', 'sweets', 'دونات', 'دونات دوناتس دونت كرزة رشات donut doughnut sprinkles', 'two glazed donuts, one pink frosted with colorful sprinkles and one chocolate, one with a bite taken', 'bubblegum pink, chocolate brown, confetti colors'),
 ('ice_cream', 'sweets', 'آيس كريم', 'ايس كريم آيس كريم بوظة بوزة جيلاتو كون icecream gelato cone', 'a waffle cone with three melting scoops in mismatched flavors, drips running down, a wafer stick', 'vanilla cream, strawberry pink, pistachio mint'),
 ('waffle', 'sweets', 'وافل', 'وافل وافلز كريب نوتيلا عسل waffle crepe nutella', 'stacked golden waffles with syrup and fresh berries on top', 'waffle gold, maple amber, berry red-blue'),
 ('pancakes', 'sweets', 'بان كيك', 'بان كيك بانكيك بنكيك فطائر عسل شيرة فطور pancake pancakes', 'a tall stack of fluffy pancakes with syrup and berries on top', 'pancake tan, maple amber, berry red'),
 ('croissant', 'sweets', 'كرواسون', 'كرواسون كرواسان معجنات سينابون مخبز فطور croissant pastry bakery', 'a flaky golden croissant on a bakery paper bag with a few crumbs and a wheat sprig', 'butter gold, paper bag brown, wheat yellow'),
 ('choco_cake', 'sweets', 'كيك شوكولاتة', 'كيك شوكلاته شوكولاتة براوني موس تيراميسو كوكيز chocolate cake brownie', 'a dark chocolate layer cake slice with glossy ganache, a cherry on top and a dusting of cocoa', 'cocoa brown, cherry red, cream filling'),
 ('rice_pudding', 'sweets', 'مهلبية ورز بحليب', 'مهلبية رز بحليب حلا بالحليب بودينغ مهلبيه pudding milk dessert', 'a small glass cup of milky pudding with cinnamon dust, rose petals and crushed nuts, with a tiny spoon', 'milk white, cinnamon tan, rose pink'),
 ('cupcake', 'sweets', 'كب كيك', 'كب كيك كبكيك كيكة صغيرة مافن cupcake muffin', 'a chocolate cupcake topped with a pink cream swirl and a cherry', 'cream pink, chocolate brown, cherry red'),
 ('cake_slice', 'sweets', 'كيك فراولة', 'كيك كيكة كيكه فراولة قطعة كيك تورتة cake strawberry slice', 'a layered sponge cake slice with strawberry cream and a fresh strawberry on top', 'sponge cream, strawberry red'),
 ('cookie', 'sweets', 'كوكيز', 'كوكيز كوكي بسكت بسكويت شوكولاتة cookie biscuit', 'a big golden cookie studded with chocolate chips', 'golden brown, chocolate'),
 ('macaron', 'sweets', 'ماكرون', 'ماكرون ماكارون حلو فرنسي macaron', 'a plump pink macaron with a cream filling', 'raspberry pink, cream'),
 ('chocolate_bar', 'sweets', 'لوح شوكولاتة', 'شوكولاتة شوكولاته شكولاته جكليت چكليت كاكاو لوح chocolate bar', 'a dark chocolate bar half unwrapped from crinkled gold foil', 'chocolate brown, foil gold'),
 # --- مشروبات باردة ---
 ('iced_coffee', 'cold', 'آيس كوفي', 'ايس كوفي آيس كوفي قهوة باردة لاتيه ايس لاتيه فرابيه iced coffee latte frappe', 'a tall clear glass of iced coffee with visible milk layers swirling, ice cubes and a bent paper straw', 'coffee brown, milk cream, icy blue'),
 ('pomegranate', 'cold', 'عصير رمان', 'رمان عصير رمان عصير فريش juice pomegranate', 'a glass of ruby pomegranate juice beside a split pomegranate spilling jewel-like seeds', 'ruby red, deep magenta, leaf green'),
 ('orange_juice', 'cold', 'عصير برتقال', 'برتقال عصير برتقال فريش ليمون عصير حمضيات orange juice citrus', 'a juice glass of fresh orange juice with an orange slice on the rim and a halved orange with leaves', 'sunny orange, leaf green, white pulp'),
 ('mojito', 'cold', 'موهيتو وليمون', 'موهيتو ليمون نعناع ليمون نعناع سلاش آيس تي mojito lemonade mint', 'a highball glass of mojito packed with lime wheels, muddled mint leaves, crushed ice and a striped straw', 'lime green, mint teal, ice white'),
 ('milkshake', 'cold', 'ميلك شيك', 'ميلك شيك ميلكشيك شيك شوكولاتة فراولة milkshake shake', 'a tall diner-style milkshake with whipped cream swirl, a cherry, a long spoon and a straw', 'strawberry pink, whipped cream white, cherry red'),
 ('smoothie', 'cold', 'سموذي فواكه', 'سموذي سموثي فواكه كوكتيل عصير مانگو فراولة smoothie fruit mango', 'a blended smoothie jar with layered mango and berry, fruit chunks floating beside it', 'mango yellow, berry purple, fresh green'),
 ('coconut', 'cold', 'جوز هند', 'جوز هند ماء جوز الهند ماء جوزه قصب مشروب استوائي coconut water tropical', 'a whole green coconut with a hole and straw, a small umbrella and a hibiscus flower', 'coconut green, hibiscus red, sand beige'),
 ('soda', 'cold', 'مشروب غازي', 'ببسي بيبسي كولا مشروب غازي غازية سفن كوكا بارد pepsi cola soda soft drink', 'a red paper soda cup with a lid and a striped straw', 'soda red, white swirl'),
 # --- چاي وقهوة ---
 ('tea_glass', 'tea', 'استكان جاي', 'جاي چاي شاي استكان ستكان استكان جاي مهيل دارسين هيل عالفحم tea glass istikan', 'a curvy waisted glass istikan of amber tea on a small gilded saucer with a sugar cube, thin steam curls and cardamom pods', 'amber, gold rim, soft glass blue'),
 ('teapot', 'tea', 'قوري وسماور', 'قوري ابريق سماور جاي شاي قوري تقديم ابريق teapot kettle samovar', 'an ornate dark teapot with a curved spout on a charcoal brazier-style stand, steam, and two small glasses', 'brass gold, dark teal, ember glow'),
 ('arabic_coffee', 'tea', 'قهوة عربية', 'قهوة عربية قهوة تركية دلة فنجان هيل قهوة مرة arabic coffee dallah turkish coffee', 'a tall brass dallah coffee pot pouring into a tiny handleless finjan cup, dates and cardamom beside', 'brass, coffee brown, date maroon'),
 ('espresso', 'tea', 'إسبريسو وكابتشينو', 'اسبريسو كابتشينو لاتيه سبانش لاتيه قهوة بندق نسكافيه espresso cappuccino latte', 'a cappuccino cup seen from a slight angle with leaf latte art, a spoon and coffee beans scattered', 'espresso brown, foam cream, cup terracotta'),
 ('hot_choc', 'tea', 'هوت چوكليت', 'هوت شوكليت شوكولاتة ساخنة چوكليت كاكاو مارشميلو hot chocolate cocoa marshmallow', 'a chunky mug of hot chocolate topped with marshmallows and a cinnamon stick, wisps of steam', 'cocoa brown, marshmallow white, mug red'),
 ('cafe_table', 'tea', 'قعدة كافيه', 'كافيه قعدة كافيه مقهى قعدة هادئة فطور بكافيه cafe coffee shop sit', 'a tiny round cafe table with two cups, a croissant plate and a small vase with a flower, a chair back peeking in', 'cafe green, wood brown, cream'),
 ('tea_cardamom', 'tea', 'چاي بالهيل', 'هيل زعفران چاي بالهيل زعفران دارسين نكهة cardamom saffron tea spice', 'a small jar of green cardamom pods, saffron threads in a dish and a cinnamon stick laid around a tea glass', 'saffron orange, cardamom green, cinnamon brown'),
 ('coffee_togo', 'tea', 'قهوة تيك أوي', 'قهوة كوفي تيك اوي تيك أواي كوب قهوة لاتيه امريكانو coffee to go takeaway latte', 'a takeaway coffee cup with a brown lid and a coffee-bean sleeve', 'kraft brown, cream'),
 # --- طلعات ---
 ('cinema', 'out', 'سينما', 'سينما فلم فيلم تذكرة فشار طلعة سينما cinema movie ticket popcorn', 'a striped popcorn box overflowing, two torn cinema tickets and a tiny film clapperboard without any writing', 'cinema red, popcorn butter, midnight blue'),
 ('bowling', 'out', 'بولينگ', 'بولينج بولينگ بولنك بليارد بلياردو كرات bowling billiards pins', 'a bowling ball mid-roll toward ten scattering pins with motion swooshes', 'lane wood, ball indigo, pin white-red'),
 ('park_picnic', 'out', 'حديقة ونزهة', 'حديقة نزهة بيكنك طلعة نهر تمشية غروب منتزه park picnic walk river', 'a checkered picnic blanket with a basket, a thermos and a tree casting soft shade, butterflies around', 'meadow green, gingham red, sky blue'),
 ('dinner_out', 'out', 'غدا وعشا بمطعم', 'مطعم غدا عشا فطور برا مطعم جديد وجبة فاخرة restaurant dinner dine out', 'a restaurant table with a candle, a covered silver cloche being lifted, wine-less glasses and folded napkin', 'candle gold, tablecloth navy, silver'),
 ('arcade', 'out', 'ألعاب أركيد', 'اركيد صالة ألعاب ملاهي مدينة ألعاب arcade amusement', 'a chunky retro arcade cabinet with a joystick and glowing pixel-like screen and a stack of tokens', 'neon violet, screen cyan, token gold'),
 ('mall_bag', 'out', 'مول وتسوق', 'مول تسوق زيارة مول جولة اسواق shopping mall bags', 'two paper shopping bags with ribbon handles tipping over, tissue paper sprouting out', 'bag pink, bag teal, tissue yellow'),
 ('theater', 'out', 'مسرح', 'مسرح مسرحية عرض كوميديا ستاند اب theater show play comedy', 'golden comedy and silver tragedy masks side by side', 'mask gold, silver grey'),
 # --- راحة ---
 ('armchair', 'rest', 'ساعة راحة', 'راحة استراحة ساعة راحة كرسي مريح ارجوحة هدوء جلسة استرخاء relax armchair rest', 'a cozy armchair with a plump cushion, a knitted blanket draped over and a small side table with a plant', 'calm sage green, wool cream, wood brown'),
 ('nap', 'rest', 'نوم', 'غفوة نوم نومة قيلولة مخدة وسادة نوم مبچر نوم زيادة sleep nap pillow', 'a cozy wooden bed with blue blanket and pillows', 'wood brown, blanket blue, pillow white'),
 ('cat_nap', 'rest', 'غفوة وكسل', 'غفوة قيلولة كسل يوم كسل تمدد بزونة قطة نومة خفيفة lazy nap cat', 'a tabby cat curled up asleep on a round cushion with zzz', 'tabby orange, cushion navy'),
 ('bath', 'rest', 'حمام دافي', 'حمام دافئ استحمام سبا مياه فقاعات bath spa bubbles tub', 'a clawfoot bathtub brimming with bubbles, a rubber duck, rolled towel and a candle on the edge', 'bubble white, brass faucet, soft aqua'),
 ('no_phone', 'rest', 'بدون موبايل', 'بدون موبايل ساعة بدون موبايل هدوء وحدك فصل ديجيتال offline unplug phone', 'a smartphone resting face-down inside a small glass dome like a museum piece, a book and tea nearby', 'glass teal, dusk purple, paper cream'),
 ('sleep_in', 'rest', 'صباح بدون منبه', 'منبه صباح بدون منبه نومة زيادة الصبح تأخير يوم خفيف alarm clock sleep in', 'a retro twin-bell alarm clock wearing a tiny sleep mask on its face, with a sunbeam and a quilt corner', 'sunrise peach, clock mint, quilt coral'),
 ('candle_spa', 'rest', 'عناية بالبشرة', 'ماسك وجه سبا شمعة معطرة عناية بالبشرة ماسك face mask spa candle', 'a lit scented candle in a glass, a clay face mask bowl with a brush and cucumber slices', 'clay beige, candle amber, cucumber green'),
 # --- ألعاب ---
 ('gamepad', 'games', 'يد تحكم', 'لعبة يد تحكم بلايستيشن ايدي جهاز العاب كونسول gamepad console controller ps', 'a chunky game controller with colorful round buttons and a tiny sparkle trail, one thumbstick tilted', 'controller charcoal, button primary colors'),
 ('board_game', 'games', 'شطرنج', 'شطرنج العاب لوحية لعبة لوحية ورق شدة لودو ليلة العاب board game chess cards', 'a wooden chess board with ivory and black pieces', 'wood brown, ivory, black'),
 ('domino', 'games', 'دومينو', 'دومينو دومنة دومنه حجار دومينو ليلة العاب domino dominoes', 'three ivory domino tiles standing together', 'ivory, black dots'),
 ('backgammon', 'games', 'طاولي', 'طاولي طاولة طاوله زهر نرد محبوسة board backgammon tavla dice', 'an open wooden backgammon board with checkers', 'wood brown, red, ivory'),
 ('handheld', 'games', 'لعبة موبايل', 'لعبة موبايل جهاز محمول لعبة جديدة شراء لعبة تحميل لعبة mobile game handheld', 'a handheld console with a glowing screen and a small pixel heart, a charging cable curled around it', 'console teal, screen lime, cable white'),
 ('puzzle', 'games', 'ألغاز', 'لغز بازل ألغاز جلسة الغاز تركيب puzzle jigsaw', 'a half-finished jigsaw puzzle with one piece floating in, mismatched pastel colored pieces', 'pastel mix, board brown'),
 ('headset', 'games', 'سماعة ألعاب', 'سماعة رأس سماعة العاب هيدفون هيدست جهاز اضافي headset gaming headphones', 'big over-ear gaming headphones with a curved mic and glowing ear cups', 'headset black, accent orange, glow cyan'),
 ('football', 'games', 'كرة قدم', 'طوبة كرة قدم ملعب مباراة فوتبول ساحة football soccer match', 'a classic black and white leather football', 'leather white, black'),
 ('basketball', 'games', 'كرة سلة', 'كرة سلة باسكت باسكيت ملعب basketball', 'an orange basketball with deep black seams', 'basketball orange, black'),
 ('billiards', 'games', 'بليارد', 'بليارد سنوكر طاولة كرة ٨ ثمانية billiards snooker pool', 'a glossy black eight ball', 'gloss black, white'),
 ('darts', 'games', 'سهام دارت', 'دارت سهام رمي هدف لوحة darts', 'a dartboard with two darts in the bullseye area', 'board black, cream, red and green'),
 # --- أفلام ومحتوى ---
 ('tv_show', 'watch', 'مسلسل وحلقة', 'مسلسل حلقة تلفزيون شاشة ماراثون مسلسل نتفلكس فلم تلفزيون tv series show', 'a retro television set with rabbit-ear antennas, a blanket-covered couch edge and a bowl of snacks in front', 'tv wood, screen blue glow, blanket red'),
 ('movie_night', 'watch', 'ليلة أفلام', 'ليلة أفلام فلم سناك بروجكتر ليلة افلام movie night projector', 'a small film projector casting a beam on a screen with silhouettes of two snack bowls and a blanket', 'beam amber, dark room blue, popcorn gold'),
 ('podcast', 'watch', 'بودكاست', 'بودكاست سماع راديو مايك حلقة صوتية podcast radio mic', 'a vintage microphone beside a vinyl record and floating music-note shapes, headphones hanging on it', 'mic chrome, vinyl black, note mint'),
 ('music', 'watch', 'موسيقى', 'موسيقى اغاني اغنية سماع اغاني بلاي لست طرب نوتة music songs playlist', 'golden treble clef and floating music notes', 'gold, amber'),
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
 ('sports_car', 'shop', 'سيارة', 'سيارة سياره سيارة رياضية موتر car sports car', 'a red sports car with white racing stripes', 'racing red, white stripes'),
 ('diamond', 'shop', 'ألماسة', 'الماس ماس الماسة مجوهرات ذهب خاتم حلي diamond jewelry', 'a brilliant cut blue diamond sparkling', 'ice blue, white sparkle'),
 # --- عناية ---
 ('perfume', 'care', 'عطر', 'عطر برفان بخور عود عطور لوشن perfume fragrance cologne', 'an elegant faceted perfume bottle with a bulb sprayer and a spray mist cloud with floating petals', 'bottle amber, mist lilac, petal rose'),
 ('hair_care', 'care', 'شعر وحلاقة', 'حلاقة قص شعر تسريحة مشط حلاق ترتيب شعر زيت haircut barber comb', 'a barber scene: scissors, a comb and a striped barber pole, a hand mirror reflecting a sparkle', 'barber red-blue stripe, steel, mirror silver'),
 ('skincare', 'care', 'كريم ولوشن', 'كريم لوشن مرطب عناية منتج عناية جلسة قدمين skincare cream lotion', 'a round jar of cream with a lid leaning beside it, a lotion tube and a soft towel roll, a daisy', 'cream pastel, towel mint, daisy yellow'),
 # --- أصدقاء وعائلة ---
 ('friends_cups', 'social', 'قعدة أصدقاء', 'اصدقاء قعدة سوالف ليلة سوالف شاي مع الاصدقاء جلسة friends hangout', 'three mismatched mugs clinking together over a low table with a plate of snacks and a speech-bubble shape (blank)', 'warm mix, table wood, bubble white'),
 ('phone_call', 'social', 'مكالمة', 'مكالمة اتصال تلفون شخص عزيز دردشة رسالة call phone chat', 'a retro telephone with a long curly cord forming a heart shape and a few small hearts drifting upward', 'phone teal, cord cream, heart pink'),
 ('family_table', 'social', 'غدا عائلي', 'عائلة اهل غدا عائلي سفرة مائدة لمة family lunch table', 'a big round table spread with shared dishes and a pot in the center, many hands reaching in (no faces)', 'tablecloth red-white, dishes varied, wood brown'),
 ('rose', 'social', 'وردة', 'ورد وردة ورود باقة ورد جوري هدية rose flowers bouquet', 'a single deep red rose with a green leaf', 'rose red, leaf green'),
 # --- تعلّم ---
 ('new_book', 'learn', 'كتاب جديد', 'كتاب جديد رواية قراءة مكتبة قراءة تخصصية مجلة book novel reading', 'an open book with aged pages, a ribbon bookmark, pressed leaf and ink-pen curls, a stack of two books beneath', 'paper sepia, ink blue, leaf green'),
 ('notebook', 'learn', 'دفتر وقلم', 'دفتر قلم قرطاسية دفتر تخطيط دفتر انيق stationery notebook pen planner', 'a leather-bound notebook with an elastic strap, a fountain pen and a few washi tapes and stickers', 'leather brown, ink navy, washi coral'),
 ('graduation', 'learn', 'دورة وتعلم', 'دورة تعلم لغة ورشة شهادة جامعة تطوير مهارة course learning graduation', 'a graduation cap resting on a stack of books with a small lightbulb and a rolled certificate (blank)', 'cap black, tassel gold, books maroon'),
 # --- سفر ---
 ('suitcase', 'travel', 'حقيبة سفر', 'سفر رحلة حقيبة سفرة ويكند سفرة يوم suitcase trip travel luggage', 'a vintage hard-shell suitcase covered with blank travel-label shapes, a passport shape and a sun hat on top', 'case teal, strap tan, hat straw'),
 ('camping', 'travel', 'تخييم ونزهة', 'تخييم خيمة طلعة برية كشتة مخيم نار camping tent bonfire', 'a small tent glowing from inside, a campfire with sparks and a few pine trees under a star sky', 'tent orange, night navy, fire gold'),
 ('landmark', 'travel', 'مكان سياحي', 'سياحة مكان سياحي متحف معرض زيارة مدينة فندق landmark museum hotel', 'a stylized domed building with arches and a minaret-like tower, a tiny bridge and a map pin shape', 'sandstone, dome turquoise, sky pale blue'),
 ('compass', 'travel', 'بوصلة', 'بوصلة مغامرة استكشاف رحلة اتجاه compass adventure', 'an antique brass pocket compass with a red and gold needle', 'brass gold, parchment'),
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
 ('medal', 'celebrate', 'ميدالية', 'ميدالية وسام انجاز فوز مركز اول medal', 'a gold star medal hanging from a red and white ribbon', 'medal gold, ribbon red'),
 ('crown', 'celebrate', 'تاج', 'تاج ملك ملكي يوم ملكي vip crown king', 'a royal red velvet crown with gold arches and jewels', 'velvet red, gold, jewels'),
 # --- CODIS-STICKERS-13 (13 ستيكراً جديداً) ---
 ('social_media', 'digital', 'سوشال ميديا', 'سوشال ميديا سوشيال سوشل مواقع التواصل تواصل اجتماعي انستغرام انستا تيك توك تكتوك يوتيوب تلكرام تلغرام فيسبوك سناب تصفح سكرول مشاهدة ريلز social media instagram tiktok youtube telegram scroll', 'a cluster of four glossy rounded social-app tiles (camera-gradient, music-note, play button, paper plane) with a small golden crown on top', 'gradient pink-orange, black, red, sky blue'),
 ('cigarettes', 'shop', 'سكائر', 'سكائر سجائر سيجارة سيكارة سجاير سكاير جكارة جكاره دخان تدخين تبغ علبة سكائر علبة دخان cigarettes cigarette smoke smoking tobacco pack', 'an open red cigarette pack with a gold crown mark and a few cigarettes sticking out, two loose cigarettes lying in front', 'pack red, filter orange, paper white'),
 ('jummar_palm', 'iraqi', 'جمّار نخيل', 'جمار جمارة جمار نخيل جمار النخلة قلب النخلة قلب النخل قلب نخل نخلة نخل نخيل خضرة نخلة عراقي بصرة palm heart hearts of palm jummar jumar', 'a freshly cut white palm heart (jummar): a tender cream-colored cylinder of layered sheaths with ribbed texture, a few green palm fronds behind it', 'cream white, pale green, palm green'),
 ('lettuce_head', 'iraqi', 'خس', 'خس خسة راس خس رأس خس ورق خس سلطة خضار خضرة اخضر سلطه lettuce salad romaine greens vegetable', 'a fresh green lettuce head with crisp ruffled leaves and visible pale ribs', 'leaf green, light lime, rib cream'),
 ('iraqi_samoon', 'iraqi', 'صمون عراقي', 'صمون صموني صمونة خبز صمون عراقي خبز رغيف فطور مخبز تنور سمون samoon samoun iraqi bread loaf', 'golden Iraqi samoon diamond-shaped loaves with crisp crust and sesame flecks, stacked in a woven basket', 'bread golden, crust brown, basket tan'),
 ('pickles', 'iraqi', 'طرشي', 'طرشي تورشي مخلل مخللات مخلل خيار مخلل عراقي طرشي عراقي مرطبان خيار مملح فلفل مخلل pickles pickle turshi jar cucumber', 'a glass jar packed with pickled cucumbers, peppers and carrots under a red lid, with a few loose pickles beside it', 'pickle green, pepper red, carrot orange'),
 ('mushrooms', 'food', 'فطر', 'فطر فطريات مشروم مشرم شامبينيون فطر ابيض فطر طازج mushroom mushrooms champignon', 'a group of fresh white button mushrooms, whole and sliced, with parsley leaves', 'cream white, brown cap, parsley green'),
 ('shish_shawarma', 'food', 'شيش شاورما', 'شيش شاورما شاورمة شاورما شيش سيخ شاورما شاورما عمودي سيخ لحم شاورما دجاج شاورما لحم شواء مشويات دوّار doner spit shawarma shish rotisserie', 'a tall vertical rotating shawarma spit of stacked seasoned meat roasting over flames, with a wrapped shawarma sandwich in front', 'roast orange, flame yellow, wrap cream'),
 ('chicken_tikka_rice', 'iraqi', 'تكة دجاج وتمن', 'تكة دجاج تكه دجاج تمن رز تمّن صحن تمن دجاج مشوي دجاج مشوي ورز صحن دجاج غدا وجبة دجاج رز chicken tikka rice plate grilled chicken', 'a round platter of golden spiced rice topped with two glossy grilled chicken pieces and herbs, a small sauce bowl on the side', 'rice yellow, chicken roast brown, sauce red'),
 ('italian_saj', 'food', 'صاج إيطالي', 'صاج صاج ايطالي صاج إيطالي صاجي بيتزا رقيقة عجينة رقيقة جبن ريحان طماطم ايطالي إيطالي saj italian flatbread thin pizza margherita', 'a thin crispy Italian saj flatbread pizza with tomato, melting mozzarella and basil, one slice lifting with a cheese pull, on a wooden board', 'tomato red, cheese gold, basil green'),
 ('fishing_trip', 'out', 'طلعة صيد سمك', 'صيد سمك صيد السمك صيد سمچ طلعة صيد طلعة سمك صنارة قصبة صياد شط نهر دجلة بحيرة قارب زورق سمچ fishing fish trip rod boat lake river', 'a big bass leaping out of splashing water on a fishing line, a fishing rod, a bobber and a small fishing boat at sunset', 'fish green, water blue, sunset orange'),
 ('cafe_front', 'out', 'كافيه', 'كافيه كافي كوفي شوب مقهى مقهي قهوة كافتيريا كافيه جديد طلعة كافيه واجهة كافيه cafe coffee shop cafeteria storefront', 'a charming cafe storefront with a striped awning, a wooden sign, a street lamp and plants, with a latte-art coffee cup and beans in front', 'awning orange-yellow, wood brown, latte cream'),
 ('lamb_mandi', 'iraqi', 'مندي لحم', 'مندي لحم لحم مندي مندي لحم غنم لحم غنم ضاني لحم ضاني تمن مندي مطعم يمني رز مندي صحن مندي ولحم mandi lamb meat rice yemeni mutton', 'a large ornate platter of fragrant mandi rice topped with tender roasted lamb, tomato and herb garnish, and a small sauce bowl', 'rice orange-yellow, lamb roast brown, platter bronze'),
]

# ---- أسلوب الهوية العام: يُلصق قبل وصف كل ستيكر في ملف المطالبات ----
STYLE = ("Modern vintage paper cartoon sticker, premium collectible sticker style, antique illustration feel: hand-drawn cartoon linework with slightly uneven ink outlines, "
         "aged paper grain and subtle halftone/letterpress print texture, rich saturated colors, a thick die-cut white border around the subject with a soft paper drop shadow, "
         "slightly tilted composition, centered single subject, fully transparent background, square 1024x1024, high detail that still reads clearly at 96 px.")
NEGATIVE = ("NO text of any kind: no letters, no numbers, no Arabic or English words, no logos, no watermarks, no labels, no captions, no signatures. "
            "Not a photo, not realistic, not a flat app icon, not an emoji. One subject only, no contact sheet, no grid, no background scene rectangle.")

# ===== CODIS-STICKER-ATMOS — «جو الستيكر» على بطاقة المكافأة (طبقة إضافية؛ الستيكر نفسه لا يتغيّر) =====
# لكل ستيكر وصفة خاصة: عناصر صغيرة مرسومة (أسماء من مكتبة CodisAtmos داخل التطبيق) بالترتيب — الأول هو البطل (أكبر موضع).
# الألوان تُستخرج آلياً من رسم الستيكر الحقيقي وقت البناء (tools/sticker_atmos.py)؛ PAL أدناه للستيكرات المرسومة بالكود فقط
# (لا صورة نقطية لها) أو لتصحيح لوحة مستخرجة: [أساسي، ثانوي، لمسة، إضاءة، ظل].
# الخيارات بعد «|»: hold = عنصر يمكن أن «تمسكه» الشخصية (يظهر فقط في البطاقات التي فيها يد بموضع آمن) · nN = أقصى عدد عناصر
ATMOS = {
 # أكل سريع
 'shawarma': 'garlic herb pickle crumb | hold', 'burger': 'sesame lettuce ketchup crumb | hold', 'pizza': 'pepperoni basil cheese crumb | hold',
 'fries': 'fry salt ketchup | hold', 'falafel': 'falafel herb sesame tomato crumb | hold', 'fried_chicken': 'crunch spice crumb | hold',
 'noodles': 'noodle steam scallion | hold', 'sambusa': 'pastry herb crumb | hold', 'hot_dog': 'mustard ketchup crumb | hold',
 'taco': 'tomato lime herb crumb | hold', 'sandwich': 'lettuce tomato crumb | hold',
 # أكلات عراقية
 'dolma': 'vineleaf lemon rice | hold', 'kebab': 'ember smoke onion herb | hold', 'tikka': 'meatcube ember smoke | hold',
 'masgouf': 'lemon wave ember', 'biryani': 'rice anise herb | hold', 'tashreeb': 'steam chickpea crumb', 'kubba': 'croquette herb crumb | hold',
 'mandi_pot': 'steam anise herb', 'lunch': 'rice tomato herb ember',
 # حلويات
 'kunafa': 'pistachio syrup sugar | hold', 'baklava': 'pistachio flake syrup | hold', 'cheesecake': 'cherry chocdrip crumb | hold',
 'donut': 'sprinkle glaze sugar | hold', 'ice_cream': 'sprinkle drip cherry | hold', 'waffle': 'berry syrup sugar | hold',
 'pancakes': 'strawberry syrup butter | hold', 'croissant': 'flake crumb sugar | hold', 'choco_cake': 'chocshard cherry crumb | hold',
 'rice_pudding': 'pistachio petal sugar | hold', 'cupcake': 'sprinkle cream cherry | hold', 'cake_slice': 'strawberry cream crumb | hold',
 'cookie': 'chocchip crumb | hold', 'macaron': 'pastel sugar crumb | hold', 'chocolate_bar': 'chocshard cocoa | hold',
 # مشروبات باردة
 'iced_coffee': 'ice bean drop | hold', 'pomegranate': 'pomseed drop leaf | hold', 'orange_juice': 'orange drop leaf | hold',
 'mojito': 'mint lime ice bubble | hold', 'milkshake': 'cream sprinkle cherry | hold', 'smoothie': 'berry strawberry drop | hold',
 'coconut': 'palm drop flower | hold', 'soda': 'bubble ice drop | hold',
 # چاي وقهوة
 'tea_glass': 'steam tealeaf sugarcube | hold', 'teapot': 'steam tealeaf', 'arabic_coffee': 'cardamom bean steam | hold',
 'espresso': 'bean steam cocoa | hold', 'hot_choc': 'marshmallow steam cocoa | hold', 'cafe_table': 'bean steam leaf',
 'tea_cardamom': 'cardamom saffron steam | hold', 'coffee_togo': 'bean steam | hold',
 # طلعات
 'cinema': 'popcorn ticket film', 'bowling': 'pin spark star', 'park_picnic': 'leaf flower butterfly', 'dinner_out': 'bulb herb spark',
 'arcade': 'pixel button star', 'mall_bag': 'tag ribbon spark', 'theater': 'ticket star spot',
 # راحة
 'armchair': 'cloud star leaf', 'nap': 'moon z star', 'cat_nap': 'z paw moon', 'bath': 'bubble ripple drop', 'no_phone': 'leaf ripple star',
 'sleep_in': 'sun z cloud', 'candle_spa': 'bubble petal leaf',
 # ألعاب
 'gamepad': 'button pixel dpad | hold', 'board_game': 'pawn dice star', 'domino': 'pip dice spark', 'backgammon': 'checker dice spark',
 'handheld': 'pixel button star | hold', 'puzzle': 'piece spark | hold', 'headset': 'wave eq pixel', 'football': 'star confetti turf',
 'basketball': 'star speed confetti', 'billiards': 'ball8 chalk star', 'darts': 'target star spark',
 # أفلام ومحتوى
 'tv_show': 'play pixel star', 'movie_night': 'popcorn film ticket', 'podcast': 'wave note', 'music': 'note wave eq', 'anime': 'burst star spark',
 # هوايات
 'paint': 'paintdrop brush splat', 'camera': 'aperture spark leaf', 'oud': 'note wave star', 'pottery': 'clay leaf drop',
 # مشتريات
 'gift_bag': 'ribbon confetti spark | hold', 'shoes': 'tag spark speed', 'wristwatch': 'tick gear spark | hold', 'backpack': 'mappath leaf star',
 'sports_car': 'speed spark star', 'diamond': 'facet spark | hold',
 # عناية
 'perfume': 'mist petal spark | hold', 'hair_care': 'mist drop spark', 'skincare': 'bubble drop leaf | hold',
 # أصدقاء وعائلة
 'friends_cups': 'chat heart spark', 'phone_call': 'chat wave heart', 'family_table': 'heart herb steam', 'rose': 'petal leaf heart | hold',
 # تعلّم
 'new_book': 'page bookmark star | hold', 'notebook': 'pencil page star', 'graduation': 'star confetti page',
 # سفر
 'suitcase': 'mappath star leaf', 'camping': 'pine ember star', 'landmark': 'mappath star leaf', 'compass': 'mappath star | hold',
 # رقمي
 'subscription': 'play pixel spark', 'ebook': 'page pixel star',
 # مفاجآت
 'mystery_box': 'confetti ribbon spark', 'wrapped_gift': 'ribbon confetti spark | hold', 'treasure': 'coin gem spark | hold',
 # احتفال
 'trophy': 'star confetti spark | hold', 'fireworks': 'burst star spark', 'party_cake': 'confetti ribbon spark', 'medal': 'star ribbon spark | hold',
 'crown': 'gem spark star | hold',
 # CODIS-STICKERS-13
 'social_media': 'heart chat play spark', 'cigarettes': 'smoke ember spark', 'jummar_palm': 'palm leaf herb | hold', 'lettuce_head': 'lettuce leaf drop | hold',
 'iraqi_samoon': 'sesame crumb flake | hold', 'pickles': 'drop pickle herb | hold', 'mushrooms': 'leaf herb garlic | hold', 'shish_shawarma': 'herb spice crumb ember | hold',
 'chicken_tikka_rice': 'rice herb tomato ember | hold', 'italian_saj': 'basil tomato cheese crumb | hold', 'fishing_trip': 'wave drop ripple', 'cafe_front': 'bean steam spark',
 'lamb_mandi': 'rice anise steam herb | hold',
}
# لوحات يدوية للستيكرات المرسومة بالكود (بلا صورة نقطية) — من ألوان رسمها الأصلي في tools/sticker_art/art_*.py
PAL = {
 'mandi_pot': ['#8fa9bf', '#d9622f', '#5e9a3a', '#e9eef2', '#3c4a57'], 'rice_pudding': ['#efe2c4', '#c98f4a', '#7fae4a', '#fff8ea', '#7a5a35'],
 'iced_coffee': ['#a9714a', '#e9d8bd', '#8fcde8', '#fbf3e6', '#4a2c1c'], 'pomegranate': ['#c42c43', '#7a1426', '#5e9a3a', '#f6c7cf', '#4a0d18'],
 'mojito': ['#8fd18a', '#e9e36a', '#3f9a54', '#f2fbe9', '#245c33'], 'smoothie': ['#f08a4b', '#e8456b', '#f2c94c', '#fff0e2', '#7a2a2a'],
 'coconut': ['#6b4a2e', '#f4efe3', '#5ea64a', '#fffaf0', '#33231a'], 'teapot': ['#c9a14a', '#8a3b22', '#3f7f5a', '#f7e7c0', '#4a2a14'],
 'arabic_coffee': ['#c99a3e', '#7a4a22', '#6b8f3a', '#f6e4b4', '#3f2512'], 'hot_choc': ['#7a4a2f', '#f2e6dc', '#d65f7a', '#fff6ee', '#3a2014'],
 'cafe_table': ['#c86a3c', '#f1e2c8', '#5c9a5a', '#fff5e6', '#4a2a18'], 'tea_cardamom': ['#b5562a', '#e3b84a', '#6f9a3e', '#f8e3b8', '#4f220f'],
 'bowling': ['#3c5fa8', '#f1f1ee', '#d83a3a', '#ffffff', '#1f2c4f'], 'arcade': ['#6d4ac2', '#3fc1e0', '#f25d8e', '#efe8ff', '#2a1d55'],
 'no_phone': ['#4f7fb8', '#e7edf5', '#8fbf6a', '#ffffff', '#24384f'], 'podcast': ['#9aa4ad', '#2b2f36', '#4fc3a1', '#eef2f4', '#1b1e22'],
 'gift_bag': ['#e46b8f', '#f5c24c', '#8f63d1', '#fde8ef', '#6a2440'], 'family_table': ['#c9784a', '#f3e3c7', '#e05a6a', '#fff6e9', '#5a3220'],
 'notebook': ['#a63a3a', '#efe4cc', '#3f6fae', '#fff8ea', '#4a1a1a'], 'graduation': ['#2f3a56', '#e8b84a', '#5b84c8', '#f3e9cf', '#151b2a'],
 'suitcase': ['#3aa39a', '#e8a33f', '#d9573f', '#e9f6f3', '#1d4f4a'], 'subscription': ['#5468d8', '#3fd1c1', '#f2b84a', '#eef0ff', '#1f2766'],
 'ebook': ['#3d4a5e', '#9fd0f0', '#f2a33f', '#eef4fa', '#1b2230'], 'mystery_box': ['#7d4ad1', '#f5c24c', '#e8577e', '#efe6ff', '#2e1660'],
 'fireworks': ['#2c2f6b', '#f5c24c', '#e8577e', '#fff3d6', '#14163a'], 'party_cake': ['#f19ab4', '#f6d36a', '#7cc6f0', '#fff0f5', '#7a3350'],
}
# تصحيح دور لون واحد في اللوحة المستخرجة (الفهرس: 0 أساسي، 1 ثانوي، 2 لمسة، 3 إضاءة، 4 ظل) حين يكون اللون المميّز صغير المساحة بالرسم
PAL_FIX = {
 'falafel': {2: '#6f9a3a'}, 'shawarma': {2: '#7aa63c'}, 'taco': {2: '#6fae3a'}, 'dolma': {2: '#d8b23a'}, 'bath': {2: '#6fc3d8'},
 'skincare': {2: '#7fae6a'}, 'nap': {2: '#5f7fbf'}, 'park_picnic': {2: '#e8b44a'}, 'masgouf': {2: '#5fa8d0'}, 'kebab': {2: '#e86a2a'},
 'tikka': {2: '#e86a2a'}, 'camping': {2: '#3f7a4a'}, 'tea_glass': {2: '#e0a23a'}, 'espresso': {2: '#d8a46a'}, 'headset': {2: '#b46cf0'},
 'domino': {2: '#3a2a20'}, 'landmark': {2: '#5f9a4a'}, 'music': {2: '#e8b84a'}, 'cheesecake': {2: '#c8202a'},
}
