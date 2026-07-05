import React from "react";
import { Globe, ShieldCheck, MousePointerClick, Puzzle, ScanLine, ExternalLink, FolderCode, ToggleLeft } from "lucide-react";
const REPO_URL = "https://github.com/aniket-3001/Antibody";

const SETUP_STEPS = [
  {
    icon: ToggleLeft,
    title: "1. Turn on Developer mode",
    body: "In Chrome, go to chrome://extensions, then flip the Developer mode toggle in the top-right corner.",
  },
  {
    icon: FolderCode,
    title: "2. Load the extension folder",
    body: "Click 'Load unpacked' and select the 'extension' folder located inside this project's directory on your machine.",
  },
  {
    icon: Puzzle,
    title: "3. Pin it",
    body: "Antibody now shows up in your extensions list. Click the puzzle-piece icon in the toolbar and pin Antibody so it's one click away.",
  },
];

const USE_STEPS = [
  {
    icon: MousePointerClick,
    title: "Right-click any suspicious text",
    body: "Select a message, email, or comment on any page, right-click it, and choose “Check with Antibody.” A notification pops up with the verdict in seconds - nothing is sent anywhere unless you do this.",
  },
  {
    icon: ScanLine,
    title: "Or use the toolbar popup",
    body: "Click the Antibody icon to open a small panel - paste text and hit Check it, or hit Scan this page to pull in the visible text automatically.",
  },
  {
    icon: ExternalLink,
    title: "Open the full app for details",
    body: "The popup gives you a quick verdict. Click Open full app for the complete breakdown - highlighted tactics, citations from the knowledge graph, and the option to report it so it protects the next person.",
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
          Not on the Chrome Web Store yet - load it as an unpacked developer extension directly from your local folder (or <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="text-[var(--color-brand)] hover:underline">grab it from GitHub</a>).
        </p>
      </div>

      <div>
        <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--color-muted)] mb-3">Set it up (one-time)</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          {SETUP_STEPS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex flex-col gap-2 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-4">
              <div className="flex items-center gap-2 font-bold text-[var(--color-ink)]">
                <Icon size={18} className="text-[var(--color-brand)]" /> {title}
              </div>
              <p className="text-sm text-[var(--color-body)] leading-relaxed break-words">{body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-4 text-sm text-[var(--color-body)] leading-relaxed">
        <b className="text-[var(--color-ink)]">Local connection:</b> the extension talks to your local backend and web
        app. Since you're already running them locally (<code>uvicorn</code> and <code>npm run dev</code>), 
        just open the extension's popup and click <b>&#9881; Ports</b> to make sure the backend and web-app ports match your setup (defaults are <code>8000</code> and <code>5173</code>).
      </div>

      <div>
        <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--color-muted)] mb-3">Use it</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          {USE_STEPS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex flex-col gap-2 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-4">
              <div className="flex items-center gap-2 font-bold text-[var(--color-ink)]">
                <Icon size={18} className="text-[var(--color-brand)]" /> {title}
              </div>
              <p className="text-sm text-[var(--color-body)] leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
