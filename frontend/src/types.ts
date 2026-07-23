/** A memory summary returned by GET /api/memories */
export interface MemorySummary {
  id: string
  type: string
  summary: string
  tags: string[]
  maturity: string
  directory: string
  status: string
  version: number
  access_count?: number
  last_access?: string | null
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
  protected?: boolean
  imports?: Record<string, string[]>
  schema?: string
  maturity?: string
  evidence?: Record<string, unknown>
  source?: Record<string, unknown>
  access_count?: number
  golden_questions?: GoldenQuestion[]
  [key: string]: unknown
}

/** A cytoscape graph node */
export interface GraphNode {
  data: {
    id: string
    label: string
    type: string
    maturity: string
    group: string
    directory: string
    tags: string[]
    status: string
    summary?: string
    dependents?: number
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

/** Request body for the primary POST /api/build endpoint. */
export interface ResolveRequest {
  id: string
  depth?: 'required' | 'recommended' | 'full'
  budget?: number
}

/** A single node in the normalized build result used by the graph UI. */
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

/** Normalized response derived from the structured POST /api/build payload. */
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
  body?: string
  type?: string
  schema?: string | null
  maturity?: string
  imports?: Record<string, string[]>
  propose?: boolean
}

/** Update memory request */
export interface UpdateMemoryRequest {
  body?: string | null
  summary?: string | null
  tags?: string[] | null
  status?: string | null
  maturity?: string | null
  change_note?: string | null
  imports?: Record<string, string[]> | null
}

export interface GoldenQuestion {
  q: string
  expect?: string | null
}

export interface TestBundle {
  format_version: string
  entry: string
  context: string
  questions: GoldenQuestion[]
  notices: string[]
}

export interface ProposedAtomReview {
  kind: 'proposed_atom'
  id: string
  target_id: string
  summary: string
  created_at: string
  created_by: string
  tags: string[]
  version: number
}

export interface PatchProposalReview {
  kind: 'patch_proposal'
  id: string
  target_id: string
  reason: string
  created_at: string
  created_by: string
  patch: Record<string, unknown>
  patch_fields: string[]
}

export interface ReviewQueueResponse {
  proposed_atoms: ProposedAtomReview[]
  patch_proposals: PatchProposalReview[]
  total: number
}
