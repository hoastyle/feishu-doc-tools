"""Notification throttling system for rate limiting and duplicate detection.

This module provides intelligent notification frequency control to prevent notification
spam and respect API rate limits. It implements a 5-layer throttling system:
    1. Duplicate detection (content hash-based)
    2. Global rate limits (per minute/hour)
    3. Channel-specific limits (per channel type)
    4. Event-specific limits (per event type with cooldown)
    5. Priority-based throttling (CRITICAL always allowed)
"""

import time
import hashlib
import logging
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ThrottleAction(Enum):
    """Actions that can be taken by the throttle system."""

    ALLOW = "allow"  # Allow notification to be sent immediately
    BLOCK = "block"  # Block notification completely
    DELAY = "delay"  # Delay notification for later sending
    MERGE = "merge"  # Merge with similar notifications (reserved)


class NotificationPriority(Enum):
    """Priority levels for notifications."""

    CRITICAL = 4  # Always allowed, minimal throttling
    HIGH = 3  # Light throttling
    NORMAL = 2  # Normal throttling
    LOW = 1  # Heavy throttling


@dataclass
class NotificationRequest:
    """Data structure for a notification request.

    Attributes:
        notification_id: Unique identifier for this notification
        event_type: Type of event (e.g., "document_created", "sync_failed")
        channel: Channel name (e.g., "webhook", "feishu")
        priority: Priority level
        content: Notification content dictionary
        created_at: Timestamp of creation (defaults to current time)
    """

    notification_id: str
    event_type: str
    channel: str
    priority: NotificationPriority
    content: Dict[str, Any]
    created_at: float = field(default_factory=time.time)

    def get_content_hash(self) -> str:
        """Generate content hash for duplicate detection.

        Uses stable content fields to generate an 8-character hash.
        This helps identify duplicate notifications with the same content.

        Returns:
            8-character MD5 hash of key content fields
        """
        key_content = {
            "event_type": self.event_type,
            "channel": self.channel,
            "doc_name": self.content.get("doc_name", ""),
            "source": self.content.get("source", ""),
            "destination": self.content.get("destination", ""),
            "error_message": self.content.get("error_message", ""),
        }
        content_str = "|".join(f"{k}:{v}" for k, v in key_content.items())
        return hashlib.md5(content_str.encode("utf-8")).hexdigest()[:8]


class NotificationThrottle:
    """Intelligent notification rate limiter with 5-layer throttling.

    This class implements comprehensive rate limiting and duplicate detection
    for notification systems. It uses multiple layers of checks to ensure
    notifications are sent at appropriate rates without overwhelming users
    or hitting API rate limits.

    Args:
        max_per_minute: Maximum notifications per minute globally (default: 30)
        max_per_hour: Maximum notifications per hour globally (default: 300)
        duplicate_window: Window in seconds for duplicate detection (default: 300)
        channel_limits: Dict of per-channel limits (optional)
        event_limits: Dict of per-event limits (optional)
        priority_weights: Dict of priority weights (optional)

    Example:
        >>> throttle = NotificationThrottle(max_per_minute=20)
        >>> request = NotificationRequest(
        ...     notification_id="123",
        ...     event_type="document_created",
        ...     channel="webhook",
        ...     priority=NotificationPriority.NORMAL,
        ...     content={"doc_name": "test.md"}
        ... )
        >>> action, reason, delay = throttle.should_allow_notification(request)
        >>> if action == ThrottleAction.ALLOW:
        ...     # Send notification
        ...     pass
    """

    def __init__(
        self,
        max_per_minute: int = 30,
        max_per_hour: int = 300,
        duplicate_window: int = 300,
        channel_limits: Optional[Dict[str, Dict[str, int]]] = None,
        event_limits: Optional[Dict[str, Dict[str, int]]] = None,
        priority_weights: Optional[Dict[str, float]] = None,
    ):
        """Initialize notification throttle with configurable limits."""
        self.logger = logging.getLogger(self.__class__.__name__)

        # Global limits
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.duplicate_window = duplicate_window

        # Channel-specific limits
        self.channel_limits = channel_limits or {
            "webhook": {"max_per_minute": 20, "max_per_hour": 200},
            "feishu": {"max_per_minute": 20, "max_per_hour": 200},
        }

        # Event-specific limits with cooldown
        self.event_limits = event_limits or {
            "document_modified": {"max_per_minute": 5, "cooldown": 60},
            "document_deleted": {"max_per_minute": 3, "cooldown": 30},
            "sync_failed": {"max_per_minute": 5, "cooldown": 10},
            "error_occurred": {"max_per_minute": 5, "cooldown": 10},
        }

        # Priority weights (lower = more restricted)
        # Higher weight = higher load threshold before throttling
        self.priority_weights = priority_weights or {
            "CRITICAL": 1.0,  # Never throttled (load > 1.0 never happens)
            "HIGH": 0.95,  # Throttled at 95% load
            "NORMAL": 0.85,  # Throttled at 85% load
            "LOW": 0.5,  # Throttled at 50% load
        }

        # Notification history (using deque with maxlen for automatic cleanup)
        self.notification_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Duplicate detection cache: hash -> (last_time, count)
        self.duplicate_cache: Dict[str, Tuple[float, int]] = {}

        # Delayed notifications queue: (execute_at, request)
        self.delayed_notifications: List[Tuple[float, NotificationRequest]] = []

        # Statistics
        self.stats = {
            "allowed": 0,
            "blocked": 0,
            "delayed": 0,
            "merged": 0,
            "duplicates_filtered": 0,
        }

        # Cleanup timer
        self._last_cleanup = time.time()

    def should_allow_notification(
        self, request: NotificationRequest
    ) -> Tuple[ThrottleAction, str, Optional[float]]:
        """Check if notification should be allowed through 5-layer system.

        This is the main entry point for throttle checking. It runs through
        all throttle layers in order and returns the first non-ALLOW result.

        Args:
            request: NotificationRequest to check

        Returns:
            Tuple of (action, reason, delay_seconds):
                - action: ThrottleAction indicating what to do
                - reason: Human-readable explanation
                - delay_seconds: Optional delay time for DELAY actions

        Example:
            >>> action, reason, delay = throttle.should_allow_notification(request)
            >>> if action == ThrottleAction.ALLOW:
            ...     send_notification(request)
            >>> elif action == ThrottleAction.DELAY:
            ...     schedule_notification(request, delay)
            >>> else:  # BLOCK
            ...     log_blocked_notification(reason)
        """
        # Periodic cache cleanup
        self._periodic_cleanup()

        try:
            # Layer 1: Duplicate detection
            duplicate_result = self._check_duplicate(request)
            if duplicate_result[0] != ThrottleAction.ALLOW:
                return duplicate_result

            # Layer 2: Global rate limits
            global_result = self._check_global_limits(request)
            if global_result[0] != ThrottleAction.ALLOW:
                return global_result

            # Layer 3: Channel-specific limits
            channel_result = self._check_channel_limits(request)
            if channel_result[0] != ThrottleAction.ALLOW:
                return channel_result

            # Layer 4: Event-specific limits
            event_result = self._check_event_limits(request)
            if event_result[0] != ThrottleAction.ALLOW:
                return event_result

            # Layer 5: Priority-based throttling
            priority_result = self._check_priority_limits(request)
            if priority_result[0] != ThrottleAction.ALLOW:
                return priority_result

            # All checks passed - record and allow
            self._record_notification(request)
            self.stats["allowed"] += 1
            return ThrottleAction.ALLOW, "Notification allowed", None

        except Exception as e:
            self.logger.error(f"Throttle check exception: {e}")
            # Default to allow on error, but log it
            return ThrottleAction.ALLOW, f"Throttle check failed, allowing: {e}", None

    def _check_duplicate(
        self, request: NotificationRequest
    ) -> Tuple[ThrottleAction, str, Optional[float]]:
        """Layer 1: Check for duplicate notifications.

        Uses content hash to detect duplicate notifications within the
        configured time window. CRITICAL priority notifications are allowed
        to repeat up to 3 times within the window.

        Returns:
            (ALLOW, "", None) if not duplicate
            (BLOCK, reason, None) if duplicate detected
        """
        content_hash = request.get_content_hash()
        current_time = time.time()

        if content_hash in self.duplicate_cache:
            last_time, count = self.duplicate_cache[content_hash]

            # Within duplicate window
            if current_time - last_time < self.duplicate_window:
                # Update count
                self.duplicate_cache[content_hash] = (current_time, count + 1)

                # Allow critical notifications to repeat a few times
                # Don't record here - let main function handle it after all checks
                if request.priority == NotificationPriority.CRITICAL and count < 3:
                    return (
                        ThrottleAction.ALLOW,
                        "",  # Empty reason to indicate this should continue through other layers
                        None,
                    )

                self.stats["duplicates_filtered"] += 1
                return (
                    ThrottleAction.BLOCK,
                    f"Duplicate notification filtered (#{count + 1})",
                    None,
                )
            else:
                # Outside duplicate window, reset count
                self.duplicate_cache[content_hash] = (current_time, 1)
        else:
            # First occurrence
            self.duplicate_cache[content_hash] = (current_time, 1)

        return ThrottleAction.ALLOW, "", None

    def _check_global_limits(
        self, request: NotificationRequest
    ) -> Tuple[ThrottleAction, str, Optional[float]]:
        """Layer 2: Check global rate limits.

        Enforces global per-minute and per-hour limits. Can suggest delays
        if close to limits but not over.

        Returns:
            (ALLOW, "", None) if within limits
            (BLOCK, reason, None) if over limits
            (DELAY, reason, seconds) if approaching limits
        """
        # Check per-minute limit
        minute_count = self._get_notification_count("global", 60)

        if minute_count >= self.max_per_minute:
            self.stats["blocked"] += 1
            return (
                ThrottleAction.BLOCK,
                f"Global rate limit ({minute_count}/{self.max_per_minute}/min)",
                None,
            )

        # Check per-hour limit
        hour_count = self._get_notification_count("global", 3600)

        if hour_count >= self.max_per_hour:
            self.stats["blocked"] += 1
            return (
                ThrottleAction.BLOCK,
                f"Global hourly limit ({hour_count}/{self.max_per_hour}/hour)",
                None,
            )

        # Check if approaching limit (>=80%)
        if minute_count >= self.max_per_minute * 0.8:
            delay = self._calculate_delay("global", 60)
            self.stats["delayed"] += 1
            return (
                ThrottleAction.DELAY,
                f"Approaching global limit, delay {delay:.1f}s",
                delay,
            )

        return ThrottleAction.ALLOW, "", None

    def _check_channel_limits(
        self, request: NotificationRequest
    ) -> Tuple[ThrottleAction, str, Optional[float]]:
        """Layer 3: Check channel-specific rate limits.

        Different channels have different rate limits. This enforces
        per-channel limits to respect API quotas.

        Returns:
            (ALLOW, "", None) if within channel limits
            (BLOCK, reason, None) if over channel limits
            (DELAY, reason, seconds) if delay suggested
        """
        channel_config = self.channel_limits.get(request.channel, {})
        if not channel_config:
            return ThrottleAction.ALLOW, "", None

        # Check channel per-minute limit
        minute_count = self._get_notification_count(f"channel:{request.channel}", 60)
        max_per_minute = channel_config.get("max_per_minute", 999)

        if minute_count >= max_per_minute:
            # Try to delay if reasonable
            delay = self._calculate_delay(f"channel:{request.channel}", 60)
            if delay <= 30:  # Max 30 second delay
                self.stats["delayed"] += 1
                return (
                    ThrottleAction.DELAY,
                    f"Channel {request.channel} rate limit, delay {delay:.1f}s",
                    delay,
                )
            else:
                self.stats["blocked"] += 1
                return (
                    ThrottleAction.BLOCK,
                    f"Channel {request.channel} rate limit ({minute_count}/{max_per_minute}/min)",
                    None,
                )

        return ThrottleAction.ALLOW, "", None

    def _check_event_limits(
        self, request: NotificationRequest
    ) -> Tuple[ThrottleAction, str, Optional[float]]:
        """Layer 4: Check event-specific rate limits with cooldown.

        Different event types have different limits and cooldown periods.
        For example, error events might have a cooldown to prevent spam.

        Returns:
            (ALLOW, "", None) if within event limits
            (BLOCK, reason, None) if event throttled or on cooldown
        """
        event_config = self.event_limits.get(request.event_type, {})
        if not event_config:
            return ThrottleAction.ALLOW, "", None

        # Check cooldown period
        cooldown = event_config.get("cooldown", 0)
        if cooldown > 0:
            last_time = self._get_last_notification_time(f"event:{request.event_type}")
            if last_time and (time.time() - last_time) < cooldown:
                remaining = cooldown - (time.time() - last_time)
                self.stats["blocked"] += 1
                return (
                    ThrottleAction.BLOCK,
                    f"Event {request.event_type} on cooldown, {remaining:.0f}s remaining",
                    None,
                )

        # Check event frequency limit
        minute_count = self._get_notification_count(f"event:{request.event_type}", 60)
        max_per_minute = event_config.get("max_per_minute", 999)

        if minute_count >= max_per_minute:
            self.stats["blocked"] += 1
            return (
                ThrottleAction.BLOCK,
                f"Event {request.event_type} rate limit ({minute_count}/{max_per_minute}/min)",
                None,
            )

        return ThrottleAction.ALLOW, "", None

    def _check_priority_limits(
        self, request: NotificationRequest
    ) -> Tuple[ThrottleAction, str, Optional[float]]:
        """Layer 5: Check priority-based throttling.

        Lower priority notifications are more heavily throttled when the
        system is under load. CRITICAL priority notifications are never
        throttled by this layer.

        Returns:
            (ALLOW, "", None) if priority allows
            (BLOCK, reason, None) if priority too low for current load
            (DELAY, reason, seconds) if should delay based on priority
        """
        # Critical priority always allowed
        if request.priority == NotificationPriority.CRITICAL:
            return ThrottleAction.ALLOW, "", None

        # Calculate current system load
        current_load = self._calculate_current_load()
        weight = self.priority_weights.get(request.priority.name, 0.5)

        # If load is high, throttle based on priority
        # Higher weight = higher threshold before throttling
        if current_load > weight:
            if request.priority == NotificationPriority.HIGH:
                delay = min(5, current_load * 10)
                self.stats["delayed"] += 1
                return (
                    ThrottleAction.DELAY,
                    f"High system load, {request.priority.name} delayed {delay:.1f}s",
                    delay,
                )
            else:
                self.stats["blocked"] += 1
                return (
                    ThrottleAction.BLOCK,
                    f"High system load, {request.priority.name} priority blocked",
                    None,
                )

        return ThrottleAction.ALLOW, "", None

    def _get_notification_count(self, key: str, window_seconds: int) -> int:
        """Get notification count within time window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        history = self.notification_history[key]
        count = sum(1 for timestamp in history if timestamp >= cutoff_time)
        return count

    def _get_last_notification_time(self, key: str) -> Optional[float]:
        """Get timestamp of last notification for key."""
        history = self.notification_history[key]
        return history[-1] if history else None

    def _calculate_delay(self, key: str, window_seconds: int) -> float:
        """Calculate appropriate delay based on current rate.

        Analyzes recent notification rate and suggests a delay that would
        bring the rate back within limits.

        Returns:
            Suggested delay in seconds (max 60)
        """
        current_count = self._get_notification_count(key, window_seconds)
        if current_count == 0:
            return 0.0

        history = self.notification_history[key]
        if len(history) < 2:
            return 1.0

        # Calculate average interval from recent notifications
        recent = list(history)[-min(10, len(history)) :]
        if len(recent) < 2:
            return 1.0

        time_span = recent[-1] - recent[0]
        if time_span <= 0:
            return 1.0

        avg_interval = time_span / (len(recent) - 1)

        # Suggest delay to bring rate within limits
        suggested_delay = max(1.0, window_seconds / current_count - avg_interval)
        return min(suggested_delay, 60.0)  # Max 60 second delay

    def _calculate_current_load(self) -> float:
        """Calculate current system load as fraction of max capacity.

        Returns:
            Float between 0.0 and 1.0 representing current load
        """
        minute_count = self._get_notification_count("global", 60)
        return (
            min(1.0, minute_count / self.max_per_minute)
            if self.max_per_minute > 0
            else 0.0
        )

    def _record_notification(self, request: NotificationRequest):
        """Record notification in history for rate tracking."""
        current_time = time.time()

        # Record to all relevant histories
        self.notification_history["global"].append(current_time)
        self.notification_history[f"channel:{request.channel}"].append(current_time)
        self.notification_history[f"event:{request.event_type}"].append(current_time)

    def add_delayed_notification(
        self, request: NotificationRequest, delay_seconds: float
    ):
        """Add notification to delayed queue.

        Args:
            request: NotificationRequest to delay
            delay_seconds: Number of seconds to delay
        """
        execute_at = time.time() + delay_seconds
        self.delayed_notifications.append((execute_at, request))
        self.logger.debug(
            f"Added delayed notification: {request.notification_id}, delay {delay_seconds:.1f}s"
        )

    def get_ready_notifications(self) -> List[NotificationRequest]:
        """Get notifications that are ready to send from delay queue.

        Returns:
            List of NotificationRequests ready to send
        """
        current_time = time.time()
        ready = []
        remaining = []

        for execute_at, request in self.delayed_notifications:
            if execute_at <= current_time:
                ready.append(request)
            else:
                remaining.append((execute_at, request))

        self.delayed_notifications = remaining

        if ready:
            self.logger.debug(f"Retrieved {len(ready)} ready delayed notifications")

        return ready

    def get_throttle_stats(self) -> Dict[str, Any]:
        """Get current throttle statistics.

        Returns:
            Dictionary containing:
                - stats: Action counts (allowed, blocked, delayed, etc.)
                - current_load: Current system load (0.0 to 1.0)
                - load_status: Human-readable load status
                - delayed_count: Number of delayed notifications in queue
                - duplicate_cache_size: Size of duplicate detection cache
                - recent_activity: Notification counts for various windows
        """
        current_load = self._calculate_current_load()

        return {
            "stats": self.stats.copy(),
            "current_load": current_load,
            "load_status": self._get_load_status(current_load),
            "delayed_count": len(self.delayed_notifications),
            "duplicate_cache_size": len(self.duplicate_cache),
            "recent_activity": {
                "global_1min": self._get_notification_count("global", 60),
                "global_5min": self._get_notification_count("global", 300),
                "global_1hour": self._get_notification_count("global", 3600),
            },
        }

    def _get_load_status(self, load: float) -> str:
        """Convert load value to human-readable status."""
        if load < 0.3:
            return "Low"
        elif load < 0.6:
            return "Normal"
        elif load < 0.8:
            return "Medium"
        elif load < 0.95:
            return "High"
        else:
            return "Overload"

    def _periodic_cleanup(self):
        """Trigger periodic cache cleanup (every 5 minutes)."""
        current_time = time.time()

        if current_time - self._last_cleanup > 300:  # 5 minutes
            self.cleanup_cache()
            self._last_cleanup = current_time

    def cleanup_cache(self):
        """Clean up expired caches."""
        current_time = time.time()

        # Clean duplicate cache (keep 1 hour)
        expired_hashes = [
            h
            for h, (last_time, _) in self.duplicate_cache.items()
            if current_time - last_time > 3600
        ]

        for h in expired_hashes:
            del self.duplicate_cache[h]

        if expired_hashes:
            self.logger.debug(
                f"Cleaned {len(expired_hashes)} expired duplicate cache entries"
            )

        # Clean expired delayed notifications (>1 hour old)
        original_count = len(self.delayed_notifications)
        self.delayed_notifications = [
            (execute_at, request)
            for execute_at, request in self.delayed_notifications
            if execute_at > current_time - 3600
        ]

        cleaned = original_count - len(self.delayed_notifications)
        if cleaned > 0:
            self.logger.debug(f"Cleaned {cleaned} expired delayed notifications")

    def reset_stats(self):
        """Reset all statistics counters."""
        self.stats = {key: 0 for key in self.stats}
        self.logger.info("Reset throttle statistics")
