import { useState, useEffect } from "react";
import { ShieldCheck, Fingerprint, Copy, CheckCircle2, RotateCcw, Info } from "lucide-react";
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
      <div className="flex items-center gap-1.5 font-bold text-[var(--color-ink)]">
        <Fingerprint size={14} className="text-[var(--color-brand)]" /> Your anonymous id
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
        <button
          onClick={() => setConfirming(true)}
          className="flex items-center gap-1 font-bold text-[var(--color-danger)] hover:underline"
        >
          <RotateCcw size={12} /> Forget me
        </button>
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
          Couldn't load this report, it may have been removed. ({err})
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
    { id: "check", label: "Scam Detector", desc: "Scan a message, audio, or image for scams." },
    { id: "feed", label: "Live Threat Feed", desc: "Watch real-time scam activity." },
    { id: "graph", label: "Cognee Memory Base", desc: "Explore the connections between scams." },
    { id: "leaderboard", label: "Community Leaderboard", desc: "Top contributors keeping the community safe." },
    { id: "reports", label: "My Reports", desc: "Your personal history of reported scams." },
    { id: "extension", label: "Browser Extension", desc: "Get real-time browser protection." },
    { id: "help", label: "Help Center", desc: "Chat with the Antibody assistant." },
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
          title: r.family ? `New report: ${r.family}` : "New report",
          variant: isConfirmed ? "danger" : "default",
        });
      }

      for (const e of feed.emerging || []) {
        if (seenEmerging.has(e.name)) continue;
        seenEmerging.add(e.name);
        showToast(
          `${e.display || e.name} is picking up, ${e.count} reports in the last ${e.emerged_hours_ago}h.`,
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
      <aside className="w-full md:w-64 shrink-0 md:sticky top-10 flex flex-col gap-6 md:gap-10 z-40">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-2)] text-[var(--color-surface)] shadow-[0_10px_22px_-8px_rgba(30,58,138,0.6)]">
            <ShieldCheck size={26} strokeWidth={2.5} />
          </div>
          <div className="text-left">
            <h1 className="m-0 text-xl font-extrabold tracking-tight text-[var(--color-ink)]">
              Antibody
            </h1>
            <p className="m-0 mt-0.5 text-xs text-[var(--color-muted)] leading-tight">
              Catch scams before they catch you
            </p>
          </div>
        </div>

        <nav className="flex flex-row overflow-x-auto md:overflow-visible md:flex-col gap-2 pb-2 md:pb-0 hide-scrollbar -mx-4 px-4 md:mx-0 md:px-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => selectTab(t.id)}
              className={cn(
                "relative rounded-lg px-4 py-3 text-sm font-bold transition-colors text-left shrink-0 flex items-center justify-between gap-2 group",
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
              <div className="relative z-10 hidden md:flex items-center">
                <Info size={14} className="opacity-40 group-hover:opacity-100 transition-opacity" />
                <div className="absolute left-full ml-2 w-48 p-2 bg-[var(--color-ink)] text-[var(--color-surface)] text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                  {t.desc}
                </div>
              </div>
            </button>
          ))}
        </nav>

        <div className="mt-auto pt-8 flex flex-col gap-4">
          <div className="text-[13px] leading-normal text-[var(--color-muted)] hidden md:block">
            <p className="mb-3">Got something suspicious? Check it here and if it was a scam, tell us.</p>
            <p className="mb-3">Every report helps protect the next person.</p>
            <p>Powered by <b className="text-[var(--color-ink)]">Cognee</b>.</p>
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
