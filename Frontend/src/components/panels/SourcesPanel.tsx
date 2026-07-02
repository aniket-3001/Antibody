'use client'

import { useState, useCallback } from 'react'
import { useAppState, useAppActions } from '@/context/AppStore'
import { useRefresh } from '@/hooks/useRefresh'
import { api } from '@/lib/api'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import type { SourceItem } from '@/lib/types'

/**
 * SourcesPanel — lists all ingested sources with delete action. Spec §4.5 / §11.6.
 */
export function SourcesPanel() {
  const { sources, loadingSources } = useAppState()
  const { addToast } = useAppActions()
  const { refreshAll } = useRefresh()

  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [confirmId, setConfirmId] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<Error | null>(null)

  const handleDeleteConfirm = useCallback(
    async (sourceId: string) => {
      setDeletingId(sourceId)
      setConfirmId(null)
      setDeleteError(null)
      try {
        await api.forget({ source_id: sourceId })
        addToast('success', 'Source removed from memory.')
        await refreshAll()
      } catch (err) {
        setDeleteError(err as Error)
        addToast('error', 'Failed to delete source.')
      } finally {
        setDeletingId(null)
      }
    },
    [addToast, refreshAll],
  )

  // Empty state
  if (!loadingSources && sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6 gap-3">
        <span className="text-3xl" aria-hidden="true">📭</span>
        <p className="text-sm font-medium text-slate-400">No sources in memory yet.</p>
        <p className="text-xs text-slate-600">
          Upload your first document in the{' '}
          <span className="text-indigo-400">Upload</span> tab.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header count */}
      <div className="flex items-center justify-between px-4 py-2 flex-none">
        <span className="text-xs text-slate-500">
          {loadingSources ? 'Loading…' : `${sources.length} source${sources.length !== 1 ? 's' : ''}`}
        </span>
      </div>

      {/* Error */}
      {deleteError && (
        <div className="px-4 pb-2">
          <ErrorMessage error={deleteError} compact />
        </div>
      )}

      {/* Source list */}
      <div className="flex-1 overflow-y-auto panel-scroll px-4 pb-4 space-y-2">
        {loadingSources && sources.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner label="Loading sources…" />
          </div>
        ) : (
          sources.map((source) => (
            <SourceCard
              key={source.source_id}
              source={source}
              isDeleting={deletingId === source.source_id}
              isConfirming={confirmId === source.source_id}
              onDeleteClick={() => setConfirmId(source.source_id)}
              onConfirm={() => void handleDeleteConfirm(source.source_id)}
              onCancel={() => setConfirmId(null)}
            />
          ))
        )}
      </div>
    </div>
  )
}

interface SourceCardProps {
  source: SourceItem
  isDeleting: boolean
  isConfirming: boolean
  onDeleteClick: () => void
  onConfirm: () => void
  onCancel: () => void
}

function SourceCard({
  source,
  isDeleting,
  isConfirming,
  onDeleteClick,
  onConfirm,
  onCancel,
}: SourceCardProps) {
  let date = '—'
  if (source.ingested_at) {
    const d = new Date(source.ingested_at)
    if (!isNaN(d.getTime())) {
      const year = d.getFullYear()
      const month = d.toLocaleString('en-US', { month: 'short' })
      const day = d.getDate()
      const hours = String(d.getHours()).padStart(2, '0')
      const minutes = String(d.getMinutes()).padStart(2, '0')
      date = `${month} ${day}, ${year} ${hours}:${minutes}`
    }
  }

  return (
    <div
      className={`rounded-lg border border-slate-700/60 bg-slate-800/40 p-3 transition-all ${
        isDeleting ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-start gap-2">
        {/* Type icon */}
        <span className="text-base flex-none mt-0.5" aria-hidden="true">
          {SOURCE_ICON[source.source_type] ?? '📄'}
        </span>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200 truncate" title={source.title}>
            {source.title || 'Untitled'}
          </p>
          <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
            <span className="capitalize">{source.source_type}</span>
            <span aria-hidden="true">·</span>
            <time dateTime={source.ingested_at}>{date}</time>
          </div>
          <p className="text-xs text-slate-600 font-mono truncate mt-1">
            {source.source_id}
          </p>
        </div>

        {/* Delete action */}
        <div className="flex-none">
          {isDeleting ? (
            <LoadingSpinner size="sm" label="" />
          ) : isConfirming ? (
            <div className="flex gap-1">
              <button
                onClick={onConfirm}
                className="text-xs px-2 py-1 bg-red-600 hover:bg-red-500 text-white rounded transition-colors"
                aria-label="Confirm deletion"
              >
                Delete
              </button>
              <button
                onClick={onCancel}
                className="text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition-colors"
                aria-label="Cancel deletion"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={onDeleteClick}
              className="text-xs text-slate-600 hover:text-red-400 transition-colors p-1.5 rounded hover:bg-red-500/10"
              aria-label={`Delete source: ${source.title || source.source_id}`}
              title="Delete source"
            >
              🗑
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

const SOURCE_ICON: Record<string, string> = {
  pdf:           '📕',
  text:          '📄',
  markdown:      '📝',
  url:           '🔗',
  paper:         '📕',
  experiment:    '🧪',
  research_note: '📓',
}
