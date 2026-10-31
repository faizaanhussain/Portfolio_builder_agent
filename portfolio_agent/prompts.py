"""
System and user prompts for Portfolio Agent.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# The exact system prompt requested for the website developer agent
WEBSITE_SYSTEM_PROMPT = """You are an expert frontend website developer.

Your job is to create complete static websites using the available tools.

Follow these rules:
1. Create a separate directory for every website.
2. Create index.html.
3. Create style.css.
4. Create script.js when JavaScript is useful.
5. Build modern, beautiful and responsive websites.
6. Use only HTML, CSS and vanilla JavaScript.
7. Do not just return website code in your response. Actually create the files using tools.
8. After creating the website, list the project files.
9. Read important files again if needed and fix obvious problems.
10. Finish only when the complete website has been created."""


def build_portfolio_prompt(
    name: str = "Alex Morgan",
    title: str = "Full-Stack AI Engineer",
    bio: Optional[str] = None,
    skills: Optional[list[str]] = None,
    projects: Optional[list[Dict[str, Any]]] = None,
    contact_email: Optional[str] = None,
    github: Optional[str] = None,
    linkedin: Optional[str] = None,
    theme: str = "modern dark mode with neon accents and glassmorphism",
    directory_name: str = "portfolio",
    extra_instructions: Optional[str] = None,
) -> str:
    """Build a comprehensive user prompt for the portfolio creation task."""
    skills_list = skills or [
        "Python",
        "TypeScript",
        "React",
        "Node.js",
        "PyTorch",
        "FastAPI",
        "Docker",
        "PostgreSQL",
        "Tailwind CSS",
        "Git",
    ]

    default_projects = [
        {
            "name": "Neural Vision Studio",
            "description": "Real-time AI computer vision processing pipeline with interactive web dashboard.",
            "tags": ["Python", "PyTorch", "FastAPI", "WebSockets"],
            "github": "https://github.com/example/neural-vision",
            "demo": "https://example.com/demo1",
        },
        {
            "name": "Agentic Workflow Orchestrator",
            "description": "Distributed multi-agent orchestration framework for autonomous LLM workflows.",
            "tags": ["TypeScript", "Python", "Docker", "Redis"],
            "github": "https://github.com/example/agentic-orchestrator",
            "demo": "https://example.com/demo2",
        },
        {
            "name": "Cloud Cost Optimizer",
            "description": "FinOps automated cost monitoring and resource rightsizing engine for AWS & GCP.",
            "tags": ["Go", "AWS", "Kubernetes", "GraphQL"],
            "github": "https://github.com/example/cloud-cost",
            "demo": "https://example.com/demo3",
        },
    ]

    project_items = projects or default_projects
    bio_text = (
        bio
        or f"Passionate {title} with over 5 years of experience architecting resilient cloud systems and autonomous AI solutions. I bridge the gap between deep machine learning models and high-throughput production interfaces."
    )

    projects_formatted = "\n".join(
        f"  - **{p.get('name', 'Project')}**: {p.get('description', '')}\n"
        f"    Tech: {', '.join(p.get('tags', []))}\n"
        f"    GitHub: {p.get('github', 'https://github.com')}\n"
        f"    Live Demo: {p.get('demo', 'https://example.com')}"
        for p in project_items
    )

    prompt = f"""Please create a complete, stunning, high-converting personal portfolio website for:

**Personal Information**:
- Name: {name}
- Title / Headline: {title}
- Directory to create: {directory_name}
- Bio / Summary: {bio_text}
- Contact Email: {contact_email or 'alex.morgan@example.com'}
- GitHub: {github or 'https://github.com'}
- LinkedIn: {linkedin or 'https://linkedin.com'}

**Key Skills & Technologies**:
{', '.join(skills_list)}

**Featured Projects**:
{projects_formatted}

**Design & UI Requirements**:
- Visual Style / Theme: {theme}
- Structure:
  1. Header / Navbar with smooth scrolling navigation links and a Theme Toggle (Dark/Light)
  2. Hero Section with impactful headline, animated badge/subtitle, CTA buttons (View Work, Contact Me)
  3. About Section highlighting background, experience stats, and philosophy
  4. Skills Section organized visually with modern pill/badge components or icon grids
  5. Projects Showcase with interactive filter tabs (All, AI/ML, Full-Stack, etc.), clean cards, preview mockups, tag badges, and GitHub/Demo links
  6. Interactive Contact Section with functional frontend form validation and direct social links
  7. Footer with copyright and quick navigation links
- Polish & Responsiveness:
  - Responsive design that looks flawless on mobile phones, tablets, and desktop displays.
  - Smooth hover animations, glassmorphism cards, and refined typography.
  - Semantic HTML5, accessible tags, and organized CSS with CSS custom properties (variables).
  - Vanilla JavaScript for mobile hamburger menu toggle, dark/light mode toggle with localStorage persistence, smooth scrolling, and contact form handling.

Remember:
1. Create the directory `{directory_name}` first.
2. Write `{directory_name}/index.html`.
3. Write `{directory_name}/style.css`.
4. Write `{directory_name}/script.js`.
5. List the files using the `list_files` tool to confirm creation.
6. Verify and read back files if necessary.
"""

    if extra_instructions:
        prompt += f"\n**Extra Instructions**:\n{extra_instructions}\n"

    return prompt
