// =========================================================
// TruthLens AI — Evidence-Grounded Verification App Logic
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

// Modal Elements
const howItWorksBtn      = document.getElementById('how-it-works-btn');
const methodologyModal   = document.getElementById('methodology-modal');
const closeModalBtn      = document.getElementById('close-modal-btn');

// Sample Presets Dictionary
const SAMPLE_PRESETS = {
    fake: "BREAKING: Secret documents leak revealing that global health authorities and governments engineered a covert energy conspiracy. Anonymous whistleblowers claim mainstream media is completely censoring this shocking truth!",
    real: "Scientists at the International Renewable Energy Agency published peer-reviewed findings in Nature demonstrating a 32 percent efficiency improvement in perovskite solar cells across twelve independent laboratory trials.",
    clickbait: "You WON'T BELIEVE what this celebrity did at the private gala! Doctors are STUNNED by this ONE simple trick that eliminates aging instantly! What happened next will leave you completely SPEECHLESS!",
    bias: "Radical partisan ideologues in Congress are aggressively pushing a corrupt, socialist legislative agenda designed to systematically dismantle constitutional liberties across our nation."
};

// ─── LIVE COUNTERS & INPUT METRICS ────────────────────────
function updateInputCounters() {
    const text = newsInput.value;
    const len = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    charCountEl.textContent = len;
    wordCountLive.textContent = words;
    
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
        tabText.setAttribute('aria-selected', 'true');
        tabMedia.classList.remove('active');
        tabMedia.setAttribute('aria-selected', 'false');
        tabTextContent.classList.add('active');
        tabTextContent.classList.remove('hidden');
        tabMediaContent.classList.remove('active');
        tabMediaContent.classList.add('hidden');
    });

    tabMedia.addEventListener('click', () => {
        tabMedia.classList.add('active');
        tabMedia.setAttribute('aria-selected', 'true');
        tabText.classList.remove('active');
        tabText.setAttribute('aria-selected', 'false');
        tabMediaContent.classList.add('active');
        tabMediaContent.classList.remove('hidden');
        tabTextContent.classList.remove('active');
        tabTextContent.classList.add('hidden');
    });
}

// ─── URL INGESTION (SERVER-SIDE SSRF GUARDED) ─────────────
const fetchUrlBtn = document.getElementById('fetch-url-btn');
const urlInput = document.getElementById('url-input');

if (fetchUrlBtn) {
    fetchUrlBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) { alert('Please enter a valid web article URL.'); return; }
        
        fetchUrlBtn.disabled = true;
        fetchUrlBtn.textContent = 'Extracting article...';

        const endpoints = [
            API,
            'https://truthlens-1-ue36.onrender.com',
            'http://127.0.0.1:8000',
            window.location.origin
        ];
        const unique = [...new Set(endpoints.filter(Boolean))];

        let extractedData = null;
        for (const base of unique) {
            try {
                const res = await fetch(`${base}/api/url/extract`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                if (res.ok) {
                    extractedData = await res.json();
                    break;
                }
            } catch (err) {
                // try fallback
            }
        }

        fetchUrlBtn.disabled = false;
        fetchUrlBtn.textContent = 'Fetch & Analyze';

        if (extractedData && extractedData.success && extractedData.text) {
            newsInput.value = (extractedData.title ? `[${extractedData.title}]\n\n` : '') + extractedData.text;
            updateInputCounters();
            tabText.click();
            form.dispatchEvent(new Event('submit'));
        } else {
            alert(extractedData?.error || 'Unable to extract web content from target URL. Please paste text directly.');
        }
    });
}

// ─── IMAGE & OCR INGESTION ────────────────────────────────
const dropZone = document.getElementById('media-drop-zone');
const fileInput = document.getElementById('media-file-input');
const mediaPreview = document.getElementById('media-preview');
const previewImg = document.getElementById('preview-img');
const removeMediaBtn = document.getElementById('remove-media-btn');
const ocrStatusTag = document.getElementById('ocr-status-tag');

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
        if (e.dataTransfer.files.length) handleFileUpload(e.dataTransfer.files[0]);
    });
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) handleFileUpload(fileInput.files[0]);
    });
}

async function handleFileUpload(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file (PNG, JPG, WEBP).');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        mediaPreview.classList.remove('hidden');
        dropZone.classList.add('hidden');
    };
    reader.readAsDataURL(file);

    if (ocrStatusTag) ocrStatusTag.textContent = 'Running OCR extraction...';

    const formData = new FormData();
    formData.append('file', file);

    const endpoints = [
        API,
        'https://truthlens-1-ue36.onrender.com',
        'http://127.0.0.1:8000',
        window.location.origin
    ];
    const unique = [...new Set(endpoints.filter(Boolean))];

    let ocrResult = null;
    for (const base of unique) {
        try {
            const res = await fetch(`${base}/api/ocr/extract`, {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                ocrResult = await res.json();
                break;
            }
        } catch (err) {
            // try fallback
        }
    }

    if (ocrResult && ocrResult.status === 'success' && ocrResult.text) {
        if (ocrStatusTag) ocrStatusTag.textContent = `✓ OCR Extracted (${ocrResult.confidence}% confidence)`;
        newsInput.value = ocrResult.text;
        updateInputCounters();
        tabText.click();
    } else {
        if (ocrStatusTag) ocrStatusTag.textContent = ocrResult?.note || 'OCR engine offline. Please paste text directly.';
        alert(ocrResult?.note || 'OCR is not configured in this environment. Please paste article text directly.');
    }
}

if (removeMediaBtn) {
    removeMediaBtn.addEventListener('click', () => {
        previewImg.src = '';
        mediaPreview.classList.add('hidden');
        dropZone.classList.remove('hidden');
        fileInput.value = '';
    });
}

// ─── SIDEBAR & MODAL CONTROLS ─────────────────────────────
if (openSidebarBtn && sidebar) {
    openSidebarBtn.addEventListener('click', () => sidebar.classList.add('open'));
}

if (toggleSidebarBtn && sidebar) {
    toggleSidebarBtn.addEventListener('click', () => sidebar.classList.remove('open'));
}

document.addEventListener('click', (e) => {
    if (sidebar && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target) && !openSidebarBtn.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});

if (howItWorksBtn && methodologyModal) {
    howItWorksBtn.addEventListener('click', () => methodologyModal.classList.remove('hidden'));
}

if (closeModalBtn && methodologyModal) {
    closeModalBtn.addEventListener('click', () => methodologyModal.classList.add('hidden'));
}

if (methodologyModal) {
    methodologyModal.addEventListener('click', (e) => {
        if (e.target === methodologyModal) methodologyModal.classList.add('hidden');
    });
}

// ─── ANIMATED LOADING STEPPER ─────────────────────────────
let stepperInterval = null;

function startStepperAnimation() {
    if (!stepperCard) return;
    stepperCard.classList.remove('hidden');
    let step = 1;
    const steps = [
        { pct: 25, title: '1. Declarative Claim Extraction & Sentence Boundary...' },
        { pct: 50, title: '2. Multi-Source Evidence Query & Normalization...' },
        { pct: 75, title: '3. Claim-Evidence Semantic NLI & Refutation Match...' },
        { pct: 95, title: '4. Deterministic Scoring & Verdict Synthesis...' }
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
    }, 600);
}

function stopStepperAnimation() {
    if (stepperInterval) clearInterval(stepperInterval);
    if (stepperCard) stepperCard.classList.add('hidden');
}

// ─── FORM SUBMIT WITH ASYNC REST ENDPOINTS ────────────────
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = newsInput.value.trim();
    if (text.length < 10) {
        alert('Please enter at least 10 characters to run forensic analysis.');
        return;
    }

    analyzeBtn.disabled = true;
    spinner.classList.remove('hidden');
    btnText.textContent = 'Verifying Factual Claims...';
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
            const tid = setTimeout(() => controller.abort(), 20000);
            
            // Try /api/analyze then fallback /analyze
            let res = await fetch(`${base}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
                signal: controller.signal
            });

            if (!res.ok && res.status !== 400 && res.status !== 413) {
                res = await fetch(`${base}/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text }),
                    signal: controller.signal
                });
            }

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
    btnText.textContent = 'Run Evidence Analysis';

    if (data && !data.error) {
        lastData = { ...data, _inputText: text };
        renderForensicResults(data, text);
        fetchHistory();
        fetchStats();
    } else {
        alert('❌ Unable to reach the analysis engine. If the cloud container is waking up, please wait a few seconds and try again!');
    }
});

// ─── ANIMATED COUNT-UP NUMBER HELPER ──────────────────────
function animateNumber(elementId, targetValue, duration = 1000) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const start = 0;
    const end = parseInt(targetValue, 10) || 0;
    if (end === 0) { el.textContent = '0'; return; }
    
    const startTime = performance.now();
    function update(time) {
        const elapsed = time - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.round(start + (end - start) * (1 - (1 - progress) * (1 - progress)));
        el.textContent = current;
        if (progress < 1) requestAnimationFrame(update);
        else el.textContent = end;
    }
    requestAnimationFrame(update);
}

// ─── RENDER FORENSIC RESULTS & EVIDENCE MATRIX ────────────
function renderForensicResults(d, text) {
    resultsPanel.classList.remove('hidden');

    // 1. Primary Scientific Verdict & Gauge
    const cred = Math.round(d.credibility_score || 0);
    const ring = document.getElementById('score-ring');
    const circ = 2 * Math.PI * 42;
    
    ring.style.strokeDasharray = circ;
    setTimeout(() => {
        ring.style.strokeDashoffset = circ - (cred / 100) * circ;
        ring.style.stroke = cred >= 65 ? '#10b981' : cred >= 45 ? '#f59e0b' : '#ef4444';
    }, 50);

    animateNumber('credibility-score', cred);
    
    // Primary Scientific Verdict Badge (SUPPORTED, CONTRADICTED, MIXED, UNVERIFIED)
    const primaryBadge = document.getElementById('primary-verdict-badge');
    const legacyBadge = document.getElementById('classification-badge');
    const verdictBanner = document.getElementById('verdict-banner');
    const pVerdict = (d.primary_verdict || 'UNVERIFIED').toUpperCase();
    const lClass = (d.legacy_classification || 'UNKNOWN').toUpperCase();

    if (primaryBadge) {
        primaryBadge.textContent = pVerdict;
        primaryBadge.className = `verdict-pill ${pVerdict.toLowerCase()}`;
    }

    if (legacyBadge) {
        legacyBadge.textContent = `VERDICT: ${lClass}`;
    }

    if (verdictBanner) {
        verdictBanner.className = `verdict-banner ${pVerdict.toLowerCase()}`;
    }

    const titleEl = document.getElementById('verdict-title');
    if (titleEl) {
        if (pVerdict === 'SUPPORTED') titleEl.textContent = 'Evidence Supports Core Assertions';
        else if (pVerdict === 'CONTRADICTED') titleEl.textContent = 'Core Assertions Contradicted by Evidence';
        else if (pVerdict === 'MIXED') titleEl.textContent = 'Mixed / Disputed Evidence Detected';
        else titleEl.textContent = 'Unverified: Limited Independent Evidence';
    }

    const msgEl = document.getElementById('classification-message');
    if (msgEl) msgEl.textContent = d.message || 'Forensic evaluation complete.';

    const stag = document.getElementById('sentiment-tag');
    if (stag && d.sentiment) stag.textContent = `${d.sentiment.tone}`;

    // 2. Quick HUD Metrics
    setText('word-count', d.text_length || text.split(/\s+/).length);
    setText('fake-prob', (d.fake_probability || 0) + '%');
    setText('confidence-metric', (d.confidence || 0) + '%');
    setText('claims-count-val', d.claims ? d.claims.length : 0);

    // 3. Render Factual Claim & Evidence Matrix Cards
    const claimStack = document.getElementById('claim-cards-stack');
    if (claimStack) {
        if (d.claims && d.claims.length > 0) {
            claimStack.innerHTML = d.claims.map((c, i) => {
                const cVerdict = (c.verdict || 'UNVERIFIED').toUpperCase();
                const evidenceHTML = (c.evidence && c.evidence.length > 0)
                    ? c.evidence.map(ev => `
                        <div class="evidence-subcard">
                            <div class="evidence-source-bar">
                                <a href="${ev.url}" target="_blank" rel="noopener noreferrer" class="evidence-link">
                                    <span>🌐 ${ev.source_name}</span>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/></svg>
                                </a>
                                <span class="authority-pill">${Math.round(ev.authority_score * 100)}% Authority</span>
                            </div>
                            <p class="evidence-snippet-text"><strong>${ev.title}:</strong> ${ev.snippet}</p>
                        </div>
                    `).join('')
                    : `<div class="evidence-subcard"><p class="empty-state">No independent wire or knowledge entries matched this specific assertion.</p></div>`;

                return `
                    <div class="claim-card-unit">
                        <div class="claim-header-row">
                            <div style="display:flex; align-items:center; gap:0.6rem;">
                                <span class="claim-id-tag">${c.claim_id || `#claim_${i+1}`}</span>
                                <span class="claim-badge ${cVerdict.toLowerCase()}">${cVerdict}</span>
                            </div>
                            <span class="micro-stats">Confidence: ${Math.round(c.confidence || 50)}%</span>
                        </div>
                        <p class="claim-statement-text">"${c.text}"</p>
                        <div class="claim-explanation-box">
                            <strong>Diagnostic Finding:</strong> ${c.explanation || 'Evaluated against knowledge repositories.'}
                        </div>
                        <div class="evidence-subcards-list">
                            <span class="section-micro-label">Citations & Evidence Retrieved</span>
                            ${evidenceHTML}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            claimStack.innerHTML = `<div class="claim-card-unit"><p class="empty-state">No declarative factual claims extracted for external verification.</p></div>`;
        }
    }

    // 4. Linguistic Risk Signals (Strictly Separated)
    if (d.sentiment) {
        setText('sentiment-tone-badge', d.sentiment.tone || 'Neutral');
        setBar('bar-positive', d.sentiment.positive_pct);
        setBar('bar-negative', d.sentiment.negative_pct);
        setBar('bar-fear', d.sentiment.fear_pct);
        setText('val-positive', d.sentiment.positive_pct + '%');
        setText('val-negative', d.sentiment.negative_pct + '%');
        setText('val-fear', d.sentiment.fear_pct + '%');
    }

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

    if (d.virality_risk) {
        animateNumber('virality-score-val', d.virality_risk.score || 0);
        setText('virality-risk-label', d.virality_risk.risk || 'Low');
        setBar('virality-bar', d.virality_risk.score);
        const vf = document.getElementById('virality-factors');
        if (vf) {
            vf.innerHTML = (d.virality_risk.velocity_factors || []).map(f =>
                `<div class="factor-item">⚡ ${f}</div>`
            ).join('');
        }
    }

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

    if (d.writing_style) {
        setText('style-formality', d.writing_style.formality || 'Standard');
        const sg = document.getElementById('style-grid');
        if (sg) {
            sg.innerHTML = `
                <div class="stat-item"><span class="stat-label">Avg Word Length</span><span class="stat-value">${d.writing_style.avg_word_length || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Passive Voice</span><span class="stat-value">${d.writing_style.passive_voice_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Direct Quotes</span><span class="stat-value">${d.writing_style.quote_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Numeric Claims</span><span class="stat-value">${d.writing_style.number_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Hyperlinks</span><span class="stat-value">${d.writing_style.url_count || 0}</span></div>
                <div class="stat-item"><span class="stat-label">Sentences</span><span class="stat-value">${d.writing_style.sentence_count || 0}</span></div>
            `;
        }
    }

    // Entities
    const entityBox = document.getElementById('entity-tags');
    if (entityBox) {
        const ents = d.entities || d.evidence || [];
        if (ents.length > 0) {
            entityBox.innerHTML = ents.map(e =>
                `<span class="entity-chip ${e.label}">${e.text} <small>${e.label}</small></span>`
            ).join('');
        } else {
            entityBox.innerHTML = '<span class="empty-state">No named entities detected</span>';
        }
    }

    // Triggered Keywords
    renderChips('keyword-chips', d.triggered_keywords || [], 'keyword-chip');

    // Raw JSON Report
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
        const res = await fetch(`${API}/api/history`);
        const data = await res.json();
        if (data.history && data.history.length > 0) {
            historyListEl.innerHTML = data.history.map(h => `
                <li class="history-item" onclick="loadHistoryItem('${h.snippet.replace(/'/g, "\\'")}')">
                    <div class="history-top">
                        <span class="history-badge ${(h.primary_verdict || h.classification).toLowerCase()}">${h.primary_verdict || h.classification}</span>
                        <span class="history-time">${new Date(h.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <div class="history-snippet">${h.snippet}</div>
                    <div class="history-score">Credibility: ${Math.round(h.credibility_score)}%</div>
                </li>
            `).join('');
            if (clearHistoryBtn) clearHistoryBtn.classList.remove('hidden');
        } else {
            historyListEl.innerHTML = `
                <div class="history-empty">
                    <div class="empty-icon">📂</div>
                    <p>No previous scans logged yet.<br>Analyze an article to start logging history.</p>
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
        const res = await fetch(`${API}/api/stats`);
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
            await fetch(`${API}/api/history`, { method: 'DELETE' });
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
        const summary = `🔍 TruthLens Evidence Summary:\n• Primary Verdict: ${lastData.primary_verdict}\n• Credibility Score: ${lastData.credibility_score}%\n• Evidence Confidence: ${lastData.confidence}%\n• Claims Extracted: ${lastData.claims ? lastData.claims.length : 0}\n• Verified via: https://dilipkumarprudhvi-a11y.github.io/truthlens/`;
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
