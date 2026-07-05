import { useEffect, useRef, useState } from "react";
import { Send, LifeBuoy, Loader2, AlertTriangle } from "lucide-react";
import { askHelp } from "../api.js";
import { Button } from "./ui/button.jsx";
import { cn } from "../lib/utils.js";

const STARTERS = [
  "What does each verdict band mean?",
  "Why is my leaderboard empty?",
  "How do I remove a false-positive report?",
  "What does the browser extension actually send?",
];

function Bubble({ turn }) {
  const isUser = turn.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed",
          isUser
            ? "bg-[var(--color-brand)] text-[var(--color-surface)] rounded-br-sm"
            : "bg-[var(--color-surface-2)] text-[var(--color-ink)] rounded-bl-sm"
        )}
      >
        <div className="whitespace-pre-wrap">{turn.content}</div>
        {turn.citations?.length > 0 && (
          <div className="mt-3 flex flex-col gap-2 border-l-2 border-[var(--color-line)] pl-3">
            {turn.citations.slice(0, 3).map((c, i) => (
              <div key={i} className="text-sm italic text-[var(--color-muted)]">
                "{c.snippet}"{c.doc ? <span className="not-italic opacity-70"> — {c.doc}</span> : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function HelpView() {
  const [turns, setTurns] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, busy]);

  const send = async (question) => {
    const q = (question ?? input).trim();
    if (!q || busy) return;
    setErr("");
    setInput("");
    const history = turns.map(({ role, content }) => ({ role, content }));
    setTurns((t) => [...t, { role: "user", content: q }]);
    setBusy(true);
    try {
      const res = await askHelp(q, history);
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          content: res.answer || "I don't have anything on that yet — try rephrasing, or check the docs directly.",
          citations: res.citations,
        },
      ]);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto flex h-[70vh] max-w-2xl flex-col gap-4">
      <div className="flex items-center gap-2">
        <LifeBuoy size={18} className="text-[var(--color-brand)]" />
        <div className="text-sm font-bold uppercase tracking-wider text-[var(--color-muted)]">
          Ask about Antibody
        </div>
      </div>

      <div className="flex-1 overflow-y-auto rounded-xl border border-[var(--color-line)] bg-[var(--color-surface)] p-4">
        {turns.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <p className="text-sm text-[var(--color-muted)]">
              Ask how a feature works, or paste an error you're seeing.
            </p>
            <div className="flex flex-col gap-2">
              {STARTERS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-lg border border-[var(--color-line)] px-3 py-2 text-sm text-[var(--color-ink)] hover:bg-[var(--color-surface-2)]"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-3">
          {turns.map((t, i) => (
            <Bubble key={i} turn={t} />
          ))}
          {busy && (
            <div className="flex items-center gap-2 text-sm text-[var(--color-muted)]">
              <Loader2 size={14} className="animate-spin" /> thinking…
            </div>
          )}
        </div>
        <div ref={endRef} />
      </div>

      {err && (
        <div className="flex items-center gap-2 rounded-lg bg-[var(--color-danger-bg)] p-3 text-sm text-[var(--color-danger)]">
          <AlertTriangle size={16} /> Couldn't reach the Help service — is it running? ({err})
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 rounded-full border border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-2 text-[15px] text-[var(--color-ink)] outline-none focus:border-[var(--color-brand)]"
        />
        <Button type="submit" size="icon" disabled={busy || !input.trim()}>
          <Send size={16} />
        </Button>
      </form>
    </div>
  );
}
