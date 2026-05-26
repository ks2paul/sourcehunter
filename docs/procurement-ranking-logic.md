# SourceHunter Procurement Ranking Logic

## 中文版

SourceHunter 的 Top 5 不是按平台搜索结果顺序展示，也不是简单展示最便宜的 5 条 listing。系统先把同一供应商的多个 listing 合并成一个唯一供应商，再用采购视角评估是否值得联系。

### 先做硬性判断

- 没有可靠供应商身份的 listing 不进入候选池。
- Factory Only 模式只保留平台可识别为 factory 的供应商。
- 同一 `shop_id`、供应商 URL 或公司名会被合并，避免重复供应商占满 Top 5。
- 不生成、不猜测任何公司名、价格、网址或联系方式。缺失就显示 unavailable。

### 评分维度

- Product Match Quality：产品标题是否符合搜索意图。
- Factory Likelihood：平台或公司信息是否支持工厂判断。
- Price Competitiveness：价格相对目标价或市场中位价是否合理。
- MOQ Suitability：MOQ 是否适合试单或用户偏好。
- Category Specialization：同一供应商是否有多个相关 listing。
- Export Readiness：是否有适合海外询盘的平台页或联系方式。
- Business Maturity：可识别经营年限时给予加分。

### 风险提示

系统会标记采购风险，而不是盲目给高分：

- Product title may not match sourcing intent.
- Price is far below market median; verify quotation.
- Price unavailable; verify quotation before shortlisting.
- MOQ unavailable; confirm minimum order quantity.
- MOQ is high for trial order.

例子：搜索 `handheld fan` 时，如果标题是 bamboo folding hand fan，虽然字面上有 fan，但实际可能是手摇折扇，不是电动手持风扇，会被标记为产品不匹配。

### 推荐等级

- A：可优先询价，适合进入第一轮联系。
- B：有潜力，但需要先确认价格、MOQ 或细节。
- C：备选供应商。
- D：不建议进入 shortlist，除非人工确认风险已经解除。

## English Version

SourceHunter does not return the first five platform listings or the five cheapest listings. It first merges multiple listings from the same supplier into one unique supplier, then evaluates each supplier from a procurement decision-making perspective.

### Hard Checks First

- Listings without reliable supplier identity are excluded.
- Factory Only keeps only suppliers identified as factories by the source platform.
- The same `shop_id`, supplier URL, or company name is merged to prevent duplicate suppliers from filling the Top 5.
- SourceHunter never fabricates company names, prices, URLs, or contact data. Missing data stays unavailable.

### Scoring Dimensions

- Product Match Quality: whether the product title matches the sourcing intent.
- Factory Likelihood: whether platform or company signals support factory status.
- Price Competitiveness: whether price is reasonable against target price or market median.
- MOQ Suitability: whether MOQ fits trial orders or the user preference.
- Category Specialization: whether the same supplier has multiple relevant listings.
- Export Readiness: whether the supplier has a usable platform page or public contact text.
- Business Maturity: years in business when available.

### Risk Flags

The system flags procurement risks instead of blindly rewarding low prices:

- Product title may not match sourcing intent.
- Price is far below market median; verify quotation.
- Price unavailable; verify quotation before shortlisting.
- MOQ unavailable; confirm minimum order quantity.
- MOQ is high for trial order.

Example: for `handheld fan`, a bamboo folding hand fan may look similar textually, but it is not an electric handheld fan. SourceHunter flags it as a product-match risk.

### Recommendation Tiers

- A: prioritize for quotation.
- B: promising, but confirm price, MOQ, or details first.
- C: backup candidate.
- D: do not shortlist until the risk is manually cleared.
