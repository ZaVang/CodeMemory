import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchStats, fetchWander, fetchValidate, fetchReindex } from '../api'
import type { StatsResponse, WanderResponse, ValidateResponse } from '../types'
import EmptyState from './EmptyState'

interface Props {
  onSelectMemory: (id: string) => void
  onNavigateToFilter?: (filter: string, type: 'tag' | 'maturity') => void
  refreshTrigger?: number
  onCreateMemory?: () => void
  /** Called when an operation fails, to display user-visible error feedback */
  onError?: (message: string) => void
}

export default function Dashboard({ onSelectMemory, onNavigateToFilter, refreshTrigger, onCreateMemory, onError }: Props) {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [wanderResult, setWanderResult] = useState<WanderResponse | null>(null)
  const [validateResult, setValidateResult] = useState<ValidateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [wanderOpen, setWanderOpen] = useState(false)
  const [validateOpen, setValidateOpen] = useState(false)
  const [wandering, setWandering] = useState(false)
  const [validating, setValidating] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const [reindexMessage, setReindexMessage] = useState<string | null>(null)
  const reindexTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const loadData = useCallback(() => {
    setLoading(true)
    fetchStats()
      .then(setStats)
      .catch((err) => onError?.(err instanceof Error ? err.message : 'Failed to load stats'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData, refreshTrigger])

  // Stale memories are identified by the backend via body-hash comparison.
  // We use stale_ids from the stats response (PL1-1 fix).
  const staleIds = stats?.stale_ids ?? []

  const handleWander = useCallback(() => {
    setWandering(true)
    setValidateOpen(false)  // R11-B2: prevent modal stacking
    fetchWander('cool')
      .then((result) => {
        setWanderResult(result)
        setWanderOpen(true)
      })
      .catch((err) => onError?.(err instanceof Error ? err.message : 'Wander failed'))
      .finally(() => setWandering(false))
  }, [])

  const handleValidate = useCallback(() => {
    setValidating(true)
    setWanderOpen(false)  // R11-B2: prevent modal stacking
    fetchValidate()
      .then((result) => {
        setValidateResult(result)
        setValidateOpen(true)
      })
      .catch((err) => onError?.(err instanceof Error ? err.message : 'Validate failed'))
      .finally(() => setValidating(false))
  }, [])

  const handleReindex = useCallback(() => {
    setReindexing(true)
    setReindexMessage(null)
    fetchReindex()
      .then((res) => {
        const count = (res as Record<string, unknown>)?.count
        const msg = typeof count === 'number' ? `Reindexed ${count} memories` : 'Reindex completed'
        setReindexMessage(msg)
        if (reindexTimerRef.current) clearTimeout(reindexTimerRef.current)
        reindexTimerRef.current = setTimeout(() => setReindexMessage(null), 4000)
        loadData()
      })
      .catch((err) => {
        setReindexMessage('Reindex failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
        if (reindexTimerRef.current) clearTimeout(reindexTimerRef.current)
        reindexTimerRef.current = setTimeout(() => setReindexMessage(null), 6000)
        onError?.(err instanceof Error ? err.message : 'Reindex failed')
      })
      .finally(() => setReindexing(false))
  }, [loadData, onError])

  // --- Render ---

  const maturityColors: Record<string, string> = {
    draft: 'var(--cm-text-secondary)',
    verified: 'var(--cm-info)',
    proven: 'var(--cm-success)',
    superseded: 'var(--cm-text-tertiary)',
  }

  const maturityOrder = ['draft', 'verified', 'proven', 'superseded']

  return (
    <div
      style={{
        height: '100%',
        overflowY: 'auto',
        padding: '32px',
        backgroundColor: 'var(--cm-bg-primary)',
      }}
    >
      {/* Reindex feedback toast */}
      {reindexMessage && (
        <div
          style={{
            padding: '10px 24px',
            marginBottom: 16,
            backgroundColor: reindexMessage.startsWith('Reindex failed') ? 'var(--cm-bg-error-subtle)' : 'var(--cm-bg-success-subtle)',
            color: reindexMessage.startsWith('Reindex failed') ? 'var(--cm-error)' : 'var(--cm-success)',
            borderRadius: 2,
            fontSize: 13,
            fontFamily: 'Raleway, sans-serif',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderLeft: `3px solid ${reindexMessage.startsWith('Reindex failed') ? 'var(--cm-error)' : 'var(--cm-success)'}`,
          }}
        >
          <span>{reindexMessage}</span>
          <button
            onClick={() => setReindexMessage(null)}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              color: 'inherit',
              fontSize: 14,
              opacity: 0.7,
              padding: '0 4px',
            }}
          >
            x
          </button>
        </div>
      )}

      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 32,
        }}
      >
        <h1
          style={{
            fontSize: 32,
            fontFamily: "'Cormorant Garamond', serif",
            fontWeight: 500,
            color: 'var(--cm-text-primary)',
            margin: 0,
            letterSpacing: '0.01em',
          }}
        >
          Dashboard
        </h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button
            onClick={handleWander}
            disabled={wandering}
            title="Surfaces a memory you haven't revisited recently"
            style={{
              padding: '10px 24px',
              border: '1px solid var(--cm-accent)',
              background: 'transparent',
              color: 'var(--cm-accent)',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              borderRadius: 2,
            }}
          >
            {wandering ? 'Wandering...' : 'Wander'}
          </button>
          <button
            onClick={handleValidate}
            disabled={validating}
            style={{
              padding: '10px 24px',
              border: '1px solid var(--cm-info)',
              background: 'transparent',
              color: 'var(--cm-info)',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              borderRadius: 2,
            }}
          >
            {validating ? 'Validating...' : 'Validate'}
          </button>
          <button
            onClick={loadData}
            style={{
              padding: '10px 24px',
              border: '1px solid var(--cm-border-cool)',
              background: 'transparent',
              color: 'var(--cm-text-secondary)',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              borderRadius: 2,
            }}
          >
            Refresh
          </button>
          <button
            onClick={handleReindex}
            disabled={reindexing}
            style={{
              padding: '10px 24px',
              border: '1px solid var(--cm-warning)',
              background: 'transparent',
              color: 'var(--cm-warning)',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              borderRadius: 2,
            }}
          >
            {reindexing ? 'Reindexing...' : 'Reindex'}
          </button>
        </div>
      </div>

      {loading && <DashboardSkeleton />}

      {stats && !loading && stats.total === 0 && (
        <EmptyState
          title="No memories yet"
          description="Create your first memory to get started."
          actions={onCreateMemory ? [{ label: 'Create Memory', onClick: onCreateMemory, variant: 'primary' }] : undefined}
        />
      )}

      {stats && !loading && stats.total > 0 && (
        <>
          {/* Stat cards row */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: 16,
              marginBottom: 32,
            }}
          >
            <StatCard label="Total Memories" value={stats.total} color="var(--cm-text-primary)" />
            <StatCard label="Stale" value={stats.stale_count} color="var(--cm-error)" />
            <StatCard label="Proven" value={stats.maturity?.proven ?? 0} color="var(--cm-success)" />
            <StatCard label="Draft" value={stats.maturity?.draft ?? 0} color="var(--cm-text-secondary)" />
          </div>

          {/* Two-column layout for maturity distribution + tags */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 24,
              marginBottom: 32,
            }}
          >
            {/* Maturity distribution */}
            <SectionCard title="Maturity Distribution">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {maturityOrder.map((key) => {
                  const count = stats.maturity?.[key] ?? 0
                  if (count === 0) return null
                  const maxVal = Math.max(...Object.values(stats.maturity ?? {}), 1)
                  const pct = Math.round((count / maxVal) * 100)
                  return (
                    <div
                      key={key}
                      onClick={() => onNavigateToFilter?.(key, 'maturity')}
                      title={`Filter by maturity: ${key}`}
                      style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer', padding: '2px 0' }}
                    >
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          fontFamily: 'Raleway, sans-serif',
                          textTransform: 'uppercase',
                          letterSpacing: '0.06em',
                          color: maturityColors[key] || 'var(--cm-text-secondary)',
                          minWidth: 90,
                        }}
                      >
                        {key}
                      </span>
                      <div
                        style={{
                          flex: 1,
                          height: 8,
                          backgroundColor: 'var(--cm-bg-subtle)',
                          borderRadius: 2,
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${pct}%`,
                            backgroundColor: maturityColors[key] || 'var(--cm-text-secondary)',
                            borderRadius: 2,
                            transition: 'width 300ms ease',
                          }}
                        />
                      </div>
                      <span
                        style={{
                          fontSize: 12,
                          fontFamily: 'JetBrains Mono, monospace',
                          color: 'var(--cm-text-secondary)',
                          minWidth: 24,
                          textAlign: 'right',
                        }}
                      >
                        {count}
                      </span>
                    </div>
                  )
                })}
              </div>
            </SectionCard>

            {/* Tag frequency */}
            <SectionCard title="Top Tags">
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {stats.tags.slice(0, 15).map(({ tag, count }) => (
                  <span
                    key={tag}
                    onClick={() => onNavigateToFilter?.(tag, 'tag')}
                    title={`Filter by tag: ${tag}`}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '4px 12px',
                      borderRadius: 2,
                      backgroundColor: 'var(--cm-bg-subtle)',
                      fontSize: 12,
                      fontFamily: 'Raleway, sans-serif',
                      color: 'var(--cm-text-primary)',
                      fontWeight: 500,
                      cursor: 'pointer',
                      transition: 'background-color 100ms ease',
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLSpanElement).style.backgroundColor = 'var(--cm-border)' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLSpanElement).style.backgroundColor = 'var(--cm-bg-subtle)' }}
                  >
                    {tag}
                    <span
                      style={{
                        fontSize: 10,
                        color: 'var(--cm-text-tertiary)',
                        fontFamily: 'JetBrains Mono, monospace',
                      }}
                    >
                      {count}
                    </span>
                  </span>
                ))}
                {stats.tags.length === 0 && (
                  <span style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif' }}>
                    No tags found
                  </span>
                )}
              </div>
            </SectionCard>
          </div>

          {/* Stale memories section */}
          {staleIds.length > 0 && (
            <SectionCard title={`Stale Memories (${staleIds.length})`}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {staleIds.map((memId) => (
                  <div
                    key={memId}
                    onClick={() => onSelectMemory(memId)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      borderRadius: 2,
                      cursor: 'pointer',
                      backgroundColor: 'var(--cm-bg-error-subtle)',
                      borderLeft: '3px solid var(--cm-error)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 13,
                        fontFamily: 'Raleway, sans-serif',
                        fontWeight: 600,
                        color: 'var(--cm-text-primary)',
                      }}
                    >
                      {memId}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 2,
                          backgroundColor: 'var(--cm-bg-error-subtle)',
                          color: 'var(--cm-error)',
                          fontSize: 10,
                          fontWeight: 600,
                          fontFamily: 'Raleway, sans-serif',
                          textTransform: 'uppercase',
                        }}
                      >
                        stale
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>
          )}

          {/* Status distribution */}
          <SectionCard title="Status Distribution">
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {Object.entries(stats.status ?? {}).map(([status, count]) => (
                <div
                  key={status}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 2,
                    backgroundColor: status === 'active' ? 'var(--cm-bg-success-subtle)' : status === 'archived' ? 'var(--cm-bg-subtle)' : 'var(--cm-bg-subtle)',
                    borderLeft: `3px solid ${status === 'active' ? 'var(--cm-success)' : status === 'archived' ? 'var(--cm-text-tertiary)' : 'var(--cm-text-secondary)'}`,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      fontFamily: 'Raleway, sans-serif',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      color: 'var(--cm-text-secondary)',
                    }}
                  >
                    {status}
                  </div>
                  <div
                    style={{
                      fontSize: 20,
                      fontFamily: "'Cormorant Garamond', serif",
                      color: 'var(--cm-text-primary)',
                    }}
                  >
                    {count}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </>
      )}

      {/* Wander modal */}
      {wanderOpen && wanderResult && (
        <Modal onClose={() => setWanderOpen(false)}>
          <h2
            style={{
              fontSize: 20,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: 'var(--cm-text-primary)',
              margin: '0 0 4px 0',
            }}
          >
            Wander Recall
          </h2>
          <p style={{
            fontSize: 12,
            fontFamily: 'Raleway, sans-serif',
            color: 'var(--cm-text-tertiary)',
            margin: '0 0 20px 0',
            fontStyle: 'italic',
            lineHeight: 1.5,
          }}>
            Surfaces a memory you haven&rsquo;t revisited recently.
          </p>

          {/* Why this memory? */}
          <div style={{
            marginBottom: 16,
            padding: '12px 16px',
            backgroundColor: 'var(--cm-bg-surface)',
            borderRadius: 2,
            border: '1px solid var(--cm-bg-subtle)',
          }}>
            <div style={{
              fontSize: 10,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--cm-text-secondary)',
              marginBottom: 10,
            }}>
              Why this memory?
            </div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 8 }}>
              <div>
                <span style={{ fontSize: 10, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif' }}>Access Count: </span>
                <span style={{ fontSize: 13, fontFamily: 'JetBrains Mono, monospace', color: 'var(--cm-text-primary)', fontWeight: 600 }}>
                  {wanderResult.access_count}
                  {wanderResult.access_count === 0 && (
                    <span style={{ fontSize: 10, fontWeight: 400, color: 'var(--cm-text-tertiary)', marginLeft: 4 }}>(never accessed)</span>
                  )}
                </span>
              </div>
              <div>
                <span style={{ fontSize: 10, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif' }}>Intensity: </span>
                <span style={{ fontSize: 13, fontFamily: 'JetBrains Mono, monospace', color: 'var(--cm-text-primary)', fontWeight: 600 }}>
                  {wanderResult.intensity}/10
                  {wanderResult.intensity >= 8 && (
                    <span style={{ fontSize: 10, fontWeight: 400, color: 'var(--cm-info)', marginLeft: 4 }}>(protected)</span>
                  )}
                </span>
              </div>
              <div>
                <span style={{ fontSize: 10, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif' }}>Last Access: </span>
                <span style={{ fontSize: 13, fontFamily: 'JetBrains Mono, monospace', color: 'var(--cm-text-primary)', fontWeight: 600 }}>
                  {wanderResult.last_access ? new Date(wanderResult.last_access).toLocaleDateString() : 'never'}
                </span>
              </div>
            </div>
            <p style={{
              fontSize: 11,
              fontFamily: 'Raleway, sans-serif',
              color: 'var(--cm-text-tertiary)',
              margin: '4px 0 0 0',
              lineHeight: 1.4,
            }}>
              {wanderResult.access_count === 0
                ? 'This memory has never been accessed — it may contain overlooked insights.'
                : wanderResult.last_access
                  ? `Last accessed ${_daysAgo(wanderResult.last_access)} days ago. Revisiting cold memories prevents knowledge decay.`
                  : 'Low-access memories are surfaced to prevent knowledge silos.'}
            </p>
          </div>

          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif', marginBottom: 4 }}>
              Memory ID
            </div>
            <div
              style={{
                fontSize: 13,
                fontFamily: 'JetBrains Mono, monospace',
                color: 'var(--cm-text-primary)',
                padding: '8px 12px',
                backgroundColor: 'var(--cm-bg-subtle)',
                borderRadius: 2,
                wordBreak: 'break-all',
              }}
            >
              {wanderResult.id}
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif', marginBottom: 4 }}>
              Summary
            </div>
            <p style={{ fontSize: 14, color: 'var(--cm-text-primary)', fontFamily: 'Raleway, sans-serif', lineHeight: 1.6, margin: 0 }}>
              {wanderResult.summary}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => onSelectMemory(wanderResult.id)}
              style={{
                padding: '8px 20px',
                backgroundColor: 'var(--cm-text-primary)',
                color: 'var(--cm-bg-primary)',
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
              View Details
            </button>
            <button
              onClick={() => {
                setWandering(true)
                fetchWander('cool')
                  .then((result) => {
                    setWanderResult(result)
                  })
                  .catch((err) => onError?.(err instanceof Error ? err.message : 'Wander failed'))
                  .finally(() => setWandering(false))
              }}
              style={{
                padding: '8px 20px',
                border: '1px solid var(--cm-accent)',
                background: 'transparent',
                color: 'var(--cm-accent)',
                cursor: 'pointer',
                fontSize: 11,
                fontWeight: 600,
                fontFamily: 'Raleway, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                borderRadius: 2,
              }}
            >
              Wander Again
            </button>
            <button
              onClick={() => setWanderOpen(false)}
              style={{
                padding: '8px 20px',
                border: '1px solid var(--cm-border-cool)',
                background: 'transparent',
                color: 'var(--cm-text-secondary)',
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
        </Modal>
      )}

      {/* Validate results modal */}
      {validateOpen && validateResult && (
        <Modal onClose={() => setValidateOpen(false)}>
          <h2
            style={{
              fontSize: 20,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: 'var(--cm-text-primary)',
              margin: '0 0 16px 0',
            }}
          >
            Validation Results
          </h2>
          <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 2,
                backgroundColor: 'var(--cm-bg-success-subtle)',
                borderLeft: '3px solid var(--cm-success)',
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--cm-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'Raleway, sans-serif' }}>
                Checked
              </div>
              <div style={{ fontSize: 22, fontFamily: "'Cormorant Garamond', serif", color: 'var(--cm-text-primary)' }}>
                {validateResult.validated_count}
              </div>
            </div>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 2,
                backgroundColor: validateResult.error_count > 0 ? 'var(--cm-bg-error-subtle)' : 'var(--cm-bg-success-subtle)',
                borderLeft: `3px solid ${validateResult.error_count > 0 ? 'var(--cm-error)' : 'var(--cm-success)'}`,
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--cm-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'Raleway, sans-serif' }}>
                Errors
              </div>
              <div style={{ fontSize: 22, fontFamily: "'Cormorant Garamond', serif", color: 'var(--cm-text-primary)' }}>
                {validateResult.error_count}
              </div>
            </div>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 2,
                backgroundColor: validateResult.warning_count > 0 ? 'var(--cm-bg-warning-subtle)' : 'var(--cm-bg-success-subtle)',
                borderLeft: `3px solid ${validateResult.warning_count > 0 ? 'var(--cm-warning)' : 'var(--cm-success)'}`,
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--cm-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'Raleway, sans-serif' }}>
                Warnings
              </div>
              <div style={{ fontSize: 22, fontFamily: "'Cormorant Garamond', serif", color: 'var(--cm-text-primary)' }}>
                {validateResult.warning_count}
              </div>
            </div>
          </div>

          {validateResult.errors.length === 0 && validateResult.warnings.length === 0 && (
            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--cm-bg-success-subtle)',
                borderRadius: 2,
                color: 'var(--cm-success)',
                fontSize: 14,
                fontFamily: 'Raleway, sans-serif',
              }}
            >
              All checks passed. No issues found.
            </div>
          )}

          {validateResult.errors.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontFamily: 'Raleway, sans-serif', fontWeight: 600, color: 'var(--cm-error)', marginBottom: 8 }}>
                Errors ({validateResult.errors.length})
              </h3>
              {renderGroupedIssues(validateResult.errors, 'error', onSelectMemory)}
            </div>
          )}

          {validateResult.warnings.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontFamily: 'Raleway, sans-serif', fontWeight: 600, color: 'var(--cm-warning)', marginBottom: 8 }}>
                Warnings ({validateResult.warnings.length})
              </h3>
              {renderGroupedIssues(validateResult.warnings, 'warning', onSelectMemory)}
            </div>
          )}

          <button
            onClick={() => setValidateOpen(false)}
            style={{
              padding: '8px 20px',
              border: '1px solid var(--cm-border-cool)',
              background: 'transparent',
              color: 'var(--cm-text-secondary)',
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
        </Modal>
      )}
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div
      style={{
        padding: '20px 24px',
        backgroundColor: 'var(--cm-bg-surface)',
        borderRadius: 2,
        border: '1px solid var(--cm-bg-subtle)',
        boxShadow: '0 1px 2px rgba(28,25,23,0.04)',
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          fontFamily: 'Raleway, sans-serif',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: 'var(--cm-text-tertiary)',
          marginBottom: 8,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 36,
          fontFamily: "'Cormorant Garamond', serif",
          fontWeight: 500,
          color,
          lineHeight: 1,
        }}
      >
        {value}
      </div>
    </div>
  )
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        padding: '20px 24px',
        backgroundColor: 'var(--cm-bg-surface)',
        borderRadius: 2,
        border: '1px solid var(--cm-bg-subtle)',
        boxShadow: '0 1px 2px rgba(28,25,23,0.04)',
      }}
    >
      <h3
        style={{
          fontSize: 13,
          fontWeight: 600,
          fontFamily: 'Raleway, sans-serif',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: 'var(--cm-text-secondary)',
          margin: '0 0 16px 0',
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  )
}

function _daysAgo(isoDate: string): number {
  const then = new Date(isoDate).getTime()
  const now = Date.now()
  return Math.max(0, Math.floor((now - then) / (1000 * 60 * 60 * 24)))
}

// R9-validate-drilldown: Regex for memory IDs like "user/facts/name", "api/endpoint", "schemas/template"
const MEMORY_ID_RE = /\b([a-zA-Z][a-zA-Z0-9_-]*(?:\/[a-zA-Z][a-zA-Z0-9_-]*)+\b)/g

/** Split a validate message into text segments and memory-ID segments for clickable rendering */
function parseMessageLinks(message: string): Array<{ text: string; isId: boolean }> {
  const parts: Array<{ text: string; isId: boolean }> = []
  let lastIndex = 0
  const re = new RegExp(MEMORY_ID_RE.source, 'g')
  let match: RegExpExecArray | null

  while ((match = re.exec(message)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ text: message.slice(lastIndex, match.index), isId: false })
    }
    parts.push({ text: match[1], isId: true })
    lastIndex = match.index + match[1].length
  }

  if (lastIndex < message.length) {
    parts.push({ text: message.slice(lastIndex), isId: false })
  }

  return parts.length > 0 ? parts : [{ text: message, isId: false }]
}

/** Return a human-readable label for a validate issue type */
function getIssueTypeLabel(type: string): string {
  switch (type) {
    case 'broken_link': return 'Broken Link'
    case 'schema_compliance': return 'Schema Compliance'
    case 'error': return 'Error'
    case 'warning': return 'Circular Dependency'
    case 'maturity': return 'Maturity Stale'
    case 'decay': return 'Decay Risk'
    default: return type
  }
}

/** Type color by issue category */
function issueTypeColor(type: string): string {
  if (type === 'broken_link' || type === 'schema_compliance' || type === 'error') return 'var(--cm-error)'
  if (type === 'maturity') return 'var(--cm-info)'
  if (type === 'decay') return 'var(--cm-warning)'
  return 'var(--cm-warning)'
}

interface ValidateResultItem {
  type: string
  message: string
}

/** Group issues by type, render each group with a label and clickable memory IDs */
function renderGroupedIssues(
  items: ValidateResultItem[],
  _category: string,
  onSelectMemory: (id: string) => void,
) {
  const grouped = new Map<string, ValidateResultItem[]>()
  for (const item of items) {
    const key = item.type
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(item)
  }

  return Array.from(grouped.entries()).map(([type, groupItems]) => (
    <div key={type} style={{ marginBottom: 14 }}>
      <div style={{
        fontSize: 10,
        fontWeight: 600,
        fontFamily: 'Raleway, sans-serif',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        color: issueTypeColor(type),
        marginBottom: 6,
        paddingLeft: 2,
      }}>
        {getIssueTypeLabel(type)} ({groupItems.length})
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {groupItems.map((item, i) => (
          <div
            key={i}
            style={{
              padding: '6px 10px',
              backgroundColor: type.includes('error') || type === 'broken_link' || type === 'schema_compliance'
                ? 'var(--cm-bg-error-subtle)'
                : 'var(--cm-bg-warning-subtle)',
              borderLeft: `3px solid ${issueTypeColor(type)}`,
              borderRadius: 2,
              fontSize: 12,
              fontFamily: 'Raleway, sans-serif',
              color: 'var(--cm-text-primary)',
              lineHeight: 1.5,
            }}
          >
            {parseMessageLinks(item.message).map((part, j) =>
              part.isId ? (
                <span
                  key={j}
                  onClick={(e) => { e.stopPropagation(); onSelectMemory(part.text) }}
                  title={`View ${part.text}`}
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 11,
                    color: 'var(--cm-accent)',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    textUnderlineOffset: '2px',
                  }}
                >
                  {part.text}
                </span>
              ) : (
                <span key={j}>{part.text}</span>
              ),
            )}
          </div>
        ))}
      </div>
    </div>
  ))
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <>
      <div
        onClick={onClose}
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
          backgroundColor: 'var(--cm-bg-primary)',
          border: '1px solid var(--cm-border)',
          borderRadius: 2,
          padding: 28,
          maxWidth: 560,
          width: '90%',
          maxHeight: '80vh',
          overflowY: 'auto',
          zIndex: 101,
          boxShadow: '0 4px 24px rgba(28,25,23,0.12)',
        }}
      >
        {children}
      </div>
    </>
  )
}

// ── R9-loading-skeletons: Dashboard skeleton ─────────────────────────

function DashboardSkeleton() {
  const cardSkeleton = (height: number) => ({
    padding: '20px 24px',
    backgroundColor: 'var(--cm-bg-surface)',
    borderRadius: 2,
    border: '1px solid var(--cm-bg-subtle)',
    height,
  })

  return (
    <div style={{ padding: '32px', backgroundColor: 'var(--cm-bg-primary)' }}>
      {/* Header row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 32,
      }}>
        <div className="skeleton-shimmer" style={{ width: 180, height: 32, borderRadius: 2 }} />
        <div style={{ display: 'flex', gap: 12 }}>
          <div className="skeleton-shimmer" style={{ width: 100, height: 40, borderRadius: 2 }} />
          <div className="skeleton-shimmer" style={{ width: 100, height: 40, borderRadius: 2 }} />
          <div className="skeleton-shimmer" style={{ width: 100, height: 40, borderRadius: 2 }} />
        </div>
      </div>

      {/* Stat cards row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 16,
        marginBottom: 32,
      }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={cardSkeleton(80)}>
            <div className="skeleton-shimmer" style={{ width: '60%', height: 12, borderRadius: 2, marginBottom: 10 }} />
            <div className="skeleton-shimmer" style={{ width: 50, height: 32, borderRadius: 2 }} />
          </div>
        ))}
      </div>

      {/* Two-column layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 24,
        marginBottom: 32,
      }}>
        {/* Maturity Distribution skeleton */}
        <div style={cardSkeleton(180)}>
          <div className="skeleton-shimmer" style={{ width: 140, height: 14, borderRadius: 2, marginBottom: 16 }} />
          {[1, 2, 3, 4].map((i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <div className="skeleton-shimmer" style={{ width: 80, height: 12, borderRadius: 2 }} />
              <div className="skeleton-shimmer" style={{ flex: 1, height: 8, borderRadius: 2 }} />
              <div className="skeleton-shimmer" style={{ width: 24, height: 12, borderRadius: 2 }} />
            </div>
          ))}
        </div>

        {/* Top Tags skeleton */}
        <div style={cardSkeleton(180)}>
          <div className="skeleton-shimmer" style={{ width: 100, height: 14, borderRadius: 2, marginBottom: 16 }} />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="skeleton-shimmer" style={{ width: 70 + (i * 10), height: 26, borderRadius: 2 }} />
            ))}
          </div>
        </div>
      </div>

      {/* Status distribution skeleton */}
      <div style={cardSkeleton(80)}>
        <div className="skeleton-shimmer" style={{ width: 140, height: 14, borderRadius: 2, marginBottom: 12 }} />
        <div style={{ display: 'flex', gap: 16 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton-shimmer" style={{ width: 120, height: 40, borderRadius: 2 }} />
          ))}
        </div>
      </div>
    </div>
  )
}
