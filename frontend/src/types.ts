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
  access_count?: number
  last_access?: string | null
  days_since_last_access?: number | null
  stability?: number
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
  days_since_last_access?: number | null
  stability?: number
  stability_source?: string | null  // R16-C2: "manual" if user-set, null/undefined = adaptive
  access_count?: number
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
    summary?: string
    dependents?: number
    days_since_last_access?: number | null
    stability?: number
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
  summary?: string
  maturity?: string
  status?: string
  tags?: string[]
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

/** A decay risk entry */
export interface DecayRiskEntry {
  id: string
  decay: number
  days_since_last_access: number
  stability: number
  access_count: number
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
  decay_risk?: DecayRiskEntry[]
}

/** Wander endpoint response */
export interface WanderResponse {
  id: string
  type: string
  summary: string
  tags: string[]
  intensity: number
  access_count: number
  last_access: string | null
  status: string
  maturity: string
  days_since_last_access?: number | null
  stability?: number
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
  stability?: number | null  // R16-C2: per-memory half-life slider
}
