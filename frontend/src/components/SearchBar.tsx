import { useState, useRef, useEffect, useCallback } from 'react'
import { fetchSearch } from '../api'
import type { SearchResultItem } from '../api'

interface Props {
  value: string
  onChange: (value: string) => void
  onNavigate?: (id: string) => void
}

export default function SearchBar({ value, onChange, onNavigate }: Props) {
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [showResults, setShowResults] = useState(false)
  const [searching, setSearching] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Close results on click outside
  useEffect(() => {
    if (!showResults) return
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowResults(false)
      }
    }
    window.addEventListener('mousedown', handler)
    return () => window.removeEventListener('mousedown', handler)
  }, [showResults])

  // Close on Escape
  useEffect(() => {
    if (!showResults) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowResults(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [showResults])

  const doSearch = useCallback((query: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query.trim()) {
      setResults([])
      setShowResults(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await fetchSearch(query.trim())
        setResults(res.results)
        setShowResults(res.results.length > 0)
      } catch (err) {
        console.error('Search failed:', err)
        setResults([])
        setShowResults(false)
      } finally {
        setSearching(false)
      }
    }, 300)
  }, [])

  // Clean up debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  const handleInputChange = (val: string) => {
    onChange(val)
    doSearch(val)
  }

  const handleResultClick = (id: string) => {
    setShowResults(false)
    if (onNavigate) onNavigate(id)
  }

  const trimStyle: Record<string, string> = {
    required: '#1C1917',
    recommended: '#57534E',
    related: '#A8A29E',
  }

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          backgroundColor: '#FFFFFF',
          border: showResults ? '1px solid #B8860B' : '1px solid #E7E5E4',
          borderRadius: 2,
          padding: '4px 8px',
        }}
      >
        {/* Search icon */}
        <svg
          width="14"
          height="14"
          viewBox="0 0 16 16"
          fill="none"
          style={{ color: '#A8A29E', flexShrink: 0 }}
        >
          <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
          <line x1="11" y1="11" x2="14" y2="14" stroke="currentColor" strokeWidth="1.5" />
        </svg>

        <input
          id="global-search-input"
          type="text"
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') doSearch(value)
          }}
          placeholder="Search memories by keyword..."
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            backgroundColor: 'transparent',
            fontSize: 13,
            fontFamily: 'Raleway, sans-serif',
            color: '#1C1917',
          }}
        />

        {searching && (
          <span style={{ fontSize: 10, color: '#A8A29E', fontFamily: 'Raleway, sans-serif' }}>
            ...
          </span>
        )}

        {value && (
          <button
            onClick={() => {
              onChange('')
              setResults([])
              setShowResults(false)
            }}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              color: '#A8A29E',
              fontSize: 12,
              padding: '2px 4px',
              borderRadius: 2,
              fontFamily: 'Raleway, sans-serif',
            }}
          >
            x
          </button>
        )}
      </div>

      {/* Results dropdown */}
      {showResults && results.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: '#FFFFFF',
            border: '1px solid #E7E5E4',
            borderRadius: 2,
            maxHeight: 320,
            overflowY: 'auto',
            zIndex: 25,
            boxShadow: '0 4px 16px rgba(28,25,23,0.1)',
            marginTop: 2,
          }}
        >
          <div
            style={{
              fontSize: 10,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: '#A8A29E',
              padding: '6px 12px',
              borderBottom: '1px solid #F5F5F4',
            }}
          >
            {results.length} result{results.length !== 1 ? 's' : ''}
          </div>
          {results.map((item) => (
            <div
              key={item.id}
              onClick={() => handleResultClick(item.id)}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid #F5F5F4',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.backgroundColor = '#FDF6E8'
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.backgroundColor = 'transparent'
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontFamily: 'JetBrains Mono, monospace',
                  color: '#1C1917',
                  marginBottom: 2,
                }}
              >
                {item.id}
              </div>
              {item.summary && (
                <div
                  style={{
                    fontSize: 12,
                    fontFamily: 'Raleway, sans-serif',
                    color: '#57534E',
                    marginBottom: item.snippet ? 4 : 0,
                    fontWeight: 500,
                  }}
                >
                  {item.summary}
                </div>
              )}
              {item.snippet && (
                <div
                  style={{
                    fontSize: 11,
                    fontFamily: 'Raleway, sans-serif',
                    color: '#A8A29E',
                    lineHeight: 1.5,
                    fontStyle: 'italic',
                  }}
                >
                  {item.snippet}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
