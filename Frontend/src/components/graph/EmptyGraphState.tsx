'use client'

import { useAppActions } from '@/context/AppStore'

/**
 * EmptyGraphState — shown when no sources have been ingested.
 *
 * Spec §10.1: animated ✦ particles suggesting latent structure.
 * The animation uses pure CSS (no canvas/WebGL) for simplicity and
 * prefers-reduced-motion respect.
 */

const PARTICLES = [
  { top: '20%', left: '35%', delay: '0s',    scale: 1.2 },
  { top: '35%', left: '25%', delay: '0.8s',  scale: 0.9 },
  { top: '25%', left: '55%', delay: '1.4s',  scale: 1.0 },
  { top: '45%', left: '60%', delay: '0.4s',  scale: 1.3 },
  { top: '55%', left: '40%', delay: '1.1s',  scale: 0.85 },
  { top: '60%', left: '30%', delay: '0.2s',  scale: 1.1 },
  { top: '40%', left: '70%', delay: '1.7s',  scale: 0.95 },
  { top: '65%', left: '55%', delay: '0.6s',  scale: 1.0 },
  { top: '30%', left: '75%', delay: '2.0s',  scale: 0.8 },
  { top: '70%', left: '20%', delay: '1.3s',  scale: 1.15 },
  { top: '18%', left: '48%', delay: '0.9s',  scale: 0.9 },
  { top: '75%', left: '68%', delay: '1.6s',  scale: 1.05 },
]

export function EmptyGraphState() {
  const { setTab } = useAppActions()

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center select-none">
      {/* Particle field */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        {PARTICLES.map((p, i) => (
          <span
            key={i}
            className="absolute text-indigo-500/40 font-bold text-lg animate-[drift_6s_ease-in-out_infinite]"
            style={{
              top: p.top,
              left: p.left,
              animationDelay: p.delay,
              transform: `scale(${p.scale})`,
              fontSize: `${14 + Math.random() * 8}px`,
            }}
          >
            ✦
          </span>
        ))}

        {/* Subtle connection lines (SVG) */}
        <svg className="absolute inset-0 w-full h-full opacity-10" aria-hidden="true">
          <line x1="35%" y1="20%" x2="25%" y2="35%" stroke="#6366f1" strokeWidth="1" strokeDasharray="4 4" />
          <line x1="35%" y1="20%" x2="55%" y2="25%" stroke="#6366f1" strokeWidth="1" strokeDasharray="4 4" />
          <line x1="55%" y1="25%" x2="60%" y2="45%" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 4" />
          <line x1="25%" y1="35%" x2="40%" y2="55%" stroke="#6366f1" strokeWidth="1" strokeDasharray="4 4" />
          <line x1="60%" y1="45%" x2="55%" y2="60%" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 4" />
        </svg>
      </div>

      {/* Central message */}
      <div className="relative z-10 flex flex-col items-center text-center max-w-xs px-6 animate-[fadeIn_0.6s_ease-out]">
        {/* Icon */}
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600/30 to-violet-600/30 border border-indigo-500/30 flex items-center justify-center mb-5 shadow-lg shadow-indigo-900/30">
          <span className="text-2xl" aria-hidden="true">✦</span>
        </div>

        <h2 className="text-slate-200 text-base font-semibold mb-2">
          Your knowledge graph will live here
        </h2>
        <p className="text-slate-500 text-sm leading-relaxed mb-6">
          Upload a research paper and watch entities and relationships
          materialise from its content.
        </p>

        <button
          onClick={() => setTab('upload')}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors duration-150 shadow-md shadow-indigo-900/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-400"
          aria-label="Open upload panel to add your first paper"
        >
          <span aria-hidden="true">→</span>
          Add First Paper
        </button>
      </div>
    </div>
  )
}
