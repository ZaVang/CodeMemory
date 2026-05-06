/** Shared empty state component used by Graph, List, and Dashboard views. */

interface Action {
  label: string
  onClick: () => void
  /** Optional visual style: 'primary' (accent button) or 'secondary' (outlined) */
  variant?: 'primary' | 'secondary'
}

interface Props {
  icon?: string
  title: string
  description: string
  actions?: Action[]
}

export default function EmptyState({ icon = '+', title, description, actions }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '64px 32px',
        textAlign: 'center',
        height: '100%',
      }}
    >
      <div
        style={{
          fontSize: 48,
          color: 'var(--cm-border-cool)',
          marginBottom: 16,
          fontFamily: "'Cormorant Garamond', serif",
        }}
      >
        {icon}
      </div>
      <h3
        style={{
          fontSize: 18,
          fontFamily: "'Cormorant Garamond', serif",
          fontWeight: 500,
          color: 'var(--cm-text-primary)',
          margin: '0 0 8px 0',
        }}
      >
        {title}
      </h3>
      <p
        style={{
          fontSize: 14,
          fontFamily: 'Raleway, sans-serif',
          color: 'var(--cm-text-tertiary)',
          margin: '0 0 24px 0',
          lineHeight: 1.6,
          maxWidth: 420,
        }}
      >
        {description}
      </p>
      {actions && actions.length > 0 && (
        <div style={{ display: 'flex', gap: 10 }}>
          {actions.map((action) => (
            <button
              key={action.label}
              onClick={action.onClick}
              style={{
                padding: '10px 24px',
                border: action.variant === 'secondary'
                  ? '1px solid var(--cm-border-cool)'
                  : 'none',
                background: action.variant === 'secondary'
                  ? 'transparent'
                  : 'var(--cm-accent)',
                color: action.variant === 'secondary'
                  ? 'var(--cm-text-secondary)'
                  : 'var(--cm-text-inverse)',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'Raleway, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                borderRadius: 2,
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
