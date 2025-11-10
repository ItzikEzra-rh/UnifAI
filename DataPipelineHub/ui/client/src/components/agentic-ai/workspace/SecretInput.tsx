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
  editingSecretFields: { [fieldName: string]: boolean };
  originalSecretValues: { [fieldName: string]: any };
  elementActions: any[];
  elementType: ElementType;
  formData: any;
  onInputChange: (field: string, value: any) => void;
  onValidationChange: (fieldName: string, isValid: boolean) => void;
  onPopulateResult: (fieldName: string, results: string[], multiSelect: boolean) => void;
  onEditingSecretFieldsChange: (fieldName: string, isEditing: boolean) => void;
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
  editingSecretFields,
  originalSecretValues,
  elementActions,
  elementType,
  formData,
  onInputChange,
  onValidationChange,
  onPopulateResult,
  onEditingSecretFieldsChange,
  maskSecretValue,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    // If user is typing in a secret field, mark it as being edited
    if (!editingSecretFields[fieldName]) {
      onEditingSecretFieldsChange(fieldName, true);
      if (editingElement && fieldSchema) {
        const originalValue = originalSecretValues[fieldName];
        if (originalValue !== undefined) {
          const maskedOriginal = maskSecretValue(originalValue, fieldSchema);
          if (value === maskedOriginal) {
            onInputChange(fieldName, newValue);
            return;
          }
        }
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
        type={editingSecretFields[fieldName] ? "password" : "text"}
        value={value}
        onChange={handleChange}
        className="bg-background-dark"
        placeholder={
          editingElement && !editingSecretFields[fieldName]
            ? "Click to edit"
            : fieldSchema.description
        }
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

