# SourceHunter

AI-Powered Supplier Discovery & Procurement Intelligence Platform.

## V1 Principle

SourceHunter must return reliable supplier data or fewer results. It must never fabricate supplier names, prices, websites, contacts, or URLs.

## Documentation

- Chinese PRD: `docs/PRD.zh.md`
- English PRD: `docs/PRD.en.md`
- Chinese MVP Scope: `docs/MVP_SCOPE.zh.md`
- English MVP Scope: `docs/MVP_SCOPE.en.md`
- Chinese Technical Spec: `docs/TECHNICAL_SPEC.zh.md`
- English Technical Spec: `docs/TECHNICAL_SPEC.en.md`
- Chinese Data Model: `docs/DATA_MODEL.zh.md`
- English Data Model: `docs/DATA_MODEL.en.md`
- Chinese Roadmap: `docs/IMPLEMENTATION_ROADMAP.zh.md`
- English Roadmap: `docs/IMPLEMENTATION_ROADMAP.en.md`

## Local Development

### One-command local trial

```bash
./scripts/start-local.sh
```

Open:

```text
http://127.0.0.1:3000
```

### Backend

```bash
cd backend
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

Search job API:

```text
POST http://localhost:8000/api/search-jobs
GET  http://localhost:8000/api/search-jobs/{job_id}
GET  http://localhost:8000/api/search-jobs/{job_id}/raw-listings
GET  http://localhost:8000/api/search-jobs/{job_id}/suppliers
```

Search jobs are persisted to SQLite by default:

```bash
SOURCEHUNTER_DB_PATH=data/sourcehunter.sqlite3
```

1688 API integration:

```bash
ELIMAPI_API_KEY=
ELIMAPI_BASE_URL=https://openapi.elim.asia/v1
```

### AI Keyword Expansion

SourceHunter supports OpenAI-compatible keyword expansion through local environment variables:

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
AI_KEYWORD_EXPANSION_ENABLED=true
```

If no API key is configured, or if the provider call fails, the backend falls back to deterministic keyword expansion. It does not fabricate supplier data.

### Playwright

The backend includes a Playwright scraping framework, a Made-in-China adapter for source-backed raw listings, and an Elimapi-backed 1688 adapter. If `ELIMAPI_API_KEY` is not configured, SourceHunter records a scrape failure instead of fabricating 1688 supplier data.

Install browser binaries only when working on real platform adapters:

```bash
cd backend
.venv/bin/python -m playwright install chromium
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## Tests

Backend:

```bash
cd backend
.venv/bin/python -m pytest -v
```

Frontend:

```bash
cd frontend
npm test
```

Frontend production build:

```bash
cd frontend
npm run build
```

## Current Build

The current build creates persistent search jobs, expands sourcing keywords, retrieves Made-in-China raw listings, retrieves 1688 listings through Elimapi when configured, deduplicates suppliers, returns Top 5 unique suppliers, scores suppliers from source-backed fields, and shows recommendation actions.
Supplier and raw listing results are cached in SQLite after the first retrieval for each search job. The UI supports CSV export and bilingual RFQ draft generation.

Known limitations:

- 1688 browser automation is not used as the primary path because it often triggers human verification. Configure `ELIMAPI_API_KEY` for reliable 1688 retrieval.
- Supplier contact extraction is only shown when reliable public data is available.
- Factory-only filtering is conservative: if factory status cannot be verified, SourceHunter returns fewer or zero results instead of guessing.
