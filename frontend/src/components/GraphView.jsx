import { useEffect, useRef, useState } from "react";
import { getGraph } from "../api.js";

const TYPE_LABEL = { family: "Scam family", tactic: "Tactic", lure: "Lure" };
const DEF_COLOR = "#948fab";

// Force-directed single-canvas graph — same node/edge shape as the am1
// memory-graph template ({id,label,type,props,color} / {id,from,to,label,props}),
// just one panel instead of the template's dual episodic/preference view.
function runGraphEngine(canvas, rawNodes, rawEdges, onSelect) {
  const ctx = canvas.getContext("2d");
  const NODE_R = 20;
  const wrap = canvas.parentElement;

  function resize() {
    canvas.width = wrap.clientWidth;
    canvas.height = wrap.clientHeight;
  }
  resize();
  const W = () => canvas.width, H = () => canvas.height;

  const nodeMap = {};
  const nodes = rawNodes.map((n) => {
    const nd = { ...n, x: W() / 2 + (Math.random() - 0.5) * W() * 0.7, y: H() / 2 + (Math.random() - 0.5) * H() * 0.7, vx: 0, vy: 0 };
    nodeMap[n.id] = nd;
    return nd;
  });
  const edges = rawEdges.map((e) => ({ ...e, src: nodeMap[e.from], dst: nodeMap[e.to] })).filter((e) => e.src && e.dst);

  let panX = 0, panY = 0, scale = 1, dragging = false, dragNode = null, lastMX = 0, lastMY = 0;
  let simRunning = true, simTick = 0, raf = null, stopped = false;
  let selectedId = null, connectedIds = new Set(), connectedEdgeIds = new Set();

  function toWorld(cx, cy) { return { x: (cx - panX) / scale, y: (cy - panY) / scale }; }
  function hitNode(wx, wy) {
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i], dx = n.x - wx, dy = n.y - wy;
      if (dx * dx + dy * dy <= NODE_R * NODE_R) return n;
    }
    return null;
  }

  function simulate() {
    if (!simRunning) return;
    const cx = W() / 2, cy = H() / 2;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const f = 4200 / (dist * dist);
        const fx = (dx / dist) * f, fy = (dy / dist) * f;
        a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy;
      }
    }
    edges.forEach((e) => {
      const a = e.src, b = e.dst;
      let dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const f = 0.045 * (dist - 150);
      const fx = (dx / dist) * f, fy = (dy / dist) * f;
      a.vx += fx; a.vy += fy; b.vx -= fx; b.vy -= fy;
    });
    nodes.forEach((n) => {
      n.vx += (cx - n.x) * 0.008; n.vy += (cy - n.y) * 0.008;
      n.vx *= 0.82; n.vy *= 0.82; n.x += n.vx; n.y += n.vy;
    });
    simTick++;
    if (simTick > 320) simRunning = false;
  }

  function hexToRgba(hex, a) {
    const h = hex || DEF_COLOR;
    const r = parseInt(h.slice(1, 3), 16), g = parseInt(h.slice(3, 5), 16), b = parseInt(h.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${a})`;
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(panX, panY);
    ctx.scale(scale, scale);
    const hasSel = selectedId !== null;
    edges.forEach((e) => {
      const active = !hasSel || connectedEdgeIds.has(e.id);
      const alpha = hasSel ? (active ? 1 : 0.08) : 0.55;
      const col = active && hasSel ? "#6b5cf0" : "#c7c3dd";
      const dx = e.dst.x - e.src.x, dy = e.dst.y - e.src.y;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      const ux = dx / len, uy = dy / len;
      const sx = e.src.x + ux * NODE_R, sy = e.src.y + uy * NODE_R;
      const ex = e.dst.x - ux * (NODE_R + 8), ey = e.dst.y - uy * (NODE_R + 8);
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey);
      ctx.strokeStyle = hexToRgba(col, alpha); ctx.lineWidth = alpha > 0.5 ? 2 : 1; ctx.stroke();
      const ax = ex - ux * 9 + uy * 5, ay = ey - uy * 9 - ux * 5, bx = ex - ux * 9 - uy * 5, by = ey - uy * 9 + ux * 5;
      ctx.beginPath(); ctx.moveTo(ex, ey); ctx.lineTo(ax, ay); ctx.lineTo(bx, by); ctx.closePath();
      ctx.fillStyle = hexToRgba(col, alpha); ctx.fill();
      if (active && scale > 0.55) {
        const mx = (e.src.x + e.dst.x) / 2, my = (e.src.y + e.dst.y) / 2;
        ctx.save(); ctx.font = "600 9px system-ui,sans-serif";
        const tw = ctx.measureText(e.label).width;
        ctx.fillStyle = "rgba(255,255,255,0.9)"; ctx.fillRect(mx - tw / 2 - 3, my - 7, tw + 6, 13);
        ctx.fillStyle = hasSel ? "#6b5cf0" : "#948fab"; ctx.globalAlpha = alpha;
        ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(e.label, mx, my);
        ctx.restore();
      }
    });
    nodes.forEach((n) => {
      const active = !hasSel || connectedIds.has(n.id);
      const alpha = hasSel ? (active ? 1 : 0.16) : 1;
      const col = active ? (n.color || DEF_COLOR) : "#dcd9ea";
      const isSel = n.id === selectedId;
      ctx.globalAlpha = alpha;
      if (isSel) { ctx.shadowColor = n.color || DEF_COLOR; ctx.shadowBlur = 20; }
      ctx.beginPath(); ctx.arc(n.x, n.y, NODE_R, 0, Math.PI * 2);
      ctx.fillStyle = col; ctx.fill();
      ctx.strokeStyle = isSel ? "#241f3a" : "rgba(255,255,255,0.9)";
      ctx.lineWidth = isSel ? 3 : 2; ctx.stroke(); ctx.shadowBlur = 0;
      if (scale > 0.32) {
        ctx.font = "600 11px system-ui,sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "top";
        const lbl = n.label.length > 20 ? n.label.slice(0, 18) + "…" : n.label;
        const tw = ctx.measureText(lbl).width;
        ctx.fillStyle = "rgba(255,255,255,0.9)"; ctx.fillRect(n.x - tw / 2 - 3, n.y + NODE_R + 3, tw + 6, 14);
        ctx.fillStyle = active ? "#241f3a" : "#b3aec6"; ctx.fillText(lbl, n.x, n.y + NODE_R + 4);
      }
      ctx.globalAlpha = 1;
    });
    ctx.restore();
  }

  function selectNode(id) {
    selectedId = id;
    connectedIds = new Set([id]);
    connectedEdgeIds = new Set();
    edges.forEach((e) => {
      if (e.from === id || e.to === id) { connectedIds.add(e.from); connectedIds.add(e.to); connectedEdgeIds.add(e.id); }
    });
    onSelect(nodeMap[id], edges, nodeMap);
    draw();
  }

  function onWheel(e) {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.91;
    panX = e.offsetX - (e.offsetX - panX) * factor;
    panY = e.offsetY - (e.offsetY - panY) * factor;
    scale *= factor;
    draw();
  }
  function onDown(e) {
    const w = toWorld(e.offsetX, e.offsetY), hit = hitNode(w.x, w.y);
    if (hit) { dragNode = hit; simRunning = false; } else { dragging = true; }
    lastMX = e.offsetX; lastMY = e.offsetY;
  }
  function onMove(e) {
    const dx = e.offsetX - lastMX, dy = e.offsetY - lastMY;
    if (dragNode) { dragNode.x += dx / scale; dragNode.y += dy / scale; draw(); }
    else if (dragging) { panX += dx; panY += dy; draw(); }
    else { const w = toWorld(e.offsetX, e.offsetY); canvas.style.cursor = hitNode(w.x, w.y) ? "pointer" : "default"; }
    lastMX = e.offsetX; lastMY = e.offsetY;
  }
  function onUp(e) {
    if (dragNode && !dragging) { const w = toWorld(e.offsetX, e.offsetY); const hit = hitNode(w.x, w.y); if (hit) selectNode(hit.id); }
    dragNode = null; dragging = false;
  }
  function onClick(e) {
    if (dragging) return;
    const w = toWorld(e.offsetX, e.offsetY), hit = hitNode(w.x, w.y);
    if (!hit) { selectedId = null; connectedIds = new Set(); connectedEdgeIds = new Set(); onSelect(null); draw(); return; }
    selectNode(hit.id);
  }
  function onResize() { resize(); draw(); }

  canvas.addEventListener("wheel", onWheel, { passive: false });
  canvas.addEventListener("mousedown", onDown);
  canvas.addEventListener("mousemove", onMove);
  canvas.addEventListener("mouseup", onUp);
  canvas.addEventListener("click", onClick);
  window.addEventListener("resize", onResize);

  function loop() {
    if (stopped) return;
    simulate();
    draw();
    raf = requestAnimationFrame(loop);
  }
  loop();

  return () => {
    stopped = true;
    if (raf) cancelAnimationFrame(raf);
    canvas.removeEventListener("wheel", onWheel);
    canvas.removeEventListener("mousedown", onDown);
    canvas.removeEventListener("mousemove", onMove);
    canvas.removeEventListener("mouseup", onUp);
    canvas.removeEventListener("click", onClick);
    window.removeEventListener("resize", onResize);
  };
}

export default function GraphView() {
  const [graph, setGraph] = useState(null);
  const [err, setErr] = useState("");
  const [selected, setSelected] = useState(null);
  const canvasRef = useRef(null);
  const edgeInfoRef = useRef({ edges: [], nodeMap: {} });

  useEffect(() => {
    getGraph().then(setGraph).catch((e) => setErr(String(e.message || e)));
  }, []);

  useEffect(() => {
    if (!graph || !canvasRef.current) return;
    const cleanup = runGraphEngine(canvasRef.current, graph.nodes, graph.edges, (node, edges, nodeMap) => {
      if (edges) edgeInfoRef.current = { edges, nodeMap };
      setSelected(node || null);
    });
    return cleanup;
  }, [graph]);

  if (err) return <div className="err">⚠ {err}</div>;
  if (!graph) return <div className="loading">Loading the knowledge graph…</div>;

  const types = [...new Set(graph.nodes.map((n) => n.type))];
  const colorFor = (t) => graph.nodes.find((n) => n.type === t)?.color || DEF_COLOR;
  const { edges, nodeMap } = edgeInfoRef.current;
  const outE = selected ? edges.filter((e) => e.from === selected.id) : [];
  const inE = selected ? edges.filter((e) => e.to === selected.id) : [];

  return (
    <>
      <p className="tagline">
        Every scam family, tactic, and lure lives in one shared graph.{" "}
        <b>Drag, scroll to zoom, click a node</b> to see how campaigns share the same tricks.
      </p>

      <div className="card graph-card">
        <div className="graph-legend">
          {types.map((t) => (
            <span className="litem" key={t}>
              <span className="ldot" style={{ background: colorFor(t) }} />
              {TYPE_LABEL[t] || t}
            </span>
          ))}
          <span className="muted graph-count">{graph.nodes.length} nodes · {graph.edges.length} edges</span>
        </div>
        <div className="graph-canvas-wrap">
          <canvas ref={canvasRef} />
        </div>
      </div>

      <div className="card graph-detail">
        {!selected ? (
          <div className="muted" style={{ textAlign: "center", padding: "18px 8px" }}>
            Click a node above to see its details and connections.
          </div>
        ) : (
          <>
            <span className="tag shared" style={{ background: selected.color, color: "#fff", borderColor: selected.color }}>
              {TYPE_LABEL[selected.type] || selected.type}
            </span>
            <div className="ntitle">{selected.label}</div>
            {Object.entries(selected.props || {}).filter(([, v]) => v !== null && v !== "").map(([k, v]) => (
              <div className="prow" key={k}>
                <span className="pkey">{k.replace(/_/g, " ")}</span>
                <span className="pval">{String(v)}</span>
              </div>
            ))}
            {outE.length > 0 && (
              <>
                <div className="section-label">Outgoing ({outE.length})</div>
                {outE.map((e) => (
                  <div className="citem" key={`o${e.id}`}>
                    <span className="cdot" style={{ background: nodeMap[e.to]?.color || DEF_COLOR }} />
                    <span className="clbl">{e.label}</span>
                    <span className="cname">→ {nodeMap[e.to]?.label || e.to}</span>
                  </div>
                ))}
              </>
            )}
            {inE.length > 0 && (
              <>
                <div className="section-label">Incoming ({inE.length})</div>
                {inE.map((e) => (
                  <div className="citem" key={`i${e.id}`}>
                    <span className="cdot" style={{ background: nodeMap[e.from]?.color || DEF_COLOR }} />
                    <span className="clbl">{e.label}</span>
                    <span className="cname">← {nodeMap[e.from]?.label || e.from}</span>
                  </div>
                ))}
              </>
            )}
          </>
        )}
      </div>
    </>
  );
}
