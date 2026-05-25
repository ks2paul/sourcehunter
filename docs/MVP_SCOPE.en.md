# SourceHunter MVP Scope V1.0

## 1. MVP Principles

The core principle of V1 is accurate supplier retrieval.

Priority order:

1. Data accuracy
2. Accurate supplier links
3. Accurate price and MOQ extraction
4. Reliable supplier deduplication
5. Clear AI recommendation explanations
6. Simple usable UI

If reliable data cannot be obtained, the system should return fewer trustworthy results rather than complete but unreliable results.

## 2. Must-Have Features

### Product Input

- Product keyword input
- Optional target price
- Optional MOQ preference
- Optional supplier preference
- Optional product image upload

### AI Keyword Expansion

- English sourcing keywords
- Chinese sourcing keywords
- Product variation terms
- Low-confidence terms must not be used as primary search terms unless marked as auxiliary terms

### Platform Search

- 1688 search
- Made-in-China search
- Playwright browser automation
- Search result list extraction
- Product detail page extraction
- Supplier homepage or company page extraction

### Data Extraction

- Company name
- Platform
- Supplier URL
- Product name
- Product URL
- Price
- MOQ
- Location
- Years in business
- Publicly available contact information

### Deduplication

- Deduplication using company name, address, phone, website, and store URL
- Unique supplier output
- Immutable `supplier_id` for each supplier

### Scoring

- Overall score
- Dimension scores
- Recommendation reasons
- Recommended action

### Frontend

- Search input page
- Search progress status
- Result list
- Supplier detail view
- Filters and sorting
- Open original links

## 3. Out of MVP Scope

- Automatic platform login
- Automatic inquiry sending
- CRM management
- Batch project management
- Supplier chat history
- Purchase orders
- Payment workflow
- Contract management
- Advanced dashboards
- Multi-user permission system

## 4. Quality Requirements

- Do not display fake data
- Do not use mock suppliers as real results
- Every supplier must have a source platform and original URL
- Prices must come from page extraction
- Contact information must come from public page extraction
- Missing fields must be clearly displayed as unavailable
- Scraping failures must retain error reasons

## 5. Acceptance Criteria

Use 3 test products for validation:

- Handheld Fan
- Pet Wipes
- Picture Frame

Each test product must verify:

- Whether English and Chinese search terms are generated
- Whether target platforms can be accessed
- Whether real product listings can be extracted
- Whether detail pages can be opened
- Whether suppliers can be identified
- Whether deduplication works
- Whether up to 5 unique suppliers are returned
- Whether clicking a result opens the correct original link

