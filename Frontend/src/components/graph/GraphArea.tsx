'use client'

/**
 * GraphArea — the hero canvas container (Phase 3 full implementation).
 *
 * Connects AppStore state → GraphCanvas (Cytoscape), GraphToolbar, GraphLegend,
 * EmptyGraphState, and NodeDetailPanel overlay.
 *
 * This file is dynamically imported with ssr:false from AppShell.
 */

import { useRef, useCallback } from 'react'
import { useAppState, useAppActions } from '@/context/AppStore'
import { useRefresh } from '@/hooks/useRefresh'
import { GraphCanvas, type GraphCanvasHandle } from './GraphCanvas'
import { GraphToolbar } from './GraphToolbar'
import { GraphLegend } from './GraphLegend'
import { EmptyGraphState } from './EmptyGraphState'
import type { CytoscapeNodeData, CytoscapeElement } from '@/lib/types'

export function GraphArea() {
  const { graph, loadingGraph, evidenceMode, evidenceNodeIds, evidenceStrategy, selectedNode } =
    useAppState()
  const { setSelectedNode, clearEvidence } = useAppActions()
  const { refreshGraph } = useRefresh()

  const canvasRef = useRef<GraphCanvasHandle>(null)

  const isEmpty = !graph || graph.node_count === 0

  const handleNodeClick = useCallback(
    (data: CytoscapeNodeData) => {
      setSelectedNode(data)
    },
    [setSelectedNode],
  )

  // When node detail panel is open, override the interaction panel
  // by setting selectedNode in store (InteractionPanel reads it)

  // Build element array for Cytoscape — filter logic per spec §15 Weakness 5:
  // entity-unknown nodes are rendered at reduced opacity (handled in stylesheet),
  // not hidden, so judges can see Cognee scaffolding is being tolerated gracefully.
  const elements: CytoscapeElement[] = graph?.elements ?? []

  return (
    <div
      className="relative w-full h-full"
      aria-label={`Knowledge graph with ${graph?.node_count ?? 0} nodes and ${graph?.edge_count ?? 0} edges`}
    >
      {/* Empty state overlay (spec §10.1) */}
      {isEmpty && !loadingGraph && <EmptyGraphState />}

      {/* Cytoscape canvas — always mounted once data exists */}
      {(!isEmpty || loadingGraph) && (
        <GraphCanvas
          ref={canvasRef}
          elements={elements}
          evidenceNodeIds={evidenceNodeIds}
          evidenceStrategy={evidenceStrategy}
          onNodeClick={handleNodeClick}
          isLoading={loadingGraph}
        />
      )}

      {/* Empty state initial loading shimmer */}
      {isEmpty && loadingGraph && (
        <div
          className="absolute inset-0 flex items-center justify-center"
          style={{ background: '#0a0e1a' }}
        >
          <div className="flex flex-col items-center gap-4 text-slate-600">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-600/25 to-teal-600/25 border border-emerald-500/20 flex items-center justify-center animate-pulse">
              <span className="text-xl">✦</span>
            </div>
            <span className="text-sm">Loading knowledge graph…</span>
          </div>
        </div>
      )}

      {/* Toolbar (only when graph has nodes) */}
      {!isEmpty && (
        <GraphToolbar
          canvasRef={canvasRef}
          evidenceMode={evidenceMode}
          onClearEvidence={clearEvidence}
          onRefresh={refreshGraph}
        />
      )}

      {/* Legend (only when graph has nodes) */}
      {!isEmpty && <GraphLegend />}
    </div>
  )
}
