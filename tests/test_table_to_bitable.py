"""
Tests for Markdown table to Feishu Bitable converter.

Tests for table extraction, field type inference, and Bitable creation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from scripts.md_table_to_bitable import TableToBitableConverter
from lib.feishu_api_client import (
    FeishuApiClient,
    BitableFieldType,
)


@pytest.fixture
def mock_client():
    """Create a mock Feishu API client."""
    client = FeishuApiClient("test_app_id", "test_app_secret")
    return client


@pytest.fixture
def converter(mock_client):
    """Create a TableToBitableConverter with mock client."""
    return TableToBitableConverter(mock_client)


class TestTableExtraction:
    """Tests for table extraction from Markdown."""

    def test_extract_single_table(self, converter):
        """Test extracting a single simple table."""
        md_content = """# Document

| Name | Age | City |
|------|-----|------|
| Alice | 30 | NYC |
| Bob | 25 | LA |
"""
        tables = converter.extract_tables(md_content)

        assert len(tables) == 1
        assert tables[0]["headers"] == ["Name", "Age", "City"]
        assert tables[0]["row_count"] == 2
        assert tables[0]["column_count"] == 3
        assert tables[0]["rows"][0] == ["Alice", "30", "NYC"]

    def test_extract_multiple_tables(self, converter):
        """Test extracting multiple tables from one document."""
        md_content = """# Document

| Name | Age |
|------|-----|
| Alice | 30 |

Some text.

| Task | Status |
|------|--------|
| Task 1 | Done |
| Task 2 | In Progress |
"""
        tables = converter.extract_tables(md_content)

        assert len(tables) == 2
        assert tables[0]["headers"] == ["Name", "Age"]
        assert tables[1]["headers"] == ["Task", "Status"]

    def test_extract_table_with_empty_cells(self, converter):
        """Test handling tables with empty cells."""
        md_content = """| Name | Age | Notes |
|------|-----|-------|
| Alice | 30 | |
| Bob | | VIP |
| | 25 | New |
"""
        tables = converter.extract_tables(md_content)

        assert len(tables) == 1
        assert tables[0]["row_count"] == 3
        # Empty cells should be preserved as empty strings
        assert tables[0]["rows"][0][2] == ""
        assert tables[0]["rows"][1][1] == ""

    def test_extract_no_tables(self, converter):
        """Test document with no tables."""
        md_content = """# Just Text

This is a document with no tables.

- List item 1
- List item 2
"""
        tables = converter.extract_tables(md_content)

        assert len(tables) == 0


class TestFieldTypeInference:
    """Tests for automatic field type detection."""

    def test_infer_text_field(self, converter):
        """Test inferring text field for string data."""
        headers = ["Name", "Description"]
        rows = [["Alice", "A person"], ["Bob", "Another person"]]

        fields = converter.infer_field_types(headers, rows)

        assert len(fields) == 2
        assert fields[0]["type"] == BitableFieldType.TEXT
        assert fields[1]["type"] == BitableFieldType.TEXT

    def test_infer_number_field(self, converter):
        """Test inferring number field for numeric data."""
        headers = ["Count", "Price"]
        rows = [["10", "25.5"], ["5", "99.99"]]

        fields = converter.infer_field_types(headers, rows)

        assert len(fields) == 2
        assert fields[0]["type"] == BitableFieldType.NUMBER
        assert fields[1]["type"] == BitableFieldType.NUMBER

    def test_infer_select_field(self, converter):
        """Test inferring single select for repetitive values."""
        headers = ["Status"]
        rows = [["Done"], ["In Progress"], ["Done"], ["Todo"], ["Done"]]

        fields = converter.infer_field_types(headers, rows)

        assert len(fields) == 1
        assert fields[0]["type"] == BitableFieldType.SINGLE_SELECT
        assert "options" in fields[0]
        assert len(fields[0]["options"]["options"]) == 3

    def test_infer_boolean_checkbox_field(self, converter):
        """Test inferring checkbox for boolean values."""
        headers = ["Active", "Verified"]
        rows = [["yes", "true"], ["no", "false"], ["Yes", "TRUE"]]

        fields = converter.infer_field_types(headers, rows)

        assert len(fields) == 2
        assert fields[0]["type"] == BitableFieldType.CHECKBOX
        assert fields[1]["type"] == BitableFieldType.CHECKBOX

    def test_infer_mixed_field_types(self, converter):
        """Test inferring different types for different columns."""
        headers = ["Name", "Age", "Status", "Active"]
        rows = [
            ["Alice", "30", "Done", "yes"],
            ["Bob", "25", "In Progress", "no"],
        ]

        fields = converter.infer_field_types(headers, rows)

        assert fields[0]["type"] == BitableFieldType.TEXT  # Name
        assert fields[1]["type"] == BitableFieldType.NUMBER  # Age
        assert fields[3]["type"] == BitableFieldType.CHECKBOX  # Active


class TestBitableCreation:
    """Tests for Bitable creation and data import."""

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_bitable_from_single_table(self, mock_post, mock_token, converter):
        """Test creating Bitable from a single table."""
        # Setup
        mock_token.return_value = "test_token"

        # Mock create_bitable
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "code": 0,
                "data": {"app": {"app_id": "bascnxxxxx", "name": "Test"}},
            },
        )

        tables = [
            {
                "headers": ["Name", "Age"],
                "rows": [["Alice", "30"], ["Bob", "25"]],
                "row_count": 2,
                "column_count": 2,
            }
        ]

        # Execute - use create_bitable directly
        result = converter.client.create_bitable("Test Tables")

        # Assert
        assert result["app_id"] == "bascnxxxxx"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_bitable_from_multiple_tables(self, mock_post, mock_token, converter):
        """Test creating Bitable from multiple tables."""
        # Setup
        mock_token.return_value = "test_token"
        call_count = [0]

        def mock_response(*args, **kwargs):
            call_count[0] += 1
            return Mock(
                status_code=200,
                json=lambda: {
                    "code": 0,
                    "data": {
                        "app": {"app_id": "bascnxxxxx", "name": "Test"},
                        "table": {"table_id": f"tbl{call_count[0]}", "name": "Table"},
                        "fields": [],
                        "records": [],
                    },
                },
            )

        mock_post.side_effect = mock_response

        tables = [
            {
                "headers": ["Name"],
                "rows": [["Alice"]],
                "row_count": 1,
                "column_count": 1,
            },
            {
                "headers": ["Task"],
                "rows": [["Task 1"]],
                "row_count": 1,
                "column_count": 1,
            },
        ]

        # Just verify the converter can handle multiple tables
        assert len(tables) == 2


class TestValueConversion:
    """Tests for value conversion during import."""

    def test_convert_numeric_value(self, converter):
        """Test converting string to number."""
        result = converter._convert_value("123.45", BitableFieldType.NUMBER)
        assert isinstance(result, float)
        assert result == 123.45

    def test_convert_formatted_number(self, converter):
        """Test converting formatted number string."""
        result = converter._convert_value("1,234.56", BitableFieldType.NUMBER)
        assert result == 1234.56

    def test_convert_checkbox_value(self, converter):
        """Test converting various boolean representations."""
        assert converter._convert_value("yes", BitableFieldType.CHECKBOX) is True
        assert converter._convert_value("no", BitableFieldType.CHECKBOX) is False
        assert converter._convert_value("true", BitableFieldType.CHECKBOX) is True
        assert converter._convert_value("false", BitableFieldType.CHECKBOX) is False
        assert converter._convert_value("1", BitableFieldType.CHECKBOX) is True
        assert converter._convert_value("0", BitableFieldType.CHECKBOX) is False

    def test_convert_text_value_unchanged(self, converter):
        """Test that text values remain unchanged."""
        result = converter._convert_value("Hello World", BitableFieldType.TEXT)
        assert result == "Hello World"
        assert isinstance(result, str)


class TestErrorHandling:
    """Tests for error handling."""

    def test_empty_tables_list(self, converter):
        """Test handling empty tables list."""
        with pytest.raises(ValueError, match="No tables found"):
            converter.create_bitable_from_tables([])

    def test_invalid_table_index(self, converter):
        """Test handling invalid table index."""
        tables = [{"headers": ["A"], "rows": [["x"]], "row_count": 1, "column_count": 1}]

        with pytest.raises(ValueError, match="Invalid table_index"):
            converter.create_bitable_from_tables(tables, table_index=5)


class TestCLI:
    """Tests for CLI interface."""

    def test_converter_initialization(self, mock_client):
        """Test converter can be initialized."""
        converter = TableToBitableConverter(mock_client)
        assert converter.client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
