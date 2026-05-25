"use client";

import { FormEvent, useState } from "react";

import { createSearchJob } from "@/lib/api";
import type { SearchJob, SupplierPreference } from "@/lib/types";

const supplierPreferences: SupplierPreference[] = ["Factory Preferred", "Factory Only", "Any Supplier"];

export default function HomePage() {
  const [productKeyword, setProductKeyword] = useState("handheld fan");
  const [targetPrice, setTargetPrice] = useState("");
  const [moqPreference, setMoqPreference] = useState("");
  const [supplierPreference, setSupplierPreference] = useState<SupplierPreference>("Factory Preferred");
  const [job, setJob] = useState<SearchJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setJob(null);

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

  return (
    <main className="min-h-screen">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-950">SourceHunter</h1>
            <p className="text-sm text-slate-600">Supplier discovery foundation build</p>
          </div>
          <span className="rounded border border-amber-300 bg-amber-50 px-3 py-1 text-sm text-amber-900">
            Scraping disabled in foundation build
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
