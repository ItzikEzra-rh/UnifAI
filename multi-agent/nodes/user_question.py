from registry import registry


@registry.register_node("user_question")
class UserQuestionNode:
    def __call__(self, state):
        print("UserQuestionNode: Prompt received:", state.get("user_input"))
        return state
