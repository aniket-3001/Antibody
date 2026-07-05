import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import CheckView from "./components/CheckView.jsx";
import FeedView from "./components/FeedView.jsx";
import GraphView from "./components/GraphView.jsx";
import { cn } from "./lib/utils.js";

export default function App() {
  const [tab, setTab] = useState("check");

  const tabs = [
    { id: "check", label: "Check a message" },
    { id: "feed", label: "What's going around" },
    { id: "graph", label: "Knowledge graph" },
  ];

  return (
    <div className="mx-auto max-w-[760px] px-[18px] pt-[26px] pb-[90px]">
      <header className="mb-6 text-center">
        <div className="inline-flex items-center gap-[13px]">
          <div className="flex h-[54px] w-[54px] items-center justify-center rounded-[18px] bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] text-white shadow-[0_10px_22px_-8px_rgba(107,92,240,0.6)]">
            <ShieldCheck size={28} strokeWidth={2.5} />
          </div>
          <div className="text-left">
            <h1 className="m-0 text-[25px] font-extrabold tracking-tight text-[var(--color-ink)]">
              Antibody
            </h1>
            <p className="m-0 mt-[3px] text-[13px] text-[var(--color-muted)]">
              your community shield against scams
            </p>
          </div>
        </div>

        <div className="mx-auto mt-5 inline-flex gap-1 rounded-full bg-[var(--color-surface)] p-[5px] shadow-[var(--shadow-custom-sm)]">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "relative rounded-full px-[22px] py-[10px] text-[14px] font-bold transition-colors",
                tab === t.id ? "text-white" : "text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              )}
            >
              {tab === t.id && (
                <motion.div
                  layoutId="active-tab"
                  className="absolute inset-0 rounded-full bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] shadow-[0_8px_18px_-8px_rgba(107,92,240,0.7)]"
                  initial={false}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
              <span className="relative z-10">{t.label}</span>
            </button>
          ))}
        </div>
      </header>

      <main className="mt-4">
        {tab === "check" ? <CheckView /> : tab === "feed" ? <FeedView /> : <GraphView />}
      </main>

      <footer className="mt-12 text-center text-[15px] leading-relaxed text-[var(--color-body)]">
        Got something suspicious? Check it here — and if it was a scam, tell us.<br />
        Every report helps protect the next person. Powered by <b className="text-[var(--color-ink)]">Cognee</b> memory · matched by meaning, not just keywords.
      </footer>
    </div>
  );
}
