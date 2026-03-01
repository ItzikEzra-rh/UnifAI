"""
Engine-agnostic merge applicator for GraphState channels.

Applies the same merge strategies that LangGraph reads from Annotated
metadata, but callable explicitly by any engine (Temporal, tests, etc.).
"""
from typing import Any, Callable, Dict, List, Type

from graph.state.graph_state import GraphState


class MergeApplicator:
    """
    Reconciles node results with the current graph state.

    Single unified method: apply(original, results).

      • 1 result  → sequential: the node's result IS the correct state.
                     No merge needed — the node received the full state,
                     modified it in place, and returned it.

      • N results → parallel fan-out: each node received the SAME original
                     state and modified it independently. We extract the
                     incremental diff from each result and apply the diffs
                     using merge strategies so changes compose correctly.

    This matches LangGraph's behavior:
      • Sequential: LG passes state by reference → node modifies in place
        → reducer sees (same_obj, same_obj) → no-op → modifications preserved.
      • Parallel: LG applies reducers to reconcile independent branch outputs.
    """

    def __init__(self, state_cls: Type[GraphState]) -> None:
        self._state_cls = state_cls
        self._strategies: Dict[str, Callable] = state_cls.get_merge_strategies()

    def apply(self, original: GraphState, results: List[GraphState]) -> GraphState:
        """
        Reconcile one or more node results against the original state.

        Args:
            original: The state BEFORE the node(s) ran.
            results:  List of states returned by the node(s).
                      Length 1 = sequential, length N = parallel.

        Returns:
            The reconciled GraphState.
        """
        if len(results) == 1:
            return results[0]

        return self._merge_parallel(original, results)

    # ------------------------------------------------------------------ #
    #  Private: parallel merge
    # ------------------------------------------------------------------ #

    def _merge_parallel(
            self,
            original: GraphState,
            results: List[GraphState],
    ) -> GraphState:
        """
        Merge results from N parallel nodes that all received `original`.

        For each result, extracts the INCREMENTAL changes relative to
        `original`, then applies those increments sequentially to an
        accumulator using the channel merge strategies.

        Example with messages=[m1,m2]:
          Node A returns [m1,m2,m3] → increment = [m3]
          Node B returns [m1,m2,m4] → increment = [m4]
          Accumulated: [m1,m2] → +[m3] → [m1,m2,m3] → +[m4] → [m1,m2,m3,m4]
        """
        accumulated: Dict[str, Any] = {
            name: getattr(original, name)
            for name in self._state_cls.model_fields
        }

        for result in results:
            changes = self._extract_changes(original, result)
            for field_name, change_val in changes.items():
                if field_name in self._strategies:
                    accumulated[field_name] = self._strategies[field_name](
                        accumulated[field_name], change_val,
                    )
                else:
                    accumulated[field_name] = change_val

        return self._state_cls(**accumulated)

    def _extract_changes(
            self,
            original: GraphState,
            modified: GraphState,
    ) -> Dict[str, Any]:
        """
        Extract incremental changes from `modified` relative to `original`.

        • Lists  → only the appended elements (if prefix matches)
        • Dicts  → only new / changed keys (with recursive list diff)
        • Scalars → the new value (if different)

        Fields that are unchanged are omitted from the result.
        """
        changes: Dict[str, Any] = {}

        for field_name in self._state_cls.model_fields:
            orig_val = getattr(original, field_name)
            mod_val = getattr(modified, field_name)

            if orig_val == mod_val:
                continue

            if isinstance(orig_val, list) and isinstance(mod_val, list):
                changes[field_name] = _extract_list_increment(orig_val, mod_val)
            elif isinstance(orig_val, dict) and isinstance(mod_val, dict):
                changes[field_name] = _extract_dict_increment(orig_val, mod_val)
            else:
                changes[field_name] = mod_val

        return changes


# ------------------------------------------------------------------ #
#  Pure helper functions (no class state needed)
# ------------------------------------------------------------------ #

def _extract_list_increment(original: list, modified: list) -> list:
    """
    If the modified list is the original with new items appended,
    return only the new items.  Otherwise return the full modified list.
    """
    if (
        len(modified) > len(original)
        and modified[:len(original)] == original
    ):
        return modified[len(original):]
    return modified


def _extract_dict_increment(original: dict, modified: dict) -> dict:
    """
    Return only keys that are new or have changed values.
    For dict values that are lists, recurse into list diff.
    """
    diff: dict = {}
    for k, v in modified.items():
        if k not in original:
            diff[k] = v
        elif v != original[k]:
            if isinstance(original[k], list) and isinstance(v, list):
                diff[k] = _extract_list_increment(original[k], v)
            else:
                diff[k] = v
    return diff
