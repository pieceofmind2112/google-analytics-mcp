# Copyright 2025 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module declaring the singleton MCP server.

The singleton allows other modules to register their tools with the same MCP
server.
"""

# MCP Server Imports
import json
import sys
from json import tool
from mcp import types as mcp_types  # Use alias to avoid conflict
from mcp.server.fastmcp import FastMCP

# ADK Tool Imports
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

from analytics_mcp.tools.admin.info import (
    get_account_summaries,
    list_google_ads_links,
    get_property_details,
    list_property_annotations,
)
from analytics_mcp.tools.reporting.core import (
    run_report,
    _run_report_description,
)
from analytics_mcp.tools.reporting.realtime import (
    run_realtime_report,
    _run_realtime_report_description,
)
from analytics_mcp.tools.reporting.metadata import (
    get_custom_dimensions_and_metrics,
)
from analytics_mcp.tools.reporting.funnel import (
    run_funnel_report,
    _run_funnel_report_description,
)
from analytics_mcp.tools.reporting.conversions import (
    run_conversions_report,
    _run_conversions_report_description,
)

run_report_with_description = FunctionTool(run_report)
run_report_with_description.description = _run_report_description()
run_realtime_report_with_description = FunctionTool(run_realtime_report)
run_realtime_report_with_description.description = (
    _run_realtime_report_description()
)
run_funnel_report_with_description = FunctionTool(run_funnel_report)
run_funnel_report_with_description.description = (
    _run_funnel_report_description()
)
run_conversions_report_with_description = FunctionTool(run_conversions_report)
run_conversions_report_with_description.description = (
    _run_conversions_report_description()
)

# Instantiate the ADK tools
tools = [
    FunctionTool(get_account_summaries),
    FunctionTool(list_google_ads_links),
    FunctionTool(get_property_details),
    FunctionTool(list_property_annotations),
    FunctionTool(get_custom_dimensions_and_metrics),
    run_report_with_description,
    run_realtime_report_with_description,
    run_funnel_report_with_description,
    run_conversions_report_with_description,
]

tool_map = {t.name: t for t in tools}

app = FastMCP("Google Analytics MCP Server")

def sanitize_mcp_schema_properties(node: dict) -> None:
    """Ensure additionalProperties is a boolean value to satisfy certain MCP clients."""
    if not isinstance(node, dict):
        return
    if "additionalProperties" in node:
        val = node["additionalProperties"]
        if not isinstance(val, bool):
            node["additionalProperties"] = True
    for key, child in node.items():
        if isinstance(child, dict):
            sanitize_mcp_schema_properties(child)
        elif isinstance(child, list):
            for element in child:
                if isinstance(element, dict):
                    sanitize_mcp_schema_properties(element)

# 1. Register each ADK tool with FastMCP
for tool_name, adk_tool in tool_map.items():
    app.add_tool(adk_tool.func, name=tool_name, description=adk_tool.description)

# 2. Override to_mcp_tool on each registered tool so FastMCP outputs the cleaned schema
for tool_name, tool in app._tool_manager._tools.items():
    # Copy raw schema dictionary from FastMCP
    raw_schema = dict(tool.parameters)

    if not raw_schema or raw_schema == {}:
        raw_schema = {"type": "object", "properties": {}}

    # Strip out anyOf / null types that break Gemini Enterprise schema parsing
    props = raw_schema.get("properties", {})
    for prop_name, prop in list(props.items()):
        if isinstance(prop, dict) and "anyOf" in prop:
            valid_types = [t.get("type") for t in prop["anyOf"] if isinstance(t, dict) and t.get("type") != "null"]
            if valid_types:
                prop["type"] = valid_types[0]
            del prop["anyOf"]

    # Ensure additionalProperties is a boolean
    sanitize_mcp_schema_properties(raw_schema)

    # Set explicit required fields for GA reporting tools
    if tool_name == "run_report":
        raw_schema["required"] = ["property_id", "date_ranges", "dimensions", "metrics"]
    elif tool_name == "run_realtime_report":
        raw_schema["required"] = ["property_id", "dimensions", "metrics"]
    elif tool_name == "run_conversions_report":
        raw_schema["required"] = ["property_id", "date_ranges", "dimensions", "metrics", "conversion_spec"]

    # Override tool output method directly
    def make_to_mcp(t_name, t_desc, clean_schema):
        def to_mcp_tool():
            return mcp_types.Tool(
                name=t_name,
                description=t_desc,
                inputSchema=clean_schema
            )
        return to_mcp_tool

    tool.to_mcp_tool = make_to_mcp(tool.name, tool.description or "", raw_schema)
