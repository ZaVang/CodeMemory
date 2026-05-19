import { useState, useRef, useEffect, useCallback } from 'react'
import { fetchSearch, fetchStats } from '../api'
import type { SearchResultItem } from '../api'

/** R16-C1: split text around a query term and wrap matches in <mark> elements. */
function highlightMatches(text: string, query: string): React.ReactNode {
  if (!query || !text) return text
  const qLower = query.toLowerCase()
  const tLower = text.toLowerCase()
  const idx = tLower.indexOf(qLower)
  if (idx < 0) return text
  const before = text.slice(0, idx)
  const match = text.slice(idx, idx + query.length)
  const after = text.slice(idx + query.length)
  return (
    <>
      {before}
      <mark style={{
        backgroundColor: 'var(--cm-bg-warning-subtle)',
        color: 'var(--cm-warning)',
        fontWeight: 600,
        padding: '0 1px',
        borderRadius: 1,
      }}>
        {match}
      </mark>
      {after}
    </>
  )
}

interface Props {
  enabled?: boolean
  value: string
  onChange: (value: string) => void
  onNavigate?: (id: string) => void
  onResolve?: (id: string) => void
}

export default function SearchBar({ enabled = true, value, onChange, onNavigate, onResolve }: Props) {
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [showResults, setShowResults] = useState(false)
  const [searching, setSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // R9-tag-autocomplete: tag suggestions
  const [allTags, setAllTags] = useState<string[]>([])

  useEffect(() => {
    if (!enabled) {
      return
    }
    fetchStats()
      .then((stats) => setAllTags(stats.tags.map((t) => t.tag).sort()))
      .catch(() => setAllTags([]))
  }, [enabled])

  // Compute matching tag suggestions from current input
  const tagMatches = (() => {
    if (!value.trim()) return []
    const q = value.trim().toLowerCase()
    return allTags
      .filter((t) => t.toLowerCase().startsWith(q) && t.toLowerCase() !== q)
      .slice(0, 5)
  })()

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
    if (!enabled) {
      setResults([])
      setShowResults(false)
      setHasSearched(false)
      return
    }
    if (!query.trim()) {
      setResults([])
      setShowResults(false)
      setHasSearched(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await fetchSearch(query.trim())
        setResults(res.results)
        setShowResults(true)
        setHasSearched(true)
      } catch (err) {
        console.error('Search failed:', err)
        setResults([])
        setShowResults(true)
        setHasSearched(true)
      } finally {
        setSearching(false)
      }
    }, 300)
  }, [enabled])

  // Clean up debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  const handleInputChange = (val: string) => {
    onChange(val)
    setHasSearched(false)
    doSearch(val)
  }

  const handleResultClick = (id: string) => {
    setShowResults(false)
    if (onNavigate) onNavigate(id)
  }

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          backgroundColor: 'var(--cm-bg-surface)',
          border: showResults ? '1px solid var(--cm-accent)' : '1px solid var(--cm-border)',
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
          style={{ color: 'var(--cm-text-tertiary)', flexShrink: 0 }}
        >
          <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
          <line x1="11" y1="11" x2="14" y2="14" stroke="currentColor" strokeWidth="1.5" />
        </svg>

        <input
          id="global-search-input"
          type="text"
          value={value}
          disabled={!enabled}
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
            color: 'var(--cm-text-primary)',
          }}
        />

        {searching && (
          <span style={{ fontSize: 12, color: 'var(--cm-text-tertiary)', fontFamily: 'Raleway, sans-serif' }}>
            ...
          </span>
        )}

        {value && (
          <button
            onClick={() => {
              onChange('')
              setResults([])
              setShowResults(false)
              setHasSearched(false)
            }}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              color: 'var(--cm-text-tertiary)',
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

      {/* Tag suggestions + Results dropdown */}
      {((showResults && results.length > 0) || tagMatches.length > 0 || (hasSearched && results.length === 0 && !searching && value.trim())) && (
        <div
          className="search-dropdown-enter"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: 'var(--cm-bg-surface)',
            border: '1px solid var(--cm-border)',
            borderRadius: 2,
            maxHeight: 320,
            overflowY: 'auto',
            zIndex: 25,
            boxShadow: '0 4px 16px rgba(28,25,23,0.1)',
            marginTop: 2,
          }}
        >
          {/* R9-tag-autocomplete: matching tag suggestions */}
          {tagMatches.length > 0 && (
            <>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--cm-text-tertiary)',
                  padding: '6px 12px',
                  borderBottom: '1px solid var(--cm-bg-subtle)',
                }}
              >
                Tags
              </div>
              {tagMatches.map((tag) => (
                <div
                  key={'tag-' + tag}
                  onClick={() => {
                    onChange(tag)
                    setShowResults(false)
                    if (onNavigate) onNavigate(tag)
                  }}
                  style={{
                    padding: '6px 12px',
                    cursor: 'pointer',
                    borderBottom: '1px solid var(--cm-bg-subtle)',
                    fontSize: 12,
                    fontFamily: 'Raleway, sans-serif',
                    color: 'var(--cm-text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLDivElement).style.backgroundColor = 'var(--cm-bg-hover)'
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLDivElement).style.backgroundColor = 'transparent'
                  }}
                >
                  <span style={{
                    fontSize: 12,
                    color: 'var(--cm-text-tertiary)',
                  }}>
                    #
                  </span>
                  {tag}
                </div>
              ))}
            </>
          )}

          {/* R9-empty-search: no results message */}
          {hasSearched && results.length === 0 && !searching && value.trim() && (
            <div
              style={{
                padding: '20px 16px',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 13,
                  fontFamily: 'Raleway, sans-serif',
                  color: 'var(--cm-text-secondary)',
                  marginBottom: 4,
                }}
              >
                No memories found matching &ldquo;{value.trim()}&rdquo;
              </div>
              <div
                style={{
                  fontSize: 12,
                  fontFamily: 'Raleway, sans-serif',
                  color: 'var(--cm-text-tertiary)',
                }}
              >
                Try broadening your search or using different keywords.
              </div>
            </div>
          )}

          {/* Existing search results header */}
          {showResults && results.length > 0 && (
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Raleway, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--cm-text-tertiary)',
              padding: '6px 12px',
              borderBottom: '1px solid var(--cm-bg-subtle)',
              borderTop: tagMatches.length > 0 ? '1px solid var(--cm-bg-subtle)' : 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>{results.length} result{results.length !== 1 ? 's' : ''}</span>
            {results.some((r) => r.match_quality === 'fuzzy') && (
              <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: '0', fontSize: 12 }}>
                includes fuzzy matches
              </span>
            )}
          </div>
          )}
          {results.map((item) => (
            <div
              key={item.id}
              onClick={() => handleResultClick(item.id)}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid var(--cm-bg-subtle)',
                opacity: item.match_quality === 'fuzzy' ? 0.85 : 1,
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.backgroundColor = 'var(--cm-bg-hover)'
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.backgroundColor = 'transparent'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontFamily: 'JetBrains Mono, monospace',
                    color: 'var(--cm-text-primary)',
                    flex: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {item.id}
                </div>
                {/* Resolve shortcut (R13-D1) */}
                {onResolve && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowResults(false)
                      onResolve(item.id)
                    }}
                    title={`Resolve this memory's dependency graph into a structured context`}
                    style={{
                      border: '1px solid var(--cm-accent)',
                      background: 'transparent',
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 600,
                      fontFamily: 'Raleway, sans-serif',
                      color: 'var(--cm-accent)',
                      padding: '1px 8px',
                      borderRadius: 2,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      whiteSpace: 'nowrap',
                      flexShrink: 0,
                    }}
                  >
                    Resolve &rarr;
                  </button>
                )}
                {/* Match quality indicator — always visible */}
                <span style={{
                  fontSize: 12,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  color: item.match_quality === 'fuzzy' ? 'var(--cm-warning)' : 'var(--cm-success)',
                  backgroundColor: item.match_quality === 'fuzzy' ? 'var(--cm-bg-warning-subtle)' : 'var(--cm-bg-success-subtle)',
                  padding: '1px 6px',
                  borderRadius: 2,
                  flexShrink: 0,
                  whiteSpace: 'nowrap',
                }}>
                  {item.match_quality === 'fuzzy'
                    ? `~${item.match_score ? Math.round(item.match_score * 100) + '%' : 'fuzzy'}`
                    : 'exact'}
                </span>
              </div>
              {item.summary && (
                <div
                  style={{
                    fontSize: 12,
                    fontFamily: 'Raleway, sans-serif',
                    color: 'var(--cm-text-secondary)',
                    marginBottom: (item.snippet || (item.match_fields && item.match_fields.length > 0)) ? 4 : 0,
                    fontWeight: 500,
                  }}
                >
                  {item.summary}
                </div>
              )}
              {/* Match fields — subtle display of which fields matched */}
              {item.match_fields && item.match_fields.length > 0 && (
                <div style={{
                  fontSize: 12,
                  fontFamily: 'Raleway, sans-serif',
                  color: 'var(--cm-text-tertiary)',
                  marginBottom: item.snippet ? 4 : 0,
                  fontStyle: 'italic',
                }}>
                  matched: {item.match_fields.map((f) => f.charAt(0).toUpperCase() + f.slice(1)).join(', ')}
                </div>
              )}
              {item.snippet && (
                <div
                  style={{
                    fontSize: 12,
                    fontFamily: 'Raleway, sans-serif',
                    color: 'var(--cm-text-tertiary)',
                    lineHeight: 1.5,
                    fontStyle: 'italic',
                  }}
                >
                  {highlightMatches(item.snippet, value)}
                </div>
              )}
              {/* R16-S2: access freshness in search results */}
              <div style={{
                fontSize: 11,
                fontFamily: 'Raleway, sans-serif',
                color: 'var(--cm-text-tertiary)',
                marginTop: 2,
              }}>
                {item.access_count != null && item.access_count > 0 && item.days_since_last_access != null ? (
                  <>
                    {item.days_since_last_access === 0 ? 'just now' : `${item.days_since_last_access}d ago`}
                    {item.stability != null && item.days_since_last_access != null && (
                      (() => {
                        const exp = Math.pow(0.5, item.days_since_last_access / item.stability)
                        const floor = 0.05 / (1 + item.days_since_last_access / (10 * item.stability))
                        const R = Math.max(exp, floor)
                        const R_pct = R * 100
                        const rColor = R_pct > 50 ? 'var(--cm-success)' : R_pct >= 10 ? 'var(--cm-warning)' : 'var(--cm-error)'
                        return (
                          <span> &middot; <span style={{ color: rColor, fontWeight: 600 }}>R: {R_pct.toFixed(1)}%</span></span>
                        )
                      })()
                    )}
                  </>
                ) : (
                  <span>never &middot; R=N/A</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
