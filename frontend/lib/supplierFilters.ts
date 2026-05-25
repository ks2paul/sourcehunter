import type { UniqueSupplier } from "./types";

export type SupplierSortMode = "highest_score" | "lowest_price" | "lowest_moq";

export function sortSuppliers(suppliers: UniqueSupplier[], mode: SupplierSortMode): UniqueSupplier[] {
  return [...suppliers].sort((left, right) => {
    if (mode === "lowest_price") {
      return compareOptionalNumber(lowestProductNumber(left, "price"), lowestProductNumber(right, "price"));
    }
    if (mode === "lowest_moq") {
      return compareOptionalNumber(lowestProductNumber(left, "moq"), lowestProductNumber(right, "moq"));
    }
    return right.supplier_score - left.supplier_score;
  });
}

function compareOptionalNumber(left: number | null, right: number | null): number {
  if (left === null && right === null) {
    return 0;
  }
  if (left === null) {
    return 1;
  }
  if (right === null) {
    return -1;
  }
  return left - right;
}

function lowestProductNumber(supplier: UniqueSupplier, field: "price" | "moq"): number | null {
  const values = supplier.products
    .map((product) => parseLowestNumber(product[field]))
    .filter((value): value is number => value !== null);
  return values.length > 0 ? Math.min(...values) : null;
}

function parseLowestNumber(value: string | null): number | null {
  if (!value) {
    return null;
  }
  const matches = value.match(/\d+(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?/g);
  if (!matches) {
    return null;
  }
  return Math.min(...matches.map((match) => Number(match.replaceAll(",", ""))));
}
