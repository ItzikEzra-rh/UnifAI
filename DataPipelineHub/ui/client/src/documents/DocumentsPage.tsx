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
import { DocumentData } from "./DocumentData";
import { DocumentFilters } from "./DocumentFilters";

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
  const response = await axiosInstance.get("/api/docs/available.docs.get");
  console.log(response)
  return response.data.docs;
};

export default function Documents() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [activeDoc, setActiveDoc] = useState(null);
  const [fileTypeFilter, setFileTypeFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");


  const { data: documents = [], isLoading, isError, error } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
    refetchInterval: 10000,
  });

  const { currentPage, setPage, resetPage, itemsPerPage, } = usePaginationStore();

  useEffect(() => {
    resetPage();
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [showUploadModal, activeDoc])

  const filteredDocuments = documents.filter((doc) => {
  const matchesType = fileTypeFilter === "all" || doc.file_type === fileTypeFilter;
  const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase());
  return matchesType && matchesSearch;
  });

  const totalPages = Math.ceil(filteredDocuments.length / itemsPerPage);
  const paginatedDocuments = filteredDocuments.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );


  const footer = (
    <div className="flex items-center justify-between w-full px-4">
      <span className="text-sm text-gray-400">
        Showing {paginatedDocuments.length} of {filteredDocuments.length} documents
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

  const filters = (
    <DocumentFilters
      fileTypeFilter={fileTypeFilter}
      setFileTypeFilter={setFileTypeFilter}
      searchQuery={searchQuery}
      setSearchQuery={setSearchQuery}
      onSearch={() => setPage(1)}
    />
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
        <Header
          title="Document Library"
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />

        <div className="flex-1 overflow-auto px-6 pb-6">
          {showUploadModal ? (
            <UploadTab setShowUploadModal={setShowUploadModal} fetchDocuments={fetchDocuments} />
          ) : (
            <>
              {isLoading ? (
                <p className="text-sm text-gray-400">Loading documents...</p>
              ) : isError ? (
                <p className="text-sm text-red-500">Error: {(error as Error).message}</p>
              ) : (
                <div className="mb-6">
                  <CardContainer title="" filters={filters} footer={footer} actions={viewButtons}>

                    {documents.length ? (
                      viewMode === "grid" ? (
                        <>
                          {paginatedDocuments.map((file) => (
                            <DocumentCard
                              key={file.pipeline_id}
                              doc={file}
                              activeDoc={activeDoc}
                              setActiveDoc={setActiveDoc}
                              fetchDocuments={fetchDocuments}
                            />
                          ))}
                        </>
                      ) : (
                        <DocumentTable documents={documents} />
                      )
                    ) : (
                      "No documents available."
                    )}
                  </CardContainer>
                </div>
              )}

              {activeDoc && (
                <div className="mt-6">
                  <DocumentData doc={activeDoc} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
