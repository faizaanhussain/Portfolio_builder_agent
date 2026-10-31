#!/usr/bin/env python3
"""
Main CLI entry point for Portfolio Agent.
Allows interactive prompting, custom JSON profiles, or raw prompts to generate portfolio websites.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path

from portfolio_agent.agent import PortfolioAgent
from portfolio_agent.config import Config, get_config
from portfolio_agent.prompts import build_portfolio_prompt
from portfolio_agent.sandbox.workspace import Workspace
from portfolio_agent.utils.logger import AgentLogger


def run_interactive_wizard() -> dict:
    """Interactively collect portfolio details from the user."""
    print("\n--- Portfolio Details Wizard ---")
    name = input("Your Full Name [Alex Morgan]: ").strip() or "Alex Morgan"
    title = input("Your Professional Title [Full-Stack AI Engineer]: ").strip() or "Full-Stack AI Engineer"
    dir_name = input(f"Target Directory Name [{name.lower().replace(' ', '_')}_portfolio]: ").strip()
    if not dir_name:
        dir_name = f"{name.lower().replace(' ', '_')}_portfolio"

    bio = input("Short Bio / About You (press Enter for default): ").strip()
    skills_raw = input("Key Skills (comma-separated, press Enter for default): ").strip()
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else None

    theme = input("Design Theme [Modern Dark Mode with Neon Accents & Glassmorphism]: ").strip()
    if not theme:
        theme = "Modern Dark Mode with Neon Accents & Glassmorphism"

    contact_email = input("Contact Email [optional]: ").strip() or None
    github = input("GitHub Profile URL [optional]: ").strip() or None
    linkedin = input("LinkedIn Profile URL [optional]: ").strip() or None

    return {
        "name": name,
        "title": title,
        "directory_name": dir_name,
        "bio": bio or None,
        "skills": skills,
        "theme": theme,
        "contact_email": contact_email,
        "github": github,
        "linkedin": linkedin,
    }


def run_mock_simulation(workspace: Workspace, dir_name: str, name: str, title: str) -> None:
    """Simulate the agent's work in mock mode for demonstrations and tests without API keys."""
    logger = AgentLogger()
    logger.header("Running Mock Portfolio Generation Simulation")
    logger.info("No API key required. Generating reference portfolio through sandbox tools...")

    # Step 1: Create directory
    logger.step(1, 4, "Creating site directory")
    logger.tool_call("create_directory", f"path='{dir_name}'")
    res1 = workspace.create_directory(dir_name)
    logger.tool_result(res1)

    # Step 2: Write index.html
    logger.step(2, 4, "Generating index.html")
    logger.tool_call("write_file", f"path='{dir_name}/index.html'")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | {title}</title>
    <link rel="stylesheet" href="style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
</head>
<body data-theme="dark">
    <!-- Navigation -->
    <header class="navbar">
        <div class="nav-container">
            <a href="#" class="nav-logo">{name.split()[0]}<span>.dev</span></a>
            <nav class="nav-links">
                <a href="#about">About</a>
                <a href="#skills">Skills</a>
                <a href="#projects">Projects</a>
                <a href="#contact">Contact</a>
                <button id="theme-toggle" class="theme-btn" aria-label="Toggle Theme">🌙</button>
            </nav>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <div class="badge">🚀 Available for new opportunities</div>
            <h1 class="hero-title">Hi, I'm <span class="gradient-text">{name}</span></h1>
            <p class="hero-subtitle">{title}</p>
            <p class="hero-desc">Building resilient, intelligent web systems and autonomous AI solutions with modern architecture.</p>
            <div class="hero-cta">
                <a href="#projects" class="btn btn-primary">View Projects</a>
                <a href="#contact" class="btn btn-secondary">Get In Touch</a>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="section">
        <div class="container">
            <h2 class="section-title">About Me</h2>
            <div class="about-grid">
                <div class="about-card glass">
                    <h3>Background</h3>
                    <p>Passionate developer dedicated to creating intuitive user interfaces and scalable backend systems. Enthusiastic about generative AI, agentic architectures, and modern web standards.</p>
                </div>
                <div class="stats-grid">
                    <div class="stat-card glass">
                        <div class="stat-num">5+</div>
                        <div class="stat-label">Years Experience</div>
                    </div>
                    <div class="stat-card glass">
                        <div class="stat-num">20+</div>
                        <div class="stat-label">Completed Projects</div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Skills Section -->
    <section id="skills" class="section">
        <div class="container">
            <h2 class="section-title">Skills & Technologies</h2>
            <div class="skills-grid">
                <span class="skill-tag">Python</span>
                <span class="skill-tag">TypeScript</span>
                <span class="skill-tag">React</span>
                <span class="skill-tag">FastAPI</span>
                <span class="skill-tag">PyTorch</span>
                <span class="skill-tag">Docker</span>
                <span class="skill-tag">PostgreSQL</span>
                <span class="skill-tag">Tailwind CSS</span>
                <span class="skill-tag">Next.js</span>
                <span class="skill-tag">Git</span>
            </div>
        </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="section">
        <div class="container">
            <h2 class="section-title">Featured Projects</h2>
            <div class="projects-grid">
                <div class="project-card glass">
                    <div class="project-tag">AI / LLM</div>
                    <h3>Autonomous Portfolio Agent</h3>
                    <p>Sandboxed AI agent generating complete production-ready static portfolios using tool-calling.</p>
                    <div class="project-tech">
                        <span>Python</span>
                        <span>OpenAI API</span>
                        <span>Security Sandbox</span>
                    </div>
                </div>
                <div class="project-card glass">
                    <div class="project-tag">Full-Stack</div>
                    <h3>Real-time Data Studio</h3>
                    <p>High-throughput telemetry ingestion pipeline and interactive reactive dashboard.</p>
                    <div class="project-tech">
                        <span>FastAPI</span>
                        <span>WebSockets</span>
                        <span>TypeScript</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="section">
        <div class="container">
            <h2 class="section-title">Get In Touch</h2>
            <div class="contact-card glass">
                <form id="contact-form">
                    <div class="form-group">
                        <label for="name">Name</label>
                        <input type="text" id="name" required placeholder="Your name">
                    </div>
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" required placeholder="your.email@example.com">
                    </div>
                    <div class="form-group">
                        <label for="message">Message</label>
                        <textarea id="message" rows="4" required placeholder="Tell me about your project..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Send Message</button>
                    <div id="form-status" class="form-status"></div>
                </form>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <p>&copy; 2025 {name}. Built with Portfolio Agent.</p>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""
    res2 = workspace.write_file(f"{dir_name}/index.html", html_content)
    logger.tool_result(res2)

    # Step 3: Write style.css
    logger.step(3, 4, "Generating style.css")
    logger.tool_call("write_file", f"path='{dir_name}/style.css'")
    css_content = """:root {
    --bg-color: #0b0f19;
    --text-color: #f1f5f9;
    --card-bg: rgba(30, 41, 59, 0.7);
    --border-color: rgba(255, 255, 255, 0.1);
    --accent-color: #38bdf8;
    --accent-glow: rgba(56, 189, 248, 0.35);
    --nav-bg: rgba(11, 15, 25, 0.85);
}

[data-theme="light"] {
    --bg-color: #f8fafc;
    --text-color: #0f172a;
    --card-bg: rgba(255, 255, 255, 0.85);
    --border-color: rgba(0, 0, 0, 0.1);
    --accent-color: #0284c7;
    --accent-glow: rgba(2, 132, 199, 0.2);
    --nav-bg: rgba(248, 250, 252, 0.85);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    line-height: 1.6;
    transition: background-color 0.3s ease, color 0.3s ease;
}

.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 1.5rem;
}

/* Glassmorphism */
.glass {
    background: var(--card-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 2rem;
}

/* Navigation */
.navbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--nav-bg);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border-color);
}

.nav-container {
    max-width: 1100px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
}

.nav-logo {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--text-color);
    text-decoration: none;
}

.nav-logo span {
    color: var(--accent-color);
}

.nav-links {
    display: flex;
    gap: 1.5rem;
    align-items: center;
}

.nav-links a {
    color: var(--text-color);
    text-decoration: none;
    font-size: 0.95rem;
    font-weight: 500;
    opacity: 0.85;
    transition: color 0.2s, opacity 0.2s;
}

.nav-links a:hover {
    opacity: 1;
    color: var(--accent-color);
}

.theme-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-color);
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1.1rem;
    transition: transform 0.2s;
}

.theme-btn:hover {
    transform: scale(1.1);
}

/* Hero Section */
.hero {
    padding: 6rem 1.5rem;
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
}

.hero-content {
    max-width: 750px;
}

.badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}

.gradient-text {
    background: linear-gradient(135deg, var(--accent-color), #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--accent-color);
    margin-bottom: 1.2rem;
}

.hero-desc {
    font-size: 1.1rem;
    opacity: 0.85;
    margin-bottom: 2rem;
}

.hero-cta {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 0.8rem 1.8rem;
    border-radius: 10px;
    font-weight: 600;
    text-decoration: none;
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
}

.btn-primary {
    background: var(--accent-color);
    color: #0b0f19;
    border: none;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px var(--accent-glow);
}

.btn-secondary {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-color);
}

.btn-secondary:hover {
    transform: translateY(-2px);
    border-color: var(--accent-color);
}

/* Sections */
.section {
    padding: 5rem 0;
}

.section-title {
    font-size: 2rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 3rem;
}

/* Skills */
.skills-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    justify-content: center;
}

.skill-tag {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    padding: 0.6rem 1.2rem;
    border-radius: 30px;
    font-weight: 500;
    font-size: 0.95rem;
    transition: border-color 0.2s, transform 0.2s;
}

.skill-tag:hover {
    border-color: var(--accent-color);
    transform: translateY(-3px);
}

/* Projects */
.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 2rem;
}

.project-card {
    transition: transform 0.3s;
}

.project-card:hover {
    transform: translateY(-6px);
}

.project-tag {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--accent-color);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}

.project-tech {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}

.project-tech span {
    font-size: 0.8rem;
    opacity: 0.75;
    background: rgba(255, 255, 255, 0.05);
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
}

/* Contact Form */
.contact-card {
    max-width: 600px;
    margin: 0 auto;
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.form-group input,
.form-group textarea {
    width: 100%;
    padding: 0.8rem 1rem;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: rgba(0, 0, 0, 0.2);
    color: var(--text-color);
    font-family: inherit;
    font-size: 1rem;
}

.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--accent-color);
}

.form-status {
    margin-top: 1rem;
    font-weight: 600;
}

/* Footer */
.footer {
    text-align: center;
    padding: 3rem 1.5rem;
    border-top: 1px solid var(--border-color);
    opacity: 0.75;
    font-size: 0.9rem;
}

/* Responsive */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.2rem;
    }
    .hero-subtitle {
        font-size: 1.2rem;
    }
    .nav-links {
        gap: 0.8rem;
    }
}"""
    res3 = workspace.write_file(f"{dir_name}/style.css", css_content)
    logger.tool_result(res3)

    # Step 4: Write script.js
    logger.step(4, 4, "Generating script.js")
    logger.tool_call("write_file", f"path='{dir_name}/script.js'")
    js_content = """// Portfolio Interactive Functions
document.addEventListener('DOMContentLoaded', () => {
    // Theme Switcher with localStorage persistence
    const themeBtn = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('portfolio-theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
    themeBtn.textContent = savedTheme === 'dark' ? '🌙' : '☀️';

    themeBtn.addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme');
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', nextTheme);
        localStorage.setItem('portfolio-theme', nextTheme);
        themeBtn.textContent = nextTheme === 'dark' ? '🌙' : '☀️';
    });

    // Smooth Scrolling for Navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const targetEl = document.querySelector(targetId);
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Contact Form Demo Submission Handler
    const contactForm = document.getElementById('contact-form');
    const formStatus = document.getElementById('form-status');

    if (contactForm && formStatus) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            formStatus.textContent = '🚀 Thank you! Your message has been sent successfully.';
            formStatus.style.color = '#10b981';
            contactForm.reset();
            setTimeout(() => {
                formStatus.textContent = '';
            }, 5000);
        });
    }
});"""
    res4 = workspace.write_file(f"{dir_name}/script.js", js_content)
    logger.tool_result(res4)

    logger.success(f"Mock website successfully generated at: {workspace.website_workspace / dir_name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous AI Agent for building responsive portfolio websites in a sandbox."
    )
    parser.add_argument("--name", type=str, default=None, help="Your full name")
    parser.add_argument("--title", type=str, default=None, help="Professional headline / title")
    parser.add_argument("--dir", type=str, default=None, help="Target directory inside generated_sites/")
    parser.add_argument("--bio", type=str, default=None, help="Bio summary")
    parser.add_argument("--skills", type=str, default=None, help="Comma-separated list of skills")
    parser.add_argument("--theme", type=str, default=None, help="Design style / theme preference")
    parser.add_argument("--prompt", type=str, default=None, help="Provide a raw custom prompt directly")
    parser.add_argument("--config-file", type=str, default=None, help="Path to JSON profile configuration")
    parser.add_argument("--model", type=str, default=None, help="LLM model (e.g. gpt-4o, gpt-4o-mini)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive setup wizard")
    parser.add_argument("--serve", "--preview", action="store_true", help="Preview website in browser after generation")
    parser.add_argument("--port", type=int, default=8000, help="Local preview server port (default: 8000)")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without calling external LLM API")

    args = parser.parse_args()
    logger = AgentLogger()

    # Load configuration
    config = get_config()
    if args.model:
        config.model = args.model
    if args.port:
        config.preview_port = args.port

    workspace = Workspace(config.workspace_dir)

    # 1. Handle Mock Mode
    if args.mock:
        dir_name = args.dir or "mock_portfolio"
        name = args.name or "Alex Morgan"
        title = args.title or "Full-Stack AI Engineer"
        run_mock_simulation(workspace, dir_name, name, title)

        if args.serve:
            from preview_server import serve_directory
            serve_directory(workspace.website_workspace / dir_name, port=config.preview_port)
        return 0

    # 2. Check API Key
    if not config.api_key:
        logger.error(
            "OPENAI_API_KEY environment variable is missing.\n"
            "Please create a .env file with your OPENAI_API_KEY, or run with --mock for a demonstration."
        )
        return 1

    # 3. Determine User Prompt & Target Directory
    target_dir = args.dir or "portfolio"

    if args.prompt:
        user_prompt = args.prompt
    elif args.config_file:
        config_path = Path(args.config_file)
        if not config_path.exists():
            logger.error(f"Config file not found: {args.config_file}")
            return 1
        with open(config_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
        target_dir = profile_data.get("directory_name", target_dir)
        user_prompt = build_portfolio_prompt(**profile_data)
    elif args.interactive:
        wizard_data = run_interactive_wizard()
        target_dir = wizard_data["directory_name"]
        user_prompt = build_portfolio_prompt(**wizard_data)
    else:
        # Build prompt from CLI flags or sensible defaults
        skills_list = [s.strip() for s in args.skills.split(",")] if args.skills else None
        target_dir = args.dir or "portfolio"
        user_prompt = build_portfolio_prompt(
            name=args.name or "Alex Morgan",
            title=args.title or "Full-Stack AI Engineer",
            bio=args.bio,
            skills=skills_list,
            theme=args.theme or "modern dark mode with neon accents and glassmorphism",
            directory_name=target_dir,
        )

    # 4. Run Agent
    agent = PortfolioAgent(config=config, workspace=workspace, logger=logger)
    result = agent.run(user_prompt=user_prompt, expected_dir=target_dir)

    if not result.success:
        logger.warning("Generation finished with issues.")
        return 1

    # 5. Optional Live Preview Server
    if args.serve:
        site_folder = workspace.website_workspace / (result.site_dir or target_dir)
        from preview_server import serve_directory
        serve_directory(site_folder, port=config.preview_port)

    return 0


if __name__ == "__main__":
    sys.exit(main())
