/**
 * MemoryOS Frontend TypeScript types.
 *
 * Every type here maps 1:1 to a schema defined in Docs/BACKEND_API_SPEC.md.
 * If the spec changes, update this file first.
 */

// ── Health ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: 'ok' | 'degraded'
  memory_core_mode: string
  provider?: string
  version: string
  // Only present when status = 'degraded'
  error?: { code: string; message: string }
}

// ── Stats ───────────────────────────────────────────────────────────────────

export interface StatsResponse {
  total_sources: number
  active_hypotheses: number
  entity_counts: Record<string, number> | null
  last_ingest_at: string | null
}

// ── Sources ─────────────────────────────────────────────────────────────────

export interface SourceItem {
  source_id: string
  title: string
  source_type: string
  ingested_at: string
}

export interface SourcesResponse {
  sources: SourceItem[]
  total: number
}

// ── Cytoscape graph ──────────────────────────────────────────────────────────

export interface CytoscapeNodeData {
  id: string          // "node-{uuid}"
  label: string
  type: string        // EntityType string e.g. "Paper", "Hypothesis"
  source_ids: string[]
  attributes: Record<string, unknown>
}

export interface CytoscapeEdgeData {
  id: string          // "edge-{n}"
  source: string      // "node-{uuid}"
  target: string      // "node-{uuid}"
  label: string       // relationship string
  relationship: string
}

export type CytoscapeElementData = CytoscapeNodeData | CytoscapeEdgeData

export function isNodeData(data: CytoscapeElementData): data is CytoscapeNodeData {
  return 'type' in data && !('source' in data && 'target' in data)
}

export function isEdgeData(data: CytoscapeElementData): data is CytoscapeEdgeData {
  return 'source' in data && 'target' in data && 'relationship' in data
}

export interface CytoscapeElement {
  data: CytoscapeElementData
  classes: string
}

export interface CytoscapeGraph {
  elements: CytoscapeElement[]
  node_count: number
  edge_count: number
}

// ── Remember / Improve ───────────────────────────────────────────────────────

export type ContentType = 'pdf' | 'text' | 'markdown' | 'url'
export type MemoryOperation = 'remember' | 'improve'
export type IngestStatus = 'created' | 'skipped_duplicate' | 'degraded'

export interface IngestResponse {
  source_id: string
  status: IngestStatus
  nodes_created: number
  edges_created: number
  duration_ms: number
  warnings: string[]
}

// ── Recall ───────────────────────────────────────────────────────────────────

export type RecallStrategy = 'relationship' | 'contradiction' | 'gap_analysis' | 'factual'

export interface RecallRequest {
  query: string
  strategy?: RecallStrategy | null
}

export interface RecallResponse {
  query: string
  answer: string
  strategy_used: string
  evidence_graph: CytoscapeGraph | null
  degraded: boolean
  duration_ms: number
}

// ── Forget ───────────────────────────────────────────────────────────────────

export interface ForgetRequest {
  source_id: string
}

export interface ForgetResponse {
  source_id: string
  deleted: boolean
  orphans_pruned: number
}

// ── Error envelope ────────────────────────────────────────────────────────────

export interface ApiErrorDetail {
  code: string
  message: string
  detail: string | null
}

export interface ApiErrorResponse {
  error: ApiErrorDetail
}

export class ApiError extends Error {
  public readonly status: number
  public readonly code: string
  public readonly detail: string | null

  constructor(status: number, detail: ApiErrorDetail) {
    super(detail.message)
    this.status = status
    this.code = detail.code
    this.detail = detail.detail
    this.name = 'ApiError'
  }
}

// ── UI-only types ─────────────────────────────────────────────────────────────

export type ActiveTab = 'recall' | 'sources' | 'upload'

export type ToastType = 'success' | 'warning' | 'error' | 'info'

export interface ToastItem {
  id: string
  type: ToastType
  message: string
  duration?: number   // ms — default 4000
}

// Strategy display metadata
export interface StrategyMeta {
  label: string
  color: string       // Tailwind text-color class
  bgColor: string     // Tailwind bg-color class
  borderColor: string // Tailwind border-color class
  cytoscapeColor: string // Hex for Cytoscape evidence glow
  emoji: string
}

export const STRATEGY_META: Record<RecallStrategy, StrategyMeta> = {
  relationship: {
    label: 'Relationship',
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/20',
    borderColor: 'border-indigo-500',
    cytoscapeColor: '#6366f1',
    emoji: '🔵',
  },
  contradiction: {
    label: 'Contradiction',
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    borderColor: 'border-red-500',
    cytoscapeColor: '#ef4444',
    emoji: '🔴',
  },
  gap_analysis: {
    label: 'Gap Analysis',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
    borderColor: 'border-amber-500',
    cytoscapeColor: '#f59e0b',
    emoji: '🟡',
  },
  factual: {
    label: 'Factual',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500',
    cytoscapeColor: '#22c55e',
    emoji: '🟢',
  },
}
