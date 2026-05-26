# SourceHunter 部署 Runbook

## 推荐部署结构

- 前端：Vercel 或其他 Next.js 托管平台。
- 后端：支持 Docker 的服务，例如 Render、Railway、Fly.io、ECS 或一台自管服务器。
- 数据：V1 可以继续用 SQLite 挂载持久化磁盘；生产扩大后建议迁移到 PostgreSQL。

## 后端部署

构建 Docker 镜像：

```bash
cd backend
docker build -t sourcehunter-backend .
```

本地运行镜像：

```bash
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=... \
  -e ELIMAPI_API_KEY=... \
  -e SOURCEHUNTER_CORS_ORIGINS=https://your-frontend-domain.example \
  sourcehunter-backend
```

后端必须配置：

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
AI_KEYWORD_EXPANSION_ENABLED=true
ELIMAPI_API_KEY=
ELIMAPI_BASE_URL=https://openapi.elim.asia/v1
SOURCEHUNTER_DB_PATH=/app/data/sourcehunter.sqlite3
SOURCEHUNTER_CORS_ORIGINS=https://your-frontend-domain.example
```

后端健康检查：

```text
GET https://your-backend-domain.example/health
```

预期返回：

```json
{"status":"ok","service":"sourcehunter-api"}
```

## 前端部署

前端构建命令：

```bash
cd frontend
npm ci
npm run build
```

前端必须配置：

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.example
```

## 上线后验证

1. 打开前端网址。
2. 搜索 `handheld fan`，确认 Made-in-China 和 1688 都有结果或明确失败原因。
3. 搜索 `台式咖啡机`，确认诊断区显示：
   - Made-in-China keyword: `home coffee machine`
   - 1688 keyword: `台式咖啡机`
4. 打开任意供应商的 Product 链接，确认链接对应当前供应商/产品。
5. 导出 CSV，确认没有伪造公司名、价格、网址或联系方式。

## 需要人工介入的点

- 域名购买或 DNS 指向。
- 部署平台授权。
- 生产环境变量录入。
- 如果使用 SQLite，给后端服务挂载持久化磁盘。

## 注意事项

- 不要把 `.env.local` 上传到 GitHub。
- 如果某个平台失败，SourceHunter 应返回失败原因，而不是伪造结果。
- 如果国内同事发现结果质量不佳，优先记录产品关键词、平台诊断区、Top 5 结果截图，再调整关键词和评分逻辑。
