"""
Tests for PortfolioAgent initialization, prompt integrity, and system prompt verification.
"""

import shutil
import tempfile
import pytest

from portfolio_agent.agent import AgentResult, PortfolioAgent
from portfolio_agent.config import Config
from portfolio_agent.prompts import WEBSITE_SYSTEM_PROMPT, build_portfolio_prompt
from portfolio_agent.sandbox.workspace import Workspace


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp(prefix="test_agent_")
    workspace = Workspace(temp_dir)
    yield workspace
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestAgentConfigurationAndPrompts:
    """Verify prompt contents and agent configuration."""

    def test_system_prompt_rules(self):
        # Verify the exact system prompt rules
        assert "You are an expert frontend website developer." in WEBSITE_SYSTEM_PROMPT
        assert "1. Create a separate directory for every website." in WEBSITE_SYSTEM_PROMPT
        assert "2. Create index.html." in WEBSITE_SYSTEM_PROMPT
        assert "3. Create style.css." in WEBSITE_SYSTEM_PROMPT
        assert "4. Create script.js when JavaScript is useful." in WEBSITE_SYSTEM_PROMPT
        assert "5. Build modern, beautiful and responsive websites." in WEBSITE_SYSTEM_PROMPT
        assert "6. Use only HTML, CSS and vanilla JavaScript." in WEBSITE_SYSTEM_PROMPT
        assert "7. Do not just return website code in your response. Actually create the files using tools." in WEBSITE_SYSTEM_PROMPT
        assert "8. After creating the website, list the project files." in WEBSITE_SYSTEM_PROMPT
        assert "9. Read important files again if needed and fix obvious problems." in WEBSITE_SYSTEM_PROMPT
        assert "10. Finish only when the complete website has been created." in WEBSITE_SYSTEM_PROMPT

    def test_build_portfolio_prompt(self):
        prompt = build_portfolio_prompt(
            name="Sarah Connor",
            title="Cybersecurity Architect",
            directory_name="sarah_portfolio",
            skills=["Penetration Testing", "Cryptography", "Python"],
        )
        assert "Sarah Connor" in prompt
        assert "Cybersecurity Architect" in prompt
        assert "sarah_portfolio" in prompt
        assert "Penetration Testing" in prompt

    def test_agent_result_dataclass(self):
        res = AgentResult(
            success=True,
            site_dir="test_dir",
            created_files=["index.html", "style.css"],
            total_turns=3,
        )
        assert res.success is True
        assert len(res.created_files) == 2
        assert res.site_dir == "test_dir"

    def test_agent_initialization(self, temp_workspace):
        config = Config(api_key="test_key_dummy", model="gpt-4o-mini")
        agent = PortfolioAgent(config=config, workspace=temp_workspace)
        assert agent.config.model == "gpt-4o-mini"
        assert agent.workspace.website_workspace == temp_workspace.website_workspace
        assert len(agent.tools) == 4
