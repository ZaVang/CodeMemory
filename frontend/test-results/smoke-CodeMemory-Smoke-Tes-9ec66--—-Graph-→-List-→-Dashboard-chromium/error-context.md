# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> CodeMemory Smoke Tests >> 2. View switching — Graph → List → Dashboard
- Location: tests\smoke.spec.ts:37:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=/Total/i').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('text=/Total/i').first()

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - heading "CodeMemory" [level=1] [ref=e5]
    - button "Create Memory" [ref=e6] [cursor=pointer]
    - generic [ref=e7]:
      - button "Graph 1" [ref=e8] [cursor=pointer]:
        - text: Graph
        - generic [ref=e9]: "1"
      - button "List 2" [ref=e10] [cursor=pointer]:
        - text: List
        - generic [ref=e11]: "2"
      - button "Dashboard 3" [active] [ref=e12] [cursor=pointer]:
        - text: Dashboard
        - generic [ref=e13]: "3"
    - button "☽" [ref=e14] [cursor=pointer]
    - button "Export" [ref=e15] [cursor=pointer]
    - button "⚙" [ref=e16] [cursor=pointer]
    - button "Help" [ref=e17] [cursor=pointer]
  - generic [ref=e21]:
    - heading "Dashboard" [level=1] [ref=e22]
    - generic [ref=e23]:
      - button "Wander" [ref=e24] [cursor=pointer]
      - button "Validate" [ref=e25] [cursor=pointer]
      - button "Refresh" [ref=e26] [cursor=pointer]
      - button "Reindex" [ref=e27] [cursor=pointer]
```

# Test source

```ts
  1   | import { test, expect, type Page } from '@playwright/test'
  2   | 
  3   | /**
  4   |  * Dismiss the onboarding dialog if it appears (first visit in clean browser).
  5   |  * Returns true once the main app is visible.
  6   |  */
  7   | async function dismissOnboarding(page: Page) {
  8   |   // Onboarding shows on first visit — click "Skip" or "Get Started"
  9   |   const skipBtn = page.locator('button').filter({ hasText: /Skip|Get Started/i }).first()
  10  |   if (await skipBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
  11  |     await skipBtn.click()
  12  |     // Wait for the modal to disappear
  13  |     await page.waitForTimeout(500)
  14  |   }
  15  | }
  16  | 
  17  | test.describe('CodeMemory Smoke Tests', () => {
  18  |   test('1. Page loads — title and key elements are present', async ({ page }) => {
  19  |     await page.goto('/')
  20  | 
  21  |     // Dismiss onboarding if present
  22  |     await dismissOnboarding(page)
  23  | 
  24  |     // The page title should contain "CodeMemory"
  25  |     await expect(page).toHaveTitle(/CodeMemory/)
  26  | 
  27  |     // View switcher buttons should be present
  28  |     const graphBtn = page.locator('button').filter({ hasText: 'Graph' })
  29  |     const listBtn = page.locator('button').filter({ hasText: 'List' })
  30  |     const dashBtn = page.locator('button').filter({ hasText: 'Dashboard' })
  31  | 
  32  |     await expect(graphBtn.first()).toBeVisible({ timeout: 10000 })
  33  |     await expect(listBtn.first()).toBeVisible({ timeout: 5000 })
  34  |     await expect(dashBtn.first()).toBeVisible({ timeout: 5000 })
  35  |   })
  36  | 
  37  |   test('2. View switching — Graph → List → Dashboard', async ({ page }) => {
  38  |     await page.goto('/')
  39  |     await dismissOnboarding(page)
  40  | 
  41  |     // Wait for data to load
  42  |     await page.waitForTimeout(3000)
  43  | 
  44  |     // Switch to List view
  45  |     const listBtn = page.locator('button').filter({ hasText: 'List' }).first()
  46  |     await listBtn.click()
  47  |     await page.waitForTimeout(1500)
  48  | 
  49  |     // List view should show a table with memory data
  50  |     const idHeader = page.locator('th').filter({ hasText: 'ID' }).first()
  51  |     await expect(idHeader).toBeVisible({ timeout: 10000 })
  52  | 
  53  |     // Switch to Dashboard view
  54  |     const dashBtn = page.locator('button').filter({ hasText: 'Dashboard' }).first()
  55  |     await dashBtn.click()
  56  |     await page.waitForTimeout(1500)
  57  | 
  58  |     // Dashboard shows statistics
  59  |     const totalText = page.locator('text=/Total/i')
> 60  |     await expect(totalText.first()).toBeVisible({ timeout: 10000 })
      |                                     ^ Error: expect(locator).toBeVisible() failed
  61  | 
  62  |     // Switch back to Graph view
  63  |     const graphBtn = page.locator('button').filter({ hasText: 'Graph' }).first()
  64  |     await graphBtn.click()
  65  |     await page.waitForTimeout(3000)
  66  | 
  67  |     // Verify we're back on graph — the "Loading graph..." label or graph content should appear
  68  |     const graphContent = page.locator('text=/Loading graph|Graph.*view|No memories/i')
  69  |     const graphVisible = await graphContent.isVisible({ timeout: 10000 }).catch(() => false)
  70  |     // If graph content isn't visible, at least the app title should still be there
  71  |     if (!graphVisible) {
  72  |       await expect(page).toHaveTitle(/CodeMemory/)
  73  |     }
  74  |   })
  75  | 
  76  |   test('3. Search — typing a query filters results', async ({ page }) => {
  77  |     await page.goto('/')
  78  |     await dismissOnboarding(page)
  79  | 
  80  |     // Find the search input — could be an input or a button that opens search
  81  |     const searchInput = page.locator('input[placeholder*="Search"], input[placeholder*="search"]').first()
  82  |     await expect(searchInput).toBeVisible({ timeout: 10000 })
  83  | 
  84  |     // Type a query
  85  |     await searchInput.click()
  86  |     await searchInput.fill('user')
  87  |     await page.waitForTimeout(800)
  88  | 
  89  |     // The app should still be functional — no crash
  90  |     await expect(page).toHaveTitle(/CodeMemory/)
  91  | 
  92  |     // Clear the search
  93  |     await searchInput.fill('')
  94  |   })
  95  | 
  96  |   test('4. Memory detail — opening and closing the detail panel', async ({ page }) => {
  97  |     await page.goto('/')
  98  |     await dismissOnboarding(page)
  99  | 
  100 |     // Wait for data to load
  101 |     await page.waitForTimeout(3000)
  102 | 
  103 |     // Switch to list view
  104 |     const listBtn = page.locator('button').filter({ hasText: 'List' }).first()
  105 |     await listBtn.click()
  106 |     await page.waitForTimeout(1500)
  107 | 
  108 |     // Click on any table row (first td after header)
  109 |     const firstDataRow = page.locator('table tbody tr, table tr').nth(1)
  110 |     if (await firstDataRow.isVisible({ timeout: 3000 }).catch(() => false)) {
  111 |       await firstDataRow.click()
  112 |       await page.waitForTimeout(1500)
  113 |     }
  114 | 
  115 |     // A detail panel may have appeared — try to close it
  116 |     const closeBtn = page.locator('button').filter({ hasText: '✕' }).first()
  117 |     if (await closeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
  118 |       await closeBtn.click()
  119 |       await page.waitForTimeout(500)
  120 |     }
  121 | 
  122 |     // App still functional
  123 |     await expect(page).toHaveTitle(/CodeMemory/)
  124 |   })
  125 | 
  126 |   test('5. Dataset switching — switching dataset updates the view', async ({ page }) => {
  127 |     await page.goto('/')
  128 |     await dismissOnboarding(page)
  129 | 
  130 |     // Wait for data to load
  131 |     await page.waitForTimeout(3000)
  132 | 
  133 |     // Find the dataset dropdown — could be a <select> element or styled div
  134 |     const datasetSelect = page.locator('select').first()
  135 |     let switched = false
  136 | 
  137 |     if (await datasetSelect.isVisible({ timeout: 5000 }).catch(() => false)) {
  138 |       // Get the current value
  139 |       const currentValue = await datasetSelect.inputValue()
  140 |       // Find a different option
  141 |       const options = await datasetSelect.locator('option').all()
  142 |       for (const opt of options) {
  143 |         const val = await opt.getAttribute('value')
  144 |         if (val && val !== currentValue) {
  145 |           await datasetSelect.selectOption(val)
  146 |           switched = true
  147 |           break
  148 |         }
  149 |       }
  150 |       if (switched) {
  151 |         await page.waitForTimeout(2000)
  152 |       }
  153 |     }
  154 | 
  155 |     // App is still alive and functional
  156 |     await expect(page).toHaveTitle(/CodeMemory/)
  157 | 
  158 |     // View switchers still work
  159 |     const graphBtn = page.locator('button').filter({ hasText: 'Graph' }).first()
  160 |     await expect(graphBtn).toBeVisible({ timeout: 10000 })
```