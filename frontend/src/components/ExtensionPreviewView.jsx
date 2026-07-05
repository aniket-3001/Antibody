import React from "react";
import { Globe, ShieldCheck, MousePointerClick, Puzzle, ScanLine, ExternalLink } from "lucide-react";
import { Card, CardContent } from "./ui/card.jsx";

const STEPS = [
  {
    icon: Puzzle,
    title: "1. Install & pin it",
    body: "Search “Antibody” on the Chrome Web Store, click Add to Chrome, then click the puzzle-piece icon in your toolbar and pin Antibody so it's always one click away.",
  },
  {
    icon: MousePointerClick,
    title: "2. Right-click any suspicious text",
    body: "Select a message, email, or comment on any page, right-click it, and choose “Check with Antibody.” A notification pops up with the verdict in seconds — nothing is sent anywhere unless you do this.",
  },
  {
    icon: ScanLine,
    title: "3. Or use the toolbar popup",
    body: "Click the Antibody icon to open a small panel — paste text and hit Check it, or hit Scan this page to pull in the visible text automatically.",
  },
  {
    icon: ExternalLink,
    title: "4. Open the full app for details",
    body: "The popup gives you a quick verdict. Click Open full app for the complete breakdown — highlighted tactics, citations from the knowledge graph, and the option to report it so it protects the next person.",
  },
];

export default function ExtensionPreviewView() {
  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <h2 className="text-2xl font-extrabold text-[var(--color-ink)] flex items-center justify-center gap-2">
          <Globe className="text-[#4285F4]" size={28} />
          Browser Extension
        </h2>
        <p className="mt-2 text-[15px] text-[var(--color-body)]">
          Check anything without leaving the page you're on — right-click selected text, or use the toolbar popup.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {STEPS.map(({ icon: Icon, title, body }) => (
          <div key={title} className="flex flex-col gap-2 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-4">
            <div className="flex items-center gap-2 font-bold text-[var(--color-ink)]">
              <Icon size={18} className="text-[var(--color-brand)]" /> {title}
            </div>
            <p className="text-sm text-[var(--color-body)] leading-relaxed">{body}</p>
          </div>
        ))}
      </div>

      <Card className="border border-[var(--color-line)] shadow-lg overflow-hidden bg-white">
        {/* Mock Browser Header */}
        <div className="bg-[#f1f3f4] p-2 flex items-center gap-2 border-b border-[#dadce0]">
          <div className="flex gap-1.5 ml-2">
            <div className="w-3 h-3 rounded-full bg-[#ff5f56]"></div>
            <div className="w-3 h-3 rounded-full bg-[#ffbd2e]"></div>
            <div className="w-3 h-3 rounded-full bg-[#27c93f]"></div>
          </div>
          <div className="flex-1 bg-white mx-4 rounded-full h-6 border border-[#dadce0] flex items-center px-3 text-[11px] text-[#5f6368]">
            mail.google.com
          </div>
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-[var(--color-brand-soft)] text-[var(--color-brand)] mr-2">
            <ShieldCheck size={14} />
          </div>
        </div>

        {/* Mock Email Body with a selection + right-click context menu open */}
        <CardContent className="p-0">
          <div className="p-6 flex flex-col gap-4 relative">
            <div>
              <h3 className="text-lg font-bold text-[#202124]">Action Required: Account Suspension Notice</h3>
              <div className="text-sm text-[#5f6368] mt-1">From: support@paypal-security-update.com</div>
            </div>
            <div className="text-sm text-[#202124] leading-relaxed relative">
              Dear Customer,<br/><br/>
              We detected unusual activity on your account. <span className="bg-[#cfe4ff]">Your account will be permanently suspended in 24 hours if you do not verify your identity.</span>
              <br/><br/>

              {/* Mock right-click context menu */}
              <div className="absolute top-10 left-10 w-64 bg-white border border-[#dadce0] rounded-md shadow-xl py-1 text-[13px] text-[#202124]">
                <div className="px-3 py-1.5 hover:bg-[#f1f3f4]">Copy</div>
                <div className="px-3 py-1.5 hover:bg-[#f1f3f4]">Search Google for "Your account..."</div>
                <div className="my-1 border-t border-[#dadce0]" />
                <div className="px-3 py-1.5 bg-[var(--color-brand-soft)] text-[var(--color-brand)] font-bold flex items-center gap-1.5">
                  <ShieldCheck size={14} /> Check with Antibody
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      <p className="-mt-2 text-center text-xs text-[var(--color-muted)]">
        What right-clicking selected text looks like once the extension is installed.
      </p>

      <div className="text-center text-sm text-[var(--color-muted)]">
        Look for <b className="text-[var(--color-ink)]">Antibody</b> in the Chrome Web Store to install it.
      </div>
    </div>
  );
}
