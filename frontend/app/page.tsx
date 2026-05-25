"use client";

import { FormEvent, useMemo, useState } from "react";

import { createSearchJob, getRawListings, getUniqueSuppliers } from "@/lib/api";
import { sortSuppliers, type SupplierSortMode } from "@/lib/supplierFilters";
import type { RawListingsResponse, SearchJob, SupplierPreference, SuppliersResponse } from "@/lib/types";

const supplierPreferences: SupplierPreference[] = ["Factory Preferred", "Factory Only", "Any Supplier"];
const supplierSortModes: Array<{ label: string; value: SupplierSortMode }> = [
  { label: "Highest Score", value: "highest_score" },
  { label: "Lowest Price", value: "lowest_price" },
  { label: "Lowest MOQ", value: "lowest_moq" },
];

export default function HomePage() {
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
  const [error, setError] = useState<string | null>(null);
  const sortedSuppliers = useMemo(
    () => (suppliers ? sortSuppliers(suppliers.suppliers, supplierSortMode) : []),
    [suppliers, supplierSortMode],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setJob(null);
    setSuppliers(null);
    setRawListings(null);

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

  return (
    <main className="min-h-screen">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-950">SourceHunter</h1>
            <p className="text-sm text-slate-600">Supplier discovery foundation build</p>
          </div>
          <span className="rounded border border-amber-300 bg-amber-50 px-3 py-1 text-sm text-amber-900">
            Made-in-China raw listings enabled
          </span>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">
        <form onSubmit={handleSubmit} className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-950">Search input</h2>

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="product_keyword">
            Product keyword
          </label>
          <input
            id="product_keyword"
            value={productKeyword}
            onChange={(event) => setProductKeyword(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            required
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="target_price">
            Target price
          </label>
          <input
            id="target_price"
            value={targetPrice}
            onChange={(event) => setTargetPrice(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            inputMode="decimal"
            placeholder="Optional"
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="moq_preference">
            MOQ preference
          </label>
          <input
            id="moq_preference"
            value={moqPreference}
            onChange={(event) => setMoqPreference(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            inputMode="numeric"
            placeholder="Optional"
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="supplier_preference">
            Supplier preference
          </label>
          <select
            id="supplier_preference"
            value={supplierPreference}
            onChange={(event) => setSupplierPreference(event.target.value as SupplierPreference)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          >
            {supplierPreferences.map((preference) => (
              <option key={preference} value={preference}>
                {preference}
              </option>
            ))}
          </select>

          <button
            type="submit"
            className="mt-5 w-full rounded bg-slate-950 px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isLoading}
          >
            {isLoading ? "Creating job..." : "Create search job"}
          </button>
        </form>

        <section className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-950">Result</h2>

          {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}

          {!job && !error ? (
            <p className="mt-4 text-sm text-slate-600">Create a search job to view keyword expansion.</p>
          ) : null}

          {job ? (
            <div className="mt-4 space-y-5">
              <div className="grid gap-3 sm:grid-cols-2">
                <Info label="Job ID" value={job.job_id} />
                <Info label="Status" value={job.status} />
                <Info label="Stage" value={job.progress.stage} />
                <Info label="Confidence" value={`${Math.round(job.keyword_expansion.confidence * 100)}%`} />
              </div>

              <p className="rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                {job.progress.message}
              </p>

              <KeywordList title="English keywords" items={job.keyword_expansion.english_keywords} />
              <KeywordList title="Chinese keywords" items={job.keyword_expansion.chinese_keywords} />
              <KeywordList title="Variation keywords" items={job.keyword_expansion.variation_keywords} />

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleFetchSuppliers}
                  className="rounded bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
                  disabled={isFetchingSuppliers}
                >
                  {isFetchingSuppliers ? "Finding suppliers..." : "Find top 5 unique suppliers"}
                </button>
                <button
                  type="button"
                  onClick={handleFetchRawListings}
                  className="rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 disabled:cursor-not-allowed disabled:bg-slate-100"
                  disabled={isFetchingListings}
                >
                  {isFetchingListings ? "Fetching raw listings..." : "Fetch raw listings"}
                </button>
              </div>

              {suppliers ? (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-slate-800">Top 5 unique suppliers</h3>
                  {suppliers.failures.length > 0 ? (
                    <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                      {suppliers.failures.map((failure) => (
                        <p key={`${failure.platform}-${failure.error_type}`}>
                          {failure.platform}: {failure.message}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {suppliers.suppliers.length > 0 ? (
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-2">
                        {supplierSortModes.map((mode) => (
                          <button
                            type="button"
                            key={mode.value}
                            onClick={() => setSupplierSortMode(mode.value)}
                            className={`rounded border px-3 py-1 text-sm ${
                              supplierSortMode === mode.value
                                ? "border-slate-950 bg-slate-950 text-white"
                                : "border-slate-300 bg-white text-slate-700"
                            }`}
                          >
                            {mode.label}
                          </button>
                        ))}
                      </div>
                      {sortedSuppliers.map((supplier) => {
                        const leadProduct = supplier.products[0];
                        return (
                          <article key={supplier.supplier_id} className="rounded border border-slate-200 p-3">
                            <div className="text-xs uppercase tracking-wide text-slate-500">
                              {supplier.platforms.join(", ")} · {supplier.listing_count} listing
                              {supplier.listing_count === 1 ? "" : "s"}
                            </div>
                            <div className="mt-1 flex flex-wrap items-start justify-between gap-3">
                              <div>
                                <h4 className="text-sm font-semibold text-slate-950">{supplier.company_name}</h4>
                                <p className="mt-1 text-xs text-slate-500">{supplier.supplier_type}</p>
                              </div>
                              <div className="rounded border border-slate-300 px-2 py-1 text-sm font-semibold text-slate-950">
                                Score {supplier.supplier_score}
                              </div>
                            </div>
                            <p className="mt-2 text-sm text-slate-600">
                              Lead product: {leadProduct?.product_name ?? "Product Name Unavailable"}
                            </p>
                            <p className="mt-1 text-sm text-slate-600">
                              Price: {leadProduct?.price ?? "Price Unavailable"} · MOQ:{" "}
                              {leadProduct?.moq ?? "MOQ Unavailable"}
                            </p>
                            <p className="mt-2 text-sm font-medium text-slate-800">
                              Action: {supplier.recommended_action}
                            </p>
                            <ul className="mt-2 space-y-1 text-sm text-slate-600">
                              {supplier.recommendation_reasons.slice(0, 3).map((reason) => (
                                <li key={reason}>{reason}</li>
                              ))}
                            </ul>
                            <div className="mt-2 flex flex-wrap gap-3 text-sm">
                              {supplier.supplier_url ? (
                                <a className="text-blue-700 underline" href={supplier.supplier_url} target="_blank">
                                  Supplier
                                </a>
                              ) : null}
                              {leadProduct?.product_url ? (
                                <a className="text-blue-700 underline" href={leadProduct.product_url} target="_blank">
                                  Product
                                </a>
                              ) : null}
                            </div>
                          </article>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">No unique suppliers returned.</p>
                  )}
                </div>
              ) : null}

              {rawListings ? (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-slate-800">Raw listings</h3>
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
                            {listing.raw_product_name ?? "Product Name Unavailable"}
                          </h4>
                          <p className="mt-1 text-sm text-slate-700">
                            {listing.raw_company_name ?? "Company Name Unavailable"}
                          </p>
                          <p className="mt-2 text-sm text-slate-600">
                            Price: {listing.raw_price ?? "Price Unavailable"} · MOQ:{" "}
                            {listing.raw_moq ?? "MOQ Unavailable"}
                          </p>
                          <div className="mt-2 flex flex-wrap gap-3 text-sm">
                            {listing.product_url ? (
                              <a className="text-blue-700 underline" href={listing.product_url} target="_blank">
                                Product
                              </a>
                            ) : null}
                            {listing.supplier_url ? (
                              <a className="text-blue-700 underline" href={listing.supplier_url} target="_blank">
                                Supplier
                              </a>
                            ) : null}
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">No reliable raw listings returned.</p>
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

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-slate-200 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm font-medium text-slate-950">{value}</div>
    </div>
  );
}

function KeywordList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      {items.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {items.map((item) => (
            <span key={item} className="rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700">
              {item}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-500">Unavailable in deterministic foundation build.</p>
      )}
    </div>
  );
}
