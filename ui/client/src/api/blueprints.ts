import axios from '@/http/axiosAgentConfig';

export interface BlueprintInfoResponse {
  blueprint_id: string;
  blueprint_name: string;
  owner_user_id: string;
  metadata: {
    usageScope?: "public" | "private";
    [key: string]: any;
  };
}

export interface SetMetadataRequest {
  blueprintId: string;
  metadata: {
    usageScope?: "public" | "private";
    [key: string]: any;
  };
  userId: string;
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
 * Get the public usage scope status of a blueprint (from metadata)
 * @deprecated Use getBlueprintInfo instead and read metadata.usageScope
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

/**
 * Update the public usage scope of a blueprint
 * @deprecated Use setBlueprintMetadata instead
 */
export async function updatePublicScope(
  blueprintId: string,
  scope: boolean,
  userId: string
): Promise<SetMetadataResponse> {
  return setBlueprintMetadata(
    blueprintId,
    { usageScope: scope ? "public" : "private" },
    userId
  );
}

