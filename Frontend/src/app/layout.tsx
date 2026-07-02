import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { AppStoreProvider } from '@/context/AppStore'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'MemoryOS — Persistent Research Memory',
  description:
    'A persistent memory operating system for researchers. Build, query, and evolve a living knowledge graph from your research papers and notes.',
  keywords: ['AI', 'knowledge graph', 'research', 'memory', 'Cognee'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased bg-slate-900 text-slate-100">
        <AppStoreProvider>{children}</AppStoreProvider>
      </body>
    </html>
  )
}
