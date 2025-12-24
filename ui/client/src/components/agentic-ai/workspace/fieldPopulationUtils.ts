/**
 * Utility functions for FieldPopulation component.
 * Handles normalizing API results into a consistent option format.
 */

export interface OptionItem {
  label: string;         // Display name (e.g., "My Document")
  value: string;         // Internal ID for deduplication (e.g., "abc123")
  originalObject: any;   // Full object from API (preserved but not used for storage)
}

/**
 * Resolve a dot-notation path on an object.
 * Example: resolvePath({a: {b: "hello"}}, "a.b") => "hello"
 */
const resolvePath = (obj: any, path: string | undefined): any => {
  if (!obj || !path) return undefined;
  const segments = path.split('.');
  let current = obj;
  for (const segment of segments) {
    if (current == null || typeof current !== 'object') return undefined;
    current = current[segment];
  }
  return current;
};

/**
 * Extract the display name from an object.
 * Uses displayField path if provided, otherwise falls back to common display fields.
 */
const extractDisplayName = (obj: any, displayField?: string): string => {
  if (!obj) return '';
  if (typeof obj === 'string') return obj;
  if (typeof obj !== 'object') return String(obj);

  // Try displayField path first
  if (displayField) {
    const val = resolvePath(obj, displayField);
    if (val != null) return String(val);
  }

  // Common display field fallbacks
  const fallbacks = ['name', 'label', 'title', 'display', 'text'];
  for (const key of fallbacks) {
    if (obj[key] != null) return String(obj[key]);
  }

  // ID as last resort
  if (obj.id != null) return String(obj.id);
  if (obj.value != null) return String(obj.value);

  return '[Unknown]';
};

/**
 * Extract the unique ID/value from an object.
 * Uses valueField path if provided, otherwise falls back to common ID fields.
 */
const extractId = (obj: any, valueField?: string): string => {
  if (!obj) return '';
  if (typeof obj === 'string') return obj;
  if (typeof obj !== 'object') return String(obj);

  // Try valueField path first
  if (valueField) {
    const val = resolvePath(obj, valueField);
    if (val != null) return String(val);
  }

  // Common ID field fallbacks
  const fallbacks = ['id', 'value', '_id', 'key'];
  for (const key of fallbacks) {
    if (obj[key] != null) return String(obj[key]);
  }

  // Name as last resort (for tags where name IS the value)
  if (obj.name != null) return String(obj.name);

  return '[Unknown]';
};

/**
 * Normalize raw API results into OptionItem format.
 * Handles both string arrays and object arrays.
 */
export const normalizeOptions = (
  items: any[],
  displayField?: string,
  valueField?: string
): OptionItem[] => {
  if (!items || !Array.isArray(items)) return [];

  return items.map(item => {
    if (typeof item === 'string') {
      return { label: item, value: item, originalObject: item };
    }

    if (typeof item === 'object' && item !== null) {
      return {
        label: extractDisplayName(item, displayField),
        value: extractId(item, valueField),
        originalObject: item
      };
    }

    return { label: String(item), value: String(item), originalObject: item };
  });
};
