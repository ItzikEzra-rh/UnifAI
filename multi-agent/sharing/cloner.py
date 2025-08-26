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
    Improved cloner with RefWalker-based efficiency and clean architecture.
    
    Key improvements:
    - Uses RefWalker for accurate dependency discovery
    - Eliminates code duplication through unified methods
    - Simple and reliable reference replacement
    - Proper logging instead of print statements
    - Batch operations for better performance
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
        """Clone resource and dependencies using unified efficient method."""
        logger.info(f"Starting resource graph clone: {root_rid} from {sender_user_id} to {recipient_user_id}")

        # Use RefWalker-based closure computation for accuracy
        closure = self._compute_resource_closure_with_refwalker({root_rid}, sender_user_id)

        # Use unified cloning method (eliminates code duplication)
        result = self._clone_resource_set_unified(closure, sender_user_id, recipient_user_id)

        if not result.success:
            raise ValueError(f"Resource cloning failed: {result.errors}")

        logger.info(f"Resource graph clone completed: {result.resources_cloned} resources cloned")
        return result.rid_mapping, result.name_conflicts

    def clone_blueprint(self, *, blueprint_id: str, sender_user_id: str,
                        recipient_user_id: str) -> Tuple[str, Dict[str, str], Dict[str, str]]:
        """Clone blueprint and dependencies using improved efficient methods."""
        logger.info(f"Starting blueprint clone: {blueprint_id} from {sender_user_id} to {recipient_user_id}")

        # Load blueprint document through service (follows service layer architecture)
        bp_doc = self.blueprints.get_blueprint_draft_doc(blueprint_id)
        if bp_doc["user_id"] != sender_user_id:
            raise ValueError(f"Blueprint {blueprint_id} not owned by sender")

        draft = BlueprintDraft(**bp_doc["spec_dict"])

        # Get dependencies using RefWalker (consistent with BlueprintService)
        external_rids = set(RefWalker.external_rids(draft))

        # Clone dependencies if any exist
        rid_mapping = {}
        name_conflicts = {}
        resources_cloned = 0

        if external_rids:  # Only if there are external refs
            logger.debug(f"Found external references: {external_rids}")

            # Use RefWalker-based closure computation for ALL external references
            all_closure = self._compute_resource_closure_with_refwalker(external_rids, sender_user_id)

            if all_closure:
                logger.debug(f"Total closure to clone: {all_closure}")
                clone_result = self._clone_resource_set_unified(all_closure, sender_user_id, recipient_user_id)

                if not clone_result.success:
                    raise ValueError(f"Failed to clone resources: {clone_result.errors}")

                rid_mapping = clone_result.rid_mapping
                name_conflicts = clone_result.name_conflicts
                resources_cloned = clone_result.resources_cloned
                logger.debug(f"RID mapping created: {rid_mapping}")

        # Rewrite blueprint references (only if there are any to rewrite)
        if rid_mapping:
            new_spec_dict = self._replace_refs_in_dict(bp_doc["spec_dict"], rid_mapping)
        else:
            new_spec_dict = bp_doc["spec_dict"]  # Direct copy for inline-only

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

    def _clone_resource_set_unified(self, resource_rids: Set[str], sender_user_id: str,
                                    recipient_user_id: str) -> CloneResult:
        """Unified method for cloning resource sets efficiently."""
        try:
            # Batch load resources (more efficient than individual gets)
            resources = self._batch_load_resources(resource_rids)
            missing = resource_rids - set(resources.keys())
            if missing:
                logger.warning(f"Missing resources: {missing}")

            # Validate ownership
            violations = self._validate_ownership_batch(resources, sender_user_id)
            if violations:
                return CloneResult(success=False, errors=[f"Resources not owned by sender: {violations}"])

            # Generate RID mapping
            rid_mapping = {old_rid: uuid4().hex for old_rid in resources.keys()}
            name_conflicts = {}

            # Process each resource
            new_docs = []
            for old_rid, original_doc in resources.items():
                try:
                    new_doc = self._clone_single_resource(original_doc, rid_mapping, recipient_user_id)

                    # Track name conflicts
                    if new_doc.name != original_doc.name:
                        name_conflicts[original_doc.name] = new_doc.name

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

    def _compute_resource_closure_with_refwalker(self, root_rids: Set[str], owner_user_id: str) -> Set[str]:
        """Compute closure using RefWalker for accuracy and consistency."""
        visited = set()
        to_visit = set(root_rids)

        while to_visit:
            rid = to_visit.pop()
            if rid in visited:
                continue
            visited.add(rid)

            try:
                doc = self.resources.get(rid)
                if doc.user_id != owner_user_id:
                    logger.warning(f"Resource {rid} not owned by {owner_user_id}, owned by {doc.user_id}")
                    continue

                # USE REFWALKER instead of trusting nested_refs for accuracy
                cfg_model = self.elements.get_schema(
                    ResourceCategory(doc.category), doc.type
                )(**doc.cfg_dict)

                # RefWalker finds ALL references accurately from actual config
                dependencies = RefWalker.external_rids(cfg_model)

                for dep_rid in dependencies:
                    if dep_rid not in visited:
                        to_visit.add(dep_rid)

            except (KeyError, Exception) as e:
                logger.warning(f"Error processing resource {rid}: {e}")
                continue

        return visited

    def _clone_single_resource(self, original_doc: ResourceDoc, rid_mapping: Dict[str, str],
                               recipient_user_id: str) -> ResourceDoc:
        """Clone a single resource with reference rewriting."""
        new_rid = rid_mapping[original_doc.rid]

        # Resolve name conflicts
        new_name = self._resolve_name_conflict(
            recipient_user_id, original_doc.category,
            original_doc.type, original_doc.name
        )

        # Clone with reference rewriting
        new_cfg_dict = self._replace_refs_in_dict(original_doc.cfg_dict, rid_mapping)

        # Recompute nested_refs using RefWalker for accuracy
        model_cls = self.elements.get_schema(
            ResourceCategory(original_doc.category), original_doc.type
        )
        cfg_model = model_cls(**new_cfg_dict)
        new_nested_refs = list(RefWalker.external_rids(cfg_model))

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

    def _batch_load_resources(self, rids: Set[str]) -> Dict[str, ResourceDoc]:
        """Load multiple resources efficiently."""
        # TODO: Implement actual batch loading in ResourcesRegistry
        # For now, fall back to individual loads but track for future optimization
        resources = {}
        for rid in rids:
            try:
                resources[rid] = self.resources.get(rid)
            except KeyError:
                logger.warning(f"Resource {rid} not found")
        return resources

    def _batch_create_resources(self, docs: List[ResourceDoc]) -> None:
        """Create multiple resources efficiently."""
        # TODO: Implement actual batch creation in ResourcesRegistry
        # For now, fall back to individual creates but in a more organized way
        for doc in docs:
            self.resources.create(doc)

    def _validate_ownership_batch(self, resources: Dict[str, ResourceDoc], owner_user_id: str) -> List[str]:
        """Validate ownership for a batch of resources."""
        violations = []
        for rid, doc in resources.items():
            if doc.user_id != owner_user_id:
                violations.append(f"{rid} (owned by {doc.user_id})")
        return violations

    def _validate_ownership(self, rids: Set[str], owner_user_id: str) -> List[str]:
        """Validate all resources are owned by user."""
        violations = []
        for rid in rids:
            try:
                doc = self.resources.get(rid)
                if doc.user_id != owner_user_id:
                    violations.append(rid)
            except KeyError:
                violations.append(rid)
        return violations

    def _resolve_name_conflict(self, user_id: str, category: str,
                               type_: str, preferred_name: str) -> str:
        """Resolve name conflicts following existing patterns."""
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
