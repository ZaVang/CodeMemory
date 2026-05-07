/** Shared badge components used across MemoryDetail, MemoryList, and other views. */

const MaturityStyles: Record<string, { bg: string; color: string }> = {
  draft:        { bg: 'var(--cm-bg-subtle)',  color: 'var(--cm-text-secondary)' },
  verified:     { bg: 'var(--cm-bg-info-subtle)', color: 'var(--cm-info)' },
  proven:       { bg: 'var(--cm-bg-success-subtle)', color: 'var(--cm-success)' },
  superseded:   { bg: 'var(--cm-bg-subtle)',  color: 'var(--cm-text-tertiary)' },
}

const StatusStyles: Record<string, { bg: string; color: string; label: string }> = {
  active:   { bg: 'var(--cm-bg-success-subtle)', color: 'var(--cm-success)', label: 'active' },
  draft:    { bg: 'var(--cm-bg-subtle)',  color: 'var(--cm-text-secondary)', label: 'draft' },
  archived: { bg: 'var(--cm-bg-subtle)',  color: 'var(--cm-text-tertiary)', label: 'archived' },
}

interface BadgeBaseOptions {
  /** Override padding. Detail view uses 2px 10px; List view uses 1px 8px. */
  padding?: string
  /** Override font size. Detail view uses 12px; List view uses 10px. */
  fontSize?: number
}

export function MaturityBadge({ maturity, opts = {} }: { maturity: string; opts?: BadgeBaseOptions }) {
  const s = MaturityStyles[maturity] || MaturityStyles.draft
  return (
    <span
      style={{
        display: 'inline-block',
        padding: opts.padding ?? '2px 10px',
        borderRadius: 2,
        fontSize: opts.fontSize ?? 12,
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

export function StatusBadge({ status, opts = {} }: { status: string; opts?: BadgeBaseOptions }) {
  const s = StatusStyles[status] || StatusStyles.draft
  return (
    <span
      style={{
        display: 'inline-block',
        padding: opts.padding ?? '2px 10px',
        borderRadius: 2,
        fontSize: opts.fontSize ?? 12,
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
