import { useCallback, useEffect, useState } from 'react'
import { applyReview, fetchReviews } from '../api'
import type { PatchProposalReview, ProposedAtomReview, ReviewQueueResponse } from '../types'

interface Props {
  datasetReady: boolean
  refreshTrigger: number
  onSelectMemory: (id: string) => void
  onChanged: () => void
  onError: (message: string) => void
}

type ReviewKind = 'atoms' | 'patches'

const buttonStyle: React.CSSProperties = {
  border: '1px solid var(--cm-border-cool)',
  backgroundColor: 'var(--cm-bg-surface)',
  color: 'var(--cm-text-primary)',
  padding: '6px 12px',
  borderRadius: 2,
  cursor: 'pointer',
  fontFamily: 'Raleway, sans-serif',
  fontSize: 12,
  fontWeight: 600,
}

export default function ReviewPage({ datasetReady, refreshTrigger, onSelectMemory, onChanged, onError }: Props) {
  const [queue, setQueue] = useState<ReviewQueueResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [pending, setPending] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!datasetReady) return
    setLoading(true)
    setLoadError(null)
    try {
      setQueue(await fetchReviews())
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Unable to load review queue')
    } finally {
      setLoading(false)
    }
  }, [datasetReady])

  useEffect(() => {
    // Queue refresh is the external synchronization performed by this view.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load()
  }, [load, refreshTrigger])

  const act = async (kind: ReviewKind, action: 'merge' | 'reject', id: string) => {
    const verb = action === 'merge' ? 'accept and merge' : 'reject'
    if (!window.confirm(`Are you sure you want to ${verb} “${id}”?`)) return
    const key = `${kind}:${action}:${id}`
    setPending(key)
    try {
      await applyReview(kind, action, id)
      await load()
      onChanged()
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Review action failed')
    } finally {
      setPending(null)
    }
  }

  return (
    <main style={{ flex: 1, overflow: 'auto', padding: '28px 32px', backgroundColor: 'var(--cm-bg-primary)' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 16, marginBottom: 24 }}>
          <div>
            <h2 style={{ margin: 0, fontFamily: 'Cormorant Garamond, serif', fontSize: 30, fontWeight: 500 }}>Owner Review</h2>
            <p style={{ margin: '6px 0 0', color: 'var(--cm-text-secondary)', fontSize: 13 }}>
              Proposed atoms and patch proposals stay separate. Nothing becomes canonical until you merge it.
            </p>
          </div>
          <button type="button" onClick={() => void load()} disabled={loading} style={buttonStyle}>Refresh</button>
        </div>

        {!datasetReady && <Notice text="Select a dataset to review its pending changes." />}
        {loading && !queue && <Notice text="Loading review queue…" />}
        {loadError && <Notice text={loadError} tone="error" />}
        {queue && queue.total === 0 && <Notice text="Review queue is empty." />}

        {queue && (
          <div style={{ display: 'grid', gap: 28 }}>
            <ReviewSection title={`Proposed Atoms (${queue.proposed_atoms.length})`} description="New atoms waiting for an owner decision.">
              {queue.proposed_atoms.map((item) => (
                <AtomCard key={item.id} item={item} pending={pending} onSelectMemory={onSelectMemory} onAct={act} />
              ))}
            </ReviewSection>
            <ReviewSection title={`Patch Proposals (${queue.patch_proposals.length})`} description="Changes proposed against existing canonical atoms.">
              {queue.patch_proposals.map((item) => (
                <PatchCard key={item.id} item={item} pending={pending} onSelectMemory={onSelectMemory} onAct={act} />
              ))}
            </ReviewSection>
          </div>
        )}
      </div>
    </main>
  )
}

function ReviewSection({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  const empty = !Array.isArray(children) || children.length === 0
  return (
    <section>
      <h3 style={{ margin: 0, fontSize: 15, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{title}</h3>
      <p style={{ margin: '5px 0 12px', color: 'var(--cm-text-tertiary)', fontSize: 12 }}>{description}</p>
      <div style={{ display: 'grid', gap: 10 }}>{empty ? <Notice text="No items in this queue." /> : children}</div>
    </section>
  )
}

function AtomCard({ item, pending, onSelectMemory, onAct }: {
  item: ProposedAtomReview
  pending: string | null
  onSelectMemory: (id: string) => void
  onAct: (kind: ReviewKind, action: 'merge' | 'reject', id: string) => void
}) {
  return (
    <ReviewCard id={item.id} target={item.target_id} subtitle={item.summary} meta={`${item.created_by} · ${item.tags.join(', ') || 'no tags'} · v${item.version} · ${item.created_at}`}>
      <ActionButtons kind="atoms" id={item.id} pending={pending} onAct={onAct} onInspect={() => onSelectMemory(item.target_id)} />
    </ReviewCard>
  )
}

function PatchCard({ item, pending, onSelectMemory, onAct }: {
  item: PatchProposalReview
  pending: string | null
  onSelectMemory: (id: string) => void
  onAct: (kind: ReviewKind, action: 'merge' | 'reject', id: string) => void
}) {
  return (
    <ReviewCard id={item.id} target={item.target_id} subtitle={item.reason} meta={`${item.created_by} · ${item.created_at}`}>
      <div style={{ fontSize: 12, color: 'var(--cm-text-secondary)' }}>Fields: {item.patch_fields.join(', ') || 'none'}</div>
      <pre style={{ margin: '8px 0 0', padding: 10, overflow: 'auto', backgroundColor: 'var(--cm-bg-subtle)', fontSize: 11 }}>
        {JSON.stringify(item.patch, null, 2)}
      </pre>
      <ActionButtons kind="patches" id={item.id} pending={pending} onAct={onAct} onInspect={() => onSelectMemory(item.target_id)} />
    </ReviewCard>
  )
}

function ReviewCard({ id, target, subtitle, meta, children }: { id: string; target: string; subtitle: string; meta: string; children: React.ReactNode }) {
  return (
    <article style={{ border: '1px solid var(--cm-border)', backgroundColor: 'var(--cm-bg-surface)', padding: 16, borderRadius: 2 }}>
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600 }}>{id}</div>
      <div style={{ marginTop: 4, fontSize: 13 }}>{subtitle || 'No summary provided'}</div>
      <div style={{ marginTop: 5, color: 'var(--cm-text-tertiary)', fontSize: 11 }}>Target: {target} · {meta}</div>
      <div style={{ marginTop: 12 }}>{children}</div>
    </article>
  )
}

function ActionButtons({ kind, id, pending, onAct, onInspect }: {
  kind: ReviewKind
  id: string
  pending: string | null
  onAct: (kind: ReviewKind, action: 'merge' | 'reject', id: string) => void
  onInspect: () => void
}) {
  const busy = pending?.endsWith(`:${id}`) ?? false
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
      <button type="button" onClick={onInspect} disabled={busy} style={buttonStyle}>Inspect Target</button>
      <button type="button" onClick={() => onAct(kind, 'merge', id)} disabled={busy} style={{ ...buttonStyle, backgroundColor: 'var(--cm-accent)', color: 'var(--cm-text-inverse)', borderColor: 'var(--cm-accent)' }}>Merge</button>
      <button type="button" onClick={() => onAct(kind, 'reject', id)} disabled={busy} style={{ ...buttonStyle, color: 'var(--cm-error)' }}>Reject</button>
    </div>
  )
}

function Notice({ text, tone = 'neutral' }: { text: string; tone?: 'neutral' | 'error' }) {
  return <div style={{ padding: 18, border: '1px solid var(--cm-border)', color: tone === 'error' ? 'var(--cm-error)' : 'var(--cm-text-secondary)', backgroundColor: 'var(--cm-bg-surface)', fontSize: 13 }}>{text}</div>
}
