/**
 * Document validation utilities for upload operations
 * Centralizes all document-related validation logic
 */

import type { Document } from "@/types";
import { PIPELINE_STATUS } from "@/constants/pipelineStatus";

/**
 * Normalizes a file name the same way the backend does:
 * - Replaces spaces with underscores
 */
export const normalizeFileName = (fileName: string): string => {
  return fileName.replace(/ /g, '_');
};

export interface DuplicateCheckResult {
  isDuplicate: boolean;
  normalizedName: string;
  existingDoc?: Document;
}

/**
 * Checks if a file with the same normalized name already exists for the current user.
 * Allows re-upload of FAILED documents (to enable retry).
 */
export const checkDuplicateFileName = (
  fileName: string,
  existingDocuments: Document[],
  currentUsername: string
): DuplicateCheckResult => {
  const normalizedName = normalizeFileName(fileName);
  
  const existingDoc = existingDocuments.find(doc => {
    const normalizedExistingName = normalizeFileName(doc.source_name);
    const isSameName = normalizedExistingName === normalizedName;
    const isSameUser = doc.upload_by === currentUsername;
    // Allow re-upload if the existing document has FAILED status
    const isNotFailed = doc.status !== PIPELINE_STATUS.FAILED;
    
    return isSameName && isSameUser && isNotFailed;
  });

  return {
    isDuplicate: !!existingDoc,
    normalizedName,
    existingDoc
  };
};

export interface SelectedFileItem {
  file: File;
  id: string;
}

/**
 * Filters out duplicate files from a list of valid files.
 * Returns non-duplicate files and a list of duplicate files with their info.
 */
export const filterDuplicateFiles = (
  validFiles: File[],
  existingDocuments: Document[],
  selectedFiles: SelectedFileItem[],
  currentUsername: string
): {
  nonDuplicateFiles: File[];
  duplicateFiles: { fileName: string; normalizedName: string }[];
} => {
  const duplicateFiles: { fileName: string; normalizedName: string }[] = [];
  const nonDuplicateFiles: File[] = [];

  for (const file of validFiles) {
    const { isDuplicate, normalizedName } = checkDuplicateFileName(
      file.name,
      existingDocuments,
      currentUsername
    );
    
    // Also check if the file is already in the selected files list
    const alreadySelected = selectedFiles.some(
      sf => normalizeFileName(sf.file.name) === normalizedName
    );

    if (isDuplicate || alreadySelected) {
      duplicateFiles.push({ fileName: file.name, normalizedName });
    } else {
      nonDuplicateFiles.push(file);
    }
  }

  return { nonDuplicateFiles, duplicateFiles };
};

/**
 * Formats duplicate file names for display in error messages.
 */
export const formatDuplicateNames = (
  duplicates: { fileName: string; normalizedName: string }[]
): string => {
  return duplicates.map(d => 
    d.fileName !== d.normalizedName 
      ? `"${d.fileName}" (saved as "${d.normalizedName}")`
      : `"${d.fileName}"`
  ).join(', ');
};

