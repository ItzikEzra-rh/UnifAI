def execute_until_exit(graph, state: dict, exit_key="exit"):
    """
    Repeatedly invokes the graph until state[exit_key] is True.
    """
    iteration = 0
    while not state.get(exit_key, False):
        print(f"🔁 Iteration {iteration}")
        state = graph.invoke(state)
        iteration += 1
    return state
