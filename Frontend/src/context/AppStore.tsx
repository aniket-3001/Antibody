'use client'

/**
 * AppStore — central React context + useReducer state for MemoryOS.
 *
 * State lives here; components read via useAppStore() and dispatch actions
 * via useAppActions(). No business logic here — only state shape.
 */

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useMemo,
  type ReactNode,
  type Dispatch,
} from 'react'
import type {
  ActiveTab,
  CytoscapeGraph,
  CytoscapeNodeData,
  HealthResponse,
  RecallResponse,
  RecallStrategy,
  SourceItem,
  StatsResponse,
  ToastItem,
  ToastType,
} from '@/lib/types'

// ── State ─────────────────────────────────────────────────────────────────────

interface AppState {
  // Backend data
  graph: CytoscapeGraph | null
  sources: SourceItem[]
  stats: StatsResponse | null
  health: HealthResponse | null

  // Panel navigation
  activeTab: ActiveTab

  // Graph — selected node
  selectedNode: CytoscapeNodeData | null

  // Evidence mode (post-recall)
  evidenceMode: boolean
  evidenceNodeIds: Set<string>
  evidenceStrategy: RecallStrategy | null

  // Recall history (last 5)
  lastRecall: RecallResponse | null
  recallHistory: string[]

  // Loading flags
  loadingGraph: boolean
  loadingStats: boolean
  loadingSources: boolean

  // Toasts
  toasts: ToastItem[]

  // Health banner
  healthBannerDismissed: boolean
}

const initialState: AppState = {
  graph: null,
  sources: [],
  stats: null,
  health: null,

  activeTab: 'recall',

  selectedNode: null,

  evidenceMode: false,
  evidenceNodeIds: new Set(),
  evidenceStrategy: null,

  lastRecall: null,
  recallHistory: [],

  loadingGraph: false,
  loadingStats: false,
  loadingSources: false,

  toasts: [],

  healthBannerDismissed: false,
}

// ── Actions ───────────────────────────────────────────────────────────────────

type AppAction =
  | { type: 'SET_GRAPH'; payload: CytoscapeGraph }
  | { type: 'SET_SOURCES'; payload: SourceItem[] }
  | { type: 'SET_STATS'; payload: StatsResponse }
  | { type: 'SET_HEALTH'; payload: HealthResponse }
  | { type: 'SET_TAB'; payload: ActiveTab }
  | { type: 'SET_SELECTED_NODE'; payload: CytoscapeNodeData | null }
  | { type: 'SET_EVIDENCE'; payload: { nodeIds: Set<string>; strategy: RecallStrategy | null } }
  | { type: 'CLEAR_EVIDENCE' }
  | { type: 'SET_LAST_RECALL'; payload: RecallResponse }
  | { type: 'ADD_RECALL_HISTORY'; payload: string }
  | { type: 'LOADING_GRAPH'; payload: boolean }
  | { type: 'LOADING_STATS'; payload: boolean }
  | { type: 'LOADING_SOURCES'; payload: boolean }
  | { type: 'ADD_TOAST'; payload: ToastItem }
  | { type: 'REMOVE_TOAST'; payload: string }
  | { type: 'DISMISS_HEALTH_BANNER' }

// ── Reducer ───────────────────────────────────────────────────────────────────

function reducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_GRAPH':
      return { ...state, graph: action.payload }
    case 'SET_SOURCES':
      return { ...state, sources: action.payload }
    case 'SET_STATS':
      return { ...state, stats: action.payload }
    case 'SET_HEALTH':
      return { ...state, health: action.payload }

    case 'SET_TAB':
      // Switching tabs clears node selection
      return { ...state, activeTab: action.payload, selectedNode: null }

    case 'SET_SELECTED_NODE':
      return { ...state, selectedNode: action.payload }

    case 'SET_EVIDENCE':
      return {
        ...state,
        evidenceMode: true,
        evidenceNodeIds: action.payload.nodeIds,
        evidenceStrategy: action.payload.strategy,
      }
    case 'CLEAR_EVIDENCE':
      return {
        ...state,
        evidenceMode: false,
        evidenceNodeIds: new Set(),
        evidenceStrategy: null,
      }

    case 'SET_LAST_RECALL':
      return { ...state, lastRecall: action.payload }
    case 'ADD_RECALL_HISTORY': {
      const existing = state.recallHistory.filter((q) => q !== action.payload)
      return { ...state, recallHistory: [action.payload, ...existing].slice(0, 5) }
    }

    case 'LOADING_GRAPH':
      return { ...state, loadingGraph: action.payload }
    case 'LOADING_STATS':
      return { ...state, loadingStats: action.payload }
    case 'LOADING_SOURCES':
      return { ...state, loadingSources: action.payload }

    case 'ADD_TOAST':
      return { ...state, toasts: [...state.toasts, action.payload] }
    case 'REMOVE_TOAST':
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.payload) }

    case 'DISMISS_HEALTH_BANNER':
      return { ...state, healthBannerDismissed: true }

    default:
      return state
  }
}

// ── Context ───────────────────────────────────────────────────────────────────

const StateContext = createContext<AppState>(initialState)
const DispatchContext = createContext<Dispatch<AppAction>>(() => undefined)

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  return (
    <StateContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>
        {children}
      </DispatchContext.Provider>
    </StateContext.Provider>
  )
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

export function useAppState(): AppState {
  return useContext(StateContext)
}

function useDispatch(): Dispatch<AppAction> {
  return useContext(DispatchContext)
}

/** High-level action creators — these are the only way components update state. */
export function useAppActions() {
  const dispatch = useDispatch()

  return useMemo(
    () => ({
      setGraph: (g: CytoscapeGraph) => dispatch({ type: 'SET_GRAPH', payload: g }),
      setSources: (s: SourceItem[]) => dispatch({ type: 'SET_SOURCES', payload: s }),
      setStats: (s: StatsResponse) => dispatch({ type: 'SET_STATS', payload: s }),
      setHealth: (h: HealthResponse) => dispatch({ type: 'SET_HEALTH', payload: h }),
      setTab: (t: ActiveTab) => dispatch({ type: 'SET_TAB', payload: t }),
      setSelectedNode: (n: CytoscapeNodeData | null) =>
        dispatch({ type: 'SET_SELECTED_NODE', payload: n }),
      setEvidence: (nodeIds: Set<string>, strategy: RecallStrategy | null) =>
        dispatch({ type: 'SET_EVIDENCE', payload: { nodeIds, strategy } }),
      clearEvidence: () => dispatch({ type: 'CLEAR_EVIDENCE' }),
      setLastRecall: (r: RecallResponse) => dispatch({ type: 'SET_LAST_RECALL', payload: r }),
      addRecallHistory: (q: string) => dispatch({ type: 'ADD_RECALL_HISTORY', payload: q }),
      setLoadingGraph: (v: boolean) => dispatch({ type: 'LOADING_GRAPH', payload: v }),
      setLoadingStats: (v: boolean) => dispatch({ type: 'LOADING_STATS', payload: v }),
      setLoadingSources: (v: boolean) => dispatch({ type: 'LOADING_SOURCES', payload: v }),
      addToast: (type: ToastType, message: string, duration?: number) => {
        const item: ToastItem = { id: `${Date.now()}-${Math.random()}`, type, message, duration }
        dispatch({ type: 'ADD_TOAST', payload: item })
      },
      removeToast: (id: string) => dispatch({ type: 'REMOVE_TOAST', payload: id }),
      dismissHealthBanner: () => dispatch({ type: 'DISMISS_HEALTH_BANNER' }),
    }),
    [dispatch],
  )
}
