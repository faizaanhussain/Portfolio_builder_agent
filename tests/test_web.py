"""
Tests for Portfolio Agent Web Studio server, JobManager, and local hosting.
"""

import io
import json
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
import pytest

from portfolio_agent.config import Config
from portfolio_agent.sandbox.workspace import Workspace
from portfolio_agent.web.runner import JobManager, _sanitize_directory_name, generate_mock_site
from portfolio_agent.web.server import create_studio_server


@pytest.fixture
def temp_workspace():
    """Create an isolated workspace for web tests."""
    temp_dir = tempfile.mkdtemp(prefix="test_web_workspace_")
    workspace = Workspace(temp_dir)
    yield workspace
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestJobManagerAndRunner:
    """Test background job runner and mock site generation."""

    def test_sanitize_directory_name(self):
        assert _sanitize_directory_name("Alex Morgan Portfolio!") == "alex_morgan_portfolio"
        assert _sanitize_directory_name("test@#$%^&*()site") == "test_site"
        assert _sanitize_directory_name("") == "my_portfolio"

    def test_job_lifecycle(self, temp_workspace):
        manager = JobManager(temp_workspace)
        job = manager.create_job(
            prompt="Create a portfolio for Sarah",
            site_dir="sarah_site",
            is_mock=True,
        )
        assert job.id.startswith("job_")
        assert job.site_dir == "sarah_site"
        assert job.status == "pending"

        # Emit events
        job.emit("step", "Starting turn 1", {"turn": 1})
        assert len(job.events) == 1
        assert job.events[0]["type"] == "step"

        # Finish job
        job.finish(success=True, created_files=["sarah_site/index.html"])
        assert job.status == "completed"
        assert len(job.created_files) == 1

        # Retrieve job
        retrieved = manager.get_job(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id

    def test_mock_generation_produces_deliverables(self, temp_workspace):
        manager = JobManager(temp_workspace)
        job = manager.create_job(
            prompt="Make portfolio for Alice",
            site_dir="alice_portfolio",
            is_mock=True,
        )
        generate_mock_site(
            job,
            temp_workspace,
            wizard_data={
                "name": "Alice Vance",
                "title": "Robotics Engineer",
                "skills": ["ROS", "C++", "Python"],
            },
        )

        assert job.status == "completed"
        site_folder = temp_workspace.website_workspace / "alice_portfolio"
        assert (site_folder / "index.html").exists()
        assert (site_folder / "style.css").exists()
        assert (site_folder / "script.js").exists()

        index_content = (site_folder / "index.html").read_text(encoding="utf-8")
        assert "Alice Vance" in index_content
        assert "Robotics Engineer" in index_content
        assert "ROS" in index_content

    def test_extract_portfolio_info_from_prompt(self):
        from portfolio_agent.web.runner import extract_portfolio_info_from_prompt
        info = extract_portfolio_info_from_prompt("Create a modern portfolio for John Doe, Senior AI Engineer")
        assert info.get("name") == "John Doe"
        assert "Engineer" in info.get("title", "")


class TestStudioServerEndpoints:
    """Integration tests for Studio HTTP server APIs and local website hosting."""

    @pytest.fixture
    def live_server(self, temp_workspace):
        # Create a sample site inside workspace
        temp_workspace.create_directory("sample_site")
        temp_workspace.write_file(
            "sample_site/index.html",
            "<!DOCTYPE html><html><head><title>Sample</title></head><body><h1>Hello World</h1></body></html>",
        )
        temp_workspace.write_file("sample_site/style.css", "body { background: #000; }")
        temp_workspace.write_file("sample_site/script.js", "console.log('test');")

        config = Config(api_key="test_dummy_key", model="gpt-4o-mini", preview_port=0)
        job_manager = JobManager(temp_workspace)

        server = create_studio_server(
            host="127.0.0.1",
            port=0,  # OS assigned port
            workspace=temp_workspace,
            job_manager=job_manager,
            config=config,
        )

        import threading

        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        host, port = server.server_address
        base_url = f"http://{host}:{port}"

        yield {
            "base_url": base_url,
            "workspace": temp_workspace,
            "job_manager": job_manager,
        }

        server.shutdown()
        server.server_close()

    def test_get_config_endpoint(self, live_server):
        req = urllib.request.Request(f"{live_server['base_url']}/api/config")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["has_api_key"] is True
            assert data["model"] == "gpt-4o-mini"
            assert "available_models" in data

    def test_get_sites_endpoint(self, live_server):
        req = urllib.request.Request(f"{live_server['base_url']}/api/sites")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            sites = data["sites"]
            assert len(sites) >= 1
            assert any(s["id"] == "sample_site" for s in sites)

    def test_local_hosting_preview(self, live_server):
        # Verify /preview/sample_site/ hosts the generated website locally
        url = f"{live_server['base_url']}/preview/sample_site/index.html"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8")
            assert "<h1>Hello World</h1>" in content
            assert resp.headers.get("Content-Type", "").startswith("text/html")

    def test_post_generate_mock(self, live_server):
        payload = {
            "mode": "prompt",
            "prompt": "Create an AI engineer portfolio",
            "dir_name": "ai_site_test",
            "mock": True,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{live_server['base_url']}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 202
            res_data = json.loads(resp.read().decode("utf-8"))
            assert res_data["success"] is True
            assert "job_id" in res_data
            job_id = res_data["job_id"]

        # Wait for background mock generation to finish
        for _ in range(30):
            job = live_server["job_manager"].get_job(job_id)
            if job and job.status in ("completed", "failed"):
                break
            time.sleep(0.1)

        assert job.status == "completed"
        # Confirm it is now previewable
        preview_req = urllib.request.Request(
            f"{live_server['base_url']}/preview/ai_site_test/index.html"
        )
        with urllib.request.urlopen(preview_req) as resp:
            assert resp.status == 200

    def test_site_file_edit_and_save(self, live_server):
        # Update sample_site/index.html via API
        new_html = "<h1>Updated via Web Studio Inspector</h1>"
        body = json.dumps({"path": "index.html", "content": new_html}).encode("utf-8")
        req = urllib.request.Request(
            f"{live_server['base_url']}/api/sites/sample_site/file",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            res = json.loads(resp.read().decode("utf-8"))
            assert res["success"] is True

        # Read back via preview
        preview_req = urllib.request.Request(
            f"{live_server['base_url']}/preview/sample_site/index.html"
        )
        with urllib.request.urlopen(preview_req) as resp:
            content = resp.read().decode("utf-8")
            assert new_html in content

    def test_site_zip_download(self, live_server):
        req = urllib.request.Request(
            f"{live_server['base_url']}/api/sites/sample_site/download"
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == "application/zip"
            zip_bytes = resp.read()
            zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
            file_names = zf.namelist()
            assert "index.html" in file_names
            assert "style.css" in file_names

    def test_sandbox_path_traversal_rejection(self, live_server):
        # Attempt traversal outside sandbox
        evil_url = f"{live_server['base_url']}/preview/../../secret.txt"
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(evil_url)
        assert exc_info.value.code in (400, 403, 404)
