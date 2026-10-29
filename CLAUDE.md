# CODIS — project context for Claude Code

> ## ⚠️ ADMIN EXEMPTION RULE — read before changing ANY restriction (owner's standing instruction)
> The **developer/admin account must have no limits at all** (absolute freedom over the app: coins, silver, inventory, prices, box probabilities, data).
> Therefore **every limit, cap, threshold, price/balance check, eligibility rule, lock, cooldown or anti-abuse guard that restricts the USER must be routed through `CodisLimits`**
> (defined next to `CodisWallet` in `app/CODIS_FINAL.html`; produced by `tools/patch_power.py`):
> - hard block (refusal) → `if(cond && !CodisLimits.bypass('area.name')) return refusal;` (register a label: `CodisLimits.reg(id, label)`)
> - balance check → `CodisLimits.afford(have, need)` · numeric constant → `CodisLimits.num('id', normalValue)` (+ `CodisLimits.reg('id', label, normal)` so the panel lists it)
> The verified developer (`CodisAccount.isAdmin()` = server RLS allowed `public.admins` + private add-on download) then passes automatically; **normal users are never affected.**
> Do NOT add a restriction that skips this, even if the task says "prevent abuse/exploits" — implement it *with* the exemption. `node tests/limits_check.js` fails if you do.
> Never expose the admin flag on a mutable object (it is the private `adminOK` in `CodisAccount`). Server-side powers live only in `sql/codis_admin.sql` and always re-check `public.admins`.

CODIS is a **single-file Arabic (RTL) HTML app** (life organizer / game). All UI + JS live in ONE html file. Do not split it, redesign it, or remove features.

## Layout
- `src/CODIS_9-7-3.html` — **latest authoritative app (user must place it here; NOT yet provided).** `src/CODIS_9-7-2.html` is the older base the auth work was built on.
- `app/CODIS_FINAL.html` — 9-7-2 + auth/sync fixes (byte-reproducible via `tools/patch.py`).
- `tools/patch_v12.py` — CODIS-AUDIT-1: إصلاحات تدقيق: تمركز اليوم النشط بشريط أيام العمليات، مجموعات الإعدادات (لا مجموعة فارغة)، أيقونة قمر لساعات الهدوء، نص تخزين رمز القفل مطابق للمزامنة، أصفار سجل الكوينز، نص يشير لصفحة محذوفة (بعد patch_v11). مسح الواجهة: tests/sweep_browser.js (26 شاشة: تجاوز أفقي/قص نص/صور مكسورة/أزرار بلا اسم/أهداف لمس صغيرة/IDs مكررة/أخطاء console).
- `tools/patch_v11.py` — CODIS-AUDIO-V2: إعادة بناء الصوت: نواقل قنوات + خفض + ستيريو + رنين مادي/FM/حبيبات/هواء + تنويع + سرقة أصوات + `name@ctx` (codemod يمرّر ctx من الدالة المحيطة) + أحداث جديدة (قلم المهام، قلب البطاقة، المنجزة، ×10…). الخريطة: docs/CODIS_AUDIO_MAP.md. فحص ساكن: tests/audio_check.js · تشغيلي: tests/audio_browser.js (تصيير offline لكل هوية + تشغيل حي). أي صوت جديد: عرّفه كـ `اسم@سياق` ومرّر `{ ctx }`، ولا تضف استدعاءات عامة.
- `tools/patch_v10.py` — CODIS-BULK-V3: فتح ×10 سينمائي على مسرح واحد (`CodisBulkCinema`): صندوق بعد صندوق تصاعدياً بالقيمة، الإيقاع والشدّة من مجموعة القيمة (1..5) عبر `econBulkSchedule`، الكرت يطير لخانته بالشريط، نقر المسرح يسرّع الصندوق الحالي، التخطّي للنتائج؛ عرض فقط (بعد patch_v9). اختبار: tests/bulk_browser.js (يستعمل `CodisBulkCinema._seek`).
- `tools/patch_v9.py` — CODIS-BULK-V2: فتح ×10: جدول زمني حسب مستوى القيمة (`econBulkSchedule`)، شدّة حركة/تسليط/نغمة/اهتزاز بالمستوى، بطاقة مكبّرة قابلة للقلب عند النقر بعد الانتهاء، كل المؤقّتات بـtoken (بعد patch_v8). اختبار: tests/bulk_browser.js.
- `tools/patch_v8.py` — CODIS-PACKUI: معاينة البكج: ترويسة + شريط توزيع + مفتاح نقر + أقسام فئات قابلة للطي بصفوف أفقية (الأرقام من `CodisBoxes.effective`) (بعد patch_v7).
- `tools/patch_v7.py` — CODIS-CARDS-V2: إزالة حشوة الإطار 4:5 مركزياً (`--card-pad:0`, `.rwc{padding:0}`) + ظهر بطاقة مولَّد SVG لكل ندرة×نوع (`codisBackOrnament`) (بعد patch_v6). اختبار: tests/cards_browser.js.
- `tools/patch_v6.py` — CODIS-BOXES-V4: نموذج احتمالات الصناديق: نطاقات قيمة ثابتة، ρ لكل مستوى (عائد البيع/السعر .78→.93 ⇒ لا ربح مضمون)، سقف نفايات، حدّ أدنى 0.4%، تقريب بالألف بأكبر باقٍ؛ `effectiveBase` هو المصدر الوحيد للسحب والعرض؛ بلا Pity (بعد patch_v5). اختبار: tests/boxes_model_browser.js.
- `tools/patch_v5.py` — CODIS-V5-NAV: الرجوع/السحب: `codisBackLayer` + `CodisNav.back()` مالك وحيد (قفل 380ms) + حارس History (base/top) + popstate ← رجوع داخلي واحد + سحب تفاعلي يتبع الإصبع (حيث لا سحب أصلي) + signIn بـ`location.replace` + pageshow يعيد تقييم بوابة الدخول من الجلسة (بعد patch_v4). اختبار: tests/nav_browser.js.
- `tools/patch_v4.py <in> <out>` — CODIS-V4: مسار المهام (غرفتا العمليات والأستاذ): «نصها» تفتح لوحة نسبة (1–99) ولا تكشف نتيجة قبل الاختيار والتأكيد · حركات قلم ✓/✕/تظليل نسبي (`CodisPen`) · المحسومة تخرج من القائمة النشطة إلى نافذة «المنجزة» · استرجاع آمن (`CodisTaskFlow.restore`: لا معاملة مالية، نتيجة اليوم المعلّقة تُلغى بـvoid والمحسومة تبقى) (بعد patch_v3.py). اختبار: tests/taskflow_browser.js. حدّ معروف: إذا اكتملت كل مهام الخطة تُؤرشف تلقائياً ولا استرجاع من الأرشيف.
- `tools/patch_v3.py <in> <out>` — CODIS-V3: إعادة تصميم غرفة التأديب (بطاقة عادة: 3 أرقام ظاهرة + «التفاصيل» قابلة للطي) (بعد patch_v2.py).
- `tools/patch_v2.py <in> <out>` — CODIS-V2: حذف صفحتي «قواعد المكافآت» و«حدود الإنجاز» ومحرّر وزن المهام (القواعد داخلية ثابتة؛ ترحيل `rulesLockedV2` يعيد القيم الافتراضية مرة وحدة)، حذف النسخ الاحتياطي اليدوي، حذف عبارة «بياناتك بجهازك بس»، ومصدر إصدار واحد (بعد patch_rules.py). فحص: tests/cleanup_check.js.
- **الإصدار**: مصدره الوحيد ملف `VERSION` → `python tools/set_version.py [x.y.z]` يختمه في `<meta name="codis-version">` داخل app/CODIS_FINAL.html (والواجهة تقرأ الوسم). بعد تشغيل سلسلة patch_* شغّل `set_version.py`. فحص: `node tests/version_check.js`. إصدار جديد = غيّر الرقم بهذا السكربت فقط ثم انسخ الملف إلى index.html.
- `tools/patch_rules.py <in> <out>` — CODIS-RULES: توزيع بكجات موحّد (82.7%) + حماية احتمالات الندرة + منع حصاد المهام (يوم/خطة/أسبوع/شهر) + عادة أسبوعية بيوم مميّز + مكافأة قاومت/خصم وقعت + هوية الأهمية (بعد patch_power.py). اختبار: tests/economy_rules_browser.js.
- `tools/patch_power.py <in> <out>` — CODIS-POWER: `CodisLimits` (إعفاء المطوّر من كل قيد) + تجاوز القيود الحالية + تعديل نسب البكجات/الأسعار/الثوابت للمطوّر + شاشة البداية: حالة نصية وفشل صريح (بعد patch_admin.py). اللوحة: `addons/dev/adapt_power.js`. حارس: `tests/limits_check.js`.
- `tools/patch_admin.py <in> <out>` — CODIS-ADMIN: استلام هدايا ورسائل المطوّر (صفوف المستخدم نفسه فقط) + `CodisAccount.adminCall` للّوحة. الخادم: `sql/codis_admin.sql`؛ اللوحة: `addons/dev/adapt_admin.js` (بعد patch_mobile.py). فحوص: `tests/run_admin_sqltest.js`.
- `tools/patch_mobile.py <in> <out>` — CODIS-MOBILE: المتجر صفحة كاملة داخل .main (إصلاح iOS) + content-visibility للأقسام البعيدة + صور blob + حركة غرفة واحدة على اللمس (بعد patch_perf.py).
- `tools/patch_perf.py <in> <out>` — CODIS-PERF: إغلاق طبقة المتجر عند التنقّل + data-view + شريط إقلاع حقيقي + شارات المباعة/المستخدمة + فتح أكياس بالكمية + تفكيك البطاقات المنتهية (25 فضة) (بعد patch_dev.py).
- `tools/patch_dev.py <in> <out>` — حاجز CODIS_SYNC_HOLD لمنع مزامنة بيانات معاينة المطوّر (بعد patch_toast.py). إضافة المطوّر نفسها: `tools/build_devaddon.py` ← `addons/dev-addon.js` (ترفع يدوياً إلى bucket dev-addon، للأدمن فقط).
- `tools/patch_toast.py <in> <out>` — يؤجّل إشعار شراء الصناديق إلى ما بعد إغلاق نافذة الفتح (يُشغَّل بعد patch_boxes.py).
- `tools/patch_boxes.py <in> <out>` — صناديق CODIS-BOXES-V3: الرسومات الخمسة (من tools/boxes/art، والأصول في assets/box_art_original) + مجسّم/طقس فتح + كشف بمستويات + ×10 + عتبات القيمة (يُشغَّل بعد patch_avatar.py).
- `tools/patch_avatar.py <in> <out>` — الصورة الشخصية (Google تلقائياً + مخصّصة بالقص) تحل محل أيقونتي الحساب والإعدادات (يُشغَّل بعد patch_profile.py).
- `tools/patch_profile.py <in> <out>` — يضيف شاشة «معلوماتك» بعد الدخول (يُشغَّل بعد patch.py؛ إخراجه = app/CODIS_FINAL.html الحالي).
- `tools/patch.py <src> <out>` — applies the auth changes to a copy; asserts each replaced string exists exactly once, fails loudly if the app changed.
- `sql/codis_supabase_setup.sql` — idempotent schema/RLS/RPC for a fresh Supabase project.
- `tests/` — `syntax.js` (inline-script parse), `harness.js` (87 client<->real-Postgres checks with a mocked GoTrue/PostgREST/Storage layer), `sqltest.sql` + `stub.sql` (RLS/RPC checks). They assume Linux + local PostgreSQL 16 with `su postgres`; adapt paths/runner if your machine differs (docker/pglite are fine).
- `docs/` — setup guide, test report, earlier audit report.

## Auth architecture (module `CodisAccount`, near end of the HTML)
Supabase REST directly (no SDK), Google OAuth via `/auth/v1/authorize?flow_type=pkce`, code exchange `grant_type=pkce`, session in localStorage, snapshot sync via RPC `save_progress(p_data, p_base_version)` with optimistic versioning, `delete_my_account()`, admins via RLS + private storage bucket `dev-addon`.
Config priority: `window.CODIS_BACKEND_OVERRIDE` > `<meta name="codis-supabase-url|key">` > `CODIS_BACKEND` const.

## Hard rules
- NEVER put `service_role`/secret keys, Google client secret, or passwords in any file. Only Project URL + anon/publishable key (public by design; RLS is the real protection).
- The user pastes the public URL/key into the `<meta>` tags themselves.
- Never disable RLS or grant broad access to fix a permission error.
- Don't fabricate test results; label simulated tests as simulated. Real Google login and real Supabase can only be verified by the user in a browser.
- Keep user-facing messages in Arabic; keep technical diagnostics in console without tokens.
- Serve over http://localhost or https (file:// cannot complete OAuth).
