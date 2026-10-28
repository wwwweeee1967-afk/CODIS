/* CODIS service worker — v2.
   • الصفحة (التنقّل وindex.html): الشبكة أولاً، والكاش احتياطاً بلا اتصال → التحديثات تظهر فوراً بدل بقاء نسخة قديمة.
   • بقية الملفات الثابتة: الكاش أولاً.
   • طلبات غير GET وطلبات Supabase (حسابات/مزامنة/تخزين) لا تُخزَّن ولا تُعترَض أبداً. */
const CACHE = 'codis-pwa-v2';
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
