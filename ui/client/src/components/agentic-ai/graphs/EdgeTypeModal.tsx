import React, { useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ArrowRight, ArrowLeftRight } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { deriveThemeColors } from "@/lib/colorUtils";

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
  const { primaryHex } = useTheme();
  const colors = useMemo(() => deriveThemeColors(primaryHex), [primaryHex]);

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
              className="group h-auto py-4 px-3 rounded-lg border border-gray-600 bg-transparent hover:bg-primary/10 hover:border-primary/60 transition-all flex flex-col items-center gap-2 cursor-pointer"
              onClick={() => onConfirm("unidirectional")}
            >
              <ArrowRight className="w-6 h-6 text-primary group-hover:text-primary" />
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
              className="group h-auto py-4 px-3 rounded-lg border border-gray-600 bg-transparent transition-all flex flex-col items-center gap-2 cursor-pointer"
              style={{
                ['--hover-bg' as string]: `${colors.primaryLight}15`,
                ['--hover-border' as string]: colors.primaryLight,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = `${colors.primaryLight}15`;
                e.currentTarget.style.borderColor = `${colors.primaryLight}99`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.borderColor = '';
              }}
              onClick={() => onConfirm("bidirectional")}
            >
              <ArrowLeftRight className="w-6 h-6" style={{ color: colors.primaryLight }} />
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
