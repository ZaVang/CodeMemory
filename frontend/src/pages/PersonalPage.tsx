import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  applyPersonalReviewBatch,
  fetchPersonalCaptures,
  fetchPersonalOverview,
  fetchPersonalTimeline,
  fetchPersonalTopics,
} from '../api'
import type {
  PersonalCapturePage,
  PersonalOverview,
  PersonalReviewDecision,
  PersonalTimeline,
  PersonalTopic,
} from '../types'

interface Props {
  datasetReady: boolean
  refreshTrigger: number
  onChanged: () => void
  onError: (message: string) => void
}

const buttonStyle: React.CSSProperties = {
  border: '1px solid var(--cm-border-cool)',
  backgroundColor: 'var(--cm-bg-surface)',
  color: 'var(--cm-text-primary)',
  padding: '7px 12px',
  borderRadius: 2,
  cursor: 'pointer',
  fontFamily: 'Raleway, sans-serif',
  fontSize: 12,
  fontWeight: 600,
}

export default function PersonalPage({ datasetReady, refreshTrigger, onChanged, onError }: Props) {
  const [overview, setOverview] = useState<PersonalOverview | null>(null)
  const [captures, setCaptures] = useState<PersonalCapturePage | null>(null)
  const [topics, setTopics] = useState<PersonalTopic[]>([])
  const [selectedRevision, setSelectedRevision] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<PersonalTimeline | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [decisions, setDecisions] = useState<Record<string, PersonalReviewDecision>>({})
  const [draftAction, setDraftAction] = useState<PersonalReviewDecision['action']>('promote')
  const [atomId, setAtomId] = useState('')
  const [mergeTarget, setMergeTarget] = useState('')
  const [previewOpen, setPreviewOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const selectedTopic = useMemo(
    () => topics.find((topic) => topic.revision_id === selectedRevision) ?? topics[0] ?? null,
    [topics, selectedRevision],
  )
  const queued = useMemo(() => Object.values(decisions), [decisions])

  const load = useCallback(async () => {
    if (!datasetReady) return
    setLoading(true)
    setLoadError(null)
    try {
      const [nextOverview, nextCaptures, nextTopics] = await Promise.all([
        fetchPersonalOverview(),
        fetchPersonalCaptures(),
        fetchPersonalTopics(),
      ])
      setOverview(nextOverview)
      setCaptures(nextCaptures)
      setTopics(nextTopics)
      setSelectedRevision((current) => (
        nextTopics.some((item) => item.revision_id === current)
          ? current
          : nextTopics[0]?.revision_id ?? null
      ))
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Unable to load Personal workspace')
    } finally {
      setLoading(false)
    }
  }, [datasetReady])

  useEffect(() => {
    // Personal workspace synchronization is isolated to this view.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load()
  }, [load, refreshTrigger])

  useEffect(() => {
    if (!selectedTopic) return
    let active = true
    fetchPersonalTimeline(selectedTopic.topic_id)
      .then((value) => { if (active) setTimeline(value) })
      .catch((error) => { if (active) onError(error instanceof Error ? error.message : 'Unable to load timeline') })
    return () => { active = false }
  }, [selectedTopic, onError])

  const selectTopic = (topic: PersonalTopic) => {
    setTimeline(null)
    setSelectedRevision(topic.revision_id)
    setDraftAction(decisions[topic.revision_id]?.action ?? 'promote')
    setAtomId(decisions[topic.revision_id]?.atom_id ?? '')
    setMergeTarget(decisions[topic.revision_id]?.target_revision_id ?? '')
  }

  const queueDecision = () => {
    if (!selectedTopic) return
    const decision: PersonalReviewDecision = {
      action: draftAction,
      revision_id: selectedTopic.revision_id,
      ...(draftAction === 'promote' ? { atom_id: atomId.trim() } : {}),
      ...(draftAction === 'merge' ? { target_revision_id: mergeTarget } : {}),
    }
    if (draftAction === 'promote' && !decision.atom_id) {
      onError('Canonical Atom ID is required for promotion')
      return
    }
    if (draftAction === 'merge' && !decision.target_revision_id) {
      onError('A distinct target revision is required for merge')
      return
    }
    setDecisions((current) => ({ ...current, [selectedTopic.revision_id]: decision }))
  }

  const confirmBatch = async () => {
    if (queued.length === 0) return
    setSubmitting(true)
    try {
      await applyPersonalReviewBatch(queued)
      setPreviewOpen(false)
      setDecisions({})
      await load()
      onChanged()
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Personal review batch failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main style={{ flex: 1, overflow: 'auto', padding: '28px 32px', backgroundColor: 'var(--cm-bg-primary)' }}>
      <div style={{ maxWidth: 1440, margin: '0 auto' }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 16, marginBottom: 22 }}>
          <div>
            <div style={{ color: 'var(--cm-accent)', fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              Owner workspace
            </div>
            <h2 style={{ margin: '4px 0 0', fontFamily: 'Cormorant Garamond, serif', fontSize: 34, fontWeight: 500 }}>
              Personal Memory
            </h2>
            <p style={{ margin: '6px 0 0', color: 'var(--cm-text-secondary)', fontSize: 13 }}>
              Trace raw captures into evolving topics, then confirm one concentrated review batch.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" onClick={() => void load()} disabled={loading} style={buttonStyle}>Refresh</button>
            <button
              type="button"
              onClick={() => setPreviewOpen(true)}
              disabled={queued.length === 0}
              style={{ ...buttonStyle, backgroundColor: 'var(--cm-accent)', color: 'var(--cm-text-inverse)', borderColor: 'var(--cm-accent)' }}
            >
              Review batch ({queued.length})
            </button>
          </div>
        </header>

        {!datasetReady && <Notice text="Select a Personal dataset to open this workspace." />}
        {loading && !overview && <Notice text="Loading Personal workspace…" />}
        {loadError && <Notice text={loadError} tone="error" />}

        {overview && (
          <>
            <section aria-label="Personal overview" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(100px, 1fr))', gap: 10, marginBottom: 18 }}>
              <Metric label="Captures" value={overview.capture_count} />
              <Metric label="Topics" value={overview.topic_count} />
              <Metric label="Claims" value={overview.claim_count} />
              <Metric label="Canonical" value={overview.canonical_count} />
              <Metric label="Diagnostics" value={overview.diagnostics_count} />
            </section>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(250px, 0.8fr) minmax(280px, 0.9fr) minmax(360px, 1.35fr)', gap: 14, alignItems: 'start' }}>
              <Panel title={`Capture feed (${captures?.total ?? 0})`} subtitle="Hash-valid, append-only source records">
                {!captures?.items.length && <Quiet text="No valid captures yet." />}
                <div style={{ display: 'grid', gap: 9 }}>
                  {captures?.items.map((capture) => (
                    <article key={capture.id} style={{ borderTop: '1px solid var(--cm-border)', paddingTop: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: 10, color: 'var(--cm-text-tertiary)' }}>
                        <span>{formatDate(capture.captured_at)}</span>
                        <span>{capture.actor}</span>
                      </div>
                      <div style={{ whiteSpace: 'pre-wrap', marginTop: 6, fontSize: 12, lineHeight: 1.55 }}>{capture.content}</div>
                      <code style={{ display: 'block', marginTop: 7, fontSize: 9, color: 'var(--cm-text-tertiary)', wordBreak: 'break-all' }}>{capture.id}</code>
                    </article>
                  ))}
                </div>
              </Panel>

              <Panel title={`Incubator topics (${topics.length})`} subtitle="Long-lived synthesis with stable revision IDs">
                {topics.length === 0 && <Quiet text="No incubator topics yet." />}
                <div style={{ display: 'grid', gap: 8 }}>
                  {topics.map((topic) => {
                    const active = selectedTopic?.revision_id === topic.revision_id
                    const pending = decisions[topic.revision_id]
                    return (
                      <button
                        type="button"
                        key={topic.revision_id}
                        onClick={() => selectTopic(topic)}
                        style={{
                          textAlign: 'left',
                          padding: 12,
                          border: `1px solid ${active ? 'var(--cm-accent)' : 'var(--cm-border)'}`,
                          background: active ? 'var(--cm-bg-subtle)' : 'var(--cm-bg-surface)',
                          color: 'var(--cm-text-primary)',
                          cursor: 'pointer',
                        }}
                      >
                        <div style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 19, fontWeight: 600 }}>{topic.title}</div>
                        <div style={{ marginTop: 5, fontSize: 10, color: 'var(--cm-text-tertiary)' }}>
                          {topic.origin} · {topic.claims.length} claims · {formatDate(topic.updated_at ?? topic.created_at)}
                        </div>
                        {pending && (
                          <span style={{ display: 'inline-block', marginTop: 7, color: 'var(--cm-accent)', fontSize: 10, fontWeight: 700, textTransform: 'uppercase' }}>
                            Queued: {pending.action}
                          </span>
                        )}
                      </button>
                    )
                  })}
                </div>
              </Panel>

              <div style={{ display: 'grid', gap: 14 }}>
                <Panel title={selectedTopic?.title ?? 'Topic detail'} subtitle={selectedTopic?.revision_id ?? 'Select a topic'}>
                  {!selectedTopic && <Quiet text="Select a topic to inspect its claims and provenance." />}
                  {selectedTopic && (
                    <>
                      <div style={{ whiteSpace: 'pre-wrap', fontSize: 12, lineHeight: 1.65, maxHeight: 280, overflow: 'auto' }}>{selectedTopic.content}</div>
                      {selectedTopic.claims.map((claim) => (
                        <article key={claim.claim_id} style={{ marginTop: 12, padding: 12, background: 'var(--cm-bg-subtle)', borderLeft: '3px solid var(--cm-accent)' }}>
                          <div style={{ fontSize: 12, fontWeight: 700 }}>{claim.title}</div>
                          <div style={{ marginTop: 3, fontSize: 10, color: 'var(--cm-text-tertiary)' }}>{claim.claim_status} · {claim.origin}</div>
                          <div style={{ marginTop: 7, fontSize: 12, lineHeight: 1.5 }}>{claim.content}</div>
                        </article>
                      ))}
                      <ReviewComposer
                        topic={selectedTopic}
                        topics={topics}
                        action={draftAction}
                        atomId={atomId}
                        mergeTarget={mergeTarget}
                        onAction={setDraftAction}
                        onAtomId={setAtomId}
                        onMergeTarget={setMergeTarget}
                        onQueue={queueDecision}
                        onRemove={() => setDecisions((current) => {
                          const next = { ...current }
                          delete next[selectedTopic.revision_id]
                          return next
                        })}
                        queued={Boolean(decisions[selectedTopic.revision_id])}
                      />
                    </>
                  )}
                </Panel>

                <Panel title="Idea timeline" subtitle="Authored timestamps and explicit provenance only">
                  {!timeline?.events.length && <Quiet text="No explicit timeline events for this topic." />}
                  <div style={{ display: 'grid', gap: 8 }}>
                    {timeline?.events.map((event) => (
                      <div key={event.id} style={{ display: 'grid', gridTemplateColumns: '100px 1fr', gap: 10, borderTop: '1px solid var(--cm-border)', paddingTop: 8 }}>
                        <div style={{ fontSize: 10, color: 'var(--cm-text-tertiary)' }}>{formatDate(event.timestamp)}</div>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--cm-accent)' }}>{event.kind.replace('_', ' ')}</div>
                          <div style={{ fontSize: 12, marginTop: 2 }}>{event.title}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Panel>
              </div>
            </div>
          </>
        )}
      </div>

      {previewOpen && (
        <div role="dialog" aria-modal="true" aria-label="Confirm Personal review batch" style={{ position: 'fixed', inset: 0, zIndex: 300, background: 'rgba(20,18,16,0.48)', display: 'grid', placeItems: 'center', padding: 24 }}>
          <div style={{ width: 'min(620px, 100%)', maxHeight: '80vh', overflow: 'auto', background: 'var(--cm-bg-surface)', border: '1px solid var(--cm-border)', padding: 24, boxShadow: '0 20px 70px rgba(0,0,0,.25)' }}>
            <h3 style={{ margin: 0, fontFamily: 'Cormorant Garamond, serif', fontSize: 28 }}>Confirm one owner batch</h3>
            <p style={{ color: 'var(--cm-text-secondary)', fontSize: 12 }}>Review every decision below. Confirmation applies the complete batch once.</p>
            <ol style={{ paddingLeft: 22 }}>
              {queued.map((decision) => (
                <li key={decision.revision_id} style={{ marginBottom: 10, fontSize: 12 }}>
                  <strong>{decision.action}</strong> {decision.revision_id}
                  {decision.atom_id ? ` → ${decision.atom_id}` : ''}
                  {decision.target_revision_id ? ` → ${decision.target_revision_id}` : ''}
                </li>
              ))}
            </ol>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button type="button" onClick={() => setPreviewOpen(false)} disabled={submitting} style={buttonStyle}>Cancel</button>
              <button
                type="button"
                onClick={() => void confirmBatch()}
                disabled={submitting}
                style={{ ...buttonStyle, background: 'var(--cm-accent)', color: 'var(--cm-text-inverse)', borderColor: 'var(--cm-accent)' }}
              >
                {submitting ? 'Applying…' : 'Confirm batch'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

function ReviewComposer({ topic, topics, action, atomId, mergeTarget, onAction, onAtomId, onMergeTarget, onQueue, onRemove, queued }: {
  topic: PersonalTopic
  topics: PersonalTopic[]
  action: PersonalReviewDecision['action']
  atomId: string
  mergeTarget: string
  onAction: (value: PersonalReviewDecision['action']) => void
  onAtomId: (value: string) => void
  onMergeTarget: (value: string) => void
  onQueue: () => void
  onRemove: () => void
  queued: boolean
}) {
  return (
    <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--cm-border)' }}>
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Prepare owner decision</div>
      <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
        <select value={action} onChange={(event) => onAction(event.target.value as PersonalReviewDecision['action'])} style={{ ...buttonStyle, minWidth: 110 }}>
          <option value="promote">Promote</option>
          <option value="merge">Merge</option>
          <option value="delete">Delete</option>
        </select>
        {action === 'promote' && (
          <input aria-label="Canonical Atom ID" value={atomId} onChange={(event) => onAtomId(event.target.value)} placeholder="memory/ideas/atom-id" style={{ ...buttonStyle, cursor: 'text', flex: 1, minWidth: 190 }} />
        )}
        {action === 'merge' && (
          <select aria-label="Merge target revision" value={mergeTarget} onChange={(event) => onMergeTarget(event.target.value)} style={{ ...buttonStyle, flex: 1 }}>
            <option value="">Choose target revision</option>
            {topics.filter((item) => item.revision_id !== topic.revision_id).map((item) => (
              <option key={item.revision_id} value={item.revision_id}>{item.title} · {item.revision_id}</option>
            ))}
          </select>
        )}
        <button type="button" onClick={onQueue} style={{ ...buttonStyle, background: 'var(--cm-text-primary)', color: 'var(--cm-text-inverse)' }}>Queue decision</button>
        {queued && <button type="button" onClick={onRemove} style={{ ...buttonStyle, color: 'var(--cm-error)' }}>Remove</button>}
      </div>
    </div>
  )
}

function Panel({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section style={{ border: '1px solid var(--cm-border)', background: 'var(--cm-bg-surface)', padding: 16 }}>
      <h3 style={{ margin: 0, fontFamily: 'Cormorant Garamond, serif', fontSize: 22, fontWeight: 600 }}>{title}</h3>
      <p style={{ margin: '3px 0 14px', fontSize: 10, color: 'var(--cm-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{subtitle}</p>
      {children}
    </section>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ border: '1px solid var(--cm-border)', background: 'var(--cm-bg-surface)', padding: '14px 16px' }}>
      <div style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 27 }}>{value}</div>
      <div style={{ color: 'var(--cm-text-tertiary)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em' }}>{label}</div>
    </div>
  )
}

function Quiet({ text }: { text: string }) {
  return <div style={{ color: 'var(--cm-text-tertiary)', fontSize: 12, padding: '12px 0' }}>{text}</div>
}

function Notice({ text, tone = 'neutral' }: { text: string; tone?: 'neutral' | 'error' }) {
  return <div style={{ padding: 18, border: '1px solid var(--cm-border)', color: tone === 'error' ? 'var(--cm-error)' : 'var(--cm-text-secondary)', backgroundColor: 'var(--cm-bg-surface)', fontSize: 13 }}>{text}</div>
}

function formatDate(value?: string | null) {
  if (!value) return 'unknown time'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}
