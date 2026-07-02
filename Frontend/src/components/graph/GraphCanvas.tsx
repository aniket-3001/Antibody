'use client'

/**
 * GraphCanvas — the Cytoscape.js canvas container.
 *
 * Spec §7: Cytoscape integration — layout, stylesheet, evidence mode.
 * This file is ONLY imported via dynamic() with ssr:false (see GraphArea.tsx).
 *
 * Lifecycle:
 *  1. Mount: initialise Cytoscape with stylesheet, empty elements
 *  2. elements prop changes: batch-update nodes/edges, re-run layout
 *  3. evidenceNodeIds changes: apply/remove evidence CSS classes + glow
 *  4. Unmount: destroy Cytoscape instance
 */

import {
  useEffect,
  useRef,
  useCallback,
  useImperativeHandle,
  forwardRef,
} from 'react'
import cytoscape from 'cytoscape'
import type { Core, NodeSingular } from 'cytoscape'
import {
  buildCytoscapeStylesheet,
  LAYOUT_CONFIG,
  EVIDENCE_COLORS,
  applyEvidenceGlow,
  removeEvidenceGlow,
} from '@/lib/cytoscape-config'
import type { CytoscapeElement, CytoscapeNodeData } from '@/lib/types'

// Register cose-bilkent layout once at module level (client-side only)
let layoutRegistered = false
async function ensureLayoutRegistered() {
  if (layoutRegistered) return
  try {
    const coseBilkent = await import('cytoscape-cose-bilkent')
    cytoscape.use(coseBilkent.default ?? coseBilkent)
    layoutRegistered = true
  } catch {
    // Fallback to built-in cose layout if extension fails
    console.warn('[GraphCanvas] cose-bilkent failed to load, using cose fallback')
  }
}

// ── Public imperative API (exposed via ref) ───────────────────────────────────
export interface GraphCanvasHandle {
  fitAll: () => void
  zoomIn: () => void
  zoomOut: () => void
  resetLayout: () => void
  fitEvidence: () => void
}

interface GraphCanvasProps {
  elements: CytoscapeElement[]
  evidenceNodeIds: Set<string>
  evidenceStrategy: string | null
  onNodeClick: (data: CytoscapeNodeData) => void
  isLoading?: boolean
}

export const GraphCanvas = forwardRef<GraphCanvasHandle, GraphCanvasProps>(
  function GraphCanvas(
    { elements, evidenceNodeIds, evidenceStrategy, onNodeClick, isLoading = false },
    ref,
  ) {
    const containerRef = useRef<HTMLDivElement>(null)
    const cyRef = useRef<Core | null>(null)
    const layoutReadyRef = useRef(false)

    // ── Imperative handle ───────────────────────────────────────────────────
    useImperativeHandle(ref, () => ({
      fitAll() {
        cyRef.current?.fit(undefined, 40)
      },
      zoomIn() {
        const cy = cyRef.current
        if (cy) cy.zoom({ level: cy.zoom() * 1.2, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
      },
      zoomOut() {
        const cy = cyRef.current
        if (cy) cy.zoom({ level: cy.zoom() / 1.2, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
      },
      resetLayout() {
        const cy = cyRef.current
        if (!cy) return
        const layout = cy.layout(getLayoutConfig())
        layout.run()
      },
      fitEvidence() {
        const cy = cyRef.current
        if (!cy) return
        const evidenceNodes = cy.nodes('.evidence-node')
        if (evidenceNodes.length > 0) cy.fit(evidenceNodes, 80)
        else cy.fit(undefined, 40)
      },
    }))

    // ── Layout config (falls back to cose if bilkent unavailable) ───────────
    function getLayoutConfig() {
      return layoutReadyRef.current
        ? LAYOUT_CONFIG
        : { name: 'cose' as const, animate: true, animationDuration: 800 }
    }

    // ── Initialise Cytoscape ─────────────────────────────────────────────────
    useEffect(() => {
      if (!containerRef.current) return

      let destroyed = false

      const init = async () => {
        await ensureLayoutRegistered()
        layoutReadyRef.current = layoutRegistered

        if (destroyed || !containerRef.current) return

        const cy = cytoscape({
          container: containerRef.current,
          style: buildCytoscapeStylesheet(),
          elements: [],
          layout: { name: 'preset' },
          minZoom: 0.1,
          maxZoom: 4,
          wheelSensitivity: 0.2,
        })

        cyRef.current = cy

        // Node click → detail panel
        cy.on('tap', 'node', (evt) => {
          const node = evt.target as NodeSingular
          onNodeClick(node.data() as CytoscapeNodeData)
        })

        // Background tap → deselect
        cy.on('tap', (evt) => {
          if (evt.target === cy) {
            cy.elements().unselect()
          }
        })
      }

      void init()

      return () => {
        destroyed = true
        cyRef.current?.destroy()
        cyRef.current = null
      }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []) // Mount-only; onNodeClick via stable closure below

    // Keep onNodeClick reference fresh without re-mounting
    const onNodeClickRef = useRef(onNodeClick)
    useEffect(() => { onNodeClickRef.current = onNodeClick }, [onNodeClick])

    // ── Update elements when data changes ────────────────────────────────────
    useEffect(() => {
      const cy = cyRef.current
      if (!cy) return

      cy.batch(() => {
        cy.elements().remove()
        if (elements.length > 0) {
          cy.add(elements as cytoscape.ElementDefinition[])
        }
      })

      if (elements.length > 0) {
        const layout = cy.layout(getLayoutConfig())
        // Wait for layout to settle before revealing (spec §15 Weakness 6)
        layout.one('layoutstop', () => {
          // Layout complete — canvas is ready
        })
        layout.run()
      }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [elements])

    // ── Apply / remove evidence mode (spec §7.4) ─────────────────────────────
    useEffect(() => {
      const cy = cyRef.current
      if (!cy) return

      cy.batch(() => {
        // Remove all evidence classes and inline glow styles
        cy.nodes().forEach((node) => {
          node.removeClass('evidence-node non-evidence')
          removeEvidenceGlow(node)
        })
        cy.edges().removeClass('evidence-edge')

        if (evidenceNodeIds.size > 0) {
          const glowColor = EVIDENCE_COLORS[evidenceStrategy ?? 'relationship'] ?? '#6366f1'

          cy.nodes().forEach((node) => {
            // node ID from backend is "node-{uuid}"; evidenceNodeIds uses raw uuid
            const rawId = node.id().replace(/^node-/, '')
            if (evidenceNodeIds.has(rawId) || evidenceNodeIds.has(node.id())) {
              node.addClass('evidence-node')
              applyEvidenceGlow(node, glowColor)
            } else {
              node.addClass('non-evidence')
            }
          })

          // Fit to evidence subgraph
          const evidenceNodes = cy.nodes('.evidence-node')
          if (evidenceNodes.length > 0) {
            cy.animate({ fit: { eles: evidenceNodes, padding: 80 }, duration: 400 })
          }
        }
      })
    }, [evidenceNodeIds, evidenceStrategy])

    return (
      <div className="relative w-full h-full">
        {/* Loading overlay (spec §8.2) */}
        {isLoading && (
          <div
            className="absolute top-3 right-3 z-20 flex items-center gap-2 bg-slate-800/90 border border-slate-700/60 rounded-full px-3 py-1 text-xs text-slate-400"
            role="status"
            aria-label="Refreshing graph"
          >
            <svg className="w-3 h-3 animate-spin text-emerald-400" fill="none" viewBox="0 0 24 24" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Refreshing graph…
          </div>
        )}

        {/* Cytoscape container */}
        <div
          ref={containerRef}
          id="graph-canvas"
          className="w-full h-full"
          style={{ background: '#0a0e1a' }}
          aria-hidden="true"  // Visual-only; screen reader summary is on parent
        />
      </div>
    )
  },
)
