import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { FaSearch, FaTh, FaList } from "react-icons/fa";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CardContainer } from "@shared/CardContainer";
import { DocumentCard } from "./DocumentCard";
import { useState, useEffect } from "react";
import { Document } from "@/types";
import { UploadTab } from "./UploadTab";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import axiosInstance from "@/http/axiosConfig";
import { useQuery } from "@tanstack/react-query";
import { usePaginationStore } from "@/stores/usePaginationStore";

// Placeholder for ListView
const DocumentTable = ({ documents }: { documents: any[] }) => (
  <div className="px-6 py-2 text-sm text-gray-300">
    <table className="w-full border-collapse">
      <thead>
        <tr className="border-b border-gray-700">
          <th className="text-left py-2">Name</th>
          <th className="text-left py-2">Type</th>
          <th className="text-left py-2">Date</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((doc) => (
          <tr key={doc.id} className="border-b border-gray-800">
            <td className="py-2">{doc.title}</td>
            <td className="py-2">{doc.fileType}</td>
            <td className="py-2">{new Date(doc.uploaded).toLocaleDateString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const fetchDocuments = async () => {
  const response = await axiosInstance.get("/api/docs/docs.get");
  return response.data.docs;
};

export default function Documents() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const { data: documents = [], isLoading, isError, error } = useQuery<any[]>({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
  });

  const { currentPage, setPage, resetPage, itemsPerPage,} = usePaginationStore();

  useEffect(() => {
    resetPage();
  }, []);

  const totalPages = Math.ceil(documents.length / itemsPerPage);
  const paginatedDocuments = documents.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const filters = (
    <div className="flex items-center space-x-2">
      <Select defaultValue="all">
        <SelectTrigger className="w-32 bg-background-dark">
          <SelectValue placeholder="All Types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Types</SelectItem>
          <SelectItem value="pdf">PDF</SelectItem>
          <SelectItem value="docx">Word</SelectItem>
          <SelectItem value="pptx">PowerPoint</SelectItem>
          <SelectItem value="xlsx">Excel</SelectItem>
          <SelectItem value="txt">Text</SelectItem>
        </SelectContent>
      </Select>
      <Input placeholder="Search documents..." className="w-64 bg-background-dark" />
      <Button variant="outline">
        <FaSearch className="mr-2" />
        Search
      </Button>
    </div>
  );

  const footer = (
    <div className="flex items-center justify-between w-full px-4">
      <span className="text-sm text-gray-400">
        Showing {documents.length < 6 ? documents.length : 6} of {documents.length} documents
      </span>
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage(Math.max(currentPage - 1, 1))}
          disabled={currentPage === 1}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage(Math.min(currentPage + 1, totalPages))}
          disabled={currentPage === totalPages}
        >
          Next
        </Button>

      </div>
    </div>
  );

  const viewButtons = (
    <div className="flex items-center space-x-4">
      <Button onClick={() => setShowUploadModal(true)}>Upload Document</Button>
      <div className="flex">
        <Button
          variant={viewMode === "grid" ? "default" : "outline"}
          size="icon"
          onClick={() => setViewMode("grid")}
        >
          <FaTh />
        </Button>
        <Button
          variant={viewMode === "list" ? "default" : "outline"}
          size="icon"
          onClick={() => setViewMode("list")}
        >
          <FaList />
        </Button>
      </div>
    </div>
  );


  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="Document Library" onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} rightSlot={showUploadModal ? null : viewButtons}/>

        <div className="grid grid-cols-1 gap-6">
          {showUploadModal ? (
            <UploadTab setShowUploadModal={setShowUploadModal} />
          ) : (
            <>
              {isLoading ? (
                <p className="text-sm text-gray-400 px-6">Loading documents...</p>
              ) : isError ? (
                <p className="text-sm text-red-500 px-6">Error: {(error as Error).message}</p>
              ) : (
                <CardContainer title="" filters={filters} footer={footer}>
                  {documents.length ? (
                    viewMode === "grid" ? (
                      <>
                        {paginatedDocuments.map((file) => (
                          <DocumentCard key={file.id} doc={file} />
                        ))}
                      </>
                    ) : (
                      <DocumentTable documents={documents} />
                    )
                  ) : (
                    "No documents available."
                  )}
                 

                </CardContainer>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
