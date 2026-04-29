const DIRECTORY_COLORS: Record<string, { color: string; label: string }> = {
  facts: { color: '#1C1917', label: 'facts' },
  preferences: { color: '#B8860B', label: 'preferences' },
  observations: { color: '#57534E', label: 'observations' },
  investment: { color: '#1E40AF', label: 'investment' },
  snapshots: { color: '#A8A29E', label: 'snapshots' },
  schemas: { color: '#1C1917', label: 'schemas' },
}

const EDGE_STYLES = [
  { strength: 'required', label: 'Required', style: 'solid 2px #1C1917' },
  { strength: 'recommended', label: 'Recommended', style: 'dashed 1.5px #57534E' },
  { strength: 'related', label: 'Related', style: 'dotted 1px #D4D4D8' },
]

export default function Legend() {
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
      }}
    >
      {/* Directory colors */}
      <div style={{ marginBottom: 8 }}>
        <h4 style={{ margin: '0 0 6px 0', fontSize: 11, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Directories
        </h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 12px', marginBottom: 8 }}>
          {Object.entries(DIRECTORY_COLORS).map(([key, { color, label }]) => (
            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  display: 'inline-block',
                  width: 10,
                  height: 10,
                  borderRadius: 2,
                  backgroundColor: color,
                }}
              />
              <span style={{ color: '#57534E' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Edge styles */}
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
              <span style={{ color: '#57534E' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
