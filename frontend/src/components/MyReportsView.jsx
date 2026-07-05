import React from "react";
import { History, CheckCircle, ShieldAlert, Clock, Smartphone, Mail, Phone, MessageSquare } from "lucide-react";
import { Card, CardContent } from "./ui/card.jsx";
import { Badge } from "./ui/badge.jsx";

const MY_REPORTS = [
  { id: 1, date: "2 hours ago", text: "USPS: Your package is on hold. A $2.99 redelivery fee is required...", status: "confirmed", points: "+50", channel: "sms" },
  { id: 2, date: "Yesterday", text: "Your bank: suspicious login detected. Reply with the 6-digit code...", status: "confirmed", points: "+50", channel: "sms" },
  { id: 3, date: "3 days ago", text: "Hey it's mum I lost my phone, text me on this new number", status: "pending", points: "Pending", channel: "whatsapp" },
  { id: 4, date: "1 week ago", text: "Immediate action required: Your account is suspended. Call us.", status: "confirmed", points: "+50", channel: "voice_call" },
  { id: 5, date: "2 weeks ago", text: "Invoice #99281 attached. Please remit payment.", status: "confirmed", points: "+50", channel: "email" },
];

const ChannelIcon = ({ channel }) => {
  switch (channel) {
    case "sms": return <div className="flex items-center gap-1.5"><Smartphone size={14} className="text-[#3b82f6]" /> Text/SMS</div>;
    case "whatsapp": return <div className="flex items-center gap-1.5"><MessageSquare size={14} className="text-[#25D366]" /> WhatsApp</div>;
    case "voice_call": return <div className="flex items-center gap-1.5"><Phone size={14} className="text-[var(--color-brand)]" /> Call</div>;
    case "email": return <div className="flex items-center gap-1.5"><Mail size={14} className="text-[var(--color-warn)]" /> Email</div>;
    default: return null;
  }
};

export default function MyReportsView() {
  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <h2 className="text-2xl font-extrabold text-[var(--color-ink)] flex items-center justify-center gap-2">
          <History className="text-[var(--color-brand)]" size={28} />
          My Reports
        </h2>
        <p className="mt-2 text-[15px] text-[var(--color-body)]">
          Your personal history of submitted threats.
        </p>
      </div>

      <div className="grid gap-4">
        {MY_REPORTS.map((report) => (
          <Card key={report.id} className="border border-[var(--color-line)] shadow-sm">
            <CardContent className="p-4 flex flex-col gap-3">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3 text-xs text-[var(--color-muted)] font-medium">
                  <span className="flex items-center gap-1"><Clock size={14} /> {report.date}</span>
                  <span className="text-[var(--color-line)]">|</span>
                  <ChannelIcon channel={report.channel} />
                </div>
                {report.status === "confirmed" ? (
                  <Badge variant="danger" className="gap-1"><ShieldAlert size={12}/> Verified Scam</Badge>
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
    </div>
  );
}
