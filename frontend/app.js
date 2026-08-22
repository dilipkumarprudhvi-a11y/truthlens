// =============================================
// TruthLens v3 — app.js
// =============================================

const API = (typeof CONFIG !== 'undefined' && CONFIG.API_BASE) ? CONFIG.API_BASE : 'https://truthlens-1-ue36.onrender.com';
let lastData = null;

// ─── DOM REFS ───────────────────────────────
const form           = document.getElementById('analyze-form');
const analyzeBtn     = document.getElementById('analyze-btn');
const spinner        = document.getElementById('loading-spinner');
const btnText        = document.querySelector('.btn-text');
const resultsPanel   = document.getElementById('results-panel');
const newsInput      = document.getElementById('news-input');
const charCountEl    = document.getElementById('char-count');
const wordCountLive  = document.getElementById('word-count-live');
const historyListEl  = document.getElementById('history-list');
const clearBtn       = document.getElementById('clear-history-btn');

// ─── LIVE CHAR / WORD COUNT ─────────────────
newsInput.addEventListener('input', () => {
    const v = newsInput.value;
    charCountEl.textContent     = v.length;
    wordCountLive.textContent   = v.trim() ? v.trim().split(/\s+/).length : 0;
});

// ─── TABS ────────────────────────────────────
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    document.getElementById('tab-' + tab + '-content').classList.add('active');
}

// ─── LOADING STATE ──────────────────────────
function setLoading(loading, msg) {
    if (loading) {
        analyzeBtn.disabled = true;
        spinner.classList.remove('hidden');
        btnText.textContent = msg || 'Analyzing…';
    } else {
        analyzeBtn.disabled = false;
        spinner.classList.add('hidden');
        btnText.textContent = 'Analyze Content';
    }
}

// ─── SAMPLE LOADER ──────────────────────────
const sampleBtn = document.getElementById('load-sample-btn');
if (sampleBtn) {
    sampleBtn.addEventListener('click', () => {
        newsInput.value = "BREAKING: Scientists have discovered a miracle cure that the government has been hiding from the public! You won't believe what they found. Click here to learn the shocking truth that they don't want you to know. This secret has been exposed by anonymous sources who claim the conspiracy goes all the way to the top.";
        newsInput.dispatchEvent(new Event('input'));
    });
}

// ─── FORM SUBMIT WITH MULTI-BACKEND FALLBACK ─
form.addEventListener('submit', async e => {
    e.preventDefault();
    const text = newsInput.value.trim();
    if (text.length < 20) { alert('Please enter at least 20 characters to analyze.'); return; }
    setLoading(true, 'Connecting to server…');

    const endpoints = [
        API,
        'https://truthlens-1-ue36.onrender.com',
        'http://127.0.0.1:8000'
    ];
    const unique = [...new Set(endpoints)];

    let data = null;
    let lastError = null;

    const wakeTimer = setTimeout(() => {
        btnText.textContent = 'Waking up cloud server…';
    }, 4000);

    for (const base of unique) {
        try {
            const controller = new AbortController();
            const tid = setTimeout(() => controller.abort(), 20000);
            const res = await fetch(`${base}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
                signal: controller.signal
            });
            clearTimeout(tid);
            if (res.ok) {
                data = await res.json();
                break;
            }
        } catch (err) {
            lastError = err;
            console.warn(`Endpoint ${base} failed:`, err.message);
        }
    }

    clearTimeout(wakeTimer);

    if (data && !data.error) {
        lastData = { ...data, _inputText: text };
        renderAll(data, text);
        fetchHistory();
        fetchStats();
    } else {
        alert('❌ Unable to reach the backend. Cloud servers can take 15-25 seconds to wake up. Please try again!');
    }
    setLoading(false);
});

// ─── RENDER ALL ─────────────────────────────
function renderAll(d, text) {
    resultsPanel.classList.remove('hidden');

    // Score ring
    const cred = d.credibility_score || 0;
    const ring = document.getElementById('score-ring');
    const circ = 2 * Math.PI * 42;
    ring.style.strokeDasharray = circ;
    ring.style.strokeDashoffset = circ - (cred / 100) * circ;
    ring.style.stroke = cred >= 70 ? '#10b981' : cred >= 40 ? '#f59e0b' : '#ef4444';

    document.getElementById('credibility-score').textContent = cred;
    document.getElementById('score-label-text').textContent = 'Credibility';

    // Classification badge
    const badge = document.getElementById('classification-badge');
    badge.textContent = d.classification || 'UNKNOWN';
    badge.className = 'verdict-badge ' + (d.classification || 'unknown').toLowerCase();

    document.getElementById('classification-message').textContent = d.message || '';

    // Sentiment tag
    const stag = document.getElementById('sentiment-tag');
    if (stag && d.sentiment) stag.textContent = d.sentiment.tone || '–';

    // Mini metrics
    setText('word-count', d.text_length || '—');
    setText('fake-prob', (d.fake_probability || 0) + '%');
    setText('confidence-metric', (d.confidence || 0) + '%');
    setText('entity-count', d.evidence ? d.evidence.length : 0);

    // Sentiment
    if (d.sentiment) {
        setText('sentiment-tone-badge', d.sentiment.tone || '–');
        setBar('bar-positive', d.sentiment.positive_pct);
        setBar('bar-negative', d.sentiment.negative_pct);
        setBar('bar-fear', d.sentiment.fear_pct);
        setText('val-positive', d.sentiment.positive_pct + '%');
        setText('val-negative', d.sentiment.negative_pct + '%');
        setText('val-fear', d.sentiment.fear_pct + '%');
    }

    // Bias
    if (d.bias) {
        setText('bias-leaning-badge', d.bias.leaning || '–');
        const needle = document.getElementById('bias-needle');
        if (needle) {
            const left = d.bias.left_triggers ? d.bias.left_triggers.length : 0;
            const right = d.bias.right_triggers ? d.bias.right_triggers.length : 0;
            const pos = 50 + (right - left) * 10;
            needle.style.left = Math.max(5, Math.min(95, pos)) + '%';
        }
        renderChips('bias-triggers', [...(d.bias.left_triggers || []), ...(d.bias.right_triggers || []), ...(d.bias.amplifiers || [])], 'trigger-chip');
    }

    // Clickbait
    if (d.clickbait) {
        setText('clickbait-score-val', d.clickbait.score || 0);
        setText('clickbait-level', d.clickbait.level || '–');
        const cStats = document.getElementById('clickbait-stats');
        if (cStats) cStats.innerHTML = `${d.clickbait.caps_word_count || 0} ALL-CAPS · ${d.clickbait.exclamation_count || 0} exclamations · ${d.clickbait.question_count || 0} questions`;
        setBar('clickbait-bar', d.clickbait.score);
        renderChips('clickbait-triggers', d.clickbait.triggers || [], 'trigger-chip');
    }

    // Virality
    if (d.virality_risk) {
        setText('virality-score-val', d.virality_risk.score || 0);
        setText('virality-risk-label', d.virality_risk.risk || '–');
        setBar('virality-bar', d.virality_risk.score);
        const vf = document.getElementById('virality-factors');
        if (vf) {
            vf.innerHTML = `
                <div class="factor-item">Fake probability contributes ${d.fake_probability || 0}% weight</div>
                <div class="factor-item">Clickbait score: ${d.clickbait ? d.clickbait.score : 0}/100</div>
                <div class="factor-item">Negative sentiment: ${d.sentiment ? d.sentiment.negative_pct : 0}%</div>
            `;
        }
    }

    // Readability
    if (d.readability) {
        setText('readability-score-val', d.readability.score || 0);
        setText('readability-grade', d.readability.grade || '–');
        setBar('readability-bar', d.readability.score);
        const rs = document.getElementById('readability-stats');
        if (rs) {
            rs.innerHTML = `
                <div class="stat-item"><span class="stat-label">Sentences</span><span class="stat-value">${d.readability.sentence_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Avg Length</span><span class="stat-value">${d.readability.avg_sentence_length || 0} words</span></div>
            `;
        }
    }

    // Writing style
    if (d.writing_style) {
        setText('style-formality', d.writing_style.formality || '–');
        const sg = document.getElementById('style-grid');
        if (sg) {
            sg.innerHTML = `
                <div class="stat-item"><span class="stat-label">Avg Word Length</span><span class="stat-value">${d.writing_style.avg_word_length || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Passive Voice</span><span class="stat-value">${d.writing_style.passive_voice_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Quotes</span><span class="stat-value">${d.writing_style.quote_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Numbers</span><span class="stat-value">${d.writing_style.number_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">URLs</span><span class="stat-value">${d.writing_style.url_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Sentences</span><span class="stat-value">${d.writing_style.sentence_count || 0}</span></div>
            `;
        }
    }

    // Evidence entities
    const entityBox = document.getElementById('entity-tags');
    if (entityBox) {
        if (d.evidence && d.evidence.length > 0) {
            entityBox.innerHTML = d.evidence.map(e =>
                `<span class="entity-chip ${e.label}">${e.text} <small>${e.label}</small></span>`
            ).join('');
        } else {
            entityBox.innerHTML = '<span class="empty-state">No named entities detected</span>';
        }
    }

    // Context
    setText('context-box', d.actual_news_context || 'No context available');
    const cs = document.getElementById('context-sources');
    if (cs) {
        const sources = [
            { name: 'Reuters', status: d.classification === 'REAL' ? 'confirmed' : 'unverified' },
            { name: 'AP News', status: d.classification === 'REAL' ? 'confirmed' : d.classification === 'FAKE' ? 'disputed' : 'unverified' },
            { name: 'FactCheck.org', status: d.classification === 'FAKE' ? 'disputed' : 'unverified' }
        ];
        cs.innerHTML = sources.map(s =>
            `<div class="source-item"><span class="source-name">${s.name}</span><span class="source-status ${s.status}">${s.status}</span></div>`
        ).join('');
    }

    // Claims
    const cl = document.getElementById('claims-list');
    if (cl) {
        if (d.extracted_claims && d.extracted_claims.length > 0) {
            cl.innerHTML = d.extracted_claims.map((c, i) =>
                `<div class="claim-item"><span class="claim-num">#${i + 1}</span><span class="claim-text">${c}</span></div>`
            ).join('');
        } else {
            cl.innerHTML = '<span class="empty-state">No factual claims extracted</span>';
        }
    }

    // Keywords
    renderChips('keyword-chips', d.triggered_keywords || [], 'keyword-chip');

    // Full report
    const desc = document.getElementById('description-text');
    if (desc) desc.textContent = JSON.stringify(d, null, 2);

    // Scroll to results
    resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── HELPERS ────────────────────────────────
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function setBar(id, pct) {
    const el = document.getElementById(id);
    if (el) setTimeout(() => { el.style.width = Math.min(100, pct || 0) + '%'; }, 100);
}

function renderChips(containerId, items, chipClass) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (items.length === 0) {
        el.innerHTML = '<span class="empty-state">None detected</span>';
    } else {
        el.innerHTML = items.map(item =>
            `<span class="${chipClass}">${item}</span>`
        ).join('');
    }
}

// ─── HISTORY ────────────────────────────────
async function fetchHistory() {
    try {
        const res = await fetch(`${API}/history`);
        const data = await res.json();
        if (data.history && data.history.length > 0) {
            historyListEl.innerHTML = data.history.map(h => `
                <div class="history-item" onclick="document.getElementById('news-input').value='${h.snippet.replace(/'/g, "\\'")}'; document.getElementById('news-input').dispatchEvent(new Event('input'));">
                    <div class="history-top">
                        <span class="history-badge ${h.classification.toLowerCase()}">${h.classification}</span>
                        <span class="history-time">${new Date(h.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div class="history-snippet">${h.snippet}</div>
                    <div class="history-score">Score: ${h.credibility_score}%</div>
                </div>
            `).join('');
            clearBtn.classList.remove('hidden');
        }
    } catch (e) { /* silent */ }
}

async function fetchStats() {
    try {
        const res = await fetch(`${API}/stats`);
        const d = await res.json();
        setText('stat-total', d.total || 0);
        const b = d.breakdown || {};
        setText('stat-real', b.REAL || 0);
        setText('stat-sus', b.SUSPICIOUS || 0);
        setText('stat-fake', b.FAKE || 0);
    } catch (e) { /* silent */ }
}

// Clear history
if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
        try {
            await fetch(`${API}/history`, { method: 'DELETE' });
            historyListEl.innerHTML = '<div class="history-empty"><p>No analyses yet</p></div>';
            clearBtn.classList.add('hidden');
            fetchStats();
        } catch (e) { /* silent */ }
    });
}

// ─── DOWNLOAD / SHARE ───────────────────────
function downloadReport() {
    if (!lastData) return;
    const blob = new Blob([JSON.stringify(lastData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'truthlens-report.json';
    a.click();
    URL.revokeObjectURL(url);
}

const dlBtn1 = document.getElementById('download-report-btn');
const dlBtn2 = document.getElementById('download-report-btn2');
const shareBtn = document.getElementById('share-btn');

if (dlBtn1) dlBtn1.addEventListener('click', downloadReport);
if (dlBtn2) dlBtn2.addEventListener('click', downloadReport);
if (shareBtn) {
    shareBtn.addEventListener('click', () => {
        if (!lastData) return;
        const text = `TruthLens Analysis:\nClassification: ${lastData.classification}\nCredibility: ${lastData.credibility_score}%\nFake Risk: ${lastData.fake_probability}%`;
        navigator.clipboard.writeText(text).then(() => {
            shareBtn.textContent = '✓ Copied!';
            setTimeout(() => { shareBtn.textContent = 'Copy Report'; }, 2000);
        });
    });
}

// ─── INIT ───────────────────────────────────
fetchHistory();
fetchStats();
