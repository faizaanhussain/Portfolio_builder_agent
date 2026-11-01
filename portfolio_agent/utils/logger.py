"""
Console logger with color formatting and structured progress displays.
"""

from __future__ import annotations

import sys
from typing import Optional

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
    _HAS_COLOR = True
except ImportError:
    _HAS_COLOR = False

    class _Empty:
        def __getattr__(self, name: str) -> str:
            return ""

    Fore = _Empty()  # type: ignore
    Style = _Empty()  # type: ignore


class AgentLogger:
    """Formatted terminal output helper for agent execution steps."""

    @staticmethod
    def header(title: str) -> None:
        line = "=" * 70
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{line}")
        print(f"  {title}")
        print(f"{line}{Style.RESET_ALL}\n")

    @staticmethod
    def step(turn: int, max_turns: int, message: str) -> None:
        print(
            f"{Fore.BLUE}[Turn {turn}/{max_turns}]{Style.RESET_ALL} "
            f"{Fore.WHITE}{Style.BRIGHT}{message}{Style.RESET_ALL}"
        )

    @staticmethod
    def tool_call(name: str, args_summary: str) -> None:
        print(
            f"  {Fore.YELLOW}[TOOL]{Style.RESET_ALL} "
            f"{Fore.YELLOW}{Style.BRIGHT}{name}{Style.RESET_ALL} "
            f"{Fore.WHITE}({args_summary}){Style.RESET_ALL}"
        )

    @staticmethod
    def tool_result(result: str, max_lines: int = 5) -> None:
        lines = result.strip().splitlines()
        if len(lines) <= max_lines:
            preview = "\n".join(f"    │ {line}" for line in lines)
        else:
            preview = "\n".join(f"    │ {line}" for line in lines[:max_lines])
            preview += f"\n    │ ... (+{len(lines) - max_lines} more lines)"
        print(f"  {Fore.GREEN}[RESULT]{Style.RESET_ALL}\n{preview}")

    @staticmethod
    def agent_message(content: str) -> None:
        print(f"\n{Fore.MAGENTA}[AGENT]{Style.RESET_ALL}\n{content}\n")

    @staticmethod
    def success(message: str) -> None:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}[SUCCESS] {message}{Style.RESET_ALL}")

    @staticmethod
    def info(message: str) -> None:
        print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")

    @staticmethod
    def warning(message: str) -> None:
        print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")

    @staticmethod
    def error(message: str) -> None:
        print(f"{Fore.RED}{Style.BRIGHT}[ERROR] {message}{Style.RESET_ALL}", file=sys.stderr)
