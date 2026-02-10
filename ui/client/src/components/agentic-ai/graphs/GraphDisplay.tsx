import React, { useContext, useEffect, useRef, useState, useCallback, useMemo } from "react";
import { dia } from "@joint/core";
import { motion } from "framer-motion";
import { useTheme } from "@/contexts/ThemeContext";
import { useWorkspaceData } from "@/hooks/use-workspace-data";
import { useJointGraph } from "@/hooks/use-joint-graph";
import { getCategoryDisplay } from "@/components/shared/helpers";
import type { BuildingBlock } from "@/types/graph";
import ResourceDetailsModal from "@/workspace/ResourceDetailsModal";
import NodeValidationIndicator from "./NodeValidationIndicator";
import { ValidationResultModal } from "../workspace/ValidationResultModal";
import type { ElementValidationResult } from "@/types/validation";
import { StreamingDataContext } from "../StreamingDataContext";
import {
  NODE_WIDTH,
  NODE_HEADER_HEIGHT,
  ELEMENT_BADGE_HEIGHT,
  BADGE_BG,
  BADGE_BORDER,
  BADGE_HOVER_BG,
  CATEGORY_TYPE_TO_PLURAL,
  STATUS_STYLES,
  nodeIconForType,
} from "./GraphDisplayHelpers";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type NodeStatus = "IDLE" | "PROGRESS" | "DONE";

export type GraphDisplayProps = {
  blueprintId?: string;
  /** Pre-fetched spec_dict – when provided, skips the network fetch entirely. */
  specDict?: any;
  height?: string;
  showBackground?: boolean;
  interactive?: boolean;
  /** Scale and center the graph in the container. */
  centerInView?: boolean;
  /** Enable subtle link animations. */
  animated?: boolean;
  /** Per-node validation results keyed by node RID. */
  validationResults?: Record<string, ElementValidationResult>;
  /** Whether validation is currently in progress. */
  isValidating?: boolean;
  /** Enable live node status tracking from streaming data. */
  isLiveRequest?: boolean;
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function GraphDisplay({
  blueprintId,
  specDict,
  height = "100%",
  showBackground = true,
  interactive = false,
  centerInView = false,
  animated = false,
  validationResults,
  isValidating = false,
  isLiveRequest = false,
}: GraphDisplayProps): React.ReactElement {
  // ── JointJS graph hook (imperative init, layout, SVG injection) ─────
  const { primaryHex } = useTheme();

  const {
    containerRef,
    graphRef,
    elementBlockRef,
    loading,
    error,
    overlayBadges,
    overlayHeaders,
    paperTransform,
  } = useJointGraph({
    blueprintId,
    primaryHex,
    specDict,
    showBackground,
    interactive,
    centerInView,
    animated,
  });

  // ── Component-level state ──────────────────────────────────────────
  const [resourceDetailsOpen, setResourceDetailsOpen] = useState(false);
  const [resourceDetailsElement, setResourceDetailsElement] =
    useState<BuildingBlock | null>(null);
  const [loadingResource, setLoadingResource] = useState(false);
  const [selectedValidationResult, setSelectedValidationResult] =
    useState<ElementValidationResult | null>(null);
  const [isValidationModalOpen, setIsValidationModalOpen] = useState(false);
  const [nodeStatusMap, setNodeStatusMap] = useState<Record<string, NodeStatus>>({});
  const nodeStatusMapRef = useRef<Record<string, NodeStatus>>({});

  // ── Hooks / context ─────────────────────────────────────────────────
  const { fetchResourceById } = useWorkspaceData();

  // Safe context access – returns null when no StreamingDataProvider is mounted
  // (e.g. AgenticOverview), avoiding the throw from useStreamingData().
  const streamingContext = useContext(StreamingDataContext);

  // ── Helper: apply status visual to a single JointJS element ────────

  const applyNodeVisual = useCallback(
    (el: dia.Element, status: NodeStatus | undefined) => {
      const s = STATUS_STYLES[status ?? "IDLE"];
      el.attr("body/stroke", s.stroke);
      el.attr("body/strokeWidth", s.strokeWidth);
      el.attr("body/filter", s.filter);
    },
    [],
  );

  // ── Live node status tracking (ported from ReactFlowGraph) ─────────

  const updateNodeStatuses = useCallback(() => {
    if (!streamingContext) return;

    const currentNodeList = streamingContext.nodeListRef.current;
    const newStatusMap: Record<string, NodeStatus> = {};

    currentNodeList.forEach((nodeEntry, nodeId) => {
      if (nodeEntry.stream === "PROGRESS") newStatusMap[nodeId] = "PROGRESS";
      else if (nodeEntry.stream === "DONE") newStatusMap[nodeId] = "DONE";
      else newStatusMap[nodeId] = "IDLE";
    });

    // Shallow-compare against ref to avoid expensive JSON.stringify
    const prevMap = nodeStatusMapRef.current;
    const newKeys = Object.keys(newStatusMap);
    const prevKeys = Object.keys(prevMap);
    const hasChanges =
      newKeys.length !== prevKeys.length ||
      newKeys.some((k) => newStatusMap[k] !== prevMap[k]);

    if (hasChanges) {
      nodeStatusMapRef.current = newStatusMap;
      setNodeStatusMap(newStatusMap);

      const graph = graphRef.current;
      if (graph) {
        for (const el of graph.getElements()) {
          applyNodeVisual(el, newStatusMap[el.id as string] || "IDLE");
        }
      }
    }
  }, [streamingContext, applyNodeVisual, graphRef]);

  // Poll streaming data every 250 ms while live tracking is active
  useEffect(() => {
    if (!isLiveRequest || !streamingContext) return;
    updateNodeStatuses();
    const id = setInterval(updateNodeStatuses, 250);
    return () => clearInterval(id);
  }, [isLiveRequest, streamingContext, updateNodeStatuses]);

  // When live tracking ends, mark remaining non-IDLE nodes as DONE
  useEffect(() => {
    if (!isLiveRequest) {
      const graph = graphRef.current;
      if (graph) {
        for (const el of graph.getElements()) {
          const nodeId = el.id as string;
          const finalStatus: NodeStatus =
            nodeStatusMap[nodeId] !== "IDLE" ? "DONE" : "IDLE";
          applyNodeVisual(el, finalStatus);
        }
      }
      setNodeStatusMap({});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLiveRequest]);

  // ── Open resource details modal ────────────────────────────────────

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
        .catch((err) => { console.debug("[GraphDisplay] resource fetch failed:", err); })
        .finally(() => setLoadingResource(false));
    },
    [fetchResourceById, elementBlockRef],
  );

  // ── Derived data for render ─────────────────────────────────────────

  const nodeLabelsMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const h of overlayHeaders) map[h.nodeId] = h.label;
    return map;
  }, [overlayHeaders]);

  // ── Render helpers ──────────────────────────────────────────────────

  /** Inline status pill ("Processing" / "Complete") shown on node headers. */
  const renderStatusPill = (
    status: NodeStatus,
    scale: number,
  ): React.ReactNode => {
    if (status !== "PROGRESS" && status !== "DONE") return null;
    const s = STATUS_STYLES[status];
    const dotSize = Math.max(4, 6 * scale);
    const fontSize = Math.max(8, 10 * scale);

    return (
      <div
        className="flex items-center rounded-full"
        style={{
          gap: 3 * scale,
          padding: `${Math.max(1, 2 * scale)}px ${Math.max(4, 6 * scale)}px`,
          background: s.bgColor,
          flexShrink: 0,
        }}
      >
        {status === "PROGRESS" ? (
          <motion.div
            style={{ width: dotSize, height: dotSize, borderRadius: "50%", background: s.dotColor }}
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
          />
        ) : (
          <div style={{ width: dotSize, height: dotSize, borderRadius: "50%", background: s.dotColor }} />
        )}
        <span style={{ fontSize, fontWeight: 500, color: "rgba(255,255,255,0.85)", whiteSpace: "nowrap" }}>
          {s.label}
        </span>
      </div>
    );
  };

  // ── JSX ─────────────────────────────────────────────────────────────

  return (
    <>
      <div className="relative overflow-auto" style={{ height }}>
        {/* Live Tracking Indicator */}
        {isLiveRequest && streamingContext && (
          <div className="absolute top-2 right-2 z-50 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs flex items-center gap-2">
            <motion.div
              className="w-2 h-2 bg-green-400 rounded-full"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            Live Tracking
          </div>
        )}

        {/* Active Nodes Status Bar */}
        {isLiveRequest && streamingContext && Object.keys(nodeStatusMap).length > 0 && (
          <div className="absolute bottom-2 left-2 right-2 z-50 bg-black bg-opacity-80 text-white px-3 py-2 rounded-lg">
            <div className="flex flex-wrap gap-2 text-xs">
              {Object.entries(nodeStatusMap).map(([nodeId, status]) => {
                if (status === "IDLE") return null;
                const nodeName = nodeLabelsMap[nodeId] || nodeId;
                return (
                  <div
                    key={nodeId}
                    className={`flex items-center gap-1 px-2 py-1 rounded ${
                      status === "PROGRESS"
                        ? "bg-blue-500 bg-opacity-50"
                        : "bg-green-500 bg-opacity-50"
                    }`}
                  >
                    <motion.div
                      className={`w-2 h-2 rounded-full ${
                        status === "PROGRESS" ? "bg-blue-400" : "bg-green-400"
                      }`}
                      animate={
                        status === "PROGRESS"
                          ? { scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }
                          : undefined
                      }
                      transition={
                        status === "PROGRESS"
                          ? { duration: 1, repeat: Infinity }
                          : undefined
                      }
                    />
                    <span className="truncate max-w-20">{nodeName}</span>
                    <span className="text-xs opacity-75">
                      {status === "PROGRESS" ? "Running" : "Done"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

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
              {/* Node status border overlays (colored ring + glow around active nodes) */}
              {overlayHeaders.map((hdr) => {
                const nodeStatus = nodeStatusMap[hdr.nodeId];
                if (nodeStatus !== "PROGRESS" && nodeStatus !== "DONE") return null;
                const s = STATUS_STYLES[nodeStatus];
                const left = hdr.x * paperTransform.sx + paperTransform.tx;
                const top = hdr.y * paperTransform.sy + paperTransform.ty;
                const width = hdr.width * paperTransform.sx;
                const fullHeight = hdr.nodeHeight * paperTransform.sy;
                const borderRadius = 12 * Math.min(paperTransform.sx, paperTransform.sy);
                const borderStyle = {
                  left,
                  top,
                  width,
                  height: fullHeight,
                  borderRadius,
                  border: `${s.strokeWidth}px solid ${s.stroke}`,
                  boxShadow: s.boxShadow,
                };

                // PROGRESS nodes get a subtle pulsing glow; DONE nodes are static
                return nodeStatus === "PROGRESS" ? (
                  <motion.div
                    key={`status-border-${hdr.nodeId}`}
                    className="absolute"
                    style={borderStyle}
                    animate={{ opacity: [1, 0.6, 1] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  />
                ) : (
                  <div
                    key={`status-border-${hdr.nodeId}`}
                    className="absolute transition-all duration-300"
                    style={borderStyle}
                  />
                );
              })}

              {/* Node headers (icon + title + status pill) */}
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
                const nodeStatus = nodeStatusMap[hdr.nodeId];
                const hasStatus = nodeStatus === "PROGRESS" || nodeStatus === "DONE";

                return (
                  <div
                    key={`hdr-${hdr.nodeId}`}
                    className="absolute"
                    style={{
                      left, top, width, height: hdrHeight,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      gap: 6 * paperTransform.sx,
                      borderBottom: hdr.hasElements ? "1px solid rgba(255,255,255,0.12)" : "none",
                    }}
                  >
                    {/* Icon */}
                    <span
                      style={{
                        width: circleSize, height: circleSize, borderRadius: "50%",
                        background: "rgba(255,255,255,0.25)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: iconFontSize, lineHeight: 1, flexShrink: 0,
                      }}
                      aria-hidden="true"
                    >
                      {icon}
                    </span>
                    {/* Label */}
                    <span
                      style={{
                        color: "rgba(255,255,255,0.95)",
                        fontSize: Math.max(9, 12 * paperTransform.sx),
                        fontWeight: 600,
                        fontFamily: "system-ui, -apple-system, sans-serif",
                        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                        maxWidth: hasStatus
                          ? width - 120 * paperTransform.sx
                          : width - 40 * paperTransform.sx,
                      }}
                    >
                      {hdr.label}
                    </span>
                    {/* Status pill */}
                    {hasStatus && renderStatusPill(nodeStatus, paperTransform.sx)}
                  </div>
                );
              })}

              {/* Validation indicators (top-right corner of each node) */}
              {overlayHeaders.map((hdr) => {
                const vResult =
                  hdr.nodeRid && validationResults
                    ? validationResults[hdr.nodeRid]
                    : undefined;
                if (!isValidating && !(vResult && !vResult.is_valid)) return null;
                const indicatorSize = Math.max(24, 28 * paperTransform.sx);
                const left =
                  (hdr.x + hdr.width) * paperTransform.sx + paperTransform.tx - indicatorSize * 0.45;
                const top =
                  hdr.y * paperTransform.sy + paperTransform.ty - indicatorSize * 0.35;
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
                const category = CATEGORY_TYPE_TO_PLURAL[badge.element.type] || "default";
                const display = getCategoryDisplay(category);
                const left = badge.x * paperTransform.sx + paperTransform.tx;
                const top = badge.y * paperTransform.sy + paperTransform.ty;
                const width = badge.width * paperTransform.sx;
                const bHeight = ELEMENT_BADGE_HEIGHT * paperTransform.sy;
                return (
                  <button
                    key={`${badge.nodeId}-${badge.element.id}-${i}`}
                    type="button"
                    className="absolute flex items-center rounded-full border transition-all duration-150 pointer-events-auto"
                    style={{
                      left, top, width, height: bHeight,
                      background: BADGE_BG, borderColor: BADGE_BORDER,
                      backdropFilter: "blur(6px)", WebkitBackdropFilter: "blur(6px)",
                      fontSize: Math.max(9, 11 * paperTransform.sx),
                      paddingLeft: 4 * paperTransform.sx,
                      paddingRight: 8 * paperTransform.sx,
                      gap: 5 * paperTransform.sx,
                      cursor: interactive ? "pointer" : "default",
                    }}
                    onClick={(e) => { e.stopPropagation(); if (interactive) openElementDetails(badge.element.id); }}
                    onMouseEnter={(e) => {
                      if (!interactive) return;
                      (e.currentTarget as HTMLElement).style.background = BADGE_HOVER_BG;
                      (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.22)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background = BADGE_BG;
                      (e.currentTarget as HTMLElement).style.borderColor = BADGE_BORDER;
                    }}
                    tabIndex={interactive ? 0 : -1}
                  >
                    <span
                      style={{ flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff" }}
                      className="[&>svg]:w-3.5 [&>svg]:h-3.5"
                    >
                      {display.icon}
                    </span>
                    <span
                      className="truncate"
                      style={{
                        color: "rgba(255,255,255,0.88)", fontWeight: 500,
                        letterSpacing: "0.01em", maxWidth: width - 40 * paperTransform.sx,
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
