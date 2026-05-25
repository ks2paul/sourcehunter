# SourceHunter Technical Specification V1.0

## 1. Technical Goal

The technical goal of SourceHunter V1 is to build a production-oriented supplier discovery system. The system must prioritize data authenticity, link accuracy, and traceability.

## 2. Recommended Tech Stack

### Frontend

- Next.js
- React
- Tailwind CSS

### Backend

- Python
- FastAPI
- Playwright

### AI Layer

- OpenAI-compatible API
- Supports GPT-5.5, Claude Sonnet, DeepSeek V4, or comparable models

### Data Storage

V1 should use PostgreSQL for production. SQLite may be used during early development, but PostgreSQL is recommended for production.

## 3. System Modules

### Frontend App

Responsibilities:

- Submit search requests
- Display search status
- Display supplier results
- Provide filters and sorting
- Open original supplier links

The frontend must not generate supplier data and must not open supplier details using array indexes.

### Backend API

Responsibilities:

- Receive search requests
- Call AI keyword expansion
- Create search jobs
- Coordinate scraping workflows
- Aggregate results
- Deduplicate suppliers
- Score suppliers
- Return structured results

### Scraping Workers

Responsibilities:

- Use Playwright to access platforms
- Execute searches
- Wait for dynamic page rendering
- Extract list and detail page information
- Record source URLs, scrape timestamps, and failure reasons

### AI Service

Responsibilities:

- Keyword expansion
- Image understanding
- Product match judgment
- Supplier scoring explanation
- Recommended action generation

The AI Service must not generate factual supplier fields.

### Deduplication Engine

Responsibilities:

- Calculate supplier similarity
- Merge multiple listings from the same supplier
- Generate stable `supplier_id`
- Preserve all source evidence

### Scoring Engine

Responsibilities:

- Calculate scores based on extracted signals
- Output dimension scores
- Output recommendation reasons
- Mark low-confidence fields

## 4. Data Flow

1. The user submits a product keyword and optional information.
2. The backend creates a `search_job`.
3. The AI Service generates English and Chinese keywords.
4. Scraping Workers search 1688 and Made-in-China.
5. The system extracts listings, product details, and supplier information.
6. The Deduplication Engine merges duplicate suppliers.
7. The Scoring Engine scores suppliers.
8. The backend returns up to 5 unique suppliers.
9. The frontend displays and opens supplier details using `supplier_id`.

## 5. Scraping Requirements

Browser automation must be the primary scraping method.

Requirements:

- Support JavaScript-rendered pages
- Support lazy loading
- Support waits and retries
- Preserve page URLs
- Record source for each extracted field
- Never generate replacement data when scraping fails

## 6. Error Handling

The system must distinguish the following errors:

- Platform inaccessible
- Page structure changed
- No search results
- Field extraction failed
- AI service failed
- Deduplication failed
- Partial supplier data missing

If one platform fails and another succeeds, the system should return partial results and mark the failed source.

## 7. Data Accuracy Constraints

All factual fields must have a source.

Factual fields include:

- Company Name
- Product Price
- MOQ
- Website
- Phone
- Email
- Location
- Years in Business
- Supplier Type

AI may infer Supplier Type, but it must be marked as inferred, for example:

- `supplier_type`: "Factory Likely"
- `supplier_type_confidence`: 0.72
- `supplier_type_evidence`: ["company profile contains manufacturing terms", "product catalog is category-focused"]

## 8. API Draft

### Create Search Job

`POST /api/search-jobs`

Request:

```json
{
  "product_keyword": "handheld fan",
  "target_price": 3.5,
  "moq_preference": 500,
  "supplier_preference": "Factory Preferred",
  "product_image_id": null
}
```

Response:

```json
{
  "job_id": "job_01H...",
  "status": "queued"
}
```

### Get Search Job

`GET /api/search-jobs/{job_id}`

Response:

```json
{
  "job_id": "job_01H...",
  "status": "running",
  "progress": {
    "stage": "scraping_made_in_china",
    "message": "Extracting supplier detail pages"
  }
}
```

### Get Supplier Results

`GET /api/search-jobs/{job_id}/suppliers`

Response:

```json
{
  "job_id": "job_01H...",
  "suppliers": []
}
```

### Get Supplier Detail

`GET /api/suppliers/{supplier_id}`

The response includes supplier details, source URLs, scoring, and recommended actions.

## 9. Development Priority

1. Backend data model
2. Search job API
3. Playwright scraping framework
4. 1688 scraping
5. Made-in-China scraping
6. Deduplication engine
7. Scoring engine
8. Frontend result page
9. Acceptance testing

