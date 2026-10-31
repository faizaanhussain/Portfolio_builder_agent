"""
Tests for tool definitions, schema conformity, and executor dispatching.
"""

import shutil
import tempfile
import pytest

from portfolio_agent.sandbox.workspace import Workspace
from portfolio_agent.tools.definitions import get_available_tools, tool
from portfolio_agent.tools.executor import ToolExecutor


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp(prefix="test_tools_")
    workspace = Workspace(temp_dir)
    yield workspace
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestToolDefinitions:
    """Verify tool schemas follow OpenAI function-calling standards."""

    def test_tool_factory(self):
        t = tool(
            name="test_fn",
            description="A test function",
            properties={"arg1": {"type": "string"}},
        )
        assert t["type"] == "function"
        assert t["function"]["name"] == "test_fn"
        assert t["function"]["description"] == "A test function"
        assert "arg1" in t["function"]["parameters"]["properties"]
        assert t["function"]["parameters"]["required"] == ["arg1"]

    def test_get_available_tools_contains_core_tools(self):
        tools = get_available_tools()
        tool_names = [t["function"]["name"] for t in tools]
        assert "create_directory" in tool_names
        assert "write_file" in tool_names
        assert "read_file" in tool_names
        assert "list_files" in tool_names


class TestToolExecutor:
    """Verify ToolExecutor correctly routes and executes tool calls."""

    def test_executor_create_dir_and_write(self, temp_workspace):
        executor = ToolExecutor(temp_workspace)

        # 1. create_directory
        res1 = executor.execute("create_directory", {"path": "portfolio_1"})
        assert "Directory created successfully" in res1

        # 2. write_file
        res2 = executor.execute(
            "write_file",
            {"path": "portfolio_1/index.html", "content": "<h1>Test Title</h1>"},
        )
        assert "File written successfully" in res2

        # 3. read_file
        res3 = executor.execute("read_file", {"path": "portfolio_1/index.html"})
        assert res3 == "<h1>Test Title</h1>"

        # 4. list_files
        res4 = executor.execute("list_files", {"path": "portfolio_1"})
        assert "portfolio_1/index.html" in res4

    def test_executor_raw_json(self, temp_workspace):
        executor = ToolExecutor(temp_workspace)
        raw_json = '{"path": "site_raw/style.css", "content": "body { margin: 0; }"}'
        res = executor.execute_raw("write_file", raw_json)
        assert "File written successfully" in res

    def test_executor_invalid_tool(self, temp_workspace):
        executor = ToolExecutor(temp_workspace)
        res = executor.execute("non_existent_tool", {})
        assert "Unknown tool" in res
