'use client'

/**
 * useAppData — initial data-loading hook. Mount this ONCE in AppShell only.
 *
 * On mount it fires all four backend calls in parallel, then polls health
 * every 30 s. All other components use useRefresh() (no side effects).
 */

import { useEffect } from 'react'
import { useRefresh } from './useRefresh'

export function useAppData() {
  const refresh = useRefresh()

  useEffect(() => {
    // Parallel initial load
    void refresh.refreshHealth()
    void refresh.refreshGraph()
    void refresh.refreshStats()
    void refresh.refreshSources()

    // Lightweight health poll — does NOT re-fetch graph/stats
    const healthInterval = setInterval(() => {
      void refresh.refreshHealth()
    }, 30_000)

    return () => clearInterval(healthInterval)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Mount-only

  return refresh
}
