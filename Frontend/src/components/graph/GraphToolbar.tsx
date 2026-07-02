'use client'

import type { GraphCanvasHandle } from './GraphCanvas'

interface GraphToolbarProps {
  canvasRef: React.RefObject<GraphCanvasHandle>
  evidenceMode: boolean
  onClearEvidence: () => void
  onRefresh: () => void
}

/**
 * GraphToolbar — floating controls bottom-left of the graph canvas.
 * Spec §6.4: Fit / Zoom+ / Zoom- / Reset layout / Refresh / Clear evidence.
 */
export function GraphToolbar({
  canvasRef,
  evidenceMode,
  onClearEvidence,
  onRefresh,
}: GraphToolbarProps) {
  return (
    <div
      className="absolute bottom-4 left-4 z-10 flex items-center gap-1 bg-slate-900/80 border border-slate-700/60 backdrop-blur-sm rounded-lg p-1 shadow-lg"
      role="toolbar"
      aria-label="Graph controls"
    >
      <ToolButton
        onClick={() => canvasRef.current?.fitAll()}
        title="Fit all nodes (F)"
        aria-label="Fit all nodes to view"
      >
        ⊞
      </ToolButton>

      <ToolButton
        onClick={() => canvasRef.current?.zoomIn()}
        title="Zoom in (+)"
        aria-label="Zoom in"
      >
        +
      </ToolButton>

      <ToolButton
        onClick={() => canvasRef.current?.zoomOut()}
        title="Zoom out (−)"
        aria-label="Zoom out"
      >
        −
      </ToolButton>

      <div className="w-px h-5 bg-slate-700 mx-0.5" aria-hidden="true" />

      <ToolButton
        onClick={() => canvasRef.current?.resetLayout()}
        title="Re-run layout (R)"
        aria-label="Reset graph layout"
      >
        ↺
      </ToolButton>

      <ToolButton
        onClick={onRefresh}
        title="Refresh graph from server"
        aria-label="Refresh graph"
      >
        ◎
      </ToolButton>

      {evidenceMode && (
        <>
          <div className="w-px h-5 bg-slate-700 mx-0.5" aria-hidden="true" />
          <button
            onClick={onClearEvidence}
            className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 rounded-md transition-colors"
            title="Clear evidence highlighting"
            aria-label="Clear evidence highlighting"
          >
            <span aria-hidden="true">✕</span>
            Clear Evidence
          </button>
        </>
      )}
    </div>
  )
}

function ToolButton({
  children,
  onClick,
  title,
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 rounded-md transition-colors text-sm font-medium"
      {...rest}
    >
      {children}
    </button>
  )
}
