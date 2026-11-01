"""
High-performance HTTP server for Portfolio Agent Web Studio.
Serves the responsive single-page web UI, REST APIs, SSE event streams,
and dynamically hosts all generated portfolio websites locally.
"""

from __future__ import annotations

import functools
import http.server
import io
import json
import mimetypes
import os
import queue
import shutil
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from portfolio_agent.config import Config, get_config
from portfolio_agent.prompts import build_portfolio_prompt
from portfolio_agent.sandbox.security import validate_safe_path
from portfolio_agent.sandbox.workspace import Workspace
from portfolio_agent.web.runner import (
    JobManager,
    _sanitize_directory_name,
    extract_portfolio_info_from_prompt,
    get_default_job_manager,
    get_default_user_name,
)

STATIC_DIR = Path(__file__).parent / "static"


class StudioRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Handles Studio UI assets, REST API endpoints,
    live SSE agent event streaming, and local hosting of generated websites.
    """

    server_version = "PortfolioAgentStudio/1.0"

    def __init__(self, *args: Any, workspace: Workspace, job_manager: JobManager, config: Config, **kwargs: Any):
        self.workspace = workspace
        self.job_manager = job_manager
        self.config = config
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Silence standard console access log clutter for clean terminal."""
        pass

    # ---------------------------------------------------------
    # Response Utilities
    # ---------------------------------------------------------
    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def send_error_json(self, message: str, status: int = 400) -> None:
        self.send_json({"error": message, "success": False}, status=status)

    def read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body) if body.strip() else {}

    # ---------------------------------------------------------
    # Router
    # ---------------------------------------------------------
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API Endpoints
        if path == "/api/config":
            self.handle_get_config()
            return
        if path == "/api/models":
            self.handle_get_models()
            return
        if path == "/api/sites":
            self.handle_get_sites()
            return
        if path.startswith("/api/jobs/"):
            parts = path.strip("/").split("/")
            if len(parts) == 3:
                self.handle_get_job(parts[2])
                return
            if len(parts) == 4 and parts[3] == "events":
                self.handle_stream_job_events(parts[2])
                return
        if path.startswith("/api/sites/"):
            parts = path.strip("/").split("/")
            site_id = parts[2]
            if len(parts) == 4 and parts[3] == "files":
                self.handle_get_site_files(site_id)
                return
            if len(parts) == 4 and parts[3] == "file":
                self.handle_get_site_file_content(site_id, query)
                return
            if len(parts) == 4 and parts[3] == "download":
                self.handle_download_site_zip(site_id)
                return

        # 2. Local Hosting of Generated Websites (/preview/<site_id>/...)
        if path.startswith("/preview/"):
            self.handle_serve_preview(path[len("/preview/") :])
            return

        # 3. Static UI Assets
        self.handle_serve_static(path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/generate":
            self.handle_post_generate()
            return
        if path.startswith("/api/sites/"):
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[3] == "file":
                self.handle_post_site_file_update(parts[2])
                return

        self.send_error_json(f"Endpoint not found: {path}", status=404)

    def do_DELETE(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/sites/"):
            parts = path.strip("/").split("/")
            if len(parts) == 3:
                self.handle_delete_site(parts[2])
                return

        self.send_error_json(f"Endpoint not found: {path}", status=404)

    # ---------------------------------------------------------
    # API Handlers
    # ---------------------------------------------------------
    def handle_get_models(self) -> None:
        """Fetch available models live from provider."""
        try:
            from openai import OpenAI

            api_key = self.config.api_key
            base_url = self.config.base_url
            if api_key and api_key.startswith("gsk_") and (not base_url or "api.openai.com" in str(base_url)):
                base_url = "https://api.groq.com/openai/v1"
            elif api_key and api_key.startswith("sk-or-") and (not base_url or "api.openai.com" in str(base_url)):
                base_url = "https://openrouter.ai/api/v1"

            if not api_key:
                self.send_json({"models": ["meta-llama/llama-3.3-70b-instruct:free", "gpt-4o-mini"]})
                return

            client_kwargs = {"api_key": api_key, "base_url": base_url}
            if base_url and "openrouter.ai" in str(base_url):
                client_kwargs["default_headers"] = {
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "FolioPilot",
                }

            client = OpenAI(**client_kwargs)
            model_items = client.models.list()
            all_ids = [m.id for m in model_items.data if getattr(m, "id", None)]
            free_models = [mid for mid in all_ids if ":free" in mid]
            models = sorted(free_models or all_ids)
            self.send_json({"models": models, "provider": base_url or "openai"})
        except Exception as err:
            self.send_error_json(str(err), status=500)

    def handle_get_config(self) -> None:
        """Return server capability, workspace paths, and LLM configuration."""
        data = {
            "has_api_key": bool(self.config.api_key),
            "model": self.config.model,
            "base_url": self.config.base_url,
            "default_name": get_default_user_name(),
            "default_title": "Full-Stack AI Engineer",
            "workspace_dir": str(self.workspace.website_workspace),
            "preview_port": self.config.preview_port,
            "available_models": [
                "llama-3.1-8b-instant",
                "llama-3.3-70b-versatile",
                "llama3-70b-8192",
                "gpt-4o-mini",
                "gpt-4o",
                "deepseek-chat",
            ],
            "themes": [
                {"id": "clean-light", "name": "Modern Clean Light", "accent": "#2563eb"},
                {"id": "minimal-mono", "name": "Monochrome Slate", "accent": "#0f172a"},
                {"id": "indigo-light", "name": "Indigo Studio", "accent": "#4f46e5"},
                {"id": "glass-dark", "name": "Dark Mode", "accent": "#38bdf8"},
            ],
        }
        self.send_json(data)

    def handle_post_generate(self) -> None:
        """Trigger an autonomous agent run or mock simulation in the background."""
        try:
            body = self.read_json_body()
        except Exception as err:
            self.send_error_json(f"Invalid JSON payload: {err}", status=400)
            return

        mode = body.get("mode", "prompt")  # 'prompt' or 'wizard'
        is_mock = bool(body.get("mock", False))
        wizard_data = body.get("wizard_data") or {}
        raw_prompt = body.get("prompt", "").strip()

        # 1. Resolve user name and professional title
        prompt_info = extract_portfolio_info_from_prompt(raw_prompt)
        default_sys_name = get_default_user_name()

        user_name = (
            body.get("name")
            or wizard_data.get("name")
            or prompt_info.get("name")
            or default_sys_name
        )
        user_title = (
            body.get("title")
            or wizard_data.get("title")
            or prompt_info.get("title")
            or "Full-Stack AI Engineer"
        )
        wizard_data["name"] = user_name
        wizard_data["title"] = user_title

        # 2. Determine site directory name
        dir_name = body.get("dir_name") or wizard_data.get("directory_name")
        if not dir_name:
            dir_name = _sanitize_directory_name(f"{user_name.lower().replace(' ', '_')}_portfolio")
        else:
            dir_name = _sanitize_directory_name(dir_name)
        wizard_data["directory_name"] = dir_name

        # 3. Build final prompt
        if mode == "wizard" or (not raw_prompt and wizard_data):
            final_prompt = build_portfolio_prompt(
                name=user_name,
                title=user_title,
                bio=wizard_data.get("bio"),
                skills=wizard_data.get("skills"),
                projects=wizard_data.get("projects"),
                contact_email=wizard_data.get("contact_email"),
                github=wizard_data.get("github"),
                linkedin=wizard_data.get("linkedin"),
                theme=wizard_data.get("theme") or "Modern Clean Light Minimalist",
                directory_name=dir_name,
                extra_instructions=wizard_data.get("extra_instructions"),
            )
        else:
            # If prompt provided, make sure user name and title are appended if missing
            if user_name and user_name.lower() not in raw_prompt.lower():
                final_prompt = f"Portfolio for {user_name} ({user_title}):\n{raw_prompt}"
            else:
                final_prompt = raw_prompt or build_portfolio_prompt(
                    name=user_name, title=user_title, directory_name=dir_name
                )

        # 3. Create job-specific config override if provided
        api_key_val = body.get("api_key") or self.config.api_key
        base_url_val = body.get("base_url") or self.config.base_url
        model_val = body.get("model") or self.config.model

        # Auto-route Groq / OpenRouter keys or models to their proper endpoints
        if api_key_val and api_key_val.startswith("gsk_"):
            if not base_url_val or "api.openai.com" in str(base_url_val):
                base_url_val = "https://api.groq.com/openai/v1"
        elif api_key_val and api_key_val.startswith("sk-or-"):
            if not base_url_val or "api.openai.com" in str(base_url_val):
                base_url_val = "https://openrouter.ai/api/v1"
        elif model_val and (":free" in model_val or "/" in model_val):
            if not base_url_val or "api.openai.com" in str(base_url_val):
                base_url_val = "https://openrouter.ai/api/v1"
        elif model_val and (model_val.startswith("llama-") or model_val.startswith("llama3")):
            if not base_url_val or "api.openai.com" in str(base_url_val):
                base_url_val = "https://api.groq.com/openai/v1"

        job_config = Config(
            api_key=api_key_val,
            base_url=base_url_val,
            model=model_val,
            workspace_dir=self.workspace.website_workspace,
            max_turns=int(body.get("max_turns", self.config.max_turns)),
            temperature=float(body.get("temperature", self.config.temperature)),
        )

        # 4. Auto-fallback to mock mode if no API key is available
        if not is_mock and not job_config.api_key:
            is_mock = True

        # 5. Create and start background job
        job = self.job_manager.create_job(
            prompt=final_prompt,
            site_dir=dir_name,
            is_mock=is_mock,
            meta={"mode": mode, "wizard_data": wizard_data, "model": job_config.model},
        )
        self.job_manager.start_job(job.id, config=job_config, wizard_data=wizard_data)

        self.send_json(
            {
                "success": True,
                "job_id": job.id,
                "site_dir": job.site_dir,
                "status": job.status,
                "is_mock": is_mock,
                "preview_url": f"/preview/{job.site_dir}/",
            },
            status=202,
        )

    def handle_get_job(self, job_id: str) -> None:
        """Fetch status and event history for a job."""
        job = self.job_manager.get_job(job_id)
        if not job:
            self.send_error_json(f"Job not found: {job_id}", status=404)
            return
        self.send_json(job.to_dict())

    def handle_stream_job_events(self, job_id: str) -> None:
        """Stream real-time agent turns and tool execution logs over SSE."""
        job = self.job_manager.get_job(job_id)
        if not job:
            self.send_error_json(f"Job not found: {job_id}", status=404)
            return

        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        # Send all pre-existing events first
        for ev in list(job.events):
            msg = f"data: {json.dumps(ev)}\n\n"
            try:
                self.wfile.write(msg.encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError):
                return
        self.wfile.flush()

        # If job is already complete, terminate stream immediately
        if job.status in ("completed", "failed"):
            try:
                self.wfile.write(b"data: {\"type\": \"stream_close\"}\n\n")
                self.wfile.flush()
            except Exception:
                pass
            return

        # Stream new events from the queue until Sentinel (None)
        while True:
            try:
                event = job.event_queue.get(timeout=20)
                if event is None:
                    # Stream complete
                    self.wfile.write(b"data: {\"type\": \"stream_close\"}\n\n")
                    self.wfile.flush()
                    break

                msg = f"data: {json.dumps(event)}\n\n"
                self.wfile.write(msg.encode("utf-8"))
                self.wfile.flush()
            except queue.Empty:
                # Send heartbeat keepalive
                try:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                except Exception:
                    break
            except (BrokenPipeError, ConnectionResetError):
                break

    def handle_get_sites(self) -> None:
        """List all generated websites in the sandbox sorted by latest modification."""
        sites: List[Dict[str, Any]] = []
        workspace_dir = self.workspace.website_workspace

        def get_site_mtime(p: Path) -> float:
            times = [p.stat().st_mtime]
            try:
                for f in p.rglob("*"):
                    if f.is_file():
                        times.append(f.stat().st_mtime)
            except OSError:
                pass
            return max(times)

        if workspace_dir.exists():
            for child in sorted(workspace_dir.iterdir(), key=get_site_mtime, reverse=True):
                if child.is_dir() and not child.name.startswith("."):
                    files = [
                        str(f.relative_to(child)).replace("\\", "/")
                        for f in child.rglob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                    has_index = "index.html" in files
                    has_css = "style.css" in files
                    has_js = "script.js" in files
                    mtime_val = get_site_mtime(child)

                    sites.append(
                        {
                            "id": child.name,
                            "name": child.name.replace("_", " ").title(),
                            "dir_name": child.name,
                            "files_count": len(files),
                            "has_index": has_index,
                            "has_css": has_css,
                            "has_js": has_js,
                            "preview_url": f"/preview/{child.name}/",
                            "mtime": mtime_val,
                        }
                    )

        self.send_json({"sites": sites, "count": len(sites)})

    def handle_get_site_files(self, site_id: str) -> None:
        """List files for a specific site with sizes."""
        try:
            site_dir = self.workspace.safe_path(site_id)
        except ValueError as err:
            self.send_error_json(str(err), status=403)
            return

        if not site_dir.exists() or not site_dir.is_dir():
            self.send_error_json(f"Site '{site_id}' not found", status=404)
            return

        files = []
        for f in sorted(site_dir.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                rel_path = str(f.relative_to(site_dir)).replace("\\", "/")
                files.append(
                    {
                        "path": rel_path,
                        "size": f.stat().st_size,
                        "mtime": f.stat().st_mtime,
                    }
                )
        self.send_json({"site_id": site_id, "files": files})

    def handle_get_site_file_content(self, site_id: str, query: Dict[str, List[str]]) -> None:
        """Retrieve source code of a generated file (e.g. index.html)."""
        file_path = query.get("path", ["index.html"])[0]
        try:
            full_path = self.workspace.safe_path(f"{site_id}/{file_path}")
        except ValueError as err:
            self.send_error_json(str(err), status=403)
            return

        if not full_path.exists() or not full_path.is_file():
            self.send_error_json(f"File not found: {file_path}", status=404)
            return

        content = self.workspace.read_file(f"{site_id}/{file_path}")
        self.send_json({"site_id": site_id, "path": file_path, "content": content})

    def handle_post_site_file_update(self, site_id: str) -> None:
        """Save edited content of a file directly from the Web Inspector."""
        body = self.read_json_body()
        file_path = body.get("path")
        content = body.get("content")

        if not file_path or content is None:
            self.send_error_json("Both 'path' and 'content' are required.", status=400)
            return

        target_str = f"{site_id}/{file_path}"
        result = self.workspace.write_file(target_str, content)
        if "successfully" in result:
            self.send_json({"success": True, "message": result})
        else:
            self.send_error_json(result, status=500)

    def handle_download_site_zip(self, site_id: str) -> None:
        """Bundle the generated website directory into a ZIP archive for export."""
        try:
            site_dir = self.workspace.safe_path(site_id)
        except ValueError as err:
            self.send_error_json(str(err), status=403)
            return

        if not site_dir.exists() or not site_dir.is_dir():
            self.send_error_json(f"Site '{site_id}' not found", status=404)
            return

        mem_file = io.BytesIO()
        with zipfile.ZipFile(mem_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(site_dir):
                for f in files:
                    file_full = Path(root) / f
                    arcname = str(file_full.relative_to(site_dir)).replace("\\", "/")
                    zf.write(file_full, arcname=arcname)

        zip_bytes = mem_file.getvalue()
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{site_id}.zip"')
        self.send_header("Content-Length", str(len(zip_bytes)))
        self.end_headers()
        self.wfile.write(zip_bytes)

    def handle_delete_site(self, site_id: str) -> None:
        """Delete a generated site from the workspace."""
        try:
            site_dir = self.workspace.safe_path(site_id)
        except ValueError as err:
            self.send_error_json(str(err), status=403)
            return

        if not site_dir.exists():
            self.send_error_json(f"Site '{site_id}' does not exist", status=404)
            return

        try:
            shutil.rmtree(site_dir)
            self.send_json({"success": True, "message": f"Deleted site '{site_id}'."})
        except OSError as err:
            self.send_error_json(f"Failed to delete site: {err}", status=500)

    # ---------------------------------------------------------
    # Hosting & Preview Serving (/preview/<site_id>/...)
    # ---------------------------------------------------------
    def handle_serve_preview(self, rel_path: str) -> None:
        """
        Dynamically host any generated website locally with strict sandboxing.
        Maps /preview/<site_id>/ to generated_sites/<site_id>/index.html
        """
        rel_path = urllib.parse.unquote(rel_path.lstrip("/"))
        if not rel_path:
            self.send_error_json("Site ID required in preview URL", status=400)
            return

        parts = rel_path.split("/", 1)
        site_id = parts[0]
        subpath = parts[1] if len(parts) > 1 else ""

        # Auto-redirect directory root to slash so relative links resolve correctly
        if not subpath and not self.path.endswith("/"):
            self.send_response(301)
            self.send_header("Location", f"{self.path}/")
            self.end_headers()
            return

        target_rel = f"{site_id}/{subpath}" if subpath else f"{site_id}/index.html"
        try:
            target_file = self.workspace.safe_path(target_rel)
            if target_file.is_dir():
                target_file = target_file / "index.html"
        except ValueError as err:
            self.send_error_json(f"Access forbidden: {err}", status=403)
            return

        if not target_file.exists() or not target_file.is_file():
            self.send_error_json(f"Resource not found: {target_rel}", status=404)
            return

        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "text/html" if target_file.suffix == ".html" else "application/octet-stream"

        try:
            content_bytes = target_file.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if mime_type.startswith("text/") else mime_type)
            self.send_header("Content-Length", str(len(content_bytes)))
            self.send_header("Cache-Control", "no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(content_bytes)
        except OSError as err:
            self.send_error_json(f"Read error: {err}", status=500)

    # ---------------------------------------------------------
    # Static Assets Serving
    # ---------------------------------------------------------
    def handle_serve_static(self, path: str) -> None:
        """Serve the Studio front-end assets."""
        if path in ("/", "/index.html"):
            target_file = STATIC_DIR / "index.html"
        elif path.startswith("/static/"):
            clean_sub = path[len("/static/") :].lstrip("/")
            target_file = (STATIC_DIR / clean_sub).resolve()
            # Enforce that static serving cannot escape STATIC_DIR
            try:
                target_file.relative_to(STATIC_DIR.resolve())
            except ValueError:
                self.send_error_json("Forbidden", status=403)
                return
        else:
            target_file = (STATIC_DIR / path.lstrip("/")).resolve()

        if not target_file.exists() or not target_file.is_file():
            # Fallback to index.html for SPA-style routing
            target_file = STATIC_DIR / "index.html"

        if not target_file.exists():
            self.send_error_json("Studio interface files not found.", status=404)
            return

        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "text/html" if target_file.suffix == ".html" else "application/octet-stream"

        try:
            content_bytes = target_file.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if mime_type.startswith("text/") else mime_type)
            self.send_header("Content-Length", str(len(content_bytes)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content_bytes)
        except OSError as err:
            self.send_error_json(f"Error serving asset: {err}", status=500)


def create_studio_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    workspace: Optional[Workspace] = None,
    job_manager: Optional[JobManager] = None,
    config: Optional[Config] = None,
) -> socketserver.TCPServer:
    """Instantiate a multi-threaded HTTP server for Portfolio Agent Studio."""
    active_config = config or get_config()
    active_workspace = workspace or Workspace(active_config.workspace_dir)
    active_job_manager = job_manager or get_default_job_manager()

    handler_factory = functools.partial(
        StudioRequestHandler,
        workspace=active_workspace,
        job_manager=active_job_manager,
        config=active_config,
    )

    socketserver.TCPServer.allow_reuse_address = True
    return socketserver.ThreadingTCPServer((host, port), handler_factory)


def start_web_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
    workspace: Optional[Workspace] = None,
    config: Optional[Config] = None,
) -> None:
    """Start the Portfolio Agent Web Studio server and optionally open the browser."""
    active_config = config or get_config()
    active_workspace = workspace or Workspace(active_config.workspace_dir)
    active_job_manager = get_default_job_manager()

    try:
        httpd = create_studio_server(
            host=host,
            port=port,
            workspace=active_workspace,
            job_manager=active_job_manager,
            config=active_config,
        )
    except OSError as err:
        print(f"\n❌ Error starting web server on {host}:{port}: {err}", file=sys.stderr)
        return

    provider_info = ""
    if active_config.api_key:
        try:
            from openai import OpenAI
            c_base = active_config.base_url
            if active_config.api_key.startswith("gsk_") and (not c_base or "api.openai.com" in str(c_base)):
                c_base = "https://api.groq.com/openai/v1"
            elif active_config.api_key.startswith("sk-or-") and (not c_base or "api.openai.com" in str(c_base)):
                c_base = "https://openrouter.ai/api/v1"

            client_kwargs = {"api_key": active_config.api_key, "base_url": c_base}
            if c_base and "openrouter.ai" in str(c_base):
                client_kwargs["default_headers"] = {
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "FolioPilot",
                }

            c = OpenAI(**client_kwargs)
            live_models = [m.id for m in c.models.list().data if getattr(m, "id", None)]
            free_models = [mid for mid in live_models if ":free" in mid]
            display_models = free_models or live_models
            if display_models:
                provider_info = f"\n  Active Provider Models: {', '.join(sorted(display_models)[:5])}"
        except Exception:
            pass

    url = f"http://{host}:{port}"
    print("\n" + "=" * 65)
    print(f"  FolioPilot — Autonomous Web Studio Running")
    print(f"  Studio URL:        {url}")
    print(f"  Sandboxed Sites:   {active_workspace.website_workspace}")
    print(f"  LLM Model:         {active_config.model}")
    print(f"  API Key:           {'Configured (Active)' if active_config.api_key else 'Missing (Mock Mode Available)'}{provider_info}")
    print("  Press Ctrl+C to stop the studio server.")
    print("=" * 65 + "\n")

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStudio server stopped.")
    finally:
        httpd.server_close()
