import React from "react";
import { Trophy, Medal, Star } from "lucide-react";
import { Card, CardContent } from "./ui/card.jsx";
import { Badge } from "./ui/badge.jsx";

const LEADERBOARD_DATA = [
  { rank: 1, user: "Alex_Guardian", points: 15420, verified: 312, tier: "gold" },
  { rank: 2, user: "ScamHunter99", points: 12150, verified: 245, tier: "gold" },
  { rank: 3, user: "CyberShield_01", points: 10400, verified: 198, tier: "silver" },
  { rank: 4, user: "PatrolBot_Human", points: 9200, verified: 175, tier: "silver" },
  { rank: 5, user: "You (Anonymous)", points: 850, verified: 12, tier: "bronze" },
];

export default function LeaderboardView() {
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

      <div className="grid gap-3">
        {LEADERBOARD_DATA.map((entry) => (
          <Card key={entry.rank} className={`border ${entry.user.includes('You') ? 'border-[var(--color-brand)] bg-[var(--color-surface-2)] shadow-[var(--shadow-custom-sm)]' : 'border-[var(--color-line)]'}`}>
            <CardContent className="p-4 flex items-center gap-4">
              <div className="flex w-10 justify-center font-bold text-lg text-[var(--color-muted)]">
                #{entry.rank}
              </div>
              <div className="flex-1">
                <div className="font-bold text-[var(--color-ink)]">{entry.user}</div>
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
