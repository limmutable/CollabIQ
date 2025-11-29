"""
Email Sender Module for CollabIQ.

Provides email sending capabilities using the Gmail API, reusing OAuth credentials
from the existing GmailReceiver component.

Features:
- Send multipart emails (HTML + plain text)
- Retry with exponential backoff on failure
- Reuses existing Gmail OAuth token
"""

__version__ = "0.1.0"
