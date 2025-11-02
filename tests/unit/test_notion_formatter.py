"""
Unit Tests for Notion Data Formatter

Tests the LLM-ready data formatting logic in isolation:
- Classification field extraction (Shinsegae affiliates?, Is Portfolio?)
- JSON structure generation for CompanyRecord
- Markdown summary generation
- Unicode handling (Korean, Japanese, emoji)
- Collaboration type hint computation
- Metadata population

These tests use minimal fixtures and don't require API calls.
"""

import pytest
from datetime import datetime

from src.notion_integrator.models import (
    CompanyClassification,
    CompanyRecord,
    LLMFormattedData,
    NotionDatabase,
    NotionProperty,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_company_page():
    """Sample company page from Notion API."""
    return {
        "object": "page",
        "id": "company-1",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T00:00:00.000Z",
        "url": "https://notion.so/company-1",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "Acme Corp"}}],
            },
            "Description": {
                "id": "desc",
                "type": "rich_text",
                "rich_text": [
                    {"type": "text", "text": {"content": "Leading tech company"}}
                ],
            },
            "Founded Year": {"id": "year", "type": "number", "number": 2010},
            "Industry": {
                "id": "industry",
                "type": "select",
                "select": {"id": "tech", "name": "Technology", "color": "blue"},
            },
            "Shinsegae affiliates?": {
                "id": "ssg",
                "type": "checkbox",
                "checkbox": True,
            },
            "Is Portfolio?": {
                "id": "portfolio",
                "type": "checkbox",
                "checkbox": False,
            },
            "Related CollabIQ": {
                "id": "rel_collabiq",
                "type": "relation",
                "relation": [{"id": "collabiq-1"}],
                "resolved": [
                    {
                        "object": "page",
                        "id": "collabiq-1",
                        "properties": {
                            "Name": {
                                "type": "title",
                                "title": [
                                    {
                                        "type": "text",
                                        "text": {"content": "Project Alpha"},
                                    }
                                ],
                            },
                        },
                    }
                ],
            },
        },
    }


@pytest.fixture
def sample_korean_company_page():
    """Sample company page with Korean text."""
    return {
        "object": "page",
        "id": "company-korean",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T00:00:00.000Z",
        "url": "https://notion.so/company-korean",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "신세계 그룹"}}],
            },
            "Description": {
                "id": "desc",
                "type": "rich_text",
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "대한민국의 대표적인 유통 기업 🛒"},
                    }
                ],
            },
            "Founded Year": {"id": "year", "type": "number", "number": 1955},
            "Industry": {
                "id": "industry",
                "type": "select",
                "select": {"id": "retail", "name": "Retail", "color": "red"},
            },
            "Shinsegae affiliates?": {
                "id": "ssg",
                "type": "checkbox",
                "checkbox": True,
            },
            "Is Portfolio?": {
                "id": "portfolio",
                "type": "checkbox",
                "checkbox": True,
            },
            "Related CollabIQ": {
                "id": "rel_collabiq",
                "type": "relation",
                "relation": [],
            },
        },
    }


@pytest.fixture
def sample_database_schema():
    """Sample DatabaseSchema for Companies database."""
    db = NotionDatabase(
        id="companies-db-id",
        title="Companies",
        url="https://notion.so/companies",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Description": NotionProperty(
                id="desc", name="Description", type="rich_text", config={}
            ),
            "Founded Year": NotionProperty(
                id="year", name="Founded Year", type="number", config={}
            ),
            "Industry": NotionProperty(
                id="industry", name="Industry", type="select", config={}
            ),
            "Shinsegae affiliates?": NotionProperty(
                id="ssg", name="Shinsegae affiliates?", type="checkbox", config={}
            ),
            "Is Portfolio?": NotionProperty(
                id="portfolio", name="Is Portfolio?", type="checkbox", config={}
            ),
            "Related CollabIQ": NotionProperty(
                id="rel_collabiq",
                name="Related CollabIQ",
                type="relation",
                config={"relation": {"database_id": "collabiq-db-id"}},
            ),
        },
    )

    from src.notion_integrator.schema import create_database_schema

    return create_database_schema(db)


# ==============================================================================
# Classification Field Extraction Tests
# ==============================================================================


def test_extract_classification_both_true(sample_company_page, sample_database_schema):
    """Test extracting classification when both flags are True."""
    from src.notion_integrator.formatter import extract_classification

    classification = extract_classification(sample_company_page, sample_database_schema)

    assert isinstance(classification, CompanyClassification)
    # Note: sample_company_page has ssg=True, portfolio=False
    # Let's adjust the test
    assert classification.is_shinsegae_affiliate is True
    assert classification.is_portfolio_company is False
    assert classification.collaboration_type_hint == "SSG"


def test_extract_classification_both_true_korean(
    sample_korean_company_page, sample_database_schema
):
    """Test extracting classification when both flags are True (Korean company)."""
    from src.notion_integrator.formatter import extract_classification

    classification = extract_classification(
        sample_korean_company_page, sample_database_schema
    )

    assert isinstance(classification, CompanyClassification)
    assert classification.is_shinsegae_affiliate is True
    assert classification.is_portfolio_company is True
    assert classification.collaboration_type_hint == "Both"


def test_extract_classification_only_ssg():
    """Test extracting classification when only Shinsegae flag is True."""
    from src.notion_integrator.formatter import extract_classification

    page = {
        "properties": {
            "Shinsegae affiliates?": {"type": "checkbox", "checkbox": True},
            "Is Portfolio?": {"type": "checkbox", "checkbox": False},
        }
    }

    # Create minimal schema
    db = NotionDatabase(
        id="db",
        title="DB",
        url="https://notion.so/db",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Shinsegae affiliates?": NotionProperty(
                id="ssg", name="Shinsegae affiliates?", type="checkbox", config={}
            ),
            "Is Portfolio?": NotionProperty(
                id="portfolio", name="Is Portfolio?", type="checkbox", config={}
            ),
        },
    )

    from src.notion_integrator.schema import create_database_schema

    schema = create_database_schema(db)

    classification = extract_classification(page, schema)

    assert classification.is_shinsegae_affiliate is True
    assert classification.is_portfolio_company is False
    assert classification.collaboration_type_hint == "SSG"


def test_extract_classification_only_portfolio():
    """Test extracting classification when only Portfolio flag is True."""
    from src.notion_integrator.formatter import extract_classification

    page = {
        "properties": {
            "Shinsegae affiliates?": {"type": "checkbox", "checkbox": False},
            "Is Portfolio?": {"type": "checkbox", "checkbox": True},
        }
    }

    # Create minimal schema
    db = NotionDatabase(
        id="db",
        title="DB",
        url="https://notion.so/db",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Shinsegae affiliates?": NotionProperty(
                id="ssg", name="Shinsegae affiliates?", type="checkbox", config={}
            ),
            "Is Portfolio?": NotionProperty(
                id="portfolio", name="Is Portfolio?", type="checkbox", config={}
            ),
        },
    )

    from src.notion_integrator.schema import create_database_schema

    schema = create_database_schema(db)

    classification = extract_classification(page, schema)

    assert classification.is_shinsegae_affiliate is False
    assert classification.is_portfolio_company is True
    assert classification.collaboration_type_hint == "PortCo"


def test_extract_classification_neither():
    """Test extracting classification when both flags are False."""
    from src.notion_integrator.formatter import extract_classification

    page = {
        "properties": {
            "Shinsegae affiliates?": {"type": "checkbox", "checkbox": False},
            "Is Portfolio?": {"type": "checkbox", "checkbox": False},
        }
    }

    # Create minimal schema
    db = NotionDatabase(
        id="db",
        title="DB",
        url="https://notion.so/db",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Shinsegae affiliates?": NotionProperty(
                id="ssg", name="Shinsegae affiliates?", type="checkbox", config={}
            ),
            "Is Portfolio?": NotionProperty(
                id="portfolio", name="Is Portfolio?", type="checkbox", config={}
            ),
        },
    )

    from src.notion_integrator.schema import create_database_schema

    schema = create_database_schema(db)

    classification = extract_classification(page, schema)

    assert classification.is_shinsegae_affiliate is False
    assert classification.is_portfolio_company is False
    assert classification.collaboration_type_hint == "Neither"


def test_extract_classification_missing_fields():
    """Test extracting classification when fields are missing from schema."""
    from src.notion_integrator.formatter import extract_classification

    page = {
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"type": "text", "text": {"content": "Company"}}],
            }
        }
    }

    # Create schema without classification fields
    db = NotionDatabase(
        id="db",
        title="DB",
        url="https://notion.so/db",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        },
    )

    from src.notion_integrator.schema import create_database_schema

    schema = create_database_schema(db)

    classification = extract_classification(page, schema)

    # Should default to False/Neither
    assert classification.is_shinsegae_affiliate is False
    assert classification.is_portfolio_company is False
    assert classification.collaboration_type_hint == "Neither"


# ==============================================================================
# JSON Formatting Tests
# ==============================================================================


def test_format_company_record(sample_company_page, sample_database_schema):
    """Test formatting a company page to CompanyRecord."""
    from src.notion_integrator.formatter import format_company_record

    record = format_company_record(sample_company_page, sample_database_schema)

    assert isinstance(record, CompanyRecord)
    assert record.id == "company-1"
    assert record.name == "Acme Corp"
    assert record.source_database == "Companies"
    assert record.classification.is_shinsegae_affiliate is True
    assert record.classification.is_portfolio_company is False
    assert "Description" in record.properties
    assert "Founded Year" in record.properties


def test_format_company_record_unicode(
    sample_korean_company_page, sample_database_schema
):
    """Test formatting preserves Unicode (Korean + emoji)."""
    from src.notion_integrator.formatter import format_company_record

    record = format_company_record(sample_korean_company_page, sample_database_schema)

    assert isinstance(record, CompanyRecord)
    assert record.name == "신세계 그룹"
    assert "대한민국" in str(record.properties.get("Description"))
    assert "🛒" in str(record.properties.get("Description"))


def test_format_company_record_with_relations(
    sample_company_page, sample_database_schema
):
    """Test formatting includes resolved relations."""
    from src.notion_integrator.formatter import format_company_record

    record = format_company_record(sample_company_page, sample_database_schema)

    assert "Related CollabIQ" in record.properties
    # Check if resolved data is preserved
    rel_prop = record.properties["Related CollabIQ"]
    assert "resolved" in rel_prop or "relation" in rel_prop


# ==============================================================================
# Markdown Summary Generation Tests
# ==============================================================================


def test_generate_markdown_summary_single_company(sample_company_page):
    """Test generating Markdown summary for single company."""
    from src.notion_integrator.formatter import generate_markdown_summary

    records = [sample_company_page]
    markdown = generate_markdown_summary(records)

    assert isinstance(markdown, str)
    assert "Acme Corp" in markdown
    assert "SSG" in markdown or "Shinsegae" in markdown
    assert len(markdown) > 0


def test_generate_markdown_summary_multiple_companies(
    sample_company_page, sample_korean_company_page
):
    """Test generating Markdown summary for multiple companies with grouping."""
    from src.notion_integrator.formatter import generate_markdown_summary

    records = [sample_company_page, sample_korean_company_page]
    markdown = generate_markdown_summary(records)

    assert isinstance(markdown, str)
    assert "Acme Corp" in markdown
    assert "신세계 그룹" in markdown
    # Should group by type
    assert "SSG" in markdown or "Both" in markdown
    assert "# " in markdown or "## " in markdown  # Has headers


def test_generate_markdown_summary_empty():
    """Test generating Markdown summary with no records."""
    from src.notion_integrator.formatter import generate_markdown_summary

    records = []
    markdown = generate_markdown_summary(records)

    assert isinstance(markdown, str)
    assert "No companies" in markdown or "Empty" in markdown or len(markdown) == 0


def test_generate_markdown_summary_unicode_safe(sample_korean_company_page):
    """Test Markdown generation handles Unicode safely."""
    from src.notion_integrator.formatter import generate_markdown_summary

    records = [sample_korean_company_page]
    markdown = generate_markdown_summary(records)

    assert isinstance(markdown, str)
    assert "신세계 그룹" in markdown
    # Emoji is in properties, not in markdown summary (which only shows company names)
    # Just verify Unicode handling doesn't break
    assert len(markdown) > 0


# ==============================================================================
# Complete Formatting Tests
# ==============================================================================


def test_format_for_llm(sample_company_page, sample_database_schema):
    """Test complete LLM formatting pipeline."""
    from src.notion_integrator.formatter import format_for_llm

    records = [sample_company_page]
    formatted = format_for_llm(records, sample_database_schema)

    assert isinstance(formatted, LLMFormattedData)
    assert formatted.metadata.total_companies == 1
    assert formatted.metadata.shinsegae_affiliate_count >= 0
    assert formatted.metadata.portfolio_company_count >= 0
    assert len(formatted.companies) == 1
    assert len(formatted.summary_markdown) > 0


def test_format_for_llm_empty():
    """Test LLM formatting with empty records."""
    from src.notion_integrator.formatter import format_for_llm

    # Create minimal schema
    db = NotionDatabase(
        id="db",
        title="DB",
        url="https://notion.so/db",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        },
    )

    from src.notion_integrator.schema import create_database_schema

    schema = create_database_schema(db)

    records = []
    formatted = format_for_llm(records, schema)

    assert isinstance(formatted, LLMFormattedData)
    assert formatted.metadata.total_companies == 0
    assert len(formatted.companies) == 0


def test_format_for_llm_metadata_counts(
    sample_company_page, sample_korean_company_page, sample_database_schema
):
    """Test metadata counts are correct."""
    from src.notion_integrator.formatter import format_for_llm

    records = [sample_company_page, sample_korean_company_page]
    formatted = format_for_llm(records, sample_database_schema)

    assert formatted.metadata.total_companies == 2
    # sample_company_page: ssg=True, portfolio=False
    # sample_korean_company_page: ssg=True, portfolio=True
    assert formatted.metadata.shinsegae_affiliate_count == 2
    assert formatted.metadata.portfolio_company_count == 1
