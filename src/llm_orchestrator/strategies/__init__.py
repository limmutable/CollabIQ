"""Orchestration strategies for multi-provider coordination.

This module provides different strategies for coordinating multiple LLM providers:
- Failover: Sequential provider attempts with automatic switching
- Consensus: Parallel queries with fuzzy matching and weighted voting
- BestMatch: Parallel queries selecting highest confidence
"""

from src.llm_orchestrator.strategies.best_match import BestMatchStrategy
from src.llm_orchestrator.strategies.consensus import ConsensusStrategy
from src.llm_orchestrator.strategies.failover import FailoverStrategy

__all__ = ["FailoverStrategy", "ConsensusStrategy", "BestMatchStrategy"]
