#!/usr/bin/env python3
"""
Example: Programmatically generate a portfolio website from a JSON profile.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure repository root is in python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portfolio_agent.agent import PortfolioAgent
from portfolio_agent.config import get_config
from portfolio_agent.prompts import build_portfolio_prompt
from portfolio_agent.sandbox.workspace import Workspace


def main():
    profile_file = Path(__file__).parent / "profile_template.json"
    if not profile_file.exists():
        print(f"Profile file not found: {profile_file}")
        return 1

    with open(profile_file, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    config = get_config()
    workspace = Workspace(config.workspace_dir)

    target_dir = profile_data.get("directory_name", "generated_portfolio")
    prompt = build_portfolio_prompt(**profile_data)

    print(f"Generating portfolio for '{profile_data.get('name')}' in '{target_dir}'...")

    agent = PortfolioAgent(config=config, workspace=workspace)
    result = agent.run(user_prompt=prompt, expected_dir=target_dir)

    if result.success:
        print(f"\nPortfolio successfully generated!")
        print(f"Files created ({len(result.created_files)}):")
        for file in result.created_files:
            print(f"  - {file}")
        return 0
    else:
        print("\nGeneration failed or incomplete.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
