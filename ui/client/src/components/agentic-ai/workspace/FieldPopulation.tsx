import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue,
} from "@/components/ui/select";
import {
  Popover, 
  PopoverContent, 
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command, 
  CommandEmpty, 
  CommandGroup, 
  CommandInput, 
  CommandItem, 
  CommandList,
} from "@/components/ui/command";
import { Loader2, RefreshCw, ChevronDown, Check } from 'lucide-react';
import axios from "../../../http/axiosAgentConfig";
import { OptionItem, normalizeOptions } from './fieldPopulationUtils';

interface PaginationState {
  nextCursor: string | null;
  hasMore: boolean;
  total: number | null;
}

interface FieldPopulationProps {
  fieldName: string;
  populateHint: any;
  elementActions: any[];
  selectedElementType: any;
  formData: any;
  onPopulateResult: (fieldName: string, results: any[], multiSelect: boolean) => void;
  autoTrigger?: boolean;
  hideUI?: boolean;
}

const SEARCH_DEBOUNCE_DELAY = 300; // ms

export const FieldPopulation: React.FC<FieldPopulationProps> = ({
  fieldName,
  populateHint,
  elementActions,
  selectedElementType,
  formData,
  onPopulateResult,
  autoTrigger = false,
  hideUI = false
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [populatedOptions, setPopulatedOptions] = useState<OptionItem[]>([]);
  const [selectedValues, setSelectedValues] = useState<string[]>([]); // Track by value (ID)
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [shouldKeepOpen, setShouldKeepOpen] = useState(false);
  const [hasAutoTriggered, setHasAutoTriggered] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  
  // Search state
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Pagination state
  const [pagination, setPagination] = useState<PaginationState>({
    nextCursor: null,
    hasMore: false,
    total: null
  });

  // Extract hint flags with defaults for backwards compatibility
  const supportsPagination = populateHint.pagination === true;
  const supportsSearch = populateHint.search === true;
  const displayField = populateHint.display_field || populateHint.label_field;
  const valueField = populateHint.value_field;

  // Find the populate action from elementActions
  const populateAction = elementActions.find(
    action => action.uid === populateHint.action_uid
  );

  if (!populateAction) {
    return null;
  }

  // Helper to extract value (ID) from an item - handles both string and object formats
  const extractValue = (item: any): string => {
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item !== null) {
      if (valueField && item[valueField] != null) return String(item[valueField]);
      return String(item.id ?? item.value ?? item.name ?? item);
    }
    return String(item);
  };

  // Helper to get display label for a value
  const getDisplayLabel = (value: string): string => {
    // First check populated options
    const option = populatedOptions.find(opt => opt.value === value);
    if (option) return option.label;
    
    // Fallback to formData for edit mode before population
    const currentValue = formData[fieldName];
    if (Array.isArray(currentValue)) {
      const item = currentValue.find((i: any) => extractValue(i) === value);
      if (item && typeof item === 'object') {
        return String(item[displayField] ?? item.name ?? item.label ?? value);
      }
    }
    return value;
  };

  // Helper to get original objects for selected value IDs - used to send full objects to backend
  const getSelectedObjects = (values: string[]): any[] => {
    return values.map(value => {
      const option = populatedOptions.find(opt => opt.value === value);
      if (option) return option.originalObject;
      
      // Fallback to formData for items not in populated options
      const currentValue = formData[fieldName];
      if (Array.isArray(currentValue)) {
        const item = currentValue.find((i: any) => extractValue(i) === value);
        if (item) return item;
      }
      // Fallback: create minimal object
      return { id: value, name: value };
    });
  };

  // Initialize selectedValues from formData when editing existing element
  useEffect(() => {
    const currentValue = formData[fieldName];
    if (Array.isArray(currentValue) && currentValue.length > 0) {
      const values = currentValue.map(extractValue);
      if (JSON.stringify(values) !== JSON.stringify(selectedValues)) {
        setSelectedValues(values);
      }
    }
  }, [formData[fieldName]]);

  // Effect to force dropdown to stay open for multi-select
  useEffect(() => {
    if (shouldKeepOpen && populateHint.multi_select && !isDropdownOpen) {
      const timer = setTimeout(() => {
        setIsDropdownOpen(true);
        setShouldKeepOpen(false);
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [shouldKeepOpen, populateHint.multi_select, isDropdownOpen]);

  // Effect to reset auto-trigger state when dependency values change
  useEffect(() => {    
    setHasAutoTriggered(false);
  }, [Object.keys(populateHint.dependencies || {}).map((depKey) => formData[depKey]).join(',')]);

  // Effect to auto-trigger population when dependencies are satisfied
  useEffect(() => {
    if (autoTrigger && !hasAutoTriggered && !isLoading) {
      // Check if all required dependencies have values
      const dependencies = populateHint.dependencies || {};
      const allDependenciesSatisfied = Object.keys(dependencies).every(
        (depKey) => formData[depKey] !== undefined && formData[depKey] !== null && formData[depKey] !== ''
      );

      if (allDependenciesSatisfied) {
        setHasAutoTriggered(true);
        performPopulation();
      }
    }
  }, [autoTrigger, hasAutoTriggered, isLoading, formData]);

  // Debounced search effect
  useEffect(() => {
    if (!supportsSearch) return;
    
    // Clear existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchTerm.trim()) {
      setIsSearching(true);

      searchTimeoutRef.current = setTimeout(() => {
        setDebouncedSearchTerm(searchTerm.trim());
        setIsSearching(false);
      }, SEARCH_DEBOUNCE_DELAY);
    } else {
      setDebouncedSearchTerm('');
      setIsSearching(false);
    }

    return () => {
      if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    };
  }, [searchTerm, supportsSearch]);

  // Effect to re-fetch when debounced search term changes
  useEffect(() => {
    if (supportsSearch && hasLoadedOnce) {
      // Reset and fetch with new search term
      performPopulation(null, debouncedSearchTerm);
    }
  }, [debouncedSearchTerm]);

  const performPopulation = async (cursor: string | null = null, searchRegex: string | null = null) => {
    const isLoadMore = cursor !== null;
    
    if (isLoadMore) {
      setIsLoadingMore(true);
    } else {
      setIsLoading(true);
    }

    try {
      // Prepare input data based on populate action's input schema
      const inputData: any = {};
      
      // Map dependencies from populate hint or use field name directly
      if (populateHint.dependencies && Object.keys(populateHint.dependencies).length > 0) {
        Object.entries(populateHint.dependencies).forEach(([configField, actionField]) => {
          const configValue = formData[configField];
          if (configValue !== undefined && configValue !== null && configValue !== '') {
            inputData[actionField as string] = configValue;
          }
        });
      } else {
        // If no dependencies specified, use form data directly
        Object.keys(populateAction.input_schema?.properties || {}).forEach(inputField => {
          if (formData[inputField] !== undefined && formData[inputField] !== null && formData[inputField] !== '') {
            inputData[inputField] = formData[inputField];
          }
        });
      }

      // Add pagination params if supported
      if (supportsPagination) {
        inputData.limit = 30;
        if (cursor) {
          inputData.cursor = cursor;
        }
      }

      // Add search param if supported and provided
      if (supportsSearch && searchRegex) {
        inputData.search_regex = searchRegex;
      }

      const response = await axios.post('/actions/action.execute', {
        uid: populateAction.uid,
        inputData
      });

      // Extract results based on field_mapping
      const fieldMapping = populateHint.field_mapping || 'results';
      const rawResults = response.data[fieldMapping] || [];

      // Handle automatic selection (non-array result)
      if (populateHint.selection_type === 'automatic' && !Array.isArray(rawResults)) {
        onPopulateResult(fieldName, rawResults, false);
        return;
      }
      
      const normalizedResults = normalizeOptions(rawResults, displayField, valueField);
      
      if (populateHint.selection_type === 'manual' || populateHint.multi_select) {
        if (isLoadMore) {
          setPopulatedOptions(prev => [...prev, ...normalizedResults]);
        } else if (!searchRegex) {
          // Initial population: set options and auto-select all
          setPopulatedOptions(normalizedResults);
          if (normalizedResults.length > 0) {
            setHasLoadedOnce(true);
            setSelectedValues(normalizedResults.map(opt => opt.value));
            setIsAllSelected(true);
            onPopulateResult(fieldName, normalizedResults.map(opt => opt.originalObject), populateHint.multi_select || false);
          }
        } else {
          // Replace options (search result)
          setPopulatedOptions(normalizedResults);
        }
      }

      // Update pagination state if supported
      if (supportsPagination) {
        setPagination({
          nextCursor: response.data.nextCursor || response.data.next_cursor || null,
          hasMore: response.data.hasMore ?? response.data.has_more ?? false,
          total: response.data.total ?? null
        });
      }

    } catch (error: any) {
      console.error('Population error:', error);
      if (!isLoadMore && !searchRegex) {
        setPopulatedOptions([]);
        setPagination({ nextCursor: null, hasMore: false, total: null });
      }
    } finally {
      if (isLoadMore) {
        setIsLoadingMore(false);
      } else {
        setIsLoading(false);
      }
    }
  };

  const handleLoadMore = () => {
    if (pagination.nextCursor && !isLoadingMore) {
      performPopulation(pagination.nextCursor, debouncedSearchTerm || null);
    }
  };

  const handleSelectChange = (value: string) => {
    if (!value || value === "__no_options_disabled__" || value === "__load_more__") return;

    let newSelectedValues: string[];
    
    if (isAllSelected) {
      // First selection after "all selected" - start fresh with just this item
      newSelectedValues = [value];
      setIsAllSelected(false);
    } else if (populateHint.multi_select) {
      // Multi-select: toggle selection
      newSelectedValues = selectedValues.includes(value)
        ? selectedValues.filter(v => v !== value)
        : [...selectedValues, value];
    } else {
      // Single select: replace current selection
      newSelectedValues = [value];
    }

    setSelectedValues(newSelectedValues);
    // Update parent component with selected objects (full objects for backend storage)
    onPopulateResult(fieldName, getSelectedObjects(newSelectedValues), populateHint.multi_select || false);
  };

  // Handle item selection for multi-select to keep dropdown open
  const handleItemSelect = (value: string) => {
    handleSelectChange(value);
    // For multi-select, signal that we want to keep the dropdown open
    if (populateHint.multi_select) {
      setShouldKeepOpen(true);
    }
  };

  // Remove a selected value (from badge click)
  const removeSelectedValue = (valueToRemove: string) => {
    if (isAllSelected) setIsAllSelected(false);
    const newSelectedValues = selectedValues.filter(v => v !== valueToRemove);
    setSelectedValues(newSelectedValues);
    onPopulateResult(fieldName, getSelectedObjects(newSelectedValues), populateHint.multi_select || false);
  };

  const availableOptions = isAllSelected || !populateHint.multi_select
    ? populatedOptions
    : populatedOptions.filter(opt => !selectedValues.includes(opt.value));
    
  const remainingCount = pagination.total ? pagination.total - populatedOptions.length : null;

  // Hide UI when auto-triggering (keep logic running in background)
  if (hideUI) {
    return null;
  }
  const getDropdownLabel = () => {
    if (isAllSelected) return `All ${populatedOptions.length} ${populateHint.field_mapping || 'options'} selected (click to choose specific)`;
    if (populateHint.multi_select) return `Add ${populateHint.field_mapping || 'option'}...`;
    if (selectedValues.length > 0) return getDisplayLabel(selectedValues[0]);
    return `Select ${populateHint.field_mapping || 'option'}...`;
  };

  const renderSearchableDropdown = () => (
    <Popover open={isDropdownOpen} onOpenChange={setIsDropdownOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={isDropdownOpen} className="w-full justify-between bg-background-dark">
          {getDropdownLabel()}
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-[--radix-popover-trigger-width] p-0" 
        align="start"
        onOpenAutoFocus={(e) => e.preventDefault()}
        onInteractOutside={(e) => {
          // Prevent closing when interacting with elements inside the popover
          const target = e.target as HTMLElement;
          if (target.closest('[data-radix-popper-content-wrapper]')) {
            e.preventDefault();
          }
        }}
      >
        <Command shouldFilter={false} loop>
          <div className="[&_input]:!text-white">
            <CommandInput 
            placeholder={`Search ${populateHint.field_mapping || 'options'}...`} 
            value={searchTerm} 
            onValueChange={setSearchTerm} 
            />
          </div>
          {isSearching && (
            <div className="flex items-center justify-center py-2">
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
              <span className="ml-2 text-sm text-gray-400">Searching...</span>
            </div>
          )}
          <CommandList>
            <CommandEmpty>
              {isLoading ? 'Loading...' : isSearching ? 'Searching...' : searchTerm ? 'No matching results found.' : 'No options found.'}
            </CommandEmpty>
            <CommandGroup>
              {availableOptions.map((option: OptionItem) => (
                <CommandItem
                  key={option.value}
                  value={option.value}
                  onSelect={() => {
                    handleItemSelect(option.value);
                    if (!populateHint.multi_select) {
                      setIsDropdownOpen(false);
                    }
                  }}
                >
                  <Check 
                  className={`mr-2 h-4 w-4 ${
                    !isAllSelected && selectedValues.includes(option.value) ? "opacity-100" : "opacity-0"
                    }`} 
                    />
                  {option.label}
                </CommandItem>
              ))}

              {/* Load More option for pagination */}
              {supportsPagination && pagination.hasMore && (
                <CommandItem 
                value="__load_more__" 
                onSelect={handleLoadMore} 
                className="text-blue-400 font-medium justify-center cursor-pointer"
                >
                  {isLoadingMore ? <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading more...
                  </>
                   : 
                   <>
                   <ChevronDown className="mr-2 h-4 w-4" />
                   Load more{remainingCount !== null ? ` (${remainingCount} remaining)` : '...'}
                   </>
                  }
                </CommandItem>
              )}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );

  // Render standard dropdown (for backwards compatibility - no search)
  const renderStandardDropdown = () => (
    <Select
      value=""
      open={isDropdownOpen}
      onOpenChange={setIsDropdownOpen}
      onValueChange={(value) => {
        if (value === "__load_more__") { 
          handleLoadMore(); 
          return; 
        }
        if (populateHint.multi_select) handleItemSelect(value);
        else { handleSelectChange(value); setIsDropdownOpen(false); }
      }}
    >
      <SelectTrigger className="bg-background-dark">
        <SelectValue placeholder={getDropdownLabel()} />
      </SelectTrigger>
      <SelectContent
        onCloseAutoFocus={(e) => { 
          if (populateHint.multi_select) {
            e.preventDefault(); 
            }
          }}
        onPointerDownOutside={() => setIsDropdownOpen(false)}
        onEscapeKeyDown={() => setIsDropdownOpen(false)}
      >
        {availableOptions.map((option, index) => (
          <SelectItem 
          key={`${option.value}-${index}`} 
          value={option.value}
          >
            {option.label}
            </SelectItem>
        ))}

        {supportsPagination && pagination.hasMore && (
          <SelectItem 
          value="__load_more__" 
          className="text-blue-400 font-medium cursor-pointer"
          >
            {isLoadingMore 
              ? <span className="flex items-center gap-2"><Loader2 className="h-3 w-3 animate-spin" />Loading...</span>
              : <span className="flex items-center gap-2"><ChevronDown className="h-3 w-3" />Load more{remainingCount !== null ? ` (${remainingCount} remaining)` : '...'}</span>}
          </SelectItem>
        )}
        {availableOptions.length === 0 && (
          <SelectItem value="__no_options_disabled__" disabled>
            {populatedOptions.length > 0 && populateHint.multi_select ? 'All options selected' : 'No options available'}
          </SelectItem>
        )}
      </SelectContent>
    </Select>
  );

  return (
    <div className="space-y-3">
      {/* Populate Button */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => performPopulation()}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {populateAction.uid}
        </Button>
        <Badge variant="outline" className="text-xs">
          populate
        </Badge>
        {populateHint.multi_select && (
          <Badge variant="outline" className="text-xs">
            multi-select
          </Badge>
        )}
        {supportsPagination && (
          <Badge variant="outline" className="text-xs text-blue-400 border-blue-400/50">
            paginated
          </Badge>
        )}
        {supportsSearch && (
          <Badge variant="outline" className="text-xs text-green-400 border-green-400/50">
            searchable
          </Badge>
        )}
      </div>

      {/* Selection Dropdown */}
      {(hasLoadedOnce || populatedOptions.length > 0) && (
        <div className="space-y-2">
          {supportsSearch ? renderSearchableDropdown() : renderStandardDropdown()}

          {/* Selected items as removable badges - show names */}
          {!isAllSelected && selectedValues.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedValues.map((value: string, index: number) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="flex items-center gap-1 bg-gray-700 text-white border-gray-600 hover:bg-gray-600"
                >
                  {getDisplayLabel(value)}
                  <button
                    type="button"
                    onClick={() => removeSelectedValue(value)}
                    className="ml-1 text-xs text-gray-300 hover:text-red-400 transition-colors"
                  >
                    ×
                  </button>
                </Badge>
              ))}
            </div>
          )}

          {supportsPagination && pagination.total !== null && (
            <p className="text-xs text-gray-400">
              Showing {populatedOptions.length} of {pagination.total} {populateHint.field_mapping || 'options'}
            </p>
          )}
        </div>
      )}

      {/* Show message when no options populated yet */}
      {!hasLoadedOnce && populatedOptions.length === 0 && !isLoading && (
        <p className="text-xs text-gray-400">
          Click the button above to populate {populateHint.field_mapping || 'options'}
        </p>
      )}
    </div>
  );
};
