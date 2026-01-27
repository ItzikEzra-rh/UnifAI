import axios from '@/http/axiosAgentConfig';
import {
  Template,
  TemplatesListResponse,
  TemplateInstantiationResponse,
  InstantiationStatusResponse
} from '@/types/templates';

// ────────────────────────────────────────────────────────────────────────────────
// Template CRUD Operations
// ────────────────────────────────────────────────────────────────────────────────

/**
 * Fetch all available templates
 */
export async function fetchTemplates(): Promise<TemplatesListResponse> {
  const response = await axios.get<TemplatesListResponse>('/api/templates');
  return response.data;
}

/**
 * Fetch a single template by ID
 */
export async function fetchTemplateById(templateId: string): Promise<Template> {
  const response = await axios.get<Template>(`/api/templates/${templateId}`);
  return response.data;
}

/**
 * Search templates by query
 */
export async function searchTemplates(query: string): Promise<TemplatesListResponse> {
  const response = await axios.get<TemplatesListResponse>('/api/templates/search', {
    params: { query }
  });
  return response.data;
}

// ────────────────────────────────────────────────────────────────────────────────
// Template Instantiation
// ────────────────────────────────────────────────────────────────────────────────

/**
 * Instantiate a template with the provided inputs
 */
export async function instantiateTemplate(
  templateId: string,
  inputs: Record<string, any>
): Promise<TemplateInstantiationResponse> {
  const response = await axios.post<TemplateInstantiationResponse>(
    `/api/templates/${templateId}/instantiate`,
    { inputs }
  );
  return response.data;
}

/**
 * Get the status of a template instantiation
 */
export async function getInstantiationStatus(
  instanceId: string
): Promise<InstantiationStatusResponse> {
  const response = await axios.get<InstantiationStatusResponse>(
    `/api/templates/instances/${instanceId}/status`
  );
  return response.data;
}

/**
 * Cancel an ongoing template instantiation
 */
export async function cancelInstantiation(instanceId: string): Promise<void> {
  await axios.delete(`/api/templates/instances/${instanceId}`);
}

// ────────────────────────────────────────────────────────────────────────────────
// Template Validation
// ────────────────────────────────────────────────────────────────────────────────

/**
 * Validate template inputs before instantiation
 */
export async function validateTemplateInputs(
  templateId: string,
  inputs: Record<string, any>
): Promise<{ valid: boolean; errors: Record<string, string> }> {
  const response = await axios.post<{ valid: boolean; errors: Record<string, string> }>(
    `/api/templates/${templateId}/validate`,
    { inputs }
  );
  return response.data;
}

