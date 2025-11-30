import axios from '@/http/axiosAgentConfig';

export interface PublicUsageScopeResponse {
  public_usage_scope: boolean;
  blueprint_id: string;
}

export interface UpdatePublicScopeRequest {
  blueprintId: string;
  public_usage_scope: boolean;
  userId: string;
}

export interface UpdatePublicScopeResponse {
  status: string;
}

/**
 * Get the public usage scope status of a blueprint
 */
export async function getPublicUsageScope(blueprintId: string): Promise<PublicUsageScopeResponse> {
  const { data } = await axios.get<PublicUsageScopeResponse>('/blueprints/public_usage_scope', {
    params: { blueprintId },
  });
  return data;
}

/**
 * Update the public usage scope of a blueprint
 */
export async function updatePublicScope(
  blueprintId: string,
  scope: boolean,
  userId: string
): Promise<UpdatePublicScopeResponse> {
  const { data } = await axios.put<UpdatePublicScopeResponse>('/blueprints/public_usage_scope', {
    blueprintId,
    public_usage_scope: scope,
    userId,
  });
  return data;
}

