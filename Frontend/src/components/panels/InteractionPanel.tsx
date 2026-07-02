'use client'

/**
 * InteractionPanel — right-side 400px panel with real tab content.
 *
 * Phase 4 upgrade: wires in RecallPanel, SourcesPanel, UploadPanel.
 * When selectedNode is set, shows NodeDetailPanel instead of the active tab.
 */

import { useAppState } from '@/context/AppStore'
import { RecallPanel } from './RecallPanel'
import { SourcesPanel } from './SourcesPanel'
import { UploadPanel } from './UploadPanel'
import { NodeDetailPanel } from '@/components/graph/NodeDetailPanel'
import type { ActiveTab } from '@/lib/types'

const PANELS: Record<ActiveTab, React.ComponentType> = {
  recall:  RecallPanel,
  sources: SourcesPanel,
  upload:  UploadPanel,
}

export function InteractionPanel() {
  const { activeTab, selectedNode } = useAppState()

  const ActivePanel = PANELS[activeTab]

  // When a node is selected, the panel shows the node detail view
  const showNodeDetail = !!selectedNode

  const panelTitle = showNodeDetail
    ? selectedNode?.label ?? 'Node Detail'
    : activeTab.charAt(0).toUpperCase() + activeTab.slice(1)

  return (
    <aside
      id={showNodeDetail ? 'panel-node-detail' : `panel-${activeTab}`}
      role="complementary"
      aria-label={panelTitle}
      className="flex flex-col h-full bg-slate-900/60 border-l border-slate-700/60 backdrop-blur-sm"
      style={{ width: 400, minWidth: 340, maxWidth: 480, flexShrink: 0 }}
    >
      {showNodeDetail ? (
        <NodeDetailPanel />
      ) : (
        <div className="flex flex-col h-full overflow-hidden">
          <ActivePanel />
        </div>
      )}
    </aside>
  )
}
