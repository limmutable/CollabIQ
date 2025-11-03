"""Unit tests for deterministic type classification logic.

This module tests the classify_collaboration_type() method:
- Portfolio + SSG Affiliate → "[A]PortCoXSSG"
- Portfolio + Portfolio → "[C]PortCoXPortCo"
- Portfolio + External/Other → "[B]Non-PortCoXSSG"
- Non-Portfolio + Any → "[D]Other"
- Null inputs → graceful degradation
"""

import pytest
from src.models.classification_service import ClassificationService


class TestTypeClassification:
    """Unit tests for deterministic type classification."""

    @pytest.fixture
    def collaboration_types(self):
        """Fixture providing collaboration type values."""
        return {
            "A": "[A]PortCoXSSG",
            "B": "[B]Non-PortCoXSSG",
            "C": "[C]PortCoXPortCo",
            "D": "[D]Other",
        }

    @pytest.fixture
    def classification_service(self, mocker):
        """Fixture providing ClassificationService instance."""
        # Mock dependencies
        mock_notion = mocker.Mock()
        mock_gemini = mocker.Mock()

        service = ClassificationService(
            notion_integrator=mock_notion,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )
        return service

    def test_portfolio_ssg_affiliate_returns_type_a(self, classification_service, collaboration_types):
        """Test: Portfolio + SSG Affiliate → type matching '[A]*' pattern."""
        collab_type, confidence = classification_service.classify_collaboration_type(
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
            collaboration_types=collaboration_types,
        )

        assert collab_type == "[A]PortCoXSSG"
        assert confidence == 0.95  # High confidence for deterministic logic

    def test_portfolio_portfolio_returns_type_c(self, classification_service, collaboration_types):
        """Test: Portfolio + Portfolio → type matching '[C]*' pattern."""
        collab_type, confidence = classification_service.classify_collaboration_type(
            company_classification="Portfolio",
            partner_classification="Portfolio",
            collaboration_types=collaboration_types,
        )

        assert collab_type == "[C]PortCoXPortCo"
        assert confidence == 0.95

    def test_portfolio_external_returns_type_b(self, classification_service, collaboration_types):
        """Test: Portfolio + External → type matching '[B]*' pattern."""
        collab_type, confidence = classification_service.classify_collaboration_type(
            company_classification="Portfolio",
            partner_classification="Other",
            collaboration_types=collaboration_types,
        )

        assert collab_type == "[B]Non-PortCoXSSG"
        assert confidence == 0.90  # Slightly lower confidence for external

    def test_non_portfolio_returns_type_d(self, classification_service, collaboration_types):
        """Test: Non-Portfolio + Any → type matching '[D]*' pattern."""
        collab_type, confidence = classification_service.classify_collaboration_type(
            company_classification="Other",
            partner_classification="SSG Affiliate",
            collaboration_types=collaboration_types,
        )

        assert collab_type == "[D]Other"
        assert confidence == 0.80

        # Test with different partner classification
        collab_type2, confidence2 = classification_service.classify_collaboration_type(
            company_classification="Other",
            partner_classification="Portfolio",
            collaboration_types=collaboration_types,
        )

        assert collab_type2 == "[D]Other"
        assert confidence2 == 0.80

    def test_null_company_classification_returns_none(self, classification_service, collaboration_types):
        """Test: Null matched_company_id → collaboration_type = None."""
        collab_type, confidence = classification_service.classify_collaboration_type(
            company_classification=None,
            partner_classification="SSG Affiliate",
            collaboration_types=collaboration_types,
        )

        assert collab_type is None
        assert confidence is None

    def test_null_partner_classification_returns_none(self, classification_service, collaboration_types):
        """Test: Null matched_partner_id → collaboration_type = None."""
        collab_type, confidence = classification_service.classify_collaboration_type(
            company_classification="Portfolio",
            partner_classification=None,
            collaboration_types=collaboration_types,
        )

        assert collab_type is None
        assert confidence is None

    def test_uses_exact_notion_field_values(self, classification_service):
        """Test: Uses exact Notion field values from collaboration_types dict."""
        # Simulate changed field values (A/B/C/D → 1/2/3/4)
        future_collaboration_types = {
            "1": "[1]NewPortCoXSSG",
            "2": "[2]NewNonPortCoXSSG",
            "3": "[3]NewPortCoXPortCo",
            "4": "[4]NewOther",
        }

        # Portfolio + SSG should map to key "1" (was "A")
        # But our logic uses A/B/C/D, so this will fail unless we update the logic
        # For now, this test documents that collaboration_types dict must contain A/B/C/D keys
        collab_type, confidence = classification_service.classify_collaboration_type(
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
            collaboration_types=future_collaboration_types,
        )

        # Will return None because "A" key doesn't exist in future_collaboration_types
        assert collab_type is None
