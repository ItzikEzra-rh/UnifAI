import { FaFileAlt, FaFileWord, FaFilePdf, FaFileExcel, FaFilePowerpoint } from "react-icons/fa";
import { PIPELINE_STATUS, PipelineStatus } from "@/constants/pipelineStatus";

export const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FaFilePdf />;
      case 'docx':
        return <FaFileWord />;
      case 'xlsx':
        return <FaFileExcel />;
      case 'pptx':
        return <FaFilePowerpoint />;
      default:
        return <FaFileAlt />;
    }
  };

export const fileByColors: Record<string, string> = {
  pdf: "bg-red-500 dark:bg-red-600",
  docx: "bg-blue-500 dark:bg-blue-600",
  pptx: "bg-orange-500 dark:bg-orange-600",
  xlsx: "bg-green-500 dark:bg-green-600",
  txt: "bg-gray-500 dark:bg-gray-600",
};

export const statusByLabel: Record<PipelineStatus, string> = {
  [PIPELINE_STATUS.DONE]: "DONE",
  [PIPELINE_STATUS.FAILED]: "FAILED",
  [PIPELINE_STATUS.ACTIVE]: "IN PROGRESS",
  [PIPELINE_STATUS.PENDING]: "IN QUEUE",
  [PIPELINE_STATUS.ARCHIVED]: "ARCHIVED",
  [PIPELINE_STATUS.PAUSED]: "PAUSED",
};

export function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
}
