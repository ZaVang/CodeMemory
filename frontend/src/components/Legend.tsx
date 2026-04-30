const DIRECTORY_COLORS: Record<string, { color: string; label: string }> = {
  'user/facts': { color: '#1C1917', label: 'user/facts — 事实' },
  'user/observations': { color: '#57534E', label: 'user/observations — 观察' },
  'user/preferences': { color: '#B8860B', label: 'user/preferences — 偏好' },
  'user/decisions': { color: '#991B1B', label: 'user/decisions — 决策' },
  'user/feelings': { color: '#CA8A04', label: 'user/feelings — 情感' },
  'user/people': { color: '#7C3AED', label: 'user/people — 人物' },
  'user/beliefs': { color: '#166534', label: 'user/beliefs — 信念' },
  'user/moments': { color: '#D97757', label: 'user/moments — 瞬间' },
  'user/snapshots': { color: '#A8A29E', label: 'user/snapshots — 快照' },
  api: { color: '#1E40AF', label: 'api — 外部知识' },
  schemas: { color: '#1C1917', label: 'schemas — 模板' },
  __default: { color: '#57534E', label: 'other — 未映射目录' },
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
        maxWidth: 220,
      }}
    >
      {/* Directory colors */}
      <div style={{ marginBottom: 8 }}>
        <h4 style={{ margin: '0 0 6px 0', fontSize: 11, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Directories
        </h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 10px' }}>
          {Object.entries(DIRECTORY_COLORS).map(([key, { color, label }]) => (
            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
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
              <span style={{ color: '#57534E', fontSize: 11, whiteSpace: 'nowrap' }}>{label}</span>
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
              <span style={{ color: '#57534E', fontSize: 11 }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
