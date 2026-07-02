'use client'

/**
 * Fake progress bar for long-running ingest operations.
 *
 * Spec §4.4: fills to 80% over 30s then holds, snaps to 100% on completion.
 * The `complete` prop triggers the 100% snap.
 */
export function ProgressBar({ complete = false }: { complete?: boolean }) {
  return (
    <div
      className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={complete ? 100 : undefined}
      aria-label="Ingest progress"
    >
      <div
        className={
          complete
            ? 'h-full bg-emerald-500 w-full transition-all duration-300 ease-out'
            : 'h-full bg-emerald-500 progress-animate'
        }
      />
    </div>
  )
}
