'use client'

import { useAppState, useAppActions } from '@/context/AppStore'
import { useRefresh } from '@/hooks/useRefresh'
import { HealthDot } from '@/components/ui/HealthDot'
import type { ActiveTab, StatsResponse } from '@/lib/types'

/** Memory pulse strip — shows node/edge/source counts. */
function MemoryStrip({ stats, nodeCount, edgeCount }: {
  stats: StatsResponse | null
  nodeCount: number
  edgeCount: number
}) {
  return (
    <div className="flex items-center gap-4 text-xs text-slate-400" aria-live="polite" aria-label="Memory statistics">
      <Pill value={nodeCount}              label="nodes"   icon="◉" />
      <Pill value={edgeCount}              label="edges"   icon="⟶" />
      <Pill value={stats?.total_sources ?? 0} label="sources" icon="📄" />
      {stats?.entity_counts && Object.keys(stats.entity_counts).length > 0 && (
        <span className="hidden lg:flex items-center gap-2">
          {Object.entries(stats.entity_counts).slice(0, 3).map(([type, count]) => (
            <Pill key={type} value={count} label={type.toLowerCase()} icon="·" />
          ))}
        </span>
      )}
    </div>
  )
}

function Pill({ value, label, icon }: { value: number; label: string; icon: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className="text-slate-500" aria-hidden="true">{icon}</span>
      <span className="font-mono text-slate-200 tabular-nums">{value}</span>
      <span className="text-slate-500">{label}</span>
    </span>
  )
}

/** Tab row with keyboard navigation. */
const TABS: { id: ActiveTab; label: string; icon: string }[] = [
  { id: 'recall',  label: 'Recall',  icon: '🔍' },
  { id: 'sources', label: 'Sources', icon: '📚' },
  { id: 'upload',  label: 'Upload',  icon: '⬆'  },
]

function TabBar() {
  const { activeTab } = useAppState()
  const { setTab } = useAppActions()

  const handleKeyDown = (e: React.KeyboardEvent, current: number) => {
    if (e.key === 'ArrowRight') setTab(TABS[(current + 1) % TABS.length].id)
    if (e.key === 'ArrowLeft')  setTab(TABS[(current + TABS.length - 1) % TABS.length].id)
  }

  return (
    <div className="flex items-center gap-1" role="tablist" aria-label="Panel navigation">
      {TABS.map((tab, i) => {
        const active = activeTab === tab.id
        return (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            role="tab"
            aria-selected={active}
            aria-controls={`panel-${tab.id}`}
            tabIndex={active ? 0 : -1}
            onClick={() => setTab(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, i)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-150
              ${active
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-900/50'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
          >
            <span aria-hidden="true" className="text-xs">{tab.icon}</span>
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}

/** Health banner — shown when backend is degraded (spec §9.3). */
function HealthBanner() {
  const { health, healthBannerDismissed } = useAppState()
  const { dismissHealthBanner } = useAppActions()
  const { refreshHealth } = useRefresh()   // side-effect-free — no mount fetch

  if (!health || health.status === 'ok' || healthBannerDismissed) return null

  return (
    <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2 flex items-center gap-3 text-sm text-amber-300">
      <span aria-hidden="true">⚠</span>
      <span>Backend misconfigured — Check your .env file (CONFIGURATION_ERROR).</span>
      <button
        onClick={() => void refreshHealth()}
        className="ml-auto text-xs underline hover:text-amber-200 transition-colors"
      >
        Retry
      </button>
      <button
        onClick={dismissHealthBanner}
        className="text-xs text-amber-500 hover:text-amber-300 transition-colors"
        aria-label="Dismiss banner"
      >
        ✕
      </button>
    </div>
  )
}

export function Header() {
  const { stats, graph, health } = useAppState()

  const healthStatus: 'ok' | 'degraded' | 'unknown' | 'error' =
    health == null     ? 'unknown'  :
    health.status === 'ok' ? 'ok'  :
    'degraded'

  const nodeCount = graph?.node_count ?? 0
  const edgeCount = graph?.edge_count ?? 0

  return (
    <header className="flex-none border-b border-slate-700/60 bg-slate-900/95 backdrop-blur-sm">
      <HealthBanner />
      <div className="flex items-center gap-4 px-4 h-14">
        {/* Logo */}
        <div className="flex items-center gap-2.5 flex-none">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-900/50">
            <span className="text-white text-xs font-bold" aria-hidden="true">M</span>
          </div>
          <div className="hidden sm:block">
            <span className="text-sm font-semibold text-slate-100 tracking-tight">MemoryOS</span>
            <span className="ml-1.5 text-xs text-slate-500">Research Memory</span>
          </div>
        </div>

        <div className="h-5 w-px bg-slate-700 hidden sm:block" aria-hidden="true" />

        {/* Memory strip */}
        <div className="flex-1 min-w-0">
          <MemoryStrip stats={stats} nodeCount={nodeCount} edgeCount={edgeCount} />
        </div>

        {/* Tab navigation */}
        <TabBar />

        <div className="h-5 w-px bg-slate-700 hidden sm:block" aria-hidden="true" />

        {/* Health dot */}
        <HealthDot status={healthStatus} />
      </div>
    </header>
  )
}
