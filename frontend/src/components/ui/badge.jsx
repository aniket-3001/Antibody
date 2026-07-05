import * as React from "react"
import { cn } from "../../lib/utils"

function Badge({ className, variant = "default", ...props }) {
  const variants = {
    default: "border-transparent bg-[var(--color-brand)] text-white hover:opacity-80",
    secondary: "border-transparent bg-[var(--color-surface-2)] text-[var(--color-ink)] hover:opacity-80",
    danger: "border-transparent bg-[var(--color-danger-bg)] text-[var(--color-danger)]",
    warn: "border-transparent bg-[var(--color-warn-bg)] text-[var(--color-warn)]",
    safe: "border-transparent bg-[var(--color-safe-bg)] text-[var(--color-safe)]",
    calm: "border-transparent bg-[var(--color-calm-bg)] text-[var(--color-calm)]",
    outline: "text-[var(--color-ink)] border-[var(--color-line)]",
  }

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
