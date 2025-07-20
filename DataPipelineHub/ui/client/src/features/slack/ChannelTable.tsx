import { useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FaSync, FaCog, FaPlus, FaTrash } from "react-icons/fa";
import { HiOutlineLockClosed } from "react-icons/hi";
import { useLocation } from "wouter";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { EmbedChannel, EMBED_CHANNEL_STATUS } from "@/types";
import { Badge } from "@/components/ui/badge";
import { DataTable, DataTableColumn } from "@/shared/DataTable";

export function isChannelNew(createdAt: Date): boolean {
  const now = new Date()
  const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)
  return createdAt > dayAgo
}

function StatusBadge({ 
  status, 
  isActivelyEmbedding = false 
}: { 
  status: EmbedChannel["status"];
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
      case EMBED_CHANNEL_STATUS.ACTIVE:
        return {
          bgColor: "bg-emerald-500/15",
          textColor: "text-emerald-400",
          label: "In Progress",
          isActive: true,
        };
      case EMBED_CHANNEL_STATUS.PAUSED:
        return {
          bgColor: "bg-amber-500/15",
          textColor: "text-amber-400",
          label: "Paused",
          isActive: false,
        };
      case EMBED_CHANNEL_STATUS.DONE:
        return {
          bgColor: "bg-green-500/15",
          textColor: "text-green-400",
          label: "Done",
          isActive: false,
        };
      case EMBED_CHANNEL_STATUS.FAILED:
        return {
          bgColor: "bg-red-500/15",
          textColor: "text-red-400",
          label: "Failed",
          isActive: false,
        };
      case EMBED_CHANNEL_STATUS.ARCHIVED:
        return {
          bgColor: "bg-slate-600/10",
          textColor: "text-slate-400",
          label: "Archived",
          isActive: false,
        };
      case EMBED_CHANNEL_STATUS.CHUNKING_AND_EMBEDDING:
        return {
          bgColor: "bg-blue-500/15",
          textColor: "text-blue-400",
          label: "Chunking and Embedding",
          isActive: true,
        };
      case EMBED_CHANNEL_STATUS.STORING:
        return {
          bgColor: "bg-blue-500/15",
          textColor: "text-blue-400",
          label: "Storing data",
          isActive: true,
        };
      case EMBED_CHANNEL_STATUS.COLLECTING:
        return {
          bgColor: "bg-blue-500/15",
          textColor: "text-blue-400",
          label: "Collecting data",
          isActive: true,
        };
      case EMBED_CHANNEL_STATUS.PROCESSING:
        return {
          bgColor: "bg-blue-500/15",
          textColor: "text-blue-400",
          label: "Processing data",
          isActive: true,
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

export function getColumns(
  onSettingsClick: (ch: EmbedChannel) => void,
  onDeleteClick: (ch: EmbedChannel) => void,
  deletingChannelId?: string,
  activeEmbeddingIds: string[] = [],
): DataTableColumn<EmbedChannel>[] {
  return [
    {
      accessorKey: "name",
      header: "Channel",
      cell: ({ row }) => {
        const channel = row.original
        const isNew = channel.created && isChannelNew(new Date(channel.created))
        
        return (
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
            {channel.is_private ? (
                <HiOutlineLockClosed className="mr-2 h-4 w-4" />
              ) : (
                <span className="mr-2">#</span>
              )}
              <span className="font-medium text-foreground">
                {channel.name}
              </span>
              {isNew && (
                <Badge className="bg-green-500/20 text-green-400 animate-pulse border-green-400/30">
                  NEW
                </Badge>
              )}
            </div>
          </div>
        )
      }
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: (info) => {
        const channel = info.row.original;
        const isActivelyEmbedding = activeEmbeddingIds.includes(channel.channel_id);
        return (
          <StatusBadge 
            status={info.getValue<EmbedChannel["status"]>()} 
            isActivelyEmbedding={isActivelyEmbedding}
          />
        );
      },
      filterFn: (row, columnId, filterValue) => {
        const status = row.getValue(columnId) as EmbedChannel["status"];
        let displayLabel: string;
        
        switch (status) {
          case EMBED_CHANNEL_STATUS.ACTIVE:
            displayLabel = "In Progress";
            break;
          case EMBED_CHANNEL_STATUS.PAUSED:
            displayLabel = "Paused";
            break;
          case EMBED_CHANNEL_STATUS.DONE:
            displayLabel = "Done";
            break;
          case EMBED_CHANNEL_STATUS.FAILED:
            displayLabel = "Failed";
            break;
          case EMBED_CHANNEL_STATUS.ARCHIVED:
            displayLabel = "Archived";
            break;
          default:
            displayLabel = status;
        }
        
        return displayLabel === filterValue;
      },
      meta: {
        align: "center",
        filterType: "select",
        filterOptions: ["In Progress", "Paused", "Done", "Failed", "Archived"],
      },
    },
    {
      accessorKey: "messages",
      header: "Messages",
      cell: (info) => (
        <span className="text-muted-foreground">{info.getValue<string>()}</span>
      ),
      meta: { align: "left", filterType: "text" },
      filterFn: "includesString",
    },
    {
      accessorKey: "lastSync",
      header: "Last Sync",
      cell: (info) => (
        <span className="text-muted-foreground">{info.getValue<string>()}</span>
      ),
      meta: { align: "left", filterType: "text" },
      filterFn: "includesString",
    },
    {
      accessorKey: "created",
      header: "Created At",
      cell: (info) => (
        <span className="text-muted-foreground">{info.getValue<string>()}</span>
      ),
      sortingFn: (rowA, rowB, columnId) => {
        const dateA = new Date(rowA.getValue(columnId) as string);
        const dateB = new Date(rowB.getValue(columnId) as string);
        
        // Handle invalid dates
        if (isNaN(dateA.getTime()) && isNaN(dateB.getTime())) return 0;
        if (isNaN(dateA.getTime())) return 1;
        if (isNaN(dateB.getTime())) return -1;
        
        return dateA.getTime() - dateB.getTime();
      },
      meta: { align: "left", filterType: "text" },
      filterFn: "includesString",
    },
    {
      accessorKey: "is_private",
      header: "Privacy",
      cell: (info) => {
        const isPrivate = info.getValue<boolean>();
        const privacyText = isPrivate ? "Private" : "Public";
        return (
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
            isPrivate 
              ? "bg-amber-500/15 text-amber-400 border border-amber-400/20" 
              : "bg-blue-500/15 text-blue-400 border border-blue-400/20"
          }`}>
            {isPrivate ? (
              <>
                <HiOutlineLockClosed className="mr-1 h-3 w-3" />
                Private
              </>
            ) : (
              <>
                <span className="mr-1">#</span>
                Public
              </>
            )}
          </span>
        );
      },
      filterFn: (row, columnId, filterValue) => {
        const isPrivate = row.getValue(columnId) as boolean;
        const rowValue = isPrivate ? "Private" : "Public";
        return rowValue === filterValue;
      },
      meta: {
        align: "center",
        filterType: "select",
        filterOptions: [
          "Private",
          "Public"
        ],
      },
    },
    {
      accessorKey: "frequency",
      header: "Frequency",
      cell: (info) => (
        <span className="text-muted-foreground">{info.getValue<string>()}</span>
      ),
      meta: { align: "center", filterType: "text" },
      filterFn: "includesString",
    },
    {
      id: "actions",
      header: "Actions",
      enableSorting: false,
      cell: (info) => {
        const ch = info.row.original;
        const isDeleting = deletingChannelId === ch.channel_id;
        return (
          <div className="flex justify-end space-x-2">
            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
              <Button
                variant="ghost"
                size="sm"
                className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-lg transition-all duration-200"
                onClick={() => {
                  /* optional per-row refresh */
                }}
              >
                <FaSync className="h-4 w-4" />
              </Button>
            </motion.div>
            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
              <Button
                variant="ghost"
                size="sm"
                className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-lg transition-all duration-200"
                onClick={() => onSettingsClick(ch)}
              >
                <FaCog className="h-4 w-4" />
              </Button>
            </motion.div>
            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
              <Button
                variant="ghost"
                size="sm"
                disabled={isDeleting}
                className={`p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-all duration-200 ${
                  isDeleting ? "opacity-50 cursor-not-allowed" : ""
                }`}
                onClick={() => !isDeleting && onDeleteClick(ch)}
              >
                {isDeleting ? (
                  <FaSync className="h-4 w-4 animate-spin" />
                ) : (
                  <FaTrash className="h-4 w-4" />
                )}
              </Button>
            </motion.div>
          </div>
        );
      },
      meta: { align: "right" },
    },
  ];
}
