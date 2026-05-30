// Production API base URL with local development fallback
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.__UDAAN_API_BASE__ = 'http://127.0.0.1:8000/api';
} else {
    window.__UDAAN_API_BASE__ = 'https://funwitharts-production.up.railway.app/api';
}