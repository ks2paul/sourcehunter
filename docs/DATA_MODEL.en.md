# SourceHunter Data Model V1.0

## 1. Core Principles

The data model must support traceability, deduplication, and non-fabrication.

Every factual field should be associated with a source URL, extraction timestamp, and confidence whenever possible.

## 2. SearchJob

Represents one search task.

Fields:

- `job_id`
- `product_keyword`
- `target_price`
- `moq_preference`
- `supplier_preference`
- `status`
- `created_at`
- `updated_at`
- `error_summary`

Statuses:

- `queued`
- `running`
- `partially_completed`
- `completed`
- `failed`

## 3. KeywordExpansion

Represents AI-generated sourcing search terms.

Fields:

- `keyword_expansion_id`
- `job_id`
- `source`
- `english_keywords`
- `chinese_keywords`
- `variation_keywords`
- `confidence`
- `created_at`

`source` may be:

- `text_input`
- `image_understanding`
- `amazon_url`

## 4. RawListing

Represents raw listings scraped from platforms.

Fields:

- `listing_id`
- `job_id`
- `platform`
- `source_url`
- `product_url`
- `supplier_url`
- `raw_product_name`
- `raw_company_name`
- `raw_price`
- `raw_moq`
- `raw_location`
- `raw_years_in_business`
- `raw_contact_text`
- `scraped_at`
- `scrape_status`
- `scrape_error`

RawListing should not be displayed directly as final supplier results.

## 5. Supplier

Represents a deduplicated unique supplier.

Fields:

- `supplier_id`
- `canonical_company_name`
- `platforms`
- `supplier_type`
- `supplier_type_confidence`
- `location`
- `years_in_business`
- `website`
- `phone`
- `email`
- `whatsapp`
- `wechat`
- `created_at`
- `updated_at`

`supplier_id` must be stable and must not depend on array indexes.

Recommended generation inputs:

- normalized company name
- platform supplier URL
- website
- phone

Generate a hash from the combined identity signals.

## 6. SupplierEvidence

Records source evidence for supplier fields.

Fields:

- `evidence_id`
- `supplier_id`
- `field_name`
- `field_value`
- `source_url`
- `source_platform`
- `confidence`
- `extracted_at`

## 7. SupplierProduct

Represents a relevant product under a supplier.

Fields:

- `supplier_product_id`
- `supplier_id`
- `listing_id`
- `product_name`
- `product_url`
- `price`
- `price_currency`
- `moq`
- `match_score`
- `created_at`

## 8. SupplierScore

Represents supplier scoring results.

Fields:

- `supplier_score_id`
- `supplier_id`
- `job_id`
- `overall_score`
- `category_specialization_score`
- `factory_likelihood_score`
- `price_competitiveness_score`
- `moq_suitability_score`
- `export_readiness_score`
- `business_maturity_score`
- `product_match_score`
- `confidence`
- `reasons`
- `recommended_action`
- `created_at`

## 9. DeduplicationGroup

Represents the deduplication process.

Fields:

- `dedupe_group_id`
- `job_id`
- `supplier_id`
- `merged_listing_ids`
- `dedupe_signals`
- `dedupe_confidence`
- `created_at`

## 10. Disallowed Data States

The following states must not enter final supplier results:

- Supplier without source URL
- AI-generated company name
- AI-generated price
- Placeholder URL
- Result without `supplier_id`
- Supplier identity based on list index

