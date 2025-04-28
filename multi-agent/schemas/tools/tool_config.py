from pydantic import BaseModel, HttpUrl
from typing import Literal, Optional, Dict


class CalculatorConfig(BaseModel):
    """
    Configuration for a simple arithmetic calculator tool.
    """
    name: str
    type: Literal["calculator"]


class WeatherConfig(BaseModel):
    """
    Configuration for a mock weather data tool.
    """
    name: str
    type: Literal["weather"]


class HTTPToolConfig(BaseModel):
    """
    Configuration for an HTTP-based tool adapter.
    """
    name: str
    type: Literal["http_tool"]
    url: HttpUrl
    headers: Optional[Dict[str, str]] = {}


class MCPToolConfig(BaseModel):
    """
    Configuration for an MCP (multi-call protocol) tool adapter.
    """
    name: str
    type: Literal["mcp"]
    function: str  # Identifier of the MCP function/task
    endpoint: HttpUrl  # MCP server endpoint
    headers: Optional[Dict[str, str]] = {}


class WebSearchConfig(BaseModel):
    """
    Configuration for an external web-search tool.
    """
    name: str
    type: Literal["web_search"]
    endpoint: HttpUrl
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = {}
