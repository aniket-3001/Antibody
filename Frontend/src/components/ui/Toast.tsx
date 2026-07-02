'use client'

import { useEffect, useCallback } from 'react'
import { useAppState, useAppActions } from '@/context/AppStore'
import type { ToastType } from '@/lib/types'

const ICONS: Record<ToastType, string> = {
  success: '✅',
  warning: '⚠',
  error: '❌',
  info: 'ℹ',
}

const BORDER: Record<ToastType, string> = {
  success: 'border-green-500/40 bg-green-500/10',
  warning: 'border-amber-500/40 bg-amber-500/10',
  error:   'border-red-500/40   bg-red-500/10',
  info:    'border-blue-500/40  bg-blue-500/10',
}

const TEXT: Record<ToastType, string> = {
  success: 'text-green-300',
  warning: 'text-amber-300',
  error:   'text-red-300',
  info:    'text-blue-300',
}

function ToastItem({ id, type, message }: { id: string; type: ToastType; message: string }) {
  const { removeToast } = useAppActions()

  const dismiss = useCallback(() => removeToast(id), [id, removeToast])

  useEffect(() => {
    const timer = setTimeout(dismiss, 4000)
    return () => clearTimeout(timer)
  }, [dismiss])

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-start gap-2.5 px-3.5 py-2.5 rounded-lg border text-sm
        shadow-lg animate-[slideUp_0.2s_ease-out] ${BORDER[type]}`}
    >
      <span aria-hidden="true" className="mt-0.5 text-base">{ICONS[type]}</span>
      <span className={TEXT[type]}>{message}</span>
      <button
        onClick={dismiss}
        className="ml-auto text-slate-500 hover:text-slate-300 transition-colors pl-2 text-base leading-none"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  )
}

/** Toast container — fixed bottom-right, stacks upward. */
export function ToastContainer() {
  const { toasts } = useAppState()

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col-reverse gap-2 max-w-sm w-full"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} {...t} />
      ))}
    </div>
  )
}
