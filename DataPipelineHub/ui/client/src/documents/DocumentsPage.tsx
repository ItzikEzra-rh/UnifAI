import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { FaSync, FaSearch, FaTrash, FaEye } from "react-icons/fa";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getFileIcon } from "./helpers";
import { CardContainer } from "@shared/CardContainer";
import { DocumentCard } from "./DocumentCard";
import { useEffect, useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";
import { Document } from "@/types";

export default function Documents() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [displayedDoc, setDisplayedDoc] = useState('')

  useEffect(() => {
    const fetchDocuments = async () => {
      // const response = await fetch('/api/documents'); // Adjust the endpoint as needed
      // const data = await response.json();
      // console.log(data);
      // Process and set documents state here
      const data = [
        {
          id: "1",
          fileType: "pdf",
          title: "Product Roadmap 2023.pdf",
          description: "PDF • 12 pages • 2.4 MB",
          uploaded: "1 day ago",
          status: "Processed",
          statusColor: "success",
          statusInfo: "34 chunks"
        },
        {
          id: "2",
          fileType: "docx",
          title: "Technical Specification.docx",
          description: "DOCX • 23 pages • 1.8 MB",
          uploaded: "3 days ago",
          status: "Processing",
          statusColor: "primary",
          statusInfo: "78% complete"
        },
        {
          id: "3",
          fileType: "pptx",
          title: "Quarterly Presentation.pptx",
          description: "PPTX • 18 slides • 5.7 MB",
          uploaded: "5 days ago",
          status: "Queued",
          statusColor: "accent",
          statusInfo: "Position: 2 in queue"
        },
        {
          id: "4",
          fileType: "xlsx",
          title: "Financial Analysis Q2.xlsx",
          description: "XLSX • 5 sheets • 3.2 MB",
          uploaded: "1 week ago",
          status: "Processed",
          statusColor: "success",
          statusInfo: "28 chunks"
        },
        {
          id: "5",
          fileType: "txt",
          title: "Release Notes v2.1.txt",
          description: "TXT • 45 KB",
          uploaded: "2 weeks ago",
          status: "Processed",
          statusColor: "success",
          statusInfo: "5 chunks"
        },
        {
          id: "6",
          fileType: "pdf",
          title: "API Documentation.pdf",
          description: "PDF • 42 pages • 3.8 MB",
          uploaded: "3 weeks ago",
          status: "Processed",
          statusColor: "success",
          statusInfo: "76 chunks"
        }
      ];
      setDocuments(data)
    } 
    fetchDocuments();
  }, []);

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
        <Header
          title="Document Management"
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-background-dark">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            


      <div className="grid grid-cols-1 gap-6">
        <CardContainer title="Document Library" filters={filters} footer={footer}>
          {documents?.map((file: Document) => (
              <DocumentCard doc={file} />
            ))}

        </CardContainer>

        { displayedDoc && 
        <Card className="bg-background-card shadow-card border-gray-800">
          <CardContent className="p-6">
            <h3 className="text-lg font-heading font-semibold mb-4">
              Document Details
            </h3>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <div className="bg-background-dark rounded-lg border border-gray-800 overflow-hidden">
                  <div className="p-4 bg-background-surface border-b border-gray-800">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        {getFileIcon('pdf')}
                        <span className="ml-2 font-medium">Product Roadmap 2023.pdf</span>
                      </div>
                      <Button variant="ghost" size="sm">
                        <FaEye className="mr-2 h-4 w-4" />
                        <span>View Original</span>
                      </Button>
                    </div>
                  </div>
                  <div className="p-4 h-80 overflow-y-auto font-mono text-xs">
                    <p className="mb-3 text-gray-300 font-medium">Page 1</p>
                    <p className="mb-2">Product Roadmap 2023</p>
                    <p className="mb-2">CONFIDENTIAL - INTERNAL USE ONLY</p>
                    <p className="mb-4">Q1-Q4 Strategic Planning Document</p>

                    <p className="font-medium mb-2">1. Executive Summary</p>
                    <p className="mb-4 pl-4">This roadmap outlines our product strategy for 2023, focusing on three main pillars: Enhanced User Experience, AI-Driven Features, and Enterprise Integration. These initiatives align with our company's mission to provide cutting-edge data management solutions while remaining user-friendly and accessible.</p>

                    <p className="font-medium mb-2">2. Q1 Objectives</p>
                    <p className="mb-2 pl-4">2.1. Launch redesigned dashboard interface</p>
                    <p className="mb-2 pl-4">2.2. Implement improved data visualization components</p>
                    <p className="mb-4 pl-4">2.3. Release mobile application beta</p>

                    <p className="font-medium mb-2">3. Q2 Objectives</p>
                    <p className="mb-2 pl-4">3.1. Introduce AI-powered data analysis features</p>
                    <p className="mb-2 pl-4">3.2. Enhance API capabilities for third-party integration</p>
                    <p className="mb-4 pl-4">3.3. Optimize performance for large datasets</p>

                    <p className="mb-3 text-gray-300 font-medium">Page 2</p>
                    <p className="font-medium mb-2">4. Q3 Objectives</p>
                    <p className="mb-2 pl-4">4.1. Launch enterprise SSO integration</p>
                    <p className="mb-2 pl-4">4.2. Implement advanced security features</p>
                    <p className="mb-4 pl-4">4.3. Release collaboration tools for team workflows</p>
                  </div>
                </div>
              </div>

              <div>
                <div className="bg-background-dark p-4 rounded-lg border border-gray-800">
                  <h4 className="font-medium mb-3">Document Metadata</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Title:</span>
                      <span className="text-sm">Product Roadmap 2023</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Author:</span>
                      <span className="text-sm">Product Management Team</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Created:</span>
                      <span className="text-sm">January 15, 2023</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Modified:</span>
                      <span className="text-sm">March 10, 2023</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">File Size:</span>
                      <span className="text-sm">2.4 MB</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Pages:</span>
                      <span className="text-sm">12</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Uploaded:</span>
                      <span className="text-sm">August 15, 2023</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Processed:</span>
                      <span className="text-sm">August 15, 2023</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 bg-background-dark p-4 rounded-lg border border-gray-800">
                  <h4 className="font-medium mb-3">Extraction Statistics</h4>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-400">Text Quality:</span>
                        <span className="text-sm">Excellent</span>
                      </div>
                      <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-success" style={{ width: '95%' }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-400">Structure Preservation:</span>
                        <span className="text-sm">Good</span>
                      </div>
                      <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-primary" style={{ width: '85%' }}></div>
                      </div>
                    </div>
                    <div className="pt-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Total Chunks:</span>
                        <span className="text-sm">34</span>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Total Tokens:</span>
                      <span className="text-sm">15,876</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Avg. Chunk Size:</span>
                      <span className="text-sm">467 tokens</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Images Extracted:</span>
                      <span className="text-sm">4</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Tables Extracted:</span>
                      <span className="text-sm">3</span>
                    </div>
                  </div>
                </div>

              
              </div>
            </div>
          </CardContent>
        </Card>}
      </div>
    

            {/* <Tabs defaultValue="upload" className="w-full">
              <TabsList className="mb-6">
                <TabsTrigger
                  value="upload"
                  className="data-[state=active]:bg-primary data-[state=active]:text-white"
                >
                  <FaUpload className="mr-2" />
                  Upload Documents
                </TabsTrigger>
                <TabsTrigger
                  value="library"
                  className="data-[state=active]:bg-primary data-[state=active]:text-white"
                >
                  <FaFolder className="mr-2" />
                  Document Library
                </TabsTrigger>
                <TabsTrigger
                  value="processing"
                  className="data-[state=active]:bg-primary data-[state=active]:text-white"
                >
                  <FaSync className="mr-2" />
                  Processing Status
                </TabsTrigger>
              </TabsList> */}

              {/* <UploadTab />

              <LibraryTab />

              <ProcessingTab /> */}
            {/* </Tabs> */}
          </motion.div>
        </main>

        <StatusBar />
      </div>
    </div>
  );
}
