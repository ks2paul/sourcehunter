# SourceHunter Deployment Prep Checklist

## Goal

Deploy the current locally usable build to an internal web URL while preserving SourceHunter's core rule: never fabricate suppliers, prices, contacts, or links.

## What You Need To Prepare

- A frontend URL or domain.
- A service environment that can run the Python FastAPI backend.
- An OpenAI-compatible API key for keyword expansion.
- An Elimapi API key for stable 1688 retrieval.
- GitHub repository access.

## Environment Variables

Frontend:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.example
```

Backend:

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
AI_KEYWORD_EXPANSION_ENABLED=true
ELIMAPI_API_KEY=
ELIMAPI_BASE_URL=https://openapi.elim.asia/v1
SOURCEHUNTER_DB_PATH=data/sourcehunter.sqlite3
SOURCEHUNTER_CORS_ORIGINS=https://your-frontend-domain.example
```

## Required Checks Before Launch

- Backend `/health` returns `status: ok`.
- Frontend can create a search job.
- `Made-in-China Top 5` returns suppliers or a clear failure reason.
- `1688 Top 5` returns suppliers or a clear failure reason.
- CSV export does not contain fabricated fields.
- RFQ drafts use only source-backed data already shown in the page.

## Current Recommendation

Continue local trial runs with 3-5 real products first, tune ranking quality, then move to web deployment. Once the domain or deployment account is ready, deployment configuration can begin.
