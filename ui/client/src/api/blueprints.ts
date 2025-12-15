import axios from '@/http/axiosAgentConfig';

export interface BlueprintInfoResponse {
  blueprint_id: string;
  user_id: string;
  spec_dict: {
    name: string;
    [key: string]: any;
  };
  metadata: {
    usageScope?: "public" | "private";
    [key: string]: any;
  };
}

export interface SetMetadataResponse {
  status: string;
}

/**
 * Get blueprint information including metadata
 */
export async function getBlueprintInfo(blueprintId: string): Promise<BlueprintInfoResponse> {
  const { data } = await axios.get<BlueprintInfoResponse>('/blueprints/blueprint.info.get', {
    params: { blueprintId },
  });
  return data;
}

/**
 * Check if a blueprint has public sharing enabled
 */
export async function getPublicUsageScope(blueprintId: string): Promise<{ public_usage_scope: boolean; blueprint_id: string }> {
  const info = await getBlueprintInfo(blueprintId);
  return {
    public_usage_scope: info.metadata?.usageScope === "public",
    blueprint_id: info.blueprint_id,
  };
}

/**
 * Set metadata for a blueprint
 */
export async function setBlueprintMetadata(
  blueprintId: string,
  metadata: { usageScope?: "public" | "private"; [key: string]: any },
  userId: string
): Promise<SetMetadataResponse> {
  const { data } = await axios.put<SetMetadataResponse>('/blueprints/blueprint.metadata.set', {
    blueprintId,
    metadata,
    userId,
  });
  return data;
}

