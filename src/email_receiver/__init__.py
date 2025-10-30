"""
Email receiver components for ingesting emails from portfolioupdates@signite.co inbox.

This package contains the EmailReceiver abstract interface and concrete implementations
(Gmail API, IMAP, Webhook).
"""

from .base import EmailReceiver
from .gmail_receiver import EmailReceiverError, GmailReceiver
from .imap_receiver import IMAPReceiver
from .webhook_receiver import WebhookReceiver

__all__ = [
    "EmailReceiver",
    "GmailReceiver",
    "IMAPReceiver",
    "WebhookReceiver",
    "EmailReceiverError",
]
