import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { fetchMemory } from '../api'
import type { MemoryDetail as MemoryDetailType, ResolveResponse } from '../types'

interface Props {
  memoryId: string | null
  onClose: () => void
  onResolve: (id: string) => void
  resolveData?: ResolveResponse | null
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, { bg: string; color: string; label: string }> = {
    active: { bg: '#16653420', color: '#166534', label: 'active' },
    draft: { bg: '#F5F5F4', color: '#57534E', label: 'draft' },
    archived: { bg: '#F5F5F4', color: '#A8A29E', label: 'archived' },
  }

  const s = styles[status] || styles.draft

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 10px',
        borderRadius: 2,
        fontSize: 11,
        fontWeight: 600,
        fontFamily: 'Raleway, sans-serif',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        backgroundColor: s.bg,
        color: s.color,
      }}
    >
      {s.label}
    </span>
  )
}

function MaturityBadge({ maturity }: { maturity: string }) {
  const styles: Record<string, { bg: string; color: string }> = {
    draft: { bg: '#F5F5F4', color: '#57534E' },
    verified: { bg: '#1E40AF15', color: '#1E40AF' },
    proven: { bg: '#16653415', color: '#166534' },
    stale: { bg: '#991B1B15', color: '#991B1B' },
  }

  const s = styles[maturity] || styles.draft

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 10px',
        borderRadius: 2,
        fontSize: 11,
        fontWeight: 600,
        fontFamily: 'Raleway, sans-serif',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        backgroundColor: s.bg,
        color: s.color,
      }}
    >
      {maturity}
    </span>
  )
}

export default function MemoryDetail({ memoryId, onClose, onResolve, resolveData }: Props) {
  const [memory, setMemory] = useState<MemoryDetailType | null>(null)
  const [loading, setLoading] = useState(false)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!memoryId) {
      setVisible(false)
      setMemory(null)
      return
    }
    setVisible(true)
    setLoading(true)
    fetchMemory(memoryId)
      .then(setMemory)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [memoryId])

  // Close on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    if (memoryId) window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [memoryId, onClose])

  if (!memoryId) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(28,25,23,0.08)',
          zIndex: 19,
          opacity: visible ? 1 : 0,
          transition: 'opacity 200ms ease',
        }}
      />

      {/* Slide-in panel */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          bottom: 0,
          width: '30vw',
          minWidth: 360,
          maxWidth: 520,
          backgroundColor: '#FFFBEB',
          borderLeft: '1px solid #E7E5E4',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 20,
          transform: visible ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 250ms ease',
          boxShadow: '0 4px 16px rgba(28,25,23,0.08)',
        }}
      >
        {/* Header bar with close button */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 24px',
            borderBottom: '1px solid #E7E5E4',
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              fontSize: 22,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: '#1C1917',
              margin: 0,
              lineHeight: 1.3,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              flex: 1,
              paddingRight: 12,
            }}
          >
            {memory?.summary || memoryId}
          </h2>
          <button
            onClick={() => onResolve(memoryId!)}
            title="Resolve dependency DAG from this node"
            style={{
              border: '1px solid #B8860B',
              background: 'transparent',
              cursor: 'pointer',
              fontSize: 11,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              color: '#B8860B',
              padding: '4px 12px',
              borderRadius: 2,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              whiteSpace: 'nowrap',
            }}
          >
            Resolve
          </button>
          <button
            onClick={onClose}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 20,
              color: '#57534E',
              padding: '4px 8px',
              borderRadius: 2,
              lineHeight: 1,
              fontFamily: 'Raleway, sans-serif',
            }}
          >
            ✕
          </button>
        </div>

        {loading && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              color: '#A8A29E',
              fontFamily: 'Raleway, sans-serif',
              fontSize: 14,
            }}
          >
            Loading...
          </div>
        )}

        {!loading && !memory && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              color: '#991B1B',
              fontFamily: 'Raleway, sans-serif',
              fontSize: 14,
              padding: 24,
            }}
          >
            Failed to load memory
          </div>
        )}

        {!loading && memory && (
          <>
            {/* Metadata card */}
            <div
              style={{
                padding: '20px 24px',
                borderBottom: '1px solid #E7E5E4',
                flexShrink: 0,
              }}
            >
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
              <StatusBadge status={memory.status} />
              {memory.maturity && <MaturityBadge maturity={memory.maturity} />}
              <span
                style={{
                  display: 'inline-block',
                  padding: '2px 10px',
                  borderRadius: 2,
                  fontSize: 11,
                  fontFamily: 'Raleway, sans-serif',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  backgroundColor: '#F5F5F4',
                  color: '#57534E',
                }}
              >
                {memory.type}
              </span>
            </div>

            {/* Metadata rows */}
            <div style={{ fontSize: 12, fontFamily: 'Raleway, sans-serif', color: '#57534E', lineHeight: 1.8 }}>
              <div><strong>ID:</strong> {memory.id}</div>
              {memory.tags && memory.tags.length > 0 && (
                <div>
                  <strong>Tags:</strong>{' '}
                  {memory.tags.map((t) => (
                    <span
                      key={t}
                      style={{
                        display: 'inline-block',
                        padding: '0 8px',
                        borderRadius: 2,
                        backgroundColor: '#F5F5F4',
                        marginRight: 4,
                        marginBottom: 2,
                        fontSize: 11,
                        fontFamily: 'Raleway, sans-serif',
                        fontWeight: 500,
                        letterSpacing: '0.04em',
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
              <div><strong>Intensity:</strong> {memory.intensity}/10</div>
              <div><strong>Version:</strong> {memory.version}</div>
              {memory.created && <div><strong>Created:</strong> {memory.created}</div>}
              {memory.updated && <div><strong>Updated:</strong> {memory.updated}</div>}
              {memory.schema && <div><strong>Schema:</strong> {memory.schema}</div>}
              {memory.protected && (
                <div style={{ color: '#B8860B' }}>Protected memory</div>
              )}
            </div>

            {/* Imports */}
            {memory.imports && Object.keys(memory.imports).length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4, fontFamily: 'Raleway, sans-serif' }}>
                  Imports
                </div>
                {Object.entries(memory.imports).map(([strength, deps]) => (
                  <div key={strength} style={{ marginBottom: 2 }}>
                    <span style={{ fontSize: 11, color: '#A8A29E', fontStyle: 'italic' }}>{strength}:</span>
                    {(Array.isArray(deps) ? deps : []).slice(0, 5).map((dep) => (
                      <div key={typeof dep === 'string' ? dep : (dep as Record<string, unknown>).id as string || ''} style={{ fontSize: 11, color: '#57534E', paddingLeft: 12, fontFamily: 'Raleway, sans-serif' }}>
                        {typeof dep === 'string' ? dep : (dep as Record<string, unknown>).id as string || ''}
                      </div>
                    ))}
                    {Array.isArray(deps) && deps.length > 5 && (
                      <div style={{ fontSize: 11, color: '#A8A29E', paddingLeft: 12, fontFamily: 'Raleway, sans-serif' }}>
                        ...and {deps.length - 5} more
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Resolve results */}
          {resolveData && resolveData.nodes.length > 0 && (
            <div
              style={{
                padding: '16px 24px',
                borderBottom: '1px solid #E7E5E4',
                flexShrink: 0,
                maxHeight: 260,
                overflowY: 'auto',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  color: '#57534E',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  marginBottom: 8,
                }}
              >
                Resolve — {resolveData.nodes.length} nodes
                {resolveData.budget && (
                  <span style={{ color: '#A8A29E', fontWeight: 400, textTransform: 'none', letterSpacing: '0' }}>
                    {' '}· budget {resolveData.budget} · depth {resolveData.depth}
                  </span>
                )}
              </div>
              {[...resolveData.nodes]
                .sort((a, b) => a.index - b.index)
                .map((node) => (
                  <div
                    key={node.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '3px 0',
                      fontSize: 11,
                      fontFamily: 'Raleway, sans-serif',
                      opacity: node.trim === 'skipped' ? 0.4 : node.trim === 'summary' ? 0.65 : 1,
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: 10,
                        color: '#A8A29E',
                        minWidth: 24,
                      }}
                    >
                      [{node.index}]
                    </span>
                    <span style={{
                      display: 'inline-block',
                      width: 6,
                      height: 6,
                      borderRadius: 1,
                      backgroundColor:
                        node.trim === 'full' ? '#166534' :
                        node.trim === 'summary' ? '#CA8A04' : '#A8A29E',
                      flexShrink: 0,
                    }}/>
                    <code
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: 10,
                        color: '#1C1917',
                        flex: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {node.id}
                    </code>
                    <span
                      style={{
                        fontSize: 9,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                        color:
                          node.trim === 'full' ? '#166534' :
                          node.trim === 'summary' ? '#CA8A04' : '#A8A29E',
                      }}
                    >
                      {node.trim}
                    </span>
                  </div>
                ))}
            </div>
          )}

          {/* Body markdown */}
          <div
            className="prose"
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '24px',
              fontSize: 15,
              fontFamily: 'Raleway, sans-serif',
              color: '#1C1917',
              lineHeight: 1.7,
            }}
          >
            {memory.body ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {memory.body}
              </ReactMarkdown>
            ) : (
              <p style={{ color: '#A8A29E', fontStyle: 'italic' }}>No content</p>
            )}
          </div>
        </>
        )}
      </div>
    </>
  )
}
