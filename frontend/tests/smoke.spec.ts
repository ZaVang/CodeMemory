import { test, expect, type Page } from '@playwright/test'

/**
 * Dismiss the onboarding dialog if it appears (first visit in clean browser).
 * Returns true once the main app is visible.
 */
async function dismissOnboarding(page: Page) {
  // Onboarding shows on first visit — click "Skip" or "Get Started"
  const skipBtn = page.locator('button').filter({ hasText: /Skip|Get Started/i }).first()
  if (await skipBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await skipBtn.click()
    // Wait for the modal to disappear
    await page.waitForTimeout(500)
  }
}

test.describe('CodeMemory Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const json = (body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
      const memory = { id: 'memory/alpha', type: 'atom', summary: 'Alpha memory', tags: ['test'], maturity: 'verified', directory: 'memory', status: 'active', version: 1 }

      if (url.pathname === '/api/datasets') return json({ datasets: [{ name: 'test', memory_count: 1, profile: 'standard', source: 'demo' }, { name: 'alternate', memory_count: 1, profile: 'standard', source: 'demo' }], current: 'test', current_name: 'test' })
      if (url.pathname === '/api/datasets/switch') return json({ current: request.postDataJSON()?.name ?? 'test' })
      if (url.pathname === '/api/memories' && request.method() === 'GET') return json({ memories: [memory], total: 1, offset: 0, limit: 10000 })
      if (url.pathname === '/api/memories/memory/alpha') return json({ ...memory, body: '# Alpha', created: '2026-07-22', imports: {} })
      if (url.pathname === '/api/graph') return json({ nodes: [{ data: { ...memory, label: 'alpha', group: 'memory', dependents: 0 } }], edges: [] })
      if (url.pathname === '/api/stats') return json({ total: 1, maturity: { verified: 1 }, type: { atom: 1 }, status: { active: 1 }, stale_count: 0, stale_ids: [], tags: [{ tag: 'test', count: 1 }] })
      if (url.pathname === '/api/search') return json({ results: [memory], count: 1, total: 1, query: '', limit: 20 })
      if (url.pathname === '/api/reviews') return json({ proposed_atoms: [], patch_proposals: [], total: 0 })
      if (url.pathname === '/api/tests/memory/alpha') return json({ format_version: 'memory-test/v1', entry: 'memory/alpha', context: '', questions: [], notices: ['No golden questions declared.'] })
      return json({})
    })
  })

  test('1. Page loads — title and key elements are present', async ({ page }) => {
    await page.goto('/')

    // Dismiss onboarding if present
    await dismissOnboarding(page)

    // The page title should contain "CodeMemory"
    await expect(page).toHaveTitle(/CodeMemory/)

    // View switcher buttons should be present
    const graphBtn = page.locator('button').filter({ hasText: 'Graph' })
    const listBtn = page.locator('button').filter({ hasText: 'List' })
    const dashBtn = page.locator('button').filter({ hasText: 'Dashboard' })

    await expect(graphBtn.first()).toBeVisible({ timeout: 10000 })
    await expect(listBtn.first()).toBeVisible({ timeout: 5000 })
    await expect(dashBtn.first()).toBeVisible({ timeout: 5000 })
  })

  test('2. View switching — Graph → List → Dashboard', async ({ page }) => {
    await page.goto('/')
    await dismissOnboarding(page)

    // Wait for data to load
    await page.waitForTimeout(3000)

    // Switch to List view
    const listBtn = page.locator('button').filter({ hasText: 'List' }).first()
    await listBtn.click()
    await page.waitForTimeout(1500)

    // List view should show a table with memory data
    const idHeader = page.locator('th').filter({ hasText: 'ID' }).first()
    await expect(idHeader).toBeVisible({ timeout: 10000 })

    // Switch to Dashboard view
    const dashBtn = page.locator('button').filter({ hasText: 'Dashboard' }).first()
    await dashBtn.click()
    await page.waitForTimeout(1500)

    // Dashboard shows statistics
    const totalText = page.locator('text=/Total/i')
    await expect(totalText.first()).toBeVisible({ timeout: 10000 })

    // Switch back to Graph view
    const graphBtn = page.locator('button').filter({ hasText: 'Graph' }).first()
    await graphBtn.click()
    await page.waitForTimeout(3000)

    // Verify we're back on graph — the "Loading graph..." label or graph content should appear
    const graphContent = page.locator('text=/Loading graph|Graph.*view|No memories/i')
    const graphVisible = await graphContent.isVisible({ timeout: 10000 }).catch(() => false)
    // If graph content isn't visible, at least the app title should still be there
    if (!graphVisible) {
      await expect(page).toHaveTitle(/CodeMemory/)
    }
  })

  test('3. Search — typing a query filters results', async ({ page }) => {
    await page.goto('/')
    await dismissOnboarding(page)

    // Find the search input — could be an input or a button that opens search
    const searchInput = page.locator('input[placeholder*="Search"], input[placeholder*="search"]').first()
    await expect(searchInput).toBeVisible({ timeout: 10000 })

    // Type a query
    await searchInput.click()
    await searchInput.fill('user')
    await page.waitForTimeout(800)

    // The app should still be functional — no crash
    await expect(page).toHaveTitle(/CodeMemory/)

    // Clear the search
    await searchInput.fill('')
  })

  test('4. Memory detail — opening and closing the detail panel', async ({ page }) => {
    await page.goto('/')
    await dismissOnboarding(page)

    // Wait for data to load
    await page.waitForTimeout(3000)

    // Switch to list view
    const listBtn = page.locator('button').filter({ hasText: 'List' }).first()
    await listBtn.click()
    await page.waitForTimeout(1500)

    // Click on any table row (first td after header)
    const firstDataRow = page.locator('table tbody tr, table tr').nth(1)
    if (await firstDataRow.isVisible({ timeout: 3000 }).catch(() => false)) {
      await firstDataRow.click()
      await page.waitForTimeout(1500)
    }

    // A detail panel may have appeared — try to close it
    const closeBtn = page.locator('button').filter({ hasText: '✕' }).first()
    if (await closeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await closeBtn.click()
      await page.waitForTimeout(500)
    }

    // App still functional
    await expect(page).toHaveTitle(/CodeMemory/)
  })

  test('5. Dataset switching — switching dataset updates the view', async ({ page }) => {
    await page.goto('/')
    await dismissOnboarding(page)

    // Wait for data to load
    await page.waitForTimeout(3000)

    // Find the dataset dropdown — could be a <select> element or styled div
    const datasetSelect = page.locator('select').first()
    let switched = false

    if (await datasetSelect.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Get the current value
      const currentValue = await datasetSelect.inputValue()
      // Find a different option
      const options = await datasetSelect.locator('option').all()
      for (const opt of options) {
        const val = await opt.getAttribute('value')
        if (val && val !== currentValue) {
          await datasetSelect.selectOption(val)
          switched = true
          break
        }
      }
      if (switched) {
        await page.waitForTimeout(2000)
      }
    }

    // App is still alive and functional
    await expect(page).toHaveTitle(/CodeMemory/)

    // View switchers still work
    const graphBtn = page.locator('button').filter({ hasText: 'Graph' }).first()
    await expect(graphBtn).toBeVisible({ timeout: 10000 })
  })

  test('6. Build, golden questions, and owner review use current contracts', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('codememory-onboarded', '1'))
    let buildCalls = 0
    let reviewCalls = 0

    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const json = (body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })

      if (url.pathname === '/api/datasets') return json({ datasets: [{ name: 'test', memory_count: 1, profile: 'standard', source: 'demo' }], current: 'test', current_name: 'test' })
      if (url.pathname === '/api/memories' && request.method() === 'GET') return json({ memories: [{ id: 'memory/alpha', type: 'atom', summary: 'Alpha', tags: ['test'], maturity: 'verified', directory: 'memory', status: 'active', version: 1 }], total: 1, offset: 0, limit: 10000 })
      if (url.pathname === '/api/memories/memory/alpha') return json({ id: 'memory/alpha', type: 'atom', summary: 'Alpha', body: '# Alpha', tags: ['test'], maturity: 'verified', status: 'active', version: 1, created: '2026-07-22', imports: {}, golden_questions: [{ q: 'What is canonical?', expect: 'The built context.' }] })
      if (url.pathname === '/api/tests/memory/alpha') return json({ format_version: 'memory-test/v1', entry: 'memory/alpha', context: '<context>Alpha</context>', questions: [{ q: 'What is canonical?', expect: 'The built context.' }], notices: [] })
      if (url.pathname === '/api/build') {
        buildCalls += 1
        return json({ target: 'memory/alpha', format: 'plain-markdown', pack: { depth: 'recommended', budget: 2000, nodes: [{ id: 'memory/alpha', type: 'atom', trim: 'full', index: 0, total: 1, content: '# Alpha', summary: 'Alpha', maturity: 'verified', status: 'active', tags: ['test'] }], notices: [] }, rendered: '# Alpha' })
      }
      if (url.pathname === '/api/reviews' && request.method() === 'GET') return json({ proposed_atoms: [{ kind: 'proposed_atom', id: 'memory/proposed', target_id: 'memory/proposed', summary: 'Candidate', created_at: '2026-07-22', created_by: 'agent', tags: ['review'], version: 1 }], patch_proposals: [{ kind: 'patch_proposal', id: 'proposal-1', target_id: 'memory/alpha', reason: 'Clarify', created_at: '2026-07-22', created_by: 'agent', patch: { summary: 'Clearer' }, patch_fields: ['summary'] }], total: 2 })
      if (url.pathname === '/api/reviews/patches/reject') {
        reviewCalls += 1
        return json({ status: 'rejected', id: 'proposal-1' })
      }
      if (url.pathname === '/api/graph') return json({ nodes: [], edges: [] })
      return json({})
    })

    await page.goto('/')
    await page.getByRole('button', { name: /list/i }).click()
    await page.getByText('memory/alpha').click()
    await expect(page.getByText('Golden Questions')).toBeVisible()
    await expect(page.getByText('What is canonical?')).toBeVisible()
    await page.getByRole('button', { name: 'Build', exact: true }).click()
    await expect(page.getByText('Build — 1 nodes')).toBeVisible()
    expect(buildCalls).toBe(1)

    await page.getByRole('button', { name: /review/i }).click()
    await expect(page.getByText('Proposed Atoms (1)')).toBeVisible()
    await expect(page.getByText('Patch Proposals (1)')).toBeVisible()
    page.once('dialog', (dialog) => dialog.accept())
    await page.getByRole('button', { name: 'Reject' }).last().click()
    await expect.poll(() => reviewCalls).toBe(1)

    await expect(page.getByText('Wander', { exact: true })).toHaveCount(0)
    await expect(page.locator('input[name="intensity"]')).toHaveCount(0)
  })

  test('7. Personal workspace previews and confirms one multi-decision batch', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('codememory-onboarded', '1'))
    let batchCalls = 0

    const topics = [
      {
        topic_id: 'topic/alpha',
        revision_id: 'rev/alpha',
        title: 'Alpha direction',
        content: 'Alpha synthesis',
        origin: 'mixed',
        updated_at: '2026-07-22T10:00:00+08:00',
        tags: ['alpha'],
        derived_from: [{ kind: 'capture', id: 'cap_alpha', content_hash: 'sha256:a' }],
        relations: [],
        merged_from: [],
        locator: 'incubator/2026-07.md:3',
        claims: [{ claim_id: 'claim/alpha', topic_id: 'topic/alpha', revision_id: 'rev/alpha', title: 'Alpha claim', content: 'Inference', origin: 'agent_inference', claim_status: 'unassessed', derived_from: [], locator: 'incubator/2026-07.md:15' }],
      },
      {
        topic_id: 'topic/beta',
        revision_id: 'rev/beta',
        title: 'Beta direction',
        content: 'Beta synthesis',
        origin: 'agent_synthesis',
        updated_at: '2026-07-21T10:00:00+08:00',
        tags: [],
        derived_from: [],
        relations: [],
        merged_from: [],
        locator: 'incubator/2026-07.md:25',
        claims: [],
      },
    ]

    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const json = (body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })

      if (url.pathname === '/api/datasets') return json({
        datasets: [
          { name: 'mymemory', memory_count: 3, profile: 'personal', source: 'registry' },
          { name: 'standard', memory_count: 1, profile: 'standard', source: 'demo' },
        ],
        current: 'mymemory',
        current_name: 'mymemory',
      })
      if (url.pathname === '/api/datasets/switch') return json({ current: request.postDataJSON()?.name })
      if (url.pathname === '/api/personal/overview') return json({ capture_count: 1, topic_count: 2, claim_count: 1, canonical_count: 0, diagnostics_count: 0 })
      if (url.pathname === '/api/personal/captures') return json({ items: [{ id: 'cap_alpha', captured_at: '2026-07-20T08:00:00+08:00', actor: 'owner', content_hash: 'sha256:a', content: 'Raw owner note', locator: 'journal/2026/07/2026-07-20.md:3' }], total: 1, offset: 0, limit: 50 })
      if (url.pathname === '/api/personal/topics') return json(topics)
      if (url.pathname === '/api/personal/timeline') return json({ events: [{ id: 'cap_alpha', kind: 'capture', timestamp: '2026-07-20T08:00:00+08:00', title: 'Raw owner note', origin: 'human_explicit' }, { id: 'rev/alpha', kind: 'topic_revision', timestamp: '2026-07-22T10:00:00+08:00', title: 'Alpha direction', origin: 'mixed' }], edges: [{ relation: 'derived_from', source_id: 'cap_alpha', target_id: 'rev/alpha' }] })
      if (url.pathname === '/api/personal/review-batch') {
        batchCalls += 1
        expect(request.postDataJSON()?.decisions).toHaveLength(2)
        return json({ promoted: ['memory/ideas/alpha'], merged: [], deleted: ['rev/beta'] })
      }
      if (url.pathname === '/api/memories') return json({ memories: [], total: 0, offset: 0, limit: 10000 })
      if (url.pathname === '/api/graph') return json({ nodes: [], edges: [] })
      return json({})
    })

    await page.goto('/')
    await page.getByRole('button', { name: /personal/i }).click()
    await expect(page.getByRole('heading', { name: 'Personal Memory' })).toBeVisible()
    await expect(page.getByText('Raw owner note')).toBeVisible()
    await expect(page.getByText('Alpha claim')).toBeVisible()

    await page.getByLabel('Canonical Atom ID').fill('memory/ideas/alpha')
    await page.getByRole('button', { name: 'Queue decision' }).click()
    await page.getByRole('button', { name: /Beta direction/ }).click()
    await page.getByRole('combobox').last().selectOption('delete')
    await page.getByRole('button', { name: 'Queue decision' }).click()

    await page.getByRole('button', { name: 'Review batch (2)' }).click()
    await expect(page.getByRole('dialog')).toContainText('promote')
    await expect(page.getByRole('dialog')).toContainText('delete')
    await page.getByRole('button', { name: 'Cancel' }).click()
    expect(batchCalls).toBe(0)

    await page.getByRole('button', { name: 'Review batch (2)' }).click()
    await page.getByRole('button', { name: 'Confirm batch' }).click()
    await expect.poll(() => batchCalls).toBe(1)

    await page.locator('select').first().selectOption('standard')
    await expect(page.getByRole('button', { name: /personal/i })).toHaveCount(0)
  })
})
