import logging
from typing import Optional, Dict
from llm_orchestrator.orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)

class SummaryEnhancer:
    """
    Enhances summary generation using multi-LLM orchestration.
    Supports failover and consensus/best-match strategies.
    """
    def __init__(self, orchestrator: LLMOrchestrator):
        self.orchestrator = orchestrator

    async def generate_summary(self, email_text: str, strategy: str = "consensus") -> str:
        """
        Generates a 1-4 line summary using the specified orchestration strategy.
        
        Args:
            email_text: Cleaned email body
            strategy: "failover", "consensus", or "best_match"
            
        Returns:
            str: Generated summary
        """
        default_summary = "[Summary unavailable due to content policy or generation error.]"
        if strategy == "failover":
            return await self._failover_strategy(email_text, default_summary=default_summary)
        elif strategy in ["consensus", "best_match"]:
            return await self._consensus_strategy(email_text, default_summary=default_summary)
        else:
            logger.warning(f"Unknown strategy {strategy}, defaulting to failover")
            return await self._failover_strategy(email_text, default_summary=default_summary)

    async def _failover_strategy(self, email_text: str, default_summary: str) -> str:
        # Reuse orchestrator config priority
        priority_order = self.orchestrator.config.provider_priority
        
        for provider_name in priority_order:
            provider = self.orchestrator.providers.get(provider_name)
            if not provider:
                continue
            
            # Skip unhealthy providers
            if not self.orchestrator.health_tracker.is_healthy(provider_name):
                continue
                
            try:
                # Assuming provider.generate_summary is async
                summary = await provider.generate_summary(email_text)
                if summary:
                    logger.info(f"Generated summary using {provider_name}")
                    return summary
            except NotImplementedError:
                logger.debug(f"Provider {provider_name} does not support generate_summary")
            except Exception as e:
                logger.warning(f"Failed to generate summary with {provider_name}: {e}")
                self.orchestrator.health_tracker.record_failure(provider_name, str(e))
                
        logger.error("All providers failed to generate summary")
        return default_summary

    async def _consensus_strategy(self, email_text: str, default_summary: str) -> str:
        # Call all available providers
        summaries = {}
        for name, provider in self.orchestrator.providers.items():
            # Skip unhealthy providers
            if not self.orchestrator.health_tracker.is_healthy(name):
                continue

            try:
                summary = await provider.generate_summary(email_text)
                if summary:
                    summaries[name] = summary
            except NotImplementedError:
                pass
            except Exception as e:
                logger.warning(f"Failed to generate summary with {name}: {e}")
                self.orchestrator.health_tracker.record_failure(name, str(e))
        
        if not summaries:
            return default_summary
            
        # Selection logic:
        # Ideally, we would use an LLM to pick the best one, but that adds cost/latency.
        # For now, we prefer the summary from the highest priority provider that succeeded.
        priority_order = self.orchestrator.config.provider_priority
        for name in priority_order:
            if name in summaries:
                logger.info(f"Consensus/BestMatch selected {name} summary")
                return summaries[name]
                
        # Fallback
        return list(summaries.values())[0]
