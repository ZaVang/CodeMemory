import { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { fetchMemory, fetchTestBundle, rehashMemory } from '../api'
import type { MemoryDetail as MemoryDetailType, ResolveResponse, TestBundle } from '../types'
import { StatusBadge, MaturityBadge } from './Badges'
import { useExitAnimation } from '../useExitAnimation'

/** Return the canonical rendered Build output for clipboard handoff. */
// eslint-disable-next-line react-refresh/only-export-components
export function buildPromptContent(resolveData: ResolveResponse): string {
  return resolveData.full_text
}


interface Props {
  memoryId: string | null
  onClose: () => void
  onResolve: (id: string) => void
  onClearResolve?: () => void
  onNavigateMemory?: (id: string) => void
  resolveData?: ResolveResponse | null
  resolveError?: string | null
  isResolving?: boolean
  backlinks?: { id: string; strength: string }[]
  /** R19-C4: incremented by App.tsx to trigger copy via Ctrl+Shift+C keyboard shortcut */
  copyTrigger?: number
}

export default function MemoryDetail({ memoryId, onClose, onResolve, onClearResolve, onNavigateMemory, resolveData, resolveError, isResolving, backlinks, copyTrigger }: Props) {
  const [memory, setMemory] = useState<MemoryDetailType | null>(null)
  const [testBundle, setTestBundle] = useState<TestBundle | null>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { visible: panelVisible, closing } = useExitAnimation(!!memoryId)
  // PL3-6: track which strength groups are fully expanded
  const [expandedImports, setExpandedImports] = useState<Record<string, boolean>>({})
  const [copyLabel, setCopyLabel] = useState('Copy Build')
  const IMPORT_PREVIEW_LIMIT = 10

  // R19-C5: clipboard write with HTTP fallback via execCommand('copy')
  const doClipboardCopy = useCallback((text: string) => {
    const onSuccess = () => {
      setCopyLabel('\u2713 Copied')
      setTimeout(() => setCopyLabel('Copy Build'), 2000)
    }
    const onError = () => setCopyLabel('Copy failed')

    // Modern clipboard API available — use it (preferred path for localhost / HTTPS)
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      navigator.clipboard.writeText(text).then(onSuccess, () => {
        // Clipboard API failed (e.g. NotAllowedError) — try synchronous fallback
        try {
          const textarea = document.createElement('textarea')
          textarea.value = text
          textarea.style.position = 'fixed'
          textarea.style.opacity = '0'
          document.body.appendChild(textarea)
          textarea.select()
          document.execCommand('copy')
          document.body.removeChild(textarea)
          onSuccess()
        } catch {
          onError()
        }
      })
      return
    }

    // No clipboard API (non-secure context) — synchronous fallback
    try {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      onSuccess()
    } catch {
      onError()
    }
  }, [])

  const handleCopyPrompt = useCallback(() => {
    if (!resolveData) return
    doClipboardCopy(buildPromptContent(resolveData))
  }, [resolveData, doClipboardCopy])

  useEffect(() => {
    if (!memoryId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMemory(null)
      setTestBundle(null)
      setTestError(null)
      return
    }
    setLoading(true)
    fetchMemory(memoryId)
      .then(setMemory)
      .catch(console.error)
      .finally(() => setLoading(false))
    setTestBundle(null)
    setTestError(null)
    fetchTestBundle(memoryId)
      .then(setTestBundle)
      .catch((error) => setTestError(error instanceof Error ? error.message : 'Golden questions unavailable'))
  }, [memoryId])

  // R19-C4: respond to copyTrigger from App.tsx (Ctrl+Shift+C keyboard shortcut)
  useEffect(() => {
    if (copyTrigger && copyTrigger > 0 && resolveData) {
      handleCopyPrompt()
    }
  }, [copyTrigger]) // eslint-disable-line react-hooks/exhaustive-deps

  // Close on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    if (memoryId) window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [memoryId, onClose])

  if (!panelVisible) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={closing ? 'backdrop-fade-exit' : 'backdrop-fade-enter'}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(28,25,23,0.08)',
          zIndex: 19,
        }}
      />

      {/* Slide-in panel */}
      <div
        className={closing ? 'panel-slide-exit' : 'panel-slide-enter'}
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          bottom: 0,
          width: '30vw',
          minWidth: 360,
          maxWidth: 520,
          backgroundColor: 'var(--cm-bg-primary)',
          borderLeft: '1px solid var(--cm-border)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 20,
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
            borderBottom: '1px solid var(--cm-border)',
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              fontSize: 22,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: 'var(--cm-text-primary)',
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
            title="Build canonical context from this node"
            style={{
              border: '1px solid var(--cm-accent)',
              background: 'transparent',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              color: 'var(--cm-accent)',
              padding: '4px 12px',
              borderRadius: 2,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              whiteSpace: 'nowrap',
            }}
          >
            Build
          </button>
          <button
            onClick={onClose}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 20,
              color: 'var(--cm-text-secondary)',
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
              color: 'var(--cm-text-tertiary)',
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
              color: 'var(--cm-error)',
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
                borderBottom: '1px solid var(--cm-border)',
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
                  fontSize: 12,
                  fontFamily: 'Raleway, sans-serif',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  backgroundColor: 'var(--cm-bg-subtle)',
                  color: 'var(--cm-text-secondary)',
                }}
              >
                {memory.type}
              </span>
            </div>

            {/* Metadata rows */}
            <div style={{ fontSize: 12, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-secondary)', lineHeight: 1.8 }}>
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
                        backgroundColor: 'var(--cm-bg-subtle)',
                        marginRight: 4,
                        marginBottom: 2,
                        fontSize: 12,
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
              <div><strong>Version:</strong> {memory.version}</div>
              {memory.created && <div><strong>Created:</strong> {memory.created}</div>}
              {memory.updated && <div><strong>Updated:</strong> {memory.updated}</div>}
              {memory.schema && <div><strong>Schema:</strong> {memory.schema}</div>}
              {memory.protected && (
                <div style={{ color: 'var(--cm-accent)' }}>Protected memory</div>
              )}
            </div>

            {/* Imports */}
            {memory.imports && Object.keys(memory.imports).length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--cm-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4, fontFamily: 'Raleway, sans-serif' }}>
                  Imports
                </div>
                {Object.entries(memory.imports).map(([strength, deps]) => {
                  const depList = Array.isArray(deps) ? deps : []
                  const expanded = expandedImports[strength] || depList.length <= IMPORT_PREVIEW_LIMIT
                  const visibleDeps = expanded ? depList : depList.slice(0, IMPORT_PREVIEW_LIMIT)
                  return (
                  <div key={strength} style={{ marginBottom: 2 }}>
                    <span style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', fontStyle: 'italic' }}>{strength}:</span>
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
                            fontSize: 12,
                            color: 'var(--cm-info)',
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
                          fontSize: 12,
                          color: 'var(--cm-accent)',
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
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--cm-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4, fontFamily: 'Raleway, sans-serif' }}>
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
                      fontSize: 12,
                      color: 'var(--cm-info)',
                      paddingLeft: 12,
                      fontFamily: 'Raleway, sans-serif',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                      marginBottom: 2,
                    }}
                  >
                    {ref.id}
                    <span style={{ color: 'var(--cm-text-tertiary)', fontStyle: 'italic', marginLeft: 6, textDecoration: 'none' }}>
                      ({ref.strength})
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif', paddingLeft: 12, fontStyle: 'italic' }}>
                  No other memories reference this one.
                </div>
              )}
            </div>

            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--cm-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6, fontFamily: 'Raleway, sans-serif' }}>
                Golden Questions
              </div>
              {testBundle && testBundle.questions.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {testBundle.questions.map((question, index) => (
                    <div key={`${question.q}-${index}`} style={{ padding: '8px 10px', backgroundColor: 'var(--cm-bg-subtle)', borderLeft: '3px solid var(--cm-info)' }}>
                      <div style={{ fontSize: 13, color: 'var(--cm-text-primary)', lineHeight: 1.5 }}>
                        {index + 1}. {question.q}
                      </div>
                      {question.expect && (
                        <div style={{ marginTop: 4, fontSize: 12, color: 'var(--cm-text-tertiary)', lineHeight: 1.5 }}>
                          Expected: {question.expect}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', lineHeight: 1.5, fontStyle: 'italic' }}>
                  {testError || testBundle?.notices[0] || 'Loading test contract...'}
                </div>
              )}
              <div style={{ marginTop: 5, fontSize: 11, color: 'var(--cm-text-tertiary)' }}>
                Read-only contract; CodeMemory does not run or judge answers in the UI.
              </div>
            </div>
          </div>

          {/* Build loading skeleton */}
          {isResolving && (
            <div
              style={{
                padding: '16px 24px',
                borderBottom: '1px solid var(--cm-border)',
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  color: 'var(--cm-text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  marginBottom: 12,
                }}
              >
                Building canonical context...
              </div>
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="skeleton-shimmer"
                  style={{
                    height: 16,
                    marginBottom: 6,
                    width: `${100 - i * 20}%`,
                  }}
                />
              ))}
            </div>
          )}

          {/* Build error feedback */}
          {resolveError && (
            <div
              style={{
                padding: '14px 24px',
                borderBottom: '1px solid var(--cm-border)',
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  padding: '8px 12px',
                  backgroundColor: 'var(--cm-bg-error-subtle)',
                  borderLeft: '3px solid var(--cm-error)',
                  borderRadius: 2,
                  fontSize: 12,
                  fontFamily: 'Raleway, sans-serif',
                  color: 'var(--cm-error)',
                  lineHeight: 1.5,
                }}
              >
                {resolveError}
              </div>
            </div>
          )}

          {/* Build results */}
          {resolveData && resolveData.nodes.length > 0 && (
            <div
              style={{
                padding: '16px 24px',
                borderBottom: '1px solid var(--cm-border)',
                flexShrink: 0,
                maxHeight: 260,
                overflowY: 'auto',
              }}
            >
              {/* Pinned version / stale notices — shown prominently before node list */}
              {resolveData.notices && resolveData.notices.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  {resolveData.notices.map((notice, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '6px 10px',
                        backgroundColor: 'var(--cm-bg-warning-subtle)',
                        borderLeft: '3px solid var(--cm-warning)',
                        borderRadius: 2,
                        fontSize: 12,
                        fontFamily: 'Raleway, sans-serif',
                        color: 'var(--cm-warning)',
                        marginBottom: 4,
                        lineHeight: 1.5,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                      }}
                    >
                      <span style={{ flex: 1 }}>{notice}</span>
                      {notice.includes('hash mismatch') && memoryId && (
                        <button
                          onClick={async (e) => {
                            e.stopPropagation()
                            try {
                              await rehashMemory(memoryId)
                              onResolve(memoryId)
                            } catch { /* notice remains if fix fails */ }
                          }}
                          style={{
                            padding: '2px 8px',
                            fontSize: 10,
                            fontWeight: 600,
                            fontFamily: 'Raleway, sans-serif',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                            background: 'none',
                            border: '1px solid var(--cm-warning)',
                            borderRadius: 2,
                            color: 'var(--cm-warning)',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                            flexShrink: 0,
                          }}
                          title="Recompute the summary hash to match current body content"
                        >
                          Fix
                        </button>
                      )}
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
                    fontSize: 12,
                    fontWeight: 600,
                    fontFamily: 'Raleway, sans-serif',
                    color: 'var(--cm-text-secondary)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                  }}
                >
                  Build — {resolveData.nodes.length} nodes
                  {resolveData.budget && (
                    <span style={{ color: 'var(--cm-text-tertiary)', fontWeight: 400, textTransform: 'none', letterSpacing: '0' }}>
                      {' '}· budget {resolveData.budget} · depth {resolveData.depth}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    onClick={handleCopyPrompt}
                    title="Copy formatted context for LLM system prompt injection"
                    style={{
                      border: '1px solid var(--cm-accent)',
                      background: copyLabel.startsWith('\u2713') ? 'var(--cm-bg-success-subtle)' : 'transparent',
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 600,
                      fontFamily: 'Raleway, sans-serif',
                      color: copyLabel.startsWith('\u2713') ? 'var(--cm-success)' : 'var(--cm-accent)',
                      padding: '2px 8px',
                      borderRadius: 2,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      transition: 'all 150ms ease',
                    }}
                  >
                    {copyLabel}
                  </button>
                  {onClearResolve && (
                    <button
                      onClick={onClearResolve}
                      style={{
                        border: '1px solid var(--cm-border-cool)',
                        background: 'transparent',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 600,
                        fontFamily: 'Raleway, sans-serif',
                        color: 'var(--cm-text-secondary)',
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
                      fontSize: 12,
                      fontFamily: 'Raleway, sans-serif',
                      opacity: node.trim === 'skipped' ? 0.4 : node.trim === 'summary' ? 0.65 : 1,
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: 12,
                        color: 'var(--cm-text-tertiary)',
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
                        node.trim === 'full' ? 'var(--cm-success)' :
                        node.trim === 'summary' ? 'var(--cm-warning)' : 'var(--cm-text-tertiary)',
                      flexShrink: 0,
                    }}/>
                    <code
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: 12,
                        color: 'var(--cm-text-primary)',
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
                        fontSize: 12,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                        color:
                          node.trim === 'full' ? 'var(--cm-success)' :
                          node.trim === 'summary' ? 'var(--cm-warning)' : 'var(--cm-text-tertiary)',
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
              color: 'var(--cm-text-primary)',
              lineHeight: 1.7,
            }}
          >
            {memory.body ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {memory.body}
              </ReactMarkdown>
            ) : (
              <p style={{ color: 'var(--cm-text-tertiary)', fontStyle: 'italic' }}>No content</p>
            )}
          </div>
        </>
        )}
      </div>
    </>
  )
}
