import { describe, expect, it } from "vitest";

describe("frontend test setup", () => {
  it("runs vitest", () => {
    expect("SourceHunter").toContain("Hunter");
  });
});
