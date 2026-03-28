import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'

test.describe('trace docs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
  })

  test('homepage loads', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible()
  })

  test('route /wiki/index /api/index /zh-CN /zh-TW /fa /fa-Latn loads', async ({ page }) => {
    await page.goto(BASE_URL + '/wiki/index /api/index /zh-CN /zh-TW /fa /fa-Latn')
    await expect(page.locator('body')).toBeVisible()
  })
})
