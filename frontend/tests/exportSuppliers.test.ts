import { describe, expect, it } from "vitest";

import { suppliersToCsv } from "../lib/exportSuppliers";
import type { UniqueSupplier } from "../lib/types";

describe("suppliersToCsv", () => {
  it("exports supplier fields and escapes CSV cells", () => {
    const suppliers: UniqueSupplier[] = [
      {
        supplier_id: "sup_1",
        company_name: 'Supplier "A"',
        supplier_type: "Verified Factory",
        supplier_url: null,
        platforms: ["1688"],
        listing_count: 1,
        supplier_score: 72,
        score_breakdown: {},
        recommendation_reasons: ["Strong match.", "Low MOQ."],
        recommended_action: "Request quotation immediately",
        products: [
          {
            product_name: "Handheld fan",
            product_url: "https://detail.1688.com/offer/1.html",
            supplier_id: "shop-1",
            price: "¥3.32",
            moq: "1 Pieces (MOQ)",
            platform: "1688",
            source_url: "https://openapi.elim.asia/v1/products/search",
          },
        ],
      },
    ];

    const csv = suppliersToCsv(suppliers);

    expect(csv).toContain('"Supplier ""A"""');
    expect(csv).toContain('"Verified Factory"');
    expect(csv).toContain('"shop-1"');
    expect(csv).toContain('"Strong match. | Low MOQ."');
  });
});
