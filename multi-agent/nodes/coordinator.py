class CoordinatorNode:
    def __init__(self, agents: list):
        self.agents = agents

    def __call__(self, state):
        query = state.get("user_input", "")
        responses = {}
        for agent in self.agents:
            responses[agent.name()] = agent.get_answer(query)
        state["agent_responses"] = responses
        return state
