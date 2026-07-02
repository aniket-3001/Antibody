'use client'

import type { ApiError } from '@/lib/types'

const CODE_MESSAGES: Record<string, string> = {
  EXTRACTION_FAILED:
    "Graph extraction failed. The LLM couldn't process this document. Try a different format.",
  PROVIDER_ERROR:
    'Memory provider unavailable. Check your API key and backend connectivity.',
  RECALL_FAILED:
    "Recall failed. Memory provider couldn't complete the search.",
  CONFIGURATION_ERROR:
    'Backend is misconfigured. Check your .env file.',
  CAPABILITY_UNAVAILABLE:
    'This capability is not available in the current configuration.',
  SOURCE_NOT_FOUND:
    'Source not found — it may have already been deleted.',
  INTERNAL_ERROR:
    'An unexpected error occurred. Check the backend logs.',
  NETWORK_ERROR:
    'Cannot reach MemoryOS server. Is the backend running on port 8000?',
}

interface ErrorMessageProps {
  error: Error | ApiError | null | undefined
  onRetry?: () => void
  compact?: boolean
}

export function ErrorMessage({ error, onRetry, compact = false }: ErrorMessageProps) {
  if (!error) return null

  const apiErr = error as ApiError
  const message =
    (apiErr.code && CODE_MESSAGES[apiErr.code]) ?? error.message ?? 'An error occurred.'

  if (compact) {
    return (
      <p className="text-red-400 text-sm flex items-start gap-1.5">
        <span aria-hidden="true">⚠</span>
        <span>{message}</span>
      </p>
    )
  }

  return (
    <div
      className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 space-y-2"
      role="alert"
    >
      <p className="text-red-300 text-sm font-medium flex items-center gap-1.5">
        <span aria-hidden="true">⚠</span> {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs text-red-400 underline hover:text-red-300 transition-colors"
        >
          Try again
        </button>
      )}
    </div>
  )
}
