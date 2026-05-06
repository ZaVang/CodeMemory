import { useState, useCallback, useRef, useEffect } from 'react'
import GraphCanvas from './components/GraphCanvas'
import MemoryDetail from './components/MemoryDetail'
import MemoryForm from './components/MemoryForm'
import Dashboard from './components/Dashboard'
import MemoryList from './components/MemoryList'
import HelpPanel from './components/HelpPanel'
import SearchBar from './components/SearchBar'
import Legend from './components/Legend'
import Onboarding from './components/Onboarding'
import { fetchResolve, updateMemory, createMemory, fetchGraph, fetchDatasets, switchDataset, fetchMemory } from './api'
import type { ResolveResponse, GraphData } from './types'
import type { DatasetInfo } from './api'

const ONBOARDING_KEY = 'codememory-onboarded'

type ViewMode = 'graph' | 'list' | 'dashboard'

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

  // List view filter state (R5-clickable-dashboard)
  const [listFilter, setListFilter] = useState('')

  // Zoom level for the graph view
  const [zoomLevel, setZoomLevel] = useState(0.5)

  // Resolve state
  const [resolveData, setResolveData] = useState<ResolveResponse | null>(null)
  const [budget, setBudget] = useState(BUDGET_DEFAULT)
  const [isResolving, setIsResolving] = useState(false)
  const [resolveError, setResolveError] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Memory form state
  const [formMemoryId, setFormMemoryId] = useState<string | null>(null) // null = create mode
  const [showCreateForm, setShowCreateForm] = useState(false)

  // Onboarding state — check localStorage on first render
  const [showOnboarding, setShowOnboarding] = useState(() => {
    return localStorage.getItem(ONBOARDING_KEY) !== '1'
  })

  // Help panel state
  const [showHelp, setShowHelp] = useState(false)

  // Context menu state
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)

  // Undo state
  interface UndoEntry {
    type: 'create' | 'update' | 'archive'
    memoryId: string
    previousState?: Record<string, unknown>  // for updates: the pre-update memory data
  }
  const [undoEntry, setUndoEntry] = useState<UndoEntry | null>(null)
  const undoToastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showUndo = useCallback((entry: UndoEntry) => {
    setUndoEntry(entry)
    if (undoToastTimerRef.current) clearTimeout(undoToastTimerRef.current)
    undoToastTimerRef.current = setTimeout(() => setUndoEntry(null), 5000)
  }, [])

  const handleUndo = useCallback(async () => {
    if (!undoEntry) return
    const entry = undoEntry
    setUndoEntry(null)
    if (undoToastTimerRef.current) {
      clearTimeout(undoToastTimerRef.current)
      undoToastTimerRef.current = null
    }

    try {
      if (entry.type === 'create') {
        // Undo create: archive the newly created memory
        await updateMemory(entry.memoryId, {
          status: 'archived',
          change_note: 'Undo create',
        })
      } else if (entry.type === 'update' && entry.previousState) {
        // Undo edit: restore previous state
        const prev = entry.previousState
        await updateMemory(entry.memoryId, {
          body: (prev.body as string) ?? undefined,
          summary: (prev.summary as string) ?? undefined,
          tags: (prev.tags as string[]) ?? undefined,
          intensity: (prev.intensity as number) ?? undefined,
          status: (prev.status as string) ?? undefined,
          maturity: (prev.maturity as string) ?? undefined,
          change_note: 'Undo edit',
        })
      } else if (entry.type === 'archive') {
        // Undo archive: restore to active
        await updateMemory(entry.memoryId, {
          status: 'active',
          change_note: 'Undo archive',
        })
      }
      setRefreshTrigger((prev) => prev + 1)
    } catch (err) {
      console.error('Undo failed:', err)
    }
  }, [undoEntry])

  // Network error banner (R6-network-error-feedback)
  const [networkError, setNetworkError] = useState<string | null>(null)
  const networkErrorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const handler = (e: Event) => {
      const msg = (e as CustomEvent<string>).detail
      setNetworkError(msg)
      if (networkErrorTimerRef.current) clearTimeout(networkErrorTimerRef.current)
      networkErrorTimerRef.current = setTimeout(() => setNetworkError(null), 6000)
    }
    window.addEventListener('codememory:network-error', handler)
    return () => {
      window.removeEventListener('codememory:network-error', handler)
      if (networkErrorTimerRef.current) clearTimeout(networkErrorTimerRef.current)
    }
  }, [])

  // Clean up undo timer on unmount
  useEffect(() => {
    return () => {
      if (undoToastTimerRef.current) clearTimeout(undoToastTimerRef.current)
    }
  }, [])

  // Archive confirmation state
  const [archiveConfirmId, setArchiveConfirmId] = useState<string | null>(null)
  const [archiving, setArchiving] = useState(false)

  // Budget no-op feedback (PL1-8)
  const [allNodesFit, setAllNodesFit] = useState(false)

  // Dataset state
  const [datasets, setDatasets] = useState<DatasetInfo[]>([])
  const [currentDataset, setCurrentDataset] = useState('')
  const [switchingDataset, setSwitchingDataset] = useState(false)

  // Graph data (loaded once, shared with Legend)
  const [graphData, setGraphData] = useState<GraphData | null>(null)

  // Graph refresh trigger (increment to reload)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  // Load available datasets on mount
  useEffect(() => {
    fetchDatasets()
      .then((res) => {
        setDatasets(res.datasets)
        setCurrentDataset(res.current_name)
      })
      .catch(console.error)
  }, [])

  // Load graph data
  useEffect(() => {
    fetchGraph().then(setGraphData).catch(console.error)
  }, [refreshTrigger])

  // Handle dataset switching
  const handleSwitchDataset = useCallback(
    (name: string) => {
      if (name === currentDataset) return
      setSwitchingDataset(true)
      switchDataset(name)
        .then(() => {
          setCurrentDataset(name)
          setRefreshTrigger((prev) => prev + 1)
          setSelectedNode(null)
          setResolveData(null)
          setResolveError(null)
          setAllNodesFit(false)
        })
        .catch(console.error)
        .finally(() => setSwitchingDataset(false))
    },
    [currentDataset],
  )

  const doResolve = useCallback(
    (nodeId: string, budgetValue: number) => {
      setIsResolving(true)
      setResolveError(null)
      setAllNodesFit(false)
      fetchResolve({ id: nodeId, depth: 'recommended', budget: budgetValue })
        .then((data) => {
          setResolveData(data)
          setIsResolving(false)
          // PL1-8: detect when all nodes fit within budget (no trimming occurred)
          if (data.nodes.length > 0 && data.nodes.every((n) => n.trim === 'full')) {
            setAllNodesFit(true)
          }
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
      if (allNodesFit && resolveData && newBudget >= budget) {
        // PL1-8: increasing budget when all nodes already fit is a no-op
        return
      }
      if (resolveData) {
        setAllNodesFit(false)
        if (debounceRef.current) clearTimeout(debounceRef.current)
        debounceRef.current = setTimeout(() => {
          doResolve(resolveData.target, newBudget)
        }, 300)
      }
    },
    [resolveData, doResolve, allNodesFit, budget],
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
    setAllNodesFit(false)
  }, [])

  // Clear resolve state without closing panel (PL3-5)
  const handleClearResolve = useCallback(() => {
    setResolveData(null)
    setResolveError(null)
    setAllNodesFit(false)
  }, [])

  // When a memory is selected from Dashboard, switch to graph view and select node
  const handleDashSelect = useCallback((id: string) => {
    setViewMode('graph')
    setSelectedNode(id)
  }, [])

  // Navigate from Dashboard clickable elements to filtered list view
  const handleNavigateToFilter = useCallback((filter: string, type: 'tag' | 'maturity') => {
    setViewMode('list')
    setListFilter(filter)
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

  // Archive from context menu (PL1-5)
  const handleArchiveFromContext = useCallback(() => {
    if (contextMenu) {
      setArchiveConfirmId(contextMenu.nodeId)
      setContextMenu(null)
    }
  }, [contextMenu])

  const handleArchiveConfirm = useCallback(async () => {
    if (!archiveConfirmId) return
    setArchiving(true)
    try {
      await updateMemory(archiveConfirmId, {
        status: 'archived',
        change_note: 'Archived via UI',
      })
      showUndo({ type: 'archive', memoryId: archiveConfirmId })
      handleMemoryChange()
    } catch (err) {
      console.error('Archive failed:', err)
    } finally {
      setArchiving(false)
      setArchiveConfirmId(null)
    }
  }, [archiveConfirmId, handleMemoryChange, showUndo])

  // Close context menu on any click outside or Escape key
  useEffect(() => {
    if (!contextMenu) return
    const clickHandler = () => closeContextMenu()
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeContextMenu()
    }
    window.addEventListener('click', clickHandler)
    window.addEventListener('keydown', keyHandler)
    return () => {
      window.removeEventListener('click', clickHandler)
      window.removeEventListener('keydown', keyHandler)
    }
  }, [contextMenu, closeContextMenu])

  // Keyboard shortcuts overlay
  const [showShortcuts, setShowShortcuts] = useState(false)

  // Global keyboard shortcuts (R5-keyboard-shortcuts)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't capture when typing in an input/textarea/select (except for Escape)
      const tag = (e.target as HTMLElement)?.tagName
      const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'

      // Escape — close any open panel (only when not in input)
      if (e.key === 'Escape') {
        if (showShortcuts) { setShowShortcuts(false); return }
        if (showHelp) { setShowHelp(false); return }
        if (archiveConfirmId) { setArchiveConfirmId(null); return }
        return
      }

      // Ctrl+K — focus search bar
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        document.getElementById('global-search-input')?.focus()
        return
      }

      // Ctrl+N — open create form
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault()
        handleOpenCreate()
        return
      }

      // Ctrl+Z — trigger undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault()
        if (undoEntry) handleUndo()
        return
      }

      // ? — show keyboard shortcuts overlay (only when not in input)
      if (e.key === '?' && !isInput) {
        e.preventDefault()
        setShowShortcuts(true)
        return
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [showShortcuts, showHelp, archiveConfirmId, undoEntry, handleUndo, handleOpenCreate])

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
            onClick={() => setViewMode('list')}
            style={{
              padding: '6px 20px',
              border: 'none',
              cursor: 'pointer',
              fontSize: 11,
              fontFamily: 'Raleway, sans-serif',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              backgroundColor: viewMode === 'list' ? '#1C1917' : 'transparent',
              color: viewMode === 'list' ? '#FFFBEB' : '#57534E',
            }}
          >
            List
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

        {/* Dataset switcher */}
        {datasets.length > 1 && (
          <select
            value={currentDataset}
            onChange={(e) => handleSwitchDataset(e.target.value)}
            disabled={switchingDataset}
            style={{
              padding: '4px 8px',
              border: '1px solid #D4D4D8',
              borderRadius: 2,
              fontSize: 11,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              color: '#1C1917',
              backgroundColor: switchingDataset ? '#F5F5F4' : '#FFFFFF',
              cursor: 'pointer',
              flexShrink: 0,
              outline: 'none',
            }}
          >
            {datasets.map((ds) => (
              <option key={ds.name} value={ds.name}>
                {ds.name} ({ds.memory_count})
              </option>
            ))}
          </select>
        )}
        {switchingDataset && (
          <span style={{ fontSize: 11, color: '#A8A29E', fontFamily: 'Raleway, sans-serif' }}>
            Switching...
          </span>
        )}

        <div style={{ flex: 1 }}>
          {(viewMode === 'graph' || viewMode === 'list') && (
            <SearchBar
              value={searchText}
              onChange={setSearchText}
              onNavigate={(id) => {
                setSelectedNode(id)
                setViewMode('graph')
              }}
            />
          )}
        </div>

        {/* Token Budget + Node Size + Layout toggle — only in graph view */}
        {viewMode === 'graph' && (
          <>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
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
                Zoom
              </label>
              <input
                type="range"
                min={0.15}
                max={2.0}
                step={0.05}
                value={zoomLevel}
                onChange={(e) => setZoomLevel(Number(e.target.value))}
                style={{
                  width: 100,
                  accentColor: '#B8860B',
                  cursor: 'pointer',
                }}
              />
            </div>

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

          </>
        )}

        {/* Help button */}
        <button
          onClick={() => setShowHelp(true)}
          title="Help"
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
            marginLeft: 'auto',
          }}
        >
          Help
        </button>
      </header>

      {/* Network error banner (R6-network-error-feedback) */}
      {networkError && (
        <div
          style={{
            margin: 0,
            padding: '10px 24px',
            backgroundColor: '#991B1B',
            color: '#FFFFFF',
            fontSize: 13,
            fontFamily: 'Raleway, sans-serif',
            textAlign: 'center',
            fontWeight: 500,
            flexShrink: 0,
            position: 'relative',
          }}
        >
          {networkError}
          <button
            onClick={() => { setNetworkError(null); if (networkErrorTimerRef.current) clearTimeout(networkErrorTimerRef.current) }}
            style={{
              position: 'absolute',
              right: 16,
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              color: '#FFFFFF',
              cursor: 'pointer',
              fontSize: 14,
              padding: '0 4px',
              opacity: 0.7,
            }}
          >
            x
          </button>
        </div>
      )}

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
            resolveData={resolveData}
            isResolving={isResolving}
            refreshTrigger={refreshTrigger}
            zoomLevel={zoomLevel}
            onGraphDataLoaded={setGraphData}
          />
          <Legend graphData={graphData} />

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

          {/* PL1-8: Budget no-op feedback */}
          {allNodesFit && !isResolving && resolveData && (
            <div
              style={{
                position: 'absolute',
                top: 16,
                left: 16,
                backgroundColor: '#166534',
                color: '#FFFFFF',
                padding: '6px 14px',
                borderRadius: 2,
                fontSize: 12,
                fontFamily: 'Raleway, sans-serif',
                zIndex: 15,
                boxShadow: '0 2px 8px rgba(28,25,23,0.06)',
              }}
            >
              All {resolveData.nodes.length} nodes fit within budget
            </div>
          )}
        </div>

        {/* List view — shown when viewMode === 'list' */}
        {viewMode === 'list' && (
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <MemoryList onSelectMemory={handleDashSelect} refreshTrigger={refreshTrigger} initialFilter={listFilter} />
          </div>
        )}

        {/* Dashboard view — shown when viewMode === 'dashboard' */}
        {viewMode === 'dashboard' && (
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <Dashboard onSelectMemory={handleDashSelect} onNavigateToFilter={handleNavigateToFilter} refreshTrigger={refreshTrigger} />
          </div>
        )}

        {/* Slide-in overlay panel (only in graph view) */}
        {viewMode === 'graph' && (
          <MemoryDetail
            memoryId={selectedNode}
            onClose={handleClosePanel}
            onResolve={handleResolve}
            onClearResolve={handleClearResolve}
            onNavigateMemory={(targetId: string) => {
              setSelectedNode(targetId)
              setResolveData(null)
              setResolveError(null)
              setAllNodesFit(false)
            }}
            resolveData={resolveData}
            resolveError={resolveError}
            backlinks={(() => {
              if (!graphData || !selectedNode) return []
              // Compute reverse references: which nodes import selectedNode?
              const refs: { id: string; strength: string }[] = []
              for (const edge of graphData.edges) {
                if (edge.data.target === selectedNode) {
                  refs.push({ id: edge.data.source, strength: edge.data.strength })
                }
              }
              // Deduplicate by ID
              const seen = new Set<string>()
              return refs.filter((r) => {
                if (seen.has(r.id)) return false
                seen.add(r.id)
                return true
              })
            })()}
          />
        )}
      </div>

      {/* Memory form (create/edit) — fixed overlay */}
      {showCreateForm && (
        <MemoryForm
          memoryId={formMemoryId}
          onClose={handleCloseForm}
          onChange={handleMemoryChange}
          onUndoEntry={showUndo}
        />
      )}

      {/* Help panel */}
      {showHelp && <HelpPanel onClose={() => setShowHelp(false)} />}

      {/* Onboarding */}
      {showOnboarding && (
        <Onboarding
          onComplete={() => {
            localStorage.setItem(ONBOARDING_KEY, '1')
            setShowOnboarding(false)
          }}
        />
      )}

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
            <div
              style={{
                height: 1,
                backgroundColor: '#E7E5E4',
                margin: '4px 0',
              }}
            />
            <ContextMenuItem label="Archive" onClick={handleArchiveFromContext} />
          </div>
        </>
      )}

      {/* Undo toast */}
      {undoEntry && (
        <div
          className="undo-toast"
          style={{
            position: 'fixed',
            bottom: 24,
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: '#1C1917',
            color: '#FFFBEB',
            padding: '10px 20px',
            borderRadius: 2,
            boxShadow: '0 2px 12px rgba(28,25,23,0.15)',
            zIndex: 200,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            fontSize: 13,
            fontFamily: 'Raleway, sans-serif',
          }}
        >
          <span>
            {undoEntry.type === 'create' && 'Memory created.'}
            {undoEntry.type === 'update' && 'Memory updated.'}
            {undoEntry.type === 'archive' && 'Memory archived.'}
          </span>
          <button
            onClick={handleUndo}
            style={{
              padding: '4px 14px',
              backgroundColor: '#B8860B',
              color: '#FFFBEB',
              border: 'none',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              borderRadius: 2,
            }}
          >
            Undo
          </button>
        </div>
      )}

      {/* Archive confirmation modal (non-destructive styling — PL1-5) */}
      {archiveConfirmId && (
        <>
          <div
            onClick={() => setArchiveConfirmId(null)}
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(28,25,23,0.15)',
              zIndex: 100,
            }}
          />
          <div
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              backgroundColor: '#FFFBEB',
              border: '1px solid #E7E5E4',
              borderRadius: 2,
              padding: 28,
              maxWidth: 420,
              width: '90%',
              zIndex: 101,
              boxShadow: '0 4px 24px rgba(28,25,23,0.12)',
            }}
          >
            <h3
              style={{
                fontSize: 18,
                fontFamily: "'Cormorant Garamond', serif",
                fontWeight: 500,
                color: '#1C1917',
                margin: '0 0 12px 0',
              }}
            >
              Archive Memory
            </h3>
            <p
              style={{
                fontSize: 14,
                fontFamily: 'Raleway, sans-serif',
                color: '#57534E',
                lineHeight: 1.6,
                margin: '0 0 8px 0',
              }}
            >
              Archive this memory? It will be hidden from most views but can be
              restored later by editing its status back to &quot;active&quot;.
            </p>
            <p
              style={{
                fontSize: 12,
                fontFamily: 'JetBrains Mono, monospace',
                color: '#A8A29E',
                margin: '0 0 20px 0',
              }}
            >
              {archiveConfirmId}
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setArchiveConfirmId(null)}
                style={{
                  padding: '8px 20px',
                  border: '1px solid #D4D4D8',
                  background: 'transparent',
                  color: '#57534E',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  borderRadius: 2,
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleArchiveConfirm}
                disabled={archiving}
                style={{
                  padding: '8px 20px',
                  backgroundColor: '#57534E',
                  color: '#FFFFFF',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  borderRadius: 2,
                }}
              >
                {archiving ? 'Archiving...' : 'Yes, Archive'}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Keyboard shortcuts overlay */}
      {showShortcuts && (
        <>
          <div
            onClick={() => setShowShortcuts(false)}
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(28,25,23,0.15)',
              zIndex: 199,
            }}
          />
          <div
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              backgroundColor: '#FFFBEB',
              border: '1px solid #E7E5E4',
              borderRadius: 2,
              padding: 28,
              maxWidth: 420,
              width: '90%',
              zIndex: 200,
              boxShadow: '0 4px 24px rgba(28,25,23,0.12)',
            }}
          >
            <h3 style={{
              fontSize: 18,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: '#1C1917',
              margin: '0 0 16px 0',
            }}>
              Keyboard Shortcuts
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { keys: 'Ctrl + K', desc: 'Focus search bar' },
                { keys: 'Ctrl + N', desc: 'Open new memory form' },
                { keys: 'Ctrl + Z', desc: 'Undo last action' },
                { keys: 'Escape', desc: 'Close open panel / menu' },
                { keys: '?', desc: 'Show this help overlay' },
              ].map(({ keys, desc }) => (
                <div key={keys} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <code style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 11,
                    backgroundColor: '#F5F5F4',
                    padding: '2px 8px',
                    borderRadius: 2,
                    color: '#1C1917',
                    minWidth: 80,
                    textAlign: 'center',
                  }}>
                    {keys}
                  </code>
                  <span style={{ fontSize: 13, fontFamily: 'Raleway, sans-serif', color: '#57534E' }}>
                    {desc}
                  </span>
                </div>
              ))}
            </div>
            <button
              onClick={() => setShowShortcuts(false)}
              style={{
                marginTop: 16,
                padding: '8px 20px',
                border: '1px solid #D4D4D8',
                background: 'transparent',
                color: '#57534E',
                cursor: 'pointer',
                fontSize: 11,
                fontWeight: 600,
                fontFamily: 'Raleway, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                borderRadius: 2,
              }}
            >
              Close
            </button>
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
        transition: 'background-color 100ms ease',
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
