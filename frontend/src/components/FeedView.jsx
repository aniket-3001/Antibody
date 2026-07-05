import { useEffect, useState } from "react";
import { Activity, AlertTriangle, ShieldAlert, Zap } from "lucide-react";
import { getFeed } from "../api.js";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card.jsx";
import { Badge } from "./ui/badge.jsx";

const BAND_COLOR = {
  confirmed_scam: "bg-[var(--color-danger)]",
  i_got_scammed: "bg-[var(--color-danger)]",
  actually_legit: "bg-[var(--color-calm)]",
};

export default function FeedView() {
  const [feed, setFeed] = useState(null);
  const [err, setErr] = useState("");

  const load = () => getFeed().then(setFeed).catch((e) => setErr(String(e.message || e)));

  useEffect(() => {
    load();
    const t = setInterval(load, 5000); // live â€” polls every 5s
    return () => clearInterval(t);
  }, []);

  if (err) {
    return (
      <div className="mx-auto flex max-w-[760px] items-center gap-2 rounded-lg bg-[var(--color-danger-bg)] p-4 text-[var(--color-danger)]">
        <AlertTriangle size={18} /> {err}
      </div>
    );
  }

  if (!feed) {
    return (
      <div className="flex animate-pulse flex-col items-center gap-3 pt-12 text-[var(--color-muted)]">
        <Activity size={32} className="animate-spin opacity-50" />
        <div className="font-medium">Loading what's going aroundâ€¦</div>
      </div>
    );
  }

  const maxCount = Math.max(1, ...feed.families.map((f) => f.count));

  return (
    <div className="flex flex-col gap-6">
      <p className="px-2 text-center text-[15px] leading-relaxed text-[var(--color-body)]">
        Here's what people are reporting right now. <b className="text-[var(--color-ink)]">The more we share, the faster everyone spots the next one.</b>{" "}
        This updates live as new reports come in.
      </p>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "total reports", n: feed.total_reports },
          { label: "scam types", n: feed.families.length },
          { label: "shared tricks", n: feed.shared_tactics.length },
          { label: "new & rising", n: feed.emerging.length },
        ].map((s) => (
          <Card key={s.label} className="border-none bg-[var(--color-surface-2)] shadow-sm">
            <CardContent className="flex flex-col items-center justify-center p-4">
              <span className="text-3xl font-black text-[var(--color-brand)]">{s.n}</span>
              <span className="mt-1 text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">{s.label}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      {feed.emerging.length > 0 && (
        <Card className="border-[var(--color-warn-line)] bg-[var(--color-warn-bg)] text-[var(--color-warn)]">
          <CardContent className="p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--color-warn)] opacity-75"></span>
                <span className="relative inline-flex h-3 w-3 rounded-full bg-[var(--color-warn)]"></span>
              </span>
              New scams picking up right now
            </h3>
            <div className="flex flex-col gap-2">
              {feed.emerging.map((e) => (
                <div className="text-sm font-medium" key={e.name}>
                  <b className="font-bold">{e.display}</b> â€” first seen {e.emerged_hours_ago}h ago, {e.count} reports and climbing.
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">Most reported</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {feed.families.map((f) => (
              <div className="flex items-center gap-3 text-sm" key={f.name}>
                <span className="w-[120px] shrink-0 truncate font-semibold text-[var(--color-ink)]" title={f.display}>{f.display}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--color-line)]">
                  <div className="h-full rounded-full bg-[var(--color-brand)] transition-all" style={{ width: `${Math.round((f.count / maxCount) * 100)}%` }} />
                </div>
                <span className="w-8 shrink-0 text-right font-bold text-[var(--color-muted)]">{f.count}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">Same tricks, different scams</CardTitle>
            <p className="mt-1 text-xs font-medium text-[var(--color-muted)]">
              The same tactic often shows up across different scams â€” learn it once, spot it everywhere.
            </p>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {feed.shared_tactics.map((s) => (
              <div className="flex flex-col gap-1.5" key={s.tactic}>
                <div className="text-[13px] font-bold text-[var(--color-ink)]">{s.tactic.replace(/_/g, " ")}</div>
                <div className="flex flex-wrap gap-1.5">
                  {s.families.map((f) => (
                    <Badge variant="secondary" className="font-normal opacity-80" key={f}>
                      {f.replace(/_/g, " ")}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">Recent reports</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-0 divide-y divide-[var(--color-line)]">
          {feed.recent.map((r) => (
            <div className="flex items-start gap-3 py-3" key={r.id}>
              <div className="mt-1 flex h-4 w-4 shrink-0 items-center justify-center">
                <span className={`h-2.5 w-2.5 rounded-full ${BAND_COLOR[r.outcome] || "bg-[var(--color-muted)]"}`} />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="font-bold text-[var(--color-ink)]">{r.family ? r.family.replace(/_/g, " ") : "unrecognized"}</span>
                  <span className="text-[var(--color-muted)]">Â·</span>
                  <span className="uppercase text-[var(--color-muted)]">{r.channel || "sms"}</span>
                </div>
                <div className="mt-1 line-clamp-2 text-sm text-[var(--color-body)]">{r.preview}</div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
