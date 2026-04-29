import type { MemorySummary, MemoryDetail, GraphData } from './types'

const BASE = '/api'

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url)
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
