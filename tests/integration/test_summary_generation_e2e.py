"""End-to-end integration tests for Phase 2c summary generation.

This module tests the complete summary generation workflow:
- Summary preserves all 5 key entities (startup, partner, activity, date, person)
- Summary omits email signatures and disclaimers
- Summary word count stays within 50-150 range

Uses real email fixtures (sample-001.txt through sample-006.txt).
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock
import json


class TestSummaryGenerationE2E:
    """End-to-end tests for summary generation workflow."""

    @pytest.fixture
    def sample_email_dir(self):
        """Fixture providing path to sample email directory."""
        return Path(__file__).parent.parent / "fixtures" / "sample_emails"

    @pytest.fixture
    def mock_notion_schema(self):
        """Fixture providing mocked Notion schema with collaboration types."""
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
        return mock_schema

    @pytest.mark.asyncio
    async def test_sample_001_summary_preserves_all_entities(
        self, sample_email_dir, mock_notion_schema
    ):
        """Test: sample-001.txt summary preserves startup, partner, activity, date, person."""
        from src.models.classification_service import ClassificationService
        from src.llm_provider.types import ExtractedEntities, ConfidenceScores
        from datetime import datetime

        # Load sample email
        sample_path = sample_email_dir / "sample-001.txt"
        with open(sample_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        # Mock Notion integrator
        mock_notion = AsyncMock()
        mock_notion.discover_database_schema.return_value = mock_notion_schema

        # Mock Gemini adapter
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

        # Mock intensity classification
        mock_intensity_response = json.dumps({
            "intensity": "협력",
            "confidence": 0.92,
            "reasoning": "PoC 킥오프 미팅과 파일럿 테스트 계획이 논의되어 협력 단계로 분류"
        })

        # Mock summary generation
        mock_summary_response = json.dumps({
            "summary": "브레이크앤컴퍼니(안동훈 팀장)와 신세계푸드가 2025년 10월 28일 PoC 킥오프 미팅을 진행했습니다. 이번 협업에서는 간편식 제품 라인업 확대를 위한 파일럿 테스트를 계획하고 있으며, 향후 본격적인 협력 방안을 논의할 예정입니다. 신세계푸드는 브레이크앤컴퍼니의 기술력을 활용한 새로운 간편식 개발에 관심을 보이고 있습니다.",
            "word_count": 95,
            "key_entities_preserved": {
                "person_in_charge": True,
                "startup_name": True,
                "partner_org": True,
                "details": True,
                "date": True
            }
        })

        # Setup mock to return different responses for intensity vs summary
        call_count = [0]
        def mock_call_with_retry(func):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_intensity_response
            else:
                return mock_summary_response

        mock_gemini._call_with_retry = Mock(side_effect=mock_call_with_retry)
        mock_gemini._call_gemini_api = Mock()

        # Create service and run classification with summarization
        service = ClassificationService(
            notion_integrator=mock_notion,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )

        result = await service.extract_with_classification(
            email_content=email_content,
            email_id="sample-001",
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
        )

        # Verify summary was generated
        assert result.collaboration_summary is not None
        assert len(result.collaboration_summary) >= 50
        assert result.summary_word_count is not None
        assert 50 <= result.summary_word_count <= 150

        # Verify all key entities preserved
        assert result.key_entities_preserved is not None
        assert result.key_entities_preserved["person_in_charge"] is True
        assert result.key_entities_preserved["startup_name"] is True
        assert result.key_entities_preserved["partner_org"] is True
        assert result.key_entities_preserved["details"] is True
        assert result.key_entities_preserved["date"] is True

        # Verify entities appear in summary
        assert "브레이크앤컴퍼니" in result.collaboration_summary
        assert "신세계" in result.collaboration_summary
        assert "PoC" in result.collaboration_summary or "킥오프" in result.collaboration_summary

    @pytest.mark.asyncio
    async def test_sample_003_summary_omits_signature(
        self, sample_email_dir, mock_notion_schema
    ):
        """Test: sample-003.txt summary omits email signature (이성범 이사)."""
        from src.models.classification_service import ClassificationService
        from src.llm_provider.types import ExtractedEntities, ConfidenceScores
        from datetime import datetime

        # Load sample email
        sample_path = sample_email_dir / "sample-003.txt"
        with open(sample_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        # Verify sample contains signature
        assert "이성범 이사" in email_content

        # Mock Notion integrator
        mock_notion = AsyncMock()
        mock_notion.discover_database_schema.return_value = mock_notion_schema

        # Mock Gemini adapter
        mock_gemini = Mock()
        mock_gemini.extract_entities.return_value = ExtractedEntities(
            person_in_charge="임정민",
            startup_name="스위트스팟",
            partner_org="신세계라이브쇼핑",
            details="골프 거리측정계 라이브 커머스 협업",
            date=datetime(2025, 11, 18),
            confidence=ConfidenceScores(
                person=0.95, startup=0.92, partner=0.90, details=0.88, date=0.85
            ),
            email_id="sample-003",
        )

        # Mock intensity classification
        mock_intensity_response = json.dumps({
            "intensity": "협력",
            "confidence": 0.90,
            "reasoning": "라이브 커머스 방송 계획과 앱 내 단독 딜 코너 오픈이 논의되어 협력 단계로 분류"
        })

        # Mock summary generation (signature should be omitted)
        mock_summary_response = json.dumps({
            "summary": "스위트스팟이 시리즈 A 투자 유치(50억원, 리드 투자사: 시그나이트)에 성공했으며, 신세계라이브쇼핑과 골프용품 라이브 커머스 협업을 진행 중입니다. 11월 중 신세계라이브쇼핑 전용 골프 특가 방송(월 1회)을 시작하고, 스위트스팟 앱 내 신세계 골프웨어 단독 딜 코너를 오픈할 계획입니다. 2026년 Q1부터 본격적인 협업이 시작될 예정입니다.",
            "word_count": 88,
            "key_entities_preserved": {
                "person_in_charge": True,
                "startup_name": True,
                "partner_org": True,
                "details": True,
                "date": True
            }
        })

        # Setup mock to return different responses
        call_count = [0]
        def mock_call_with_retry(func):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_intensity_response
            else:
                return mock_summary_response

        mock_gemini._call_with_retry = Mock(side_effect=mock_call_with_retry)
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
            company_classification="Portfolio",
            partner_classification="External",
        )

        # Verify summary was generated
        assert result.collaboration_summary is not None
        assert len(result.collaboration_summary) >= 50

        # Verify signature "이성범 이사" is NOT in summary
        # (Summary should focus on collaboration details, not email sender signature)
        assert "이성범 이사" not in result.collaboration_summary

        # Verify key collaboration details ARE in summary
        assert "스위트스팟" in result.collaboration_summary
        assert "신세계" in result.collaboration_summary

    @pytest.mark.asyncio
    async def test_sample_005_summary_within_word_count_range(
        self, sample_email_dir, mock_notion_schema
    ):
        """Test: sample-005.txt summary has word count in 50-150 range."""
        from src.models.classification_service import ClassificationService
        from src.llm_provider.types import ExtractedEntities, ConfidenceScores
        from datetime import datetime

        # Load sample email
        sample_path = sample_email_dir / "sample-005.txt"
        with open(sample_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        # Mock Notion integrator
        mock_notion = AsyncMock()
        mock_notion.discover_database_schema.return_value = mock_notion_schema

        # Mock Gemini adapter
        mock_gemini = Mock()
        mock_gemini.extract_entities.return_value = ExtractedEntities(
            person_in_charge="김주영",
            startup_name="파지티브호텔",
            partner_org="신세계백화점",
            details="호텔 예약 플랫폼 협업 논의",
            date=datetime(2025, 7, 25),
            confidence=ConfidenceScores(
                person=0.95, startup=0.92, partner=0.90, details=0.88, date=0.85
            ),
            email_id="sample-005",
        )

        # Mock intensity classification
        mock_intensity_response = json.dumps({
            "intensity": "이해",
            "confidence": 0.88,
            "reasoning": "첫 미팅 결과 공유 및 협업 가능성 논의 단계로 이해 단계로 분류"
        })

        # Mock summary generation (within 50-150 word count)
        mock_summary_response = json.dumps({
            "summary": "파지티브호텔 장예지 대표가 신세계백화점과 호텔 예약 플랫폼 협업 가능성을 논의했습니다. 파지티브호텔은 호텔 재고 최적화 및 다이나믹 프라이싱 SaaS를 제공하며, 국내 중소형 호텔 200여 곳이 사용 중이고 월 거래액은 약 100억원입니다. 협업 안건으로는 신세계백화점 VIP 고객 대상 호텔 제휴 프로그램, SSG PAY 연동 특가 예약 서비스, 신세계 상품권 결제 지원 등이 논의되었습니다.",
            "word_count": 120,
            "key_entities_preserved": {
                "person_in_charge": True,
                "startup_name": True,
                "partner_org": True,
                "details": True,
                "date": True
            }
        })

        # Setup mock to return different responses
        call_count = [0]
        def mock_call_with_retry(func):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_intensity_response
            else:
                return mock_summary_response

        mock_gemini._call_with_retry = Mock(side_effect=mock_call_with_retry)
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
            company_classification="Portfolio",
            partner_classification="External",
        )

        # Verify summary word count is within range
        assert result.summary_word_count is not None
        assert 50 <= result.summary_word_count <= 150, (
            f"Word count {result.summary_word_count} outside expected range [50, 150]"
        )

        # Verify summary length constraint (50-750 characters)
        assert result.collaboration_summary is not None
        assert 50 <= len(result.collaboration_summary) <= 750

        # Verify all key entities preserved
        assert result.key_entities_preserved is not None
        assert all(result.key_entities_preserved.values()), (
            "All key entities should be preserved in summary"
        )
