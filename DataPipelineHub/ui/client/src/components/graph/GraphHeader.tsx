import React from 'react';
import { CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2, Save } from 'lucide-react';

interface GraphHeaderProps {
  onClearGraph: () => void;
  onSaveGraph: () => void;
}

const GraphHeader: React.FC<GraphHeaderProps> = ({ onClearGraph, onSaveGraph }) => {
  return (
    <CardHeader className="py-3 px-6 border-b border-gray-800">
      <div className="flex justify-between items-center">
        <CardTitle className="text-lg font-heading">Graph Canvas</CardTitle>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onClearGraph}
            className="flex items-center"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onSaveGraph}
            className="bg-primary hover:bg-opacity-80 flex items-center"
          >
            <Save className="w-4 h-4" />
            Save
          </Button>
        </div>
      </div>
    </CardHeader>
  );
};

export default GraphHeader; 