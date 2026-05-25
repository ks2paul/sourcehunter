# SourceHunter 数据模型 V1.0

## 1. 核心原则

数据模型必须支持可追溯、可去重、不可伪造。

每个事实字段都应尽可能关联来源 URL、提取时间和置信度。

## 2. SearchJob

表示一次搜索任务。

字段：

- `job_id`
- `product_keyword`
- `target_price`
- `moq_preference`
- `supplier_preference`
- `status`
- `created_at`
- `updated_at`
- `error_summary`

状态：

- `queued`
- `running`
- `partially_completed`
- `completed`
- `failed`

## 3. KeywordExpansion

表示 AI 生成的采购搜索词。

字段：

- `keyword_expansion_id`
- `job_id`
- `source`
- `english_keywords`
- `chinese_keywords`
- `variation_keywords`
- `confidence`
- `created_at`

`source` 可为：

- `text_input`
- `image_understanding`
- `amazon_url`

## 4. RawListing

表示从平台抓取到的原始 listing。

字段：

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

RawListing 不应被前端直接当作最终供应商结果展示。

## 5. Supplier

表示去重后的唯一供应商。

字段：

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

`supplier_id` 必须稳定，不可依赖数组 index。

推荐生成方式：

- company name normalized
- platform supplier URL
- website
- phone

组合后生成 hash。

## 6. SupplierEvidence

记录供应商字段的来源证据。

字段：

- `evidence_id`
- `supplier_id`
- `field_name`
- `field_value`
- `source_url`
- `source_platform`
- `confidence`
- `extracted_at`

## 7. SupplierProduct

表示供应商下的相关产品。

字段：

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

表示供应商评分结果。

字段：

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

表示去重过程。

字段：

- `dedupe_group_id`
- `job_id`
- `supplier_id`
- `merged_listing_ids`
- `dedupe_signals`
- `dedupe_confidence`
- `created_at`

## 10. 不允许的数据状态

以下状态不得进入最终供应商结果：

- 无来源 URL 的供应商
- AI 生成的公司名
- AI 生成的价格
- Placeholder URL
- 没有 `supplier_id` 的结果
- 用列表 index 作为供应商身份

