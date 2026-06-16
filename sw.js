// ── SERVICE WORKER — Valmiki Ramayana PWA ──
const CACHE = 'ramayana-v1';
const OFFLINE_ASSETS = [
  '/',
  '/index.html',
  '/app.js',
  '/style.css',
  '/manifest.json',
  '/data/ramayana.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  'https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@300;400;500;600&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap'
];

// Install: cache all app shell assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(OFFLINE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate: remove old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch: cache-first for app assets, network-first for translations
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Always serve app shell from cache
  if (OFFLINE_ASSETS.some(a => e.request.url.endsWith(a) || url.pathname === '/')) {
    e.respondWith(
      caches.match(e.request).then(cached => cached || fetch(e.request))
    );
    return;
  }

  // For ramayana.info translation fetches: network first, fall through to offline message
  if (url.hostname === 'ramayana.info') {
    e.respondWith(
      fetch(e.request).catch(() =>
        new Response(JSON.stringify({ error: 'offline' }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
    );
    return;
  }

  // Default: try cache, then network
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
