"use client";

import { FormEvent, useMemo, useState } from "react";

import { createSearchJob, getRawListings, getUniqueSuppliers } from "@/lib/api";
import { downloadCsv, suppliersToCsv } from "@/lib/exportSuppliers";
import { buildRfqDraft } from "@/lib/rfq";
import { sortSuppliers, type SupplierSortMode } from "@/lib/supplierFilters";
import type { RawListingsResponse, SearchJob, SupplierPreference, SuppliersResponse, UniqueSupplier } from "@/lib/types";

type Language = "zh" | "en";

const supplierPreferences: SupplierPreference[] = ["Factory Preferred", "Factory Only", "Any Supplier"];
const supplierSortModes: SupplierSortMode[] = ["highest_score", "lowest_price", "lowest_moq"];

const copy = {
  zh: {
    subtitle: "AI 供应商发现与采购判断工具",
    searchInput: "搜索输入",
    productKeyword: "产品关键词",
    targetPrice: "目标价格",
    moqPreference: "MOQ 偏好",
    supplierPreference: "供应商偏好",
    optional: "可选",
    createJob: "创建搜索任务",
    creatingJob: "创建中...",
    englishKeywords: "英文关键词",
    chineseKeywords: "中文关键词",
    variationKeywords: "变体关键词",
    result: "结果",
    createPrompt: "创建搜索任务后查看关键词扩展。",
    jobId: "任务 ID",
    status: "状态",
    stage: "阶段",
    confidence: "置信度",
    findSuppliers: "查找各平台 Top 5 供应商",
    findingSuppliers: "查找供应商中...",
    fetchRawListings: "查看原始 Listings",
    fetchingRawListings: "抓取原始 Listings 中...",
    searchingTitle: "正在搜索供应商平台",
    searchingMessage: "SourceHunter 正在检查 Made-in-China 和 1688，去重供应商，并按平台分别排序。",
    fetchingTitle: "正在抓取原始 Listings",
    fetchingMessage: "SourceHunter 正在收集有来源链接的 listings，方便检查数据。",
    supplierShortlists: "供应商候选名单",
    keyword: "关键词",
    rawListingsCount: "原始 Listings",
    uniqueSuppliersCount: "去重供应商",
    unavailable: "不可用",
    exportCsv: "导出 CSV",
    noUniqueSuppliers: "暂无去重后的供应商结果。",
    supplierUnit: "家供应商",
    noSuppliersForGroup: "该平台暂无供应商结果。",
    rfqDraft: "询盘草稿",
    copyRfq: "复制询盘",
    rfqCopied: "询盘已复制",
    rawListings: "原始 Listings",
    noReliableRawListings: "暂无可靠原始 listing。",
    productNameUnavailable: "产品名不可用",
    companyNameUnavailable: "公司名不可用",
    priceUnavailable: "价格不可用",
    moqUnavailable: "MOQ 不可用",
    price: "价格",
    leadProduct: "主产品",
    supplierId: "供应商 ID",
    action: "建议动作",
    risk: "风险",
    tier: "等级",
    score: "评分",
    listing: "条 listing",
    listings: "条 listings",
    supplier: "供应商",
    product: "产品",
    deterministicUnavailable: "当前基础版本暂无可靠数据。",
    languageLabel: "语言",
    zh: "中文",
    en: "English",
  },
  en: {
    subtitle: "AI-powered supplier discovery and procurement intelligence",
    searchInput: "Search input",
    productKeyword: "Product keyword",
    targetPrice: "Target price",
    moqPreference: "MOQ preference",
    supplierPreference: "Supplier preference",
    optional: "Optional",
    createJob: "Create search job",
    creatingJob: "Creating job...",
    englishKeywords: "English keywords",
    chineseKeywords: "Chinese keywords",
    variationKeywords: "Variation keywords",
    result: "Result",
    createPrompt: "Create a search job to view keyword expansion.",
    jobId: "Job ID",
    status: "Status",
    stage: "Stage",
    confidence: "Confidence",
    findSuppliers: "Find platform Top 5 suppliers",
    findingSuppliers: "Finding suppliers...",
    fetchRawListings: "Fetch raw listings",
    fetchingRawListings: "Fetching raw listings...",
    searchingTitle: "Searching supplier platforms",
    searchingMessage:
      "SourceHunter is checking Made-in-China and 1688, deduplicating suppliers, and ranking each platform separately.",
    fetchingTitle: "Fetching raw listings",
    fetchingMessage: "SourceHunter is collecting source-backed listings for inspection.",
    supplierShortlists: "Supplier shortlists",
    keyword: "Keyword",
    rawListingsCount: "Raw listings",
    uniqueSuppliersCount: "Unique suppliers",
    unavailable: "Unavailable",
    exportCsv: "Export CSV",
    noUniqueSuppliers: "No unique suppliers returned.",
    supplierUnit: "supplier",
    noSuppliersForGroup: "No suppliers returned for this group.",
    rfqDraft: "RFQ draft",
    copyRfq: "Copy RFQ",
    rfqCopied: "RFQ copied",
    rawListings: "Raw listings",
    noReliableRawListings: "No reliable raw listings returned.",
    productNameUnavailable: "Product Name Unavailable",
    companyNameUnavailable: "Company Name Unavailable",
    priceUnavailable: "Price Unavailable",
    moqUnavailable: "MOQ Unavailable",
    price: "Price",
    leadProduct: "Lead product",
    supplierId: "Supplier ID",
    action: "Action",
    risk: "Risk",
    tier: "Tier",
    score: "Score",
    listing: "listing",
    listings: "listings",
    supplier: "Supplier",
    product: "Product",
    deterministicUnavailable: "Unavailable in deterministic foundation build.",
    languageLabel: "Language",
    zh: "中文",
    en: "English",
  },
} as const;

type UiCopy = (typeof copy)[Language];

export default function HomePage() {
  const [language, setLanguage] = useState<Language>("zh");
  const [productKeyword, setProductKeyword] = useState("handheld fan");
  const [targetPrice, setTargetPrice] = useState("");
  const [moqPreference, setMoqPreference] = useState("");
  const [supplierPreference, setSupplierPreference] = useState<SupplierPreference>("Factory Preferred");
  const [job, setJob] = useState<SearchJob | null>(null);
  const [suppliers, setSuppliers] = useState<SuppliersResponse | null>(null);
  const [rawListings, setRawListings] = useState<RawListingsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingSuppliers, setIsFetchingSuppliers] = useState(false);
  const [isFetchingListings, setIsFetchingListings] = useState(false);
  const [supplierSortMode, setSupplierSortMode] = useState<SupplierSortMode>("highest_score");
  const [rfqDraft, setRfqDraft] = useState<string | null>(null);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const t = copy[language];
  const sortedPlatformGroups = useMemo(
    () =>
      (suppliers?.platform_supplier_groups ?? []).map((group) => ({
        ...group,
        suppliers: sortSuppliers(group.suppliers, supplierSortMode),
      })),
    [suppliers, supplierSortMode],
  );
  const rawListingCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const listing of rawListings?.listings ?? []) {
      counts.set(listing.platform, (counts.get(listing.platform) ?? 0) + 1);
    }
    return Array.from(counts.entries()).map(([platform, count]) => ({ platform, count }));
  }, [rawListings]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setJob(null);
    setSuppliers(null);
    setRawListings(null);
    setRfqDraft(null);

    try {
      const createdJob = await createSearchJob({
        product_keyword: productKeyword,
        target_price: targetPrice ? Number(targetPrice) : null,
        moq_preference: moqPreference ? Number(moqPreference) : null,
        supplier_preference: supplierPreference,
        product_image_id: null,
      });
      setJob(createdJob);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Search request failed");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleFetchSuppliers() {
    if (!job) {
      return;
    }
    setIsFetchingSuppliers(true);
    setError(null);
    setSuppliers(null);
    setRfqDraft(null);

    try {
      setSuppliers(await getUniqueSuppliers(job.job_id));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Supplier request failed");
    } finally {
      setIsFetchingSuppliers(false);
    }
  }

  async function handleFetchRawListings() {
    if (!job) {
      return;
    }
    setIsFetchingListings(true);
    setError(null);

    try {
      setRawListings(await getRawListings(job.job_id));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Raw listing request failed");
    } finally {
      setIsFetchingListings(false);
    }
  }

  async function handleCopyRfq() {
    if (!rfqDraft) {
      return;
    }
    await navigator.clipboard.writeText(rfqDraft);
    setCopyMessage(t.rfqCopied);
  }

  function handleExportSuppliers() {
    if (!suppliers) {
      return;
    }
    const filename = `${job?.product_keyword ?? "sourcehunter"}-${suppliers.job_id}-suppliers.csv`;
    const platformSuppliers = sortedPlatformGroups.flatMap((group) => group.suppliers);
    downloadCsv(filename, suppliersToCsv(platformSuppliers));
  }

  return (
    <main className="min-h-screen">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-950">SourceHunter</h1>
            <p className="text-sm text-slate-600">{t.subtitle}</p>
          </div>
          <div className="flex items-center gap-2" aria-label={t.languageLabel}>
            {(["zh", "en"] as Language[]).map((item) => (
              <button
                type="button"
                key={item}
                onClick={() => setLanguage(item)}
                className={`rounded border px-3 py-1 text-sm font-medium ${
                  language === item
                    ? "border-slate-950 bg-slate-950 text-white"
                    : "border-slate-300 bg-white text-slate-700"
                }`}
              >
                {copy[item][item]}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">
        <aside className="space-y-4">
          <form onSubmit={handleSubmit} className="rounded border border-slate-200 bg-white p-5">
            <h2 className="text-base font-semibold text-slate-950">{t.searchInput}</h2>

            <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="product_keyword">
              {t.productKeyword}
            </label>
            <input
              id="product_keyword"
              value={productKeyword}
              onChange={(event) => setProductKeyword(event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              required
            />

            <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="target_price">
              {t.targetPrice}
            </label>
            <input
              id="target_price"
              value={targetPrice}
              onChange={(event) => setTargetPrice(event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              inputMode="decimal"
              placeholder={t.optional}
            />

            <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="moq_preference">
              {t.moqPreference}
            </label>
            <input
              id="moq_preference"
              value={moqPreference}
              onChange={(event) => setMoqPreference(event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              inputMode="numeric"
              placeholder={t.optional}
            />

            <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="supplier_preference">
              {t.supplierPreference}
            </label>
            <select
              id="supplier_preference"
              value={supplierPreference}
              onChange={(event) => setSupplierPreference(event.target.value as SupplierPreference)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            >
              {supplierPreferences.map((preference) => (
                <option key={preference} value={preference}>
                  {translateSupplierPreference(preference, language)}
                </option>
              ))}
            </select>

            <button
              type="submit"
              className="mt-5 w-full rounded bg-slate-950 px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={isLoading}
            >
              {isLoading ? t.creatingJob : t.createJob}
            </button>
          </form>

          {job ? (
            <div className="space-y-4 rounded border border-slate-200 bg-white p-5">
              <KeywordList
                title={t.englishKeywords}
                items={job.keyword_expansion.english_keywords}
                tone="blue"
                emptyMessage={t.deterministicUnavailable}
              />
              <KeywordList
                title={t.chineseKeywords}
                items={job.keyword_expansion.chinese_keywords}
                tone="emerald"
                emptyMessage={t.deterministicUnavailable}
              />
              <KeywordList
                title={t.variationKeywords}
                items={job.keyword_expansion.variation_keywords}
                tone="amber"
                emptyMessage={t.deterministicUnavailable}
              />
            </div>
          ) : null}
        </aside>

        <section className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-950">{t.result}</h2>

          {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}

          {!job && !error ? (
            <p className="mt-4 text-sm text-slate-600">{t.createPrompt}</p>
          ) : null}

          {job ? (
            <div className="mt-4 space-y-5">
              <div className="grid gap-3 sm:grid-cols-2">
                <Info label={t.jobId} value={job.job_id} />
                <Info label={t.status} value={translateStatus(job.status, language)} />
                <Info label={t.stage} value={translateStage(job.progress.stage, language)} />
                <Info label={t.confidence} value={`${Math.round(job.keyword_expansion.confidence * 100)}%`} />
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleFetchSuppliers}
                  className="rounded bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
                  disabled={isFetchingSuppliers}
                >
                  {isFetchingSuppliers ? t.findingSuppliers : t.findSuppliers}
                </button>
                <button
                  type="button"
                  onClick={handleFetchRawListings}
                  className="rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 disabled:cursor-not-allowed disabled:bg-slate-100"
                  disabled={isFetchingListings}
                >
                  {isFetchingListings ? t.fetchingRawListings : t.fetchRawListings}
                </button>
              </div>

              {isFetchingSuppliers ? (
                <StatusNotice
                  tone="blue"
                  title={t.searchingTitle}
                  message={t.searchingMessage}
                />
              ) : null}

              {isFetchingListings ? (
                <StatusNotice
                  tone="blue"
                  title={t.fetchingTitle}
                  message={t.fetchingMessage}
                />
              ) : null}

              {suppliers ? (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-slate-800">{t.supplierShortlists}</h3>
                  {(suppliers.platform_diagnostics ?? []).length > 0 ? (
                    <div className="grid gap-2 md:grid-cols-2">
                      {(suppliers.platform_diagnostics ?? []).map((item) => (
                        <div key={item.platform} className="rounded border border-slate-200 bg-slate-50 p-3 text-sm">
                          <div className="font-medium text-slate-900">{item.platform}</div>
                          <p className="mt-1 text-slate-600">
                            {t.keyword}: {item.searched_keyword ?? t.unavailable}
                          </p>
                          <p className="mt-1 text-slate-600">
                            {t.rawListingsCount}: {item.raw_listing_count} · {t.uniqueSuppliersCount}:{" "}
                            {item.unique_supplier_count}
                          </p>
                          {item.failure ? <p className="mt-1 text-red-700">{item.failure.message}</p> : null}
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {suppliers.failures.length > 0 ? (
                    <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                      {suppliers.failures.map((failure) => (
                        <p key={`${failure.platform}-${failure.error_type}`}>
                          {failure.platform}: {failure.message}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {sortedPlatformGroups.some((group) => group.suppliers.length > 0) ? (
                    <div className="space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex flex-wrap gap-2">
                          {supplierSortModes.map((mode) => (
                            <button
                              type="button"
                              key={mode}
                              onClick={() => setSupplierSortMode(mode)}
                              className={`rounded border px-3 py-1 text-sm ${
                                supplierSortMode === mode
                                  ? "border-slate-950 bg-slate-950 text-white"
                                  : "border-slate-300 bg-white text-slate-700"
                              }`}
                            >
                              {translateSortMode(mode, language)}
                            </button>
                          ))}
                        </div>
                        <button
                          type="button"
                          onClick={handleExportSuppliers}
                          className="rounded border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-900"
                        >
                          {t.exportCsv}
                        </button>
                      </div>
                      <div className="grid gap-4 lg:grid-cols-2">
                        {sortedPlatformGroups.map((group) => (
                          <SupplierGroup
                            key={group.platform}
                            title={`${group.platform} Top 5`}
                            suppliers={group.suppliers}
                            failureMessage={platformFailureMessage(suppliers, group.platform)}
                            productKeyword={job.product_keyword}
                            onBuildRfq={setRfqDraft}
                            language={language}
                            labels={t}
                          />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">{t.noUniqueSuppliers}</p>
                  )}
                </div>
              ) : null}

              {rfqDraft ? (
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-slate-800">{t.rfqDraft}</h3>
                    <div className="flex items-center gap-3">
                      {copyMessage ? <span className="text-sm text-emerald-700">{copyMessage}</span> : null}
                      <button
                        type="button"
                        onClick={handleCopyRfq}
                        className="rounded border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-900"
                      >
                        {t.copyRfq}
                      </button>
                    </div>
                  </div>
                  <textarea
                    readOnly
                    value={rfqDraft}
                    className="min-h-80 w-full rounded border border-slate-300 bg-slate-50 p-3 font-mono text-sm text-slate-800"
                  />
                </div>
              ) : null}

              {rawListings ? (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-slate-800">{t.rawListings}</h3>
                  {rawListingCounts.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {rawListingCounts.map((item) => (
                        <span
                          key={item.platform}
                          className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-sm text-slate-700"
                        >
                          {item.platform}: {item.count}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  {rawListings.failures.length > 0 ? (
                    <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                      {rawListings.failures.map((failure) => (
                        <p key={`${failure.platform}-${failure.error_type}`}>
                          {failure.platform}: {failure.message}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {rawListings.listings.length > 0 ? (
                    <div className="space-y-3">
                      {rawListings.listings.map((listing) => (
                        <article
                          key={`${listing.platform}-${listing.product_url}`}
                          className="rounded border border-slate-200 p-3"
                        >
                          <div className="text-xs uppercase tracking-wide text-slate-500">{listing.platform}</div>
                          <h4 className="mt-1 text-sm font-semibold text-slate-950">
                            {listing.raw_product_name ?? t.productNameUnavailable}
                          </h4>
                          <p className="mt-1 text-sm text-slate-700">
                            {listing.raw_company_name ?? t.companyNameUnavailable}
                          </p>
                          <p className="mt-2 text-sm text-slate-600">
                            {t.price}: {listing.raw_price ?? t.priceUnavailable} · MOQ:{" "}
                            {listing.raw_moq ?? t.moqUnavailable}
                          </p>
                          <div className="mt-2 flex flex-wrap gap-3 text-sm">
                            {listing.product_url ? (
                              <a className="text-blue-700 underline" href={listing.product_url} target="_blank">
                                {t.product}
                              </a>
                            ) : null}
                            {listing.supplier_url ? (
                              <a className="text-blue-700 underline" href={listing.supplier_url} target="_blank">
                                {t.supplier}
                              </a>
                            ) : null}
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">{t.noReliableRawListings}</p>
                  )}
                </div>
              ) : null}
            </div>
          ) : null}
        </section>
      </section>
    </main>
  );
}

function SupplierGroup({
  title,
  suppliers,
  failureMessage,
  productKeyword,
  onBuildRfq,
  language,
  labels,
}: {
  title: string;
  suppliers: UniqueSupplier[];
  failureMessage?: string;
  productKeyword: string;
  onBuildRfq: (draft: string) => void;
  language: Language;
  labels: UiCopy;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600">
          {language === "zh"
            ? `${suppliers.length}${labels.supplierUnit}`
            : `${suppliers.length} ${labels.supplierUnit}${suppliers.length === 1 ? "" : "s"}`}
        </span>
      </div>
      {suppliers.length > 0 ? (
        suppliers.map((supplier) => (
          <SupplierCard
            key={`${title}-${supplier.supplier_id}`}
            supplier={supplier}
            productKeyword={productKeyword}
            onBuildRfq={onBuildRfq}
            language={language}
            labels={labels}
          />
        ))
      ) : (
        <div className="rounded border border-slate-200 p-3 text-sm text-slate-500">
          <p>{labels.noSuppliersForGroup}</p>
          {failureMessage ? <p className="mt-1 text-red-700">{failureMessage}</p> : null}
        </div>
      )}
    </div>
  );
}

function SupplierCard({
  supplier,
  productKeyword,
  onBuildRfq,
  language,
  labels,
}: {
  supplier: UniqueSupplier;
  productKeyword: string;
  onBuildRfq: (draft: string) => void;
  language: Language;
  labels: UiCopy;
}) {
  const leadProduct = supplier.products[0];
  const riskFlags = supplier.risk_flags ?? [];
  const tier = supplier.recommendation_tier ?? "Unrated";

  return (
    <article className="rounded border border-slate-200 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {supplier.platforms.join(", ")} · {supplier.listing_count}{" "}
        {supplier.listing_count === 1 ? labels.listing : labels.listings}
      </div>
      <div className="mt-1 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-950">{supplier.company_name}</h4>
          <p className="mt-1 text-xs text-slate-500">{translateSupplierType(supplier.supplier_type, language)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="rounded border border-slate-300 px-2 py-1 text-sm font-semibold text-slate-950">
            {labels.tier} {tier}
          </div>
          <div className="rounded border border-slate-300 px-2 py-1 text-sm font-semibold text-slate-950">
            {labels.score} {supplier.supplier_score}
          </div>
        </div>
      </div>
      <p className="mt-2 text-sm text-slate-600">
        {labels.leadProduct}: {leadProduct?.product_name ?? labels.productNameUnavailable}
      </p>
      <p className="mt-1 text-sm text-slate-600">
        {labels.price}: {leadProduct?.price ?? labels.priceUnavailable} · MOQ: {leadProduct?.moq ?? labels.moqUnavailable}
      </p>
      {leadProduct?.supplier_id ? (
        <p className="mt-1 break-all text-xs text-slate-500">
          {labels.supplierId}: {leadProduct.supplier_id}
        </p>
      ) : null}
      <p className="mt-2 text-sm font-medium text-slate-800">
        {labels.action}: {translateRecommendedAction(supplier.recommended_action, language)}
      </p>
      {riskFlags.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm text-amber-800">
          {riskFlags.map((flag) => (
            <li key={flag}>
              {labels.risk}: {translateRiskFlag(flag, language)}
            </li>
          ))}
        </ul>
      ) : null}
      <ul className="mt-2 space-y-1 text-sm text-slate-600">
        {supplier.recommendation_reasons.slice(0, 3).map((reason) => (
          <li key={reason}>{translateReason(reason, language)}</li>
        ))}
      </ul>
      <div className="mt-2 flex flex-wrap gap-3 text-sm">
        <button
          type="button"
          onClick={() => onBuildRfq(buildRfqDraft(supplier, productKeyword))}
          className="text-slate-900 underline"
        >
          {labels.rfqDraft}
        </button>
        {supplier.supplier_url ? (
          <a className="text-blue-700 underline" href={supplier.supplier_url} target="_blank">
            {labels.supplier}
          </a>
        ) : null}
        {leadProduct?.product_url ? (
          <a className="text-blue-700 underline" href={leadProduct.product_url} target="_blank">
            {labels.product}
          </a>
        ) : null}
      </div>
    </article>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-slate-200 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm font-medium text-slate-950">{value}</div>
    </div>
  );
}

function StatusNotice({ title, message, tone }: { title: string; message: string; tone: "blue" }) {
  const toneClassName = {
    blue: "border-blue-200 bg-blue-50 text-blue-800",
  }[tone];

  return (
    <div className={`rounded border p-3 text-sm ${toneClassName}`}>
      <div className="font-medium">{title}</div>
      <p className="mt-1">{message}</p>
    </div>
  );
}

function platformFailureMessage(suppliers: SuppliersResponse, platform: string): string | undefined {
  const failure = suppliers.failures.find((item) => item.platform === platform);
  return failure?.message;
}

function KeywordList({
  title,
  items,
  tone,
  emptyMessage,
}: {
  title: string;
  items: string[];
  tone: "blue" | "emerald" | "amber";
  emptyMessage: string;
}) {
  const toneClassName = {
    blue: "border-blue-200 bg-blue-50 text-blue-800",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-800",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
  }[tone];

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      {items.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {items.map((item) => (
            <span key={item} className={`rounded border px-2 py-1 text-sm ${toneClassName}`}>
              {item}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-500">{emptyMessage}</p>
      )}
    </div>
  );
}

function translateSupplierPreference(preference: SupplierPreference, language: Language): string {
  if (language === "en") {
    return preference;
  }
  return (
    {
      "Factory Preferred": "工厂优先",
      "Factory Only": "只看工厂",
      "Any Supplier": "不限供应商",
    } satisfies Record<SupplierPreference, string>
  )[preference];
}

function translateSortMode(mode: SupplierSortMode, language: Language): string {
  const labels: Record<SupplierSortMode, Record<Language, string>> = {
    highest_score: { zh: "最高评分", en: "Highest Score" },
    lowest_price: { zh: "最低价格", en: "Lowest Price" },
    lowest_moq: { zh: "最低 MOQ", en: "Lowest MOQ" },
  };
  return labels[mode][language];
}

function translateStatus(status: string, language: Language): string {
  if (language === "en") {
    return status;
  }
  return (
    {
      completed: "已完成",
      running: "运行中",
      failed: "失败",
      pending: "等待中",
    }[status] ?? status
  );
}

function translateStage(stage: string, language: Language): string {
  if (language === "en") {
    return stage;
  }
  return (
    {
      created: "已创建",
      keyword_expansion_completed: "关键词扩展完成",
      supplier_search_completed: "供应商搜索完成",
      raw_listing_retrieval_completed: "原始 listing 抓取完成",
      failed: "失败",
    }[stage] ?? stage
  );
}

function translateSupplierType(supplierType: string, language: Language): string {
  if (language === "en") {
    return supplierType;
  }
  return (
    {
      "Verified Factory": "已验证工厂",
      "Verified Merchant": "已验证商家",
      "Verified Seller": "已验证卖家",
      "Supplier Type Unknown": "供应商类型未知",
    }[supplierType] ?? supplierType
  );
}

function translateRecommendedAction(action: string, language: Language): string {
  if (language === "en") {
    return action;
  }
  return (
    {
      "Request quotation immediately": "立即询价",
      "Request samples": "申请样品",
      "Negotiate MOQ": "谈判 MOQ",
      "Verify supplier details first": "先核实供应商信息",
      "Ask for quotation and MOQ": "询价并确认 MOQ",
      "Do not shortlist until product match is verified": "产品匹配确认前不要列入候选",
      "Verify price authenticity before contacting": "联系前先核实价格真实性",
    }[action] ?? action
  );
}

function translateRiskFlag(flag: string, language: Language): string {
  if (language === "en") {
    return flag;
  }
  return (
    {
      "Product match needs manual review": "产品匹配需要人工复核",
      "Price may be abnormally low": "价格可能异常偏低",
      "MOQ may be too high": "MOQ 可能偏高",
      "Supplier type unknown": "供应商类型未知",
      "Limited supplier maturity data": "供应商成熟度数据有限",
      "No public contact information": "暂无公开联系方式",
    }[flag] ?? flag
  );
}

function translateReason(reason: string, language: Language): string {
  if (language === "en") {
    return reason;
  }
  return (
    {
      "Strong product match": "产品匹配度高",
      "Good product match": "产品匹配度较好",
      "Factory signal found": "发现工厂信号",
      "Verified supplier profile": "供应商资料已验证",
      "Competitive price signal": "价格具备竞争力",
      "MOQ appears suitable": "MOQ 看起来合适",
      "Multiple listings from same supplier": "同一供应商有多个相关 listing",
      "Export readiness signal found": "发现出口准备度信号",
      "Business maturity signal found": "发现经营成熟度信号",
    }[reason] ?? reason
  );
}
