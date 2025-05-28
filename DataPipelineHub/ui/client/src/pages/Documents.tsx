import { useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { 
  FaFileAlt, FaUpload, FaFolder, FaSync, FaSearch, 
  FaFileWord, FaFilePdf, FaFileExcel, FaFilePowerpoint, 
  FaTimes, FaTrash, FaEye
} from "react-icons/fa";
import { motion } from "framer-motion";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tooltip } from "@/components/ui/tooltip";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function Documents() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    // Simulate file upload with progress
    setIsUploading(true);
    let progress = 0;
    const interval = setInterval(() => {
      progress += 5;
      setUploadProgress(progress);
      if (progress >= 100) {
        clearInterval(interval);
        setTimeout(() => {
          setIsUploading(false);
          setUploadProgress(0);
        }, 500);
      }
    }, 200);
  };
  
  const cancelUpload = () => {
    setIsUploading(false);
    setUploadProgress(0);
  };

  const getFileIcon = (type: string) => {
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
            <Tabs defaultValue="upload" className="w-full">
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
              </TabsList>

              <TabsContent value="upload">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card className="bg-background-card shadow-card border-gray-800">
                    <CardContent className="p-6">
                      <div className="flex items-center mb-6">
                        <FaFileAlt className="text-accent text-2xl mr-3" />
                        <h3 className="text-lg font-heading font-semibold">
                          Upload Documents
                        </h3>
                      </div>

                      <div 
                        className={`h-56 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors ${
                          isDragging ? 'border-primary bg-primary bg-opacity-5' : 'border-gray-700 hover:border-gray-600'
                        }`}
                        onDragEnter={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('file-upload')?.click()}
                      >
                        {!isUploading ? (
                          <>
                            <div className="w-16 h-16 bg-background-surface rounded-full flex items-center justify-center mb-4">
                              <FaUpload className="text-accent text-xl" />
                            </div>
                            <p className="font-medium mb-1">Drag and drop files here</p>
                            <p className="text-sm text-gray-400">or click to browse files</p>
                            <p className="text-xs text-gray-500 mt-4">
                              Supported formats: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV
                            </p>
                            <input 
                              id="file-upload" 
                              type="file" 
                              multiple 
                              className="hidden" 
                              onChange={() => {
                                // Simulate file upload with progress
                                setIsUploading(true);
                                let progress = 0;
                                const interval = setInterval(() => {
                                  progress += 5;
                                  setUploadProgress(progress);
                                  if (progress >= 100) {
                                    clearInterval(interval);
                                    setTimeout(() => {
                                      setIsUploading(false);
                                      setUploadProgress(0);
                                    }, 500);
                                  }
                                }, 200);
                              }} 
                            />
                          </>
                        ) : (
                          <div className="w-full px-8">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">Uploading files...</span>
                              <Button variant="ghost" size="sm" onClick={cancelUpload}>
                                <FaTimes className="h-4 w-4" />
                              </Button>
                            </div>
                            <Progress value={uploadProgress} className="h-2 mb-2" />
                            <div className="flex justify-between text-xs text-gray-400">
                              <span>{uploadProgress}% complete</span>
                              <span>3 of 5 files</span>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="mt-6 space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="auto-process" className="text-base">
                              Auto-Process Files
                            </Label>
                            <p className="text-xs text-gray-400 mt-1">
                              Automatically start processing after upload
                            </p>
                          </div>
                          <Switch id="auto-process" defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="extract-metadata" className="text-base">
                              Extract Metadata
                            </Label>
                            <p className="text-xs text-gray-400 mt-1">
                              Extract file properties as metadata
                            </p>
                          </div>
                          <Switch id="extract-metadata" defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="ocr-enabled" className="text-base">
                              Enable OCR
                            </Label>
                            <p className="text-xs text-gray-400 mt-1">
                              Extract text from images within documents
                            </p>
                          </div>
                          <Switch id="ocr-enabled" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-background-card shadow-card border-gray-800">
                    <CardContent className="p-6">
                      <h3 className="text-lg font-heading font-semibold mb-4">
                        Processing Options
                      </h3>

                      <div className="space-y-6">
                        <div>
                          <Label htmlFor="chunk-size" className="text-sm">
                            Chunk Size
                          </Label>
                          <Select defaultValue="512">
                            <SelectTrigger
                              id="chunk-size"
                              className="mt-1 bg-background-dark"
                            >
                              <SelectValue placeholder="Select chunk size" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="256">256 tokens</SelectItem>
                              <SelectItem value="512">512 tokens</SelectItem>
                              <SelectItem value="1024">1024 tokens</SelectItem>
                              <SelectItem value="2048">2048 tokens</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-xs text-gray-400 mt-1">
                            Size of text chunks for processing
                          </p>
                        </div>

                        <div>
                          <Label htmlFor="chunk-overlap" className="text-sm">
                            Chunk Overlap
                          </Label>
                          <div className="flex items-center space-x-2 mt-1">
                            <Input
                              id="chunk-overlap"
                              type="number"
                              min="0"
                              max="200"
                              defaultValue="50"
                              className="bg-background-dark"
                            />
                            <span className="text-sm">tokens</span>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">
                            Overlap between consecutive chunks
                          </p>
                        </div>

                        <Separator className="bg-gray-800" />

                        <div>
                          <Label htmlFor="parsing-mode" className="text-sm">
                            Document Parsing Mode
                          </Label>
                          <Select defaultValue="auto">
                            <SelectTrigger
                              id="parsing-mode"
                              className="mt-1 bg-background-dark"
                            >
                              <SelectValue placeholder="Select parsing mode" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="auto">Auto-detect</SelectItem>
                              <SelectItem value="simple">Simple (faster)</SelectItem>
                              <SelectItem value="structure">Structure-aware (slower)</SelectItem>
                              <SelectItem value="markdown">Preserve Markdown</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-xs text-gray-400 mt-1">
                            How to parse the document text
                          </p>
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="extract-tables" className="text-base">
                              Extract Tables
                            </Label>
                            <p className="text-xs text-gray-400 mt-1">
                              Parse and extract tabular data
                            </p>
                          </div>
                          <Switch id="extract-tables" defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="preserve-hierarchy" className="text-base">
                              Preserve Document Hierarchy
                            </Label>
                            <p className="text-xs text-gray-400 mt-1">
                              Maintain heading/section hierarchy
                            </p>
                          </div>
                          <Switch id="preserve-hierarchy" defaultChecked />
                        </div>

                        <Separator className="bg-gray-800" />

                        <div>
                          <div className="bg-background-dark p-4 rounded-md border border-gray-800">
                            <div className="flex items-start space-x-2">
                              <div className="mt-1 text-accent">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <circle cx="12" cy="12" r="10"></circle>
                                  <line x1="12" y1="16" x2="12" y2="12"></line>
                                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                                </svg>
                              </div>
                              <div>
                                <p className="text-sm font-medium">Processing Tips</p>
                                <ul className="text-xs text-gray-400 mt-1 space-y-1 list-disc pl-4">
                                  <li>Larger chunk sizes provide more context but may result in less precise retrieval</li>
                                  <li>Enable OCR for scanned documents or files with images</li>
                                  <li>Structure-aware parsing preserves document layout but takes longer</li>
                                </ul>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="lg:col-span-2 bg-background-card shadow-card border-gray-800">
                    <CardContent className="p-6">
                      <h3 className="text-lg font-heading font-semibold mb-4">
                        Recent Uploads
                      </h3>

                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-[250px]">File Name</TableHead>
                              <TableHead>Type</TableHead>
                              <TableHead>Size</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Uploaded</TableHead>
                              <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('pdf')}
                                <span className="ml-2">Product Roadmap 2023.pdf</span>
                              </TableCell>
                              <TableCell>PDF</TableCell>
                              <TableCell>2.4 MB</TableCell>
                              <TableCell>
                                <Badge className="bg-success bg-opacity-20 text-success">
                                  Processed
                                </Badge>
                              </TableCell>
                              <TableCell>5 minutes ago</TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end space-x-2">
                                  <Button variant="ghost" size="sm">
                                    <FaEye className="h-4 w-4" />
                                  </Button>
                                  <Button variant="ghost" size="sm">
                                    <FaTrash className="h-4 w-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('docx')}
                                <span className="ml-2">Technical Specification.docx</span>
                              </TableCell>
                              <TableCell>DOCX</TableCell>
                              <TableCell>1.8 MB</TableCell>
                              <TableCell>
                                <div className="flex items-center space-x-2">
                                  <Badge className="bg-primary bg-opacity-20 text-primary">
                                    Processing
                                  </Badge>
                                  <span className="text-xs">78%</span>
                                </div>
                              </TableCell>
                              <TableCell>10 minutes ago</TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end space-x-2">
                                  <Button variant="ghost" size="sm">
                                    <FaEye className="h-4 w-4" />
                                  </Button>
                                  <Button variant="ghost" size="sm">
                                    <FaTrash className="h-4 w-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('pptx')}
                                <span className="ml-2">Quarterly Presentation.pptx</span>
                              </TableCell>
                              <TableCell>PPTX</TableCell>
                              <TableCell>5.7 MB</TableCell>
                              <TableCell>
                                <Badge className="bg-accent bg-opacity-20 text-accent">
                                  Queued
                                </Badge>
                              </TableCell>
                              <TableCell>15 minutes ago</TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end space-x-2">
                                  <Button variant="ghost" size="sm">
                                    <FaEye className="h-4 w-4" />
                                  </Button>
                                  <Button variant="ghost" size="sm">
                                    <FaTrash className="h-4 w-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </div>

                      <div className="mt-4 flex justify-end">
                        <Button variant="outline" size="sm">
                          View All Uploads
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="library">
                <div className="grid grid-cols-1 gap-6">
                  <Card className="bg-background-card shadow-card border-gray-800">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-heading font-semibold">
                          Document Library
                        </h3>
                        <div className="flex items-center space-x-2">
                          <div>
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
                          </div>
                          <Input
                            placeholder="Search documents..."
                            className="w-64 bg-background-dark"
                          />
                          <Button variant="outline">
                            <FaSearch className="mr-2" />
                            Search
                          </Button>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {/* Document Cards */}
                        <motion.div 
                          whileHover={{ y: -5, transition: { duration: 0.2 } }}
                          className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
                        >
                          <div className="flex items-start">
                            <div className="mr-3 bg-red-100 dark:bg-red-900 bg-opacity-20 p-2 rounded-md">
                              {getFileIcon('pdf')}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm truncate">Product Roadmap 2023.pdf</h4>
                              <p className="text-xs text-gray-400 mt-1">PDF • 12 pages • 2.4 MB</p>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-gray-400">Uploaded 1 day ago</span>
                            <Badge className="bg-success bg-opacity-20 text-success text-xs">
                              Processed
                            </Badge>
                          </div>
                          <div className="mt-3 flex justify-between text-xs">
                            <span className="text-gray-400">34 chunks</span>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaEye className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaTrash className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                        
                        <motion.div 
                          whileHover={{ y: -5, transition: { duration: 0.2 } }}
                          className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
                        >
                          <div className="flex items-start">
                            <div className="mr-3 bg-blue-100 dark:bg-blue-900 bg-opacity-20 p-2 rounded-md">
                              {getFileIcon('docx')}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm truncate">Technical Specification.docx</h4>
                              <p className="text-xs text-gray-400 mt-1">DOCX • 23 pages • 1.8 MB</p>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-gray-400">Uploaded 3 days ago</span>
                            <Badge className="bg-primary bg-opacity-20 text-primary text-xs">
                              Processing
                            </Badge>
                          </div>
                          <div className="mt-3 flex justify-between text-xs">
                            <span className="text-gray-400">78% complete</span>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaEye className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaTrash className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                        
                        <motion.div 
                          whileHover={{ y: -5, transition: { duration: 0.2 } }}
                          className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
                        >
                          <div className="flex items-start">
                            <div className="mr-3 bg-orange-100 dark:bg-orange-900 bg-opacity-20 p-2 rounded-md">
                              {getFileIcon('pptx')}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm truncate">Quarterly Presentation.pptx</h4>
                              <p className="text-xs text-gray-400 mt-1">PPTX • 18 slides • 5.7 MB</p>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-gray-400">Uploaded 5 days ago</span>
                            <Badge className="bg-accent bg-opacity-20 text-accent text-xs">
                              Queued
                            </Badge>
                          </div>
                          <div className="mt-3 flex justify-between text-xs">
                            <span className="text-gray-400">Position: 2 in queue</span>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaEye className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaTrash className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                        
                        <motion.div 
                          whileHover={{ y: -5, transition: { duration: 0.2 } }}
                          className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
                        >
                          <div className="flex items-start">
                            <div className="mr-3 bg-green-100 dark:bg-green-900 bg-opacity-20 p-2 rounded-md">
                              {getFileIcon('xlsx')}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm truncate">Financial Analysis Q2.xlsx</h4>
                              <p className="text-xs text-gray-400 mt-1">XLSX • 5 sheets • 3.2 MB</p>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-gray-400">Uploaded 1 week ago</span>
                            <Badge className="bg-success bg-opacity-20 text-success text-xs">
                              Processed
                            </Badge>
                          </div>
                          <div className="mt-3 flex justify-between text-xs">
                            <span className="text-gray-400">28 chunks</span>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaEye className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaTrash className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                        
                        <motion.div 
                          whileHover={{ y: -5, transition: { duration: 0.2 } }}
                          className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
                        >
                          <div className="flex items-start">
                            <div className="mr-3 bg-gray-100 dark:bg-gray-700 bg-opacity-20 p-2 rounded-md">
                              {getFileIcon('txt')}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm truncate">Release Notes v2.1.txt</h4>
                              <p className="text-xs text-gray-400 mt-1">TXT • 45 KB</p>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-gray-400">Uploaded 2 weeks ago</span>
                            <Badge className="bg-success bg-opacity-20 text-success text-xs">
                              Processed
                            </Badge>
                          </div>
                          <div className="mt-3 flex justify-between text-xs">
                            <span className="text-gray-400">5 chunks</span>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaEye className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaTrash className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                        
                        <motion.div 
                          whileHover={{ y: -5, transition: { duration: 0.2 } }}
                          className="bg-background-dark p-4 rounded-lg border border-gray-800 cursor-pointer hover:border-primary transition-colors"
                        >
                          <div className="flex items-start">
                            <div className="mr-3 bg-red-100 dark:bg-red-900 bg-opacity-20 p-2 rounded-md">
                              {getFileIcon('pdf')}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm truncate">API Documentation.pdf</h4>
                              <p className="text-xs text-gray-400 mt-1">PDF • 42 pages • 3.8 MB</p>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-gray-400">Uploaded 3 weeks ago</span>
                            <Badge className="bg-success bg-opacity-20 text-success text-xs">
                              Processed
                            </Badge>
                          </div>
                          <div className="mt-3 flex justify-between text-xs">
                            <span className="text-gray-400">76 chunks</span>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaEye className="h-3 w-3" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                <FaTrash className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                      </div>

                      <div className="mt-6 flex justify-between items-center">
                        <span className="text-sm text-gray-400">
                          Showing 6 of 23 documents
                        </span>
                        <div className="flex items-center space-x-2">
                          <Button variant="outline" size="sm" disabled>
                            Previous
                          </Button>
                          <Button variant="outline" size="sm">
                            Next
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

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
                          
                          <div className="mt-4">
                            <div className="flex space-x-2">
                              <Button variant="outline" className="flex-1">
                                <FaSync className="mr-2" />
                                Reprocess
                              </Button>
                              <Button variant="destructive" className="flex-1">
                                <FaTrash className="mr-2" />
                                Delete
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="processing">
                <div className="grid grid-cols-1 gap-6">
                  <Card className="bg-background-card shadow-card border-gray-800">
                    <CardContent className="p-6">
                      <h3 className="text-lg font-heading font-semibold mb-6">
                        Document Processing Status
                      </h3>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                        <div className="bg-background-dark p-4 rounded-lg border border-gray-800">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">Processed</h4>
                            <Badge className="bg-success bg-opacity-20 text-success">
                              18 Documents
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-400 mb-3">
                            Documents successfully processed and available
                          </p>
                          <div className="mt-2">
                            <Button variant="outline" size="sm" className="w-full">
                              View Documents
                            </Button>
                          </div>
                        </div>
                        
                        <div className="bg-background-dark p-4 rounded-lg border border-gray-800">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">In Progress</h4>
                            <Badge className="bg-primary bg-opacity-20 text-primary">
                              3 Documents
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-400 mb-3">
                            Documents currently being processed
                          </p>
                          <div className="mt-2">
                            <Button variant="outline" size="sm" className="w-full">
                              View Progress
                            </Button>
                          </div>
                        </div>
                        
                        <div className="bg-background-dark p-4 rounded-lg border border-gray-800">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">Queued</h4>
                            <Badge className="bg-accent bg-opacity-20 text-accent">
                              2 Documents
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-400 mb-3">
                            Documents waiting to be processed
                          </p>
                          <div className="mt-2">
                            <Button variant="outline" size="sm" className="w-full">
                              Manage Queue
                            </Button>
                          </div>
                        </div>
                      </div>

                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-[250px]">File Name</TableHead>
                              <TableHead>Type</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Progress</TableHead>
                              <TableHead>Started</TableHead>
                              <TableHead>ETA</TableHead>
                              <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('docx')}
                                <span className="ml-2">Technical Specification.docx</span>
                              </TableCell>
                              <TableCell>DOCX</TableCell>
                              <TableCell>
                                <Badge className="bg-primary bg-opacity-20 text-primary">
                                  Processing
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="w-full max-w-xs flex items-center space-x-2">
                                  <Progress value={78} className="h-2" />
                                  <span className="text-xs w-8">78%</span>
                                </div>
                              </TableCell>
                              <TableCell>10 minutes ago</TableCell>
                              <TableCell>2 minutes</TableCell>
                              <TableCell className="text-right">
                                <Button variant="ghost" size="sm">
                                  <FaTimes className="mr-2 h-4 w-4" />
                                  Cancel
                                </Button>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('pdf')}
                                <span className="ml-2">User Research Report.pdf</span>
                              </TableCell>
                              <TableCell>PDF</TableCell>
                              <TableCell>
                                <Badge className="bg-primary bg-opacity-20 text-primary">
                                  Processing
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="w-full max-w-xs flex items-center space-x-2">
                                  <Progress value={45} className="h-2" />
                                  <span className="text-xs w-8">45%</span>
                                </div>
                              </TableCell>
                              <TableCell>15 minutes ago</TableCell>
                              <TableCell>8 minutes</TableCell>
                              <TableCell className="text-right">
                                <Button variant="ghost" size="sm">
                                  <FaTimes className="mr-2 h-4 w-4" />
                                  Cancel
                                </Button>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('xlsx')}
                                <span className="ml-2">Sales Data Q3.xlsx</span>
                              </TableCell>
                              <TableCell>XLSX</TableCell>
                              <TableCell>
                                <Badge className="bg-primary bg-opacity-20 text-primary">
                                  Processing
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="w-full max-w-xs flex items-center space-x-2">
                                  <Progress value={12} className="h-2" />
                                  <span className="text-xs w-8">12%</span>
                                </div>
                              </TableCell>
                              <TableCell>5 minutes ago</TableCell>
                              <TableCell>15 minutes</TableCell>
                              <TableCell className="text-right">
                                <Button variant="ghost" size="sm">
                                  <FaTimes className="mr-2 h-4 w-4" />
                                  Cancel
                                </Button>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('pptx')}
                                <span className="ml-2">Quarterly Presentation.pptx</span>
                              </TableCell>
                              <TableCell>PPTX</TableCell>
                              <TableCell>
                                <Badge className="bg-accent bg-opacity-20 text-accent">
                                  Queued
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="w-full max-w-xs flex items-center space-x-2">
                                  <Progress value={0} className="h-2" />
                                  <span className="text-xs w-8">0%</span>
                                </div>
                              </TableCell>
                              <TableCell>-</TableCell>
                              <TableCell>Est. 20 minutes</TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end space-x-2">
                                  <Button variant="ghost" size="sm">
                                    <FaSync className="h-4 w-4" />
                                  </Button>
                                  <Button variant="ghost" size="sm">
                                    <FaTrash className="h-4 w-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell className="font-medium flex items-center">
                                {getFileIcon('pdf')}
                                <span className="ml-2">Project Proposal.pdf</span>
                              </TableCell>
                              <TableCell>PDF</TableCell>
                              <TableCell>
                                <Badge className="bg-accent bg-opacity-20 text-accent">
                                  Queued
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="w-full max-w-xs flex items-center space-x-2">
                                  <Progress value={0} className="h-2" />
                                  <span className="text-xs w-8">0%</span>
                                </div>
                              </TableCell>
                              <TableCell>-</TableCell>
                              <TableCell>Est. 12 minutes</TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end space-x-2">
                                  <Button variant="ghost" size="sm">
                                    <FaSync className="h-4 w-4" />
                                  </Button>
                                  <Button variant="ghost" size="sm">
                                    <FaTrash className="h-4 w-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-background-card shadow-card border-gray-800">
                    <CardContent className="p-6">
                      <h3 className="text-lg font-heading font-semibold mb-4">
                        Document Conversion Status
                      </h3>

                      <div className="bg-background-dark p-4 rounded-lg border border-gray-800">
                        <h4 className="font-medium mb-3">Technical Specification.docx</h4>
                        
                        <div className="space-y-6">
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm flex items-center">
                                <Badge className="mr-2 bg-success bg-opacity-20 text-success">
                                  Complete
                                </Badge>
                                Text Extraction
                              </span>
                              <span className="text-sm">100%</span>
                            </div>
                            <Progress value={100} className="h-1.5" />
                            <p className="text-xs text-gray-400 mt-1">
                              23 pages processed, 24,532 words extracted
                            </p>
                          </div>
                          
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm flex items-center">
                                <Badge className="mr-2 bg-primary bg-opacity-20 text-primary">
                                  In Progress
                                </Badge>
                                Chunking & Analysis
                              </span>
                              <span className="text-sm">78%</span>
                            </div>
                            <Progress value={78} className="h-1.5" />
                            <p className="text-xs text-gray-400 mt-1">
                              42 chunks created so far, processing sections 3-4
                            </p>
                          </div>
                          
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm flex items-center">
                                <Badge className="mr-2 bg-accent bg-opacity-20 text-accent">
                                  Pending
                                </Badge>
                                Embedding Generation
                              </span>
                              <span className="text-sm">0%</span>
                            </div>
                            <Progress value={0} className="h-1.5" />
                            <p className="text-xs text-gray-400 mt-1">
                              Waiting for chunking to complete
                            </p>
                          </div>
                          
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm flex items-center">
                                <Badge className="mr-2 bg-accent bg-opacity-20 text-accent">
                                  Pending
                                </Badge>
                                Vector Storage
                              </span>
                              <span className="text-sm">0%</span>
                            </div>
                            <Progress value={0} className="h-1.5" />
                            <p className="text-xs text-gray-400 mt-1">
                              Waiting for embedding generation
                            </p>
                          </div>
                        </div>
                        
                        <div className="mt-6 pt-4 border-t border-gray-800">
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="text-sm">Overall Progress: 78%</p>
                              <p className="text-xs text-gray-400">
                                Estimated completion in 2 minutes
                              </p>
                            </div>
                            <Button variant="outline" size="sm">
                              View Details
                            </Button>
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-6">
                        <h4 className="font-medium mb-3">Processing Logs</h4>
                        <div className="bg-background-dark p-3 rounded-md border border-gray-800 font-mono text-xs h-60 overflow-y-auto">
                          <div className="text-success">[INFO] 14:23:12 - Starting document processing for Technical Specification.docx</div>
                          <div className="text-gray-400">[INFO] 14:23:13 - Document size: 1.8 MB, 23 pages</div>
                          <div className="text-gray-400">[INFO] 14:23:15 - Initiating text extraction using docx parser</div>
                          <div className="text-gray-400">[INFO] 14:23:18 - Extracted 24,532 words from document</div>
                          <div className="text-gray-400">[INFO] 14:23:19 - Found 5 tables in document</div>
                          <div className="text-gray-400">[INFO] 14:23:20 - Found 8 images in document</div>
                          <div className="text-success">[INFO] 14:23:21 - Text extraction complete</div>
                          <div className="text-gray-400">[INFO] 14:23:22 - Starting document chunking with size=512, overlap=50</div>
                          <div className="text-gray-400">[INFO] 14:23:25 - Preserving document structure during chunking</div>
                          <div className="text-gray-400">[INFO] 14:23:28 - Created 15 chunks from sections 1-2</div>
                          <div className="text-error">[WARN] 14:23:30 - Table on page 12 has complex formatting, using simplified extraction</div>
                          <div className="text-gray-400">[INFO] 14:23:32 - Created 27 chunks from sections 3-4</div>
                          <div className="text-gray-400">[INFO] 14:23:35 - Chunking 78% complete</div>
                          <div className="text-gray-400">[INFO] 14:23:36 - Processing section 5 of 6</div>
                          <div className="text-gray-400">[INFO] 14:23:38 - Extracting metadata from document properties</div>
                          <div className="text-gray-400">[INFO] 14:23:39 - Found author: "Engineering Team"</div>
                          <div className="text-gray-400">[INFO] 14:23:40 - Found created date: "2023-07-15"</div>
                          <div className="text-gray-400">[INFO] 14:23:41 - Documents contains technical specifications for API v2.0</div>
                        </div>
                        
                        <div className="mt-4 flex justify-between items-center">
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center">
                              <div className="w-3 h-3 rounded-full bg-success mr-1"></div>
                              <span className="text-xs">Info</span>
                            </div>
                            <div className="flex items-center">
                              <div className="w-3 h-3 rounded-full bg-accent mr-1"></div>
                              <span className="text-xs">Warning</span>
                            </div>
                            <div className="flex items-center">
                              <div className="w-3 h-3 rounded-full bg-error mr-1"></div>
                              <span className="text-xs">Error</span>
                            </div>
                          </div>
                          <Button variant="outline" size="sm">
                            Download Logs
                          </Button>
                        </div>
                      </div>
                      
                      <div className="mt-6 pt-4 border-t border-gray-800">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <h4 className="font-medium mb-2">Document Queue</h4>
                            <div className="bg-background-dark p-3 rounded-md border border-gray-800">
                              <div className="text-sm">
                                <div className="flex items-center justify-between mb-2">
                                  <span>Current position:</span>
                                  <span>0/2</span>
                                </div>
                                <div className="text-xs text-gray-400">
                                  <p>Active processing: 3 documents</p>
                                  <p className="mt-1">Queued: 2 documents</p>
                                  <p className="mt-1">Estimated wait time: 0 minutes</p>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div>
                            <h4 className="font-medium mb-2">Processing Resources</h4>
                            <div className="bg-background-dark p-3 rounded-md border border-gray-800">
                              <div className="text-sm">
                                <div className="flex items-center justify-between mb-2">
                                  <span>System load:</span>
                                  <span>Medium</span>
                                </div>
                                <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden mb-3">
                                  <div className="h-full bg-secondary" style={{ width: '65%' }}></div>
                                </div>
                                <div className="text-xs text-gray-400">
                                  <p>Processing rate: 1.8 pages/second</p>
                                  <p className="mt-1">Embedding rate: 32 chunks/minute</p>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div>
                            <h4 className="font-medium mb-2">Error Handling</h4>
                            <div className="bg-background-dark p-3 rounded-md border border-gray-800">
                              <div className="text-sm">
                                <div className="flex items-center justify-between mb-2">
                                  <span>Status:</span>
                                  <Badge className="bg-success bg-opacity-20 text-success">
                                    Healthy
                                  </Badge>
                                </div>
                                <div className="text-xs text-gray-400">
                                  <p>Warnings: 1 (non-critical)</p>
                                  <p className="mt-1">Errors: 0</p>
                                  <p className="mt-1">Auto-recovery: Enabled</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </motion.div>
        </main>

        <StatusBar />
      </div>
    </div>
  );
}
