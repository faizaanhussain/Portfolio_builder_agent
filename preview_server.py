#!/usr/bin/env python3
"""
Lightweight local HTTP preview server for generated websites.
Uses Python's standard http.server with CORS and auto-browser opening.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path


def serve_directory(
    directory: Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
) -> None:
    """Serve a local directory over HTTP and optionally open the browser."""
    directory = Path(directory).resolve()
    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory does not exist: {directory}", file=sys.stderr)
        return

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(directory),
    )

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer((host, port), handler) as httpd:
            url = f"http://{host}:{port}"
            print("\n" + "=" * 60)
            print(f"  🚀 Portfolio Live Preview Server Running")
            print(f"  📁 Serving Directory: {directory}")
            print(f"  🔗 Local URL:        {url}")
            print("  Press Ctrl+C to stop the server")
            print("=" * 60 + "\n")

            if open_browser:
                # Open browser slightly after starting
                threading.Timer(0.8, lambda: webbrowser.open(url)).start()

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nPreview server stopped.")
    except OSError as err:
        print(f"Failed to start server on {host}:{port}: {err}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Serve and preview a generated website locally."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="./generated_sites/sample_portfolio",
        help="Directory to serve (default: ./generated_sites/sample_portfolio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to serve on (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the browser automatically",
    )

    args = parser.parse_args()
    target_dir = Path(args.dir)

    serve_directory(
        directory=target_dir,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
