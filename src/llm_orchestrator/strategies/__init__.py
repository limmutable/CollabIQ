"""Orchestration strategies for multi-provider coordination.

This module provides different strategies for coordinating multiple LLM providers:
- Failover: Sequential provider attempts with automatic switching
- Consensus: Parallel queries with weighted voting (future)
- BestMatch: Parallel queries selecting highest confidence (future)
"""

from src.llm_orchestrator.strategies.failover import FailoverStrategy

__all__ = ["FailoverStrategy"]
