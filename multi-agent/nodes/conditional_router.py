class ConditionalRouterNode:
    def __init__(self, route_fn):
        self.route_fn = route_fn  # function that returns "yes", "no", etc.

    def __call__(self, state):
        return self.route_fn(state)  # Must return branch key like "yes"
