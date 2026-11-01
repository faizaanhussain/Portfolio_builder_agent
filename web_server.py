#!/usr/bin/env python3
"""
Launcher for Portfolio Agent Web Studio.
Starts the local HTTP server hosting the web frontend, REST API, SSE streaming,
and sandboxed portfolio websites.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portfolio_agent.config import get_config
from portfolio_agent.sandbox.workspace import Workspace
from portfolio_agent.web.server import start_web_server


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Portfolio Agent Web Studio: Interactive web frontend for generating and hosting portfolio websites locally."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the Web Studio server on (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the default web browser on launch",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default="./generated_sites",
        help="Path to workspace directory (default: ./generated_sites)",
    )

    args = parser.parse_args()
    config = get_config()
    config.preview_port = args.port
    config.preview_host = args.host
    workspace = Workspace(args.workspace)

    start_web_server(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        workspace=workspace,
        config=config,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
