import pickle

class GraphSaver:
    """
    Responsible for saving/loading the graph plan and runtime metadata.
    """

    def __init__(self, save_path="runtime_state.pkl"):
        self.save_path = save_path

    def save(self, runtime_state):
        data = {
            "plan": runtime_state.plan,
            "metadata": runtime_state.metadata
        }
        with open(self.save_path, "wb") as f:
            pickle.dump(data, f)

    def load(self):
        with open(self.save_path, "rb") as f:
            data = pickle.load(f)
        return data["plan"], data.get("metadata", {})
