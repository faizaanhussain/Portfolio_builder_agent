"""
Tool schema definitions for OpenAI-compatible function calling.
"""

from __future__ import annotations

from typing import Any, Dict, List


def tool(name: str, description: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construct an OpenAI-compatible function tool schema.
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties.keys()),
            },
        },
    }


def get_available_tools() -> List[Dict[str, Any]]:
    """Return the list of all tools available to the website developer agent."""
    return [
        tool(
            name="create_directory",
            description="Create a new directory inside the sandboxed website workspace.",
            properties={
                "path": {
                    "type": "string",
                    "description": "Relative directory path to create inside the workspace (e.g. 'my_portfolio')",
                }
            },
        ),
        tool(
            name="write_file",
            description="Write text content into a file inside the sandboxed workspace. Automatically creates parent directories.",
            properties={
                "path": {
                    "type": "string",
                    "description": "Relative file path inside the workspace to write to (e.g. 'my_portfolio/index.html')",
                },
                "content": {
                    "type": "string",
                    "description": "The exact full text content to write into the file",
                },
            },
        ),
        tool(
            name="read_file",
            description="Read and inspect the text content of an existing file inside the sandboxed workspace.",
            properties={
                "path": {
                    "type": "string",
                    "description": "Relative file path inside the workspace to read from (e.g. 'my_portfolio/index.html')",
                }
            },
        ),
        tool(
            name="list_files",
            description="List all files and subdirectories recursively inside a directory path within the workspace.",
            properties={
                "path": {
                    "type": "string",
                    "description": "Relative directory path to list files from (e.g. 'my_portfolio' or '' for workspace root)",
                }
            },
        ),
    ]
