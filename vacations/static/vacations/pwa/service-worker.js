const CACHE_VERSION = 'kalpae-ausencias-pwa-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const STATIC_ASSETS = [
  '/static/vacations/css/app.css',
  '/static/vacations/pwa/icon-192.png',
  '/static/vacations/pwa/icon-512.png',
  '/static/vacations/pwa/apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS)).then(() => self.skipWaiting()).catch(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.map(key => {
    if (!key.startsWith(CACHE_VERSION)) return caches.delete(key);
  }))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  // Cache only static assets. Authenticated pages and forms stay network-only.
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(caches.match(request).then(cached => {
      const fetchPromise = fetch(request).then(response => {
        if (response && response.ok) {
          const clone = response.clone();
          caches.open(STATIC_CACHE).then(cache => cache.put(request, clone));
        }
        return response;
      }).catch(() => cached);
      return cached || fetchPromise;
    }));
  }
});
