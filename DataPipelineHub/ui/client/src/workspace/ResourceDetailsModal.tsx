import React from 'react';
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { BuildingBlock } from '@/types/graph';
import { FileText } from 'lucide-react';

interface ResourceDetailsModalProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  selectedElement: BuildingBlock | null;
}

const ResourceDetailsModal: React.FC<ResourceDetailsModalProps> = ({
  isOpen,
  onClose,
  selectedElement
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-background-card border-gray-800 text-foreground max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            {selectedElement?.label || 'Resource Details'}
          </DialogTitle>
        </DialogHeader>
        
        {selectedElement?.workspaceData && (
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-400">Resource ID</label>
                <p className="font-mono text-sm text-gray-300">{selectedElement.workspaceData.rid}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-400">Type</label>
                <p className="text-sm text-gray-300">{selectedElement.workspaceData.type}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-400">Version</label>
                <p className="text-sm text-gray-300">v{selectedElement.workspaceData.version || 1}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-400">Category</label>
                <p className="text-sm text-gray-300">{selectedElement.workspaceData.category}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-400">Created</label>
                <p className="text-sm text-gray-300">
                  {selectedElement.workspaceData.created ? new Date(selectedElement.workspaceData.created).toLocaleString() : 'N/A'}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-400">Last Updated</label>
                <p className="text-sm text-gray-300">
                  {selectedElement.workspaceData.updated ? new Date(selectedElement.workspaceData.updated).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>

            {/* References */}
            {selectedElement.workspaceData.nested_refs && selectedElement.workspaceData.nested_refs.length > 0 && (
              <div>
                <label className="text-sm font-medium text-gray-400">Referenced Resources</label>
                <div className="mt-1 space-y-1">
                  {selectedElement.workspaceData.nested_refs.map((ref, index) => (
                    <Badge key={index} variant="outline" className="mr-2">
                      {ref}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Configuration */}
            {selectedElement.workspaceData.config && (
              <div>
                <label className="text-sm font-medium text-gray-400">Full Configuration</label>
                <div className="mt-2 bg-gray-900 p-4 rounded-md">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(selectedElement.workspaceData.config, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ResourceDetailsModal; 