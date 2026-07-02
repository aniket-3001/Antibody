'use client'

import { useState, useCallback, useRef } from 'react'
import { useAppState, useAppActions } from '@/context/AppStore'
import { api } from '@/lib/api'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import type { RecallStrategy } from '@/lib/types'
import { STRATEGY_META } from '@/lib/types'

/**
 * RecallPanel — implements the full recall UX: spec §5.
 * - Query input + strategy selector
 * - Loading state
 * - Answer display with evidence count
 * - Recall history chips
 * - Evidence mode triggers graph highlighting
 */

const STRATEGY_OPTIONS: { value: RecallStrategy | ''; label: string; emoji: string }[] = [
  { value: '',              label: 'Auto-detect', emoji: '🤖' },
  { value: 'relationship',  label: 'Relationship', emoji: '🔵' },
  { value: 'contradiction', label: 'Contradiction', emoji: '🔴' },
  { value: 'gap_analysis',  label: 'Gap Analysis',  emoji: '🟡' },
  { value: 'factual',       label: 'Factual',       emoji: '🟢' },
]

export function RecallPanel() {
  const { lastRecall, recallHistory, graph, loadingGraph } = useAppState()
  const { setLastRecall, addRecallHistory, setEvidence, clearEvidence, addToast } = useAppActions()

  const [query, setQuery] = useState('')
  const [strategy, setStrategy] = useState<RecallStrategy | ''>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [showResult, setShowResult] = useState(false)

  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const hasGraph = !!graph && graph.node_count > 0

  const handleSubmit = useCallback(async () => {
    const trimmed = query.trim()
    if (!trimmed) return
    setError(null)
    setLoading(true)
    clearEvidence()

    try {
      const result = await api.recall({
        query: trimmed,
        strategy: strategy || null,
      })

      setLastRecall(result)
      addRecallHistory(trimmed)
      setShowResult(true)

      // Apply evidence mode if evidence graph returned (spec §5.2)
      if (result.evidence_graph && result.evidence_graph.node_count > 0) {
        const nodeIds = new Set(
          result.evidence_graph.elements
            .filter((el) => !('source' in el.data) || !('target' in el.data))
            .map((el) => el.data.id.replace(/^node-/, '')),
        )
        setEvidence(nodeIds, (result.strategy_used as RecallStrategy) || null)
        addToast('info', `${nodeIds.size} nodes highlighted in graph`)
      } else {
        addToast('warning', 'No graph evidence found — answer is from semantic search only.')
      }
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [query, strategy, clearEvidence, setLastRecall, addRecallHistory, setEvidence, addToast])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSubmit()
    }
  }

  const handleNewQuestion = () => {
    setShowResult(false)
    setQuery('')
    clearEvidence()
    setTimeout(() => textareaRef.current?.focus(), 50)
  }

  const strategyMeta = strategy ? STRATEGY_META[strategy] : null

  return (
    <div className="flex flex-col h-full panel-scroll">
      {showResult && lastRecall ? (
        /* ── Result view (spec §5.3) ────────────────────────────────────── */
        <div className="flex flex-col h-full">
          <div className="flex-none px-4 pt-3 pb-2 border-b border-slate-700/60">
            <button
              onClick={handleNewQuestion}
              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 transition-colors"
              aria-label="Ask a new question"
            >
              ← New Question
            </button>
          </div>

          <div className="flex-1 overflow-y-auto panel-scroll px-4 py-4 space-y-5">
            {/* Answer */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg" aria-hidden="true">✦</span>
                <h3 className="text-sm font-semibold text-slate-200">Answer</h3>
              </div>
              <div className="h-px bg-slate-700/60 mb-3" />
              <p
                className="text-slate-300 text-sm leading-relaxed"
                aria-live="polite"
              >
                {lastRecall.answer || 'No answer returned.'}
              </p>
            </div>

            {/* Metadata */}
            <div className="border-t border-slate-700/60 pt-3 space-y-2">
              <MetaRow label="Strategy used">
                <StrategyBadge strategy={lastRecall.strategy_used as RecallStrategy} />
              </MetaRow>

              {lastRecall.evidence_graph && lastRecall.evidence_graph.node_count > 0 ? (
                <MetaRow label="Evidence">
                  <button
                    onClick={() => {/* canvas auto-fit is handled in GraphArea */}}
                    className="text-emerald-400 hover:text-emerald-300 text-sm transition-colors"
                  >
                    {lastRecall.evidence_graph.node_count} nodes highlighted in graph →
                  </button>
                </MetaRow>
              ) : (
                <div className="rounded-md border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-300 flex items-start gap-1.5">
                  <span aria-hidden="true">⚠</span>
                  <span>
                    No graph evidence found. Answer is based on semantic search only.
                    Try the Contradiction or Relationship strategy.
                  </span>
                </div>
              )}

              <MetaRow label="Duration">
                <span className="text-slate-400 text-sm">{(lastRecall.duration_ms / 1000).toFixed(1)} s</span>
              </MetaRow>
            </div>
          </div>
        </div>
      ) : (
        /* ── Query input view (spec §5.1) ───────────────────────────────── */
        <div className="flex flex-col h-full px-4 py-4 space-y-4">
          {/* Recall history chips (spec §5.5) */}
          {recallHistory.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-1.5">Recent:</p>
              <div className="flex flex-wrap gap-1.5">
                {recallHistory.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setQuery(q)}
                    className="text-xs px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-colors truncate max-w-[160px]"
                    title={q}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Query input */}
          <div className="space-y-2">
            <label htmlFor="recall-query" className="text-sm font-medium text-slate-300">
              Ask your memory
            </label>
            <div className="relative">
              <textarea
                id="recall-query"
                ref={textareaRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Which papers contradict each other?"
                rows={4}
                maxLength={2000}
                disabled={loading}
                className="w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-colors resize-none disabled:opacity-50"
                aria-describedby="recall-hint"
              />
              <span className="absolute bottom-2 right-2.5 text-xs text-slate-600" aria-hidden="true">
                {query.length}/2000
              </span>
            </div>
            <p id="recall-hint" className="text-xs text-slate-600">
              Press Enter to submit. Shift+Enter for new line.
            </p>
          </div>

          {/* Strategy selector */}
          <div className="space-y-1.5">
            <label htmlFor="recall-strategy" className="text-xs font-medium text-slate-400">
              Strategy
            </label>
            <select
              id="recall-strategy"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as RecallStrategy | '')}
              disabled={loading}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 focus:border-emerald-500/60 focus:outline-none transition-colors disabled:opacity-50"
            >
              {STRATEGY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.emoji} {opt.label}
                </option>
              ))}
            </select>
            {strategyMeta && (
              <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${strategyMeta.bgColor} ${strategyMeta.borderColor} ${strategyMeta.color}`}>
                {strategyMeta.emoji} {strategyMeta.label}
              </span>
            )}
          </div>

          {/* Error */}
          {error && <ErrorMessage error={error} onRetry={() => void handleSubmit()} />}

          {/* No graph warning */}
          {!hasGraph && !loadingGraph && (
            <div className="text-xs text-slate-600 flex items-center gap-1.5">
              <span aria-hidden="true">ℹ</span>
              Upload a source first to enable recall.
            </div>
          )}

          {/* Submit */}
          <button
            onClick={() => void handleSubmit()}
            disabled={loading || !query.trim() || !hasGraph}
            className="flex items-center justify-center gap-2 w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-medium rounded-lg transition-colors shadow-md shadow-emerald-900/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400"
            aria-label="Submit recall query"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" label="" />
                <span>Searching memory…</span>
              </>
            ) : (
              <>
                <span aria-hidden="true">▶</span>
                Recall
              </>
            )}
          </button>

          {loading && (
            <p className="text-xs text-slate-500 text-center animate-pulse">
              Traversing knowledge graph…
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function MetaRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-xs text-slate-500">{label}:</span>
      <span>{children}</span>
    </div>
  )
}

function StrategyBadge({ strategy }: { strategy: RecallStrategy | string }) {
  const meta = STRATEGY_META[strategy as RecallStrategy]
  if (!meta) return <span className="text-slate-400 text-sm">{strategy || '—'}</span>
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${meta.bgColor} ${meta.borderColor} ${meta.color}`}>
      {meta.emoji} {meta.label}
    </span>
  )
}
