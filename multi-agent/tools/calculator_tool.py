from tools.base_tool import BaseTool

class CalculatorTool(BaseTool):
    """
    A basic calculator that evaluates arithmetic expressions.
    """

    def name(self) -> str:
        return "calculator"

    def invoke(self, input_data: dict) -> dict:
        expression = input_data.get("expression", "")
        try:
            result = eval(expression, {"__builtins__": {}})
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
