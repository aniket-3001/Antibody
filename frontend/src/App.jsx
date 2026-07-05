import { useState, useEffect } from "react";
import { ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import CheckView from "./components/CheckView.jsx";
import FeedView from "./components/FeedView.jsx";
import GraphView from "./components/GraphView.jsx";
import LeaderboardView from "./components/LeaderboardView.jsx";
import MyReportsView from "./components/MyReportsView.jsx";
import ExtensionPreviewView from "./components/ExtensionPreviewView.jsx";
import { Toaster, toast as showToast } from "./components/ui/toast.jsx";
import { cn } from "./lib/utils.js";

export default function App() {
  const [tab, setTab] = useState("check");

  const tabs = [
    { id: "check", label: "Check a message" },
    { id: "feed", label: "What's going around" },
    { id: "graph", label: "Knowledge graph" },
    { id: "leaderboard", label: "Leaderboard" },
    { id: "reports", label: "My Reports" },
    { id: "extension", label: "Extension Preview" },
  ];

  // Mock Real-time Threat Alerts
  useEffect(() => {
    const alerts = [
      { title: "Critical Threat", message: "New 'Bank OTP' scam trending — 120 reports in the last hour.", variant: "danger" },
      { title: "Warning", message: "Spike in 'Fake USPS Delivery' texts detected in your region.", variant: "warn" },
      { title: "Update", message: "New tactic 'Urgency Threat' mapped to 3 active scam families.", variant: "default" },
      { title: "Threat Blocked", message: "A highly reported crypto phishing link was just neutralized.", variant: "safe" }
    ];

    const timer = setInterval(() => {
      const alert = alerts[Math.floor(Math.random() * alerts.length)];
      showToast(alert.message, { title: alert.title, variant: alert.variant });
    }, 18000); // Fire an alert every 18 seconds for demo purposes

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="mx-auto flex max-w-[1200px] gap-10 px-6 pt-10 pb-20 items-start min-h-screen">
      {/* Sidebar Navigation */}
      <aside className="w-64 shrink-0 sticky top-10 flex flex-col gap-10">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] text-[var(--color-surface)] shadow-[0_10px_22px_-8px_rgba(30,58,138,0.6)]">
            <ShieldCheck size={26} strokeWidth={2.5} />
          </div>
          <div className="text-left">
            <h1 className="m-0 text-xl font-extrabold tracking-tight text-[var(--color-ink)]">
              Antibody
            </h1>
            <p className="m-0 mt-0.5 text-xs text-[var(--color-muted)] leading-tight">
              your collective immune system
            </p>
          </div>
        </div>

        <nav className="flex flex-col gap-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "relative rounded-lg px-4 py-3 text-sm font-bold transition-colors text-left",
                tab === t.id ? "text-[var(--color-surface)]" : "text-[var(--color-muted)] hover:text-[var(--color-ink)] hover:bg-[var(--color-surface)] border border-transparent hover:border-[var(--color-line)] shadow-none"
              )}
            >
              {tab === t.id && (
                <motion.div
                  layoutId="active-tab"
                  className="absolute inset-0 rounded-lg bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] shadow-[0_8px_18px_-8px_rgba(30,58,138,0.6)]"
                  initial={false}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
              <span className="relative z-10 block">{t.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto pt-8 text-[13px] leading-relaxed text-[var(--color-muted)]">
          Got something suspicious? Check it here — and if it was a scam, tell us.<br /><br />
          Every report helps protect the next person. Powered by <b className="text-[var(--color-ink)]">Cognee</b>.
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 bg-[var(--color-surface)] p-8 rounded-2xl border border-[var(--color-line)] shadow-[var(--shadow-custom-sm)]">
        {tab === "check" && <CheckView />}
        {tab === "feed" && <FeedView />}
        {tab === "graph" && <GraphView />}
        {tab === "leaderboard" && <LeaderboardView />}
        {tab === "reports" && <MyReportsView />}
        {tab === "extension" && <ExtensionPreviewView />}
      </main>

      <Toaster />
    </div>
  );
}
