# مطالبات توليد ستيكرات CODIS

كل ستيكر يُولَّد **بصورة مستقلة** (PNG أو WebP شفاف، مربع 1024×1024) ويُحفظ باسم **المعرّف** داخل `assets/stickers/` مثل `shawarma.webp`.
بعد وضع الصور شغّل: `py -3 tools/build_stickers.py` (يحدّث المكتبة ويظهر المتاح فقط بالمنتقي). يمكن لاحقاً تبديل أي صورة بنفس الاسم.

## الأسلوب العام (يُلصق قبل وصف كل ستيكر)

```
Modern vintage paper cartoon sticker, premium collectible sticker style, antique illustration feel: hand-drawn cartoon linework with slightly uneven ink outlines, aged paper grain and subtle halftone/letterpress print texture, rich saturated colors, a thick die-cut white border around the subject with a soft paper drop shadow, slightly tilted composition, centered single subject, fully transparent background, square 1024x1024, high detail that still reads clearly at 96 px.
```

## الممنوعات (تُلصق بعد وصف كل ستيكر)

```
NO text of any kind: no letters, no numbers, no Arabic or English words, no logos, no watermarks, no labels, no captions, no signatures. Not a photo, not realistic, not a flat app icon, not an emoji. One subject only, no contact sheet, no grid, no background scene rectangle.
```

> ملاحظة جودة: وزّع التنوّع فعلاً — كل ستيكر بتكوين وزاوية ولوحة ألوان وملمس مختلف، ضمن نفس العائلة الفنية. لا تستعمل قالباً واحداً.

## أكل سريع

### `shawarma` — لفة شاورمة (موجود)

```
Subject: a hand-drawn shawarma wrap half-unwrapped from crinkled paper, charred pita, pickles, lettuce and garlic sauce spilling out. Palette: warm toasted orange, cream, olive green.
```

### `burger` — بركر (موجود)

```
Subject: a tall double cheeseburger with sesame bun, melting cheese, tomato slices, lettuce, with a toothpick flag. Palette: mustard yellow, tomato red, bun brown.
```

### `pizza` — بيتزا (موجود)

```
Subject: one pizza slice with stretching mozzarella strand, pepperoni discs and basil leaves on a checkered paper tray. Palette: tomato red, cheese gold, basil green.
```

### `fries` — بطاطا مقلية (موجود)

```
Subject: a red paper cone overflowing with golden fries, a puddle of cheese sauce, salt sparkles. Palette: golden yellow, red stripes.
```

### `falafel` — صمون فلافل (موجود)

```
Subject: a loaf of samoon bread stuffed with falafel balls, tahini drizzle, pickled turnip and tomato. Palette: bread tan, herb green, tahini cream.
```

### `fried_chicken` — دجاج كرسبي (موجود)

```
Subject: a stack of crispy fried chicken drumsticks in a striped bucket with a hot pepper. Palette: crunchy amber, red and white stripes.
```

### `noodles` — نودلز (موجود)

```
Subject: a steaming bowl of spicy noodles with chopsticks lifting a twirl, a soft egg and chili flakes. Palette: chili red, broth brown, bowl indigo.
```

### `sambusa` — سمبوسة (موجود)

```
Subject: three golden triangular fried pastries with a lemon wedge and a dipping sauce cup. Palette: fried gold, lemon yellow, mint green.
```

### `hot_dog` — هوت دوك (موجود)

```
Subject: a grilled hot dog in a soft bun with a wavy mustard line. Palette: bun gold, sausage red, mustard yellow.
```

### `taco` — تاكو (موجود)

```
Subject: a crunchy taco shell packed with seasoned meat, lettuce, tomato and cheese. Palette: shell yellow, lettuce green, tomato red.
```

### `sandwich` — سندويچ توست (موجود)

```
Subject: a triangle toast club sandwich stacked with ham, cheese, lettuce and tomato. Palette: toast brown, lettuce green, tomato red.
```

### `mushrooms` — فطر (موجود)

```
Subject: a group of fresh white button mushrooms, whole and sliced, with parsley leaves. Palette: cream white, brown cap, parsley green.
```

### `shish_shawarma` — شيش شاورما (موجود)

```
Subject: a tall vertical rotating shawarma spit of stacked seasoned meat roasting over flames, with a wrapped shawarma sandwich in front. Palette: roast orange, flame yellow, wrap cream.
```

### `italian_saj` — صاج إيطالي (موجود)

```
Subject: a thin crispy Italian saj flatbread pizza with tomato, melting mozzarella and basil, one slice lifting with a cheese pull, on a wooden board. Palette: tomato red, cheese gold, basil green.
```

## أكلات عراقية

### `dolma` — دولمة (موجود)

```
Subject: a round copper tray of rolled vine-leaf dolma arranged in a spiral with onions and a lemon. Palette: copper, vine green, lemon.
```

### `kebab` — مشاوي كباب (موجود)

```
Subject: four long skewers of grilled minced-meat kebab, glossy and charred. Palette: charcoal black, ember orange, meat brown.
```

### `tikka` — مشاوي تكة (موجود)

```
Subject: four skewers of grilled meat cubes (tikka) with charred edges. Palette: ember orange, meat brown, wood tan.
```

### `masgouf` — مسگوف (موجود)

```
Subject: a butterflied carp fish standing by an open fire on wooden stakes, with tomatoes, onions and flatbread. Palette: fire orange, river blue, fish silver.
```

### `biryani` — برياني ورز (موجود)

```
Subject: a steaming platter of saffron rice heaped with roasted chicken, almonds and raisins, a ladle of broth beside it. Palette: saffron yellow, roast brown, white platter.
```

### `tashreeb` — تشريب (موجود)

```
Subject: a deep clay bowl of tashreeb stew with torn bread soaking in rich red broth, chickpeas and herbs. Palette: terracotta, stew red, bread beige.
```

### `kubba` — كبة (موجود)

```
Subject: a tray of oval kubba croquettes, one cut open to show spiced meat filling, beside a small bowl of pickles. Palette: golden brown, spice red, cream.
```

### `mandi_pot` — قدر بيتي (موجود)

```
Subject: a big dented cooking pot with lid ajar releasing steam, a wooden spoon, okra and tomatoes around it. Palette: pot silver-blue, okra green, tomato red.
```

### `lunch` — صحن غدا (موجود)

```
Subject: a full lunch plate: grilled meat, rice, salad and fried vegetables. Palette: meat brown, rice white, salad green.
```

### `jummar_palm` — جمّار نخيل (موجود)

```
Subject: a freshly cut white palm heart (jummar): a tender cream-colored cylinder of layered sheaths with ribbed texture, a few green palm fronds behind it. Palette: cream white, pale green, palm green.
```

### `lettuce_head` — خس (موجود)

```
Subject: a fresh green lettuce head with crisp ruffled leaves and visible pale ribs. Palette: leaf green, light lime, rib cream.
```

### `iraqi_samoon` — صمون عراقي (موجود)

```
Subject: golden Iraqi samoon diamond-shaped loaves with crisp crust and sesame flecks, stacked in a woven basket. Palette: bread golden, crust brown, basket tan.
```

### `pickles` — طرشي (موجود)

```
Subject: a glass jar packed with pickled cucumbers, peppers and carrots under a red lid, with a few loose pickles beside it. Palette: pickle green, pepper red, carrot orange.
```

### `chicken_tikka_rice` — تكة دجاج وتمن (موجود)

```
Subject: a round platter of golden spiced rice topped with two glossy grilled chicken pieces and herbs, a small sauce bowl on the side. Palette: rice yellow, chicken roast brown, sauce red.
```

### `lamb_mandi` — مندي لحم (موجود)

```
Subject: a large ornate platter of fragrant mandi rice topped with tender roasted lamb, tomato and herb garnish, and a small sauce bowl. Palette: rice orange-yellow, lamb roast brown, platter bronze.
```

## حلويات

### `kunafa` — كنافة (موجود)

```
Subject: a round tray of kunafa with golden shredded-pastry top, a slice lifted showing stretchy cheese, pistachio crumbs and syrup. Palette: deep gold, orange blossom syrup, pistachio green.
```

### `baklava` — بقلاوة (موجود)

```
Subject: a stack of diamond-shaped baklava with flaky layers, honey drizzle and chopped pistachios. Palette: honey amber, pistachio green, pastry cream.
```

### `cheesecake` — تشيز كيك (موجود)

```
Subject: a creamy cheesecake slice with a strawberry sauce top, a fork and a mint leaf on a small plate. Palette: cream white, strawberry red, plate blue.
```

### `donut` — دونات (موجود)

```
Subject: two glazed donuts, one pink frosted with colorful sprinkles and one chocolate, one with a bite taken. Palette: bubblegum pink, chocolate brown, confetti colors.
```

### `ice_cream` — آيس كريم (موجود)

```
Subject: a waffle cone with three melting scoops in mismatched flavors, drips running down, a wafer stick. Palette: vanilla cream, strawberry pink, pistachio mint.
```

### `waffle` — وافل (موجود)

```
Subject: stacked golden waffles with syrup and fresh berries on top. Palette: waffle gold, maple amber, berry red-blue.
```

### `pancakes` — بان كيك (موجود)

```
Subject: a tall stack of fluffy pancakes with syrup and berries on top. Palette: pancake tan, maple amber, berry red.
```

### `croissant` — كرواسون (موجود)

```
Subject: a flaky golden croissant on a bakery paper bag with a few crumbs and a wheat sprig. Palette: butter gold, paper bag brown, wheat yellow.
```

### `choco_cake` — كيك شوكولاتة (موجود)

```
Subject: a dark chocolate layer cake slice with glossy ganache, a cherry on top and a dusting of cocoa. Palette: cocoa brown, cherry red, cream filling.
```

### `rice_pudding` — مهلبية ورز بحليب (موجود)

```
Subject: a small glass cup of milky pudding with cinnamon dust, rose petals and crushed nuts, with a tiny spoon. Palette: milk white, cinnamon tan, rose pink.
```

### `cupcake` — كب كيك (موجود)

```
Subject: a chocolate cupcake topped with a pink cream swirl and a cherry. Palette: cream pink, chocolate brown, cherry red.
```

### `cake_slice` — كيك فراولة (موجود)

```
Subject: a layered sponge cake slice with strawberry cream and a fresh strawberry on top. Palette: sponge cream, strawberry red.
```

### `cookie` — كوكيز (موجود)

```
Subject: a big golden cookie studded with chocolate chips. Palette: golden brown, chocolate.
```

### `macaron` — ماكرون (موجود)

```
Subject: a plump pink macaron with a cream filling. Palette: raspberry pink, cream.
```

### `chocolate_bar` — لوح شوكولاتة (موجود)

```
Subject: a dark chocolate bar half unwrapped from crinkled gold foil. Palette: chocolate brown, foil gold.
```

## مشروبات باردة

### `iced_coffee` — آيس كوفي (موجود)

```
Subject: a tall clear glass of iced coffee with visible milk layers swirling, ice cubes and a bent paper straw. Palette: coffee brown, milk cream, icy blue.
```

### `pomegranate` — عصير رمان (موجود)

```
Subject: a glass of ruby pomegranate juice beside a split pomegranate spilling jewel-like seeds. Palette: ruby red, deep magenta, leaf green.
```

### `orange_juice` — عصير برتقال (موجود)

```
Subject: a juice glass of fresh orange juice with an orange slice on the rim and a halved orange with leaves. Palette: sunny orange, leaf green, white pulp.
```

### `mojito` — موهيتو وليمون (موجود)

```
Subject: a highball glass of mojito packed with lime wheels, muddled mint leaves, crushed ice and a striped straw. Palette: lime green, mint teal, ice white.
```

### `milkshake` — ميلك شيك (موجود)

```
Subject: a tall diner-style milkshake with whipped cream swirl, a cherry, a long spoon and a straw. Palette: strawberry pink, whipped cream white, cherry red.
```

### `smoothie` — سموذي فواكه (موجود)

```
Subject: a blended smoothie jar with layered mango and berry, fruit chunks floating beside it. Palette: mango yellow, berry purple, fresh green.
```

### `coconut` — جوز هند (موجود)

```
Subject: a whole green coconut with a hole and straw, a small umbrella and a hibiscus flower. Palette: coconut green, hibiscus red, sand beige.
```

### `soda` — مشروب غازي (موجود)

```
Subject: a red paper soda cup with a lid and a striped straw. Palette: soda red, white swirl.
```

## چاي وقهوة

### `tea_glass` — استكان جاي (موجود)

```
Subject: a curvy waisted glass istikan of amber tea on a small gilded saucer with a sugar cube, thin steam curls and cardamom pods. Palette: amber, gold rim, soft glass blue.
```

### `teapot` — قوري وسماور (موجود)

```
Subject: an ornate dark teapot with a curved spout on a charcoal brazier-style stand, steam, and two small glasses. Palette: brass gold, dark teal, ember glow.
```

### `arabic_coffee` — قهوة عربية (موجود)

```
Subject: a tall brass dallah coffee pot pouring into a tiny handleless finjan cup, dates and cardamom beside. Palette: brass, coffee brown, date maroon.
```

### `espresso` — إسبريسو وكابتشينو (موجود)

```
Subject: a cappuccino cup seen from a slight angle with leaf latte art, a spoon and coffee beans scattered. Palette: espresso brown, foam cream, cup terracotta.
```

### `hot_choc` — هوت چوكليت (موجود)

```
Subject: a chunky mug of hot chocolate topped with marshmallows and a cinnamon stick, wisps of steam. Palette: cocoa brown, marshmallow white, mug red.
```

### `cafe_table` — قعدة كافيه (موجود)

```
Subject: a tiny round cafe table with two cups, a croissant plate and a small vase with a flower, a chair back peeking in. Palette: cafe green, wood brown, cream.
```

### `tea_cardamom` — چاي بالهيل (موجود)

```
Subject: a small jar of green cardamom pods, saffron threads in a dish and a cinnamon stick laid around a tea glass. Palette: saffron orange, cardamom green, cinnamon brown.
```

### `coffee_togo` — قهوة تيك أوي (موجود)

```
Subject: a takeaway coffee cup with a brown lid and a coffee-bean sleeve. Palette: kraft brown, cream.
```

## طلعات

### `cinema` — سينما (موجود)

```
Subject: a striped popcorn box overflowing, two torn cinema tickets and a tiny film clapperboard without any writing. Palette: cinema red, popcorn butter, midnight blue.
```

### `bowling` — بولينگ (موجود)

```
Subject: a bowling ball mid-roll toward ten scattering pins with motion swooshes. Palette: lane wood, ball indigo, pin white-red.
```

### `park_picnic` — حديقة ونزهة (موجود)

```
Subject: a checkered picnic blanket with a basket, a thermos and a tree casting soft shade, butterflies around. Palette: meadow green, gingham red, sky blue.
```

### `dinner_out` — غدا وعشا بمطعم (موجود)

```
Subject: a restaurant table with a candle, a covered silver cloche being lifted, wine-less glasses and folded napkin. Palette: candle gold, tablecloth navy, silver.
```

### `arcade` — ألعاب أركيد (موجود)

```
Subject: a chunky retro arcade cabinet with a joystick and glowing pixel-like screen and a stack of tokens. Palette: neon violet, screen cyan, token gold.
```

### `mall_bag` — مول وتسوق (موجود)

```
Subject: two paper shopping bags with ribbon handles tipping over, tissue paper sprouting out. Palette: bag pink, bag teal, tissue yellow.
```

### `theater` — مسرح (موجود)

```
Subject: golden comedy and silver tragedy masks side by side. Palette: mask gold, silver grey.
```

### `fishing_trip` — طلعة صيد سمك (موجود)

```
Subject: a big bass leaping out of splashing water on a fishing line, a fishing rod, a bobber and a small fishing boat at sunset. Palette: fish green, water blue, sunset orange.
```

### `cafe_front` — كافيه (موجود)

```
Subject: a charming cafe storefront with a striped awning, a wooden sign, a street lamp and plants, with a latte-art coffee cup and beans in front. Palette: awning orange-yellow, wood brown, latte cream.
```

## راحة

### `armchair` — ساعة راحة (موجود)

```
Subject: a cozy armchair with a plump cushion, a knitted blanket draped over and a small side table with a plant. Palette: calm sage green, wool cream, wood brown.
```

### `nap` — نوم (موجود)

```
Subject: a cozy wooden bed with blue blanket and pillows. Palette: wood brown, blanket blue, pillow white.
```

### `cat_nap` — غفوة وكسل (موجود)

```
Subject: a tabby cat curled up asleep on a round cushion with zzz. Palette: tabby orange, cushion navy.
```

### `bath` — حمام دافي (موجود)

```
Subject: a clawfoot bathtub brimming with bubbles, a rubber duck, rolled towel and a candle on the edge. Palette: bubble white, brass faucet, soft aqua.
```

### `no_phone` — بدون موبايل (موجود)

```
Subject: a smartphone resting face-down inside a small glass dome like a museum piece, a book and tea nearby. Palette: glass teal, dusk purple, paper cream.
```

### `sleep_in` — صباح بدون منبه (موجود)

```
Subject: a retro twin-bell alarm clock wearing a tiny sleep mask on its face, with a sunbeam and a quilt corner. Palette: sunrise peach, clock mint, quilt coral.
```

### `candle_spa` — عناية بالبشرة (موجود)

```
Subject: a lit scented candle in a glass, a clay face mask bowl with a brush and cucumber slices. Palette: clay beige, candle amber, cucumber green.
```

## ألعاب

### `gamepad` — يد تحكم (موجود)

```
Subject: a chunky game controller with colorful round buttons and a tiny sparkle trail, one thumbstick tilted. Palette: controller charcoal, button primary colors.
```

### `board_game` — شطرنج (موجود)

```
Subject: a wooden chess board with ivory and black pieces. Palette: wood brown, ivory, black.
```

### `domino` — دومينو (موجود)

```
Subject: three ivory domino tiles standing together. Palette: ivory, black dots.
```

### `backgammon` — طاولي (موجود)

```
Subject: an open wooden backgammon board with checkers. Palette: wood brown, red, ivory.
```

### `handheld` — لعبة موبايل (موجود)

```
Subject: a handheld console with a glowing screen and a small pixel heart, a charging cable curled around it. Palette: console teal, screen lime, cable white.
```

### `puzzle` — ألغاز (موجود)

```
Subject: a half-finished jigsaw puzzle with one piece floating in, mismatched pastel colored pieces. Palette: pastel mix, board brown.
```

### `headset` — سماعة ألعاب (موجود)

```
Subject: big over-ear gaming headphones with a curved mic and glowing ear cups. Palette: headset black, accent orange, glow cyan.
```

### `football` — كرة قدم (موجود)

```
Subject: a classic black and white leather football. Palette: leather white, black.
```

### `basketball` — كرة سلة (موجود)

```
Subject: an orange basketball with deep black seams. Palette: basketball orange, black.
```

### `billiards` — بليارد (موجود)

```
Subject: a glossy black eight ball. Palette: gloss black, white.
```

### `darts` — سهام دارت (موجود)

```
Subject: a dartboard with two darts in the bullseye area. Palette: board black, cream, red and green.
```

## أفلام ومحتوى

### `tv_show` — مسلسل وحلقة (موجود)

```
Subject: a retro television set with rabbit-ear antennas, a blanket-covered couch edge and a bowl of snacks in front. Palette: tv wood, screen blue glow, blanket red.
```

### `movie_night` — ليلة أفلام (موجود)

```
Subject: a small film projector casting a beam on a screen with silhouettes of two snack bowls and a blanket. Palette: beam amber, dark room blue, popcorn gold.
```

### `podcast` — بودكاست (موجود)

```
Subject: a vintage microphone beside a vinyl record and floating music-note shapes, headphones hanging on it. Palette: mic chrome, vinyl black, note mint.
```

### `music` — موسيقى (موجود)

```
Subject: golden treble clef and floating music notes. Palette: gold, amber.
```

### `anime` — أنمي وكرتون (موجود)

```
Subject: a bubbly cartoon-style character-less scene: a bowl of ramen with a speech-cloud-shaped steam and sparkle stars, manga-screentone dots. Palette: sakura pink, ramen orange, ink black.
```

## هوايات

### `paint` — جلسة رسم (موجود)

```
Subject: a wooden painter palette with dollops of color, two brushes crossed and a small canvas on an easel corner. Palette: palette wood, vivid pigments.
```

### `camera` — تصوير (موجود)

```
Subject: a vintage film camera with a leather strap, a few instant photos fanning out, one with a tiny paper clip. Palette: camera black-silver, photo white, strap tan.
```

### `oud` — عود وموسيقى (موجود)

```
Subject: a beautiful pear-shaped oud with a decorative rosette and bent neck, a few music-note swirls. Palette: oud wood amber, rosette cream, strings gold.
```

### `pottery` — فخار وحرف (موجود)

```
Subject: a clay pot on a spinning wheel with wet hands shaping it, a ball of yarn and crochet hook beside. Palette: clay terracotta, yarn teal, wood brown.
```

## مشتريات

### `gift_bag` — هدية صغيرة (موجود)

```
Subject: a small kraft gift bag with tissue sprouting, a keychain charm and a tiny wrapped trinket beside. Palette: kraft brown, tissue pink, charm gold.
```

### `shoes` — حذاء وملابس (موجود)

```
Subject: a pair of stylish sneakers with mismatched laces and a folded shirt with a hanger hook above. Palette: sneaker white-red, shirt denim blue.
```

### `wristwatch` — ساعة يد (موجود)

```
Subject: a classic wristwatch with a leather strap partly unrolled, gears peeking from the back and a small wallet. Palette: steel silver, strap brown, wallet navy.
```

### `backpack` — شنطة (موجود)

```
Subject: a rugged backpack with buckles and pockets, a laptop corner sticking out of the top flap. Palette: bag forest green, buckle brass, laptop silver.
```

### `sports_car` — سيارة (موجود)

```
Subject: a red sports car with white racing stripes. Palette: racing red, white stripes.
```

### `diamond` — ألماسة (موجود)

```
Subject: a brilliant cut blue diamond sparkling. Palette: ice blue, white sparkle.
```

### `cigarettes` — سكائر (موجود)

```
Subject: an open red cigarette pack with a gold crown mark and a few cigarettes sticking out, two loose cigarettes lying in front. Palette: pack red, filter orange, paper white.
```

## عناية

### `perfume` — عطر (موجود)

```
Subject: an elegant faceted perfume bottle with a bulb sprayer and a spray mist cloud with floating petals. Palette: bottle amber, mist lilac, petal rose.
```

### `hair_care` — شعر وحلاقة (موجود)

```
Subject: a barber scene: scissors, a comb and a striped barber pole, a hand mirror reflecting a sparkle. Palette: barber red-blue stripe, steel, mirror silver.
```

### `skincare` — كريم ولوشن (موجود)

```
Subject: a round jar of cream with a lid leaning beside it, a lotion tube and a soft towel roll, a daisy. Palette: cream pastel, towel mint, daisy yellow.
```

## أصدقاء وعائلة

### `friends_cups` — قعدة أصدقاء (موجود)

```
Subject: three mismatched mugs clinking together over a low table with a plate of snacks and a speech-bubble shape (blank). Palette: warm mix, table wood, bubble white.
```

### `phone_call` — مكالمة (موجود)

```
Subject: a retro telephone with a long curly cord forming a heart shape and a few small hearts drifting upward. Palette: phone teal, cord cream, heart pink.
```

### `family_table` — غدا عائلي (موجود)

```
Subject: a big round table spread with shared dishes and a pot in the center, many hands reaching in (no faces). Palette: tablecloth red-white, dishes varied, wood brown.
```

### `rose` — وردة (موجود)

```
Subject: a single deep red rose with a green leaf. Palette: rose red, leaf green.
```

## تعلّم

### `new_book` — كتاب جديد (موجود)

```
Subject: an open book with aged pages, a ribbon bookmark, pressed leaf and ink-pen curls, a stack of two books beneath. Palette: paper sepia, ink blue, leaf green.
```

### `notebook` — دفتر وقلم (موجود)

```
Subject: a leather-bound notebook with an elastic strap, a fountain pen and a few washi tapes and stickers. Palette: leather brown, ink navy, washi coral.
```

### `graduation` — دورة وتعلم (موجود)

```
Subject: a graduation cap resting on a stack of books with a small lightbulb and a rolled certificate (blank). Palette: cap black, tassel gold, books maroon.
```

## سفر

### `suitcase` — حقيبة سفر (موجود)

```
Subject: a vintage hard-shell suitcase covered with blank travel-label shapes, a passport shape and a sun hat on top. Palette: case teal, strap tan, hat straw.
```

### `camping` — تخييم ونزهة (موجود)

```
Subject: a small tent glowing from inside, a campfire with sparks and a few pine trees under a star sky. Palette: tent orange, night navy, fire gold.
```

### `landmark` — مكان سياحي (موجود)

```
Subject: a stylized domed building with arches and a minaret-like tower, a tiny bridge and a map pin shape. Palette: sandstone, dome turquoise, sky pale blue.
```

### `compass` — بوصلة (موجود)

```
Subject: an antique brass pocket compass with a red and gold needle. Palette: brass gold, parchment.
```

## رقمي

### `subscription` — اشتراك رقمي (موجود)

```
Subject: a floating glowing app-card with a play triangle and a cloud, small key and calendar page shapes orbiting. Palette: screen glow violet, cloud white, key gold.
```

### `ebook` — كتاب إلكتروني (موجود)

```
Subject: a tablet showing blank text lines resting against a stack of paper books with a cozy mug. Palette: tablet slate, paper cream, mug orange.
```

### `social_media` — سوشال ميديا (موجود)

```
Subject: a cluster of four glossy rounded social-app tiles (camera-gradient, music-note, play button, paper plane) with a small golden crown on top. Palette: gradient pink-orange, black, red, sky blue.
```

## مفاجآت

### `mystery_box` — بوكس مفاجأة (موجود)

```
Subject: a mysterious box with a big question-mark-shaped keyhole glow (no letters), ribbons springing out and confetti. Palette: box violet, glow gold, ribbon pink.
```

### `wrapped_gift` — هدية ملفوفة (موجود)

```
Subject: a wrapped present with a big ribbon bow, curly ribbon tails and a handful of falling confetti. Palette: wrap red, ribbon gold, confetti mix.
```

### `treasure` — صندوق كنز (موجود)

```
Subject: an old wooden treasure chest overflowing with coins and gems with a skeleton-key lying in front. Palette: chest wood, gold, gem green-blue.
```

## احتفال

### `trophy` — كأس إنجاز (موجود)

```
Subject: a gleaming golden trophy cup with laurel wreath and a star on a small pedestal, light rays behind. Palette: trophy gold, laurel green, ray yellow.
```

### `fireworks` — ألعاب نارية (موجود)

```
Subject: a night sky bursting with a cluster of colorful fireworks over a tiny skyline silhouette. Palette: night navy, firework mix.
```

### `party_cake` — كيكة احتفال (موجود)

```
Subject: a small layered celebration cake with lit candles, a party hat and a bunch of balloons tied to it. Palette: cake pink-white, balloons bright mix, candle flame.
```

### `medal` — ميدالية (موجود)

```
Subject: a gold star medal hanging from a red and white ribbon. Palette: medal gold, ribbon red.
```

### `crown` — تاج (موجود)

```
Subject: a royal red velvet crown with gold arches and jewels. Palette: velvet red, gold, jewels.
```
