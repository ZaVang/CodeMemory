import { useState, useCallback, useRef, useEffect } from 'react'
import GraphCanvas from './components/GraphCanvas'
import MemoryDetail from './components/MemoryDetail'
import MemoryForm from './components/MemoryForm'
import Dashboard from './components/Dashboard'
import HelpPanel from './components/HelpPanel'
import SearchBar from './components/SearchBar'
import Legend from './components/Legend'
import { fetchResolve } from './api'
import type { ResolveResponse } from './types'

type LayoutMode = 'dagre' | 'force'
type ViewMode = 'graph' | 'dashboard'

const BUDGET_MIN = 200
const BUDGET_MAX = 5000
const BUDGET_DEFAULT = 2000

interface ContextMenuState {
  nodeId: string
  x: number
  y: number
}

export default function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('graph')
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [searchText, setSearchText] = useState('')
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('dagre')

  // Resolve state
  const [resolveData, setResolveData] = useState<ResolveResponse | null>(null)
  const [budget, setBudget] = useState(BUDGET_DEFAULT)
  const [isResolving, setIsResolving] = useState(false)
  const [resolveError, setResolveError] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Memory form state
  const [formMemoryId, setFormMemoryId] = useState<string | null>(null) // null = create mode
  const [showCreateForm, setShowCreateForm] = useState(false)

  // Help panel state
  const [showHelp, setShowHelp] = useState(false)

  // Context menu state
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)

  // Graph refresh trigger (increment to reload)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const doResolve = useCallback(
    (nodeId: string, budgetValue: number) => {
      setIsResolving(true)
      setResolveError(null)
      fetchResolve({ id: nodeId, depth: 'required', budget: budgetValue })
        .then((data) => {
          setResolveData(data)
          setIsResolving(false)
        })
        .catch((err) => {
          console.error('Resolve failed:', err)
          setResolveError(err.message || 'Resolve failed')
          setIsResolving(false)
        })
    },
    [],
  )

  // When budget slider changes, re-resolve if we have an active node
  const handleBudgetChange = useCallback(
    (newBudget: number) => {
      setBudget(newBudget)
      if (resolveData) {
        if (debounceRef.current) clearTimeout(debounceRef.current)
        debounceRef.current = setTimeout(() => {
          doResolve(resolveData.target, newBudget)
        }, 300)
      }
    },
    [resolveData, doResolve],
  )

  // Trigger resolve from MemoryDetail
  const handleResolve = useCallback(
    (nodeId: string) => {
      setSelectedNode(nodeId) // keep panel open
      doResolve(nodeId, budget)
    },
    [budget, doResolve],
  )

  // Clean up debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  // Close panel: clear resolve state too
  const handleClosePanel = useCallback(() => {
    setSelectedNode(null)
    setResolveData(null)
    setResolveError(null)
  }, [])

  // When a memory is selected from Dashboard, switch to graph view and select node
  const handleDashSelect = useCallback((id: string) => {
    setViewMode('graph')
    setSelectedNode(id)
  }, [])

  // Context menu from right-click on graph node
  const handleContextMenu = useCallback((nodeId: string, position: { x: number; y: number }) => {
    setContextMenu({ nodeId, x: position.x, y: position.y })
  }, [])

  const closeContextMenu = useCallback(() => {
    setContextMenu(null)
  }, [])

  // Handle graph refresh after create/edit/delete
  const handleMemoryChange = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1)
  }, [])

  // Open create form
  const handleOpenCreate = useCallback(() => {
    setFormMemoryId(null)
    setShowCreateForm(true)
  }, [])

  // Open edit form from context menu
  const handleEditFromContext = useCallback(() => {
    if (contextMenu) {
      setFormMemoryId(contextMenu.nodeId)
      setShowCreateForm(true)
      setContextMenu(null)
    }
  }, [contextMenu])

  // Open detail from context menu
  const handleDetailFromContext = useCallback(() => {
    if (contextMenu) {
      setSelectedNode(contextMenu.nodeId)
      setViewMode('graph')
      setContextMenu(null)
    }
  }, [contextMenu])

  // Close form
  const handleCloseForm = useCallback(() => {
    setFormMemoryId(null)
    setShowCreateForm(false)
  }, [])

  // Close context menu on any click outside
  useEffect(() => {
    if (!contextMenu) return
    const handler = () => closeContextMenu()
    window.addEventListener('click', handler)
    return () => window.removeEventListener('click', handler)
  }, [contextMenu, closeContextMenu])

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: '#FFFBEB',
        fontFamily: 'Raleway, sans-serif',
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: '16px 24px',
          backgroundColor: '#FFFBEB',
          borderBottom: '1px solid #E7E5E4',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          flexShrink: 0,
        }}
      >
        <h1
          style={{
            fontSize: 24,
            fontFamily: "'Cormorant Garamond', serif",
            fontWeight: 500,
            color: '#1C1917',
            margin: 0,
            whiteSpace: 'nowrap',
            letterSpacing: '0.01em',
          }}
        >
          CodeMemory
        </h1>

        {/* New Memory button */}
        <button
          onClick={handleOpenCreate}
          style={{
            padding: '6px 18px',
            backgroundColor: '#B8860B',
            color: '#FFFBEB',
            border: 'none',
            cursor: 'pointer',
            fontSize: 11,
            fontWeight: 600,
            fontFamily: 'Raleway, sans-serif',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            borderRadius: 2,
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          + New
        </button>

        {/* View switcher: Graph / Dashboard */}
        <div
          style={{
            display: 'flex',
            borderRadius: 2,
            border: '1px solid #D4D4D8',
            overflow: 'hidden',
            flexShrink: 0,
          }}
        >
          <button
            onClick={() => setViewMode('graph')}
            style={{
              padding: '6px 20px',
              border: 'none',
              cursor: 'pointer',
              fontSize: 11,
              fontFamily: 'Raleway, sans-serif',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              backgroundColor: viewMode === 'graph' ? '#1C1917' : 'transparent',
              color: viewMode === 'graph' ? '#FFFBEB' : '#57534E',
            }}
          >
            Graph
          </button>
          <button
            onClick={() => setViewMode('dashboard')}
            style={{
              padding: '6px 20px',
              border: 'none',
              cursor: 'pointer',
              fontSize: 11,
              fontFamily: 'Raleway, sans-serif',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              backgroundColor: viewMode === 'dashboard' ? '#1C1917' : 'transparent',
              color: viewMode === 'dashboard' ? '#FFFBEB' : '#57534E',
            }}
          >
            Dashboard
          </button>
        </div>

        <div style={{ flex: 1 }}>
          {viewMode === 'graph' && <SearchBar value={searchText} onChange={setSearchText} />}
        </div>

        {/* Token Budget + Layout toggle — only in graph view */}
        {viewMode === 'graph' && (
          <>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                flexShrink: 0,
              }}
            >
              <label
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  color: '#57534E',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  whiteSpace: 'nowrap',
                }}
              >
                Budget
              </label>
              <input
                type="range"
                min={BUDGET_MIN}
                max={BUDGET_MAX}
                step={100}
                value={budget}
                onChange={(e) => handleBudgetChange(Number(e.target.value))}
                style={{
                  width: 120,
                  accentColor: '#B8860B',
                  cursor: 'pointer',
                }}
              />
              <span
                style={{
                  fontSize: 12,
                  fontFamily: 'JetBrains Mono, monospace',
                  color: '#1C1917',
                  minWidth: 40,
                  textAlign: 'right',
                }}
              >
                {budget}
              </span>
            </div>

            {/* Layout toggle */}
            <div
              style={{
                display: 'flex',
                borderRadius: 2,
                border: '1px solid #D4D4D8',
                overflow: 'hidden',
                flexShrink: 0,
              }}
            >
              <button
                onClick={() => setLayoutMode('dagre')}
                style={{
                  padding: '6px 16px',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontFamily: 'Raleway, sans-serif',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  backgroundColor: layoutMode === 'dagre' ? '#1C1917' : 'transparent',
                  color: layoutMode === 'dagre' ? '#FFFBEB' : '#57534E',
                }}
              >
                Dagre
              </button>
              <button
                onClick={() => setLayoutMode('force')}
                style={{
                  padding: '6px 16px',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontFamily: 'Raleway, sans-serif',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  backgroundColor: layoutMode === 'force' ? '#1C1917' : 'transparent',
                  color: layoutMode === 'force' ? '#FFFBEB' : '#57534E',
                }}
              >
                Force
              </button>
            </div>
          </>
        )}

        {/* Help button */}
        <button
          onClick={() => setShowHelp(true)}
          title="Help"
          style={{
            width: 28,
            height: 28,
            borderRadius: 2,
            border: '1px solid #D4D4D8',
            backgroundColor: 'transparent',
            cursor: 'pointer',
            fontSize: 14,
            fontFamily: "'Cormorant Garamond', serif",
            color: '#57534E',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            marginLeft: 'auto',
          }}
        >
          ?
        </button>
      </header>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        {/* Graph view — always mounted (display toggled) to preserve cytoscape */}
        <div
          style={{
            flex: 1,
            position: 'relative',
            overflow: 'hidden',
            display: viewMode === 'graph' ? 'flex' : 'none',
          }}
        >
          <GraphCanvas
            searchText={searchText}
            onNodeClick={setSelectedNode}
            onNodeContextMenu={handleContextMenu}
            layoutMode={layoutMode}
            resolveData={resolveData}
            isResolving={isResolving}
            refreshTrigger={refreshTrigger}
          />
          <Legend />

          {/* Resolve error toast */}
          {resolveError && (
            <div
              style={{
                position: 'absolute',
                top: 16,
                right: 16,
                backgroundColor: '#991B1B',
                color: '#FFFFFF',
                padding: '8px 16px',
                borderRadius: 2,
                fontSize: 12,
                fontFamily: 'Raleway, sans-serif',
                zIndex: 15,
                boxShadow: '0 2px 8px rgba(28,25,23,0.06)',
              }}
            >
              {resolveError}
            </div>
          )}

          {/* Resolving indicator */}
          {isResolving && (
            <div
              style={{
                position: 'absolute',
                top: 16,
                left: 16,
                backgroundColor: '#1C1917',
                color: '#FFFBEB',
                padding: '6px 14px',
                borderRadius: 2,
                fontSize: 12,
                fontFamily: 'Raleway, sans-serif',
                zIndex: 15,
                boxShadow: '0 2px 8px rgba(28,25,23,0.06)',
              }}
            >
              Resolving...
            </div>
          )}
        </div>

        {/* Dashboard view — shown when viewMode === 'dashboard' */}
        {viewMode === 'dashboard' && (
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <Dashboard onSelectMemory={handleDashSelect} />
          </div>
        )}

        {/* Slide-in overlay panel (only in graph view) */}
        {viewMode === 'graph' && (
          <MemoryDetail
            memoryId={selectedNode}
            onClose={handleClosePanel}
            onResolve={handleResolve}
          />
        )}
      </div>

      {/* Memory form (create/edit) — fixed overlay */}
      {showCreateForm && (
        <MemoryForm
          memoryId={formMemoryId}
          onClose={handleCloseForm}
          onChange={handleMemoryChange}
        />
      )}

      {/* Help panel */}
      {showHelp && <HelpPanel onClose={() => setShowHelp(false)} />}

      {/* Context menu for right-click on graph nodes */}
      {contextMenu && (
        <>
          <div
            onClick={closeContextMenu}
            style={{ position: 'fixed', inset: 0, zIndex: 99 }}
          />
          <div
            style={{
              position: 'fixed',
              left: contextMenu.x,
              top: contextMenu.y,
              zIndex: 100,
              backgroundColor: '#FFFFFF',
              border: '1px solid #E7E5E4',
              borderRadius: 2,
              boxShadow: '0 4px 16px rgba(28,25,23,0.12)',
              padding: '4px 0',
              minWidth: 160,
            }}
          >
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                fontFamily: 'Raleway, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#A8A29E',
                padding: '6px 14px 4px',
              }}
            >
              {contextMenu.nodeId}
            </div>
            <ContextMenuItem label="View Details" onClick={handleDetailFromContext} />
            <ContextMenuItem label="Edit" onClick={handleEditFromContext} />
          </div>
        </>
      )}
    </div>
  )
}

function ContextMenuItem({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        padding: '8px 14px',
        border: 'none',
        background: 'none',
        cursor: 'pointer',
        fontSize: 13,
        fontFamily: 'Raleway, sans-serif',
        color: '#1C1917',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#F5F5F4'
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent'
      }}
    >
      {label}
    </button>
  )
}
