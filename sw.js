/* CODIS service worker — v6.
   • v6 (CODIS-BUTTER): الصور رجعت مدفونة بالصفحة (ملف واحد)؛ لا تحميل صور مسبق، والكاش القديم (v5 وصوره) يُمسح.
   • v5 (CODIS-ASSETS): صور التطبيق ملفات ثابتة الأسماء تُحمَّل مسبقاً للعمل بلا إنترنت؛ الصفحة: الشبكة أولاً بمهلة 3.5ث ثم الكاش.
   • الصفحة (التنقّل وindex.html): الشبكة أولاً، والكاش احتياطاً بلا اتصال → التحديثات تظهر فوراً بدل بقاء نسخة قديمة.
   • بقية الملفات الثابتة: الكاش أولاً.
   • طلبات غير GET وطلبات Supabase (حسابات/مزامنة/تخزين) لا تُخزَّن ولا تُعترَض أبداً.
   • v3 (CODIS-TIMERS): إشعارات Web Push من الخادم (انتهاء المؤقتات والتطبيق مسكّر) + فتح التطبيق عند الضغط على الإشعار.
   • v4 (CODIS-OFFLINE): Background Sync ('codis-sync' ← يوقظ صفحات التطبيق المفتوحة لتكمل الرفع) + pushsubscriptionchange (يطلب من الصفحة إعادة الاشتراك).
     ملاحظة صريحة: الـSW لا يحمل جلسة الحساب، فلا يرفع بنفسه والتطبيق مغلق؛ الرفع يتم من الصفحة (online/visibility/focus/pageshow). */
const CACHE = 'codis-pwa-v6';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon.svg'];
const IMAGES = [];
const PAGE_TIMEOUT = 3500;

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(async cache => {
    await cache.addAll(ASSETS);
    /* الصور: كل ملف لوحده (فشل واحد لا يُفشل التثبيت)، والموجود بالكاش القديم يُنقل بلا تنزيل */
    const old = (await caches.keys()).filter(k => k !== CACHE);
    await Promise.all(IMAGES.map(async u => {
      if (await cache.match(u)) return;
      for (const k of old) { const r = await (await caches.open(k)).match(u); if (r) { await cache.put(u, r); return; } }
      try { const r = await fetch(u, { cache: 'reload' }); if (r.ok) await cache.put(u, r); } catch (e) {}
    }));
  }));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // Supabase وكل ما هو خارج الموقع: مباشرة من الشبكة
  const isPage = req.mode === 'navigate' || url.pathname.endsWith('/') || url.pathname.endsWith('/index.html');
  if (isPage) {
    /* الشبكة أولاً؛ إن تأخرت أكثر من PAGE_TIMEOUT تُعرض النسخة المخزّنة فوراً، والطلب يكمل ويحدّث الكاش للفتحة الجاية */
    const net = fetch(req).then(response => {
      if (response && response.ok) { const copy = response.clone(); caches.open(CACHE).then(cache => cache.put(req, copy)); }
      return response;
    });
    event.waitUntil(net.catch(() => {}));
    const cached = () => caches.match(req).then(c => c || caches.match('./index.html'));
    event.respondWith(new Promise(resolve => {
      let done = false;
      const timer = setTimeout(() => { cached().then(c => { if (!done && c) { done = true; resolve(c); } }); }, PAGE_TIMEOUT);
      net.then(r => { if (!done) { done = true; clearTimeout(timer); resolve(r); } })
         .catch(() => cached().then(c => { if (!done) { done = true; clearTimeout(timer); resolve(c || Response.error()); } }));
    }));
    return;
  }
  event.respondWith(
    caches.match(req).then(cached =>
      cached || fetch(req).then(response => {
        if (response && response.ok) { const copy = response.clone(); caches.open(CACHE).then(cache => cache.put(req, copy)); }
        return response;
      }).catch(() => caches.match('./index.html'))
    )
  );
});

/* Web Push: الحمولة من supabase/functions/codis-push — { title, body, tag, url }. نفس الوسم (معرّف حدث المؤقت) يمنع التكرار مع إشعار الصفحة */
self.addEventListener('push', event => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch (e) { d = { body: event.data ? event.data.text() : '' }; }
  const title = d.title || 'CODIS';
  event.waitUntil(self.registration.showNotification(title, {
    body: d.body || '', tag: d.tag || 'codis', renotify: false, lang: 'ar', dir: 'rtl',
    icon: 'icon.svg', badge: 'icon.svg', data: { url: d.url || './' }
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = new URL((event.notification.data && event.notification.data.url) || './', self.registration.scope).href;
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
    for (const c of list) { if (c.url.startsWith(self.registration.scope) && 'focus' in c) return c.focus(); }
    return self.clients.openWindow ? self.clients.openWindow(target) : null;
  }));
});


/* Background Sync: عند عودة الاتصال يرسل SW رسالة لكل صفحة مفتوحة لتبدأ المزامنة (لا بيانات ولا رموز داخل SW) */
self.addEventListener('sync', event => {
  if (event.tag !== 'codis-sync') return;
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => { list.forEach(c => c.postMessage({ type: 'codis-sync' })); }));
});

/* انتهاء/تبديل اشتراك Push من المتصفح: الصفحة هي التي تملك المفتاح العام وجلسة الحساب، فنطلب منها إعادة الاشتراك */
self.addEventListener('pushsubscriptionchange', event => {
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => { list.forEach(c => c.postMessage({ type: 'codis-push-resub' })); }));
});
