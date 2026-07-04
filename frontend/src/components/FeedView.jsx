import { useEffect, useState } from "react";
import { getFeed } from "../api.js";

const BAND_COLOR = {
  confirmed_scam: "var(--confirmed)",
  i_got_scammed: "var(--confirmed)",
  actually_legit: "var(--unrecognized)",
};

export default function FeedView() {
  const [feed, setFeed] = useState(null);
  const [err, setErr] = useState("");

  const load = () => getFeed().then(setFeed).catch((e) => setErr(String(e.message || e)));

  useEffect(() => {
    load();
    const t = setInterval(load, 5000); // live — polls every 5s
    return () => clearInterval(t);
  }, []);

  if (err) return <div className="err">⚠ {err}</div>;
  if (!feed) return <div className="loading">Loading what's going around…</div>;

  const maxCount = Math.max(1, ...feed.families.map((f) => f.count));

  return (
    <>
      <p className="tagline">
        Here's what people are reporting right now. <b>The more we share, the faster everyone spots the next one.</b>{" "}
        This updates live as new reports come in.
      </p>

      <div className="stats">
        <div className="stat"><div className="n">{feed.total_reports}</div><div className="l">total reports</div></div>
        <div className="stat"><div className="n">{feed.families.length}</div><div className="l">scam types</div></div>
        <div className="stat"><div className="n">{feed.shared_tactics.length}</div><div className="l">shared tricks</div></div>
        <div className="stat"><div className="n">{feed.emerging.length}</div><div className="l">new & rising</div></div>
      </div>

      {feed.emerging.length > 0 && (
        <div className="emerging">
          <h3><span className="pulse" /> 🆕 New scams picking up right now</h3>
          {feed.emerging.map((e) => (
            <div className="emerge-item" key={e.name}>
              <b>{e.display}</b> — first seen {e.emerged_hours_ago}h ago, {e.count} reports and climbing.
            </div>
          ))}
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <div className="section-label" style={{ marginTop: 0 }}>Most reported</div>
          {feed.families.map((f) => (
            <div className="fam-row" key={f.name}>
              <span className="name">{f.display}</span>
              <span className="track"><span style={{ width: `${Math.round((f.count / maxCount) * 100)}%` }} /></span>
              <span className="count">{f.count}</span>
            </div>
          ))}
        </div>

        <div className="card tactic-map">
          <div className="section-label" style={{ marginTop: 0 }}>Same tricks, different scams</div>
          <p className="muted" style={{ fontSize: 12.5, marginTop: 0 }}>
            The same tactic often shows up across different scams — learn it once, spot it everywhere.
          </p>
          {feed.shared_tactics.map((s) => (
            <div className="tm-row" key={s.tactic}>
              <div className="tm-tactic">{s.tactic.replace(/_/g, " ")}</div>
              <div className="tm-fams">
                {s.families.map((f) => <span className="tag shared" key={f}>{f.replace(/_/g, " ")}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card recent">
        <div className="section-label" style={{ marginTop: 0 }}>Recent reports</div>
        {feed.recent.map((r) => (
          <div className="r-item" key={r.id}>
            <span className="dot" style={{ background: BAND_COLOR[r.outcome] || "var(--muted)" }} />
            <div>
              <span className="r-fam">{r.family ? r.family.replace(/_/g, " ") : "unrecognized"}</span>
              <span className="muted"> · {r.channel || "sms"}</span>
              <div className="r-text">{r.preview}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
