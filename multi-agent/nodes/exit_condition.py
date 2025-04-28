class ExitConditionNode:
    def __call__(self, state):
        # Determine loop exit
        return {"exit": state.get("loop_done", False)}
