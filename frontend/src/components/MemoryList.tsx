import { useState, useEffect, useCallback, useMemo } from 'react'
import { fetchAllMemories } from '../api'
import type { MemorySummary } from '../types'
import { StatusBadge, MaturityBadge } from './Badges'

interface Props {
  onSelectMemory: (id: string) => void
  refreshTrigger?: number
  initialFilter?: string  // pre-fill filter from dashboard navigation
}

type SortField = 'id' | 'summary' | 'type' | 'maturity' | 'status'
type SortDir = 'asc' | 'desc'

const PAGE_SIZE = 20

export default function MemoryList({ onSelectMemory, refreshTrigger, initialFilter }: Props) {
  const [allMemories, setAllMemories] = useState<MemorySummary[]>([])
  const [loading, setLoading] = useState(true)
  const [filterText, setFilterText] = useState('')
  const [sortField, setSortField] = useState<SortField>('id')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [page, setPage] = useState(0)
  const [pageSize] = useState(PAGE_SIZE)

  // Load all memories for client-side sort/filter (backend pagination still
  // available via the API for future large-dataset use)
  const loadData = useCallback(() => {
    setLoading(true)
    fetchAllMemories()
      .then(setAllMemories)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData, refreshTrigger])

  // Apply initial filter from dashboard navigation
  useEffect(() => {
    if (initialFilter) {
      setFilterText(initialFilter)
      setPage(0)
    }
  }, [initialFilter])

  // Filter
  const filtered = useMemo(() => {
    if (!filterText.trim()) return allMemories
    const q = filterText.toLowerCase()
    return allMemories.filter((m) =>
      m.id.toLowerCase().includes(q) ||
      m.summary.toLowerCase().includes(q) ||
      m.tags.some((t) => t.toLowerCase().includes(q)) ||
      m.type.toLowerCase().includes(q) ||
      m.maturity.toLowerCase().includes(q) ||
      m.status.toLowerCase().includes(q) ||
      m.directory.toLowerCase().includes(q)
    )
  }, [allMemories, filterText])

  // Sort
  const sorted = useMemo(() => {
    const dir = sortDir === 'asc' ? 1 : -1
    return [...filtered].sort((a, b) => {
      const va = (a[sortField] || '').toString().toLowerCase()
      const vb = (b[sortField] || '').toString().toLowerCase()
      return va.localeCompare(vb) * dir
    })
  }, [filtered, sortField, sortDir])

  // Paginate
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const effectivePage = Math.min(page, totalPages - 1)
  const paginated = sorted.slice(effectivePage * pageSize, (effectivePage + 1) * pageSize)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('asc')
    }
    setPage(0)
  }

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return null
    return <span style={{ marginLeft: 2, fontSize: 10 }}>{sortDir === 'asc' ? ' ↑' : ' ↓'}</span>
  }

  const thStyle: React.CSSProperties = {
    padding: '8px 12px',
    textAlign: 'left',
    fontSize: 10,
    fontWeight: 600,
    fontFamily: 'Raleway, sans-serif',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: '#57534E',
    borderBottom: '2px solid #E7E5E4',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    userSelect: 'none',
    backgroundColor: '#FFFBEB',
    position: 'sticky',
    top: 0,
    zIndex: 1,
  }

  const tdStyle: React.CSSProperties = {
    padding: '8px 12px',
    fontSize: 12,
    fontFamily: 'Raleway, sans-serif',
    color: '#1C1917',
    borderBottom: '1px solid #F5F5F4',
    verticalAlign: 'middle',
  }

  if (loading) {
    return (
      <div style={{ padding: 32, color: '#A8A29E', fontFamily: 'Raleway, sans-serif', fontSize: 14, backgroundColor: '#FFFBEB', height: '100%' }}>
        Loading...
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: '#FFFBEB' }}>
      {/* Filter bar */}
      <div style={{ padding: '16px 24px', borderBottom: '1px solid #E7E5E4', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          backgroundColor: '#FFFFFF',
          border: '1px solid #E7E5E4',
          borderRadius: 2,
          padding: '4px 8px',
          flex: 1,
          maxWidth: 400,
        }}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ color: '#A8A29E', flexShrink: 0 }}>
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
            <line x1="11" y1="11" x2="14" y2="14" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          <input
            type="text"
            value={filterText}
            onChange={(e) => { setFilterText(e.target.value); setPage(0) }}
            placeholder="Filter memories..."
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              fontSize: 12,
              fontFamily: 'Raleway, sans-serif',
              color: '#1C1917',
            }}
          />
          {filterText && (
            <button
              onClick={() => { setFilterText(''); setPage(0) }}
              style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#A8A29E', fontSize: 12, padding: '2px 4px', fontFamily: 'Raleway, sans-serif' }}
            >
              x
            </button>
          )}
        </div>
        <span style={{ fontSize: 11, color: '#A8A29E', fontFamily: 'Raleway, sans-serif', whiteSpace: 'nowrap' }}>
          {filtered.length} of {allMemories.length} memories
        </span>
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ ...thStyle, width: '30%' }} onClick={() => handleSort('id')}>
                ID{sortIndicator('id')}
              </th>
              <th style={{ ...thStyle, width: '28%' }} onClick={() => handleSort('summary')}>
                Summary{sortIndicator('summary')}
              </th>
              <th style={{ ...thStyle, width: '10%' }} onClick={() => handleSort('type')}>
                Type{sortIndicator('type')}
              </th>
              <th style={{ ...thStyle, width: '12%' }} onClick={() => handleSort('maturity')}>
                Maturity{sortIndicator('maturity')}
              </th>
              <th style={{ ...thStyle, width: '10%' }} onClick={() => handleSort('status')}>
                Status{sortIndicator('status')}
              </th>
              <th style={{ ...thStyle, width: '20%', cursor: 'default' }}>
                Tags
              </th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((mem) => (
              <tr
                key={mem.id}
                onClick={() => onSelectMemory(mem.id)}
                style={{ cursor: 'pointer' }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.backgroundColor = '#FDF6E8' }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.backgroundColor = 'transparent' }}
              >
                <td style={{ ...tdStyle, fontFamily: 'JetBrains Mono, monospace', fontSize: 11, wordBreak: 'break-all' }}>
                  {mem.id}
                </td>
                <td style={{ ...tdStyle, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
                  {mem.summary}
                </td>
                <td style={tdStyle}>
                  <span style={{
                    fontSize: 10,
                    fontFamily: 'Raleway, sans-serif',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    color: mem.type === 'schema' ? '#7C3AED' : '#57534E',
                  }}>
                    {mem.type}
                  </span>
                </td>
                <td style={tdStyle}><MaturityBadge maturity={mem.maturity} opts={{ padding: '1px 8px', fontSize: 10 }} /></td>
                <td style={tdStyle}><StatusBadge status={mem.status} opts={{ padding: '1px 8px', fontSize: 10 }} /></td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                    {mem.tags.slice(0, 4).map((t) => (
                      <span key={t} style={{
                        fontSize: 10,
                        fontFamily: 'Raleway, sans-serif',
                        padding: '1px 6px',
                        borderRadius: 2,
                        backgroundColor: '#F5F5F4',
                        color: '#57534E',
                        whiteSpace: 'nowrap',
                      }}>
                        {t}
                      </span>
                    ))}
                    {mem.tags.length > 4 && (
                      <span style={{ fontSize: 10, color: '#A8A29E' }}>+{mem.tags.length - 4}</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {paginated.length === 0 && (
              <tr>
                <td colSpan={6} style={{ padding: '48px 16px', textAlign: 'center', color: '#A8A29E', fontFamily: 'Raleway, sans-serif', fontSize: 13 }}>
                  {allMemories.length === 0 ? 'No memories found. Create your first memory to get started.' : 'No memories match the current filter.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{
          padding: '12px 24px',
          borderTop: '1px solid #E7E5E4',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          flexShrink: 0,
        }}>
          <button
            onClick={() => setPage(0)}
            disabled={effectivePage === 0}
            style={pageBtnStyle}
          >
            First
          </button>
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={effectivePage === 0}
            style={pageBtnStyle}
          >
            Prev
          </button>
          <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono, monospace', color: '#57534E', padding: '0 8px' }}>
            {effectivePage + 1} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={effectivePage >= totalPages - 1}
            style={pageBtnStyle}
          >
            Next
          </button>
          <button
            onClick={() => setPage(totalPages - 1)}
            disabled={effectivePage >= totalPages - 1}
            style={pageBtnStyle}
          >
            Last
          </button>
        </div>
      )}
    </div>
  )
}

const pageBtnStyle: React.CSSProperties = {
  padding: '4px 12px',
  border: '1px solid #D4D4D8',
  background: 'transparent',
  color: '#57534E',
  cursor: 'pointer',
  fontSize: 11,
  fontWeight: 600,
  fontFamily: 'Raleway, sans-serif',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  borderRadius: 2,
}
