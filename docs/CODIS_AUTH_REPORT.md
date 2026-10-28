# CODIS — تقرير تدقيق وإكمال تسجيل الدخول بـ Google + المزامنة

**الحالة النهائية: IMPLEMENTATION COMPLETE, EXTERNAL VERIFICATION REQUIRED**
(الكود والـ SQL جاهزين ومُختبَرين محلياً؛ يبقى ربط Google/Supabase الحقيقيين واختبار حيّ عليهم — ما أقدر أسويهم من هنا.)

---

## A. نتائج التدقيق

### موجود وصحيح (لم يُمَس)
- PKCE: توليد verifier (64 حرف) و challenge بـ SHA-256 صحيح (مطابق لمثال RFC 7636).
- رابط الدخول `/auth/v1/authorize?provider=google&flow_type=pkce&code_challenge_method=s256` وتبادل الكود `/auth/v1/token?grant_type=pkce` صحيحين.
- حفظ الجلسة، استرجاعها، تجديدها قبل الانتهاء بدقيقة، تسجيل الخروج (يلغي الجلسة بالخادم ويمسح بيانات الجهاز).
- تصميم المزامنة: لقطة كاملة + رقم نسخة (version) + نافذة اختيار عند التعارض + نسخ احتياطية محلية + ترحيل تقدّم الضيف لأول حساب.
- حذف الحساب: ما يعلن النجاح إلا إذا نجح الخادم.

### عيوب لقيتها وأصلحتها
| # | العيب | الخطورة | الإصلاح |
|---|---|---|---|
| 1 | `CODIS_BACKEND` فارغ، وما كو أي تحقق: يقبل أي مفتاح بما فيه `service_role` (كان يصير مكشوف بالمتصفح) | عالية | تحقق صارم: رفض `service_role` / `sb_secret_`، فحص شكل الرابط والمفتاح، رسالة عربية واضحة |
| 2 | الكود يقبل `access_token` من **#fragment** الرابط. رابط خبيث يخلي الضحية تدخل بحساب المهاجم وتقدّمها ينرفع لحسابه (session fixation) | عالية | ما نقبل إلا `code` (PKCE) |
| 3 | فتح الملف مباشرة (`file://`) يفشل بصمت لأن Supabase ما يقدر يرجّع المستخدم | متوسطة | يُعطَّل مع شرح واضح؛ التطبيق يشتغل كضيف |
| 4 | إذا Google غير مفعّل بـ Supabase، المتصفح يروح لصفحة JSON خام ويعلق المستخدم | متوسطة | فحص مسبق `/auth/v1/settings` قبل التحويل + رسالة عربية |
| 5 | الـ verifier بلا مدة صلاحية، وكود بدون verifier يُرسَل للخادم ويطلع خطأ عام | متوسطة | صلاحية 10 دقايق + رسالة صريحة وما يُرسل شي |
| 6 | رسائل أخطاء الرجوع إنجليزية خام، والإلغاء (`access_denied`) ما يتميّز | منخفضة | ترجمة: إلغاء، المزوّد غير مفعّل، Client Secret غلط، Redirect URL غير مسموح |
| 7 | تجديد الجلسة غير محمي من التزامن/تعدد التبويبات؛ مع تدوير refresh token يسبب خروج عشوائي | متوسطة | طلب تجديد واحد فقط + تبنّي الجلسة المجدَّدة من تبويب ثاني |
| 8 | أخطاء الخادم الدائمة (دالة/جدول ناقص، RLS) تنعاد للأبد بلا رسالة مفهومة | متوسطة | تصنيف الأخطاء، رسالة عربية بصفحة الحساب، وقف إعادة المحاولة التلقائية للأخطاء الدائمة |
| 9 | استثناءات مبلوعة (خروج، أدمن) | منخفضة | تشخيص بالكونسول (بدون أي توكنات) |
| 10 | عند تبديل الحساب `location.reload()` بدون حماية من الحلقة | منخفضة | نفس حارس الحلقة الموجود |
| 11 | فحص الأدمن `rows.length` فقط | منخفضة (الحماية الفعلية بالخادم) | يتأكد إن الصف يخصّ المستخدم نفسه |
| 12 | `hideGate` ما يرجّع حالة «جارٍ التحميل» | منخفضة | يُصفّرها |

### مفقود
- **ملف `codis_supabase_setup.sql` ما كان موجود بالملفات المرفوعة** (الكود يشير له فقط). كتبته من العمليات الفعلية بالكود (انظر C). **ما أعرف إذا مشروعك الحالي بالفعل فيه جداول/دوال بنفس الأسماء** — إذا موجودة راجعها قبل التشغيل (الملف idempotent لكنه يعيد تعريف الدوال).
- القيم الفعلية (Project URL / anon key) — ما أخترعها.

### إعدادات خارجية غير متحقَّق منها (ما عندي وصول)
Google Cloud، لوحة Supabase، النطاق/الـ HTTPS.

---

## B. التغييرات

| الملف | الغرض |
|---|---|
| `CODIS_9-7-2_auth.html` | نفس التطبيق مع تعديلات محصورة بوحدة `CodisAccount` + وسمَي `<meta>` بالـ `<head>` + سطرين بصفحة الحساب. **ما تغيّر شي بباقي التطبيق.** (الفرق الكامل: `auth_changes.diff`) |
| `codis_supabase_setup.sql` | الجداول/الدوال/السياسات المطلوبة (جديد) |
| `CODIS_AUTH_REPORT.md` | هذا التقرير |
| `codis_auth_tests.zip` | سكربتات الاختبار ونتائجها |

آلية الإعداد (بالأولوية): `window.CODIS_BACKEND_OVERRIDE` ← وسما `<meta name="codis-supabase-url">` و`<meta name="codis-supabase-key">` ← الثابت `CODIS_BACKEND`.

---

## C. متطلبات قاعدة البيانات (مستخرجة من الكود)

| العنصر | الحالة |
|---|---|
| `GET /rest/v1/progress?select=data,version,updated_at&user_id=eq.<uid>` | **جديد** — جدول `public.progress(user_id pk→auth.users, data jsonb, version bigint, updated_at)` |
| RLS على `progress` | **جديد** — SELECT لصفّك فقط؛ لا INSERT/UPDATE/DELETE مباشر لأي أحد |
| `rpc/save_progress(p_data jsonb, p_base_version bigint) → jsonb` | **جديد** — `{ok,version}` أو `{ok:false,conflict:true,version,data,updated_at}`؛ SECURITY DEFINER + `search_path=''`؛ المالك من `auth.uid()` فقط؛ حد 8MB؛ قفل صف لمنع التزامن |
| `rpc/delete_my_account() → void` | **جديد** — يحذف التقدّم + `auth.users` (cascade)، ويرفع خطأ عند الفشل |
| `GET /rest/v1/admins?select=user_id` | **جديد** — جدول `public.admins`؛ RLS: كل مستخدم يرى صفّه فقط؛ ما كو كتابة من العميل |
| `public.is_admin()` | **جديد** — فحص أدمن موثوق بالخادم (للسياسات) |
| Storage: bucket خاص `dev-addon` | **جديد** — سياسة قراءة للأدمن فقط؛ بلا كتابة من العميل (ارفع `dev-addon.js` من الداشبورد) |
| صلاحيات الدوال | `revoke … from public, anon` ثم `grant execute … to authenticated` |

إضافة نفسك أدمن (من SQL Editor):
```sql
insert into public.admins(user_id) select id from auth.users where email = 'your@email.com';
```

---

## D. دليل الإعداد (يدوي — لازم تسويه أنت)

### 1) Google Cloud Console
1. اختر/أنشئ مشروع.
2. **OAuth consent screen** (أو *Google Auth Platform*): اكتب اسم التطبيق وإيميل الدعم. إذا الحالة *Testing* فقط الحسابات المضافة كـ Test users تقدر تدخل؛ انشر (*In production*) إذا تريد الكل.
3. **Credentials → Create credentials → OAuth client ID → Web application.**
4. **Authorized redirect URIs** (هذا عنوان Supabase وليس عنوان تطبيقك):
   `https://<PROJECT_REF>.supabase.co/auth/v1/callback`
5. *Authorized JavaScript origins*: مو مطلوب لهذا المسار (الدخول يمر عبر خادم Supabase).
6. انسخ **Client ID** و**Client Secret**.

### 2) Supabase Dashboard
1. **Authentication → Sign In / Providers → Google** → فعّله وحط Client ID و Client Secret.
2. **Authentication → URL Configuration**
   - **Site URL**: أصل تطبيقك، مثل `https://your-domain.com`
   - **Redirect URLs**: العنوان **الحرفي** الذي يرجّع له التطبيق = `origin + pathname` للصفحة. أمثلة:
     - `https://your-domain.com/CODIS_9-7-2_auth.html`
     - للتجربة المحلية: `http://localhost:8080/CODIS_9-7-2_auth.html`
   - ⚠️ إذا العنوان مو بالقائمة، Supabase **ما يعطي خطأ**؛ يرجّعك لـ Site URL بصمت.
3. **Project Settings → API**: انسخ **Project URL** و**anon / publishable key** فقط. **لا تنسخ `service_role` / `secret`.**
4. **SQL Editor**: شغّل `codis_supabase_setup.sql` كاملاً.
5. (اختياري، للأدمن) Storage → bucket `dev-addon` → ارفع `dev-addon.js`.

### 3) حط القيم بالتطبيق
بالـ `<head>` من `CODIS_9-7-2_auth.html`:
```html
<meta name="codis-supabase-url" content="https://xxxx.supabase.co">
<meta name="codis-supabase-key" content="eyJ…أو sb_publishable_…">
```
المفتاح العام معمول يكون ظاهر؛ الحماية الفعلية هي RLS بالـ SQL.

---

## E. النشر
- **لازم HTTPS** (أو `http://localhost`). فتح الملف بـ `file://` = الدخول بـ Google معطّل (رسالة تظهر بصفحة الحساب).
- أسهل: أي استضافة ملفات ثابتة (Netlify / Cloudflare Pages / GitHub Pages / Vercel) أو محلياً:
  `python3 -m http.server 8080` ثم افتح `http://localhost:8080/CODIS_9-7-2_auth.html`.
- العنوان اللي تفتحه لازم يطابق حرفياً الـ Redirect URL المضاف بـ Supabase (نفس النطاق والمنفذ والمسار).
- ⚠️ إذا تغلّف CODIS كتطبيق سطح مكتب (Electron/WebView) بأصل غير http(s) مثل `app://`، الرجوع من Google ما راح يشتغل بدون معالجة deep-link (غير موجودة بالكود). الحل الأبسط: يفتح من `http://localhost`.

---

## F. نتائج الاختبار (حقيقية)

بيئة الاختبار: Node 22 + **PostgreSQL 16 حقيقي** ينفّذ ملف الـ SQL نفسه؛ طبقات Supabase (GoTrue/PostgREST/Storage) مُحاكاة بـ mock يوجّه الطلبات للدوال الحقيقية بدور `authenticated` و`auth.uid()` من JWT.

**اجتاز:**
- Syntax: 7 سكربتات داخل الملف (الأصلي والمعدّل) بلا أخطاء.
- SQL مرتين متتاليتين (idempotent) بلا أخطاء.
- **87/87** فحص عميل↔قاعدة بيانات (`tests/harness.js`)، منها:
  - التحقق من الإعداد (13 حالة): رفض service_role/sb_secret، رابط خطأ، file://، إلخ؛ والأولوية OVERRIDE > meta.
  - PKCE: مطابقة RFC 7636، بناء الرابط، redirect_to، التحقق بالخادم المحاكى أن `sha256(verifier)==challenge`.
  - أول دخول، رجوع مستخدم بجهاز ثاني (استرجاع)، إعادة تحميل بجلسة صالحة (بدون طلبات توكن)، معالجة الكود مرة واحدة، رفض كود بلا verifier / verifier قديم، رفض توكنات الـ fragment.
  - إلغاء المستخدم، المزوّد معطّل، مفتاح مرفوض، خادم غير متاح — بدون تحويل لصفحة خطأ.
  - جلسة منتهية: تجديد، تجديد مرفوض (حالة expired بلا حلقة وبلا مساس بالتقدّم المحلي)، تجديد متزامن = طلب واحد.
  - انقطاع الشبكة: يحتفظ بالتقدّم، يعيد المحاولة، ويحفظ عند عودة الاتصال.
  - تعارض جهازين (الخيارين) + نسخة احتياطية.
  - خروج ثم دخول بحساب ثاني: لا تسرب بيانات (محلياً ولا بالخادم)؛ تبديل حساب بدون خروج.
  - أخطاء الخادم: دالة ناقصة / جدول ناقص / RLS (رسالة عربية، بلا إعادة محاولة)، 5xx (يعيد المحاولة).
  - الأدمن: غير الأدمن لا يطلب الإضافة ولا يقدر يحمّلها مباشرة (404)، والأدمن يحمّلها.
  - حذف الحساب: فشل الخادم لا يُعرض كنجاح؛ النجاح يحذف الهوية والبيانات ويمسح المحلي؛ توكن الحساب المحذوف ما يقدر يعيد إنشاء بيانات.
- **SQL مباشر** (`tests/sql_test_results.txt`): anon مرفوض بكل شي؛ مستخدم لا يرى/يعدّل/يحذف صف غيره؛ RPC يكتب لصاحب الـ JWT فقط؛ تعارض النسخ؛ رفض payload غير object/أكبر من 8MB؛ ما كو ترقية ذاتية لأدمن؛ bucket الأدمن مقفول على غيره؛ كل الدوال بـ `search_path` مثبّت؛ RLS مفعّل.

**ما قدرت أنفّذه (يحتاج وصول/اعتمادات منك):**
- دخول فعلي بحساب Google + Supabase حقيقي (GoTrue حقيقي، Redirect URLs، Client Secret).
- التأكد من أن `delete from auth.users` داخل الدالة يعمل بصلاحيات مشروعك الحقيقي (شغّل `delete_my_account` على حساب تجريبي).
- النشر على HTTPS، وسلوك الجوال/التطبيق المغلّف.
- فحص بصري للواجهة بمتصفح (ما شغّلت المتصفح؛ التعديلات على الواجهة سطرين نصيين).
- رفع `dev-addon.js` الحقيقي واختباره.

---

## G. العوائق المتبقية (يدوية)
1. إنشاء OAuth client بـ Google وإضافة redirect URI الخاص بـ Supabase.
2. تفعيل Google provider بـ Supabase + Client ID/Secret.
3. ضبط Site URL و Redirect URLs.
4. تشغيل `codis_supabase_setup.sql` (بعد مراجعة أي جداول/دوال موجودة مسبقاً بنفس الأسماء).
5. لصق Project URL + anon/publishable key بالـ `<meta>`.
6. نشر التطبيق على HTTPS (أو localhost).
7. اختبار حيّ: دخول → حفظ → جهاز ثاني → خروج → حذف حساب تجريبي.
8. (اختياري) إضافتك لـ `admins` ورفع `dev-addon.js`.

## ملاحظات أمان متبقية (قرارات مو أخطاء)
- التوكنات (بما فيها refresh token) محفوظة بـ localStorage — طبيعي لتطبيق بلا خادم، لكن أي ثغرة XSS تكشفها. التطبيق بلا CSP؛ يُنصح بإضافة CSP عند النشر.
- نسختان احتياطيتان محليتان (`codis_bk_*`) قد تحتويان بيانات الحساب السابق بعد الخروج (شبكة أمان عند التعارض)؛ تُمسح عند حذف الحساب مع «احذف بيانات الجهاز». غير ظاهرة بالواجهة.
- إضافة المطوّر تُنفَّذ ككود قادم من الخادم لحساب الأدمن فقط (بتصميمك): احمِ حساب الأدمن (2FA).
