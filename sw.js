/* CODIS service worker — v3.
   • الصفحة (التنقّل وindex.html): الشبكة أولاً، والكاش احتياطاً بلا اتصال → التحديثات تظهر فوراً بدل بقاء نسخة قديمة.
   • بقية الملفات الثابتة: الكاش أولاً.
   • طلبات غير GET وطلبات Supabase (حسابات/مزامنة/تخزين) لا تُخزَّن ولا تُعترَض أبداً.
   • v3 (CODIS-TIMERS): إشعارات Web Push من الخادم (انتهاء المؤقتات والتطبيق مسكّر) + فتح التطبيق عند الضغط على الإشعار. */
const CACHE = 'codis-pwa-v3';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon.svg'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
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
    event.respondWith(
      fetch(req).then(response => {
        const copy = response.clone();
        caches.open(CACHE).then(cache => cache.put(req, copy));
        return response;
      }).catch(() => caches.match(req).then(c => c || caches.match('./index.html')))
    );
    return;
  }
  event.respondWith(
    caches.match(req).then(cached =>
      cached || fetch(req).then(response => {
        const copy = response.clone();
        caches.open(CACHE).then(cache => cache.put(req, copy));
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

