import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';

const CustomNode: React.FC<NodeProps> = ({ data, selected, id }) => {
  return (
    <>
      <Handle
        type="target"
        position={Position.Top}
        style={{ 
          background: data.color, 
          width: 10, 
          height: 10
        }}
      />
      
      <motion.div 
        className={`rounded-lg px-4 py-3 border-2 min-w-[150px] relative ${data.style} ${
          selected ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-gray-600'
        }`}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {selected && (
          <button
            className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 transition-colors"
            onClick={() => data.onDelete && data.onDelete(id)}
          >
            <X className="w-3 h-3" />
          </button>
        )}
        
        <div className="flex items-center gap-2 mb-1">
          {data.icon}
          <span className="font-medium text-sm">{data.label}</span>
        </div>
        {data.description && (
          <p className="text-xs text-gray-400">{data.description}</p>
        )}
      </motion.div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ 
          background: data.color, 
          width: 10, 
          height: 10
        }}
      />
    </>
  );
};

export default CustomNode; 