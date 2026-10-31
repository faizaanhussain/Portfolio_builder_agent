"""
Tests for sandbox security, path validation, and isolated file system operations.
"""

import shutil
import tempfile
from pathlib import Path
import pytest

from portfolio_agent.sandbox.security import safe_path, validate_safe_path
from portfolio_agent.sandbox.workspace import Workspace


@pytest.fixture
def temp_workspace():
    """Create a temporary isolated workspace for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_sandbox_")
    workspace = Workspace(temp_dir)
    yield workspace
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestSandboxSecurity:
    """Security tests to verify sandbox containment and path traversal protection."""

    def test_safe_relative_path(self, temp_workspace):
        path = temp_workspace.safe_path("my_site/index.html")
        assert path.name == "index.html"
        assert str(path).startswith(str(temp_workspace.website_workspace))

    def test_reject_parent_traversal(self, temp_workspace):
        with pytest.raises(ValueError, match="Access outside generated-sites is not allowed"):
            temp_workspace.safe_path("../../outside.txt")

    def test_reject_nested_traversal(self, temp_workspace):
        with pytest.raises(ValueError, match="Access outside generated-sites is not allowed"):
            temp_workspace.safe_path("my_site/../../../escaped.txt")

    def test_reject_absolute_path_outside(self, temp_workspace):
        # Even if an absolute path is passed, validate_safe_path prevents escaping
        outside_path = Path(tempfile.gettempdir()).resolve().parent
        with pytest.raises(ValueError, match="Access outside generated-sites is not allowed"):
            validate_safe_path(str(outside_path), temp_workspace.website_workspace)


class TestWorkspaceOperations:
    """Functional tests for workspace file operations."""

    def test_create_directory(self, temp_workspace):
        result = temp_workspace.create_directory("test_dir/subdir")
        assert "Directory created successfully" in result
        target = temp_workspace.safe_path("test_dir/subdir")
        assert target.exists()
        assert target.is_dir()

    def test_write_and_read_file(self, temp_workspace):
        content = "<h1>Hello Portfolio Agent</h1>"
        write_res = temp_workspace.write_file("test_site/index.html", content)
        assert "File written successfully" in write_res

        read_res = temp_workspace.read_file("test_site/index.html")
        assert read_res == content

    def test_read_nonexistent_file(self, temp_workspace):
        read_res = temp_workspace.read_file("nonexistent.html")
        assert "Failed to read file" in read_res

    def test_list_files(self, temp_workspace):
        temp_workspace.write_file("site1/index.html", "<html></html>")
        temp_workspace.write_file("site1/style.css", "body {}")
        temp_workspace.write_file("site1/script.js", "console.log();")

        files_str = temp_workspace.list_files("site1")
        assert "site1/index.html" in files_str or "site1\\index.html" in files_str
        assert "site1/style.css" in files_str or "site1\\style.css" in files_str
        assert "site1/script.js" in files_str or "site1\\script.js" in files_str

    def test_traversal_returns_clean_error(self, temp_workspace):
        res = temp_workspace.write_file("../../evil.txt", "exploit")
        assert "Failed to write file" in res
        assert "Access outside generated-sites is not allowed" in res
