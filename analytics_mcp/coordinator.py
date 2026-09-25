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
The singleton allows other modules to register their tools with the same MCP server.
"""

# MCP Server Imports
import json
import sys
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


def sanitize_mcp_schema(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return schema

    cleaned = {}

    # Collapse anyOf / oneOf unions containing 'null'
    raw_any_of = schema.get("anyOf") or schema.get("oneOf")
    if isinstance(raw_any_of, list):
        non_nulls = [
            item
            for item in raw_any_of
            if isinstance(item, dict) and item.get("type") != "null"
        ]
        if len(non_nulls) == 1:
            collapsed = sanitize_mcp_schema(non_nulls[0])
            for k, v in collapsed.items():
                cleaned[k] = v

    for key, value in schema.items():
        if key in ("anyOf", "oneOf"):
            if "type" in cleaned:
                continue
            non_nulls = [
                item
                for item in value
                if isinstance(item, dict) and item.get("type") != "null"
            ]
            if len(non_nulls) == 1:
                collapsed = sanitize_mcp_schema(non_nulls[0])
                for k, v in collapsed.items():
                    if k not in cleaned:
                        cleaned[k] = v
            else:
                cleaned[key] = [
                    sanitize_mcp_schema(item) if isinstance(item, dict) else item
                    for item in non_nulls
                ]
        elif key == "additionalProperties":
            cleaned[key] = value if isinstance(value, bool) else False
        elif key == "default" and value is None:
            continue
        elif isinstance(value, dict):
            cleaned[key] = sanitize_mcp_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [
                sanitize_mcp_schema(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            if key not in cleaned or value is not None:
                cleaned[key] = value

    if cleaned.get("type") == "object" and "properties" in cleaned:
        if "required" not in cleaned or not isinstance(cleaned["required"], list):
            cleaned["required"] = []

    return cleaned

# 1. Register tools with FastMCP
for tool_name, adk_tool in tool_map.items():
    app.add_tool(adk_tool.func, name=tool_name, description=adk_tool.description)

# 2. Sanitize parameter schemas directly on registered FastMCP tools
for tool in app._tool_manager._tools.values():
    if hasattr(tool, "parameters") and isinstance(tool.parameters, dict):
        tool.parameters = sanitize_mcp_schema(tool.parameters)
    elif hasattr(tool, "inputSchema") and isinstance(tool.inputSchema, dict):
        tool.inputSchema = sanitize_mcp_schema(tool.inputSchema)
