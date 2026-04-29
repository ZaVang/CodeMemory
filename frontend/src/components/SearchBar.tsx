interface Props {
  value: string
  onChange: (value: string) => void
}

export default function SearchBar({ value, onChange }: Props) {
  return (
    <div
      style={{
        padding: '12px 20px',
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #F5F5F4',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}
    >
      {/* Search icon */}
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        style={{ color: '#A8A29E', flexShrink: 0 }}
      >
        <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
        <line x1="11" y1="11" x2="14" y2="14" stroke="currentColor" strokeWidth="1.5" />
      </svg>

      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search by tag, directory, maturity, or keyword..."
        style={{
          flex: 1,
          border: 'none',
          outline: 'none',
          backgroundColor: 'transparent',
          fontSize: 14,
          fontFamily: 'Raleway, sans-serif',
          color: '#1C1917',
        }}
      />

      {value && (
        <button
          onClick={() => onChange('')}
          style={{
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            color: '#A8A29E',
            fontSize: 14,
            padding: '2px 6px',
            borderRadius: 2,
            fontFamily: 'Raleway, sans-serif',
          }}
        >
          Clear
        </button>
      )}
    </div>
  )
}
