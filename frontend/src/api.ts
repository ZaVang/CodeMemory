import type { MemorySummary, PaginatedMemoriesResponse, MemoryDetail, GraphData, ResolveRequest, ResolveResponse, StatsResponse, ValidateResponse, CreateMemoryRequest, UpdateMemoryRequest, ReviewQueueResponse, TestBundle } from './types'

const BASE = '/api'

// Per-tab dataset tracker — set via setCurrentDataset() before requests.
// This replaces the backend global MEMORY_ROOT, enabling concurrent tabs
// to view different datasets independently.
// R17-CR1: Initialize empty to avoid sending a premature header on the
// first /api/datasets call. The server's response.current field sets the
// real initial value, which the App layer persists to localStorage.
let _currentDataset: string = ''

/** Inform the API layer which dataset to scope subsequent requests to. */
export function setCurrentDataset(name: string) {
  _currentDataset = name
}

function _emitNetworkError(message: string) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('codememory:network-error', { detail: message }))
  }
}

function _headers(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...extra }
  if (_currentDataset) {
    h['X-Codememory-Dataset'] = _currentDataset
  }
  return h
}

/** Map HTTP status codes to human-readable error messages (R11-UX7) */
function _humanReadableError(status: number): string {
  switch (status) {
    case 400: return 'Bad request — check your input and try again'
    case 404: return 'The requested resource was not found'
    case 422: return 'Validation failed — check your input and try again'
    case 500: return 'An unexpected server error occurred — try again or contact support'
    case 502: return 'Server is temporarily unavailable — try again in a moment'
    case 503: return 'Server is overloaded — try again shortly'
    default: return `Request failed (${status}) — try again`
  }
}

async function fetcher<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(url, { ...init, headers: _headers(init?.headers as Record<string, string> | undefined) })
  } catch {
    // Network failure (server unreachable, DNS, etc.)
    _emitNetworkError('Cannot reach server. Check your connection and try again.')
    throw new Error('Cannot reach server')
  }
  if (!res.ok) {
    // Try to extract FastAPI detail field from the error response body
    let detail = _humanReadableError(res.status)
    try {
      const body = await res.json()
      if (body && typeof body === 'object' && 'detail' in body) {
        const d = (body as { detail: unknown }).detail
        if (Array.isArray(d)) {
          // FastAPI validation errors: detail is an array of { msg, loc } objects
          detail = d.map((e: { msg?: string }) => e.msg || String(e)).join('; ')
        } else if (typeof d === 'string') {
          detail = d
        }
      }
    } catch {
      // Response body is not JSON; fall back to status text
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export async function fetchMemories(offset = 0, limit = 100): Promise<PaginatedMemoriesResponse> {
  return fetcher<PaginatedMemoriesResponse>(`${BASE}/memories?offset=${offset}&limit=${limit}`)
}

export async function fetchAllMemories(): Promise<MemorySummary[]> {
  // Fetch all memories for components that need the full list
  const res = await fetchMemories(0, 10000)
  return res.memories
}

/** Encode a memory ID for use in a URL path, preserving / separators. */
function encodePathId(id: string): string {
  return id.split('/').map(encodeURIComponent).join('/')
}

export async function fetchMemory(id: string): Promise<MemoryDetail> {
  return fetcher<MemoryDetail>(`${BASE}/memories/${encodePathId(id)}`)
}

export async function fetchGraph(): Promise<GraphData> {
  return fetcher<GraphData>(`${BASE}/graph`)
}

interface BuildApiResponse {
  target: string
  format: string
  pack: {
    depth: string
    budget: number
    nodes: Array<{
      id: string
      type: string
      trim: 'full' | 'summary' | 'skipped'
      index: number
      total: number
      content?: string | null
      summary?: string
      maturity?: string
      status?: string
      tags?: string[]
    }>
    notices: Array<{ type: string; message: string }>
  }
  rendered: string
}

export async function fetchBuild(req: ResolveRequest): Promise<ResolveResponse> {
  const response = await fetcher<BuildApiResponse>(`${BASE}/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...req, format: 'plain-markdown' }),
  })
  return {
    target: response.target,
    depth: response.pack.depth,
    budget: response.pack.budget,
    nodes: response.pack.nodes.map((node) => ({
      ...node,
      body: node.content ?? '',
      tags: node.tags ?? [],
    })),
    full_text: response.rendered,
    notices: response.pack.notices.map((notice) => `${notice.type}: ${notice.message}`),
  }
}

export async function fetchStats(): Promise<StatsResponse> {
  return fetcher<StatsResponse>(`${BASE}/stats`)
}

export async function fetchValidate(): Promise<ValidateResponse> {
  const raw = await fetcher<unknown>(`${BASE}/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  })
  if (Array.isArray(raw)) {
    return {
      validated_count: 0,
      error_count: Number(raw[0] ?? 0),
      warning_count: Number(raw[1] ?? 0),
      errors: [],
      warnings: [],
    }
  }

  const body = (raw ?? {}) as Partial<ValidateResponse>
  return {
    validated_count: Number(body.validated_count ?? 0),
    error_count: Number(body.error_count ?? 0),
    warning_count: Number(body.warning_count ?? 0),
    errors: Array.isArray(body.errors) ? body.errors : [],
    warnings: Array.isArray(body.warnings) ? body.warnings : [],
  }
}

export async function createMemory(req: CreateMemoryRequest): Promise<Record<string, unknown>> {
  return fetcher(`${BASE}/memories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export async function updateMemory(id: string, req: UpdateMemoryRequest): Promise<Record<string, unknown>> {
  return fetcher(`${BASE}/memories/${encodePathId(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export async function rehashMemory(id: string): Promise<{ id: string; summary_hash: string; stale: boolean }> {
  return fetcher(`${BASE}/memories/${encodePathId(id)}/rehash`, {
    method: 'POST',
  })
}

export interface DatasetInfo {
  name: string
  memory_count: number
  profile: 'standard' | 'personal'
  source: 'demo' | 'registry'
}

export interface DatasetsResponse {
  datasets: DatasetInfo[]
  current: string
  current_name: string
}

export async function fetchDatasets(): Promise<DatasetsResponse> {
  return fetcher<DatasetsResponse>(`${BASE}/datasets`)
}

export async function switchDataset(name: string): Promise<Record<string, unknown>> {
  return fetcher(`${BASE}/datasets/switch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export async function fetchReindex(): Promise<Record<string, unknown>> {
  return fetcher(`${BASE}/reindex`, { method: 'POST' })
}

export interface SearchResultItem {
  id: string
  summary: string
  type: string
  tags: string[]
  maturity: string
  status: string
  snippet: string
  match_quality?: 'exact' | 'fuzzy' | 'filter'
  match_score?: number
  match_fields?: string[]
  access_count?: number
}

export interface SearchResultsResponse {
  results: SearchResultItem[]
  count: number
  total: number
  query: string
  limit: number
}

export async function fetchSearch(query: string, limit = 20): Promise<SearchResultsResponse> {
  return fetcher<SearchResultsResponse>(`${BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit }),
  })
}

export async function fetchReviews(): Promise<ReviewQueueResponse> {
  return fetcher<ReviewQueueResponse>(`${BASE}/reviews`)
}

export async function applyReview(
  kind: 'atoms' | 'patches',
  action: 'merge' | 'reject',
  id: string,
): Promise<Record<string, unknown>> {
  return fetcher(`${BASE}/reviews/${kind}/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  })
}

export async function fetchTestBundle(id: string): Promise<TestBundle> {
  return fetcher<TestBundle>(`${BASE}/tests/${encodePathId(id)}`)
}

export async function fetchPersonalOverview(): Promise<import('./types').PersonalOverview> {
  return fetcher(`${BASE}/personal/overview`)
}

export async function fetchPersonalCaptures(offset = 0, limit = 50): Promise<import('./types').PersonalCapturePage> {
  return fetcher(`${BASE}/personal/captures?offset=${offset}&limit=${limit}`)
}

export async function fetchPersonalTopics(): Promise<import('./types').PersonalTopic[]> {
  return fetcher(`${BASE}/personal/topics`)
}

export async function fetchPersonalTimeline(topicId?: string): Promise<import('./types').PersonalTimeline> {
  const query = topicId ? `?topic_id=${encodeURIComponent(topicId)}` : ''
  return fetcher(`${BASE}/personal/timeline${query}`)
}

export async function applyPersonalReviewBatch(
  decisions: import('./types').PersonalReviewDecision[],
): Promise<import('./types').PersonalReviewBatchResult> {
  return fetcher(`${BASE}/personal/review-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ owner_confirmed: true, decisions }),
  })
}

/** Trigger a download of the memory .zip export. */
export function downloadExport(): void {
  const a = document.createElement('a')
  a.href = `${BASE}/export`
  a.download = 'codememory-export.zip'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
