import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {FaSync, FaTimes, FaTrash} from "react-icons/fa";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getFileIcon } from "./helpers";

interface ProcessingTabProps {

}


export const ProcessingTab: React.FC<ProcessingTabProps> = ({ }) => {
  return (
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
  )}
