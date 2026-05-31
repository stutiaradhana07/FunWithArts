// Production API base URL with local development fallback
(function () {
  var h = window.location.hostname;
  var isLocal = h === 'localhost' || h === '127.0.0.1' || h.startsWith('192.168.');
  window.__UDAAN_API_BASE__ = isLocal
    ? 'http://127.0.0.1:8000/api'
    : 'https://funwitharts-production.up.railway.app/api';
})();