#!/usr/bin/env python3
"""
Batch create Feishu documents from local folder.

This script scans a folder for markdown files and creates a Feishu document
for each one. Useful for migrating documentation from local files to Feishu.

Usage Examples:
    # Create documents from all .md files in ./docs
    uv run python scripts/batch_create_docs.py ./docs

    # Create in specific Feishu folder
    uv run python scripts/batch_create_docs.py ./docs --folder fldcnxxxxx

    # Custom file pattern
    uv run python scripts/batch_create_docs.py ./docs --pattern "*.markdown"

    # Use custom credentials
    uv run python scripts/batch_create_docs.py ./docs \\
      --app-id cli_xxxxx --app-secret xxxxx

    # Verbose output for debugging
    uv run python scripts/batch_create_docs.py ./docs -v

Features:
    - Scans folder recursively for markdown files
    - Creates individual Feishu documents for each file
    - Parallel-friendly logging (one document per line)
    - Detailed summary with success/failure counts
    - Error recovery (continues on individual file failures)
    - Custom file pattern support
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path so we can import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import (
    batch_create_documents_from_folder,
    FeishuApiClientError
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def format_size(bytes_size: int) -> str:
    """Format bytes to human readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_size < 1024:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f}TB"


def print_summary(result: Dict[str, Any]) -> None:
    """Print batch creation summary."""
    print("\n" + "="*70)
    print("📊 Batch Creation Summary")
    print("="*70)
    print(f"Total Files:    {result['total_files']}")
    print(f"✅ Successful:  {result['successful']}")
    print(f"❌ Failed:      {result['failed']}")

    if result['documents']:
        print("\n" + "─"*70)
        print("📄 Created Documents:")
        print("─"*70)

        total_blocks = 0
        total_images = 0

        for doc in result['documents']:
            print(f"  • {doc['file']:<30} → {doc['url']}")
            print(f"    Blocks: {doc['blocks']:>3} | Images: {doc['images']}")
            total_blocks += doc['blocks']
            total_images += doc['images']

        print("─"*70)
        print(f"Total Blocks Created: {total_blocks}")
        print(f"Total Images Uploaded: {total_images}")

    if result['failures']:
        print("\n" + "─"*70)
        print("❌ Failed Files:")
        print("─"*70)

        for failure in result['failures']:
            print(f"  • {failure['file']}")
            print(f"    Error: {failure['error']}")

    print("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch create Feishu documents from local folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create from all .md files in ./docs
  uv run python scripts/batch_create_docs.py ./docs

  # Create in specific Feishu folder
  uv run python scripts/batch_create_docs.py ./docs --folder fldcnxxxxx

  # Custom file pattern
  uv run python scripts/batch_create_docs.py ./docs --pattern "*.markdown"

  # Recursive search in subdirectories
  uv run python scripts/batch_create_docs.py ./docs --pattern "**/*.md"

  # Custom credentials
  uv run python scripts/batch_create_docs.py ./docs \\
    --app-id cli_xxxxx --app-secret xxxxx
        """
    )

    parser.add_argument(
        "folder",
        type=Path,
        help="Path to folder with markdown files"
    )

    parser.add_argument(
        "--folder",
        dest="feishu_folder",
        type=str,
        default=None,
        help="Target folder token in Feishu (default: root folder)"
    )

    parser.add_argument(
        "--pattern",
        type=str,
        default="*.md",
        help="File glob pattern to match (default: *.md)"
    )

    parser.add_argument(
        "--app-id",
        type=str,
        default=None,
        help="Feishu app ID (or set FEISHU_APP_ID env var)"
    )

    parser.add_argument(
        "--app-secret",
        type=str,
        default=None,
        help="Feishu app secret (or set FEISHU_APP_SECRET env var)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (debug logging)"
    )

    args = parser.parse_args()

    # Enable debug logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate input folder
    if not args.folder.exists():
        logger.error(f"Folder not found: {args.folder}")
        return 1

    if not args.folder.is_dir():
        logger.error(f"Not a directory: {args.folder}")
        return 1

    try:
        # Batch create documents
        logger.info(f"Scanning folder: {args.folder}")
        logger.info(f"Pattern: {args.pattern}")

        result = batch_create_documents_from_folder(
            folder_path=str(args.folder),
            feishu_folder_token=args.feishu_folder,
            pattern=args.pattern,
            app_id=args.app_id,
            app_secret=args.app_secret
        )

        # Print summary
        print_summary(result)

        # Return appropriate exit code
        return 0 if result['success'] else 1

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
