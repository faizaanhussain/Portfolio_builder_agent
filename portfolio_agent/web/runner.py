"""
Job runner and event streaming engine for the Portfolio Agent web interface.
"""

from __future__ import annotations

import json
import queue
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from portfolio_agent.agent import AgentResult, PortfolioAgent
from portfolio_agent.config import Config, get_config
from portfolio_agent.prompts import build_portfolio_prompt
from portfolio_agent.sandbox.workspace import Workspace
from portfolio_agent.utils.logger import AgentLogger


@dataclass
class JobEvent:
    """An event emitted during agent execution."""

    event_type: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class WebAgentLogger(AgentLogger):
    """
    Subclasses AgentLogger to pipe execution events to both
    the console and the web job's event stream.
    """

    def __init__(self, job: "WebJob"):
        self.job = job

    def header(self, title: str) -> None:
        super().header(title)
        self.job.emit("header", title)

    def step(self, turn: int, max_turns: int, message: str) -> None:
        super().step(turn, max_turns, message)
        self.job.emit(
            "step",
            message,
            {"turn": turn, "max_turns": max_turns, "progress": int((turn / max_turns) * 100)},
        )

    def tool_call(self, name: str, args_summary: str) -> None:
        super().tool_call(name, args_summary)
        self.job.emit("tool_call", f"Calling tool: {name}", {"tool": name, "args": args_summary})

    def tool_result(self, result: str, max_lines: int = 5) -> None:
        super().tool_result(result, max_lines=max_lines)
        self.job.emit("tool_result", "Tool executed", {"result": result})

    def agent_message(self, content: str) -> None:
        super().agent_message(content)
        self.job.emit("agent_message", content, {"content": content})

    def success(self, message: str) -> None:
        super().success(message)
        self.job.emit("success", message)

    def info(self, message: str) -> None:
        super().info(message)
        self.job.emit("info", message)

    def warning(self, message: str) -> None:
        super().warning(message)
        self.job.emit("warning", message)

    def error(self, message: str) -> None:
        super().error(message)
        self.job.emit("error", message)


class WebJob:
    """Represents a portfolio generation task run by the agent."""

    def __init__(
        self,
        job_id: str,
        prompt: str,
        site_dir: str,
        is_mock: bool = False,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.id = job_id
        self.prompt = prompt
        self.site_dir = site_dir
        self.is_mock = is_mock
        self.meta = meta or {}
        self.status = "pending"  # pending, running, completed, failed
        self.created_files: List[str] = []
        self.events: List[Dict[str, Any]] = []
        self.event_queue: "queue.Queue[Optional[Dict[str, Any]]]" = queue.Queue()
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self._thread: Optional[threading.Thread] = None

    def emit(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Record and broadcast an event."""
        event = JobEvent(event_type=event_type, message=message, data=data or {})
        payload = event.to_dict()
        self.events.append(payload)
        self.event_queue.put(payload)

    def finish(self, success: bool, created_files: Optional[List[str]] = None, error: Optional[str] = None) -> None:
        """Mark the job as completed or failed."""
        self.status = "completed" if success else "failed"
        self.completed_at = time.time()
        if created_files:
            self.created_files = created_files
        if error:
            self.error = error

        self.emit(
            "complete" if success else "failed",
            "Website generation complete!" if success else f"Generation failed: {error}",
            {
                "success": success,
                "site_dir": self.site_dir,
                "created_files": self.created_files,
                "error": error,
                "duration": round(self.completed_at - self.created_at, 2),
            },
        )
        # Sentinel to signal event stream conclusion
        self.event_queue.put(None)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize job state for API responses."""
        return {
            "id": self.id,
            "status": self.status,
            "site_dir": self.site_dir,
            "is_mock": self.is_mock,
            "prompt": self.prompt,
            "meta": self.meta,
            "created_files": self.created_files,
            "events_count": len(self.events),
            "events": self.events,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "preview_url": f"/preview/{self.site_dir}/" if self.status == "completed" else None,
        }


def _sanitize_directory_name(name: str) -> str:
    """Convert arbitrary user input into a safe directory name."""
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip().lower())
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean or "my_portfolio"


def get_default_user_name() -> str:
    """Return default generic example name."""
    return "John Doe"


def extract_portfolio_info_from_prompt(prompt: str) -> Dict[str, Any]:
    """Extract name, title, and key attributes from natural language prompt."""
    info: Dict[str, Any] = {}
    if not prompt:
        return info

    name_patterns = [
        r"(?:for|portfolio for|website for|dr\.|named)\s+([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)+)",
        r"(?:name\s*(?:is|:)|i am|i'm)\s+([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)+)",
        r"(?:for|named|about)\s+([A-Z][a-zA-Z'\-]+)",
    ]
    for pat in name_patterns:
        m = re.search(pat, prompt)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in (
                "full-stack", "frontend", "backend", "developer", "engineer",
                "designer", "architect", "alex", "john",
            ):
                info["name"] = candidate
                break

    title_patterns = [
        r"(?:,\s*(?:an?|the)\s+)?([A-Z][a-zA-Z\s\-/]+?\b(?:Engineer|Developer|Architect|Designer|Scientist|Consultant|Specialist|Manager|Director|Researcher|Lead|Founder))\b",
        r"(?:title\s*(?:is|:)|role\s*(?:is|:)|as an?)\s+([A-Za-z0-9\s\-/,]+?)(?:\.|\n|with|,|featuring|including|and|\bwho\b)",
    ]
    for pat in title_patterns:
        m = re.search(pat, prompt, re.IGNORECASE)
        if m:
            candidate_title = m.group(1).strip()
            if len(candidate_title) < 50:
                info["title"] = candidate_title.title()
                break

    return info


def generate_mock_site(
    job: WebJob,
    workspace: Workspace,
    wizard_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Simulate real-time agent workflow in mock mode.
    Emits authentic step-by-step turns with delay so the user experiences
    the agentic lifecycle even without an external API key.
    """
    logger = WebAgentLogger(job)
    data = wizard_data or {}
    prompt_info = extract_portfolio_info_from_prompt(job.prompt)
    default_name = get_default_user_name()

    name = data.get("name") or prompt_info.get("name") or default_name
    title = data.get("title") or prompt_info.get("title") or "Full-Stack AI Engineer"
    bio = data.get("bio") or (
        f"Hi, I'm {name}. I engineer high-performance web systems, distributed architectures, "
        "and agentic AI solutions. Passionate about building seamless human-AI interfaces."
    )
    skills = data.get("skills") or [
        "Python",
        "TypeScript",
        "React",
        "FastAPI",
        "PyTorch",
        "Docker",
        "Tailwind CSS",
        "PostgreSQL",
        "Next.js",
        "Git",
    ]
    theme_name = data.get("theme") or "Modern Glassmorphic Dark"
    contact_email = data.get("contact_email") or "contact@example.dev"
    github = data.get("github") or "https://github.com"
    linkedin = data.get("linkedin") or "https://linkedin.com"

    dir_name = job.site_dir
    max_turns = 5

    logger.header(f"Starting Website Creation Agent (Mock Simulation: {name})")
    time.sleep(0.3)

    # Step 1: Create directory
    logger.step(1, max_turns, f"Creating sandboxed workspace folder: '{dir_name}'")
    logger.tool_call("create_directory", f"path='{dir_name}'")
    time.sleep(0.4)
    res1 = workspace.create_directory(dir_name)
    logger.tool_result(res1)
    time.sleep(0.3)

    # Step 2: Write index.html
    logger.step(2, max_turns, "Generating semantic HTML5 layout (index.html)")
    logger.agent_message(
        f"I am designing a modern, accessible portfolio for {name} ({title}) with "
        f"{theme_name} theme, responsive navigation, skills grid, projects cards, and interactive contact form."
    )
    logger.tool_call("write_file", f"path='{dir_name}/index.html'")
    time.sleep(0.5)

    skills_html = "\n".join(f'                <span class="skill-tag">{s}</span>' for s in skills)

    projects = data.get("projects") or [
        {
            "name": "Neural Workflow Studio",
            "tag": "AI & AGENTIC",
            "desc": "Autonomous multi-agent workflow generator and real-time prompt optimization studio.",
            "tech": ["Python", "OpenAI", "FastAPI", "WebSockets"],
        },
        {
            "name": "Cloud Observability Hub",
            "tag": "FULL-STACK",
            "desc": "Distributed telemetry visualizer with sub-second real-time metrics streaming.",
            "tech": ["TypeScript", "React", "Docker", "Go"],
        },
        {
            "name": "Decentralized Key-Value Store",
            "tag": "SYSTEMS",
            "desc": "High-throughput fault-tolerant distributed consensus cluster built on Raft.",
            "tech": ["Rust", "gRPC", "PostgreSQL"],
        },
    ]

    projects_html = "\n".join(
        f"""                <div class="project-card glass">
                    <div class="project-tag">{p.get('tag', 'FEATURED')}</div>
                    <h3>{p.get('name', 'Project')}</h3>
                    <p>{p.get('desc', 'Modern high-performance solution.')}</p>
                    <div class="project-tech">
                        {"".join(f"<span>{t}</span>" for t in p.get('tech', ['Web']))}
                    </div>
                    <div class="project-links">
                        <a href="{github}" target="_blank" rel="noopener" class="card-link">GitHub</a>
                        <a href="#contact" class="card-link primary">Live Demo</a>
                    </div>
                </div>"""
        for p in projects
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | {title}</title>
    <link rel="stylesheet" href="style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body data-theme="light">
    <!-- Navigation -->
    <header class="navbar">
        <div class="nav-container">
            <a href="#" class="nav-logo">{name.split()[0]}<span>.dev</span></a>
            <nav class="nav-links" id="nav-links">
                <a href="#about">About</a>
                <a href="#skills">Skills</a>
                <a href="#projects">Projects</a>
                <a href="#contact">Contact</a>
                <button id="theme-toggle" class="theme-btn" aria-label="Toggle Theme">
                    <span id="theme-btn-text">Dark</span>
                </button>
            </nav>
            <button class="mobile-menu-btn" id="mobile-toggle" aria-label="Toggle Navigation">
                <span></span><span></span><span></span>
            </button>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
        <div class="container hero-content">
            <div class="badge animate-pop">
                <span class="badge-dot"></span>
                <span>Available for projects</span>
            </div>
            <h1 class="hero-title">Hi, I'm <span class="gradient-text">{name}</span></h1>
            <p class="hero-subtitle">{title}</p>
            <p class="hero-desc">{bio}</p>
            <div class="hero-cta">
                <a href="#projects" class="btn btn-primary">View Featured Work</a>
                <a href="#contact" class="btn btn-secondary">Get In Touch</a>
            </div>
            <div class="hero-stats">
                <div class="stat-item">
                    <span class="stat-number">5+</span>
                    <span class="stat-label">Years Experience</span>
                </div>
                <div class="stat-divider"></div>
                <div class="stat-item">
                    <span class="stat-number">30+</span>
                    <span class="stat-label">Completed Projects</span>
                </div>
                <div class="stat-divider"></div>
                <div class="stat-item">
                    <span class="stat-number">99.9%</span>
                    <span class="stat-label">Uptime</span>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="section">
        <div class="container">
            <div class="section-header">
                <span class="section-badge">ABOUT ME</span>
                <h2 class="section-title">Architecting with Code & Vision</h2>
            </div>
            <div class="about-grid">
                <div class="about-card glass">
                    <h3>Philosophy & Approach</h3>
                    <p>I believe in building software that is functional, resilient under heavy load, and straightforward to use. Combining deep technical systems knowledge with refined interface craftsmanship.</p>
                    <div class="about-bullets">
                        <div class="bullet-item"><span class="bullet-check"></span> Production-grade systems architecture</div>
                        <div class="bullet-item"><span class="bullet-check"></span> Autonomous AI and tool-calling workflows</div>
                        <div class="bullet-item"><span class="bullet-check"></span> Human-centered responsive interface design</div>
                    </div>
                </div>
                <div class="about-card glass highlights-card">
                    <h3>Connect Directly</h3>
                    <p>Interested in collaborating, technical advisory, or engineering roles?</p>
                    <div class="social-list">
                        <a href="{github}" target="_blank" rel="noopener" class="social-btn">GitHub Profile</a>
                        <a href="{linkedin}" target="_blank" rel="noopener" class="social-btn">LinkedIn Network</a>
                        <a href="mailto:{contact_email}" class="social-btn email-btn">Email Direct</a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Skills Section -->
    <section id="skills" class="section">
        <div class="container">
            <div class="section-header">
                <span class="section-badge">EXPERTISE</span>
                <h2 class="section-title">Technologies & Core Competencies</h2>
            </div>
            <div class="skills-grid">
{skills_html}
            </div>
        </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="section">
        <div class="container">
            <div class="section-header">
                <span class="section-badge">PORTFOLIO</span>
                <h2 class="section-title">Featured Projects</h2>
            </div>
            <div class="projects-grid">
{projects_html}
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="section">
        <div class="container">
            <div class="section-header">
                <span class="section-badge">GET IN TOUCH</span>
                <h2 class="section-title">Let's Build Something Great</h2>
            </div>
            <div class="contact-card glass">
                <form id="contact-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="name">Your Name</label>
                            <input type="text" id="name" required placeholder="Alex Rivera">
                        </div>
                        <div class="form-group">
                            <label for="email">Your Email</label>
                            <input type="email" id="email" required placeholder="alex@company.com">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="message">Project Details or Inquiry</label>
                        <textarea id="message" rows="5" required placeholder="Describe your project, timeline, or question..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary btn-block">Send Message</button>
                    <div id="form-status" class="form-status"></div>
                </form>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container footer-content">
            <p>&copy; 2025 {name}. All rights reserved.</p>
            <p class="footer-credit">Built with <strong>Portfolio Agent</strong></p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""
    res2 = workspace.write_file(f"{dir_name}/index.html", html_content)
    logger.tool_result(res2)
    time.sleep(0.3)

    # Step 3: Write style.css
    logger.step(3, max_turns, "Generating responsive styles & themes (style.css)")
    logger.tool_call("write_file", f"path='{dir_name}/style.css'")
    time.sleep(0.5)

    css_content = """:root {
    --bg-color: #f8fafc;
    --bg-alt: #ffffff;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --accent: #2563eb;
    --accent-rgb: 37, 99, 235;
    --accent-hover: #1d4ed8;
    --accent-glow: rgba(37, 99, 235, 0.12);
    --secondary-accent: #4f46e5;
    --nav-bg: rgba(255, 255, 255, 0.9);
    --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
    --shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.03);
}

[data-theme="dark"] {
    --bg-color: #0b0f19;
    --bg-alt: #111827;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --card-bg: #1f2937;
    --border-color: #374151;
    --accent: #38bdf8;
    --accent-rgb: 56, 189, 248;
    --accent-hover: #0284c7;
    --accent-glow: rgba(56, 189, 248, 0.2);
    --secondary-accent: #818cf8;
    --nav-bg: rgba(17, 24, 39, 0.9);
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3);
    --shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    font-family: var(--font-sans);
    background-color: var(--bg-color);
    color: var(--text-primary);
    line-height: 1.6;
    overflow-x: hidden;
    position: relative;
    transition: background-color 0.2s ease, color 0.2s ease;
}

.container {
    max-width: 1120px;
    margin: 0 auto;
    padding: 0 1.5rem;
}

/* Glass & Card */
.glass {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
}

/* Navigation */
.navbar {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: var(--nav-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border-color);
}

.nav-container {
    max-width: 1120px;
    margin: 0 auto;
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-logo {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
    letter-spacing: -0.3px;
}
.nav-logo span {
    color: var(--accent);
}

.nav-links {
    display: flex;
    gap: 1.6rem;
    align-items: center;
}

.nav-links a {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.92rem;
    font-weight: 500;
    transition: color 0.15s;
}
.nav-links a:hover {
    color: var(--accent);
}

.theme-btn {
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 0.35rem 0.75rem;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    transition: all 0.15s;
}
.theme-btn:hover {
    color: var(--text-primary);
    border-color: var(--accent);
}

.mobile-menu-btn {
    display: none;
    background: none;
    border: none;
    cursor: pointer;
    flex-direction: column;
    gap: 5px;
}
.mobile-menu-btn span {
    width: 22px;
    height: 2px;
    background: var(--text-primary);
    transition: 0.2s;
}

/* Hero */
.hero {
    position: relative;
    padding: 6.5rem 0 4.5rem;
    text-align: center;
    z-index: 1;
}

.hero-content {
    max-width: 780px;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.35rem 0.9rem;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    color: var(--text-secondary);
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow);
}

.badge-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #059669;
}

.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -1px;
    margin-bottom: 0.5rem;
}

.gradient-text {
    background: linear-gradient(135deg, var(--accent) 0%, var(--secondary-accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 1.1rem;
}

.hero-desc {
    font-size: 1.08rem;
    color: var(--text-secondary);
    max-width: 640px;
    margin: 0 auto 2rem;
}

.hero-cta {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 3.2rem;
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.8rem 1.6rem;
    border-radius: var(--radius-sm);
    font-size: 0.92rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.15s ease;
}
.btn-primary {
    background: var(--accent);
    color: #ffffff;
    border: none;
    box-shadow: var(--shadow);
}
.btn-primary:hover {
    background: var(--accent-hover);
    box-shadow: var(--shadow-hover);
}
.btn-secondary {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
}
.btn-secondary:hover {
    border-color: var(--accent);
}
.btn-block {
    width: 100%;
}

.hero-stats {
    display: inline-flex;
    align-items: center;
    gap: 2rem;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    padding: 1rem 2rem;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow);
}
.stat-item {
    display: flex;
    flex-direction: column;
}
.stat-number {
    font-size: 1.45rem;
    font-weight: 800;
    color: var(--text-primary);
}
.stat-label {
    font-size: 0.74rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.stat-divider {
    width: 1px;
    height: 32px;
    background: var(--border-color);
}

/* Sections */
.section {
    position: relative;
    padding: 5rem 0;
}
.section-header {
    text-align: center;
    margin-bottom: 3rem;
}
.section-badge {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    display: block;
    margin-bottom: 0.35rem;
}
.section-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* About Grid */
.about-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 1.8rem;
}
.about-card {
    padding: 2rem;
}
.about-card h3 {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.8rem;
}
.about-card p {
    color: var(--text-secondary);
    margin-bottom: 1.4rem;
}
.about-bullets {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
}
.bullet-item {
    font-size: 0.92rem;
    color: var(--text-secondary);
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.bullet-check {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
}
.social-list {
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
}
.social-btn {
    display: block;
    padding: 0.7rem 1.1rem;
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    text-decoration: none;
    font-weight: 600;
    font-size: 0.88rem;
    transition: all 0.15s;
    text-align: center;
}
.social-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
}
.email-btn {
    background: var(--accent);
    color: #ffffff;
    border-color: var(--accent);
}
.email-btn:hover {
    background: var(--accent-hover);
    color: #ffffff;
}

/* Skills */
.skills-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    justify-content: center;
    max-width: 840px;
    margin: 0 auto;
}
.skill-tag {
    padding: 0.55rem 1.2rem;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-secondary);
    box-shadow: var(--shadow);
    transition: all 0.15s;
    cursor: default;
}
.skill-tag:hover {
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-2px);
}

/* Projects */
.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
    gap: 1.8rem;
}
.project-card {
    padding: 1.8rem;
    display: flex;
    flex-direction: column;
    transition: all 0.2s ease;
}
.project-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover);
    border-color: var(--accent);
}
.project-tag {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}
.project-card h3 {
    font-size: 1.2rem;
    margin-bottom: 0.6rem;
}
.project-card p {
    color: var(--text-secondary);
    font-size: 0.92rem;
    margin-bottom: 1.3rem;
    flex-grow: 1;
}
.project-tech {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-bottom: 1.3rem;
}
.project-tech span {
    font-size: 0.76rem;
    font-family: var(--font-mono);
    padding: 0.2rem 0.5rem;
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-secondary);
}
.project-links {
    display: flex;
    gap: 1rem;
}
.card-link {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-decoration: none;
    transition: color 0.15s;
}
.card-link:hover {
    color: var(--accent);
}
.card-link.primary {
    color: var(--accent);
}

/* Contact */
.contact-card {
    max-width: 620px;
    margin: 0 auto;
    padding: 2.2rem;
}
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}
.form-group {
    margin-bottom: 1.2rem;
}
.form-group label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.45rem;
}
.form-group input,
.form-group textarea {
    width: 100%;
    padding: 0.75rem 1rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-color);
    background: var(--bg-color);
    color: var(--text-primary);
    font-family: inherit;
    font-size: 0.92rem;
    transition: border-color 0.15s;
}
.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--accent);
}
.form-status {
    margin-top: 0.9rem;
    font-weight: 600;
    text-align: center;
    font-size: 0.9rem;
}

/* Footer */
.footer {
    padding: 2.8rem 0;
    border-top: 1px solid var(--border-color);
    text-align: center;
}
.footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--text-secondary);
    font-size: 0.88rem;
}
.footer-credit strong {
    color: var(--text-primary);
}

/* Mobile */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.3rem;
    }
    .hero-subtitle {
        font-size: 1.15rem;
    }
    .about-grid {
        grid-template-columns: 1fr;
    }
    .form-row {
        grid-template-columns: 1fr;
    }
    .footer-content {
        flex-direction: column;
        gap: 0.7rem;
    }
    .mobile-menu-btn {
        display: flex;
    }
    .nav-links {
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--nav-bg);
        flex-direction: column;
        padding: 1.3rem;
        border-bottom: 1px solid var(--border-color);
    }
    .nav-links.active {
        display: flex;
    }
}"""
    res3 = workspace.write_file(f"{dir_name}/style.css", css_content)
    logger.tool_result(res3)
    time.sleep(0.3)

    # Step 4: Write script.js
    logger.step(4, max_turns, "Generating interactive behaviors (script.js)")
    logger.tool_call("write_file", f"path='{dir_name}/script.js'")
    time.sleep(0.4)

    js_content = """// Interactive Client Functions
document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Toggle with localStorage Persistence
    const themeBtn = document.getElementById('theme-toggle');
    const themeBtnText = document.getElementById('theme-btn-text');
    const savedTheme = localStorage.getItem('portfolio-theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    if (themeBtnText) {
        themeBtnText.textContent = savedTheme === 'dark' ? 'Light' : 'Dark';
    }

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = document.body.getAttribute('data-theme');
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.body.setAttribute('data-theme', nextTheme);
            localStorage.setItem('portfolio-theme', nextTheme);
            if (themeBtnText) {
                themeBtnText.textContent = nextTheme === 'dark' ? 'Light' : 'Dark';
            }
        });
    }

    // 2. Mobile Navigation Toggle
    const mobileBtn = document.getElementById('mobile-toggle');
    const navLinks = document.getElementById('nav-links');
    if (mobileBtn && navLinks) {
        mobileBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => navLinks.classList.remove('active'));
        });
    }

    // 3. Smooth Anchor Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // 4. Contact Form Submission
    const contactForm = document.getElementById('contact-form');
    const formStatus = document.getElementById('form-status');
    if (contactForm && formStatus) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            formStatus.textContent = 'Thank you! Your message has been sent successfully.';
            formStatus.style.color = 'var(--accent)';
            contactForm.reset();
            setTimeout(() => {
                formStatus.textContent = '';
            }, 6000);
        });
    }
});"""
    res4 = workspace.write_file(f"{dir_name}/script.js", js_content)
    logger.tool_result(res4)
    time.sleep(0.3)

    # Step 5: List files
    logger.step(5, max_turns, "Verifying workspace deliverables (list_files)")
    logger.tool_call("list_files", f"path='{dir_name}'")
    time.sleep(0.3)
    files_str = workspace.list_files(dir_name)
    logger.tool_result(files_str)

    created = [f"{dir_name}/index.html", f"{dir_name}/style.css", f"{dir_name}/script.js"]
    logger.success(f"Website created successfully in '{dir_name}'! (3 files)")
    job.finish(success=True, created_files=created)

    created = [f"{dir_name}/index.html", f"{dir_name}/style.css", f"{dir_name}/script.js"]
    logger.success(f"Website created successfully in '{dir_name}'! (3 files)")
    job.finish(success=True, created_files=created)


class JobManager:
    """Manages background agent generation jobs and lifecycle."""

    def __init__(self, workspace: Optional[Workspace] = None):
        self.workspace = workspace or Workspace("generated_sites")
        self.jobs: Dict[str, WebJob] = {}
        self._lock = threading.Lock()

    def create_job(
        self,
        prompt: str,
        site_dir: Optional[str] = None,
        is_mock: bool = False,
        meta: Optional[Dict[str, Any]] = None,
    ) -> WebJob:
        """Create and register a new generation task."""
        job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        safe_dir = _sanitize_directory_name(site_dir or "my_portfolio")

        job = WebJob(
            job_id=job_id,
            prompt=prompt,
            site_dir=safe_dir,
            is_mock=is_mock,
            meta=meta or {},
        )
        with self._lock:
            self.jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[WebJob]:
        """Fetch job by ID."""
        with self._lock:
            return self.jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List summary of all jobs."""
        with self._lock:
            return [job.to_dict() for job in reversed(list(self.jobs.values()))]

    def start_job(
        self,
        job_id: str,
        config: Optional[Config] = None,
        wizard_data: Optional[Dict[str, Any]] = None,
    ) -> WebJob:
        """Start job in background daemon thread."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        def worker() -> None:
            job.status = "running"
            job.emit("start", f"Generation initialized for '{job.site_dir}'")

            try:
                if job.is_mock:
                    generate_mock_site(job, self.workspace, wizard_data)
                else:
                    active_config = config or get_config()
                    if not active_config.api_key:
                        raise ValueError(
                            "OPENAI_API_KEY is not configured on the server. "
                            "Please provide an API key in Advanced Settings or switch to Mock Mode."
                        )

                    logger = WebAgentLogger(job)
                    agent = PortfolioAgent(
                        config=active_config,
                        workspace=self.workspace,
                        logger=logger,
                    )
                    result = agent.run(user_prompt=job.prompt, expected_dir=job.site_dir)
                    job.finish(
                        success=result.success,
                        created_files=result.created_files,
                        error=result.error_message,
                    )
            except Exception as err:
                job.finish(success=False, error=str(err))

        t = threading.Thread(target=worker, daemon=True)
        job._thread = t
        t.start()
        return job


_default_job_manager: Optional[JobManager] = None


def get_default_job_manager() -> JobManager:
    """Retrieve global default JobManager instance."""
    global _default_job_manager
    if _default_job_manager is None:
        _default_job_manager = JobManager()
    return _default_job_manager
