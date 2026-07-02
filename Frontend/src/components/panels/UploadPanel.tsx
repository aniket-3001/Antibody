'use client'

import { useState, useRef, useCallback } from 'react'
import { useAppActions } from '@/context/AppStore'
import { useRefresh } from '@/hooks/useRefresh'
import { api } from '@/lib/api'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { ProgressBar } from '@/components/ui/ProgressBar'
import type { ContentType, MemoryOperation, IngestStatus } from '@/lib/types'

/**
 * UploadPanel — full ingest form. Spec §4.
 *
 * Supports: PDF file, text, markdown, URL.
 * Operation: Add (remember) or Expand (improve).
 * Validation: client-side mirrors backend spec §5.1.
 * Progress: fake 30s bar, snaps to 100% on completion.
 */

const CONTENT_TYPES: { value: ContentType; label: string; icon: string }[] = [
  { value: 'pdf',      label: 'PDF',      icon: '📕' },
  { value: 'text',     label: 'Text',     icon: '📄' },
  { value: 'markdown', label: 'Markdown', icon: '📝' },
  { value: 'url',      label: 'URL',      icon: '🔗' },
]

type UploadPhase = 'idle' | 'submitting' | 'processing' | 'success' | 'error'

interface SuccessResult {
  status: IngestStatus
  nodes_created: number
  edges_created: number
}

export function UploadPanel() {
  const { addToast, setTab } = useAppActions()
  const { refreshAll } = useRefresh()

  // Form state
  const [operation, setOperation] = useState<MemoryOperation>('remember')
  const [contentType, setContentType] = useState<ContentType>('pdf')
  const [file, setFile] = useState<File | null>(null)
  const [textContent, setTextContent] = useState('')
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [hypotheses, setHypotheses] = useState<string[]>([])
  const [hypothesisInput, setHypothesisInput] = useState('')

  // Upload phase
  const [phase, setPhase] = useState<UploadPhase>('idle')
  const [result, setResult] = useState<SuccessResult | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)

  // ── Validation ─────────────────────────────────────────────────────────────
  function validate(): boolean {
    const errs: Record<string, string> = {}

    if (contentType === 'pdf' && !file) {
      errs.file = 'Please select a PDF file.'
    }
    if (contentType === 'pdf' && file && file.size > 20 * 1024 * 1024) {
      errs.file = 'File must be ≤ 20 MB.'
    }
    if ((contentType === 'text' || contentType === 'markdown') && !textContent.trim()) {
      errs.content = 'Content is required.'
    }
    if (contentType === 'text' && textContent.length > 500_000) {
      errs.content = 'Content must be ≤ 500,000 characters.'
    }
    if (contentType === 'url') {
      if (!url.trim()) {
        errs.url = 'URL is required.'
      } else if (!/^https?:\/\//i.test(url.trim())) {
        errs.url = 'URL must begin with http:// or https://.'
      }
    }
    if (title.length > 255) {
      errs.title = 'Title must be ≤ 255 characters.'
    }
    if (hypotheses.length > 5) {
      errs.hypotheses = 'Maximum 5 hypotheses.'
    }

    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    if (!validate()) return

    setError(null)
    setPhase('submitting')

    // Build FormData per spec §5.1
    const fd = new FormData()
    fd.append('content_type', contentType)

    if (contentType === 'pdf' && file) {
      fd.append('file', file)
    } else if (contentType === 'url') {
      fd.append('content', url.trim())
    } else {
      fd.append('content', textContent)
    }

    if (title.trim()) fd.append('title', title.trim())
    if (hypotheses.length > 0) {
      fd.append('active_hypotheses', JSON.stringify(hypotheses))
    }

    setTimeout(() => {
      if (phase === 'submitting') setPhase('processing')
    }, 1000)
    setPhase('processing')

    try {
      const res = operation === 'remember'
        ? await api.remember(fd)
        : await api.improve(fd)

      setResult({
        status: res.status,
        nodes_created: res.nodes_created,
        edges_created: res.edges_created,
      })
      setPhase('success')

      await refreshAll()
      addToast('success', 'Graph expanded. Ask a question.')

      // Switch to recall after short delay
      setTimeout(() => setTab('recall'), 2000)
    } catch (err) {
      setError(err as Error)
      setPhase('error')
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [operation, contentType, file, textContent, url, title, hypotheses, refreshAll, addToast, setTab])

  // ── Drag and drop ──────────────────────────────────────────────────────────
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files[0]
    if (dropped?.type === 'application/pdf') {
      setFile(dropped)
      setFieldErrors((prev) => ({ ...prev, file: '' }))
    }
  }

  const handleDragOver = (e: React.DragEvent) => e.preventDefault()

  // ── Reset ──────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setPhase('idle')
    setResult(null)
    setError(null)
    setFile(null)
    setTextContent('')
    setUrl('')
    setTitle('')
    setHypotheses([])
    setFieldErrors({})
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full overflow-y-auto panel-scroll px-4 py-4 space-y-5">

      {/* ── Success state ────────────────────────────────────────────────── */}
      {phase === 'success' && result && (
        <div className="flex flex-col items-center text-center gap-4 py-6">
          <div className="text-4xl" aria-hidden="true">✅</div>
          <div>
            <p className="text-sm font-semibold text-slate-200 mb-1">
              {result.status === 'skipped_duplicate' ? 'Already in memory' : 'Memory updated'}
            </p>
            {result.status !== 'skipped_duplicate' && (
              <p className="text-xs text-slate-400">
                {result.nodes_created} nodes · {result.edges_created} edges added
              </p>
            )}
            {result.status === 'skipped_duplicate' && (
              <p className="text-xs text-slate-500">This document was previously ingested (skipped).</p>
            )}
            {result.status === 'degraded' && (
              <p className="text-xs text-amber-400 mt-1">
                Stored but no new structure extracted. Try a richer document.
              </p>
            )}
          </div>
          <p className="text-xs text-slate-600">Switching to Recall…</p>
          <button
            onClick={handleReset}
            className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            Upload another
          </button>
        </div>
      )}

      {/* ── Progress state ───────────────────────────────────────────────── */}
      {(phase === 'submitting' || phase === 'processing') && (
        <div className="flex flex-col gap-4 py-6">
          <div className="text-center">
            <p className="text-sm font-medium text-slate-200 mb-1">
              {phase === 'submitting' ? 'Sending to memory…' : 'Building knowledge graph…'}
            </p>
            <p className="text-xs text-slate-500">~30s remaining</p>
          </div>
          <ProgressBar complete={false} />
          <p className="text-xs text-slate-600 text-center flex items-center justify-center gap-1.5">
            <span aria-hidden="true">ℹ</span>
            Extracting entities and relationships. This takes 15–60 seconds.
          </p>
        </div>
      )}

      {/* ── Idle / error form ────────────────────────────────────────────── */}
      {(phase === 'idle' || phase === 'error') && (
        <>
          {/* Operation toggle */}
          <div>
            <p className="text-xs font-medium text-slate-400 mb-2">Memory Operation</p>
            <div className="flex rounded-lg border border-slate-700 overflow-hidden">
              {(['remember', 'improve'] as MemoryOperation[]).map((op) => (
                <button
                  key={op}
                  onClick={() => setOperation(op)}
                  className={`flex-1 py-2 text-xs font-medium transition-colors ${
                    operation === op
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                  aria-pressed={operation === op}
                >
                  {op === 'remember' ? '📥 Add (remember)' : '📈 Expand (improve)'}
                </button>
              ))}
            </div>
          </div>

          {/* Source type */}
          <div>
            <label htmlFor="source-type" className="text-xs font-medium text-slate-400 block mb-2">
              Source Type
            </label>
            <div className="grid grid-cols-4 gap-1">
              {CONTENT_TYPES.map((ct) => (
                <button
                  key={ct.value}
                  onClick={() => { setContentType(ct.value); setFieldErrors({}) }}
                  className={`flex flex-col items-center gap-1 py-2.5 rounded-lg border text-xs font-medium transition-all ${
                    contentType === ct.value
                      ? 'border-emerald-500 bg-emerald-500/10 text-emerald-300'
                      : 'border-slate-700 bg-slate-800/40 text-slate-500 hover:border-slate-600 hover:text-slate-300'
                  }`}
                  aria-pressed={contentType === ct.value}
                >
                  <span className="text-base" aria-hidden="true">{ct.icon}</span>
                  {ct.label}
                </button>
              ))}
            </div>
          </div>

          {/* Content input */}
          {contentType === 'pdf' && (
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-2">PDF File</label>
              <div
                ref={dropZoneRef}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                  file ? 'border-emerald-500/60 bg-emerald-500/5' : 'border-slate-700 hover:border-slate-600 bg-slate-800/30'
                }`}
                role="button"
                aria-label="Click or drag to upload PDF"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
              >
                {file ? (
                  <div className="space-y-1">
                    <p className="text-sm text-slate-300 font-medium truncate">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                    <button
                      onClick={(e) => { e.stopPropagation(); setFile(null) }}
                      className="text-xs text-red-400 hover:text-red-300 transition-colors"
                      aria-label="Remove file"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="space-y-1 text-slate-500">
                    <p className="text-2xl" aria-hidden="true">📁</p>
                    <p className="text-sm">Drag &amp; drop a PDF here</p>
                    <p className="text-xs">or click to browse · Max 20 MB</p>
                  </div>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                aria-hidden="true"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) { setFile(f); setFieldErrors((p) => ({ ...p, file: '' })) }
                }}
              />
              {fieldErrors.file && <FieldError msg={fieldErrors.file} />}
            </div>
          )}

          {(contentType === 'text' || contentType === 'markdown') && (
            <div>
              <label htmlFor="text-content" className="text-xs font-medium text-slate-400 block mb-2">
                Content
              </label>
              <textarea
                id="text-content"
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="Paste or type content here…"
                rows={8}
                maxLength={500_000}
                className="w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 resize-none transition-colors"
              />
              <div className="flex justify-between items-center mt-1">
                {fieldErrors.content ? <FieldError msg={fieldErrors.content} /> : <span />}
                <span className="text-xs text-slate-600">{textContent.length.toLocaleString()} / 500,000</span>
              </div>
            </div>
          )}

          {contentType === 'url' && (
            <div>
              <label htmlFor="url-input" className="text-xs font-medium text-slate-400 block mb-2">
                URL
              </label>
              <input
                id="url-input"
                type="url"
                value={url}
                onChange={(e) => { setUrl(e.target.value); setFieldErrors((p) => ({ ...p, url: '' })) }}
                placeholder="https://…"
                className="w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-colors"
              />
              {fieldErrors.url && <FieldError msg={fieldErrors.url} />}
            </div>
          )}

          {/* Title */}
          <div>
            <label htmlFor="title-input" className="text-xs font-medium text-slate-400 block mb-2">
              Title <span className="text-slate-600">(optional)</span>
            </label>
            <input
              id="title-input"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="YOLO11 Detection Paper"
              maxLength={255}
              className="w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-colors"
            />
            {fieldErrors.title && <FieldError msg={fieldErrors.title} />}
          </div>

          {/* Hypotheses */}
          <div>
            <p className="text-xs font-medium text-slate-400 mb-2">
              Active Hypotheses <span className="text-slate-600">(optional, max 5)</span>
            </p>
            {hypotheses.map((h, i) => (
              <div key={i} className="flex items-start gap-2 mb-1.5">
                <span className="text-slate-600 text-xs mt-1.5">—</span>
                <p className="flex-1 text-xs text-slate-400 bg-slate-800/60 rounded px-2 py-1.5 border border-slate-700">{h}</p>
                <button
                  onClick={() => setHypotheses((prev) => prev.filter((_, j) => j !== i))}
                  className="text-slate-600 hover:text-red-400 text-xs mt-1"
                  aria-label={`Remove hypothesis: ${h}`}
                >
                  ×
                </button>
              </div>
            ))}
            {hypotheses.length < 5 && (
              <div className="flex gap-2 mt-1">
                <input
                  type="text"
                  value={hypothesisInput}
                  onChange={(e) => setHypothesisInput(e.target.value)}
                  placeholder="YOLO11 outperforms YOLO9 on COCO"
                  maxLength={1000}
                  className="flex-1 bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 placeholder-slate-600 focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-colors"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && hypothesisInput.trim()) {
                      e.preventDefault()
                      setHypotheses((prev) => [...prev, hypothesisInput.trim()])
                      setHypothesisInput('')
                    }
                  }}
                />
                <button
                  onClick={() => {
                    if (hypothesisInput.trim()) {
                      setHypotheses((prev) => [...prev, hypothesisInput.trim()])
                      setHypothesisInput('')
                    }
                  }}
                  className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors px-2"
                  aria-label="Add hypothesis"
                >
                  + Add
                </button>
              </div>
            )}
          </div>

          {/* Error */}
          {phase === 'error' && error && (
            <ErrorMessage error={error} onRetry={() => void handleSubmit()} />
          )}

          {/* Submit */}
          <button
            onClick={() => void handleSubmit()}
            className="flex items-center justify-center gap-2 w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors shadow-md shadow-emerald-900/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400"
            aria-label={operation === 'remember' ? 'Add to memory' : 'Expand memory'}
          >
            <span aria-hidden="true">▶</span>
            {operation === 'remember' ? 'Add to Memory' : 'Expand Memory'}
          </button>
        </>
      )}
    </div>
  )
}

function FieldError({ msg }: { msg: string }) {
  return <p className="text-xs text-red-400 mt-1 flex items-center gap-1"><span aria-hidden="true">⚠</span>{msg}</p>
}
