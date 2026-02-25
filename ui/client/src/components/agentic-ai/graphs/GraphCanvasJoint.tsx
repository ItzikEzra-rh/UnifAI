import React, { useState, useMemo, useEffect, useCallback } from "react";
import { dia, linkTools } from "@joint/core";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Link2, X, ZoomIn, ZoomOut, Maximize2, GitBranch, Trash2 } from "lucide-react";
import GraphHeader from "./GraphHeader";
import InnerRefElement from "./InnerRefElement";
import * as yaml from "js-yaml";
import { useTheme } from "@/contexts/ThemeContext";
import { deriveThemeColors } from "@/lib/colorUtils";
import {
  useJointGraphCanvas,
  type CanvasOverlayHeader,
} from "@/hooks/use-joint-graph-canvas";
import { NODE_WIDTH, NODE_HEADER_HEIGHT, nodeIconForType } from "./GraphDisplayHelpers";
import type { CanvasNode, CanvasEdge, BuildingBlock } from "@/types/graph";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface GraphCanvasJointProps {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  yamlFlow?: any;
  onDrop: (event: React.DragEvent) => void;
  onDragOver: (event: React.DragEvent) => void;
  onClearGraph: () => void;
  onSaveGraph: () => void;
  onDeleteNode?: (nodeId: string) => void;
  onDeleteEdge?: (edgeId: string) => void;
  onBack?: () => void;
  isGraphValid?: boolean;
  onNodeClick?: (nodeId: string) => void;
  onPaneClick?: () => void;
  onNodePositionChange?: (nodeId: string, pos: { x: number; y: number }) => void;
  pendingConnectionSource?: string | null;
  onCancelConnection?: () => void;
}

// ---------------------------------------------------------------------------
// Zoom controls
// ---------------------------------------------------------------------------

function ZoomControls({
  onZoomIn,
  onZoomOut,
  onFitToView,
}: {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToView: () => void;
}) {
  return (
    <div className="absolute bottom-3 right-3 z-40 flex flex-col rounded-lg bg-black/70 backdrop-blur-sm">
      <button
        type="button"
        className="flex items-center justify-center w-8 h-8 text-white/80 hover:text-white hover:bg-white/10 rounded-t-lg transition-colors"
        onClick={onZoomIn}
        aria-label="Zoom in"
      >
        <ZoomIn size={16} />
      </button>
      <button
        type="button"
        className="flex items-center justify-center w-8 h-8 text-white/80 hover:text-white hover:bg-white/10 transition-colors"
        onClick={onZoomOut}
        aria-label="Zoom out"
      >
        <ZoomOut size={16} />
      </button>
      <button
        type="button"
        className="flex items-center justify-center w-8 h-8 text-white/80 hover:text-white hover:bg-white/10 rounded-b-lg transition-colors"
        onClick={onFitToView}
        aria-label="Fit to view"
      >
        <Maximize2 size={16} />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Connection banner (positioned via paper transform, no ReactFlow dependency)
// ---------------------------------------------------------------------------

function ConnectionBanner({
  pendingConnectionSource,
  nodes,
  paperTransform,
  edgeColor,
  accentColor,
  onCancel,
}: {
  pendingConnectionSource: string;
  nodes: CanvasNode[];
  paperTransform: { sx: number; sy: number; tx: number; ty: number };
  edgeColor: string;
  accentColor: string;
  onCancel?: () => void;
}) {
  const sourceNode = nodes.find((n) => n.id === pendingConnectionSource);
  if (!sourceNode) return null;

  const nodeWidth = NODE_WIDTH;
  const centerX = (sourceNode.position.x + nodeWidth / 2) * paperTransform.sx + paperTransform.tx;
  const topY = sourceNode.position.y * paperTransform.sy + paperTransform.ty;
  const sourceLabel = sourceNode.data?.label || pendingConnectionSource;

  return (
    <div
      className="absolute z-40 flex items-center gap-3 text-white px-4 py-2.5 rounded-xl shadow-xl backdrop-blur-md border whitespace-nowrap"
      style={{
        left: centerX,
        top: Math.max(topY - 56, 8),
        transform: "translateX(-50%)",
        background: `linear-gradient(to right, ${edgeColor}F2, ${edgeColor}CC)`,
        borderColor: `${accentColor}60`,
        pointerEvents: "auto",
      }}
    >
      <div
        className="flex items-center justify-center w-7 h-7 rounded-full border"
        style={{ backgroundColor: `${edgeColor}30`, borderColor: `${accentColor}40` }}
      >
        <Link2 className="w-3.5 h-3.5 animate-pulse" style={{ color: accentColor }} />
      </div>
      <span className="text-sm font-medium">
        Select a target to connect{" "}
        <span className="font-semibold" style={{ color: accentColor }}>
          {sourceLabel}
        </span>
      </span>
      <button
        onClick={onCancel}
        className="ml-1 p-1 rounded-md text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
        title="Cancel (ESC)"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Per-node creation overlay
// ---------------------------------------------------------------------------

function CreationNodeOverlay({
  hdr,
  node,
  sx,
  selected,
  isConnectionSource,
  onDelete,
}: {
  hdr: CanvasOverlayHeader;
  node: CanvasNode;
  sx: number;
  selected: boolean;
  isConnectionSource: boolean;
  onDelete?: (nodeId: string) => void;
}) {
  const icon = nodeIconForType(hdr.nodeType);
  const circleSize = Math.max(20 / sx, 26);
  const iconFontSize = Math.max(12 / sx, 14);
  const conditions: BuildingBlock[] = node.data.referencedConditions || [];
  const isProtected = node.id === "user_input" || node.id === "finalize";

  const extractReferences = (config: any): Record<string, string> => {
    const refs: Record<string, string> = {};
    if (!config || typeof config !== "object") return refs;
    const traverse = (obj: any) => {
      for (const [key, value] of Object.entries(obj)) {
        if (typeof value === "string" && (value as string).startsWith("$ref:")) {
          refs[key] = (value as string).substring(5);
        } else if (Array.isArray(value)) {
          value.forEach((item, idx) => {
            if (typeof item === "string" && item.startsWith("$ref:")) {
              refs[`${key}[${idx}]`] = item.substring(5);
            }
          });
        } else if (typeof value === "object" && value !== null) {
          traverse(value);
        }
      }
    };
    traverse(config);
    return refs;
  };

  const references = node.data.workspaceData?.config
    ? extractReferences(node.data.workspaceData.config)
    : {};
  const hasRefs = Object.keys(references).length > 0;

  return (
    <>
      {/* Header row */}
      <div
        className="absolute pointer-events-auto"
        style={{
          left: hdr.x,
          top: hdr.y,
          width: hdr.width,
          height: NODE_HEADER_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          borderBottom:
            conditions.length > 0 || hasRefs
              ? "1px solid rgba(255,255,255,0.12)"
              : "none",
          cursor: "pointer",
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
        >
          {icon}
        </span>
        <span
          style={{
            color: "rgba(255,255,255,0.95)",
            fontSize: Math.max(9 / sx, 12),
            fontWeight: 600,
            fontFamily: "system-ui, -apple-system, sans-serif",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            maxWidth: hdr.width - 80,
          }}
        >
          {hdr.label}
        </span>

        {isConnectionSource && (
          <span
            className="text-xs font-medium px-2 py-0.5 rounded-full"
            style={{ background: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.9)" }}
          >
            Source
          </span>
        )}

        {(selected || isConnectionSource) && !isProtected && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete?.(hdr.nodeId);
            }}
            className="w-5 h-5 text-gray-400 hover:text-red-400 transition-colors flex-shrink-0"
            title="Delete node"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Conditions */}
      {conditions.length > 0 && (
        <div
          className="absolute pointer-events-auto"
          style={{
            left: hdr.x + 8,
            top: hdr.y + NODE_HEADER_HEIGHT + 4,
            width: hdr.width - 16,
          }}
        >
          <div className="flex items-center gap-2 text-xs font-medium text-orange-400 mb-1">
            <GitBranch className="w-3 h-3" />
            Conditions
          </div>
          {conditions.map((cond) => (
            <div
              key={cond.id}
              className="bg-orange-900/30 border border-orange-700 rounded px-2 py-1 mb-1 flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-orange-600 flex items-center justify-center">
                  <GitBranch className="w-2 h-2 text-white" />
                </div>
                <span className="text-xs text-white">{cond.label}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0 text-red-400 hover:text-red-300"
                onClick={(e) => {
                  e.stopPropagation();
                  node.data.onRemoveCondition?.(
                    hdr.nodeId,
                    cond.workspaceData?.rid || cond.id,
                  );
                }}
              >
                <Trash2 className="w-3 h-3" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Inner reference elements */}
      {hasRefs && (
        <div
          className="absolute pointer-events-auto"
          style={{
            left: hdr.x + 8,
            top:
              hdr.y +
              NODE_HEADER_HEIGHT +
              (conditions.length > 0 ? 24 + conditions.length * 32 : 0) +
              4,
            width: hdr.width - 16,
          }}
        >
          <div className="text-xs text-gray-400 mb-1">Resources:</div>
          <div className="grid grid-cols-3 gap-1">
            {Object.entries(references).map(([key, refId]) => (
              <InnerRefElement
                key={`${key}-${refId}`}
                refId={refId}
                refData={{ key, value: refId }}
                allBlocks={node.data.allBlocks || []}
              />
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const GraphCanvasJoint: React.FC<GraphCanvasJointProps> = ({
  nodes,
  edges,
  yamlFlow,
  onDrop,
  onDragOver,
  onClearGraph,
  onSaveGraph,
  onDeleteNode,
  onDeleteEdge,
  onBack,
  isGraphValid = false,
  onNodeClick,
  onPaneClick,
  onNodePositionChange,
  pendingConnectionSource = null,
  onCancelConnection,
}) => {
  const [showYamlDebug, setShowYamlDebug] = useState(false);
  const { primaryHex } = useTheme();

  const { primary: edgeColor, primaryLight: accentColor } = useMemo(
    () => deriveThemeColors(primaryHex),
    [primaryHex],
  );

  const {
    containerRef,
    paperRef,
    graphRef,
    overlayHeaders,
    paperTransform,
    handleZoomIn,
    handleZoomOut,
    handleFitToView,
    runAutoLayout,
  } = useJointGraphCanvas({
    nodes,
    edges,
    primaryHex,
    onNodeClick,
    onPaneClick,
    onNodePositionChange,
  });

  // Run auto-layout once after the initial nodes are placed
  const didAutoLayoutRef = React.useRef(false);
  useEffect(() => {
    if (nodes.length >= 2 && !didAutoLayoutRef.current) {
      didAutoLayoutRef.current = true;
      // Slight delay to let JointJS render the elements
      const t = setTimeout(() => runAutoLayout(), 80);
      return () => clearTimeout(t);
    }
  }, [nodes.length, runAutoLayout]);

  // ── Edge delete tools via JointJS link tools ──
  useEffect(() => {
    const paper = paperRef.current;
    if (!paper || !onDeleteEdge) return;

    const onLinkEnter = (linkView: dia.LinkView) => {
      const edgeId = linkView.model.id as string;
      const removeButton = new linkTools.Remove({
        distance: "50%",
        action: () => {
          onDeleteEdge(edgeId);
        },
      });
      const tools = new dia.ToolsView({ tools: [removeButton] });
      linkView.addTools(tools);
    };

    const onLinkLeave = (linkView: dia.LinkView) => {
      linkView.removeTools();
    };

    paper.on("link:mouseenter", onLinkEnter);
    paper.on("link:mouseleave", onLinkLeave);

    return () => {
      paper.off("link:mouseenter", onLinkEnter);
      paper.off("link:mouseleave", onLinkLeave);
    };
  }, [paperRef, onDeleteEdge]);

  // Build a quick lookup for nodes by id
  const nodeById = useMemo(() => {
    const map = new Map<string, CanvasNode>();
    for (const n of nodes) map.set(n.id, n);
    return map;
  }, [nodes]);

  return (
    <div className="flex-1 relative">
      <Card className="bg-background-card shadow-card border-gray-800 h-full">
        <GraphHeader
          onClearGraph={onClearGraph}
          onSaveGraph={onSaveGraph}
          onBack={onBack}
          isGraphValid={isGraphValid}
        />
        <CardContent className="p-0 h-full relative">
          {/* YAML debug panel */}
          {showYamlDebug && yamlFlow && (
            <div className="absolute top-4 right-4 z-50 bg-gray-900 border border-gray-700 rounded-lg p-4 max-w-md max-h-96 overflow-auto">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium text-white">YAML Flow State</h3>
                <button
                  onClick={() => setShowYamlDebug(false)}
                  className="text-gray-400 hover:text-white"
                >
                  x
                </button>
              </div>
              <pre className="text-xs text-gray-300 overflow-auto">
                {yaml.dump(yamlFlow, { indent: 2, lineWidth: -1 })}
              </pre>
            </div>
          )}

          <button
            onClick={() => setShowYamlDebug(!showYamlDebug)}
            className="absolute top-4 right-4 z-40 bg-gray-800 hover:bg-gray-700 text-white px-3 py-1 text-xs rounded border border-gray-600"
          >
            {showYamlDebug ? "Hide" : "Show"} YAML
          </button>

          {/* Main canvas area */}
          <div
            className="h-full relative"
            style={{ height: "calc(100vh - 180px)" }}
            onDrop={onDrop}
            onDragOver={onDragOver}
          >
            {/* Connection banner */}
            {pendingConnectionSource && (
              <ConnectionBanner
                pendingConnectionSource={pendingConnectionSource}
                nodes={nodes}
                paperTransform={paperTransform}
                edgeColor={edgeColor}
                accentColor={accentColor}
                onCancel={onCancelConnection}
              />
            )}

            {/* Zoom controls */}
            <ZoomControls
              onZoomIn={handleZoomIn}
              onZoomOut={handleZoomOut}
              onFitToView={handleFitToView}
            />

            {/* JointJS paper container */}
            <div
              ref={containerRef}
              className="min-h-full min-w-full h-full"
              style={{ height: "100%" }}
            />

            {/* HTML overlay layer – mirrors the paper transform */}
            {overlayHeaders.length > 0 && (
              <div
                className="absolute inset-0 pointer-events-none"
                style={{ overflow: "hidden" }}
              >
                <div
                  style={{
                    transformOrigin: "0 0",
                    transform: `matrix(${paperTransform.sx}, 0, 0, ${paperTransform.sy}, ${paperTransform.tx}, ${paperTransform.ty})`,
                  }}
                >
                  {overlayHeaders.map((hdr) => {
                    const node = nodeById.get(hdr.nodeId);
                    if (!node) return null;
                    return (
                      <CreationNodeOverlay
                        key={hdr.nodeId}
                        hdr={hdr}
                        node={node}
                        sx={paperTransform.sx}
                        selected={!!node.selected}
                        isConnectionSource={!!node.data.isConnectionSource}
                        onDelete={onDeleteNode}
                      />
                    );
                  })}
                </div>
              </div>
            )}

            {/* Empty state */}
            {nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="text-center">
                  <Plus className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="mt-2 text-sm font-medium text-gray-300">
                    No nodes yet
                  </h3>
                  <p className="mt-1 text-sm text-gray-400">
                    Drag building blocks from the sidebar to get started
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GraphCanvasJoint;
