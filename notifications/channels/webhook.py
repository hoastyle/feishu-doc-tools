"""Webhook channel for sending notifications.

This module provides a concrete implementation of BaseChannel for Feishu webhooks.
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Dict, Any, Optional

import httpx

from .base import BaseChannel
from ..config.settings import NotificationSettings

logger = logging.getLogger(__name__)


def gen_sign(timestamp: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for Feishu webhook authentication.

    Args:
        timestamp: Unix timestamp as string
        secret: Webhook secret key

    Returns:
        Base64 encoded HMAC signature

    Raises:
        ValueError: If timestamp or secret is empty

    Note:
        The signature is generated according to Feishu's webhook security
        specification: HMAC-SHA256 of "timestamp\\nsecret" encoded as base64.
    """
    if not timestamp or not secret:
        raise ValueError("Both timestamp and secret must be non-empty")

    # Concatenate timestamp and secret with newline separator
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()

    # Base64 encode the result
    sign = base64.b64encode(hmac_code).decode("utf-8")
    return sign


class WebhookChannel(BaseChannel):
    """Webhook channel for sending Feishu notifications.

    This channel sends notifications to a Feishu webhook URL with proper
    HMAC-SHA256 signature authentication.

    Example:
        >>> from ..config.settings import create_settings
        >>> settings = create_settings(
        ...     webhook_url="https://open.feishu.cn/...",
        ...     webhook_secret="your-secret"
        ... )
        >>> channel = WebhookChannel(settings)
        >>> template_data = {"schema": "2.0", "body": {...}}
        >>> success = channel.send(template_data, "document_created")
    """

    def __init__(
        self,
        settings: NotificationSettings,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ):
        """Initialize the webhook channel.

        Args:
            settings: Notification settings with webhook URL and secret
            max_retries: Override max retries (uses settings if not provided)
            timeout_seconds: Override timeout (uses settings if not provided)

        Raises:
            ValueError: If webhook URL is not configured
        """
        # Use settings values or fallback to provided overrides
        super().__init__(
            max_retries=max_retries or settings.max_retries,
            retry_delay=1.0,
            timeout_seconds=timeout_seconds or settings.timeout_seconds,
        )

        # Validate configuration
        self.webhook_url = settings.get_webhook_url()
        self.webhook_secret = settings.webhook_secret or ""

        # Initialize HTTP client
        self.client = httpx.Client(timeout=self.timeout_seconds)

        logger.info(f"WebhookChannel initialized with URL: {self.webhook_url[:50]}...")

    def _create_payload(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create the signed payload for the webhook request.

        Args:
            template_data: Template data (card content)

        Returns:
            Complete webhook payload with signature and metadata
        """
        timestamp = str(int(time.time()))
        sign = ""

        # Only generate signature if secret is configured
        if self.webhook_secret:
            sign = gen_sign(timestamp, self.webhook_secret)

        return {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "interactive",
            "card": template_data,
        }

    def send(self, template_data: Dict[str, Any], event_type: str) -> bool:
        """Send notification to webhook endpoint.

        Args:
            template_data: Template data to send (card content)
            event_type: Type of event (for logging)

        Returns:
            True if notification was sent successfully, False otherwise

        Raises:
            httpx.HTTPError: If HTTP request fails
            json.JSONDecodeError: If response is not valid JSON
        """
        if not self.is_enabled():
            logger.warning(f"WebhookChannel is disabled, skipping {event_type}")
            return False

        payload = self._create_payload(template_data)
        headers = {"Content-Type": "application/json"}

        try:
            logger.debug(f"Sending {event_type} to {self.webhook_url}")

            response = self.client.post(
                self.webhook_url,
                headers=headers,
                content=json.dumps(payload, ensure_ascii=False),
            )
            response.raise_for_status()
            resp_data = response.json()

            # Check Feishu API response code
            api_code = resp_data.get("code")
            if api_code != 0:
                error_msg = resp_data.get("msg", "Unknown error")
                logger.error(f"Feishu API error for {event_type}: code {api_code} - {error_msg}")
                return False

            logger.info(f"Successfully sent {event_type} notification")
            logger.debug(f"API response: {resp_data}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending {event_type}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response for {event_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending {event_type}: {e}")
            raise

    def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        self.client.close()
        logger.debug("HTTP client closed")

    def __enter__(self) -> "WebhookChannel":
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager and clean up resources."""
        self.close()
