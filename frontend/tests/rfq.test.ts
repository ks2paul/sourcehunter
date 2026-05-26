import { describe, expect, it } from "vitest";

import { buildRfqDraft } from "../lib/rfq";
import type { UniqueSupplier } from "../lib/types";

const supplier: UniqueSupplier = {
  supplier_id: "sup_1",
  company_name: "Company Name Unavailable",
  supplier_type: "Verified Factory",
  supplier_url: null,
  platforms: ["1688"],
  listing_count: 1,
  supplier_score: 60,
  score_breakdown: {},
  recommendation_tier: "B",
  recommendation_reasons: [],
  risk_flags: [],
  recommended_action: "Request quotation immediately",
  products: [
    {
      product_name: "Rechargeable handheld fan",
      product_url: "https://detail.1688.com/offer/123.html",
      supplier_id: "shop-123",
      price: "¥3.32",
      moq: "1 Pieces (MOQ)",
      platform: "1688",
      source_url: "https://openapi.elim.asia/v1/products/search",
    },
  ],
};

describe("buildRfqDraft", () => {
  it("builds a bilingual RFQ draft from source-backed supplier data", () => {
    const draft = buildRfqDraft(supplier, "handheld fan");

    expect(draft).toContain("We are sourcing handheld fan.");
    expect(draft).toContain("Listed price: ¥3.32");
    expect(draft).toContain("Listed MOQ: 1 Pieces (MOQ)");
    expect(draft).toContain("Product URL: https://detail.1688.com/offer/123.html");
    expect(draft).toContain("我们正在寻找 handheld fan 供应商。");
    expect(draft).toContain("私标/定制包装 MOQ");
  });
});
