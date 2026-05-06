/** A memory summary returned by GET /api/memories */
export interface MemorySummary {
  id: string
  type: string
  summary: string
  tags: string[]
  intensity: number
  maturity: string
  directory: string
  status: string
  version: number
}

/** Paginated response from GET /api/memories */
export interface PaginatedMemoriesResponse {
  memories: MemorySummary[]
  total: number
  offset: number
  limit: number
}

/** Full memory content returned by GET /api/memories/{id} */
export interface MemoryDetail {
  id: string
  body: string
  type: string
  summary: string
  status: string
  created: string
  updated?: string
  version: number
  tags: string[]
  intensity: number
  protected?: boolean
  imports?: Record<string, string[]>
  schema?: string
  maturity?: string
  evidence?: Record<string, unknown>
  source?: Record<string, unknown>
  [key: string]: unknown
}

/** A cytoscape graph node */
export interface GraphNode {
  data: {
    id: string
    label: string
    type: string
    intensity: number
    maturity: string
    group: string
    directory: string
    tags: string[]
    status: string
  }
}

/** A cytoscape graph edge */
export interface GraphEdge {
  data: {
    id: string
    source: string
    target: string
    strength: 'required' | 'recommended' | 'related'
  }
}

/** The full graph response */
export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

/** Request body for POST /api/resolve */
export interface ResolveRequest {
  id: string
  depth?: 'required' | 'recommended' | 'full'
  budget?: number
}

/** A single node in the resolve result */
export interface ResolveNode {
  id: string
  type: string
  trim: 'full' | 'summary' | 'skipped'
  index: number
  total: number
  body: string
}

/** Response from POST /api/resolve */
export interface ResolveResponse {
  target: string
  depth: string
  budget: number
  nodes: ResolveNode[]
  full_text: string
  notices: string[]
}

/** Stats endpoint response */
export interface StatsResponse {
  total: number
  maturity: Record<string, number>
  type: Record<string, number>
  status: Record<string, number>
  stale_count: number
  stale_ids: string[]
  tags: { tag: string; count: number }[]
}

/** Wander endpoint response */
export interface WanderResponse {
  id: string
  type: string
  summary: string
  tags: string[]
  intensity: number
  access_count: number
  status: string
  maturity: string
}

/** Validate endpoint response */
export interface ValidateResultItem {
  type: string
  message: string
}

export interface ValidateResponse {
  validated_count: number
  error_count: number
  warning_count: number
  errors: ValidateResultItem[]
  warnings: ValidateResultItem[]
}

/** A single import dependency with strength */
export interface ImportEntry {
  id: string
  strength: 'required' | 'recommended' | 'related'
}

/** Create memory request */
export interface CreateMemoryRequest {
  id: string
  summary?: string
  tags?: string[]
  intensity?: number
  body?: string
  type?: string
  schema?: string | null
  maturity?: string
  imports?: Record<string, string[]>
}

/** Update memory request */
export interface UpdateMemoryRequest {
  body?: string | null
  summary?: string | null
  tags?: string[] | null
  intensity?: number | null
  status?: string | null
  maturity?: string | null
  change_note?: string | null
  imports?: Record<string, string[]> | null
}
