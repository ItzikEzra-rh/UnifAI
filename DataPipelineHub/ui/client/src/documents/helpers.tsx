import { FaFileAlt, FaFileWord, FaFilePdf, FaFileExcel, FaFilePowerpoint } from "react-icons/fa";

export const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FaFilePdf className="text-accent" />;
      case 'docx':
        return <FaFileWord className="text-blue-500" />;
      case 'xlsx':
        return <FaFileExcel className="text-green-500" />;
      case 'pptx':
        return <FaFilePowerpoint className="text-orange-500" />;
      default:
        return <FaFileAlt className="text-gray-400" />;
    }
  };
