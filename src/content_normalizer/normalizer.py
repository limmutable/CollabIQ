"""
Content normalizer for email text cleaning.

This module defines the ContentNormalizer class that removes signatures,
quoted threads, and disclaimers from email body text.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

try:
    from ..models.cleaned_email import CleanedEmail, CleaningStatus, RemovedContent
    from ..models.raw_email import RawEmail
    from . import patterns
except ImportError:
    from models.cleaned_email import CleanedEmail, CleaningStatus, RemovedContent
    from models.raw_email import RawEmail
    from content_normalizer import patterns

# Configure logging (FR-009)
logger = logging.getLogger(__name__)


class CleaningResult:
    """
    Result object containing cleaned body text and removal metadata.

    Attributes:
        cleaned_body: Email body with signatures, quotes, and disclaimers removed
        removed_content: Summary of what was removed (pattern names, character counts)
    """

    def __init__(self, cleaned_body: str, removed_content: RemovedContent):
        self.cleaned_body = cleaned_body
        self.removed_content = removed_content


class ContentNormalizer:
    """
    Email text cleaning component that removes signatures, quoted threads, and disclaimers.

    Uses pattern-based detection with Korean and English regex patterns.

    Requirements Coverage:
    - FR-004: Detect and remove email signatures (Korean: "감사합니다", "드립니다"; English: "Best regards")
    - FR-005: Detect and remove quoted thread content ("> " prefix, "On [date]" headers)
    - FR-006: Detect and remove legal disclaimers and confidentiality notices
    - FR-007: Preserve original collaboration content while removing noise
    - FR-008: Output cleaned email text to file storage
    - FR-012: Handle empty emails gracefully (flag for review)
    - SC-002: Remove signatures from 95%+ of test emails
    - SC-003: Remove quoted threads from 95%+ of test emails
    """

    def clean(
        self,
        body: str,
        remove_signatures: bool = True,
        remove_quotes: bool = True,
        remove_disclaimers: bool = True,
    ) -> CleaningResult:
        """
        Remove signatures, quoted threads, and disclaimers from email body text.

        This is the primary cleaning method implementing three-stage pipeline:
        Stage 1: Remove disclaimers
        Stage 2: Remove quoted threads
        Stage 3: Remove signatures

        Args:
            body: Raw email body text containing collaboration content mixed with
                  signatures, quoted threads, and disclaimers.
            remove_signatures: Enable signature removal (FR-004)
            remove_quotes: Enable quoted thread removal (FR-005)
            remove_disclaimers: Enable disclaimer removal (FR-006)

        Returns:
            CleaningResult object containing cleaned body text and removal metadata.
            cleaned_body may be empty if entire email was noise (FR-012).

        Implementation:
            - T087: Three-stage cleaning pipeline (disclaimers → quotes → signatures)
            - T089: Empty content handling per FR-012
        """
        if not body or not body.strip():
            logger.debug("Empty body provided to clean()")
            return CleaningResult(
                cleaned_body="",
                removed_content=RemovedContent(
                    original_length=len(body),
                    cleaned_length=0,
                    signature_removed=False,
                    quoted_thread_removed=False,
                    disclaimer_removed=False,
                ),
            )

        original_length = len(body)
        cleaned = body

        # Track what was removed
        signature_removed = False
        quoted_thread_removed = False
        disclaimer_removed = False

        # Stage 1: Remove disclaimers (FR-006)
        if remove_disclaimers:
            disclaimer_result = self.remove_disclaimer(cleaned)
            if len(disclaimer_result) < len(cleaned):
                disclaimer_removed = True
                cleaned = disclaimer_result

        # Stage 2: Remove quoted threads (FR-005)
        if remove_quotes:
            quote_result = self.remove_quoted_thread(cleaned)
            if len(quote_result) < len(cleaned):
                quoted_thread_removed = True
                cleaned = quote_result

        # Stage 3: Remove signatures (FR-004)
        if remove_signatures:
            signature_result = self.remove_signature(cleaned)
            if len(signature_result) < len(cleaned):
                signature_removed = True
                cleaned = signature_result

        cleaned = cleaned.strip()
        cleaned_length = len(cleaned)

        # Log final result
        logger.info(
            f"Email cleaned: {original_length} → {cleaned_length} chars "
            f"(signature={signature_removed}, quotes={quoted_thread_removed}, "
            f"disclaimer={disclaimer_removed})"
        )

        return CleaningResult(
            cleaned_body=cleaned,
            removed_content=RemovedContent(
                original_length=original_length,
                cleaned_length=cleaned_length,
                signature_removed=signature_removed,
                quoted_thread_removed=quoted_thread_removed,
                disclaimer_removed=disclaimer_removed,
            ),
        )

    def detect_signature(self, body: str) -> Optional[int]:
        """
        Detect signature location in email body text.

        Args:
            body: Email body text

        Returns:
            Starting position of signature, or None if no signature detected
        """
        result = patterns.detect_signature(body)
        if result is None:
            return None
        return result[0]  # Return only position

    def remove_signature(self, body: str) -> str:
        """
        Remove email signature from body text using Korean and English patterns.

        Uses multi-stage detection: exact patterns → heuristics → fallback.

        Args:
            body: Email body text

        Returns:
            Text with signature removed (or original if no signature detected)

        Implementation:
        - T056: detect_signature() method
        - T057: remove_signature() method
        - T059: Logging per FR-009
        """
        if not body or not body.strip():
            logger.debug("Empty body provided to remove_signature")
            return body

        result = patterns.detect_signature(body)
        if result is None:
            logger.debug("No signature detected in email body")
            return body

        signature_start, pattern_name = result
        cleaned_body = body[:signature_start].rstrip()

        # Log signature removal (FR-009)
        removed_chars = len(body) - len(cleaned_body)
        logger.info(
            f"Signature removed using pattern '{pattern_name}': "
            f"{removed_chars} characters removed"
        )

        return cleaned_body

    def detect_quoted_thread(self, body: str) -> Optional[int]:
        """
        Detect quoted thread location in email body text.

        Args:
            body: Email body text

        Returns:
            Starting position of quoted thread, or None if no quotes detected
        """
        result = patterns.detect_quoted_thread(body)
        if result is None:
            return None
        return result[0]  # Return only position

    def remove_quoted_thread(self, body: str) -> str:
        """
        Remove quoted email thread content (reply chains).

        Detects patterns like:
        - Lines starting with "> "
        - "On [date], [person] wrote:" headers
        - Nested quoted content (multiple levels)

        Args:
            body: Email body text

        Returns:
            Text with quoted content removed (or original if no quotes detected)

        Implementation:
        - T070: detect_quoted_thread() method
        - T071: remove_quoted_thread() method
        - T073: Logging per FR-009
        """
        if not body or not body.strip():
            logger.debug("Empty body provided to remove_quoted_thread")
            return body

        result = patterns.detect_quoted_thread(body)
        if result is None:
            logger.debug("No quoted thread detected in email body")
            return body

        quote_start, pattern_name = result
        cleaned_body = body[:quote_start].rstrip()

        # Log quoted thread removal (FR-009)
        removed_chars = len(body) - len(cleaned_body)
        logger.info(
            f"Quoted thread removed using pattern '{pattern_name}': "
            f"{removed_chars} characters removed"
        )

        return cleaned_body

    def detect_disclaimer(self, body: str) -> Optional[int]:
        """
        Detect disclaimer location in email body text.

        Args:
            body: Email body text

        Returns:
            Starting position of disclaimer, or None if no disclaimer detected
        """
        result = patterns.detect_disclaimer(body)
        if result is None:
            return None
        return result[0]  # Return only position

    def remove_disclaimer(self, body: str) -> str:
        """
        Remove legal disclaimers and confidentiality notices.

        Detects patterns like:
        - "This email is confidential..."
        - "This message is intended only for..."
        - Corporate disclaimer boilerplate

        Args:
            body: Email body text

        Returns:
            Text with disclaimer removed (or original if no disclaimer detected)

        Implementation:
        - T083: detect_disclaimer() method
        - T084: remove_disclaimer() method
        - T086: Logging per FR-009
        """
        if not body or not body.strip():
            logger.debug("Empty body provided to remove_disclaimer")
            return body

        result = patterns.detect_disclaimer(body)
        if result is None:
            logger.debug("No disclaimer detected in email body")
            return body

        disclaimer_start, pattern_name = result
        cleaned_body = body[:disclaimer_start].rstrip()

        # Log disclaimer removal (FR-009)
        removed_chars = len(body) - len(cleaned_body)
        logger.info(
            f"Disclaimer removed using pattern '{pattern_name}': "
            f"{removed_chars} characters removed"
        )

        return cleaned_body

    def process_raw_email(self, raw_email: RawEmail) -> CleanedEmail:
        """
        Process a RawEmail and produce a CleanedEmail.

        High-level method that combines cleaning with metadata generation.

        Args:
            raw_email: The RawEmail object to process

        Returns:
            CleanedEmail object with cleaned body and processing metadata

        Implementation:
            - T088: Main method orchestrating all cleaning stages
            - T090: CleanedEmail model creation with RemovedContent summary
            - T089: Empty content handling per FR-012
        """
        # Clean the email body
        cleaning_result = self.clean(raw_email.body)

        # Determine cleaning status and is_empty flag
        is_empty = (
            not cleaning_result.cleaned_body or not cleaning_result.cleaned_body.strip()
        )

        if is_empty:
            # Email is entirely noise (FR-012)
            status = CleaningStatus.EMPTY
            logger.warning(
                f"Email {raw_email.metadata.message_id} resulted in empty content after cleaning"
            )
        else:
            status = CleaningStatus.SUCCESS

        # Create CleanedEmail model
        cleaned_email = CleanedEmail(
            original_message_id=raw_email.metadata.message_id,
            cleaned_body=cleaning_result.cleaned_body,
            removed_content=cleaning_result.removed_content,
            processed_at=datetime.now(UTC),
            status=status,
            is_empty=is_empty,
        )

        logger.info(
            f"Processed email {raw_email.metadata.message_id}: "
            f"status={status}, length={len(cleaning_result.cleaned_body)}"
        )

        return cleaned_email

    def save_cleaned_email(
        self, cleaned_email: CleanedEmail, base_dir: Path = Path("data/cleaned")
    ) -> Path:
        """
        Save cleaned email to file storage with monthly directory structure.

        Args:
            cleaned_email: The CleanedEmail object to save
            base_dir: Base directory for cleaned emails (default: data/cleaned)

        Returns:
            Path to the saved file

        Implementation:
            - T091: Save to data/cleaned/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json per FR-008
        """
        # Create monthly directory structure: data/cleaned/YYYY/MM/
        processed_date = cleaned_email.processed_at
        monthly_dir = (
            base_dir / str(processed_date.year) / f"{processed_date.month:02d}"
        )
        monthly_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: YYYYMMDD_HHMMSS_{message_id}.json
        timestamp = processed_date.strftime("%Y%m%d_%H%M%S")
        # Clean message_id for filename (remove < > and @ symbols)
        clean_id = (
            cleaned_email.original_message_id.strip("<>")
            .replace("@", "_at_")
            .replace("/", "_")
        )
        filename = f"{timestamp}_{clean_id}.json"
        file_path = monthly_dir / filename

        # Serialize CleanedEmail to JSON
        cleaned_dict = cleaned_email.model_dump(mode="json")
        file_path.write_text(json.dumps(cleaned_dict, indent=2, ensure_ascii=False))

        logger.info(f"Saved cleaned email to {file_path}")

        return file_path
