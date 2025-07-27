import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BuildingBlock } from '@/types/graph';
import { getCategoryDisplay, getCategoryDisplayName } from '../shared/helpers';
import { Eye } from 'lucide-react';
import ResourceDetailsModal from '../../workspace/ResourceDetailsModal';

interface BuildingBlocksSidebarProps {
  buildingBlocks: BuildingBlock[];
  isLoading: boolean;
  onDragStart: (event: React.DragEvent, block: BuildingBlock) => void;
}

const BuildingBlocksSidebar: React.FC<BuildingBlocksSidebarProps> = ({ buildingBlocks, isLoading, onDragStart }) => {
  const [selectedElement, setSelectedElement] = useState<BuildingBlock | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);

  const handleViewDetails = (block: BuildingBlock) => {
    setSelectedElement(block);
    setIsDetailsModalOpen(true);
  };

  return (
    <div className="w-80">
      <Card className="bg-background-card shadow-card border-gray-800 h-full">
        <CardHeader className="py-3 px-6 border-b border-gray-800">
          <CardTitle className="text-lg font-heading">Elements</CardTitle>
          <p className="text-sm text-gray-400">
            {isLoading ? "Loading building blocks..." : "Drag components to the canvas"}
          </p>
        </CardHeader>
        <CardContent className="p-4">
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gray-700"></div>
                    <div>
                      <div className="h-4 bg-gray-700 rounded w-20 mb-1"></div>
                      <div className="h-3 bg-gray-700 rounded w-32"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {buildingBlocks.map((block) => (
                <Card key={block.id} className="bg-gray-800 border-gray-700 hover:border-gray-600 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div
                        className="flex items-center gap-3 flex-1 cursor-grab active:cursor-grabbing"
                        draggable
                        onDragStart={(event: React.DragEvent) => onDragStart(event, block)}
                      >
                        <div 
                          className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
                          style={{ backgroundColor: block.color }}
                        >
                          {block.workspaceData ? 
                            getCategoryDisplay(block.workspaceData.category).icon : 
                            getCategoryDisplay('default').icon
                          }
                        </div>
                        <div className="flex-1">
                          <h3 className="font-medium text-white">{block.label}</h3>
                          <p className="text-xs text-gray-400">
                            {block.workspaceData ? 
                              `${getCategoryDisplayName(block.workspaceData.category)} | ${block.workspaceData.type}` : 
                              'Drag to add to graph'
                            }
                          </p>
                        </div>
                      </div>
                      
                      {block.workspaceData && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-8 w-8 p-0 text-gray-400 hover:text-white"
                          onClick={() => handleViewDetails(block)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          
          {/* Instructions */}
          {!isLoading && (
            <div className="mt-6 p-4 bg-gray-900 rounded-lg border border-gray-700">
              <h4 className="font-medium text-white mb-2">How to use:</h4>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• Drag blocks to the canvas</li>
                <li>• Connect nodes by dragging from handles</li>
                <li>• Click nodes to select them</li>
                <li>• Press Delete button on keyboard/X button to remove selected nodes</li>
                <li>• Use controls to zoom and pan</li>
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <ResourceDetailsModal 
        isOpen={isDetailsModalOpen}
        onClose={setIsDetailsModalOpen}
        selectedElement={selectedElement}
      />
    </div>
  );
};

export default BuildingBlocksSidebar; 