# SourceHunter 开发路线图 V1.0

## 阶段 0：项目初始化

目标：

- 创建 Next.js 前端项目
- 创建 FastAPI 后端项目
- 配置本地开发环境
- 配置 Playwright
- 建立基础目录结构

交付物：

- 可启动前端
- 可启动后端
- 健康检查 API
- Playwright 可打开测试页面

## 阶段 1：搜索任务基础

目标：

- 建立 SearchJob 数据模型
- 实现创建搜索任务 API
- 实现任务状态查询 API
- 前端可以提交关键词并看到任务状态

交付物：

- `POST /api/search-jobs`
- `GET /api/search-jobs/{job_id}`
- 简单搜索输入页面

## 阶段 2：AI 关键词扩展

目标：

- 接入 OpenAI-compatible API
- 根据产品关键词生成中英文搜索词
- 支持产品图片理解
- 保存关键词扩展结果

交付物：

- KeywordExpansion 模块
- AI 输出结构化 JSON
- 前端显示搜索词

## 阶段 3：Playwright 抓取框架

目标：

- 建立可扩展的抓取 worker
- 支持平台适配器
- 记录原始 URL、错误、抓取时间
- 不生成替代数据

交付物：

- Browser session 管理
- Retry 机制
- RawListing 存储
- 抓取日志

## 阶段 4：1688 抓取

目标：

- 搜索 1688
- 提取列表页信息
- 进入详情页
- 提取供应商和产品字段

交付物：

- 1688 adapter
- RawListing 结果
- 基础字段来源记录

## 阶段 5：Made-in-China 抓取

目标：

- 搜索 Made-in-China
- 提取列表页信息
- 进入详情页或公司页
- 提取供应商和产品字段

交付物：

- Made-in-China adapter
- RawListing 结果
- 基础字段来源记录

## 阶段 6：去重引擎

目标：

- 根据公司名、URL、电话、网站、地址去重
- 输出唯一 Supplier
- 生成稳定 `supplier_id`
- 保留合并证据

交付物：

- Deduplication Engine
- DeduplicationGroup
- Top unique supplier candidates

## 阶段 7：评分和推荐

目标：

- 根据真实信号评分
- 输出推荐理由
- 输出推荐动作
- 标记置信度

交付物：

- SupplierScore
- Recommended Action
- 不确定字段标记

## 阶段 8：前端结果页

目标：

- 展示搜索结果
- 展示供应商详情
- 支持筛选和排序
- 打开原始链接

交付物：

- Results page
- Supplier detail panel
- Filters
- Stable supplier link handling

## 阶段 9：验收测试

目标：

- 使用 Handheld Fan、Pet Wipes、Picture Frame 验证
- 检查链接准确性
- 检查价格和 MOQ
- 检查去重结果
- 检查失败处理

交付物：

- 验收报告
- 已知限制清单
- V2 建议

## 风险

- 1688 可能需要登录或出现反爬限制
- 页面结构可能变化
- 联系方式可能不公开
- 部分价格可能只显示区间
- Made-in-China 的工厂信息可能需要进一步验证

## 风险处理原则

- 抓不到就标记 unavailable
- 不绕过平台安全限制
- 不编造数据
- 不把 AI 推断当事实
- 优先保留原始来源

