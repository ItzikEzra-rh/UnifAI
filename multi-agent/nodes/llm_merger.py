from .base_node import BaseNode


class LLMMergerNode(BaseNode):
    """this class is a node that merges the output of multiple Nodes using LLM and a custom system prompt."""

    def run(self, state: dict) -> dict:
        # 1) Build messages
        messages = state.get("messages", [])
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        # messages.append({"role": "user", "content": state.get("user_prompt", "")})

        agents_output = state.get("nodes_output", [])
        agents_output_str = ""
        for agent_dict in agents_output:
            agents_output_str += f"{agent_dict}\n"
        messages.append({"role": "user", "content": agents_output_str})
        # print(f"""agents_output: {agents_output_str}""")
        # 2) Call LLM
        response = self.llm.chat(messages)
        # print(f"""response: {response}""")

        state["output"] = response
        return state
