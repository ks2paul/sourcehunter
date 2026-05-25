export type SupplierPreference = "Factory Only" | "Factory Preferred" | "Any Supplier";

export type KeywordExpansion = {
  english_keywords: string[];
  chinese_keywords: string[];
  variation_keywords: string[];
  confidence: number;
  source: "deterministic_v1" | "openai_compatible";
};

export type SearchJob = {
  job_id: string;
  product_keyword: string;
  target_price: number | null;
  moq_preference: number | null;
  supplier_preference: SupplierPreference;
  status: "queued" | "running" | "partially_completed" | "completed" | "failed";
  progress: {
    stage: string;
    message: string;
  };
  keyword_expansion: KeywordExpansion;
  created_at: string;
  updated_at: string;
  error_summary: string | null;
};

export type CreateSearchJobPayload = {
  product_keyword: string;
  target_price: number | null;
  moq_preference: number | null;
  supplier_preference: SupplierPreference;
  product_image_id: string | null;
};
