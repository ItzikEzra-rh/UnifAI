import React, { useState } from "react";
import { FaEye, FaTrash, FaSync } from "react-icons/fa";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { InlineLoader } from "@/components/shared/InlineLoader";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Document } from "@/types";
import { getFileIcon, fileByColors, statusByLabel, statusByColors } from "./helpers";
import { DataTable, DataTableColumn } from "@/components/shared/DataTable";
import axiosInstance from "@/http/axiosConfig";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { DocumentData } from "./DocumentData";

interface DocumentTableProps {
    documents: Document[];
    fetchDocuments: () => Promise<void>;
    activeDoc?: Document | null;
    setActiveDoc?: (doc: Document | null) => void;
    deleteLoading?: boolean;
    onDeleteConfirmed?: (id: string) => void;
    retrying?: boolean;
    handleRetry?: (id: string) => void;
}


export const DocumentTable: React.FC<DocumentTableProps> = ({
    documents,
    fetchDocuments,
    activeDoc,
    setActiveDoc, deleteLoading, onDeleteConfirmed, retrying, handleRetry
}) => {
    const [confirmDoc, setConfirmDoc] = useState<Document | null>(null);


    const handleDelete = async (doc: Document) => {
        try {
            await axiosInstance.post("/api/docs/delete", { pipelineId: doc.pipeline_id });
            await fetchDocuments();
        } catch (error) {
            console.error("Error deleting document:", error);
        }
    };

    const columns: DataTableColumn<Document>[] = [
        {
            accessorKey: "name",
            header: "Name",
            cell: ({ row }) => {
                const doc = row.original;
                return (
                    <div className="flex items-center space-x-2">
                        <div className={`p-1.5 rounded ${fileByColors[doc.file_type]}`}>
                            {getFileIcon(doc.file_type)}
                        </div>
                        <div className="truncate max-w-[200px]">{doc.name}</div>
                    </div>
                );
            },
            meta: { align: "left", filterType: "text" }
        },
        {
            accessorKey: "created_at",
            header: "Uploaded",
            cell: ({ row }) =>
                new Date(row.original.created_at).toLocaleString("en-GB"),
            meta: { align: "left" }
        },
        {
            accessorKey: "page_count",
            header: "Pages",
            cell: ({ row }) => {
                const doc = row.original;
                return doc.status === "ACTIVE" ? (
                    <InlineLoader />
                ) : doc.status === "PENDING" ? (
                    "-"
                ) : (
                    doc.page_count
                );
            },
            meta: { align: "center" }
        },
        {
            accessorKey: "file_size",
            header: "Size (MB)",
            cell: ({ row }) => {
                const doc = row.original;
                if (doc.status === "ACTIVE") return <InlineLoader />;
                if (doc.status === "PENDING") return "-";

                const sizeMatch = doc.file_size?.match(/[\d.]+/);
                return sizeMatch ? sizeMatch[0] : "-";
            },
            meta: { align: "center" }
        },
        {
            accessorKey: "file_type",
            header: "File Type",
            cell: ({ row }) => row.original.file_type.toUpperCase(),
            meta: { align: "center", filterType: "select", filterOptions: ["PDF", "DOCX", "TXT", "XLSX", "OTHER"] }
        },
        {
            accessorKey: "chunks",
            header: "Chunks",
            cell: ({ row }) =>
                row.original.status === "ACTIVE" ? (
                    <InlineLoader />
                ) : row.original.status === "PENDING" ? (
                    "-"
                ) : (
                    `${row.original.chunks}`
                ),
            meta: { align: "center" }
        },
        {
            accessorKey: "status",
            header: "Status",
            cell: ({ row }) => {
                const doc = row.original;
                return (
                    <Badge className={`text-xs ${statusByColors[doc.status]}`}>
                        {statusByLabel[doc.status] || "Unknown"}
                    </Badge>
                );
            },
            meta: {
                align: "center",
                filterType: "select",
                filterOptions: Object.keys(statusByLabel)
            }
        },
        {
            id: "actions",
            header: "",
            cell: ({ row }) => {
                const doc = row.original;
                const isActive = activeDoc?.pipeline_id === doc.pipeline_id;
                return (
                    <div className="flex items-center space-x-2 justify-end">
                        {doc.status === "FAILED" && (
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 p-0"
                                onClick={() => handleRetry?.(doc.pipeline_id)}
                                disabled={retrying}
                            >
                                <FaSync />
                            </Button>
                        )}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 p-0"
                            onClick={() => setActiveDoc?.(isActive ? null : doc)}
                        >
                            <FaEye className={isActive ? "text-primary" : ""} />
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 p-0"
                            onClick={() => setConfirmDoc(doc)}
                            disabled={deleteLoading}
                        >
                            <FaTrash className="h-3 w-3" />
                        </Button>

                    </div>
                );
            },
            meta: { align: "right" }
        }

    ];


    return (
        <div className="w-full">
            <DataTable
                columns={columns}
                data={documents}
                enableGlobalFilter={true}
                enableColumnFilters={true}
                enablePagination={true}
                expendedRow={activeDoc}
                renderExpandedRow={(doc) => <DocumentData doc={doc} />}
            />
          

            {confirmDoc && (
                <ConfirmDialog
                    open={true}
                    title="Delete Document"
                    message={`Are you sure you want to delete "${confirmDoc.name}"?`}
                    confirmLabel="Yes, Delete"
                    onConfirm={async () => {
                        await onDeleteConfirmed?.(confirmDoc.pipeline_id);
                        setConfirmDoc(null);
                    }}
                    onCancel={() => setConfirmDoc(null)}
                    loading={deleteLoading}
                />
            )}
        </div>
    );
};
