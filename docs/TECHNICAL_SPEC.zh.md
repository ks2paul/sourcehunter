# SourceHunter 技术规格 V1.0

## 1. 技术目标

SourceHunter V1 的技术目标是建立一个生产导向的供应商发现系统。系统必须优先保证数据真实性、链接准确性和可追溯性。

## 2. 推荐技术栈

### 前端

- Next.js
- React
- Tailwind CSS

### 后端

- Python
- FastAPI
- Playwright

### AI Layer

- OpenAI-compatible API
- 支持 GPT-5.5、Claude Sonnet、DeepSeek V4 或同类模型

### 数据存储

V1 可先使用 PostgreSQL。开发早期也可以使用 SQLite，但生产版本建议 PostgreSQL。

## 3. 系统模块

### Frontend App

职责：

- 提交搜索请求
- 展示搜索状态
- 展示供应商结果
- 提供筛选和排序
- 打开原始供应商链接

前端不得自行生成供应商数据，不得通过数组 index 打开供应商详情。

### Backend API

职责：

- 接收搜索请求
- 调用 AI 关键词扩展
- 创建搜索任务
- 调度抓取流程
- 聚合结果
- 去重
- 评分
- 返回结构化结果

### Scraping Workers

职责：

- 使用 Playwright 访问平台
- 执行搜索
- 等待页面动态加载
- 抽取列表页和详情页信息
- 记录来源 URL、抓取时间、失败原因

### AI Service

职责：

- 关键词扩展
- 图片理解
- 产品匹配判断
- 供应商评分解释
- 推荐动作生成

AI Service 不允许生成事实型供应商字段。

### Deduplication Engine

职责：

- 计算供应商相似度
- 合并同一供应商的多个 listing
- 生成稳定 `supplier_id`
- 保留所有来源证据

### Scoring Engine

职责：

- 根据提取信号计算分数
- 输出分项评分
- 输出推荐理由
- 标记低置信度字段

## 4. 数据流程

1. 用户提交产品关键词和可选信息。
2. 后端创建 `search_job`。
3. AI Service 生成中英文关键词。
4. Scraping Workers 分别搜索 1688 和 Made-in-China。
5. 系统提取 listing、产品详情、供应商信息。
6. Deduplication Engine 合并重复供应商。
7. Scoring Engine 评分。
8. 后端返回最多 5 个唯一供应商。
9. 前端按 `supplier_id` 展示和打开详情。

## 5. 抓取要求

必须使用浏览器自动化作为主要方式。

要求：

- 支持 JavaScript 渲染页面
- 支持 lazy loading
- 支持页面等待和重试
- 保留页面 URL
- 对每个字段记录来源
- 抓取失败不能生成替代数据

## 6. 错误处理

系统必须区分以下错误：

- 平台无法访问
- 页面结构变化
- 搜索无结果
- 字段无法提取
- AI 服务失败
- 去重失败
- 部分供应商数据缺失

如果某个平台失败，另一个平台成功，系统应返回部分结果并标记失败来源。

## 7. 数据准确性约束

所有事实字段必须有来源。

事实字段包括：

- Company Name
- Product Price
- MOQ
- Website
- Phone
- Email
- Location
- Years in Business
- Supplier Type

AI 可以对 Supplier Type 做判断，但必须标记为推断字段，例如：

- `supplier_type`: "Factory Likely"
- `supplier_type_confidence`: 0.72
- `supplier_type_evidence`: ["company profile contains manufacturing terms", "product catalog is category-focused"]

## 8. API 草案

### Create Search Job

`POST /api/search-jobs`

请求：

```json
{
  "product_keyword": "handheld fan",
  "target_price": 3.5,
  "moq_preference": 500,
  "supplier_preference": "Factory Preferred",
  "product_image_id": null
}
```

响应：

```json
{
  "job_id": "job_01H...",
  "status": "queued"
}
```

### Get Search Job

`GET /api/search-jobs/{job_id}`

响应：

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

响应：

```json
{
  "job_id": "job_01H...",
  "suppliers": []
}
```

### Get Supplier Detail

`GET /api/suppliers/{supplier_id}`

响应包含供应商详情、来源 URLs、评分和推荐动作。

## 9. 开发优先级

1. 后端数据模型
2. 搜索任务 API
3. Playwright 抓取框架
4. 1688 抓取
5. Made-in-China 抓取
6. 去重引擎
7. 评分引擎
8. 前端结果页
9. 验收测试

