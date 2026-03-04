// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
import { expect, test } from "@playwright/test";

test.describe("expert journey smoke", () => {
  test("expert queue page renders static shell", async ({ page, context }) => {
    await context.addCookies([
      { name: "ta_token", value: "test-token", domain: "127.0.0.1", path: "/" },
      { name: "ta_role", value: "expert", domain: "127.0.0.1", path: "/" },
    ]);
    await page.goto("/queue");
    await expect(
      page.getByRole("heading", { name: "İnceleme Kuyruğu" }),
    ).toBeVisible();
  });
});
