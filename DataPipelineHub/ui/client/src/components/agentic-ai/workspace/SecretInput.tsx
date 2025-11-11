import React, { useState } from 'react';
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
  const [showMasked, setShowMasked] = useState(true);
  
  // In edit mode: if value exists and matches original, show masked dots
  const originalValue = editingElement?.config?.[fieldName];
  const isUnchanged = editingElement && value && value === originalValue;
  
  // Display: show masked dots if unchanged, otherwise show actual (password type)
  const displayValue = (isUnchanged && showMasked) 
    ? maskSecretValue(originalValue, fieldSchema) 
    : (value || "");
  const inputType = (isUnchanged && showMasked) ? "text" : "password";

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // User started typing - stop showing masked
    if (showMasked) {
      setShowMasked(false);
    }
    onInputChange(fieldName, e.target.value);
  };

  const handleFocus = () => {
    // When user focuses, stop showing masked so they can type
    if (showMasked) {
      setShowMasked(false);
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
