"""
RefRemapper - Recursively remap $ref values in any object graph.

Extracted from ShareCloner._walk_and_replace() for reuse.
Uses same traversal pattern as RefWalker.

SOLID: Single responsibility - reference remapping only.
"""
from typing import Any, Dict
from pydantic import BaseModel
from core.ref.models import Ref


class RefRemapper:
    """
    Recursively remaps $ref values in any object graph.
    
    Handles:
    - Ref objects (Pydantic models with $ref semantics)
    - Dict with "$ref" key
    - Bare string refs (exact match replacement)
    - Nested structures (BaseModel, dict, list, tuple)
    
    Thread-safe: stateless utility with static methods.
    """
    
    @staticmethod
    def remap(node: Any, mapping: Dict[str, str]) -> Any:
        """
        Walk object graph and replace refs according to mapping.
        
        Args:
            node: Any object (Pydantic model, dict, list, Ref, etc.)
            mapping: Dict of old_rid → new_rid
            
        Returns:
            New object with refs replaced (deep copy for mutable objects)
        """
        if isinstance(node, Ref):
            return RefRemapper._remap_ref(node, mapping)
        
        elif isinstance(node, BaseModel):
            new_node = node.model_copy(deep=True)
            for field_name, field_value in new_node.__dict__.items():
                setattr(new_node, field_name, RefRemapper.remap(field_value, mapping))
            return new_node
        
        elif isinstance(node, dict):
            # Handle $ref dict pattern
            if "$ref" in node and node["$ref"] in mapping:
                return {"$ref": mapping[node["$ref"]]}
            return {k: RefRemapper.remap(v, mapping) for k, v in node.items()}
        
        elif isinstance(node, (list, tuple)):
            result = [RefRemapper.remap(v, mapping) for v in node]
            return tuple(result) if isinstance(node, tuple) else result
        
        elif isinstance(node, str):
            # Bare string ref (like exit_condition value)
            return RefRemapper._replace_string_ref(node, mapping)
        
        return node
    
    @staticmethod
    def _remap_ref(ref_obj: Ref, mapping: Dict[str, str]) -> Ref:
        """Remap a single Ref object if it's in the mapping."""
        old_rid = ref_obj.ref
        if old_rid not in mapping:
            return ref_obj
        
        new_rid = mapping[old_rid]
        
        # Create new Ref with updated rid, preserving the ref format and type
        new_ref = ref_obj.__class__(ref_obj.root)
        if ref_obj.is_external_ref():
            new_ref.root = f"$ref:{new_rid}"
        else:
            new_ref.root = new_rid
        
        return new_ref
    
    @staticmethod
    def _replace_string_ref(text: str, mapping: Dict[str, str]) -> str:
        """
        Replace reference patterns in a string.
        
        Handles:
        - Exact match: "old_rid" → "new_rid"
        - $ref: pattern: "$ref:old_rid" → "$ref:new_rid"
        """
        if not mapping:
            return text
        
        result = text
        
        # Check for $ref: pattern replacements
        for old_rid, new_rid in mapping.items():
            result = result.replace(f"$ref:{old_rid}", f"$ref:{new_rid}")
        
        # Handle bare refs if they appear as full strings (exact match)
        if result in mapping:
            result = mapping[result]
        
        return result
