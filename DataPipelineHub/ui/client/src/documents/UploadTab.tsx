import { useState } from "react";
import { FaChevronRight, FaChevronDown } from "react-icons/fa";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { FaFileAlt, FaUpload, FaTimes } from "react-icons/fa";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

interface UploadTabProps {
    setShowUploadModal: (showUploadModal: boolean) => void;
}

export const UploadTab: React.FC<UploadTabProps> = ({
    setShowUploadModal,
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [showProcessingOptions, setShowProcessingOptions] = useState(false);
    const [error, setError] = useState<string>("");

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
        handleFiles(e.dataTransfer.files);
    };

    const handleFiles = (files: FileList) => {
        setSelectedFiles((prev) => [...prev, ...Array.from(files)]);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleFiles(e.target.files? e.target.files : new FileList());
    };

    const uploadFiles = async (files: File[]) => {
        setIsUploading(true);
        setUploadProgress(0);

        for (let i = 0; i < files.length; i++) {
            setUploadProgress(((i + 1) / files.length) * 100);
            await new Promise((resolve) => setTimeout(resolve, 500)); // Simulating upload
        }

        setIsUploading(false);
        setShowUploadModal(false)
    };

    const submitToAPI = async (docs: { doc_name: string; doc_path: string }[]) => {
        try {
            const res = await fetch("http://10.46.254.113:13456/api/docs/embed.docs", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ docs })
            });

            if (!res.ok) {
                throw new Error(await res.text()); // extract error
            }

            console.log("API submission successful!");
        } catch (error) {
            console.error(error);
            setError((error as Error).message);
        }
    }

    const handleSubmit = async () => {
        if (selectedFiles.length === 0) return;

        // First upload files
        await uploadFiles(selectedFiles);

        // After upload, submit their paths to API
        // Here we are simulating with their names
        // Ideally, you would replace this with URLs or server-side paths
        const docs = selectedFiles.map((file) => ({
            doc_name: file.name,
            doc_path: `home/cloud-user/unifai/DataPipelineHub/backend/data/pdfs/${file.name}`
        }));

        await submitToAPI(docs);
        setSelectedFiles([]);
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
                        <div className="flex justify-between mb-4">
                            <Button onClick={() => setShowUploadModal(false)}>Cancel</Button>
                        </div>
                    </div>

                    <div
                        className={`h-56 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors ${isDragging ? "border-primary bg-primary bg-opacity-5" : "border-gray-700 hover:border-gray-600"}`}
                        onDragEnter={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        onClick={() =>
                            document.getElementById("file-upload")?.click()
                        }
                    >
                        {!isUploading ? (
                            <>
                                <div className="w-16 h-16 bg-background-surface rounded-full flex items-center justify-center mb-4">
                                   <FaUpload className="text-accent text-xl" />
                                </div>
                                <p className="font-semibold mb-1">
                                   Drag and drop files here
                                </p>
                                <p className="text-sm text-gray-400">
                                   or click to browse files
                                </p>
                                <p className="text-xs text-gray-500 mt-4">
                                   Supported formats: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV
                                </p>
                                <input
                                   id="file-upload"
                                   type="file"
                                   multiple
                                   className="hidden"
                                   onChange={handleFileSelect}
                                />
                            </>
                        ) : (
                            <div className="w-full px-8">
                                <div className="flex items-center justify-between mb-2">
                                   <span className="font-semibold">
                                      Uploading files...
                                   </span>
                                   <Button variant="ghost" size="sm" onClick={() => setIsUploading(false)}>
                                      <FaTimes className="h-4 w-4" />
                                   </Button>
                                </div>
                                <Progress value={uploadProgress} className="h-2 mb-2" />
                                <div className="flex justify-between text-xs text-gray-400">
                                   <span>{Math.round(uploadProgress)}% complete</span>
                                   <span>{selectedFiles.length} files</span>
                                </div>
                            </div>
                        )}

                        {/* File list after upload */}
                        {selectedFiles.length > 0 && (
                            <ul className="list-inside list-decimal mt-4">
                                {selectedFiles.map((file, idx) => (
                                   <li key={idx} className="text-gray-300">
                                      {file.name}
                                   </li>
                                ))}
                            </ul>
                        )}


                        {/* Error message if submission fails */}
                        {error && <p className="text-red-500 mt-4">{error}</p>}

                    </div>
                </CardContent>
                {selectedFiles.length > 0 && !isUploading && (
                    <div className="flex justify-end p-4">
                        <Button disabled={selectedFiles.length === 0} onClick={handleSubmit}>
                            Submit
                        </Button>
                    </div>
                )}
            </Card>

            {/* Processing options */}
            <div
                className="flex items-center space-x-2 cursor-pointer text-primary text-sm font-semibold mt-4"
                onClick={() =>
                    setShowProcessingOptions((prev) => !prev)
                }
            >
                {showProcessingOptions ? (
                    <FaChevronDown className="transition-transform duration-200" />
                ) : (
                    <FaChevronRight className="transition-transform duration-200" />
                )}

                <span>Processing Options</span>
            </div>

            {showProcessingOptions && (
                <Card className="bg-background-card shadow-card border-gray-800 w-full">
                    <CardContent className="p-6 space-y-6">
                        {/* Your processing options here */}
                        {/* Auto-Process, Extract Metadata, Enable OCR etc.*/}
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

                        <Separator className="bg-gray-800" />

                        {/* Add any other processing options you already had */}
                    </CardContent>
                </Card>
            )}

        </div>
    )
}

