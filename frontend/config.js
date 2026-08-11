// ─────────────────────────────────────────────────────────────
// TruthLens — API Configuration
// ─────────────────────────────────────────────────────────────
// Automatically uses Netlify same-origin proxy (/api) when deployed on Netlify,
// or direct Render URL / localhost when running elsewhere.
// ─────────────────────────────────────────────────────────────

const CONFIG = {
    API_BASE: (window.location.hostname.includes('netlify.app'))
        ? '/api'
        : (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
            ? 'http://127.0.0.1:8000'
            : 'https://truthlens-1-ue36.onrender.com'
};
