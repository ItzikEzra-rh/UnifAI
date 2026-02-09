import React, { useEffect, useRef, useState, useCallback } from "react";
import { dia, shapes } from "@joint/core";
import { DirectedGraph } from "@joint/layout-directed-graph";
import type { GraphFlow } from "./interfaces";
import {
  graphFlowToLayoutData,
  type LayoutNode,
} from "@/utils/graphFlowLayout";
import { useTheme } from "@/contexts/ThemeContext";
import axios from "@/http/axiosAgentConfig";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspaceData } from "@/hooks/use-workspace-data";
import { getCategoryDisplay } from "@/components/shared/helpers";
import type { BuildingBlock } from "@/types/graph";
import ResourceDetailsModal from "@/workspace/ResourceDetailsModal";
import NodeValidationIndicator from "./NodeValidationIndicator";
import { ValidationResultModal } from "../workspace/ValidationResultModal";
import type { ElementValidationResult } from "@/types/validation";
import {
  NODE_WIDTH,
  NODE_HEADER_HEIGHT,
  ELEMENT_BADGE_HEIGHT,
  ELEMENT_GAP,
  NODE_BODY_PADDING,
  LAYOUT_OPTS,
  BADGE_BG,
  BADGE_BORDER,
  BADGE_HOVER_BG,
  CATEGORY_TYPE_TO_PLURAL,
  nodeIconForType,
  computeNodeHeight,
  nodeFillForType,
  injectSvgDefs,
  injectLinkAnimations,
  buildElementBlockMap,
  type OverlayBadge,
  type OverlayHeader,
} from "./GraphDisplayHelpers";

export type GraphDisplayProps = {
  blueprintId?: string;
  height?: string;
  showBackground?: boolean;
  interactive?: boolean;
  /** When true, scale and center the graph in the container. */
  centerInView?: boolean;
  /** When true, enable subtle animations. */
  animated?: boolean;
  /** Per-node validation results keyed by node RID. */
  validationResults?: Record<string, ElementValidationResult>;
  /** Whether validation is currently in progress. */
  isValidating?: boolean;
};

export default function GraphDisplay({
  blueprintId,
  height = "100%",
  showBackground = true,
  interactive = false,
  centerInView = false,
  animated = false,
  validationResults,
  isValidating = false,
}: GraphDisplayProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);
  const elementBlockRef = useRef<Map<string, BuildingBlock>>(new Map());
  const graphRef = useRef<dia.Graph | null>(null);
  const layoutNodesRef = useRef<LayoutNode[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resourceDetailsOpen, setResourceDetailsOpen] = useState(false);
  const [resourceDetailsElement, setResourceDetailsElement] =
    useState<BuildingBlock | null>(null);
  const [loadingResource, setLoadingResource] = useState(false);
  const [overlayBadges, setOverlayBadges] = useState<OverlayBadge[]>([]);
  const [overlayHeaders, setOverlayHeaders] = useState<OverlayHeader[]>([]);
  /** Paper transform (scale + translate) so overlays match SVG coordinates. */
  const [paperTransform, setPaperTransform] = useState({
    sx: 1,
    sy: 1,
    tx: 0,
    ty: 0,
  });
  const [selectedValidationResult, setSelectedValidationResult] =
    useState<ElementValidationResult | null>(null);
  const [isValidationModalOpen, setIsValidationModalOpen] = useState(false);

  const { user } = useAuth();
  const { primaryHex } = useTheme();
  const { fetchResourceById } = useWorkspaceData();
  const primaryHexRef = useRef(primaryHex);
  primaryHexRef.current = primaryHex;

  // ── Open resource details modal ──────────────────────────────────────

  const openElementDetails = useCallback(
    (elementId: string) => {
      const block = elementBlockRef.current.get(elementId);
      if (block) {
        setResourceDetailsElement(block);
        setResourceDetailsOpen(true);
        return;
      }

      setLoadingResource(true);
      fetchResourceById(elementId)
        .then((resource) => {
          if (!resource) return;
          const display = getCategoryDisplay(resource.category);
          const built: BuildingBlock = {
            id: resource.rid,
            type: resource.type,
            label: resource.name,
            color: display.color,
            description: `${resource.category}/${resource.type} - ${resource.name}`,
            workspaceData: {
              rid: resource.rid,
              name: resource.name,
              category: resource.category,
              type: resource.type,
              config: resource.cfg_dict,
              version: resource.version ?? 1,
              created: resource.created ?? "",
              updated: resource.updated ?? "",
              nested_refs: resource.nested_refs ?? [],
            },
          };
          setResourceDetailsElement(built);
          setResourceDetailsOpen(true);
        })
        .catch(() => {
          /* resource not found – silent */
        })
        .finally(() => setLoadingResource(false));
    },
    [fetchResourceById],
  );

  // ── Rebuild overlay positions from current graph element positions ───

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

  // ── Main effect: fetch blueprint → build JointJS graph → layout ─────

  useEffect(() => {
    if (!blueprintId || !containerRef.current) return;

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
              {
                color: "rgba(255,255,255,0.12)",
                scaleFactor: 4,
                thickness: 1,
              },
            ],
          }
        : false,
    });

    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(paper.el);
    paper.el.classList.add("joint-paper");

    (async () => {
      try {
        const response = await axios.get(
          `/blueprints/available.blueprints.resolved.get?userId=${user?.username || "default"}`,
        );
        const list = response.data || [];
        const blueprint = list.find(
          (b: { blueprint_id: string }) => b.blueprint_id === blueprintId,
        );
        if (!blueprint?.spec_dict) {
          setError("Workflow not found");
          setLoading(false);
          return;
        }

        const spec = blueprint.spec_dict as GraphFlow;
        const { nodes: layoutNodes, edges: layoutEdges } =
          graphFlowToLayoutData(spec);
        layoutNodesRef.current = layoutNodes;

        // Build element → BuildingBlock lookup for overlay badges
        elementBlockRef.current = buildElementBlockMap(layoutNodes, spec);

        if (layoutNodes.length === 0) {
          setError("No steps in workflow");
          setLoading(false);
          return;
        }

        // Inject SVG gradient defs + shadow filter
        const primaryNow = primaryHexRef.current || "#8b5cf6";
        injectSvgDefs(paper.el, primaryNow);

        // Create JointJS rectangle nodes
        for (const n of layoutNodes) {
          const rect = new shapes.standard.Rectangle({
            id: n.id,
            position: { x: 0, y: 0 },
            size: {
              width: NODE_WIDTH,
              height: computeNodeHeight(n.resolvedElements.length),
            },
            attrs: {
              body: {
                fill: nodeFillForType(n.type),
                stroke: "rgba(255,255,255,0.12)",
                strokeWidth: 1,
                rx: 12,
                ry: 12,
                filter: "url(#nodeShadow)",
              },
              label: { text: "" },
            },
          });
          rect.addTo(graph);
        }

        // Create edges
        const linkColor = primaryHexRef.current?.startsWith("#")
          ? primaryHexRef.current
          : `#${primaryHexRef.current || "8b5cf6"}`;

        const linkStyle = {
          attrs: {
            line: {
              stroke: linkColor,
              strokeWidth: 2,
              opacity: 0.9,
              sourceMarker: { type: "circle", r: 4, fill: linkColor },
              targetMarker: { type: "classic", size: 12, fill: linkColor },
            },
          },
        };

        const conditionalLinkStyle = {
          attrs: {
            line: {
              stroke: "rgba(148, 163, 184, 0.8)",
              strokeWidth: 1.5,
              sourceMarker: { type: "circle", r: 3, fill: "#94a3b8" },
              targetMarker: { type: "classic", size: 10, fill: "#94a3b8" },
            },
          },
        };

        for (const e of layoutEdges) {
          const link = new shapes.standard.Link({
            source: { id: e.source },
            target: { id: e.target },
            ...(e.isConditional ? conditionalLinkStyle : linkStyle),
          });
          link.addTo(graph);
        }

        // Auto-layout
        const bbox = DirectedGraph.layout(graph, LAYOUT_OPTS);

        // Force final_answer_node to the bottom layer
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

        // Size paper and optionally center
        const padding = 40;
        const container = containerRef.current!;
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
            Math.max(bbox.width + padding * 2, cw > 0 ? cw : 400),
            Math.max(bbox.height + padding * 2, ch > 0 ? ch : 300),
          );
        }

        // Animate link paths with flowing dashes
        injectLinkAnimations(paper.el);

        // Read paper transform so overlays align with SVG nodes
        const scale = paper.scale();
        const translate = paper.translate();
        setPaperTransform({
          sx: scale.sx,
          sy: scale.sy,
          tx: translate.tx,
          ty: translate.ty,
        });

        // Build initial overlay positions
        rebuildOverlays();

        // When user drags a node, rebuild overlays so they follow
        if (interactive) {
          graph.on("change:position", rebuildOverlays);
        }

        setLoading(false);
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Failed to load workflow",
        );
        setLoading(false);
      }
    })();

    return () => {
      graph.off("change:position");
      paper.remove();
      graph.clear();
      graphRef.current = null;
      layoutNodesRef.current = [];
    };
    // Note: openElementDetails is intentionally excluded – it is only used by
    // overlay click handlers (rendered via JSX), not inside this effect body.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    blueprintId,
    user?.username,
    showBackground,
    interactive,
    centerInView,
    primaryHex,
    rebuildOverlays,
  ]);

  // ── Render ───────────────────────────────────────────────────────────

  return (
    <>
      <div className="relative overflow-auto" style={{ height }}>
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background-dark/80 text-gray-400">
            Loading graph...
          </div>
        )}
        {error && !loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center text-gray-400">
            {error}
          </div>
        )}
        {loadingResource && (
          <div className="absolute bottom-4 left-4 z-20 text-xs text-gray-400 bg-background-dark/90 px-3 py-1.5 rounded-md">
            Loading resource...
          </div>
        )}

        <div
          className={`workflow-graph-wrap h-full min-h-[280px] rounded-2xl relative ${
            animated ? "workflow-graph-animated" : ""
          }`}
        >
          <div
            ref={containerRef}
            className="min-h-full min-w-full h-full"
            style={{ height }}
          />

          {/* HTML overlay for node headers + element badges */}
          {(overlayHeaders.length > 0 || overlayBadges.length > 0) && (
            <div
              className="absolute inset-0 pointer-events-none"
              style={{ overflow: "hidden" }}
            >
              {/* Node headers (icon + title) */}
              {overlayHeaders.map((hdr) => {
                const left = hdr.x * paperTransform.sx + paperTransform.tx;
                const top = hdr.y * paperTransform.sy + paperTransform.ty;
                const width = hdr.width * paperTransform.sx;
                const hdrHeight = hdr.hasElements
                  ? NODE_HEADER_HEIGHT * paperTransform.sy
                  : hdr.nodeHeight * paperTransform.sy;
                const icon = nodeIconForType(hdr.nodeType);
                const circleSize = Math.max(20, 26 * paperTransform.sx);
                const iconFontSize = Math.max(12, 14 * paperTransform.sx);
                return (
                  <div
                    key={`hdr-${hdr.nodeId}`}
                    className="absolute"
                    style={{
                      left,
                      top,
                      width,
                      height: hdrHeight,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 6 * paperTransform.sx,
                      borderBottom: hdr.hasElements
                        ? "1px solid rgba(255,255,255,0.12)"
                        : "none",
                    }}
                  >
                    <span
                      style={{
                        width: circleSize,
                        height: circleSize,
                        borderRadius: "50%",
                        background: "rgba(255,255,255,0.25)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: iconFontSize,
                        lineHeight: 1,
                        flexShrink: 0,
                      }}
                      aria-hidden="true"
                    >
                      {icon}
                    </span>
                    <span
                      style={{
                        color: "rgba(255,255,255,0.95)",
                        fontSize: Math.max(9, 12 * paperTransform.sx),
                        fontWeight: 600,
                        fontFamily: "system-ui, -apple-system, sans-serif",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        maxWidth: width - 40 * paperTransform.sx,
                      }}
                    >
                      {hdr.label}
                    </span>
                  </div>
                );
              })}

              {/* Validation indicators (top-right corner of each node) */}
              {overlayHeaders.map((hdr) => {
                const vResult =
                  hdr.nodeRid && validationResults
                    ? validationResults[hdr.nodeRid]
                    : undefined;
                if (!isValidating && !(vResult && !vResult.is_valid))
                  return null;
                const left =
                  (hdr.x + hdr.width) * paperTransform.sx +
                  paperTransform.tx -
                  12;
                const top =
                  hdr.y * paperTransform.sy + paperTransform.ty - 6;
                return (
                  <div
                    key={`val-${hdr.nodeId}`}
                    className="absolute z-10 pointer-events-auto"
                    style={{ left, top }}
                  >
                    <NodeValidationIndicator
                      validationResult={vResult}
                      isValidating={isValidating}
                      onClick={() => {
                        if (vResult) {
                          setSelectedValidationResult(vResult);
                          setIsValidationModalOpen(true);
                        }
                      }}
                    />
                  </div>
                );
              })}

              {/* Element badges */}
              {overlayBadges.map((badge, i) => {
                const category =
                  CATEGORY_TYPE_TO_PLURAL[badge.element.type] || "default";
                const display = getCategoryDisplay(category);
                const left =
                  badge.x * paperTransform.sx + paperTransform.tx;
                const top =
                  badge.y * paperTransform.sy + paperTransform.ty;
                const width = badge.width * paperTransform.sx;
                const bHeight = ELEMENT_BADGE_HEIGHT * paperTransform.sy;
                return (
                  <button
                    key={`${badge.nodeId}-${badge.element.id}-${i}`}
                    type="button"
                    className="absolute flex items-center rounded-full border transition-all duration-150 pointer-events-auto"
                    style={{
                      left,
                      top,
                      width,
                      height: bHeight,
                      background: BADGE_BG,
                      borderColor: BADGE_BORDER,
                      backdropFilter: "blur(6px)",
                      WebkitBackdropFilter: "blur(6px)",
                      fontSize: Math.max(9, 11 * paperTransform.sx),
                      paddingLeft: 4 * paperTransform.sx,
                      paddingRight: 8 * paperTransform.sx,
                      gap: 5 * paperTransform.sx,
                      cursor: interactive ? "pointer" : "default",
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (interactive) openElementDetails(badge.element.id);
                    }}
                    onMouseEnter={(e) => {
                      if (interactive) {
                        (e.currentTarget as HTMLElement).style.background =
                          BADGE_HOVER_BG;
                        (
                          e.currentTarget as HTMLElement
                        ).style.borderColor = "rgba(255,255,255,0.22)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background =
                        BADGE_BG;
                      (e.currentTarget as HTMLElement).style.borderColor =
                        BADGE_BORDER;
                    }}
                    tabIndex={interactive ? 0 : -1}
                  >
                    {/* Category icon */}
                    <span
                      style={{
                        flexShrink: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#fff",
                      }}
                      className="[&>svg]:w-3.5 [&>svg]:h-3.5"
                    >
                      {display.icon}
                    </span>
                    <span
                      className="truncate"
                      style={{
                        color: "rgba(255,255,255,0.88)",
                        fontWeight: 500,
                        letterSpacing: "0.01em",
                        maxWidth: width - 40 * paperTransform.sx,
                      }}
                    >
                      {badge.element.name}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <ResourceDetailsModal
        isOpen={resourceDetailsOpen}
        onClose={setResourceDetailsOpen}
        element={resourceDetailsElement}
      />

      <ValidationResultModal
        validationResult={selectedValidationResult}
        isOpen={isValidationModalOpen}
        onOpenChange={setIsValidationModalOpen}
        showRefreshButton={false}
      />
    </>
  );
}
