/* Nagoya Journey — offline support */
const SHELL_CACHE = "shell-v7";
const TILE_CACHE = "tiles-v2";

/* remote map/photo hosts whose responses are cached for offline use */
const MAP_HOSTS = ["tiles.openfreemap.org", "server.arcgisonline.com", "upload.wikimedia.org"];
const SHELL = [
  "./",
  "index.html",
  "style.css",
  "app.js",
  "manifest.webmanifest",
  "vendor/maplibre-gl.js",
  "vendor/maplibre-gl.css",
  "icons/icon-192.png",
  "icons/icon-512.png",
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL_CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== SHELL_CACHE && k !== TILE_CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

async function trimCache(name, max) {
  const cache = await caches.open(name);
  const keys = await cache.keys();
  if (keys.length > max) {
    await cache.delete(keys[0]);
    return trimCache(name, max);
  }
}

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);

  // map data (style, fonts, sprites, tiles) + waypoint photos: cache-first,
  // capped — whatever you viewed online stays viewable offline
  if (MAP_HOSTS.includes(url.hostname)) {
    e.respondWith(
      caches.open(TILE_CACHE).then(async cache => {
        const hit = await cache.match(e.request);
        if (hit) return hit;
        try {
          const resp = await fetch(e.request);
          if (resp.ok) {
            cache.put(e.request, resp.clone());
            trimCache(TILE_CACHE, 1200);
          }
          return resp;
        } catch {
          return new Response("", { status: 503 });
        }
      })
    );
    return;
  }

  // app shell: cache-first, then network fallback (so the app opens with no signal)
  if (e.request.method === "GET" && url.origin === location.origin) {
    e.respondWith(
      caches.match(e.request).then(hit => hit || fetch(e.request).then(resp => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(SHELL_CACHE).then(c => c.put(e.request, clone));
        }
        return resp;
      }))
    );
  }
});
