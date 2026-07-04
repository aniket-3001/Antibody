import { useRef, useState } from "react";
import { checkMessage, submitOutcome, uploadFile } from "../api.js";

const EXAMPLES = [
  ["📦 Fake delivery fee", "USPS: Your package is on hold. A $2.99 redelivery fee is required. Pay now at http://usps-redelivery.com to reschedule delivery."],
  ["🏦 Bank OTP scam", "Your bank: suspicious login detected. Reply with the 6-digit code we just sent to confirm it's you, or your account will be suspended."],
  ["✅ A real 2FA code", "Your verification code is 448291. Do not share this code with anyone. — Google"],
];

const SIGNAL_LABELS = {
  indicator: "Known-bad link or number",
  semantic: "Sounds like reported scams",
  structural: "Uses the same tricks",
  corroboration: "Others reported it too",
  family: "How active this scam is",
};

function fmtDate(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    const days = Math.round((Date.now() - d.getTime()) / 86400000);
    if (days <= 0) return "today";
    if (days === 1) return "yesterday";
    return `${days} days ago`;
  } catch { return null; }
}

const SpeechRec =
  typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

const HL_LEGEND = [
  ["indicator", "Known-bad link/phone/wallet"],
  ["tactic", "Manipulation tactic"],
  ["lure", "Scam pretext"],
];

// Underlines the exact words that drove the verdict (indicators/tactics/lures)
// instead of only listing them separately. Spans are character offsets into `text`.
function renderHighlighted(text, highlights) {
  if (!highlights?.length) return text;
  const spans = [...highlights].sort((a, b) => a.start - b.start);
  const nodes = [];
  let pos = 0;
  for (const s of spans) {
    if (s.start < pos || s.end <= s.start) continue; // skip overlaps/invalid
    if (s.start > pos) nodes.push(text.slice(pos, s.start));
    nodes.push(
      <mark key={`${s.start}-${s.end}`} className={`hl-${s.kind}`} title={s.label}>
        {text.slice(s.start, s.end)}
      </mark>
    );
    pos = s.end;
  }
  if (pos < text.length) nodes.push(text.slice(pos));
  return nodes;
}

export default function CheckView() {
  const [text, setText] = useState("");
  const [channel, setChannel] = useState("sms");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [listening, setListening] = useState(false);
  const [v, setV] = useState(null);
  const [err, setErr] = useState("");
  const [outcome, setOutcome] = useState(null);

  const recogRef = useRef(null);
  const finalRef = useRef("");
  const fileRef = useRef(null);

  const run = async () => {
    if (!text.trim()) return;
    stopMic();
    const sent = text;
    setLoading(true); setErr(""); setV(null); setOutcome(null);
    try {
      const res = await checkMessage(sent, channel);
      setV({ ...res, checked_text: sent });
    } catch (e) { setErr(String(e.message || e)); }
    setLoading(false);
  };

  // ---- live mic (browser Web Speech API — no keys, no install) ----
  const stopMic = () => { try { recogRef.current?.stop(); } catch {} };
  const toggleMic = () => {
    if (!SpeechRec) return;
    if (listening) { stopMic(); return; }
    setErr("");
    const r = new SpeechRec();
    r.lang = "en-US"; r.interimResults = true; r.continuous = true;
    finalRef.current = text ? text.trim() + " " : "";
    r.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const seg = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalRef.current += seg + " ";
        else interim += seg;
      }
      setText((finalRef.current + interim).replace(/\s+/g, " ").trimStart());
    };
    r.onend = () => setListening(false);
    r.onerror = (ev) => { setListening(false); if (ev.error !== "aborted") setErr(`Mic: ${ev.error}`); };
    recogRef.current = r;
    r.start();
    setListening(true);
  };

  // ---- upload a recorded call clip / screenshot → server transcribes/OCRs ----
  const onFile = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    stopMic();
    setUploading(true); setErr(""); setV(null); setOutcome(null); setText("");
    try {
      const res = await uploadFile(f, channel);
      setV({ ...res, checked_text: res.transcript || "" });
      if (res.transcript) setText(res.transcript);
    } catch (er) { setErr(String(er.message || er)); }
    setUploading(false);
    e.target.value = "";
  };

  const record = async (o) => {
    if (!v?.report_id) return;
    try { await submitOutcome(v.report_id, o); setOutcome(o); } catch (e) { setErr(String(e)); }
  };

  return (
    <>
      <p className="tagline">
        Got a text, email, or call that feels off? <b>Paste it, say it, or upload a recording, screenshot, or PDF.</b> We'll tell you
        if it's a known scam, how to spot it, and what to do — and your report protects the next person.
      </p>

      <div className="card">
        <textarea
          placeholder="Paste the suspicious message here… or tap the mic and read it out."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <div className="voice-row">
          {SpeechRec && (
            <button className={`voice-btn ${listening ? "listening" : ""}`} onClick={toggleMic} type="button">
              <span className="ico">🎙️</span>{listening ? "Listening… tap to stop" : "Speak it"}
            </button>
          )}
          <button className="voice-btn" onClick={() => fileRef.current?.click()} type="button" disabled={uploading}>
            <span className="ico">📎</span>{uploading ? "Reading…" : "Upload a recording, screenshot, or PDF"}
          </button>
          <input
            ref={fileRef} type="file" accept="audio/*,image/*,application/pdf,.pdf"
            onChange={onFile} style={{ display: "none" }}
          />
          {listening && <span className="voice-hint"><span className="rec-dot" />recording your voice</span>}
          {uploading && <span className="voice-hint">transcribing… first run downloads the model, give it a moment</span>}
        </div>

        <div className="row">
          <select value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="sms">Text / SMS</option>
            <option value="email">Email</option>
            <option value="voice_call">Phone call</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
          <button className="btn btn-primary" onClick={run} disabled={loading || uploading || !text.trim()}>
            {loading ? "Checking…" : "Check it"}
          </button>
        </div>

        <div className="examples">
          <span className="try">Try one:</span>
          {EXAMPLES.map(([label, ex]) => (
            <span key={label} className="chip" onClick={() => { stopMic(); setText(ex); }}>{label}</span>
          ))}
        </div>
        {err && <div className="err">⚠ {err}</div>}
      </div>

      {v && <Verdict v={v} outcome={outcome} onOutcome={record} />}
    </>
  );
}

function Verdict({ v, outcome, onOutcome }) {
  const seen = fmtDate(v.first_seen);
  return (
    <div className={`verdict ${v.band}`}>
      <div className="verdict-head">
        <span className="verdict-emoji">{v.band_emoji}</span>
        <div>
          <div className="verdict-title">{v.band_label}</div>
          <div className="verdict-sub">
            {v.family_display ? (
              <>{v.family_display}{v.report_count ? ` · reported ${v.report_count}×` : ""}{seen ? ` · first seen ${seen}` : ""}</>
            ) : "We don't recognize this one yet — stay cautious and trust your gut."}
          </div>
        </div>
        <div className="conf-pill">
          <div className="n">{Math.round((v.confidence || 0) * 100)}%</div>
          <div className="l">sure</div>
        </div>
      </div>

      {v.checked_text && (
        <>
          <div className="section-label">
            {v.input_kind === "audio" ? "🎙️ What we heard"
              : v.input_kind === "document" ? "📄 What we read"
              : v.input_kind === "image" ? "🖼️ What we read"
              : "Message checked"}
          </div>
          <div className="transcript">{renderHighlighted(v.checked_text, v.highlights)}</div>
          {v.highlights?.length > 0 && (
            <div className="hl-legend">
              {HL_LEGEND.map(([kind, label]) => (
                <span className="litem" key={kind}>
                  <span className={`ldot hl-${kind}`} />{label}
                </span>
              ))}
            </div>
          )}
        </>
      )}

      {v.explanation && (
        <>
          <div className="section-label">
            What it is
            <span className={`source-tag ${v.explanation_source === "cognee_graph" ? "cognee" : ""}`}>
              {v.explanation_source === "cognee_graph" ? "from memory, cited" : "from our playbook"}
            </span>
          </div>
          <div className="explain">{v.explanation}</div>
          {v.citations?.length > 0 && (
            <div className="citations">
              {v.citations.slice(0, 3).map((c, i) => (
                <div key={i} className="cite">"{c.snippet}"</div>
              ))}
            </div>
          )}
        </>
      )}

      {v.signals && Object.keys(v.signals).length > 0 && (v.band !== "unrecognized") && (
        <>
          <div className="section-label">Why we think so</div>
          <div className="signals">
            {Object.entries(v.signals).map(([k, val]) => (
              <div className="signal" key={k}>
                <div className="top">
                  <span className="name">{SIGNAL_LABELS[k] || k}</span>
                  <span className="val">{Math.round(val * 100)}%</span>
                </div>
                <div className="bar"><span style={{ width: `${Math.round(val * 100)}%` }} /></div>
              </div>
            ))}
          </div>
        </>
      )}

      {v.shared_tactics?.length > 0 && (
        <>
          <div className="section-label">Seen elsewhere too</div>
          {v.shared_tactics.map((s, i) => (
            <div className="shared-item" key={i}>
              The <b>{s.tactic.replace(/_/g, " ")}</b> trick here also shows up in{" "}
              {s.also_used_by.map((f) => f.replace(/_/g, " ")).join(", ")}.
            </div>
          ))}
        </>
      )}

      {v.guidance && (
        <>
          <div className="section-label">What to do now</div>
          <div className="guidance">
            <GBlock cls="do" title="🛑 Do this" items={v.guidance.do_now} />
            <GBlock cls="report" title="📣 Report it" items={v.guidance.report_to} />
            <GBlock cls="recover" title="💜 If you already replied" items={v.guidance.recovery} />
          </div>
        </>
      )}

      <div className="outcome-row">
        {outcome ? (
          <span className="thanks">💜 Thank you — you just helped protect the next person.</span>
        ) : (
          <>
            <span className="lbl">Help others — what happened?</span>
            <button className="btn btn-ghost" onClick={() => onOutcome("confirmed_scam")}>It was a scam</button>
            <button className="btn btn-ghost" onClick={() => onOutcome("i_got_scammed")}>I got scammed</button>
            <button className="btn btn-ghost" onClick={() => onOutcome("actually_legit")}>It was legit</button>
          </>
        )}
      </div>
    </div>
  );
}

function GBlock({ cls, title, items }) {
  if (!items?.length) return null;
  return (
    <div className={`g-block ${cls}`}>
      <h4>{title}</h4>
      <ul>{items.map((it, i) => <li key={i}>{it}</li>)}</ul>
    </div>
  );
}
