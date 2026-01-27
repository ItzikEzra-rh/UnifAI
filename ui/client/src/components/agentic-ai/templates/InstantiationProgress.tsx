import React, { useEffect, useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, 
  XCircle, 
  LoaderCircle, 
  ArrowRight,
  RefreshCw,
  FileText,
  Zap,
  Server,
  MessageSquare
} from 'lucide-react';
import { InstantiationStatus, TemplateInstantiationResponse } from '@/types/templates';

interface InstantiationProgressProps {
  status: InstantiationStatus;
  result: TemplateInstantiationResponse | null;
  error?: string | null;
  onClose: () => void;
  onRetry: () => void;
  onNavigateToWorkflow: () => void;
  onNavigateToChat: () => void;
}

interface StepConfig {
  key: InstantiationStatus;
  label: string;
  icon: React.ReactNode;
}

const STEPS: StepConfig[] = [
  { key: 'validating', label: 'Validating inputs', icon: <FileText className="h-5 w-5" /> },
  { key: 'submitting', label: 'Submitting request', icon: <Zap className="h-5 w-5" /> },
  { key: 'provisioning', label: 'Provisioning resources', icon: <Server className="h-5 w-5" /> },
  { key: 'finalizing', label: 'Finalizing workflow', icon: <MessageSquare className="h-5 w-5" /> },
];

const getStepIndex = (status: InstantiationStatus): number => {
  const index = STEPS.findIndex(s => s.key === status);
  if (status === 'completed') return STEPS.length;
  if (status === 'failed') return -1;
  return index;
};

const getProgressValue = (status: InstantiationStatus): number => {
  switch (status) {
    case 'idle': return 0;
    case 'validating': return 15;
    case 'submitting': return 35;
    case 'provisioning': return 65;
    case 'finalizing': return 85;
    case 'completed': return 100;
    case 'failed': return 0;
    default: return 0;
  }
};

export const InstantiationProgress: React.FC<InstantiationProgressProps> = ({
  status,
  result,
  error,
  onClose,
  onRetry,
  onNavigateToWorkflow,
  onNavigateToChat
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const currentStepIndex = getStepIndex(status);
  const progressValue = getProgressValue(status);

  useEffect(() => {
    if (status !== 'idle') {
      setIsOpen(true);
    }
  }, [status]);

  const handleClose = () => {
    setIsOpen(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-background-card border-gray-800 text-foreground max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-heading">
            {status === 'completed' 
              ? 'Workflow Created!' 
              : status === 'failed' 
                ? 'Creation Failed' 
                : 'Creating Workflow...'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <Progress value={progressValue} className="h-2" />

          <div className="space-y-3">
            {STEPS.map((step, index) => {
              const isCompleted = currentStepIndex > index || status === 'completed';
              const isActive = currentStepIndex === index && status !== 'failed';
              const isFailed = status === 'failed' && currentStepIndex === index;

              return (
                <motion.div
                  key={step.key}
                  initial={{ opacity: 0.5 }}
                  animate={{ 
                    opacity: isCompleted || isActive ? 1 : 0.5 
                  }}
                  className={`flex items-center gap-3 p-3 rounded-lg border ${
                    isCompleted 
                      ? 'bg-green-500/10 border-green-500/30' 
                      : isActive 
                        ? 'bg-primary/10 border-primary/30' 
                        : isFailed
                          ? 'bg-red-500/10 border-red-500/30'
                          : 'bg-background-dark border-gray-800'
                  }`}
                >
                  <div className={`${
                    isCompleted 
                      ? 'text-green-500' 
                      : isActive 
                        ? 'text-primary' 
                        : isFailed
                          ? 'text-red-500'
                          : 'text-gray-500'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : isActive ? (
                      <LoaderCircle className="h-5 w-5 animate-spin" />
                    ) : isFailed ? (
                      <XCircle className="h-5 w-5" />
                    ) : (
                      step.icon
                    )}
                  </div>
                  <span className={`text-sm ${
                    isCompleted || isActive ? 'text-gray-200' : 'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                </motion.div>
              );
            })}
          </div>

          <AnimatePresence mode="wait">
            {status === 'completed' && result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-green-500 mb-2">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Success!</span>
                  </div>
                  <p className="text-sm text-gray-400">
                    Your workflow has been created and is ready to use.
                  </p>
                  {result.created_elements && result.created_elements.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                      Created {result.created_elements.length} elements
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={onNavigateToWorkflow}
                    className="flex-1 bg-primary hover:bg-primary/90"
                  >
                    View Workflow
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                  <Button 
                    onClick={onNavigateToChat}
                    variant="outline"
                    className="flex-1 border-gray-700"
                  >
                    Open Chat
                    <MessageSquare className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </motion.div>
            )}

            {status === 'failed' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-red-500 mb-2">
                    <XCircle className="h-5 w-5" />
                    <span className="font-medium">Creation Failed</span>
                  </div>
                  <p className="text-sm text-gray-400">
                    {error || 'An unexpected error occurred while creating the workflow.'}
                  </p>
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={onRetry}
                    className="flex-1 bg-primary hover:bg-primary/90"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry
                  </Button>
                  <Button 
                    onClick={handleClose}
                    variant="outline"
                    className="flex-1 border-gray-700"
                  >
                    Close
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default InstantiationProgress;