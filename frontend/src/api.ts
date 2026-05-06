import type { MemorySummary, MemoryDetail, GraphData, ResolveRequest, ResolveResponse, StatsResponse, WanderResponse, ValidateResponse, CreateMemoryRequest, UpdateMemoryRequest } from './types'

const BASE = '/api'

async function fetcher<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    // Try to extract FastAPI detail field from the error response body
    let detail = `${res.status} ${res.statusText}`
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

export async function fetchMemories(): Promise<MemorySummary[]> {
  return fetcher<MemorySummary[]>(`${BASE}/memories`)
}

export async function fetchMemory(id: string): Promise<MemoryDetail> {
  return fetcher<MemoryDetail>(`${BASE}/memories/${encodeURIComponent(id)}`)
}

export async function fetchGraph(): Promise<GraphData> {
  return fetcher<GraphData>(`${BASE}/graph`)
}

export async function fetchResolve(req: ResolveRequest): Promise<ResolveResponse> {
  return fetcher<ResolveResponse>(`${BASE}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export async function fetchStats(): Promise<StatsResponse> {
  return fetcher<StatsResponse>(`${BASE}/stats`)
}

export async function fetchWander(mode: 'cool' | 'random' = 'cool'): Promise<WanderResponse> {
  return fetcher<WanderResponse>(`${BASE}/wander`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  })
}

export async function fetchValidate(): Promise<ValidateResponse> {
  return fetcher<ValidateResponse>(`${BASE}/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  })
}

export async function createMemory(req: CreateMemoryRequest): Promise<Record<string, unknown>> {
  return fetcher(`${BASE}/memories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export async function updateMemory(id: string, req: UpdateMemoryRequest): Promise<Record<string, unknown>> {
  return fetcher(`${BASE}/memories/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export interface DatasetInfo {
  name: string
  path: string
  memory_count: number
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
  intensity: number
  maturity: string
  status: string
  snippet: string
}

export interface SearchResultsResponse {
  results: SearchResultItem[]
  count: number
  query: string
}

export async function fetchSearch(query: string): Promise<SearchResultsResponse> {
  return fetcher<SearchResultsResponse>(`${BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
}
