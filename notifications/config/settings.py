"""Configuration management for Feishu notifications.

This module provides a hierarchical configuration system that reads settings
from multiple sources in order of precedence:
1. Direct parameters (highest priority)
2. Environment variables (FEISHU_WEBHOOK_URL, FEISHU_WEBHOOK_SECRET)
3. TOML configuration file (feishu_notify.toml)
4. Default values (lowest priority)

Example:
    >>> from notifications.config.settings import NotificationSettings, create_settings
    >>>
    >>> # Load from environment variables and defaults
    >>> settings = create_settings()
    >>>
    >>> # Override with direct parameters
    >>> settings = create_settings(
    ...     webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    ...     webhook_secret="my-secret"
    ... )
"""

from __future__ import annotations
from typing import Optional
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class NotificationSettings(BaseSettings):
    """Feishu notification configuration settings.

    This class manages configuration loading from multiple sources with
    proper precedence ordering. Environment variables should be prefixed
    with 'FEISHU_' (e.g., FEISHU_WEBHOOK_URL).

    Attributes:
        webhook_url: The Feishu webhook URL endpoint for sending notifications
        webhook_secret: The webhook secret for generating signatures (optional)
        enable_throttling: Whether to enable rate limiting (default: True)
        enable_grouping: Whether to enable message grouping (default: True)
        max_retries: Maximum number of retry attempts for failed requests (default: 3)
        timeout_seconds: Request timeout in seconds (default: 10)
    """

    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    enable_throttling: bool = True
    enable_grouping: bool = True
    max_retries: int = 3
    timeout_seconds: int = 10

    model_config = SettingsConfigDict(
        env_prefix="FEISHU_",
        env_file=".env",
        toml_file="feishu_notify.toml",
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Define the order of configuration sources.

        Returns sources in order of precedence (highest to lowest):
        1. Direct initialization parameters (function arguments)
        2. Environment variables (FEISHU_*)
        3. TOML configuration file (feishu_notify.toml)

        Args:
            settings_cls: The settings class being configured
            init_settings: Direct initialization parameters source
            env_settings: Environment variable source
            dotenv_settings: .env file source
            file_secret_settings: Secret file source (unused)

        Returns:
            Tuple of settings sources in precedence order
        """
        # Order: Direct params (init_settings), env vars, .env file, TOML file
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    def validate_required_fields(self) -> tuple[bool, list[str]]:
        """Validate that required configuration fields are set.

        Returns:
            Tuple of (is_valid, missing_fields)
            - is_valid: True if all required fields are set
            - missing_fields: List of missing required field names

        Example:
            >>> settings = create_settings()
            >>> is_valid, missing = settings.validate_required_fields()
            >>> if not is_valid:
            ...     print(f"Missing fields: {missing}")
        """
        missing_fields = []

        if not self.webhook_url:
            missing_fields.append("webhook_url")

        return len(missing_fields) == 0, missing_fields

    def get_webhook_url(self) -> str:
        """Get the webhook URL, raising an error if not configured.

        Returns:
            The configured webhook URL

        Raises:
            ValueError: If webhook_url is not configured

        Example:
            >>> settings = create_settings(webhook_url="https://example.com")
            >>> url = settings.get_webhook_url()
        """
        if not self.webhook_url:
            raise ValueError(
                "Webhook URL not configured. Please set:\n"
                "  - FEISHU_WEBHOOK_URL environment variable, or\n"
                "  - webhook_url in feishu_notify.toml, or\n"
                "  - Pass webhook_url parameter directly"
            )
        return self.webhook_url

    def has_secret(self) -> bool:
        """Check if webhook secret is configured.

        Returns:
            True if webhook_secret is set, False otherwise

        Example:
            >>> settings = create_settings(webhook_secret="my-secret")
            >>> if settings.has_secret():
            ...     print("Secret is configured")
        """
        return self.webhook_secret is not None and len(self.webhook_secret) > 0


def create_settings(
    toml_file: Optional[str] = None,
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None,
    enable_throttling: Optional[bool] = None,
    enable_grouping: Optional[bool] = None,
    max_retries: Optional[int] = None,
    timeout_seconds: Optional[int] = None,
) -> NotificationSettings:
    """Create settings with optional custom configuration sources.

    This function creates a settings instance that respects the configuration
    hierarchy while allowing for custom TOML file paths and direct parameter
    overrides.

    Args:
        toml_file: Custom path to TOML configuration file (optional)
        webhook_url: Direct webhook URL override (highest priority)
        webhook_secret: Direct webhook secret override (highest priority)
        enable_throttling: Enable rate limiting (default: True)
        enable_grouping: Enable message grouping (default: True)
        max_retries: Maximum retry attempts (default: 3)
        timeout_seconds: Request timeout in seconds (default: 10)

    Returns:
        Configured NotificationSettings instance

    Example:
        >>> # Use default configuration sources
        >>> settings = create_settings()
        >>>
        >>> # Use custom TOML file
        >>> settings = create_settings(toml_file="/path/to/config.toml")
        >>>
        >>> # Override with direct parameters
        >>> settings = create_settings(
        ...     webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
        ...     webhook_secret="secret123",
        ...     max_retries=5
        ... )
    """
    # Prepare initialization parameters (highest priority)
    init_kwargs = {}
    if webhook_url is not None:
        init_kwargs["webhook_url"] = webhook_url
    if webhook_secret is not None:
        init_kwargs["webhook_secret"] = webhook_secret
    if enable_throttling is not None:
        init_kwargs["enable_throttling"] = enable_throttling
    if enable_grouping is not None:
        init_kwargs["enable_grouping"] = enable_grouping
    if max_retries is not None:
        init_kwargs["max_retries"] = max_retries
    if timeout_seconds is not None:
        init_kwargs["timeout_seconds"] = timeout_seconds

    if toml_file and Path(toml_file).exists():
        # Create a custom settings class with specified TOML file
        class CustomSettings(NotificationSettings):
            model_config = SettingsConfigDict(
                env_prefix="FEISHU_",
                env_file=".env",
                toml_file=toml_file,
                extra="ignore",
                case_sensitive=False,
            )

        return CustomSettings(**init_kwargs)
    else:
        # Use default TOML file path
        if toml_file and not Path(toml_file).exists():
            # Log a warning about missing custom TOML file, but continue
            import logging

            logger = logging.getLogger("feishu-notifications")
            logger.propagate = False
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter("%(levelname)s: %(message)s")
                )
                logger.addHandler(handler)
                logger.setLevel(logging.WARNING)
            logger.warning(
                f"Custom TOML file not found: {toml_file}. "
                "Using default configuration sources."
            )

        return NotificationSettings(**init_kwargs)


if __name__ == "__main__":
    """Simple configuration test when run as a script."""
    import sys

    print("Feishu Notification Configuration")
    print("=" * 50)

    config = create_settings()

    print("\nLoaded Configuration:")
    print(f"  Webhook URL: {config.webhook_url or 'Not configured'}")
    print(f"  Webhook Secret: {'Set' if config.has_secret() else 'Not configured'}")
    print(f"  Enable Throttling: {config.enable_throttling}")
    print(f"  Enable Grouping: {config.enable_grouping}")
    print(f"  Max Retries: {config.max_retries}")
    print(f"  Timeout: {config.timeout_seconds}s")

    is_valid, missing = config.validate_required_fields()

    if not is_valid:
        print("\n⚠ Configuration incomplete!")
        print("Missing required fields:")
        for field in missing:
            print(f"  - {field}")
        print("\nPlease set:")
        print("  - FEISHU_WEBHOOK_URL environment variable, or")
        print("  - webhook_url in feishu_notify.toml")
        sys.exit(1)
    else:
        print("\n✅ Configuration is valid!")
        sys.exit(0)
