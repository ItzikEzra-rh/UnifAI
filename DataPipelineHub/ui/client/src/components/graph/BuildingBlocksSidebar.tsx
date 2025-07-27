import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BuildingBlock } from '@/types/graph';
import { getIconComponent } from '../shared/helpers';

interface BuildingBlocksSidebarProps {
  buildingBlocks: BuildingBlock[];
  isLoading: boolean;
  onDragStart: (event: React.DragEvent, block: BuildingBlock) => void;
}

const BuildingBlocksSidebar: React.FC<BuildingBlocksSidebarProps> = ({ buildingBlocks, isLoading, onDragStart }) => {
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
              {/* Loading skeleton */}
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
                <div
                  key={block.id}
                  className="bg-gray-800 rounded-lg p-4 cursor-grab active:cursor-grabbing border border-gray-700 hover:border-gray-600 transition-colors"
                  draggable
                  onDragStart={(event: React.DragEvent) => onDragStart(event, block)}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
                      style={{ backgroundColor: block.color }}
                    >
                      {getIconComponent(block.iconType)}
                    </div>
                    <div>
                      <h3 className="font-medium text-white">{block.label}</h3>
                      <p className="text-xs text-gray-400">
                        Drag to add to graph
                      </p>
                    </div>
                  </div>
                </div>
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
    </div>
  );
};

export default BuildingBlocksSidebar; 