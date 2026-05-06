/** Shared badge components used across MemoryDetail, MemoryList, and other views. */

const MaturityStyles: Record<string, { bg: string; color: string }> = {
  draft:        { bg: '#F5F5F4',  color: '#57534E' },
  verified:     { bg: '#1E40AF15', color: '#1E40AF' },
  proven:       { bg: '#16653415', color: '#166534' },
  superseded:   { bg: '#F5F5F4',  color: '#A8A29E' },
}

const StatusStyles: Record<string, { bg: string; color: string; label: string }> = {
  active:   { bg: '#16653420', color: '#166534', label: 'active' },
  draft:    { bg: '#F5F5F4',  color: '#57534E', label: 'draft' },
  archived: { bg: '#F5F5F4',  color: '#A8A29E', label: 'archived' },
}

interface BadgeBaseOptions {
  /** Override padding. Detail view uses 2px 10px; List view uses 1px 8px. */
  padding?: string
  /** Override font size. Detail view uses 11px; List view uses 10px. */
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
        fontSize: opts.fontSize ?? 11,
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
        fontSize: opts.fontSize ?? 11,
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
