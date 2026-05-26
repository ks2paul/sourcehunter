import type { UniqueSupplier } from "./types";

export function buildRfqDraft(supplier: UniqueSupplier, productKeyword: string): string {
  const leadProduct = supplier.products[0];
  const productName = leadProduct?.product_name ?? productKeyword;
  const priceLine = leadProduct?.price ? `Listed price: ${leadProduct.price}` : "Listed price: Price Unavailable";
  const moqLine = leadProduct?.moq ? `Listed MOQ: ${leadProduct.moq}` : "Listed MOQ: MOQ Unavailable";
  const productUrl = leadProduct?.product_url ? `Product URL: ${leadProduct.product_url}` : "Product URL: Unavailable";

  return [
    "Hello,",
    "",
    `We are sourcing ${productKeyword}. We found your product: ${productName}.`,
    priceLine,
    moqLine,
    productUrl,
    "",
    "Please confirm:",
    "1. Current EXW/FOB unit price by quantity tier",
    "2. MOQ for private label / custom packaging",
    "3. Sample cost and sample lead time",
    "4. Production lead time",
    "5. Available certifications and export experience",
    "6. Product photos, specification sheet, and packaging details",
    "",
    "你好，",
    "",
    `我们正在寻找 ${productKeyword} 供应商。我们看到贵司产品：${productName}。`,
    `${priceLine}`,
    `${moqLine}`,
    `${productUrl}`,
    "",
    "请确认以下信息：",
    "1. 不同数量阶梯的最新 EXW/FOB 单价",
    "2. 私标/定制包装 MOQ",
    "3. 样品费用和样品交期",
    "4. 大货生产交期",
    "5. 可提供的认证和出口经验",
    "6. 产品图片、规格书和包装资料",
  ].join("\n");
}
