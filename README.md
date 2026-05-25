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

## Foundation Build Limitation

The first runnable build creates search jobs and expands sourcing keywords. Supplier scraping, supplier deduplication, supplier scoring, and real contact extraction are intentionally deferred to later implementation plans.
