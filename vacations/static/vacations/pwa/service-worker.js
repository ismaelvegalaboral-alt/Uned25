const CACHE_VERSION = 'kalpae-ausencias-pwa-v3';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const STATIC_ASSETS = [
  '/static/vacations/css/app.css',
  '/static/vacations/pwa/kalpae-white-icon-192.png',
  '/static/vacations/pwa/kalpae-white-icon-512.png',
  '/static/vacations/pwa/kalpae-white-apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.map(key => {
        if (!key.startsWith(CACHE_VERSION)) {
          return caches.delete(key);
        }
      })))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        const fetchPromise = fetch(request).then(response => {
          if (response && response.ok) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then(cache => cache.put(request, clone));
          }
          return response;
        }).catch(() => cached);

        return cached || fetchPromise;
      })
    );
  }
});

self.addEventListener('push', event => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (error) {
    data = {
      title: 'Kalpae Ausencias',
      body: event.data ? event.data.text() : 'Nueva notificación'
    };
  }

  const title = data.title || 'Kalpae Ausencias';
  const options = {
    body: data.body || '',
    icon: data.icon || '/static/vacations/pwa/kalpae-white-icon-192.png',
    badge: data.badge || '/static/vacations/pwa/kalpae-white-icon-192.png',
    data: {
      url: data.url || '/'
    }
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const targetUrl = event.notification.data && event.notification.data.url ? event.notification.data.url : '/';

  event.waitUntil(
    clients.matchAll({type: 'window', includeUncontrolled: true}).then(clientList => {
      for (const client of clientList) {
        if ('focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
