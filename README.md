# 🌐 FolioPilot — Autonomous Portfolio Builder

> **An autonomous, tool-calling AI agent and web studio that designs, codes, and refines complete, responsive portfolio websites inside a secure sandbox environment.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI Compatible](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Groq%20%7C%20Ollama-emerald.svg)](https://platform.openai.com/)
[![Security: Sandboxed](https://img.shields.io/badge/Security-Sandboxed%20Workspace-red.svg)](#-sandbox-security-architecture)

---

## 📖 Overview

**Portfolio AI Agent** is an autonomous website development agent designed for GitHub. Rather than merely outputting raw code snippets in chat messages, this agent operates through an **iterative tool-calling loop** with sandboxed file operations. It creates folders, writes HTML, CSS, and JavaScript files, verifies project structures, and refines the code until a complete, responsive personal website is generated.

All file operations are strictly confined within a **sandboxed workspace** (`generated_sites/`), enforcing deterministic path traversal checks to guarantee host system safety.

---

## 📐 Architecture & Workflow

```
                                  ┌───────────────────────────┐
                                  │   User Input / Profile    │
                                  │  (CLI / Wizard / JSON)    │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │   WEBSITE_SYSTEM_PROMPT   │
                                  │   + Structured Brief      │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                 ┌─────────────────────────────┐
                    ┌───────────►│   Autonomous Agent Loop     │◄────────────┐
                    │            │ (LLM Function Calling)      │             │
                    │            └──────────────┬──────────────┘             │
                    │                           │                            │
             Tool Results                       ▼ Tool Calls                 │
                    │                  ┌─────────────────┐                   │
                    │                  │  Tool Executor  │                   │
                    │                  └────────┬────────┘                   │
                    │                           │                            │
                    │                           ▼                            │
                    │            ┌─────────────────────────────┐             │
                    │            │   Sandbox Security Guard    │             │
                    │            │   (safe_path Validation)    │             │
                    │            └──────────────┬──────────────┘             │
                    │                           │                            │
                    │                           ▼ Isolated Operations        │
                    │             ┌───────────────────────────┐              │
                    └─────────────┤  Sandboxed Workspace:     ├──────────────┘
                                  │  • create_directory       │
                                  │  • write_file             │
                                  │  • read_file              │
                                  │  • list_files             │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │ Generated Static Website  │
                                  │ (index.html, style.css,   │
                                  │  script.js in sandbox)    │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │ Live Local Preview Server │
                                  │ (http://localhost:8000)   │
                                  └───────────────────────────┘
```

---

## ✨ Key Features

- **Interactive Web Studio Frontend**: Modern, responsive browser interface where users can write prompts, choose templates, watch live agent streaming turns, and interact with the locally hosted preview in real time.
- **Autonomous Agentic Loop**: The agent plans, generates, inspects, and refines web deliverables across multiple reasoning turns.
- **Strict Sandbox Security**: Protects against path traversal attacks (`../`, nested parent escaping, absolute host paths). The agent cannot access or modify any file outside the designated workspace.
- **Production-Ready Deliverables**: Built strictly using modern **HTML5, CSS3, and vanilla JavaScript** with responsive grids, flexbox, glassmorphism, mobile navigation drawers, and dark/light mode toggles with `localStorage` persistence.
- **Multi-Device Live Preview**: Embedded responsive viewport switcher (Desktop, Laptop, Tablet, Mobile) with direct local hosting (`http://localhost:8000/preview/<site_name>/`).
- **In-Browser Code Inspector**: Inspect generated `index.html`, `style.css`, and `script.js` files with syntax formatting and live edit/save capabilities.
- **Provider Agnostic**: Works out of the box with **OpenAI** (`gpt-4o`, `gpt-4o-mini`), **Groq**, **DeepSeek**, **OpenRouter**, and local **Ollama** models via the OpenAI-compatible function-calling API.
- **Mock Simulation Mode**: Run the agent pipeline without an API key using `--mock` for local demonstrations and testing.
- **1-Click ZIP Export**: Download your completed portfolio folder directly as a clean `.zip` archive ready for deployment on GitHub Pages, Vercel, or Netlify.

---

## 📁 Repository Directory Structure

```text
Portfolio_Agent/
├── .env.example                # Template for environment variables and API keys
├── .gitignore                  # Git ignore rules (protects API keys & generated sites)
├── LICENSE                     # MIT License
├── README.md                   # Comprehensive project documentation
├── pyproject.toml              # Build system & packaging configuration
├── requirements.txt            # Python dependencies
├── main.py                     # Main CLI application entry point
├── preview_server.py           # Local HTTP server for viewing generated websites
├── web_server.py               # Web Studio entry point for interactive browser UI
│
├── portfolio_agent/            # Core Python package
│   ├── __init__.py             # Package exports
│   ├── config.py               # Environment configuration & settings manager
│   ├── agent.py                # Autonomous agent loop & conversation manager
│   ├── prompts.py              # WEBSITE_SYSTEM_PROMPT & user prompt builders
│   │
│   ├── web/                    # Web Studio frontend & server engine
│   │   ├── __init__.py
│   │   ├── server.py           # HTTP server, REST API, SSE streaming & local hosting
│   │   ├── runner.py           # Multi-threaded job manager & mock simulation
│   │   └── static/             # Frontend Single-Page Application
│   │       ├── index.html      # Modern Studio HTML layout
│   │       ├── style.css       # Dark/Light theme, glassmorphism, responsive styles
│   │       └── app.js          # Studio app logic, SSE streams, device preview & editor
│   │
│   ├── sandbox/                # Security sandbox layer
│   │   ├── __init__.py
│   │   ├── security.py         # safe_path validation & path traversal defense
│   │   └── workspace.py        # Isolated file system operations
│   │
│   ├── tools/                  # Function calling definitions & execution
│   │   ├── __init__.py
│   │   ├── definitions.py      # OpenAI-compatible function calling schemas
│   │   └── executor.py         # Tool dispatcher connecting LLM to sandbox
│   │
│   └── utils/                  # Utilities & formatting
│       ├── __init__.py
│       └── logger.py           # Color-coded terminal progress display
│
├── examples/                   # Usage examples & templates
│   ├── profile_template.json   # Customizable JSON profile template
│   └── generate_from_json.py   # Programmatic Python script example
│
├── generated_sites/            # Sandboxed workspace for generated websites
│   ├── .gitkeep
│   └── sample_portfolio/       # Included reference portfolio
│       ├── index.html
│       ├── style.css
│       └── script.js
│
└── tests/                      # Unit & integration test suite
    ├── __init__.py
    ├── test_sandbox.py         # Sandbox security & path traversal tests
    ├── test_tools.py           # Tool schema & execution tests
    ├── test_agent.py           # Agent configuration & prompt tests
    └── test_web.py             # Web server, REST API & local hosting tests
```

---

## 🛡️ Sandbox Security Architecture

The sandbox guarantees that all file read/write operations initiated by the LLM are confined strictly inside the designated workspace folder (default: `generated_sites/`).

### How `safe_path` Works:
```python
def safe_path(relative_path):
    resolved = (website_workspace / relative_path).resolve()
    if resolved != website_workspace and website_workspace not in resolved.parents:
        raise ValueError("Access outside generated-sites is not allowed")
    return resolved
```

### Security Measures:
1. **Path Resolution**: Normalizes all relative paths and resolves symbolic links.
2. **Boundary Containment**: Checks that `resolved == website_workspace` or `website_workspace in resolved.parents`.
3. **Traversal Prevention**: Any attempt to escape via `../../`, root directories (`/etc/`, `C:\Windows`), or malicious symlinks raises a `ValueError("Access outside generated-sites is not allowed")`.
4. **Graceful Agent Recovery**: The sandbox returns informative error messages back to the LLM agent via the tool response, allowing the model to self-correct its paths without crashing.

---

## 🤖 System Prompt

The agent is powered by the following strict system prompt:

```python
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
```

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/portfolio-agent.git
cd portfolio-agent
```

### 2. Set Up a Virtual Environment
```bash
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# Or install in editable mode:
pip install -e .
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your API key:
```ini
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

*(Optional)* To use free local models via **Ollama** or alternative providers like **Groq** or **OpenRouter**:
```ini
# For Groq:
OPENAI_API_KEY=gsk_your_groq_key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile

# For Ollama (Local):
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1
```

---

## 💻 Usage

### 1. Interactive Web Studio (Recommended)
Launch the full web frontend studio in your browser:
```bash
python web_server.py
# Or launch through main.py:
python main.py --web
```
- Open `http://localhost:8000` in your browser.
- Write a natural prompt or use the guided wizard.
- Choose from 1-click prompt presets (AI Engineer, Creative Frontend, DevOps, etc.).
- Watch the agent build your site live turn-by-turn with tool-calling logs.
- Preview your site live in the embedded multi-device simulator (Desktop, Laptop, Tablet, Mobile).
- Inspect and edit `index.html`, `style.css`, and `script.js` with live auto-refresh.
- Download your completed portfolio as a ZIP package.

### 2. Interactive Terminal Wizard
The terminal-based wizard:
```bash
python main.py -i --serve
```
This wizard will ask for your name, title, bio, key skills, and design preferences, then generate your site and launch the browser preview.

### 3. Command Line Arguments
```bash
python main.py \
  --name "Alex Morgan" \
  --title "Full-Stack AI Engineer" \
  --dir "alex_portfolio" \
  --skills "Python,TypeScript,React,FastAPI,Docker,PyTorch" \
  --theme "Cyberpunk neon dark mode with glassmorphism" \
  --serve
```

### 4. Generate from a JSON Profile
Fill out your details in `examples/profile_template.json` and run:
```bash
python main.py --config-file examples/profile_template.json --serve
```

### 5. Direct Custom Prompt
```bash
python main.py \
  --dir "cybersec_portfolio" \
  --prompt "Build a portfolio for a Senior Penetration Tester with a dark green terminal aesthetics and an interactive CTF writeups section." \
  --serve
```

### 6. Mock Simulation (No API Key Required)
Experience the sandbox generation pipeline locally without spending API credits:
```bash
python main.py --mock --serve
# Or launch the Web Studio directly in Mock mode:
python web_server.py
```

### 7. Preview an Existing Generated Website
```bash
python preview_server.py --dir ./generated_sites/sample_portfolio --port 8000
```

---

## 🧪 Running Tests

The test suite covers sandbox path validation, directory traversal prevention, tool schemas, and agent configuration.

Run tests using `pytest`:
```bash
pytest -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute it for personal or commercial projects.
