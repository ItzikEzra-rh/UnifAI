import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from 'react';
import axios from '@/http/axiosAgentConfig';
import { useAuth } from './AuthContext';
import { catalogService } from '@/api/catalog';
import { ElementValidationResult, CachedValidationResult } from '@/types/validation';

// Validation status type
export type ValidationStatus = 'loading' | 'valid' | 'invalid';

interface ResourceMapping {
  rid: string;
  name: string;
  category: string;
  type: string;
}

interface AgenticAIContextType {
  // Mapping from UUID (rid) to resource name
  uuidToNameMap: Map<string, string>;
  // Mapping from UUID (rid) to full resource info
  uuidToResourceMap: Map<string, ResourceMapping>;
  isLoading: boolean;
  error: string | null;
  getResourceName: (ref: string | any) => string;
  getResource: (ref: string | any) => ResourceMapping | null;
  // Recursively resolve all refs in a config object
  resolveRefsInConfig: (config: any) => any;
  refreshMapping: () => Promise<void>;
  // Incrementally update resource mapping (smart updates)
  addOrUpdateResource: (resource: ResourceMapping) => void;
  removeResource: (rid: string) => void;
  // Validation functions
  getValidationResult: (rid: string) => ElementValidationResult | null;
  getValidationStatus: (rid: string) => ValidationStatus;
  invalidateValidation: (rid: string) => void;
  validateResources: (rids: string[]) => Promise<void>;
}

const AgenticAIContext = createContext<AgenticAIContextType | undefined>(undefined);

interface AgenticAIProviderProps {
  children: ReactNode;
}

export const AgenticAIProvider: React.FC<AgenticAIProviderProps> = ({ children }) => {
  const [uuidToNameMap, setUuidToNameMap] = useState<Map<string, string>>(new Map());
  const [uuidToResourceMap, setUuidToResourceMap] = useState<Map<string, ResourceMapping>>(new Map());
  const [validationCache, setValidationCache] = useState<Map<string, CachedValidationResult>>(new Map());
  const [validationStatusMap, setValidationStatusMap] = useState<Map<string, ValidationStatus>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const USER_ID = user?.username || "default";
  
  // Use ref to access latest cache without causing re-renders in callbacks
  const validationCacheRef = useRef(validationCache);
  validationCacheRef.current = validationCache;

  // ==================== Helper Functions ====================

  // Helper: Remove rid from validation cache
  const removeFromValidationCache = useCallback((rid: string) => {
    setValidationCache((prevCache) => {
      const newCache = new Map(prevCache);
      newCache.delete(rid);
      return newCache;
    });
    setValidationStatusMap((prevStatus) => {
      const newStatus = new Map(prevStatus);
      newStatus.delete(rid);
      return newStatus;
    });
  }, []);

  // Helper: Set validation status for a rid
  const setValidationStatus = useCallback((rid: string, status: ValidationStatus) => {
    setValidationStatusMap((prevStatus) => {
      const newStatus = new Map(prevStatus);
      newStatus.set(rid, status);
      return newStatus;
    });
  }, []);

  // Helper: Cache a validation result and update status
  const cacheValidationResult = useCallback((rid: string, result: ElementValidationResult) => {
    setValidationCache((prevCache) => {
      const newCache = new Map(prevCache);
      newCache.set(rid, {
        result,
        timestamp: Date.now(),
      });
      return newCache;
    });
    setValidationStatusMap((prevStatus) => {
      const newStatus = new Map(prevStatus);
      newStatus.set(rid, result.is_valid ? 'valid' : 'invalid');
      return newStatus;
    });
  }, []);

  // Helper: Create error validation result
  const createErrorResult = useCallback((rid: string, errorMessage: string): ElementValidationResult => {
    return {
      is_valid: false,
      element_rid: rid,
      element_type: 'unknown',
      name: null,
      messages: [{
        severity: 'error',
        code: 'NETWORK_ERROR',
        message: errorMessage,
        field: null,
      }],
      dependency_results: {},
    };
  }, []);

  // Helper: Fetch validation from API and cache result
  const fetchAndCacheValidation = useCallback(async (rid: string): Promise<ElementValidationResult> => {
    try {
      const response = await axios.post<ElementValidationResult>(
        '/resources/resource.validate',
        { resourceId: rid }
      );
      const result = response.data;
      cacheValidationResult(rid, result);
      return result;
    } catch (err: any) {
      console.error(`Error validating resource ${rid}:`, err);
      const errorResult = createErrorResult(
        rid, 
        err.response?.data?.error || 'Failed to validate resource'
      );
      cacheValidationResult(rid, errorResult);
      return errorResult;
    }
  }, [cacheValidationResult, createErrorResult]);

  // ==================== Resource Mapping Functions ====================

  // Fetch all resources for all categories
  const fetchAllResources = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch categories from backend using centralized catalog service
      const categories = await catalogService.fetchCategories();      

      const nameMap = new Map<string, string>();
      const resourceMap = new Map<string, ResourceMapping>();

      // Fetch resources for each category
      await Promise.all(
        categories.map(async (category) => {
          try {
            const response = await axios.get<{
              resources: Array<{
                rid: string;
                name: string;
                category: string;
                type: string;
              }>;
            }>(`/resources/resources.list?userId=${USER_ID}&category=${category}&limit=1000`);

            response.data.resources.forEach((resource) => {
              nameMap.set(resource.rid, resource.name);
              resourceMap.set(resource.rid, {
                rid: resource.rid,
                name: resource.name,
                category: resource.category,
                type: resource.type,
              });
            });
          } catch (err: any) {
            console.warn(`Failed to fetch resources for category ${category}:`, err);
          }
        })
      );

      setUuidToNameMap(nameMap);
      setUuidToResourceMap(resourceMap);
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || "Failed to fetch resource mappings";
      setError(errorMessage);
      console.error("Error fetching resource mappings:", err);
    } finally {
      setIsLoading(false);
    }
  }, [USER_ID]);

  // Get resource name from a ref (falls back to type if no name)
  const getResourceName = useCallback((ref: string | any): string => {
    if (!ref) return '';
    
// Helper to get display name from resource (name or type as fallback)
const getDisplayName = (uuid: string): string => {
  const resource = uuidToResourceMap.get(uuid);
  if (resource) {
    // Return name if available, otherwise return type
    return resource.name || resource.type || uuid;
  }
  return uuidToNameMap.get(uuid) || uuid;
};

if (typeof ref === 'string') {
  if (ref.startsWith('$ref:')) {
    const uuid = ref.substring(5);
    return getDisplayName(uuid);
  }
  // Handle raw UUIDs (check if it exists in the map)
  if (uuidToResourceMap.has(ref) || uuidToNameMap.has(ref)) {
    return getDisplayName(ref);
  }
  return ref;
}

if (typeof ref === 'object' && ref !== null) {
  if (ref.$ref) {
    const uuid = typeof ref.$ref === 'string' && ref.$ref.startsWith('$ref:') 
      ? ref.$ref.substring(5) 
      : ref.$ref;
    return getDisplayName(uuid);
  }
}

return String(ref);
}, [uuidToNameMap, uuidToResourceMap]);

  // Get full resource info from a ref
  const getResource = useCallback((ref: string | any): ResourceMapping | null => {
    if (!ref) return null;
    
    let uuid: string | null = null;

    // Handle string references like "$ref:uuid"
    if (typeof ref === 'string') {
      if (ref.startsWith('$ref:')) {
        uuid = ref.substring(5);
      } else if (uuidToResourceMap.has(ref)) {
        uuid = ref;
      } else {
        return null;
      }
    } else if (typeof ref === 'object' && ref !== null && ref.$ref) {
      uuid = typeof ref.$ref === 'string' && ref.$ref.startsWith('$ref:') 
        ? ref.$ref.substring(5) 
        : ref.$ref;
    }
    
    if (uuid) {
      return uuidToResourceMap.get(uuid) || null;
    }
    
    return null;
  }, [uuidToResourceMap]);

  // Check if a string is a known resource ID (exists in our resource map)
  const isKnownResourceId = useCallback((str: string): boolean => {
    return uuidToResourceMap.has(str);
  }, [uuidToResourceMap]);

  // Recursively resolve all refs in a config object
  const resolveRefsInConfig = useCallback((config: any): any => {
    // Handle null/undefined
    if (config === null || config === undefined) {
      return config;
    }

    // Handle arrays - map over items and resolve refs
    if (Array.isArray(config)) {
      return config.map((item) => {
        // If item is a string ref, resolve it directly
        if (typeof item === 'string' && item.startsWith('$ref:')) {
          return getResourceName(item);
        }
        // If item is an object ref like { "$ref": "uuid" }, resolve it
        if (typeof item === 'object' && item !== null && item.$ref) {
          return getResourceName(item);
        }
        // If item is a known resource ID (raw UUID), resolve it
        if (typeof item === 'string' && isKnownResourceId(item)) {
          return getResourceName(item);
        }
        // Otherwise, recursively resolve
        return resolveRefsInConfig(item);
      });
    }

    // Handle primitives (strings, numbers, booleans)
    if (typeof config !== 'object') {
      // If it's a string ref, resolve it
      if (typeof config === 'string' && config.startsWith('$ref:')) {
        return getResourceName(config);
      }
      // If it's a known resource ID (raw UUID), resolve it
      if (typeof config === 'string' && isKnownResourceId(config)) {
        return getResourceName(config);
      }
      return config;
    }

    // Handle object refs like { "$ref": "uuid" } - resolve to name directly
    if (config.$ref) {
      return getResourceName(config);
    }

    // Handle objects - recursively resolve all properties
    const resolved: any = {};
    for (const [key, value] of Object.entries(config)) {
      if (typeof value === 'string' && value.startsWith('$ref:')) {
        // Resolve the ref to a name
        resolved[key] = getResourceName(value);
      } else if (typeof value === 'string' && isKnownResourceId(value)) {
        // Resolve known resource IDs (raw UUIDs)
        resolved[key] = getResourceName(value);
      } else if (typeof value === 'object' && value !== null) {
        // Check if this object is itself a ref
        if ('$ref' in value) {
          resolved[key] = getResourceName(value);
        } else {
          // Recursively resolve nested objects and arrays
          resolved[key] = resolveRefsInConfig(value);
        }
      } else {
        resolved[key] = value;
      }
    }
    return resolved;
  }, [getResourceName, isKnownResourceId]);

  // Refresh the mapping
  const refreshMapping = useCallback(async () => {
    await fetchAllResources();
  }, [fetchAllResources]);

  // Incrementally add or update a single resource in the mapping
  const addOrUpdateResource = useCallback((resource: ResourceMapping) => {
    setUuidToNameMap((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.set(resource.rid, resource.name);
      return newMap;
    });
    setUuidToResourceMap((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.set(resource.rid, resource);
      return newMap;
    });
  }, []);

  // Incrementally remove a resource from the mapping
  const removeResource = useCallback((rid: string) => {
    setUuidToNameMap((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.delete(rid);
      return newMap;
    });
    setUuidToResourceMap((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.delete(rid);
      return newMap;
    });
    removeFromValidationCache(rid);
  }, [removeFromValidationCache]);

  // ==================== Validation Functions ====================

  // Get cached validation result for a resource
  const getValidationResult = useCallback((rid: string): ElementValidationResult | null => {
    const cached = validationCache.get(rid);
    return cached ? cached.result : null;
  }, [validationCache]);

  // Get validation status for a resource
  const getValidationStatus = useCallback((rid: string): ValidationStatus => {
    return validationStatusMap.get(rid) || 'loading';
  }, [validationStatusMap]);

  // Invalidate validation cache for a specific resource
  const invalidateValidation = useCallback((rid: string) => {
    removeFromValidationCache(rid);
  }, [removeFromValidationCache]);

  // Validate multiple resources in parallel (only those not already cached)
  const validateResources = useCallback(async (rids: string[]): Promise<void> => {
    // Filter out resources that are already cached
    const uncachedRids = rids.filter(rid => !validationCacheRef.current.has(rid));
    
    if (uncachedRids.length === 0) {
      return;
    }

    // Set all uncached resources to loading state
    uncachedRids.forEach(rid => setValidationStatus(rid, 'loading'));

    // Validate all uncached resources in parallel
    await Promise.all(
      uncachedRids.map(rid => fetchAndCacheValidation(rid))
    );
  }, [setValidationStatus, fetchAndCacheValidation]);

  // ==================== Effects ====================

  // Fetch resources when user changes or component mounts
  useEffect(() => {
    if (USER_ID) {
      fetchAllResources();
    }
  }, [USER_ID, fetchAllResources]);

  // ==================== Context Value ====================

  const value: AgenticAIContextType = {
    uuidToNameMap,
    uuidToResourceMap,
    isLoading,
    error,
    getResourceName,
    getResource,
    resolveRefsInConfig,
    refreshMapping,
    addOrUpdateResource,
    removeResource,
    getValidationResult,
    getValidationStatus,
    invalidateValidation,
    validateResources,
  };

  return (
    <AgenticAIContext.Provider value={value}>
      {children}
    </AgenticAIContext.Provider>
  );
};

export const useAgenticAI = (): AgenticAIContextType => {
  const context = useContext(AgenticAIContext);
  if (context === undefined) {
    throw new Error('useAgenticAI must be used within an AgenticAIProvider');
  }
  return context;
};

