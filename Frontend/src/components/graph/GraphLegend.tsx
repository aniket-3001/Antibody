'use client'

import { useState } from 'react'
import { ENTITY_LEGEND } from '@/lib/cytoscape-config'

/**
 * GraphLegend — bottom-left corner entity type legend.
 * Spec §7.6: collapsible, click-to-filter (filter in Phase 5).
 */
export function GraphLegend() {
  const [expanded, setExpanded] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const visible = expanded ? ENTITY_LEGEND : ENTITY_LEGEND.slice(0, 5)

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="absolute bottom-4 right-4 z-10 w-8 h-8 flex items-center justify-center bg-slate-900/80 border border-slate-700/60 rounded-lg text-slate-400 hover:text-slate-200 text-xs backdrop-blur-sm"
        aria-label="Show legend"
        title="Show legend"
      >
        ≡
      </button>
    )
  }

  return (
    <div
      className="absolute bottom-4 right-4 z-10 bg-slate-900/85 border border-slate-700/60 rounded-lg px-3 py-2.5 backdrop-blur-sm shadow-lg max-w-[200px]"
      role="note"
      aria-label="Graph node type legend"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2 gap-2">
        <span className="text-xs font-medium text-slate-400">Legend</span>
        <button
          onClick={() => setCollapsed(true)}
          className="text-slate-600 hover:text-slate-400 transition-colors text-xs leading-none"
          aria-label="Hide legend"
        >
          ≡
        </button>
      </div>

      {/* Items */}
      <div className="flex flex-col gap-1.5">
        {visible.map((item) => (
          <div key={item.cls} className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-sm flex-none"
              style={{ backgroundColor: item.color }}
              aria-hidden="true"
            />
            <span className="text-xs text-slate-400">{item.label}</span>
          </div>
        ))}

        {!expanded && ENTITY_LEGEND.length > 5 && (
          <button
            onClick={() => setExpanded(true)}
            className="text-xs text-slate-600 hover:text-slate-400 transition-colors text-left mt-0.5"
            aria-label={`Show ${ENTITY_LEGEND.length - 5} more entity types`}
          >
            + {ENTITY_LEGEND.length - 5} more
          </button>
        )}
        {expanded && (
          <button
            onClick={() => setExpanded(false)}
            className="text-xs text-slate-600 hover:text-slate-400 transition-colors text-left mt-0.5"
          >
            show less
          </button>
        )}
      </div>
    </div>
  )
}
