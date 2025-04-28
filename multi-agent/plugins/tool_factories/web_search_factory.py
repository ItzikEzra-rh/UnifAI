# # plugins/tool_factories/web_search_factory.py
#
# from typing import Any, Dict, Literal, Optional
# from pydantic import BaseModel, ValidationError, HttpUrl
# from plugins.base_factory import BaseFactory
# from plugins.exceptions import PluginConfigurationError
# from tools.web_search_tool import WebSearchTool
#
#
# class WebSearchConfig(BaseModel):
#     """
#     Configuration schema for an external web-search tool.
#     """
#     name: str
#     type: Literal["web_search"]
#     endpoint: HttpUrl              # Base URL of the search API
#     api_key: Optional[str] = None  # API key if required
#     headers: Dict[str, str] = {}   # Additional HTTP headers
#
#
# class WebSearchFactory(BaseFactory):
#     """
#     Factory for creating WebSearchTool instances from config.
#     """
#
#     def accepts(self, cfg: Dict[str, Any]) -> bool:
#         # This factory handles configs where type == "web_search"
#         return cfg.get("type") == "web_search"
#
#     def create(self, cfg: Dict[str, Any]) -> WebSearchTool:
#         # 1) Validate config against the pydantic schema
#         try:
#             data = WebSearchConfig(**cfg)
#         except ValidationError as ve:
#             raise PluginConfigurationError("Invalid web_search tool config", cfg) from ve
#
#         # 2) Instantiate the tool
#         try:
#             tool = WebSearchTool(
#                 name=data.name,
#                 endpoint=str(data.endpoint),
#                 api_key=data.api_key,
#                 headers=data.headers,
#             )
#         except Exception as e:
#             raise PluginConfigurationError(f"Failed to create WebSearchTool: {e}", cfg) from e
#
#         return tool
