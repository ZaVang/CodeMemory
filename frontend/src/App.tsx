import { useState } from 'react'
import GraphCanvas from './components/GraphCanvas'
import MemoryDetail from './components/MemoryDetail'
import SearchBar from './components/SearchBar'
import Legend from './components/Legend'

type LayoutMode = 'dagre' | 'force'

export default function App() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [searchText, setSearchText] = useState('')
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('dagre')

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

        <div style={{ flex: 1 }}>
          <SearchBar value={searchText} onChange={setSearchText} />
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
      </header>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        {/* Canvas area — always full width */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          <GraphCanvas
            searchText={searchText}
            onNodeClick={setSelectedNode}
            layoutMode={layoutMode}
          />
          <Legend />
        </div>

        {/* Slide-in overlay panel */}
        <MemoryDetail memoryId={selectedNode} onClose={() => setSelectedNode(null)} />
      </div>
    </div>
  )
}
