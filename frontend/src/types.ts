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
