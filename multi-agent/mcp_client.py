# import asyncio
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from langchain_core.tools import BaseTool, InjectedToolArg, StructuredTool
# from pydantic import BaseModel, Field
# from datamodel_code_generator import InputFileType, generate
# from datamodel_code_generator.model import PythonVersion
# from pydantic import BaseModel, Field
# import json
# from typing import Type
# from datamodel_code_generator import (
#     generate,
#     InputFileType,
#     DataModelType,
#     PythonVersion
# )
# import tempfile
# from pathlib import Path
# import importlib.util
# import sys
#
#
# async def main():
#     # Define the server parameters (command to start the server)
#     server_params = StdioServerParameters(
#         command="python",
#         args=["mcp_server.py"]
#     )
#
#     # Establish connection with the MCP server
#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             # Initialize the session
#             await session.initialize()
#
#             # Retrieve the list of available tools
#             response = await session.list_tools()
#             tools = response.tools
#
#             # Display tool information
#             for tool in tools:
#                 print(f"Tool Name: {tool.name}")
#                 print(f"Description: {tool.description}")
#                 print(f"Input Schema: {tool.inputSchema}")
#                 print("-" * 40)
#
#                 _model = json_schema_model(tool.inputSchema, to_pascal_case(tool.inputSchema.get("title")))
#                 print(_model(name="my name"))
#     # Example: Call the 'greet_user' tool
#     if any(tool.name == "greet_user" for tool in tools):
#         result = await session.call_tool("greet_user", {"name": "Alice"})
#         print("Tool Output:", result[0].text)
#
#
# def json_schema_model(
#         schema: dict,
#         model_name: str = "AdditionInput"
# ) -> Type[BaseModel]:
#     """
#     Generate and load a Pydantic model class from a given JSON Schema.
#
#     Args:
#         schema (dict): The JSON schema dict to convert into a model.
#         model_name (str): The name of the model class to retrieve after generation.
#
#     Returns:
#         Type[BaseModel]: The generated Pydantic model class.
#
#     Raises:
#         AttributeError: If the specified model class is not found.
#     """
#     schema_str = json.dumps(schema)
#
#     with tempfile.TemporaryDirectory() as temp_dir:
#         module_name = "_generated_model"
#         output_file = Path(temp_dir) / f"{module_name}.py"
#
#         generate(
#             input_=schema_str,
#             input_file_type=InputFileType.JsonSchema,
#             output_model_type=DataModelType.PydanticV2BaseModel,
#             target_python_version=PythonVersion.PY_310,
#             use_annotated=False,
#             field_constraints=True,
#             use_field_description=True,
#             reuse_model=True,
#             use_title_as_name=True,
#             use_standard_collections=True,
#             use_union_operator=True,
#             strict_nullable=True,
#             keep_model_order=True,
#             output=output_file
#         )
#
#         sys.path.insert(0, temp_dir)
#         try:
#             # with open(output_file, "r") as f:
#             #     print(f.read())
#             spec = importlib.util.spec_from_file_location(module_name, str(output_file))
#             if not spec or not spec.loader:
#                 raise ImportError(f"Could not create module spec for '{module_name}'")
#
#             module = importlib.util.module_from_spec(spec)
#             spec.loader.exec_module(module)
#
#             model_cls = getattr(module, model_name, None)
#             if model_cls is None:
#                 raise AttributeError(f"Model class '{model_name}' not found in generated code.")
#             model_cls.model_rebuild()
#             return model_cls
#         finally:
#             sys.path.remove(temp_dir)
#
#
# import re
#
#
# def to_pascal_case(s: str) -> str:
#     # Split on underscores, hyphens, and capital word boundaries
#     words = re.findall(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])', re.sub(r'[-_]', ' ', s))
#     return ''.join(word.capitalize() for word in words)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
#
#     # class AdditionInput(BaseModel):
#     #     a: int = Field(..., description="First number")
#     #     b: int = Field(..., description="Second number")
#     # schema = AdditionInput.model_json_schema()
#     # print(schema)
#     # _model = json_schema_model(schema)
#     # print(_model(a=1,b=2))


import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    server_url = "http://localhost:8004/sse"  # change if needed

    # Connect to the SSE server
    async with sse_client(url=server_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tool_list = await session.list_tools()
            for tool in tool_list.tools:
                print(f"Tool Name: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input Schema: {tool.inputSchema}")
                print("-" * 40)

            # Call greet_user if available
            if any(tool.name == "greet_user" for tool in tool_list.tools):
                name = "odai"
                response = await session.call_tool("greet_user", {"name": name})
                print("Tool Response:", response)
            else:
                print("Tool 'greet_user' not found on server.")


if __name__ == "__main__":
    asyncio.run(main())
