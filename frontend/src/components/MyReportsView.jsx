import { useEffect, useState } from "react";
import { History, ShieldAlert, Clock, Smartphone, Mail, Phone, MessageSquare, FileText, Image as ImageIcon, Mic, Search } from "lucide-react";
import { Card, CardContent } from "./ui/card.jsx";
import { Badge } from "./ui/badge.jsx";
import { loadHistory } from "../lib/history.js";

const BAND_POINTS = { confirmed: 50, likely: 35, suspicious: 20, unrecognized: 10 };

function fmtDate(iso) {
  try {
    const d = new Date(iso);
    const days = Math.floor((Date.now() - d.getTime()) / 86400000);
    if (days <= 0) {
      const hrs = Math.floor((Date.now() - d.getTime()) / 3600000);
      if (hrs <= 0) return "just now";
      return `${hrs}h ago`;
    }
    if (days === 1) return "yesterday";
    return `${days} days ago`;
  } catch { return ""; }
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

export default function MyReportsView() {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    setReports(loadHistory());
  }, []);

  if (reports.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center text-[var(--color-muted)]">
        <Search size={32} className="opacity-50" />
        <div className="font-medium">You haven't checked anything yet.</div>
        <p className="max-w-sm text-sm">
          Reports you check on the "Check a message" tab will show up here — this is
          only stored on this device.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <h2 className="text-2xl font-extrabold text-[var(--color-ink)] flex items-center justify-center gap-2">
          <History className="text-[var(--color-brand)]" size={28} />
          My Reports
        </h2>
        <p className="mt-2 text-[15px] text-[var(--color-body)]">
          Your personal history of submitted checks, on this device.
        </p>
      </div>

      <div className="grid gap-4">
        {reports.map((report) => {
          const points = BAND_POINTS[report.band] ?? 10;
          const confirmed = report.outcome === "confirmed_scam" || report.outcome === "i_got_scammed";
          return (
            <Card key={report.report_id} className="border border-[var(--color-line)] shadow-sm">
              <CardContent className="p-4 flex flex-col gap-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3 text-xs text-[var(--color-muted)] font-medium">
                    <span className="flex items-center gap-1"><Clock size={14} /> {fmtDate(report.added_at)}</span>
                    <span className="text-[var(--color-line)]">|</span>
                    <ChannelIcon channel={report.channel} inputKind={report.input_kind} />
                  </div>
                  {confirmed ? (
                    <Badge variant="danger" className="gap-1"><ShieldAlert size={12} /> Verified Scam</Badge>
                  ) : report.outcome === "actually_legit" ? (
                    <Badge variant="secondary" className="gap-1">Marked legit</Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1">{report.band_emoji} {report.band_label}</Badge>
                  )}
                </div>
                <div className="text-[14px] text-[var(--color-ink)] font-medium leading-relaxed bg-[var(--color-surface-2)] p-3 rounded-lg border border-[var(--color-line)] line-clamp-3">
                  "{report.text}"
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-[var(--color-body)] font-medium">
                    {report.family_display || "Not recognized"}
                  </span>
                  <span className={`font-bold ${report.outcome ? "text-[var(--color-safe)]" : "text-[var(--color-muted)]"}`}>
                    {report.outcome ? `+${points} pts` : "Pending feedback"}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
