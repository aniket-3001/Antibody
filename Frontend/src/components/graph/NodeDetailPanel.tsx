'use client'

import { useAppState, useAppActions } from '@/context/AppStore'
import type { CytoscapeNodeData } from '@/lib/types'
import { ENTITY_LEGEND } from '@/lib/cytoscape-config'

/**
 * NodeDetailPanel — slides into the interaction panel area when a graph node
 * is clicked. Shows label, type, attributes, and source connections.
 * Spec §6.2.
 */
export function NodeDetailPanel() {
  const { selectedNode, graph } = useAppState()
  const { setSelectedNode } = useAppActions()

  if (!selectedNode) return null

  const node = selectedNode as CytoscapeNodeData

  // Find connected edges from the cached graph
  const edges = (graph?.elements ?? []).filter((el) => {
    if (!('source' in el.data)) return false
    return el.data.source === node.id || el.data.target === node.id
  })

  // Resolve node labels from graph data
  const nodeMap = new Map<string, string>()
  for (const el of graph?.elements ?? []) {
    if ('label' in el.data && !('source' in el.data)) {
      nodeMap.set(el.data.id, (el.data as CytoscapeNodeData).label)
    }
  }

  // Find the legend color for this type
  const entityClass = `entity-${node.type.toLowerCase().replace(/\s+/g, '-').replace(/_/g, '-')}`
  const legendEntry = ENTITY_LEGEND.find((e) => e.cls === entityClass)
  const typeColor = legendEntry?.color ?? '#64748b'

  const attributes = Object.entries(node.attributes ?? {}).filter(
    ([, v]) => v !== null && v !== undefined && v !== '',
  )

  return (
    <div className="flex flex-col h-full animate-[fadeIn_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-700/60 flex-none">
        <button
          onClick={() => setSelectedNode(null)}
          className="text-slate-500 hover:text-slate-300 transition-colors text-sm"
          aria-label="Back to panel"
        >
          ← Back
        </button>
      </div>

      <div className="flex-1 overflow-y-auto panel-scroll px-4 py-4 space-y-5">
        {/* Node identity */}
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className="w-3 h-3 rounded-sm flex-none"
              style={{ backgroundColor: typeColor }}
              aria-hidden="true"
            />
            <span className="text-xs font-medium px-2 py-0.5 rounded-full text-slate-400 bg-slate-800 border border-slate-700">
              {node.type}
            </span>
          </div>
          <h3 className="text-slate-100 text-base font-semibold leading-tight">{node.label}</h3>
        </div>

        {/* Attributes */}
        {attributes.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Attributes</h4>
            <dl className="space-y-1">
              {attributes.map(([key, val]) => (
                <div key={key} className="flex gap-2 text-sm">
                  <dt className="text-slate-500 flex-none capitalize">{key}:</dt>
                  <dd className="text-slate-300 break-words">{String(val)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {/* Connections */}
        {edges.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Connections ({edges.length})
            </h4>
            <ul className="space-y-1.5">
              {edges.map((el) => {
                if (!('source' in el.data)) return null
                const edgeData = el.data as { source: string; target: string; relationship: string; id: string }
                const isSource = edgeData.source === node.id
                const otherId  = isSource ? edgeData.target : edgeData.source
                const otherLabel = nodeMap.get(otherId) ?? otherId
                return (
                  <li key={edgeData.id} className="flex items-start gap-2 text-xs">
                    <span className="text-slate-600 mt-0.5">{isSource ? '→' : '←'}</span>
                    <span className="text-indigo-400 font-medium">{edgeData.relationship}</span>
                    <span className="text-slate-400 break-words">{otherLabel}</span>
                  </li>
                )
              })}
            </ul>
          </div>
        )}

        {/* Source documents */}
        {node.source_ids?.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Sources</h4>
            <ul className="space-y-1">
              {node.source_ids.map((sid) => (
                <li key={sid} className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="text-slate-600" aria-hidden="true">📎</span>
                  <span className="font-mono text-slate-500 truncate">{sid}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
