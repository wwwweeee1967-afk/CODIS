#!/usr/bin/env python3
"""CODIS-ASSETS: يكتب قسم التخزين في sw.js (v5) — قائمة الصور من assets/img/index.txt (أسماء sha1 ثابتة = لا تتغير أبداً)
+ الصفحة: الشبكة أولاً مع مهلة 3.5ث ثم النسخة المخزّنة (لا شاشة بيضاء بإنترنت ضعيف؛ التحديث يكمل بالخلفية ويظهر بالفتحة الجاية).
Usage: py -3 tools/build_sw.py <sw.js> <assets/img/index.txt>"""
import sys, json
sw, idx = sys.argv[1], sys.argv[2]
t = open(sw, encoding='utf-8').read()
imgs = ['./assets/img/' + l.strip() for l in open(idx, encoding='utf-8') if l.strip()]
head = t[:t.index("const CACHE = ")]
tail = t[t.index("/* Web Push:"):]
head = head.replace("/* CODIS service worker — v4.", "/* CODIS service worker — v5.\n   • v5 (CODIS-ASSETS): صور التطبيق ملفات ثابتة الأسماء تُحمَّل مسبقاً للعمل بلا إنترنت؛ الصفحة: الشبكة أولاً بمهلة 3.5ث ثم الكاش.", 1)
body = """const CACHE = 'codis-pwa-v5';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon.svg'];
const IMAGES = %s;
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

""" % json.dumps(imgs)
open(sw, 'w', encoding='utf-8', newline='').write(head + body + tail)
print('sw ok images', len(imgs))
