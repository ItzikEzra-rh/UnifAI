export type TemplateFieldType = 
  | 'string' 
  | 'secret' 
  | 'number' 
  | 'boolean' 
  | 'string[]' 
  | 'enum' 
  | 'object';

export interface TemplateFieldValidation {
  regex?: string;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  custom?: string;
}

export interface TemplateFieldUIHints {
  multiselect?: boolean;
  masked?: boolean;
  dropdown?: boolean;
  tagInput?: boolean;
  fileInput?: boolean;
  placeholder?: string;
  rows?: number;
}

export interface TemplateField {
  key: string;
  label: string;
  type: TemplateFieldType;
  required: boolean;
  default?: any;
  description?: string;
  validation?: TemplateFieldValidation;
  ui_hints?: TemplateFieldUIHints;
  options?: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  icon?: string;
  fields: TemplateField[];
  output_capabilities?: string[];
  estimated_setup_time?: string;
  tags?: string[];
}

export interface TemplatesListResponse {
  templates: Template[];
}

export interface TemplateInstantiationRequest {
  inputs: Record<string, any>;
}

export interface TemplateInstantiationResponse {
  workflow_id: string;
  instance_id: string;
  created_elements: string[];
  chat_endpoint?: string;
  status: InstantiationStatus;
}

export type InstantiationStatus = 
  | 'idle'
  | 'validating'
  | 'submitting'
  | 'provisioning'
  | 'finalizing'
  | 'completed'
  | 'failed';

export interface InstantiationStatusResponse {
  instance_id: string;
  status: InstantiationStatus;
  progress?: number;
  message?: string;
  error?: string;
  workflow_id?: string;
  created_elements?: string[];
}

export interface TemplateFormData {
  [key: string]: any;
}

export interface TemplateCategory {
  name: string;
  count: number;
}
