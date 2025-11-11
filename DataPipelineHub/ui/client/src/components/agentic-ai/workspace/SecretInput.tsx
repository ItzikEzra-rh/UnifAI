import React, { useState, useEffect } from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { FieldValidation } from "./FieldValidation";
import { FieldPopulation } from "./FieldPopulation";
import { ElementType } from "../../../types/workspace";
import { maskSecretValue } from "../../../utils/maskSecretFields";

interface SecretInputProps {
  fieldName: string;
  fieldSchema: any;
  value: any;
  isRequired: boolean;
  validationHint: any;
  populateHint: any;
  editingElement: any;
  elementActions: any[];
  elementType: ElementType;
  formData: any;
  onInputChange: (field: string, value: any) => void;
  onValidationChange: (fieldName: string, isValid: boolean) => void;
  onPopulateResult: (fieldName: string, results: string[], multiSelect: boolean) => void;
}

export const SecretInput: React.FC<SecretInputProps> = ({
  fieldName,
  fieldSchema,
  value,
  isRequired,
  validationHint,
  populateHint,
  editingElement,
  elementActions,
  elementType,
  formData,
  onInputChange,
  onValidationChange,
  onPopulateResult,
}) => {
  const [isTyping, setIsTyping] = useState(false);
  
  // Get original value if editing
  const originalValue = editingElement?.config?.[fieldName];
  const hasOriginal = editingElement && originalValue !== undefined;
  
  // Reset typing state when form opens/closes or editingElement changes
  useEffect(() => {
    setIsTyping(false);
  }, [editingElement, fieldName]);
  
  // Determine what to display: show masked if we have original, user hasn't typed, and value matches original
  const shouldShowMasked = hasOriginal && !isTyping && value === originalValue;
  const displayValue = shouldShowMasked ? maskSecretValue(originalValue, fieldSchema) : (value || "");
  const inputType = shouldShowMasked ? "text" : "password";

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    // Mark as typing when user starts typing
    if (!isTyping) {
      setIsTyping(true);
    }
    
    onInputChange(fieldName, newValue);
  };

  const handleFocus = () => {
    // When user focuses on masked field, clear it so they can type fresh
    if (shouldShowMasked) {
      setIsTyping(true);
      onInputChange(fieldName, "");
    }
  };

  return (
    <div key={fieldName} className="space-y-2">
      <Label htmlFor={fieldName}>
        {fieldName} {isRequired && <span className="text-red-400">*</span>}
        <Badge variant="outline" className="ml-2 text-xs">
          secret
        </Badge>
        {validationHint && (
          <Badge variant="outline" className="ml-2 text-xs">
            validation
          </Badge>
        )}
        {populateHint && (
          <Badge variant="outline" className="ml-2 text-xs">
            populate
          </Badge>
        )}
      </Label>
      <Input
        id={fieldName}
        type={inputType}
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        className="bg-background-dark"
        placeholder={fieldSchema.description}
        readOnly={!!populateHint}
        disabled={!!populateHint}
      />
      {validationHint && (
        <FieldValidation
          fieldName={fieldName}
          fieldValue={value}
          validationHint={validationHint}
          elementActions={elementActions}
          selectedElementType={elementType}
          onValidationChange={onValidationChange}
        />
      )}
      {populateHint && (
        <FieldPopulation
          fieldName={fieldName}
          populateHint={populateHint}
          elementActions={elementActions}
          selectedElementType={elementType}
          formData={formData}
          onPopulateResult={onPopulateResult}
        />
      )}
      {fieldSchema.description && (
        <p className="text-xs text-gray-400">{fieldSchema.description}</p>
      )}
    </div>
  );
};
