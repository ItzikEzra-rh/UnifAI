"""
Engine-agnostic merge applicator for GraphState channels.

Fully LangGraph-aligned architecture, mirroring apply_writes() in _algo.py:

  Sequential (1 result):
    The node received the full state, modified it, returned the full state.
    No reconciliation needed — return it directly.
    Matches LangGraph: sequential nodes run exclusively, no conflict possible.

  Parallel (N results, e.g. fan-out to Jira + Confluence agents):
    Three-step pipeline mirrors LangGraph's apply_writes():

    Step 1 — extract_write (per field, per result):
        channel.extract_write(original_value, result_value)
        → "what did this node write to this field?"
        → _MISSING if unchanged

        For lists:  pure append  → returns the new tail (increment)
                    mutation     → returns full list (let operator reconcile)
        For dicts:  returns only new/changed keys
        For scalars: returns new value

    Step 2 — group writes by field  (mirrors pending_writes_by_channel):
        writes_by_field[field] = [write_nodeA, write_nodeB, ...]

    Step 3 — reconcile via channel  (mirrors channel.update(vals)):
        BinOpChannel:    reduce(operator, writes, base)
        LastValueChannel: writes[-1]

This correctly handles all parallel scenarios:
  • messages:      extract increments [m3],[m4] → operator appends → [m1,m2,m3,m4]
  • inter_packets: extract full lists  (ack_by mutated) → operator unions ack_by
  • nodes_output:  extract dict diffs  → operator merges keys
  • scalars:       extract new value   → last write wins
"""
from typing import Any, Dict, List, Type

from graph.state.graph_state import GraphState
from graph.state.channel_types import build_channel_registry, _MISSING


class MergeApplicator:
    """
    Reconciles parallel node results into a single GraphState.

    Constructed once per workflow execution (or per worker startup).
    Channel registry is built from GraphState annotations at construction time,
    exactly as LangGraph builds its channel map from StateGraph schema.
    """

    def __init__(self, state_cls: Type[GraphState]) -> None:
        self._state_cls = state_cls
        # Built once: maps field_name → channel instance
        # LangGraph equivalent: channels dict passed into apply_writes()
        self._channels = build_channel_registry(state_cls)

    def apply(self, original: GraphState, results: List[GraphState]) -> GraphState:
        """
        Reconcile one or more node results against the original state.

        Args:
            original: GraphState snapshot before any node in this superstep ran.
            results:  List of GraphStates returned by the node(s).
                      Length 1 = sequential execution.
                      Length N = parallel fan-out.

        Returns:
            The reconciled GraphState.
        """
        if len(results) == 1:
            # Sequential: node ran exclusively — its result IS the new state.
            return results[0]

        return self._merge_parallel(original, results)

    # ------------------------------------------------------------------ #
    #  Private
    # ------------------------------------------------------------------ #

    def _merge_parallel(
        self,
        original: GraphState,
        results: List[GraphState],
    ) -> GraphState:
        """
        Full parallel reconciliation — mirrors LangGraph's apply_writes().

        For each GraphState field:
          1. Ask each channel: "what did this node write?" (extract_write)
          2. Collect non-MISSING writes  (pending_writes_by_channel grouping)
          3. Let the channel reconcile:  channel.update(base, writes)
        """
        accumulated: Dict[str, Any] = {}

        for field_name, channel in self._channels.items():
            base_value = getattr(original, field_name)

            # Step 1 + 2: extract writes from each parallel result
            # Mirrors: pending_writes_by_channel[chan].append(val)
            writes: List[Any] = []
            for result in results:
                result_value = getattr(result, field_name)
                write = channel.extract_write(base_value, result_value)
                if write is not _MISSING:
                    writes.append(write)

            # Step 3: apply channel reconciliation
            # Mirrors: channels[chan].update(vals) in apply_writes()
            accumulated[field_name] = (
                channel.update(base_value, writes) if writes else base_value
            )

        return self._state_cls(**accumulated)
