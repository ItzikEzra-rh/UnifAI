import { cn } from "@/lib/utils";
import { EmbedChannel, Document } from "@/types";
import { useMemo } from "react";

export function StatusBadge({ 
  status, 
  isActivelyEmbedding = false 
}: { 
  status: EmbedChannel["status"] | Document["status"];
  isActivelyEmbedding?: boolean;
}) {
  const { bgColor, textColor, label, isActive } = useMemo(() => {
    // Override status if actively embedding
    if (isActivelyEmbedding) {
      return {
        bgColor: "bg-blue-500/15",
        textColor: "text-blue-400",
        label: "Embedding...",
        isActive: true,
      };
    }

    switch (status) {
      case "ACTIVE":
        return {
          bgColor: "bg-emerald-500/15",
          textColor: "text-emerald-400",
          label: "In Progress",
          isActive: true,
        };
      case "PAUSED":
        return {
          bgColor: "bg-amber-500/15",
          textColor: "text-amber-400",
          label: "Paused",
          isActive: false,
        };
      case "DONE":
        return {
          bgColor: "bg-green-500/15",
          textColor: "text-green-400",
          label: "Done",
          isActive: false,
        };
      case "FAILED":
        return {
          bgColor: "bg-red-500/15",
          textColor: "text-red-400",
          label: "Failed",
          isActive: false,
        };
      case "ARCHIVED":
        return {
          bgColor: "bg-slate-600/10",
          textColor: "text-slate-400",
          label: "Archived",
          isActive: false,
        };
      default:
        return {
          bgColor: "bg-slate-600/10",
          textColor: "text-slate-400",
          label: status,
          isActive: false,
        };
    }
  }, [status, isActivelyEmbedding]);

  return (
    <span
      className={cn(
        "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border",
        bgColor,
        textColor,
        isActive && "animate-pulse-glow border-emerald-400/30",
        !isActive && "border-current/20",
      )}
    >
      <span
        className={cn(
          "w-2 h-2 rounded-full mr-2",
          isActive ? "bg-emerald-400 animate-pulse" : "bg-current",
        )}
      ></span>
      {label}
    </span>
  );
}