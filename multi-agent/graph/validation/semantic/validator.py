from typing import Optional, Set, AbstractSet
from graph.graph_plan import GraphPlan
from ..base import Validator, ValidationReport, ValidationMessage, MessageSeverity, MessageCode
from .models import SemanticValidationDetails, RequiredNodeIssue


class RequiredNodesValidator(Validator):
    """Validates that required node types are present in the graph.

    All required nodes are specified solely by their ``type_key`` string. We purposely ignore
    the category here because business rules for start/end/required nodes are expressed at the
    element-type level.
    """

    def __init__(
        self,
        required_start_nodes: Optional[Set[str]] = None,
        required_end_nodes: Optional[Set[str]] = None,
        required_any_nodes: Optional[Set[str]] = None,
    ) -> None:
        # Normalize to regular sets for easier downstream use
        self._required_start_nodes = set(required_start_nodes or set())
        self._required_end_nodes = set(required_end_nodes or set())
        self._required_any_nodes = set(required_any_nodes or set())

    @property
    def name(self) -> str:
        return "required-nodes"

    def validate(self, plan: GraphPlan) -> ValidationReport:
        """Check required nodes are present."""
        messages: list[ValidationMessage] = []
        required_node_issues: list[RequiredNodeIssue] = []

        # Root, leaf, and all node sets by type_key
        root_types = {s.type_key for s in plan.get_roots()}
        leaf_types = {s.type_key for s in plan.steps if s.uid in self._get_leaf_nodes(plan)}
        all_types = {s.type_key for s in plan.steps}

        # Dictionaries to collect missing specs for details
        missing_start_nodes: Set[str] = set()
        missing_end_nodes: Set[str] = set()

        # Validate each group using helper method
        self._check_nodes(
            self._required_start_nodes,
            root_types,
            node_type="start",
            error_code=MessageCode.MISSING_START_NODE,
            messages=messages,
            required_node_issues=required_node_issues,
            missing_collector=missing_start_nodes,
            extra_ctx_key="actual_roots",
        )

        self._check_nodes(
            self._required_end_nodes,
            leaf_types,
            node_type="end",
            error_code=MessageCode.MISSING_END_NODE,
            messages=messages,
            required_node_issues=required_node_issues,
            missing_collector=missing_end_nodes,
            extra_ctx_key="actual_leaves",
        )

        self._check_nodes(
            self._required_any_nodes,
            all_types,
            node_type="any",
            error_code=MessageCode.MISSING_REQUIRED_NODE,
            messages=messages,
            required_node_issues=required_node_issues,
            missing_collector=None,  # Not tracked in details yet
            extra_ctx_key=None,
        )

        is_valid = not any(msg.severity == MessageSeverity.ERROR for msg in messages)

        # Create typed details
        details = SemanticValidationDetails(
            required_node_issues=required_node_issues,
            missing_start_nodes=missing_start_nodes,
            missing_end_nodes=missing_end_nodes,
        )

        return ValidationReport(
            validator_name=self.name,
            is_valid=is_valid,
            messages=messages,
            details=details
        )

    def _get_leaf_nodes(self, plan: GraphPlan) -> Set[str]:
        """Find all leaf nodes (no outgoing edges)."""
        # A node has outgoing edges if:
        #   1) It appears in another step's 'after' list (dependency edge), or
        #   2) It defines conditional branches.

        outgoing_nodes = {parent_uid for step in plan.steps for parent_uid in step.after}
        outgoing_nodes.update({step.uid for step in plan.steps if step.branches})

        return {step.uid for step in plan.steps if step.uid not in outgoing_nodes}

    # ------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------

    def _check_nodes(
        self,
        required_specs: AbstractSet[str],
        available_specs: AbstractSet[str],
        node_type: str,
        error_code: MessageCode,
        messages: list[ValidationMessage],
        required_node_issues: list[RequiredNodeIssue],
        missing_collector: Set[str] | None = None,
        extra_ctx_key: str | None = None,
    ) -> None:
        """Append issues/messages for any required spec not in available set."""
        for spec in required_specs - available_specs:

            required_node_issues.append(
                RequiredNodeIssue(
                    node_type=node_type,
                    expected=spec,
                    actual=None if not available_specs else next(iter(available_specs)),
                )
            )

            if missing_collector is not None:
                missing_collector.add(spec)

            ctx = {"expected": spec}
            if extra_ctx_key:
                ctx[extra_ctx_key] = list(available_specs)

            base_msg = "Graph must {verb} '{spec}' node"
            verb = {
                "start": "start with",
                "end": "end with",
                "any": "contain",
            }[node_type]

            messages.append(
                ValidationMessage(
                    text=base_msg.format(verb=verb, spec=spec),
                    severity=MessageSeverity.ERROR,
                    code=error_code,
                    context=ctx,
                )
            )
