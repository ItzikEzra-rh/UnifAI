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
