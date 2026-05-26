# SourceHunter Deployment Runbook

## Recommended Architecture

- Frontend: Vercel or another Next.js hosting platform.
- Backend: a Docker-capable service such as Render, Railway, Fly.io, ECS, or a self-managed server.
- Data: V1 can use SQLite with persistent disk. Move to PostgreSQL when production usage grows.

## Backend Deployment

Build the Docker image:

```bash
cd backend
docker build -t sourcehunter-backend .
```

Run the image locally:

```bash
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=... \
  -e ELIMAPI_API_KEY=... \
  -e SOURCEHUNTER_CORS_ORIGINS=https://your-frontend-domain.example \
  sourcehunter-backend
```

Required backend environment variables:

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
AI_KEYWORD_EXPANSION_ENABLED=true
ELIMAPI_API_KEY=
ELIMAPI_BASE_URL=https://openapi.elim.asia/v1
SOURCEHUNTER_DB_PATH=/app/data/sourcehunter.sqlite3
SOURCEHUNTER_CORS_ORIGINS=https://your-frontend-domain.example
```

Backend health check:

```text
GET https://your-backend-domain.example/health
```

Expected response:

```json
{"status":"ok","service":"sourcehunter-api"}
```

## Frontend Deployment

Frontend build commands:

```bash
cd frontend
npm ci
npm run build
```

Required frontend environment variable:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.example
```

## Post-Launch Verification

1. Open the frontend URL.
2. Search `handheld fan` and confirm Made-in-China and 1688 return suppliers or clear failure reasons.
3. Search `台式咖啡机` and confirm the diagnostics show:
   - Made-in-China keyword: `home coffee machine`
   - 1688 keyword: `台式咖啡机`
4. Open a supplier Product link and confirm it matches the shown supplier/product.
5. Export CSV and confirm it contains no fabricated company names, prices, URLs, or contacts.

## Human Input Required

- Domain purchase or DNS configuration.
- Deployment platform authorization.
- Production environment variable entry.
- Persistent disk setup if SQLite is used.

## Notes

- Never upload `.env.local` to GitHub.
- If a platform fails, SourceHunter should return the failure reason instead of fabricating results.
- If local procurement users report poor result quality, capture the product keyword, platform diagnostics, and Top 5 screenshot before tuning keyword and ranking logic.
