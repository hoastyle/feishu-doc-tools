"""Notification channels module.

This module provides different channel implementations for sending notifications.
"""

from .base import BaseChannel
from .webhook import WebhookChannel

__all__ = ["BaseChannel", "WebhookChannel"]
