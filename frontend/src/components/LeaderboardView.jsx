import { useEffect, useState } from "react";
import { Trophy, Star } from "lucide-react";
import { Card, CardContent } from "./ui/card.jsx";
import { Badge } from "./ui/badge.jsx";
import { getLeaderboard } from "../api.js";
import { getClientId } from "../lib/identity.js";

export default function LeaderboardView() {
  const [entries, setEntries] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    getLeaderboard(getClientId())
      .then((res) => setEntries(res.leaderboard || []))
      .catch((e) => setErr(String(e.message || e)));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <h2 className="text-2xl font-extrabold text-[var(--color-ink)] flex items-center justify-center gap-2">
          <Trophy className="text-[var(--color-warn)]" size={28} />
          Community Leaderboard
        </h2>
        <p className="mt-2 text-[15px] text-[var(--color-body)]">
          Top contributors keeping the collective immune system strong.
        </p>
      </div>

      {err && (
        <div className="rounded-lg bg-[var(--color-danger-bg)] p-3 text-sm text-[var(--color-danger)]">{err}</div>
      )}

      {entries === null && !err && (
        <div className="text-center text-sm text-[var(--color-muted)]">Loading…</div>
      )}

      {entries?.length === 0 && (
        <div className="text-center text-sm text-[var(--color-muted)]">
          No verified reports yet — be the first on the board.
        </div>
      )}

      <div className="grid gap-3">
        {entries?.map((entry) => (
          <Card key={entry.rank} className={`border ${entry.is_you ? 'border-[var(--color-brand)] bg-[var(--color-surface-2)] shadow-[var(--shadow-custom-sm)]' : 'border-[var(--color-line)]'}`}>
            <CardContent className="p-4 flex items-center gap-4">
              <div className="flex w-10 justify-center font-bold text-lg text-[var(--color-muted)]">
                #{entry.rank}
              </div>
              <div className="flex-1">
                <div className="font-bold text-[var(--color-ink)]">{entry.is_you ? "You" : entry.label}</div>
                <div className="text-xs text-[var(--color-body)] flex items-center gap-2 mt-1">
                  <span>{entry.verified} verified scams reported</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <div className="font-black text-[var(--color-brand)] flex items-center gap-1">
                  <Star size={14} /> {entry.points.toLocaleString()} pts
                </div>
                {entry.tier === "gold" && <Badge variant="warn" className="text-[10px] py-0">Gold Tier</Badge>}
                {entry.tier === "silver" && <Badge variant="secondary" className="text-[10px] py-0">Silver Tier</Badge>}
                {entry.tier === "bronze" && <Badge variant="safe" className="text-[10px] py-0">Bronze Tier</Badge>}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
