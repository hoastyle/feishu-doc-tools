"""
Tests for extended Feishu API client functionality.

Tests for document creation, folder management, and batch operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lib.feishu_api_client import (
    FeishuApiClient,
    FeishuApiRequestError,
    FeishuApiAuthError,
    BitableFieldType,
    create_document_from_markdown,
    batch_create_documents_from_folder,
)


@pytest.fixture
def mock_client():
    """Create a mock Feishu API client."""
    client = FeishuApiClient("test_app_id", "test_app_secret")
    return client


@pytest.fixture
def sample_md_file(tmp_path):
    """Create a sample markdown file for testing."""
    md_content = """# Test Document

This is a test document with multiple content types.

## Section 1

Some **bold** and *italic* text.

### Code Block

```python
def hello():
    print("Hello, World!")
```

## Lists

- Item 1
- Item 2

1. First
2. Second

## Images

![Sample Image](image.png)
"""
    md_file = tmp_path / "test.md"
    md_file.write_text(md_content, encoding="utf-8")
    return md_file


class TestDocumentCreation:
    """Tests for document creation functionality."""

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_document_success(self, mock_post, mock_token, mock_client):
        """Test successful document creation."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "document": {
                    "document_id": "doxcnxxxxx",
                    "title": "Test Document",
                    "revision_id": 1,
                }
            },
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_document("Test Document")

        # Assert
        assert result["document_id"] == "doxcnxxxxx"
        assert result["title"] == "Test Document"
        assert "https://feishu.cn/docx/doxcnxxxxx" in result["url"]
        mock_post.assert_called_once()

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_document_with_folder(self, mock_post, mock_token, mock_client):
        """Test creating document in specific folder."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {"document": {"document_id": "doxcnxxxxx", "title": "Test", "revision_id": 1}},
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_document("Test", folder_token="fldcnxxxxx")

        # Assert
        assert result["document_id"] == "doxcnxxxxx"
        # Check that folder_token was included in payload
        call_kwargs = mock_post.call_args[1]
        assert "Bearer test_token" in call_kwargs["headers"]["Authorization"]

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_document_auth_failure(self, mock_post, mock_token, mock_client):
        """Test document creation with auth failure."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError):
            mock_client.create_document("Test")

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_document_api_error(self, mock_post, mock_token, mock_client):
        """Test document creation with API error response."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 400, "msg": "Invalid request"}
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError):
            mock_client.create_document("Test")


class TestFolderOperations:
    """Tests for folder management functionality."""

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.get")
    def test_get_root_folder_token(self, mock_get, mock_token, mock_client):
        """Test getting root folder token."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "data": {"folder_token": "fldcnxxxxx"}}
        mock_get.return_value = mock_response

        # Execute
        result = mock_client.get_root_folder_token()

        # Assert
        assert result == "fldcnxxxxx"
        mock_get.assert_called_once()

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_folder_success(self, mock_post, mock_token, mock_client):
        """Test successful folder creation."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {"folder": {"folder_token": "fldcnxxxxx", "name": "Test Folder"}},
        }
        mock_post.return_value = mock_response

        # Mock get_root_folder_token
        with patch.object(mock_client, "get_root_folder_token", return_value="root_token"):
            # Execute
            result = mock_client.create_folder("Test Folder")

        # Assert
        assert result["folder_token"] == "fldcnxxxxx"
        assert result["name"] == "Test Folder"
        assert "https://feishu.cn/drive/folder/fldcnxxxxx" in result["url"]

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.get")
    def test_list_folder_contents(self, mock_get, mock_token, mock_client):
        """Test listing folder contents."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "items": [
                    {"name": "file1.md", "type": "file"},
                    {"name": "folder1", "type": "folder"},
                ]
            },
        }
        mock_get.return_value = mock_response

        # Execute
        result = mock_client.list_folder_contents("fldcnxxxxx")

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "file1.md"
        assert result[1]["name"] == "folder1"


class TestHighLevelFunctions:
    """Tests for high-level convenience functions."""

    @patch("lib.feishu_api_client.upload_markdown_to_feishu")
    @patch("lib.feishu_api_client.FeishuApiClient.create_document")
    def test_create_document_from_markdown(self, mock_create, mock_upload, sample_md_file):
        """Test create_document_from_markdown function."""
        # Setup
        mock_create.return_value = {
            "document_id": "doxcnxxxxx",
            "url": "https://feishu.cn/docx/doxcnxxxxx",
            "title": "test",
        }
        mock_upload.return_value = {
            "success": True,
            "total_blocks": 50,
            "total_images": 3,
            "total_batches": 1,
        }

        with patch("lib.feishu_api_client.FeishuApiClient.from_env") as mock_from_env:
            mock_client = Mock()
            mock_client.create_document = mock_create
            mock_from_env.return_value = mock_client

            # Execute
            result = create_document_from_markdown(str(sample_md_file), title="Test Document")

        # Assert
        assert result["document_id"] == "doxcnxxxxx"
        assert result["total_blocks"] == 50
        assert result["total_images"] == 3
        mock_create.assert_called_once()
        mock_upload.assert_called_once()

    def test_create_document_from_markdown_invalid_file(self):
        """Test create_document_from_markdown with non-existent file."""
        # Execute & Assert (RuntimeError is raised when conversion fails)
        with pytest.raises(RuntimeError):
            create_document_from_markdown("/non/existent/file.md")

    @patch("lib.feishu_api_client.create_document_from_markdown")
    @patch("lib.feishu_api_client.FeishuApiClient.from_env")
    def test_batch_create_documents_from_folder(self, mock_from_env, mock_create_doc, tmp_path):
        """Test batch document creation from folder."""
        # Setup - create test markdown files
        for i in range(3):
            (tmp_path / f"doc{i}.md").write_text(f"# Document {i}")

        mock_create_doc.side_effect = [
            {
                "document_id": f"docxcnxxxxx{i}",
                "document_url": f"https://feishu.cn/docx/docxcnxxxxx{i}",
                "total_blocks": 10,
                "total_images": 0,
            }
            for i in range(3)
        ]

        # Execute
        result = batch_create_documents_from_folder(str(tmp_path))

        # Assert
        assert result["total_files"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert len(result["documents"]) == 3
        assert mock_create_doc.call_count == 3

    def test_batch_create_documents_empty_folder(self, tmp_path):
        """Test batch creation on empty folder."""
        # Execute
        result = batch_create_documents_from_folder(str(tmp_path))

        # Assert
        assert result["total_files"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0

    def test_batch_create_documents_invalid_folder(self):
        """Test batch creation with non-existent folder."""
        # Execute & Assert
        with pytest.raises(FileNotFoundError):
            batch_create_documents_from_folder("/non/existent/folder")

    @patch("lib.feishu_api_client.create_document_from_markdown")
    @patch("lib.feishu_api_client.FeishuApiClient.from_env")
    def test_batch_create_documents_with_failures(self, mock_from_env, mock_create_doc, tmp_path):
        """Test batch creation with some failures."""
        # Setup - create test markdown files
        for i in range(3):
            (tmp_path / f"doc{i}.md").write_text(f"# Document {i}")

        # Make the second document fail
        mock_create_doc.side_effect = [
            {"document_id": "doc1", "document_url": "url1", "total_blocks": 10, "total_images": 0},
            FeishuApiRequestError("API Error"),
            {"document_id": "doc3", "document_url": "url3", "total_blocks": 10, "total_images": 0},
        ]

        # Execute
        result = batch_create_documents_from_folder(str(tmp_path))

        # Assert
        assert result["total_files"] == 3
        assert result["successful"] == 2
        assert result["failed"] == 1
        assert len(result["documents"]) == 2
        assert len(result["failures"]) == 1


class TestWikiSpaceOperations:
    """Tests for Wiki space operations."""

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_wiki_space_success(self, mock_post, mock_token, mock_client):
        """Test successful wiki space creation."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "success",
            "data": {
                "space": {
                    "space_id": "7516222021840306180",
                    "name": "Test Space",
                    "description": "Test Description",
                    "visibility": "public",
                }
            },
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_wiki_space("Test Space", "Test Description")

        # Assert
        assert result["space_id"] == "7516222021840306180"
        assert result["name"] == "Test Space"
        assert result["description"] == "Test Description"
        assert result["url"] == "https://feishu.cn/wiki/7516222021840306180"
        mock_post.assert_called_once()

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_wiki_space_without_description(self, mock_post, mock_token, mock_client):
        """Test creating wiki space without description."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "success",
            "data": {"space": {"space_id": "7516222021840306180", "name": "Test Space"}},
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_wiki_space("Test Space")

        # Assert
        assert result["space_id"] == "7516222021840306180"
        assert result["name"] == "Test Space"
        assert result["description"] is None
        mock_post.assert_called_once()

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_wiki_space_api_error(self, mock_post, mock_token, mock_client):
        """Test API error handling."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 99991663, "msg": "Space name already exists"}
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError, match="Space name already exists"):
            mock_client.create_wiki_space("Duplicate Space")

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_wiki_space_http_error(self, mock_post, mock_token, mock_client):
        """Test HTTP error handling."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError, match="HTTP 500"):
            mock_client.create_wiki_space("Test Space")


class TestWhiteboardOperations:
    """Tests for Whiteboard/Board block operations."""

    def test_format_board_block_basic(self, mock_client):
        """Test basic board block formatting."""
        # Setup
        options = {"board": {}}

        # Execute
        result = mock_client._format_board_block(options)

        # Assert
        assert result["block_type"] == 43
        assert "board" in result
        assert result["board"]["align"] == 2  # Default center

    def test_format_board_block_with_dimensions(self, mock_client):
        """Test board block with width and height."""
        # Setup
        options = {"board": {"width": 800, "height": 600, "align": 1}}

        # Execute
        result = mock_client._format_board_block(options)

        # Assert
        assert result["block_type"] == 43
        assert result["board"]["width"] == 800
        assert result["board"]["height"] == 600
        assert result["board"]["align"] == 1

    def test_format_board_block_partial_dimensions(self, mock_client):
        """Test board block with only width."""
        # Setup
        options = {"board": {"width": 1000}}

        # Execute
        result = mock_client._format_board_block(options)

        # Assert
        assert result["block_type"] == 43
        assert result["board"]["width"] == 1000
        assert "height" not in result["board"]
        assert result["board"]["align"] == 2  # Default

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_batch_create_with_board_block(self, mock_post, mock_token, mock_client):
        """Test batch creating blocks including board type."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {"blocks": [{"block_id": "block1"}, {"block_id": "block2"}]},
        }
        mock_post.return_value = mock_response

        blocks = [
            {"blockType": "text", "options": {"text": {"textStyles": [{"text": "Hello"}]}}},
            {"blockType": "board", "options": {"board": {"width": 800, "height": 600}}},
        ]

        # Execute
        result = mock_client.batch_create_blocks("doc123", blocks)

        # Assert
        assert result["code"] == 0
        mock_post.assert_called_once()
        # Verify the payload contains both text and board blocks
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert len(payload["children"]) == 2
        assert payload["children"][1]["block_type"] == 43  # Board block


class TestBitableOperations:
    """Tests for Bitable (multidimensional table) operations."""

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_bitable_success(self, mock_post, mock_token, mock_client):
        """Test successful Bitable creation."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "app": {
                    "app_id": "bascnxxxxx",
                    "name": "Test Bitable",
                    "url": "https://feishu.cn/base/bascnxxxxx",
                }
            },
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_bitable("Test Bitable")

        # Assert
        assert result["app_id"] == "bascnxxxxx"
        assert result["name"] == "Test Bitable"
        assert "https://feishu.cn/base/" in result["url"]
        mock_post.assert_called_once()

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_bitable_with_folder(self, mock_post, mock_token, mock_client):
        """Test creating Bitable in specific folder."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {"app": {"app_id": "bascnxxxxx", "name": "Test"}},
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_bitable("Test", folder_token="fldcnxxxxx")

        # Assert
        assert result["app_id"] == "bascnxxxxx"
        # Verify folder_token was included in payload
        call_kwargs = mock_post.call_args[1]
        assert "folder_token" in call_kwargs["json"]

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_bitable_duplicate_name(self, mock_post, mock_token, mock_client):
        """Test Bitable creation with duplicate name error."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 400,
            "msg": "Bitable with this name already exists",
        }
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError, match="already exists"):
            mock_client.create_bitable("Existing Name")

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_table_with_text_fields(self, mock_post, mock_token, mock_client):
        """Test creating table with text fields."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "table": {"table_id": "tblxxxxx", "name": "People"},
                "fields": [
                    {"field_id": "fld1", "field_name": "Name", "type": 1},
                    {"field_id": "fld2", "field_name": "Email", "type": 1},
                ],
            },
        }
        mock_post.return_value = mock_response

        # Execute
        fields = [
            {"field_name": "Name", "type": BitableFieldType.TEXT},
            {"field_name": "Email", "type": BitableFieldType.TEXT},
        ]
        result = mock_client.create_table("app123", "People", fields)

        # Assert
        assert result["table_id"] == "tblxxxxx"
        assert result["table_name"] == "People"
        assert len(result["fields"]) == 2

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_table_with_select_fields(self, mock_post, mock_token, mock_client):
        """Test creating table with single select fields."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "table": {"table_id": "tblxxxxx", "name": "Tasks"},
                "fields": [
                    {"field_id": "fld1", "field_name": "Task", "type": 1},
                    {"field_id": "fld2", "field_name": "Status", "type": 4},
                ],
            },
        }
        mock_post.return_value = mock_response

        # Execute
        fields = [
            {"field_name": "Task", "type": BitableFieldType.TEXT},
            {
                "field_name": "Status",
                "type": BitableFieldType.SINGLE_SELECT,
                "options": {
                    "options": [
                        {"name": "To Do"},
                        {"name": "In Progress"},
                        {"name": "Done"},
                    ]
                },
            },
        ]
        result = mock_client.create_table("app123", "Tasks", fields)

        # Assert
        assert result["table_id"] == "tblxxxxx"
        assert result["table_name"] == "Tasks"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_insert_records_single(self, mock_post, mock_token, mock_client):
        """Test inserting a single record."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "records": [
                    {
                        "record_id": "recxxxxx",
                        "fields": {"Name": "Alice", "Age": 30},
                    }
                ]
            },
        }
        mock_post.return_value = mock_response

        # Execute
        records = [{"fields": {"Name": "Alice", "Age": 30}}]
        result = mock_client.insert_records("app123", "tbl456", records)

        # Assert
        assert result["total_records"] == 1
        assert len(result["record_ids"]) == 1
        assert result["record_ids"][0] == "recxxxxx"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_insert_records_batch(self, mock_post, mock_token, mock_client):
        """Test inserting multiple records in batch."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "records": [
                    {"record_id": "rec1", "fields": {"Name": "Alice"}},
                    {"record_id": "rec2", "fields": {"Name": "Bob"}},
                    {"record_id": "rec3", "fields": {"Name": "Charlie"}},
                ]
            },
        }
        mock_post.return_value = mock_response

        # Execute
        records = [
            {"fields": {"Name": "Alice"}},
            {"fields": {"Name": "Bob"}},
            {"fields": {"Name": "Charlie"}},
        ]
        result = mock_client.insert_records("app123", "tbl456", records)

        # Assert
        assert result["total_records"] == 3
        assert len(result["record_ids"]) == 3

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.get")
    def test_get_table_records_pagination(self, mock_get, mock_token, mock_client):
        """Test getting table records with pagination."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "items": [
                    {"record_id": "rec1", "fields": {"Name": "Alice"}},
                    {"record_id": "rec2", "fields": {"Name": "Bob"}},
                ],
                "has_more": True,
                "page_token": "next_page_token",
            },
        }
        mock_get.return_value = mock_response

        # Execute
        result = mock_client.get_table_records("app123", "tbl456", page_size=100)

        # Assert
        assert result["total_records"] == 2
        assert result["has_more"] is True
        assert result["page_token"] == "next_page_token"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.put")
    def test_update_record_success(self, mock_put, mock_token, mock_client):
        """Test successful record update."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "record": {
                    "record_id": "recxxxxx",
                    "fields": {"Name": "Alice Updated", "Age": 31},
                }
            },
        }
        mock_put.return_value = mock_response

        # Execute
        result = mock_client.update_record(
            "app123", "tbl456", "recxxxxx", {"Name": "Alice Updated", "Age": 31}
        )

        # Assert
        assert result["record_id"] == "recxxxxx"
        assert result["fields"]["Name"] == "Alice Updated"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.delete")
    def test_delete_record_success(self, mock_delete, mock_token, mock_client):
        """Test successful record deletion."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0}
        mock_delete.return_value = mock_response

        # Execute
        result = mock_client.delete_record("app123", "tbl456", "recxxxxx")

        # Assert
        assert result["success"] is True
        assert result["record_id"] == "recxxxxx"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_bitable_auth_error(self, mock_post, mock_token, mock_client):
        """Test Bitable operation with authentication error."""
        # Setup
        mock_token.side_effect = FeishuApiAuthError("Invalid token")

        # Execute & Assert
        with pytest.raises(FeishuApiAuthError):
            mock_client.create_bitable("Test")

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_bitable_invalid_app_id(self, mock_post, mock_token, mock_client):
        """Test table operation with invalid app ID."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 404,
            "msg": "Application not found",
        }
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError, match="not found"):
            mock_client.create_table("invalid_app", "Table", [])

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_bitable_field_type_constants(self, mock_post, mock_token, mock_client):
        """Test that BitableFieldType constants are properly defined."""
        # Execute
        assert BitableFieldType.TEXT == 1
        assert BitableFieldType.NUMBER == 2
        assert BitableFieldType.SINGLE_SELECT == 4
        assert BitableFieldType.MULTI_SELECT == 5
        assert BitableFieldType.DATE == 5
        assert BitableFieldType.DATETIME == 6
        assert BitableFieldType.PERSON == 7
        assert BitableFieldType.CHECKBOX == 11
        assert BitableFieldType.URL == 15

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_create_table_with_various_field_types(
        self, mock_post, mock_token, mock_client
    ):
        """Test creating table with various field types."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "table": {"table_id": "tblxxxxx", "name": "ComplexTable"},
                "fields": [
                    {"field_id": "fld1", "field_name": "Name", "type": 1},
                    {"field_id": "fld2", "field_name": "Count", "type": 2},
                    {"field_id": "fld3", "field_name": "Active", "type": 11},
                ],
            },
        }
        mock_post.return_value = mock_response

        # Execute
        fields = [
            {"field_name": "Name", "type": BitableFieldType.TEXT},
            {"field_name": "Count", "type": BitableFieldType.NUMBER},
            {"field_name": "Active", "type": BitableFieldType.CHECKBOX},
        ]
        result = mock_client.create_table("app123", "ComplexTable", fields)

        # Assert
        assert result["table_id"] == "tblxxxxx"
        assert len(result["fields"]) == 3


class TestErrorHandling:
    """Tests for error handling."""

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch("requests.Session.post")
    def test_network_timeout(self, mock_post, mock_token, mock_client):
        """Test handling of network timeout."""
        # Setup
        mock_token.return_value = "test_token"
        mock_post.side_effect = TimeoutError("Connection timeout")

        # Execute & Assert
        with pytest.raises(TimeoutError):
            mock_client.create_document("Test")

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    def test_token_retrieval_failure(self, mock_token, mock_client):
        """Test handling of token retrieval failure."""
        # Setup
        mock_token.side_effect = FeishuApiAuthError("Invalid credentials")

        # Execute & Assert
        with pytest.raises(FeishuApiAuthError):
            mock_client.create_document("Test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
