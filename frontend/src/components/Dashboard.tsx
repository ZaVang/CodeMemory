import { useState, useEffect, useCallback } from 'react'
import { fetchStats, fetchWander, fetchValidate, fetchReindex } from '../api'
import type { StatsResponse, WanderResponse, ValidateResponse } from '../types'

interface Props {
  onSelectMemory: (id: string) => void
  onNavigateToFilter?: (filter: string, type: 'tag' | 'maturity') => void
  refreshTrigger?: number
}

export default function Dashboard({ onSelectMemory, onNavigateToFilter, refreshTrigger }: Props) {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [wanderResult, setWanderResult] = useState<WanderResponse | null>(null)
  const [validateResult, setValidateResult] = useState<ValidateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [wanderOpen, setWanderOpen] = useState(false)
  const [validateOpen, setValidateOpen] = useState(false)
  const [wandering, setWandering] = useState(false)
  const [validating, setValidating] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const [wanderMode, setWanderMode] = useState<'cool' | 'random'>('cool')

  const loadData = useCallback(() => {
    setLoading(true)
    fetchStats()
      .then(setStats)
      .catch(console.error)
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
    fetchWander(wanderMode)
      .then((result) => {
        setWanderResult(result)
        setWanderOpen(true)
      })
      .catch(console.error)
      .finally(() => setWandering(false))
  }, [wanderMode])

  const handleValidate = useCallback(() => {
    setValidating(true)
    fetchValidate()
      .then((result) => {
        setValidateResult(result)
        setValidateOpen(true)
      })
      .catch(console.error)
      .finally(() => setValidating(false))
  }, [])

  const handleReindex = useCallback(() => {
    setReindexing(true)
    fetchReindex()
      .then(() => loadData())
      .catch(console.error)
      .finally(() => setReindexing(false))
  }, [loadData])

  // --- Render ---

  const maturityColors: Record<string, string> = {
    draft: '#57534E',
    verified: '#1E40AF',
    proven: '#166534',
    superseded: '#A8A29E',
  }

  const maturityOrder = ['draft', 'verified', 'proven', 'superseded']

  return (
    <div
      style={{
        height: '100%',
        overflowY: 'auto',
        padding: '32px',
        backgroundColor: '#FFFBEB',
      }}
    >
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
            color: '#1C1917',
            margin: 0,
            letterSpacing: '0.01em',
          }}
        >
          Dashboard
        </h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {/* Wander mode toggle */}
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
              onClick={() => setWanderMode('cool')}
              style={{
                padding: '6px 14px',
                border: 'none',
                cursor: 'pointer',
                fontSize: 11,
                fontFamily: 'Raleway, sans-serif',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                backgroundColor: wanderMode === 'cool' ? '#B8860B' : 'transparent',
                color: wanderMode === 'cool' ? '#FFFBEB' : '#57534E',
              }}
            >
              Cool
            </button>
            <button
              onClick={() => setWanderMode('random')}
              style={{
                padding: '6px 14px',
                border: 'none',
                cursor: 'pointer',
                fontSize: 11,
                fontFamily: 'Raleway, sans-serif',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                backgroundColor: wanderMode === 'random' ? '#B8860B' : 'transparent',
                color: wanderMode === 'random' ? '#FFFBEB' : '#57534E',
              }}
            >
              Random
            </button>
          </div>
          <button
            onClick={handleWander}
            disabled={wandering}
            style={{
              padding: '10px 24px',
              border: '1px solid #B8860B',
              background: 'transparent',
              color: '#B8860B',
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
              border: '1px solid #1E40AF',
              background: 'transparent',
              color: '#1E40AF',
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
              border: '1px solid #D4D4D8',
              background: 'transparent',
              color: '#57534E',
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
              border: '1px solid #CA8A04',
              background: 'transparent',
              color: '#CA8A04',
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

      {loading && (
        <p style={{ color: '#A8A29E', fontFamily: 'Raleway, sans-serif', fontSize: 14 }}>
          Loading...
        </p>
      )}

      {stats && !loading && stats.total === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: '64px 32px',
            backgroundColor: '#FFFFFF',
            borderRadius: 2,
            border: '1px solid #F5F5F4',
            boxShadow: '0 1px 2px rgba(28,25,23,0.04)',
          }}
        >
          <div
            style={{
              fontSize: 48,
              color: '#D4D4D8',
              marginBottom: 16,
              fontFamily: "'Cormorant Garamond', serif",
            }}
          >
            +
          </div>
          <h3
            style={{
              fontSize: 18,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: '#1C1917',
              margin: '0 0 8px 0',
            }}
          >
            No memories yet
          </h3>
          <p
            style={{
              fontSize: 14,
              fontFamily: 'Raleway, sans-serif',
              color: '#A8A29E',
              margin: '0 0 24px 0',
              lineHeight: 1.6,
            }}
          >
            Create your first memory to get started.
          </p>
        </div>
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
            <StatCard label="Total Memories" value={stats.total} color="#1C1917" />
            <StatCard label="Stale" value={stats.stale_count} color="#991B1B" />
            <StatCard label="Proven" value={stats.maturity?.proven ?? 0} color="#166534" />
            <StatCard label="Draft" value={stats.maturity?.draft ?? 0} color="#57534E" />
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
                          color: maturityColors[key] || '#57534E',
                          minWidth: 90,
                        }}
                      >
                        {key}
                      </span>
                      <div
                        style={{
                          flex: 1,
                          height: 8,
                          backgroundColor: '#F5F5F4',
                          borderRadius: 2,
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${pct}%`,
                            backgroundColor: maturityColors[key] || '#57534E',
                            borderRadius: 2,
                            transition: 'width 300ms ease',
                          }}
                        />
                      </div>
                      <span
                        style={{
                          fontSize: 12,
                          fontFamily: 'JetBrains Mono, monospace',
                          color: '#57534E',
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
                      backgroundColor: '#F5F5F4',
                      fontSize: 12,
                      fontFamily: 'Raleway, sans-serif',
                      color: '#1C1917',
                      fontWeight: 500,
                      cursor: 'pointer',
                      transition: 'background-color 100ms ease',
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLSpanElement).style.backgroundColor = '#E7E5E4' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLSpanElement).style.backgroundColor = '#F5F5F4' }}
                  >
                    {tag}
                    <span
                      style={{
                        fontSize: 10,
                        color: '#A8A29E',
                        fontFamily: 'JetBrains Mono, monospace',
                      }}
                    >
                      {count}
                    </span>
                  </span>
                ))}
                {stats.tags.length === 0 && (
                  <span style={{ fontSize: 12, color: '#A8A29E', fontFamily: 'Raleway, sans-serif' }}>
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
                      backgroundColor: '#991B1B08',
                      borderLeft: '3px solid #991B1B',
                    }}
                  >
                    <div>
                      <div
                        style={{
                          fontSize: 13,
                          fontFamily: 'Raleway, sans-serif',
                          fontWeight: 600,
                          color: '#1C1917',
                        }}
                      >
                        {memId}
                      </div>
                      <div
                        style={{
                          fontSize: 11,
                          fontFamily: 'JetBrains Mono, monospace',
                          color: '#A8A29E',
                          marginTop: 2,
                        }}
                      >
                        {memId}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 2,
                          backgroundColor: '#991B1B15',
                          color: '#991B1B',
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
                    backgroundColor: status === 'active' ? '#16653415' : status === 'archived' ? '#F5F5F4' : '#F5F5F4',
                    borderLeft: `3px solid ${status === 'active' ? '#166534' : status === 'archived' ? '#A8A29E' : '#57534E'}`,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      fontFamily: 'Raleway, sans-serif',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      color: '#57534E',
                    }}
                  >
                    {status}
                  </div>
                  <div
                    style={{
                      fontSize: 20,
                      fontFamily: "'Cormorant Garamond', serif",
                      color: '#1C1917',
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
              color: '#1C1917',
              margin: '0 0 16px 0',
            }}
          >
            Wander Recall
          </h2>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: '#A8A29E', fontFamily: 'Raleway, sans-serif', marginBottom: 4 }}>
              Memory ID
            </div>
            <div
              style={{
                fontSize: 13,
                fontFamily: 'JetBrains Mono, monospace',
                color: '#1C1917',
                padding: '8px 12px',
                backgroundColor: '#F5F5F4',
                borderRadius: 2,
                wordBreak: 'break-all',
              }}
            >
              {wanderResult.id}
            </div>
          </div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: '#A8A29E', fontFamily: 'Raleway, sans-serif', marginBottom: 4 }}>
              Summary
            </div>
            <p style={{ fontSize: 14, color: '#1C1917', fontFamily: 'Raleway, sans-serif', lineHeight: 1.6, margin: 0 }}>
              {wanderResult.summary}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12, fontSize: 12, fontFamily: 'Raleway, sans-serif', color: '#57534E', marginBottom: 16 }}>
            <span>Type: {wanderResult.type}</span>
            <span>Intensity: {wanderResult.intensity}/10</span>
            <span>Access: {wanderResult.access_count}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => onSelectMemory(wanderResult.id)}
              style={{
                padding: '8px 20px',
                backgroundColor: '#1C1917',
                color: '#FFFBEB',
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
              onClick={() => setWanderOpen(false)}
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
              color: '#1C1917',
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
                backgroundColor: '#16653415',
                borderLeft: '3px solid #166534',
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'Raleway, sans-serif' }}>
                Checked
              </div>
              <div style={{ fontSize: 22, fontFamily: "'Cormorant Garamond', serif", color: '#1C1917' }}>
                {validateResult.validated_count}
              </div>
            </div>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 2,
                backgroundColor: validateResult.error_count > 0 ? '#991B1B15' : '#16653415',
                borderLeft: `3px solid ${validateResult.error_count > 0 ? '#991B1B' : '#166534'}`,
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'Raleway, sans-serif' }}>
                Errors
              </div>
              <div style={{ fontSize: 22, fontFamily: "'Cormorant Garamond', serif", color: '#1C1917' }}>
                {validateResult.error_count}
              </div>
            </div>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 2,
                backgroundColor: validateResult.warning_count > 0 ? '#CA8A0415' : '#16653415',
                borderLeft: `3px solid ${validateResult.warning_count > 0 ? '#CA8A04' : '#166534'}`,
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 600, color: '#57534E', textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'Raleway, sans-serif' }}>
                Warnings
              </div>
              <div style={{ fontSize: 22, fontFamily: "'Cormorant Garamond', serif", color: '#1C1917' }}>
                {validateResult.warning_count}
              </div>
            </div>
          </div>

          {validateResult.errors.length === 0 && validateResult.warnings.length === 0 && (
            <div
              style={{
                padding: '16px',
                backgroundColor: '#16653410',
                borderRadius: 2,
                color: '#166534',
                fontSize: 14,
                fontFamily: 'Raleway, sans-serif',
              }}
            >
              All checks passed. No issues found.
            </div>
          )}

          {validateResult.errors.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontFamily: 'Raleway, sans-serif', fontWeight: 600, color: '#991B1B', marginBottom: 8 }}>
                Errors ({validateResult.errors.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {validateResult.errors.map((err, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '6px 10px',
                      backgroundColor: '#991B1B0A',
                      borderLeft: '3px solid #991B1B',
                      borderRadius: 2,
                      fontSize: 12,
                      fontFamily: 'Raleway, sans-serif',
                      color: '#1C1917',
                    }}
                  >
                    {err.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {validateResult.warnings.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontFamily: 'Raleway, sans-serif', fontWeight: 600, color: '#CA8A04', marginBottom: 8 }}>
                Warnings ({validateResult.warnings.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {validateResult.warnings.map((warn, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '6px 10px',
                      backgroundColor: '#CA8A040A',
                      borderLeft: '3px solid #CA8A04',
                      borderRadius: 2,
                      fontSize: 12,
                      fontFamily: 'Raleway, sans-serif',
                      color: '#1C1917',
                    }}
                  >
                    <span style={{ fontSize: 10, color: '#A8A29E', marginRight: 6 }}>
                      [{warn.type}]
                    </span>
                    {warn.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={() => setValidateOpen(false)}
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
        backgroundColor: '#FFFFFF',
        borderRadius: 2,
        border: '1px solid #F5F5F4',
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
          color: '#A8A29E',
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
        backgroundColor: '#FFFFFF',
        borderRadius: 2,
        border: '1px solid #F5F5F4',
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
          color: '#57534E',
          margin: '0 0 16px 0',
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  )
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
          backgroundColor: '#FFFBEB',
          border: '1px solid #E7E5E4',
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
