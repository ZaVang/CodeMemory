import { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { fetchMemory } from '../api'
import type { MemoryDetail as MemoryDetailType, ResolveResponse } from '../types'
import { StatusBadge, MaturityBadge } from './Badges'

/** Build an LLM system prompt from resolved nodes and copy to clipboard. */
function buildPromptContent(resolveData: ResolveResponse): string {
  const lines: string[] = []
  const nodes = [...resolveData.nodes].sort((a, b) => a.index - b.index)
  const fullNodes = nodes.filter((n) => n.trim === 'full')
  const summaryNodes = nodes.filter((n) => n.trim === 'summary')
  const skippedNodes = nodes.filter((n) => n.trim === 'skipped')
  const totalTokens = nodes.reduce((sum, n) => sum + n.body.length, 0)

  lines.push('You are an assistant with access to a structured memory system.')
  lines.push('Below is a context assembled from linked memory nodes in topological (dependency) order.\n')

  lines.push(`## Resolved Context — ${resolveData.target}`)
  lines.push(`Depth: ${resolveData.depth}  |  Budget: ${resolveData.budget}  |  Estimated tokens: ~${totalTokens}`)
  lines.push(`Nodes: ${fullNodes.length} full-text, ${summaryNodes.length} summary, ${skippedNodes.length} skipped\n`)

  for (const node of nodes) {
    const trimLabel = node.trim === 'full' ? 'FULL' : node.trim === 'summary' ? 'SUMMARY' : 'SKIPPED'
    lines.push(`### [${node.index}/${node.total}] ${node.id}  (${node.type}, ${trimLabel})`)
    if (node.body) {
      lines.push('')
      lines.push(node.body)
      lines.push('')
    }
  }

  // Trailing instruction block
  lines.push('---')
  lines.push('## Instructions')
  lines.push('')
  lines.push('1. Nodes marked FULL contain the complete memory content — prioritise these.')
  lines.push('2. Nodes marked SUMMARY contain only a summary — treat as background context.')
  lines.push('3. Nodes marked SKIPPED are listed for awareness but their content is omitted.')
  lines.push('4. Use the context above to ground your responses. When citing, reference the memory ID.')
  lines.push('5. If the context is insufficient, state what additional information you need.')

  return lines.join('\n')
}


interface Props {
  memoryId: string | null
  onClose: () => void
  onResolve: (id: string) => void
  onClearResolve?: () => void
  onNavigateMemory?: (id: string) => void
  resolveData?: ResolveResponse | null
  resolveError?: string | null
  backlinks?: { id: string; strength: string }[]
}

export default function MemoryDetail({ memoryId, onClose, onResolve, onClearResolve, onNavigateMemory, resolveData, resolveError, backlinks }: Props) {
  const [memory, setMemory] = useState<MemoryDetailType | null>(null)
  const [loading, setLoading] = useState(false)
  const [visible, setVisible] = useState(false)
  // PL3-6: track which strength groups are fully expanded
  const [expandedImports, setExpandedImports] = useState<Record<string, boolean>>({})
  const [copyLabel, setCopyLabel] = useState('Generate Prompt')
  const IMPORT_PREVIEW_LIMIT = 10

  const handleCopyPrompt = useCallback(() => {
    if (!resolveData) return
    const text = buildPromptContent(resolveData)
    navigator.clipboard.writeText(text).then(
      () => {
        setCopyLabel('Copied!')
        setTimeout(() => setCopyLabel('Generate Prompt'), 2000)
      },
      () => setCopyLabel('Copy failed'),
    )
  }, [resolveData])

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
                {Object.entries(memory.imports).map(([strength, deps]) => {
                  const depList = Array.isArray(deps) ? deps : []
                  const expanded = expandedImports[strength] || depList.length <= IMPORT_PREVIEW_LIMIT
                  const visibleDeps = expanded ? depList : depList.slice(0, IMPORT_PREVIEW_LIMIT)
                  return (
                  <div key={strength} style={{ marginBottom: 2 }}>
                    <span style={{ fontSize: 11, color: '#A8A29E', fontStyle: 'italic' }}>{strength}:</span>
                    {visibleDeps.map((dep) => {
                      const depId = typeof dep === 'string' ? dep : (dep as Record<string, unknown>).id as string || ''
                      return (
                        <div
                          key={depId}
                          onClick={(e) => {
                            e.stopPropagation()
                            if (onNavigateMemory && depId) onNavigateMemory(depId)
                          }}
                          title={`Navigate to ${depId}`}
                          style={{
                            fontSize: 11,
                            color: '#1E40AF',
                            paddingLeft: 12,
                            fontFamily: 'Raleway, sans-serif',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                          }}
                        >
                          {depId}
                        </div>
                      )
                    })}
                    {depList.length > IMPORT_PREVIEW_LIMIT && (
                      <div
                        onClick={() =>
                          setExpandedImports((prev) => ({ ...prev, [strength]: !prev[strength] }))
                        }
                        style={{
                          fontSize: 11,
                          color: '#B8860B',
                          paddingLeft: 12,
                          fontFamily: 'Raleway, sans-serif',
                          cursor: 'pointer',
                          fontWeight: 500,
                        }}
                      >
                        {expanded ? `Show less` : `Show all ${depList.length} (${depList.length - IMPORT_PREVIEW_LIMIT} more)`}
                      </div>
                    )}
                  </div>
                  )
                })}
              </div>
            )}

            {/* Referenced By (backlinks) */}
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4, fontFamily: 'Raleway, sans-serif' }}>
                Referenced By
              </div>
              {backlinks && backlinks.length > 0 ? (
                backlinks.map((ref) => (
                  <div
                    key={ref.id}
                    onClick={(e) => {
                      e.stopPropagation()
                      if (onNavigateMemory) onNavigateMemory(ref.id)
                    }}
                    title={`Navigate to ${ref.id}`}
                    style={{
                      fontSize: 11,
                      color: '#1E40AF',
                      paddingLeft: 12,
                      fontFamily: 'Raleway, sans-serif',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                      marginBottom: 2,
                    }}
                  >
                    {ref.id}
                    <span style={{ color: '#A8A29E', fontStyle: 'italic', marginLeft: 6, textDecoration: 'none' }}>
                      ({ref.strength})
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: 11, color: '#A8A29E', fontFamily: 'Raleway, sans-serif', paddingLeft: 12, fontStyle: 'italic' }}>
                  No other memories reference this one.
                </div>
              )}
            </div>
          </div>

          {/* Resolve error feedback (R6-resolve-error-feedback) */}
          {resolveError && (
            <div
              style={{
                padding: '14px 24px',
                borderBottom: '1px solid #E7E5E4',
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#991B1B0A',
                  borderLeft: '3px solid #991B1B',
                  borderRadius: 2,
                  fontSize: 12,
                  fontFamily: 'Raleway, sans-serif',
                  color: '#991B1B',
                  lineHeight: 1.5,
                }}
              >
                {resolveError}
              </div>
            </div>
          )}

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
              {/* Pinned version notices — shown prominently before node list */}
              {resolveData.notices && resolveData.notices.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  {resolveData.notices.map((notice, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '6px 10px',
                        backgroundColor: '#CA8A0415',
                        borderLeft: '3px solid #CA8A04',
                        borderRadius: 2,
                        fontSize: 11,
                        fontFamily: 'Raleway, sans-serif',
                        color: '#CA8A04',
                        marginBottom: 4,
                        lineHeight: 1.5,
                      }}
                    >
                      {notice}
                    </div>
                  ))}
                </div>
              )}

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 8,
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
                  }}
                >
                  Resolve — {resolveData.nodes.length} nodes
                  {resolveData.budget && (
                    <span style={{ color: '#A8A29E', fontWeight: 400, textTransform: 'none', letterSpacing: '0' }}>
                      {' '}· budget {resolveData.budget} · depth {resolveData.depth}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    onClick={handleCopyPrompt}
                    style={{
                      border: '1px solid #166534',
                      background: copyLabel === 'Copied!' ? '#16653415' : 'transparent',
                      cursor: 'pointer',
                      fontSize: 10,
                      fontWeight: 600,
                      fontFamily: 'Raleway, sans-serif',
                      color: copyLabel === 'Copied!' ? '#166534' : '#166534',
                      padding: '2px 8px',
                      borderRadius: 2,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                    }}
                  >
                    {copyLabel}
                  </button>
                  {onClearResolve && (
                    <button
                      onClick={onClearResolve}
                      style={{
                        border: '1px solid #D4D4D8',
                        background: 'transparent',
                        cursor: 'pointer',
                        fontSize: 10,
                        fontWeight: 600,
                        fontFamily: 'Raleway, sans-serif',
                        color: '#57534E',
                        padding: '2px 8px',
                        borderRadius: 2,
                        textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                      }}
                    >
                      Clear
                    </button>
                  )}
                </div>
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
