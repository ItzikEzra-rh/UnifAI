import { useState } from "react";
import { motion } from "framer-motion";
import { FaEye, FaTrash, FaSync } from "react-icons/fa";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Document } from "@/types";
import { fileByColors, getFileIcon, statusByColors, statusByLabel } from "./helpers";
import axiosInstance from '@/http/axiosConfig';
import { InlineLoader } from "@/components/shared/InlineLoader";

interface DocumentCardProps {
  doc: Document;
  activeDoc: Document | null;
  setActiveDoc: any;
  fetchDocuments: () => Promise<void>;
}

export const DocumentCard = ({ doc, activeDoc, setActiveDoc, fetchDocuments }: DocumentCardProps) => {
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const onEyeClick = () => {
    const newDoc = doc === activeDoc ? null : doc;
    setActiveDoc(newDoc);
  };

  const onDeleteConfirmed = async () => {
    try {
      setLoading(true);
      await axiosInstance.post("/api/docs/delete", { pipelineId: doc.pipeline_id });
      setShowConfirmModal(false);
      await fetchDocuments(); // Refresh document list after deletion
    } catch (error) {
      console.error("Error deleting document:", error);
    } finally {
      setLoading(false);
      setActiveDoc(null);
    }
  };

  const handleRetry = async () => {
    try {
      setRetrying(true);
      await axiosInstance.put("/api/docs/retry.embedding", { "pipelineId": doc.pipeline_id });
    } catch (error) {
      console.error("Error retrying embedding:", error);
    } finally {
      setRetrying(false);
    }
  };

  return (
    <>
      <motion.div
        whileHover={{ y: -5, transition: { duration: 0.2 } }}
        className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
      >
        <div className="flex items-start">
          <div className={`mr-3 p-2 rounded-md ${fileByColors[doc.file_type]}`}>
            {getFileIcon(doc.file_type)}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm truncate">{doc.name}</h4>
            <p className="text-xs text-gray-400 mt-1">
              {doc.status === "ACTIVE" ? (<InlineLoader />) : doc.status === "PENDING" ? ("-") : (`${doc.page_count} pages | ${doc.file_type} | ${doc.file_size}`)}
            </p>


          </div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-gray-400">Uploaded {new Date(doc.created_at).toLocaleString("en-GB")}</span>
          <div className="flex items-center gap-2">
            <Badge className={`text-xs ${statusByColors[doc.status]}`}>
              {statusByLabel[doc.status] || "Unknown"}
            </Badge>

            {doc.status === "FAILED" && (
              <Button
                variant="ghost"
                size="icon"
                className="h-5 w-5 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRetry();
                }}
                disabled={retrying}
              >
                <FaSync className={`animate-spin ${retrying ? "" : "hidden"}`} />
                {!retrying && <FaSync />}
              </Button>
            )}
          </div>
        </div>

        <div className="mt-3 flex justify-between text-xs">
          <span className="text-gray-400">
            {doc.status === "ACTIVE" ? (<InlineLoader />) : doc.status === "PENDING" ? ("-") : (`${doc.chunks} chunks`)}
          </span>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={(e) => {
              e.stopPropagation();
              onEyeClick();
            }}>
              <FaEye />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={(e) => {
              e.stopPropagation();
              setShowConfirmModal(true);
            }}>
              <FaTrash className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Delete Confirmation Modal */}
      <Dialog open={showConfirmModal} onOpenChange={setShowConfirmModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
          </DialogHeader>
          <p className="text-sm">Are you sure you want to delete <strong>{doc.name}</strong>?</p>
          <DialogFooter className="mt-4">
            <Button variant="ghost" onClick={() => setShowConfirmModal(false)}>Cancel</Button>
            <Button variant="destructive" onClick={onDeleteConfirmed} disabled={loading}>
              {loading ? "Deleting..." : "Yes, Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
