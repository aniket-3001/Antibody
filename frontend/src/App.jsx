import { useState, useEffect } from "react";
import { ShieldCheck, Fingerprint, Copy, CheckCircle2, RotateCcw, Info, GitBranch } from "lucide-react";
import { motion } from "framer-motion";
import CheckView, { Verdict } from "./components/CheckView.jsx";
import FeedView from "./components/FeedView.jsx";
import GraphView from "./components/GraphView.jsx";
import LeaderboardView from "./components/LeaderboardView.jsx";
import MyReportsView from "./components/MyReportsView.jsx";
import ExtensionPreviewView from "./components/ExtensionPreviewView.jsx";
import HelpView from "./components/HelpView.jsx";
import { Toaster, toast as showToast } from "./components/ui/toast.jsx";
import { Modal } from "./components/ui/modal.jsx";
import { Button } from "./components/ui/button.jsx";
import { cn } from "./lib/utils.js";
import { getFeed, getReport, submitOutcome, forgetReporter } from "./api.js";
import { getClientId, resetClientId } from "./lib/identity.js";

// Sidebar panel: shows this browser's anonymous id and offers real erasure —
// hard-deletes the id and every report tied to it, then rotates to a fresh id.
function ReporterIdPanel() {
  const [id, setId] = useState(() => getClientId());
  const [copied, setCopied] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const doReset = async () => {
    setBusy(true);
    try {
      await forgetReporter(id);
      const fresh = resetClientId();
      setId(fresh);
      showToast("Your old id and every report tied to it were deleted from our server.", {
        title: "Forgotten",
        variant: "safe",
      });
    } catch (e) {
      showToast(String(e.message || e), { title: "Couldn't reach the server", variant: "danger" });
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  return (
    <div className="hidden md:flex flex-col gap-2 rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-2)] p-3 text-xs">
      <div className="relative group flex items-center gap-1.5 font-bold text-[var(--color-ink)] cursor-help w-max">
        <Fingerprint size={14} className="text-[var(--color-brand)]" /> Your anonymous id
        <Info size={12} className="text-[var(--color-body)] group-hover:text-[var(--color-ink)] transition-colors" />
        <div className="absolute bottom-full left-0 mb-2 w-56 p-2 bg-[var(--color-ink)] text-[var(--color-surface)] font-normal text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
          A random id tied to this browser, used to track your reports and leaderboard score while keeping you completely anonymous.
        </div>
      </div>
      <div className="truncate font-mono text-[var(--color-muted)]" title={id}>{id}</div>
      <div className="flex gap-2">
        <button
          onClick={copy}
          className="flex items-center gap-1 font-bold text-[var(--color-brand)] hover:underline"
        >
          {copied ? <CheckCircle2 size={12} /> : <Copy size={12} />}
          {copied ? "Copied" : "Copy"}
        </button>
        <div className="relative group flex items-center cursor-help">
          <button
            onClick={() => setConfirming(true)}
            className="flex items-center gap-1 font-bold text-[var(--color-danger)] hover:underline"
          >
            <RotateCcw size={12} /> Forget me
          </button>
          <Info size={12} className="ml-1 text-[var(--color-body)] group-hover:text-[var(--color-ink)] transition-colors" />
          <div className="absolute bottom-full right-0 md:left-0 mb-2 w-56 p-2 bg-[var(--color-ink)] text-[var(--color-surface)] font-normal text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
            Hard-deletes your id and every report tied to it from our server, then gives this browser a fresh id.
          </div>
        </div>
      </div>

      <Modal isOpen={confirming} onClose={() => setConfirming(false)} title="Forget this id?">
        <div className="flex flex-col gap-4">
          <p className="text-sm text-[var(--color-body)]">
            This deletes every report you've filed and your trust/leaderboard
            score from our server, then gives this browser a brand-new
            anonymous id. It can't be undone, and your old My Reports history
            won't be recoverable.
          </p>
          <div className="flex gap-2">
            <Button variant="secondary" className="flex-1" onClick={() => setConfirming(false)} disabled={busy}>
              Cancel
            </Button>
            <Button variant="destructive" className="flex-1" onClick={doReset} disabled={busy}>
              {busy ? "Deleting…" : "Yes, forget me"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// Standalone page for a shared verdict link (?v=<report_id>) — someone was sent
// a verdict and lands here without the full app chrome.
function SharedVerdictView({ reportId, onBack }) {
  const [v, setV] = useState(null);
  const [outcome, setOutcome] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    getReport(reportId)
      .then((res) => setV({ ...res, checked_text: res.transcript || "" }))
      .catch((e) => setErr(String(e)));
  }, [reportId]);

  const record = async (o) => {
    if (!v?.report_id) return;
    try {
      await submitOutcome(v.report_id, o);
      setOutcome(o);
    } catch (e) { setErr(String(e)); }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-10 md:py-16">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] text-[var(--color-surface)]">
          <ShieldCheck size={20} strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="m-0 text-lg font-extrabold tracking-tight text-[var(--color-ink)]">Antibody</h1>
          <p className="m-0 text-xs text-[var(--color-muted)]">someone shared this verdict with you</p>
        </div>
      </div>

      {err && (
        <div className="rounded-lg border border-[var(--color-danger-line)] bg-[var(--color-danger-bg)] p-4 text-sm text-[var(--color-danger)]">
          Couldn't load this report — it may have been removed. ({err})
        </div>
      )}
      {!err && !v && <div className="text-sm text-[var(--color-muted)]">Loading…</div>}
      {v && <Verdict v={v} outcome={outcome} onOutcome={record} />}

      <button
        onClick={onBack}
        className="self-start text-sm font-bold text-[var(--color-brand)] hover:underline"
      >
        Check your own message →
      </button>
    </div>
  );
}

function MainApp() {
  const [tab, setTab] = useState(() => {
    return localStorage.getItem("antibody_active_tab") || "check";
  });
  // Tabs are lazy-mounted on first visit, then kept alive (hidden, not
  // unmounted) so switching away and back doesn't lose in-progress input or
  // an in-flight request — e.g. typing a message on Check, or a Help chat.
  const [visited, setVisited] = useState(() => new Set([tab]));

  useEffect(() => {
    localStorage.setItem("antibody_active_tab", tab);
  }, [tab]);

  const selectTab = (id) => {
    setVisited((prev) => (prev.has(id) ? prev : new Set(prev).add(id)));
    setTab(id);
  };

  const tabs = [
    { id: "check", label: "Check a Message" },
    { id: "feed", label: "Live Threat Feed" },
    { id: "graph", label: "Knowledge Graph" },
    { id: "leaderboard", label: "Community Leaderboard" },
    { id: "reports", label: "My Reports" },
    { id: "extension", label: "Browser Extension" },
    { id: "help", label: "Help Center" },
  ];

  // Real threat ticker — polls /feed and toasts only genuinely NEW activity
  // (not on every poll tick), so it reflects what's actually happening.
  useEffect(() => {
    let cancelled = false;
    let initialized = false;
    const seenReportIds = new Set();
    const seenEmerging = new Set();

    const poll = async () => {
      let feed;
      try {
        feed = await getFeed();
      } catch {
        return; // feed unavailable this tick — try again next interval
      }
      if (cancelled) return;

      if (!initialized) {
        // Seed baseline from current state so we don't toast a backlog on load.
        (feed.recent || []).forEach((r) => seenReportIds.add(r.id));
        (feed.emerging || []).forEach((e) => seenEmerging.add(e.name));
        initialized = true;
        return;
      }

      for (const r of feed.recent || []) {
        if (seenReportIds.has(r.id)) continue;
        seenReportIds.add(r.id);
        const isConfirmed = r.outcome === "confirmed_scam" || r.outcome === "i_got_scammed";
        showToast(r.preview || "A new report just came in.", {
          title: r.family ? `New '${r.family.replace(/_/g, " ")}' report` : "New report",
          variant: isConfirmed ? "danger" : "default",
        });
      }

      for (const e of feed.emerging || []) {
        if (seenEmerging.has(e.name)) continue;
        seenEmerging.add(e.name);
        showToast(
          `${e.display || e.name} is picking up — ${e.count} reports in the last ${e.emerged_hours_ago}h.`,
          { title: "Emerging threat", variant: "warn" }
        );
      }
    };

    poll();
    const timer = setInterval(poll, 20000);
    return () => { cancelled = true; clearInterval(timer); };
  }, []);

  return (
    <div className="mx-auto flex flex-col md:flex-row max-w-[1200px] gap-6 md:gap-10 px-4 md:px-6 pt-6 md:pt-10 pb-20 items-start min-h-screen">
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 shrink-0 md:sticky top-10 flex flex-col gap-6 md:gap-10">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] text-[var(--color-surface)] shadow-[0_10px_22px_-8px_rgba(30,58,138,0.6)]">
            <ShieldCheck size={26} strokeWidth={2.5} />
          </div>
          <div className="text-left flex flex-col items-start">
            <a
              href="https://github.com/aniket-3001/Antibody"
              target="_blank"
              rel="noopener noreferrer"
              className="m-0 text-xl font-extrabold tracking-tight text-[var(--color-ink)] hover:text-[var(--color-brand)] transition-colors flex items-center gap-1.5"
            >
              Antibody
            </a>
            <p className="m-0 mt-0.5 text-xs text-[var(--color-muted)] leading-tight">
              your collective immune system
            </p>
            <a
              href="https://github.com/aniket-3001/Antibody"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 flex items-center gap-1.5 text-[11px] font-bold tracking-wider text-[var(--color-ink)] bg-[var(--color-surface-2)] hover:bg-[var(--color-line)] border border-[var(--color-line)] px-2 py-1 rounded-md transition-colors w-max"
            >
              <GitBranch size={12} /> GitHub
            </a>
          </div>
        </div>

        <nav className="flex flex-row overflow-x-auto md:flex-col gap-2 pb-2 md:pb-0 hide-scrollbar -mx-4 px-4 md:mx-0 md:px-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => selectTab(t.id)}
              className={cn(
                "relative rounded-lg px-4 py-3 text-sm font-bold transition-colors text-left shrink-0",
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

        <div className="mt-auto pt-8 flex flex-col gap-4">
          <div className="text-[13px] leading-relaxed text-[var(--color-muted)] hidden md:block">
            Got something suspicious? Check it here — and if it was a scam, tell us.<br /><br />
            Every report helps protect the next person. Powered by <a href="https://www.cognee.ai/" target="_blank" rel="noopener noreferrer" className="text-[var(--color-ink)] hover:text-[var(--color-brand)] font-bold transition-colors">Cognee</a>.
          </div>
          <ReporterIdPanel />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 w-full bg-[var(--color-surface)] p-6 md:p-8 rounded-2xl border border-[var(--color-line)] shadow-[var(--shadow-custom-sm)]">
        {visited.has("check") && <div className={tab === "check" ? "" : "hidden"}><CheckView /></div>}
        {visited.has("feed") && <div className={tab === "feed" ? "" : "hidden"}><FeedView /></div>}
        {visited.has("graph") && <div className={tab === "graph" ? "" : "hidden"}><GraphView /></div>}
        {visited.has("leaderboard") && <div className={tab === "leaderboard" ? "" : "hidden"}><LeaderboardView /></div>}
        {visited.has("reports") && <div className={tab === "reports" ? "" : "hidden"}><MyReportsView /></div>}
        {visited.has("extension") && <div className={tab === "extension" ? "" : "hidden"}><ExtensionPreviewView /></div>}
        {visited.has("help") && <div className={tab === "help" ? "" : "hidden"}><HelpView /></div>}
      </main>

      <Toaster />
    </div>
  );
}

export default function App() {
  const [sharedReportId, setSharedReportId] = useState(() => {
    return new URLSearchParams(window.location.search).get("v");
  });

  if (sharedReportId) {
    return (
      <>
        <SharedVerdictView
          reportId={sharedReportId}
          onBack={() => {
            window.history.pushState({}, "", window.location.pathname);
            setSharedReportId(null);
          }}
        />
        <Toaster />
      </>
    );
  }

  return <MainApp />;
}
