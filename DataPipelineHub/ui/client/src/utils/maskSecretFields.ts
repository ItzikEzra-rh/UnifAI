/**
 * Utility functions for masking secret/sensitive field values
 */

const SECRET_FIELD_NAMES = ['api_key', 'password', 'secret', 'token', 'access_token', 'api_token'];

/**
 * Checks if a field name indicates it should be treated as a secret field
 * @param fieldName The name of the field
 * @param fieldSchema Optional schema for the field (if available)
 * @returns true if the field should be masked
 */
export const isSecretField = (fieldName: string, fieldSchema?: any): boolean => {
  // Check if schema explicitly marks it as secret
  if (fieldSchema?.secret === true) {
    return true;
  }
  
  // Check if field name matches secret patterns
  const lowerFieldName = fieldName.toLowerCase();
  return SECRET_FIELD_NAMES.some(secretField => 
    lowerFieldName.includes(secretField.toLowerCase())
  );
};

/**
 * Masks a value if it's a secret field
 * @param value The value to potentially mask
 * @param fieldName The name of the field
 * @param fieldSchema Optional schema for the field
 * @returns The masked value (dots) or original value
 */
export const maskSecretValue = (value: any, fieldName: string, fieldSchema?: any): string => {
  if (!isSecretField(fieldName, fieldSchema)) {
    return typeof value === 'string' ? value : String(value);
  }
  
  // Mask the value with dots
  if (typeof value === 'string' && value.length > 0) {
    // If it's a $ref value, keep the prefix visible
    if (value.startsWith('$ref:')) {
      return '$ref:••••••••';
    }
    // Otherwise, mask with dots based on approximate length
    const length = value.length;
    if (length <= 8) {
      return '••••';
    } else if (length <= 16) {
      return '••••••••';
    } else {
      return '••••••••••••';
    }
  }
  
  // For non-string values, return a generic mask
  return '••••••••';
};

/**
 * Masks secret values in a config object
 * @param config The config object to mask
 * @param schema Optional schema object with properties
 * @returns A new object with secret values masked
 */
export const maskSecretFieldsInConfig = (config: any, schema?: { properties?: { [key: string]: any } }): any => {
  if (!config || typeof config !== 'object') {
    return config;
  }
  
  const masked: any = {};
  
  for (const [key, value] of Object.entries(config)) {
    const fieldSchema = schema?.properties?.[key];
    
    if (isSecretField(key, fieldSchema)) {
      masked[key] = maskSecretValue(value, key, fieldSchema);
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // Recursively mask nested objects
      masked[key] = maskSecretFieldsInConfig(value, schema);
    } else {
      masked[key] = value;
    }
  }
  
  return masked;
};

/**
 * Formats a value for display, masking secrets
 * @param value The value to format
 * @param fieldName The field name
 * @param fieldSchema Optional field schema
 * @param maxLength Optional max length for non-secret strings
 * @returns Formatted string
 */
export const formatConfigValue = (
  value: any,
  fieldName: string,
  fieldSchema?: any,
  maxLength: number = 15
): string => {
  if (isSecretField(fieldName, fieldSchema)) {
    return maskSecretValue(value, fieldName, fieldSchema);
  }
  
  if (typeof value === 'string') {
    if (value.length > maxLength) {
      return value.slice(0, maxLength) + '...';
    }
    return value;
  }
  
  if (typeof value === 'object' && value !== null) {
    return '[Object]';
  }
  
  return String(value);
};

