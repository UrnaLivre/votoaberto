{{flutter_js}}
{{flutter_build_config}}

// Retire only Flutter's former worker at this app's root. Other registrations
// and unrelated browser caches are untouched. No new service worker is installed.
(async function start() {
  try {
    if ('serviceWorker' in navigator) {
      const root = new URL('.', document.baseURI).href;
      const legacyUrl = new URL('flutter_service_worker.js', root).href;
      const registrations = await navigator.serviceWorker.getRegistrations();
      const legacy = registrations.filter(registration =>
        registration.scope === root &&
        [registration.active, registration.waiting, registration.installing]
          .some(worker => worker && worker.scriptURL === legacyUrl));
      if (legacy.length) {
        const controlled = navigator.serviceWorker.controller?.scriptURL === legacyUrl;
        await Promise.all(legacy.map(registration => registration.unregister()));
        if ('caches' in window) {
          await Promise.all(['flutter-app-cache', 'flutter-temp-cache', 'flutter-app-manifest']
            .map(name => caches.delete(name)));
        }
        if (controlled) {
          location.reload();
          return;
        }
      }
    }
  } catch (error) {
    // Browser privacy settings may forbid service worker/cache access.
    console.warn('Não foi possível verificar o cache Flutter legado.', error);
  }
  _flutter.loader.load();
})();
