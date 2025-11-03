"""Classification service for Phase 2c: Type and intensity classification.

This module orchestrates collaboration classification:
- Fetch "협업형태" values dynamically from Notion
- Classify type deterministically based on Phase 2b company matching
- Classify intensity using Gemini LLM Korean semantic analysis
- Generate summaries preserving 5 key entities
- Return confidence scores for auto-acceptance vs manual review
"""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for classifying collaboration type and intensity.

    This service coordinates:
    1. Dynamic schema fetching from Notion (via NotionIntegrator)
    2. Deterministic type classification (Portfolio+SSG → "[A]PortCoXSSG", etc.)
    3. LLM-based intensity classification (이해/협력/투자/인수)
    4. Summary generation (3-5 sentences, 50-150 words)
    5. Confidence scoring (0.85 threshold for auto-acceptance)

    Attributes:
        notion_integrator: NotionIntegrator for dynamic schema fetching
        gemini_adapter: GeminiAdapter for LLM classification and summarization
        collabiq_db_id: Notion database ID for CollabIQ database
        _type_values_cache: Session-level cache for collaboration type values
    """

    def __init__(
        self,
        notion_integrator,  # NotionIntegrator from Phase 2a
        gemini_adapter,  # GeminiAdapter from Phase 1b
        collabiq_db_id: str,
    ):
        """Initialize classification service.

        Args:
            notion_integrator: NotionIntegrator instance for schema fetching
            gemini_adapter: GeminiAdapter instance for LLM operations
            collabiq_db_id: Notion database ID for CollabIQ database
        """
        self.notion = notion_integrator
        self.gemini = gemini_adapter
        self.collabiq_db_id = collabiq_db_id
        self._type_values_cache: Optional[Dict[str, str]] = None

        logger.info(
            "ClassificationService initialized",
            extra={
                "collabiq_db_id": collabiq_db_id,
                "cache_enabled": True,
            },
        )

    async def get_collaboration_types(self) -> Dict[str, str]:
        """Fetch and parse collaboration type values from Notion.

        Fetches "협업형태" property values from Notion CollabIQ database
        and parses them into {code: full_value} dict. Values are cached
        for session duration to avoid repeated API calls.

        Returns:
            Dict mapping type codes to exact Notion field values.
            Example: {"A": "[A]PortCoXSSG", "B": "[B]Non-PortCoXSSG", ...}

        Raises:
            ValueError: If "협업형태" property not found or invalid type
        """
        if self._type_values_cache is None:
            logger.info("Fetching collaboration types from Notion", extra={"db_id": self.collabiq_db_id})

            schema = await self.notion.discover_database_schema(self.collabiq_db_id)
            collab_type_prop = schema.properties.get("협업형태")

            if not collab_type_prop:
                error_msg = "협업형태 property not found in CollabIQ database"
                logger.error(error_msg, extra={"db_id": self.collabiq_db_id})
                raise ValueError(error_msg)

            if collab_type_prop.type != "select":
                error_msg = f"협업형태 property has invalid type: {collab_type_prop.type} (expected: select)"
                logger.error(error_msg, extra={"db_id": self.collabiq_db_id})
                raise ValueError(error_msg)

            # Parse options into {code: full_value} dict
            self._type_values_cache = {}
            for option in collab_type_prop.options:
                match = re.match(r'^\[([A-Z0-9]+)\]', option.name)
                if match:
                    code = match.group(1)
                    self._type_values_cache[code] = option.name

            logger.info(
                "Collaboration types fetched and cached",
                extra={
                    "type_count": len(self._type_values_cache),
                    "types": list(self._type_values_cache.keys()),
                },
            )

        return self._type_values_cache

    def classify_collaboration_type(
        self,
        company_classification: Optional[str],
        partner_classification: Optional[str],
        collaboration_types: Dict[str, str],
    ) -> tuple[Optional[str], Optional[float]]:
        """Classify collaboration type deterministically.

        Uses Phase 2b company classifications to determine type:
        - Portfolio + SSG Affiliate → "[A]PortCoXSSG"
        - Portfolio + Portfolio → "[C]PortCoXPortCo"
        - Portfolio + External/Other → "[B]Non-PortCoXSSG"
        - Non-Portfolio + Any → "[D]Other"

        Args:
            company_classification: Company type ("Portfolio", "SSG Affiliate", "Other")
            partner_classification: Partner type ("Portfolio", "SSG Affiliate", "Other")
            collaboration_types: Dict mapping codes to exact Notion field values

        Returns:
            Tuple of (collaboration_type, confidence_score):
            - collaboration_type: Exact Notion field value or None if cannot classify
            - confidence: 0.95 (Portfolio+SSG), 0.90 (Portfolio+External), 0.80 (Other), None if cannot classify
        """
        if not company_classification or not partner_classification:
            logger.warning(
                "Cannot classify type: missing company or partner classification",
                extra={
                    "company_classification": company_classification,
                    "partner_classification": partner_classification,
                },
            )
            return (None, None)

        # Deterministic classification logic
        if company_classification == "Portfolio" and partner_classification == "SSG Affiliate":
            type_code = "A"
            confidence = 0.95
        elif company_classification == "Portfolio" and partner_classification == "Portfolio":
            type_code = "C"
            confidence = 0.95
        elif company_classification == "Portfolio":
            # External or Other
            type_code = "B"
            confidence = 0.90
        else:
            # Non-Portfolio
            type_code = "D"
            confidence = 0.80

        collaboration_type = collaboration_types.get(type_code)

        logger.info(
            "Type classification completed",
            extra={
                "company_classification": company_classification,
                "partner_classification": partner_classification,
                "type_code": type_code,
                "collaboration_type": collaboration_type,
                "confidence": confidence,
            },
        )

        return (collaboration_type, confidence)

    async def classify_intensity(
        self,
        email_content: str,
        details: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[float], Optional[str]]:
        """Classify collaboration intensity using Gemini LLM.

        Uses Korean semantic analysis to determine intensity level based on
        activity keywords and context.

        Intensity Levels:
        - 이해 (Understanding/Exploration): 초기 미팅, 탐색, 논의, 가능성 검토
        - 협력 (Cooperation/Pilot): PoC, 파일럿, 테스트, 프로토타입, 협업 진행
        - 투자 (Investment): 투자 검토, DD, 밸류에이션, 계약 검토
        - 인수 (Acquisition): 인수 협상, M&A, 통합 논의, 최종 계약

        Args:
            email_content: Full email text for context
            details: Extracted collaboration details (optional, for focused analysis)

        Returns:
            Tuple of (intensity, confidence, reasoning):
            - intensity: One of ["이해", "협력", "투자", "인수"] or None
            - confidence: 0.0-1.0 confidence score or None
            - reasoning: 1-2 sentence explanation or None
        """
        import json

        # Prepare content for analysis
        analysis_text = details if details else email_content

        if not analysis_text or not analysis_text.strip():
            logger.warning("No content provided for intensity classification")
            return (None, None, None)

        # LLM prompt for intensity classification
        prompt = f"""Analyze this Korean business collaboration email and classify its intensity level.

Intensity Levels (choose ONE):
- 이해: Initial meetings, exploration, possibility discussions (초기 미팅, 탐색, 논의, 가능성 검토)
- 협력: PoC, pilot tests, prototypes, active collaboration (PoC, 파일럿, 테스트, 프로토타입, 협업 진행)
- 투자: Investment review, due diligence, valuation, contract review (투자 검토, DD, 밸류에이션, 계약 검토)
- 인수: Acquisition negotiations, M&A, integration discussions, final contracts (인수 협상, M&A, 통합 논의, 최종 계약)

Email Content:
{analysis_text}

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{{
  "intensity": "이해" | "협력" | "투자" | "인수",
  "confidence": 0.0-1.0,
  "reasoning": "1-2 sentence explanation in Korean"
}}"""

        try:
            # Call Gemini API (using internal method)
            logger.info("Calling Gemini for intensity classification")

            # Use Gemini's internal _call_gemini_api method
            import asyncio
            response_text = await asyncio.to_thread(
                self.gemini._call_with_retry,
                lambda: self.gemini._call_gemini_api(
                    prompt=prompt,
                    temperature=0.1,  # Low temperature for consistent classification
                )
            )

            response_text = response_text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)

            intensity = result.get("intensity")
            confidence = result.get("confidence")
            reasoning = result.get("reasoning")

            # Validate intensity value
            valid_intensities = ["이해", "협력", "투자", "인수"]
            if intensity not in valid_intensities:
                logger.error(
                    f"Invalid intensity value from LLM: {intensity}",
                    extra={"valid_values": valid_intensities},
                )
                return (None, None, None)

            # Validate confidence range
            if confidence is not None and (confidence < 0.0 or confidence > 1.0):
                logger.warning(
                    f"Confidence out of range: {confidence}, clamping to [0.0, 1.0]"
                )
                confidence = max(0.0, min(1.0, confidence))

            logger.info(
                "Intensity classification completed",
                extra={
                    "intensity": intensity,
                    "confidence": confidence,
                    "reasoning": reasoning[:100] if reasoning else None,
                },
            )

            return (intensity, confidence, reasoning)

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Gemini response as JSON",
                extra={"error": str(e), "response": response_text[:200]},
            )
            return (None, None, None)
        except Exception as e:
            logger.error(
                "Error during intensity classification",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            return (None, None, None)

    async def extract_with_classification(
        self,
        email_content: str,
        email_id: str,
        matched_company_id: Optional[str] = None,
        matched_partner_id: Optional[str] = None,
        company_classification: Optional[str] = None,
        partner_classification: Optional[str] = None,
    ):
        """Extract entities with Phase 2c classification and summarization.

        Orchestrates the complete Phase 1b + 2c workflow:
        1. Extract 5 key entities using Gemini LLM
        2. Classify collaboration type based on company classifications
        3. Return ExtractedEntitiesWithClassification

        Args:
            email_content: Cleaned email text (from Phase 1a)
            email_id: Unique email identifier
            matched_company_id: Company ID from Phase 2b matching (optional)
            matched_partner_id: Partner ID from Phase 2b matching (optional)
            company_classification: Company type ("Portfolio", "SSG Affiliate", "Other")
            partner_classification: Partner type ("Portfolio", "SSG Affiliate", "Other")

        Returns:
            ExtractedEntitiesWithClassification with all Phase 1b/2b/2c fields

        Example:
            >>> service = ClassificationService(notion, gemini, db_id)
            >>> result = await service.extract_with_classification(
            ...     email_content="브레이크앤컴퍼니 × 신세계푸드 PoC 킥오프",
            ...     email_id="msg_001",
            ...     matched_company_id="abc123",
            ...     matched_partner_id="xyz789",
            ...     company_classification="Portfolio",
            ...     partner_classification="SSG Affiliate"
            ... )
            >>> result.collaboration_type
            '[A]PortCoXSSG'
            >>> result.type_confidence
            0.95
        """
        from src.llm_provider.types import ExtractedEntitiesWithClassification
        from datetime import datetime

        logger.info(
            "Starting extraction with classification",
            extra={
                "email_id": email_id,
                "has_company_classification": company_classification is not None,
                "has_partner_classification": partner_classification is not None,
            },
        )

        # Step 1: Extract 5 key entities using Gemini
        entities = self.gemini.extract_entities(email_content)

        # Step 2: Fetch collaboration type values from Notion
        collaboration_types = await self.get_collaboration_types()

        # Step 3: Classify collaboration type
        collaboration_type, type_confidence = self.classify_collaboration_type(
            company_classification=company_classification,
            partner_classification=partner_classification,
            collaboration_types=collaboration_types,
        )

        # Step 4: Classify collaboration intensity
        collaboration_intensity, intensity_confidence, intensity_reasoning = await self.classify_intensity(
            email_content=email_content,
            details=entities.details,
        )

        # Step 5: Create ExtractedEntitiesWithClassification with all fields
        result = ExtractedEntitiesWithClassification(
            # Phase 1b fields
            person_in_charge=entities.person_in_charge,
            startup_name=entities.startup_name,
            partner_org=entities.partner_org,
            details=entities.details,
            date=entities.date,
            confidence=entities.confidence,
            email_id=email_id,
            extracted_at=entities.extracted_at,
            # Phase 2b fields
            matched_company_id=matched_company_id,
            matched_partner_id=matched_partner_id,
            startup_match_confidence=getattr(entities, "startup_match_confidence", None),
            partner_match_confidence=getattr(entities, "partner_match_confidence", None),
            # Phase 2c type classification fields
            collaboration_type=collaboration_type,
            type_confidence=type_confidence,
            classification_timestamp=datetime.utcnow().isoformat(),
            # Phase 2c intensity classification fields
            collaboration_intensity=collaboration_intensity,
            intensity_confidence=intensity_confidence,
            intensity_reasoning=intensity_reasoning,
            # Phase 2c summary fields (not yet implemented in Phase 5)
            collaboration_summary=None,
            summary_word_count=None,
            key_entities_preserved=None,
        )

        logger.info(
            "Extraction with classification completed",
            extra={
                "email_id": email_id,
                "collaboration_type": collaboration_type,
                "type_confidence": type_confidence,
                "collaboration_intensity": collaboration_intensity,
                "intensity_confidence": intensity_confidence,
                "needs_manual_review": result.needs_manual_review(),
            },
        )

        return result
