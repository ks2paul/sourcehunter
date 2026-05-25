# SourceHunter Product Requirements Document V1.0

## 1. Product Positioning

SourceHunter is an AI-powered supplier discovery and procurement intelligence platform for Amazon sellers and sourcing teams.

It is not a product search engine. It is a supplier decision-making system. Its core purpose is to help procurement teams find real, independent, contactable, and suitable suppliers faster and more accurately.

## 2. Background

The company already has an AI Opportunity Radar system for identifying promising product opportunities. After a product opportunity is identified, the sourcing team still needs to manually search platforms such as 1688 and Made-in-China.

The current process has several issues:

- Slow search workflow
- Search terms depend heavily on individual experience
- Duplicate suppliers are hard to detect
- Platform listings do not equal real suppliers
- Factories and trading companies are mixed together
- Price, MOQ, and contact extraction are inconsistent

SourceHunter aims to standardize and automate supplier discovery while improving sourcing decision quality.

## 3. Core Users

- Amazon product development teams
- Procurement teams
- Private label brand operators
- Business owners validating supply chain feasibility

## 4. V1 Workflow

1. AI Opportunity Radar identifies a product opportunity.
2. The user sends product information into SourceHunter.
3. AI expands English and Chinese sourcing keywords.
4. The system searches 1688 and Made-in-China using browser automation.
5. The system extracts public supplier, product, price, MOQ, and contact information.
6. The system deduplicates suppliers.
7. The system scores suppliers and returns the Top 5 independent suppliers.
8. The user reviews recommendation reasons and opens original supplier links.

## 5. Inputs

### Required

- Product keyword

### Optional

- Product image
- Amazon listing URL
- Competitor image
- Target price
- MOQ preference
- Supplier preference

Supplier preference options:

- Factory Only
- Factory Preferred
- Any Supplier

## 6. Image Input Rules

Images are not used for reverse image search in V1.

Images are used for AI understanding, including:

- Product category
- Alternative names
- English and Chinese sourcing terms
- Structure and functional features
- Common product variations

AI-derived image understanding may only improve search terms and product match judgment. It must not generate fake suppliers, prices, or contact information.

## 7. Outputs

Each supplier result includes the following information.

### Basic Information

- Company Name
- Platform
- Supplier Type
- Location
- Years in Business

### Product Information

- Product Name
- Product Price
- MOQ
- Product URL

### Contact Information

Only publicly available information may be displayed:

- Website
- Phone
- Email
- WhatsApp
- WeChat

If reliable information is unavailable, display:

- Price Unavailable
- Contact Unavailable
- Supplier Type Unknown

### AI Evaluation

- Supplier Score
- Recommendation Reasons
- Recommended Action

## 8. Supplier Scoring Dimensions

Supplier scoring is based on:

- Category Specialization
- Factory Likelihood
- Price Competitiveness
- MOQ Suitability
- Export Readiness
- Business Maturity
- Product Match Quality

Scores must be based on scraped evidence or defensible signals. When the system cannot determine something, it should reduce confidence instead of inventing information.

## 9. Deduplication Requirements

Deduplication is mandatory for V1.

Multiple product listings may belong to the same supplier. Final output must represent independent suppliers, not independent listings.

Deduplication signals include:

- Similar company name
- Same or highly similar address
- Same phone number
- Same website
- Same store URL
- Same or highly similar product images
- Similar description text

The system must generate an immutable `supplier_id` for each unique supplier. The frontend must open supplier links using `supplier_id`, not array indexes.

## 10. Data Accuracy Rules

Data reliability is more important than UI quality.

Strictly forbidden:

- Fake prices
- Fake websites
- Placeholder URLs
- Simulated supplier contacts
- Generated company names
- Displaying AI guesses as facts

If reliable data is insufficient, the system should return fewer results instead of filling the list with fake suppliers.

## 11. V1 Data Sources

Phase 1:

- 1688.com
- Made-in-China.com

Future versions:

- Alibaba.com
- GlobalSources.com

## 12. Filters and Sorting

V1 supports:

- Factory Only
- Lowest Price
- Lowest MOQ
- Highest Score
- Export Ready
- Amazon Private Label Friendly

## 13. MVP Success Criteria

V1 success is measured by operational usefulness, not visual polish:

- Real supplier results can be retrieved from a product keyword
- Output is Top 5 unique suppliers, not Top 5 listings
- Supplier links are stable and accurate
- Prices and MOQs are not fabricated
- Missing contact information is clearly marked as unavailable
- The system explains recommendation reasons
- The system performs basic deduplication
- Search failures return clear error messages

## 14. Non-Goals

V1 does not prioritize:

- Complex dashboards
- Chart analytics
- Fancy animations
- CRM
- Automatic supplier outreach
- Order management
- Supplier payment or contract management

