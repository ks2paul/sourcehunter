import { describe, expect, it } from "vitest";

import { sortSuppliers } from "../lib/supplierFilters";
import type { UniqueSupplier } from "../lib/types";

function supplier(overrides: Partial<UniqueSupplier>): UniqueSupplier {
  return {
    supplier_id: "sup_default",
    company_name: "Default Supplier",
    supplier_type: "Supplier Type Unknown",
    supplier_url: null,
    platforms: ["Made-in-China"],
    listing_count: 1,
    supplier_score: 0,
    score_breakdown: {},
    recommendation_reasons: [],
    recommended_action: "Verify supplier details first",
    products: [],
    ...overrides,
  };
}

describe("sortSuppliers", () => {
  it("sorts by highest score by default", () => {
    const suppliers = [
      supplier({ supplier_id: "low", supplier_score: 20 }),
      supplier({ supplier_id: "high", supplier_score: 80 }),
    ];

    expect(sortSuppliers(suppliers, "highest_score").map((item) => item.supplier_id)).toEqual(["high", "low"]);
  });

  it("sorts suppliers with known lowest price first", () => {
    const suppliers = [
      supplier({
        supplier_id: "unknown",
        products: [{ product_name: null, product_url: null, supplier_id: null, price: null, moq: null, platform: "Made-in-China", source_url: "https://example.test" }],
      }),
      supplier({
        supplier_id: "expensive",
        products: [{ product_name: null, product_url: null, supplier_id: null, price: "US$9.00", moq: null, platform: "Made-in-China", source_url: "https://example.test" }],
      }),
      supplier({
        supplier_id: "cheap",
        products: [{ product_name: null, product_url: null, supplier_id: null, price: "US$2.20-2.80", moq: null, platform: "Made-in-China", source_url: "https://example.test" }],
      }),
    ];

    expect(sortSuppliers(suppliers, "lowest_price").map((item) => item.supplier_id)).toEqual([
      "cheap",
      "expensive",
      "unknown",
    ]);
  });

  it("sorts suppliers with known lowest MOQ first", () => {
    const suppliers = [
      supplier({
        supplier_id: "high_moq",
        products: [{ product_name: null, product_url: null, supplier_id: null, price: null, moq: "1,000 Pieces (MOQ)", platform: "Made-in-China", source_url: "https://example.test" }],
      }),
      supplier({
        supplier_id: "low_moq",
        products: [{ product_name: null, product_url: null, supplier_id: null, price: null, moq: "20 Pieces (MOQ)", platform: "Made-in-China", source_url: "https://example.test" }],
      }),
    ];

    expect(sortSuppliers(suppliers, "lowest_moq").map((item) => item.supplier_id)).toEqual(["low_moq", "high_moq"]);
  });
});
