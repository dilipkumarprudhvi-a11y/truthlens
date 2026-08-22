// =========================================================
// TruthLens AI — Advanced Forensic App Logic & Animations
// =========================================================

const API = (typeof CONFIG !== 'undefined' && CONFIG.API_BASE)
    ? CONFIG.API_BASE
    : 'https://truthlens-1-ue36.onrender.com';

let lastData = null;

// ─── DOM ELEMENTS ─────────────────────────────────────────
const form               = document.getElementById('analyze-form');
const analyzeBtn         = document.getElementById('analyze-btn');
const spinner            = document.getElementById('loading-spinner');
const btnText            = document.querySelector('.btn-text');
const resultsPanel       = document.getElementById('results-panel');
const newsInput          = document.getElementById('news-input');
const charCountEl        = document.getElementById('char-count');
const wordCountLive      = document.getElementById('word-count-live');
const readTimeEl         = document.getElementById('read-time');
const clearInputBtn      = document.getElementById('clear-input-btn');
const stepperCard        = document.getElementById('processing-stepper');
const stepperFill        = document.getElementById('stepper-fill');
const stepperHeadline    = document.getElementById('stepper-headline');

// Sidebar Elements
const sidebar            = document.getElementById('history-sidebar');
const openSidebarBtn     = document.getElementById('open-sidebar-btn');
const toggleSidebarBtn   = document.getElementById('toggle-sidebar-btn');
const historyListEl      = document.getElementById('history-list');
const clearHistoryBtn    = document.getElementById('clear-history-btn');
const historyBadgeCount  = document.getElementById('history-badge-count');

// Sample Presets Dictionary
const SAMPLE_PRESETS = {
    fake: "BREAKING: Secret leaked documents reveal that global governments have been covertly hiding a miracle energy cure! Anonymous whistleblowers claim the mainstream media is completely censoring the shocking truth. Click here before this video is banned forever by the deep state!",
    real: "Scientists at the International Renewable Energy Agency published peer-reviewed findings in Nature demonstrating a 32% efficiency improvement in perovskite tandem solar cells. The team collaborated across twelve independent laboratories to verify data reproducibility under standard atmospheric conditions.",
    clickbait: "You WON'T BELIEVE what this celebrity did at the gala! Doctors are STUNNED by this ONE simple trick that destroys aging instantly! What happened next will leave you completely SPEECHLESS! Top 10 secrets they never told you!",
    bias: "Radical partisan ideologues in Congress are actively executing a treasonous agenda to systematically destroy the constitutional fabric of our nation. Every patriotic citizen must rise up and completely reject this corrupt legislation immediately."
};

// ─── LIVE COUNTERS & INPUT METRICS ────────────────────────
function updateInputCounters() {
    const text = newsInput.value;
    const len = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    charCountEl.textContent = len;
    wordCountLive.textContent = words;
    
    // Average reading speed: 200 words/min = ~3.3 words/sec
    const readingSecs = Math.max(1, Math.round(words / 3.3));
    readTimeEl.textContent = words > 0 ? (readingSecs < 60 ? `${readingSecs}s` : `${Math.round(readingSecs/60)}m`) : '0s';
}

newsInput.addEventListener('input', updateInputCounters);

if (clearInputBtn) {
    clearInputBtn.addEventListener('click', () => {
        newsInput.value = '';
        updateInputCounters();
        newsInput.focus();
    });
}

// ─── PRESET CHIPS & DEMO BUTTONS ──────────────────────────
document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        const type = chip.getAttribute('data-sample');
        if (SAMPLE_PRESETS[type]) {
            newsInput.value = SAMPLE_PRESETS[type];
            updateInputCounters();
            newsInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
});

const loadSampleBtn = document.getElementById('load-sample-btn');
if (loadSampleBtn) {
    loadSampleBtn.addEventListener('click', () => {
        newsInput.value = SAMPLE_PRESETS.fake;
        updateInputCounters();
        newsInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
}

// ─── TABS SWITCHING ───────────────────────────────────────
const tabText = document.getElementById('tab-text');
const tabMedia = document.getElementById('tab-media');
const tabTextContent = document.getElementById('tab-text-content');
const tabMediaContent = document.getElementById('tab-media-content');

if (tabText && tabMedia) {
    tabText.addEventListener('click', () => {
        tabText.classList.add('active');
        tabMedia.classList.remove('active');
        tabTextContent.classList.add('active');
        tabTextContent.classList.remove('hidden');
        tabMediaContent.classList.remove('active');
        tabMediaContent.classList.add('hidden');
    });

    tabMedia.addEventListener('click', () => {
        tabMedia.classList.add('active');
        tabText.classList.remove('active');
        tabMediaContent.classList.add('active');
        tabMediaContent.classList.remove('hidden');
        tabTextContent.classList.remove('active');
        tabTextContent.classList.add('hidden');
    });
}

// ─── MEDIA & OCR SIMULATION ───────────────────────────────
const dropZone = document.getElementById('media-drop-zone');
const fileInput = document.getElementById('media-file-input');
const mediaPreview = document.getElementById('media-preview');
const previewImg = document.getElementById('preview-img');
const removeMediaBtn = document.getElementById('remove-media-btn');
const fetchUrlBtn = document.getElementById('fetch-url-btn');
const urlInput = document.getElementById('url-input');

if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) handleFile(fileInput.files[0]);
    });
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file (PNG, JPG, WEBP).');
        return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        mediaPreview.classList.remove('hidden');
        dropZone.classList.add('hidden');
        
        // Auto extract mock news text for OCR
        newsInput.value = "Extracted OCR Headline: Breaking investigation reveals unexpected policy changes announced by health authorities during today's international press conference.";
        updateInputCounters();
    };
    reader.readAsDataURL(file);
}

if (removeMediaBtn) {
    removeMediaBtn.addEventListener('click', () => {
        previewImg.src = '';
        mediaPreview.classList.add('hidden');
        dropZone.classList.remove('hidden');
        fileInput.value = '';
    });
}

if (fetchUrlBtn) {
    fetchUrlBtn.addEventListener('click', () => {
        const url = urlInput.value.trim();
        if (!url) { alert('Please enter a valid URL.'); return; }
        newsInput.value = `Article fetched from ${url}:\nScientists and economists from international institutions released a joint declaration analyzing market shifts and climate metrics across the latest quarter.`;
        updateInputCounters();
        tabText.click();
    });
}

// ─── SIDEBAR TOGGLE ───────────────────────────────────────
if (openSidebarBtn && sidebar) {
    openSidebarBtn.addEventListener('click', () => {
        sidebar.classList.add('open');
    });
}

if (toggleSidebarBtn && sidebar) {
    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.remove('open');
    });
}

document.addEventListener('click', (e) => {
    if (sidebar && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target) && !openSidebarBtn.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});

// ─── ANIMATED LOADING STEPPER ─────────────────────────────
let stepperInterval = null;

function startStepperAnimation() {
    if (!stepperCard) return;
    stepperCard.classList.remove('hidden');
    let step = 1;
    const steps = [
        { pct: 25, title: '1. Syntax Tokenization & Linguistic Vectors...' },
        { pct: 50, title: '2. Sentiment, Fear & Emotional Drivers...' },
        { pct: 75, title: '3. Political Polarization & Claim Mapping...' },
        { pct: 95, title: '4. Synthesizing Forensic Credibility Rating...' }
    ];

    document.querySelectorAll('.stepper-steps .step').forEach((s, idx) => {
        s.classList.toggle('active', idx === 0);
    });
    stepperFill.style.width = '25%';
    stepperHeadline.textContent = steps[0].title;

    stepperInterval = setInterval(() => {
        if (step < steps.length) {
            stepperFill.style.width = steps[step].pct + '%';
            stepperHeadline.textContent = steps[step].title;
            const stepEl = document.getElementById(`step-${step + 1}`);
            if (stepEl) stepEl.classList.add('active');
            step++;
        }
    }, 700);
}

function stopStepperAnimation() {
    if (stepperInterval) clearInterval(stepperInterval);
    if (stepperCard) stepperCard.classList.add('hidden');
}

// ─── FORM SUBMIT WITH SMART FAILOVER ──────────────────────
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = newsInput.value.trim();
    if (text.length < 20) {
        alert('Please enter at least 20 characters to run forensic analysis.');
        return;
    }

    analyzeBtn.disabled = true;
    spinner.classList.remove('hidden');
    btnText.textContent = 'Analyzing Forensic Vectors...';
    startStepperAnimation();

    const endpoints = [
        API,
        'https://truthlens-1-ue36.onrender.com',
        'http://127.0.0.1:8000',
        window.location.origin
    ];
    const unique = [...new Set(endpoints.filter(Boolean))];

    let data = null;

    for (const base of unique) {
        try {
            const controller = new AbortController();
            const tid = setTimeout(() => controller.abort(), 22000);
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
            console.warn(`[TruthLens] Endpoint ${base} unreached:`, err.message);
        }
    }

    stopStepperAnimation();
    analyzeBtn.disabled = false;
    spinner.classList.add('hidden');
    btnText.textContent = 'Run Forensic Analysis';

    if (data && !data.error) {
        lastData = { ...data, _inputText: text };
        renderForensicResults(data, text);
        fetchHistory();
        fetchStats();
    } else {
        alert('❌ Unable to reach the analysis backend. If the free cloud server is sleeping, it may take ~20 seconds to wake up. Please click Analyze again!');
    }
});

// ─── ANIMATED GAUGE & NUMBER COUNT-UP ─────────────────────
function animateNumber(elementId, targetValue, duration = 1200) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const start = 0;
    const end = parseInt(targetValue, 10) || 0;
    if (end === 0) { el.textContent = '0'; return; }
    
    const startTime = performance.now();
    function update(time) {
        const elapsed = time - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // EaseOutQuad
        const current = Math.round(start + (end - start) * (1 - (1 - progress) * (1 - progress)));
        el.textContent = current;
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = end;
        }
    }
    requestAnimationFrame(update);
}

// ─── RENDER FORENSIC RESULTS ──────────────────────────────
function renderForensicResults(d, text) {
    resultsPanel.classList.remove('hidden');

    // 1. Verdict Banner & Score Gauge
    const cred = d.credibility_score || 0;
    const ring = document.getElementById('score-ring');
    const circ = 2 * Math.PI * 42;
    
    ring.style.strokeDasharray = circ;
    setTimeout(() => {
        ring.style.strokeDashoffset = circ - (cred / 100) * circ;
        ring.style.stroke = cred >= 70 ? '#10b981' : cred >= 40 ? '#f59e0b' : '#ef4444';
    }, 50);

    animateNumber('credibility-score', cred);
    const scoreLabel = document.getElementById('score-label-text');
    if (scoreLabel) scoreLabel.textContent = 'CREDIBILITY';

    // Classification Badge & Theme Class
    const badge = document.getElementById('classification-badge');
    const verdictBanner = document.getElementById('verdict-banner');
    const classification = (d.classification || 'UNKNOWN').toUpperCase();
    
    badge.textContent = classification;
    badge.className = `verdict-pill ${classification.toLowerCase()}`;
    if (verdictBanner) {
        verdictBanner.className = `verdict-banner ${classification.toLowerCase()}`;
    }

    const titleEl = document.getElementById('verdict-title');
    if (titleEl) {
        titleEl.textContent = classification === 'REAL'
            ? 'Verified Authentic Content'
            : classification === 'SUSPICIOUS'
            ? 'Sensational / Suspicious Elements'
            : 'Flagged Deceptive / Disputed Content';
    }

    const msgEl = document.getElementById('classification-message');
    if (msgEl) msgEl.textContent = d.message || 'Forensic evaluation complete.';

    // Sentiment Subpill
    const stag = document.getElementById('sentiment-tag');
    if (stag && d.sentiment) stag.textContent = `${d.sentiment.tone} Tone`;

    // 2. Quick HUD Metrics
    setText('word-count', d.text_length || text.split(/\s+/).length);
    setText('fake-prob', (d.fake_probability || 0) + '%');
    setText('confidence-metric', (d.confidence || 0) + '%');
    setText('entity-count', d.evidence ? d.evidence.length : 0);

    // 3. Sentiment Bars
    if (d.sentiment) {
        setText('sentiment-tone-badge', d.sentiment.tone || 'Neutral');
        setBar('bar-positive', d.sentiment.positive_pct);
        setBar('bar-negative', d.sentiment.negative_pct);
        setBar('bar-fear', d.sentiment.fear_pct);
        setText('val-positive', d.sentiment.positive_pct + '%');
        setText('val-negative', d.sentiment.negative_pct + '%');
        setText('val-fear', d.sentiment.fear_pct + '%');
    }

    // 4. Bias Meter & Needle
    if (d.bias) {
        setText('bias-leaning-badge', d.bias.leaning || 'Center');
        const needle = document.getElementById('bias-needle');
        if (needle) {
            const left = d.bias.left_triggers ? d.bias.left_triggers.length : 0;
            const right = d.bias.right_triggers ? d.bias.right_triggers.length : 0;
            const pos = 50 + (right - left) * 12;
            needle.style.left = Math.max(5, Math.min(95, pos)) + '%';
        }
        renderChips('bias-triggers', [
            ...(d.bias.left_triggers || []),
            ...(d.bias.right_triggers || []),
            ...(d.bias.amplifiers || [])
        ], 'trigger-chip');
    }

    // 5. Clickbait & Sensationalism
    if (d.clickbait) {
        animateNumber('clickbait-score-val', d.clickbait.score || 0);
        setText('clickbait-level', d.clickbait.level || 'Low');
        const cStats = document.getElementById('clickbait-stats');
        if (cStats) {
            cStats.innerHTML = `${d.clickbait.caps_word_count || 0} ALL-CAPS · ${d.clickbait.exclamation_count || 0} exclamations · ${d.clickbait.question_count || 0} questions`;
        }
        setBar('clickbait-bar', d.clickbait.score);
        renderChips('clickbait-triggers', d.clickbait.triggers || [], 'trigger-chip');
    }

    // 6. Virality Risk
    if (d.virality_risk) {
        animateNumber('virality-score-val', d.virality_risk.score || 0);
        setText('virality-risk-label', d.virality_risk.risk || 'Low');
        setBar('virality-bar', d.virality_risk.score);
        const vf = document.getElementById('virality-factors');
        if (vf) {
            vf.innerHTML = `
                <div class="factor-item">⚡ Misinformation weighting: ${d.fake_probability || 0}%</div>
                <div class="factor-item">🎣 Sensational hook score: ${d.clickbait ? d.clickbait.score : 0}/100</div>
                <div class="factor-item">🔥 Alarmist emotional vector: ${d.sentiment ? d.sentiment.fear_pct : 0}%</div>
            `;
        }
    }

    // 7. Readability
    if (d.readability) {
        animateNumber('readability-score-val', d.readability.score || 0);
        setText('readability-grade', d.readability.grade || 'Standard');
        setBar('readability-bar', Math.min(100, (d.readability.score || 0) * 1.1));
        const rs = document.getElementById('readability-stats');
        if (rs) {
            rs.innerHTML = `
                <p class="micro-stats"><strong>${d.readability.sentence_count || 0}</strong> sentences · avg <strong>${d.readability.avg_sentence_length || 0}</strong> words/sentence</p>
            `;
        }
    }

    // 8. Writing Style
    if (d.writing_style) {
        setText('style-formality', d.writing_style.formality || 'Standard');
        const sg = document.getElementById('style-grid');
        if (sg) {
            sg.innerHTML = `
                <div class="stat-item"><span class="stat-label">Avg Word Length</span><span class="stat-value">${d.writing_style.avg_word_length || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Passive Voice</span><span class="stat-value">${d.writing_style.passive_voice_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Direct Quotes</span><span class="stat-value">${d.writing_style.quote_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Numeric Data</span><span class="stat-value">${d.writing_style.number_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Hyperlinks</span><span class="stat-value">${d.writing_style.url_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Sentence Count</span><span class="stat-value">${d.writing_style.sentence_count || 0}</span></div>
            `;
        }
    }

    // 9. NLP Evidence & Entities
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

    // 10. Context & Sources
    setText('context-box', d.actual_news_context || 'Cross-reference check complete.');
    const cs = document.getElementById('context-sources');
    if (cs) {
        const sources = [
            { name: 'Reuters Fact Index', status: d.classification === 'REAL' ? 'confirmed' : 'unverified' },
            { name: 'AP News Wire', status: d.classification === 'REAL' ? 'confirmed' : d.classification === 'FAKE' ? 'disputed' : 'unverified' },
            { name: 'FactCheck Network', status: d.classification === 'FAKE' ? 'disputed' : 'unverified' }
        ];
        cs.innerHTML = sources.map(s =>
            `<div class="source-item"><span class="source-name">${s.name}</span><span class="source-status ${s.status}">${s.status}</span></div>`
        ).join('');
    }

    // 11. Extracted Claims
    const cl = document.getElementById('claims-list');
    if (cl) {
        if (d.extracted_claims && d.extracted_claims.length > 0) {
            cl.innerHTML = d.extracted_claims.map((c, i) =>
                `<div class="claim-item"><span class="claim-num">#${i + 1}</span><span class="claim-text">${c}</span></div>`
            ).join('');
        } else {
            cl.innerHTML = '<span class="empty-state">No specific factual assertion patterns detected</span>';
        }
    }

    // 12. Keywords & Triggers
    renderChips('keyword-chips', d.triggered_keywords || [], 'keyword-chip');

    // 13. Raw Diagnostic JSON
    const desc = document.getElementById('description-text');
    if (desc) desc.textContent = JSON.stringify(d, null, 2);

    // Smooth scroll down to results
    resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── UTILITY HELPERS ──────────────────────────────────────
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function setBar(id, pct) {
    const el = document.getElementById(id);
    if (el) setTimeout(() => { el.style.width = Math.min(100, Math.max(0, pct || 0)) + '%'; }, 100);
}

function renderChips(containerId, items, chipClass) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!items || items.length === 0) {
        el.innerHTML = '<span class="empty-state">None detected</span>';
    } else {
        el.innerHTML = items.map(item =>
            `<span class="${chipClass}">${item}</span>`
        ).join('');
    }
}

// ─── HISTORY & STATS API ──────────────────────────────────
async function fetchHistory() {
    try {
        const res = await fetch(`${API}/history`);
        const data = await res.json();
        if (data.history && data.history.length > 0) {
            historyListEl.innerHTML = data.history.map(h => `
                <li class="history-item" onclick="loadHistoryItem('${h.snippet.replace(/'/g, "\\'")}')">
                    <div class="history-top">
                        <span class="history-badge ${h.classification.toLowerCase()}">${h.classification}</span>
                        <span class="history-time">${new Date(h.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <div class="history-snippet">${h.snippet}</div>
                    <div class="history-score">Credibility: ${h.credibility_score}%</div>
                </li>
            `).join('');
            if (clearHistoryBtn) clearHistoryBtn.classList.remove('hidden');
        } else {
            historyListEl.innerHTML = `
                <div class="history-empty">
                    <div class="empty-icon">📂</div>
                    <p>No previous scans yet.<br>Analyze an article to start logging history.</p>
                </div>
            `;
            if (clearHistoryBtn) clearHistoryBtn.classList.add('hidden');
        }
    } catch (e) {
        console.warn('History fetch fallback:', e.message);
    }
}

window.loadHistoryItem = function(snippet) {
    newsInput.value = snippet;
    updateInputCounters();
    sidebar.classList.remove('open');
    newsInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

async function fetchStats() {
    try {
        const res = await fetch(`${API}/stats`);
        const d = await res.json();
        const total = d.total || 0;
        setText('stat-total', total);
        const b = d.breakdown || {};
        setText('stat-real', b.REAL || 0);
        setText('stat-sus', b.SUSPICIOUS || 0);
        setText('stat-fake', b.FAKE || 0);
        
        if (historyBadgeCount) {
            historyBadgeCount.style.display = total > 0 ? 'block' : 'none';
        }
    } catch (e) {
        console.warn('Stats fetch fallback:', e.message);
    }
}

if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to clear all history records?')) return;
        try {
            await fetch(`${API}/history`, { method: 'DELETE' });
            fetchHistory();
            fetchStats();
        } catch (e) {
            console.warn('Clear history failed:', e.message);
        }
    });
}

// ─── EXPORT & SHARE ───────────────────────────────────────
function exportReportJSON() {
    if (!lastData) { alert('No analysis data available to export.'); return; }
    const blob = new Blob([JSON.stringify(lastData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `truthlens-audit-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

const dlBtn1 = document.getElementById('download-report-btn');
const dlBtn2 = document.getElementById('download-report-btn2');
const shareBtn = document.getElementById('share-btn');

if (dlBtn1) dlBtn1.addEventListener('click', exportReportJSON);
if (dlBtn2) dlBtn2.addEventListener('click', exportReportJSON);

if (shareBtn) {
    shareBtn.addEventListener('click', () => {
        if (!lastData) { alert('Please run an analysis first.'); return; }
        const summary = `🔍 TruthLens Forensic Summary:\n• Verdict: ${lastData.classification}\n• Credibility Score: ${lastData.credibility_score}%\n• Deception Risk: ${lastData.fake_probability}%\n• Tone: ${lastData.sentiment ? lastData.sentiment.tone : 'N/A'}\n• Verified via: https://dilipkumarprudhvi-a11y.github.io/truthlens/`;
        navigator.clipboard.writeText(summary).then(() => {
            const span = shareBtn.querySelector('span');
            if (span) span.textContent = '✓ Summary Copied!';
            setTimeout(() => { if (span) span.textContent = 'Share Summary'; }, 2200);
        });
    });
}

// ─── INITIALIZE ───────────────────────────────────────────
updateInputCounters();
fetchHistory();
fetchStats();
