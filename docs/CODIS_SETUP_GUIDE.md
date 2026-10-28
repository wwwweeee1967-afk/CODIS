# دليل الإعداد — CODIS (تسجيل الدخول بـ Google + المزامنة)

> **تنبيه مهم:** `CODIS_FINAL.html` مبني على `CODIS_9-7-2.html` + تعديلات الدخول. النسخة `9-7-3` لم تصل المحادثة، فأي ميزة أضفتها فيها غير موجودة هنا. عند رفع 9-7-3 تُطبَّق نفس التعديلات عليها.

## قبل البدء — شنو تحتاج
- حساب Supabase (مجاني) وحساب Google.
- مكان يشغّل الملف عبر **https://** أو **http://localhost** (فتح الملف بالنقر المزدوج `file://` لا يصلح للدخول بـ Google؛ التطبيق يشتغل كضيف فقط).

## الخطوة 1: مشروع Supabase
1. supabase.com ← New project ← اختر اسم وكلمة سر لقاعدة البيانات (احفظها، ما نحتاجها بالتطبيق).
2. بعد ما يجهز: **Project Settings → API**. انسخ:
   - **Project URL** (مثل `https://abcd.supabase.co`)
   - **anon / publishable key**
   - ⛔ لا تنسخ `service_role` أو `secret` أبداً.

## الخطوة 2: قاعدة البيانات
1. **SQL Editor → New query**.
2. افتح `codis_supabase_setup.sql`، انسخ كل محتواه، الصقه، اضغط **Run**.
3. المفروض يطلع Success. الملف آمن للتشغيل أكثر من مرة.
4. حتى تكون أدمن (اختياري): شغّل
   `insert into public.admins(user_id) select id from auth.users where email='إيميلك';`
   (بعد ما تسجل دخول مرة وحدة على الأقل).
5. للأدمن فقط: **Storage → bucket dev-addon** (ينشأ تلقائياً) ← ارفع `dev-addon.js`.

**مشروع قديم فيه جداول `progress` أو `admins` أو دوال بنفس الاسم؟** لا تشغّل الملف قبل ما تراجعها؛ الملف يعيد تعريف الدوال ويغيّر الصلاحيات.

## الخطوة 3: Google
1. console.cloud.google.com ← أنشئ/اختر مشروع.
2. **OAuth consent screen** (أو Google Auth Platform): اسم التطبيق + إيميلك. إذا الحالة *Testing*، أضف إيميلك كـ **Test user**، وإلا ما تدخل.
3. **Credentials → Create credentials → OAuth client ID → Web application**.
4. **Authorized redirect URIs** أضف: `https://<PROJECT_REF>.supabase.co/auth/v1/callback` (بدّل PROJECT_REF بالجزء الأول من Project URL).
5. احفظ، وانسخ **Client ID** و **Client Secret**.

(أسماء القوائم بـ Google تتغير أحياناً؛ المهم الحقول المذكورة.)

## الخطوة 4: ربط Google بـ Supabase
1. **Authentication → Sign In / Providers → Google** ← فعّل ← الصق Client ID و Client Secret ← Save.
2. **Authentication → URL Configuration**:
   - **Site URL**: عنوان تطبيقك (مثل `http://localhost:8080` للتجربة).
   - **Redirect URLs**: أضف **العنوان الكامل للصفحة**، مثل `http://localhost:8080/CODIS_FINAL.html`. لازم يطابق حرفياً (النطاق + المنفذ + اسم الملف).

## الخطوة 5: حط القيم بالتطبيق
افتح `CODIS_FINAL.html` بمحرر نصوص، دوّر على `codis-supabase-url` (قريب من أول الملف) واملأ:
```html
<meta name="codis-supabase-url" content="https://abcd.supabase.co">
<meta name="codis-supabase-key" content="مفتاح anon أو publishable">
```

## الخطوة 6: التشغيل
- محلياً: افتح Terminal بمجلد الملف واكتب `python3 -m http.server 8080`، ثم افتح `http://localhost:8080/CODIS_FINAL.html`.
- أو ارفعه على Netlify / Cloudflare Pages / GitHub Pages (يعطيك https تلقائياً؛ أضف عنوانه بـ Redirect URLs).

## اختبار حيّ (5 دقايق)
1. اضغط «الدخول بحساب Google» ← تدخل ← يرجعك للتطبيق.
2. الإعدادات ← الحساب: لازم تشوف إيميلك و«تمّت المزامنة».
3. افتح التطبيق بمتصفح/جهاز ثاني، سجّل بنفس الحساب: لازم يظهر تقدّمك.
4. سجّل خروج ثم دخول بحساب ثاني: ما لازم تشوف بيانات الأول.
5. (آخر شي) جرّب «حذف الحساب» بحساب تجريبي فقط.

## أخطاء شائعة
| الرسالة / العَرَض | السبب والحل |
|---|---|
| «خدمة الحسابات غير مهيّأة» | القيمتان فارغتان بالـ `<meta>` |
| «المفتاح ... ليس المفتاح العام» | حطيت service_role/secret؛ استبدله بـ anon/publishable |
| «لا يعمل عند فتح الملف مباشرة» | شغّله من http://localhost أو https |
| «تسجيل الدخول بحساب Google غير مفعّل» | فعّل Google بالخطوة 4 |
| «المفتاح العام مرفوض» | المفتاح أو الـ URL غلط/من مشروع ثاني |
| «إعداد Google ... Client Secret» | Client ID/Secret غلط بـ Supabase |
| يرجعك لصفحة ثانية بعد Google | الصفحة مو بـ Redirect URLs (Supabase يرجعك لـ Site URL بصمت) |
| Google يقول access blocked / not verified | حالة OAuth *Testing*: أضف إيميلك Test user |
| «دالة/جداول المزامنة غير موجودة» | ما شغّلت `codis_supabase_setup.sql` |
| «لا تملك صلاحية الوصول لبياناتك» | السياسات ما انطبقت؛ أعد تشغيل الـ SQL |
| «انتهت الجلسة» | سجّل دخول مجدداً؛ تقدّمك المحلي ما ضاع |
| «اختلاف بين نسختين» | اختر نسخة؛ الثانية تنحفظ احتياطياً على الجهاز |

للتشخيص: افتح Console بالمتصفح وابحث عن سطور تبدأ بـ `[CODIS auth]` أو `[CODIS sync]` (لا تحتوي توكنات).
