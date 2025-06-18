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
import { Document } from "@/types";
import { DocumentCard } from "./DocumentCard";

interface LibraryTabProps {
  doc: Document
}


export const DocumentData: React.FC<LibraryTabProps> = ({ doc }) => {

  return (
    <div className="grid grid-cols-1 gap-6">
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
                      <span className="ml-2 font-medium">{doc.name}</span>
                    </div>
                    <Button variant="ghost" size="sm">
                      <FaEye className="mr-2 h-4 w-4" />
                      <span>View Original</span>
                    </Button>
                  </div>
                </div>
                <div className="p-4 h-80 overflow-y-auto font-mono text-xs whitespace-pre-line">
                  {doc.full_text ? (
                    <p>{doc.full_text}</p>
                  ) : (
                    <p className="text-gray-400 italic">No extracted text available.</p>
                  )}
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
  )
}
