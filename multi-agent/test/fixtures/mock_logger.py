class MockLogger:
    def __init__(self):
        self.events = []

    def log_node_start(self, name):
        self.events.append(f"START:{name}")

    def log_node_end(self, name):
        self.events.append(f"END:{name}")

    def log_tool_use(self, tool_name):
        self.events.append(f"TOOL:{tool_name}")

    def get_events(self):
        return self.events
