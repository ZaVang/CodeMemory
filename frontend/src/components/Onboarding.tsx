import { useState, useEffect } from 'react'

/** Static descriptions for known datasets. Falls back to name + memory count. */
const KNOWN_DATASET_DESCRIPTIONS: Record<string, string> = {
  investment: 'interconnected memories about financial decisions, market analysis, and risk assessment',
  companion: 'personal journal entries capturing habits, feelings, beliefs, and important people in your life',
  'software-architecture': 'concepts and decisions about software design patterns, architectural styles, and system composition',
  quant_operators: 'trading strategies, quantitative operations, and algorithmic decision-making signals',
}

/** Simplified resolve result for onboarding demo display */
export interface OnboardingResolveDemo {
  nodeCount: number
  target: string
  fullCount: number
  summaryCount: number
  skippedCount: number
}

interface Props {
  onComplete: () => void
  datasetName?: string
  datasetCount?: number
  /** R19-C2: callback to trigger a resolve demo. Returns simplified result or null on failure. */
  onDemoResolve?: () => Promise<OnboardingResolveDemo | null>
}

// R12-P1: SVG geometric icons for each onboarding step
const StepIcon = ({ step }: { step: number }) => {
  const size = 32
  const color = 'var(--cm-accent)'
  const strokeW = 2
  switch (step) {
    case 0: // Welcome — star
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" />
        </svg>
      )
    case 1: // Graph View — circle (node)
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="8" />
          <circle cx="12" cy="12" r="3" />
          <line x1="12" y1="4" x2="12" y2="9" />
          <line x1="20" y1="8" x2="17" y2="10.5" strokeDasharray="2 1" />
        </svg>
      )
    case 2: // Resolve — arrow / dependency
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="7" cy="7" r="3" />
          <circle cx="17" cy="17" r="3" />
          <line x1="9.5" y1="8.5" x2="14.5" y2="13.5" />
          <polyline points="16,15 14.5,13.5 16,12" />
        </svg>
      )
    case 3: // Create — plus
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="8" />
          <line x1="12" y1="8" x2="12" y2="16" />
          <line x1="8" y1="12" x2="16" y2="12" />
        </svg>
      )
    case 4: // You're Ready — checkmark in circle
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="8" />
          <polyline points="8,12 11,15 16,9" />
        </svg>
      )
    default:
      return null
  }
}

const BASE_STEPS = [
  // Step 0 is dynamically built in the component
  null as unknown as { title: string; subtitle: string; description: string },
  {
    title: 'Graph View',
    subtitle: 'Explore your memory network visually.',
    description:
      'Each circle is a memory. Color = category, size = importance. Solid lines mean required dependencies (must-read), dashed lines are recommended, dotted lines are related. Click a node to see details. Right-click to Edit or Archive.',
  },
  {
    title: 'Build',
    subtitle: 'Reconstruct the full context of any idea.',
    description:
      'Click "Build" in the detail panel to assemble canonical context through imports. The graph animates through the dependency chain in topological order. Use the Budget slider to control how much context to load.',
  },
  {
    title: 'Create Memories',
    subtitle: 'Build your knowledge graph.',
    description:
      'Click "Create Memory" to create a memory. Give it an ID (e.g. "user/ideas/my-thought"), add tags, set importance (1–10), and write your content in Markdown. Add imports to link it to existing memories.',
  },
  {
    title: "You're Ready",
    subtitle: 'Start building your memory network.',
    description:
      'The Dashboard shows statistics and health checks. Switch datasets from the header dropdown. Press Escape to close panels. The Help button (top-right) has full reference documentation.',
  },
]

export default function Onboarding({ onComplete, datasetName, datasetCount, onDemoResolve }: Props) {
  // Build steps with dataset-aware welcome step
  const hasDataset = !!datasetName && datasetCount != null && datasetCount > 0
  const datasetDesc = datasetName ? (KNOWN_DATASET_DESCRIPTIONS[datasetName] || '') : ''

  const welcomeStep = hasDataset && datasetDesc
    ? {
        title: 'Welcome to CodeMemory',
        subtitle: `You are viewing the ${datasetName} dataset`,
        description:
          `This dataset contains ${datasetCount} ${datasetDesc}. CodeMemory organizes knowledge as interconnected "atoms" — small, self-contained memories linked by explicit dependencies. Think of it as a personal knowledge graph where every piece of information knows what it depends on.`,
      }
    : hasDataset
    ? {
        title: 'Welcome to CodeMemory',
        subtitle: `You are viewing the ${datasetName} dataset (${datasetCount} memories)`,
        description:
          'CodeMemory organizes knowledge as interconnected "atoms" — small, self-contained memories linked by explicit dependencies. Think of it as a personal knowledge graph where every piece of information knows what it depends on.',
      }
    : {
        title: 'Welcome to CodeMemory',
        subtitle: 'Your memory is a dependency graph, not a search index.',
        description:
          'CodeMemory organizes knowledge as interconnected "atoms" — small, self-contained memories linked by explicit dependencies. Think of it as a personal knowledge graph where every piece of information knows what it depends on.',
      }

  const STEPS = [welcomeStep, ...BASE_STEPS.slice(1)]

  const [step, setStep] = useState(0)
  const current = STEPS[step]
  const isLast = step === STEPS.length - 1

  // R19-C2: resolve demo state
  const [demoResult, setDemoResult] = useState<OnboardingResolveDemo | null>(null)
  const [demoLoading, setDemoLoading] = useState(false)
  const [demoFailed, setDemoFailed] = useState(false)

  // Trigger resolve demo when user reaches the Resolve step (step 2)
  useEffect(() => {
    if (step !== 2 || demoResult || demoLoading || demoFailed || !onDemoResolve) return
    // Only trigger for the investment dataset (the canonical demo dataset with a known entry point)
    if (datasetName !== 'investment') return

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDemoLoading(true)
    onDemoResolve()
      .then((result) => {
        if (result) {
          setDemoResult(result)
        } else {
          setDemoFailed(true)
        }
      })
      .catch(() => setDemoFailed(true))
      .finally(() => setDemoLoading(false))
  }, [step, datasetName, demoResult, demoLoading, demoFailed, onDemoResolve])

  return (
    <>
      {/* Backdrop */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(28,25,23,0.6)',
          zIndex: 300,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            backgroundColor: 'var(--cm-bg-primary)',
            borderRadius: 2,
            padding: 40,
            maxWidth: 520,
            width: '90%',
            textAlign: 'center',
            boxShadow: '0 8px 40px rgba(28,25,23,0.18)',
          }}
        >
          {/* Step icon */}
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              backgroundColor: 'var(--cm-bg-hover)',
              border: '2px solid var(--cm-accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 24px',
            }}
          >
            <StepIcon step={step} />
          </div>

          {/* Title */}
          <h2
            style={{
              fontSize: 24,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: 'var(--cm-text-primary)',
              margin: '0 0 8px 0',
            }}
          >
            {current.title}
          </h2>

          {/* Subtitle */}
          <h3
            style={{
              fontSize: 16,
              fontFamily: 'Raleway, sans-serif',
              fontWeight: 600,
              color: 'var(--cm-accent)',
              margin: '0 0 16px 0',
              lineHeight: 1.5,
            }}
          >
            {current.subtitle}
          </h3>

          {/* Description */}
          <p
            style={{
              fontSize: 14,
              fontFamily: 'Raleway, sans-serif',
              color: 'var(--cm-text-secondary)',
              lineHeight: 1.7,
              margin: '0 0 28px 0',
            }}
          >
            {current.description}
          </p>

          {/* R19-C2: resolve demo result display */}
          {step === 2 && (
            <div
              style={{
                margin: '0 0 24px 0',
                padding: '12px 16px',
                borderRadius: 2,
                border: '1px solid var(--cm-border)',
                backgroundColor: 'var(--cm-bg-subtle)',
                textAlign: 'left',
              }}
            >
              {demoLoading && (
                <div style={{ fontSize: 13, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-tertiary)' }}>
                  Resolving <code style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>user/investment/context</code>...
                </div>
              )}

              {demoFailed && (
                <div style={{ fontSize: 13, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-secondary)' }}>
                  <strong style={{ color: 'var(--cm-accent)' }}>Try it yourself:</strong> Click a memory node, then click "Build" in the detail panel to assemble its dependency chain.
                </div>
              )}

              {demoResult && (
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-accent)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                    This is what Build looks like
                  </div>
                  <div style={{ fontSize: 13, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-primary)', marginBottom: 6 }}>
                    Resolving <code style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, backgroundColor: 'var(--cm-bg-hover)', padding: '1px 4px', borderRadius: 2 }}>{demoResult.target}</code> —
                    {' '}{demoResult.nodeCount} nodes assembled in topological order
                  </div>
                  <div style={{ display: 'flex', gap: 8, fontSize: 12, fontFamily: 'Raleway, sans-serif' }}>
                    <span style={{ color: 'var(--cm-success)' }}>
                      <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: 1, backgroundColor: 'var(--cm-success)', marginRight: 4 }} />
                      {demoResult.fullCount} full-text
                    </span>
                    {demoResult.summaryCount > 0 && (
                      <span style={{ color: 'var(--cm-warning)' }}>
                        <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: 1, backgroundColor: 'var(--cm-warning)', marginRight: 4 }} />
                        {demoResult.summaryCount} summarized
                      </span>
                    )}
                    {demoResult.skippedCount > 0 && (
                      <span style={{ color: 'var(--cm-text-tertiary)' }}>
                        <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: 1, backgroundColor: 'var(--cm-text-tertiary)', marginRight: 4 }} />
                        {demoResult.skippedCount} skipped
                      </span>
                    )}
                  </div>
                </div>
              )}

              {!demoLoading && !demoFailed && !demoResult && !onDemoResolve && (
                <div style={{ fontSize: 13, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-secondary)' }}>
                  <strong style={{ color: 'var(--cm-accent)' }}>Try it yourself:</strong> Click a memory node, then click "Build" in the detail panel to assemble its dependency chain.
                </div>
              )}
            </div>
          )}

          {/* Step dots */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 8,
              marginBottom: 24,
            }}
          >
            {STEPS.map((_, i) => (
              <span
                key={i}
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: i === step ? 'var(--cm-accent)' : 'var(--cm-border-cool)',
                  transition: 'background-color 200ms ease',
                }}
              />
            ))}
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <button
              onClick={onComplete}
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
              Skip
            </button>
            {!isLast ? (
              <button
                onClick={() => setStep((s) => s + 1)}
                style={{
                  padding: '10px 24px',
                  backgroundColor: 'var(--cm-text-primary)',
                  color: 'var(--cm-bg-primary)',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 12,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  borderRadius: 2,
                }}
              >
                Next
              </button>
            ) : (
              <button
                onClick={onComplete}
                style={{
                  padding: '10px 24px',
                  backgroundColor: 'var(--cm-accent)',
                  color: 'var(--cm-bg-primary)',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 12,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  borderRadius: 2,
                }}
              >
                Get Started
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
