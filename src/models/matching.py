"""
Fuzzy matching result models for Notion field population.

This module defines Pydantic models for representing the results of fuzzy
matching operations for company names and person names.
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class CompanyMatch(BaseModel):
    """
    Result of fuzzy company name matching.

    Used to populate relation fields (스타트업명, 협력기관) by matching
    extracted company names to the Notion Companies database.

    Attributes:
        page_id: Notion page ID of matched company (None if no match)
        company_name: Name of matched company from database
        similarity_score: Jaro-Winkler similarity score (0.0-1.0)
        match_type: How the match was determined
        confidence_level: Confidence in the match quality
        was_created: Whether a new company entry was auto-created
        match_method: Algorithm used (for evaluation/monitoring)
    """

    page_id: Optional[str] = Field(
        None, description="Notion page ID of matched company"
    )
    company_name: str = Field(..., description="Name of matched company")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Similarity score (0.0-1.0)"
    )
    match_type: Literal["exact", "fuzzy", "created", "none", "semantic"] = Field(
        ..., description="Type of match"
    )
    confidence_level: Literal["high", "medium", "low", "none"] = Field(
        ..., description="Confidence in match quality"
    )
    was_created: bool = Field(
        False, description="Whether company was auto-created"
    )
    match_method: Optional[Literal["character", "llm", "hybrid"]] = Field(
        None, description="Algorithm used (for evaluation/monitoring)"
    )

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate field consistency constraints."""
        # Validate similarity score consistency
        if self.match_type == "exact" and self.similarity_score != 1.0:
            raise ValueError("Exact match must have similarity 1.0")
        if self.match_type == "fuzzy" and not (0.85 <= self.similarity_score < 1.0):
            raise ValueError("Fuzzy match must have similarity 0.85-0.99")
        if self.match_type == "semantic" and not (0.70 <= self.similarity_score < 1.0):
            raise ValueError("Semantic match must have similarity 0.70-0.99")

        # Validate page_id consistency
        if self.match_type == "none" and self.page_id is not None:
            raise ValueError("Match type 'none' must have page_id=None")
        if self.match_type in ["exact", "fuzzy", "semantic", "created"] and self.page_id is None:
            raise ValueError(f"Match type '{self.match_type}' must have non-None page_id")

        # Validate was_created consistency
        if self.was_created and self.match_type != "created":
            raise ValueError("was_created=True requires match_type='created'")
        if not self.was_created and self.match_type == "created":
            raise ValueError("match_type='created' requires was_created=True")

        return self

    class Config:
        """Pydantic model configuration with example."""

        json_schema_extra = {
            "example": {
                "page_id": "abc123def456",
                "company_name": "웨이크",
                "similarity_score": 0.87,
                "match_type": "fuzzy",
                "confidence_level": "medium",
                "was_created": False,
                "match_method": "character",
            }
        }


class PersonMatch(BaseModel):
    """
    Result of person name matching.

    Used to populate people field (담당자) by matching extracted person names
    to Notion workspace users.

    Attributes:
        user_id: Notion user UUID (None if no match)
        user_name: Full name of matched user
        similarity_score: Name similarity score (0.0-1.0)
        match_type: How the match was determined
        confidence_level: Confidence in the match quality
        is_ambiguous: Whether multiple users had similar scores
        alternative_matches: Other potential matches (if ambiguous)
    """

    user_id: Optional[str] = Field(None, description="Notion user UUID")
    user_name: Optional[str] = Field(None, description="Full name of matched user")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Similarity score (0.0-1.0)"
    )
    match_type: Literal["exact", "fuzzy", "none"] = Field(
        ..., description="Type of match"
    )
    confidence_level: Literal["high", "medium", "low", "none"] = Field(
        ..., description="Confidence in match quality"
    )
    is_ambiguous: bool = Field(
        False, description="Multiple similar matches found"
    )
    alternative_matches: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Other potential matches (if ambiguous)",
    )

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate field consistency constraints."""
        # Validate user_id consistency
        if self.match_type == "none" and self.user_id is not None:
            raise ValueError("Match type 'none' must have user_id=None")
        if self.match_type in ["exact", "fuzzy"] and self.user_id is None:
            raise ValueError(f"Match type '{self.match_type}' must have non-None user_id")

        # Validate user_name consistency
        if self.user_id is not None and not self.user_name:
            raise ValueError("user_name must be non-empty when user_id is present")

        # Validate similarity score consistency
        if self.match_type == "exact" and self.similarity_score != 1.0:
            raise ValueError("Exact match must have similarity 1.0")
        if self.match_type == "fuzzy" and not (0.70 <= self.similarity_score < 1.0):
            raise ValueError("Fuzzy match must have similarity 0.70-0.99")
        if self.match_type == "none" and self.similarity_score >= 0.70:
            raise ValueError("Match type 'none' must have similarity < 0.70")

        # Validate alternative_matches consistency
        if self.is_ambiguous and not self.alternative_matches:
            raise ValueError("is_ambiguous=True requires non-empty alternative_matches")

        return self

    class Config:
        """Pydantic model configuration with example."""

        json_schema_extra = {
            "example": {
                "user_id": "user-uuid-789",
                "user_name": "김철수 (Cheolsu Kim)",
                "similarity_score": 0.95,
                "match_type": "exact",
                "confidence_level": "high",
                "is_ambiguous": False,
                "alternative_matches": [],
            }
        }
