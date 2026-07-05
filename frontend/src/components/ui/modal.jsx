import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "../../lib/utils.js";

export function Modal({ isOpen, onClose, title, children, className }) {
  // Prevent body scrolling when modal is open
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal Content */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className={cn(
                "pointer-events-auto relative w-full max-w-md overflow-hidden rounded-[var(--radius-xl)] border border-[var(--color-line)] bg-[var(--color-surface)] shadow-[0_16px_48px_-12px_rgba(30,58,138,0.15)]",
                className
              )}
            >
              <div className="flex items-center justify-between border-b border-[var(--color-line)] p-4 bg-[var(--color-surface-2)]">
                <h3 className="text-lg font-bold text-[var(--color-ink)]">{title}</h3>
                <button
                  onClick={onClose}
                  className="rounded-full p-1.5 text-[var(--color-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-ink)] transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="p-6">{children}</div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
