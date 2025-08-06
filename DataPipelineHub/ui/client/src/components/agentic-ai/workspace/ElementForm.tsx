import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  ElementType,
  ElementSchema,
  ElementInstance,
} from "../../../types/workspace";
import { useWorkspaceData } from "../../../hooks/useWorkspaceData";

interface ElementFormProps {
  isOpen: boolean;
  onClose: () => void;
  elementType: ElementType;
  elementSchema: ElementSchema;
  editingElement: ElementInstance | null;
  onSave: (data: any) => Promise<void>;
}

export const ElementForm: React.FC<ElementFormProps> = ({
  isOpen,
  onClose,
  elementType,
  elementSchema,
  editingElement,
  onSave,
}) => {
  const [formData, setFormData] = useState<any>({});
  const [isSaving, setIsSaving] = useState(false);
  const [refOptions, setRefOptions] = useState<{ [category: string]: any[] }>(
    {},
  );
  const [resourceSchema, setResourceSchema] = useState<any>(null);
  const [firstLevelRequired, setFirstLevelRequired] = useState<string[]>([]);

  const { fetchResourcesForCategory, fetchResourceSchema } = useWorkspaceData();

  // Fetch resource schema and determine first-level required fields
  useEffect(() => {
    const loadResourceSchema = async () => {
      const schema = await fetchResourceSchema();
      if (schema) {
        setResourceSchema(schema);
        
        // Extract required fields, excluding 'category', 'type', and 'cfg_dict'
        const required = schema.required || [];
        const filteredRequired = required.filter((field: string) => 
          field !== 'category' && field !== 'type' && field !== 'cfg_dict'
        );
        setFirstLevelRequired(filteredRequired);
      } else {
        // Fallback to current behavior if schema fetch fails
        setFirstLevelRequired(['name']);
      }
    };

    if (isOpen) {
      loadResourceSchema();
    }
  }, [isOpen, fetchResourceSchema]);

  // Initialize form data
  useEffect(() => {
    if (elementSchema && isOpen && resourceSchema) {
      const initialData: any = {};

      // Initialize first-level required fields
      firstLevelRequired.forEach((field) => {
        const fieldSchema = resourceSchema.properties?.[field];
        if (fieldSchema) {
          if (fieldSchema.default !== undefined) {
            initialData[field] = fieldSchema.default;
          } else if (fieldSchema.type === "array") {
            initialData[field] = [];
          } else if (fieldSchema.type === "boolean") {
            initialData[field] = false;
          } else if (fieldSchema.type === "object") {
            initialData[field] = {};
          } else {
            initialData[field] = "";
          }
        } else {
          // Fallback for fields without schema
          initialData[field] = "";
        }
      });

      // Set default values from element config schema
      Object.entries(elementSchema.config_schema.properties).forEach(
        ([key, property]: [string, any]) => {
          if (property.default !== undefined) {
            initialData[key] = property.default;
          } else if (property.type === "array") {
            initialData[key] = [];
          } else if (property.type === "boolean") {
            initialData[key] = false;
          } else if (property.type === "object") {
            initialData[key] = {};
          } else {
            initialData[key] = "";
          }
        },
      );

      // If editing, populate with existing data
      if (editingElement) {
        // Handle first-level required fields
        firstLevelRequired.forEach((field) => {
          if (editingElement[field] !== undefined) {
            initialData[field] = editingElement[field];
          }
        });

        // Handle config data
        if (editingElement.config) {
          Object.entries(editingElement.config).forEach(([key, value]) => {
            // Handle $ref values - extract the rid from $ref:rid format
            if (typeof value === "string" && value.startsWith("$ref:")) {
              initialData[key] = value.substring(5); // Remove '$ref:' prefix
            } else if (Array.isArray(value)) {
              // Handle array of $ref values
              initialData[key] = value.map((item: any) =>
                typeof item === "string" && item.startsWith("$ref:")
                  ? item.substring(5)
                  : item,
              );
            } else {
              initialData[key] = value;
            }
          });
        }
      }

      setFormData(initialData);
    }
  }, [elementSchema, editingElement, isOpen, resourceSchema, firstLevelRequired]);

  // Re-apply form data when ref options are loaded (for proper pre-selection)
  useEffect(() => {
    if (editingElement?.config && Object.keys(refOptions).length > 0) {
      setFormData((prevData) => {
        const updatedData = { ...prevData };

        Object.entries(editingElement.config).forEach(([key, value]) => {
          if (typeof value === "string" && value.startsWith("$ref:")) {
            const rid = value.substring(5);
            updatedData[key] = rid;
          } else if (Array.isArray(value)) {
            // Handle array of $ref values
            updatedData[key] = value.map((item: any) =>
              typeof item === "string" && item.startsWith("$ref:")
                ? item.substring(5)
                : item,
            );
          }
        });

        return updatedData;
      });
    }
  }, [refOptions, editingElement]);

  // Helper function to check if a field is an array with $ref items
  const isArrayWithRefItems = (fieldSchema: any) => {
    // Direct array type
    if (
      fieldSchema.type === "array" &&
      fieldSchema.items &&
      fieldSchema.items.$ref
    ) {
      return true;
    }
    // anyOf structure (like tools field)
    if (fieldSchema.anyOf && Array.isArray(fieldSchema.anyOf)) {
      return fieldSchema.anyOf.some(
        (option: any) =>
          option.type === "array" && option.items && option.items.$ref,
      );
    }
    return false;
  };

  // Helper function to get array items schema from anyOf or direct structure
  const getArrayItemsSchema = (fieldSchema: any) => {
    if (fieldSchema.type === "array" && fieldSchema.items) {
      return fieldSchema.items;
    }
    if (fieldSchema.anyOf && Array.isArray(fieldSchema.anyOf)) {
      const arrayOption = fieldSchema.anyOf.find(
        (option: any) => option.type === "array" && option.items,
      );
      return arrayOption?.items;
    }
    return null;
  };

  // Load reference options for $ref fields
  useEffect(() => {
    if (elementSchema && isOpen) {
      const refFields = Object.entries(
        elementSchema.config_schema.properties,
      ).filter(
        ([, property]: [string, any]) =>
          property.$ref ||
          (property.items && property.items.$ref) ||
          (property.type === "array" &&
            property.items &&
            property.items.$ref) ||
          isArrayWithRefItems(property) ||
          (property.anyOf && property.anyOf.some((option: any) => option.$ref)),
      );

      const refCategories = new Set<string>();
      refFields.forEach(([, property]: [string, any]) => {
        if (property.category) {
          refCategories.add(property.category);
        }
        if (property.items && property.items.category) {
          refCategories.add(property.items.category);
        }
        // Handle anyOf structure
        const itemsSchema = getArrayItemsSchema(property);
        if (itemsSchema && itemsSchema.category) {
          refCategories.add(itemsSchema.category);
        }
        // Handle anyOf with $ref
        if (property.anyOf) {
          property.anyOf.forEach((option: any) => {
            if (option.$ref && option.category) {
              refCategories.add(option.category);
            }
          });
        }
      });

      // Fetch actual reference options from Resources API
      const loadRefOptions = async () => {
        const options: { [category: string]: any[] } = {};

        for (const category of refCategories) {
          try {
            const resources = await fetchResourcesForCategory(category);
            options[category] = resources;
          } catch (error) {
            console.error(
              `Failed to load resources for category ${category}:`,
              error,
            );
            options[category] = [];
          }
        }

        setRefOptions(options);
      };

      if (refCategories.size > 0) {
        loadRefOptions();
      }
    }
  }, [elementSchema, isOpen, fetchResourcesForCategory]);

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleArrayChange = (field: string, index: number, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: prev[field].map((item: any, i: number) =>
        i === index ? value : item,
      ),
    }));
  };

  const addArrayItem = (field: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: [...(prev[field] || []), ""],
    }));
  };

  const removeArrayItem = (field: string, index: number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: prev[field].filter((_: any, i: number) => i !== index),
    }));
  };

  // Check if all required fields are filled
  const isFormValid = () => {
    if (!elementSchema || !resourceSchema) return false;

    // Check first-level required fields
    const firstLevelValid = firstLevelRequired.every((field) => {
      const value = formData[field];
      if (Array.isArray(value)) {
        return value.length > 0;
      }
      return value !== undefined && value !== null && value !== "" && 
             (typeof value !== "string" || value.trim() !== "");
    });

    if (!firstLevelValid) return false;

    // Check config schema required fields
    const required = elementSchema.config_schema.required || [];
    return required.every((field) => {
      const value = formData[field];
      if (Array.isArray(value)) {
        return value.length > 0;
      }
      return value !== undefined && value !== null && value !== "";
    });
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);

      // Validate first-level required fields (dynamic from resource schema)
      const missingFirstLevel = firstLevelRequired.filter((field) => {
        const value = formData[field];
        if (Array.isArray(value)) {
          return value.length === 0;
        }
        return !value || (typeof value === "string" && value.trim() === "");
      });

      if (missingFirstLevel.length > 0) {
        alert(`Please fill in required fields: ${missingFirstLevel.join(", ")}`);
        return;
      }

      // Validate config schema required fields
      const required = elementSchema.config_schema.required || [];
      const missing = required.filter((field) => {
        const value = formData[field];
        if (Array.isArray(value)) {
          return value.length === 0;
        }
        return !value || value === "";
      });

      if (missing.length > 0) {
        alert(`Please fill in required config fields: ${missing.join(", ")}`);
        return;
      }

      // Prepare data for saving
      const saveData: any = {};
      
      // Add first-level required fields
      firstLevelRequired.forEach((field) => {
        if (formData[field] !== undefined) {
          saveData[field] = typeof formData[field] === "string" ? 
            formData[field].trim() : formData[field];
        }
      });

      // Prepare config data - convert $ref fields back to proper format
      const configForSave = { ...formData };
      
      // Remove first-level fields from config
      firstLevelRequired.forEach((field) => {
        delete configForSave[field];
      });

      // Convert reference fields back to $ref:rid format
      Object.entries(elementSchema.config_schema.properties).forEach(
        ([fieldName, fieldSchema]: [string, any]) => {
          if (
            fieldSchema.$ref &&
            configForSave[fieldName] &&
            configForSave[fieldName] !== ""
          ) {
            configForSave[fieldName] = `$ref:${configForSave[fieldName]}`;
          }
          // Handle anyOf with $ref
          if (
            fieldSchema.anyOf &&
            fieldSchema.anyOf.some((option: any) => option.$ref) &&
            configForSave[fieldName] &&
            configForSave[fieldName] !== ""
          ) {
            configForSave[fieldName] = `$ref:${configForSave[fieldName]}`;
          }
          // Handle array fields with $ref items (including anyOf structure)
          if (
            isArrayWithRefItems(fieldSchema) &&
            Array.isArray(configForSave[fieldName])
          ) {
            configForSave[fieldName] = configForSave[fieldName].map(
              (rid: string) => `$ref:${rid}`,
            );
          }
        },
      );

      // Add cfg_dict to save data
      saveData.cfg_dict = configForSave;

      const result = await onSave(saveData);

      // Only close the dialog if save was successful (result is not null/false)
      if (result !== null && result !== false) {
        onClose();
      }
    } catch (error) {
      console.error("Error saving element:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const renderFormField = (fieldName: string, fieldSchema: any, isFirstLevel: boolean = false) => {
    const isRequired = isFirstLevel 
      ? firstLevelRequired.includes(fieldName)
      : elementSchema.config_schema.required?.includes(fieldName);
    const value = formData[fieldName] || "";

    // Handle array fields with $ref items (multi-select dropdown)
    if (isArrayWithRefItems(fieldSchema)) {
      const itemsSchema = getArrayItemsSchema(fieldSchema);
      const category = itemsSchema?.category;

      if (!category) {
        console.warn(`No category found for array field ${fieldName}`);
        return null;
      }

      const validOptions = (refOptions[category] || []).filter(
        (option: any) => option.rid && option.rid.trim() !== "",
      );

      return (
        <div key={fieldName} className="space-y-2">
          <Label htmlFor={fieldName}>
            {fieldName} {isRequired && <span className="text-red-400">*</span>}
            {category && (
              <Badge variant="outline" className="ml-2 text-xs">
                {category}
              </Badge>
            )}
          </Label>
          <div className="space-y-2">
            <Select
              value=""
              onValueChange={(newValue) => {
                if (newValue && newValue !== "__no_options_disabled__") {
                  const currentArray = formData[fieldName] || [];
                  if (!currentArray.includes(newValue)) {
                    handleInputChange(fieldName, [...currentArray, newValue]);
                  }
                }
              }}
            >
              <SelectTrigger className="bg-background-dark">
                <SelectValue placeholder={`Add ${category}`} />
              </SelectTrigger>
              <SelectContent>
                {validOptions.map((option: any) => (
                  <SelectItem key={option.rid} value={option.rid}>
                    {option.name} ({option.type})
                  </SelectItem>
                ))}
                {validOptions.length === 0 && (
                  <SelectItem value="__no_options_disabled__" disabled>
                    No {category} resources available
                  </SelectItem>
                )}
              </SelectContent>
            </Select>

            {/* Show selected items */}
            {value && Array.isArray(value) && value.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {value.map((selectedRid: string, index: number) => {
                  const selectedOption = validOptions.find(
                    (opt: any) => opt.rid === selectedRid,
                  );
                  return (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="flex items-center gap-1"
                    >
                      {selectedOption
                        ? `${selectedOption.name} (${selectedOption.type})`
                        : selectedRid}
                      <button
                        type="button"
                        onClick={() => {
                          const newArray = value.filter(
                            (_: any, i: number) => i !== index,
                          );
                          handleInputChange(fieldName, newArray);
                        }}
                        className="ml-1 text-xs hover:text-red-400"
                      >
                        ×
                      </button>
                    </Badge>
                  );
                })}
              </div>
            )}
          </div>
          {fieldSchema.description && (
            <p className="text-xs text-gray-400">{fieldSchema.description}</p>
          )}
        </div>
      );
    }

    // Handle $ref fields (dropdown selection) - including anyOf with $ref
    const hasRefField = fieldSchema.$ref || 
      (fieldSchema.anyOf && fieldSchema.anyOf.some((option: any) => option.$ref));
    
    if (hasRefField) {
      // Extract category from direct $ref or from anyOf structure
      let category = fieldSchema.category;
      if (!category && fieldSchema.anyOf) {
        const refOption = fieldSchema.anyOf.find((option: any) => option.$ref && option.category);
        category = refOption?.category;
      }

      if (category) {
        const validOptions = (refOptions[category] || []).filter(
          (option: any) => option.rid && option.rid.trim() !== "",
        );

        return (
          <div key={fieldName} className="space-y-2">
            <Label htmlFor={fieldName}>
              {fieldName} {isRequired && <span className="text-red-400">*</span>}
              {category && (
                <Badge variant="outline" className="ml-2 text-xs">
                  {category}
                </Badge>
              )}
            </Label>
            <Select
              value={value && value !== "" ? value : undefined}
              onValueChange={(newValue) => {
                handleInputChange(fieldName, newValue);
              }}
            >
              <SelectTrigger className="bg-background-dark">
                <SelectValue placeholder={`Select ${fieldName}`} />
              </SelectTrigger>
              <SelectContent>
                {validOptions.map((option: any) => (
                  <SelectItem key={option.rid} value={option.rid}>
                    {option.name} ({option.type})
                  </SelectItem>
                ))}
                {validOptions.length === 0 && (
                  <SelectItem value="__no_options_disabled__" disabled>
                    No {category} resources available
                  </SelectItem>
                )}
              </SelectContent>
            </Select>

            {fieldSchema.description && (
              <p className="text-xs text-gray-400">{fieldSchema.description}</p>
            )}
          </div>
        );
      }
    }

    // Handle object fields (like 'extra')
    if (fieldSchema.type === "object") {
      return (
        <div key={fieldName} className="space-y-2">
          <Label htmlFor={fieldName}>
            {fieldName} {isRequired && <span className="text-red-400">*</span>}
          </Label>
          <Textarea
            id={fieldName}
            value={
              typeof value === "object" ? JSON.stringify(value, null, 2) : value
            }
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleInputChange(fieldName, parsed);
              } catch (error) {
                // If invalid JSON, store as string for now
                handleInputChange(fieldName, e.target.value);
              }
            }}
            rows={6}
            className="bg-background-dark resize-none font-mono text-sm"
            placeholder="Enter JSON object (e.g., {})"
          />
          {fieldSchema.description && (
            <p className="text-xs text-gray-400">{fieldSchema.description}</p>
          )}
        </div>
      );
    }

    // Handle array fields (non-$ref arrays)
    if (fieldSchema.type === "array") {
      return (
        <div key={fieldName} className="space-y-2">
          <Label>
            {fieldName} {isRequired && <span className="text-red-400">*</span>}
          </Label>
          <div className="space-y-2">
            {(value || []).map((item: any, index: number) => (
              <div key={index} className="flex gap-2">
                <Input
                  value={item}
                  onChange={(e) =>
                    handleArrayChange(fieldName, index, e.target.value)
                  }
                  className="bg-background-dark flex-1"
                  placeholder={`${fieldName} item ${index + 1}`}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => removeArrayItem(fieldName, index)}
                >
                  Remove
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => addArrayItem(fieldName)}
            >
              Add {fieldName}
            </Button>
          </div>
          {fieldSchema.description && (
            <p className="text-xs text-gray-400">{fieldSchema.description}</p>
          )}
        </div>
      );
    }

    // Handle boolean fields
    if (fieldSchema.type === "boolean") {
      return (
        <div key={fieldName} className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id={fieldName}
              checked={value}
              onCheckedChange={(checked) =>
                handleInputChange(fieldName, checked)
              }
            />
            <Label htmlFor={fieldName}>
              {fieldName}{" "}
              {isRequired && <span className="text-red-400">*</span>}
            </Label>
          </div>
          {fieldSchema.description && (
            <p className="text-xs text-gray-400">{fieldSchema.description}</p>
          )}
        </div>
      );
    }

    // Handle number fields (including anyOf with integer/number types)
    const isNumberField = fieldSchema.type === "integer" || 
      fieldSchema.type === "number" ||
      (fieldSchema.anyOf && fieldSchema.anyOf.some((option: any) => 
        option.type === "integer" || option.type === "number"
      ));

    if (isNumberField) {
      return (
        <div key={fieldName} className="space-y-2">
          <Label htmlFor={fieldName}>
            {fieldName} {isRequired && <span className="text-red-400">*</span>}
          </Label>
          <Input
            id={fieldName}
            type="number"
            value={value || ""}
            onChange={(e) => {
              const numValue = e.target.value === "" ? null : parseFloat(e.target.value);
              handleInputChange(fieldName, numValue);
            }}
            className="bg-background-dark"
            placeholder={fieldSchema.description}
          />
          {fieldSchema.description && (
            <p className="text-xs text-gray-400">{fieldSchema.description}</p>
          )}
        </div>
      );
    }

    // Handle long text fields
    if (
      fieldName.includes("message") ||
      fieldName.includes("prompt") ||
      fieldName.includes("description")
    ) {
      return (
        <div key={fieldName} className="space-y-2">
          <Label htmlFor={fieldName}>
            {fieldName} {isRequired && <span className="text-red-400">*</span>}
          </Label>
          <Textarea
            id={fieldName}
            value={value}
            onChange={(e) => handleInputChange(fieldName, e.target.value)}
            rows={4}
            className="bg-background-dark resize-none"
            placeholder={fieldSchema.description}
          />
          {fieldSchema.description && (
            <p className="text-xs text-gray-400">{fieldSchema.description}</p>
          )}
        </div>
      );
    }

    // Handle regular string fields
    return (
      <div key={fieldName} className="space-y-2">
        <Label htmlFor={fieldName}>
          {fieldName} {isRequired && <span className="text-red-400">*</span>}
        </Label>
        <Input
          id={fieldName}
          value={value}
          onChange={(e) => handleInputChange(fieldName, e.target.value)}
          className="bg-background-dark"
          placeholder={fieldSchema.description}
        />
        {fieldSchema.description && (
          <p className="text-xs text-gray-400">{fieldSchema.description}</p>
        )}
      </div>
    );
  };

  if (!elementSchema || !resourceSchema) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-background-card border-gray-800 text-foreground max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editingElement ? "Edit" : "Create"} {elementType.name}
          </DialogTitle>
          <DialogDescription>{elementSchema.description}</DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSave();
          }}
          className="space-y-4"
        >
          {/* Render first-level required fields dynamically */}
          {firstLevelRequired.map((fieldName) => {
            const fieldSchema = resourceSchema?.properties?.[fieldName];
            return renderFormField(fieldName, fieldSchema, true);
          })}

          {/* Render config schema fields dynamically */}
          {Object.entries(elementSchema.config_schema.properties)
            .filter(([fieldName]) => !firstLevelRequired.includes(fieldName)) // Exclude first-level fields
            .map(([fieldName, fieldSchema]) => renderFormField(fieldName, fieldSchema, false))}

          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-primary hover:bg-opacity-80"
              disabled={isSaving || !isFormValid()}
            >
              {isSaving ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
