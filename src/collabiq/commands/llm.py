"""
LLM provider management commands.

Commands:
- status: View all provider health metrics
- test: Test provider connectivity
- policy: Display orchestration strategy
- set-policy: Change orchestration strategy
- usage: View API usage and costs
- disable/enable: Manage provider status

Gracefully handles Phase 3a (Gemini only) and Phase 3b (multi-LLM).
"""

import typer

app = typer.Typer(
    name="llm",
    help="LLM provider management (status, test, policy, usage, enable/disable)",
)

# Commands will be implemented in Phase 6 (User Story 4)
