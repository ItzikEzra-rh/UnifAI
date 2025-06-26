import { FaFileAlt, FaFileWord, FaFilePdf, FaFileExcel, FaFilePowerpoint } from "react-icons/fa";

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

export const statusByColors: Record<string, string> = {
  PENDING: "bg-grey-500 text-white",
  ACTIVE: "bg-blue-500 text-white",
  DONE: "bg-green-500 text-white",
  FAILED: "bg-red-500 text-white",
};

export const statusByLabel: Record<string, string> = {
  DONE: "DONE",
  FAILED: "FAILED",
  ACTIVE: "IN PROGRESS",
  PENDING: "IN QUEUE",
};