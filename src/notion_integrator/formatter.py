"""
LLM-Ready Data Formatting

Formats Notion data for LLM consumption with:
- Classification field extraction (Shinsegae affiliates?, Is Portfolio?)
- JSON structure generation (CompanyRecord format)
- Markdown summary generation (grouped by type)
- Unicode handling (Korean, Japanese, emoji)
- Metadata population (counts, timestamps)

Key Functions:
- extract_classification(): Extract classification fields from page
- format_company_record(): Convert page to CompanyRecord
- generate_markdown_summary(): Generate human-readable Markdown
- format_for_llm(): Complete formatting pipeline
"""

from datetime import datetime
from typing import Any, Dict, List

from .logging_config import get_logger, PerformanceLogger
from .models import (
    CompanyClassification,
    CompanyRecord,
    DatabaseSchema,
    FormatMetadata,
    LLMFormattedData,
)


logger = get_logger(__name__)


# ==============================================================================
# Classification Field Extraction
# ==============================================================================


def extract_classification(
    page: Dict[str, Any],
    schema: DatabaseSchema,
) -> CompanyClassification:
    """
    Extract classification fields from a Notion page.

    Args:
        page: Notion page data
        schema: DatabaseSchema for field identification

    Returns:
        CompanyClassification with flags and type hint

    Notes:
        - Looks for "Shinsegae affiliates?" and "Is Portfolio?" checkboxes
        - Defaults to False if fields not found
        - Computes collaboration_type_hint based on flags
    """
    properties = page.get("properties", {})

    # Get classification field IDs from schema
    classification_fields = schema.classification_fields

    # Extract Shinsegae affiliate flag
    is_ssg = False
    if "is_shinsegae_affiliate" in classification_fields:
        ssg_prop_name = None
        # Find property name by ID
        for prop_name, prop in schema.database.properties.items():
            if prop.id == classification_fields["is_shinsegae_affiliate"]:
                ssg_prop_name = prop_name
                break

        if ssg_prop_name and ssg_prop_name in properties:
            ssg_data = properties[ssg_prop_name]
            if ssg_data.get("type") == "checkbox":
                is_ssg = ssg_data.get("checkbox", False)

    # Extract Portfolio flag
    is_portfolio = False
    if "is_portfolio_company" in classification_fields:
        portfolio_prop_name = None
        # Find property name by ID
        for prop_name, prop in schema.database.properties.items():
            if prop.id == classification_fields["is_portfolio_company"]:
                portfolio_prop_name = prop_name
                break

        if portfolio_prop_name and portfolio_prop_name in properties:
            portfolio_data = properties[portfolio_prop_name]
            if portfolio_data.get("type") == "checkbox":
                is_portfolio = portfolio_data.get("checkbox", False)

    # Create classification with computed hint
    return CompanyClassification.from_checkboxes(is_ssg, is_portfolio)


# ==============================================================================
# Property Value Extraction
# ==============================================================================


def extract_property_value(prop_data: Dict[str, Any]) -> Any:
    """
    Extract value from Notion property data.

    Args:
        prop_data: Property data from Notion API

    Returns:
        Extracted value (type depends on property type)

    Notes:
        - Handles all common Notion property types
        - Returns None for empty/null values
        - Preserves Unicode (Korean, Japanese, emoji)
    """
    prop_type = prop_data.get("type")

    if prop_type == "title":
        title_array = prop_data.get("title", [])
        if title_array:
            return title_array[0].get("text", {}).get("content", "")
        return ""

    elif prop_type == "rich_text":
        text_array = prop_data.get("rich_text", [])
        if text_array:
            # Concatenate all text segments
            return "".join(
                segment.get("text", {}).get("content", "") for segment in text_array
            )
        return ""

    elif prop_type == "number":
        return prop_data.get("number")

    elif prop_type == "select":
        select_data = prop_data.get("select")
        if select_data:
            return select_data.get("name")
        return None

    elif prop_type == "multi_select":
        multi_select = prop_data.get("multi_select", [])
        return [item.get("name") for item in multi_select]

    elif prop_type == "date":
        date_data = prop_data.get("date")
        if date_data:
            return date_data.get("start")  # ISO format string
        return None

    elif prop_type == "checkbox":
        return prop_data.get("checkbox", False)

    elif prop_type == "url":
        return prop_data.get("url")

    elif prop_type == "email":
        return prop_data.get("email")

    elif prop_type == "phone_number":
        return prop_data.get("phone_number")

    elif prop_type == "relation":
        # Return relation IDs (resolved data handled separately)
        relation_array = prop_data.get("relation", [])
        return [rel.get("id") for rel in relation_array]

    elif prop_type == "people":
        people_array = prop_data.get("people", [])
        return [person.get("name") for person in people_array]

    elif prop_type == "files":
        files_array = prop_data.get("files", [])
        return [file.get("name") for file in files_array]

    elif prop_type == "created_time":
        return prop_data.get("created_time")

    elif prop_type == "last_edited_time":
        return prop_data.get("last_edited_time")

    else:
        # Unknown type - return raw data
        return prop_data


def extract_title(page: Dict[str, Any]) -> str:
    """
    Extract title from Notion page.

    Args:
        page: Notion page data

    Returns:
        Page title (empty string if not found)
    """
    properties = page.get("properties", {})

    # Find title property
    for prop_name, prop_data in properties.items():
        if prop_data.get("type") == "title":
            title_array = prop_data.get("title", [])
            if title_array:
                return title_array[0].get("text", {}).get("content", "")

    return ""


# ==============================================================================
# JSON Formatting
# ==============================================================================


def format_company_record(
    page: Dict[str, Any],
    schema: DatabaseSchema,
) -> CompanyRecord:
    """
    Format Notion page to CompanyRecord.

    Args:
        page: Notion page data
        schema: DatabaseSchema for field identification

    Returns:
        CompanyRecord with all properties formatted

    Notes:
        - Extracts all properties with type-aware parsing
        - Preserves Unicode (Korean, Japanese, emoji)
        - Includes classification fields
        - Preserves relation data (both IDs and resolved)
    """
    # Extract basic fields
    page_id = page.get("id", "")
    name = extract_title(page)
    source_database = schema.database.title

    # Extract classification
    classification = extract_classification(page, schema)

    # Extract all properties
    properties = {}
    for prop_name, prop_data in page.get("properties", {}).items():
        # Store both the extracted value and raw data
        properties[prop_name] = {
            "type": prop_data.get("type"),
            "value": extract_property_value(prop_data),
        }

        # Preserve resolved relation data if present
        if prop_data.get("type") == "relation" and "resolved" in prop_data:
            properties[prop_name]["resolved"] = prop_data["resolved"]

    # Create CompanyRecord
    return CompanyRecord(
        id=page_id,
        name=name,
        source_database=source_database,
        classification=classification,
        properties=properties,
    )


# ==============================================================================
# Markdown Summary Generation
# ==============================================================================


def generate_markdown_summary(
    records: List[Dict[str, Any]],
) -> str:
    """
    Generate Markdown summary of companies grouped by type.

    Args:
        records: List of Notion page records

    Returns:
        Markdown-formatted summary string

    Notes:
        - Groups companies by collaboration type (SSG, PortCo, Both, Neither)
        - Includes company names and key details
        - Unicode-safe (preserves Korean, Japanese, emoji)
    """
    if not records:
        return "# Companies\n\nNo companies found.\n"

    # Group by classification
    ssg_only = []
    portfolio_only = []
    both = []
    neither = []

    for record in records:
        name = extract_title(record)
        properties = record.get("properties", {})

        # Check classification flags
        is_ssg = False
        is_portfolio = False

        for prop_name, prop_data in properties.items():
            if (
                prop_name.lower() == "shinsegae affiliates?"
                and prop_data.get("type") == "checkbox"
            ):
                is_ssg = prop_data.get("checkbox", False)
            if (
                prop_name.lower() == "is portfolio?"
                and prop_data.get("type") == "checkbox"
            ):
                is_portfolio = prop_data.get("checkbox", False)

        # Categorize
        if is_ssg and is_portfolio:
            both.append((name, record))
        elif is_ssg:
            ssg_only.append((name, record))
        elif is_portfolio:
            portfolio_only.append((name, record))
        else:
            neither.append((name, record))

    # Generate Markdown
    lines = ["# Companies Summary\n"]

    if both:
        lines.append("## Both SSG & Portfolio Companies\n")
        for name, _ in sorted(both):
            lines.append(f"- {name}")
        lines.append("")

    if ssg_only:
        lines.append("## Shinsegae Affiliates\n")
        for name, _ in sorted(ssg_only):
            lines.append(f"- {name}")
        lines.append("")

    if portfolio_only:
        lines.append("## Portfolio Companies\n")
        for name, _ in sorted(portfolio_only):
            lines.append(f"- {name}")
        lines.append("")

    if neither:
        lines.append("## Other Companies\n")
        for name, _ in sorted(neither):
            lines.append(f"- {name}")
        lines.append("")

    # Add counts
    lines.append("---\n")
    lines.append(f"**Total**: {len(records)} companies")
    if both or ssg_only:
        lines.append(f"- **SSG Affiliates**: {len(both) + len(ssg_only)}")
    if both or portfolio_only:
        lines.append(f"- **Portfolio**: {len(both) + len(portfolio_only)}")

    return "\n".join(lines)


# ==============================================================================
# Complete Formatting Pipeline
# ==============================================================================


def format_for_llm(
    records: List[Dict[str, Any]],
    schema: DatabaseSchema,
) -> LLMFormattedData:
    """
    Format Notion records for LLM consumption.

    Args:
        records: List of Notion page records
        schema: DatabaseSchema for field identification

    Returns:
        LLMFormattedData with JSON + Markdown

    Notes:
        - Formats each record to CompanyRecord
        - Generates Markdown summary
        - Populates metadata (counts, timestamps)
        - Preserves Unicode throughout
    """
    with PerformanceLogger(
        logger,
        "format_for_llm",
        record_count=len(records),
        database_name=schema.database.title,
    ):
        # Format each record
        companies = []
        ssg_count = 0
        portfolio_count = 0

        for record in records:
            company = format_company_record(record, schema)
            companies.append(company)

            # Count classifications
            if company.classification.is_shinsegae_affiliate:
                ssg_count += 1
            if company.classification.is_portfolio_company:
                portfolio_count += 1

        # Generate Markdown summary
        markdown = generate_markdown_summary(records)

        # Create metadata
        metadata = FormatMetadata(
            total_companies=len(records),
            shinsegae_affiliate_count=ssg_count,
            portfolio_company_count=portfolio_count,
            formatted_at=datetime.now(),
            data_freshness="fresh",  # Default to fresh, caller can override
            databases_included=[schema.database.title],
        )

        logger.info(
            "Data formatted for LLM",
            extra={
                "total_companies": len(records),
                "ssg_count": ssg_count,
                "portfolio_count": portfolio_count,
                "database_name": schema.database.title,
            },
        )

        return LLMFormattedData(
            companies=companies,
            summary_markdown=markdown,
            metadata=metadata,
        )


# ==============================================================================
# Batch Formatting
# ==============================================================================


def format_multiple_databases(
    data_by_database: Dict[str, List[Dict[str, Any]]],
    schemas: Dict[str, DatabaseSchema],
) -> Dict[str, LLMFormattedData]:
    """
    Format data from multiple databases.

    Args:
        data_by_database: Dict mapping database_id to records
        schemas: Dict mapping database_id to DatabaseSchema

    Returns:
        Dict mapping database_id to LLMFormattedData

    Notes:
        - Formats each database independently
        - Preserves Unicode across all databases
        - Logs formatting progress
    """
    with PerformanceLogger(
        logger,
        "format_multiple_databases",
        database_count=len(data_by_database),
    ):
        formatted_data = {}

        for database_id, records in data_by_database.items():
            if database_id not in schemas:
                logger.warning(
                    "Schema not found for database",
                    extra={"database_id": database_id},
                )
                continue

            schema = schemas[database_id]
            formatted = format_for_llm(records, schema)
            formatted_data[database_id] = formatted

            logger.debug(
                "Database formatted",
                extra={
                    "database_id": database_id,
                    "database_name": schema.database.title,
                    "record_count": len(records),
                },
            )

        logger.info(
            "Multiple databases formatted",
            extra={
                "database_count": len(formatted_data),
                "total_companies": sum(
                    data.metadata.total_companies for data in formatted_data.values()
                ),
            },
        )

        return formatted_data
