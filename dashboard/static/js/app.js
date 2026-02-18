/**
 * HumanifyAI dashboard — handles API calls and DOM updates.
 * No external dependencies; plain vanilla JS.
 *
 * Security notes:
 *  - All text is inserted via textContent / value, never innerHTML with user data.
 *  - API responses that render into the DOM are escaped before display.
 */

"use strict";

const $ = (id) => document.getElementById(id);

// ── DOM refs ──────────────────────────────────────────────────────────────
const inputText    = $("inputText");
const outputText   = $("outputText");
const placeholder  = $("outputPlaceholder");
const charCount    = $("charCount");
const analyzeBtn   = $("analyzeBtn");
const transformBtn = $("transformBtn");
const copyBtn      = $("copyBtn");
const errorBanner  = $("errorBanner");
const errorMsg     = $("errorMsg");
const scoreSection = $("scoreSection");
const suggestionsSection = $("suggestionsSection");
const featuresSection    = $("featuresSection");

// ── Char counter ──────────────────────────────────────────────────────────
inputText.addEventListener("input", () => {
  const len = inputText.value.length;
  charCount.textContent = `${len.toLocaleString()} / 10,000`;
  charCount.style.color = len > 9000 ? "#f87171" : "";
});

// ── Copy button ───────────────────────────────────────────────────────────
copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(outputText.value).then(() => {
    copyBtn.textContent = "Copied!";
    setTimeout(() => { copyBtn.textContent = "Copy"; }, 2000);
  });
});

// ── Buttons ───────────────────────────────────────────────────────────────
analyzeBtn.addEventListener("click", () => runAnalyze());
transformBtn.addEventListener("click", () => runTransform());

// ── API helpers ───────────────────────────────────────────────────────────
function getOptions() {
  return {
    use_contractions: $("optContractions").checked,
    simplify_formal:  $("optFormal").checked,
    vary_sentences:   $("optVariety").checked,
  };
}

function setLoading(btn, state) {
  btn.disabled = state;
  state ? btn.classList.add("loading") : btn.classList.remove("loading");
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorBanner.style.display = "flex";
}

function clearError() {
  errorBanner.style.display = "none";
}

async function apiPost(endpoint, body) {
  const res = await fetch(endpoint, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || `Server error ${res.status}`);
  }
  return data;
}

// ── Analyze only ──────────────────────────────────────────────────────────
async function runAnalyze() {
  const text = inputText.value.trim();
  if (!text) { showError("Please enter some text first."); return; }

  clearError();
  setLoading(analyzeBtn, true);

  try {
    const result = await apiPost("/api/v1/analyze", { text });
    renderScoreCard("beforeScore", "beforeGrade", "beforeMeta", result);
    $("afterCard").style.display = "none";
    $("improvement").textContent = "";
    scoreSection.style.display = "flex";
    renderSuggestions(result.suggestions);
    renderFeatures(result.features);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(analyzeBtn, false);
  }
}

// ── Transform ─────────────────────────────────────────────────────────────
async function runTransform() {
  const text = inputText.value.trim();
  if (!text) { showError("Please enter some text first."); return; }

  clearError();
  setLoading(transformBtn, true);

  try {
    const result = await apiPost("/api/v1/transform", {
      text,
      options: getOptions(),
    });

    // Show output
    placeholder.style.display = "none";
    outputText.style.display  = "block";
    outputText.value          = result.transformed_text;
    copyBtn.style.display     = "block";

    // Scores
    renderScoreCard("beforeScore", "beforeGrade", "beforeMeta", result.before_score);
    renderScoreCard("afterScore", "afterGrade", null, result.after_score);

    const imp = result.improvement;
    const impEl = $("improvement");
    impEl.textContent = (imp >= 0 ? "+" : "") + imp.toFixed(1) + " pts";
    impEl.className   = "improvement " + (imp >= 0 ? "positive" : "negative");

    $("afterCard").style.display = "block";
    scoreSection.style.display   = "flex";

    renderSuggestions(result.after_score.suggestions);
    renderFeatures(result.after_score.features);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(transformBtn, false);
  }
}

// ── Render helpers ────────────────────────────────────────────────────────
function renderScoreCard(scoreId, gradeId, metaId, data) {
  const scoreEl = $(scoreId);
  const gradeEl = $(gradeId);

  scoreEl.textContent = data.score.toFixed(1);

  // Color the score based on value
  if (data.score >= 70) {
    scoreEl.style.color = "#34d399";
  } else if (data.score >= 50) {
    scoreEl.style.color = "#fbbf24";
  } else {
    scoreEl.style.color = "#f87171";
  }

  gradeEl.textContent = `Grade ${data.grade}`;

  if (metaId) {
    $(metaId).textContent = `${data.word_count} words · ${data.sentence_count} sentences`;
  }
}

function renderSuggestions(suggestions) {
  const list = $("suggestionsList");
  list.innerHTML = "";    // safe — no user data inserted here

  if (!suggestions || suggestions.length === 0) {
    suggestionsSection.style.display = "none";
    return;
  }

  suggestions.forEach((tip) => {
    const li = document.createElement("li");
    li.textContent = tip;    // textContent, not innerHTML
    list.appendChild(li);
  });

  suggestionsSection.style.display = "block";
}

function renderFeatures(features) {
  const grid = $("featuresGrid");
  grid.innerHTML = "";    // safe — keys/values are numbers from our own API

  if (!features || Object.keys(features).length === 0) {
    featuresSection.style.display = "none";
    return;
  }

  Object.entries(features).forEach(([name, value]) => {
    const item  = document.createElement("div");
    item.className = "feature-item";

    const label = document.createElement("div");
    label.className   = "feature-name";
    label.textContent = name.replace(/_/g, " ");

    const barWrap = document.createElement("div");
    barWrap.className = "feature-bar-wrap";

    const bar = document.createElement("div");
    bar.className = "feature-bar";
    bar.style.width = `${Math.min(100, value)}%`;
    bar.style.background = barColor(value);

    const val = document.createElement("div");
    val.className   = "feature-val";
    val.textContent = value.toFixed(1);

    barWrap.appendChild(bar);
    item.append(label, barWrap, val);
    grid.appendChild(item);
  });

  featuresSection.style.display = "block";
}

function barColor(value) {
  if (value >= 75) return "#34d399";
  if (value >= 50) return "#fbbf24";
  return "#f87171";
}