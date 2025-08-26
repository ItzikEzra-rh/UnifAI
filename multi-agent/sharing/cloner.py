import logging
from typing import Dict, List, Tuple, Set, Optional
from uuid import uuid4
from dataclasses import dataclass, field
from datetime import datetime

from resources.models import ResourceDoc
from resources.registry import ResourcesRegistry
from blueprints.models.blueprint import BlueprintDraft
from blueprints.service import BlueprintService
from catalog.element_registry import ElementRegistry
from core.ref import RefWalker
from core.enums import ResourceCategory

logger = logging.getLogger(__name__)


@dataclass
class ResourceCacheData:
    """Cached data for a resource."""
    doc: ResourceDoc
    dependencies: Set[str]  # Pre-computed dependencies
    cfg_model: object       # Pre-built schema model


@dataclass
class CloneResult:
    """Result of a cloning operation with comprehensive metrics."""
    success: bool
    new_item_id: Optional[str] = None
    rid_mapping: Dict[str, str] = field(default_factory=dict)
    name_conflicts: Dict[str, str] = field(default_factory=dict)
    resources_cloned: int = 0
    errors: List[str] = field(default_factory=list)


class ShareCloner:
    """
    Efficient cloner for sharing resources and blueprints.
    
    - Accurate dependency discovery with RefWalker
    - Single-pass loading and caching for efficiency  
    - Clean reference replacement
    - Proper logging and error handling
    """

    def __init__(self,
                 resources_registry: ResourcesRegistry,
                 blueprint_service: BlueprintService,
                 element_registry: ElementRegistry):
        self.resources = resources_registry
        self.blueprints = blueprint_service
        self.elements = element_registry

    def clone_resource_graph(self, *, root_rid: str, sender_user_id: str,
                             recipient_user_id: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Clone resource and all its dependencies."""
        logger.info(f"Starting resource graph clone: {root_rid} from {sender_user_id} to {recipient_user_id}")

        # Single pass: Load resources + compute dependencies + cache models
        closure_data = self._compute_closure({root_rid}, sender_user_id)

        # Clone using pre-computed data
        result = self._clone_resource_set(closure_data, sender_user_id, recipient_user_id)

        if not result.success:
            raise ValueError(f"Resource cloning failed: {result.errors}")

        logger.info(f"Resource graph clone completed: {result.resources_cloned} resources cloned")
        return result.rid_mapping, result.name_conflicts

    def clone_blueprint(self, *, blueprint_id: str, sender_user_id: str,
                        recipient_user_id: str) -> Tuple[str, Dict[str, str], Dict[str, str]]:
        """Clone blueprint and all its dependencies."""
        logger.info(f"Starting blueprint clone: {blueprint_id} from {sender_user_id} to {recipient_user_id}")

        # Load blueprint document through service
        bp_doc = self.blueprints.get_blueprint_draft_doc(blueprint_id)
        if bp_doc["user_id"] != sender_user_id:
            raise ValueError(f"Blueprint {blueprint_id} not owned by sender")

        draft = BlueprintDraft(**bp_doc["spec_dict"])

        # Get dependencies using RefWalker
        external_rids = set(RefWalker.external_rids(draft))

        # Clone dependencies if any exist
        rid_mapping = {}
        name_conflicts = {}
        resources_cloned = 0

        if external_rids:  # Only if there are external refs
            logger.debug(f"Found external references: {external_rids}")

            # Single pass: Load + analyze + cache all resource data
            closure_data = self._compute_closure(external_rids, sender_user_id)

            if closure_data:
                logger.debug(f"Total closure to clone: {set(closure_data.keys())}")
                clone_result = self._clone_resource_set(closure_data, sender_user_id, recipient_user_id)

                if not clone_result.success:
                    raise ValueError(f"Failed to clone resources: {clone_result.errors}")

                rid_mapping = clone_result.rid_mapping
                name_conflicts = clone_result.name_conflicts
                resources_cloned = clone_result.resources_cloned
                logger.debug(f"RID mapping created: {rid_mapping}")

        # Rewrite blueprint references if any exist
        if rid_mapping:
            new_spec_dict = self._replace_refs_in_dict(bp_doc["spec_dict"], rid_mapping)
        else:
            new_spec_dict = bp_doc["spec_dict"]

        new_draft = BlueprintDraft(**new_spec_dict)

        # Handle blueprint name
        new_draft.name = f"{new_draft.name} (from {sender_user_id})"

        # Save blueprint through service
        new_blueprint_id = self.blueprints.save_draft(
            user_id=recipient_user_id,
            draft_dict=new_draft.model_dump(mode="json")
        )

        logger.info(f"Blueprint clone completed: {new_blueprint_id}, {resources_cloned} resources cloned")
        return new_blueprint_id, rid_mapping, name_conflicts

    def _clone_resource_set(self, closure_data: Dict[str, ResourceCacheData], 
                           sender_user_id: str, recipient_user_id: str) -> CloneResult:
        """Clone a set of resources using pre-computed closure data."""
        try:
            logger.debug(f"Cloning {len(closure_data)} resources using cached data")

            # Ownership already validated during closure computation
            # Generate RID mapping for all resources
            rid_mapping = {old_rid: uuid4().hex for old_rid in closure_data.keys()}
            name_conflicts = {}

            # Process each resource using cached data (no redundant loading/analysis)
            new_docs = []
            for old_rid, cache_data in closure_data.items():
                try:
                    # Use pre-computed dependencies
                    new_doc = self._clone_single_resource(
                        cache_data, rid_mapping, recipient_user_id
                    )

                    # Track name conflicts
                    if new_doc.name != cache_data.doc.name:
                        name_conflicts[cache_data.doc.name] = new_doc.name

                    new_docs.append(new_doc)

                except Exception as e:
                    logger.error(f"Failed to clone resource {old_rid}: {e}")
                    return CloneResult(success=False, errors=[f"Failed to clone {old_rid}: {e}"])

            # Batch create all resources
            self._batch_create_resources(new_docs)

            return CloneResult(
                success=True,
                rid_mapping=rid_mapping,
                name_conflicts=name_conflicts,
                resources_cloned=len(new_docs)
            )

        except Exception as e:
            logger.error(f"Resource set clone failed: {e}")
            return CloneResult(success=False, errors=[str(e)])

    def _compute_closure(self, root_rids: Set[str], owner_user_id: str) -> Dict[str, ResourceCacheData]:
        """
        Compute resource closure and cache all data in a single pass.
        
        - Loads each resource only once
        - Runs RefWalker only once per resource 
        - Caches schema models for reuse
        - Validates ownership during traversal
        """
        visited_rids = set()
        to_visit = set(root_rids)
        closure_cache = {}  # rid -> ResourceCacheData

        while to_visit:
            rid = to_visit.pop()
            if rid in visited_rids:
                continue
            visited_rids.add(rid)

            try:
                # Load resource (only once per resource)
                doc = self.resources.get(rid)
                
                # Validate ownership (only once per resource)
                if doc.user_id != owner_user_id:
                    logger.warning(f"Resource {rid} not owned by {owner_user_id}, owned by {doc.user_id}")
                    continue

                # Create schema model (only once per resource)
                cfg_model = self.elements.get_schema(
                    ResourceCategory(doc.category), doc.type
                )(**doc.cfg_dict)

                # Run RefWalker (only once per resource)
                dependencies = RefWalker.external_rids(cfg_model)

                # Cache all computed data for later use
                closure_cache[rid] = ResourceCacheData(
                    doc=doc,
                    dependencies=dependencies,
                    cfg_model=cfg_model
                )

                # Add dependencies to traversal queue
                for dep_rid in dependencies:
                    if dep_rid not in visited_rids:
                        to_visit.add(dep_rid)

            except (KeyError, Exception) as e:
                logger.warning(f"Error processing resource {rid}: {e}")
                continue

        logger.debug(f"Cached data for {len(closure_cache)} resources")
        return closure_cache

    def _clone_single_resource(self, cache_data: ResourceCacheData, rid_mapping: Dict[str, str],
                              recipient_user_id: str) -> ResourceDoc:
        """
        Clone a single resource using pre-computed data.
        
        - Uses cached dependencies instead of re-running RefWalker
        - Reuses schema model data from cache
        """
        original_doc = cache_data.doc
        new_rid = rid_mapping[original_doc.rid]

        # Resolve name conflicts (no changes here)
        new_name = self._resolve_name_conflict(
            recipient_user_id, original_doc.category,
            original_doc.type, original_doc.name
        )

        # Clone with reference rewriting (no changes here)
        new_cfg_dict = self._replace_refs_in_dict(original_doc.cfg_dict, rid_mapping)

        # Use pre-computed dependencies instead of re-running RefWalker
        # Map old dependencies to new RIDs
        original_dependencies = cache_data.dependencies
        new_nested_refs = [
            rid_mapping.get(dep_rid, dep_rid) for dep_rid in original_dependencies
        ]

        return ResourceDoc(
            rid=new_rid,
            user_id=recipient_user_id,
            category=original_doc.category,
            type=original_doc.type,
            name=new_name,
            version=1,
            cfg_dict=new_cfg_dict,
            nested_refs=new_nested_refs
        )

    def _batch_create_resources(self, docs: List[ResourceDoc]) -> None:
        """Create multiple resources efficiently."""
        # TODO: Implement actual batch creation in ResourcesRegistry
        for doc in docs:
            self.resources.create(doc)

    def _resolve_name_conflict(self, user_id: str, category: str,
                               type_: str, preferred_name: str) -> str:
        """Resolve name conflicts by adding copy suffix."""
        base_name = preferred_name
        counter = 1
        current_name = base_name

        while True:
            existing = self.resources._repo.find_by_name(user_id, category, type_, current_name)
            if not existing:
                return current_name

            current_name = f"{base_name} (copy {counter})" if counter > 1 else f"{base_name} (copy)"
            counter += 1

            if counter > 100:  # Prevent infinite loops
                current_name = f"{base_name} ({uuid4().hex[:8]})"
                break

        return current_name

    def _replace_refs_in_dict(self, obj, rid_mapping: Dict[str, str]):
        """Replace references in nested structures."""
        if isinstance(obj, dict):
            return {k: self._replace_refs_in_dict(v, rid_mapping) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_refs_in_dict(v, rid_mapping) for v in obj]
        elif isinstance(obj, str):
            result = obj
            for old_rid, new_rid in rid_mapping.items():
                # Replace $ref: patterns
                result = result.replace(f"$ref:{old_rid}", f"$ref:{new_rid}")
            return result
        else:
            return obj
