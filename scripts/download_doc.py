#!/usr/bin/env python3
"""
Download Feishu Document as Markdown

Downloads a Feishu document and converts it to Markdown format.
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.feishu_api_client import FeishuApiClient
from scripts.feishu_to_md import convert_feishu_to_markdown

logger = logging.getLogger(__name__)


def download_document(
    doc_id: str,
    output_path: str,
    app_id: str = None,
    app_secret: str = None,
) -> bool:
    """
    Download a Feishu document and save as Markdown.

    Args:
        doc_id: Document ID
        output_path: Output file path
        app_id: Optional Feishu app ID
        app_secret: Optional Feishu app secret

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize client
        if app_id and app_secret:
            client = FeishuApiClient(app_id, app_secret)
        else:
            client = FeishuApiClient.from_env()

        logger.info(f"Downloading document: {doc_id}")

        # Get all blocks
        blocks = client.get_all_document_blocks(doc_id)

        if not blocks:
            logger.warning("No blocks found in document")
            return False

        logger.info(f"Retrieved {len(blocks)} blocks")

        # Convert to Markdown
        markdown = convert_feishu_to_markdown(blocks)

        # Save to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        logger.info(f"Saved to: {output_file}")
        logger.info(f"File size: {len(markdown)} characters")

        return True

    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download Feishu document as Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download document to output.md
  uv run python scripts/download_doc.py doxcnxxxxx output.md

  # Download with custom app credentials
  uv run python scripts/download_doc.py doxcnxxxxx output.md \\
    --app-id cli_xxxxx --app-secret xxxxx

  # Enable verbose logging
  uv run python scripts/download_doc.py doxcnxxxxx output.md -v
        """,
    )

    parser.add_argument(
        "doc_id",
        help="Document ID (e.g., doxcnxxxxx)",
    )
    parser.add_argument(
        "output",
        help="Output Markdown file path",
    )
    parser.add_argument(
        "--app-id",
        help="Feishu app ID (or set FEISHU_APP_ID env var)",
    )
    parser.add_argument(
        "--app-secret",
        help="Feishu app secret (or set FEISHU_APP_SECRET env var)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Download document
    success = download_document(
        doc_id=args.doc_id,
        output_path=args.output,
        app_id=args.app_id,
        app_secret=args.app_secret,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
