'use client'

/**
 * Health dot — top-right corner status indicator.
 * Green = ok, Amber (pulsing) = degraded/unknown, Red = health call failed.
 */
export function HealthDot({
  status,
}: {
  status: 'ok' | 'degraded' | 'unknown' | 'error'
}) {
  const config = {
    ok:       { color: 'bg-green-500',  pulse: false, label: 'Backend healthy' },
    degraded: { color: 'bg-amber-500',  pulse: true,  label: 'Backend degraded' },
    unknown:  { color: 'bg-slate-500',  pulse: true,  label: 'Checking backend…' },
    error:    { color: 'bg-red-500',    pulse: false,  label: 'Backend unreachable' },
  }[status]

  return (
    <span
      className="relative flex items-center gap-1.5"
      title={config.label}
      aria-label={config.label}
    >
      <span className="relative flex h-2.5 w-2.5">
        {config.pulse && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.color} opacity-60`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${config.color}`} />
      </span>
      <span className="text-xs text-slate-400 hidden sm:inline">{config.label}</span>
    </span>
  )
}
