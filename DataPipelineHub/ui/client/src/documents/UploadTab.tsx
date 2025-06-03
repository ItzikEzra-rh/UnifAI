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
import { getFileIcon } from "./shared";

interface UploadTabProps {

}


export const UploadTab: React.FC<UploadTabProps> = ({ }) => {
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

    return (
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
                            className={`h-56 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors ${isDragging ? 'border-primary bg-primary bg-opacity-5' : 'border-gray-700 hover:border-gray-600'
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
    )
}
