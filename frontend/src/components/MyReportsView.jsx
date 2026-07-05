import { useEffect, useState } from "react";
import { History, ShieldAlert, Clock, Smartphone, Mail, Phone, MessageSquare, FileText, Image as ImageIcon, Mic, Database, Loader2 } from "lucide-react";
import { Card, CardContent } from "./ui/card.jsx";
import { Badge } from "./ui/badge.jsx";
import { Modal } from "./ui/modal.jsx";
import { getMyReports, getReport, submitOutcome } from "../api.js";
import { getClientId } from "../lib/identity.js";
import { Verdict } from "./CheckView.jsx";

function fmtDate(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const days = Math.round((Date.now() - d.getTime()) / 86400000);
    if (days <= 0) return "today";
    if (days === 1) return "yesterday";
    return `${days} days ago`;
  } catch { return iso; }
}

const ChannelIcon = ({ channel, inputKind }) => {
  if (inputKind === "document") return <div className="flex items-center gap-1.5"><FileText size={14} className="text-[var(--color-brand)]" /> Document</div>;
  if (inputKind === "image") return <div className="flex items-center gap-1.5"><ImageIcon size={14} className="text-[var(--color-brand)]" /> Screenshot</div>;
  if (inputKind === "audio") return <div className="flex items-center gap-1.5"><Mic size={14} className="text-[var(--color-brand)]" /> Recording</div>;
  
  switch (channel) {
    case "sms": return <div className="flex items-center gap-1.5"><Smartphone size={14} className="text-[#3b82f6]" /> Text/SMS</div>;
    case "whatsapp": return <div className="flex items-center gap-1.5"><MessageSquare size={14} className="text-[#25D366]" /> WhatsApp</div>;
    case "voice_call": return <div className="flex items-center gap-1.5"><Phone size={14} className="text-[var(--color-brand)]" /> Call</div>;
    case "email": return <div className="flex items-center gap-1.5"><Mail size={14} className="text-[var(--color-warn)]" /> Email</div>;
    default: return <div className="flex items-center gap-1.5"><Smartphone size={14} className="text-[var(--color-muted)]" /> Message</div>;
  }
};

function KbStatus({ dataId }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-[var(--color-surface-2)] p-3 text-sm">
      <Database size={16} className={dataId ? "text-[var(--color-safe)]" : "text-[var(--color-muted)]"} />
      {dataId ? (
        <span className="text-[var(--color-ink)]">
          Stored in the knowledge graph <span className="text-[var(--color-muted)] font-mono text-xs">({dataId})</span> - future checks can draw on this report.
        </span>
      ) : (
        <span className="text-[var(--color-muted)]">
          Not yet in the knowledge graph - still processing in the background, or Cognee is unavailable right now (the verdict above still stands on its own).
        </span>
      )}
    </div>
  );
}

function ReportDetailModal({ reportId, onClose, onOutcomeChanged }) {
  const [detail, setDetail] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!reportId) return;
    setDetail(null);
    setErr("");
    getReport(reportId)
      .then((res) => setDetail({ ...res, checked_text: res.transcript || "" }))
      .catch((e) => setErr(String(e.message || e)));
  }, [reportId]);

  const recordOutcome = async (o) => {
    try {
      await submitOutcome(reportId, o);
      setDetail((d) => ({ ...d, outcome: o }));
      onOutcomeChanged?.();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  return (
    <Modal isOpen={!!reportId} onClose={onClose} title="Report details" className="max-w-2xl">
      <div className="max-h-[70vh] overflow-y-auto -m-6 p-6 flex flex-col gap-4">
        {err && <div className="rounded-lg bg-[var(--color-danger-bg)] p-3 text-sm text-[var(--color-danger)]">{err}</div>}
        {!detail && !err && (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-[var(--color-muted)]">
            <Loader2 size={16} className="animate-spin" /> Loading…
          </div>
        )}
        {detail && (
          <>
            <Verdict v={detail} outcome={detail.outcome} onOutcome={recordOutcome} />
            <KbStatus dataId={detail.cognee_data_id} />
          </>
        )}
      </div>
    </Modal>
  );
}

export default function MyReportsView() {
  const [reports, setReports] = useState(null);
  const [err, setErr] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  const load = () => {
    getMyReports(getClientId())
      .then((res) => setReports(res.reports || []))
      .catch((e) => setErr(String(e.message || e)));
  };

  useEffect(load, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <h2 className="text-2xl font-extrabold text-[var(--color-ink)] flex items-center justify-center gap-2">
          <History className="text-[var(--color-brand)]" size={28} />
          My Reports
        </h2>
        <p className="mt-2 text-[15px] text-[var(--color-body)]">
          Your personal history of submitted threats, tied to this browser.
        </p>
      </div>

      {err && (
        <div className="rounded-lg bg-[var(--color-danger-bg)] p-3 text-sm text-[var(--color-danger)]">{err}</div>
      )}

      {reports === null && !err && (
        <div className="text-center text-sm text-[var(--color-muted)]">Loading…</div>
      )}

      {reports?.length === 0 && (
        <div className="text-center text-sm text-[var(--color-muted)]">
          You haven't submitted anything from this browser yet - check a message to get started.
        </div>
      )}

      <div className="grid gap-4">
        {reports?.map((report) => (
          <Card
            key={report.id}
            onClick={() => setSelectedId(report.id)}
            className="border border-[var(--color-line)] shadow-sm cursor-pointer transition-colors hover:border-[var(--color-brand)] hover:bg-[var(--color-surface-2)]/40"
          >
            <CardContent className="p-4 flex flex-col gap-3">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3 text-xs text-[var(--color-muted)] font-medium">
                  <span className="flex items-center gap-1"><Clock size={14} /> {fmtDate(report.date)}</span>
                  <span className="text-[var(--color-line)]">|</span>
                  <ChannelIcon channel={report.channel} inputKind={report.input_kind} />
                </div>
                {report.status === "confirmed" ? (
                  <Badge variant="danger" className="gap-1"><ShieldAlert size={12}/> Verified Scam</Badge>
                ) : report.status === "legit" ? (
                  <Badge variant="safe" className="gap-1">Marked Legit</Badge>
                ) : (
                  <Badge variant="secondary" className="gap-1"><Clock size={12}/> Processing</Badge>
                )}
              </div>
              <div className="text-[14px] text-[var(--color-ink)] font-medium leading-relaxed bg-[var(--color-surface-2)] p-3 rounded-lg border border-[var(--color-line)]">
                "{report.text}"
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-[var(--color-body)] font-medium">Immunity Points Earned:</span>
                <span className={`font-bold ${report.status === "confirmed" ? 'text-[var(--color-safe)]' : 'text-[var(--color-muted)]'}`}>
                  {report.points}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <ReportDetailModal
        reportId={selectedId}
        onClose={() => setSelectedId(null)}
        onOutcomeChanged={load}
      />
    </div>
  );
}
