import type { MemorySummary, MemoryDetail, GraphData, ResolveRequest, ResolveResponse, StatsResponse, WanderResponse, ValidateResponse, CreateMemoryRequest, UpdateMemoryRequest } from './types'

const BASE = '/api'

async function fetcher<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
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

export async function fetchWander(): Promise<WanderResponse> {
  return fetcher<WanderResponse>(`${BASE}/wander`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
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
