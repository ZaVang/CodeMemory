import SearchBar from './SearchBar'
import type { DatasetInfo } from '../api'

export type ViewMode = 'graph' | 'list' | 'dashboard' | 'review' | 'personal'

interface Props {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  onCreateMemory: () => void
  datasets: DatasetInfo[]
  currentDataset: string
  datasetReady: boolean
  switchingDataset: boolean
  isPersonalDataset: boolean
  onSwitchDataset: (name: string) => void
  showQuantInfo: boolean
  searchText: string
  onSearchChange: (value: string) => void
  onSearchNavigate: (id: string) => void
  onSearchBuild: (id: string) => void
  zoomLevel: number
  onZoomChange: (value: number) => void
  budget: number
  budgetMin: number
  budgetMax: number
  onBudgetChange: (value: number) => void
  activeTheme: 'light' | 'dark'
  onToggleTheme: () => void
  onExportPng: () => void
  onExportMemories: () => void
  onOpenSettings: () => void
  onOpenHelp: () => void
}

const navButtonBase = {
  padding: '6px 16px',
  border: 'none',
  cursor: 'pointer',
  fontSize: 12,
  fontFamily: 'Raleway, sans-serif',
  fontWeight: 600,
  textTransform: 'uppercase' as const,
  letterSpacing: '0.08em',
  display: 'flex',
  alignItems: 'center',
  gap: 6,
}

export default function AppHeader({
  viewMode,
  onViewModeChange,
  onCreateMemory,
  datasets,
  currentDataset,
  datasetReady,
  switchingDataset,
  isPersonalDataset,
  onSwitchDataset,
  showQuantInfo,
  searchText,
  onSearchChange,
  onSearchNavigate,
  onSearchBuild,
  zoomLevel,
  onZoomChange,
  budget,
  budgetMin,
  budgetMax,
  onBudgetChange,
  activeTheme,
  onToggleTheme,
  onExportPng,
  onExportMemories,
  onOpenSettings,
  onOpenHelp,
}: Props) {
  return (
    <header
      style={{
        padding: '12px 24px',
        backgroundColor: 'var(--cm-bg-primary)',
        borderBottom: '1px solid var(--cm-border)',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
        flexShrink: 0,
        overflow: 'visible',
      }}
    >
      <h1
        style={{
          fontSize: 24,
          fontFamily: "'Cormorant Garamond', serif",
          fontWeight: 500,
          color: 'var(--cm-text-primary)',
          margin: 0,
          whiteSpace: 'nowrap',
          letterSpacing: '0.01em',
        }}
      >
        CodeMemory
      </h1>

      <button
        onClick={onCreateMemory}
        style={{
          padding: '6px 18px',
          backgroundColor: 'var(--cm-accent)',
          color: 'var(--cm-text-inverse)',
          border: 'none',
          cursor: 'pointer',
          fontSize: 12,
          fontWeight: 600,
          fontFamily: 'Raleway, sans-serif',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          borderRadius: 2,
          whiteSpace: 'nowrap',
          flexShrink: 0,
        }}
      >
        Create Memory
      </button>

      <div
        style={{
          display: 'flex',
          borderRadius: 2,
          border: '1px solid var(--cm-border-cool)',
          overflow: 'hidden',
          flexShrink: 0,
        }}
      >
        {([
          'graph',
          'list',
          'dashboard',
          'review',
          ...(isPersonalDataset ? ['personal' as const] : []),
        ] as const).map((mode, index) => (
          <button
            key={mode}
            onClick={() => onViewModeChange(mode)}
            title={`${mode[0].toUpperCase()}${mode.slice(1)} view (keyboard: ${index + 1})`}
            style={{
              ...navButtonBase,
              backgroundColor: viewMode === mode ? 'var(--cm-text-primary)' : 'transparent',
              color: viewMode === mode ? 'var(--cm-text-inverse)' : 'var(--cm-text-secondary)',
            }}
          >
            {mode}<span style={{ fontSize: 12, opacity: 0.55, letterSpacing: 0 }}>{index + 1}</span>
          </button>
        ))}
      </div>

      {datasets.length > 1 && (
        <select
          value={currentDataset}
          onChange={(e) => onSwitchDataset(e.target.value)}
          disabled={switchingDataset}
          title="Stats, validation, and reindex apply to the selected dataset"
          style={{
            padding: '4px 8px',
            border: '1px solid var(--cm-border-cool)',
            borderRadius: 2,
            fontSize: 12,
            fontWeight: 600,
            fontFamily: 'Raleway, sans-serif',
            color: 'var(--cm-text-primary)',
            backgroundColor: switchingDataset ? 'var(--cm-bg-subtle)' : 'var(--cm-bg-surface)',
            cursor: 'pointer',
            flexShrink: 0,
            outline: 'none',
            maxWidth: 220,
          }}
        >
          {datasets.map((ds) => (
            <option key={ds.name} value={ds.name}>
              {ds.name} ({ds.memory_count})
            </option>
          ))}
        </select>
      )}

      {switchingDataset && (
        <span style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif' }}>
          Switching...
        </span>
      )}

      {showQuantInfo && (
        <span
          title="Auto-generated API documentation. Dependency graph reflects algorithmic inference, not human-authored links."
          aria-label="Dataset info"
          style={{
            fontSize: 14,
            lineHeight: 1,
            color: 'var(--cm-text-tertiary)',
            cursor: 'help',
            flexShrink: 0,
            userSelect: 'none',
          }}
        >
          ⓘ
        </span>
      )}

      {(viewMode === 'graph' || viewMode === 'list') && (
        <div style={{ flex: '1 1 240px', minWidth: 180 }}>
          <SearchBar
            enabled={datasetReady}
            value={searchText}
            onChange={onSearchChange}
            onNavigate={onSearchNavigate}
            onBuild={onSearchBuild}
          />
        </div>
      )}

      {viewMode === 'graph' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', flex: '0 1 auto' }}>
          <RangeControl
            label="Zoom"
            value={zoomLevel}
            min={0.15}
            max={2}
            step={0.05}
            width={84}
            onChange={onZoomChange}
          />
          <RangeControl
            label="Budget"
            value={budget}
            min={budgetMin}
            max={budgetMax}
            step={100}
            width={96}
            onChange={onBudgetChange}
            valueLabel={String(budget)}
          />
        </div>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          flexWrap: 'wrap',
          marginLeft: 'auto',
        }}
      >
        <button
          onClick={onToggleTheme}
          title={`Current: ${activeTheme}. Click to toggle.`}
          style={iconButtonStyle(16)}
        >
          {activeTheme === 'dark' ? '☀' : '☽'}
        </button>

        {viewMode === 'graph' && (
          <button
            onClick={onExportPng}
            title="Export graph as PNG image"
            style={outlineButtonStyle}
          >
            PNG
          </button>
        )}

        <button onClick={onExportMemories} title="Export all memories as .zip" style={outlineButtonStyle}>
          Export
        </button>

        <button onClick={onOpenSettings} title="Settings" style={iconButtonStyle(18)}>
          &#9881;
        </button>

        <button
          onClick={onOpenHelp}
          title="Help"
          style={{
            padding: '6px 18px',
            backgroundColor: 'var(--cm-accent)',
            color: 'var(--cm-text-inverse)',
            border: 'none',
            cursor: 'pointer',
            fontSize: 12,
            fontWeight: 600,
            fontFamily: 'Raleway, sans-serif',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            borderRadius: 2,
            whiteSpace: 'nowrap',
          }}
        >
          Help
        </button>
      </div>
    </header>
  )
}

function RangeControl({
  label,
  value,
  min,
  max,
  step,
  width,
  onChange,
  valueLabel,
}: {
  label: string
  value: number
  min: number
  max: number
  step: number
  width: number
  onChange: (value: number) => void
  valueLabel?: string
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
      <label
        style={{
          fontSize: 12,
          fontWeight: 600,
          fontFamily: 'Raleway, sans-serif',
          color: 'var(--cm-text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          whiteSpace: 'nowrap',
        }}
      >
        {label}
      </label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          width,
          accentColor: 'var(--cm-accent)',
          cursor: 'pointer',
        }}
      />
      {valueLabel && (
        <span
          style={{
            fontSize: 12,
            fontFamily: 'JetBrains Mono, monospace',
            color: 'var(--cm-text-primary)',
            minWidth: 40,
            textAlign: 'right',
          }}
        >
          {valueLabel}
        </span>
      )}
    </div>
  )
}

const outlineButtonStyle = {
  padding: '6px 14px',
  backgroundColor: 'transparent',
  color: 'var(--cm-text-secondary)',
  border: '1px solid var(--cm-border-cool)',
  cursor: 'pointer',
  fontSize: 12,
  fontWeight: 600,
  fontFamily: 'Raleway, sans-serif',
  textTransform: 'uppercase' as const,
  letterSpacing: '0.08em',
  borderRadius: 2,
  whiteSpace: 'nowrap' as const,
}

function iconButtonStyle(fontSize: number) {
  return {
    padding: '6px 10px',
    backgroundColor: 'transparent',
    color: 'var(--cm-text-secondary)',
    border: '1px solid var(--cm-border-cool)',
    cursor: 'pointer',
    fontSize,
    fontFamily: 'Raleway, sans-serif',
    borderRadius: 2,
    whiteSpace: 'nowrap' as const,
    lineHeight: 1,
  }
}
