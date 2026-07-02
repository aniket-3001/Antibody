# MemoryOS — Frontend UX Specification

Version: 1.0  
Status: **FROZEN for Milestone 4 implementation.**  
Author: Engineering (pre-Milestone-4 design review).  
Dependency: `Docs/BACKEND_API_SPEC.md` (Milestone 3, stable — treat as a
library, not editable).

> **Design contract**: this document is the source of truth for all visual and
> interaction decisions. If implementation discovers a genuine gap, update this
> document first and re-obtain approval — do not silently deviate.

---

## 0. Design Mandate

> **The graph is the hero.**

The knowledge graph must be visible the instant the application loads. It
must be the primary surface — not a tab, not a modal, not a drawer. Every
other UI element exists in service of the graph.

When a judge opens MemoryOS for the first time they must *see* — before
reading a word — that this is fundamentally different from a chatbot.

Ordinary RAG retrieves a list of text chunks. MemoryOS constructs a living
knowledge graph. That difference must be immediately visceral.

The design principle is: **memory made visible**.

---

## 1. Information Architecture

### 1.1 Application surfaces

MemoryOS has **one primary surface** and **three supporting panels**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  APP SHELL (persistent chrome)                                          │
│  ─ Logo + tagline       ─ Memory pulse strip (stats)   ─ Health dot    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   GRAPH CANVAS (hero, ~65% width)    │  INTERACTION PANEL (~35% width) │
│                                       │                                 │
│   Cytoscape.js knowledge graph        │  Tabs:                         │
│   Full-height, always visible         │   [Recall] [Sources] [Upload]  │
│   Interactive: pan, zoom, click       │                                 │
│                                       │  Active tab content renders    │
│                                       │  below the tab row             │
│                                       │                                 │
└───────────────────────────────────────┴─────────────────────────────────┘
```

### 1.2 Navigation model

There is **no page routing** in the MVP. MemoryOS is a **single-page
application** with one persistent layout. The right panel switches between
three modes via tab controls:

| Tab | Purpose | Primary backend call |
|-----|---------|----------------------|
| **Recall** | Ask questions, see evidence | POST /recall |
| **Sources** | List, manage, delete ingested sources | GET /sources |
| **Upload** | Ingest new sources (remember / improve) | POST /remember or POST /improve |

The active tab is persisted in URL hash (`#recall`, `#sources`, `#upload`)
so deep links work and browser back/forward behave correctly. Default on
first load: `#recall`.

### 1.3 Content hierarchy

```
Level 1: Knowledge Graph (always visible, 65% of viewport)
Level 2: Active Panel (recall / sources / upload)
Level 3: Memory Strip (total sources, entity counts — always visible)
Level 4: Health Indicator (top-right corner dot — always visible)
```

Nothing should ever fully obscure the graph. Panels float alongside it —
they never slide over it.

---

## 2. Screen Layout

### 2.1 Desktop layout (≥ 1280 px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ╔══════════╗  MemoryOS   │  ◉ 24 nodes   ╌ 18 edges   📄 3 sources          ●│
│ ╚══════════╝  Research Memory OS          [entity breakdown pills]     [status]│
├──────────────────────────────────────────────────────────────────────────────┤
│                                          │                                    │
│                                          │  ┌─────────────────────────────┐  │
│                                          │  │ [Recall] [Sources] [Upload] │  │
│                                          │  └─────────────────────────────┘  │
│                                          │                                    │
│     KNOWLEDGE GRAPH CANVAS               │  [Active panel content]            │
│                                          │                                    │
│     Nodes: color-coded by entity type    │  (Recall tab = query input +       │
│     Edges: styled by relationship type   │   strategy selector + answer +     │
│     Evidence: glowing highlight          │   evidence summary)                │
│                                          │                                    │
│     Pan / zoom / click                   │  (Sources tab = source cards with  │
│     Toolbar: [Fit] [+] [-] [Reset]       │   title, date, delete button)      │
│                                          │                                    │
│     Empty state: animation + CTA         │  (Upload tab = form fields +       │
│                                          │   drag-drop zone + progress)       │
│                                          │                                    │
└──────────────────────────────────────────┴────────────────────────────────────┘
```

**Proportions:**
- Graph canvas: `flex: 1` (takes remaining width after panel)
- Interaction panel: `400px` fixed, scrollable, min-height = 100vh

**Toolbar (bottom-left of graph canvas, floating):**
```
[⊞ Fit]  [+]  [−]  [↺ Reset]
```
- Fit: `cy.fit()` — shows all nodes
- +/−: incremental zoom
- Reset: returns to initial layout, clears evidence highlighting

### 2.2 Narrow desktop (1024–1279 px)

Panel shrinks to `340px`. Graph label font size reduces. Same structural
layout preserved.

### 2.3 Tablet (768–1023 px)

Interaction panel collapses into a **bottom drawer** (initial height 280px,
drag to expand to 50vh). Graph canvas takes full width. Bottom drawer
overlaps the bottom 30% of graph — acceptable at this breakpoint because
the graph nodes occupy the upper portion.

### 2.4 Mobile (< 768 px)

Out of scope for the hackathon demo (spec §13 for rationale). The app
renders at the minimum supported width (768px) on mobile and shows a
"Best viewed on desktop" banner.

---

## 3. Navigation

### 3.1 Tab switching

Tab switching is **instant** — no network call required on switch. Data is
pre-fetched and cached:

| Event | Network | Cache |
|-------|---------|-------|
| App load | GET /stats, GET /graph, GET /sources | Stored in React state |
| Tab switch (any) | None | Render from cache |
| After ingest | GET /graph, GET /stats, GET /sources | Refresh all three |
| After forget | GET /graph, GET /stats, GET /sources | Refresh all three |
| After recall | None for graph; receive evidence_graph in response | Merge evidence into graph |

### 3.2 Graph refresh policy

The graph is **not polled**. It refreshes only after:
1. Successful POST /remember (status = created or degraded)
2. Successful POST /improve (status = created or degraded)
3. Successful POST /forget (deleted = true)
4. Manual "Refresh" action (small icon in graph toolbar)

Rationale: graph computation is expensive; automatic polling on a
single-tenant demo adds noise without value.

### 3.3 Evidence overlay mode

After a POST /recall with a non-null evidence_graph, the graph enters
**Evidence Mode**:
- All non-evidence nodes dim to 20% opacity
- Evidence nodes glow (box-shadow / shadow colour from strategy palette)
- Evidence edges draw bold with animated stroke-dashoffset
- The canvas auto-fits to the evidence subgraph bounding box
- The toolbar gains a `[✕ Clear Evidence]` button that exits Evidence Mode
- Evidence Mode is cleared automatically when a new query is submitted

Evidence Mode does not replace the full graph — it is a CSS class overlay.
The underlying element data is unchanged.

---

## 4. Upload Flow

### 4.1 Two upload actions

| Action | Button label | Endpoint | Lifecycle verb |
|--------|-------------|----------|----------------|
| Add new paper | **"Add to Memory"** | POST /remember | remember() |
| Expand existing memory | **"Expand Memory"** | POST /improve | improve() |

Both actions share the same form UI. The distinction is visible via a
toggle switch at the top of the Upload tab:

```
Memory Operation:  ○ Add (remember)   ● Expand (improve)
```

Toggling changes the button label and the endpoint. No other UI difference.

### 4.2 Upload form fields

```
┌─────────────────────────────────────────────┐
│ Memory Operation: [Add ●] [Expand ○]        │
│                                             │
│ Source Type                                 │
│ [PDF ▼]  pdf / text / markdown / url        │
│                                             │
│ ── PDF selected ──────────────────────────  │
│ Drag & drop a PDF here                      │
│ or [Browse files]                           │
│ Max 20 MB                                   │
│                                             │
│ ── text/markdown selected ────────────────  │
│ ┌─────────────────────────────────────────┐ │
│ │ Paste or type content here...           │ │
│ │                                         │ │
│ └─────────────────────────────────────────┘ │
│ 0 / 500,000 characters                      │
│                                             │
│ ── url selected ──────────────────────────  │
│ https://...                                 │
│                                             │
│ Title (optional)                            │
│ [                                         ] │
│                                             │
│ Active Hypotheses (optional)               │
│ [+ Add hypothesis]                          │
│  ─ "YOLO11 outperforms YOLO9 on COCO"      │
│                                             │
│ [Add to Memory ▶]                           │
└─────────────────────────────────────────────┘
```

### 4.3 Validation (client-side, before network call)

| Field | Rule | Error |
|-------|------|-------|
| Source type | Required | "Please select a source type" |
| File | Required for PDF, max 20 MB | "File must be ≤ 20 MB" |
| Content | Required for text/markdown/url | "Content is required" |
| Content | URL must start with http:// or https:// | "Please enter a full URL" |
| Title | Max 255 chars | "Title must be ≤ 255 characters" |
| Active hypotheses | Max 5, each ≤ 1,000 chars | inline per hypothesis |

Client-side validation mirrors the backend spec §5.1 rules exactly.
Errors appear inline immediately on field blur — no submit-then-show.

### 4.4 Progress states

Ingest is slow (15–60 s). The UI must communicate progress honestly:

**State 1: Submitting** (0–1 s)
```
Sending to memory...
[⠿ spinner]
```

**State 2: Processing** (1 s → completion)
```
Building knowledge graph...  ████░░░░░░  ~30s remaining
```
The progress bar is **fake-progress** (animated fill, not real %) because
the backend provides no streaming. It fills to 80% over 30 s then holds.
When the response arrives it snaps to 100%.

A short explanatory note appears below:
```
ℹ  Extracting entities and relationships.
   This takes 15–60 seconds for most documents.
```

**State 3: Success**
```
✅  Memory updated
    12 nodes  ·  8 edges added to the knowledge graph
```
The graph canvas re-fetches and animates new nodes into view.

**State 4: Duplicate**
```
ℹ  Already in memory
   This document was previously ingested (skipped).
```

**State 5: Degraded**
```
⚠  Stored but no new structure
   The document was saved to memory but no new
   entities or relationships were extracted.
   Try rephrasing or uploading a richer document.
```

### 4.5 After successful ingest

1. Graph canvas shows loading shimmer
2. GET /graph called → new elements merged in with fade-in animation
3. GET /stats called → memory strip updates
4. GET /sources called → source list refreshes
5. Tab automatically switches to Recall
6. Toast notification appears: "Graph expanded. Ask a question."

---

## 5. Recall Flow

### 5.1 Recall interface

```
┌─────────────────────────────────────────────────────┐
│ Ask your memory                                     │
│ ┌───────────────────────────────────────────────┐  │
│ │ Which papers contradict each other?           │  │
│ └───────────────────────────────────────────────┘  │
│                                                     │
│ Strategy  [Auto-detect ▼]                          │
│           Auto-detect                               │
│           Relationship                              │
│           Contradiction                             │
│           Gap Analysis                              │
│           Factual                                   │
│                                                     │
│ [Recall ▶]                                         │
└─────────────────────────────────────────────────────┘
```

**Strategy selector behavior:**
- Default: `null` → backend auto-detects from query keywords
- Selecting a strategy adds a colored badge next to the selector:
  - Contradiction → 🔴 red badge
  - Relationship → 🔵 blue badge
  - Gap Analysis → 🟡 amber badge
  - Factual → 🟢 green badge
- The badge color matches the evidence highlighting color used on the graph

### 5.2 Recall progress state (3–8 s)

```
Searching memory...  [⠿ spinner]
Traversing knowledge graph
```

No fake progress bar (shorter latency than ingest — spinner is sufficient).

### 5.3 Recall result

```
┌─────────────────────────────────────────────────────┐
│ [← New Question]                                    │
│                                                     │
│ ✦ Answer                                            │
│ ─────────────────────────────────────────────────── │
│ YOLO11 was preferred over YOLO9 because it achieved │
│ a 4.2% mAP improvement on COCO while reducing model │
│ parameter count by 22%...                           │
│                                                     │
│ ─────────────────────────────────────────────────── │
│ Strategy used:  Relationship           [🔵]         │
│ Evidence:       6 nodes highlighted in graph        │
│ Duration:       2.4 s                               │
│                                                     │
│ ⚠  Degraded recall — no structured evidence found.  │
│    (only shown when evidence_graph is null)         │
└─────────────────────────────────────────────────────┘
```

**Evidence notification triggers graph action:**
When `evidence_graph` is non-null, the graph automatically:
1. Enters Evidence Mode (dims non-evidence nodes)
2. Fits viewport to evidence subgraph bounding box
3. Evidence nodes pulse once (CSS animation, not loop)

The "6 nodes highlighted in graph" text is a clickable link:
`→ Show in graph` — triggers the same viewport fit.

### 5.4 Degraded recall

When `evidence_graph` is null (no structured evidence found):
- The prose answer is still shown normally
- A `⚠` warning badge appears below the answer:
  ```
  ⚠  No graph evidence found for this query.
     The answer is based on semantic search only.
     Try the Contradiction or Relationship strategy.
  ```
- The graph does NOT enter Evidence Mode
- No node highlighting occurs

### 5.5 Recall history

The last 5 recall queries are stored in component state (not
localStorage — lost on refresh). They appear as **quick-recall chips**
above the query input:

```
Recent:  [Which papers contradict?]  [YOLO11 vs YOLO9]  [×]
```

Clicking a chip replaces the query input text. `[×]` clears history.

---

## 6. Graph Interaction Model

### 6.1 Node interactions

| Interaction | Behavior |
|-------------|----------|
| Hover | Tooltip: node label + type badge |
| Single click | **Node Detail Panel** slides in from right (replaces interaction panel) |
| Double click | Fit graph to this node and its 1-hop neighborhood |
| Right click | Context menu: "Highlight neighborhood", "Copy label", "Show sources" |

### 6.2 Node Detail Panel

Replaces the interaction panel when a node is clicked:

```
┌──────────────────────────────────────────────────┐
│ [← Back]                                        │
│                                                  │
│ 📄 Paper                        [entity-paper]  │
│ YOLO11: Real-Time Object Detection               │
│                                                  │
│ Attributes                                       │
│   year: 2024                                     │
│   venue: arXiv                                   │
│                                                  │
│ Connections (4)                                  │
│   → CONTRADICTS  YOLO9 Detection                │
│   → USES         COCO Dataset                   │
│   → WRITTEN_BY   Ultralytics Team               │
│   → SUPPORTS     Speed Benchmark Results        │
│                                                  │
│ Sources                                          │
│   📎  yolo11_paper.pdf                          │
│                                                  │
└──────────────────────────────────────────────────┘
```

The "Connections" list shows edges from the full graph data
(not a new API call — computed from the cached graph elements).

### 6.3 Edge interactions

| Interaction | Behavior |
|-------------|----------|
| Hover | Tooltip: source node → relationship type → target node |
| Click | Highlight both connected nodes (add `selected` class) |

Edges are **not** clickable to open a detail panel in the MVP
(too much UI complexity for the demo; noted as future extensibility §14.3).

### 6.4 Graph toolbar actions

```
[⊞ Fit All]  [+]  [−]  [↺ Reset Layout]  [◎ Refresh]
```

| Button | Action |
|--------|--------|
| ⊞ Fit All | `cy.fit()` — show all nodes |
| + | `cy.zoom(cy.zoom() * 1.2)` |
| − | `cy.zoom(cy.zoom() / 1.2)` |
| ↺ Reset Layout | Re-run cose-bilkent layout from scratch |
| ◎ Refresh | GET /graph + GET /stats (manual refresh) |

When in Evidence Mode, a fifth button appears:
```
[✕ Clear Evidence]
```
Clicking it removes all `evidence-node` classes and returns to full-graph view.

### 6.5 Selection and multi-select

Single-click selects one node. Shift+click adds to selection. Selecting
multiple nodes shows a mini status bar at the bottom of the graph:
```
3 nodes selected  |  [Highlight neighborhood]  [Clear]
```

---

## 7. Cytoscape.js Integration

### 7.1 Library and layout

- **Cytoscape.js** `^3.29` (latest stable)
- **Layout**: `cytoscape-cose-bilkent` (force-directed, handles clusters)
  - `quality: 'proof'` for final render
  - `animate: true`, `animationDuration: 800`
  - `nodeRepulsion: 4500`
  - `idealEdgeLength: 100`
  - `edgeElasticity: 0.45`
- **Extensions**: `cytoscape-popper` for tooltips (uses Floating UI)

Layout fallback: if `cose-bilkent` fails to load, use `circle` layout
to ensure the graph always renders.

### 7.2 Node stylesheet (CSS classes from Backend §6)

| Class | Background | Border | Shape |
|-------|-----------|--------|-------|
| `entity-paper` | `#6366f1` (indigo) | `#4338ca` | `roundrectangle` |
| `entity-author` | `#8b5cf6` (violet) | `#6d28d9` | `ellipse` |
| `entity-method` | `#0ea5e9` (sky) | `#0369a1` | `roundrectangle` |
| `entity-dataset` | `#14b8a6` (teal) | `#0f766e` | `roundrectangle` |
| `entity-benchmark` | `#f59e0b` (amber) | `#b45309` | `roundrectangle` |
| `entity-experiment` | `#f97316` (orange) | `#c2410c` | `roundrectangle` |
| `entity-hypothesis` | `#ec4899` (pink) | `#be185d` | `diamond` |
| `entity-finding` | `#22c55e` (green) | `#15803d` | `roundrectangle` |
| `entity-research-note` | `#84cc16` (lime) | `#4d7c0f` | `roundrectangle` |
| `entity-topic` | `#64748b` (slate) | `#475569` | `ellipse` |
| `entity-unknown` | `#374151` (gray-700) | `#1f2937` | `ellipse` |

All nodes:
- `label`: `data(label)` — truncated to 28 chars (`\n` wrapping)
- `font-size`: 11px
- `font-family`: `"Inter", sans-serif`
- `text-valign`: `bottom`
- `text-wrap`: `wrap`
- `width`: 48, `height`: 48 (base)
- `min-zoomed-font-size`: 8

### 7.3 Edge stylesheet

| Class | Line style | Color | Arrow |
|-------|-----------|-------|-------|
| `rel-contradicts` | `solid` | `#ef4444` (red) | `triangle` |
| `rel-supports` | `solid` | `#22c55e` (green) | `triangle` |
| `rel-uses` | `dashed` | `#60a5fa` (blue) | `triangle` |
| `rel-evaluates` | `dotted` | `#f59e0b` (amber) | `triangle` |
| `rel-written-by` | `solid` | `#a78bfa` (violet) | `none` |
| `rel-references` | `dashed` | `#94a3b8` (slate) | `triangle` |
| `rel-derived-from` | `solid` | `#fb923c` (orange) | `triangle` |
| `rel-about` | `dashed` | `#64748b` (gray) | `none` |
| default (unknown) | `solid` | `#4b5563` | `triangle` |

All edges:
- `width`: 2
- `label`: `data(label)` — shown on hover only (opacity 0 → 1)
- `curve-style`: `bezier`
- `target-arrow-shape`: per class table above

### 7.4 Evidence Mode stylesheet

Applied when `evidence-node` class is set (spec §6.4):

```css
/* Non-evidence nodes */
.non-evidence {
  opacity: 0.15;
}

/* Evidence nodes */
.evidence-node {
  border-width: 3;
  border-color: [strategy color — see §5.1];
  shadow-blur: 20;
  shadow-color: [strategy color];
  shadow-opacity: 0.8;
  width: 64;   /* 33% larger */
  height: 64;
}
```

The non-evidence class is applied to all nodes NOT in the evidence set.

Strategy-specific evidence border/shadow colors:
- `contradiction` → `#ef4444` (red)
- `relationship` → `#6366f1` (indigo)
- `gap_analysis` → `#f59e0b` (amber)
- `factual` → `#22c55e` (green)

### 7.5 Node appearance animation

When new nodes arrive (after ingest):
1. New elements start at `opacity: 0`, `width: 0`, `height: 0`
2. Animate to `opacity: 1`, `width: 48`, `height: 48` over 400ms
3. After all nodes appear (600ms), re-run layout with `animate: true`

### 7.6 Legend

A compact legend is rendered in the **bottom-left corner of the graph canvas**
(not inside Cytoscape — a separate HTML overlay):

```
■ Paper   ■ Author   ■ Method   ■ Dataset   ■ Hypothesis   ■ Finding
[+ 5 more]
```

Clicking a legend item adds a CSS filter to highlight all nodes of that type.
Clicking `[+ 5 more]` expands to show all 10 types.

The legend is collapsible via a `[≡]` toggle.

---

## 8. Loading States

### 8.1 Initial app load

While GET /graph + GET /stats + GET /sources are in flight:

```
Graph canvas:
  Skeleton shimmer (gray animated gradient fills the canvas area)
  Center: spinning Cognee-branded logo (60px)

Right panel:
  Skeleton cards for each tab section
```

Target: < 3 s for initial load with no data (empty graph).

### 8.2 Graph loading (after ingest / manual refresh)

The existing graph remains visible (no blank canvas). A **loading overlay**
appears:
```
[⠿ Refreshing graph...]
```
— top-right corner of graph canvas, small pill with spinner.

When new elements arrive, they fade in without the old elements disappearing.

### 8.3 Recall loading

The answer area shows:
```
[⠿ Searching memory...]
Traversing knowledge graph...
```

The graph canvas is NOT loading-blocked during recall. The user can still
pan/zoom the graph while the recall is in flight.

### 8.4 Source deletion

When DELETE (POST /forget) is initiated:
- The source card shows a spinner in place of the delete button
- The card dims to 50% opacity
- The rest of the sources list remains fully interactive

---

## 9. Error States

All errors use the backend's standard error envelope:
```json
{"error": {"code": "...", "message": "...", "detail": "..."}}
```

### 9.1 Error display pattern

Errors appear as **inline messages within the relevant section** — NOT as
full-page error screens. The graph and other UI elements remain accessible.

### 9.2 Error mapping

| Backend `error.code` | Shown where | Message |
|---------------------|-------------|---------|
| `VALIDATION_ERROR` | Below the relevant form field | Backend message text (safe for display) |
| `EXTRACTION_FAILED` | Upload progress area | "Graph extraction failed. The LLM couldn't process this document. Try a different format." |
| `PROVIDER_ERROR` | Upload or recall result area | "Memory provider unavailable. Check your API key and backend connectivity." |
| `RECALL_FAILED` | Recall result area | "Recall failed. Memory provider couldn't complete the search." |
| `CONFIGURATION_ERROR` | Health banner (top of page) | "Backend is misconfigured. Check your .env file." — banner persists until resolved |
| `CAPABILITY_UNAVAILABLE` | Graph or recall area | "This capability is not available in the current configuration." |
| `SOURCE_NOT_FOUND` | Sources panel | "Source not found — it may have already been deleted." |
| `INTERNAL_ERROR` | Relevant section | "An unexpected error occurred. Check the backend logs." |
| Network error (no response) | Toast notification | "Cannot reach MemoryOS server. Is the backend running on port 8000?" |

### 9.3 Health banner

When GET /health returns `status: "degraded"` (503):
```
⚠  Backend misconfigured — Check your .env file (CONFIGURATION_ERROR).
   [Retry]
```
A persistent amber banner across the full top of the page. Cannot be
dismissed — it clears only when health returns 200.

### 9.4 Retry behavior

All errors (except validation) show a `[Try again]` button that re-submits
the last request without requiring the user to re-fill the form.

No automatic retries in MVP (to avoid hidden LLM cost loops).

---

## 10. Empty States

### 10.1 Empty graph (no sources ingested)

This is the **most important empty state** — it's the first thing a new
judge sees.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│           ✦                                                         │
│        ✦     ✦     ✦                                               │
│           ✦     ✦                                                   │
│        ✦     ✦     ✦                                               │
│           ✦                                                         │
│                                                                     │
│     This is where your knowledge graph will live.                  │
│                                                                     │
│     Upload a research paper and watch entities and               │
│     relationships materialize from its content.                    │
│                                                                     │
│              [ → Add First Paper ]                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

The `✦` symbols are animated — they slowly pulse and drift, suggesting
the latent structure waiting to emerge. The animation uses CSS keyframes
(no canvas, no WebGL — simple and lightweight).

Clicking "Add First Paper" switches to the Upload tab.

### 10.2 Empty recall result

After a recall with a successful response but no evidence:
→ See §5.4 (Degraded recall).

### 10.3 Empty sources list

```
No sources in memory yet.
→ Upload your first document
```

Simple text link, not a full illustrated empty state (sources tab is
secondary to the graph canvas).

### 10.4 Empty recall history

No chips shown. Query input shows placeholder:
```
"Ask anything about your research memory..."
```

---

## 11. Demo Journey

This section documents the exact sequence a judge should experience
during the 3-minute live demo. The UI must support this journey without
any configuration or setup.

### 11.1 Pre-demo setup (not visible to judges)

Before the demo begins, the engineer:
1. Starts the backend: `uvicorn Backend.app:app --port 8000`
2. Opens the frontend at `http://localhost:3000`
3. Verifies health dot is green
4. Ensures the graph is empty (fresh start shows the animated empty state)

### 11.2 Act 1 — "Memory is Empty" (30 seconds)

**What the judge sees:**
- The animated `✦` graph empty state
- The memory strip shows: `0 nodes · 0 edges · 0 sources`
- The health dot is green

**What the presenter says:**
> "This is MemoryOS. Unlike a chatbot, it has no memory until you give it some.
> Watch what happens when I add a research paper."

### 11.3 Act 2 — "Memory Is Created" (60–90 seconds)

**Action:** Drag-drop a pre-staged PDF (e.g., YOLO11 paper) onto the upload zone.

**What the judge sees:**
1. File appears in upload zone with filename + size
2. Click "Add to Memory" button
3. Progress bar animates: "Building knowledge graph... ~30s remaining"
4. Explanatory note: "Extracting entities and relationships"
5. After ~30s: "✅ Memory updated — 12 nodes · 8 edges added"
6. **Graph canvas fills with nodes** — entities appear with fade-in animation
7. Papers (indigo), Authors (violet), Methods (sky) are visually distinct
8. Edges connect them: WRITTEN_BY, USES, EVALUATES etc.
9. Layout settles into a readable force-directed arrangement

**What the presenter says:**
> "MemoryOS didn't just store the PDF — it extracted structured knowledge.
> Every entity is a node. Every relationship is an edge. This is your memory
> made visible."

### 11.4 Act 3 — "Memory Is Recalled" (45 seconds)

**Action:** Switch to Recall tab. Type: "Why do we prefer YOLO11?"

**What the judge sees:**
1. Query submitted
2. Spinner: "Searching memory..."
3. After ~4s: prose answer appears
4. Graph enters Evidence Mode — non-relevant nodes dim
5. 4–6 nodes glow (the entities cited in the answer)
6. "Strategy: Relationship · 4 nodes highlighted"
7. Graph viewport fits to the evidence subgraph

**What the presenter says:**
> "The answer isn't from a vector index. It's from graph traversal.
> Those glowing nodes are exactly what the memory used to construct this answer.
> You can see the reasoning path."

### 11.5 Act 4 — "Memory Evolves" (30 seconds)

**Action:** Upload a second paper (e.g., YOLO9 comparison study). Click "Expand Memory".

**What the judge sees:**
1. Progress (same as before, faster if smaller doc)
2. New nodes appear on the existing graph — they animate in alongside old ones
3. New edges form — including a `CONTRADICTS` edge (red, solid) between the two papers
4. Memory strip updates: "18 nodes · 14 edges · 2 sources"

**What the presenter says:**
> "Notice: YOLO11 and YOLO9 are now connected by a CONTRADICTS edge — in red.
> MemoryOS didn't need to be told they conflict. It extracted that relationship
> automatically."

**Action:** Type: "What contradicts YOLO11?" (strategy: Contradiction selected)

**What the judge sees:**
1. Evidence Mode — contradiction edges glow red
2. The CONTRADICTS relationship is front and center

### 11.6 Act 5 — "Memory Is Selective" (30 seconds)

**Action:** Switch to Sources tab. Click "Delete" on the YOLO9 paper.

**What the judge sees:**
1. Source card dims
2. Confirmation: "Delete this source? This will remove it from memory. [Cancel] [Delete]"
3. Click Delete
4. Spinner on card
5. "✅ Source removed" toast
6. Graph reloads — YOLO9-related nodes fade out
7. The CONTRADICTS edge disappears
8. Memory strip: "12 nodes · 8 edges · 1 source"

**What the presenter says:**
> "Memory is editable. Delete a source and its knowledge is cleanly removed
> from the graph. This is forget() — not truncation, not a summary — it's
> precise, structural removal."

### 11.7 Demo success criteria

The demo succeeds if the judge can answer YES to:
- [ ] "Did I see the graph grow when memory was created?"
- [ ] "Did I see which nodes the answer was based on?"
- [ ] "Did I see the graph change when memory evolved?"
- [ ] "Did I see the graph contract when memory was deleted?"

---

## 12. Mobile / Desktop Assumptions

### 12.1 Target device

**Primary target:** Desktop / large laptop, 1440px × 900px or larger.

This is a developer-facing research tool presented to hackathon judges
who will be at a laptop or desktop. Mobile support is **explicitly out of scope**
for the MVP (HACKATHON_CONTEXT.md confirms: focus on polished single workflow).

### 12.2 Minimum supported width

**1024px.** Below this, the layout degrades gracefully (panel collapses)
but is not tested or optimised.

### 12.3 Browser support

- Chrome 120+ (primary, demo browser)
- Firefox 120+ (secondary, test)
- Safari 17+ (should work, not primary)
- No IE11, no Edge Legacy

### 12.4 Screen resolution assumptions

The graph canvas is designed for 1440×900 at 1x DPI. High-DPI (2x)
screens are supported automatically by Cytoscape.js canvas scaling.

### 12.5 Touch support

Pan and zoom work via touch on Cytoscape.js by default. The right panel
is scrollable via touch. No specific touch optimisations in MVP.

---

## 13. Accessibility

### 13.1 Baseline commitment

The MVP targets **WCAG 2.1 Level A** with selected AA criteria.
Full AA compliance is deferred post-hackathon.

### 13.2 Color

- All text meets 4.5:1 contrast ratio against background (AA)
- Graph node colors are distinguishable at normal saturation
- Evidence highlighting does NOT rely on color alone —
  evidence nodes also increase in size (+33%) and gain a visible border
- Color-blind friendly: red/green evidence modes also differ in
  border width and shadow opacity, not just hue

### 13.3 Keyboard navigation

| Element | Keyboard behavior |
|---------|-------------------|
| Tab tabs | Arrow keys to switch tabs |
| Upload form | Fully keyboard-navigable (tab to each field) |
| Recall input | Enter to submit |
| Delete button | Enter to trigger, Escape to cancel dialog |
| Graph canvas | Cytoscape built-in keyboard: arrow keys to pan, +/- to zoom |
| Node click (keyboard) | Focus a node and press Enter to open detail panel |

### 13.4 Screen readers

- All interactive elements have `aria-label` attributes
- Graph canvas has `role="img" aria-label="Knowledge graph with N nodes and M edges"`
- Node count and edge count are announced in the live region after graph updates
- The answer text from recall is placed in an `aria-live="polite"` region
- Loading states use `aria-busy="true"` on their container

### 13.5 Motion reduction

Respects `prefers-reduced-motion`:
- All CSS animations disabled (nodes appear instantly, no fade)
- Cytoscape `animate: false` when motion is reduced
- Progress bar does not animate (static fill)

### 13.6 Font sizing

Base font: 16px. UI uses `rem` units throughout. User can increase browser
font size up to 200% without layout breakage.

---

## 14. Future Extensibility

This section documents explicitly excluded features and how to add them
without architectural rework.

### 14.1 Multi-project support

Currently: `PROJECT_ID = "demo"` is hard-coded in the backend.

**Future path:**
- Add a project selector dropdown in the top bar
- Switch from `GET /api/v1/graph` to `GET /api/v1/projects/{id}/graph`
- No frontend architectural changes needed beyond the selector component

### 14.2 Graph filtering and search

Currently: all nodes always visible (modulo Evidence Mode).

**Future path:**
- Add a filter bar above the graph: filter by entity type, relationship type, source
- Cytoscape already supports `cy.elements('[type = "Paper"]').show()`
- The legend §7.6 click-to-filter is the first step toward this

### 14.3 Edge detail panel

Currently: clicking an edge only highlights both nodes.

**Future path:**
- Add a third panel type: `EdgeDetailPanel`
- Shows: source node → relationship → target node + any attributes
- No new API call needed — edge data already in the cached graph

### 14.4 Export

Currently: no export.

**Future path:**
- "Export Graph" button → `cy.png()` for image, or serialize elements to JSON
- "Export Answer" button → copy answer text to clipboard (trivial)

### 14.5 Hypothesis steering UI

Currently: active_hypotheses is a text field (JSON string).

**Future path:**
- Replace with a proper hypothesis management panel
- Saved hypotheses persist in localStorage
- Each hypothesis shows which recalls it has influenced

### 14.6 Graph history / timeline

Currently: the graph shows the current state only.

**Future path:**
- A timeline scrubber below the graph
- Each ingest is a checkpoint
- Scrubbing shows the graph state at that point in time
- This requires the backend to support timestamped graph snapshots (memory_core change)

### 14.7 Streaming recall

Currently: recall blocks until complete (15–60 s for complex queries).

**Future path:**
- Backend adds `GET /api/v1/recall/stream` (Server-Sent Events)
- Frontend renders tokens as they arrive
- Progress in graph: edges animate as they're traversed

---

## 15. Design Self-Critique

> The following section deliberately challenges the design decisions made
> above. These are genuine weaknesses, not hypothetical edge cases.

### Weakness 1: The 65/35 split may feel cramped on 13" laptops

**Problem:** At 1280×800, the graph canvas is ~832px wide and the panel
is 400px. With Cytoscape's node labels and multiple nodes, the graph can
feel crowded. The interaction panel has very little breathing room.

**Mitigation:** The panel is resizable (drag handle between graph and panel).
Default split: 60/40. A `[⊠ Fullscreen Graph]` button hides the panel
entirely, useful when presenting the graph close-up.

**Unresolved risk:** If the user has a 13" laptop at 1366×768, the layout
is tight but workable. Not tested at this resolution.

---

### Weakness 2: Fake progress bar is dishonest

**Problem:** The 30-second fake progress bar fills based on a time estimate,
not actual backend progress. If cognify() completes in 10 s (fast) the bar
will have only reached ~30% fill. If it takes 90 s (slow), the bar will
appear stuck at 80% for 60 s.

**Mitigation:** The bar does not claim to show real progress — it says
"Building knowledge graph..." with the loading animation. The fake fill
provides psychological comfort. A hard number ("~30s remaining") sets
expectations honestly.

**Alternative considered:** Remove the progress bar entirely. Use only a
spinner. Rejected: a bare spinner gives no sense of progress duration,
which causes users to think the app is broken after 20 s.

**Better future solution:** Backend streaming (§14.7). For now, the fake
bar is honest if labeled correctly.

---

### Weakness 3: Evidence Mode is additive — no way to compare two queries

**Problem:** If the judge runs two different recall queries in sequence, the
second query clears the first evidence set and replaces it. There is no way
to compare "what does query A recall" vs "what does query B recall" side by side.

**Mitigation:** The recall result panel shows the previous query in the
"Recent:" chips bar. The judge can rapidly switch between them. The graph
re-highlights each time.

**Unresolved:** Side-by-side evidence comparison would require two graph
canvases or an overlay mode. This is genuinely out of scope for the MVP and
noted in §14 as future work.

---

### Weakness 4: The delete confirmation modal adds friction to a demo moment

**Problem:** The demo Act 5 (forget) requires: click Delete → confirm dialog
→ click Delete again. This two-step interrupts the demo flow and requires
the presenter to explain the confirmation dialog.

**Alternative considered:** Single-click delete with a 5-second undo toast
(Gmail-style). Rejected because: single-tenant demo, accidental deletion is
worse than dialog friction, and the dialog is part of the narrative
("this is a deliberate, reversible action").

**Mitigation:** The confirmation dialog is designed to be minimal
(2 buttons, no long text) and keyboard-operable (Enter = confirm). A
practiced presenter can complete it in under 2 seconds.

---

### Weakness 5: Cognee scaffolding nodes pollute the graph

**Problem:** The backend passes through ALL nodes from Cognee's graph,
including internal scaffolding nodes (`type: "unknown"`, BELONGS_TO_SET
edges, IS_A edges). These appear as gray unlabeled nodes in the graph
and clutter the visual for judges.

**Mitigation (in spec):** Unknown nodes are rendered smaller (36px vs 48px),
lower opacity (0.6), and pushed to graph periphery by the force-directed
layout. The legend says `■ Other (internal)` for these.

**Better solution:** A backend filter. Add a `?typed_only=true` query
parameter to `GET /api/v1/graph` that returns only nodes with known
EntityType values. This is a backend change but a trivial one.

**Decision:** The scaffolding node issue should be reported to memory_core
before Milestone 4 begins. If the filter can be added to the backend
without touching memory_core internals, it should be.

**This is a genuine gap** in the current spec. The frontend will need
a client-side filter as a fallback: render `entity-unknown` nodes with
`display: none` by default, toggled on via the legend.

---

### Weakness 6: No loading state for the initial graph mount

**Problem:** On first load, if the graph is large (>100 nodes), Cytoscape
layout computation can take 2–4 s. During this time, the canvas shows
nodes in random positions before the layout settles. This looks broken.

**Mitigation:** Show a full-canvas loading overlay until the `layoutstop`
event fires. Only then remove the overlay and reveal the graph.

---

### Weakness 7: The interaction panel is too narrow for long recall answers

**Problem:** A 400px panel is fine for 2–3 sentence answers. For longer
answers (5+ paragraphs), the panel becomes a long scroll. The judge may
not scroll and miss key content.

**Mitigation:** The answer section has a `max-height: 40vh` with
`overflow-y: auto` and a subtle gradient fade at the bottom indicating
more content. A "Show full answer" toggle expands it.

The panel is resizable (§15.1 mitigation), so the judge can drag it wider
if needed.

---

### Weakness 8: Recall strategy is invisible when "Auto-detect" is selected

**Problem:** When strategy = null, the backend auto-detects. But the
frontend doesn't show which strategy was actually used until after the
response arrives. The judge may not notice the `strategy_used` field
in the result.

**Mitigation:** After a recall response, display a clear badge:
```
Strategy detected: [🔵 Relationship]
```
This is already in the spec (§5.3). The real weakness is that it appears
only after the response. The presenter should call it out verbally.

**Better design:** Show the auto-detected strategy in real-time as the
query is typed (client-side keyword matching). This requires maintaining
a local copy of the router logic. Flagged as §14 future extensibility,
not implemented in MVP.

---

## Appendix A: Color Palette Reference

```
Background:  #0f172a  (slate-900)
Surface:     #1e293b  (slate-800)
Border:      #334155  (slate-700)
Text primary: #f1f5f9 (slate-100)
Text muted:   #94a3b8 (slate-400)

Accent:      #6366f1  (indigo-500)
Accent hover: #818cf8 (indigo-400)

Success:     #22c55e  (green-500)
Warning:     #f59e0b  (amber-500)
Error:       #ef4444  (red-500)
Info:        #60a5fa  (blue-400)

Graph background: #0a0e1a (darker than surface — makes nodes pop)
```

---

## Appendix B: Typography

```
Font family: "Inter", system-ui, sans-serif
             Loaded from Google Fonts (subset: latin)

Scale:
  App title:    24px / 700 / slate-100
  Panel header: 16px / 600 / slate-100
  Body:         14px / 400 / slate-300
  Caption:      12px / 400 / slate-400
  Node label:   11px / 400 / white (inside Cytoscape canvas)
  Code:         13px / 400 / "JetBrains Mono", monospace
```

---

## Appendix C: Animation Timing Reference

```
Node fade-in:          400ms ease-out
Layout settle:         800ms ease-in-out (cose-bilkent animate)
Evidence dim:          300ms ease
Evidence glow appear:  300ms ease-out
Evidence glow clear:   200ms ease-in
Panel slide (tablet):  250ms cubic-bezier(0.4, 0, 0.2, 1)
Tab switch:            instant (no animation — tabs are filter, not navigation)
Toast appear:          200ms ease-out (slide up from bottom)
Toast disappear:       3000ms auto-dismiss, 150ms ease-in
Progress bar fill:     linear, 30s to reach 80%
Progress bar snap:     300ms ease-out when response arrives
```
