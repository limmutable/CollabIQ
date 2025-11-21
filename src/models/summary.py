from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CollaborationSummary(BaseModel):
    """
    Represents a concise summary of collaboration content extracted from an email.
    """
    summary_text: str = Field(..., max_length=400, description="The 1-4 line summary of the collaboration content.")
    orchestration_strategy: str = Field(..., description="The orchestration strategy used (e.g., consensus, best-match).")
    contributing_llm_models: List[str] = Field(..., description="List of LLM models that contributed to the summary generation.")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="A quality score for the generated summary.")
    generation_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of when the summary was generated.")
