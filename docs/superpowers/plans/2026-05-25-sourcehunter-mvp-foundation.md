# SourceHunter MVP Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable SourceHunter foundation: FastAPI backend, Next.js frontend, search job lifecycle, deterministic keyword expansion, and a simple UI that proves the product flow works before real supplier scraping is added.

**Architecture:** Use a monorepo with `backend/` for FastAPI and `frontend/` for Next.js. The backend owns all sourcing logic, IDs, validation, and future scraping boundaries; the frontend only submits requests and displays API data. V1 foundation uses in-memory storage and a deterministic keyword expansion service so the app works without fabricating supplier data or requiring platform scraping on day one.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, pytest, Next.js, React, TypeScript, Tailwind CSS, Vitest.

---

## Scope

This plan implements Roadmap Phases 0, 1, and the non-AI fallback portion of Phase 2.

Included:

- Backend app structure
- Health check API
- Search job create API
- Search job status API
- Keyword expansion service with deterministic terms for initial validation
- Frontend app structure
- Search input page
- Job status display
- Keyword expansion display
- Tests for backend core behavior

Not included:

- 1688 scraping
- Made-in-China scraping
- Playwright platform adapters
- Real OpenAI-compatible API calls
- Supplier scoring
- Supplier deduplication
- Database persistence

Those items should be implemented in follow-up plans after this foundation runs locally.

## File Structure

Create:

- `backend/pyproject.toml` - backend dependencies and pytest config
- `backend/app/__init__.py` - package marker
- `backend/app/main.py` - FastAPI app and router registration
- `backend/app/models.py` - Pydantic request and response models
- `backend/app/storage.py` - in-memory search job repository
- `backend/app/keyword_expansion.py` - deterministic keyword expansion service
- `backend/app/routes/__init__.py` - route package marker
- `backend/app/routes/health.py` - health check route
- `backend/app/routes/search_jobs.py` - search job routes
- `backend/tests/test_health.py` - health route tests
- `backend/tests/test_search_jobs.py` - search job API tests
- `frontend/package.json` - frontend scripts and dependencies
- `frontend/next.config.ts` - Next.js config
- `frontend/tsconfig.json` - TypeScript config
- `frontend/postcss.config.mjs` - PostCSS config
- `frontend/tailwind.config.ts` - Tailwind config
- `frontend/app/globals.css` - global styles
- `frontend/app/layout.tsx` - app shell
- `frontend/app/page.tsx` - SourceHunter search UI
- `frontend/lib/api.ts` - backend API client
- `frontend/lib/types.ts` - shared frontend types
- `frontend/tests/basic.test.ts` - basic frontend test
- `frontend/vitest.config.ts` - Vitest config
- `.env.example` - documented local environment variables

Modify:

- `README.md` - add local development instructions
- `.gitignore` - add local database and coverage outputs if missing

---

## Task 1: Backend Project Skeleton

**Files:**

- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/routes/__init__.py`
- Create: `backend/app/routes/health.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing health API test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sourcehunter-api"}
```

- [ ] **Step 2: Add backend dependency config**

Create `backend/pyproject.toml`:

```toml
[project]
name = "sourcehunter-backend"
version = "0.1.0"
description = "FastAPI backend for SourceHunter supplier discovery"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "pydantic>=2.8.0",
    "uvicorn[standard]>=0.30.0",
]

[project.optional-dependencies]
dev = [
    "httpx>=0.27.0",
    "pytest>=8.2.0",
    "pytest-cov>=5.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 3: Create the FastAPI app package**

Create `backend/app/__init__.py`:

```python
"""SourceHunter backend package."""
```

Create `backend/app/routes/__init__.py`:

```python
"""API route modules."""
```

Create `backend/app/routes/health.py`:

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "sourcehunter-api"}
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router

app = FastAPI(title="SourceHunter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
```

- [ ] **Step 4: Run the backend health test**

Run:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest tests/test_health.py -v
```

Expected:

```text
tests/test_health.py::test_health_check_returns_ok PASSED
```

- [ ] **Step 5: Commit backend skeleton**

Run:

```bash
git add backend/pyproject.toml backend/app backend/tests/test_health.py
git commit -m "feat: add backend API skeleton"
```

---

## Task 2: Search Job Models and Storage

**Files:**

- Create: `backend/app/models.py`
- Create: `backend/app/storage.py`
- Create: `backend/tests/test_search_jobs.py`

- [ ] **Step 1: Write model and storage tests**

Create `backend/tests/test_search_jobs.py`:

```python
from app.models import SearchJobCreate, SupplierPreference
from app.storage import SearchJobRepository


def test_search_job_repository_creates_queued_job():
    repository = SearchJobRepository()
    request = SearchJobCreate(
        product_keyword="handheld fan",
        target_price=3.5,
        moq_preference=500,
        supplier_preference=SupplierPreference.FACTORY_PREFERRED,
        product_image_id=None,
    )

    job = repository.create(request)

    assert job.job_id.startswith("job_")
    assert job.status == "completed"
    assert job.product_keyword == "handheld fan"
    assert job.keyword_expansion.english_keywords[0] == "handheld fan"
    assert "手持风扇" in job.keyword_expansion.chinese_keywords


def test_search_job_repository_returns_none_for_missing_job():
    repository = SearchJobRepository()

    assert repository.get("job_missing") is None
```

- [ ] **Step 2: Create Pydantic models**

Create `backend/app/models.py`:

```python
from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class SupplierPreference(StrEnum):
    FACTORY_ONLY = "Factory Only"
    FACTORY_PREFERRED = "Factory Preferred"
    ANY_SUPPLIER = "Any Supplier"


class SearchJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchJobCreate(BaseModel):
    product_keyword: str = Field(min_length=1, max_length=120)
    target_price: float | None = Field(default=None, gt=0)
    moq_preference: int | None = Field(default=None, gt=0)
    supplier_preference: SupplierPreference = SupplierPreference.FACTORY_PREFERRED
    product_image_id: str | None = None


class KeywordExpansion(BaseModel):
    english_keywords: list[str]
    chinese_keywords: list[str]
    variation_keywords: list[str]
    confidence: float = Field(ge=0, le=1)
    source: Literal["deterministic_v1"]


class SearchProgress(BaseModel):
    stage: str
    message: str


class SearchJob(BaseModel):
    job_id: str
    product_keyword: str
    target_price: float | None
    moq_preference: int | None
    supplier_preference: SupplierPreference
    status: SearchJobStatus
    progress: SearchProgress
    keyword_expansion: KeywordExpansion
    created_at: datetime
    updated_at: datetime
    error_summary: str | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
```

- [ ] **Step 3: Create keyword expansion service**

Create `backend/app/keyword_expansion.py`:

```python
from app.models import KeywordExpansion

KNOWN_EXPANSIONS = {
    "handheld fan": KeywordExpansion(
        english_keywords=[
            "handheld fan",
            "mini fan",
            "portable fan",
            "rechargeable fan",
            "cooling fan",
        ],
        chinese_keywords=[
            "手持风扇",
            "便携风扇",
            "充电风扇",
            "小风扇",
            "折叠风扇",
        ],
        variation_keywords=["usb fan", "desk fan", "travel fan"],
        confidence=0.86,
        source="deterministic_v1",
    ),
    "pet wipes": KeywordExpansion(
        english_keywords=[
            "pet wipes",
            "dog wipes",
            "cat wipes",
            "pet cleaning wipes",
            "deodorizing pet wipes",
        ],
        chinese_keywords=[
            "宠物湿巾",
            "狗狗湿巾",
            "猫咪湿巾",
            "宠物清洁湿巾",
            "除臭宠物湿巾",
        ],
        variation_keywords=["unscented pet wipes", "biodegradable pet wipes"],
        confidence=0.84,
        source="deterministic_v1",
    ),
    "picture frame": KeywordExpansion(
        english_keywords=[
            "picture frame",
            "photo frame",
            "wall frame",
            "tabletop frame",
            "wood picture frame",
        ],
        chinese_keywords=[
            "相框",
            "照片框",
            "画框",
            "木质相框",
            "桌面相框",
        ],
        variation_keywords=["gallery frame", "poster frame", "certificate frame"],
        confidence=0.88,
        source="deterministic_v1",
    ),
}


def expand_keywords(product_keyword: str) -> KeywordExpansion:
    normalized = product_keyword.strip().lower()
    if normalized in KNOWN_EXPANSIONS:
        return KNOWN_EXPANSIONS[normalized]

    return KeywordExpansion(
        english_keywords=[product_keyword.strip()],
        chinese_keywords=[],
        variation_keywords=[],
        confidence=0.35,
        source="deterministic_v1",
    )
```

- [ ] **Step 4: Create in-memory repository**

Create `backend/app/storage.py`:

```python
from uuid import uuid4

from app.keyword_expansion import expand_keywords
from app.models import SearchJob, SearchJobCreate, SearchJobStatus, SearchProgress, utc_now


class SearchJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, SearchJob] = {}

    def create(self, request: SearchJobCreate) -> SearchJob:
        now = utc_now()
        job_id = f"job_{uuid4().hex}"
        keyword_expansion = expand_keywords(request.product_keyword)
        job = SearchJob(
            job_id=job_id,
            product_keyword=request.product_keyword.strip(),
            target_price=request.target_price,
            moq_preference=request.moq_preference,
            supplier_preference=request.supplier_preference,
            status=SearchJobStatus.COMPLETED,
            progress=SearchProgress(
                stage="keyword_expansion_completed",
                message="Keyword expansion completed. Supplier scraping is not enabled in the foundation build.",
            ),
            keyword_expansion=keyword_expansion,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> SearchJob | None:
        return self._jobs.get(job_id)
```

- [ ] **Step 5: Run model and storage tests**

Run:

```bash
cd backend
.venv/bin/python -m pytest tests/test_search_jobs.py -v
```

Expected:

```text
tests/test_search_jobs.py::test_search_job_repository_creates_queued_job PASSED
tests/test_search_jobs.py::test_search_job_repository_returns_none_for_missing_job PASSED
```

- [ ] **Step 6: Commit search job models**

Run:

```bash
git add backend/app/models.py backend/app/storage.py backend/app/keyword_expansion.py backend/tests/test_search_jobs.py
git commit -m "feat: add search job domain model"
```

---

## Task 3: Search Job API

**Files:**

- Modify: `backend/app/main.py`
- Create: `backend/app/routes/search_jobs.py`
- Modify: `backend/tests/test_search_jobs.py`

- [ ] **Step 1: Add API route tests**

Replace `backend/tests/test_search_jobs.py` with:

```python
from fastapi.testclient import TestClient

from app.main import app
from app.models import SearchJobCreate, SupplierPreference
from app.storage import SearchJobRepository


def test_search_job_repository_creates_queued_job():
    repository = SearchJobRepository()
    request = SearchJobCreate(
        product_keyword="handheld fan",
        target_price=3.5,
        moq_preference=500,
        supplier_preference=SupplierPreference.FACTORY_PREFERRED,
        product_image_id=None,
    )

    job = repository.create(request)

    assert job.job_id.startswith("job_")
    assert job.status == "completed"
    assert job.product_keyword == "handheld fan"
    assert job.keyword_expansion.english_keywords[0] == "handheld fan"
    assert "手持风扇" in job.keyword_expansion.chinese_keywords


def test_search_job_repository_returns_none_for_missing_job():
    repository = SearchJobRepository()

    assert repository.get("job_missing") is None


def test_create_search_job_api_returns_job():
    client = TestClient(app)

    response = client.post(
        "/api/search-jobs",
        json={
            "product_keyword": "handheld fan",
            "target_price": 3.5,
            "moq_preference": 500,
            "supplier_preference": "Factory Preferred",
            "product_image_id": None,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["job_id"].startswith("job_")
    assert payload["status"] == "completed"
    assert payload["keyword_expansion"]["english_keywords"][0] == "handheld fan"


def test_get_search_job_api_returns_created_job():
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "picture frame"}).json()

    response = client.get(f"/api/search-jobs/{created['job_id']}")

    assert response.status_code == 200
    assert response.json()["job_id"] == created["job_id"]
    assert "相框" in response.json()["keyword_expansion"]["chinese_keywords"]


def test_get_search_job_api_returns_404_for_missing_job():
    client = TestClient(app)

    response = client.get("/api/search-jobs/job_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Search job not found"
```

- [ ] **Step 2: Create search job routes**

Create `backend/app/routes/search_jobs.py`:

```python
from fastapi import APIRouter, HTTPException, status

from app.models import SearchJob, SearchJobCreate
from app.storage import SearchJobRepository

router = APIRouter(prefix="/api/search-jobs", tags=["search-jobs"])
repository = SearchJobRepository()


@router.post("", response_model=SearchJob, status_code=status.HTTP_201_CREATED)
def create_search_job(request: SearchJobCreate) -> SearchJob:
    return repository.create(request)


@router.get("/{job_id}", response_model=SearchJob)
def get_search_job(job_id: str) -> SearchJob:
    job = repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")
    return job
```

- [ ] **Step 3: Register the search job router**

Replace `backend/app/main.py` with:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router
from app.routes.search_jobs import router as search_jobs_router

app = FastAPI(title="SourceHunter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(search_jobs_router)
```

- [ ] **Step 4: Run backend tests**

Run:

```bash
cd backend
.venv/bin/python -m pytest -v
```

Expected:

```text
5 passed
```

- [ ] **Step 5: Commit search job API**

Run:

```bash
git add backend/app/main.py backend/app/routes/search_jobs.py backend/tests/test_search_jobs.py
git commit -m "feat: add search job API"
```

---

## Task 4: Frontend Project Skeleton

**Files:**

- Create: `frontend/package.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/tests/basic.test.ts`
- Create: `frontend/vitest.config.ts`

- [ ] **Step 1: Create frontend package config**

Create `frontend/package.json`:

```json
{
  "name": "sourcehunter-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "test": "vitest run"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.7.0",
    "vitest": "^2.1.0"
  }
}
```

- [ ] **Step 2: Add Next.js and TypeScript config**

Create `frontend/next.config.ts`:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Add Tailwind config and global styles**

Create `frontend/postcss.config.mjs`:

```javascript
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;
```

Create `frontend/tailwind.config.ts`:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
```

Create `frontend/app/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color-scheme: light;
}

body {
  margin: 0;
  background: #f7f8fa;
  color: #17202a;
}

button,
input,
select {
  font: inherit;
}
```

- [ ] **Step 4: Add app layout**

Create `frontend/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SourceHunter",
  description: "Supplier discovery and procurement intelligence",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 5: Add Vitest smoke test**

Create `frontend/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
  },
});
```

Create `frontend/tests/basic.test.ts`:

```typescript
import { describe, expect, it } from "vitest";

describe("frontend test setup", () => {
  it("runs vitest", () => {
    expect("SourceHunter").toContain("Hunter");
  });
});
```

- [ ] **Step 6: Install and test frontend**

Run:

```bash
cd frontend
npm install
npm test
```

Expected:

```text
1 passed
```

- [ ] **Step 7: Commit frontend skeleton**

Run:

```bash
git add frontend
git commit -m "feat: add frontend app skeleton"
```

---

## Task 5: Frontend API Client and Search UI

**Files:**

- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: Add frontend API types**

Create `frontend/lib/types.ts`:

```typescript
export type SupplierPreference = "Factory Only" | "Factory Preferred" | "Any Supplier";

export type KeywordExpansion = {
  english_keywords: string[];
  chinese_keywords: string[];
  variation_keywords: string[];
  confidence: number;
  source: "deterministic_v1";
};

export type SearchJob = {
  job_id: string;
  product_keyword: string;
  target_price: number | null;
  moq_preference: number | null;
  supplier_preference: SupplierPreference;
  status: "queued" | "running" | "partially_completed" | "completed" | "failed";
  progress: {
    stage: string;
    message: string;
  };
  keyword_expansion: KeywordExpansion;
  created_at: string;
  updated_at: string;
  error_summary: string | null;
};

export type CreateSearchJobPayload = {
  product_keyword: string;
  target_price: number | null;
  moq_preference: number | null;
  supplier_preference: SupplierPreference;
  product_image_id: string | null;
};
```

- [ ] **Step 2: Add API client**

Create `frontend/lib/api.ts`:

```typescript
import type { CreateSearchJobPayload, SearchJob } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function createSearchJob(payload: CreateSearchJobPayload): Promise<SearchJob> {
  const response = await fetch(`${API_BASE_URL}/api/search-jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Search request failed with status ${response.status}`);
  }

  return response.json();
}
```

- [ ] **Step 3: Add SourceHunter search page**

Create `frontend/app/page.tsx`:

```tsx
"use client";

import { FormEvent, useState } from "react";

import { createSearchJob } from "@/lib/api";
import type { SearchJob, SupplierPreference } from "@/lib/types";

const supplierPreferences: SupplierPreference[] = ["Factory Preferred", "Factory Only", "Any Supplier"];

export default function HomePage() {
  const [productKeyword, setProductKeyword] = useState("handheld fan");
  const [targetPrice, setTargetPrice] = useState("");
  const [moqPreference, setMoqPreference] = useState("");
  const [supplierPreference, setSupplierPreference] = useState<SupplierPreference>("Factory Preferred");
  const [job, setJob] = useState<SearchJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setJob(null);

    try {
      const createdJob = await createSearchJob({
        product_keyword: productKeyword,
        target_price: targetPrice ? Number(targetPrice) : null,
        moq_preference: moqPreference ? Number(moqPreference) : null,
        supplier_preference: supplierPreference,
        product_image_id: null,
      });
      setJob(createdJob);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Search request failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-950">SourceHunter</h1>
            <p className="text-sm text-slate-600">Supplier discovery foundation build</p>
          </div>
          <span className="rounded border border-amber-300 bg-amber-50 px-3 py-1 text-sm text-amber-900">
            Scraping disabled in foundation build
          </span>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">
        <form onSubmit={handleSubmit} className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-950">Search input</h2>

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="product_keyword">
            Product keyword
          </label>
          <input
            id="product_keyword"
            value={productKeyword}
            onChange={(event) => setProductKeyword(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            required
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="target_price">
            Target price
          </label>
          <input
            id="target_price"
            value={targetPrice}
            onChange={(event) => setTargetPrice(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            inputMode="decimal"
            placeholder="Optional"
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="moq_preference">
            MOQ preference
          </label>
          <input
            id="moq_preference"
            value={moqPreference}
            onChange={(event) => setMoqPreference(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            inputMode="numeric"
            placeholder="Optional"
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="supplier_preference">
            Supplier preference
          </label>
          <select
            id="supplier_preference"
            value={supplierPreference}
            onChange={(event) => setSupplierPreference(event.target.value as SupplierPreference)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          >
            {supplierPreferences.map((preference) => (
              <option key={preference} value={preference}>
                {preference}
              </option>
            ))}
          </select>

          <button
            type="submit"
            className="mt-5 w-full rounded bg-slate-950 px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isLoading}
          >
            {isLoading ? "Creating job..." : "Create search job"}
          </button>
        </form>

        <section className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-950">Result</h2>

          {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}

          {!job && !error ? (
            <p className="mt-4 text-sm text-slate-600">Create a search job to view keyword expansion.</p>
          ) : null}

          {job ? (
            <div className="mt-4 space-y-5">
              <div className="grid gap-3 sm:grid-cols-2">
                <Info label="Job ID" value={job.job_id} />
                <Info label="Status" value={job.status} />
                <Info label="Stage" value={job.progress.stage} />
                <Info label="Confidence" value={`${Math.round(job.keyword_expansion.confidence * 100)}%`} />
              </div>

              <p className="rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                {job.progress.message}
              </p>

              <KeywordList title="English keywords" items={job.keyword_expansion.english_keywords} />
              <KeywordList title="Chinese keywords" items={job.keyword_expansion.chinese_keywords} />
              <KeywordList title="Variation keywords" items={job.keyword_expansion.variation_keywords} />
            </div>
          ) : null}
        </section>
      </section>
    </main>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-slate-200 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm font-medium text-slate-950">{value}</div>
    </div>
  );
}

function KeywordList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      {items.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {items.map((item) => (
            <span key={item} className="rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700">
              {item}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-500">Unavailable in deterministic foundation build.</p>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run frontend tests**

Run:

```bash
cd frontend
npm test
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit frontend search UI**

Run:

```bash
git add frontend/app/page.tsx frontend/lib
git commit -m "feat: add search job UI"
```

---

## Task 6: Local Development Documentation

**Files:**

- Create: `.env.example`
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 1: Add environment example**

Create `.env.example`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 2: Update `.gitignore`**

Ensure `.gitignore` contains:

```gitignore
# Coverage
.coverage
htmlcov/
coverage/

# Local data
*.sqlite3
*.db
```

- [ ] **Step 3: Replace README with development guide**

Replace `README.md` with:

```markdown
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
python3 -m venv .venv
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

## Foundation Build Limitation

The first runnable build creates search jobs and expands sourcing keywords. Supplier scraping, supplier deduplication, supplier scoring, and real contact extraction are intentionally deferred to later implementation plans.
```

- [ ] **Step 4: Commit documentation**

Run:

```bash
git add .env.example .gitignore README.md docs/superpowers/plans/2026-05-25-sourcehunter-mvp-foundation.md
git commit -m "docs: add MVP foundation implementation plan"
```

---

## Task 7: Foundation Verification

**Files:**

- No new files

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd backend
.venv/bin/python -m pytest -v
```

Expected:

```text
tests/test_health.py::test_health_check_returns_ok PASSED
tests/test_search_jobs.py::test_search_job_repository_creates_queued_job PASSED
tests/test_search_jobs.py::test_search_job_repository_returns_none_for_missing_job PASSED
tests/test_search_jobs.py::test_create_search_job_api_returns_job PASSED
tests/test_search_jobs.py::test_get_search_job_api_returns_created_job PASSED
tests/test_search_jobs.py::test_get_search_job_api_returns_404_for_missing_job PASSED
```

- [ ] **Step 2: Run frontend tests**

Run:

```bash
cd frontend
npm test
```

Expected:

```text
1 passed
```

- [ ] **Step 3: Start backend**

Run:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload
```

Expected:

```text
Uvicorn running on http://127.0.0.1:8000
```

- [ ] **Step 4: Start frontend in a separate terminal**

Run:

```bash
cd frontend
npm run dev
```

Expected:

```text
Local: http://localhost:3000
```

- [ ] **Step 5: Browser acceptance check**

Open:

```text
http://localhost:3000
```

Submit:

```text
Product keyword: handheld fan
Target price: 3.5
MOQ preference: 500
Supplier preference: Factory Preferred
```

Expected visible result:

```text
Status: completed
Stage: keyword_expansion_completed
English keywords include handheld fan, mini fan, portable fan
Chinese keywords include 手持风扇, 便携风扇, 充电风扇
```

- [ ] **Step 6: Push to GitHub**

Run:

```bash
git status --short --branch
git push
```

Expected:

```text
Everything up-to-date
```

or a successful push showing new commits on `origin/main`.

---

## Self-Review

Spec coverage:

- Product input is covered by Task 5.
- Search job API is covered by Tasks 2 and 3.
- Keyword expansion is covered by Task 2.
- Frontend status and keyword display are covered by Task 5.
- Data accuracy principle is preserved because the foundation build displays no supplier data and clearly states that scraping is disabled.

Intentional gaps:

- Real supplier retrieval is deferred because it requires platform-specific scraping adapters and anti-bot risk handling.
- Supplier deduplication is deferred until raw listing data exists.
- Supplier scoring is deferred until supplier evidence exists.
- OpenAI-compatible API integration is deferred until the deterministic foundation build is stable.

Placeholder scan:

- The plan contains no unresolved placeholder steps.
- Each implementation step includes exact file paths and code.

Type consistency:

- Backend status values match frontend status union.
- `supplier_preference` values match backend enum and frontend union.
- `keyword_expansion` fields match backend and frontend models.
