import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ShieldAlert, X } from "lucide-react";
import { cn } from "../../lib/utils.js";

// Global toast state manager
const listeners = new Set();
let toasts = [];

export const toast = (message, options = {}) => {
  const id = Math.random().toString(36).slice(2);
  const newToast = { id, message, ...options };
  toasts = [...toasts, newToast];
  listeners.forEach((listener) => listener(toasts));

  // Auto-dismiss after 6 seconds unless specified
  if (options.duration !== Infinity) {
    setTimeout(() => {
      dismissToast(id);
    }, options.duration || 6000);
  }
  return id;
};

const dismissToast = (id) => {
  toasts = toasts.filter((t) => t.id !== id);
  listeners.forEach((listener) => listener(toasts));
};

export function Toaster() {
  const [currentToasts, setCurrentToasts] = React.useState(toasts);

  React.useEffect(() => {
    setCurrentToasts(toasts);
    const listener = (newToasts) => setCurrentToasts(newToasts);
    listeners.add(listener);
    return () => listeners.delete(listener);
  }, []);

  return (
    <div className="pointer-events-none fixed bottom-0 right-0 z-50 flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:bottom-4 sm:right-4 sm:w-auto sm:flex-col">
      <AnimatePresence mode="popLayout">
        {currentToasts.map((t) => {
          const isDanger = t.variant === "danger";
          const isWarn = t.variant === "warn";
          
          let cardClasses = "bg-[var(--color-surface-2)] border-[var(--color-line)] text-[var(--color-ink)] shadow-lg";
          let icon = <ShieldAlert className="text-[var(--color-brand)]" size={20} />;
          
          if (isDanger) {
            cardClasses = "bg-[var(--color-danger-bg)] border-[var(--color-danger-line)] text-[var(--color-danger)] shadow-[0_4px_24px_-8px_rgba(255,0,60,0.4)]";
            icon = <AlertTriangle size={20} />;
          } else if (isWarn) {
            cardClasses = "bg-[var(--color-warn-bg)] border-[var(--color-warn-line)] text-[var(--color-warn)] shadow-[0_4px_24px_-8px_rgba(255,183,3,0.3)]";
            icon = <AlertTriangle size={20} />;
          }

          return (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 50, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.95 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className={cn(
                "pointer-events-auto flex w-full items-start gap-3 rounded-[var(--radius-lg)] border p-4 sm:w-[380px]",
                cardClasses
              )}
            >
              <div className="mt-0.5 shrink-0">{icon}</div>
              <div className="flex flex-1 flex-col gap-1">
                {t.title && <div className="text-sm font-bold uppercase tracking-wider">{t.title}</div>}
                <div className="text-sm font-medium leading-relaxed opacity-90">{t.message}</div>
              </div>
              <button
                onClick={() => dismissToast(t.id)}
                className="shrink-0 rounded-md p-1 opacity-70 transition-opacity hover:bg-black/10 hover:opacity-100"
              >
                <X size={16} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
