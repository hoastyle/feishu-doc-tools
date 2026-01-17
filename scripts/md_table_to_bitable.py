#!/usr/bin/env python3
"""
Markdown Table to Feishu Bitable Converter

This script extracts tables from Markdown files and converts them to
Feishu Bitable (multidimensional tables) with automatic field type detection.

Usage:
    python md_table_to_bitable.py data.md
    python md_table_to_bitable.py data.md --name "My Data"
    python md_table_to_bitable.py data.md --folder fldcnxxxxx --auto-types
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import (
    FeishuApiClient,
    FeishuApiRequestError,
    BitableFieldType,
)

logger = logging.getLogger(__name__)


class TableToBitableConverter:
    """Convert Markdown tables to Feishu Bitable."""

    # Date patterns for type detection
    DATE_PATTERNS = [
        r"\d{4}-\d{2}-\d{2}",  # 2024-01-15
        r"\d{4}/\d{2}/\d{2}",  # 2024/01/15
        r"\d{2}-\d{2}-\d{4}",  # 01-15-2024
        r"\d{1,2}\.\d{1,2}\.\d{4}",  # 1.15.2024
    ]

    def __init__(self, client: FeishuApiClient):
        """
        Initialize converter.

        Args:
            client: Feishu API client instance
        """
        self.client = client

    def extract_tables(self, md_content: str) -> List[Dict[str, Any]]:
        """
        Extract all tables from Markdown content.

        This method parses Markdown tables in pipe syntax:
        | Header1 | Header2 |
        |---------|---------|
        | Data1   | Data2   |

        Args:
            md_content: Markdown file content

        Returns:
            List of tables, each with:
                - headers: List of column headers
                - rows: List of data rows
                - row_count: Number of rows
                - column_count: Number of columns
        """
        tables = []

        # Split content into lines
        lines = md_content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Detect table header: starts with |
            if line.startswith("|") and "|" in line[1:]:
                # Found potential table, parse it
                headers, rows, end_idx = self._parse_table(lines, i)
                if headers and rows:
                    tables.append(
                        {
                            "headers": headers,
                            "rows": rows,
                            "row_count": len(rows),
                            "column_count": len(headers),
                        }
                    )
                i = end_idx
            else:
                i += 1

        logger.info(f"Extracted {len(tables)} table(s) from Markdown")
        return tables

    def _parse_table(
        self, lines: List[str], start_idx: int
    ) -> Tuple[List[str], List[List[str]], int]:
        """
        Parse a single table from lines.

        Args:
            lines: All content lines
            start_idx: Starting line index

        Returns:
            Tuple of (headers, rows, end_index)
        """
        # Parse header row
        header_line = lines[start_idx].strip()
        headers = [
            cell.strip() for cell in header_line.split("|")[1:-1]  # Remove empty ends
        ]

        if not headers:
            return [], [], start_idx + 1

        # Check for separator row (next line)
        if start_idx + 1 >= len(lines):
            return headers, [], start_idx + 1

        sep_line = lines[start_idx + 1].strip()
        if not (sep_line.startswith("|") and re.search(r"\|[\s\-:]+\|", sep_line)):
            # No separator found, might not be a proper Markdown table
            return headers, [], start_idx + 1

        # Parse data rows
        rows = []
        i = start_idx + 2
        while i < len(lines):
            line = lines[i].strip()
            if not line.startswith("|"):
                # End of table
                break

            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells and len(cells) == len(headers):
                rows.append(cells)
            i += 1

        return headers, rows, i

    def infer_field_types(
        self, headers: List[str], rows: List[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Auto-detect field types from table data.

        Detection logic:
        - All numeric values -> NUMBER
        - Contains date patterns -> DATE or DATETIME
        - Few unique values (< 10) and repetitive -> SINGLE_SELECT
        - All boolean-like (yes/no, true/false) -> CHECKBOX
        - Default -> TEXT

        Args:
            headers: Column headers
            rows: Data rows

        Returns:
            List of field definitions with type and options
        """
        fields = []

        for col_idx, header in enumerate(headers):
            # Get all values in this column
            values = []
            for row in rows:
                if col_idx < len(row):
                    val = row[col_idx].strip()
                    if val:
                        values.append(val)

            if not values:
                # Empty column, default to text
                fields.append({"field_name": header, "type": BitableFieldType.TEXT})
                continue

            # Detect type
            field_type, options = self._detect_column_type(header, values)
            fields.append(
                {
                    "field_name": header,
                    "type": field_type,
                    **({"options": options} if options else {}),
                }
            )

        logger.info(f"Inferred field types: {[f['field_name'] for f in fields]}")
        return fields

    def _detect_column_type(
        self, header: str, values: List[str]
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        Detect the type of a column based on its values.

        Args:
            header: Column header name
            values: Non-empty cell values

        Returns:
            Tuple of (field_type, options)
        """
        # Check for checkbox/boolean
        if self._is_boolean_column(values):
            return BitableFieldType.CHECKBOX, None

        # Check for numeric
        if self._is_numeric_column(values):
            return BitableFieldType.NUMBER, None

        # Check for date
        if self._is_date_column(values):
            return BitableFieldType.DATE, None

        # Check for select (few unique values)
        unique_values = set(values)
        if len(unique_values) <= 10 and len(unique_values) < len(values) * 0.5:
            options = [
                {"name": str(val)} for val in sorted(unique_values, key=lambda x: str(x))
            ]
            return BitableFieldType.SINGLE_SELECT, {"options": options}

        # Default to text
        return BitableFieldType.TEXT, None

    def _is_boolean_column(self, values: List[str]) -> bool:
        """Check if column contains boolean values."""
        boolean_values = {
            "true",
            "false",
            "yes",
            "no",
            "y",
            "n",
            "1",
            "0",
            "✓",
            "✗",
            "是",
            "否",
        }
        normalized = {v.lower().strip() for v in values}
        return normalized.issubset(boolean_values)

    def _is_numeric_column(self, values: List[str]) -> bool:
        """Check if column contains only numeric values."""
        for val in values:
            # Remove common number formatting
            cleaned = (
                val.replace(",", "").replace("%", "").replace("$", "").replace("¥", "").strip()
            )
            try:
                float(cleaned)
            except ValueError:
                return False
        return True

    def _is_date_column(self, values: List[str]) -> bool:
        """Check if column contains date values."""
        date_count = 0
        for val in values:
            for pattern in self.DATE_PATTERNS:
                if re.search(pattern, val):
                    date_count += 1
                    break
        # If more than 50% match date patterns, consider it a date column
        return len(values) > 0 and (date_count / len(values)) > 0.5

    def create_bitable_from_tables(
        self,
        tables: List[Dict[str, Any]],
        bitable_name: Optional[str] = None,
        folder_token: Optional[str] = None,
        auto_types: bool = True,
        table_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create Bitable from extracted tables.

        Args:
            tables: List of extracted tables
            bitable_name: Name for the Bitable app (default: "Tables from {filename}")
            folder_token: Optional folder token
            auto_types: Whether to auto-detect field types
            table_index: Only convert specific table (0-based index)

        Returns:
            Dictionary with created Bitable information
        """
        if not tables:
            raise ValueError("No tables found in Markdown file")

        # Filter to specific table if requested
        if table_index is not None:
            if table_index < 0 or table_index >= len(tables):
                raise ValueError(
                    f"Invalid table_index: {table_index}. "
                    f"File contains {len(tables)} table(s)."
                )
            tables = [tables[table_index]]

        # Create Bitable app
        if not bitable_name:
            bitable_name = f"Tables from {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        logger.info(f"Creating Bitable: {bitable_name}")
        bitable = self.client.create_bitable(bitable_name, folder_token=folder_token)
        app_id = bitable["app_id"]

        results = {
            "success": True,
            "app_id": app_id,
            "app_name": bitable_name,
            "app_url": bitable["url"],
            "tables": [],
        }

        # Create tables and import data
        for idx, table in enumerate(tables):
            headers = table["headers"]
            rows = table["rows"]

            # Infer or use default field types
            if auto_types:
                fields = self.infer_field_types(headers, rows)
            else:
                # Default all to text
                fields = [
                    {"field_name": h, "type": BitableFieldType.TEXT} for h in headers
                ]

            # Create table name
            table_name = headers[0] if headers else f"Table {idx + 1}"
            if len(table_name) > 50:
                table_name = table_name[:50]

            logger.info(f"Creating table: {table_name}")
            table_result = self.client.create_table(app_id, table_name, fields)
            table_id = table_result["table_id"]

            # Insert records
            if rows:
                records = []
                for row in rows:
                    record = {"fields": {}}
                    for col_idx, header in enumerate(headers):
                        if col_idx < len(row):
                            value = row[col_idx].strip()
                            if value:
                                # Convert based on field type
                                field_type = fields[col_idx]["type"]
                                record["fields"][header] = self._convert_value(
                                    value, field_type
                                )
                    records.append(record)

                logger.info(f"Inserting {len(records)} records into {table_name}")
                insert_result = self.client.insert_records(app_id, table_id, records)

                results["tables"].append(
                    {
                        "table_id": table_id,
                        "table_name": table_name,
                        "row_count": len(rows),
                        "column_count": len(headers),
                        "records_inserted": insert_result["total_records"],
                    }
                )
            else:
                results["tables"].append(
                    {
                        "table_id": table_id,
                        "table_name": table_name,
                        "row_count": 0,
                        "column_count": len(headers),
                        "records_inserted": 0,
                    }
                )

        return results

    def _convert_value(self, value: str, field_type: int) -> Any:
        """
        Convert string value to appropriate type for field.

        Args:
            value: String value from cell
            field_type: Bitable field type constant

        Returns:
            Converted value
        """
        if field_type == BitableFieldType.NUMBER:
            try:
                # Remove formatting
                cleaned = (
                    value.replace(",", "")
                    .replace("%", "")
                    .replace("$", "")
                    .replace("¥", "")
                    .strip()
                )
                return float(cleaned)
            except ValueError:
                return value

        elif field_type == BitableFieldType.CHECKBOX:
            normalized = value.lower().strip()
            return normalized in {"true", "yes", "y", "1", "✓", "是"}

        elif field_type == BitableFieldType.DATE:
            # Try to parse and format date
            for pattern in self.DATE_PATTERNS:
                match = re.search(pattern, value)
                if match:
                    date_str = match.group()
                    # Normalize to YYYY-MM-DD format
                    try:
                        # Simple normalization
                        if "-" in date_str and len(date_str.split("-")[0]) == 4:
                            return int(
                                datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000
                            )
                    except ValueError:
                        pass
            return value

        # Default: return as string
        return value


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown tables to Feishu Bitable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python md_table_to_bitable.py data.md

  # Custom Bitable name
  python md_table_to_bitable.py data.md --name "My Data"

  # Create in specific folder
  python md_table_to_bitable.py data.md --folder fldcnxxxxx

  # Auto-detect field types
  python md_table_to_bitable.py data.md --auto-types

  # Convert only specific table (first table = 0)
  python md_table_to_bitable.py data.md --table-index 0
        """,
    )
    parser.add_argument(
        "markdown_file",
        help="Path to Markdown file containing tables",
    )
    parser.add_argument(
        "--name",
        help="Custom name for the Bitable (default: auto-generated)",
    )
    parser.add_argument(
        "--folder",
        help="Folder token to create Bitable in specific location",
    )
    parser.add_argument(
        "--auto-types",
        action="store_true",
        help="Auto-detect field types from data (default: True)",
    )
    parser.add_argument(
        "--table-index",
        type=int,
        help="Only convert specific table (0-based index)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
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
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Validate input file
    md_file = Path(args.markdown_file)
    if not md_file.exists():
        logger.error(f"File not found: {md_file}")
        sys.exit(1)

    # Initialize client
    try:
        client = FeishuApiClient.from_env()
    except ValueError as e:
        logger.error(f"Failed to initialize Feishu API client: {e}")
        sys.exit(1)

    # Read Markdown content
    logger.info(f"Reading Markdown file: {md_file}")
    md_content = md_file.read_text(encoding="utf-8")

    # Initialize converter
    converter = TableToBitableConverter(client)

    # Extract tables
    tables = converter.extract_tables(md_content)

    if not tables:
        logger.error("No tables found in Markdown file")
        sys.exit(1)

    logger.info(f"Found {len(tables)} table(s)")

    # Create Bitable
    try:
        result = converter.create_bitable_from_tables(
            tables=tables,
            bitable_name=args.name,
            folder_token=args.folder,
            auto_types=args.auto_types,
            table_index=args.table_index,
        )

        # Output results
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\n" + "=" * 50)
            print("Bitable Created Successfully!")
            print("=" * 50)
            print(f"App ID: {result['app_id']}")
            print(f"App Name: {result['app_name']}")
            print(f"URL: {result['app_url']}")
            print(f"\nTables Created: {len(result['tables'])}")
            for i, table in enumerate(result['tables']):
                print(f"\n  Table {i + 1}: {table['table_name']}")
                print(f"    - Dimensions: {table['row_count']} rows x {table['column_count']} columns")
                print(f"    - Records inserted: {table['records_inserted']}")
            print("\n" + "=" * 50)

        sys.exit(0)

    except Exception as e:
        logger.error(f"Failed to create Bitable: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
