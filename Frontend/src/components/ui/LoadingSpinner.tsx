'use client'

export function LoadingSpinner({ size = 'md', label = 'Loading...' }: {
  size?: 'sm' | 'md' | 'lg'
  label?: string
}) {
  const sizeClass = { sm: 'w-4 h-4', md: 'w-5 h-5', lg: 'w-8 h-8' }[size]
  return (
    <span className="inline-flex items-center gap-2" role="status" aria-label={label}>
      <svg
        className={`${sizeClass} animate-spin text-emerald-400`}
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      {label && <span className="text-slate-400 text-sm">{label}</span>}
    </span>
  )
}
