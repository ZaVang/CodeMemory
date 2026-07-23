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

export interface PersonalOverview {
  capture_count: number
  topic_count: number
  claim_count: number
  canonical_count: number
  diagnostics_count: number
}

export interface PersonalCapture {
  id: string
  captured_at: string
  actor: string
  content_hash: string
  content: string
  locator: string
}

export interface PersonalCapturePage {
  items: PersonalCapture[]
  total: number
  offset: number
  limit: number
}

export interface PersonalClaim {
  claim_id: string
  topic_id: string
  revision_id: string
  title: string
  content: string
  origin: string
  claim_status: string
  confidence?: number | null
  derived_from: Record<string, unknown>[]
  locator: string
}

export interface PersonalTopic {
  topic_id: string
  revision_id: string
  title: string
  content: string
  origin: string
  created_at?: string | null
  updated_at?: string | null
  content_hash?: string | null
  tags: string[]
  derived_from: Record<string, unknown>[]
  relations: Record<string, unknown>[]
  merged_from: Record<string, unknown>[]
  claims: PersonalClaim[]
  locator: string
}

export interface PersonalTimelineEvent {
  id: string
  kind: 'capture' | 'topic_revision' | 'canonical_promotion'
  timestamp: string
  title: string
  origin?: string | null
  locator?: string | null
}

export interface PersonalTimelineEdge {
  relation: string
  source_id: string
  target_id: string
}

export interface PersonalTimeline {
  events: PersonalTimelineEvent[]
  edges: PersonalTimelineEdge[]
}

export interface PersonalReviewDecision {
  action: 'promote' | 'merge' | 'delete'
  revision_id: string
  atom_id?: string
  target_revision_id?: string
}

export interface PersonalReviewBatchResult {
  promoted: string[]
  merged: string[]
  deleted: string[]
}
