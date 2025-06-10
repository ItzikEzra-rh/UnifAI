import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {  FaSearch } from "react-icons/fa";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CardContainer } from "@shared/CardContainer";
import { DocumentCard } from "./DocumentCard";
import { useEffect, useState } from "react";
import { Document } from "@/types";
import { UploadTab } from "./UploadTab";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import axiosInstance from "@/http/axiosConfig";
import { useQuery } from "@tanstack/react-query";

const fetchDocuments = async () => {
  console.log("heys")
  const response = await axiosInstance.get("/api/docs/available.docs.get");
  return response.data; // Ensure it returns an array of Document[]
};

export default function Documents() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [displayedDoc, setDisplayedDoc] = useState('')
  const [showUploadModal, setShowUploadModal] = useState(false);

  const { data: documents = [], isLoading, isError, error } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
  });

  // useEffect(() => {
  //   const fetchDocuments = async () => {
  //     // const response = await fetch('/api/documents'); // Adjust the endpoint as needed
  //     // const data = await response.json();
  //     // console.log(data);
  //     // Process and set documents state here
  //     const data = [
  //       {
  //         id: "1",
  //         fileType: "pdf",
  //         title: "Product Roadmap 2023.pdf",
  //         description: "PDF • 12 pages • 2.4 MB",
  //         uploaded: "1 day ago",
  //         status: "Processed",
  //         statusColor: "success",
  //         statusInfo: "34 chunks"
  //       },
  //       {
  //         id: "2",
  //         fileType: "docx",
  //         title: "Technical Specification.docx",
  //         description: "DOCX • 23 pages • 1.8 MB",
  //         uploaded: "3 days ago",
  //         status: "Processing",
  //         statusColor: "primary",
  //         statusInfo: "78% complete"
  //       },
  //       {
  //         id: "3",
  //         fileType: "pptx",
  //         title: "Quarterly Presentation.pptx",
  //         description: "PPTX • 18 slides • 5.7 MB",
  //         uploaded: "5 days ago",
  //         status: "Queued",
  //         statusColor: "accent",
  //         statusInfo: "Position: 2 in queue"
  //       },
  //       {
  //         id: "4",
  //         fileType: "xlsx",
  //         title: "Financial Analysis Q2.xlsx",
  //         description: "XLSX • 5 sheets • 3.2 MB",
  //         uploaded: "1 week ago",
  //         status: "Processed",
  //         statusColor: "success",
  //         statusInfo: "28 chunks"
  //       },
  //       {
  //         id: "5",
  //         fileType: "txt",
  //         title: "Release Notes v2.1.txt",
  //         description: "TXT • 45 KB",
  //         uploaded: "2 weeks ago",
  //         status: "Processed",
  //         statusColor: "success",
  //         statusInfo: "5 chunks"
  //       },
  //       {
  //         id: "6",
  //         fileType: "pdf",
  //         title: "API Documentation.pdf",
  //         description: "PDF • 42 pages • 3.8 MB",
  //         uploaded: "3 weeks ago",
  //         status: "Processed",
  //         statusColor: "success",
  //         statusInfo: "76 chunks"
  //       }
  //     ];
  //     setDocuments(data)
  //   } 
  //   fetchDocuments();
  // }, []);

  <div className="flex justify-between mb-4">
    <Button onClick={() => setShowUploadModal(true)}>Upload Document</Button>
  </div>


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
    <>
      <span className="text-sm text-gray-400">Showing 6 of 23 documents</span>
      <div className="flex items-center space-x-2">
        <Button variant="outline" size="sm" disabled>
          Previous
        </Button>
        <Button variant="outline" size="sm">
          Next
        </Button>
      </div>
    </>
  );


  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="Document Library" onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        <div className="grid grid-cols-1 gap-6">
          {showUploadModal ? (
            <UploadTab setShowUploadModal={setShowUploadModal} />
          ) : (
            <>
              <div className="flex justify-between mb-4">
                <Button onClick={() => setShowUploadModal(true)}>Upload Document</Button>
              </div>

              {isLoading ? (
                <p className="text-sm text-gray-400 px-6">Loading documents...</p>
              ) : isError ? (
                <p className="text-sm text-red-500 px-6">Error: {(error as Error).message}</p>
              ) : (
                <CardContainer title="" filters={filters} footer={footer}>
                  {documents.map((file) => (
                    <DocumentCard key={file.id} doc={file} />
                  ))}
                </CardContainer>
              )}

              {displayedDoc && (
                <Card className="bg-background-card shadow-card border-gray-800">
                  <CardContent className="p-6">
                    {/* Document detail content */}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
