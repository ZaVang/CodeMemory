import { useState, useEffect, useCallback } from 'react'
import type { DatasetInfo } from '../api'

const SETTINGS_KEY = 'codememory-settings'

export interface UserSettings {
  defaultDataset: string
  defaultBudget: number
  theme: 'light' | 'dark' | 'system'
}

export function loadSettings(): UserSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        defaultDataset: parsed.defaultDataset || '',
        defaultBudget: typeof parsed.defaultBudget === 'number' ? parsed.defaultBudget : 2000,
        theme: ['light', 'dark', 'system'].includes(parsed.theme) ? parsed.theme : 'system',
      }
    }
  } catch { /* ignore */ }
  return { defaultDataset: '', defaultBudget: 2000, theme: 'system' }
}

export function saveSettings(settings: UserSettings): void {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
}

interface Props {
  open: boolean
  onClose: () => void
  datasets: DatasetInfo[]
  currentDataset: string
  onSwitchDataset: (name: string) => void
  currentBudget: number
  onBudgetChange: (budget: number) => void
  currentTheme: 'light' | 'dark' | 'system'
  onThemeChange: (theme: 'light' | 'dark' | 'system') => void
}

export default function Settings({
  open, onClose, datasets, currentDataset, onSwitchDataset,
  currentBudget, onBudgetChange, currentTheme, onThemeChange,
}: Props) {
  const [budgetValue, setBudgetValue] = useState(currentBudget)
  const [datasetValue, setDatasetValue] = useState(currentDataset)
  const [themeValue, setThemeValue] = useState(currentTheme)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setBudgetValue(currentBudget)
    setDatasetValue(currentDataset)
    setThemeValue(currentTheme)
  }, [currentBudget, currentDataset, currentTheme, open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  const handleSave = useCallback(() => {
    const settings: UserSettings = {
      defaultDataset: datasetValue,
      defaultBudget: budgetValue,
      theme: themeValue,
    }
    saveSettings(settings)
    // Apply changes
    if (datasetValue !== currentDataset && datasetValue) {
      onSwitchDataset(datasetValue)
    }
    onBudgetChange(budgetValue)
    onThemeChange(themeValue)
    setSaved(true)
    setTimeout(() => setSaved(false), 1500)
    setTimeout(onClose, 600)
  }, [datasetValue, budgetValue, themeValue, currentDataset, onSwitchDataset, onBudgetChange, onThemeChange, onClose])

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(28,25,23,0.12)',
          zIndex: 29,
        }}
      />

      {/* Panel */}
      <div
        className="panel-slide-enter"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '34vw',
          minWidth: 400,
          maxWidth: 520,
          backgroundColor: 'var(--cm-bg-primary)',
          borderLeft: '1px solid var(--cm-border)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 30,
          boxShadow: '0 8px 32px rgba(28,25,23,0.12)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 24px',
            borderBottom: '1px solid var(--cm-border)',
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              fontSize: 24,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: 'var(--cm-text-primary)',
              margin: 0,
            }}
          >
            Settings
          </h2>
          <button
            onClick={onClose}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 20,
              color: 'var(--cm-text-secondary)',
              padding: '4px 8px',
              borderRadius: 2,
              lineHeight: 1,
              fontFamily: 'Raleway, sans-serif',
            }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          {/* Default Dataset */}
          <div style={{ marginBottom: 32 }}>
            <label
              style={{
                display: 'block',
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'Raleway, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--cm-text-secondary)',
                marginBottom: 8,
              }}
            >
              Default Dataset
            </label>
            <p style={{
              fontSize: 12,
              fontFamily: 'Raleway, sans-serif',
              color: 'var(--cm-text-tertiary)',
              margin: '0 0 8px 0',
            }}>
              Automatically loaded on startup.
            </p>
            <select
              value={datasetValue}
              onChange={(e) => setDatasetValue(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid var(--cm-border-cool)',
                borderRadius: 2,
                fontSize: 13,
                fontFamily: 'Raleway, sans-serif',
                color: 'var(--cm-text-primary)',
                backgroundColor: 'var(--cm-input-bg)',
                outline: 'none',
              }}
            >
              <option value="">Use server default</option>
              {datasets.map((ds) => (
                <option key={ds.name} value={ds.name}>
                  {ds.name} ({ds.memory_count} memories)
                </option>
              ))}
            </select>
          </div>

          {/* Default Budget */}
          <div style={{ marginBottom: 32 }}>
            <label
              style={{
                display: 'block',
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'Raleway, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--cm-text-secondary)',
                marginBottom: 8,
              }}
            >
              Default Resolve Budget
            </label>
            <p style={{
              fontSize: 12,
              fontFamily: 'Raleway, sans-serif',
              color: 'var(--cm-text-tertiary)',
              margin: '0 0 8px 0',
            }}>
              Initial value for the budget slider (200-5000).
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="range"
                min={200}
                max={5000}
                step={100}
                value={budgetValue}
                onChange={(e) => setBudgetValue(Number(e.target.value))}
                style={{
                  flex: 1,
                  accentColor: 'var(--cm-accent)',
                  cursor: 'pointer',
                }}
              />
              <span style={{
                fontSize: 14,
                fontFamily: 'JetBrains Mono, monospace',
                color: 'var(--cm-text-primary)',
                minWidth: 50,
                textAlign: 'right',
              }}>
                {budgetValue}
              </span>
            </div>
          </div>

          {/* Theme */}
          <div style={{ marginBottom: 32 }}>
            <label
              style={{
                display: 'block',
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'Raleway, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--cm-text-secondary)',
                marginBottom: 8,
              }}
            >
              Theme
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              {([
                ['system', 'System'],
                ['light', 'Light'],
                ['dark', 'Dark'],
              ] as const).map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => setThemeValue(value)}
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    border: themeValue === value
                      ? `2px solid var(--cm-accent)`
                      : '1px solid var(--cm-border-cool)',
                    borderRadius: 2,
                    background: themeValue === value
                      ? 'var(--cm-bg-accent-subtle)'
                      : 'var(--cm-bg-surface)',
                    color: themeValue === value
                      ? 'var(--cm-accent)'
                      : 'var(--cm-text-secondary)',
                    cursor: 'pointer',
                    fontSize: 12,
                    fontWeight: 600,
                    fontFamily: 'Raleway, sans-serif',
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
            <p style={{
              fontSize: 12,
              fontFamily: 'Raleway, sans-serif',
              color: 'var(--cm-text-tertiary)',
              margin: '8px 0 0 0',
            }}>
              System follows your OS preference.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--cm-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 12,
            flexShrink: 0,
          }}
        >
          <button
            onClick={onClose}
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
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: '10px 24px',
              backgroundColor: saved ? 'var(--cm-success)' : 'var(--cm-accent)',
              color: 'var(--cm-text-inverse)',
              border: 'none',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              borderRadius: 2,
              transition: 'background-color 200ms ease',
            }}
          >
            {saved ? 'Saved' : 'Save'}
          </button>
        </div>
      </div>
    </>
  )
}
