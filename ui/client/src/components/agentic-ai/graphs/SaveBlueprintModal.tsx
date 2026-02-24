
import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { UmamiTrack } from '@/components/ui/umamitrack';
import { UmamiEvents } from '@/config/umamiEvents';

interface SaveBlueprintModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, description: string) => void;
  isLoading?: boolean;
  isEditMode?: boolean;
  defaultName?: string;
  defaultDescription?: string;
}

const SaveBlueprintModal: React.FC<SaveBlueprintModalProps> = ({
  isOpen,
  onClose,
  onSave,
  isLoading = false,
  isEditMode = false,
  defaultName = "",
  defaultDescription = "",
}) => {
  const [name, setName] = useState(defaultName);
  const [description, setDescription] = useState(defaultDescription);

  useEffect(() => {
    if (isEditMode) {
      setName(defaultName);
      setDescription(defaultDescription);
    }
  }, [isEditMode, defaultName, defaultDescription]);

  const handleSave = () => {
    if (!name.trim()) {
      return;
    }
    onSave(name.trim(), description.trim());
  };

  const handleClose = () => {
    setName(isEditMode ? defaultName : "");
    setDescription(isEditMode ? defaultDescription : "");
    onClose();
  };

  const isFormValid = name.trim().length > 0;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px] bg-gray-900 border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-white">
            {isEditMode ? "Update Workflow" : "Save Workflow"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="blueprint-name" className="text-gray-300">
              Name *
            </Label>
            <Input
              id="blueprint-name"
              placeholder={isEditMode && defaultName ? defaultName : "e.g., Slack, Docs & Jira Search"}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-dark-theme bg-input border-border text-foreground"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="blueprint-description" className="text-gray-300">
              Description
            </Label>
            <Textarea
              id="blueprint-description"
              placeholder="e.g., A multi-agent pipeline that combines document retrieval, Slack context, and Jira tool execution to produce a single smart answer to user questions."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="input-dark-theme bg-input border-border text-foreground resize-none"
              disabled={isLoading}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isLoading}
            className="border-gray-600 text-gray-300"
          >
            Cancel
          </Button>
          <UmamiTrack 
            event={UmamiEvents.AGENT_GRAPHS_SAVE_BUTTON}
          >
            <Button
              onClick={handleSave}
              disabled={!isFormValid || isLoading}
              className="bg-primary hover:bg-primary/80"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  {isEditMode ? "Updating..." : "Saving..."}
                </div>
              ) : (
                isEditMode ? "Update Workflow" : "Save Workflow"
              )}
            </Button>
          </UmamiTrack>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SaveBlueprintModal;