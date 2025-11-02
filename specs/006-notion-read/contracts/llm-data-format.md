# Data Format Contract: LLM Output

**Feature**: 006-notion-read
**Purpose**: Define the structured format for Notion data optimized for LLM consumption

---

## Overview

This contract specifies the exact JSON structure and Markdown format for Notion database data presented to LLMs. The format prioritizes:
1. **Easy company lookup** by name or ID
2. **Prominent classification fields** for collaboration type determination
3. **Human-readable summaries** for LLM context understanding
4. **Relationship clarity** showing connections between records

---

## JSON Structure

### Root Object

```typescript
interface LLMFormattedData {
    companies: CompanyRecord[];          // All company records
    summary_markdown: string;             // Human-readable summary
    metadata: FormatMetadata;             // Metadata about the dataset
}
```

### CompanyRecord

```typescript
interface CompanyRecord {
    id: string;                          // Notion page ID (UUID)
    name: string;                        // Company name (from title property)
    classification: CompanyClassification;  // Classification flags
    source_database: string;             // "Companies" or "CollabIQ"
    properties: Record<string, any>;     // All other properties (dynamic)
    related_records: RelatedRecord[];    // Resolved relationships (if any)
}
```

**Field Requirements**:
- `id`: MUST be valid Notion page ID
- `name`: MUST NOT be empty, extracted from title property
- `classification`: MUST be present with both flags
- `source_database`: MUST be "Companies" or "CollabIQ"
- `properties`: MAY be empty, MUST NOT include title/classification (already extracted)
- `related_records`: MAY be empty if no relationships

### CompanyClassification

```typescript
interface CompanyClassification {
    is_shinsegae_affiliate: boolean;     // "Shinsegae affiliates?" checkbox
    is_portfolio_company: boolean;       // "Is Portfolio?" checkbox
    collaboration_type_hint: string;     // One of: "SSG", "PortCo", "Both", "Neither"
}
```

**Field Rules**:
- `is_shinsegae_affiliate`: Directly maps to "Shinsegae affiliates?" checkbox (default: false if missing)
- `is_portfolio_company`: Directly maps to "Is Portfolio?" checkbox (default: false if missing)
- `collaboration_type_hint`: Computed helper field for quick identification
  - "SSG": `is_shinsegae_affiliate=true, is_portfolio_company=false`
  - "PortCo": `is_shinsegae_affiliate=false, is_portfolio_company=true`
  - "Both": `is_shinsegae_affiliate=true, is_portfolio_company=true`
  - "Neither": `is_shinsegae_affiliate=false, is_portfolio_company=false`

### RelatedRecord

```typescript
interface RelatedRecord {
    id: string;                          // Notion page ID
    name: string;                        // Record title
    database: string;                    // Source database name
    relationship_type: string;           // Relation property name
    properties: Record<string, any>;     // Simplified property set (key fields only)
}
```

**Field Requirements**:
- `id`: MUST be valid Notion page ID
- `name`: MUST NOT be empty
- `database`: MUST indicate source ("Companies" or "CollabIQ")
- `relationship_type`: Name of the relation property (e.g., "Related CollabIQ")
- `properties`: SHOULD include only key fields to avoid verbosity

### FormatMetadata

```typescript
interface FormatMetadata {
    total_companies: number;             // Count of all companies
    shinsegae_affiliate_count: number;   // Count with is_shinsegae_affiliate=true
    portfolio_company_count: number;     // Count with is_portfolio_company=true
    formatted_at: string;                // ISO 8601 timestamp
    data_freshness: string;              // "cached" or "fresh"
    databases_included: string[];        // List of database names included
}
```

**Field Requirements**:
- Counts MUST be accurate (not estimates)
- `formatted_at`: ISO 8601 format (e.g., "2025-11-02T10:35:00Z")
- `data_freshness`: "cached" if any cached data used, "fresh" if all from API

---

## Example JSON Output

```json
{
    "companies": [
        {
            "id": "page_abc123",
            "name": "Company A",
            "classification": {
                "is_shinsegae_affiliate": false,
                "is_portfolio_company": true,
                "collaboration_type_hint": "PortCo"
            },
            "source_database": "Companies",
            "properties": {
                "industry": "Technology",
                "founded_year": 2020,
                "website": "https://companya.com"
            },
            "related_records": [
                {
                    "id": "page_xyz789",
                    "name": "Strategic Partnership with Company B",
                    "database": "CollabIQ",
                    "relationship_type": "Related CollabIQ",
                    "properties": {
                        "partnership_type": "Strategic Alliance",
                        "start_date": "2024-01-15"
                    }
                }
            ]
        },
        {
            "id": "page_def456",
            "name": "Shinsegae Department Store",
            "classification": {
                "is_shinsegae_affiliate": true,
                "is_portfolio_company": false,
                "collaboration_type_hint": "SSG"
            },
            "source_database": "Companies",
            "properties": {
                "industry": "Retail",
                "founded_year": 1955
            },
            "related_records": []
        },
        {
            "id": "page_ghi789",
            "name": "Company C",
            "classification": {
                "is_shinsegae_affiliate": true,
                "is_portfolio_company": true,
                "collaboration_type_hint": "Both"
            },
            "source_database": "Companies",
            "properties": {
                "industry": "E-commerce"
            },
            "related_records": []
        }
    ],
    "summary_markdown": "# Company Database\n\n## Overview\nTotal companies: 3\n- Portfolio companies: 2\n- Shinsegae affiliates: 2\n\n## Portfolio Companies (PortCo)\n- **Company A** (Technology)\n- **Company C** (E-commerce) *Also SSG affiliate*\n\n## Shinsegae Affiliates (SSG)\n- **Shinsegae Department Store** (Retail)\n- **Company C** (E-commerce) *Also Portfolio company*\n\n## Other Companies\nNone\n\n## Collaboration Types\n### Type A - PortCo × SSG Potential\n- Company A can partner with Shinsegae Department Store\n- Company A can partner with Company C\n\n### Type C - PortCo × PortCo Potential\n- Company A can partner with Company C\n",
    "metadata": {
        "total_companies": 3,
        "shinsegae_affiliate_count": 2,
        "portfolio_company_count": 2,
        "formatted_at": "2025-11-02T10:35:00Z",
        "data_freshness": "cached",
        "databases_included": ["Companies", "CollabIQ"]
    }
}
```

---

## Markdown Summary Format

### Structure

The Markdown summary MUST follow this structure:

```markdown
# Company Database

## Overview
Total companies: {count}
- Portfolio companies: {portfolio_count}
- Shinsegae affiliates: {ssg_count}

## Portfolio Companies (PortCo)
- **{Company Name}** ({Industry}) [*Additional note if also SSG*]
- ...

## Shinsegae Affiliates (SSG)
- **{Company Name}** ({Industry}) [*Additional note if also PortCo*]
- ...

## Other Companies
- **{Company Name}** ({Industry})
- ...
(Or "None" if no other companies)

## Collaboration Types
### Type A - PortCo × SSG Potential
- {PortCo} can partner with {SSG}
- ...

### Type B - Non-PortCo × SSG Potential
(Only if non-PortCo companies exist)

### Type C - PortCo × PortCo Potential
(Only if multiple PortCo companies exist)
- {PortCo1} can partner with {PortCo2}
- ...
```

### Formatting Rules

1. **Headers**: Use ATX-style headers (`#`, `##`, `###`)
2. **Lists**: Use dash (`-`) for unordered lists
3. **Emphasis**: Use `**bold**` for company names, `*italic*` for notes
4. **Sections**: Include all sections, use "None" if category is empty
5. **Industry**: Include in parentheses after company name when available
6. **Duplicates**: Companies in multiple categories get notes (e.g., "*Also SSG affiliate*")

### Collaboration Type Hints

Only include sections for types that have potential pairs:
- **Type A**: Include if any (PortCo + SSG) pairs exist
- **Type B**: Include if any (Non-PortCo + SSG) pairs exist
- **Type C**: Include if 2+ PortCo companies exist
- **Type D**: Don't explicitly list (catch-all for LLM to infer)

---

## Property Handling

### Standard Properties

Commonly expected properties in `properties` object:

```typescript
interface CommonProperties {
    industry?: string;
    founded_year?: number;
    website?: string;
    description?: string;
    location?: string;
    employee_count?: number;
    // ... other custom properties from Notion
}
```

### Property Type Mapping

Notion property types mapped to JSON:

| Notion Type | JSON Type | Example |
|-------------|-----------|---------|
| title | string | "Company A" |
| rich_text | string | "Description text" |
| number | number | 2020 |
| checkbox | boolean | true |
| select | string | "Option 1" |
| multi_select | string[] | ["Tag1", "Tag2"] |
| date | string (ISO 8601) | "2024-01-15" |
| url | string | "https://example.com" |
| email | string | "contact@example.com" |
| phone_number | string | "+1-555-0100" |

### Property Exclusions

The following properties MUST NOT appear in the `properties` object (extracted separately):
- Title property (used for `name` field)
- "Shinsegae affiliates?" checkbox (used in `classification`)
- "Is Portfolio?" checkbox (used in `classification`)

### Missing Properties

- If a property has no value: Omit from `properties` object (don't include `null`)
- If classification checkbox is missing: Default to `false`

---

## Unicode Handling

### Requirements

- ALL strings MUST be UTF-8 encoded
- Company names with Korean, Japanese, emoji MUST be preserved exactly
- Markdown summary MUST correctly render Unicode characters
- JSON MUST use proper Unicode escaping if needed

### Example

```json
{
    "name": "신세계백화점",
    "properties": {
        "description": "대한민국 최대 백화점 체인 🏬",
        "location": "서울특별시"
    }
}
```

---

## Validation Rules

### JSON Schema Validation

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["companies", "summary_markdown", "metadata"],
    "properties": {
        "companies": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "classification", "source_database", "properties", "related_records"]
            }
        },
        "summary_markdown": {
            "type": "string",
            "minLength": 1
        },
        "metadata": {
            "type": "object",
            "required": ["total_companies", "shinsegae_affiliate_count", "portfolio_company_count", "formatted_at", "data_freshness", "databases_included"]
        }
    }
}
```

### Data Consistency Rules

1. **Count Accuracy**: `metadata.total_companies` MUST equal `companies.length`
2. **Classification Counts**: Sum of classification counts MUST NOT exceed total (companies can be in multiple categories)
3. **Related Record IDs**: All `related_records[].id` MUST reference valid pages
4. **Database Names**: All `source_database` values MUST be in `metadata.databases_included`

---

## Performance Requirements

### Size Constraints

- JSON output: <5 MB for 1000 companies (average ~5 KB per company)
- Markdown summary: <50 KB (concise, scannable)
- Related records: Limit depth to prevent explosion (default: 1 level)

### Generation Time

- Format 500 companies: <2 seconds
- Generate Markdown summary: <500 ms

---

## Usage in LLM Prompts

### Recommended Prompt Structure

```
You are analyzing an email to identify companies and collaboration types.

# Company Database
{summary_markdown}

# Available Company Data
{JSON stringified companies list}

# Task
1. Identify all companies mentioned in the email
2. For each company pair, determine collaboration type:
   - Type A: PortCo × SSG
   - Type B: Non-PortCo × SSG
   - Type C: PortCo × PortCo
   - Type D: Other

# Email Content
{email text}

Respond with identified companies and their collaboration types.
```

### Why This Format Works for LLMs

1. **Markdown summary**: Provides quick context, helps LLM understand dataset
2. **Classification fields prominent**: Easy for LLM to check company type
3. **Structured JSON**: Allows programmatic lookup by name or ID
4. **Collaboration hints**: Pre-computed types speed up LLM inference
5. **Concise**: Fits within token limits for typical prompts

---

## Extensibility

### Adding New Classifications

To add a new classification field (e.g., "Is Startup?"):

1. Add to `CompanyClassification` interface
2. Update `collaboration_type_hint` logic if needed
3. Update Markdown summary sections
4. Update metadata counts

### Adding New Property Types

To support new Notion property types:

1. Add type mapping in "Property Type Mapping" table
2. Update property extraction logic
3. Update JSON schema validation

### Adding New Output Formats

To add a new format (e.g., CSV, XML):

1. Define new format contract document
2. Implement formatter method in NotionIntegrator
3. Update `format_type` parameter options
4. Maintain same semantic content (classification, relationships)

---

## Versioning

**Format Version**: 1.0.0
**Breaking Changes**: Field removal, type changes, structure changes
**Compatible Changes**: New optional fields, additional metadata
**Deprecation Policy**: Deprecated fields kept for 2 minor versions

---

## Testing

### Test Cases

1. **Empty Database**: Verify graceful handling (empty companies array)
2. **Single Company**: All 4 classification combinations (SSG only, PortCo only, Both, Neither)
3. **Multiple Companies**: Mixed types, verify counts accurate
4. **Unicode Names**: Korean, Japanese, emoji preserved
5. **Relationships**: Verify nested records included correctly
6. **Large Dataset**: 1000 companies, verify performance and size

### Validation Tools

Recommended validation approach:
```python
import jsonschema

def validate_llm_format(data: dict):
    # Load schema from above
    schema = {...}
    jsonschema.validate(data, schema)

    # Additional checks
    assert len(data["companies"]) == data["metadata"]["total_companies"]
    # ... other consistency checks
```

---

## References

- [Notion API Property Types](https://developers.notion.com/reference/property-object)
- [JSON Schema Specification](https://json-schema.org/)
- [ISO 8601 Date Format](https://www.iso.org/iso-8601-date-and-time-format.html)
- [UTF-8 Encoding Standard](https://www.unicode.org/standard/standard.html)
