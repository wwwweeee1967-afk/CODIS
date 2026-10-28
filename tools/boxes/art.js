/* ===== CODIS-BOXES-V3 · رسومات الصناديق الخمسة (مصدر وحيد لكل مواضع عرض الصندوق) =====
   الرسومات الأصلية (1024×1024 PNG شفافة) محفوظة كما وصلت في assets/box_art_original؛ هنا نسخ WebP مقصوصة على حدود الصندوق الفعلية (alpha محفوظ) ومدمجة كي يبقى التطبيق ملفاً واحداً.
   w/h = أبعاد الصورة المقصوصة (نسبتها تختلف من صندوق لآخر ولا تُشوَّه أبداً) · seam = خط الغطاء كنسبة من ارتفاع الصورة عند حافتها اليسرى واليمنى (يتبع منظور كل رسم)
   wf = عرض الصندوق كنسبة من خانة العرض: تُعادَل بحيث تتقارب «المساحة المرئية» للصناديق الخمسة رغم اختلاف أشكالها (برونزي عريض ↔ كريستالي طويل). */
const CODIS_BOX_ART = {
  1:{ w:576, h:399, seam:[.385,.300], wf:.945, b64:'__B64_1__' },
  2:{ w:576, h:490, seam:[.500,.350], wf:.853, b64:'__B64_2__' },
  3:{ w:431, h:576, seam:[.430,.370], wf:.681, b64:'__B64_3__' },
  4:{ w:576, h:433, seam:[.395,.265], wf:.908, b64:'__B64_4__' },
  5:{ w:487, h:576, seam:[.372,.372], wf:.724, b64:'__B64_5__' }
};
const CODIS_BOX_URLS = {};
function econBoxArtMeta(n){ return CODIS_BOX_ART[Math.max(1, Math.min(5, n | 0))]; }
/* blob: URL قصير بدل تكرار base64 (70–115KB) في كل نسخة من الصندوق على الشاشة؛ يعود إلى data: إن فشل */
function econBoxArtUrl(n){
  n = Math.max(1, Math.min(5, n | 0));
  if(CODIS_BOX_URLS[n]) return CODIS_BOX_URLS[n];
  const a = CODIS_BOX_ART[n]; let u = 'data:image/webp;base64,' + a.b64;
  try{ const bin = atob(a.b64), buf = new Uint8Array(bin.length); for(let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i); u = URL.createObjectURL(new Blob([buf], { type:'image/webp' })); }catch(e){}
  return CODIS_BOX_URLS[n] = u;
}
/* الصندوق الثابت (المتجر، المخزون، التفاصيل، نافذة الشراء…): خانة بنسبة 120:112 تتحكم بها قواعد كل موضع، والصورة تتناسب داخلها بلا تشويه */
function econBoxArt(n){
  const a = econBoxArtMeta(n);
  return '<span class="bxa" style="--wf:' + a.wf + '"><img class="bxa-img" alt="" draggable="false" decoding="async" src="' + econBoxArtUrl(n) + '"></span>';
}
/* وسم فئة القيمة: «فئة ٣ · 375–420» (أو قيمة واحدة إن تساوى الحد الأدنى والأعلى) — كانت ضمن الكتلة القديمة وتُستعمل في احتمالات البكج */
function econClassLabel(o){ return o.name + ' · ' + (o.min === o.max ? econFmt(o.min) : econFmt(o.min) + '–' + econFmt(o.max)); }
