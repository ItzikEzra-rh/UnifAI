/**
 * useJointGraph – custom hook encapsulating the imperative JointJS graph
 * initialisation, data-fetching, layout, SVG injection, and sizing logic that
 * was previously inlined in the main useEffect of GraphDisplay.
 *
 * Keeps GraphDisplay lean by separating React rendering from the imperative
 * JointJS/DOM manipulation.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { dia, shapes } from "@joint/core";
import { DirectedGraph } from "@joint/layout-directed-graph";
import type { GraphFlow } from "@/components/agentic-ai/graphs/interfaces";
import {
  graphFlowToLayoutData,
  type LayoutNode,
} from "@/utils/graphFlowLayout";
import { getBlueprintInfo } from "@/api/blueprints";
import type { BuildingBlock } from "@/types/graph";
import {
  NODE_WIDTH,
  NODE_HEADER_HEIGHT,
  ELEMENT_BADGE_HEIGHT,
  ELEMENT_GAP,
  NODE_BODY_PADDING,
  LAYOUT_OPTS,
  STATUS_STYLES,
  computeNodeHeight,
  nodeFillForType,
  injectSvgDefs,
  injectStatusGlowFilters,
  injectLinkAnimations,
  removeLinkAnimations,
  buildElementBlockMap,
  type OverlayBadge,
  type OverlayHeader,
} from "@/components/agentic-ai/graphs/GraphDisplayHelpers";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UseJointGraphOptions {
  blueprintId?: string;
  primaryHex?: string;
  /** Pre-fetched spec_dict – when provided, skips the network fetch entirely. */
  specDict?: any;
  showBackground?: boolean;
  interactive?: boolean;
  centerInView?: boolean;
  animated?: boolean;
}

export interface UseJointGraphReturn {
  containerRef: React.RefObject<HTMLDivElement>;
  graphRef: React.MutableRefObject<dia.Graph | null>;
  layoutNodesRef: React.MutableRefObject<LayoutNode[]>;
  elementBlockRef: React.MutableRefObject<Map<string, BuildingBlock>>;
  loading: boolean;
  error: string | null;
  overlayBadges: OverlayBadge[];
  overlayHeaders: OverlayHeader[];
  paperTransform: { sx: number; sy: number; tx: number; ty: number };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useJointGraph({
  blueprintId,
  primaryHex,
  specDict,
  showBackground = true,
  interactive = false,
  centerInView = false,
  animated = false,
}: UseJointGraphOptions): UseJointGraphReturn {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<dia.Graph | null>(null);
  const layoutNodesRef = useRef<LayoutNode[]>([]);
  const elementBlockRef = useRef<Map<string, BuildingBlock>>(new Map());
  const paperRef = useRef<dia.Paper | null>(null);
  const conditionalLinkIdsRef = useRef<Set<string>>(new Set());

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overlayBadges, setOverlayBadges] = useState<OverlayBadge[]>([]);
  const [overlayHeaders, setOverlayHeaders] = useState<OverlayHeader[]>([]);
  const [paperTransform, setPaperTransform] = useState({
    sx: 1, sy: 1, tx: 0, ty: 0,
  });

  // Keep mutable ref so the async callback always reads the latest primary color.
  const primaryHexRef = useRef(primaryHex);
  primaryHexRef.current = primaryHex;

  // ── Rebuild overlay positions from current graph element positions ──
  const rebuildOverlays = useCallback(() => {
    const graph = graphRef.current;
    const nodes = layoutNodesRef.current;
    if (!graph || nodes.length === 0) return;

    const headers: OverlayHeader[] = [];
    const badges: OverlayBadge[] = [];

    for (const n of nodes) {
      const el = graph.getCell(n.id);
      if (!el) continue;
      const pos = (el as dia.Element).position();
      const size = (el as dia.Element).size();
      const hasElements = n.resolvedElements.length > 0;

      headers.push({
        nodeId: n.id,
        label: n.label,
        nodeType: n.type,
        hasElements,
        x: pos.x,
        y: pos.y,
        width: NODE_WIDTH,
        nodeHeight: size.height,
        nodeRid: n.nodeDefinition?.rid,
      });

      if (!hasElements) continue;
      const bodyStartY = pos.y + NODE_HEADER_HEIGHT + NODE_BODY_PADDING;
      const badgeInnerWidth = NODE_WIDTH - NODE_BODY_PADDING * 2;
      n.resolvedElements.forEach((re, i) => {
        badges.push({
          nodeId: n.id,
          element: re,
          x: pos.x + NODE_BODY_PADDING,
          y: bodyStartY + i * (ELEMENT_BADGE_HEIGHT + ELEMENT_GAP),
          width: badgeInnerWidth,
        });
      });
    }

    setOverlayHeaders(headers);
    setOverlayBadges(badges);
  }, []);

  // ── Main effect: fetch blueprint → build JointJS graph → layout ────
  useEffect(() => {
    if ((!blueprintId && !specDict) || !containerRef.current) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setOverlayBadges([]);
    setOverlayHeaders([]);

    const namespace = { ...shapes };
    const graph = new dia.Graph({}, { cellNamespace: namespace });
    graphRef.current = graph;

    const paper = new dia.Paper({
      model: graph,
      cellViewNamespace: namespace,
      width: "100%",
      height: "100%",
      interactive: interactive ? { elementMove: true } : false,
      background: showBackground ? { color: "transparent" } : undefined,
      gridSize: 16,
      drawGrid: showBackground
        ? {
            name: "doubleMesh",
            args: [
              { color: "rgba(255,255,255,0.06)", thickness: 1 },
              { color: "rgba(255,255,255,0.12)", scaleFactor: 4, thickness: 1 },
            ],
          }
        : false,
    });

    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(paper.el);
    paper.el.classList.add("joint-paper");
    paperRef.current = paper;

    let cancelled = false;
    (async () => {
      try {
        // Use provided specDict directly if available, otherwise fetch single blueprint
        let spec: GraphFlow;
        if (specDict) {
          spec = specDict as GraphFlow;
        } else if (blueprintId) {
          const blueprintInfo = await getBlueprintInfo(blueprintId);
          if (cancelled) return;
          if (!blueprintInfo?.spec_dict) {
            setError("Workflow not found");
            setLoading(false);
            return;
          }
          spec = blueprintInfo.spec_dict as GraphFlow;
        } else {
          setLoading(false);
          return;
        }
        const { nodes: layoutNodes, edges: layoutEdges } =
          graphFlowToLayoutData(spec);
        layoutNodesRef.current = layoutNodes;
        elementBlockRef.current = buildElementBlockMap(layoutNodes, spec);

        if (layoutNodes.length === 0) {
          setError("No steps in workflow");
          setLoading(false);
          return;
        }

        // SVG defs: gradients + shadow + status glow filters
        const primaryNow = primaryHexRef.current || "#8b5cf6";
        injectSvgDefs(paper.el, primaryNow);
        injectStatusGlowFilters(paper.el);

        // Create JointJS nodes
        for (const n of layoutNodes) {
          new shapes.standard.Rectangle({
            id: n.id,
            position: { x: 0, y: 0 },
            size: {
              width: NODE_WIDTH,
              height: computeNodeHeight(n.resolvedElements.length),
            },
            attrs: {
              body: {
                fill: nodeFillForType(n.type),
                stroke: STATUS_STYLES.IDLE.stroke,
                strokeWidth: STATUS_STYLES.IDLE.strokeWidth,
                rx: 12,
                ry: 12,
                filter: STATUS_STYLES.IDLE.filter,
              },
              label: { text: "" },
            },
          }).addTo(graph);
        }

        // Create edges
        const linkColor = primaryHexRef.current?.startsWith("#")
          ? primaryHexRef.current
          : `#${primaryHexRef.current || "8b5cf6"}`;

        const mkMarker = (color: string, r: number) => ({
          type: "circle" as const, r, fill: color,
        });

        conditionalLinkIdsRef.current.clear();
        for (const e of layoutEdges) {
          const isCond = e.isConditional;
          const c = isCond ? "#94a3b8" : linkColor;
          const link = new shapes.standard.Link({
            source: { id: e.source },
            target: { id: e.target },
            attrs: {
              line: {
                stroke: isCond ? "rgba(148, 163, 184, 0.8)" : c,
                strokeWidth: isCond ? 1.5 : 2,
                opacity: isCond ? 1 : 0.9,
                sourceMarker: mkMarker(c, isCond ? 3 : 4),
                targetMarker: { type: "classic", size: isCond ? 10 : 12, fill: c },
              },
            },
          }).addTo(graph);
          if (isCond) conditionalLinkIdsRef.current.add(link.id as string);
        }

        // Auto-layout
        const bbox = DirectedGraph.layout(graph, LAYOUT_OPTS);

        // Force final_answer_node to the bottom
        const typeById = new Map(layoutNodes.map((n) => [n.id, n.type]));
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

        // Recompute bounding box after manual repositioning of final_answer_node
        let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
        graph.getElements().forEach((el) => {
          const b = el.getBBox();
          minX = Math.min(minX, b.x);
          minY = Math.min(minY, b.y);
          maxX = Math.max(maxX, b.x + b.width);
          maxY = Math.max(maxY, b.y + b.height);
        });
        const actualBbox = {
          width: maxX - (Number.isFinite(minX) ? minX : 0),
          height: maxY - (Number.isFinite(minY) ? minY : 0),
        };

        // Size paper and optionally center
        const padding = 40;
        const container = containerRef.current;
        if (!container) return;
        const cw = container.clientWidth ?? 0;
        const ch = container.clientHeight ?? 0;

        if (centerInView && cw > 0 && ch > 0) {
          paper.setDimensions(cw, ch);
          paper.scaleContentToFit({
            padding,
            preserveAspectRatio: true,
            verticalAlign: "middle",
            horizontalAlign: "middle",
            useModelGeometry: true,
          });
        } else {
          paper.setDimensions(
            Math.max(actualBbox.width + padding * 2, cw > 0 ? cw : 400),
            Math.max(actualBbox.height + padding * 2, ch > 0 ? ch : 300),
          );
        }

        if (animated) {
          injectLinkAnimations(paper.el);
        }

        const scale = paper.scale();
        const translate = paper.translate();
        setPaperTransform({ sx: scale.sx, sy: scale.sy, tx: translate.tx, ty: translate.ty });

        rebuildOverlays();
        if (interactive) graph.on("change:position", rebuildOverlays);

        setLoading(false);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load workflow");
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      graph.off("change:position");
      removeLinkAnimations(paper.el);
      paper.remove();
      graph.clear();
      graphRef.current = null;
      paperRef.current = null;
      layoutNodesRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [blueprintId, specDict, showBackground, interactive, centerInView, animated, rebuildOverlays]);

  // ── Lightweight theme-color update (avoids full graph rebuild) ──────
  useEffect(() => {
    const paper = paperRef.current;
    const graph = graphRef.current;
    if (!paper || !graph) return;

    const primaryNow = primaryHex || "#8b5cf6";
    injectSvgDefs(paper.el, primaryNow);

    const linkColor = primaryNow.startsWith("#") ? primaryNow : `#${primaryNow}`;
    for (const link of graph.getLinks()) {
      if (conditionalLinkIdsRef.current.has(link.id as string)) continue;
      link.attr("line/stroke", linkColor);
      link.attr("line/sourceMarker/fill", linkColor);
      link.attr("line/targetMarker/fill", linkColor);
    }
  }, [primaryHex]);

  return {
    containerRef,
    graphRef,
    layoutNodesRef,
    elementBlockRef,
    loading,
    error,
    overlayBadges,
    overlayHeaders,
    paperTransform,
  };
}
