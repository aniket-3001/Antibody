/**
 * MemoryOS API client.
 *
 * Every public function maps to one endpoint in Docs/BACKEND_API_SPEC.md.
 * No other file in Frontend/ should construct fetch() calls directly.
 */

import type {
  HealthResponse,
  StatsResponse,
  SourcesResponse,
  CytoscapeGraph,
  IngestResponse,
  RecallRequest,
  RecallResponse,
  ForgetRequest,
  ForgetResponse,
  ApiErrorResponse,
} from './types'
import { ApiError } from './types'

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'

// ── Core request helper ───────────────────────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      // Include credentials if API ever requires cookies
      credentials: 'same-origin',
    })
  } catch (networkErr) {
    // Network-level failure (server not running, CORS failure, etc.)
    throw new ApiError(0, {
      code: 'NETWORK_ERROR',
      message: 'Cannot reach MemoryOS server. Is the backend running on port 8000?',
      detail: String(networkErr),
    })
  }

  if (!res.ok) {
    let errBody: ApiErrorResponse
    try {
      errBody = (await res.json()) as ApiErrorResponse
    } catch {
      throw new ApiError(res.status, {
        code: 'UNKNOWN_ERROR',
        message: `HTTP ${res.status}: ${res.statusText}`,
        detail: null,
      })
    }
    throw new ApiError(res.status, errBody.error)
  }

  return res.json() as Promise<T>
}

// ── Public API surface ─────────────────────────────────────────────────────────

export const api = {
  /**
   * GET /api/v1/health
   * Liveness check. Never throws — returns a degraded response on failure.
   */
  async health(): Promise<HealthResponse> {
    return request<HealthResponse>('/api/v1/health')
  },

  /**
   * GET /api/v1/stats
   * Summary counts: total_sources, entity_counts, last_ingest_at.
   */
  async stats(): Promise<StatsResponse> {
    return request<StatsResponse>('/api/v1/stats')
  },

  /**
   * GET /api/v1/sources
   * List all ingested sources.
   */
  async sources(): Promise<SourcesResponse> {
    return request<SourcesResponse>('/api/v1/sources')
  },

  /**
   * GET /api/v1/graph
   * Full knowledge graph in Cytoscape.js elements format.
   */
  async graph(): Promise<CytoscapeGraph> {
    return request<CytoscapeGraph>('/api/v1/graph')
  },

  /**
   * POST /api/v1/recall
   * Answer a natural-language question using graph traversal.
   */
  async recall(body: RecallRequest): Promise<RecallResponse> {
    return request<RecallResponse>('/api/v1/recall', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  },

  /**
   * POST /api/v1/remember
   * Ingest a new source (remember() lifecycle).
   * Uses multipart/form-data — caller builds the FormData.
   */
  async remember(formData: FormData): Promise<IngestResponse> {
    // Do NOT set Content-Type header — browser sets multipart boundary automatically
    return request<IngestResponse>('/api/v1/remember', {
      method: 'POST',
      body: formData,
    })
  },

  /**
   * POST /api/v1/improve
   * Expand existing memory with a new source (improve() lifecycle).
   */
  async improve(formData: FormData): Promise<IngestResponse> {
    return request<IngestResponse>('/api/v1/improve', {
      method: 'POST',
      body: formData,
    })
  },

  /**
   * POST /api/v1/forget
   * Remove a source from memory (forget() lifecycle).
   */
  async forget(body: ForgetRequest): Promise<ForgetResponse> {
    return request<ForgetResponse>('/api/v1/forget', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  },
}
