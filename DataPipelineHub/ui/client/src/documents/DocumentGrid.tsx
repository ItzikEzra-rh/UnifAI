import { FaEye, FaSync, FaTrash } from "react-icons/fa";
import { DataCard } from "@/components/shared/DataCard";
import { fileByColors, getFileIcon, statusByColors, statusByLabel } from "@/documents/helpers";
import { InlineLoader } from "@/components/shared/InlineLoader";
import { Document } from "@/types";
import { CardContainer } from "@shared/CardContainer";
import { Button } from "@/components/ui/button";
import { DocumentData } from "./DocumentData";

interface DocumentGridProps {
  paginatedDocuments: Document[];
  activeDoc: Document | null;
  setActiveDoc: (doc: Document | null) => void;
  deleteLoading: boolean;
  onDeleteConfirmed: (id: string) => void;
  retrying: boolean;
  handleRetry: (id: string) => void;
  footer?: React.ReactNode;
}

const getSubtitle = (doc: Document) => {
  if (doc.status === "ACTIVE") return <InlineLoader />;
  if (doc.status === "PENDING") return "-";
  if (doc.status === "FAILED") return "-";
  return `${doc.page_count} pages | ${doc.file_type} | ${doc.file_size}`;
};

const getFooterText = (doc: Document) => {
  if (doc.status === "ACTIVE") return <InlineLoader />;
  if (doc.status === "PENDING") return "-";
  if (doc.status === "FAILED") return "-";
  return `${doc.chunks} chunks`;
};

const getStatusBadge = (doc: Document) => ({
  label: statusByLabel[doc.status] || "Unknown",
  className: statusByColors[doc.status],
});

const getExtraTopRight = (
  doc: Document,
  handleRetry: (id: string) => void,
  retrying: boolean
) =>
  doc.status === "FAILED" ? (
    <Button
      variant="ghost"
      size="icon"
      className="h-5 w-5 p-0"
      onClick={(e) => {
        e.stopPropagation();
        handleRetry(doc.pipeline_id);
      }}
      disabled={retrying}
    >
      <FaSync className={`animate-spin ${retrying ? "" : "hidden"}`} />
      {!retrying && <FaSync />}
    </Button>
  ) : null;

const getActions = (
  doc: Document,
  activeDoc: Document | null,
  setActiveDoc: (doc: Document | null) => void,
  deleteLoading: boolean,
  onDeleteConfirmed: (id: string) => void
) => [
  {
    icon: <FaEye />,
    onClick: () => setActiveDoc(doc === activeDoc ? null : doc),
  },
  {
    icon: <FaTrash className="h-3 w-3" />,
    onClick: () => {},
    confirm: {
      title: "Delete Document",
      message: `Are you sure you want to delete "${doc.name}"?`,
      onConfirm: () => onDeleteConfirmed(doc.pipeline_id),
      loading: deleteLoading,
      confirmLabel: "Yes, Delete",
    },
  },
];

export const DocumentGrid = ({paginatedDocuments, activeDoc, setActiveDoc, deleteLoading, onDeleteConfirmed, retrying, handleRetry, footer}: DocumentGridProps) => {
  return (
    <CardContainer title="" footer={footer} activeCardComponent={DocumentData} activeCard={activeDoc}>
      {paginatedDocuments.map((doc) => (
        <DataCard
          key={doc.pipeline_id}
          iconRenderer={() => getFileIcon(doc.file_type)}
          iconBgClass={fileByColors[doc.file_type]}
          title={doc.name}
          subtitle={getSubtitle(doc)}
          metadata={`Uploaded ${new Date(doc.created_at).toLocaleString("en-GB")} by ${doc.upload_by}`}
          footer={getFooterText(doc)}
          selected={doc === activeDoc}
          onClick={() => setActiveDoc(doc === activeDoc ? null : doc)}
          statusBadge={getStatusBadge(doc)}
          extraTopRight={getExtraTopRight(doc, handleRetry, retrying)}
          actions={getActions(doc, activeDoc, setActiveDoc, deleteLoading, onDeleteConfirmed)}
        />
      ))}
    </CardContainer>
  );
};
