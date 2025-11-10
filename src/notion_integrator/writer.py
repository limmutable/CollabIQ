"""NotionWriter - Handles writing extracted email data to Notion databases.

This module provides functionality to create entries in the CollabIQ Notion database
with all extracted and classified data fields.
"""

import logging
from typing import Optional, Dict, Any

from notion_client.errors import APIResponseError
from llm_provider.types import ExtractedEntitiesWithClassification, WriteResult
from .field_mapper import FieldMapper

try:
    from ..error_handling import retry_with_backoff, NOTION_RETRY_CONFIG
except ImportError:
    from error_handling import retry_with_backoff, NOTION_RETRY_CONFIG


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
        self._retry_count = 0  # Track retry attempts for current operation

    async def check_duplicate(self, email_id: str) -> Optional[str]:
        """Check if an entry with the given email_id already exists.

        Args:
            email_id: Email identifier to check for duplicates

        Returns:
            Existing page_id if duplicate found, None otherwise
        """
        try:
            # Query for existing entry with this email_id (Notion API 2025-09-03)
            # Uses data_sources.query() via NotionClient.query_database()
            filter_conditions = {
                "property": "Email ID",
                "rich_text": {"equals": email_id},
            }

            response = await self.notion_integrator.client.query_database(
                database_id=self.collabiq_db_id,
                filter_conditions=filter_conditions,
                page_size=1,  # Only need to check if at least one exists
            )

            results = response.get("results", [])
            if results:
                page_id = results[0]["id"]
                logger.info(
                    f"Duplicate found for email_id={email_id}, page_id={page_id}"
                )
                return page_id

            logger.debug(f"No duplicate found for email_id={email_id}")
            return None

        except Exception as e:
            logger.warning(f"Error checking for duplicate email_id={email_id}: {e}")
            return None  # On error, assume no duplicate and allow write attempt

    async def create_company(
        self, company_name: str, companies_db_id: str
    ) -> Optional[str]:
        """Create a new company entry in the Companies database.

        This method is called by the fuzzy matcher when no match is found
        (similarity < threshold) and auto_create=True. It creates a new
        Companies database entry with the extracted company name.

        Args:
            company_name: Company name to create (already normalized)
            companies_db_id: Companies database ID

        Returns:
            page_id of the newly created company entry (32-character UUID)
            Returns None if creation fails

        Raises:
            APIResponseError: If Notion API call fails after retries
        """
        try:
            logger.info(f"Creating new company: {company_name}")

            # Build properties for Companies database
            # Companies database typically has a "Name" title property
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": company_name
                            }
                        }
                    ]
                }
            }

            # Create page in Companies database (with retry logic)
            response = await self._create_company_page(companies_db_id, properties)

            page_id = response["id"]
            logger.info(
                f"Successfully created company: {company_name}, page_id={page_id}"
            )

            return page_id

        except Exception as e:
            logger.error(
                f"Failed to create company: {company_name}: {e}",
                exc_info=True,
            )
            return None

    @retry_with_backoff(NOTION_RETRY_CONFIG)
    async def _create_company_page(
        self, companies_db_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create company page with retry logic handled by decorator.

        Args:
            companies_db_id: Companies database ID
            properties: Notion properties dict for company

        Returns:
            Notion API response dict

        Raises:
            APIResponseError: If page creation fails after retries
        """
        response = await self.notion_integrator.client.client.pages.create(
            parent={"database_id": companies_db_id},
            properties=properties,
        )
        return response

    async def create_collabiq_entry(
        self, extracted_data: ExtractedEntitiesWithClassification
    ) -> WriteResult:
        """Create a new entry in the CollabIQ Notion database.

        Args:
            extracted_data: Extracted and classified email data

        Returns:
            WriteResult with success status, page_id, or error details
        """
        # Reset retry counter for this operation
        self._retry_count = 0

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
                    # Use async version if available, otherwise fall back to sync
                    if hasattr(self.field_mapper, "map_to_notion_properties_async"):
                        properties = await self.field_mapper.map_to_notion_properties_async(
                            extracted_data
                        )
                    else:
                        properties = self.field_mapper.map_to_notion_properties(
                            extracted_data
                        )

                    # Update existing page
                    await self.notion_integrator.client.client.pages.update(
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
            # Use async version if available, otherwise fall back to sync
            if hasattr(self.field_mapper, "map_to_notion_properties_async"):
                properties = await self.field_mapper.map_to_notion_properties_async(
                    extracted_data
                )
            else:
                properties = self.field_mapper.map_to_notion_properties(extracted_data)

            # Create page (retry logic handled by decorator)
            page_response = await self._create_page(properties)

            # Return success result
            # retry_count: subtract 1 because first attempt is not a retry
            actual_retries = max(0, self._retry_count - 1)
            return WriteResult(
                success=True,
                page_id=page_response["id"],
                email_id=extracted_data.email_id,
                retry_count=actual_retries,
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

    @retry_with_backoff(NOTION_RETRY_CONFIG)
    async def _create_page(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create Notion page with retry logic handled by decorator.

        The @retry_with_backoff decorator handles:
        - Exponential backoff with jitter
        - Circuit breaker integration
        - Structured error logging
        - Automatic classification of transient vs permanent errors

        Args:
            properties: Notion properties dict

        Returns:
            Notion API response dict

        Raises:
            APIResponseError: If page creation fails after retries
        """
        # Track retry attempts (incremented on each call by decorator)
        if self._retry_count > 0:
            logger.debug(f"Retry attempt {self._retry_count} for page creation")
        self._retry_count += 1

        # Call Notion API to create page
        # Retry logic is handled by the decorator
        response = await self.notion_integrator.client.client.pages.create(
            parent={"database_id": self.collabiq_db_id},
            properties=properties,
        )
        return response
