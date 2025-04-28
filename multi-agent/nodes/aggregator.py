class AggregatorNode:
    def __call__(self, state):
        responses = state.get("agent_responses", {})
        combined = " | ".join(responses.values())
        state["aggregated_answer"] = combined
        return state
