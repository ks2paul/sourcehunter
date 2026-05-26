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

export type RawListing = {
  platform: string;
  source_url: string;
  product_url: string | null;
  supplier_url: string | null;
  raw_supplier_id: string | null;
  raw_product_name: string | null;
  raw_company_name: string | null;
  raw_price: string | null;
  raw_moq: string | null;
  raw_location: string | null;
  raw_years_in_business: string | null;
  raw_contact_text: string | null;
  raw_supplier_type: string | null;
  scraped_at: string;
};

export type RawListingsResponse = {
  job_id: string;
  status: "completed" | "no_results";
  listings: RawListing[];
  failures: Array<{
    platform: string;
    keyword: string;
    error_type: string;
    message: string;
  }>;
};

export type UniqueSupplier = {
  supplier_id: string;
  company_name: string;
  supplier_type: string;
  supplier_url: string | null;
  platforms: string[];
  listing_count: number;
  supplier_score: number;
  score_breakdown: Record<string, number>;
  recommendation_reasons: string[];
  recommended_action: string;
  products: Array<{
    product_name: string | null;
    product_url: string | null;
    supplier_id: string | null;
    price: string | null;
    moq: string | null;
    platform: string;
    source_url: string;
  }>;
};

export type SuppliersResponse = {
  job_id: string;
  status: "completed" | "no_results";
  suppliers: UniqueSupplier[];
  failures: RawListingsResponse["failures"];
};
