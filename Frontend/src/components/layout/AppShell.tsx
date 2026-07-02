'use client'

/**
 * AppShell — top-level layout.
 *
 * Spec §2.1: 65/35 split (graph canvas / interaction panel).
 * Header is full-width across the top.
 * The graph canvas is always visible — never covered by panels.
 */

import dynamic from 'next/dynamic'
import { Header } from './Header'
import { InteractionPanel } from '@/components/panels/InteractionPanel'
import { ToastContainer } from '@/components/ui/Toast'
import { useAppData } from '@/hooks/useAppData'

/**
 * GraphArea is dynamically imported (no SSR) because Cytoscape.js uses
 * browser APIs (window, document, canvas) not available in Node.js.
 */
const GraphArea = dynamic(
  () => import('@/components/graph/GraphArea').then((m) => m.GraphArea),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center bg-[#0a0e1a]">
        <div className="text-slate-600 text-sm flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center animate-pulse">
            <span className="text-white text-sm font-bold">M</span>
          </div>
          <span>Initialising graph canvas…</span>
        </div>
      </div>
    ),
  },
)

/** Inner component that mounts data fetching (must be inside AppStoreProvider). */
function AppShellInner() {
  // Mount data fetching — this hook drives all backend calls
  useAppData()

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Persistent header with tabs + stats strip */}
      <Header />

      {/* Main area: graph canvas + interaction panel side by side */}
      <main className="flex flex-1 min-h-0 overflow-hidden">
        {/* Graph canvas — hero element, takes all remaining width */}
        <div className="flex-1 min-w-0 relative" id="graph-region">
          <GraphArea />
        </div>

        {/* Interaction panel — fixed 400px right side */}
        <InteractionPanel />
      </main>

      {/* Global toast notifications */}
      <ToastContainer />
    </div>
  )
}

export function AppShell() {
  return <AppShellInner />
}
