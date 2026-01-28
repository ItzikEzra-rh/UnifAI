"""
ResourceMaterializer - Saves blueprint resources and creates $ref-based blueprint.

Converts a BlueprintDraft with inline configs into:
1. Saved resources in user's account
2. BlueprintDraft with $ref references

SOLID:
- Single Responsibility: Orchestrates resource saving and blueprint building
- Open/Closed: Uses ResourceCategory enum, works with any category
- Dependency Inversion: Depends on ResourcesService abstraction

Key insight: BlueprintDraft uses typed refs (LLMRef, ToolRef, etc.) which
RefWalker understands. No need for custom ref detection.

Two-Phase Materialization:
1. Pre-validation: Validate configs against Pydantic schemas
2. Save with rollback: Save resources, rollback on failure
"""
from typing import Dict, List, Set, Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, Extra

from blueprints.models.blueprint import BlueprintDraft, Resource
from resources.service import ResourcesService
from core.ref import RefWalker, RefRemapper
from core.enums import ResourceCategory


class MaterializationError(Exception):
    """Raised when materialization fails."""
    
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []


# System node types that should never be saved as resources
# These are blueprint-internal nodes that stay inline
SYSTEM_NODE_TYPES = frozenset({
    "user_question_node",
    "final_answer_node",
})


class ResourceToSave(BaseModel):
    """Resource data collected for saving."""
    rid: str
    category: ResourceCategory
    type: str
    name: Optional[str] = None
    config: Dict[str, Any]
    deps: Set[str] = Field(default_factory=set)
    unique_name: str = ""

    class Config:
        extra = Extra.forbid


class MaterializationResult(BaseModel):
    """Result of materializing a blueprint."""
    blueprint_draft: BlueprintDraft
    resource_ids: List[str] = Field(default_factory=list)
    id_mapping: Dict[str, str] = Field(default_factory=dict)

    class Config:
        extra = Extra.forbid


class ResourceMaterializer:
    """
    Materializes inline blueprint resources to saved resources.
    
    Flow:
    1. Collect inline resources (those with config defined)
    2. Build dependency graph using RefWalker (understands typed refs)
    3. Topological sort (dependencies first)
    4. Pre-validate all configs
    5. Save resources with rollback on failure
    6. Build final blueprint with $ref entries
    """
    
    def __init__(self, resources_service: ResourcesService):
        self._resources = resources_service
    
    def materialize(
        self,
        draft: BlueprintDraft,
        user_id: str,
    ) -> MaterializationResult:
        """
        Materialize inline resources and build final blueprint.
        
        Args:
            draft: BlueprintDraft with inline configs
            user_id: User who will own the resources
            
        Returns:
            MaterializationResult with blueprint and saved resource info
        """
        # Step 1: Collect resources with inline configs
        resources_to_save = self._collect_inline_resources(draft)
        
        if not resources_to_save:
            # Nothing to save - return draft as-is
            return MaterializationResult(
                blueprint_draft=draft,
                resource_ids=[],
                id_mapping={},
            )
        
        # Step 2: Topological sort (dependencies first)
        save_order = self._topological_sort(resources_to_save)
        
        # Step 3: Pre-validate and generate unique names
        self._prepare_and_validate(resources_to_save, save_order)
        
        # Step 4: Save resources with rollback on failure
        id_mapping = self._save_with_rollback(resources_to_save, save_order, user_id)
        
        # Step 5: Build final blueprint with $ref entries
        final_draft = self._build_final_draft(draft, id_mapping)
        
        return MaterializationResult(
            blueprint_draft=final_draft,
            resource_ids=list(id_mapping.values()),
            id_mapping=id_mapping,
        )
    
    def _collect_inline_resources(
        self,
        draft: BlueprintDraft,
    ) -> Dict[str, ResourceToSave]:
        """
        Collect resources that have inline configs (need to be saved).
        
        Skips:
        - Resources with config=None (already external refs)
        - System node types (user_question_node, final_answer_node)
        """
        resources: Dict[str, ResourceToSave] = {}
        
        for category in ResourceCategory:
            for resource in getattr(draft, category.value, []):
                # Skip if no config (already an external $ref)
                if resource.config is None:
                    continue
                
                # Skip if already external ref
                if resource.rid.is_external_ref():
                    continue
                
                # Get clean rid (strips $ref: if present)
                rid = resource.rid.ref
                
                # Skip system node types (they stay inline)
                resource_type = resource.type or ""
                if resource_type in SYSTEM_NODE_TYPES:
                    continue
                
                # Convert config to dict for saving
                config_dict = resource.config.model_dump(mode="python")
                
                resources[rid] = ResourceToSave(
                    rid=rid,
                    category=category,
                    type=resource.type or config_dict.get("type", ""),
                    name=resource.name,
                    config=config_dict,
                    deps=set(),  # Will be filled below
                )
        
        # Extract dependencies using RefWalker (understands typed refs)
        all_rids = set(resources.keys())
        for rid, res in resources.items():
            res.deps = self._extract_deps(res.config, all_rids)
        
        return resources
    
    def _extract_deps(self, config: Dict[str, Any], known_rids: Set[str]) -> Set[str]:
        """
        Extract dependency rids from config.
        
        Uses RefWalker for typed refs + bare string matching for inline refs.
        """
        deps: Set[str] = set()
        
        # RefWalker finds typed refs (LLMRef, ToolRef, etc.)
        deps.update(RefWalker.all_rids(config))
        
        # Also find bare string refs (template-local refs stored as plain strings)
        self._find_bare_string_refs(config, known_rids, deps)
        
        return deps
    
    def _find_bare_string_refs(
        self, 
        obj: Any, 
        known_rids: Set[str], 
        deps: Set[str]
    ) -> None:
        """Find bare string values that match known resource rids."""
        if isinstance(obj, str):
            if obj in known_rids:
                deps.add(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                self._find_bare_string_refs(v, known_rids, deps)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                self._find_bare_string_refs(item, known_rids, deps)
    
    def _topological_sort(
        self,
        resources: Dict[str, ResourceToSave],
    ) -> List[str]:
        """Sort rids so dependencies come first."""
        visited: Set[str] = set()
        result: List[str] = []
        
        def visit(rid: str):
            if rid in visited or rid not in resources:
                return
            visited.add(rid)
            for dep in resources[rid].deps:
                visit(dep)
            result.append(rid)
        
        for rid in resources:
            visit(rid)
        
        return result
    
    def _prepare_and_validate(
        self,
        resources: Dict[str, ResourceToSave],
        order: List[str],
    ) -> None:
        """
        Generate unique names and validate configs against Pydantic schemas.
        """
        errors: List[Dict[str, Any]] = []
        unique_suffix = uuid4().hex[:8]
        
        for rid in order:
            res = resources[rid]
            
            # Generate unique name
            base_name = res.name or res.type
            res.unique_name = f"{base_name}_{unique_suffix}"
            
            # Validate config against element Pydantic schema
            try:
                schema_cls = self._resources.element_registry.get_schema(
                    res.category, res.type
                )
                schema_cls(**res.config)
            except KeyError as e:
                errors.append({
                    "rid": rid,
                    "category": res.category.value,
                    "type": res.type,
                    "error": f"Unknown element type: {e}",
                })
            except Exception as e:
                errors.append({
                    "rid": rid,
                    "category": res.category.value,
                    "type": res.type,
                    "error": str(e),
                })
        
        if errors:
            raise MaterializationError(
                f"Validation failed for {len(errors)} resource(s)",
                errors=errors,
            )
    
    def _save_with_rollback(
        self,
        resources: Dict[str, ResourceToSave],
        order: List[str],
        user_id: str,
    ) -> Dict[str, str]:
        """
        Save resources in order with rollback on failure.
        
        Returns mapping: local_rid → saved_rid
        """
        id_mapping: Dict[str, str] = {}
        saved_ids: List[str] = []
        
        try:
            for rid in order:
                res = resources[rid]
                
                # Build prefixed mapping for config remapping
                # Template-local refs become external refs ($ref:saved_id)
                prefixed_mapping = {k: f"$ref:{v}" for k, v in id_mapping.items()}
                
                # Remap internal refs in config
                remapped_config = RefRemapper.remap(res.config, prefixed_mapping)
                
                # Save via service
                saved_doc = self._resources.create(
                    user_id=user_id,
                    category=res.category.value,
                    type=res.type,
                    name=res.unique_name,
                    config=remapped_config,
                )
                
                saved_ids.append(saved_doc.rid)
                id_mapping[rid] = saved_doc.rid
                
        except Exception as e:
            self._rollback(saved_ids)
            raise MaterializationError(
                f"Save failed, rolled back {len(saved_ids)} resource(s): {e}",
                errors=[{"message": str(e), "rolled_back": saved_ids}],
            )
        
        return id_mapping
    
    def _rollback(self, saved_ids: List[str]) -> None:
        """Delete resources that were saved before failure."""
        for rid in saved_ids:
            try:
                self._resources.delete(rid)
            except Exception:
                pass  # Best effort rollback
    
    def _build_final_draft(
        self,
        draft: BlueprintDraft,
        id_mapping: Dict[str, str],
    ) -> BlueprintDraft:
        """
        Build final blueprint with only plan-referenced resources.
        
        The blueprint only needs:
        - nodes: Referenced by plan steps
        - conditions: Referenced by plan exit_conditions
        
        Other categories (llms, tools, retrievers, providers) are embedded
        in the saved node/condition configs as $refs - not needed in blueprint.
        """
        # Categories that appear in the blueprint (plan-referenced)
        PLAN_CATEGORIES = {ResourceCategory.NODE, ResourceCategory.CONDITION}
        
        result: Dict[str, Any] = {}
        
        for category in ResourceCategory:
            if category in PLAN_CATEGORIES:
                # Nodes and Conditions: include with refs or inline
                entries = []
                for resource in getattr(draft, category.value, []):
                    rid = resource.rid.ref
                    
                    if rid in id_mapping:
                        # Was saved - dump full resource and update rid to external ref
                        entry = resource.model_dump(mode="json")
                        entry["rid"] = f"$ref:{id_mapping[rid]}"
                        entries.append(entry)
                    else:
                        # Keep as-is (system node stays inline)
                        entries.append(resource.model_dump(mode="json"))
                
                result[category.value] = entries
            else:
                # LLMs, Tools, Retrievers, Providers: empty (embedded in saved configs)
                result[category.value] = []
        
        # Remap plan refs
        remapped_plan = self._remap_plan(draft, id_mapping)
        
        return BlueprintDraft(
            **result,
            plan=remapped_plan,
            name=draft.name,
            description=draft.description,
        )
    
    def _remap_plan(
        self,
        draft: BlueprintDraft,
        id_mapping: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Remap plan step references to saved resource IDs."""
        remapped_plan = []
        
        for step in draft.plan:
            step_dict = step.model_dump(mode="json")
            
            # Remap node ref
            node_rid = step.node.ref
            if node_rid in id_mapping:
                step_dict["node"] = f"$ref:{id_mapping[node_rid]}"
            
            # Remap exit_condition if present
            if step.exit_condition:
                cond_rid = step.exit_condition.ref
                if cond_rid in id_mapping:
                    step_dict["exit_condition"] = f"$ref:{id_mapping[cond_rid]}"
            
            remapped_plan.append(step_dict)
        
        return remapped_plan
