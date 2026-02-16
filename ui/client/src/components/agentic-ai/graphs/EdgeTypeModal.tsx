import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ArrowRight, ArrowLeftRight } from "lucide-react";

interface EdgeTypeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (type: "unidirectional" | "bidirectional") => void;
  sourceNodeName: string;
  targetNodeName: string;
}

const EdgeTypeModal: React.FC<EdgeTypeModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  sourceNodeName,
  targetNodeName,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[450px] bg-gray-900 border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-white">Create Connection</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-400">
              Connect{" "}
              <span className="text-white font-medium">{sourceNodeName}</span>{" "}
              and{" "}
              <span className="text-white font-medium">{targetNodeName}</span>
            </p>
          </div>

          <div className="text-sm text-gray-300">Choose connection type:</div>

          <div className="grid grid-cols-2 gap-3">
            <button
              className="group h-auto py-4 px-3 rounded-lg border border-gray-600 bg-transparent hover:border-purple-500 hover:bg-purple-900/20 transition-all flex flex-col items-center gap-2 cursor-pointer"
              onClick={() => onConfirm("unidirectional")}
            >
              <ArrowRight className="w-6 h-6 text-purple-400 group-hover:text-purple-300" />
              <div className="text-center">
                <div className="font-medium text-white text-sm">
                  Unidirectional
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {sourceNodeName} → {targetNodeName}
                </div>
              </div>
            </button>

            <button
              className="group h-auto py-4 px-3 rounded-lg border border-gray-600 bg-transparent hover:border-emerald-500 hover:bg-emerald-900/20 transition-all flex flex-col items-center gap-2 cursor-pointer"
              onClick={() => onConfirm("bidirectional")}
            >
              <ArrowLeftRight className="w-6 h-6 text-emerald-400 group-hover:text-emerald-300" />
              <div className="text-center">
                <div className="font-medium text-white text-sm">
                  Bidirectional
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {sourceNodeName} ↔ {targetNodeName}
                </div>
              </div>
            </button>
          </div>

          <div className="flex justify-end pt-2">
            <Button
              variant="outline"
              onClick={onClose}
              className="border-gray-600 text-gray-300"
            >
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default EdgeTypeModal;
