// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-019: Expert journey smoke test.
import { expect, test } from "@playwright/test";

// Fake JWT with valid 3-segment format (header.payload.signature)
const FAKE_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.dGVzdHNpZw";

test.describe("expert journey smoke", () => {
  test("expert queue page renders static shell", async ({ page, context }) => {
    await context.addCookies([
      { name: "ta_token", value: FAKE_JWT, domain: "127.0.0.1", path: "/" },
      { name: "ta_role", value: "expert", domain: "127.0.0.1", path: "/" },
    ]);
    await page.goto("/queue");
    await expect(
      page.getByRole("heading", { name: "Inceleme Kuyrugu" }),
    ).toBeVisible();
  });
});
