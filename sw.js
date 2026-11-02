/* CODIS service worker — v5.
   • v5 (CODIS-ASSETS): صور التطبيق ملفات ثابتة الأسماء تُحمَّل مسبقاً للعمل بلا إنترنت؛ الصفحة: الشبكة أولاً بمهلة 3.5ث ثم الكاش.
   • الصفحة (التنقّل وindex.html): الشبكة أولاً، والكاش احتياطاً بلا اتصال → التحديثات تظهر فوراً بدل بقاء نسخة قديمة.
   • بقية الملفات الثابتة: الكاش أولاً.
   • طلبات غير GET وطلبات Supabase (حسابات/مزامنة/تخزين) لا تُخزَّن ولا تُعترَض أبداً.
   • v3 (CODIS-TIMERS): إشعارات Web Push من الخادم (انتهاء المؤقتات والتطبيق مسكّر) + فتح التطبيق عند الضغط على الإشعار.
   • v4 (CODIS-OFFLINE): Background Sync ('codis-sync' ← يوقظ صفحات التطبيق المفتوحة لتكمل الرفع) + pushsubscriptionchange (يطلب من الصفحة إعادة الاشتراك).
     ملاحظة صريحة: الـSW لا يحمل جلسة الحساب، فلا يرفع بنفسه والتطبيق مغلق؛ الرفع يتم من الصفحة (online/visibility/focus/pageshow). */
const CACHE = 'codis-pwa-v5';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon.svg'];
const IMAGES = ["./assets/img/024a8cd3118273b5.webp", "./assets/img/03d985e2eaa4520c.webp", "./assets/img/04ae6b5af7a7dc02.webp", "./assets/img/04f1b2c162c6a6d0.webp", "./assets/img/08a5d5c1eca5254b.webp", "./assets/img/0a85149be9a7bc96.webp", "./assets/img/0c8d8b6ab26af648.webp", "./assets/img/0d8320e4f0f57fde.webp", "./assets/img/0e8b287d4fe8fad2.webp", "./assets/img/1796d1c2dd2d35f1.webp", "./assets/img/1c7539ae9553ddb4.webp", "./assets/img/20826b17a460dd71.webp", "./assets/img/224ae74cd1800572.webp", "./assets/img/231435512a41f49e.webp", "./assets/img/24c18e3c3eb93246.webp", "./assets/img/24d12ff321a87ee5.webp", "./assets/img/2740948d370256c8.webp", "./assets/img/27be29a18b297071.webp", "./assets/img/29ad6f6a289ddce4.webp", "./assets/img/2ade278504793ccf.webp", "./assets/img/2b57698c7644f8f2.webp", "./assets/img/30961564e354645f.webp", "./assets/img/30d6cbaf37990bde.webp", "./assets/img/33cdec57073f9097.webp", "./assets/img/33da59548cc7b9a0.webp", "./assets/img/342209d3d80b27d7.webp", "./assets/img/366cd00fbe80164c.webp", "./assets/img/374d0c3b01402c56.webp", "./assets/img/3be49f8a0e33d42c.webp", "./assets/img/446291dd05a5d5d9.webp", "./assets/img/4797679f800fb193.webp", "./assets/img/4808899e94592f3f.webp", "./assets/img/4e19a2e59b0e4631.webp", "./assets/img/54e748d557701d6f.webp", "./assets/img/58f3e0e845fae478.webp", "./assets/img/5e5c969c166d83e4.webp", "./assets/img/620cb69329253a91.webp", "./assets/img/6562f7503fd62e5c.webp", "./assets/img/66d225b564a79c93.webp", "./assets/img/688445ea09119e7a.webp", "./assets/img/68a42e7373999561.webp", "./assets/img/68a89e4fb305db4e.webp", "./assets/img/6a2a0c2e9fd675a7.webp", "./assets/img/6ac125218caeefa7.webp", "./assets/img/6bdf8da09984647a.webp", "./assets/img/6f3f7d7e5643c9c7.webp", "./assets/img/6f7e0b12fc2a5b2e.png", "./assets/img/732c3d0c72e9cc11.webp", "./assets/img/74166d8981ac798d.webp", "./assets/img/7cce39068f8d720d.webp", "./assets/img/7ce46b3c16d5956f.webp", "./assets/img/7f10d980170317f4.webp", "./assets/img/85080765c09b30c7.webp", "./assets/img/8741f4591ad7c23a.webp", "./assets/img/8add76a4cf3dbbf4.webp", "./assets/img/8bed61335e4d268e.webp", "./assets/img/8bf0c8efb357ecf4.webp", "./assets/img/8fe6e294ca7415ed.webp", "./assets/img/914e3a0f29c9c99e.png", "./assets/img/916f4cd0591cea18.webp", "./assets/img/9242a46421d5be9d.webp", "./assets/img/98a442b9ab927732.webp", "./assets/img/a171b43e654c5f3d.webp", "./assets/img/a2ed1787aef028f5.webp", "./assets/img/a371a7a5aee7b106.webp", "./assets/img/a79d758ee9d6054b.webp", "./assets/img/a882f60f55bfb4ce.webp", "./assets/img/ac6ab09b76b613cc.webp", "./assets/img/ad7f65047ba98c4b.webp", "./assets/img/b3fa0e279fd89d89.webp", "./assets/img/b5c298de61fe3aad.webp", "./assets/img/b9b806585eb831a1.webp", "./assets/img/bd264612a8e66e09.webp", "./assets/img/c38929306fe34ccf.webp", "./assets/img/c390c0e47e262074.webp", "./assets/img/c89fecbdb3003511.webp", "./assets/img/c9eaa38346b3a265.webp", "./assets/img/cb7f7b5ac1dd50d2.webp", "./assets/img/cd8f3f55ee66437d.webp", "./assets/img/cd939ec5046d5f4c.webp", "./assets/img/d0a7251f0ab0764c.webp", "./assets/img/d1faf07b44ee32bf.webp", "./assets/img/d589e64727f024e5.webp", "./assets/img/dc208c5beecf58de.webp", "./assets/img/df6092371bf991f3.webp", "./assets/img/e1a15e94ce49609f.webp", "./assets/img/e299a86eeaaf9c96.webp", "./assets/img/e37660c88440bbba.webp", "./assets/img/e5a9cca7b5ddb452.webp", "./assets/img/e5af233e55b944e9.webp", "./assets/img/ebe2e36f4dc76333.webp", "./assets/img/ee088a3e7b23d2be.webp", "./assets/img/f10a21cfb779f916.webp", "./assets/img/f2a65c6c38cff6b4.webp", "./assets/img/f75a1e1e5fdf9ab4.webp", "./assets/img/fd72f00a78997fdd.webp"];
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
