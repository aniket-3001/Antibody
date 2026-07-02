import { AppShell } from '@/components/layout/AppShell'

/**
 * MemoryOS — single-page application.
 *
 * All routing is managed via URL hash (#recall / #sources / #upload)
 * inside AppShell. This page file is the single entry point.
 */
export default function Home() {
  return <AppShell />
}
