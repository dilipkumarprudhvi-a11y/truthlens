/**
 * TruthLens AI — Client-Side Application v3
 *
 * Architecture:
 *  - All API calls go to CONFIG.API_BASE (set in config.js)
 *  - Multi-endpoint fallback: tries Render.com backend first, local server second
 *  - Evidence matrix renders per-claim cards with supporting/contradicting sources
 *  - No random numbers are used anywhere in this file
 */

/* ═══ CONFIG & CONSTANTS ════════════════════════════════════ */

const SAMPLES = {
  real: `NASA's James Webb Space Telescope has captured detailed images of a distant galaxy, revealing early star formation that occurred approximately 13 billion years ago. Scientists at the Space Telescope Science Institute published these findings in the Astrophysical Journal.`,
  breaking: `BREAKING: The Federal Reserve announced an emergency interest rate adjustment following stronger-than-expected inflation data. The central bank confirmed the decision was reached by unanimous vote of the Federal Open Market Committee.`,
  clickbait: `You WON'T BELIEVE what happened next!! Scientists are SHOCKED by this incredible discovery that will change EVERYTHING you know about nutrition. Click to reveal the SECRET they don't want you to see!!!`,
  disinfo: `URGENT: The illuminati globalist plot to destroy our country through new world order chemtrails is exposed. What doctors are hiding: miracle cure discovered. Wake up sheeple! Banned video reveals it all!`
};

const API_ENDPOINTS = [
  typeof CONFIG !== 'undefined' ? CONFIG.API_BASE : null,
  'http://127.0.0.1:8000',
].filter(Boolean);

const STEP_MSGS = [
  'Extracting factual claims…',
  'Querying evidence repositories…',
  'Running NLI evaluation…',
  'Synthesizing credibility score…',
];

/* ═══ STATE ═════════════════════════════════════════════════ */

let latestResult = null;
let uploadedFile = null;
let abortCtrl = null;

/* ═══ DOM REFERENCES ════════════════════════════════════════ */

const $ = id => document.getElementById(id);

const ui = {
  form:           $('analyze-form'),
  textInput:      $('text-input'),
  analyzeBtn:     $('analyze-btn'),
  clearBtn:       $('clear-btn'),
  progressCard:   $('progress-card'),
  progressFill:   $('progress-fill'),
  progressLabel:  $('progress-label'),
  results:        $('results'),
  verdictCard:    $('verdict-card'),
  apiStatusPill:  $('api-status-pill'),
  apiStatusText:  $('api-status-text'),
  modal:          $('modal'),
  sidebar:        $('sidebar'),
  historyList:    $('history-list'),
  charCount:      $('char-count'),
  wordCount:      $('word-count'),
  readTime:       $('read-time'),
  urlInput:       $('url-input'),
  fetchUrlBtn:    $('fetch-url-btn'),
  dropZone:       $('drop-zone'),
  fileInput:      $('file-input'),
};

/* ═══ UTILITIES ═════════════════════════════════════════════ */

const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const round1 = v => Math.round(v * 10) / 10;

function fmtTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  Object.assign(t.style, {
    position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 9999,
    background: type === 'error' ? '#EF4444' : type === 'success' ? '#22C55E' : '#2563EB',
    color: '#fff', fontWeight: '700', fontSize: '.82rem',
    padding: '.6rem 1.1rem', borderRadius: '8px',
    boxShadow: '0 8px 24px rgba(0,0,0,.5)',
    transform: 'translateY(20px)', opacity: '0',
    transition: 'all .3s cubic-bezier(.16,1,.3,1)',
  });
  document.body.appendChild(t);
  requestAnimationFrame(() => { t.style.transform = 'translateY(0)'; t.style.opacity = '1'; });
  setTimeout(() => {
    t.style.transform = 'translateY(10px)'; t.style.opacity = '0';
    setTimeout(() => t.remove(), 350);
  }, 2800);
}

/* ═══ API HEALTH CHECK ══════════════════════════════════════ */

async function checkApiHealth() {
  setStatus('checking', 'Connecting to backend…');
  const probeUrls = [];
  for (const base of API_ENDPOINTS) {
    probeUrls.push(`${base}/api/health`);
    probeUrls.push(`${base}/health`);
  }

  for (const url of probeUrls) {
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(12000) });
      if (r.ok) {
        const d = await r.json();
        const nlp = d.nlp_available ?? d.nlp ?? true;
        setStatus('ok', `Backend online · ${nlp ? 'NLP active' : 'Engine online'}`);
        return url;
      }
    } catch { /* try next endpoint */ }
  }

  setStatus('error', 'Backend offline — waking up server…');
  // Retry after 5 seconds in case Render is spinning up from cold sleep
  setTimeout(checkApiHealth, 5000);
  return null;
}

function setStatus(state, msg) {
  const pill = ui.apiStatusPill;
  if (!pill) return;
  const dot = pill.querySelector('.dot');
  const text = ui.apiStatusText;
  pill.className = 'api-status-pill ' + (state === 'ok' ? 'ok' : state === 'error' ? 'error' : '');
  if (dot) dot.className = 'dot ' + (state === 'ok' ? 'dot-ok' : state === 'error' ? 'dot-error' : 'dot-checking');
  if (text) text.textContent = msg || (state === 'checking' ? 'Connecting…' : state);
}

/* ═══ PROGRESS ══════════════════════════════════════════════ */

let stepTimer = null;
let stepIdx = 0;

function startProgress() {
  ui.progressCard.classList.remove('hidden');
  ui.results.classList.add('hidden');
  stepIdx = 0;
  updateStep(0);
  stepTimer = setInterval(() => {
    stepIdx = Math.min(stepIdx + 1, STEP_MSGS.length - 1);
    updateStep(stepIdx);
  }, 2200);
}

function updateStep(i) {
  ui.progressLabel.textContent = STEP_MSGS[i];
  ui.progressFill.style.width = `${(i + 1) / STEP_MSGS.length * 90}%`;
  ['ps1','ps2','ps3','ps4'].forEach((id, idx) => {
    $(`ps${idx+1}`)?.classList.toggle('active', idx <= i);
  });
}

function stopProgress() {
  clearInterval(stepTimer);
  ui.progressFill.style.width = '100%';
  setTimeout(() => { ui.progressCard.classList.add('hidden'); }, 400);
}

/* ═══ API CALL ══════════════════════════════════════════════ */

async function callAnalyzeApi(payload) {
  abortCtrl = new AbortController();
  const timeout = setTimeout(() => abortCtrl.abort(), 60000);

  const candidateUrls = [];
  for (const base of API_ENDPOINTS) {
    candidateUrls.push(`${base}/api/analyze`);
    candidateUrls.push(`${base}/analyze`);
  }

  let lastErr;
  for (const url of candidateUrls) {
    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: abortCtrl.signal,
      });
      clearTimeout(timeout);
      if (r.ok) {
        setStatus('ok', 'Backend online · Active');
        return await r.json();
      } else if (r.status !== 404 && r.status !== 405) {
        const err = await r.json().catch(() => ({ detail: r.statusText }));
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
    } catch (e) {
      lastErr = e;
      if (e.name === 'AbortError') break;
    }
  }
  clearTimeout(timeout);
  throw lastErr || new Error('All endpoints unreachable');
}

/* ═══ MAIN ANALYZE FLOW ═════════════════════════════════════ */

async function analyze(text) {
  if (!text || text.trim().length < 15) {
    showToast('Please enter at least 15 characters', 'error');
    return;
  }

  setBtnLoading(ui.analyzeBtn, true);
  startProgress();

  try {
    const result = await callAnalyzeApi({ text: text.trim() });
    stopProgress();
    latestResult = result;
    renderResults(result);
    persistHistory(result, text.trim());
    loadHistory();
  } catch (e) {
    stopProgress();
    if (e.name !== 'AbortError') {
      showToast(`Analysis failed: ${e.message}`, 'error');
    }
  } finally {
    setBtnLoading(ui.analyzeBtn, false);
  }
}

function setBtnLoading(btn, on) {
  const label = btn.querySelector('.btn-label');
  const spin = btn.querySelector('.btn-spinner');
  const icon = btn.querySelector('.btn-icon-svg');
  if (label) label.textContent = on ? 'Analyzing…' : 'Analyze';
  if (spin) spin.classList.toggle('hidden', !on);
  if (icon) icon.style.display = on ? 'none' : '';
  btn.disabled = on;
}

/* ═══ RENDER RESULTS ════════════════════════════════════════ */

function renderResults(d) {
  ui.results.classList.remove('hidden');

  // Verdict card
  renderVerdictCard(d);

  // Claims & Evidence
  renderClaimsSection(d.claims || []);

  // Linguistic signals
  const ling = d.linguistic_signals || {};
  renderSentiment(d.sentiment || ling.sentiment, ling.triggered_keywords || d.triggered_keywords || []);
  renderClickbait(d.clickbait || ling.clickbait);
  renderBias(d.bias || ling.bias);
  renderVirality(d.virality_risk || ling.virality_risk);
  renderReadability(d.readability || ling.readability);
  renderWritingStyle(d.writing_style || ling.writing_style);
  renderEntities(d.entities || d.evidence || []);
  renderFlags(ling.triggered_keywords || d.triggered_keywords || []);
  renderJson(d);

  ui.results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* Verdict card */
function renderVerdictCard(d) {
  const verdict = (d.primary_verdict || 'UNVERIFIED').toLowerCase();
  const legacy  = (d.legacy_classification || d.classification || 'SUSPICIOUS').toUpperCase();
  const cred    = d.credibility_score || 50;
  const fake    = d.fake_probability || 50;

  // Determine if result is REAL, FAKE, or SUSPICIOUS/UNCERTAIN
  const isFake = legacy === 'FAKE' || verdict === 'contradicted' || fake > cred;
  const isSuspicious = legacy === 'SUSPICIOUS' || verdict === 'mixed';

  let displayScore, scoreColor, scoreLabel;
  if (isFake) {
    displayScore = Math.round(fake);
    scoreColor = '#EF4444'; // Vibrant Red
    scoreLabel = 'FAKE';
  } else if (isSuspicious) {
    displayScore = Math.round(fake >= 50 ? fake : cred);
    scoreColor = '#F59E0B'; // Amber
    scoreLabel = 'SUSPICIOUS';
  } else {
    displayScore = Math.round(cred);
    scoreColor = '#22C55E'; // Emerald Green
    scoreLabel = 'REAL';
  }

  // Gauge ring (circumference = 2π×42 ≈ 264)
  const dashOffset = 264 - (264 * clamp(displayScore, 0, 100)) / 100;
  const ring = $('gauge-ring');
  ring.style.strokeDashoffset = dashOffset;
  ring.style.stroke = scoreColor;

  const valEl = $('gauge-val');
  valEl.textContent = displayScore;
  valEl.style.color = scoreColor;

  const lblEl = $('gauge-lbl');
  if (lblEl) {
    lblEl.textContent = scoreLabel;
    lblEl.style.color = scoreColor;
  }

  // Card coloring
  ui.verdictCard.className = `verdict-card ${verdict}`;

  // Primary badge
  const pb = $('primary-badge');
  pb.className = `verdict-badge ${verdict}`;
  pb.textContent = d.primary_verdict || (isFake ? 'CONTRADICTED' : 'SUPPORTED');

  // Legacy badge
  const lb = $('legacy-badge');
  lb.textContent = `Verdict: ${legacy}`;
  lb.style.color = scoreColor;

  // Tone badge
  const tone = (d.sentiment || {}).tone || (d.linguistic_signals?.sentiment || {}).tone || '';
  $('tone-badge').textContent = tone || '—';

  // Headline and message
  const headlines = {
    SUPPORTED:    'Content Appears Credible',
    CONTRADICTED: 'Content Contradicted by Evidence',
    MIXED:        'Mixed Signals — Partial Verification',
    UNVERIFIED:    'Insufficient Evidence to Verify',
  };
  $('verdict-headline').textContent = headlines[d.primary_verdict] || 'Analysis Complete';
  $('verdict-msg').textContent = d.message || '—';

  // Dual percentage bar (True/Real in Green vs False/Fake in Red)
  const realVal = Math.round(cred);
  const fakeVal = Math.round(fake);
  if ($('vbar-val-real')) $('vbar-val-real').textContent = `${realVal}%`;
  if ($('vbar-val-fake')) $('vbar-val-fake').textContent = `${fakeVal}%`;
  if ($('vbar-fill-real')) $('vbar-fill-real').style.width = `${realVal}%`;
  if ($('vbar-fill-fake')) $('vbar-fill-fake').style.width = `${fakeVal}%`;

  // Metrics
  $('vm-fake').textContent = `${fake}%`;
  $('vm-conf').textContent = `${d.confidence || 0}%`;
  $('vm-words').textContent = (d.text_length || 0).toLocaleString();
  $('vm-claims').textContent = (d.claims || []).length;

  const fakeEl = $('vm-fake');
  fakeEl.style.color = fake > 60 ? '#EF4444' : fake > 40 ? '#F59E0B' : '#22C55E';
}

/* Claims & evidence matrix */
function renderClaimsSection(claims) {
  const container = $('claims-container');
  if (!claims.length) {
    container.innerHTML = '<div class="claim-card"><p class="no-evidence">No structured factual claims were extracted from this content.</p></div>';
    return;
  }

  container.innerHTML = claims.map((claim, i) => {
    const vc = (claim.verdict || 'UNVERIFIED').toLowerCase();
    const ev = claim.evidence || [];
    const evHtml = ev.length
      ? ev.map(e => `
        <div class="evidence-card">
          <div class="evidence-top">
            <a href="${escHtml(e.url)}" target="_blank" rel="noopener" class="evidence-link">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
              ${escHtml(e.title || e.source_name)}
            </a>
            <span class="authority-tag">${e.source_name} · Auth: ${Math.round((e.authority_score || 0) * 100)}%</span>
          </div>
          <p class="evidence-snippet">${escHtml(e.snippet || 'No snippet available.')}</p>
        </div>`).join('')
      : `<p class="no-evidence">No matching evidence found in Wikipedia, DuckDuckGo, or configured fact-check APIs for this claim.</p>`;

    return `
      <div class="claim-card">
        <div class="claim-header">
          <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap">
            <span class="claim-id">CLAIM ${String(i + 1).padStart(2, '0')}</span>
            <span class="claim-verdict cv-${vc}">${claim.verdict}</span>
            <span class="claim-verdict" style="background:rgba(255,255,255,.05);border:1px solid var(--border);color:var(--text-3);font-size:.68rem">Confidence: ${claim.confidence || 0}%</span>
          </div>
        </div>
        <p class="claim-text">"${escHtml(claim.text)}"</p>
        <div class="claim-explanation">${escHtml(claim.explanation || 'No explanation available.')}</div>
        ${ev.length ? `<p class="evidence-label">${ev.length} evidence source${ev.length > 1 ? 's' : ''} retrieved</p>` : ''}
        <div class="evidence-list">${evHtml}</div>
      </div>`;
  }).join('');
}

/* Sentiment */
function renderSentiment(s, flags) {
  if (!s) return;
  $('badge-sentiment').textContent = s.tone || '—';
  const mContainer = $('meters-sentiment');
  mContainer.innerHTML = [
    { label: 'Positive Tone', val: s.positive_pct || 0, cls: 'green' },
    { label: 'Negative Tone', val: s.negative_pct || 0, cls: 'amber' },
    { label: 'Fear / Alarm',  val: s.fear_pct || 0,     cls: 'red' },
  ].map(m => `
    <div class="meter">
      <div class="meter-meta"><span>${m.label}</span><span class="meter-val">${m.val}%</span></div>
      <div class="track"><div class="bar ${m.cls}" style="width:${m.val}%"></div></div>
    </div>`).join('');
}

/* Clickbait */
function renderClickbait(c) {
  if (!c) return;
  const score = c.score || 0;
  $('badge-clickbait').textContent = c.level || '—';
  $('score-clickbait').textContent = score;
  const barCls = score >= 70 ? 'red' : score >= 45 ? 'amber' : 'teal';
  $('bar-clickbait').className = `bar ${barCls}`;
  $('bar-clickbait').style.width = `${score}%`;

  const chips = $('chips-clickbait');
  const trig = c.triggers || [];
  chips.innerHTML = trig.length
    ? trig.map(t => `<span class="c-chip flag">${escHtml(t)}</span>`).join('')
    : '<span class="empty-note">No clickbait triggers found</span>';
}

/* Bias */
function renderBias(b) {
  if (!b) return;
  $('badge-bias').textContent = b.leaning || 'Center';
  const needle = $('bias-needle');
  const ratio = clamp(b.balance_ratio || 0.5, 0, 1);
  needle.style.left = `${ratio * 100}%`;

  const left = (b.left_triggers || []).map(t => `<span class="c-chip">${escHtml(t)}</span>`).join('');
  const right = (b.right_triggers || []).map(t => `<span class="c-chip">${escHtml(t)}</span>`).join('');
  $('chips-bias').innerHTML = left + right || '<span class="empty-note">No strong partisan vocabulary detected</span>';
}

/* Virality */
function renderVirality(v) {
  if (!v) return;
  const score = v.score || 0;
  $('badge-virality').textContent = v.risk || '—';
  $('score-virality').textContent = score;
  const barCls = score >= 65 ? 'red' : score >= 35 ? 'amber' : 'teal';
  $('bar-virality').className = `bar ${barCls}`;
  $('bar-virality').style.width = `${score}%`;
  $('factors-virality').innerHTML = (v.velocity_factors || [])
    .map(f => `<div class="factor-item">• ${escHtml(f)}</div>`).join('');
}

/* Readability */
function renderReadability(r) {
  if (!r) return;
  const score = r.score || 0;
  $('badge-readability').textContent = r.grade || '—';
  $('score-readability').textContent = score;
  $('bar-readability').style.width = `${score}%`;
  $('read-stats').innerHTML = `${r.sentence_count || 0} sentences · avg ${r.avg_sentence_length || 0} words/sentence`;
}

/* Writing Style */
function renderWritingStyle(w) {
  if (!w) return;
  $('badge-style').textContent = w.formality || '—';
  $('style-grid').innerHTML = [
    { l: 'Formality',     v: w.formality || '—' },
    { l: 'Avg Word Len',  v: w.avg_word_length || '—' },
    { l: 'Passive Voice', v: w.passive_voice_count ?? '—' },
    { l: 'Direct Quotes', v: w.quote_count ?? '—' },
    { l: 'Statistics',    v: w.number_count ?? '—' },
    { l: 'URLs Cited',    v: w.url_count ?? '—' },
  ].map(i => `<div class="sg-item"><span class="sg-label">${i.l}</span><span class="sg-val">${i.v}</span></div>`).join('');
}

/* Entities */
function renderEntities(entities) {
  const chips = $('chips-entities');
  if (!entities.length) {
    chips.innerHTML = '<span class="empty-note">No named entities detected (spaCy unavailable or text too short)</span>';
    return;
  }
  chips.innerHTML = entities.map(e => `
    <span class="ent-chip ${escHtml(e.label)}">
      ${escHtml(e.text)} <small>${escHtml(e.label)}</small>
    </span>`).join('');
}

/* Deception flags */
function renderFlags(flags) {
  const chips = $('chips-flags');
  if (!flags.length) {
    chips.innerHTML = '<span class="empty-note">✓ No hard deception trigger patterns detected</span>';
    return;
  }
  chips.innerHTML = flags.map(f => `<span class="c-chip flag">🚩 ${escHtml(f)}</span>`).join('');
}

/* JSON */
function renderJson(d) {
  $('json-output').textContent = JSON.stringify(d, null, 2);
}

/* ═══ URL FETCH ════════════════════════════════════════════ */

async function fetchAndAnalyzeUrl(url) {
  if (!url || !url.startsWith('http')) {
    showToast('Please enter a valid http/https URL', 'error');
    return;
  }

  const btn = ui.fetchUrlBtn;
  setBtnLoading(btn, true);
  startProgress();

  const candidateUrls = [];
  for (const base of API_ENDPOINTS) {
    candidateUrls.push(`${base}/api/url/extract`);
    candidateUrls.push(`${base}/url/extract`);
  }

  try {
    for (const ep of candidateUrls) {
      try {
        const r = await fetch(ep, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url }),
          signal: AbortSignal.timeout(30000),
        });
        if (r.ok) {
          const d = await r.json();
          if (d.text) {
            stopProgress();
            setBtnLoading(btn, false);
            ui.textInput.value = d.text.slice(0, 25000);
            switchTab('text');
            updateCounts();
            showToast(`Article extracted: ${d.length?.toLocaleString() || d.text.length} chars`, 'success');
            await analyze(d.text.slice(0, 25000));
            return;
          }
        }
      } catch { /* try next */ }
    }
    throw new Error('Could not fetch article from specified URL');
  } catch (e) {
    stopProgress();
    showToast(`URL fetch failed: ${e.message}`, 'error');
  } finally {
    setBtnLoading(btn, false);
  }
}

/* ═══ OCR ══════════════════════════════════════════════════ */

async function ocrAndAnalyze(file) {
  const form = new FormData();
  form.append('image', file);

  startProgress();
  const candidateUrls = [];
  for (const base of API_ENDPOINTS) {
    candidateUrls.push(`${base}/api/ocr/extract`);
    candidateUrls.push(`${base}/ocr/extract`);
  }

  try {
    for (const ep of candidateUrls) {
      try {
        const r = await fetch(ep, { method: 'POST', body: form, signal: AbortSignal.timeout(35000) });
        if (r.ok) {
          const d = await r.json();
          stopProgress();
          if (d.text) {
            ui.textInput.value = d.text.slice(0, 25000);
            switchTab('text');
            updateCounts();
            showToast(`OCR complete — ${d.text.length} chars extracted`, 'success');
            await analyze(d.text);
            return;
          }
        }
      } catch { /* try next */ }
    }
    throw new Error('OCR service unreachable or returned empty text');
  } catch (e) {
    stopProgress();
    showToast(`OCR failed: ${e.message}`, 'error');
  }
}

/* ═══ HISTORY ══════════════════════════════════════════════ */

function persistHistory(result, text) {
  const stored = JSON.parse(localStorage.getItem('tl_history') || '[]');
  const item = {
    id: result.scan_id,
    timestamp: result.created_at || new Date().toISOString(),
    snippet: text.slice(0, 120),
    classification: result.legacy_classification,
    primary_verdict: result.primary_verdict,
    credibility_score: result.credibility_score,
    fake_probability: result.fake_probability,
  };
  stored.unshift(item);
  localStorage.setItem('tl_history', JSON.stringify(stored.slice(0, 50)));
}

function loadHistory() {
  const stored = JSON.parse(localStorage.getItem('tl_history') || '[]');
  const list = ui.historyList;

  if (!stored.length) {
    list.innerHTML = '<li style="font-size:.8rem;color:var(--text-3);text-align:center;padding:1rem">No scans yet</li>';
    updateStats([], $('s-total'), $('s-real'), $('s-sus'), $('s-fake'));
    $('clear-history-btn').classList.add('hidden');
    return;
  }

  $('clear-history-btn').classList.remove('hidden');
  list.innerHTML = stored.map(item => `
    <li class="history-item" data-snippet="${escHtml(item.snippet)}">
      <div class="hi-top">
        <span class="hi-badge ${(item.classification || '').toLowerCase()}">${item.classification}</span>
        <span class="hi-time">${fmtTime(item.timestamp)}</span>
      </div>
      <p class="hi-snippet">${escHtml(item.snippet)}</p>
      <p class="hi-score">Credibility: ${item.credibility_score}% · Deception: ${item.fake_probability}%</p>
    </li>`).join('');

  updateStats(stored, $('s-total'), $('s-real'), $('s-sus'), $('s-fake'));
  attachHistoryClicks();
}

function updateStats(items, total, real, sus, fake) {
  total.textContent = items.length;
  real.textContent  = items.filter(i => i.classification === 'REAL').length;
  sus.textContent   = items.filter(i => i.classification === 'SUSPICIOUS').length;
  fake.textContent  = items.filter(i => i.classification === 'FAKE').length;
}

function attachHistoryClicks() {
  ui.historyList.querySelectorAll('.history-item').forEach(el => {
    el.addEventListener('click', () => {
      const snip = el.dataset.snippet;
      if (snip) {
        ui.textInput.value = snip;
        switchTab('text');
        updateCounts();
        closeSidebar();
        ui.textInput.focus();
      }
    });
  });
}

/* ═══ TABS ══════════════════════════════════════════════════ */

function switchTab(name) {
  ['text', 'url', 'img'].forEach(n => {
    const tab = $(`tab-${n}`);
    const panel = $(`panel-${n}`);
    const isActive = n === name;
    tab.classList.toggle('active', isActive);
    tab.setAttribute('aria-selected', String(isActive));
    panel.classList.toggle('hidden', !isActive);
  });
}

document.getElementById('tab-text')?.addEventListener('click', () => switchTab('text'));
document.getElementById('tab-url')?.addEventListener('click',  () => switchTab('url'));
document.getElementById('tab-img')?.addEventListener('click',  () => switchTab('img'));

/* ═══ COUNTER ═══════════════════════════════════════════════ */

function updateCounts() {
  const text = ui.textInput.value;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const chars = text.length;
  ui.charCount.textContent = chars.toLocaleString();
  ui.wordCount.textContent = words.toLocaleString();
  const mins = Math.ceil(words / 200);
  ui.readTime.textContent = words > 30 ? `~${mins} min read` : '';
  ui.analyzeBtn.disabled = chars < 15 || chars > 25000;
}

ui.textInput.addEventListener('input', updateCounts);

/* ═══ SAMPLE CHIPS ══════════════════════════════════════════ */

document.querySelectorAll('.chip[data-s]').forEach(btn => {
  btn.addEventListener('click', () => {
    const key = btn.dataset.s;
    if (SAMPLES[key]) {
      ui.textInput.value = SAMPLES[key];
      switchTab('text');
      updateCounts();
      ui.textInput.focus();
    }
  });
});

/* ═══ SIDEBAR ════════════════════════════════════════════════ */

function openSidebar()  { ui.sidebar.classList.add('open');  }
function closeSidebar() { ui.sidebar.classList.remove('open'); }

$('open-sidebar')?.addEventListener('click', openSidebar);
$('close-sidebar')?.addEventListener('click', closeSidebar);

$('clear-history-btn')?.addEventListener('click', () => {
  if (confirm('Clear all scan history?')) {
    localStorage.removeItem('tl_history');
    loadHistory();
  }
});

/* ═══ FORM SUBMIT ════════════════════════════════════════════ */

ui.form?.addEventListener('submit', e => {
  e.preventDefault();
  analyze(ui.textInput.value.trim());
});

ui.clearBtn?.addEventListener('click', () => {
  ui.textInput.value = '';
  updateCounts();
  ui.textInput.focus();
});

/* ═══ URL FETCH ════════════════════════════════════════════ */

ui.fetchUrlBtn?.addEventListener('click', () => {
  fetchAndAnalyzeUrl(ui.urlInput.value.trim());
});
ui.urlInput?.addEventListener('keydown', e => {
  if (e.key === 'Enter') fetchAndAnalyzeUrl(ui.urlInput.value.trim());
});

/* ═══ DRAG-DROP IMAGE ═══════════════════════════════════════ */

ui.dropZone?.addEventListener('click', () => ui.fileInput.click());
ui.dropZone?.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') ui.fileInput.click(); });
ui.fileInput?.addEventListener('change', () => {
  const f = ui.fileInput.files[0];
  if (f) handleImageFile(f);
});

['dragenter','dragover'].forEach(ev => {
  ui.dropZone?.addEventListener(ev, e => { e.preventDefault(); ui.dropZone.classList.add('over'); });
});
['dragleave','drop'].forEach(ev => {
  ui.dropZone?.addEventListener(ev, e => { e.preventDefault(); ui.dropZone.classList.remove('over'); });
});
ui.dropZone?.addEventListener('drop', e => {
  const f = e.dataTransfer?.files[0];
  if (f && f.type.startsWith('image/')) handleImageFile(f);
  else showToast('Please drop an image file (PNG, JPG, WEBP)', 'error');
});

function handleImageFile(f) {
  if (f.size > 5 * 1024 * 1024) { showToast('Image too large (max 5MB)', 'error'); return; }
  uploadedFile = f;
  const url = URL.createObjectURL(f);
  $('preview-img').src = url;
  $('img-preview').classList.remove('hidden');
  ui.dropZone.classList.add('hidden');
  $('ocr-note').textContent = `${f.name} — ready to OCR`;
  ocrAndAnalyze(f);
}

$('remove-img-btn')?.addEventListener('click', () => {
  uploadedFile = null;
  ui.fileInput.value = '';
  $('img-preview').classList.add('hidden');
  ui.dropZone.classList.remove('hidden');
});

/* ═══ MODAL ══════════════════════════════════════════════════ */

$('methodology-btn')?.addEventListener('click', () => { ui.modal.classList.remove('hidden'); });
$('close-modal')?.addEventListener('click',    () => { ui.modal.classList.add('hidden'); });
ui.modal?.addEventListener('click', e => { if (e.target === ui.modal) ui.modal.classList.add('hidden'); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') ui.modal?.classList.add('hidden'); });

/* ═══ EXPORT / COPY ══════════════════════════════════════════ */

$('share-btn')?.addEventListener('click', async () => {
  if (!latestResult) return;
  const r = latestResult;
  const summary = `TruthLens Analysis
Verdict: ${r.primary_verdict} | Classification: ${r.legacy_classification}
Credibility: ${r.credibility_score}% | Deception Risk: ${r.fake_probability}%
Claims: ${(r.claims||[]).length} | Message: ${r.message}
Analyzed at: ${r.created_at}`;
  if (await copyText(summary)) showToast('Summary copied!', 'success');
  else showToast('Copy failed — try selecting manually', 'error');
});

const doExport = () => {
  if (!latestResult) return;
  const blob = new Blob([JSON.stringify(latestResult, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `truthlens-${latestResult.scan_id || 'report'}.json`;
  a.click(); URL.revokeObjectURL(url);
};
$('export-btn')?.addEventListener('click', doExport);
$('export-btn2')?.addEventListener('click', doExport);

/* ═══ INIT ═══════════════════════════════════════════════════ */

(async () => {
  await checkApiHealth();
  loadHistory();
  updateCounts();
})();
