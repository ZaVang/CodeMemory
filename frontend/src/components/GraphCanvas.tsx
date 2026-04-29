import { useEffect, useRef, useState, useCallback } from 'react'
import cytoscape, { type Core } from 'cytoscape'
import dagre from 'dagre'
import type { GraphData, GraphNode, GraphEdge } from '../types'
import { fetchGraph } from '../api'

interface Props {
  searchText: string
  onNodeClick: (id: string) => void
  layoutMode: 'dagre' | 'force'
}

// LuxCart directory colors — border color for nodes
const DIRECTORY_COLORS: Record<string, string> = {
  'user/facts': '#1C1917',         // Charcoal — foundation
  'user/preferences': '#B8860B',   // Gold — personal values
  'user/observations': '#57534E',  // Warm Gray — neutral
  'user/investment': '#1E40AF',    // Info Blue — analytical
  'user/snapshots': '#A8A29E',     // Light Gray — frozen in time
  schemas: '#1C1917',
}

// LuxCart tints — light fill for nodes
const DIRECTORY_TINTS: Record<string, string> = {
  'user/facts': '#F5F5F4',
  'user/preferences': '#FDF6E8',   // warm gold
  'user/observations': '#F5F5F4',
  'user/investment': '#EEF2FA',    // cool blue
  'user/snapshots': '#F5F5F4',
  schemas: '#FDFBF5',
}

function shortId(id: string): string {
  const parts = id.split('/')
  return parts[parts.length - 1]
}

function getNodeColor(node: GraphNode): string {
  const dir = node.data.directory || node.data.group || ''
  for (const [key, color] of Object.entries(DIRECTORY_COLORS)) {
    if (dir === key || dir.startsWith(key)) return color
  }
  return '#57534E'
}

function getNodeTint(node: GraphNode): string {
  const dir = node.data.directory || node.data.group || ''
  for (const [key, color] of Object.entries(DIRECTORY_TINTS)) {
    if (dir === key || dir.startsWith(key)) return color
  }
  return '#FDFBF5'
}

function intensityToRadius(intensity: number): number {
  return Math.max(18, Math.min(50, 14 + intensity * 4))
}

export default function GraphCanvas({ searchText, onNodeClick, layoutMode }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)

  // Load graph data
  useEffect(() => {
    fetchGraph().then(setGraphData).catch(console.error)
  }, [])

  // Run dagre layout on node positions
  const runDagreLayout = useCallback((cy: Core) => {
    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: 'LR', nodesep: 60, ranksep: 120 })

    cy.nodes().forEach((node) => {
      const label = shortId(node.id()) || ''
      const r = intensityToRadius(node.data('intensity') || 5) * 2
      const w = Math.max(r * 3, label.length * 10 + 24)
      g.setNode(node.id(), { width: w, height: r * 1.8 })
    })

    cy.edges().forEach((edge) => {
      g.setEdge(edge.source().id(), edge.target().id())
    })

    dagre.layout(g)

    cy.nodes().forEach((node) => {
      const pos = g.node(node.id())
      if (pos) {
        node.position({ x: pos.x, y: pos.y })
      }
    })
  }, [])

  // Initialize cytoscape
  useEffect(() => {
    if (!graphData || !containerRef.current) return

    // Clean up previous instance
    if (cyRef.current) {
      cyRef.current.destroy()
    }

    const elements: cytoscape.ElementDefinition[] = [
      ...graphData.nodes.map((n) => ({
        data: { ...n.data },
        classes: n.data.type === 'schema' ? 'schema' : 'atom',
      })),
      ...graphData.edges.map((e) => ({
        data: { ...e.data, source: e.data.source, target: e.data.target },
        classes: e.data.strength,
      })),
    ]

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        // Node base style
        {
          selector: 'node',
          style: {
            'background-color': (el) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              return n ? getNodeTint(n) : '#FDFBF5'
            },
            'width': (el) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              return intensityToRadius(n?.data.intensity || 5) * 2
            },
            'height': (el) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              return intensityToRadius(n?.data.intensity || 5) * 2
            },
            'label': (el) => shortId(el.id()),
            'text-wrap': 'ellipsis',
            'text-max-width': '80px',
            'font-size': '11px',
            'font-family': 'Inter, sans-serif',
            'font-weight': '500',
            'color': '#1C1917',
            'text-valign': 'center',
            'text-halign': 'center',
            'border-width': 2,
            'border-color': (el) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              return n ? getNodeColor(n) : '#87867f'
            },
          },
        },
        // Schema nodes — diamond shape with dashed border
        {
          selector: 'node.schema',
          style: {
            'shape': 'diamond',
            'background-color': '#faf9f5',
            'border-style': 'dashed',
            'border-color': '#141413',
          },
        },
        // Intensity 10 — permanent memories get ring shadow
        {
          selector: 'node[?intensity]',
          style: {
            'border-width': (el) => el.data('intensity') === 10 ? 3 : 2,
          },
        },
        // Edge styles by strength
        {
          selector: 'edge.required',
          style: {
            'width': 2,
            'line-color': '#1C1917',
            'line-style': 'solid',
            'target-arrow-color': '#1C1917',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1,
            'opacity': 0.85,
          },
        },
        {
          selector: 'edge.recommended',
          style: {
            'width': 1.5,
            'line-color': '#57534E',
            'line-style': 'dashed',
            'target-arrow-color': '#57534E',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.9,
            'opacity': 0.65,
          },
        },
        {
          selector: 'edge.related',
          style: {
            'width': 1,
            'line-color': '#D4D4D8',
            'line-style': 'dotted',
            'target-arrow-color': '#D4D4D8',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.7,
            'opacity': 0.45,
          },
        },
        // Match highlight
        {
          selector: 'node.dimmed',
          style: { 'opacity': 0.1, 'color': '#D4D4D8' },
        },
        {
          selector: 'node.highlighted',
          style: { 'border-width': 3, 'border-color': '#B8860B', 'opacity': 1 },
        },
        // Selected node
        {
          selector: 'node:selected',
          style: {
            'border-width': 2,
            'border-color': '#B8860B',
            'overlay-opacity': 0,
          },
        },
      ],
      layout: { name: 'preset' },
      wheelSensitivity: 0.3,
    })

    cyRef.current = cy

    // Apply initial layout
    if (layoutMode === 'dagre') {
      runDagreLayout(cy)
    } else {
      cy.layout({ name: 'cose', animate: true, nodeRepulsion: () => 4000 }).run()
    }

    // Click handler
    cy.on('tap', 'node', (evt) => {
      const node = evt.target
      onNodeClick(node.id())
    })

    // Fit to view
    setTimeout(() => cy.fit(undefined, 50), 100)

    return () => {
      cy.destroy()
      cyRef.current = null
    }
  }, [graphData]) // Only re-init when graph data changes

  // Handle layout mode changes without full re-init
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    if (layoutMode === 'dagre') {
      runDagreLayout(cy)
      cy.fit(undefined, 50)
    } else {
      cy.layout({ name: 'cose', animate: true, nodeRepulsion: () => 4000 }).run()
    }
  }, [layoutMode, runDagreLayout])

  // Handle search filtering
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    if (!searchText.trim()) {
      cy.nodes().removeClass('highlighted dimmed')
      return
    }

    const q = searchText.toLowerCase()
    cy.nodes().forEach((node) => {
      const label = (node.data('label') as string || '').toLowerCase()
      const tags = (node.data('tags') as string[] || []).join(' ').toLowerCase()
      const id = (node.data('id') as string || '').toLowerCase()
      const dir = (node.data('directory') as string || '').toLowerCase()
      const maturity = (node.data('maturity') as string || '').toLowerCase()

      const match = label.includes(q) || tags.includes(q) || id.includes(q) || dir.includes(q) || maturity === q

      if (match) {
        node.removeClass('dimmed').addClass('highlighted')
      } else {
        node.removeClass('highlighted').addClass('dimmed')
      }
    })
  }, [searchText])

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: '#FFFBEB',
      }}
    />
  )
}
