const CACHE_NAME = 'u18-baseball-v4';
const ASSETS = [
  './',
  './u18_players.html',
  './u18_schedule.html',
  './u18_app_data.js',
  './u18_schedule_data.js',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

// Install: cache core assets (개별 캐시 - 일부 실패해도 설치 진행)
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      Promise.all(ASSETS.map(a => cache.add(a).catch(() => {})))
    )
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: network first, fallback to cache
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || e.request.url.includes('/refresh')) return;
  e.respondWith(
    fetch(e.request)
      .then(resp => {
        const clone = resp.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        return resp;
      })
      .catch(() => caches.match(e.request))
  );
});
