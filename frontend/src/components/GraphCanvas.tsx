import { useEffect, useRef, useState, useCallback, useImperativeHandle, forwardRef } from 'react'
import cytoscape, { type Core, type NodeSingular } from 'cytoscape'
import dagre from 'dagre'
import type { GraphData, GraphNode, ResolveResponse } from '../types'
import { fetchGraph } from '../api'
import { DIRECTORY_COLORS, DIRECTORY_TINTS, DIRECTORY_TINTS_DARK, DEFAULT_COLOR, DEFAULT_TINT, DEFAULT_TINT_DARK } from '../colors'
import EmptyState from './EmptyState'

interface Props {
  enabled?: boolean
  searchText: string
  onNodeClick: (id: string) => void
  onNodeContextMenu?: (id: string, position: { x: number; y: number }) => void
  resolveData: ResolveResponse | null
  isResolving: boolean
  refreshTrigger?: number  // increment to reload graph data
  zoomLevel?: number  // 0.15 to 2.0, default 0.5
  onGraphDataLoaded?: (data: GraphData) => void
  activeTheme?: 'light' | 'dark'
  onCreateMemory?: () => void
  highlightedDirectory?: string | null
}

export interface GraphCanvasHandle {
  exportPng: () => void
}

/** Read a CSS custom property value from the document root */
function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
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
  return DEFAULT_COLOR
}

function getNodeTint(node: GraphNode, isDark: boolean = false): string {
  const dir = node.data.directory || node.data.group || ''
  const palette = isDark ? DIRECTORY_TINTS_DARK : DIRECTORY_TINTS
  const fallback = isDark ? DEFAULT_TINT_DARK : DEFAULT_TINT
  for (const [key, tint] of Object.entries(palette)) {
    if (dir === key || dir.startsWith(key)) return tint
  }
  return fallback
}

function nodeRadius(dependents: number = 0): number {
  return Math.max(26, Math.min(44, 26 + Math.log2(dependents + 1) * 6))
}

const GraphCanvas = forwardRef<GraphCanvasHandle, Props>(function GraphCanvas({ enabled = true, searchText, onNodeClick, onNodeContextMenu, resolveData, isResolving, refreshTrigger, zoomLevel = 0.5, onGraphDataLoaded, activeTheme = 'light', onCreateMemory, highlightedDirectory }, ref) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  // R9-graph-viewport: preserve zoom/pan across theme-switch instance rebuilds
  const savedViewportRef = useRef<{ zoom: number; pan: { x: number; y: number } } | null>(null)
  // Tooltip state (R5-graph-node-tooltips + R18-P6 enrichment)
  const tooltipTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [tooltip, setTooltip] = useState<{
    summary: string
    dependents?: number
    x: number
    y: number
  } | null>(null)

  // Load graph data
  useEffect(() => {
    if (!enabled) {
      return
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    fetchGraph().then((data) => {
      setGraphData(data)
      if (onGraphDataLoaded) onGraphDataLoaded(data)
    }).catch((err) => {
      console.error('Graph load failed:', err)
    }).finally(() => setLoading(false))
  }, [refreshTrigger, enabled, onGraphDataLoaded])

  // Run dagre layout on node positions
  const runDagreLayout = useCallback((cy: Core) => {
    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: 'LR', nodesep: 60, ranksep: 120 })

    cy.nodes().forEach((node) => {
      const label = shortId(node.id()) || ''
      const r = nodeRadius(node.data('dependents') || 0) * 2
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

  // Track whether we're rebuilding for a theme change (same data) vs data change.
  // Saved viewport should only be restored for theme switches.
  const prevGraphDataRef = useRef<GraphData | null>(null)

  // Initialize cytoscape
  useEffect(() => {
    if (!graphData || !containerRef.current) return

    const isThemeSwitch = graphData === prevGraphDataRef.current
    prevGraphDataRef.current = graphData

    // Save viewport before destroying the old instance, but only when
    // rebuilding for a theme change (R9-graph-viewport).  On data changes
    // (dataset switch, reindex, etc.) the old viewport position is meaningless.
    if (cyRef.current) {
      if (isThemeSwitch) {
        try {
          savedViewportRef.current = {
            zoom: cyRef.current.zoom(),
            pan: { ...cyRef.current.pan() },
          }
        } catch { /* ignore errors from a potentially broken instance */ }
      }
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
            'background-color': (el: NodeSingular) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              const isDark = activeTheme === 'dark'
              return n ? getNodeTint(n, isDark) : (isDark ? DEFAULT_TINT_DARK : DEFAULT_TINT)
            },
            'width': (el: NodeSingular) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              return nodeRadius(n?.data.dependents) * 2
            },
            'height': (el: NodeSingular) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              return nodeRadius(n?.data.dependents) * 2
            },
            'label': (el: NodeSingular) => shortId(el.id()),
            'text-wrap': 'ellipsis',
            'text-max-width': '80px',
            'font-size': '12px',
            'font-family': 'Raleway, sans-serif',
            'font-weight': 500,
            'color': cssVar('--cm-text-primary'),
            'text-valign': 'center',
            'text-halign': 'center',
            'border-width': 2,
            'border-color': (el) => {
              const n = graphData.nodes.find((no) => no.data.id === el.id())
              return n ? getNodeColor(n) : cssVar('--cm-text-tertiary')
            },
          },
        },
        // Schema nodes — diamond shape with dashed border
        {
          selector: 'node.schema',
          style: {
            'shape': 'diamond',
            'background-color': cssVar('--cm-bg-subtle'),
            'border-style': 'dashed',
            'border-color': cssVar('--cm-text-primary'),
          },
        },
        // Edge styles by strength
        {
          selector: 'edge.required',
          style: {
            'width': 2,
            'line-color': cssVar('--cm-text-primary'),
            'line-style': 'solid',
            'target-arrow-color': cssVar('--cm-text-primary'),
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1,
            'opacity': 0.85,
          },
        },
        {
          selector: 'edge.recommended',
          style: {
            'width': 1.5,
            'line-color': cssVar('--cm-text-secondary'),
            'line-style': 'dashed',
            'target-arrow-color': cssVar('--cm-text-secondary'),
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.9,
            'opacity': 0.65,
          },
        },
        {
          selector: 'edge.related',
          style: {
            'width': 1,
            'line-color': cssVar('--cm-border-cool'),
            'line-style': 'dotted',
            'target-arrow-color': cssVar('--cm-border-cool'),
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.7,
            'opacity': 0.45,
          },
        },
        // Match highlight
        {
          selector: 'node.dimmed',
          style: { 'opacity': 0.1, 'color': cssVar('--cm-text-tertiary') },
        },
        {
          selector: 'node.highlighted',
          style: { 'border-width': 3, 'border-color': cssVar('--cm-accent'), 'opacity': 1 },
        },
        // R18-P4: Legend directory click-highlight
        {
          selector: 'node.dir-dimmed',
          style: { 'opacity': 0.2, 'color': cssVar('--cm-text-tertiary') },
        },
        {
          selector: 'node.dir-bright',
          style: { 'border-width': 3, 'border-color': cssVar('--cm-accent'), 'opacity': 1 },
        },
        // Selected node
        {
          selector: 'node:selected',
          style: {
            'border-width': 2,
            'border-color': cssVar('--cm-accent'),
            'overlay-opacity': 0,
          },
        },
        // Resolve: off-path nodes and edges (not in dependency tree)
        {
          selector: 'node.off-path',
          style: { 'opacity': 0.06, 'text-opacity': 0 },
        },
        {
          selector: 'edge.off-path',
          style: { 'opacity': 0.04 },
        },
        // Resolve highlight — gold glow during topological animation
        {
          selector: 'node.resolve-highlight',
          style: {
            'border-width': 3,
            'border-color': cssVar('--cm-accent'),
            'background-color': cssVar('--cm-bg-hover'),
            'opacity': 1,
            'z-index': 10,
          },
        },
        // Trim: summary — semi-transparent, dashed border, italic, 12px min
        {
          selector: 'node.trim-summary',
          style: {
            'opacity': 0.65,
            'border-style': 'dashed',
            'border-width': 1.5,
            'width': (el: NodeSingular) => nodeRadius(el.data('dependents') || 0) * 1.3,
            'height': (el: NodeSingular) => nodeRadius(el.data('dependents') || 0) * 1.3,
            'font-size': '12px',
            'font-style': 'italic',
          },
        },
        // Trim: skipped — dimmer, dashed, 12px min
        {
          selector: 'node.trim-skipped',
          style: {
            'opacity': 0.4,
            'border-style': 'dashed',
            'border-width': 1,
            'width': (el: NodeSingular) => nodeRadius(el.data('dependents') || 0) * 1.1,
            'height': (el: NodeSingular) => nodeRadius(el.data('dependents') || 0) * 1.1,
            'font-size': '12px',
            'color': cssVar('--cm-text-tertiary'),
          },
        },
      ],
      layout: { name: 'preset' },
      wheelSensitivity: 0.3,
    })

    cyRef.current = cy

    // Apply dagre layout (the only layout)
    runDagreLayout(cy)

    // Click handler
    cy.on('tap', 'node', (evt) => {
      const node = evt.target
      onNodeClick(node.id())
    })

    // Right-click context menu
    if (onNodeContextMenu) {
      cy.on('cxttap', 'node', (evt) => {
        const node = evt.target
        onNodeContextMenu(node.id(), {
          x: evt.originalEvent.clientX,
          y: evt.originalEvent.clientY,
        })
      })
    }

    // Graph node tooltip: summary plus direct dependent count.
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target
      const id = node.id()
      const nd = graphData.nodes.find((n) => n.data.id === id)
      const summary = nd?.data?.summary || ''
      const dependents = nd?.data?.dependents

      if (tooltipTimerRef.current) clearTimeout(tooltipTimerRef.current)
      tooltipTimerRef.current = setTimeout(() => {
        setTooltip({
          summary: summary || id,
          dependents,
          x: evt.originalEvent.clientX,
          y: evt.originalEvent.clientY,
        })
      }, 300)
    })

    cy.on('mouseout', 'node', () => {
      if (tooltipTimerRef.current) {
        clearTimeout(tooltipTimerRef.current)
        tooltipTimerRef.current = null
      }
      setTooltip(null)
    })

    // Clear tooltip on graph pan/zoom
    cy.on('pan zoom', () => setTooltip(null))

    // Always fit and center after layout so the graph is never blank.
    // On theme switches, restore the saved viewport AFTER the fit so the user
    // sees the same region they were looking at before.
    const saved = savedViewportRef.current
    setTimeout(() => {
      cy.fit(undefined, 32) // 32px padding so nodes don't touch viewport edges
      cy.center()
      cy.zoom(zoomLevel)
      if (saved && saved.zoom > 0) {
        cy.zoom(saved.zoom)
        cy.pan(saved.pan)
        savedViewportRef.current = null
      }
    }, 250)

    return () => {
      // Only save viewport for theme switches — stale viewport positions
      // from a different dataset's graph produce blank screens.
      if (isThemeSwitch) {
        try {
          savedViewportRef.current = {
            zoom: cy.zoom(),
            pan: { ...cy.pan() },
          }
        } catch { /* ignore */ }
      } else {
        savedViewportRef.current = null
      }
      cy.destroy()
      cyRef.current = null
    }
  // Recreating Cytoscape is intentionally scoped to dataset/theme changes;
  // interaction callbacks read current props through the owning render.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphData, activeTheme])

  // Handle zoom level changes
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.stop()
    cy.zoom(zoomLevel)
    cy.center()
  }, [zoomLevel])

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

  // R18-P4: Handle Legend directory click-highlight
  useEffect(() => {
    const cy = cyRef.current
    if (!cy || !graphData) return

    if (!highlightedDirectory) {
      // Restore all nodes to normal
      cy.batch(() => {
        cy.nodes().removeClass('dir-dimmed dir-bright')
      })
      return
    }

    // Find nodes in the highlighted directory
    const dirNodes = graphData.nodes.filter(
      (n) => (n.data.directory || n.data.group || '') === highlightedDirectory
    )
    const dirIdSet = new Set(dirNodes.map((n) => n.data.id))

    cy.batch(() => {
      cy.nodes().forEach((node) => {
        if (dirIdSet.has(node.id())) {
          node.removeClass('dir-dimmed').addClass('dir-bright')
        } else {
          node.removeClass('dir-bright').addClass('dir-dimmed')
        }
      })
    })
  }, [highlightedDirectory, graphData])

  // Animation timer ref (for cleanup)
  const animTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Track previous resolve state for clear animation detection
  const prevResolveDataRef = useRef<ResolveResponse | null>(null)

  // Handle resolve: animate topology then apply trim (PL3-3)
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    // Clean up any running animation timer
    if (animTimerRef.current) {
      clearTimeout(animTimerRef.current)
      animTimerRef.current = null
    }

    // Detect clear-resolve transition (had data → now null) for smooth animation
    const isClearing = prevResolveDataRef.current && !resolveData && !isResolving
    prevResolveDataRef.current = resolveData

    if (isClearing) {
      // R5-resolve-clear-animation: animate nodes back to normal over ~300ms
      const trimmedNodes = cy.nodes('.trim-summary, .trim-skipped, .off-path')
      const trimmedEdges = cy.edges('.off-path')

      trimmedNodes.stop().animate(
        {
          style: { opacity: 1 },
        },
        {
          duration: 300,
          easing: 'ease-out',
          complete: () => {
            cy.nodes().removeClass('resolve-highlight trim-summary trim-skipped off-path')
            cy.edges().removeClass('off-path')
          },
        },
      )

      trimmedEdges.animate(
        { style: { opacity: 1 } },
        { duration: 300, easing: 'ease-out' },
      )

      return
    }

    // Clear previous resolve classes
    cy.nodes().removeClass('resolve-highlight trim-summary trim-skipped off-path')
    cy.edges().removeClass('off-path')

    if (!resolveData || isResolving) {
      return
    }

    // Build path ID set + trim map
    const pathIds = new Set(resolveData.nodes.map((n) => n.id))
    const trimMap = new Map<string, 'full' | 'summary' | 'skipped'>()
    for (const n of resolveData.nodes) {
      trimMap.set(n.id, n.trim)
    }

    // Immediately dim off-path nodes and edges
    cy.nodes().forEach((node) => {
      if (!pathIds.has(node.id())) {
        node.addClass('off-path')
      }
    })
    cy.edges().forEach((edge) => {
      if (!pathIds.has(edge.source().id()) || !pathIds.has(edge.target().id())) {
        edge.addClass('off-path')
      }
    })

    // Sort resolve nodes by topological index for animation
    const sortedNodes = [...resolveData.nodes].sort((a, b) => a.index - b.index)
    const cyNodes = sortedNodes
      .map((n) => cy.getElementById(n.id))
      .filter((node) => node.length > 0)

    if (cyNodes.length === 0) return

    const STEP_MS = 300

    // Animate: highlight nodes sequentially in topological order
    cyNodes.forEach((node, i) => {
      animTimerRef.current = setTimeout(() => {
        node.addClass('resolve-highlight')
        // After pulse, apply trim style
        setTimeout(() => {
          node.removeClass('resolve-highlight')
          const nodeId = node.id()
          const trim = trimMap.get(nodeId)
          if (trim === 'summary') node.addClass('trim-summary')
          else if (trim === 'skipped') node.addClass('trim-skipped')
        }, STEP_MS)
      }, i * STEP_MS)
    })

    return () => {
      if (animTimerRef.current) {
        clearTimeout(animTimerRef.current)
        animTimerRef.current = null
      }
    }
  }, [resolveData, isResolving])

  // R7-export: Export graph as PNG
  const handleExportPng = useCallback(() => {
    const cy = cyRef.current
    if (!cy) return
    const bgColor = cssVar('--cm-bg-primary')
    const pngDataUrl = cy.png({ full: true, scale: 2, bg: bgColor })
    const a = document.createElement('a')
    a.href = pngDataUrl
    a.download = 'codememory-graph.png'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }, [])

  // Expose exportPng to parent via ref
  useImperativeHandle(ref, () => ({ exportPng: handleExportPng }), [handleExportPng])

  // R10-loading-skeletons: show skeleton while graph data loads
  if (loading && !graphData) {
    return <GraphSkeleton />
  }

  // R7-N5: Unified EmptyState — shown when no memories exist
  if (graphData && graphData.nodes.length === 0) {
    return (
      <div style={{ width: '100%', height: '100%', backgroundColor: 'var(--cm-bg-primary)' }}>
        <EmptyState
          icon="o"
          title="No memories yet"
          description="Create your first memory to get started."
          actions={onCreateMemory ? [{ label: 'Create Memory', onClick: onCreateMemory, variant: 'primary' }] : undefined}
        />
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: 'var(--cm-bg-primary)',
        }}
      />
      {/* R7-export: Export PNG button */}
      {graphData && graphData.nodes.length > 0 && (
        <button
          onClick={handleExportPng}
          title="Export graph as PNG"
          style={{
            position: 'absolute',
            bottom: 14,
            right: 14,
            padding: '5px 12px',
            border: '1px solid var(--cm-border-cool)',
            background: 'var(--cm-bg-surface)',
            color: 'var(--cm-text-secondary)',
            cursor: 'pointer',
            fontSize: 12,
            fontWeight: 600,
            fontFamily: 'Raleway, sans-serif',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            borderRadius: 2,
            zIndex: 5,
            opacity: 0.7,
          }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.opacity = '1' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.opacity = '0.7' }}
        >
          PNG
        </button>
      )}

      {/* R5-graph-node-tooltips + R18-P6: enriched tip with R-probability and dependents */}
      {tooltip && (
        <div
          style={{
            position: 'fixed',
            left: tooltip.x + 12,
            top: tooltip.y + 12,
            backgroundColor: 'var(--cm-text-primary)',
            color: 'var(--cm-bg-primary)',
            padding: '8px 12px',
            borderRadius: 2,
            fontSize: 12,
            fontFamily: 'Raleway, sans-serif',
            maxWidth: 300,
            lineHeight: 1.5,
            zIndex: 25,
            pointerEvents: 'none',
            boxShadow: '0 2px 8px rgba(28,25,23,0.15)',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>{tooltip.summary}</div>
          {tooltip.dependents != null && (
            <div style={{
              display: 'flex',
              gap: 12,
              marginTop: 4,
              fontSize: 11,
              opacity: 0.85,
            }}>
              {tooltip.dependents != null && (
                <span>Deps: {tooltip.dependents}</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
})

// ── R10-loading-skeletons: Graph skeleton ─────────────────────────────

function GraphSkeleton() {
  // Placeholder node circles arranged in a DAG-like layout
  const nodePositions = [
    { x: '50%', y: '20%', r: 24 },
    { x: '30%', y: '38%', r: 18 },
    { x: '70%', y: '38%', r: 18 },
    { x: '20%', y: '56%', r: 20 },
    { x: '45%', y: '56%', r: 22 },
    { x: '65%', y: '56%', r: 16 },
    { x: '80%', y: '56%', r: 18 },
    { x: '30%', y: '74%', r: 20 },
    { x: '55%', y: '74%', r: 18 },
    { x: '70%', y: '74%', r: 20 },
  ]

  // Edge lines connecting some node pairs
  const edges = [
    { x1: '50%', y1: '20%', x2: '30%', y2: '38%' },
    { x1: '50%', y1: '20%', x2: '70%', y2: '38%' },
    { x1: '30%', y1: '38%', x2: '20%', y2: '56%' },
    { x1: '30%', y1: '38%', x2: '45%', y2: '56%' },
    { x1: '70%', y1: '38%', x2: '65%', y2: '56%' },
    { x1: '70%', y1: '38%', x2: '80%', y2: '56%' },
    { x1: '20%', y1: '56%', x2: '30%', y2: '74%' },
    { x1: '45%', y1: '56%', x2: '55%', y2: '74%' },
    { x1: '65%', y1: '56%', x2: '55%', y2: '74%' },
    { x1: '80%', y1: '56%', x2: '70%', y2: '74%' },
  ]

  return (
    <div style={{
      width: '100%',
      height: '100%',
      backgroundColor: 'var(--cm-bg-primary)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Edge placeholder lines */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
        <defs>
          <linearGradient id="edge-shimmer">
            <stop offset="0%" stopColor="var(--cm-border)" />
            <stop offset="50%" stopColor="var(--cm-border-cool)" />
            <stop offset="100%" stopColor="var(--cm-border)" />
            <animateTransform
              attributeName="gradientTransform"
              type="translate"
              from="-2 0"
              to="2 0"
              dur="1.5s"
              repeatCount="indefinite"
            />
          </linearGradient>
        </defs>
        {edges.map((e, i) => (
          <line
            key={`edge-${i}`}
            x1={e.x1}
            y1={e.y1}
            x2={e.x2}
            y2={e.y2}
            stroke="var(--cm-border)"
            strokeWidth={1.5}
            opacity={0.5}
          />
        ))}
      </svg>

      {/* Placeholder node circles */}
      {nodePositions.map((n, i) => (
        <div
          key={`node-${i}`}
          className="skeleton-shimmer"
          style={{
            position: 'absolute',
            left: `calc(${n.x} - ${n.r}px)`,
            top: `calc(${n.y} - ${n.r}px)`,
            width: n.r * 2,
            height: n.r * 2,
            borderRadius: '50%',
          }}
        />
      ))}

      {/* Center label */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        fontSize: 12,
        fontFamily: 'Raleway, sans-serif',
        color: 'var(--cm-text-tertiary)',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      }}>
        Loading graph...
      </div>
    </div>
  )
}

export default GraphCanvas
