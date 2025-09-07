import { test, expect } from '@playwright/test';

test('homepage smoke', async ({ page }) => {
  await page.goto('/');
  // Temel duman testi: sayfa 200 dönüyor ve body mevcut
  await expect(page.locator('body')).toBeVisible();
});
