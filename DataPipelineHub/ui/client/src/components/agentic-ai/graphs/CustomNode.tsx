
import React from "react";
import { Handle, Position } from "reactflow";
import { X } from "lucide-react";
import { CustomNodeData } from "@/types/graph";
import InnerRefElement from "./InnerRefElement";

interface CustomNodeProps {
  id: string;
  data: CustomNodeData & { allBlocks?: any[] };
  selected: boolean;
}

const CustomNode: React.FC<CustomNodeProps> = ({ id, data, selected }) => {
  const handleDelete = () => {
    if (data.onDelete) {
      data.onDelete(id);
    }
  };

  // Extract reference IDs from the node configuration
  const extractReferences = (config: any): { [key: string]: string } => {
    const refs: { [key: string]: string } = {};
    
    if (!config || typeof config !== "object") {
      return refs;
    }

    const traverse = (obj: any, path: string = "") => {
      for (const [key, value] of Object.entries(obj)) {
        if (typeof value === "string" && value.startsWith("$ref:")) {
          // Extract the actual reference ID after $ref:
          const refId = value.substring(5);
          refs[key] = refId;
        } else if (Array.isArray(value)) {
          // Handle arrays that might contain $ref values
          value.forEach((item, index) => {
            if (typeof item === "string" && item.startsWith("$ref:")) {
              const refId = item.substring(5);
              refs[`${key}[${index}]`] = refId;
            }
          });
        } else if (typeof value === "object" && value !== null) {
          traverse(value, path ? `${path}.${key}` : key);
        }
      }
    };

    traverse(config);
    return refs;
  };

  const references = data.workspaceData?.config 
    ? extractReferences(data.workspaceData.config)
    : {};

  return (
    <div
      className={`px-4 py-3 shadow-lg rounded-lg border-2 bg-gray-800 text-white min-w-[200px] ${
        selected ? "border-blue-500" : "border-gray-600"
      } hover:border-gray-500 transition-colors`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />

      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 flex items-center justify-center">
            {data.icon}
          </div>
          <div className="font-medium text-sm">{data.label}</div>
        </div>
        
        {selected && (
          <button
            onClick={handleDelete}
            className="w-5 h-5 text-gray-400 hover:text-red-400 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Inner reference elements */}
      {Object.keys(references).length > 0 && (
        <div className="mt-2 space-y-1">
          <div className="text-xs text-gray-400 mb-1">References:</div>
          <div className="flex flex-wrap gap-1">
            {Object.entries(references).map(([key, refId]) => (
              <InnerRefElement
                key={`${key}-${refId}`}
                refId={refId}
                refData={{ key, value: refId }}
                allBlocks={data.allBlocks || []}
              />
            ))}
          </div>
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />
    </div>
  );
};

export default CustomNode;