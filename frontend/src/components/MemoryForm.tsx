import { useState, useEffect, useCallback } from 'react'
import { fetchMemory, createMemory, updateMemory, fetchAllMemories } from '../api'
import type { MemoryDetail, MemorySummary } from '../types'

interface Props {
  /** If set, edit mode; otherwise create mode */
  memoryId: string | null
  onClose: () => void
  /** Called after successful create/edit/delete to refresh the graph */
  onChange: () => void
  /** Called when user clicks "View in Graph" after editing */
  onSelectMemory?: (id: string) => void
  /** Called with undo entry after a successful operation */
  onUndoEntry?: (entry: { type: 'create' | 'update' | 'archive'; memoryId: string; previousState?: Record<string, unknown> }) => void
}

export default function MemoryForm({ memoryId, onClose, onChange, onSelectMemory, onUndoEntry }: Props) {
  const isEdit = memoryId !== null

  // Form fields
  const [id, setId] = useState('')
  const [summary, setSummary] = useState('')
  const [tags, setTags] = useState('')
  const [intensity, setIntensity] = useState(5)
  const [body, setBody] = useState('')
  const [status, setStatus] = useState('active')
  const [maturity, setMaturity] = useState('draft')
  const [changeNote, setChangeNote] = useState('')
  // Imports (PL1-9): comma-separated IDs with strength selection
  const [importsText, setImportsText] = useState('')
  const [importStrengths, setImportStrengths] = useState<Record<string, string>>({})

  // UI state
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [visible, setVisible] = useState(false)
  const [showUnsavedWarning, setShowUnsavedWarning] = useState(false)
  const previousStateRef = useRef<Record<string, unknown> | null>(null)
  // Track initial values to detect unsaved changes
  const initialValuesRef = useRef<{ summary: string; tags: string; intensity: number; body: string; status: string; maturity: string; importsText: string } | null>(null)
  const pendingCloseRef = useRef<(() => void) | null>(null)

  // Template support (R5-template-create)
  const [templates, setTemplates] = useState<MemorySummary[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState('')

  // Load existing data in edit mode
  useEffect(() => {
    if (!memoryId) {
      setId('')
      setSummary('')
      setTags('')
      setIntensity(5)
      setBody('')
      setStatus('active')
      setMaturity('draft')
      setChangeNote('')
      setImportsText('')
      setImportStrengths({})
      setVisible(true)
      initialValuesRef.current = {
        summary: '', tags: '', intensity: 5, body: '', status: 'active', maturity: 'draft', importsText: '',
      }
      return
    }

    setVisible(true)
    setLoading(true)
    setError(null)

    fetchMemory(memoryId)
      .then((mem) => {
        // Store previous state for undo
        previousStateRef.current = {
          body: mem.body ?? '',
          summary: mem.summary ?? '',
          tags: mem.tags ?? [],
          intensity: mem.intensity ?? 5,
          status: mem.status ?? 'active',
          maturity: mem.maturity ?? 'draft',
        }
        setId(mem.id)
        setSummary(mem.summary || '')
        setTags((mem.tags || []).join(', '))
        setIntensity(mem.intensity || 5)
        setBody(mem.body || '')
        setStatus(mem.status || 'active')
        setMaturity(mem.maturity || 'draft')
        setChangeNote('')
        // PL1-9: populate imports from existing memory
        const allIds: string[] = []
        const strengths: Record<string, string> = {}
        if (mem.imports) {
          for (const [strength, deps] of Object.entries(mem.imports)) {
            if (Array.isArray(deps)) {
              for (const dep of deps) {
                const depId = typeof dep === 'string' ? dep : (dep as { id?: string }).id || ''
                if (depId) {
                  allIds.push(depId)
                  strengths[depId] = strength
                }
              }
            }
          }
          setImportsText(allIds.join(', '))
          setImportStrengths(strengths)
        } else {
          setImportsText('')
          setImportStrengths({})
        }
        // Capture initial values for dirty detection
        initialValuesRef.current = {
          summary: mem.summary || '',
          tags: (mem.tags || []).join(', '),
          intensity: mem.intensity || 5,
          body: mem.body || '',
          status: mem.status || 'active',
          maturity: mem.maturity || 'draft',
          importsText: allIds.join(', '),
        }
      })
      .catch((err) => {
        console.error('Failed to load memory:', err)
        setError('Failed to load memory data')
      })
      .finally(() => setLoading(false))
  }, [memoryId])

  // Load schemas for template selection (create mode only)
  useEffect(() => {
    if (isEdit) return
    fetchAllMemories()
      .then((mems) => setTemplates(mems.filter((m) => m.type === 'schema')))
      .catch(() => setTemplates([]))
  }, [isEdit])

  // When a template is selected, load its details and prefill form
  const handleTemplateSelect = useCallback((templateId: string) => {
    if (!templateId) return
    setSelectedTemplate(templateId)
    fetchMemory(templateId)
      .then((mem) => {
        // Prefill: use the schema's body/summary as guidance, set schema field
        setSummary(mem.summary ? `[from ${templateId}] ` : '')
        setTags((mem.tags || []).join(', '))
        setMaturity(mem.maturity || 'draft')
        if (mem.body) {
          setBody(`<!-- Template from ${templateId} -->\n${mem.body}`)
        }
        // Don't override ID or intensity — user controls those
      })
      .catch((err) => console.error('Failed to load template:', err))
  }, [])

  // Validation
  const validate = useCallback((): string | null => {
    if (!isEdit && !id.trim()) {
      return 'ID is required'
    }
    if (!isEdit && id.trim() && !id.includes('/')) {
      return 'ID must contain at least one "/" (e.g. "user/ideas/my-thesis")'
    }
    if (intensity < 1 || intensity > 10) {
      return 'Intensity must be between 1 and 10'
    }
    return null
  }, [id, intensity, isEdit])

  // Dirty state detection (R5-unsaved-changes-warning)
  const isDirty = useCallback((): boolean => {
    const init = initialValuesRef.current
    if (!init) return false
    return (
      summary !== init.summary ||
      tags !== init.tags ||
      intensity !== init.intensity ||
      body !== init.body ||
      (isEdit && status !== init.status) ||
      maturity !== init.maturity ||
      importsText !== init.importsText
    )
  }, [summary, tags, intensity, body, status, maturity, importsText, isEdit])

  // Safe close with dirty check
  const requestClose = useCallback((action?: () => void) => {
    if (isDirty()) {
      pendingCloseRef.current = action || (() => onClose())
      setShowUnsavedWarning(true)
    } else if (action) {
      action()
    } else {
      onClose()
    }
  }, [isDirty, onClose])

  const confirmDiscard = useCallback(() => {
    setShowUnsavedWarning(false)
    if (pendingCloseRef.current) {
      pendingCloseRef.current()
      pendingCloseRef.current = null
    } else {
      onClose()
    }
  }, [onClose])

  const cancelDiscard = useCallback(() => {
    setShowUnsavedWarning(false)
    pendingCloseRef.current = null
  }, [])

  // Handle create
  const handleCreate = useCallback(async () => {
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setSaving(true)
    setError(null)

    try {
      const tagList = tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)

      // PL1-9: build imports structure from comma-separated IDs + strengths
      const importIds = importsText
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)
      const imports: Record<string, string[]> = { required: [], recommended: [], related: [] }
      for (const impId of importIds) {
        const strength = (importStrengths[impId] || 'required') as 'required' | 'recommended' | 'related'
        imports[strength].push(impId)
      }
      const hasImports = imports.required.length > 0 || imports.recommended.length > 0 || imports.related.length > 0

      await createMemory({
        id: id.trim(),
        summary: summary.trim() || undefined,
        tags: tagList.length > 0 ? tagList : undefined,
        intensity,
        body: body || undefined,
        maturity: maturity || undefined,
        ...(hasImports ? { imports } : {}),
      })

      onChange()
      if (onUndoEntry) onUndoEntry({ type: 'create', memoryId: id.trim() })
      onClose()
    } catch (err) {
      console.error('Create failed:', err)
      setError(err instanceof Error ? err.message : 'Create failed')
    } finally {
      setSaving(false)
    }
  }, [id, summary, tags, intensity, body, maturity, importsText, importStrengths, validate, onChange, onClose, onUndoEntry])

  // Handle update
  const handleUpdate = useCallback(async () => {
    if (!memoryId) return

    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setSaving(true)
    setError(null)

    try {
      const tagList = tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)

      // PL1-9: build imports structure
      const importIds = importsText
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)
      const imports: Record<string, string[]> = { required: [], recommended: [], related: [] }
      for (const impId of importIds) {
        const strength = (importStrengths[impId] || 'required') as 'required' | 'recommended' | 'related'
        imports[strength].push(impId)
      }
      const hasImports = imports.required.length > 0 || imports.recommended.length > 0 || imports.related.length > 0

      await updateMemory(memoryId, {
        body: body || undefined,
        summary: summary.trim() || undefined,
        tags: tagList.length > 0 ? tagList : undefined,
        intensity,
        status: status || undefined,
        maturity: maturity || undefined,
        change_note: changeNote.trim() || 'UI update',
        ...(hasImports ? { imports } : {}),
      })

      onChange()
      if (onUndoEntry && memoryId) {
        onUndoEntry({
          type: 'update',
          memoryId,
          previousState: previousStateRef.current ?? undefined,
        })
      }
      onClose()
    } catch (err) {
      console.error('Update failed:', err)
      setError(err instanceof Error ? err.message : 'Update failed')
    } finally {
      setSaving(false)
    }
  }, [memoryId, body, summary, tags, intensity, status, maturity, changeNote, importsText, importStrengths, validate, onChange, onClose, onUndoEntry])

  // Handle delete
  const handleDelete = useCallback(async () => {
    if (!memoryId) return

    setDeleting(true)
    setError(null)

    try {
      // Store current status for undo (if it was active, undo should restore active)
      const prevStatus = status
      await updateMemory(memoryId, {
        status: 'archived',
        change_note: 'Archived via UI',
      })

      onChange()
      if (onUndoEntry && memoryId) {
        onUndoEntry({
          type: 'archive',
          memoryId,
          previousState: { status: prevStatus },
        })
      }
      onClose()
    } catch (err) {
      console.error('Delete failed:', err)
      setError(err instanceof Error ? err.message : 'Archive failed')
    } finally {
      setDeleting(false)
      setShowDeleteConfirm(false)
    }
  }, [memoryId, onChange, onClose])

  // Close on Escape (with dirty check)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !showDeleteConfirm && !showUnsavedWarning) requestClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [requestClose, showDeleteConfirm, showUnsavedWarning])

  if (!visible) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={() => requestClose()}
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(28,25,23,0.15)',
          zIndex: 50,
        }}
      />

      {/* Slide-in panel */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '34vw',
          minWidth: 400,
          maxWidth: 560,
          backgroundColor: '#FFFBEB',
          borderLeft: '1px solid #E7E5E4',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 51,
          boxShadow: '0 4px 24px rgba(28,25,23,0.12)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '18px 24px',
            borderBottom: '1px solid #E7E5E4',
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              fontSize: 22,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: '#1C1917',
              margin: 0,
            }}
          >
            {isEdit ? 'Edit Memory' : 'New Memory'}
          </h2>
          <button
            onClick={() => requestClose()}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 20,
              color: '#57534E',
              padding: '4px 8px',
              borderRadius: 2,
              lineHeight: 1,
              fontFamily: 'Raleway, sans-serif',
            }}
          >
            ✕
          </button>
        </div>

        {/* Error banner */}
        {error && (
          <div
            style={{
              margin: '12px 24px 0',
              padding: '8px 12px',
              backgroundColor: '#991B1B0A',
              borderLeft: '3px solid #991B1B',
              borderRadius: 2,
              fontSize: 12,
              fontFamily: 'Raleway, sans-serif',
              color: '#991B1B',
            }}
          >
            {error}
          </div>
        )}

        {/* Form body */}
        {loading ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#A8A29E',
              fontFamily: 'Raleway, sans-serif',
              fontSize: 14,
            }}
          >
            Loading...
          </div>
        ) : (
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '24px',
            }}
          >
            {/* Template selector (create mode only) */}
            {!isEdit && templates.length > 0 && (
              <Field label="Template (optional)">
                <select
                  value={selectedTemplate}
                  onChange={(e) => handleTemplateSelect(e.target.value)}
                  style={inputStyle}
                >
                  <option value="">None — start blank</option>
                  {templates.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.id} — {t.summary}
                    </option>
                  ))}
                </select>
              </Field>
            )}

            {/* ID field */}
            <Field label="ID" required={!isEdit}>
              <input
                type="text"
                value={id}
                onChange={(e) => setId(e.target.value)}
                disabled={isEdit}
                placeholder="user/ideas/my-thesis"
                style={inputStyle}
              />
              {isEdit && (
                <div style={{ fontSize: 10, color: '#A8A29E', fontFamily: 'Raleway, sans-serif', marginTop: 2 }}>
                  ID cannot be changed after creation
                </div>
              )}
            </Field>

            {/* Summary */}
            <Field label="Summary">
              <input
                type="text"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="Brief description of this memory"
                style={inputStyle}
              />
            </Field>

            {/* Tags */}
            <Field label="Tags (comma-separated)">
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="tag1, tag2, tag3"
                style={inputStyle}
              />
            </Field>

            {/* Imports (PL1-9) */}
            <Field label="Imports (comma-separated IDs)">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <input
                  type="text"
                  value={importsText}
                  onChange={(e) => {
                    setImportsText(e.target.value)
                    // Parse IDs and init strengths for new ones
                    const ids = e.target.value
                      .split(',')
                      .map((t) => t.trim())
                      .filter(Boolean)
                    const newStrengths = { ...importStrengths }
                    for (const id of ids) {
                      if (!newStrengths[id]) {
                        newStrengths[id] = 'required'
                      }
                    }
                    // Remove strengths for removed IDs
                    for (const key of Object.keys(newStrengths)) {
                      if (!ids.includes(key)) {
                        delete newStrengths[key]
                      }
                    }
                    setImportStrengths(newStrengths)
                  }}
                  placeholder="user/ideas/a, user/facts/b"
                  style={inputStyle}
                />
                {Object.entries(importStrengths).length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {Object.entries(importStrengths).map(([impId, strength]) => (
                      <div
                        key={impId}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          fontSize: 12,
                          fontFamily: 'JetBrains Mono, monospace',
                          color: '#57534E',
                        }}
                      >
                        <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {impId}
                        </span>
                        <select
                          value={strength}
                          onChange={(e) =>
                            setImportStrengths((prev) => ({ ...prev, [impId]: e.target.value }))
                          }
                          style={{
                            ...inputStyle,
                            width: 120,
                            padding: '2px 8px',
                            fontSize: 11,
                          }}
                        >
                          <option value="required">Required</option>
                          <option value="recommended">Recommended</option>
                          <option value="related">Related</option>
                        </select>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Field>

            {/* Intensity */}
            <Field label="Intensity (1-10)">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={intensity}
                  onChange={(e) => setIntensity(Number(e.target.value))}
                  style={{ flex: 1, accentColor: '#B8860B', cursor: 'pointer' }}
                />
                <span
                  style={{
                    fontSize: 14,
                    fontFamily: 'JetBrains Mono, monospace',
                    color: '#1C1917',
                    minWidth: 20,
                    textAlign: 'center',
                  }}
                >
                  {intensity}
                </span>
              </div>
            </Field>

            {/* Maturity (PL3-7: exposed in both create and edit) */}
            <Field label="Maturity">
              <select
                value={maturity}
                onChange={(e) => setMaturity(e.target.value)}
                style={inputStyle}
              >
                <option value="draft">Draft</option>
                <option value="verified">Verified</option>
                <option value="proven">Proven</option>
                <option value="superseded">Superseded</option>
              </select>
            </Field>

            {/* Status (edit only) */}
            {isEdit && (
              <Field label="Status">
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  style={inputStyle}
                >
                  <option value="active">Active</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                  <option value="superseded">Superseded</option>
                </select>
              </Field>
            )}

            {/* Change note (edit only) */}
            {isEdit && (
              <Field label="Change Note">
                <input
                  type="text"
                  value={changeNote}
                  onChange={(e) => setChangeNote(e.target.value)}
                  placeholder="What changed and why"
                  style={inputStyle}
                />
              </Field>
            )}

            {/* Body */}
            <Field label="Body (Markdown)">
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write markdown content here..."
                style={{
                  ...inputStyle,
                  minHeight: 180,
                  resize: 'vertical',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: 13,
                  lineHeight: 1.6,
                }}
              />
            </Field>
          </div>
        )}

        {/* Footer buttons */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid #E7E5E4',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            flexShrink: 0,
          }}
        >
          {isEdit && (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={saving || deleting}
              style={{
                padding: '10px 20px',
                border: '1px solid #A8A29E',
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
              {deleting ? 'Archiving...' : 'Archive'}
            </button>
          )}

          <div style={{ flex: 1 }} />

          <button
            onClick={() => requestClose()}
            style={{
              padding: '10px 20px',
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
            Cancel
          </button>

          <button
            onClick={isEdit ? handleUpdate : handleCreate}
            disabled={saving || loading}
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
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create'}
          </button>
        </div>
      </div>

      {/* Unsaved changes warning modal */}
      {showUnsavedWarning && (
        <>
          <div
            onClick={cancelDiscard}
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(28,25,23,0.2)',
              zIndex: 60,
            }}
          />
          <div
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              backgroundColor: '#FFFBEB',
              border: '1px solid #E7E5E4',
              borderRadius: 2,
              padding: 28,
              maxWidth: 400,
              width: '90%',
              zIndex: 61,
              boxShadow: '0 4px 24px rgba(28,25,23,0.12)',
            }}
          >
            <h3
              style={{
                fontSize: 18,
                fontFamily: "'Cormorant Garamond', serif",
                fontWeight: 500,
                color: '#1C1917',
                margin: '0 0 12px 0',
              }}
            >
              Unsaved Changes
            </h3>
            <p
              style={{
                fontSize: 14,
                fontFamily: 'Raleway, sans-serif',
                color: '#57534E',
                lineHeight: 1.6,
                margin: '0 0 20px 0',
              }}
            >
              You have unsaved changes. Discard them?
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                onClick={cancelDiscard}
                style={{
                  padding: '8px 20px',
                  border: '1px solid #D4D4D8',
                  background: 'transparent',
                  color: '#57534E',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  borderRadius: 2,
                }}
              >
                Keep Editing
              </button>
              <button
                onClick={confirmDiscard}
                style={{
                  padding: '8px 20px',
                  backgroundColor: '#991B1B',
                  color: '#FFFFFF',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  borderRadius: 2,
                }}
              >
                Discard
              </button>
            </div>
          </div>
        </>
      )}

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <>
          <div
            onClick={() => setShowDeleteConfirm(false)}
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(28,25,23,0.2)',
              zIndex: 60,
            }}
          />
          <div
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              backgroundColor: '#FFFBEB',
              border: '1px solid #E7E5E4',
              borderRadius: 2,
              padding: 28,
              maxWidth: 420,
              width: '90%',
              zIndex: 61,
              boxShadow: '0 4px 24px rgba(28,25,23,0.12)',
            }}
          >
            <h3
              style={{
                fontSize: 18,
                fontFamily: "'Cormorant Garamond', serif",
                fontWeight: 500,
                color: '#1C1917',
                margin: '0 0 12px 0',
              }}
            >
              Archive Memory
            </h3>
            <p
              style={{
                fontSize: 14,
                fontFamily: 'Raleway, sans-serif',
                color: '#57534E',
                lineHeight: 1.6,
                margin: '0 0 8px 0',
              }}
            >
              Are you sure you want to archive this memory? It will be marked as archived
              and hidden from most views.
            </p>
            <p
              style={{
                fontSize: 12,
                fontFamily: 'JetBrains Mono, monospace',
                color: '#A8A29E',
                margin: '0 0 20px 0',
              }}
            >
              {memoryId}
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                style={{
                  padding: '8px 20px',
                  border: '1px solid #D4D4D8',
                  background: 'transparent',
                  color: '#57534E',
                  cursor: 'pointer',
                  fontSize: 11,
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
                onClick={handleDelete}
                disabled={deleting}
                style={{
                  padding: '8px 20px',
                  backgroundColor: '#57534E',
                  color: '#FFFFFF',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: 'Raleway, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  borderRadius: 2,
                }}
              >
                {deleting ? 'Archiving...' : 'Yes, Archive'}
              </button>
            </div>
          </div>
        </>
      )}
    </>
  )
}

// ── Shared field component ─────────────────────────────────────────

function Field({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div style={{ marginBottom: 20 }}>
      <label
        style={{
          display: 'block',
          fontSize: 11,
          fontWeight: 600,
          fontFamily: 'Raleway, sans-serif',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: '#57534E',
          marginBottom: 6,
        }}
      >
        {label}
        {required && (
          <span style={{ color: '#991B1B', marginLeft: 4 }}>*</span>
        )}
      </label>
      {children}
    </div>
  )
}

// ── Shared input style ─────────────────────────────────────────────

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  border: '1px solid #D4D4D8',
  borderRadius: 2,
  fontSize: 13,
  fontFamily: 'Raleway, sans-serif',
  color: '#1C1917',
  backgroundColor: '#FFFFFF',
  outline: 'none',
  boxSizing: 'border-box',
}
