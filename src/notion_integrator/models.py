"""
Pydantic Data Models for Notion Integration

Defines all data structures used in the Notion integration system, including:
- Core Notion entities (Database, Property, Record)
- Schema and cache structures
- LLM output format
- Relationship tracking

All models use Pydantic for validation, serialization, and type safety.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, computed_field


# ==============================================================================
# Core Notion Entities
# ==============================================================================


class NotionProperty(BaseModel):
    """
    Represents a field/property in a Notion database.

    Attributes:
        id: Notion property ID
        name: Property name (e.g., "Name", "Shinsegae affiliates?")
        type: Property type (title, rich_text, checkbox, relation, etc.)
        config: Type-specific configuration (relation targets, select options, etc.)
    """

    id: str
    name: str
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Validate that property name is not empty."""
        if not v or not v.strip():
            raise ValueError("Property name must not be empty")
        return v


class NotionDatabase(BaseModel):
    """
    Represents a Notion database with metadata and schema.

    Attributes:
        id: Notion database ID (UUID format)
        title: Human-readable database name
        url: Notion URL to the database
        created_time: When database was created
        last_edited_time: When database was last modified
        properties: All properties/fields in the database
    """

    id: str
    title: str
    url: str
    created_time: datetime
    last_edited_time: datetime
    properties: Dict[str, NotionProperty]

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        """Validate that database title is not empty."""
        if not v or not v.strip():
            raise ValueError("Database title must not be empty")
        return v

    @field_validator("properties")
    @classmethod
    def properties_must_not_be_empty(cls, v: Dict[str, NotionProperty]) -> Dict[str, NotionProperty]:
        """Validate that database has at least one property."""
        if not v:
            raise ValueError("Database must have at least one property")
        return v


class NotionRecord(BaseModel):
    """
    Represents a single page/record from a Notion database.

    Attributes:
        id: Page ID (UUID format)
        database_id: Parent database ID
        created_time: When record was created
        last_edited_time: When record was last modified
        archived: Whether record is archived
        properties: Property values (structure depends on property type)
    """

    id: str
    database_id: str
    created_time: datetime
    last_edited_time: datetime
    archived: bool = False
    properties: Dict[str, Any]


# ==============================================================================
# Schema and Relationship Structures
# ==============================================================================


class DatabaseSchema(BaseModel):
    """
    Complete structure definition for a database.

    Attributes:
        database: Database metadata
        properties_by_type: Properties grouped by type
        relation_properties: Subset of properties that are relations
        classification_fields: Maps classification field names to property IDs
    """

    database: NotionDatabase
    properties_by_type: Dict[str, List[NotionProperty]]
    relation_properties: List[NotionProperty]
    classification_fields: Dict[str, str] = Field(default_factory=dict)

    @computed_field
    @property
    def has_relations(self) -> bool:
        """Check if database has any relation properties."""
        return len(self.relation_properties) > 0

    @computed_field
    @property
    def property_count(self) -> int:
        """Get total number of properties in database."""
        return len(self.database.properties)


class Relationship(BaseModel):
    """
    Represents a relationship between databases via a relation property.

    Attributes:
        source_db_id: Source database ID
        source_property: The relation property
        target_db_id: Target database ID
        is_bidirectional: Whether relationship is bidirectional
    """

    source_db_id: str
    source_property: NotionProperty
    target_db_id: str
    is_bidirectional: bool


class RelationshipGraph(BaseModel):
    """
    Tracks relationships between databases.

    Attributes:
        databases: All known databases by ID
        relationships: All relation properties across databases
        adjacency_list: Database ID → List of related database IDs
    """

    databases: Dict[str, NotionDatabase]
    relationships: List[Relationship]
    adjacency_list: Dict[str, List[str]]

    @computed_field
    @property
    def has_circular_refs(self) -> bool:
        """
        Detect if any circular relationships exist.

        Uses DFS to detect cycles in the relationship graph.
        """
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.adjacency_list.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for db_id in self.databases:
            if db_id not in visited:
                if has_cycle(db_id):
                    return True

        return False

    @computed_field
    @property
    def max_depth(self) -> int:
        """
        Calculate maximum relationship depth in graph.

        Returns the longest path length in the relationship graph.
        """
        if not self.relationships:
            return 0

        def dfs_depth(node: str, visited: set) -> int:
            if node in visited:
                return 0
            visited.add(node)
            max_child_depth = 0
            for neighbor in self.adjacency_list.get(node, []):
                max_child_depth = max(max_child_depth, dfs_depth(neighbor, visited.copy()))
            return 1 + max_child_depth

        depths = []
        for db_id in self.databases:
            depths.append(dfs_depth(db_id, set()))

        return max(depths) if depths else 0


# ==============================================================================
# Cache Structures
# ==============================================================================


class DataCache(BaseModel):
    """
    Cached data with metadata for TTL validation.

    Attributes:
        cache_type: "schema" or "data"
        database_id: Which database this cache belongs to
        database_name: Human-readable name
        cached_at: When cache was created
        ttl_hours: Time-to-live in hours
        expires_at: Computed expiration time
        content: Cached data (schema dict or records list)
        metadata: Additional metadata (record count, version, etc.)
    """

    cache_type: str
    database_id: str
    database_name: str
    cached_at: datetime
    ttl_hours: int
    expires_at: datetime
    content: Dict[str, Any] | List[Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("cache_type")
    @classmethod
    def cache_type_must_be_valid(cls, v: str) -> str:
        """Validate cache type is schema or data."""
        if v not in ("schema", "data"):
            raise ValueError("cache_type must be 'schema' or 'data'")
        return v

    @field_validator("ttl_hours")
    @classmethod
    def ttl_must_be_positive(cls, v: int) -> int:
        """Validate TTL is positive."""
        if v <= 0:
            raise ValueError("ttl_hours must be positive")
        return v

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v: Dict[str, Any] | List[Any]) -> Dict[str, Any] | List[Any]:
        """Validate content is not empty."""
        if not v:
            raise ValueError("Cache content must not be empty")
        return v

    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if cache has expired."""
        return datetime.now() > self.expires_at

    @computed_field
    @property
    def age_hours(self) -> float:
        """Calculate cache age in hours."""
        age = datetime.now() - self.cached_at
        return age.total_seconds() / 3600

    @classmethod
    def create(
        cls,
        cache_type: str,
        database_id: str,
        database_name: str,
        ttl_hours: int,
        content: Dict[str, Any] | List[Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DataCache":
        """
        Factory method to create a new cache entry.

        Automatically sets cached_at to now and computes expires_at.
        """
        now = datetime.now()
        return cls(
            cache_type=cache_type,
            database_id=database_id,
            database_name=database_name,
            cached_at=now,
            ttl_hours=ttl_hours,
            expires_at=now + timedelta(hours=ttl_hours),
            content=content,
            metadata=metadata or {},
        )


# ==============================================================================
# LLM Output Format
# ==============================================================================


class CompanyClassification(BaseModel):
    """
    Company classification flags for collaboration type determination.

    Attributes:
        is_shinsegae_affiliate: "Shinsegae affiliates?" checkbox value
        is_portfolio_company: "Is Portfolio?" checkbox value
        collaboration_type_hint: Computed type hint
    """

    is_shinsegae_affiliate: bool
    is_portfolio_company: bool
    collaboration_type_hint: str

    @field_validator("collaboration_type_hint")
    @classmethod
    def validate_type_hint(cls, v: str) -> str:
        """Validate collaboration type hint."""
        valid_hints = ("SSG", "PortCo", "Both", "Neither")
        if v not in valid_hints:
            raise ValueError(f"collaboration_type_hint must be one of {valid_hints}")
        return v

    @classmethod
    def from_checkboxes(cls, is_ssg: bool, is_portfolio: bool) -> "CompanyClassification":
        """
        Factory method to create classification from checkbox values.

        Automatically computes the collaboration_type_hint based on flags.
        """
        if is_ssg and is_portfolio:
            hint = "Both"
        elif is_ssg:
            hint = "SSG"
        elif is_portfolio:
            hint = "PortCo"
        else:
            hint = "Neither"

        return cls(
            is_shinsegae_affiliate=is_ssg,
            is_portfolio_company=is_portfolio,
            collaboration_type_hint=hint,
        )


class RelatedRecord(BaseModel):
    """
    Simplified view of a related record.

    Attributes:
        id: Notion page ID
        name: Record title
        database: Source database name
        relationship_type: Relation property name
        properties: Simplified property set (key fields only)
    """

    id: str
    name: str
    database: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class CompanyRecord(BaseModel):
    """
    Complete company record for LLM consumption.

    Attributes:
        id: Notion page ID
        name: Company name
        classification: Classification flags
        source_database: "Companies" or "CollabIQ"
        properties: All other properties (excluding name and classification)
        related_records: Resolved relationships
    """

    id: str
    name: str
    classification: CompanyClassification
    source_database: str
    properties: Dict[str, Any]
    related_records: List[RelatedRecord] = Field(default_factory=list)


class FormatMetadata(BaseModel):
    """
    Metadata about the formatted dataset.

    Attributes:
        total_companies: Count of all companies
        shinsegae_affiliate_count: Count with is_shinsegae_affiliate=True
        portfolio_company_count: Count with is_portfolio_company=True
        formatted_at: ISO 8601 timestamp
        data_freshness: "cached" or "fresh"
        databases_included: List of database names included
    """

    total_companies: int
    shinsegae_affiliate_count: int
    portfolio_company_count: int
    formatted_at: datetime
    data_freshness: str
    databases_included: List[str]

    @field_validator("data_freshness")
    @classmethod
    def validate_freshness(cls, v: str) -> str:
        """Validate data freshness value."""
        if v not in ("cached", "fresh"):
            raise ValueError("data_freshness must be 'cached' or 'fresh'")
        return v


class LLMFormattedData(BaseModel):
    """
    Complete formatted dataset for LLM consumption.

    Combines structured JSON data with human-readable Markdown summary.

    Attributes:
        companies: All company records
        summary_markdown: Human-readable summary
        metadata: Dataset metadata
    """

    companies: List[CompanyRecord]
    summary_markdown: str
    metadata: FormatMetadata

    @field_validator("summary_markdown")
    @classmethod
    def summary_must_not_be_empty(cls, v: str) -> str:
        """Validate summary is not empty."""
        if not v or not v.strip():
            raise ValueError("summary_markdown must not be empty")
        return v
