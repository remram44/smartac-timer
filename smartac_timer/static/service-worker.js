self.addEventListener('install', function(evt) {
    console.log("The service worker is being installed");
    evt.waitUntil(caches.open('cache').then(function(cache) {
        cache.addAll(['index.html']);
    }));
});

self.addEventListener('fetch', function(e) {
    e.respondWith(
        caches.match(e.request).then(function(r) {
            console.log('[Service Worker] Fetching resource: ', e.request.url);
            return r || fetch(e.request).then(function(response) {
                return caches.open(cacheName).then(function(cache) {
                    console.log('[Service Worker] Caching new resource: ', e.request.url);
                    cache.put(e.request, response.clone());
                    return response;
                });
            });
        })
    );
});
