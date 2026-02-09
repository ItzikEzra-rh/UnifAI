import React from 'react';
import { CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { ElementValidationResult } from '@/types/validation';
import SimpleTooltip from '@/components/shared/SimpleTooltip';

interface NodeValidationIndicatorProps {
  validationResult?: ElementValidationResult;
  isValidating?: boolean;
  onClick?: (e: React.MouseEvent) => void;
  className?: string;
}

/**
 * A compact validation indicator component for displaying on graph nodes.
 * Shows a green checkmark for valid nodes, yellow warning for invalid nodes,
 * and a spinner while validation is in progress.
 */
export const NodeValidationIndicator: React.FC<NodeValidationIndicatorProps> = ({
  validationResult,
  isValidating = false,
  onClick,
  className = '',
}) => {
  // Show spinner while validating
  if (isValidating) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <SimpleTooltip content={<p>Validating...</p>}>
          <div className={`p-2 rounded-full bg-gray-700/50`}>
            <Loader2 className={`h-6 w-6 text-gray-400 animate-spin`} />
          </div>
        </SimpleTooltip>
      </div>
    );
  }

  // Don't show anything if no validation result
  if (!validationResult || validationResult.is_valid) {
    return null;
  }

  const isValid = validationResult.is_valid;

  // Count issues by severity
  const errorCount = validationResult.messages.filter(m => m.severity === 'error').length;
  const warningCount = validationResult.messages.filter(m => m.severity === 'warning').length;

  const tooltipContent = isValid
    ? 'Validation passed'
    : `${errorCount} error${errorCount !== 1 ? 's' : ''}${warningCount > 0 ? `, ${warningCount} warning${warningCount !== 1 ? 's' : ''}` : ''}`;

  return (
    <div
      className={`flex items-center justify-center cursor-pointer transition-transform hover:scale-110 ${className}`}
      onClick={(e) => {
        e.stopPropagation();
        onClick?.(e);
      }}
    >
      <SimpleTooltip content={<p>{tooltipContent}</p>}>
          <div
            className={`p-2 rounded-full bg-yellow-500/25 hover:bg-yellow-500/20 ring-1 ring-yellow-500/30 shadow-lg`}>
            <AlertTriangle className={`h-6 w-6 text-yellow-500 drop-shadow-[0_0_3px_rgba(234,179,8,0.4)]`} />
          </div>
      </SimpleTooltip>
    </div>
  );
};

export default NodeValidationIndicator;

