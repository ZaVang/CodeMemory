import type { GraphData } from '../types'

interface Props {
  graphData: GraphData | null
}

// LuxCart directory color palette — shared with GraphCanvas
const DIRECTORY_COLORS: Record<string, string> = {
  'user/facts': '#1C1917',
  'user/observations': '#57534E',
  'user/preferences': '#B8860B',
  'user/decisions': '#991B1B',
  'user/feelings': '#CA8A04',
  'user/people': '#7C3AED',
  'user/beliefs': '#166534',
  'user/moments': '#D97757',
  'user/snapshots': '#A8A29E',
  'api': '#1E40AF',
  'schemas': '#1C1917',
}

const DEFAULT_COLOR = '#57534E'

// Fallback colors for directories not in the known palette
const FALLBACK_COLORS = [
  '#1E40AF', '#7C3AED', '#166534', '#991B1B', '#CA8A04',
  '#D97757', '#0F766E', '#BE185D', '#854D0E', '#4F46E5',
]

function getColorForDirectory(dir: string, extraIndex: number): string {
  // Check known mappings first
  if (DIRECTORY_COLORS[dir]) return DIRECTORY_COLORS[dir]
  // Also check prefix match (e.g. "user/facts" partially matches "user/facts/something")
  for (const [key, color] of Object.entries(DIRECTORY_COLORS)) {
    if (dir.startsWith(key + '/') || key.startsWith(dir + '/')) return color
  }
  // Fallback: assign from palette based on index
  return FALLBACK_COLORS[extraIndex % FALLBACK_COLORS.length]
}

const EDGE_STYLES = [
  { strength: 'required', label: 'Required', style: 'solid 2px #1C1917' },
  { strength: 'recommended', label: 'Recommended', style: 'dashed 1.5px #57534E' },
  { strength: 'related', label: 'Related', style: 'dotted 1px #D4D4D8' },
]

export default function Legend({ graphData }: Props) {
  // Derive directory-color entries from actual graph data
  const directories = new Set<string>()
  if (graphData) {
    for (const node of graphData.nodes) {
      const dir = node.data.directory || node.data.group || ''
      if (dir) directories.add(dir)
    }
  }

  // Build sorted list with color assignments
  const knownDirs: { dir: string; color: string; isFallback: boolean }[] = []
  const unknownDirs: { dir: string; color: string; isFallback: boolean }[] = []

  let extraIndex = 0
  for (const dir of [...directories].sort()) {
    const inKnown = dir in DIRECTORY_COLORS
    if (inKnown) {
      knownDirs.push({ dir, color: DIRECTORY_COLORS[dir], isFallback: false })
    } else {
      unknownDirs.push({ dir, color: getColorForDirectory(dir, extraIndex), isFallback: true })
      extraIndex++
    }
  }

  const allDirs = [...knownDirs, ...unknownDirs]

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 16,
        left: 16,
        backgroundColor: '#FFFFFF',
        borderRadius: 4,
        padding: '12px 16px',
        boxShadow: '0 2px 8px rgba(28,25,23,0.06)',
        border: '1px solid #F5F5F4',
        fontSize: 12,
        fontFamily: 'Raleway, sans-serif',
        zIndex: 10,
        maxWidth: 240,
      }}
    >
      {/* Directory colors — dynamic from graph data */}
      <div style={{ marginBottom: 8 }}>
        <h4 style={{ margin: '0 0 6px 0', fontSize: 11, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Directories
        </h4>
        {allDirs.length === 0 && (
          <span style={{ color: '#A8A29E', fontSize: 11 }}>No directories</span>
        )}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 10px' }}>
          {allDirs.map(({ dir, color, isFallback }) => (
            <div key={dir} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span
                style={{
                  display: 'inline-block',
                  width: 9,
                  height: 9,
                  borderRadius: 2,
                  backgroundColor: color,
                  flexShrink: 0,
                }}
              />
              <span style={{ color: '#57534E', fontSize: 11, whiteSpace: 'nowrap' }}>
                {dir}{isFallback ? ' (auto)' : ''}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Edge styles — static */}
      <div>
        <h4 style={{ margin: '0 0 6px 0', fontSize: 11, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Edges
        </h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 12px' }}>
          {EDGE_STYLES.map(({ strength, label, style }) => (
            <div key={strength} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  display: 'inline-block',
                  width: 20,
                  height: 2,
                  borderTop: style,
                }}
              />
              <span style={{ color: '#57534E', fontSize: 11 }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
