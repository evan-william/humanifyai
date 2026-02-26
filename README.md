<div align="center">

<img src="assets/humanify-banner.png" alt="HumanifyAI" width="600"/>

# HumanifyAI

**Transform AI-generated text into natural, human-sounding writing, with real-time linguistic scoring.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[**API Docs**](#api-reference) · [**Quick Start**](#quick-start) · [**Report Bug**](https://github.com/your-username/humanifyai/issues)

</div>

---

## What is HumanifyAI?

HumanifyAI is a self-hosted API and web dashboard that analyzes text for how closely it resembles natural human writing, then applies targeted transformations to improve that score.

Under the hood it extracts ~15 statistical linguistic features — sentence length variance, contraction rate, lexical diversity, passive voice density, and more — and maps them to a weighted 0–100 Human-Likeness score. The transformation engine then applies rule-based rewrites across four passes: passive voice rewriting, formal phrase simplification, contraction expansion, and sentence-opener variation. Results are shown as a before/after comparison with improvement delta.

No data is stored. Text is processed in memory and discarded after the response.

---

## Features

- Real-time Human-Likeness scoring (0–100) with a letter grade
- 15 linguistic feature breakdown with visual bars in the dashboard
- Configurable transformation pipeline (toggleable per feature)
- Before/after score comparison with improvement delta
- Actionable suggestions for manual edits
- Rate limiting, security headers, input validation — all on by default
- Full REST API with OpenAPI docs at `/api/docs`

---

## Transformation Engine

The transformer runs four passes in order:

**1. Passive Voice Rewrite** — Converts impersonal AI constructions into direct active voice. Example: "It has been shown that" → "Research shows that", "It is recommended that" → "We recommend that".

**2. Formal Simplification** — Replaces 80+ formal phrases, verbose constructions, and AI-typical words with casual equivalents. Covers transition words (Furthermore → On top of that), filler openings (It is important to note that → Worth noting:), verbose constructions (in order to → to, due to the fact that → because), formal verbs (utilize → use, leverage → use, prioritize → focus on), and redundant qualifiers (basically, essentially → removed).

**3. Contractions** — Expands 60+ patterns across all subjects and tenses. Handles capitalization variants, all negations, and subject-verb combinations (he is/she is/they are/we will, etc.).

**4. Sentence Variety** — Injects casual openers into monotonous mid-paragraph sentences to break up uniform AI structure.

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/your-username/humanifyai.git
cd humanifyai

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — at minimum set a real SECRET_KEY
```

### Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` for the web dashboard, or `http://localhost:8000/api/docs` for the interactive API explorer.

> **Note:** Always run via `uvicorn`, not `python main.py` directly. uvicorn sets up the correct Python path and ASGI server for the app to work.

---

## API Reference

All endpoints are under `/api/v1/`. Input validation and rate limiting (60 req/min per IP) apply to all routes.

### `POST /api/v1/analyze`

Score a text sample without modifying it.

**Request**
```json
{
  "text": "Your text here..."
}
```

**Response**
```json
{
  "score": 72.4,
  "grade": "B",
  "word_count": 85,
  "sentence_count": 6,
  "features": {
    "avg_sentence_length": 88.3,
    "contraction_rate": 76.0,
    "lexical_diversity": 91.2
  },
  "suggestions": [
    "Add contractions (it's, don't, you'll) for a more conversational tone."
  ]
}
```

---

### `POST /api/v1/transform`

Humanize text and return before/after scores.

**Request**
```json
{
  "text": "In conclusion, the utilization of advanced methodologies...",
  "options": {
    "use_contractions": true,
    "simplify_formal": true,
    "vary_sentences": true
  }
}
```

**Response**
```json
{
  "original_text": "...",
  "transformed_text": "To wrap up, using better methods...",
  "before_score": { "score": 38.1, "grade": "F" },
  "after_score":  { "score": 61.4, "grade": "C" },
  "improvement": 23.3
}
```

---

### `GET /api/health`

Returns `{"status": "ok", "version": "1.0.0"}`. Used by load balancers.

---

## Project Structure

```
humanifyai/
├── main.py                        # App entry point, middleware, router wiring
├── core/
│   ├── config.py                  # Settings from environment variables
│   ├── logging_config.py          # Centralized logging setup
│   ├── analyzer.py                # Linguistic feature extractor + scorer
│   └── transformer.py             # Text humanization pipeline (4 passes)
├── api/
│   ├── middleware/
│   │   ├── rate_limit.py          # Sliding-window rate limiter
│   │   └── security.py            # Security header injection
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   └── routers/
│       ├── analyze.py             # POST /api/v1/analyze
│       ├── transform.py           # POST /api/v1/transform
│       ├── health.py              # GET  /api/health
│       └── dashboard.py           # GET  / (web UI)
├── dashboard/
│   ├── templates/index.html       # Jinja2 dashboard template
│   └── static/
│       ├── css/main.css
│       └── js/app.js
├── tests/
│   ├── unit/
│   │   ├── test_analyzer.py
│   │   └── test_transformer.py
│   └── integration/
│       └── test_api.py
├── scripts/
│   ├── dev.sh                     # Development server launcher
│   └── run_tests.sh               # Test runner
├── pyrightconfig.json             # Pylance / Pyright config
├── .vscode/settings.json          # VS Code workspace settings
├── .env.example
├── .gitignore
├── LICENSE
├── pytest.ini
└── requirements.txt
```

---

## Running Tests

```bash
# All tests
./scripts/run_tests.sh

# Unit tests only
./scripts/run_tests.sh unit

# Integration tests only
./scripts/run_tests.sh integration

# With coverage report
./scripts/run_tests.sh --cov
```

Or run pytest directly:

```bash
pytest -v
pytest tests/unit -v
pytest tests/integration -v --tb=long
```

---

## Configuration

All settings live in `.env` (copy from `.env.example`). No config is hardcoded.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | **Required.** Long random string for request signing. |
| `ENVIRONMENT` | `development` | Set to `production` for stricter behavior. |
| `MAX_TEXT_LENGTH` | `10000` | Maximum characters per request. |
| `RATE_LIMIT_REQUESTS` | `60` | Requests per window per IP. |
| `RATE_LIMIT_WINDOW` | `60` | Window size in seconds. |
| `LOG_LEVEL` | `INFO` | Python logging level. |
| `ALLOWED_ORIGINS` | `["http://localhost:8000"]` | CORS allowed origins. |

---

## Security

- Input is validated and length-bounded before reaching any business logic.
- User text is never logged or persisted.
- All API responses include `Cache-Control: no-store`.
- Security headers (CSP, X-Frame-Options, HSTS-ready) are injected on every response.
- Rate limiting is applied per IP with a sliding window.
- CORS is set to explicit allowed origins — wildcard `*` is not used.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your change
4. Commit (`git commit -m 'Add my feature'`)
5. Push and open a Pull Request

Please run `./scripts/run_tests.sh` before submitting.

---

## License

MIT — see [LICENSE](LICENSE).
