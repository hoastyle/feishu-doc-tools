#!/usr/bin/env python3
"""
Create new Feishu document from markdown file.

This script creates a new Feishu document and uploads markdown content to it.

Usage Examples:
    # Create document in root folder (use filename as title)
    uv run python scripts/create_feishu_doc.py README.md

    # Create with custom title
    uv run python scripts/create_feishu_doc.py README.md --title "My Document"

    # Create in specific folder
    uv run python scripts/create_feishu_doc.py README.md --folder fldcnxxxxx

    # Create with custom credentials
    uv run python scripts/create_feishu_doc.py README.md --app-id cli_xxxxx --app-secret xxxxx

    # Create and add edit permission for current user
    uv run python scripts/create_feishu_doc.py README.md --add-permission

    # Create with admin permission
    uv run python scripts/create_feishu_doc.py README.md --add-permission --permission-level admin

    # Create with permission for specific user
    uv run python scripts/create_feishu_doc.py README.md --add-permission --user-id ou_xxxxx

    # Show progress (already enabled by default)
    uv run python scripts/create_feishu_doc.py README.md -v

Features:
    - Creates new Feishu document with markdown content
    - Uploads images automatically
    - Supports folder targeting
    - Optional permission setting for users
    - Detailed logging and progress reporting
    - Error handling with helpful messages

Permission Setup:
    By default, created documents are only accessible to the app. To grant access:
    1. Use --add-permission flag to auto-grant edit permission to current user
    2. Set FEISHU_USER_ID environment variable with your user ID
    3. Or use --user-id to specify the user ID directly

    To find your user ID in Feishu:
    - Go to Settings > Profile > Copy User ID
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path so we can import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import create_document_from_markdown, FeishuApiClientError


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create new Feishu document from markdown file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create in root folder with filename as title
  uv run python scripts/create_feishu_doc.py README.md

  # Create with custom title
  uv run python scripts/create_feishu_doc.py docs/guide.md --title "User Guide"

  # Create in specific folder
  uv run python scripts/create_feishu_doc.py README.md --folder fldcnxxxxx

  # Use custom credentials
  uv run python scripts/create_feishu_doc.py README.md \\
    --app-id cli_xxxxx --app-secret xxxxx
        """,
    )

    parser.add_argument("md_file", type=Path, help="Path to markdown file to upload")

    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Document title (default: filename without extension)",
    )

    parser.add_argument(
        "--folder", type=str, default=None, help="Target folder token (default: root folder)"
    )

    parser.add_argument(
        "--app-id", type=str, default=None, help="Feishu app ID (or set FEISHU_APP_ID env var)"
    )

    parser.add_argument(
        "--app-secret",
        type=str,
        default=None,
        help="Feishu app secret (or set FEISHU_APP_SECRET env var)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output (debug logging)"
    )

    parser.add_argument(
        "--add-permission",
        action="store_true",
        help="Add edit permission for current user after creating document",
    )

    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="User ID to grant permission to (default: auto-detect or from FEISHU_USER_ID env var)",
    )

    parser.add_argument(
        "--permission-level",
        type=str,
        default="edit",
        choices=["view", "edit", "admin"],
        help="Permission level: view, edit, or admin (default: edit)",
    )

    args = parser.parse_args()

    # Enable debug logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate input file
    if not args.md_file.exists():
        logger.error(f"File not found: {args.md_file}")
        return 1

    if not args.md_file.is_file():
        logger.error(f"Not a file: {args.md_file}")
        return 1

    if args.md_file.suffix.lower() != ".md":
        logger.warning(f"File extension is not .md: {args.md_file}")

    try:
        # Create document
        logger.info(f"Creating document from: {args.md_file}")

        result = create_document_from_markdown(
            md_file=str(args.md_file),
            title=args.title,
            folder_token=args.folder,
            app_id=args.app_id,
            app_secret=args.app_secret,
            add_permission=args.add_permission,
            user_id=args.user_id,
            permission_level=args.permission_level,
        )

        # Print results
        print("\n" + "=" * 60)
        print("✅ Document Created Successfully")
        print("=" * 60)
        print(f"Title:           {result['title']}")
        print(f"Document ID:     {result['document_id']}")
        print(f"URL:             {result['document_url']}")
        print(f"Blocks:          {result['total_blocks']}")
        print(f"Images:          {result['total_images']}")
        print(f"Batches:         {result['total_batches']}")
        if result.get("permission_set"):
            print(f"Permission:      ✅ {args.permission_level} permission set for user")
        print("=" * 60)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1

    except FeishuApiClientError as e:
        logger.error(f"API Error: {e}")
        return 2

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
