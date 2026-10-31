"""
Security and path validation utilities for sandboxing file operations.
Prevents directory traversal, unauthorized file system access, and symlink exploits.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

# Default fallback workspace name
DEFAULT_WORKSPACE_NAME = "generated_sites"


def validate_safe_path(
    relative_path: Union[str, Path],
    workspace_dir: Path,
) -> Path:
    """
    Safely resolve a path relative to workspace_dir and enforce that
    it cannot escape the workspace directory.

    Raises ValueError("Access outside generated-sites is not allowed")
    if the resolved path is outside the workspace.
    """
    clean_path_str = str(relative_path).strip()

    # Normalize leading slashes/backslashes so relative paths like "/site/index.html"
    # are treated as relative inside the workspace rather than root-relative
    clean_path_str = clean_path_str.lstrip("/\\")

    workspace_resolved = Path(workspace_dir).resolve()
    resolved = (workspace_resolved / clean_path_str).resolve()

    # Enforce containment: resolved path must be the workspace or a descendant
    if resolved != workspace_resolved and workspace_resolved not in resolved.parents:
        raise ValueError("Access outside generated-sites is not allowed")

    return resolved


def safe_path(
    relative_path: Union[str, Path],
    workspace_dir: Union[str, Path, None] = None,
) -> Path:
    """
    Resolves relative_path against workspace_dir and verifies sandbox containment.
    If workspace_dir is omitted, defaults to Path(DEFAULT_WORKSPACE_NAME).resolve().
    """
    if workspace_dir is None:
        target_workspace = Path(DEFAULT_WORKSPACE_NAME).resolve()
    else:
        target_workspace = Path(workspace_dir).resolve()

    return validate_safe_path(relative_path, target_workspace)
