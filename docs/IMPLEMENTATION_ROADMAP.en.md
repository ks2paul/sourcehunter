# SourceHunter Implementation Roadmap V1.0

## Phase 0: Project Initialization

Goals:

- Create the Next.js frontend project
- Create the FastAPI backend project
- Configure local development environment
- Configure Playwright
- Establish the base folder structure

Deliverables:

- Frontend can start
- Backend can start
- Health check API
- Playwright can open a test page

## Phase 1: Search Job Foundation

Goals:

- Create the SearchJob data model
- Implement create search job API
- Implement job status API
- Frontend can submit a keyword and view job status

Deliverables:

- `POST /api/search-jobs`
- `GET /api/search-jobs/{job_id}`
- Simple search input page

## Phase 2: AI Keyword Expansion

Goals:

- Connect to an OpenAI-compatible API
- Generate English and Chinese search terms from product keyword
- Support product image understanding
- Save keyword expansion results

Deliverables:

- KeywordExpansion module
- Structured JSON AI output
- Frontend displays generated search terms

## Phase 3: Playwright Scraping Framework

Goals:

- Build an extensible scraping worker
- Support platform adapters
- Record original URL, errors, and scrape timestamps
- Never generate replacement data

Deliverables:

- Browser session management
- Retry mechanism
- RawListing storage
- Scraping logs

## Phase 4: 1688 Scraping

Goals:

- Search 1688
- Extract listing page information
- Open detail pages
- Extract supplier and product fields

Deliverables:

- 1688 adapter
- RawListing results
- Basic field source records

## Phase 5: Made-in-China Scraping

Goals:

- Search Made-in-China
- Extract listing page information
- Open detail or company pages
- Extract supplier and product fields

Deliverables:

- Made-in-China adapter
- RawListing results
- Basic field source records

## Phase 6: Deduplication Engine

Goals:

- Deduplicate by company name, URL, phone, website, and address
- Output unique Supplier records
- Generate stable `supplier_id`
- Preserve merge evidence

Deliverables:

- Deduplication Engine
- DeduplicationGroup
- Top unique supplier candidates

## Phase 7: Scoring and Recommendation

Goals:

- Score suppliers based on real signals
- Output recommendation reasons
- Output recommended actions
- Mark confidence

Deliverables:

- SupplierScore
- Recommended Action
- Uncertain field markers

## Phase 8: Frontend Results Page

Goals:

- Display search results
- Display supplier details
- Support filters and sorting
- Open original links

Deliverables:

- Results page
- Supplier detail panel
- Filters
- Stable supplier link handling

## Phase 9: Acceptance Testing

Goals:

- Validate with Handheld Fan, Pet Wipes, and Picture Frame
- Check link accuracy
- Check price and MOQ extraction
- Check deduplication results
- Check failure handling

Deliverables:

- Acceptance report
- Known limitations list
- V2 recommendations

## Risks

- 1688 may require login or trigger anti-bot restrictions
- Page structure may change
- Contact information may not be public
- Some prices may only appear as ranges
- Factory information on Made-in-China may require additional verification

## Risk Handling Principles

- Mark unavailable when data cannot be extracted
- Do not bypass platform security restrictions
- Do not fabricate data
- Do not treat AI inference as fact
- Preserve original sources first

