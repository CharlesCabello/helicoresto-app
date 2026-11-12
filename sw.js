const CACHE='helicoresto-shell-v3';
const ASSETS=['./','./index.html','./style.css','./app.js','./manifest.webmanifest','./assets/icon.svg','./assets/apple-touch-icon.png','./data/fallback-data.js','./data/venues.json'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const req=e.request;if(req.method!=='GET'||new URL(req.url).origin!==self.location.origin)return;
 e.respondWith(fetch(req).then(response=>{if(response.ok){const clone=response.clone();e.waitUntil(caches.open(CACHE).then(c=>c.put(req,clone)))}return response}).catch(()=>caches.match(req).then(r=>r||Response.error())));
});
