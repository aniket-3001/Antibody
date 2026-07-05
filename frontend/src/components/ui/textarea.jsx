import * as React from "react"
import { cn } from "../../lib/utils"

const Textarea = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[128px] w-full rounded-[var(--radius-lg)] border-2 border-[var(--color-line)] bg-[var(--color-surface-2)] px-4 py-3 text-base text-[var(--color-ink)] placeholder:text-[#737373] transition-colors focus-visible:outline-none focus-visible:border-[var(--color-brand)] focus-visible:bg-[var(--color-surface)] focus-visible:ring-4 focus-visible:ring-[rgba(30,58,138,0.12)] disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Textarea.displayName = "Textarea"

export { Textarea }
