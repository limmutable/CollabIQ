"""
Unit tests for group alias query construction.

Test Coverage:
- T018: deliveredto query construction

These tests validate Phase 3 (User Story 2): Handle Group Alias Email Access

To run these tests:
    pytest tests/unit/test_group_alias.py -v
"""

import pytest


def construct_deliveredto_query(email_address: str, additional_filters: str = "") -> str:
    """
    Helper function to construct Gmail API query with deliveredto filter.

    This function will be integrated into GmailReceiver in T021.

    Args:
        email_address: Email address to filter by (e.g., "collab@signite.co")
        additional_filters: Optional additional query filters (e.g., "in:inbox", "after:2025/01/01")

    Returns:
        Formatted Gmail API query string

    Examples:
        >>> construct_deliveredto_query("collab@signite.co")
        'deliveredto:"collab@signite.co"'

        >>> construct_deliveredto_query("collab@signite.co", "in:inbox")
        'deliveredto:"collab@signite.co" in:inbox'
    """
    query = f'deliveredto:"{email_address}"'
    if additional_filters:
        query += f" {additional_filters}"
    return query


# T018: Test deliveredto query construction
class TestDeliveredToQueryConstruction:
    """Tests for deliveredto query string construction."""

    def test_deliveredto_query_basic(self):
        """
        T018 [P] [US2]: Verify basic deliveredto query is constructed correctly.

        Given: Email address "collab@signite.co"
        When: construct_deliveredto_query() is called
        Then: Returns 'deliveredto:"collab@signite.co"'

        This test validates:
        - FR-011: System MUST filter emails by deliveredto header
        - research.md Decision 3: Use deliveredto: operator for group alias filtering
        """
        result = construct_deliveredto_query("collab@signite.co")
        assert result == 'deliveredto:"collab@signite.co"'

    def test_deliveredto_query_with_inbox_filter(self):
        """
        Verify deliveredto query combined with inbox filter.

        Given: Email address and "in:inbox" filter
        When: construct_deliveredto_query() is called
        Then: Returns combined query string
        """
        result = construct_deliveredto_query("collab@signite.co", "in:inbox")
        assert result == 'deliveredto:"collab@signite.co" in:inbox'

    def test_deliveredto_query_with_date_filter(self):
        """
        Verify deliveredto query combined with date filter.

        Given: Email address and date filter
        When: construct_deliveredto_query() is called
        Then: Returns combined query with after: clause
        """
        result = construct_deliveredto_query("collab@signite.co", "after:2025/11/01")
        assert result == 'deliveredto:"collab@signite.co" after:2025/11/01'

    def test_deliveredto_query_with_multiple_filters(self):
        """
        Verify deliveredto query combined with multiple filters.

        Given: Email address and multiple filters
        When: construct_deliveredto_query() is called
        Then: Returns combined query string
        """
        result = construct_deliveredto_query(
            "collab@signite.co",
            "in:inbox after:2025/11/01"
        )
        assert result == 'deliveredto:"collab@signite.co" in:inbox after:2025/11/01'

    def test_deliveredto_query_escapes_quotes(self):
        """
        Verify email address is properly quoted in query.

        Given: Email address without quotes
        When: construct_deliveredto_query() is called
        Then: Returns query with email address in quotes
        """
        result = construct_deliveredto_query("test@example.com")
        assert '"test@example.com"' in result
        assert result.startswith('deliveredto:')

    def test_deliveredto_query_different_email(self):
        """
        Verify query construction works with different email addresses.

        Given: Different email address (portfolioupdates@signite.co)
        When: construct_deliveredto_query() is called
        Then: Returns correctly formatted query
        """
        result = construct_deliveredto_query("portfolioupdates@signite.co")
        assert result == 'deliveredto:"portfolioupdates@signite.co"'
