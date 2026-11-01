"""
Core Autonomous AI Agent for creating portfolio websites inside a secure sandbox.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from portfolio_agent.config import Config, get_config
from portfolio_agent.prompts import WEBSITE_SYSTEM_PROMPT
from portfolio_agent.sandbox.workspace import Workspace, get_default_workspace
from portfolio_agent.tools.definitions import get_available_tools
from portfolio_agent.tools.executor import ToolExecutor
from portfolio_agent.utils.logger import AgentLogger


@dataclass
class AgentResult:
    """Summary of the agent's execution run."""

    success: bool
    site_dir: Optional[str] = None
    created_files: List[str] = field(default_factory=list)
    total_turns: int = 0
    final_message: str = ""
    error_message: Optional[str] = None


class PortfolioAgent:
    """
    Autonomous website development agent that interacts with an LLM
    via tool-calling to build complete, responsive static websites.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        workspace: Optional[Workspace] = None,
        logger: Optional[AgentLogger] = None,
    ):
        self.config = config or get_config()
        self.workspace = workspace or Workspace(self.config.workspace_dir)
        self.executor = ToolExecutor(self.workspace)
        self.tools = get_available_tools()
        self.logger = logger or AgentLogger()
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy-load OpenAI client to allow graceful handling if API key is missing."""
        if self._client is None:
            try:
                from openai import OpenAI

                client_kwargs: Dict[str, Any] = {}
                api_key = self.config.api_key
                base_url = self.config.base_url

                # Auto-route Groq keys to Groq API
                if api_key and api_key.startswith("gsk_") and (not base_url or "api.openai.com" in base_url):
                    base_url = "https://api.groq.com/openai/v1"
                elif api_key and api_key.startswith("sk-or-") and (not base_url or "api.openai.com" in base_url):
                    base_url = "https://openrouter.ai/api/v1"

                if api_key:
                    client_kwargs["api_key"] = api_key
                if base_url:
                    client_kwargs["base_url"] = base_url
                if base_url and "openrouter.ai" in str(base_url):
                    client_kwargs["default_headers"] = {
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "Portfolio Agent",
                    }

                self._client = OpenAI(**client_kwargs)
            except ImportError as err:
                raise ImportError(
                    "openai package is required. Install it using: pip install openai"
                ) from err
        return self._client

    def run(
        self,
        user_prompt: str,
        expected_dir: Optional[str] = None,
    ) -> AgentResult:
        """
        Execute the agent loop until the website is completely created or max_turns is reached.
        """
        active_url = self.config.base_url or "https://api.openai.com/v1"
        self.logger.header(f"Starting Website Creation Agent ({self.config.model})")
        self.logger.info(f"LLM Provider: {active_url}")
        self.logger.info(f"Workspace Directory: {self.workspace.website_workspace}")

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": WEBSITE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        turn = 0
        final_text = ""
        detected_site_dir: Optional[str] = expected_dir

        while turn < self.config.max_turns:
            turn += 1
            self.logger.step(turn, self.config.max_turns, "Querying model...")

            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=self.config.temperature,
                )
            except Exception as err:
                err_str = str(err)
                if ("404" in err_str or "does not exist" in err_str) and turn == 1:
                    try:
                        valid_models = sorted([m.id for m in self.client.models.list().data if getattr(m, 'id', None)])
                        self.logger.warning(
                            f"Model '{self.config.model}' not found on provider. Available models on your account:\n"
                            f"  {', '.join(valid_models)}"
                        )
                        # Pick best available candidate
                        candidates = [
                            m for m in valid_models
                            if any(k in m.lower() for k in ("llama", "mixtral", "gemma", "gpt"))
                            and not any(ex in m.lower() for ex in ("whisper", "embed", "guard", "vision", "bfloat"))
                        ]
                        if candidates:
                            fallback_model = candidates[0]
                            self.logger.info(f"Auto-recovering: Switching to active model '{fallback_model}'...")
                            self.config.model = fallback_model
                            response = self.client.chat.completions.create(
                                model=fallback_model,
                                messages=messages,
                                tools=self.tools,
                                tool_choice="auto",
                                temperature=self.config.temperature,
                            )
                        else:
                            raise err
                    except Exception as retry_err:
                        self.logger.error(f"API request failed: {retry_err}")
                        return AgentResult(
                            success=False,
                            total_turns=turn,
                            error_message=str(retry_err),
                        )
                else:
                    self.logger.error(f"API request failed: {err}")
                    return AgentResult(
                        success=False,
                        total_turns=turn,
                        error_message=str(err),
                    )

            choice = response.choices[0]
            message = choice.message
            content = message.content or ""
            tool_calls = message.tool_calls or []

            # Display any textual commentary or thoughts from the agent
            if content.strip():
                final_text = content.strip()
                self.logger.agent_message(content.strip())

            # Convert response message to standard dictionary for conversation history
            assistant_msg_dict: Dict[str, Any] = {
                "role": "assistant",
                "content": content,
            }
            if tool_calls:
                assistant_msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(assistant_msg_dict)

            # If no tool calls were requested, the agent has finished its work
            if not tool_calls:
                self.logger.info("Agent signaled completion (no more tool calls).")
                break

            # Execute every tool call requested in this turn
            for tc in tool_calls:
                tool_name = tc.function.name
                arguments_json = tc.function.arguments

                # Extract preview of arguments for logging
                try:
                    args_obj = json.loads(arguments_json) if arguments_json else {}
                    if "content" in args_obj:
                        args_preview = f"path='{args_obj.get('path')}', content_len={len(args_obj.get('content', ''))}"
                    else:
                        args_preview = str(args_obj)

                    # Track site directory if created or written to
                    target_path = args_obj.get("path", "")
                    if target_path and not detected_site_dir:
                        parts = Path(target_path).parts
                        if parts:
                            detected_site_dir = parts[0]
                except Exception:
                    args_preview = arguments_json[:60]

                self.logger.tool_call(tool_name, args_preview)

                # Execute inside the sandbox
                tool_output = self.executor.execute_raw(tool_name, arguments_json)
                self.logger.tool_result(tool_output)

                # Append tool result back to the conversation
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output,
                    }
                )

        # Inspect generated files in the workspace
        all_files_str = self.workspace.list_files(detected_site_dir or "")
        created_files = [
            f.strip() for f in all_files_str.splitlines() if f.strip() and not f.startswith("Directory")
        ]

        # Verify key deliverables (index.html, style.css)
        has_index = any(f.endswith("index.html") for f in created_files)
        has_css = any(f.endswith("style.css") for f in created_files)
        success = has_index and has_css

        if success:
            self.logger.success(
                f"Website created successfully in '{detected_site_dir}'! ({len(created_files)} files)"
            )
        else:
            self.logger.warning(
                f"Website generation completed with missing core files (index: {has_index}, css: {has_css})."
            )

        return AgentResult(
            success=success,
            site_dir=detected_site_dir,
            created_files=created_files,
            total_turns=turn,
            final_message=final_text,
        )
