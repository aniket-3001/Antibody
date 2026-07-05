import * as React from "react"
import { cn } from "../../lib/utils"

const Button = React.forwardRef(({ className, variant = "default", size = "default", ...props }, ref) => {
  const variants = {
    default: "bg-[var(--color-brand)] text-[var(--color-surface)] hover:bg-[var(--color-brand-2)] shadow-[0_8px_18px_-8px_rgba(0,255,65,0.7)]",
    secondary: "bg-[var(--color-surface-2)] text-[var(--color-ink)] hover:bg-[var(--color-line)]",
    ghost: "hover:bg-[var(--color-surface-2)] text-[var(--color-muted)] hover:text-[var(--color-ink)]",
    destructive: "bg-[var(--color-danger)] text-white hover:opacity-90",
  }
  
  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-12 px-8 py-3 text-base",
    icon: "h-10 w-10",
  }

  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-bold ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }
