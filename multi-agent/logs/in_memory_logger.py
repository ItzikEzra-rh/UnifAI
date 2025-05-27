from logs.logger_interface.py import LoggerInterface
from datetime import datetime

class InMemoryLogger(LoggerInterface):
    def __init__(self):
        self.logs = []

    def log_node_start(self, node_name):
        self.logs.append({"type": "node_start", "node": node_name, "timestamp": str(datetime.utcnow())})

    def log_node_end(self, node_name, output=None):
        self.logs.append({
            "type": "node_end", "node": node_name, "output": output, "timestamp": str(datetime.utcnow())
        })

    def log_tool_use(self, tool_name, input_data):
        self.logs.append({
            "type": "tool", "tool": tool_name, "input": input_data, "timestamp": str(datetime.utcnow())
        })

    def get_logs(self):
        return self.logs
