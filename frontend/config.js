// ─────────────────────────────────────────────────────────────
// TruthLens — API Configuration
// ─────────────────────────────────────────────────────────────
// Points to your live Railway backend in production, or localhost in development
// ─────────────────────────────────────────────────────────────

const CONFIG = {
    API_BASE: (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:8000'
        : 'https://truthlens-backend-production-33a8.up.railway.app'
};
