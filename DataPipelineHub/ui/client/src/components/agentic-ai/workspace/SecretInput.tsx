import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { FieldValidation } from "./FieldValidation";
import { FieldPopulation } from "./FieldPopulation";
import { ElementType } from "../../../types/workspace";

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
  maskSecretValue: (value: any, fieldSchema: any) => string;
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
  maskSecretValue,
}) => {
  // For secret fields: display masked dots if value hasn't changed from original, otherwise show actual
  const originalValue = editingElement?.config?.[fieldName];
  const maskedOriginal = originalValue !== undefined ? maskSecretValue(originalValue, fieldSchema) : "";
  const isUnchanged = editingElement && value === maskedOriginal;
  
  // Display: if unchanged, show masked dots; if changed, show actual (password type)
  const displayValue = isUnchanged ? maskedOriginal : value;
  const inputType = isUnchanged ? "text" : "password";

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let newValue = e.target.value;
    
    // If user is typing over masked value, extract just the typed characters
    // (browser may give us "a•••" when they type "a" over "••••")
    if (isUnchanged && newValue !== maskedOriginal) {
      const maskChar = fieldSchema?.hints?.secret?.mask_char || "•";
      // Check if newValue contains non-mask characters (user is typing)
      const nonMaskPart = newValue.split(maskChar).filter(part => part.length > 0).join("");
      if (nonMaskPart.length > 0) {
        // User is typing - use just the non-mask part (what they actually typed)
        onInputChange(fieldName, nonMaskPart);
        return;
      }
    }
    
    onInputChange(fieldName, newValue);
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

