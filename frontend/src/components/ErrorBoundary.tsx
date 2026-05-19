import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  label?: string
}

interface State {
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught render failure:', error, info)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div
        role="alert"
        style={{
          height: '100%',
          padding: 32,
          backgroundColor: 'var(--cm-bg-primary)',
          color: 'var(--cm-text-primary)',
          fontFamily: 'Raleway, sans-serif',
        }}
      >
        <h2
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 28,
            fontWeight: 500,
            margin: '0 0 12px 0',
          }}
        >
          {this.props.label ?? 'This panel failed to render'}
        </h2>
        <p style={{ margin: '0 0 16px 0', color: 'var(--cm-text-secondary)' }}>
          The rest of CodeMemory is still running. Close or switch views, then retry the action.
        </p>
        <pre
          style={{
            padding: 16,
            backgroundColor: 'var(--cm-bg-subtle)',
            border: '1px solid var(--cm-border)',
            whiteSpace: 'pre-wrap',
            fontSize: 12,
            color: 'var(--cm-error)',
          }}
        >
          {this.state.error.message}
        </pre>
      </div>
    )
  }
}
