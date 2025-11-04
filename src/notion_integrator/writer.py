"""NotionWriter - Handles writing extracted email data to Notion databases.

This module provides functionality to create entries in the CollabIQ Notion database
with all extracted and classified data fields.
"""

import logging
from typing import Optional, Dict, Any

from notion_client.errors import APIResponseError
from llm_provider.types import ExtractedEntitiesWithClassification, WriteResult
from .field_mapper import FieldMapper


logger = logging.getLogger(__name__)


class NotionWriter:
    """Handles writing extracted email data to Notion databases."""

    def __init__(
        self,
        notion_integrator,
        collabiq_db_id: str,
        duplicate_behavior: str = "skip",
        dlq_manager=None,
    ):
        """Initialize NotionWriter with Notion integrator and database ID.

        Args:
            notion_integrator: NotionIntegrator instance for API access
            collabiq_db_id: CollabIQ database ID
            duplicate_behavior: Behavior for duplicates - "skip" or "update" (default: "skip")
            dlq_manager: Optional DLQManager for failed write handling
        """
        self.notion_integrator = notion_integrator
        self.collabiq_db_id = collabiq_db_id
        self.duplicate_behavior = duplicate_behavior
        self.dlq_manager = dlq_manager
        self.field_mapper: Optional[FieldMapper] = None

    async def check_duplicate(self, email_id: str) -> Optional[str]:
        """Check if an entry with the given email_id already exists.

        Args:
            email_id: Email identifier to check for duplicates

        Returns:
            Existing page_id if duplicate found, None otherwise
        """
        try:
            # Query Notion database for entries with matching email_id
            query_response = await self.notion_integrator.notion_client.databases.query(
                database_id=self.collabiq_db_id,
                filter={"property": "email_id", "rich_text": {"equals": email_id}},
            )

            # Return page_id of first matching result
            results = query_response.get("results", [])
            if results:
                return results[0]["id"]

            return None

        except Exception as e:
            logger.warning(f"Error checking for duplicate email_id={email_id}: {e}")
            return None  # On error, assume no duplicate and allow write attempt

    async def create_collabiq_entry(
        self, extracted_data: ExtractedEntitiesWithClassification
    ) -> WriteResult:
        """Create a new entry in the CollabIQ Notion database.

        Args:
            extracted_data: Extracted and classified email data

        Returns:
            WriteResult with success status, page_id, or error details
        """
        try:
            # Initialize FieldMapper with schema discovery (lazy load)
            if self.field_mapper is None:
                schema = await self.notion_integrator.discover_database_schema(
                    self.collabiq_db_id
                )
                self.field_mapper = FieldMapper(schema)

            # Check for duplicate entry
            existing_page_id = await self.check_duplicate(extracted_data.email_id)

            if existing_page_id:
                # Duplicate detected
                if self.duplicate_behavior == "skip":
                    logger.info(
                        f"Duplicate detected for email_id={extracted_data.email_id}, "
                        f"existing_page_id={existing_page_id}. Skipping write (duplicate_behavior=skip)."
                    )
                    return WriteResult(
                        success=True,
                        page_id=None,
                        email_id=extracted_data.email_id,
                        retry_count=0,
                        is_duplicate=True,
                        existing_page_id=existing_page_id,
                    )
                elif self.duplicate_behavior == "update":
                    logger.info(
                        f"Duplicate detected for email_id={extracted_data.email_id}, "
                        f"existing_page_id={existing_page_id}. Updating entry (duplicate_behavior=update)."
                    )
                    # Map extracted data to Notion properties format
                    properties = self.field_mapper.map_to_notion_properties(
                        extracted_data
                    )

                    # Update existing page
                    await self.notion_integrator.notion_client.pages.update(
                        page_id=existing_page_id, properties=properties
                    )

                    return WriteResult(
                        success=True,
                        page_id=existing_page_id,
                        email_id=extracted_data.email_id,
                        retry_count=0,
                        is_duplicate=True,
                        existing_page_id=existing_page_id,
                    )

            # No duplicate - proceed with creation
            # Map extracted data to Notion properties format
            properties = self.field_mapper.map_to_notion_properties(extracted_data)

            # Create page with retry logic
            page_response = await self._create_page_with_retry(properties)

            # Return success result
            return WriteResult(
                success=True,
                page_id=page_response["id"],
                email_id=extracted_data.email_id,
                retry_count=0,
                is_duplicate=False,
            )

        except Exception as e:
            logger.error(
                f"Failed to create Notion entry for email_id={extracted_data.email_id}: {e}",
                exc_info=True,
            )

            # Extract error details
            error_type = type(e).__name__
            error_message = str(e)
            status_code = None

            if isinstance(e, APIResponseError):
                # Safely extract status code
                if hasattr(e, "response") and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code
                # Format error message
                if hasattr(e, "message") and hasattr(e, "code"):
                    error_message = f"{e.message} (code: {e.code})"

            # Save to DLQ if manager is available
            if self.dlq_manager:
                error_details = {
                    "error_type": error_type,
                    "error_message": error_message,
                    "status_code": status_code,
                    "retry_count": 3,  # Assume max retries attempted
                }
                try:
                    dlq_file = self.dlq_manager.save_failed_write(
                        extracted_data=extracted_data, error_details=error_details
                    )
                    logger.info(f"Failed write saved to DLQ: {dlq_file}")
                except Exception as dlq_error:
                    logger.error(f"Failed to save to DLQ: {dlq_error}", exc_info=True)

            # Return error result
            return WriteResult(
                success=False,
                page_id=None,
                email_id=extracted_data.email_id,
                error_type=error_type,
                error_message=error_message,
                status_code=status_code,
                retry_count=3,  # Assume max retries attempted
                is_duplicate=False,
            )

    async def _create_page_with_retry(
        self, properties: Dict[str, Any], max_retries: int = 3
    ) -> Dict[str, Any]:
        """Create Notion page with immediate retry for transient errors.

        Args:
            properties: Notion properties dict
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Notion API response dict

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                # Call Notion API to create page
                response = await self.notion_integrator.notion_client.pages.create(
                    parent={"database_id": self.collabiq_db_id},
                    properties=properties,
                )
                return response

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Notion write attempt {attempt + 1}/{max_retries} failed: {e}"
                )

                # Don't retry on validation errors (400)
                if isinstance(e, APIResponseError):
                    if hasattr(e, "response") and hasattr(e.response, "status_code"):
                        if e.response.status_code == 400:
                            logger.error(f"Validation error, will not retry: {e}")
                            raise e

                # Continue to next retry for transient errors
                if attempt < max_retries - 1:
                    logger.info(
                        f"Retrying immediately (attempt {attempt + 2}/{max_retries})"
                    )

        # All retries exhausted
        logger.error(f"All {max_retries} retry attempts failed")
        raise last_exception
