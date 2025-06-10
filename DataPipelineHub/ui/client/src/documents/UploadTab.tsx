import { useState } from "react";
import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { FaFileAlt, FaUpload, FaTimes, FaTrash, FaEye } from "react-icons/fa";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";


interface UploadTabProps {
    setShowUploadModal: (showUploadModal: boolean) => void;
}


export const UploadTab: React.FC<UploadTabProps> = ({ setShowUploadModal }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isUploading, setIsUploading] = useState(false);
    const [showProcessingOptions, setShowProcessingOptions] = useState(false)


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

    const simulateUpload = () => {
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
           <div className="space-y-6">
            <Card className="bg-background-card shadow-card border-gray-800 w-full">
                <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center">
                            <FaFileAlt className="text-accent text-2xl mr-3" />
                            <h3 className="text-lg font-heading font-semibold">
                                Upload Documents
                            </h3>
                        </div>
                        <Button variant="outline" onClick={() => setShowProcessingOptions(!showProcessingOptions)}>
                            {showProcessingOptions ? 'Hide' : 'Show'} Options
                        </Button>
                    </div>
<div className="flex justify-between mb-4">
        <Button onClick={() => setShowUploadModal(false)}>Cancel</Button>
      </div>
                    <div
                        className={`h-56 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors ${isDragging ? 'border-primary bg-primary bg-opacity-5' : 'border-gray-700 hover:border-gray-600'}`}
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
                                    onChange={simulateUpload}
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
                </CardContent>
            </Card>

            {showProcessingOptions && (
                <Card className="bg-background-card shadow-card border-gray-800 w-full">
                    <CardContent className="p-6 space-y-6">
                        <h3 className="text-lg font-heading font-semibold">Processing Options</h3>

                        {/* Your existing switches and select inputs go here — unchanged */}

                        <div className="flex items-center justify-between">
                            <div>
                                <Label htmlFor="auto-process" className="text-base">Auto-Process Files</Label>
                                <p className="text-xs text-gray-400 mt-1">Automatically start processing after upload</p>
                            </div>
                            <Switch id="auto-process" defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                            <div>
                                <Label htmlFor="extract-metadata" className="text-base">Extract Metadata</Label>
                                <p className="text-xs text-gray-400 mt-1">Extract file properties as metadata</p>
                            </div>
                            <Switch id="extract-metadata" defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                            <div>
                                <Label htmlFor="ocr-enabled" className="text-base">Enable OCR</Label>
                                <p className="text-xs text-gray-400 mt-1">Extract text from images within documents</p>
                            </div>
                            <Switch id="ocr-enabled" />
                        </div>

                        <Separator className="bg-gray-800" />

                        {/* Add any other processing options you already had */}
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
