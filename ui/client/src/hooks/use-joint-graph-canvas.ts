/**
 * useJointGraphCanvas – JointJS paper hook for the *creation* canvas.
 *
 * Unlike `useJointGraph` (which loads a saved blueprint), this hook takes
 * live `CanvasNode[]` / `CanvasEdge[]` arrays from `useGraphLogic` and keeps
 * the JointJS graph imperatively synchronised with them.
 *
 * Provides: pan, zoom, node drag, overlay data, and paper coordinate helpers.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { dia, shapes } from "@joint/core";
import { DirectedGraph } from "@joint/layout-directed-graph";
import type { CanvasNode, CanvasEdge } from "@/types/graph";
import { safeFlushSync } from "@/lib/reactUtils";
import {
  NODE_WIDTH,
  NODE_HEADER_HEIGHT,
  LAYOUT_OPTS,
  FIT_PADDING,
  SCALE_CONTENT_TO_FIT_OPTS,
  STATUS_STYLES,
  nodeFillForType,
  injectSvgDefs,
  injectStatusGlowFilters,
} from "@/components/agentic-ai/graphs/GraphDisplayHelpers";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CanvasOverlayHeader {
  nodeId: string;
  label: string;
  nodeType: string;
  x: number;
  y: number;
  width: number;
  nodeHeight: number;
}

export interface UseJointGraphCanvasOptions {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  primaryHex?: string;
  onNodeClick?: (nodeId: string) => void;
  onPaneClick?: () => void;
  onNodePositionChange?: (nodeId: string, position: { x: number; y: number }) => void;
}

export interface UseJointGraphCanvasReturn {
  containerRef: React.RefObject<HTMLDivElement>;
  paperRef: React.MutableRefObject<dia.Paper | null>;
  graphRef: React.MutableRefObject<dia.Graph | null>;
  overlayHeaders: CanvasOverlayHeader[];
  paperTransform: { sx: number; sy: number; tx: number; ty: number };
  handleZoomIn: () => void;
  handleZoomOut: () => void;
  handleFitToView: () => void;
  runAutoLayout: () => void;
  clientToLocalPoint: (clientX: number, clientY: number) => { x: number; y: number };
}

function normalizePrimaryHex(raw: string | undefined | null): string {
  if (!raw) return "#8b5cf6";
  return raw.startsWith("#") ? raw : `#${raw}`;
}

const CANVAS_NODE_HEIGHT = NODE_HEADER_HEIGHT;

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useJointGraphCanvas({
  nodes,
  edges,
  primaryHex,
  onNodeClick,
  onPaneClick,
  onNodePositionChange,
}: UseJointGraphCanvasOptions): UseJointGraphCanvasReturn {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<dia.Graph | null>(null);
  const paperRef = useRef<dia.Paper | null>(null);

  const [overlayHeaders, setOverlayHeaders] = useState<CanvasOverlayHeader[]>([]);
  const [paperTransform, setPaperTransform] = useState({ sx: 1, sy: 1, tx: 0, ty: 0 });

  const primaryHexRef = useRef(primaryHex);
  primaryHexRef.current = primaryHex;

  const nodesRef = useRef(nodes);
  nodesRef.current = nodes;
  const edgesRef = useRef(edges);
  edgesRef.current = edges;

  const onNodeClickRef = useRef(onNodeClick);
  onNodeClickRef.current = onNodeClick;
  const onPaneClickRef = useRef(onPaneClick);
  onPaneClickRef.current = onPaneClick;
  const onNodePositionChangeRef = useRef(onNodePositionChange);
  onNodePositionChangeRef.current = onNodePositionChange;

  // Suppress position-sync-back while we're programmatically moving elements
  const suppressPositionSyncRef = useRef(false);

  // ── Rebuild overlay positions from JointJS element positions ──
  const rebuildOverlays = useCallback(() => {
    const graph = graphRef.current;
    const currentNodes = nodesRef.current;
    if (!graph || currentNodes.length === 0) {
      setOverlayHeaders([]);
      return;
    }

    const headers: CanvasOverlayHeader[] = [];
    for (const n of currentNodes) {
      const el = graph.getCell(n.id) as dia.Element | undefined;
      if (!el) continue;
      const pos = el.position();
      const size = el.size();
      headers.push({
        nodeId: n.id,
        label: n.data.label,
        nodeType: n.data.workspaceData?.type || "agent_node",
        x: pos.x,
        y: pos.y,
        width: NODE_WIDTH,
        nodeHeight: size.height,
      });
    }
    setOverlayHeaders(headers);
  }, []);

  // ── Initialise paper once ──
  useEffect(() => {
    if (!containerRef.current) return;

    const namespace = { ...shapes };
    const graph = new dia.Graph({}, { cellNamespace: namespace });
    graphRef.current = graph;

    const paper = new dia.Paper({
      model: graph,
      cellViewNamespace: namespace,
      width: "100%",
      height: "100%",
      interactive: { elementMove: true },
      background: { color: "transparent" },
      gridSize: 16,
      drawGrid: {
        name: "doubleMesh",
        args: [
          { color: "rgba(255,255,255,0.06)", thickness: 1 },
          { color: "rgba(255,255,255,0.12)", scaleFactor: 4, thickness: 1 },
        ],
      },
    });

    containerRef.current.replaceChildren(paper.el);
    paper.el.classList.add("joint-paper");
    paperRef.current = paper;

    const primaryNow = normalizePrimaryHex(primaryHexRef.current);
    injectSvgDefs(paper.el, primaryNow);
    injectStatusGlowFilters(paper.el);

    // ── Panning ──
    let isPanning = false;
    let panStartX = 0;
    let panStartY = 0;

    paper.el.style.cursor = "grab";

    paper.on("blank:pointerdown", (evt: dia.Event) => {
      isPanning = true;
      const ne = (evt as any).originalEvent ?? evt;
      panStartX = ne.clientX;
      panStartY = ne.clientY;
      paper.el.style.cursor = "grabbing";
    });

    const panMoveHandler = (evt: PointerEvent) => {
      if (!isPanning) return;
      const dx = evt.clientX - panStartX;
      const dy = evt.clientY - panStartY;
      panStartX = evt.clientX;
      panStartY = evt.clientY;
      const t = paper.translate();
      paper.translate(t.tx + dx, t.ty + dy);
      syncTransformState();
    };

    const panUpHandler = () => {
      if (!isPanning) return;
      isPanning = false;
      paper.el.style.cursor = "grab";
    };

    document.addEventListener("pointermove", panMoveHandler);
    document.addEventListener("pointerup", panUpHandler);

    // ── Mouse-wheel zoom ──
    const ZOOM_FACTOR = 1.1;
    const MIN_ZOOM = 0.1;
    const MAX_ZOOM = 4;

    const onMouseWheel = (_evt: dia.Event, ox: number, oy: number, delta: number) => {
      const oldScale = paper.scale().sx;
      const newScale = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, delta > 0 ? oldScale * ZOOM_FACTOR : oldScale / ZOOM_FACTOR));
      if (newScale === oldScale) return;
      const t = paper.translate();
      const scaleDiff = newScale / oldScale;
      const tx = t.tx - ox * (scaleDiff - 1) * oldScale;
      const ty = t.ty - oy * (scaleDiff - 1) * oldScale;
      paper.scale(newScale, newScale);
      paper.translate(tx, ty);
      syncTransformState();
    };

    paper.on("blank:mousewheel", onMouseWheel);
    paper.on("cell:mousewheel", (_cv: unknown, evt: dia.Event, ox: number, oy: number, delta: number) => {
      onMouseWheel(evt, ox, oy, delta);
    });

    // ── Click events ──
    paper.on("blank:pointerclick", () => {
      onPaneClickRef.current?.();
    });

    paper.on("element:pointerclick", (cellView: dia.CellView) => {
      onNodeClickRef.current?.(cellView.model.id as string);
    });

    // ── Drag end: sync position back to React state ──
    graph.on("change:position", (_el: dia.Element, _newPos: unknown, opt: any) => {
      if (suppressPositionSyncRef.current) return;
      if (opt?.skipSync) return;
      const el = _el as dia.Element;
      const pos = el.position();
      onNodePositionChangeRef.current?.(el.id as string, { x: pos.x, y: pos.y });
      safeFlushSync(() => rebuildOverlays());
    });

    function syncTransformState() {
      const s = paper.scale();
      const tr = paper.translate();
      safeFlushSync(() => {
        setPaperTransform({ sx: s.sx, sy: s.sy, tx: tr.tx, ty: tr.ty });
        rebuildOverlays();
      });
    }

    return () => {
      document.removeEventListener("pointermove", panMoveHandler);
      document.removeEventListener("pointerup", panUpHandler);
      graph.off("change:position");
      paper.remove();
      graph.clear();
      graphRef.current = null;
      paperRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rebuildOverlays]);

  // ── Sync nodes ──
  useEffect(() => {
    const graph = graphRef.current;
    const paper = paperRef.current;
    if (!graph || !paper) return;

    suppressPositionSyncRef.current = true;

    const existingElementIds = new Set(graph.getElements().map((el) => el.id as string));
    const desiredNodeIds = new Set(nodes.map((n) => n.id));

    // Remove elements that no longer exist
    for (const id of existingElementIds) {
      if (!desiredNodeIds.has(id)) {
        const cell = graph.getCell(id);
        if (cell) cell.remove();
      }
    }

    // Add or update elements
    for (const n of nodes) {
      const nodeType = n.data.workspaceData?.type || "agent_node";
      const existing = graph.getCell(n.id) as dia.Element | undefined;
      if (existing) {
        const pos = existing.position();
        if (Math.abs(pos.x - n.position.x) > 1 || Math.abs(pos.y - n.position.y) > 1) {
          existing.position(n.position.x, n.position.y, { skipSync: true });
        }
        existing.attr("body/fill", nodeFillForType(nodeType));

        // Update stroke for connection highlighting
        if (n.data.isConnectionSource) {
          existing.attr("body/stroke", normalizePrimaryHex(primaryHexRef.current));
          existing.attr("body/strokeWidth", 3);
          existing.attr("body/filter", "url(#progressGlow)");
        } else if (n.data.isConnectionTarget) {
          existing.attr("body/stroke", `${normalizePrimaryHex(primaryHexRef.current)}66`);
          existing.attr("body/strokeWidth", 2);
          existing.attr("body/filter", STATUS_STYLES.IDLE.filter);
        } else {
          existing.attr("body/stroke", STATUS_STYLES.IDLE.stroke);
          existing.attr("body/strokeWidth", STATUS_STYLES.IDLE.strokeWidth);
          existing.attr("body/filter", STATUS_STYLES.IDLE.filter);
        }
      } else {
        const isSource = n.data.isConnectionSource;
        const isTarget = n.data.isConnectionTarget;
        const strokeColor = isSource
          ? normalizePrimaryHex(primaryHexRef.current)
          : isTarget
            ? `${normalizePrimaryHex(primaryHexRef.current)}66`
            : STATUS_STYLES.IDLE.stroke;
        const strokeWidth = isSource ? 3 : isTarget ? 2 : STATUS_STYLES.IDLE.strokeWidth;

        new shapes.standard.Rectangle({
          id: n.id,
          position: { x: n.position.x, y: n.position.y },
          size: { width: NODE_WIDTH, height: CANVAS_NODE_HEIGHT },
          attrs: {
            body: {
              fill: nodeFillForType(nodeType),
              stroke: strokeColor,
              strokeWidth,
              rx: 12,
              ry: 12,
              filter: isSource ? "url(#progressGlow)" : STATUS_STYLES.IDLE.filter,
            },
            label: { text: "" },
          },
        }).addTo(graph);
      }
    }

    suppressPositionSyncRef.current = false;
    rebuildOverlays();
  }, [nodes, rebuildOverlays]);

  // ── Sync edges ──
  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;

    const existingLinkIds = new Set(graph.getLinks().map((l) => l.id as string));
    const desiredEdgeIds = new Set(edges.map((e) => e.id));

    for (const id of existingLinkIds) {
      if (!desiredEdgeIds.has(id)) {
        const cell = graph.getCell(id);
        if (cell) cell.remove();
      }
    }

    const linkColor = normalizePrimaryHex(primaryHexRef.current);
    for (const e of edges) {
      if (existingLinkIds.has(e.id)) continue;

      const isCond = e.data?.isConditional;
      const c = isCond ? "#94a3b8" : linkColor;

      new shapes.standard.Link({
        id: e.id,
        source: { id: e.source },
        target: { id: e.target },
        attrs: {
          line: {
            stroke: isCond ? "rgba(148, 163, 184, 0.8)" : c,
            strokeWidth: isCond ? 1.5 : 2,
            opacity: isCond ? 1 : 0.9,
            sourceMarker: { type: "circle" as const, r: isCond ? 3 : 4, fill: c },
            targetMarker: { type: "classic" as const, size: isCond ? 10 : 12, fill: c },
          },
        },
      }).addTo(graph);
    }
  }, [edges]);

  // ── Theme colour update ──
  useEffect(() => {
    const paper = paperRef.current;
    const graph = graphRef.current;
    if (!paper || !graph) return;

    const primaryNow = normalizePrimaryHex(primaryHex);
    injectSvgDefs(paper.el, primaryNow);

    for (const link of graph.getLinks()) {
      const edgeData = edgesRef.current.find((e) => e.id === link.id);
      if (edgeData?.data?.isConditional) continue;
      link.attr("line/stroke", primaryNow);
      link.attr("line/sourceMarker/fill", primaryNow);
      link.attr("line/targetMarker/fill", primaryNow);
    }
  }, [primaryHex]);

  // ── Zoom / fit-to-view ──
  const syncTransform = useCallback(() => {
    const paper = paperRef.current;
    if (!paper) return;
    const s = paper.scale();
    const tr = paper.translate();
    safeFlushSync(() => {
      setPaperTransform({ sx: s.sx, sy: s.sy, tx: tr.tx, ty: tr.ty });
      rebuildOverlays();
    });
  }, [rebuildOverlays]);

  const handleZoomIn = useCallback(() => {
    const paper = paperRef.current;
    if (!paper) return;
    const { sx } = paper.scale();
    paper.scale(sx * 1.2, sx * 1.2);
    syncTransform();
  }, [syncTransform]);

  const handleZoomOut = useCallback(() => {
    const paper = paperRef.current;
    if (!paper) return;
    const { sx } = paper.scale();
    const ns = Math.max(sx / 1.2, 0.1);
    paper.scale(ns, ns);
    syncTransform();
  }, [syncTransform]);

  const handleFitToView = useCallback(() => {
    const paper = paperRef.current;
    const container = containerRef.current;
    if (!paper) return;
    try {
      paper.scale(1, 1);
      paper.translate(0, 0);
      if (container) {
        const cw = container.clientWidth;
        const ch = container.clientHeight;
        if (cw > 0 && ch > 0) paper.setDimensions(cw, ch);
      }
      paper.transformToFitContent(SCALE_CONTENT_TO_FIT_OPTS);
    } catch {
      return;
    }
    syncTransform();
  }, [syncTransform]);

  // ── Auto-layout ──
  const runAutoLayout = useCallback(() => {
    const graph = graphRef.current;
    if (!graph || graph.getElements().length === 0) return;

    suppressPositionSyncRef.current = true;
    DirectedGraph.layout(graph, LAYOUT_OPTS);

    // Push final_answer_node to the bottom
    const currentNodes = nodesRef.current;
    const typeById = new Map(currentNodes.map((n) => [n.id, n.data.workspaceData?.type]));
    let maxBottom = 0;
    graph.getElements().forEach((el) => {
      if (typeById.get(el.id as string) !== "final_answer_node") {
        const b = el.getBBox();
        maxBottom = Math.max(maxBottom, b.y + b.height);
      }
    });
    graph.getElements().forEach((el) => {
      if (typeById.get(el.id as string) === "final_answer_node") {
        const pos = el.position();
        el.position(pos.x, maxBottom + LAYOUT_OPTS.rankSep);
      }
    });

    // Sync positions back to React state
    for (const el of graph.getElements()) {
      const pos = el.position();
      onNodePositionChangeRef.current?.(el.id as string, { x: pos.x, y: pos.y });
    }

    suppressPositionSyncRef.current = false;
    rebuildOverlays();
  }, [rebuildOverlays]);

  // ── Paper coordinate helper for drop events ──
  const clientToLocalPoint = useCallback((clientX: number, clientY: number) => {
    const paper = paperRef.current;
    if (!paper) return { x: clientX, y: clientY };
    const p = paper.clientToLocalPoint({ x: clientX, y: clientY });
    return { x: p.x, y: p.y };
  }, []);

  return {
    containerRef,
    paperRef,
    graphRef,
    overlayHeaders,
    paperTransform,
    handleZoomIn,
    handleZoomOut,
    handleFitToView,
    runAutoLayout,
    clientToLocalPoint,
  };
}
