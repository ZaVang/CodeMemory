import { useState } from 'react'

interface Props {
  onComplete: () => void
}

const STEPS = [
  {
    title: 'Welcome to CodeMemory',
    subtitle: 'Your memory is a dependency graph, not a search index.',
    description:
      'CodeMemory organizes knowledge as interconnected "atoms" — small, self-contained memories linked by explicit dependencies. Think of it as a personal knowledge graph where every piece of information knows what it depends on.',
    icon: '+',
  },
  {
    title: 'Graph View',
    subtitle: 'Explore your memory network visually.',
    description:
      'Each circle is a memory. Color = category, size = importance. Solid lines mean required dependencies (must-read), dashed lines are recommended, dotted lines are related. Click a node to see details. Right-click to Edit or Archive.',
    icon: 'o',
  },
  {
    title: 'Resolve',
    subtitle: 'Reconstruct the full context of any idea.',
    description:
      'Click "Resolve" in the detail panel to trace all dependencies. The graph animates through the dependency chain in topological order — showing you exactly how ideas connect. Use the Budget slider to control how much context to load.',
    icon: '>',
  },
  {
    title: 'Create Memories',
    subtitle: 'Build your knowledge graph.',
    description:
      'Click "+ New" to create a memory. Give it an ID (e.g. "user/ideas/my-thought"), add tags, set importance (1–10), and write your content in Markdown. Add imports to link it to existing memories.',
    icon: '~',
  },
  {
    title: "You're Ready",
    subtitle: 'Start building your memory network.',
    description:
      'The Dashboard shows statistics and health checks. Switch datasets from the header dropdown. Press Escape to close panels. The Help button (top-right) has full reference documentation.',
    icon: '✓',
  },
]

export default function Onboarding({ onComplete }: Props) {
  const [step, setStep] = useState(0)
  const current = STEPS[step]
  const isLast = step === STEPS.length - 1

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
            backgroundColor: '#FFFBEB',
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
              backgroundColor: '#FDF6E8',
              border: '2px solid #B8860B',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 24px',
              fontSize: 28,
              fontFamily: "'Cormorant Garamond', serif",
              color: '#B8860B',
              fontWeight: 500,
            }}
          >
            {current.icon}
          </div>

          {/* Title */}
          <h2
            style={{
              fontSize: 24,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: '#1C1917',
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
              color: '#B8860B',
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
              color: '#57534E',
              lineHeight: 1.7,
              margin: '0 0 28px 0',
            }}
          >
            {current.description}
          </p>

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
                  backgroundColor: i === step ? '#B8860B' : '#D4D4D8',
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
              Skip
            </button>
            {!isLast ? (
              <button
                onClick={() => setStep((s) => s + 1)}
                style={{
                  padding: '10px 24px',
                  backgroundColor: '#1C1917',
                  color: '#FFFBEB',
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
                  backgroundColor: '#B8860B',
                  color: '#FFFBEB',
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
