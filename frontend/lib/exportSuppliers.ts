import type { UniqueSupplier } from "./types";

export function suppliersToCsv(suppliers: UniqueSupplier[]): string {
  const rows = suppliers.map((supplier) => {
    const leadProduct = supplier.products[0];
    return [
      supplier.supplier_id,
      supplier.company_name,
      supplier.supplier_type,
      supplier.platforms.join(" / "),
      String(supplier.supplier_score),
      supplier.recommended_action,
      leadProduct?.supplier_id ?? "",
      leadProduct?.product_name ?? "",
      leadProduct?.price ?? "",
      leadProduct?.moq ?? "",
      leadProduct?.product_url ?? "",
      supplier.supplier_url ?? "",
      supplier.recommendation_reasons.join(" | "),
    ];
  });

  return [
    [
      "Supplier ID",
      "Company Name",
      "Supplier Type",
      "Platforms",
      "Score",
      "Recommended Action",
      "Platform Supplier ID",
      "Lead Product",
      "Price",
      "MOQ",
      "Product URL",
      "Supplier URL",
      "Recommendation Reasons",
    ],
    ...rows,
  ]
    .map((row) => row.map(escapeCsvCell).join(","))
    .join("\n");
}

export function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function escapeCsvCell(value: string): string {
  return `"${value.replaceAll('"', '""')}"`;
}
