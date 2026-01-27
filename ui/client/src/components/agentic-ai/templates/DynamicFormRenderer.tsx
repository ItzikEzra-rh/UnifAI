import React, { useState, useCallback } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogFooter,
  DialogDescription
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  X, 
  Plus, 
  Key, 
  Eye, 
  EyeOff,
  AlertCircle
} from 'lucide-react';
import { Template, TemplateField, TemplateFormData } from '@/types/templates';

interface DynamicFormRendererProps {
  template: Template;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TemplateFormData) => void;
  isSubmitting?: boolean;
}

interface FieldInputProps {
  field: TemplateField;
  value: any;
  onChange: (value: any) => void;
  error?: string;
}

const StringArrayInput: React.FC<{
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
}> = ({ value = [], onChange, placeholder }) => {
  const [inputValue, setInputValue] = useState('');

  const handleAdd = () => {
    if (inputValue.trim() && !value.includes(inputValue.trim())) {
      onChange([...value, inputValue.trim()]);
      setInputValue('');
    }
  };

  const handleRemove = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || 'Add item...'}
          className="bg-background-dark border-gray-700"
        />
        <Button 
          type="button" 
          onClick={handleAdd}
          variant="outline"
          size="sm"
          className="border-gray-700"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((item, index) => (
            <Badge 
              key={index} 
              variant="secondary"
              className="bg-primary/20 text-primary border-primary/30 flex items-center gap-1"
            >
              {item}
              <button
                type="button"
                onClick={() => handleRemove(index)}
                className="ml-1 hover:text-red-400"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
};

const SecretInput: React.FC<{
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}> = ({ value, onChange, placeholder }) => {
  const [showSecret, setShowSecret] = useState(false);

  return (
    <div className="relative">
      <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-yellow-500" />
      <Input
        type={showSecret ? 'text' : 'password'}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="pl-10 pr-10 bg-background-dark border-gray-700 font-mono"
      />
      <button
        type="button"
        onClick={() => setShowSecret(!showSecret)}
        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
      >
        {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
};

const FieldInput: React.FC<FieldInputProps> = ({ field, value, onChange, error }) => {
  const renderInput = () => {
    switch (field.type) {
      case 'secret':
        return (
          <SecretInput
            value={value}
            onChange={onChange}
            placeholder={field.ui_hints?.placeholder}
          />
        );
      
      case 'string[]':
        return (
          <StringArrayInput
            value={value || []}
            onChange={onChange}
            placeholder={field.ui_hints?.placeholder}
          />
        );
      
      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id={field.key}
              checked={value || false}
              onCheckedChange={onChange}
            />
            <label 
              htmlFor={field.key}
              className="text-sm text-gray-400 cursor-pointer"
            >
              {field.description || 'Enable this option'}
            </label>
          </div>
        );
      
      case 'enum':
        return (
          <Select value={value || field.default} onValueChange={onChange}>
            <SelectTrigger className="bg-background-dark border-gray-700">
              <SelectValue placeholder={`Select ${field.label}`} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      
      case 'number':
        return (
          <Input
            type="number"
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
            placeholder={field.ui_hints?.placeholder}
            className="bg-background-dark border-gray-700"
            min={field.validation?.min}
            max={field.validation?.max}
          />
        );
      
      default:
        if (field.ui_hints?.rows && field.ui_hints.rows > 1) {
          return (
            <Textarea
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              placeholder={field.ui_hints?.placeholder}
              className="bg-background-dark border-gray-700"
              rows={field.ui_hints.rows}
            />
          );
        }
        return (
          <Input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.ui_hints?.placeholder}
            className="bg-background-dark border-gray-700"
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      {field.type !== 'boolean' && (
        <div className="flex items-center justify-between">
          <Label htmlFor={field.key} className="text-sm font-medium">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Badge variant="outline" className="text-xs px-1.5 py-0">
            {field.type}
          </Badge>
        </div>
      )}
      {renderInput()}
      {field.description && field.type !== 'boolean' && (
        <p className="text-xs text-gray-500">{field.description}</p>
      )}
      {error && (
        <p className="text-xs text-red-500 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          {error}
        </p>
      )}
    </div>
  );
};

export const DynamicFormRenderer: React.FC<DynamicFormRendererProps> = ({
  template,
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState<TemplateFormData>(() => {
    const initial: TemplateFormData = {};
    template.fields.forEach(field => {
      if (field.default !== undefined) {
        initial[field.key] = field.default;
      //TODO: Check if this is correct after getting the template from the backend (how pydnatic treat list of strings)
      } else if (field.type === 'string[]') {
        initial[field.key] = [];
      } else if (field.type === 'boolean') {
        initial[field.key] = false;
      }
    });
    return initial;
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleFieldChange = useCallback((key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  }, [errors]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    template.fields.forEach(field => {
      if (field.required) {
        const value = formData[field.key];
        
        if (value === undefined || value === null || value === '') {
          newErrors[field.key] = `${field.label} is required`;
        } else if (field.type === 'string[]' && Array.isArray(value) && value.length === 0) {
          newErrors[field.key] = `At least one ${field.label.toLowerCase()} is required`;
        }
      }

      if (field.validation?.regex && formData[field.key]) {
        const regex = new RegExp(field.validation.regex);
        if (!regex.test(formData[field.key])) {
          newErrors[field.key] = `Invalid format for ${field.label}`;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const requiredFields = template.fields.filter(f => f.required);
  const optionalFields = template.fields.filter(f => !f.required);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-background-card border-gray-800 text-foreground max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-heading">
            Configure {template.name}
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Fill in the required fields to generate your workflow
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="space-y-6 p-1">
            {requiredFields.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-300 border-b border-gray-800 pb-2">
                  Required Fields
                </h3>
                {requiredFields.map(field => (
                  <FieldInput
                    key={field.key}
                    field={field}
                    value={formData[field.key]}
                    onChange={(value) => handleFieldChange(field.key, value)}
                    error={errors[field.key]}
                  />
                ))}
              </div>
            )}

            {optionalFields.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-300 border-b border-gray-800 pb-2">
                  Optional Settings
                </h3>
                {optionalFields.map(field => (
                  <FieldInput
                    key={field.key}
                    field={field}
                    value={formData[field.key]}
                    onChange={(value) => handleFieldChange(field.key, value)}
                    error={errors[field.key]}
                  />
                ))}
              </div>
            )}
          </div>
        </form>

        <DialogFooter className="border-t border-gray-800 pt-4">
          <Button 
            type="button" 
            variant="outline" 
            onClick={onClose}
            className="border-gray-700"
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button 
            type="submit"
            onClick={handleSubmit}
            className="bg-primary hover:bg-primary/90"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Generating...' : 'Generate Workflow'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DynamicFormRenderer;