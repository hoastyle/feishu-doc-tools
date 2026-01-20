"""Base channel for sending notifications.

This module provides the abstract base class for notification channels.
All concrete channel implementations should inherit from BaseChannel.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
import time

logger = logging.getLogger(__name__)


class BaseChannel(ABC):
    """Abstract base class for notification channels.

    All notification channels must implement the send() method.
    This class provides common functionality like retry logic and error handling.

    Example:
        >>> class MyChannel(BaseChannel):
        ...     def send(self, template_data: Dict[str, Any], event_type: str) -> bool:
        ...         # Implementation
        ...         pass
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout_seconds: int = 10,
    ):
        """Initialize the channel.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
            timeout_seconds: Request timeout in seconds (default: 10)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout_seconds = timeout_seconds
        self._enabled = True

    @abstractmethod
    def send(self, template_data: Dict[str, Any], event_type: str) -> bool:
        """Send a notification through this channel.

        Args:
            template_data: Template data to send (card content)
            event_type: Type of event (e.g., "document_created")

        Returns:
            True if notification was sent successfully, False otherwise

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement send()")

    def send_with_retry(
        self,
        template_data: Dict[str, Any],
        event_type: str
    ) -> bool:
        """Send notification with automatic retry on failure.

        Args:
            template_data: Template data to send
            event_type: Type of event

        Returns:
            True if sent successfully (after retries if needed), False otherwise
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(
                        f"Retry attempt {attempt}/{self.max_retries} for {event_type}"
                    )
                    time.sleep(self.retry_delay * attempt)  # Exponential backoff

                return self.send(template_data, event_type)

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Send attempt {attempt + 1} failed for {event_type}: {e}"
                )

        logger.error(
            f"Failed to send {event_type} after {self.max_retries + 1} attempts: "
            f"{last_exception}"
        )
        return False

    def is_enabled(self) -> bool:
        """Check if this channel is enabled.

        Returns:
            True if channel is enabled, False otherwise
        """
        return self._enabled

    def enable(self) -> None:
        """Enable this channel."""
        self._enabled = True
        logger.info(f"{self.__class__.__name__} enabled")

    def disable(self) -> None:
        """Disable this channel."""
        self._enabled = False
        logger.info(f"{self.__class__.__name__} disabled")

    def supports_rich_content(self) -> bool:
        """Check if this channel supports rich content (cards, images, etc.).

        Returns:
            True if rich content is supported (default: True)
        """
        return True

    def get_max_content_length(self) -> int:
        """Get maximum content length for this channel.

        Returns:
            Maximum content length in characters (default: unlimited)
        """
        return -1  # -1 means unlimited
