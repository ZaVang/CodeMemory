import GraphCanvas, { type GraphCanvasHandle } from '../components/GraphCanvas'
import MemoryDetail from '../components/MemoryDetail'
import Legend from '../components/Legend'
import type { GraphData, ResolveResponse } from '../types'
import type { ReactNode, RefObject } from 'react'

interface Props {
  graphCanvasRef: RefObject<GraphCanvasHandle | null>
  datasetReady: boolean
  searchText: string
  selectedNode: string | null
  onNodeClick: (id: string) => void
  onNodeContextMenu: (id: string, position: { x: number; y: number }) => void
  resolveData: ResolveResponse | null
  resolveError: string | null
  isResolving: boolean
  refreshTrigger: number
  zoomLevel: number
  graphData: GraphData | null
  onGraphDataLoaded: (data: GraphData) => void
  activeTheme: 'light' | 'dark'
  onCreateMemory: () => void
  highlightedDirectory: string | null
  onHighlightDirectory: (directory: string | null) => void
  allNodesFit: boolean
  onCloseDetail: () => void
  onResolve: (id: string) => void
  onClearResolve: () => void
  onNavigateMemory: (id: string) => void
  copyTrigger: number
}

export default function GraphPage({
  graphCanvasRef,
  datasetReady,
  searchText,
  selectedNode,
  onNodeClick,
  onNodeContextMenu,
  resolveData,
  resolveError,
  isResolving,
  refreshTrigger,
  zoomLevel,
  graphData,
  onGraphDataLoaded,
  activeTheme,
  onCreateMemory,
  highlightedDirectory,
  onHighlightDirectory,
  allNodesFit,
  onCloseDetail,
  onResolve,
  onClearResolve,
  onNavigateMemory,
  copyTrigger,
}: Props) {
  const backlinks = (() => {
    if (!graphData || !selectedNode) return []
    const refs: { id: string; strength: string }[] = []
    for (const edge of graphData.edges) {
      if (edge.data.target === selectedNode) {
        refs.push({ id: edge.data.source, strength: edge.data.strength })
      }
    }
    const seen = new Set<string>()
    return refs.filter((r) => {
      if (seen.has(r.id)) return false
      seen.add(r.id)
      return true
    })
  })()

  return (
    <>
      <div
        style={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
        }}
      >
        <GraphCanvas
          ref={graphCanvasRef}
          enabled={datasetReady}
          searchText={searchText}
          onNodeClick={onNodeClick}
          onNodeContextMenu={onNodeContextMenu}
          resolveData={resolveData}
          isResolving={isResolving}
          refreshTrigger={refreshTrigger}
          zoomLevel={zoomLevel}
          onGraphDataLoaded={onGraphDataLoaded}
          activeTheme={activeTheme}
          onCreateMemory={onCreateMemory}
          highlightedDirectory={highlightedDirectory}
        />
        <Legend
          graphData={graphData}
          highlightedDirectory={highlightedDirectory}
          onHighlightDirectory={onHighlightDirectory}
        />

        {resolveError && (
          <FloatingNotice tone="error" position="right">
            {resolveError}
          </FloatingNotice>
        )}

        {isResolving && (
          <FloatingNotice tone="dark" position="left">
            Resolving...
          </FloatingNotice>
        )}

        {allNodesFit && !isResolving && resolveData && (
          <FloatingNotice tone="success" position="left">
            All {resolveData.nodes.length} nodes fit within budget
          </FloatingNotice>
        )}
      </div>

      <MemoryDetail
        memoryId={selectedNode}
        onClose={onCloseDetail}
        onResolve={onResolve}
        onClearResolve={onClearResolve}
        onNavigateMemory={onNavigateMemory}
        resolveData={resolveData}
        resolveError={resolveError}
        isResolving={isResolving}
        copyTrigger={copyTrigger}
        backlinks={backlinks}
      />
    </>
  )
}

function FloatingNotice({
  children,
  tone,
  position,
}: {
  children: ReactNode
  tone: 'error' | 'dark' | 'success'
  position: 'left' | 'right'
}) {
  const toneStyle = {
    error: {
      backgroundColor: 'var(--cm-error)',
      color: 'var(--cm-bg-surface)',
    },
    dark: {
      backgroundColor: 'var(--cm-text-primary)',
      color: 'var(--cm-text-inverse)',
    },
    success: {
      backgroundColor: 'var(--cm-success)',
      color: 'var(--cm-bg-surface)',
    },
  }[tone]

  return (
    <div
      style={{
        position: 'absolute',
        top: 16,
        [position]: 16,
        ...toneStyle,
        padding: '6px 14px',
        borderRadius: 2,
        fontSize: 12,
        fontFamily: 'Raleway, sans-serif',
        zIndex: 15,
        boxShadow: '0 2px 8px rgba(28,25,23,0.06)',
      }}
    >
      {children}
    </div>
  )
}
