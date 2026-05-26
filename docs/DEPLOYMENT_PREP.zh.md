# SourceHunter 上线前准备清单

## 目标

把当前本地可用版本部署到一个内部可访问的网址。上线时仍然遵守 SourceHunter 的核心原则：不伪造供应商、价格、联系方式或链接。

## 你需要准备

- 一个用于部署前端的网址或域名。
- 一个可以运行 Python FastAPI 后端的服务环境。
- OpenAI-compatible API key，用于关键词扩展。
- Elimapi API key，用于稳定获取 1688 数据。
- GitHub 仓库访问权限。

## 需要配置的环境变量

前端：

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.example
```

后端：

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
AI_KEYWORD_EXPANSION_ENABLED=true
ELIMAPI_API_KEY=
ELIMAPI_BASE_URL=https://openapi.elim.asia/v1
SOURCEHUNTER_DB_PATH=data/sourcehunter.sqlite3
SOURCEHUNTER_CORS_ORIGINS=https://your-frontend-domain.example
```

## 上线前必须验证

- 后端 `/health` 返回 `status: ok`。
- 前端可以成功创建 search job。
- `Made-in-China Top 5` 可以返回供应商，或显示明确失败原因。
- `1688 Top 5` 可以返回供应商，或显示明确失败原因。
- CSV 导出不包含伪造字段。
- RFQ 草稿只使用页面已有的真实数据。

## 当前建议

先继续本地试用 3-5 个真实产品，把筛选质量调稳，再进入网址部署。等你准备好域名或部署平台账号时，我会接手配置。
