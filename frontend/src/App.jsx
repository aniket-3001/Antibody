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
    <div className="mx-auto max-w-[760px] px-[18px] pt-[26px] pb-[90px]">
      <header className="mb-6 text-center">
        <div className="inline-flex items-center gap-[13px]">
          <div className="flex h-[54px] w-[54px] items-center justify-center rounded-[18px] bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] text-[var(--color-surface)] shadow-[0_10px_22px_-8px_rgba(0,255,65,0.6)]">
            <ShieldCheck size={28} strokeWidth={2.5} />
          </div>
          <div className="text-left">
            <h1 className="m-0 text-[25px] font-extrabold tracking-tight text-[var(--color-ink)]">
              Antibody
            </h1>
            <p className="m-0 mt-[3px] text-[13px] text-[var(--color-muted)]">
              your collective immune system
            </p>
          </div>
        </div>

        <div className="mx-auto mt-5 inline-flex gap-1 rounded-full bg-[var(--color-surface)] p-[5px] shadow-[var(--shadow-custom-sm)] border border-[var(--color-line)]">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "relative rounded-full px-[22px] py-[10px] text-[14px] font-bold transition-colors",
                tab === t.id ? "text-[var(--color-surface)]" : "text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              )}
            >
              {tab === t.id && (
                <motion.div
                  layoutId="active-tab"
                  className="absolute inset-0 rounded-full bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] shadow-[0_8px_18px_-8px_rgba(30,58,138,0.6)]"
                  initial={false}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
              <span className="relative z-10">{t.label}</span>
            </button>
          ))}
        </div>
      </header>

      <main>
        {tab === "check" && <CheckView />}
        {tab === "feed" && <FeedView />}
        {tab === "graph" && <GraphView />}
        {tab === "leaderboard" && <LeaderboardView />}
        {tab === "reports" && <MyReportsView />}
        {tab === "extension" && <ExtensionPreviewView />}
      </main>

      <footer className="mt-12 text-center text-[15px] leading-relaxed text-[var(--color-body)]">
        Got something suspicious? Check it here — and if it was a scam, tell us.<br />
        Every report helps protect the next person. Powered by <b className="text-[var(--color-ink)]">Cognee</b> memory · matched by meaning, not just keywords.
      </footer>
      <Toaster />
    </div>
  );
}
