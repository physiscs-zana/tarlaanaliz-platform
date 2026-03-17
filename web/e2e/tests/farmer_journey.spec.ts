// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
import { expect, test } from "@playwright/test";

test.describe("farmer journey smoke", () => {
  test("home page links to register page", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /tarlanızın sağlığını/i }),
    ).toBeVisible();
    await page.getByRole("link", { name: "Hemen Üye Ol" }).first().click();
    await expect(page).toHaveURL(/\/register$/);
  });
});
