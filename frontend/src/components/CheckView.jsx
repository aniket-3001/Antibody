import { useRef, useState } from "react";
import { Mic, Paperclip, AlertTriangle, ShieldCheck, Info, UploadCloud } from "lucide-react";
import { checkMessage, submitOutcome, uploadFile } from "../api.js";
import { Button } from "./ui/button.jsx";
import { Card, CardContent } from "./ui/card.jsx";
import { Textarea } from "./ui/textarea.jsx";
import { Badge } from "./ui/badge.jsx";
import { cn } from "../lib/utils.js";

const EXAMPLES = [
  ["Fake delivery fee", "USPS: Your package is on hold. A $2.99 redelivery fee is required. Pay now at http://usps-redelivery.com to reschedule delivery."],
  ["Bank OTP scam", "Your bank: suspicious login detected. Reply with the 6-digit code we just sent to confirm it's you, or your account will be suspended."],
  ["A real 2FA code", "Your verification code is 448291. Do not share this code with anyone. — Google"],
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
  ["indicator", "Known-bad link/phone/wallet", "bg-[var(--color-danger-line)]"],
  ["tactic", "Manipulation tactic", "bg-[var(--color-warn-line)]"],
  ["lure", "Scam pretext", "bg-[var(--color-calm-line)]"],
];

function renderHighlighted(text, highlights) {
  if (!highlights?.length) return text;
  const spans = [...highlights].sort((a, b) => a.start - b.start);
  const nodes = [];
  let pos = 0;
  for (const s of spans) {
    if (s.start < pos || s.end <= s.start) continue; 
    if (s.start > pos) nodes.push(text.slice(pos, s.start));
    
    let hlClass = "bg-[var(--color-warn-line)]";
    if (s.kind === "indicator") hlClass = "bg-[var(--color-danger-line)]";
    if (s.kind === "lure") hlClass = "bg-[var(--color-calm-line)]";
    
    nodes.push(
      <mark key={`${s.start}-${s.end}`} className={cn("rounded-sm px-1 py-0.5", hlClass)} title={s.label}>
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
    <div className="flex flex-col gap-6">
      <p className="text-center text-[15px] leading-relaxed text-[var(--color-body)] px-2">
        Got a text, email, or call that feels off? <b className="text-[var(--color-ink)]">Paste it, say it, or upload a recording, screenshot, or PDF.</b> We'll tell you
        if it's a known scam, how to spot it, and what to do — and your report protects the next person.
      </p>

      <Card>
        <CardContent className="pt-6 flex flex-col gap-4">
          <Textarea
            placeholder="Paste the suspicious message here… or tap the mic and read it out."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />

          <div className="flex flex-wrap items-center gap-3">
            {SpeechRec && (
              <Button 
                variant="secondary" 
                size="sm" 
                className={cn("gap-2", listening && "bg-[var(--color-danger-bg)] text-[var(--color-danger)] hover:bg-[var(--color-danger-line)]")}
                onClick={toggleMic}
              >
                <Mic size={16} className={listening ? "animate-pulse" : ""} />
                {listening ? "Listening… tap to stop" : "Speak it"}
              </Button>
            )}
            <Button variant="secondary" size="sm" className="gap-2" onClick={() => fileRef.current?.click()} disabled={uploading}>
              {uploading ? <UploadCloud size={16} className="animate-bounce" /> : <Paperclip size={16} />}
              {uploading ? "Reading…" : "Upload file"}
            </Button>
            <input ref={fileRef} type="file" accept="audio/*,image/*,application/pdf,.pdf" onChange={onFile} className="hidden" />
          </div>

          <div className="flex items-center gap-3 mt-2">
            <select 
              value={channel} 
              onChange={(e) => setChannel(e.target.value)}
              className="h-10 rounded-full border border-[var(--color-line)] bg-[var(--color-surface-2)] px-4 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]"
            >
              <option value="sms">Text / SMS</option>
              <option value="email">Email</option>
              <option value="voice_call">Phone call</option>
              <option value="whatsapp">WhatsApp</option>
            </select>
            <Button onClick={run} disabled={loading || uploading || !text.trim()} className="flex-1">
              {loading ? "Checking…" : "Check it"}
            </Button>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-[var(--color-muted)]">
            <span className="font-medium">Try one:</span>
            {EXAMPLES.map(([label, ex]) => (
              <Badge 
                key={label} 
                variant="secondary" 
                className="cursor-pointer font-normal" 
                onClick={() => { stopMic(); setText(ex); }}
              >
                {label}
              </Badge>
            ))}
          </div>
          {err && (
            <div className="mt-2 flex items-center gap-2 rounded-lg bg-[var(--color-danger-bg)] p-3 text-sm text-[var(--color-danger)]">
              <AlertTriangle size={16} /> {err}
            </div>
          )}
        </CardContent>
      </Card>

      {v && <Verdict v={v} outcome={outcome} onOutcome={record} />}
    </div>
  );
}

function Verdict({ v, outcome, onOutcome }) {
  const seen = fmtDate(v.first_seen);
  
  let bandColorClass = "bg-[var(--color-surface-2)] border-[var(--color-line)] text-[var(--color-ink)]";
  if (v.band === "confirmed") bandColorClass = "bg-[var(--color-danger-bg)] border-[var(--color-danger-line)] text-[var(--color-danger)]";
  if (v.band === "likely" || v.band === "suspicious") bandColorClass = "bg-[var(--color-warn-bg)] border-[var(--color-warn-line)] text-[var(--color-warn)]";
  if (v.band === "unrecognized") bandColorClass = "bg-[var(--color-calm-bg)] border-[var(--color-calm-line)] text-[var(--color-calm)]";
  if (v.band === "safe") bandColorClass = "bg-[var(--color-safe-bg)] border-[var(--color-safe-line)] text-[var(--color-safe)]";

  return (
    <Card className={cn("overflow-hidden border-2", bandColorClass.split(" ")[1])}>
      <div className={cn("p-6 pb-4", bandColorClass)}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="text-4xl">{v.band_emoji}</div>
            <div>
              <h2 className="text-xl font-bold tracking-tight">{v.band_label}</h2>
              <div className="mt-1 text-sm opacity-90">
                {v.family_display ? (
                  <>{v.family_display}{v.report_count ? ` · reported ${v.report_count}×` : ""}{seen ? ` · first seen ${seen}` : ""}</>
                ) : "We don't recognize this one yet — stay cautious and trust your gut."}
              </div>
            </div>
          </div>
          <div className="flex flex-col items-center justify-center rounded-xl bg-[var(--color-surface-2)]/60 px-3 py-1.5 backdrop-blur-md">
            <span className="text-2xl font-black leading-none">{Math.round((v.confidence || 0) * 100)}%</span>
            <span className="text-xs font-bold uppercase tracking-wider opacity-80">sure</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6 p-6">
        {v.checked_text && (
          <div className="flex flex-col gap-2">
            <div className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">
              {v.input_kind === "audio" ? "🎙️ What we heard"
                : v.input_kind === "document" ? "📄 What we read"
                : v.input_kind === "image" ? "🖼️ What we read"
                : "Message checked"}
            </div>
            <div className="rounded-lg bg-[var(--color-surface-2)] p-4 text-[15px] leading-relaxed text-[var(--color-ink)]">
              {renderHighlighted(v.checked_text, v.highlights)}
            </div>
            {v.highlights?.length > 0 && (
              <div className="flex gap-4 text-xs font-medium text-[var(--color-muted)]">
                {HL_LEGEND.map(([kind, label, color]) => (
                  <div className="flex items-center gap-1.5" key={kind}>
                    <div className={cn("h-2.5 w-2.5 rounded-full", color)} />{label}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {v.explanation && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">
              What it is
              <Badge variant="outline" className="text-[10px] uppercase">
                {v.explanation_source === "cognee_graph" ? "from memory" : "from playbook"}
              </Badge>
            </div>
            <div className="text-[15px] leading-relaxed text-[var(--color-ink)]">{v.explanation}</div>
            {v.citations?.length > 0 && (
              <div className="mt-2 flex flex-col gap-2 border-l-2 border-[var(--color-line)] pl-3">
                {v.citations.slice(0, 3).map((c, i) => (
                  <div key={i} className="text-sm italic text-[var(--color-muted)]">"{c.snippet}"</div>
                ))}
              </div>
            )}
          </div>
        )}

        {v.signals && Object.keys(v.signals).length > 0 && (v.band !== "unrecognized") && (
          <div className="flex flex-col gap-2">
            <div className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">Why we think so</div>
            <div className="flex flex-col gap-3">
              {Object.entries(v.signals).map(([k, val]) => (
                <div className="flex flex-col gap-1" key={k}>
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-[var(--color-ink)]">{SIGNAL_LABELS[k] || k}</span>
                    <span className="text-[var(--color-muted)]">{Math.round(val * 100)}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--color-line)]">
                    <div className="h-full bg-[var(--color-brand)] transition-all" style={{ width: `${Math.round(val * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {v.shared_tactics?.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">Seen elsewhere too</div>
            {v.shared_tactics.map((s, i) => (
              <div className="rounded-lg bg-[var(--color-surface-2)] p-3 text-sm text-[var(--color-ink)]" key={i}>
                The <b className="font-semibold">{s.tactic.replace(/_/g, " ")}</b> trick here also shows up in{" "}
                {s.also_used_by.map((f) => f.replace(/_/g, " ")).join(", ")}.
              </div>
            ))}
          </div>
        )}

        {v.guidance && (
          <div className="flex flex-col gap-3">
            <div className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">What to do now</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <GBlock icon="🛑" title="Do this" items={v.guidance.do_now} />
              <GBlock icon="📣" title="Report it" items={v.guidance.report_to} />
              <GBlock icon="💜" title="If you already replied" items={v.guidance.recovery} cls="sm:col-span-2" />
            </div>
          </div>
        )}

        <div className="mt-4 rounded-xl bg-[var(--color-surface-2)] p-4 text-center">
          {outcome ? (
            <span className="font-semibold text-[var(--color-brand)]">💜 Thank you — you just helped protect the next person.</span>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <span className="text-sm font-semibold text-[var(--color-muted)]">Help others — what happened?</span>
              <div className="flex flex-wrap justify-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => onOutcome("confirmed_scam")}>It was a scam</Button>
                <Button variant="ghost" size="sm" onClick={() => onOutcome("i_got_scammed")}>I got scammed</Button>
                <Button variant="ghost" size="sm" onClick={() => onOutcome("actually_legit")}>It was legit</Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

function GBlock({ icon, title, items, cls }) {
  if (!items?.length) return null;
  return (
    <div className={cn("rounded-lg border border-[var(--color-line)] bg-[var(--color-surface)] p-4", cls)}>
      <h4 className="mb-2 flex items-center gap-2 text-sm font-bold text-[var(--color-ink)]">
        <span>{icon}</span> {title}
      </h4>
      <ul className="m-0 flex flex-col gap-1.5 pl-0 text-sm text-[var(--color-body)]">
        {items.map((it, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-brand)]" />
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
