"""
Tool executor for dispatching LLM tool calls to the sandboxed workspace.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from portfolio_agent.sandbox.workspace import Workspace, get_default_workspace


class ToolExecutor:
    """Dispatches and runs sandboxed file operations requested by the agent."""

    def __init__(self, workspace: Optional[Workspace] = None):
        self.workspace = workspace or get_default_workspace()

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute the specified tool with arguments and return output string.
        """
        try:
            if tool_name == "create_directory":
                path = str(arguments.get("path", "")).strip()
                if not path:
                    return "Failed to create directory: 'path' argument is required"
                return self.workspace.create_directory(path)

            elif tool_name == "write_file":
                path = str(arguments.get("path", "")).strip()
                content = arguments.get("content", "")
                if not path:
                    return "Failed to write file: 'path' argument is required"
                return self.workspace.write_file(path, content)

            elif tool_name == "read_file":
                path = str(arguments.get("path", "")).strip()
                if not path:
                    return "Failed to read file: 'path' argument is required"
                return self.workspace.read_file(path)

            elif tool_name == "list_files":
                path = str(arguments.get("path", "")).strip()
                return self.workspace.list_files(path)

            else:
                return f"Error: Unknown tool '{tool_name}'."

        except Exception as error:
            return f"Execution error in tool '{tool_name}': {error}"

    def execute_raw(self, tool_name: str, arguments_json: str) -> str:
        """
        Execute tool call from raw JSON string arguments as passed by LLM APIs.
        """
        try:
            if arguments_json and arguments_json.strip():
                args = json.loads(arguments_json)
            else:
                args = {}
        except json.JSONDecodeError as err:
            return f"Error parsing tool arguments as JSON: {err}"

        return self.execute(tool_name, args)
