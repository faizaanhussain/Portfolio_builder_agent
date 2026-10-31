"""
Sandboxed workspace implementation for safe website file system operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from portfolio_agent.sandbox.security import validate_safe_path


class Workspace:
    """
    Manages an isolated directory sandbox for generated websites.
    Ensures that all file operations remain strictly contained.
    """

    def __init__(self, workspace_path: Union[str, Path] = "generated_sites"):
        self.website_workspace: Path = Path(workspace_path).resolve()
        self.website_workspace.mkdir(parents=True, exist_ok=True)

    def safe_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Validate and resolve relative_path inside this workspace.
        Raises ValueError if the path attempts to escape the workspace.
        """
        return validate_safe_path(relative_path, self.website_workspace)

    def create_directory(self, path: str) -> str:
        """Create a directory inside the workspace."""
        try:
            target = self.safe_path(path)
            target.mkdir(parents=True, exist_ok=True)
            return f"Directory created successfully: {path}"
        except (OSError, ValueError) as error:
            return f"Failed to create directory: {error}"

    def write_file(self, path: str, content: str) -> str:
        """Write text content to a file inside the workspace."""
        try:
            file = self.safe_path(path)
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content, encoding="utf-8")
            return f"File written successfully: {path}"
        except (OSError, ValueError) as error:
            return f"Failed to write file: {error}"

    def read_file(self, path: str) -> str:
        """Read text content from a file inside the workspace."""
        try:
            file = self.safe_path(path)
            if not file.exists():
                return f"Failed to read file: File does not exist: {path}"
            return file.read_text(encoding="utf-8")
        except (OSError, ValueError) as error:
            return f"Failed to read file: {error}"

    def list_files(self, path: str = "") -> str:
        """
        List all files inside the given directory path relative to the workspace.
        Pass empty string or '.' to list the entire workspace.
        """
        try:
            target_path = path if path else "."
            directory = self.safe_path(target_path)
            if not directory.exists():
                return f"Directory does not exist: {path}"
            if not directory.is_dir():
                return f"Path is not a directory: {path}"

            items: List[str] = [
                str(item.relative_to(self.website_workspace)).replace("\\", "/")
                for item in sorted(directory.rglob("*"))
            ]
            if not items:
                return "Directory is empty."
            return "\n".join(items)
        except (OSError, ValueError) as error:
            return f"Failed to list files: {error}"

    def get_site_files(self, site_name: str) -> List[Path]:
        """Return list of existing files for a specific site."""
        site_dir = self.safe_path(site_name)
        if not site_dir.exists() or not site_dir.is_dir():
            return []
        return [f for f in site_dir.rglob("*") if f.is_file()]


# Global default workspace instance
_default_workspace: Optional[Workspace] = None


def get_default_workspace() -> Workspace:
    """Retrieve or initialize the global default workspace."""
    global _default_workspace
    if _default_workspace is None:
        _default_workspace = Workspace("generated_sites")
    return _default_workspace


def set_default_workspace(workspace: Workspace) -> None:
    """Set the global default workspace."""
    global _default_workspace
    _default_workspace = workspace


# Module-level functions matching user's exact signatures
def safe_path(relative_path: Union[str, Path]) -> Path:
    return get_default_workspace().safe_path(relative_path)


def create_directory(path: str) -> str:
    return get_default_workspace().create_directory(path)


def write_file(path: str, content: str) -> str:
    return get_default_workspace().write_file(path, content)


def read_file(path: str) -> str:
    return get_default_workspace().read_file(path)


def list_files(path: str) -> str:
    return get_default_workspace().list_files(path)
