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

export const DocumentCard = ({doc, activeDoc, setActiveDoc}: DocumentCardProps) => {
  const onEyeClick = () => {
    const newDoc = doc === activeDoc ? null : doc;
    setActiveDoc(newDoc);
  }

  return (
    <motion.div
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
    >
      <div className="flex items-start">
        <div className={`mr-3 bg-${doc.statusColor}-100 dark:bg-${doc.statusColor}-900 bg-opacity-20 p-2 rounded-md`}>
          {getFileIcon(doc.fileType)}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{doc.title}</h4>
          <p className="text-xs text-gray-400 mt-1">{doc.description}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-gray-400">Uploaded {doc.uploaded}</span>
        <Badge className={`bg-${doc.statusColor} bg-opacity-20 text-${doc.statusColor} text-xs`}>
          {status}
        </Badge>
      </div>
      <div className="mt-3 flex justify-between text-xs">
        <span className="text-gray-400">{doc.statusInfo}</span>
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
  )}
;
