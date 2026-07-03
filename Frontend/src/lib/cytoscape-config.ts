/**
 * Cytoscape.js stylesheet and layout configuration.
 *
 * Spec §7.2 (node stylesheet), §7.3 (edge stylesheet), §7.4 (evidence mode).
 * This file is imported only by GraphCanvas (client-side).
 */

import type { StylesheetStyle, LayoutOptions } from 'cytoscape'

// ── Node colours (spec §7.2) ──────────────────────────────────────────────────
const NODE_COLORS: Record<string, { bg: string; border: string }> = {
  'entity-paper':          { bg: '#10b981', border: '#047857' },
  'entity-author':         { bg: '#14b8a6', border: '#0f766e' },
  'entity-method':         { bg: '#0ea5e9', border: '#0369a1' },
  'entity-dataset':        { bg: '#14b8a6', border: '#0f766e' },
  'entity-benchmark':      { bg: '#f59e0b', border: '#b45309' },
  'entity-experiment':     { bg: '#f97316', border: '#c2410c' },
  'entity-hypothesis':     { bg: '#ec4899', border: '#be185d' },
  'entity-finding':        { bg: '#22c55e', border: '#15803d' },
  'entity-research-note':  { bg: '#84cc16', border: '#4d7c0f' },
  'entity-topic':          { bg: '#64748b', border: '#475569' },
  'entity-unknown':        { bg: '#374151', border: '#1f2937' },
}

// ── Edge colours (spec §7.3) ──────────────────────────────────────────────────
const EDGE_STYLES: Record<string, { color: string; style: 'solid' | 'dashed' | 'dotted'; arrow: string }> = {
  'rel-contradicts':   { color: '#ef4444', style: 'solid',  arrow: 'triangle' },
  'rel-supports':      { color: '#22c55e', style: 'solid',  arrow: 'triangle' },
  'rel-uses':          { color: '#60a5fa', style: 'dashed', arrow: 'triangle' },
  'rel-evaluates':     { color: '#f59e0b', style: 'dotted', arrow: 'triangle' },
  'rel-written-by':    { color: '#a78bfa', style: 'solid',  arrow: 'none'     },
  'rel-references':    { color: '#94a3b8', style: 'dashed', arrow: 'triangle' },
  'rel-derived-from':  { color: '#fb923c', style: 'solid',  arrow: 'triangle' },
  'rel-about':         { color: '#64748b', style: 'dashed', arrow: 'none'     },
}

// ── Node shape map (spec §7.2) ────────────────────────────────────────────────
const NODE_SHAPES: Record<string, string> = {
  'entity-paper':         'roundrectangle',
  'entity-author':        'ellipse',
  'entity-method':        'roundrectangle',
  'entity-dataset':       'roundrectangle',
  'entity-benchmark':     'roundrectangle',
  'entity-experiment':    'roundrectangle',
  'entity-hypothesis':    'diamond',
  'entity-finding':       'roundrectangle',
  'entity-research-note': 'roundrectangle',
  'entity-topic':         'ellipse',
  'entity-unknown':       'ellipse',
}

// ── Build stylesheet ──────────────────────────────────────────────────────────
export function buildCytoscapeStylesheet(): StylesheetStyle[] {
  const styles: StylesheetStyle[] = [
    // ── Base node style ────────────────────────────────────────────────────────
    {
      selector: 'node',
      style: {
        'width': 48,
        'height': 48,
        'background-color': '#475569',
        'border-width': 2,
        'border-color': '#334155',
        'label': 'data(label)',
        'color': '#f1f5f9',
        'font-size': 11,
        'font-family': '"Inter", system-ui, sans-serif',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': 4,
        'text-wrap': 'ellipsis',
        'text-max-width': 80,
        'min-zoomed-font-size': 8,
        'z-index': 10,
      } as Record<string, unknown>,
    },

    // ── Base edge style ────────────────────────────────────────────────────────
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#475569',
        'target-arrow-color': '#475569',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'color': '#94a3b8',
        'font-size': 9,
        'text-opacity': 0,          // hidden by default, shown on hover
        'text-background-color': '#0f172a',
        'text-background-opacity': 0.8,
        'text-background-padding': '2px',
        'z-index': 5,
      } as Record<string, unknown>,
    },

    // ── Edge label shown on hover ──────────────────────────────────────────────
    {
      selector: 'edge:hover',
      style: {
        'text-opacity': 1,
        'width': 3,
      } as Record<string, unknown>,
    },

    // ── Selected node ──────────────────────────────────────────────────────────
    {
      selector: 'node:selected',
      style: {
        'border-width': 3,
        'border-color': '#34d399',
        'z-index': 20,
      } as Record<string, unknown>,
    },

    // ── Selected edge ──────────────────────────────────────────────────────────
    {
      selector: 'edge:selected',
      style: {
        'width': 3,
        'text-opacity': 1,
      } as Record<string, unknown>,
    },

    // ── Unknown type nodes (spec §15 Weakness 5) — smaller, more transparent ──
    {
      selector: '.entity-unknown',
      style: {
        'opacity': 0.45,
        'width': 28,
        'height': 28,
      } as Record<string, unknown>,
    },

    // ── Evidence mode — dimmed non-evidence nodes (spec §7.4) ─────────────────
    {
      selector: '.non-evidence',
      style: {
        'opacity': 0.15,
      } as Record<string, unknown>,
    },

    // ── Evidence mode — highlighted evidence nodes (spec §7.4) ────────────────
    {
      selector: '.evidence-node',
      style: {
        'width': 64,
        'height': 64,
        'border-width': 3,
        'z-index': 30,
      } as Record<string, unknown>,
    },
  ]

  // ── Per-type node styles ───────────────────────────────────────────────────
  for (const [cls, colors] of Object.entries(NODE_COLORS)) {
    styles.push({
      selector: `.${cls}`,
      style: {
        'background-color': colors.bg,
        'border-color':     colors.border,
        'shape':            NODE_SHAPES[cls] ?? 'roundrectangle',
      } as Record<string, unknown>,
    })
  }

  // ── Per-type edge styles ───────────────────────────────────────────────────
  for (const [cls, edgeStyle] of Object.entries(EDGE_STYLES)) {
    styles.push({
      selector: `.${cls}`,
      style: {
        'line-color':           edgeStyle.color,
        'target-arrow-color':   edgeStyle.color,
        'target-arrow-shape':   edgeStyle.arrow,
        'line-style':           edgeStyle.style,
      } as Record<string, unknown>,
    })
  }

  return styles
}

// ── Layout config (spec §7.1) ─────────────────────────────────────────────────
export const LAYOUT_CONFIG = {
  name: 'cose-bilkent' as const,
  quality: 'proof' as const,
  animate: true,
  animationDuration: 800,
  randomize: false,
  nodeDimensionsIncludeLabels: true,
  idealEdgeLength: 120,
  nodeRepulsion: 4500,
  edgeElasticity: 0.45,
  nestingFactor: 0.1,
  gravity: 0.25,
  numIter: 2500,
  tile: true,
  padding: 40,
}

// ── Evidence glow colours per strategy (spec §7.4) ───────────────────────────
export const EVIDENCE_COLORS: Record<string, string> = {
  contradiction: '#ef4444',
  relationship:  '#10b981',
  gap_analysis:  '#f59e0b',
  factual:       '#22c55e',
}

/** Apply evidence glow style to a node element imperatively. */
export function applyEvidenceGlow(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  node: any,
  color: string,
) {
  node.style({
    'border-color':    color,
    'shadow-blur':     20,
    'shadow-color':    color,
    'shadow-opacity':  0.8,
    'shadow-offset-x': 0,
    'shadow-offset-y': 0,
  })
}

/** Remove evidence glow from a node (restore its class-derived border). */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function removeEvidenceGlow(node: any) {
  node.removeStyle()
}

// ── Entity type metadata for legend ──────────────────────────────────────────
export const ENTITY_LEGEND = [
  { cls: 'entity-paper',         label: 'Paper',         color: '#10b981' },
  { cls: 'entity-author',        label: 'Author',        color: '#14b8a6' },
  { cls: 'entity-method',        label: 'Method',        color: '#0ea5e9' },
  { cls: 'entity-dataset',       label: 'Dataset',       color: '#14b8a6' },
  { cls: 'entity-benchmark',     label: 'Benchmark',     color: '#f59e0b' },
  { cls: 'entity-experiment',    label: 'Experiment',    color: '#f97316' },
  { cls: 'entity-hypothesis',    label: 'Hypothesis',    color: '#ec4899' },
  { cls: 'entity-finding',       label: 'Finding',       color: '#22c55e' },
  { cls: 'entity-research-note', label: 'Research Note', color: '#84cc16' },
  { cls: 'entity-topic',         label: 'Topic',         color: '#64748b' },
]
