# SourceHunter 产品需求文档 V1.0

## 1. 产品定位

SourceHunter 是一个面向 Amazon 卖家和采购团队的 AI 供应商发现与采购决策平台。

它不是产品搜索引擎，而是供应商决策系统。系统的核心目标是帮助采购团队更快、更准地找到真实、独立、可联系、适合开发的供应商。

## 2. 背景

公司已经拥有 AI Opportunity Radar，用于发现有潜力的产品机会。产品机会被发现之后，采购团队仍然需要在 1688、Made-in-China 等平台上手动寻找供应商。

当前流程存在几个问题：

- 搜索效率低
- 搜索词依赖个人经验
- 重复供应商难以识别
- 平台列表不等于真实供应商
- 贸易商和工厂混杂
- 价格、MOQ、联系方式提取不稳定

SourceHunter 的目标是把供应商发现流程标准化、自动化，并提高决策质量。

## 3. 核心用户

- Amazon 产品开发团队
- 采购团队
- 私标品牌运营团队
- 需要快速验证供应链可行性的业务负责人

## 4. V1 使用流程

1. AI Opportunity Radar 发现产品机会。
2. 用户把产品信息输入 SourceHunter。
3. AI 扩展英文和中文采购关键词。
4. 系统通过浏览器自动化搜索 1688 和 Made-in-China。
5. 系统提取供应商、产品、价格、MOQ、联系方式等公开信息。
6. 系统进行供应商去重。
7. 系统评分并返回 Top 5 独立供应商。
8. 用户查看推荐理由并打开原始供应商链接。

## 5. 输入

### 必填

- Product keyword

### 选填

- Product image
- Amazon listing URL
- Competitor image
- Target price
- MOQ preference
- Supplier preference

Supplier preference 支持：

- Factory Only
- Factory Preferred
- Any Supplier

## 6. 图片输入规则

图片不用于直接以图搜图。

图片用于 AI 理解产品，包括：

- 产品类别
- 产品别名
- 中英文采购术语
- 结构和功能特点
- 常见变体

AI 从图片中得到的信息只能用于改善搜索词和产品匹配判断，不能生成虚假的供应商、价格或联系方式。

## 7. 输出

每个供应商输出以下信息。

### 基本信息

- Company Name
- Platform
- Supplier Type
- Location
- Years in Business

### 产品信息

- Product Name
- Product Price
- MOQ
- Product URL

### 联系信息

只显示公开可获取的信息：

- Website
- Phone
- Email
- WhatsApp
- WeChat

如果没有可靠数据，显示：

- Price Unavailable
- Contact Unavailable
- Supplier Type Unknown

### AI 评估

- Supplier Score
- Recommendation Reasons
- Recommended Action

## 8. 供应商评分维度

供应商评分基于以下维度：

- Category Specialization
- Factory Likelihood
- Price Competitiveness
- MOQ Suitability
- Export Readiness
- Business Maturity
- Product Match Quality

评分必须基于已抓取或可推断的真实信号。无法判断时应降低置信度，而不是补充虚假信息。

## 9. 去重要求

去重是 V1 必须功能。

多个产品 listing 可能来自同一个供应商。系统最终输出必须是独立供应商，而不是独立 listing。

去重信号包括：

- 公司名称相似度
- 地址相同或高度相似
- 电话相同
- 网站相同
- 店铺链接相同
- 产品图片相同或高度相似
- 描述文本相似

系统必须为每个唯一供应商生成不可变 `supplier_id`。前端打开链接时必须使用 `supplier_id`，不能使用数组 index。

## 10. 数据准确性规则

数据可靠性高于 UI 表现。

严格禁止：

- 生成虚假价格
- 生成虚假网站
- 使用 placeholder URL
- 模拟供应商联系方式
- 生成不存在的公司名称
- 把 AI 猜测当成事实显示

如果可靠数据不足，系统应返回更少结果，而不是补齐 5 个假结果。

## 11. V1 支持数据源

Phase 1：

- 1688.com
- Made-in-China.com

未来版本：

- Alibaba.com
- GlobalSources.com

## 12. 筛选和排序

V1 支持：

- Factory Only
- Lowest Price
- Lowest MOQ
- Highest Score
- Export Ready
- Amazon Private Label Friendly

## 13. MVP 成功标准

V1 成功不以视觉效果衡量，而以以下结果衡量：

- 输入产品关键词后可获得真实供应商结果
- 输出 Top 5 unique suppliers，而不是 Top 5 listings
- 供应商链接稳定且准确
- 价格和 MOQ 不被编造
- 联系信息缺失时明确显示 unavailable
- 系统能解释推荐理由
- 系统能进行基础去重
- 搜索失败时能返回清晰错误信息

## 14. 非目标

V1 不优先做：

- 复杂仪表盘
- 图表分析
- Fancy animation
- CRM
- 自动联系供应商
- 订单管理
- 供应商付款或合同管理

