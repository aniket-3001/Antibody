'use client'

/**
 * useRefresh — side-effect-free refresh functions.
 *
 * Safe to call from any component. Contains NO useEffect / mount-side-effects.
 * Components that only need refresh (not initial load) should import this.
 *
 * Only AppShell's useAppData hook performs the initial mount fetch.
 */

import { useCallback, useRef } from 'react'
import { api } from '@/lib/api'
import { useAppActions } from '@/context/AppStore'

export function useRefresh() {
  const actions = useAppActions()
  const mountedRef = useRef(true)

  const refreshHealth = useCallback(async () => {
    try {
      const h = await api.health()
      actions.setHealth(h)
    } catch {
      /* non-fatal */
    }
  }, [actions])

  const refreshStats = useCallback(async () => {
    actions.setLoadingStats(true)
    try {
      const s = await api.stats()
      actions.setStats(s)
    } catch {
      /* non-fatal */
    } finally {
      actions.setLoadingStats(false)
    }
  }, [actions])

  const refreshSources = useCallback(async () => {
    actions.setLoadingSources(true)
    try {
      const s = await api.sources()
      actions.setSources(s.sources)
    } catch {
      /* non-fatal */
    } finally {
      actions.setLoadingSources(false)
    }
  }, [actions])

  const refreshGraph = useCallback(async () => {
    actions.setLoadingGraph(true)
    try {
      const g = await api.graph()
      actions.setGraph(g)
      actions.clearEvidence()
    } catch {
      /* non-fatal */
    } finally {
      actions.setLoadingGraph(false)
    }
  }, [actions])

  const refreshAll = useCallback(async () => {
    await Promise.allSettled([refreshGraph(), refreshStats(), refreshSources()])
  }, [refreshGraph, refreshStats, refreshSources])

  return { refreshGraph, refreshStats, refreshSources, refreshHealth, refreshAll }
}
