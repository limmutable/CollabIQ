"""End-to-end integration tests for Phase 2c classification.

This module tests the complete classification workflow:
- Dynamic schema fetching from Notion
- Type classification based on company matching
- Intensity classification using Gemini LLM
- Summary generation preserving 5 key entities
- Confidence scoring and manual review routing

Uses real email fixtures (sample-001.txt through sample-006.txt).
"""

import pytest
from pathlib import Path


class TestClassificationE2E:
    """End-to-end tests for classification workflow."""

    @pytest.fixture
    def sample_email_dir(self):
        """Fixture providing path to sample email directory."""
        return Path(__file__).parent.parent / "fixtures" / "sample_emails"

    @pytest.mark.asyncio
    async def test_sample_001_poc_kickoff_classification(self, sample_email_dir):
        """Test: sample-001.txt (브레이크앤컴퍼니 × 신세계푸드 PoC) → type '[A]PortCoXSSG', intensity '협력'."""
        from models.classification_service import ClassificationService
        from unittest.mock import AsyncMock, Mock

        # Load sample email
        sample_path = sample_email_dir / "sample-001.txt"
        with open(sample_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        # Mock Notion integrator
        mock_notion = AsyncMock()
        mock_schema = Mock()

        # Create mock options with .name attribute
        option_a = Mock()
        option_a.name = "[A]PortCoXSSG"
        option_b = Mock()
        option_b.name = "[B]Non-PortCoXSSG"
        option_c = Mock()
        option_c.name = "[C]PortCoXPortCo"
        option_d = Mock()
        option_d.name = "[D]Other"

        mock_schema.properties = {
            "협업형태": Mock(
                type="select",
                options=[option_a, option_b, option_c, option_d],
            )
        }
        mock_notion.discover_database_schema.return_value = mock_schema

        # Mock Gemini adapter
        from llm_provider.types import ExtractedEntities, ConfidenceScores
        from datetime import datetime

        mock_gemini = Mock()
        mock_gemini.extract_entities.return_value = ExtractedEntities(
            person_in_charge="안동훈",
            startup_name="브레이크앤컴퍼니",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 10, 28),
            confidence=ConfidenceScores(
                person=0.95, startup=0.92, partner=0.90, details=0.88, date=0.85
            ),
            email_id="sample-001",
        )

        # Mock intensity classification (Gemini API response)
        import json

        mock_intensity_response = json.dumps(
            {
                "intensity": "협력",
                "confidence": 0.92,
                "reasoning": "PoC 킥오프 미팅과 파일럿 테스트 계획이 논의되어 협력 단계로 분류",
            }
        )
        mock_gemini._call_with_retry = Mock(return_value=mock_intensity_response)
        mock_gemini._call_gemini_api = Mock()

        # Create service and run classification
        service = ClassificationService(
            notion_integrator=mock_notion,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )

        result = await service.extract_with_classification(
            email_content=email_content,
            email_id="sample-001",
            matched_company_id="abc123def456ghi789jkl012mno345pq",  # 32-char Notion ID
            matched_partner_id="xyz789uvw012abc345def678ghi901jk",  # 32-char Notion ID
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
        )

        # Assertions for type classification
        assert result.collaboration_type == "[A]PortCoXSSG"
        assert result.type_confidence == 0.95

        # Assertions for intensity classification
        assert result.collaboration_intensity == "협력"
        assert result.intensity_confidence == 0.92
        assert result.intensity_reasoning is not None
        assert (
            "협력" in result.intensity_reasoning or "PoC" in result.intensity_reasoning
        )

        # Assertions for extracted entities
        assert result.startup_name == "브레이크앤컴퍼니"
        assert result.partner_org == "신세계"

        # Manual review check
        assert result.needs_manual_review() is False  # High confidence on both

    @pytest.mark.asyncio
    async def test_sample_003_investment_classification(self, sample_email_dir):
        """Test: sample-003.txt (투자 유치) → intensity '투자'."""
        from models.classification_service import ClassificationService
        from unittest.mock import AsyncMock, Mock
        import json

        # Load sample email
        sample_path = sample_email_dir / "sample-003.txt"
        with open(sample_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        # Mock Notion integrator
        mock_notion = AsyncMock()
        mock_schema = Mock()
        option_a = Mock()
        option_a.name = "[A]PortCoXSSG"
        option_b = Mock()
        option_b.name = "[B]Non-PortCoXSSG"
        option_c = Mock()
        option_c.name = "[C]PortCoXPortCo"
        option_d = Mock()
        option_d.name = "[D]Other"
        mock_schema.properties = {
            "협업형태": Mock(
                type="select", options=[option_a, option_b, option_c, option_d]
            )
        }
        mock_notion.discover_database_schema.return_value = mock_schema

        # Mock Gemini adapter
        from llm_provider.types import ExtractedEntities, ConfidenceScores
        from datetime import datetime

        mock_gemini = Mock()
        mock_gemini.extract_entities.return_value = ExtractedEntities(
            person_in_charge="이규봉",
            startup_name="스위트스팟",
            partner_org="신세계",
            details="시리즈 A 투자 유치",
            date=datetime(2025, 11, 18),
            confidence=ConfidenceScores(
                person=0.90, startup=0.95, partner=0.92, details=0.93, date=0.88
            ),
            email_id="sample-003",
        )

        # Mock intensity classification - should return "투자"
        mock_intensity_response = json.dumps(
            {
                "intensity": "투자",
                "confidence": 0.95,
                "reasoning": "시리즈 A 투자 유치 성공이 명시되어 투자 단계로 분류",
            }
        )
        mock_gemini._call_with_retry = Mock(return_value=mock_intensity_response)
        mock_gemini._call_gemini_api = Mock()

        # Create service and run classification
        service = ClassificationService(
            notion_integrator=mock_notion,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )

        result = await service.extract_with_classification(
            email_content=email_content,
            email_id="sample-003",
            matched_company_id="abc123def456ghi789jkl012mno345pq",
            matched_partner_id="xyz789uvw012abc345def678ghi901jk",
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
        )

        # Assertions for intensity classification
        assert result.collaboration_intensity == "투자"
        assert result.intensity_confidence >= 0.85
        assert result.intensity_reasoning is not None

        # Assertions for type classification
        assert result.collaboration_type == "[A]PortCoXSSG"

        # High confidence, no manual review needed
        assert result.needs_manual_review() is False

    @pytest.mark.asyncio
    async def test_sample_005_initial_meeting_classification(self, sample_email_dir):
        """Test: sample-005.txt (첫 미팅) → intensity '이해'."""
        from models.classification_service import ClassificationService
        from unittest.mock import AsyncMock, Mock
        import json

        # Load sample email
        sample_path = sample_email_dir / "sample-005.txt"
        with open(sample_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        # Mock Notion integrator
        mock_notion = AsyncMock()
        mock_schema = Mock()
        option_a = Mock()
        option_a.name = "[A]PortCoXSSG"
        option_b = Mock()
        option_b.name = "[B]Non-PortCoXSSG"
        option_c = Mock()
        option_c.name = "[C]PortCoXPortCo"
        option_d = Mock()
        option_d.name = "[D]Other"
        mock_schema.properties = {
            "협업형태": Mock(
                type="select", options=[option_a, option_b, option_c, option_d]
            )
        }
        mock_notion.discover_database_schema.return_value = mock_schema

        # Mock Gemini adapter
        from llm_provider.types import ExtractedEntities, ConfidenceScores
        from datetime import datetime

        mock_gemini = Mock()
        mock_gemini.extract_entities.return_value = ExtractedEntities(
            person_in_charge="이혜원",
            startup_name="파지티브호텔",
            partner_org="신세계",
            details="첫 미팅 결과",
            date=datetime(2025, 7, 25),
            confidence=ConfidenceScores(
                person=0.92, startup=0.90, partner=0.93, details=0.88, date=0.90
            ),
            email_id="sample-005",
        )

        # Mock intensity classification - should return "이해"
        mock_intensity_response = json.dumps(
            {
                "intensity": "이해",
                "confidence": 0.88,
                "reasoning": "첫 미팅과 협업 가능성 논의로 이해/탐색 단계로 분류",
            }
        )
        mock_gemini._call_with_retry = Mock(return_value=mock_intensity_response)
        mock_gemini._call_gemini_api = Mock()

        # Create service and run classification
        service = ClassificationService(
            notion_integrator=mock_notion,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )

        result = await service.extract_with_classification(
            email_content=email_content,
            email_id="sample-005",
            matched_company_id="abc123def456ghi789jkl012mno345pq",
            matched_partner_id="xyz789uvw012abc345def678ghi901jk",
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
        )

        # Assertions for intensity classification
        assert result.collaboration_intensity == "이해"
        assert result.intensity_confidence >= 0.80
        assert result.intensity_reasoning is not None

        # Assertions for type classification
        assert result.collaboration_type == "[A]PortCoXSSG"

        # Good confidence, no manual review needed
        assert result.needs_manual_review() is False

    @pytest.mark.asyncio
    async def test_all_sample_emails(self, sample_email_dir):
        """Test: All 6 sample emails with ground truth validation."""
        pytest.skip("Implementation pending - Phase 7 validation")

    @pytest.mark.asyncio
    async def test_classification_accuracy_above_85_percent(self):
        """Test: Classification accuracy ≥85% on test dataset (SC-001, SC-002)."""
        pytest.skip("Implementation pending - Phase 7 validation")

    @pytest.mark.asyncio
    async def test_summary_preserves_5_key_entities(self):
        """Test: Summaries preserve all 5 key entities in ≥90% of cases (SC-003)."""
        pytest.skip("Implementation pending - Phase 5")

    @pytest.mark.asyncio
    async def test_summary_word_count_within_range(self):
        """Test: Summary word count in 50-150 range for ≥95% of emails (SC-004)."""
        pytest.skip("Implementation pending - Phase 5")

    @pytest.mark.asyncio
    async def test_confidence_scores_predict_accuracy(self):
        """Test: Confidence ≥0.90 → ≥95% accuracy, 0.70-0.89 → ≥80% accuracy (SC-005)."""
        pytest.skip("Implementation pending - Phase 6")

    @pytest.mark.asyncio
    async def test_processing_time_under_4_seconds(self):
        """Test: Phase 1b + 2b + 2c completes in ≤4 seconds (SC-006)."""
        pytest.skip("Implementation pending - Phase 7 performance")

    @pytest.mark.asyncio
    async def test_manual_review_queue_under_25_percent(self):
        """Test: Manual review queue ≤25% of classifications (SC-007)."""
        pytest.skip("Implementation pending - Phase 6")
