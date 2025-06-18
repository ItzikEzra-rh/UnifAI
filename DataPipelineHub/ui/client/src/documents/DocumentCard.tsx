import { motion } from "framer-motion";
import { FaEye, FaTrash } from "react-icons/fa";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Document } from "@/types";
import { getFileIcon } from "./helpers";


interface DocumentCardProps {
  doc: Document;
  activeDoc: Document | null;
  setActiveDoc: any;
}

export const DocumentCard = ({ doc, activeDoc, setActiveDoc }: DocumentCardProps) => {
  const onEyeClick = () => {
    const newDoc = doc === activeDoc ? null : doc;
    setActiveDoc(newDoc);
  }

  const fileByColors: Record<string, string> = {
    pdf: "bg-red-500 dark:bg-red-600",
    docx: "bg-blue-500 dark:bg-blue-600",
    pptx: "bg-orange-500 dark:bg-orange-600",
    xlsx: "bg-green-500 dark:bg-green-600",
    txt: "bg-gray-500 dark:bg-gray-600",
  };

  const statusByColors: Record<string, string> = {
    processing: "bg-yellow-500 text-white",
    waiting: "bg-blue-500 text-white",
    paused: "bg-orange-500 text-white",
    DONE: "bg-green-500 text-white",
    error: "bg-red-500 text-white",
  };


  return (
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
          <p className="text-xs text-gray-400 mt-1">{`${doc.file_type} | ${doc.page_count} pages`}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-gray-400">Uploaded {doc.created_at}</span>
        <Badge className={`text-xs ${statusByColors[doc.status]}`}>
          {doc.status}
        </Badge>

      </div>
      <div className="mt-3 flex justify-between text-xs">
        <span className="text-gray-400">{`${doc.chunks} chunks`}</span>
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={(e) => {
            e.stopPropagation();
            onEyeClick();
          }}>
            <FaEye />
          </Button>
          <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
            <FaTrash className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </motion.div>
  )
}
  ;
