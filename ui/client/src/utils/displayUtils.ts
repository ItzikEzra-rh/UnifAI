/**
 * Shared display utilities for formatting config values and objects for UI display.
 * Used by ElementData, ElementGrid, and ResourceDetailsModal.
 */

/**
 * Extract display value from an object.
 * Checks common display field names in priority order.
 */
export const getDisplayValue = (obj: any): string => {
  if (!obj || typeof obj !== 'object') return String(obj || '');
  
  // Common display field names in priority order
  const displayFields = ['name', 'label', 'title', 'display', 'text'];
  for (const field of displayFields) {
    if (obj[field] != null) return String(obj[field]);
  }
  
  // Fallback to id/value
  if (obj.id != null) return String(obj.id);
  if (obj.value != null) return String(obj.value);
  
  return '[Unknown]';
};

/**
 * Extract display value from an item, with optional fallback function for strings.
 * Used for arrays that may contain strings (refs) or objects.
 */
export const getDisplayValueFromItem = (
  item: any, 
  fallbackFn?: (ref: string | any) => string
): string => {
  if (!item) return '';
  
  // If it's a string, use the fallback function if provided
  if (typeof item === 'string') {
    return fallbackFn ? fallbackFn(item) : item;
  }
  
  // If it's an object, extract display value
  if (typeof item === 'object' && item !== null) {
    // Check for common display field patterns
    const displayFields = ['name', 'label', 'title', 'display', 'text'];
    for (const field of displayFields) {
      if (item[field] != null) return String(item[field]);
    }
    // Fallback to id/value
    if (item.id != null) return String(item.id);
    if (item.value != null) return String(item.value);
    
    // If object has $ref, use fallback function
    if (item.$ref && fallbackFn) return fallbackFn(item);
  }
  
  return String(item);
};

/**
 * Recursively simplify config objects for display.
 * Converts object arrays with display patterns (name+id, label+value) to just display names.
 */
export const simplifyConfigForDisplay = (config: any): any => {
  if (!config || typeof config !== 'object') return config;
  
  if (Array.isArray(config)) {
    return config.map(item => {
      if (typeof item === 'object' && item !== null) {
        // Check if this looks like a "display object" (has name/id or name/value pattern)
        const hasDisplayPattern = ('name' in item && ('id' in item || 'value' in item)) ||
                                   ('label' in item && 'value' in item);
        if (hasDisplayPattern) {
          return getDisplayValue(item);
        }
      }
      return simplifyConfigForDisplay(item);
    });
  }
  
  // For objects, recursively simplify each property
  const result: any = {};
  for (const [key, value] of Object.entries(config)) {
    result[key] = simplifyConfigForDisplay(value);
  }
  return result;
};

